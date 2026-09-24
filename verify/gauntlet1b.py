# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""gauntlet1b.py — GAUNTLET-1b: the same-apparatus emit speed delta on a named host, as a record under the envelope (off-gate).

    python verify/gauntlet1b.py --host NAME [--samples 300] [--warm 30] [--scene witness] [--tiles identity]

Compiles kernel/main.rs in release, then in ONE invocation (`--fast --fast-bench`) it (1) checks the two witnesses
against the frozen corpus and confirms the candidate emit is byte-identical to the frozen emit (`fast_equal OK`,
`fast_pixels == pixels`) — a wrong or differing picture is refused before any number is printed — and (2) times the
frozen `mantle` emit and the GAUNTLET-1b `fast` emit back to back over the SAME frozen strips + frame. Records both
emits' p50/p95/p99/max microseconds and the floor divide reduction (4 -> 2 per textured floor px) AS DATA; the
comparison lives in the reading. No verdict-shaped key exists in the record; `records-firewall` would refuse one.

This is an EMIT-LEVEL, same-apparatus, frozen-vs-candidate delta — NOT the whole render, and NEVER compared to
GAUNTLET-0's instrumented render absolute (a different apparatus): the locked GAUNTLET-1 promotion rule. Correctness
(byte-identity) is the gate's court (gauntlet1-equiv, gauntlet1b-reduction); this seat measures only the speed given
it. Writes kernel/attest/gauntlet1b-<host>.json, citing the GAUNTLET-1 preregistration.
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--samples", type=int, default=300)
    ap.add_argument("--warm", type=int, default=30)
    ap.add_argument("--scene", default="witness")
    ap.add_argument("--tiles", default="identity")
    a = ap.parse_args()
    rustc = shutil.which("rustc")
    if rustc is None:
        print("REFUSE: rustc not found")
        return 2
    with open(os.path.join(ROOT, "oracle", "witnesses.json"), encoding="utf-8") as fh:
        corpus = json.load(fh)
    scene = corpus["scenes"][a.scene]
    want = scene["witnesses"][a.tiles]
    build = os.path.join(ROOT, "verify", "build")
    os.makedirs(build, exist_ok=True)
    exe = os.path.join(build, "kernel-gauntlet1b" + (".exe" if os.name == "nt" else ""))
    cp = subprocess.run([rustc, "-C", "opt-level=3", os.path.join(ROOT, "kernel", "main.rs"), "-o", exe], capture_output=True, text=True)
    if cp.returncode != 0:
        print("REFUSE: rustc failed\n" + cp.stderr)
        return 2
    x, z, f = scene["camera"]
    args = [exe, "--level", os.path.join(ROOT, "oracle", "levels", scene["level"] + ".lvl"),
            "--tiles", os.path.join(ROOT, "oracle", "tiles", a.tiles + ".tiles"), "--camera", f"{x},{z},{f}",
            "--fast", "--fast-bench", str(a.samples), "--warm", str(a.warm)]
    cp = subprocess.run(args, capture_output=True, text=True)
    lines = dict(ln.split(" ", 1) for ln in cp.stdout.strip().splitlines() if " " in ln)
    # witnesses first: a wrong or differing picture prints no number
    if cp.returncode != 0 or lines.get("selfcheck") != "OK":
        print("REFUSE: the kernel did not selfcheck\n" + cp.stdout + cp.stderr)
        return 2
    if lines.get("frame") != want["frame"] or lines.get("pixels") != want["pixels"]:
        print("REFUSE: the bench rendered something other than the frozen witnesses; no number is printed")
        return 2
    if lines.get("fast_equal") != "OK" or lines.get("fast_pixels") != lines.get("pixels"):
        print("REFUSE: the candidate emit is NOT byte-identical to the frozen emit; no speed number is printed")
        return 2
    if not lines.get("fastbench_samples", "").endswith("same_witnesses OK"):
        print("REFUSE: an emit did not reproduce the frozen witness during the bench")
        return 2

    def pct(key):
        kv = dict(p.split("=") for p in lines[key].split())
        return {k: int(v) for k, v in kv.items()}

    frozen_us, fast_us = pct("fastbench_frozen_us"), pct("fastbench_fast_us")
    reg = dict(kv.split("=") for kv in lines["fast_region"].split())
    opt = dict(kv.split("=") for kv in lines["fast_optwork"].split() if "=" in kv)
    wall_tex, floor_tex = int(reg["wall_tex"]), int(reg["floor_tex"])
    floor_saved = int(opt["floor_saved"])
    data = {
        "emit_us": {"frozen": frozen_us, "fast": fast_us},
        "floor_divides_per_px": {"frozen": 4, "candidate": 2},
        "divide_work_on_witness": {"wall": wall_tex, "floor_frozen": 4 * floor_tex,
                                   "floor_candidate": 2 * floor_tex, "floor_saved": floor_saved},
        "samples": a.samples,
        "warmup": a.warm,
        "witnesses": {"frame": lines["frame"], "pixels": lines["pixels"]},
    }
    prov = {
        "tool": "kernel/main.rs --fast --fast-bench + verify/gauntlet1b.py", "kernel": "kernel/main.rs (+ mantle.rs, fast.rs, formats.rs, hud.rs)",
        "flags": ["-C", "opt-level=3"], "rustc": subprocess.run([rustc, "--version"], capture_output=True, text=True).stdout.strip(),
        "host": a.host, "host_line": lines.get("host", ""), "python": platform.python_version(), "os": platform.system(), "machine": platform.machine(),
        "scene": a.scene, "tiles": a.tiles, "camera": [x, z, f], "corpus_commit": corpus["origin"]["commit"],
    }
    with open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8") as fh:
        reg1 = json.load(fh)
    g1 = reg1["entries"]["GAUNTLET-1"]["chain_hash"]
    prov["preregistered"] = {"rung": "GAUNTLET-1", "chain_hash": g1}
    fz99, ft99 = frozen_us["p99"], fast_us["p99"]
    speedup_permille = (fz99 * 1000) // ft99 if ft99 > 0 else 0
    reading = (f"emit-only, same-apparatus delta on host {a.host}: the frozen emit p99 {fz99} µs vs the GAUNTLET-1b "
               f"candidate {ft99} µs ({speedup_permille} permille of frozen at p99). The candidate reproduced the "
               f"frozen pixel witness (byte-identical — gate-enforced by gauntlet1-equiv / gauntlet1b-reduction, not "
               f"by this record), and its floor loop does 2 divides/px where the frozen did 4 ({floor_saved} floor "
               f"divides removed on the witness frame). The promotion bar is the reader's: promote iff byte-identical "
               f"AND the candidate emit p99 is strictly below the frozen emit's (speedup > 1000 permille); identical-"
               f"but-not-faster is a correctness pass and a performance fail. This is an EMIT-level number, NOT the "
               f"whole render, and NEVER compared to GAUNTLET-0's instrumented render absolute (a different "
               f"apparatus). Witnesses were checked before any number was taken")
    rec = envelope.seal(
        "verdandi-gauntlet1b-emit", 1, "measured", prov,
        {"certifies": f"the same-apparatus emit-level speed delta (frozen mantle emit vs the GAUNTLET-1b candidate) on host {a.host} for scene {a.scene} with {a.tiles} tiles, {a.samples} samples after {a.warm} warm-ups",
         "host": a.host, "scene": a.scene, "tiles": a.tiles},
        ["input-to-photon latency (input transport, present wait and the panel need capture hardware)",
         "a present, a window, a compositor: none is in this number",
         "the whole-render or per-frame cost: this is emit ONLY, timed over the frozen strips + frame both emits share",
         "any comparison to GAUNTLET-0's instrumented render absolute: different apparatus; this is a same-apparatus frozen-vs-candidate delta",
         "any other host, scene, tile set or resolution; absolute µs are host-specific",
         "that byte-identity is earned by this record: correctness is the gate's court (gauntlet1-equiv, gauntlet1b-reduction); this seat measures only the speed given it"],
        data, reading)
    out_dir = os.path.join(ROOT, "kernel", "attest")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"gauntlet1b-{a.host}.json")
    envelope.write(out, rec)
    print(json.dumps({"host": a.host, "emit_us": {"frozen": frozen_us, "fast": fast_us},
                      "p99_speedup_permille": speedup_permille, "floor_divides_saved": floor_saved}, indent=1))
    print(f"[gauntlet1b] -> {os.path.relpath(out, ROOT)}  (cites GAUNTLET-1 {g1[:8]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
