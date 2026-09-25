# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""rebreakdown1.py — RE-BREAKDOWN-1: emit's cost structure on a named host, as a record under the envelope (off-gate).

    python verify/rebreakdown1.py --host NAME [--samples 300] [--warm 30] [--scene witness] [--tiles identity]

Compiles kernel/main.rs in release, then runs `--emit-breakdown` in one invocation. Court A (deterministic) is
recorded as-is: the divide-work, the tile/map memory reads, the tile working-set cardinality, the floor texel-stride
locality, and the write-once coverage. Court B is the host ablation: probe_addr -> probe_lookup -> probe_full timed
against emit on ONE apparatus, with probe VERIFY byte-identical to emit checked FIRST (the apparatus is a proven
subset of the certified path). The Court B increments are recorded AS DATA and read as INCREMENTAL WALL-CLOCK
ATTRIBUTION UNDER CONTROLLED ABLATION — never as pure hardware-resource costs, and never compared to GAUNTLET-0's
instrumented render absolute. No verdict-shaped key exists in the record; `records-firewall` would refuse one.

This rung MEASURES; it commits no optimization. The promotion table (locked in the preregistration) is the reader's,
applied to these numbers. Writes kernel/attest/emit-breakdown-<host>.json, citing the RE-BREAKDOWN-1 registration.
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
    exe = os.path.join(build, "kernel-rebreakdown1" + (".exe" if os.name == "nt" else ""))
    cp = subprocess.run([rustc, "-C", "opt-level=3", os.path.join(ROOT, "kernel", "main.rs"), "-o", exe], capture_output=True, text=True)
    if cp.returncode != 0:
        print("REFUSE: rustc failed\n" + cp.stderr)
        return 2
    x, z, f = scene["camera"]
    args = [exe, "--level", os.path.join(ROOT, "oracle", "levels", scene["level"] + ".lvl"),
            "--tiles", os.path.join(ROOT, "oracle", "tiles", a.tiles + ".tiles"), "--camera", f"{x},{z},{f}",
            "--emit-breakdown", str(a.samples), "--warm", str(a.warm)]
    cp = subprocess.run(args, capture_output=True, text=True)
    lines = dict(ln.split(" ", 1) for ln in cp.stdout.strip().splitlines() if " " in ln)
    # the apparatus must be a subset of the certified path, and it must render the frozen witness, before any number
    if cp.returncode != 0 or lines.get("selfcheck") != "OK":
        print("REFUSE: the kernel did not selfcheck\n" + cp.stdout + cp.stderr)
        return 2
    if lines.get("frame") != want["frame"] or lines.get("pixels") != want["pixels"]:
        print("REFUSE: the emit-breakdown rendered something other than the frozen witnesses; no number is printed")
        return 2
    if lines.get("emitbd_verify") != "OK":
        print("REFUSE: the probe VERIFY path is NOT byte-identical to emit; the apparatus is not a subset of the certified path")
        return 2
    if not lines.get("emitbd_samples", "").endswith("same_witnesses OK"):
        print("REFUSE: the timed emit did not reproduce the frozen witness")
        return 2

    def kv(key):
        return dict(p.split("=") for p in lines[key].split() if "=" in p)

    def pct(key):
        return {k: int(v) for k, v in kv(key).items()}

    st = kv("emitbd_struct")
    lo = kv("emitbd_locality")
    wr = kv("emitbd_writes")
    addr, lookup, full, emit = pct("emitbd_addr_us"), pct("emitbd_lookup_us"), pct("emitbd_full_us"), pct("emitbd_emit_us")
    structure = {k: int(v) for k, v in st.items()}
    structure["floor_adj"] = int(lo["floor_adj"])
    structure["floor_local"] = int(lo["floor_local"])
    structure["local_permille"] = int(lo["local_permille"])
    structure["writes"] = int(wr["writes"])
    increments = {
        "lookup_minus_addr_p99": lookup["p99"] - addr["p99"],
        "full_minus_lookup_p99": full["p99"] - lookup["p99"],
        "full_vs_emit_p99": full["p99"] - emit["p99"],
    }
    data = {
        "court_a_structure": structure,
        "court_b_ablation_us": {"addr": addr, "lookup": lookup, "full": full, "emit": emit},
        "court_b_increments_us_p99": increments,
        "samples": a.samples,
        "warmup": a.warm,
        "witnesses": {"frame": lines["frame"], "pixels": lines["pixels"]},
    }
    prov = {
        "tool": "kernel/main.rs --emit-breakdown + verify/rebreakdown1.py", "kernel": "kernel/main.rs (+ mantle.rs, fast.rs, formats.rs, hud.rs)",
        "flags": ["-C", "opt-level=3"], "rustc": subprocess.run([rustc, "--version"], capture_output=True, text=True).stdout.strip(),
        "host": a.host, "host_line": lines.get("host", ""), "python": platform.python_version(), "os": platform.system(), "machine": platform.machine(),
        "scene": a.scene, "tiles": a.tiles, "camera": [x, z, f], "corpus_commit": corpus["origin"]["commit"],
    }
    with open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8") as fh:
        reg1 = json.load(fh)
    rb = reg1["entries"]["RE-BREAKDOWN-1"]["chain_hash"]
    prov["preregistered"] = {"rung": "RE-BREAKDOWN-1", "chain_hash": rb}
    incs = {"tile fetch (lookup - addr)": increments["lookup_minus_addr_p99"],
            "map/assembly (full - lookup)": increments["full_minus_lookup_p99"]}
    largest = max(incs, key=incs.get)
    reading = (f"emit's cost structure on host {a.host}. Court A (deterministic): {structure['wall_tex']} wall + "
               f"{structure['floor_tex']} floor textured px, {structure['divides']} divides, {structure['tile_reads']} "
               f"tile reads, working set {structure['ws_floor']} floor / {structure['ws_wall']} wall distinct texels "
               f"(of 65536), and {structure['local_permille']} permille of adjacent floor texels within a cache line. "
               f"Court B (host ablation, p99 us): addr {addr['p99']} -> lookup {lookup['p99']} -> full {full['p99']}, "
               f"emit {emit['p99']}; the increments are lookup-addr {increments['lookup_minus_addr_p99']} (tile fetch), "
               f"full-lookup {increments['full_minus_lookup_p99']} (map/assembly). These are INCREMENTAL wall-clock "
               f"attribution under controlled ablation, NOT pure resource costs: cache/branch/scheduling make the "
               f"subtraction non-additive and the experiment has no architectural counters. The largest increment is "
               f"'{largest}'; the promotion table (the reader's, from the preregistration) says a dominant lookup "
               f"increment or pathological locality LOCKs a data-layout/locality court, a dominant address increment "
               f"the arithmetic path, a dominant write the framebuffer path, and disagreement or no dominance DEFERs. "
               f"probe VERIFY is byte-identical to emit (the apparatus is a subset of the certified path); FULL carries "
               f"a small black_box anchor tax vs emit (full-emit {increments['full_vs_emit_p99']} us at p99). This is "
               f"EMIT-level only, never the whole render, and NEVER compared to GAUNTLET-0's instrumented absolute")
    rec = envelope.seal(
        "verdandi-emit-breakdown", 1, "measured", prov,
        {"certifies": f"the deterministic structure of emit and the same-apparatus ablation attribution of its work classes on host {a.host} for scene {a.scene} with {a.tiles} tiles, {a.samples} samples after {a.warm} warm-ups",
         "host": a.host, "scene": a.scene, "tiles": a.tiles},
        ["the Court B increments as pure hardware-resource costs: they are incremental wall-clock attribution under controlled ablation, non-additive, with no architectural counters",
         "input-to-photon latency (input transport, present wait and the panel need capture hardware)",
         "a present, a window, a compositor: none is in this number",
         "the whole-render or per-frame cost: this is emit ONLY, timed over the frozen strips + frame the probes share",
         "any comparison to GAUNTLET-0's instrumented render absolute: different apparatus",
         "any other host, scene, tile set or resolution; absolute us are host-specific",
         "that the probes are renderers: they are fenced measurement apparatus (probe VERIFY == emit is the subset proof; the ablated probes are wrong by construction)",
         "that Court A's counts are a wall-clock: they are a deterministic source-cost proxy that names candidates, not the time"],
        data, reading)
    out_dir = os.path.join(ROOT, "kernel", "attest")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"emit-breakdown-{a.host}.json")
    envelope.write(out, rec)
    print(json.dumps({"host": a.host, "court_a": {"ws_floor": structure["ws_floor"], "ws_wall": structure["ws_wall"],
                      "local_permille": structure["local_permille"], "writes": structure["writes"]},
                      "court_b_p99_us": {"addr": addr["p99"], "lookup": lookup["p99"], "full": full["p99"], "emit": emit["p99"]},
                      "increments_us_p99": increments, "largest_increment": largest}, indent=1))
    print(f"[rebreakdown1] -> {os.path.relpath(out, ROOT)}  (cites RE-BREAKDOWN-1 {rb[:8]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
