# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""latency1.py — LATENCY-1 (court A): the locked present-path court, read through its amendment (off-gate, host).

    python verify/latency1.py --host NAME [--session workshop/attest/sessionwalk-demo.json] [--measure 200] [--confirm]

LATENCY-1 runs EXACTLY as locked (entry 8e93118e): the same sealed reference session, the same instrument
(`shell playback-window --measure N`, whose source is LATENCY-0's byte for byte — gate row latency1r-fence), the same
frame-ready -> composited observable, and LATENCY-0's sealed p99 inherited as the comparator, never re-derived.

Its reading is bound by the amendment LATENCY-1a, registered before this number: in that instrument the render runs
BEFORE the window opens (`playback::frames`), so the interval is blit -> composited over pre-rendered frames and cannot
see the T=8 renderer. The delta therefore reads as a statement about the presentation interval only — NO MATERIAL
CHANGE (|delta p99| < 50 permille of the baseline: a second-run shape confirmation of LATENCY-0), or a DECREASE /
INCREASE of the presentation interval itself — never as render headroom propagating or render contention. The
render-inclusive question is LATENCY-1R's (verify/latency1r.py), a different observable never compared with this one.

The instrument writes its raw record to shell/attest/latency-<host>.json — the path of the SEALED LATENCY-0 baseline.
This script therefore reads and validates the baseline first, runs the instrument, takes the new raw bytes, and
restores the baseline byte-exact (checked by sha256) before sealing shell/attest/latency1-<host>.json. The record
stores numbers only; the reading is computed from them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "verify"))
import envelope  # noqa: E402

MATERIAL_PERMILLE = 50          # LATENCY-1a: |delta p99| below this share of the baseline p99 is no material change
DEFAULT_SESSION = "workshop/attest/sessionwalk-demo.json"
PCT = ("p50", "p95", "p99", "max")


class Refuse(Exception):
    pass


def registry() -> dict:
    with open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8") as fh:
        return json.load(fh)["entries"]


def inherit_baseline(rec: dict, reg: dict) -> dict:
    """The LATENCY-0 comparator, validated: the sealed record, citing LATENCY-0's registration, with the present
    distribution and the refresh. Returns the record unchanged; the numbers are never re-derived."""
    envelope.validate(rec)
    if rec.get("name") != "verdandi-latency":
        raise Refuse("the baseline is not a verdandi-latency record")
    pr = rec["provenance"].get("preregistered") or {}
    if pr.get("rung") != "LATENCY-0" or pr.get("chain_hash") != reg["LATENCY-0"]["chain_hash"]:
        raise Refuse("the baseline does not cite LATENCY-0's registration — it is not the sealed LATENCY-0 record")
    d = rec["data"]
    if not all(isinstance(d.get("present_us", {}).get(k), int) for k in PCT) or not isinstance(d.get("refresh_period_us"), int):
        raise Refuse("the baseline carries no integer present distribution / refresh")
    return rec


def classify(this_p99: int, base_p99: int) -> tuple[str, int, int]:
    """The locked categories, read through LATENCY-1a: (label, delta_p99_us, |delta| permille of the baseline)."""
    delta = this_p99 - base_p99
    permille = (abs(delta) * 1000) // base_p99 if base_p99 > 0 else 0
    if permille < MATERIAL_PERMILLE:
        return "NO MATERIAL CHANGE", delta, permille
    return ("IMPROVEMENT" if delta < 0 else "DEGRADATION"), delta, permille


def reading_for(label: str, delta: int, permille: int, this_p99: int, base_p99: int,
                refresh: int, base_refresh: int) -> str:
    if label == "NO MATERIAL CHANGE":
        core = (f"NO MATERIAL CHANGE: the blit -> composited interval reproduces LATENCY-0 (p99 {this_p99} us vs the "
                f"inherited {base_p99} us, |delta| {permille} permille < {MATERIAL_PERMILLE}) — a second-run shape "
                f"confirmation of LATENCY-0's refresh-coupled composed-GDI present.")
    elif label == "IMPROVEMENT":
        core = (f"IMPROVEMENT of the presentation interval: p99 {this_p99} us vs the inherited {base_p99} us (delta "
                f"{delta} us, {permille} permille) — a change in the blit -> composited interval itself (DWM, system "
                f"state, build).")
    else:
        core = (f"DEGRADATION of the presentation interval: p99 {this_p99} us vs the inherited {base_p99} us (delta "
                f"+{delta} us, {permille} permille) — a change in the blit -> composited interval itself (DWM, system "
                f"state, build).")
    refresh_note = ""
    if base_refresh > 0 and abs(refresh - base_refresh) * 1000 // base_refresh >= MATERIAL_PERMILLE:
        refresh_note = (f" The measured refresh moved ({refresh} us vs LATENCY-0's {base_refresh} us): the display is "
                        f"not the one LATENCY-0 measured, which weakens the comparison.")
    return (core + " Per the LATENCY-1a amendment this says NOTHING about the renderer: the frames were rendered "
            "before the window opened, outside this interval, so neither render headroom propagating nor render "
            "contention can appear in it — the render-inclusive question is LATENCY-1R's, a different observable "
            "never compared with this one. Not input-to-photon; never compared to an emit p99." + refresh_note)


def seal_latency1(raw: dict, base: dict, base_rel: str, reg: dict, host: str, session: dict, build: dict,
                  confirm_of: dict | None = None) -> tuple[dict, str]:
    """Pure: the raw instrument record + the inherited baseline -> the sealed LATENCY-1 record and its label."""
    if raw.get("name") != "verdandi-latency":
        raise Refuse("the instrument's raw output is not a verdandi-latency record")
    d, b = raw["data"], base["data"]
    for k in ("present_us", "refresh_period_us", "samples", "sequence_frames"):
        if k not in d:
            raise Refuse(f"the raw record is missing {k}")
    if not all(isinstance(d["present_us"].get(k), int) for k in PCT):
        raise Refuse("the raw present distribution is not integer p50/p95/p99/max")
    if d["sequence_frames"] != b.get("sequence_frames"):
        raise Refuse("the sequence differs from LATENCY-0's — not the same sealed session, not the same experiment")
    if d["samples"] != b.get("samples"):
        raise Refuse(f"{d['samples']} samples, LATENCY-0 took {b.get('samples')} — a partial or different run")
    this_p99, base_p99 = d["present_us"]["p99"], b["present_us"]["p99"]
    label, delta, permille = classify(this_p99, base_p99)
    data = {
        "present_us": {k: d["present_us"][k] for k in PCT},
        "refresh_period_us": d["refresh_period_us"],
        "samples": d["samples"],
        "sequence_frames": d["sequence_frames"],
        "baseline_present_us": {k: b["present_us"][k] for k in PCT},
        "baseline_refresh_period_us": b["refresh_period_us"],
        "delta_p50_us": d["present_us"]["p50"] - b["present_us"]["p50"],
        "delta_p99_us": delta,
        "abs_delta_p99_permille_of_baseline": permille,
        "materiality_permille": MATERIAL_PERMILLE,
    }
    prov = {
        "tool": "shell/win32.rs playback_window --measure (LATENCY-0's instrument, unchanged) + verify/latency1.py",
        "host": host, "session": session, "build": build,
        "raw_unix_seconds": raw.get("provenance", {}).get("unix_seconds"),
        "python": platform.python_version(), "os": platform.system(), "machine": platform.machine(),
        "preregistered": {"rung": "LATENCY-1", "chain_hash": reg["LATENCY-1"]["chain_hash"]},
        "amended_by": {"rung": "LATENCY-1a", "chain_hash": reg["LATENCY-1a"]["chain_hash"]},
        "inherited_baseline": {"rung": "LATENCY-0", "from": base_rel, "chain_hash": base["chain_hash"],
                               "present_us": {k: b["present_us"][k] for k in PCT},
                               "refresh_period_us": b["refresh_period_us"]},
    }
    reading = reading_for(label, delta, permille, this_p99, base_p99, d["refresh_period_us"], b["refresh_period_us"])
    name = "verdandi-latency1"
    if confirm_of is not None:
        name = "verdandi-latency1-confirm"
        prov["confirms"] = confirm_of
        same = confirm_of.get("original_label") == label
        reading = (f"CONFIRMATION run — does NOT replace the sealed LATENCY-1 record (chain {confirm_of['chain_hash'][:8]}). "
                   f"The shape {'REPRODUCED' if same else 'did NOT reproduce'}: original {confirm_of.get('original_label')} "
                   f"(p99 {confirm_of.get('original_p99_us')} us), this run {label} (p99 {this_p99} us). ") + reading
    rec = envelope.seal(
        name, 1, "measured", prov,
        {"certifies": f"the frame-ready -> composited (blit -> composited) time of LATENCY-0's instrument replaying the "
                      f"sealed reference session on host {host}, {d['samples']} samples over {d['sequence_frames']} "
                      f"frames, from a build whose production render is the T=8 threaded path — which runs BEFORE this "
                      f"interval" + (" (a confirmation run)" if confirm_of is not None else ""),
         "host": host},
        ["that the T=8 renderer's headroom propagates, is absorbed, or contends: the render ran before the window opened, "
         "outside this interval (LATENCY-1a)",
         "input-to-photon latency: input transport, the present wait beyond composition and the panel need capture hardware",
         "a comparison to any emit p99 (GAUNTLET-2's 7734 us baseline is a render-phase time, a different observable)",
         "a comparison with LATENCY-1R's render-start -> composited numbers (a different observable)",
         "the baseline as re-derived here: it is inherited from the sealed LATENCY-0 record, unchanged",
         "any other host, session, window state or interactive load; absolute us are host- and panel-specific"],
        data, reading)
    return rec, label


def run_preserving(path: str, run) -> bytes | None:
    """Run the instrument, which overwrites `path`; return the bytes it wrote and restore the original byte-exact."""
    had = os.path.exists(path)
    orig = open(path, "rb").read() if had else None
    new = None
    try:
        run()
        if os.path.exists(path):
            new = open(path, "rb").read()
    finally:
        if had:
            with open(path, "wb") as fh:
                fh.write(orig)
        elif os.path.exists(path):
            os.remove(path)
    if had and hashlib.sha256(open(path, "rb").read()).hexdigest() != hashlib.sha256(orig).hexdigest():
        raise Refuse(f"{path} was not restored byte-exact")
    return new


def main() -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--session", default=DEFAULT_SESSION)
    ap.add_argument("--measure", type=int, default=200)
    ap.add_argument("--confirm", action="store_true",
                    help="a reproducibility run: seal a SEPARATE latency1-confirm-<host>.json citing the sealed record")
    a = ap.parse_args()
    try:
        if os.name != "nt":
            raise Refuse("LATENCY-1 is Windows-only (the instrument is the GDI/DWM window)")
        reg = registry()
        base_rel = f"shell/attest/latency-{a.host}.json"
        base_path = os.path.join(ROOT, base_rel)
        if not os.path.exists(base_path):
            raise Refuse(f"the sealed LATENCY-0 record {base_rel} is missing — the comparator is INHERITED, never "
                         f"re-derived")
        base = inherit_baseline(envelope.read(base_path), reg)
        if a.measure != base["data"]["samples"]:
            raise Refuse(f"--measure {a.measure} differs from LATENCY-0's {base['data']['samples']} samples — same apparatus means same N")
        rustc = shutil.which("rustc")
        if rustc is None:
            raise Refuse("rustc not found")
        build_dir = os.path.join(ROOT, "verify", "build")
        os.makedirs(build_dir, exist_ok=True)
        exe = os.path.join(build_dir, "shell-latency1.exe")
        flags = ["-O", "--cfg", "shell_window"]      # LATENCY-0's build: rustc -O --cfg shell_window shell/main.rs
        cp = subprocess.run([rustc] + flags + [os.path.join(ROOT, "shell", "main.rs"), "-o", exe],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
        if cp.returncode != 0:
            raise Refuse("rustc failed:\n" + cp.stderr)
        build = {"rustc": subprocess.run([rustc, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip(),
                 "flags": flags}
        # witnesses first: the sealed session replays to its sealed head through the headless present path
        srec = envelope.read(os.path.join(ROOT, a.session))
        cp = subprocess.run([exe, "playback", "--session", a.session], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if cp.returncode != 0 or f"playback head {srec['data']['head']}" not in cp.stdout:
            raise Refuse("the sealed session did not replay to its sealed head — no number is taken\n" + cp.stdout + cp.stderr)
        session = {"path": a.session, "chain_hash": srec["chain_hash"], "head": srec["data"]["head"]}

        def instrument():
            c = subprocess.run([exe, "playback-window", "--session", a.session, "--measure", str(a.measure),
                                "--host", a.host], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
            print(c.stdout, end="")
            if c.returncode != 0:
                raise Refuse("the instrument failed:\n" + c.stderr)

        raw_bytes = run_preserving(base_path, instrument)
        if raw_bytes is None:
            raise Refuse("the instrument wrote no record")
        raw = json.loads(raw_bytes.decode("utf-8"))
        confirm_of = None
        name = f"latency1-{a.host}.json"
        if a.confirm:
            canon = os.path.join(ROOT, "shell", "attest", name)
            if not os.path.exists(canon):
                raise Refuse(f"nothing to confirm — no sealed shell/attest/{name}; run without --confirm first")
            orig = envelope.read(canon)
            orig_label, _, _ = classify(orig["data"]["present_us"]["p99"], orig["data"]["baseline_present_us"]["p99"])
            confirm_of = {"of": f"shell/attest/{name}", "chain_hash": orig["chain_hash"],
                          "original_p99_us": orig["data"]["present_us"]["p99"], "original_label": orig_label}
            name = f"latency1-confirm-{a.host}.json"
        rec, label = seal_latency1(raw, base, base_rel, reg, a.host, session, build, confirm_of)
    except Refuse as e:
        print(f"REFUSE: {e}")
        return 2
    out = os.path.join(ROOT, "shell", "attest", name)
    envelope.write(out, rec)
    print(f"[latency1] {label} — p99 {rec['data']['present_us']['p99']} us vs LATENCY-0 {rec['data']['baseline_present_us']['p99']} us "
          f"(delta {rec['data']['delta_p99_us']} us); read through LATENCY-1a: the render is outside this interval")
    print(f"[latency1] -> {os.path.relpath(out, ROOT)}  (cites LATENCY-1 {reg['LATENCY-1']['chain_hash'][:8]} + "
          f"LATENCY-1a {reg['LATENCY-1a']['chain_hash'][:8]}; LATENCY-0 record restored byte-exact)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
