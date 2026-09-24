# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""bench.py — the kernel's wall-clock on a named host, as a record under the envelope (off-gate).

    python verify/bench.py --host NAME [--samples 200] [--warm 20] [--scene witness] [--tiles identity]

Compiles kernel/main.rs in release, checks the two witnesses against the frozen corpus FIRST (a bench of the
wrong picture is refused), then records per-phase p50/p95/p99/max microseconds and the three budgets AS DATA —
16,667 / 6,944 / 4,167 µs for 60 / 144 / 240 Hz — with the comparison left to the reading. No verdict-shaped
key exists in the record; `records-firewall` would refuse one. Renderer time only: no window, no present, no
input. Writes kernel/attest/bench-<host>.json.
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "verify"))
import envelope  # noqa: E402

BUDGETS_US = {"60hz": 16667, "144hz": 6944, "240hz": 4167}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--samples", type=int, default=200)
    ap.add_argument("--warm", type=int, default=20)
    ap.add_argument("--scene", default="witness")
    ap.add_argument("--tiles", default="identity")
    a = ap.parse_args()
    rustc = shutil.which("rustc")
    if rustc is None:
        print("REFUSE: rustc not found")
        return 2
    import json
    with open(os.path.join(ROOT, "oracle", "witnesses.json"), encoding="utf-8") as fh:
        corpus = json.load(fh)
    scene = corpus["scenes"][a.scene]
    want = scene["witnesses"][a.tiles]
    build = os.path.join(ROOT, "verify", "build")
    os.makedirs(build, exist_ok=True)
    exe = os.path.join(build, "kernel-bench" + (".exe" if os.name == "nt" else ""))
    cp = subprocess.run([rustc, "-C", "opt-level=3", os.path.join(ROOT, "kernel", "main.rs"), "-o", exe], capture_output=True, text=True)
    if cp.returncode != 0:
        print("REFUSE: rustc failed\n" + cp.stderr)
        return 2
    x, z, f = scene["camera"]
    args = [exe, "--level", os.path.join(ROOT, "oracle", "levels", scene["level"] + ".lvl"),
            "--tiles", os.path.join(ROOT, "oracle", "tiles", a.tiles + ".tiles"), "--camera", f"{x},{z},{f}",
            "--bench", str(a.samples), "--warm", str(a.warm)]
    cp = subprocess.run(args, capture_output=True, text=True)
    lines = dict(ln.split(" ", 1) for ln in cp.stdout.strip().splitlines() if " " in ln)
    if cp.returncode != 0 or lines.get("selfcheck") != "OK":
        print("REFUSE: the kernel did not selfcheck\n" + cp.stdout + cp.stderr)
        return 2
    if lines["frame"] != want["frame"] or lines["pixels"] != want["pixels"]:
        print("REFUSE: the bench rendered something other than the frozen witnesses; no number is printed")
        return 2
    if not lines.get("bench_samples", "").endswith("same_witnesses OK"):
        print("REFUSE: the witnesses moved during the bench")
        return 2

    def pct(key):
        kv = dict(p.split("=") for p in lines[key].split())
        return {k: int(v) for k, v in kv.items()}
    data = {
        "phases_us": {"frame": pct("bench_frame_us"), "pixels": pct("bench_pixels_us"), "total": pct("bench_total_us")},
        "budgets_us": BUDGETS_US,
        "samples": a.samples,
        "warmup": a.warm,
        "witnesses": {"frame": lines["frame"], "pixels": lines["pixels"]},
    }
    prov = {
        "tool": "verify/bench.py", "kernel": "kernel/main.rs (+ mantle.rs, formats.rs, hud.rs)", "flags": ["-C", "opt-level=3"],
        "rustc": subprocess.run([rustc, "--version"], capture_output=True, text=True).stdout.strip(),
        "host": a.host, "host_line": lines.get("host", ""), "python": platform.python_version(), "os": platform.system(), "machine": platform.machine(),
        "scene": a.scene, "tiles": a.tiles, "camera": [x, z, f], "corpus_commit": corpus["origin"]["commit"],
    }
    total = data["phases_us"]["total"]
    reading = (f"renderer time per frame on host {a.host}: total p50 {total['p50']} / p95 {total['p95']} / p99 {total['p99']} / max {total['max']} µs "
               f"against budgets 16,667 (60 Hz), 6,944 (144 Hz), 4,167 (240 Hz); the comparison is the reader's, from the two numbers; "
               f"the witnesses were checked before any number was taken")
    rec = envelope.seal(
        "verdandi-kernel-bench", 1, "measured", prov,
        {"certifies": f"per-frame renderer time of the kernel on host {a.host} for scene {a.scene} with {a.tiles} tiles, {a.samples} samples after {a.warm} warm-ups",
         "host": a.host, "scene": a.scene, "tiles": a.tiles},
        ["input-to-photon latency (input transport, present wait and the panel need capture hardware)",
         "a present, a window, a compositor: none is in this number",
         "any other host, scene or tile set",
         "that the kernel is optimised: this is the baseline the gauntlet is measured against"],
        data, reading)
    out_dir = os.path.join(ROOT, "kernel", "attest")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"bench-{a.host}.json")
    envelope.write(out, rec)
    print(json.dumps({"host": a.host, "total_us": total, "frame_us": data["phases_us"]["frame"], "pixels_us": data["phases_us"]["pixels"]}, indent=1))
    print(f"[bench] -> {os.path.relpath(out, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
