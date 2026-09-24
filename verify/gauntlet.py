# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""gauntlet.py — GAUNTLET-0: the reference render decomposed on a named host, as a record under the envelope (off-gate).

    python verify/gauntlet.py --host NAME [--samples 300] [--warm 30] [--scene witness] [--tiles identity]

Compiles kernel/main.rs in release, checks the two witnesses against the frozen corpus FIRST (a breakdown of the
wrong picture is refused), then records per-phase p50/p95/p99/max microseconds — strips (traversal), frame
(walls + floor cast), emit (texel pass), and the two WITNESS hashes (frame_digest, pixel_sha) — plus each render
phase's p99 render-share in permille, AS DATA. No verdict-shaped key exists in the record; `records-firewall`
would refuse one. The 500-permille decision rule (a render phase must clear it to earn a GAUNTLET-1 seat) is the
reader's, applied to the shares. mantle.rs is not modified — this only times existing pub calls. Renderer time
only. Writes kernel/attest/breakdown-<host>.json, citing the LATENCY-0-style GAUNTLET-0 preregistration.
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
    exe = os.path.join(build, "kernel-breakdown" + (".exe" if os.name == "nt" else ""))
    cp = subprocess.run([rustc, "-C", "opt-level=3", os.path.join(ROOT, "kernel", "main.rs"), "-o", exe], capture_output=True, text=True)
    if cp.returncode != 0:
        print("REFUSE: rustc failed\n" + cp.stderr)
        return 2
    x, z, f = scene["camera"]
    args = [exe, "--level", os.path.join(ROOT, "oracle", "levels", scene["level"] + ".lvl"),
            "--tiles", os.path.join(ROOT, "oracle", "tiles", a.tiles + ".tiles"), "--camera", f"{x},{z},{f}",
            "--breakdown", str(a.samples), "--warm", str(a.warm)]
    cp = subprocess.run(args, capture_output=True, text=True)
    lines = dict(ln.split(" ", 1) for ln in cp.stdout.strip().splitlines() if " " in ln)
    if cp.returncode != 0 or lines.get("selfcheck") != "OK":
        print("REFUSE: the kernel did not selfcheck\n" + cp.stdout + cp.stderr)
        return 2
    if lines["frame"] != want["frame"] or lines["pixels"] != want["pixels"]:
        print("REFUSE: the breakdown rendered something other than the frozen witnesses; no number is printed")
        return 2
    if not lines.get("breakdown_samples", "").endswith("same_witnesses OK"):
        print("REFUSE: the witnesses moved during the breakdown")
        return 2

    def pct(key):
        parts = lines[key].split()
        kv = dict(p.split("=") for p in parts)
        return {k: int(v) for k, v in kv.items()}

    strips, frame, emit = pct("breakdown_strips_us"), pct("breakdown_frame_us"), pct("breakdown_emit_us")
    fdh, psh, render = pct("breakdown_framedigest_us"), pct("breakdown_pixelsha_us"), pct("breakdown_render_us")
    shares = {"strips": strips.pop("render_permille"), "frame": frame.pop("render_permille"),
              "emit": emit.pop("render_permille")}
    fdh.pop("render_permille", None)
    psh.pop("render_permille", None)
    data = {
        "render_phases_us": {"strips": strips, "frame": frame, "emit": emit, "render": render},
        "render_p99_shares_permille": shares,
        "witness_hashes_us": {"frame_digest": fdh, "pixel_sha": psh},
        "decision_rule_permille": 500,
        "samples": a.samples,
        "warmup": a.warm,
        "witnesses": {"frame": lines["frame"], "pixels": lines["pixels"]},
    }
    prov = {
        "tool": "kernel/main.rs --breakdown + verify/gauntlet.py", "kernel": "kernel/main.rs (+ mantle.rs, formats.rs, hud.rs)",
        "flags": ["-C", "opt-level=3"], "rustc": subprocess.run([rustc, "--version"], capture_output=True, text=True).stdout.strip(),
        "host": a.host, "host_line": lines.get("host", ""), "python": platform.python_version(), "os": platform.system(), "machine": platform.machine(),
        "scene": a.scene, "tiles": a.tiles, "camera": [x, z, f], "corpus_commit": corpus["origin"]["commit"],
    }
    with open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8") as fh:
        reg = json.load(fh)
    g0 = reg["entries"]["GAUNTLET-0"]["chain_hash"]
    prov["preregistered"] = {"rung": "GAUNTLET-0", "chain_hash": g0}
    dom = max(shares, key=shares.get)
    reading = (f"reference render decomposed on host {a.host}: strips {shares['strips']} / frame {shares['frame']} / emit "
               f"{shares['emit']} permille of the render p99; the largest is {dom} ({shares[dom]} permille). The 500-permille "
               f"decision rule (the reader's, applied to these shares) says GAUNTLET-1 targets {dom} iff its share >= 500, and "
               f"the incremental-floor-cast hypothesis dies unless frame >= 500. The two witness hashes are verification-only "
               f"cost, excluded from the render total; the witnesses were checked before any number was taken")
    rec = envelope.seal(
        "verdandi-render-breakdown", 1, "measured", prov,
        {"certifies": f"the per-phase render decomposition of the kernel on host {a.host} for scene {a.scene} with {a.tiles} tiles, {a.samples} samples after {a.warm} warm-ups",
         "host": a.host, "scene": a.scene, "tiles": a.tiles},
        ["input-to-photon latency (input transport, present wait and the panel need capture hardware)",
         "a present, a window, a compositor: none is in this number",
         "any other host, scene, tile set or resolution; absolute us are host-specific — the permille shares are the portable quantity",
         "a speed improvement: a breakdown is a target-finder, not an optimization; GAUNTLET-1 must prove byte-identity before any speed claim",
         "that the witness hashes (frame_digest, pixel_sha) are interactive-render cost: they are verification-only and excluded from the render total"],
        data, reading)
    out_dir = os.path.join(ROOT, "kernel", "attest")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"breakdown-{a.host}.json")
    envelope.write(out, rec)
    print(json.dumps({"host": a.host, "shares_permille": shares, "dominant": dom, "render_us": render,
                      "witness_hashes_us": {"frame_digest": fdh, "pixel_sha": psh}}, indent=1))
    print(f"[gauntlet] -> {os.path.relpath(out, ROOT)}  (cites GAUNTLET-0 {g0[:8]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
