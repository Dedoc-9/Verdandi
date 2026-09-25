# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""gauntlet2.py — GAUNTLET-2: the parallel-execution performance court on a named host (off-gate).

    python verify/gauntlet2.py --host NAME [--samples 300] [--warm 30] [--strips 8]
                               [--threads 1,2,4,8,16] [--scene witness] [--tiles identity]

GAUNTLET-2 is not "make emit multithreaded"; it establishes that partitioning the column domain changes execution
parallelism but NOT the certified picture. Correctness (byte-identity at every thread count) is gate-enforced
(gauntlet2-threaded-equiv). This orchestrator measures only the SPEED, off-gate: for each explicit thread count T it
invokes the SAME binary with `--gauntlet2-bench --threads T` (one T per process for a clean measurement) and
INTERLEAVES the thread counts across strips (T1, T2, T4, ..., T1, ...) so slow thermal drift cancels between
neighbours; the per-T p99 is the median across strips.

Byte-identity is checked FIRST (`--gauntlet2-threads`), before any number. The single-thread baseline is INHERITED
from the sealed LOCALITY-0 record (kernel/attest/locality0-<host>.json), never re-derived here. The record stores only
numbers; the promotion call and the preregistered memory-hierarchy reading (a scaling stall is memory-bandwidth/cache
contention, not too few threads) are stated in the reading. Never compared to GAUNTLET-0's absolute; no refresh claim.
Writes kernel/attest/gauntlet2-<host>.json, citing the GAUNTLET-2 registration.
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


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) // 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--samples", type=int, default=300)
    ap.add_argument("--warm", type=int, default=30)
    ap.add_argument("--strips", type=int, default=8)
    ap.add_argument("--threads", default="1,2,4,8,16")
    ap.add_argument("--scene", default="witness")
    ap.add_argument("--tiles", default="identity")
    ap.add_argument("--confirm", action="store_true",
                    help="a reproducibility run: seal a SEPARATE gauntlet2-confirm-<host>.json citing the sealed record, "
                         "without overwriting the canonical measurement")
    a = ap.parse_args()
    sweep = [int(x) for x in a.threads.split(",") if x.strip()]
    if 1 not in sweep:
        sweep = [1] + sweep
    sweep = sorted(set(sweep))
    if not any(t > 1 for t in sweep):
        print("REFUSE: --threads must include at least one T > 1 (the parallel court needs a parallel point)")
        return 2
    rustc = shutil.which("rustc")
    if rustc is None:
        print("REFUSE: rustc not found")
        return 2
    with open(os.path.join(ROOT, "oracle", "witnesses.json"), encoding="utf-8") as fh:
        corpus = json.load(fh)
    scene = corpus["scenes"][a.scene]
    want = scene["witnesses"][a.tiles]
    x, z, f = scene["camera"]
    build = os.path.join(ROOT, "verify", "build")
    os.makedirs(build, exist_ok=True)
    exe = os.path.join(build, "kernel-gauntlet2" + (".exe" if os.name == "nt" else ""))
    cp = subprocess.run([rustc, "-C", "opt-level=3", os.path.join(ROOT, "kernel", "main.rs"), "-o", exe], capture_output=True, text=True)
    if cp.returncode != 0:
        print("REFUSE: rustc failed\n" + cp.stderr)
        return 2
    lvl = os.path.join(ROOT, "oracle", "levels", scene["level"] + ".lvl")
    til = os.path.join(ROOT, "oracle", "tiles", a.tiles + ".tiles")
    cam = f"{x},{z},{f}"
    base = [exe, "--level", lvl, "--tiles", til, "--camera", cam]

    def parse(out):
        return dict(ln.split(" ", 1) for ln in out.strip().splitlines() if " " in ln)

    # the inherited single-thread baseline — from the sealed LOCALITY-0 record, NEVER re-derived here
    loc_path = os.path.join(ROOT, "kernel", "attest", f"locality0-{a.host}.json")
    if not os.path.exists(loc_path):
        print("REFUSE: the sealed LOCALITY-0 record %s is missing — the GAUNTLET-2 baseline is INHERITED, not "
              "re-derived. Run verify/locality0.py --host %s first." % (os.path.relpath(loc_path, ROOT), a.host))
        return 2
    loc = envelope.read(loc_path)
    baseline = loc["data"].get("gauntlet2_baseline_p99_us")
    if not isinstance(baseline, int):
        print("REFUSE: the LOCALITY-0 record carries no integer gauntlet2_baseline_p99_us")
        return 2

    # byte-identity FIRST — every thread count, before any timing
    cp = subprocess.run(base + ["--gauntlet2-threads"], capture_output=True, text=True)
    T = parse(cp.stdout)
    if cp.returncode != 0 or T.get("selfcheck") != "OK":
        print("REFUSE: the kernel did not selfcheck\n" + cp.stdout + cp.stderr)
        return 2
    if T.get("frame") != want["frame"] or T.get("pixels") != want["pixels"]:
        print("REFUSE: --gauntlet2-threads rendered something other than the frozen witnesses")
        return 2
    eq = {}
    for ln in cp.stdout.strip().splitlines():
        if ln.startswith("g2t_thread "):
            parts = ln.split()
            eq[parts[1]] = dict(p.split("=") for p in parts[2:] if "=" in p)
    for t in sweep:
        if eq.get(str(t), {}).get("equal") != "OK":
            print(f"REFUSE: the threaded emit at T={t} is NOT byte-identical to the frozen picture; no number is printed")
            return 2

    # interleaved, one T per process: (strip) x (T1, T2, ...), so slow drift cancels between neighbouring T
    def invoke(t):
        c = subprocess.run(base + ["--gauntlet2-bench", str(a.samples), "--warm", str(a.warm), "--threads", str(t)],
                           capture_output=True, text=True)
        if c.returncode != 0:
            raise RuntimeError("gauntlet2-bench T=%d failed: %s" % (t, c.stderr.strip()))
        d = parse(c.stdout)
        if d.get("g2bench_equal") != "OK":
            raise RuntimeError("gauntlet2-bench T=%d did not reproduce the witness" % t)
        return int(dict(p.split("=") for p in d["g2bench_us"].split() if "=" in p)["p99"]), d.get("host", "")

    acc = {t: [] for t in sweep}
    host_line = ""
    for _ in range(a.strips):
        for t in sweep:
            p99, hl = invoke(t)
            acc[t].append(p99)
            host_line = host_line or hl

    med = {t: _median(acc[t]) for t in sweep}
    par = [t for t in sweep if t > 1]
    best_t = min(par, key=lambda t: med[t])
    best = med[best_t]
    max_t = max(par)
    promoted = best < baseline
    scaling_to_max = (best_t == max_t)
    speedup_permille = (baseline * 1000) // best if best else 0

    data = {
        "threads_p99_us": {str(t): med[t] for t in sweep},
        "baseline_p99_us": baseline,
        "best_parallel_threads": best_t,
        "best_parallel_p99_us": best,
        "speedup_permille": speedup_permille,
        "samples": a.samples, "warmup": a.warm, "strips": a.strips,
        "witnesses": {"frame": want["frame"], "pixels": want["pixels"]},
    }
    prov = {
        "tool": "kernel/main.rs --gauntlet2-bench (one thread count per process, interleaved) + verify/gauntlet2.py",
        "kernel": "kernel/main.rs (+ mantle.rs, fast.rs, formats.rs, hud.rs)", "flags": ["-C", "opt-level=3"],
        "rustc": subprocess.run([rustc, "--version"], capture_output=True, text=True).stdout.strip(),
        "host": a.host, "host_line": host_line, "python": platform.python_version(),
        "os": platform.system(), "machine": platform.machine(), "scene": a.scene, "tiles": a.tiles,
        "camera": [x, z, f], "corpus_commit": corpus["origin"]["commit"],
        "instrument": "interleaved per-thread-count strips, one T per process",
    }
    with open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8") as fh:
        reg = json.load(fh)["entries"]["GAUNTLET-2"]["chain_hash"]
    prov["preregistered"] = {"rung": "GAUNTLET-2", "chain_hash": reg}
    prov["inherited_baseline"] = {"rung": "LOCALITY-0", "from": f"kernel/attest/locality0-{a.host}.json",
                                  "chain_hash": loc["chain_hash"], "baseline_p99_us": baseline}

    matrix = ", ".join(f"T{t}={med[t]}" for t in sweep)
    if promoted and scaling_to_max:
        verdict = (f"PROMOTE: parallel execution beats the sealed single-thread baseline — best at T={best_t} with p99 "
                   f"{best} us vs baseline {baseline} us ({speedup_permille} permille of it), and p99 kept improving out "
                   f"to the largest T tested. Action for the reader: adopt the threaded emit; the parallel court is open "
                   f"for higher T if the platform has the cores.")
    elif promoted:
        verdict = (f"PROMOTE at T={best_t} (p99 {best} us vs baseline {baseline}, {speedup_permille} permille), BUT p99 "
                   f"stopped improving beyond T={best_t} (larger T no faster). Per the preregistered reading this plateau "
                   f"is MEMORY-BANDWIDTH / CACHE CONTENTION, not insufficient parallelism: adopt T={best_t}; do NOT "
                   f"expand the thread search blindly — the next axis is the memory hierarchy, not more threads.")
    else:
        verdict = (f"NO PROMOTION: no thread count beats the sealed single-thread baseline (best T={best_t} p99 {best} us "
                   f"vs baseline {baseline}). Per the preregistered reading this is MEMORY-BANDWIDTH / CACHE CONTENTION — "
                   f"parallelism did not hide the tile-fetch latency here; the next axis is the memory hierarchy, not "
                   f"more threads.")
    reading = (f"the parallel-execution court on host {a.host}, off-gate, interleaved over {a.strips} strips (per-T p99 "
               f"medians): {matrix} us; inherited single-thread baseline {baseline} us (sealed by LOCALITY-0, never "
               f"re-derived). {verdict} Byte-identity was proven FIRST at every T (gauntlet2-threaded-equiv), so the "
               f"threaded emit is the certified picture at every thread count. These are same-apparatus p99 deltas vs the "
               f"sealed single-thread baseline — NOT compared to GAUNTLET-0's instrumented render absolute, and NOT a "
               f"refresh-rate or input-to-photon claim.")
    name, out_name = "verdandi-gauntlet2", f"gauntlet2-{a.host}.json"
    if a.confirm:
        # a reproducibility run: seal a SEPARATE confirmation record citing the sealed measurement, never replacing it
        canon = os.path.join(ROOT, "kernel", "attest", f"gauntlet2-{a.host}.json")
        if not os.path.exists(canon):
            print("REFUSE: nothing to confirm — no sealed kernel/attest/gauntlet2-%s.json. Run without --confirm first." % a.host)
            return 2
        orig = envelope.read(canon)
        prov["confirms"] = {"of": f"kernel/attest/gauntlet2-{a.host}.json", "chain_hash": orig["chain_hash"],
                            "original_best_parallel_p99_us": orig["data"].get("best_parallel_p99_us"),
                            "original_speedup_permille": orig["data"].get("speedup_permille")}
        name, out_name = "verdandi-gauntlet2-confirm", f"gauntlet2-confirm-{a.host}.json"
        shape_ok = promoted and best < baseline
        reading = (f"CONFIRMATION run — does NOT replace the sealed measurement (kernel/attest/gauntlet2-{a.host}.json, "
                   f"chain_hash {orig['chain_hash'][:8]}). The shape {'REPRODUCED' if shape_ok else 'did NOT reproduce'}: "
                   f"original best {orig['data'].get('best_parallel_p99_us')} us ({orig['data'].get('speedup_permille')} "
                   f"permille of baseline), this run best {best} us ({speedup_permille} permille); per-T this run: {matrix} "
                   f"us. ") + reading
    rec = envelope.seal(
        name, 1, "measured", prov,
        {"certifies": f"the same-apparatus p99 of the threaded emit at thread counts {sweep} vs the inherited single-thread baseline on host {a.host} for scene {a.scene} with {a.tiles} tiles, {a.samples} samples x {a.strips} interleaved strips" + (" (a confirmation run, citing the sealed measurement)" if a.confirm else ""),
         "host": a.host, "scene": a.scene, "tiles": a.tiles},
        ["input-to-photon latency, a present, a window, a compositor, a refresh-rate claim: none is in this number",
         "the whole-render cost: this is emit only, over the frozen strips + frame every thread count shares",
         "any comparison to GAUNTLET-0's instrumented render absolute (a different apparatus)",
         "the single-thread baseline as re-derived here: it is INHERITED from the sealed LOCALITY-0 record, unchanged",
         "the per-T p99 as a pure core-count law: cache/bandwidth/scheduling make scaling sublinear, and a plateau is a memory-hierarchy finding, not a call for more threads",
         "any other host, scene, tile set, resolution or core count; absolute us are host-specific",
         "that the threaded emit is promoted by this record: promotion is the reader's, from the decision rule and the p99 matrix"],
        data, reading)
    out_dir = os.path.join(ROOT, "kernel", "attest")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, out_name)
    envelope.write(out, rec)
    print(json.dumps({"host": a.host, "baseline_p99_us": baseline, "threads_p99_us": data["threads_p99_us"],
                      "best_parallel_threads": best_t, "best_parallel_p99_us": best,
                      "speedup_permille": speedup_permille, "promoted": promoted, "confirm": a.confirm}, indent=1))
    print("[gauntlet2] " + verdict)
    print(f"[gauntlet2] -> {os.path.relpath(out, ROOT)}  (cites GAUNTLET-2 {reg[:8]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
