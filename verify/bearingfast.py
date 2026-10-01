# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""bearingfast.py — BEARING-FAST-0's speed court on a named host (off-gate, sealed).

    python verify/bearingfast.py --host NAME [--samples 200] [--warm 20]

Byte-identity is the gate's (rows bearingfast-court, -threads, -checked). This court measures only time, as the
preregistration fixed it before any build: each tread — the reference `ref`, A `a` (exact stepping), B `b` (A with
the blocked floor), and C over each layout (`ca`, `cb`, PROD_THREADS row bands) — runs in its own process
(`kernel --bearing-bench`), and every process checks its tread's index frame and picture against the reference's
before it prints a number. At each of the four registered cameras the treads run twice in mirrored order (ref a b ca
cb, then cb ca b a ref), so slow drift cancels; a tread's p99 at a camera is the LARGER of its two runs, and its score
is its worst camera's p99. The decision is the registered one, applied in order:

    A is promoted if its p99 is below the reference's at every camera;
    B is retained if its score is at most 950 permille of A's;
    C (over the retained layout) is retained if its score is at most 950 permille of the best retained so far;
    the production candidate is the last retained tread; THE TARGET is a production score at most 6,667 us
    (half of 13,333 us, the panel's period at 75 Hz).

The record stores numbers; the decision is stated in the reading. Renderer time only — strips, index frame and
picture — never the blit, the present or input to photon. Writes kernel/attest/bearingfast-<host>.json, citing the
BEARING-FAST-0 registration.
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

CAMERAS = (("witness", "witness", 34, 28, 123457), ("witness", "witness", 34, 28, 45000),
           ("corridor", "corridor", 34, 26, 300001), ("pointblank", "corridor", 29, 26, 270088))
TREADS = ("ref", "a", "b", "ca", "cb")
MARGIN_PERMILLE = 950
TARGET_US = 6667
PANEL_PERIOD_US = 13333


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--samples", type=int, default=200)
    ap.add_argument("--warm", type=int, default=20)
    a = ap.parse_args()
    if (a.samples, a.warm) != (200, 20):
        print("NOTE: the registered court is 20 warm-up and 200 samples; this run is not the registered court")
    rustc = shutil.which("rustc")
    if rustc is None:
        print("REFUSE: rustc not found")
        return 2
    build = os.path.join(ROOT, "verify", "build")
    os.makedirs(build, exist_ok=True)
    exe = os.path.join(build, "kernel-bearingfast" + (".exe" if os.name == "nt" else ""))
    flags = ["-O"]
    print("[bearingfast] compiling kernel/main.rs with -O (the shell's flag) ...", flush=True)
    cp = subprocess.run([rustc] + flags + [os.path.join(ROOT, "kernel", "main.rs"), "-o", exe], capture_output=True, text=True)
    if cp.returncode != 0:
        print("REFUSE: rustc failed\n" + cp.stderr)
        return 2

    def bench(cam, tread):
        _name, level, x, z, k = cam
        c = subprocess.run([exe, "--level", os.path.join(ROOT, "oracle", "levels", level + ".lvl"),
                            "--tiles", os.path.join(ROOT, "oracle", "tiles", "identity.tiles"), "--at", f"{x},{z},{k}",
                            "--bearing-bench", str(a.samples), "--warm", str(a.warm), "--tread", tread],
                           capture_output=True, text=True)
        d = dict(ln.split(" ", 1) for ln in c.stdout.strip().splitlines() if " " in ln)
        if c.returncode != 0 or d.get("bench_witness") != "OK":
            raise SystemExit(f"REFUSE: tread {tread} at {cam[0]}:{k} did not reproduce the reference; no number is kept\n{c.stderr}")
        p = dict(kv.split("=") for kv in d["bench_total_us"].split())
        return int(p["p50"]), int(p["p99"]), d.get("host", "")

    runs = {t: {} for t in TREADS}
    host_line = ""
    total = len(CAMERAS) * len(TREADS) * 2
    done = 0
    for cam in CAMERAS:
        label = f"{cam[0]}:{cam[4]}"
        for order in (TREADS, tuple(reversed(TREADS))):
            for t in order:
                p50, p99, hl = bench(cam, t)
                runs[t].setdefault(label, []).append({"p50_us": p50, "p99_us": p99})
                host_line = host_line or hl
                done += 1
                print(f"[bearingfast] {done}/{total}  {label:<18} {t:<4} p50 {p50:>6} us  p99 {p99:>6} us", flush=True)

    cam_p99 = {t: {lab: max(r["p99_us"] for r in rs) for lab, rs in runs[t].items()} for t in TREADS}
    score = {t: max(cam_p99[t].values()) for t in TREADS}
    a_promoted = all(cam_p99["a"][lab] < cam_p99["ref"][lab] for lab in cam_p99["ref"])
    chain = []
    if a_promoted:
        chain.append("a")
        b_kept = score["b"] * 1000 <= MARGIN_PERMILLE * score["a"]
        if b_kept:
            chain.append("b")
        c_name = "cb" if b_kept else "ca"
        if score[c_name] * 1000 <= MARGIN_PERMILLE * score[chain[-1]]:
            chain.append(c_name)
    production = chain[-1] if chain else "ref"
    prod_score = score[production]
    meets = prod_score <= TARGET_US

    data = {
        "cameras": [{"label": f"{c[0]}:{c[4]}", "level": c[1], "cell": [c[2], c[3]], "heading": c[4]} for c in CAMERAS],
        "runs": runs,
        "camera_p99_us": cam_p99,
        "score_p99_us": score,
        "retained_chain": chain,
        "production_tread": production,
        "production_score_p99_us": prod_score,
        "target_p99_us": TARGET_US,
        "panel_period_us": PANEL_PERIOD_US,
        "margin_permille": MARGIN_PERMILLE,
        "samples": a.samples, "warmup": a.warm,
    }
    with open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8") as fh:
        reg = json.load(fh)["entries"]["BEARING-FAST-0"]["chain_hash"]
    prov = {
        "tool": "kernel/main.rs --bearing-bench (one tread per process, mirrored order per camera) + verify/bearingfast.py",
        "kernel": "kernel/main.rs (+ bearing.rs, bearingfast.rs, vocab.rs, mantle.rs, formats.rs, fast.rs, hud.rs)",
        "flags": flags, "rustc": subprocess.run([rustc, "--version"], capture_output=True, text=True).stdout.strip(),
        "host": a.host, "host_line": host_line, "python": platform.python_version(), "os": platform.system(),
        "machine": platform.machine(), "tiles": "identity",
        "preregistered": {"rung": "BEARING-FAST-0", "chain_hash": reg},
    }
    scores = ", ".join(f"{t}={score[t]}" for t in TREADS)
    if not a_promoted:
        decision = ("A is NOT promoted: its p99 is not below the reference's at every camera, so no tread is retained and "
                    "the reference stays the only bearing renderer.")
    else:
        decision = (f"A is promoted (below the reference at every camera); retained in order: {' -> '.join(chain)}; the "
                    f"production candidate is {production} with a worst-camera p99 of {prod_score} us. ")
        if meets:
            decision += (f"THE TARGET IS MET ({prod_score} <= {TARGET_US} us, half the panel's {PANEL_PERIOD_US} us): the "
                         f"staircase may stop here, and MOUSE-LOOK-0 may drive {production}.")
        elif production in ("ca", "cb"):
            decision += (f"THE TARGET IS NOT MET ({prod_score} > {TARGET_US} us) with C retained: tread D's trigger fires "
                         f"(persistent workers), to be registered with its own court.")
        else:
            decision += (f"THE TARGET IS NOT MET ({prod_score} > {TARGET_US} us): the next tread is required.")
    reading = (f"BEARING-FAST-0's speed court on host {a.host}, off-gate: worst-camera p99 of the whole render (strips, "
               f"index frame and picture) per tread, each tread in its own process, mirrored order per camera, the larger "
               f"of its two runs: {scores} us. {decision} Every number was kept only after its process reproduced the "
               f"reference's frame and picture. Renderer time on this host only: not the blit, the present or input to "
               f"photon.")
    rec = envelope.seal(
        "verdandi-bearingfast", 1, "measured", prov,
        {"certifies": f"the worst-camera p99 of each BEARING-FAST-0 tread and the reference on host {a.host}, at the four "
                      f"registered cameras, {a.samples} samples after {a.warm} warm-up, two mirrored runs per camera",
         "host": a.host},
        ["input-to-photon latency, a present, a blit, a window or a frame rate: none is in this number",
         "any other host, build, resolution or camera set; absolute us are host-specific",
         "correctness: byte-identity is the gate's (bearingfast-court, -threads, -checked), checked here only per process",
         "that a tread is retained by this record: retention is the registered rule applied in the reading"],
        data, reading)
    out = os.path.join(ROOT, "kernel", "attest", f"bearingfast-{a.host}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    envelope.write(out, rec)
    print(json.dumps({"score_p99_us": score, "retained_chain": chain, "production_tread": production,
                      "production_score_p99_us": prod_score, "target_p99_us": TARGET_US}, indent=1))
    print("[bearingfast] " + decision)
    print(f"[bearingfast] -> {os.path.relpath(out, ROOT)}  (cites BEARING-FAST-0 {reg[:8]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
