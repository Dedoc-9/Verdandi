# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
r"""drift.py — DRIFT-0: what variation is present within a run and between runs of the same workload (observational).

    python verify/drift.py --host NAME --sitting N --overlay off|on|unknown   # one run: seal it (or its refusal)
    python verify/drift.py --host NAME --report                               # the panel; writes nothing

The workload is the locked PRESENT-EXACT-0 court, unchanged: the same shell command, both calls, 1000 samples per
cell, the composed screen read back before and after, checked by PRESENT-EXACT-0's own sealer check. DRIFT-0 changes
repetition and observation only: 3 sittings of 4 completed runs, runs at least 60 s apart within a sitting, sittings at
least 4 h apart, the owner's declared overlay state (on, off or unknown: recorded, never verified), and HOST-STATE-1's
version 2 snapshot just before and just after each run. No intervention, no rule, no verdict, no threshold.

Every run is sealed. A completed run: shell/attest/drift-<host>-s<S>-r<R>.json, carrying the workload's numbers and
its within-run spread (p95 - p50 and p99 - p50 per call). A run whose court refuses:
shell/attest/drift-<host>-s<S>-x<K>.json, carrying the protocol, the host state and the fact of the refusal; it is
kept, never discarded, and does not count toward the sitting's four completed runs. The sealer enforces the protocol
(sitting order, four completed runs each, the spacing) before a run starts; it never looks at a number to decide.

The report prints, for every run, the per-call envelope p50/p95/p99, the within-run spread and the host state; then
per call the between-run spread of p50 and p99 (min, median, max, range) within each sitting, across all runs and
across the sittings' medians; the two sealed PRESENT-EXACT-0 runs are shown beside as history, never pooled. It joins
each run to the run ledger and the refusal log by time (the shell's unsealed observations) and prints what they hold.
It answers only: what variation is present, within a run and between runs, under the same workload.
"""
from __future__ import annotations

import argparse
import os
import platform
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envelope  # noqa: E402
import presentexact as PX  # noqa: E402
from diagcommon import CourtRefused, Refuse, host_run, registry, write_record  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATTEST = os.path.join(ROOT, "shell", "attest")
DEFAULT_SESSION = PX.DEFAULT_SESSION
WORKLOAD = "PRESENT-EXACT-0"
SITTINGS = 3
RUNS_PER_SITTING = 4
MIN_RUN_GAP_S = 60
MIN_SITTING_GAP_S = 4 * 3600
OVERLAY = ("on", "off", "unknown")
HOSTSTATE_VERSION = 2
DONE, REFUSED = "verdandi-drift", "verdandi-drift-refused"
STATS = ("render_p50_us", "render_p99_us")


# ------------------------------------------------------------------ the protocol (before a run; never reads a number)
def plan_next(records: list[dict], sitting: int, now: int) -> int:
    """The next completed run's number in `sitting`, or Refuse: sittings in order, four completed runs each, every run
    at least MIN_RUN_GAP_S after the previous one, a sitting's first run at least MIN_SITTING_GAP_S after the previous
    sitting's last. `records` are the host's sealed DRIFT-0 records (completed and refused)."""
    if sitting not in range(1, SITTINGS + 1):
        raise Refuse(f"DRIFT-SITTING: sitting {sitting} is not one of 1..{SITTINGS}")
    p = [r["data"]["protocol"] for r in records]
    done = lambda s: sum(1 for x, r in zip(p, records) if x["sitting"] == s and r["name"] == DONE)  # noqa: E731
    if any(x["sitting"] > sitting for x in p):
        raise Refuse(f"DRIFT-ORDER: a later sitting has already begun; sitting {sitting} is closed")
    if done(sitting) >= RUNS_PER_SITTING:
        raise Refuse(f"DRIFT-FULL: sitting {sitting} already holds its {RUNS_PER_SITTING} completed runs")
    if sitting > 1 and done(sitting - 1) < RUNS_PER_SITTING:
        raise Refuse(f"DRIFT-ORDER: sitting {sitting - 1} holds {done(sitting - 1)} of its {RUNS_PER_SITTING} completed runs")
    here = [x for x in p if x["sitting"] == sitting]
    if here:
        last = max(x["unix_seconds_end"] for x in here)
        if now - last < MIN_RUN_GAP_S:
            raise Refuse(f"DRIFT-SPACING: {now - last} s since the previous run; runs are at least {MIN_RUN_GAP_S} s apart")
    elif sitting > 1:
        last = max(x["unix_seconds_end"] for x in p if x["sitting"] == sitting - 1)
        if now - last < MIN_SITTING_GAP_S:
            raise Refuse(f"DRIFT-SPACING: {now - last} s since sitting {sitting - 1} ended; sittings are at least "
                         f"{MIN_SITTING_GAP_S} s apart")
    return done(sitting) + 1


def protocol(sitting: int, run: int, overlay: str, started: int, ended: int) -> dict:
    if overlay not in OVERLAY:
        raise Refuse(f"DRIFT-OVERLAY: the declared overlay state is one of {', '.join(OVERLAY)}")
    return {"sitting": sitting, "run_in_sitting": run, "sittings": SITTINGS, "runs_per_sitting": RUNS_PER_SITTING,
            "min_run_gap_s": MIN_RUN_GAP_S, "min_sitting_gap_s": MIN_SITTING_GAP_S, "overlay_declared": overlay,
            "unix_seconds_start": started, "unix_seconds_end": ended}


def within_run(dv: dict) -> dict:
    """p95 - p50 and p99 - p50 of the envelope, in microseconds and in permille of the p50."""
    p50 = max(dv["render_p50_us"], 1)
    a, b = dv["render_p95_us"] - dv["render_p50_us"], dv["render_p99_us"] - dv["render_p50_us"]
    return {"p95_minus_p50_us": a, "p99_minus_p50_us": b, "p95_minus_p50_permille": a * 1000 // p50,
            "p99_minus_p50_permille": b * 1000 // p50}


def _prov(reg: dict, host: str, extra: dict) -> dict:
    prov = {"tool": "shell presentexact-window (the locked PRESENT-EXACT-0 court, unchanged) + verify/drift.py",
            "host": host, "python": platform.python_version(), "os": platform.system(), "machine": platform.machine(),
            "preregistered": {"rung": "DRIFT-0", "chain_hash": reg["DRIFT-0"]["chain_hash"]},
            "workload": {"rung": WORKLOAD, "chain_hash": reg[WORKLOAD]["chain_hash"]},
            "host_state_preregistered": {"rung": "HOST-STATE-1", "chain_hash": reg["HOST-STATE-1"]["chain_hash"]}}
    prov.update(extra)
    return prov


FORBIDDEN = ["a verdict, a threshold or a stable/unstable reading: DRIFT-0 reports variation and decides nothing",
             "that the recorded host state or the declared overlay state caused, explains or corrects a number: "
             "association, never cause",
             "any adoption or rule reading: the workload's numbers are carried without PRESENT-EXACT-0's rule",
             "input-to-photon latency, or any host, screen or workload other than this one"]


def seal_drift(raw: dict, reg: dict, host: str, session: dict, build: dict, proto: dict,
               host_state: dict | None = None) -> dict:
    """A completed run: the workload's own check and derivation (PRESENT-EXACT-0's), the within-run spread, the
    protocol and the host state. No rule, no label."""
    d = PX.check_raw(raw)
    dv = {c: PX.derive(d["calls"][c]) for c in PX.CALLS}
    data = dict(d)
    data["derived"] = {"calls": dv, "within_run": {c: within_run(dv[c]) for c in PX.CALLS}}
    data["protocol"] = proto
    data["host_state"] = host_state if host_state is not None else {"unavailable": "no host-state probe (a gate or synthetic seal)"}
    s, t = dv["stretchdibits"], dv["setdibitstodevice"]
    reading = (f"DRIFT-0 sitting {proto['sitting']}, run {proto['run_in_sitting']} on host {host}: the locked PRESENT-EXACT-0 "
               f"court, unchanged ({d['samples_per_cell']} samples per cell, ABBA; the screen read back exact in all "
               f"{d['readback']['checks']} checks). Envelope p50/p99 SetDIBitsToDevice {t['render_p50_us']}/{t['render_p99_us']} "
               f"us, StretchDIBits {s['render_p50_us']}/{s['render_p99_us']} us. Overlay declared {proto['overlay_declared']}. "
               f"An observation: no rule, no verdict.")
    return envelope.seal(DONE, 1, "measured", _prov(reg, host, {"session": session, "build": build,
                                                                   "raw_unix_seconds": raw.get("provenance", {}).get("unix_seconds")}),
                         {"certifies": f"one run of the locked PRESENT-EXACT-0 court on host {host}, sealed as observed, with "
                                       f"the host state just before and just after it", "host": host},
                         FORBIDDEN, data, reading)


def seal_refused(reg: dict, host: str, proto: dict, why: str, host_state: dict | None = None) -> dict:
    """A run whose court refused: kept, never discarded. The refusal's code and what covered the screen are in the
    shell's refusal log, joined by time in the report."""
    data = {"protocol": proto, "refusal": why,
            "host_state": host_state if host_state is not None else {"unavailable": "no host-state probe (a gate or synthetic seal)"}}
    reading = (f"DRIFT-0 sitting {proto['sitting']} on host {host}: the court refused; the run is kept and does not count "
               f"toward the sitting's {RUNS_PER_SITTING} completed runs. Overlay declared {proto['overlay_declared']}.")
    return envelope.seal(REFUSED, 1, "measured", _prov(reg, host, {}),
                         {"certifies": f"one run of the locked PRESENT-EXACT-0 court on host {host} that refused", "host": host},
                         FORBIDDEN, data, reading)


def load(host: str, attest: str = ATTEST) -> list[dict]:
    if not os.path.isdir(attest):
        return []
    out = []
    for f in sorted(os.listdir(attest)):
        if f.startswith(f"drift-{host}-s") and f.endswith(".json"):
            out.append(envelope.read(os.path.join(attest, f)))
    return sorted(out, key=lambda r: r["data"]["protocol"]["unix_seconds_start"])


# ------------------------------------------------------------------ the panel (reads; writes nothing)
def _median(xs: list[int]) -> int:
    ys = sorted(xs)
    return ys[(len(ys) - 1) // 2]  # the lower median for an even count


def spread(xs: list[int]) -> dict:
    if not xs:
        return {}
    m = _median(xs)
    return {"n": len(xs), "min": min(xs), "median": m, "max": max(xs), "range": max(xs) - min(xs),
            "range_permille_of_median": (max(xs) - min(xs)) * 1000 // max(m, 1)}


def _hs(snap: dict) -> str:
    f = snap.get("fields", {}) if isinstance(snap, dict) else {}
    def g(field, key):
        v = f.get(field, {}).get(key) if isinstance(f.get(field), dict) else None
        return "-" if v is None or isinstance(v, dict) else str(v)
    return ("mem %s%% avail %s MB, busy %s‰, perf %s‰ util %s‰ freq %s, hard faults %s/s"
            % (g("memory", "load_percent"), g("memory", "available_mb"), g("load", "cpu_busy_permille"),
               g("clock", "performance_permille"), g("clock", "utility_permille"), g("clock", "processor_frequency_mhz"),
               g("faults", "page_reads_per_s")))


def report(host: str, records: list[dict], history: list[dict], ledger: list[dict], refusals: list[dict]) -> list[str]:
    """The panel: every run, the within-run spread, the between-run spread within and across sittings, the history
    beside, and the shell's observations joined by time. Descriptive only."""
    out = [f"DRIFT-0 on host {host}: {sum(r['name'] == DONE for r in records)} completed run(s), "
           f"{sum(r['name'] == REFUSED for r in records)} refused, of {SITTINGS} x {RUNS_PER_SITTING} completed runs"]
    for r in records:
        p = r["data"]["protocol"]
        hs = r["data"]["host_state"]
        head = f"  s{p['sitting']} {'r%d' % p['run_in_sitting'] if r['name'] == DONE else 'refused'} overlay={p['overlay_declared']}"
        if r["name"] == DONE:
            for c in PX.CALLS:
                dv, w = r["data"]["derived"]["calls"][c], r["data"]["derived"]["within_run"][c]
                out.append(f"{head} {c:18s} p50 {dv['render_p50_us']} p95 {dv['render_p95_us']} p99 {dv['render_p99_us']} us; "
                           f"within-run p95-p50 {w['p95_minus_p50_us']} us ({w['p95_minus_p50_permille']}‰), "
                           f"p99-p50 {w['p99_minus_p50_us']} us ({w['p99_minus_p50_permille']}‰)")
        else:
            out.append(f"{head} {r['data']['refusal']}")
        out.append(f"      host before: {_hs(hs.get('before', {}))}; after: {_hs(hs.get('after', {}))}")
        lo, hi = p["unix_seconds_start"] * 1000, (p["unix_seconds_end"] + 1) * 1000
        lines = [x for x in ledger if x["operation"] == "presentexact.court" and x["surface"] == "gdi"
                 and lo <= x["unix_ms_start"] and x["unix_ms_end"] <= hi]
        out.append("      ledger: " + ("; ".join(f"exit={x['exit_code']} readbacks={x['readbacks_checked']} differed={x['differed']} "
                                         f"refusals={x['refusals']}" for x in lines) or "no line in the run's window"))
        for x in refusals:
            if x["operation"] == "presentexact.court" and x["surface"] == "gdi" and lo <= x["unix_ms"] <= hi:
                c = x["context"]
                cov = "; ".join(f"{c['window_%d_program' % i]} | {c['window_%d_class' % i]} | {c['window_%d_flags' % i]}"
                                for i in range(1, 7) if "window_%d_program" % i in c)
                out.append(f"      refusal: {x['reason_code']} / {x['attribution']}"
                           + (f"; covering {c.get('covering_layer')}" if "covering_layer" in c else "") + (f": {cov}" if cov else ""))
    done = [r for r in records if r["name"] == DONE]
    for c in PX.CALLS:
        for stat in STATS:
            vals = [r["data"]["derived"]["calls"][c][stat] for r in done]
            if not vals:
                continue
            a = spread(vals)
            out.append(f"  between runs, {c} {stat}: min {a['min']} median {a['median']} max {a['max']} range {a['range']} us "
                       f"({a['range_permille_of_median']}‰ of the median), {a['n']} runs")
            meds = []
            for s in range(1, SITTINGS + 1):
                sv = [r["data"]["derived"]["calls"][c][stat] for r in done if r["data"]["protocol"]["sitting"] == s]
                if sv:
                    b = spread(sv)
                    meds.append(b["median"])
                    out.append(f"    within sitting {s}: min {b['min']} median {b['median']} max {b['max']} range {b['range']} us, {b['n']} runs")
            if len(meds) > 1:
                m = spread(meds)
                out.append(f"    between sittings (their medians): min {m['min']} median {m['median']} max {m['max']} range {m['range']} us")
        w = [r["data"]["derived"]["within_run"][c]["p99_minus_p50_us"] for r in done]
        if w:
            a = spread(w)
            out.append(f"  within runs, {c} p99-p50: min {a['min']} median {a['median']} max {a['max']} us across {a['n']} runs")
    for h in history:
        dv = h["data"]["derived"]["calls"]
        out.append(f"  history (beside, not pooled): {h['name']} p50/p99 SetDIBitsToDevice {dv['setdibitstodevice']['render_p50_us']}/"
                   f"{dv['setdibitstodevice']['render_p99_us']} us, StretchDIBits {dv['stretchdibits']['render_p50_us']}/"
                   f"{dv['stretchdibits']['render_p99_us']} us")
    out.append("an observation: no verdict, no threshold; variation beside host state is association, never cause")
    return out


def main() -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--sitting", type=int)
    ap.add_argument("--overlay", choices=OVERLAY)
    ap.add_argument("--session", default=DEFAULT_SESSION)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.report:
        import refusallog
        import runledger
        history = [envelope.read(os.path.join(ATTEST, f)) for f in (f"presentexact-{a.host}.json", f"presentexact-confirm-{a.host}.json")
                   if os.path.exists(os.path.join(ATTEST, f))]
        ledger, _ = runledger.read(runledger.default_path())
        refusals, _ = refusallog.read(refusallog.default_path())
        for ln in report(a.host, load(a.host), history, ledger, refusals):
            print(ln)
        return 0
    try:
        if a.sitting is None or a.overlay is None:
            raise Refuse("a run needs --sitting N and --overlay on|off|unknown")
        reg = registry()
        records = load(a.host)
        run = plan_next(records, a.sitting, int(time.time()))
        protocol(a.sitting, run, a.overlay, 0, 0)
        probe: dict = {}
        started = int(time.time())
        missing = {"hoststate": "HOST-STATE-1", "version": HOSTSTATE_VERSION, "unavailable": "not taken"}
        try:
            raw, session, build = host_run("DRIFT-0", "presentexact", a.host, a.session, PX.REQUIRED_PER_CELL, 2, probe=probe,
                                           hoststate_version=HOSTSTATE_VERSION)
        except CourtRefused as e:
            host_state = {"before": probe.get("before", missing), "after": probe.get("after", missing)}
            proto = protocol(a.sitting, 0, a.overlay, started, int(time.time()))
            k = 1 + sum(1 for r in records if r["name"] == REFUSED and r["data"]["protocol"]["sitting"] == a.sitting)
            out = write_record(f"drift-{a.host}-s{a.sitting}-x{k}.json", seal_refused(reg, a.host, proto, str(e), host_state))
            print(f"[drift] the court refused; the run is kept -> {os.path.relpath(out)}")
            return 2
        host_state = {"before": probe.get("before", missing), "after": probe.get("after", missing)}
        proto = protocol(a.sitting, run, a.overlay, started, int(time.time()))
        rec = seal_drift(raw, reg, a.host, session, build, proto, host_state)
    except Refuse as e:
        print(f"REFUSE: {e}")
        return 2
    out = write_record(f"drift-{a.host}-s{a.sitting}-r{run}.json", rec)
    t = rec["data"]["derived"]["calls"]["setdibitstodevice"]
    print(f"[drift] sitting {a.sitting}, run {run}: SetDIBitsToDevice p50/p99 {t['render_p50_us']}/{t['render_p99_us']} us "
          f"-> {os.path.relpath(out)}  (cites DRIFT-0 {reg['DRIFT-0']['chain_hash'][:8]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
