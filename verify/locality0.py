# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""locality0.py — LOCALITY-0: the process-isolated floor-tile execution-format court on a named host (off-gate).

    python verify/locality0.py --host NAME [--samples 300] [--warm 30] [--strips 8] [--scene witness] [--tiles identity]

Per the Epistemic-Invariance theorem (EPISTEMIC-INVARIANCE.md), the two layouts are NOT timed in one process (that
pollutes the branch predictor and the instruction cache) and NOT in two loose runs (that leaks thermal drift).
Instead this orchestrator invokes the SAME binary once per variant with `--variant blocked|morton`, so each process
has a clean BTB and a single variant's I-cache, and it INTERLEAVES those invocations in alternating strips
(blocked, morton, blocked, ...) so slow drift cancels between neighbours. Each invocation times its variant against
a DDA baseline measured IN THE SAME PROCESS; the orchestrator compares the two DDA-relative improvements (medians
across strips, robust to a one-off spike), so per-process baseline drift cancels too.

Byte-identity is checked FIRST (`--locality`), before any number. The record stores only numbers; the promotion
call (the three exits) is the reader's, stated in the reading. Never compared to GAUNTLET-0's instrumented absolute.
Writes kernel/attest/locality0-<host>.json, citing the LOCALITY-0 registration.
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
    x, z, f = scene["camera"]
    build = os.path.join(ROOT, "verify", "build")
    os.makedirs(build, exist_ok=True)
    exe = os.path.join(build, "kernel-locality0" + (".exe" if os.name == "nt" else ""))
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

    def kv(d, key):
        return dict(p.split("=") for p in d[key].split() if "=" in p)

    # byte-identity FIRST — both layouts, non-vacuous, before any timing
    cp = subprocess.run(base + ["--locality"], capture_output=True, text=True)
    L = parse(cp.stdout)
    if cp.returncode != 0 or L.get("selfcheck") != "OK":
        print("REFUSE: the kernel did not selfcheck\n" + cp.stdout + cp.stderr)
        return 2
    if L.get("frame") != want["frame"] or L.get("pixels") != want["pixels"]:
        print("REFUSE: --locality rendered something other than the frozen witnesses")
        return 2
    eq, se = kv(L, "locality_equal"), kv(L, "locality_synthemit")
    if eq.get("blocked") != "OK" or eq.get("morton") != "OK" or eq.get("linear_anchor") != "OK" \
       or se.get("blocked") != "OK" or se.get("morton") != "OK":
        print("REFUSE: a swizzled layout is NOT byte-identical to the frozen emit; no speed number is printed")
        return 2

    # interleaved, process-isolated strips: blocked, morton, blocked, morton, ...
    def invoke(variant):
        c = subprocess.run(base + ["--variant", variant, "--locality-bench", str(a.samples), "--warm", str(a.warm)],
                           capture_output=True, text=True)
        if c.returncode != 0:
            raise RuntimeError("locality-bench %s failed: %s" % (variant, c.stderr.strip()))
        d = parse(c.stdout)
        r = {
            "dda_p99": int(kv(d, "locbench_dda_us")["p99"]),
            "var_p99": int(kv(d, "locbench_" + variant + "_us")["p99"]),
            "x_lin": int(kv(d, "locbench_addr_us")["lin_p99"]),
            "x_var": int(kv(d, "locbench_addr_us")["var_p99"]),
            "bands": {b: {"dda": int(kv(d, "locband_%s_%s" % (variant, b))["dda_p99"]),
                          "var": int(kv(d, "locband_%s_%s" % (variant, b))["var_p99"])} for b in ("near", "mid", "far")},
            "host": d.get("host", ""),
        }
        return r

    acc = {"blocked": [], "morton": []}
    for _ in range(a.strips):
        for v in ("blocked", "morton"):
            acc[v].append(invoke(v))

    def agg(v):
        rs = acc[v]
        out = {
            "dda_p99": _median([r["dda_p99"] for r in rs]),
            "variant_p99": _median([r["var_p99"] for r in rs]),
            "index_tax_x_p99": _median([r["x_var"] - r["x_lin"] for r in rs]),
            "bands": {b: {"dda_p99": _median([r["bands"][b]["dda"] for r in rs]),
                          "var_p99": _median([r["bands"][b]["var"] for r in rs])} for b in ("near", "mid", "far")},
        }
        out["improve_permille"] = (out["dda_p99"] * 1000) // out["variant_p99"] if out["variant_p99"] else 0
        return out

    blocked, morton = agg("blocked"), agg("morton")
    data = {
        "blocked": blocked,
        "morton": morton,
        "strips": a.strips, "samples": a.samples, "warmup": a.warm,
        "dda_baseline_us": _median([r["dda_p99"] for r in acc["blocked"] + acc["morton"]]),
        "witnesses": {"frame": L["frame"], "pixels": L["pixels"]},
    }
    prov = {
        "tool": "kernel/main.rs --locality-bench (process-isolated) + verify/locality0.py",
        "kernel": "kernel/main.rs (+ mantle.rs, fast.rs, formats.rs, hud.rs)", "flags": ["-C", "opt-level=3"],
        "rustc": subprocess.run([rustc, "--version"], capture_output=True, text=True).stdout.strip(),
        "host": a.host, "host_line": acc["blocked"][0]["host"], "python": platform.python_version(),
        "os": platform.system(), "machine": platform.machine(), "scene": a.scene, "tiles": a.tiles,
        "camera": [x, z, f], "corpus_commit": corpus["origin"]["commit"], "instrument": "Epistemic-Invariance process-isolated interleaved strips",
    }
    with open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8") as fh:
        rb = json.load(fh)["entries"]["LOCALITY-0"]["chain_hash"]
    prov["preregistered"] = {"rung": "LOCALITY-0", "chain_hash": rb}

    # the three exits — a READING of the numbers, not a stored verdict
    b_faster = blocked["improve_permille"] > 1000
    m_faster = morton["improve_permille"] > 1000
    if b_faster and blocked["improve_permille"] >= morton["improve_permille"]:
        exit_line = ("EXIT 1 (blocked wins): blocked is byte-identical AND faster than the DDA baseline "
                     f"({blocked['improve_permille']} permille of it) and at least as fast as morton "
                     f"({morton['improve_permille']}). Action for the reader: LOCK the 8x8 blocked layout.")
        g2 = blocked["variant_p99"]
    elif m_faster:
        exit_line = ("EXIT 2 (morton wins): morton is byte-identical AND faster than the DDA baseline "
                     f"({morton['improve_permille']} permille) and beats blocked ({blocked['improve_permille']}). "
                     "Action for the reader: LOCK the Morton Z-order layout.")
        g2 = morton["variant_p99"]
    else:
        exit_line = ("EXIT 3 (capacity collapse): NEITHER layout beats the DDA baseline "
                     f"(blocked {blocked['improve_permille']}, morton {morton['improve_permille']} permille of it). "
                     "This is a finding, not a null: the tile-fetch stall is a capacity/LRU miss no permutation of the "
                     "192 KB tile can fix. Action for the reader: spatial locality is irrelevant for single-thread "
                     "scaling; transition to GAUNTLET-2 (multi-threaded column stripping) to hide the latency behind compute.")
        g2 = data["dda_baseline_us"]
    data["gauntlet2_baseline_p99_us"] = g2
    reading = (f"the floor-tile execution-format court on host {a.host}, process-isolated and interleaved over {a.strips} "
               f"strips (medians). Whole-frame p99: DDA baseline {data['dda_baseline_us']} us; blocked {blocked['variant_p99']} "
               f"({blocked['improve_permille']} permille of DDA, index tax X {blocked['index_tax_x_p99']} us), morton "
               f"{morton['variant_p99']} ({morton['improve_permille']} permille, X {morton['index_tax_x_p99']} us). {exit_line} "
               f"Per-band floor p99 (dda/var): blocked near {blocked['bands']['near']['dda_p99']}/{blocked['bands']['near']['var_p99']}, "
               f"mid {blocked['bands']['mid']['dda_p99']}/{blocked['bands']['mid']['var_p99']}, far "
               f"{blocked['bands']['far']['dda_p99']}/{blocked['bands']['far']['var_p99']}; morton near "
               f"{morton['bands']['near']['dda_p99']}/{morton['bands']['near']['var_p99']}, mid "
               f"{morton['bands']['mid']['dda_p99']}/{morton['bands']['mid']['var_p99']}, far "
               f"{morton['bands']['far']['dda_p99']}/{morton['bands']['far']['var_p99']}. Byte-identity was proven first "
               f"(locality0-equiv, non-vacuous). The accepted single-thread emit p99 {g2} us is the sealed HARD BASELINE "
               f"for GAUNTLET-2. Deltas are process-isolated same-apparatus improvements (medians, outliers absorbed), "
               f"NOT hardware-resource costs and NEVER compared to GAUNTLET-0's instrumented render absolute")
    rec = envelope.seal(
        "verdandi-locality0", 1, "measured", prov,
        {"certifies": f"the process-isolated same-apparatus speed of the blocked and Morton floor-tile layouts vs the DDA baseline on host {a.host} for scene {a.scene} with {a.tiles} tiles, {a.samples} samples x {a.strips} interleaved strips",
         "host": a.host, "scene": a.scene, "tiles": a.tiles},
        ["input-to-photon latency, a present, a window, a compositor: none is in this number",
         "the whole-render cost: this is emit only, over the frozen strips + frame the layouts share",
         "any comparison to GAUNTLET-0's instrumented render absolute (a different apparatus)",
         "the per-variant deltas as pure hardware-resource costs: they are process-isolated same-apparatus improvements, and cache/scheduling make sub-phase subtraction non-additive",
         "instruction-level invariance as proven: only OUTPUT byte-identity is proven (locality0-equiv); the address-generation isolation is a best-effort of code structure",
         "any other host, scene, tile set or resolution; absolute us are host-specific",
         "that a layout is promoted by this record: promotion is the reader's, from the three exits and the locked table"],
        data, reading)
    out_dir = os.path.join(ROOT, "kernel", "attest")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"locality0-{a.host}.json")
    envelope.write(out, rec)
    print(json.dumps({"host": a.host, "dda_baseline_us": data["dda_baseline_us"],
                      "blocked": {"p99": blocked["variant_p99"], "improve_permille": blocked["improve_permille"], "X": blocked["index_tax_x_p99"]},
                      "morton": {"p99": morton["variant_p99"], "improve_permille": morton["improve_permille"], "X": morton["index_tax_x_p99"]},
                      "gauntlet2_baseline_p99_us": g2}, indent=1))
    print("[locality0] " + exit_line)
    print(f"[locality0] -> {os.path.relpath(out, ROOT)}  (cites LOCALITY-0 {rb[:8]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
