# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""gauntlet1c.py — GAUNTLET-1c: the row-major floor DDA's same-apparatus speed delta on a named host (off-gate).

    python verify/gauntlet1c.py --host NAME [--samples 300] [--warm 30] [--scene witness] [--tiles identity]

Compiles kernel/main.rs in release, then in ONE invocation (`--fast --fast-bench`) it (1) checks the two witnesses
against the frozen corpus and confirms BOTH the DDA (`fast::emit`) and the retained GAUNTLET-1b collapse
(`fast::emit_collapse`) are byte-identical to the frozen emit (`fast_equal OK`, `collapse_equal OK`, both pixel
shas == the corpus) — a wrong or differing picture is refused before any number — and (2) times the frozen emit,
the collapse baseline, and the DDA back to back over the SAME frozen strips + frame. Records all three emits'
p50/p95/p99/max microseconds and the floor divide structure (collapse 2/px vs DDA 5/row) AS DATA; the comparison
lives in the reading. No verdict-shaped key exists in the record; `records-firewall` would refuse one.

GAUNTLET-1c is judged against the COLLAPSE (GAUNTLET-1b's promoted baseline), not against frozen: this is an
EMIT-LEVEL, same-apparatus, candidate-vs-baseline delta — NOT the whole render, and NEVER compared to GAUNTLET-0's
instrumented render absolute (a different apparatus): the locked GAUNTLET-1 promotion rule. Correctness (byte-
identity) is the gate's court (gauntlet1-equiv, gauntlet1c-dda); this seat measures only the speed given it. Writes
kernel/attest/gauntlet1c-<host>.json, citing the GAUNTLET-1 preregistration.
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
    exe = os.path.join(build, "kernel-gauntlet1c" + (".exe" if os.name == "nt" else ""))
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
    # witnesses + byte-identity first: a wrong or differing picture prints no number
    if cp.returncode != 0 or lines.get("selfcheck") != "OK":
        print("REFUSE: the kernel did not selfcheck\n" + cp.stdout + cp.stderr)
        return 2
    if lines.get("frame") != want["frame"] or lines.get("pixels") != want["pixels"]:
        print("REFUSE: the bench rendered something other than the frozen witnesses; no number is printed")
        return 2
    if lines.get("fast_equal") != "OK" or lines.get("fast_pixels") != lines.get("pixels"):
        print("REFUSE: the DDA emit is NOT byte-identical to the frozen emit; no speed number is printed")
        return 2
    if lines.get("collapse_equal") != "OK" or lines.get("collapse_pixels") != lines.get("pixels"):
        print("REFUSE: the retained collapse baseline is NOT byte-identical to the frozen emit; no number is printed")
        return 2
    if not lines.get("fastbench_samples", "").endswith("same_witnesses OK"):
        print("REFUSE: an emit did not reproduce the frozen witness during the bench")
        return 2

    def pct(key):
        kv = dict(p.split("=") for p in lines[key].split())
        return {k: int(v) for k, v in kv.items()}

    frozen_us, collapse_us, dda_us = pct("fastbench_frozen_us"), pct("fastbench_collapse_us"), pct("fastbench_fast_us")
    w = dict(kv.split("=") for kv in lines["fast_ddawork"].split() if "=" in kv)
    floor_px, floor_rows = int(w["floor_px"]), int(w["floor_rows"])
    dda_div, collapse_div = int(w["dda_div"]), int(w["collapse_div"])
    data = {
        "emit_us": {"frozen": frozen_us, "collapse": collapse_us, "dda": dda_us},
        "floor_divide_work": {"collapse_per_px": 2, "dda_per_row": 5, "floor_px": floor_px,
                              "floor_rows": floor_rows, "collapse_div": collapse_div, "dda_div": dda_div},
        "samples": a.samples,
        "warmup": a.warm,
        "witnesses": {"frame": lines["frame"], "pixels": lines["pixels"]},
    }
    prov = {
        "tool": "kernel/main.rs --fast --fast-bench + verify/gauntlet1c.py", "kernel": "kernel/main.rs (+ mantle.rs, fast.rs, formats.rs, hud.rs)",
        "flags": ["-C", "opt-level=3"], "rustc": subprocess.run([rustc, "--version"], capture_output=True, text=True).stdout.strip(),
        "host": a.host, "host_line": lines.get("host", ""), "python": platform.python_version(), "os": platform.system(), "machine": platform.machine(),
        "scene": a.scene, "tiles": a.tiles, "camera": [x, z, f], "corpus_commit": corpus["origin"]["commit"],
    }
    with open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8") as fh:
        reg1 = json.load(fh)
    g1 = reg1["entries"]["GAUNTLET-1"]["chain_hash"]
    prov["preregistered"] = {"rung": "GAUNTLET-1", "chain_hash": g1}
    fz99, co99, dd99 = frozen_us["p99"], collapse_us["p99"], dda_us["p99"]
    vs_collapse = (co99 * 1000) // dd99 if dd99 > 0 else 0     # the promotion measurement: DDA vs the 1b baseline
    vs_frozen = (fz99 * 1000) // dd99 if dd99 > 0 else 0       # cumulative frozen -> DDA, for context only
    reading = (f"emit-only, same-apparatus delta on host {a.host}. The promotion measurement is DDA vs the GAUNTLET-1b "
               f"COLLAPSE baseline (not frozen): collapse emit p99 {co99} µs vs the DDA {dd99} µs ({vs_collapse} permille "
               f"of the collapse at p99); the cumulative frozen->DDA is {fz99} -> {dd99} µs ({vs_frozen} permille), for "
               f"context only. All three emits reproduced the frozen pixel witness (byte-identical — gate-enforced by "
               f"gauntlet1-equiv / gauntlet1c-dda, not by this record), and the DDA does the floor's perspective divide "
               f"per ROW ({dda_div} div/rem ops over {floor_rows} rows) where the collapse did per PIXEL ({collapse_div} "
               f"over {floor_px} px). The promotion bar is the reader's: promote iff byte-identical AND the DDA emit p99 "
               f"is strictly below the collapse's (vs_collapse > 1000 permille); identical-but-not-faster than the "
               f"baseline is a correctness pass and a performance fail. This is an EMIT-level number, NOT the whole "
               f"render, and NEVER compared to GAUNTLET-0's instrumented render absolute (a different apparatus). "
               f"Witnesses were checked before any number was taken")
    rec = envelope.seal(
        "verdandi-gauntlet1c-emit", 1, "measured", prov,
        {"certifies": f"the same-apparatus emit-level speed delta (the GAUNTLET-1c DDA vs the GAUNTLET-1b collapse baseline, with frozen mantle for context) on host {a.host} for scene {a.scene} with {a.tiles} tiles, {a.samples} samples after {a.warm} warm-ups",
         "host": a.host, "scene": a.scene, "tiles": a.tiles},
        ["input-to-photon latency (input transport, present wait and the panel need capture hardware)",
         "a present, a window, a compositor: none is in this number",
         "the whole-render or per-frame cost: this is emit ONLY, timed over the frozen strips + frame all three share",
         "any comparison to GAUNTLET-0's instrumented render absolute: different apparatus; this is a same-apparatus candidate-vs-baseline delta",
         "any other host, scene, tile set or resolution; absolute µs are host-specific",
         "that byte-identity is earned by this record: correctness is the gate's court (gauntlet1-equiv, gauntlet1c-dda); this seat measures only the speed given it",
         "that the frozen->DDA cumulative number is the promotion test: GAUNTLET-1c is promoted against the collapse baseline, not frozen"],
        data, reading)
    out_dir = os.path.join(ROOT, "kernel", "attest")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"gauntlet1c-{a.host}.json")
    envelope.write(out, rec)
    print(json.dumps({"host": a.host, "emit_us": {"frozen": frozen_us, "collapse": collapse_us, "dda": dda_us},
                      "dda_vs_collapse_permille": vs_collapse, "dda_vs_frozen_permille": vs_frozen,
                      "floor_divides": {"collapse": collapse_div, "dda": dda_div}}, indent=1))
    print(f"[gauntlet1c] -> {os.path.relpath(out, ROOT)}  (cites GAUNTLET-1 {g1[:8]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
