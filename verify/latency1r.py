# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""latency1r.py — LATENCY-1R (court B): render-start -> composited, the production render against the single-thread
reference, in the same sealed window session (off-gate, host).

    python verify/latency1r.py --host NAME [--session workshop/attest/sessionwalk-demo.json] [--per-cell 200] [--confirm]

LATENCY-1 cannot see the renderer (its instrument renders every frame before the window opens — LATENCY-1a). This
court, preregistered as its own rung before any host number, puts the render inside the clock: per sample the arm's
renderer runs on a pre-parsed sealed scene, the composite is blitted, and the sample ends when DwmFlush returns.
Two arms render the identical certified frame (PRODUCTION = fast::render at T=8; SINGLE-THREAD = the LOCKED
fast::emit), in two phase regimes (LOCKED: the render starts right after a composition; UNIFORM: at a seeded offset
uniform in [0, refresh) after one), interleaved ABBA. Witnesses come first, twice: the headless court
(`shell latency1r-selftest`, a deterministic mock surface) on THIS build, then the window court itself refuses to
take a number unless both arms reproduce every sealed frame witness and each other's composites.

Per regime the reading is computed from p50s (tail percentiles do not subtract): render delta dR = render(S) -
render(P), glass delta dG = total(S) - total(P), propagation = 1000*dG/dR permille (floored) — >= 500 PROPAGATES,
1..499 PARTIALLY ABSORBED, <= 0 ABSORBED, and dR <= 0 VOID (no render headroom in this apparatus). p99s are reported
beside it, never folded into it. Writes shell/attest/latency1r-<host>.json, citing LATENCY-1R. Never compared to
LATENCY-0/LATENCY-1 (a different observable) or to any emit p99; not input-to-photon.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "verify"))
import envelope  # noqa: E402

DEFAULT_SESSION = "workshop/attest/sessionwalk-demo.json"
PHASE_SEED = "0x5EED1A7E00000001"
PROD_THREADS = 8
PHASES = ("locked", "uniform")
ARMS = ("production", "single_thread")
SUBS = ("render_us", "present_us", "total_us")
PCT = ("p50", "p95", "p99", "max")
PROPAGATES_PERMILLE = 500


class Refuse(Exception):
    pass


def registry() -> dict:
    with open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8") as fh:
        return json.load(fh)["entries"]


def check_raw(raw: dict) -> dict:
    """The court's raw record, structurally: every cell, every sub-interval, integer percentiles, N per cell."""
    if raw.get("name") != "verdandi-latency1r":
        raise Refuse("not a verdandi-latency1r record")
    d = raw.get("data", {})
    if d.get("production_threads") != PROD_THREADS:
        raise Refuse(f"the production arm is not T={PROD_THREADS}")
    if d.get("phase_seed") != PHASE_SEED:
        raise Refuse("the phase seed is not the preregistered one")
    n = d.get("samples_per_cell")
    if not isinstance(n, int) or n <= 0 or not isinstance(d.get("refresh_period_us"), int) or d["refresh_period_us"] <= 0:
        raise Refuse("no samples per cell or no measured refresh")
    for ph in PHASES:
        for arm in ARMS:
            cell = d.get("cells", {}).get(ph, {}).get(arm)
            if not cell or cell.get("samples") != n:
                raise Refuse(f"cell {ph}/{arm} is missing or partial")
            for sub in SUBS:
                if not all(isinstance(cell.get(sub, {}).get(k), int) for k in PCT):
                    raise Refuse(f"cell {ph}/{arm} {sub} is not integer p50/p95/p99/max")
    return d


def classify_phase(cells: dict) -> dict:
    """The preregistered per-regime rule, on p50s: dR, dG, propagation permille, and the label."""
    P, S = cells["production"], cells["single_thread"]
    dR = S["render_us"]["p50"] - P["render_us"]["p50"]
    dG = S["total_us"]["p50"] - P["total_us"]["p50"]
    dPresent = P["present_us"]["p50"] - S["present_us"]["p50"]
    if dR <= 0:
        label, pm = "VOID", None
    else:
        pm = (1000 * dG) // dR
        label = "PROPAGATES" if pm >= PROPAGATES_PERMILLE else ("PARTIALLY ABSORBED" if pm > 0 else "ABSORBED")
    return {"label": label, "render_delta_p50_us": dR, "glass_delta_p50_us": dG, "propagation_permille": pm,
            "present_growth_p50_us": dPresent,
            "total_delta_p99_us": S["total_us"]["p99"] - P["total_us"]["p99"]}


def phase_sentence(ph: str, c: dict) -> str:
    if c["label"] == "VOID":
        return (f"{ph}: VOID — the production arm was not faster than the single-thread reference in the render "
                f"sub-interval (dR {c['render_delta_p50_us']} us), so there is no render headroom here to propagate.")
    s = (f"{ph}: {c['label']} — render delta {c['render_delta_p50_us']} us, glass delta {c['glass_delta_p50_us']} us, "
         f"{c['propagation_permille']} permille of the render headroom reached composited (p50s; the p99 total delta "
         f"is {c['total_delta_p99_us']} us, reported beside it).")
    if c["label"] != "PROPAGATES" and c["present_growth_p50_us"] > 0:
        s += (f" The production arm's frame-ready -> composited grew by {c['present_growth_p50_us']} us: the saved render "
              f"time was spent waiting for the composition.")
    return s


def seal_latency1r(raw: dict, reg: dict, host: str, session: dict, build: dict,
                   confirm_of: dict | None = None) -> tuple[dict, dict]:
    """Pure: the court's raw record -> the sealed LATENCY-1R record and the per-regime classification."""
    d = check_raw(raw)
    cls = {ph: classify_phase(d["cells"][ph]) for ph in PHASES}
    data = {
        "cells": {ph: {arm: {sub: {k: d["cells"][ph][arm][sub][k] for k in PCT} for sub in SUBS}
                       | {"samples": d["cells"][ph][arm]["samples"]} for arm in ARMS} for ph in PHASES},
        "refresh_period_us": d["refresh_period_us"],
        "sequence_frames": d["sequence_frames"],
        "samples_per_cell": d["samples_per_cell"],
        "production_threads": d["production_threads"],
        "phase_seed": d["phase_seed"],
        "derived": {ph: {k: v for k, v in cls[ph].items() if k != "label"} for ph in PHASES},
    }
    prov = {
        "tool": "shell latency1r-window (shell/latency1r.rs court over the GDI surface appended to shell/win32.rs) "
                "+ verify/latency1r.py",
        "surface": raw.get("provenance", {}).get("tool", ""),
        "host": host, "session": session, "build": build,
        "raw_unix_seconds": raw.get("provenance", {}).get("unix_seconds"),
        "python": platform.python_version(), "os": platform.system(), "machine": platform.machine(),
        "preregistered": {"rung": "LATENCY-1R", "chain_hash": reg["LATENCY-1R"]["chain_hash"]},
    }
    reading = ("LATENCY-1R, render-start -> composited, production (T=8) vs the single-thread reference, on host "
               f"{host} (refresh {d['refresh_period_us']} us, {d['samples_per_cell']} samples per cell). "
               + " ".join(phase_sentence(ph, cls[ph]) for ph in PHASES)
               + " A composed-GDI present is refresh-coupled (LATENCY-0), so absorption in the locked regime is a "
                 "property of this present path, not evidence that faster rendering is useless; decoupling it is "
                 "PRESENT-1's hypothesis. Within this apparatus only: never compared to LATENCY-0/LATENCY-1 or to any "
                 "emit p99; not input-to-photon.")
    name = "verdandi-latency1r"
    if confirm_of is not None:
        name = "verdandi-latency1r-confirm"
        prov["confirms"] = confirm_of
        orig = confirm_of.get("original_labels", {})
        same = all(orig.get(ph) == cls[ph]["label"] for ph in PHASES)
        was = ", ".join("%s %s" % (ph, orig.get(ph)) for ph in PHASES)
        now = ", ".join("%s %s" % (ph, cls[ph]["label"]) for ph in PHASES)
        reading = (f"CONFIRMATION run — does NOT replace the sealed LATENCY-1R record (chain {confirm_of['chain_hash'][:8]}). "
                   f"The per-regime shape {'REPRODUCED' if same else 'did NOT reproduce'}: original {was}; this run "
                   f"{now}. ") + reading
    rec = envelope.seal(
        name, 1, "measured", prov,
        {"certifies": f"render-start -> composited of the production render (T={PROD_THREADS}) and the single-thread "
                      f"reference over the sealed reference session on host {host}, locked and uniform phase, "
                      f"{d['samples_per_cell']} samples per cell over {d['sequence_frames']} frames"
                      + (" (a confirmation run)" if confirm_of is not None else ""),
         "host": host},
        ["input-to-photon latency: input transport and panel scan-out need capture hardware",
         "a comparison with LATENCY-0's or LATENCY-1's frame-ready -> composited, or with any emit p99 (different observables)",
         "a render-speed claim: that is GAUNTLET-2's; here the render is one part of a render-inclusive present interval",
         "that the locked or uniform regime is a real game loop under load (each is a declared phase model)",
         "that absorption in the locked regime means faster rendering is useless (it is the refresh-coupled GDI present's property)",
         "a single scalar: the propagation permille is on p50s; the p99s are reported beside it, never folded in",
         "any other host, session, panel or window state; absolute us are host- and panel-specific"],
        data, reading)
    return rec, {ph: cls[ph]["label"] for ph in PHASES}


def main() -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--session", default=DEFAULT_SESSION)
    ap.add_argument("--per-cell", type=int, default=200)
    ap.add_argument("--confirm", action="store_true",
                    help="a reproducibility run: seal a SEPARATE latency1r-confirm-<host>.json citing the sealed record")
    a = ap.parse_args()
    run = dict(capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        if os.name != "nt":
            raise Refuse("LATENCY-1R is Windows-only (the instrument is the GDI/DWM window)")
        reg = registry()
        if "LATENCY-1R" not in reg:
            raise Refuse("LATENCY-1R is not preregistered — no number before the method")
        rustc = shutil.which("rustc")
        if rustc is None:
            raise Refuse("rustc not found")
        build_dir = os.path.join(ROOT, "verify", "build")
        os.makedirs(build_dir, exist_ok=True)
        exe = os.path.join(build_dir, "shell-latency1r.exe")
        flags = ["-O", "--cfg", "shell_window"]
        cp = subprocess.run([rustc] + flags + [os.path.join(ROOT, "shell", "main.rs"), "-o", exe], **run)
        if cp.returncode != 0:
            raise Refuse("rustc failed:\n" + cp.stderr)
        build = {"rustc": subprocess.run([rustc, "--version"], **run).stdout.strip(), "flags": flags}
        srec = envelope.read(os.path.join(ROOT, a.session))
        session = {"path": a.session, "chain_hash": srec["chain_hash"], "head": srec["data"]["head"]}
        # witnesses first, on THIS build: the headless court (mock surface) renders both arms to the sealed witnesses
        cp = subprocess.run([exe, "latency1r-selftest", "--session", a.session, "--per-cell", "1"], cwd=ROOT, **run)
        if cp.returncode != 0 or "latency1r court OK" not in cp.stdout:
            raise Refuse("the headless court did not reproduce the sealed witnesses — no number is taken\n" + cp.stdout + cp.stderr)
        raw_path = os.path.join(build_dir, f"latency1r-raw-{a.host}.json")
        if os.path.exists(raw_path):
            os.remove(raw_path)
        # the window court streams its progress and any refusal straight to this console (not captured)
        sys.stdout.flush()
        rc = subprocess.run([exe, "latency1r-window", "--session", a.session, "--per-cell", str(a.per_cell),
                             "--host", a.host, "--out", raw_path], cwd=ROOT).returncode
        if rc != 0 or not os.path.exists(raw_path):
            raise Refuse("the window court refused or wrote nothing (its reason is printed above)")
        with open(raw_path, encoding="utf-8") as fh:
            raw = json.load(fh)
        os.remove(raw_path)
        confirm_of = None
        name = f"latency1r-{a.host}.json"
        if a.confirm:
            canon = os.path.join(ROOT, "shell", "attest", name)
            if not os.path.exists(canon):
                raise Refuse(f"nothing to confirm — no sealed shell/attest/{name}; run without --confirm first")
            orig = envelope.read(canon)
            labels = {ph: classify_phase(orig["data"]["cells"][ph])["label"] for ph in PHASES}
            confirm_of = {"of": f"shell/attest/{name}", "chain_hash": orig["chain_hash"], "original_labels": labels}
            name = f"latency1r-confirm-{a.host}.json"
        rec, labels = seal_latency1r(raw, reg, a.host, session, build, confirm_of)
    except Refuse as e:
        print(f"REFUSE: {e}")
        return 2
    out_dir = os.path.join(ROOT, "shell", "attest")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name)
    envelope.write(out, rec)
    print("[latency1r] " + "; ".join(f"{ph} {labels[ph]}" for ph in PHASES))
    print(f"[latency1r] -> {os.path.relpath(out, ROOT)}  (cites LATENCY-1R {reg['LATENCY-1R']['chain_hash'][:8]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
