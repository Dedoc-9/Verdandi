# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""allocreuse1.py — ALLOC-REUSE-1: the adoption court for the persistent-buffer render-loop entry (off-gate, host).

    python verify/allocreuse1.py --host NAME [--session workshop/attest/sessionwalk-demo.json] [--confirm]

What is adopted is an ENTRY CONTRACT: `present::LoopRenderer` as the production entry for any loop that renders once
per presented frame. No shipped window changes: `run` renders once and `playback-window` pre-renders frames that must
own their buffers. The fresh path (`arm_composite` + `to_blit`) is the frozen reference and is never rewritten.

Correctness comes first and is not this script's number: the gate's `allocreuse1-equiv` row proves the loop renderer
byte-identical to the fresh path over the certified corpus (goldens), the adversarial cameras and the sealed session,
in three orders from poisoned buffers, with no buffer replaced; and the host court refuses (no record) unless the
witnesses reproduce first and every sample's composite and blit equal their verified bytes, the buffers persistent.

The preregistered performance rule, on the uninstrumented envelope render-start -> frame-ready, fresh and reused
interleaved ABBA in the SAME run after 10 warm-up rounds, 1000 samples per cell:

    PERFORMANCE PASS   iff   p99(reused) <= 950 permille x p99(fresh)

The 50 permille is an ADOPTION MARGIN: a declared engineering decision threshold, not a measurement uncertainty or a
confidence interval. ADOPT requires PERFORMANCE PASS in this run AND in its --confirm run; anything else is REJECT
(the renderer stays an unused candidate and ALLOC-REUSE-0's diagnostic stands). p50s, frame-ready -> composited and
the 12 largest samples per variant are reported beside, never ruled on. HOST-STATE-0 snapshots (before and after the
window court) are recorded beside; they are attached after the label and the verdict are fixed, and no rule reads them.
Writes shell/attest/allocreuse1-<host>.json (and allocreuse1-confirm-<host>.json) citing ALLOC-REUSE-1.
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
VARIANTS = ("fresh", "reused")
PCT = ("p50", "p95", "p99", "max")
REQUIRED_PER_CELL = 1000
WARM_ROUNDS = 10
TAIL = 12
ADOPT_P99_PERMILLE = 950
PASS, FAIL = "PERFORMANCE PASS", "PERFORMANCE FAIL"


def _pct(x) -> bool:
    return (isinstance(x, dict) and all(isinstance(x.get(k), int) and not isinstance(x.get(k), bool) for k in PCT)
            and x["p50"] <= x["p95"] <= x["p99"] <= x["max"])


def check_raw(raw: dict, required_per_cell: int = REQUIRED_PER_CELL) -> dict:
    if raw.get("name") != "verdandi-allocreuse1":
        raise Refuse("not a verdandi-allocreuse1 record")
    d = raw.get("data", {})
    if (d.get("block_order"), d.get("warm_rounds"), d.get("phase_origin"), d.get("production_threads"),
            d.get("persistent_buffers")) != ("ABBA", WARM_ROUNDS, "locked", 8, 4):
        raise Refuse("the block order, warm-up, phase origin, production T or buffer count is not the registered one")
    n = d.get("samples_per_cell")
    if n != required_per_cell:
        raise Refuse(f"the run has {n} samples per cell; ALLOC-REUSE-1 is registered at {required_per_cell}")
    if tuple(d.get("variants", {}).keys()) != VARIANTS:
        raise Refuse("the variants are not fresh and reused, in order")
    for v in VARIANTS:
        vd = d["variants"][v]
        env = vd.get("envelope", {})
        if env.get("samples") != n:
            raise Refuse(f"{v}: the cell is missing or partial")
        if not (_pct(env.get("render_us")) and _pct(env.get("present_us"))):
            raise Refuse(f"{v}: the intervals are not integer, ordered p50/p95/p99/max")
        t = vd.get("tail_render_us")
        if (not isinstance(t, list) or len(t) != min(TAIL, n) or not all(isinstance(x, int) for x in t)
                or t != sorted(t, reverse=True) or t[0] != env["render_us"]["max"]):
            raise Refuse(f"{v}: the tail is not the {TAIL} largest samples, largest first")
    if not isinstance(d.get("reuse_renders"), int) or d["reuse_renders"] < n + WARM_ROUNDS:
        raise Refuse("the loop renderer did not render every warm-up and recorded sample")
    return d


def derive(vd: dict) -> dict:
    env = vd["envelope"]
    return {"render_p50_us": env["render_us"]["p50"], "render_p95_us": env["render_us"]["p95"],
            "render_p99_us": env["render_us"]["p99"], "render_max_us": env["render_us"]["max"],
            "composited_p50_us": env["present_us"]["p50"], "composited_p99_us": env["present_us"]["p99"],
            "tail_render_us": list(vd["tail_render_us"])}


def performance(dv: dict) -> tuple[str, dict]:
    """The preregistered rule. It reads the two variants' derived envelopes and nothing else."""
    f, r = dv["fresh"]["render_p99_us"], dv["reused"]["render_p99_us"]
    if f <= 0:
        raise Refuse("the fresh p99 is zero; no ratio can be formed")
    label = PASS if r * 1000 <= ADOPT_P99_PERMILLE * f else FAIL
    beside = {"p99_reused_permille_of_fresh": (r * 1000) // f, "p99_delta_us": r - f,
              "p50_delta_us": dv["reused"]["render_p50_us"] - dv["fresh"]["render_p50_us"],
              "composited_p50_delta_us": dv["reused"]["composited_p50_us"] - dv["fresh"]["composited_p50_us"]}
    return label, beside


def adoption(first_label: str, confirm_label: str) -> str:
    return "ADOPT" if first_label == PASS and confirm_label == PASS else "REJECT"


def seal_allocreuse1(raw: dict, reg: dict, host: str, session: dict, build: dict, confirm_of: dict | None = None,
                     host_state: dict | None = None, required_per_cell: int = REQUIRED_PER_CELL) -> tuple[dict, str]:
    d = check_raw(raw, required_per_cell)
    dv = {v: derive(d["variants"][v]) for v in VARIANTS}
    label, beside = performance(dv)
    verdict = adoption(confirm_of["original_label"], label) if confirm_of is not None else None
    data = dict(d)
    data["derived"] = {"variants": dv, "against_fresh": beside}
    data["rule"] = {"adopt_p99_permille_of_fresh": ADOPT_P99_PERMILLE, "required_per_cell": required_per_cell,
                    "runs_that_must_pass": 2, "margin": "an adoption margin (a declared decision threshold), not an uncertainty"}
    # the adoption is stated in the reading, never stored as a data key (RECORD-0 keeps verdicts out of data)
    # HOST-STATE-0 — recorded beside, attached only after the label and the verdict are fixed; no rule reads it
    data["host_state"] = host_state if host_state is not None else {"unavailable": "no host-state probe (a gate or synthetic seal)"}
    prov = {"tool": "shell allocreuse1-window (shell/allocreuse1.rs court over LATENCY-1R's GDI surface in FRAME-SPLIT-0's "
                    "window) + verify/allocreuse1.py",
            "surface": raw.get("provenance", {}).get("tool", ""), "host": host, "session": session, "build": build,
            "raw_unix_seconds": raw.get("provenance", {}).get("unix_seconds"),
            "python": platform.python_version(), "os": platform.system(), "machine": platform.machine(),
            "preregistered": {"rung": "ALLOC-REUSE-1", "chain_hash": reg["ALLOC-REUSE-1"]["chain_hash"]},
            "host_state_preregistered": {"rung": "HOST-STATE-0", "chain_hash": reg["HOST-STATE-0"]["chain_hash"]}}
    f, r = dv["fresh"], dv["reused"]
    reading = (f"ALLOC-REUSE-1 on host {host} ({d['samples_per_cell']} samples per cell, ABBA). Envelope p99 fresh "
               f"{f['render_p99_us']} us, reused {r['render_p99_us']} us ({beside['p99_reused_permille_of_fresh']} permille "
               f"of fresh; the rule: <= {ADOPT_P99_PERMILLE}). {label}. p50 fresh {f['render_p50_us']} us, reused "
               f"{r['render_p50_us']} us (beside, not the rule). Correctness held on every sample, or there would be no "
               f"record. One run adopts nothing: ADOPT needs this run and its --confirm to pass. An entry contract for a "
               f"render loop; no shipped window changes; not input-to-photon.")
    name = "verdandi-allocreuse1"
    if confirm_of is not None:
        name = "verdandi-allocreuse1-confirm"
        prov["confirms"] = confirm_of
        tail = ("ADOPT: the persistent-buffer LoopRenderer becomes the production entry for in-loop rendering (declared, "
                "with its call-site fence, in the following patch); the fresh path stays the frozen reference"
                if verdict == "ADOPT" else
                "REJECT: the LoopRenderer stays an unused candidate; ALLOC-REUSE-0's diagnostic stands")
        reading = (f"CONFIRMATION run — does NOT replace the sealed ALLOC-REUSE-1 record (chain {confirm_of['chain_hash'][:8]}). "
                   f"First run {confirm_of['original_label']}; this run {label}. ADOPTION: {tail}. ") + reading
    rec = envelope.seal(
        name, 1, "measured", prov,
        {"certifies": f"the fresh production path and the persistent-buffer render-loop entry on host {host}, uninstrumented "
                      f"envelopes interleaved ABBA, locked phase origin, {d['samples_per_cell']} samples per cell over "
                      f"{d['sequence_frames']} frames" + (" (a confirmation run)" if confirm_of is not None else ""),
         "host": host},
        ["that any shipped window got faster: run renders once and playback-window pre-renders frames that own their buffers",
         "an adoption from one run, from a comparator sealed in another run, or from the p50s",
         "that the fresh reference may be deleted or rewritten",
         "that the recorded host state explains or caused a number: HOST-STATE-0 is recorded beside and never read",
         "input-to-photon latency, or a comparison with any emit p99",
         "any other host, allocator, OS or buffer size"],
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
    ap.add_argument("--per-cell", type=int, default=REQUIRED_PER_CELL)
    ap.add_argument("--confirm", action="store_true")
    a = ap.parse_args()
    try:
        if a.per_cell != REQUIRED_PER_CELL:
            raise Refuse(f"ALLOC-REUSE-1 is registered at {REQUIRED_PER_CELL} samples per cell")
        reg = registry()
        name, confirm_of = f"allocreuse1-{a.host}.json", None
        if a.confirm:
            canon = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shell", "attest", name)
            if not os.path.exists(canon):
                raise Refuse(f"nothing to confirm — no sealed shell/attest/{name}; run without --confirm first")
            orig = envelope.read(canon)
            lab, _ = performance(orig["data"]["derived"]["variants"])
            confirm_of = {"of": f"shell/attest/{name}", "chain_hash": orig["chain_hash"], "original_label": lab}
            name = f"allocreuse1-confirm-{a.host}.json"
        probe: dict = {}
        raw, session, build = host_run("ALLOC-REUSE-1", "allocreuse1", a.host, a.session, a.per_cell, 2, probe=probe)
        missing = {"hoststate": "HOST-STATE-0", "version": 1, "unavailable": "not taken"}
        host_state = {"before": probe.get("before", missing), "after": probe.get("after", missing)}
        rec, label = seal_allocreuse1(raw, reg, a.host, session, build, confirm_of, host_state)
    except Refuse as e:
        print(f"REFUSE: {e}")
        return 2
    out = write_record(name, rec)
    dv = rec["data"]["derived"]
    print(f"[allocreuse1] {label} — envelope p99 fresh {dv['variants']['fresh']['render_p99_us']} us, reused "
          f"{dv['variants']['reused']['render_p99_us']} us ({dv['against_fresh']['p99_reused_permille_of_fresh']} permille "
          f"of fresh; the rule: <= {ADOPT_P99_PERMILLE})")
    if confirm_of is not None:
        print(f"[allocreuse1] ADOPTION: {adoption(confirm_of['original_label'], label)} (first run {confirm_of['original_label']}; "
              f"this run {label})")
    print(f"[allocreuse1] -> {os.path.relpath(out)}  (cites ALLOC-REUSE-1 {reg['ALLOC-REUSE-1']['chain_hash'][:8]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
