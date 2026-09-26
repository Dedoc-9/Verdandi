# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""allocreuse.py — ALLOC-REUSE-0: how much of the frame is buffer allocation (off-gate, host).

    python verify/allocreuse.py --host NAME [--session workshop/attest/sessionwalk-demo.json] [--per-cell 300] [--confirm]

FRAME-SPLIT-0 (confirmed) attributes each buffer's allocation to its phase: strips, frame (2 MB), emit (6 MB), bgr
(6 MB). This diagnostic court varies ONE thing — the buffers' lifetime: FRESH (allocated every frame, the production
path) against REUSED (allocated once, overwritten), the same calls in the same order otherwise, on FRAME-SPLIT-0's
window and apparatus; per variant an envelope and a split, four cells ABBA after 10 warm-up rounds, witnesses first
(the reused composite and blit bytes equal the fresh path's for every sealed frame). The floor swizzle's buffer stays
fresh in both (it is fast.rs's own, untouched).

The preregistered reading, on p50s: VOID if either variant's |instrumentation tax| >= 100 permille of its envelope;
CONFOUNDED if the phases whose allocation does not change (floor_swizzle, hud, blit, summed) moved >= 50 permille of
the fresh sum; otherwise with dE = envelope(reused) - envelope(fresh), |dE| >= 50 permille of the fresh envelope reads
ALLOCATION MATERIAL (reuse cheaper or dearer), less reads ALLOCATION IMMATERIAL. The per-phase deltas (strips, frame,
emit, bgr) are reported beside, never ruled on. A diagnostic: no seat, and no change to the production path is
adopted by it. Writes shell/attest/allocreuse-<host>.json citing ALLOC-REUSE-0.
"""
from __future__ import annotations

import argparse
import os
import platform
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envelope  # noqa: E402
from diagcommon import Refuse, host_run, registry, write_record  # noqa: E402

DEFAULT_SESSION = "workshop/attest/sessionwalk-demo.json"
PHASES = ("strips", "frame", "floor_swizzle", "emit", "hud", "bgr", "blit")
ALLOCATING = ("strips", "frame", "emit", "bgr")
UNCHANGED = ("floor_swizzle", "hud", "blit")
VARIANTS = ("fresh", "reused")
PCT = ("p50", "p95", "p99", "max")
WARM_ROUNDS = 10
VOID_TAX_PERMILLE = 100
CONFOUND_PERMILLE = 50
MATERIAL_PERMILLE = 50


def _pct(x) -> bool:
    return isinstance(x, dict) and all(isinstance(x.get(k), int) for k in PCT)


def check_raw(raw: dict) -> dict:
    if raw.get("name") != "verdandi-allocreuse":
        raise Refuse("not a verdandi-allocreuse record")
    d = raw.get("data", {})
    if tuple(d.get("phases", ())) != PHASES:
        raise Refuse("the phases are not the registered ones, in order")
    if (d.get("production_threads"), d.get("warm_rounds"), d.get("phase_origin")) != (8, WARM_ROUNDS, "locked"):
        raise Refuse("production T, warm-up or phase origin is not the registered one")
    n = d.get("samples_per_cell")
    if not isinstance(n, int) or n <= 0:
        raise Refuse("no samples per cell")
    for v in VARIANTS:
        vd = d.get("variants", {}).get(v, {})
        env, spl = vd.get("envelope", {}), vd.get("split", {})
        if env.get("samples") != n or spl.get("samples") != n:
            raise Refuse(f"{v}: a cell is missing or partial")
        if not (_pct(env.get("render_us")) and _pct(env.get("present_us")) and _pct(spl.get("render_us")) and _pct(spl.get("present_us"))):
            raise Refuse(f"{v}: intervals are not integer p50/p95/p99/max")
        if tuple(spl.get("phases_us", {}).keys()) != PHASES or not all(_pct(x) for x in spl["phases_us"].values()):
            raise Refuse(f"{v}: the split's phases are missing or not integer percentiles")
    return d


def derive(vd: dict) -> dict:
    env, spl, ph = vd["envelope"]["render_us"], vd["split"]["render_us"], vd["split"]["phases_us"]
    tax = spl["p50"] - env["p50"]
    return {"envelope_p50_us": env["p50"], "envelope_p99_us": env["p99"],
            "phase_p50_us": {p: ph[p]["p50"] for p in PHASES},
            "unchanged_p50_sum_us": sum(ph[p]["p50"] for p in UNCHANGED),
            "tax_p50_us": tax, "abs_tax_p50_permille_of_envelope": (abs(tax) * 1000) // env["p50"] if env["p50"] > 0 else 0}


def attribute(f: dict, r: dict) -> tuple[str, dict]:
    dE = r["envelope_p50_us"] - f["envelope_p50_us"]
    dU = r["unchanged_p50_sum_us"] - f["unchanged_p50_sum_us"]
    deltas = {"envelope_delta_p50_us": dE,
              "envelope_delta_permille_of_fresh": (abs(dE) * 1000) // f["envelope_p50_us"] if f["envelope_p50_us"] > 0 else 0,
              "envelope_delta_p99_us": r["envelope_p99_us"] - f["envelope_p99_us"],
              "unchanged_delta_p50_us": dU,
              "unchanged_delta_permille_of_fresh": (abs(dU) * 1000) // f["unchanged_p50_sum_us"] if f["unchanged_p50_sum_us"] > 0 else 0,
              "phase_delta_p50_us": {p: r["phase_p50_us"][p] - f["phase_p50_us"][p] for p in PHASES}}
    if max(f["abs_tax_p50_permille_of_envelope"], r["abs_tax_p50_permille_of_envelope"]) >= VOID_TAX_PERMILLE:
        return "VOID", deltas
    if deltas["unchanged_delta_permille_of_fresh"] >= CONFOUND_PERMILLE:
        return "CONFOUNDED", deltas
    if deltas["envelope_delta_permille_of_fresh"] >= MATERIAL_PERMILLE:
        return ("ALLOCATION MATERIAL (reuse cheaper)" if dE < 0 else "ALLOCATION MATERIAL (reuse dearer)"), deltas
    return "ALLOCATION IMMATERIAL", deltas


def seal_allocreuse(raw: dict, reg: dict, host: str, session: dict, build: dict,
                    confirm_of: dict | None = None) -> tuple[dict, str]:
    d = check_raw(raw)
    f, r = derive(d["variants"]["fresh"]), derive(d["variants"]["reused"])
    label, deltas = attribute(f, r)
    data = dict(d)
    data["derived"] = {"fresh": f, "reused": r, "deltas": deltas}
    data["rule_permille"] = {"void_tax": VOID_TAX_PERMILLE, "confounded": CONFOUND_PERMILLE, "material": MATERIAL_PERMILLE}
    prov = {"tool": "shell allocreuse-window (shell/allocreuse.rs court over LATENCY-1R's GDI surface in FRAME-SPLIT-0's "
                    "window) + verify/allocreuse.py",
            "surface": raw.get("provenance", {}).get("tool", ""), "host": host, "session": session, "build": build,
            "raw_unix_seconds": raw.get("provenance", {}).get("unix_seconds"),
            "python": platform.python_version(), "os": platform.system(), "machine": platform.machine(),
            "preregistered": {"rung": "ALLOC-REUSE-0", "chain_hash": reg["ALLOC-REUSE-0"]["chain_hash"]}}
    per_phase = ", ".join(f"{p} {deltas['phase_delta_p50_us'][p]:+d}" for p in PHASES)
    reading = (f"ALLOC-REUSE-0 on host {host} ({d['samples_per_cell']} samples per cell). Envelope p50 fresh "
               f"{f['envelope_p50_us']} us, reused {r['envelope_p50_us']} us (delta {deltas['envelope_delta_p50_us']} us, "
               f"{deltas['envelope_delta_permille_of_fresh']} permille); the phases whose allocation does not change moved "
               f"{deltas['unchanged_delta_permille_of_fresh']} permille. Reading: {label}. Per-phase p50 deltas (reused - "
               f"fresh, us): {per_phase} — reported, not ruled on. A diagnostic: no seat, no change to the production path; "
               f"not input-to-photon.")
    name = "verdandi-allocreuse"
    if confirm_of is not None:
        name = "verdandi-allocreuse-confirm"
        prov["confirms"] = confirm_of
        same = confirm_of.get("original_label") == label
        reading = (f"CONFIRMATION run — does NOT replace the sealed ALLOC-REUSE-0 record (chain {confirm_of['chain_hash'][:8]}). "
                   f"The reading {'REPRODUCED' if same else 'did NOT reproduce'}: original {confirm_of.get('original_label')}, "
                   f"this run {label}. ") + reading
    rec = envelope.seal(
        name, 1, "measured", prov,
        {"certifies": f"the shell's production frame with its buffers allocated every frame and allocated once, on host "
                      f"{host}, envelope and split per variant, locked phase origin, {d['samples_per_cell']} samples per "
                      f"cell over {d['sequence_frames']} frames" + (" (a confirmation run)" if confirm_of is not None else ""),
         "host": host},
        ["a seat or an adopted change: the production path still allocates; adopting reuse would be its own change and court",
         "that allocation cost is the same on another allocator, OS, host or buffer size",
         "a per-phase verdict: the per-phase deltas are reported, the rule is on the envelope only",
         "input-to-photon latency, or a comparison with any emit p99"],
        data, reading)
    return rec, label


def main() -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--session", default=DEFAULT_SESSION)
    ap.add_argument("--per-cell", type=int, default=300)
    ap.add_argument("--confirm", action="store_true")
    a = ap.parse_args()
    try:
        raw, session, build = host_run("ALLOC-REUSE-0", "allocreuse", a.host, a.session, a.per_cell, 1)
        reg = registry()
        name, confirm_of = f"allocreuse-{a.host}.json", None
        if a.confirm:
            canon = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shell", "attest", name)
            if not os.path.exists(canon):
                raise Refuse(f"nothing to confirm — no sealed shell/attest/{name}; run without --confirm first")
            orig = envelope.read(canon)
            lab, _ = attribute(orig["data"]["derived"]["fresh"], orig["data"]["derived"]["reused"])
            confirm_of = {"of": f"shell/attest/{name}", "chain_hash": orig["chain_hash"], "original_label": lab}
            name = f"allocreuse-confirm-{a.host}.json"
        rec, label = seal_allocreuse(raw, reg, a.host, session, build, confirm_of)
    except Refuse as e:
        print(f"REFUSE: {e}")
        return 2
    out = write_record(name, rec)
    print(f"[allocreuse] {label} — envelope p50 fresh {rec['data']['derived']['fresh']['envelope_p50_us']} us, reused "
          f"{rec['data']['derived']['reused']['envelope_p50_us']} us")
    print(f"[allocreuse] -> {os.path.relpath(out)}  (cites ALLOC-REUSE-0 {reg['ALLOC-REUSE-0']['chain_hash'][:8]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
