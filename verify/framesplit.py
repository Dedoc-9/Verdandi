# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""framesplit.py — FRAME-SPLIT-0: where the shell's render-start -> frame-ready interval goes (off-gate, host).

    python verify/framesplit.py --host NAME [--session workshop/attest/sessionwalk-demo.json] [--per-cell 300] [--confirm]

LATENCY-1R measured the production render-start -> frame-ready interval at 14.8-15.7 ms p50, longer than a refresh,
without a split. This court splits it on the same window, sealed session and locked phase origin, adding no
variable. Per arm (production T=8, single-thread reference) it interleaves ABBA an uninstrumented ENVELOPE (the path
LATENCY-1R timed) with an instrumented SPLIT (the same statements, a clock read at every phase boundary): strips,
frame, floor_swizzle, emit, hud, bgr, blit — frame-ready is the hard boundary. Witnesses come first, twice: the
headless court on THIS build, then the window court refuses to take a number unless every arm reproduces every
sealed frame witness, the marked path reproduces the envelope path byte for byte, and the arms agree.

The preregistered reading, on the PRODUCTION arm (the single-thread split is context):
  * the instrumentation tax = split total - envelope, at p50 and p99; if |tax p50| >= 100 permille of the envelope
    p50 the split is VOID — the probes perturbed the interval too much to attribute it;
  * otherwise each phase's share = 1000 * p99(phase) / p99(envelope) (GAUNTLET-0's formula, the envelope as the
    denominator); exactly one phase >= 500 permille -> SEAT: that phase is the next target; none -> NO SEAT
    (multi-component: no single phase is promoted); several (p99s do not add, so it can happen) -> NO SEAT (several
    named, none promoted).
  * reconciliation is reported, never distributed: the split's phases sum to its total per sample by construction;
    the sum of the phase p50s against the split total p50 (medians do not add) and the tax are both recorded.
Writes shell/attest/framesplit-<host>.json citing FRAME-SPLIT-0. Not input-to-photon; never compared to an emit p99.
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
PHASES = ("strips", "frame", "floor_swizzle", "emit", "hud", "bgr", "blit")
ARMS = ("production", "single_thread")
PCT = ("p50", "p95", "p99", "max")
PROD_THREADS = 8
WARM_ROUNDS = 10
SEAT_PERMILLE = 500
VOID_TAX_PERMILLE = 100


class Refuse(Exception):
    pass


def registry() -> dict:
    with open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8") as fh:
        return json.load(fh)["entries"]


def _pct(x) -> bool:
    return isinstance(x, dict) and all(isinstance(x.get(k), int) for k in PCT)


def check_raw(raw: dict) -> dict:
    if raw.get("name") != "verdandi-framesplit":
        raise Refuse("not a verdandi-framesplit record")
    d = raw.get("data", {})
    if tuple(d.get("phases", ())) != PHASES:
        raise Refuse("the phases are not the registered ones, in order")
    if d.get("production_threads") != PROD_THREADS or d.get("warm_rounds") != WARM_ROUNDS or d.get("phase_origin") != "locked":
        raise Refuse("production T, warm-up or phase origin is not the registered one")
    n = d.get("samples_per_cell")
    if not isinstance(n, int) or n <= 0:
        raise Refuse("no samples per cell")
    for arm in ARMS:
        a = d.get("arms", {}).get(arm, {})
        env, spl = a.get("envelope", {}), a.get("split", {})
        if env.get("samples") != n or spl.get("samples") != n:
            raise Refuse(f"{arm}: a cell is missing or partial")
        if not (_pct(env.get("render_us")) and _pct(env.get("present_us")) and _pct(spl.get("render_us")) and _pct(spl.get("present_us"))):
            raise Refuse(f"{arm}: envelope/split intervals are not integer p50/p95/p99/max")
        if tuple(spl.get("phases_us", {}).keys()) != PHASES or not all(_pct(v) for v in spl["phases_us"].values()):
            raise Refuse(f"{arm}: the split's phases are missing or not integer percentiles")
    return d


def derive(arm: dict) -> dict:
    env, spl = arm["envelope"]["render_us"], arm["split"]["render_us"]
    ph = arm["split"]["phases_us"]
    tax50, tax99 = spl["p50"] - env["p50"], spl["p99"] - env["p99"]
    return {
        "tax_p50_us": tax50,
        "tax_p99_us": tax99,
        "abs_tax_p50_permille_of_envelope": (abs(tax50) * 1000) // env["p50"] if env["p50"] > 0 else 0,
        "shares_p99_permille_of_envelope": {p: (ph[p]["p99"] * 1000) // env["p99"] if env["p99"] > 0 else 0 for p in PHASES},
        "shares_p50_permille_of_envelope": {p: (ph[p]["p50"] * 1000) // env["p50"] if env["p50"] > 0 else 0 for p in PHASES},
        "sum_of_phase_p50s_us": sum(ph[p]["p50"] for p in PHASES),
        "split_total_p50_us": spl["p50"],
        "median_additivity_gap_us": spl["p50"] - sum(ph[p]["p50"] for p in PHASES),
    }


def seat(dv: dict) -> tuple[str, list]:
    """The preregistered rule on one arm's derived numbers -> (label, named phases)."""
    if dv["abs_tax_p50_permille_of_envelope"] >= VOID_TAX_PERMILLE:
        return "VOID", []
    named = [p for p in PHASES if dv["shares_p99_permille_of_envelope"][p] >= SEAT_PERMILLE]
    if len(named) == 1:
        return "SEAT", named
    if not named:
        return "NO SEAT (multi-component)", []
    return "NO SEAT (several at the threshold)", named


def sentence(arm: str, dv: dict, label: str, named: list) -> str:
    shares = ", ".join(f"{p} {dv['shares_p99_permille_of_envelope'][p]}" for p in PHASES)
    head = {"SEAT": f"SEAT — {named[0] if named else ''} is the next target",
            "VOID": "VOID — the instrumentation tax is too large to attribute the interval",
            "NO SEAT (multi-component)": "NO SEAT — multi-component: no phase reaches 500 permille, none is promoted",
            "NO SEAT (several at the threshold)": f"NO SEAT — several phases at or above 500 permille ({', '.join(named)}), none promoted"}[label]
    return (f"{arm}: {head}. p99 shares of the envelope (permille): {shares}. Tax {dv['tax_p50_us']} us at p50 "
            f"({dv['abs_tax_p50_permille_of_envelope']} permille of the envelope) and {dv['tax_p99_us']} us at p99; the phase "
            f"p50s sum to {dv['sum_of_phase_p50s_us']} us against a split total of {dv['split_total_p50_us']} us (medians do "
            f"not add; the {dv['median_additivity_gap_us']} us gap is reported, not distributed).")


def seal_framesplit(raw: dict, reg: dict, host: str, session: dict, build: dict,
                    confirm_of: dict | None = None) -> tuple[dict, str]:
    d = check_raw(raw)
    derived = {arm: derive(d["arms"][arm]) for arm in ARMS}
    label, named = seat(derived["production"])
    s_label, s_named = seat(derived["single_thread"])
    data = {
        "arms": d["arms"], "phases": list(PHASES), "refresh_period_us": d["refresh_period_us"],
        "sequence_frames": d["sequence_frames"], "samples_per_cell": d["samples_per_cell"],
        "warm_rounds": d["warm_rounds"], "production_threads": d["production_threads"], "phase_origin": d["phase_origin"],
        "derived": derived,
        "seat_rule_permille": SEAT_PERMILLE, "void_tax_permille": VOID_TAX_PERMILLE,
    }
    prov = {
        "tool": "shell framesplit-window (shell/framesplit.rs court over the GDI surface appended to shell/win32.rs) "
                "+ verify/framesplit.py",
        "surface": raw.get("provenance", {}).get("tool", ""),
        "host": host, "session": session, "build": build,
        "raw_unix_seconds": raw.get("provenance", {}).get("unix_seconds"),
        "python": platform.python_version(), "os": platform.system(), "machine": platform.machine(),
        "preregistered": {"rung": "FRAME-SPLIT-0", "chain_hash": reg["FRAME-SPLIT-0"]["chain_hash"]},
    }
    reading = (f"FRAME-SPLIT-0 on host {host} (locked phase origin, {d['samples_per_cell']} samples per cell, refresh "
               f"{d['refresh_period_us']} us, context only). Production envelope render-start -> frame-ready p50 "
               f"{d['arms']['production']['envelope']['render_us']['p50']} us / p99 "
               f"{d['arms']['production']['envelope']['render_us']['p99']} us. "
               + sentence("production", derived["production"], label, named) + " Context, no seat: "
               + sentence("single_thread", derived["single_thread"], s_label, s_named)
               + " Not input-to-photon; never compared to an emit p99; within this apparatus only.")
    full = label + (": " + named[0] if label == "SEAT" and named else "")
    name = "verdandi-framesplit"
    if confirm_of is not None:
        name = "verdandi-framesplit-confirm"
        prov["confirms"] = confirm_of
        same = confirm_of.get("original_label") == full
        reading = (f"CONFIRMATION run — does NOT replace the sealed FRAME-SPLIT-0 record (chain {confirm_of['chain_hash'][:8]}). "
                   f"The production reading {'REPRODUCED' if same else 'did NOT reproduce'}: original "
                   f"{confirm_of.get('original_label')}, this run {full}. ") + reading
    rec = envelope.seal(
        name, 1, "measured", prov,
        {"certifies": f"the render-start -> frame-ready interval of the shell's frame on host {host} split into "
                      f"{len(PHASES)} phases for the production (T={PROD_THREADS}) and single-thread arms, with the "
                      f"uninstrumented envelope beside it, locked phase origin, {d['samples_per_cell']} samples per cell "
                      f"over {d['sequence_frames']} frames" + (" (a confirmation run)" if confirm_of is not None else ""),
         "host": host},
        ["input-to-photon latency: input transport and panel scan-out need capture hardware",
         "a comparison with any emit p99 (a different apparatus and observable)",
         "that a phase's share is its cost outside this frame (the shares are p99s of one interval, and p99s do not add)",
         "that the instrumentation tax is zero: it is measured and reported, and a VOID reading refuses attribution",
         "a split of the time AFTER frame-ready (the composition wait) — that is frame-ready -> composited, kept as an anchor",
         "that the seat names an optimization that will work: it names where the time is, not what will remove it",
         "any other host, session, panel, window size or phase origin; absolute us are host-specific"],
        data, reading)
    return rec, full


def main() -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--session", default=DEFAULT_SESSION)
    ap.add_argument("--per-cell", type=int, default=300)
    ap.add_argument("--confirm", action="store_true",
                    help="a reproducibility run: seal a SEPARATE framesplit-confirm-<host>.json citing the sealed record")
    a = ap.parse_args()
    run = dict(capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        if os.name != "nt":
            raise Refuse("FRAME-SPLIT-0 is Windows-only (the instrument is the GDI/DWM window)")
        reg = registry()
        if "FRAME-SPLIT-0" not in reg:
            raise Refuse("FRAME-SPLIT-0 is not preregistered — no number before the method")
        rustc = shutil.which("rustc")
        if rustc is None:
            raise Refuse("rustc not found")
        build_dir = os.path.join(ROOT, "verify", "build")
        os.makedirs(build_dir, exist_ok=True)
        exe = os.path.join(build_dir, "shell-framesplit.exe")
        flags = ["-O", "--cfg", "shell_window"]
        cp = subprocess.run([rustc] + flags + [os.path.join(ROOT, "shell", "main.rs"), "-o", exe], **run)
        if cp.returncode != 0:
            raise Refuse("rustc failed:\n" + cp.stderr)
        build = {"rustc": subprocess.run([rustc, "--version"], **run).stdout.strip(), "flags": flags}
        srec = envelope.read(os.path.join(ROOT, a.session))
        session = {"path": a.session, "chain_hash": srec["chain_hash"], "head": srec["data"]["head"]}
        cp = subprocess.run([exe, "framesplit-selftest", "--session", a.session, "--per-cell", "1"], cwd=ROOT, **run)
        if cp.returncode != 0 or "framesplit court OK" not in cp.stdout:
            raise Refuse("the headless court did not reproduce the sealed witnesses — no number is taken\n" + cp.stdout + cp.stderr)
        raw_path = os.path.join(build_dir, f"framesplit-raw-{a.host}.json")
        if os.path.exists(raw_path):
            os.remove(raw_path)
        sys.stdout.flush()
        rc = subprocess.run([exe, "framesplit-window", "--session", a.session, "--per-cell", str(a.per_cell),
                             "--host", a.host, "--out", raw_path], cwd=ROOT).returncode
        if rc != 0 or not os.path.exists(raw_path):
            raise Refuse("the window court refused or wrote nothing (its reason is printed above)")
        with open(raw_path, encoding="utf-8") as fh:
            raw = json.load(fh)
        os.remove(raw_path)
        confirm_of = None
        name = f"framesplit-{a.host}.json"
        if a.confirm:
            canon = os.path.join(ROOT, "shell", "attest", name)
            if not os.path.exists(canon):
                raise Refuse(f"nothing to confirm — no sealed shell/attest/{name}; run without --confirm first")
            orig = envelope.read(canon)
            lab, nm = seat(orig["data"]["derived"]["production"])
            confirm_of = {"of": f"shell/attest/{name}", "chain_hash": orig["chain_hash"],
                          "original_label": lab + (": " + nm[0] if lab == "SEAT" and nm else "")}
            name = f"framesplit-confirm-{a.host}.json"
        rec, label = seal_framesplit(raw, reg, a.host, session, build, confirm_of)
    except Refuse as e:
        print(f"REFUSE: {e}")
        return 2
    out_dir = os.path.join(ROOT, "shell", "attest")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name)
    envelope.write(out, rec)
    dv = rec["data"]["derived"]["production"]
    print("[framesplit] production: " + label + " — p99 shares (permille of the envelope): "
          + ", ".join(f"{p} {dv['shares_p99_permille_of_envelope'][p]}" for p in PHASES)
          + f"; tax {dv['tax_p50_us']} us at p50")
    print(f"[framesplit] -> {os.path.relpath(out, ROOT)}  (cites FRAME-SPLIT-0 {reg['FRAME-SPLIT-0']['chain_hash'][:8]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
