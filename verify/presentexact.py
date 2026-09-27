# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""presentexact.py — PRESENT-EXACT-0: which GDI call presents the certified picture 1:1 (off-gate, host).

    python verify/presentexact.py --host NAME [--session workshop/attest/sessionwalk-demo.json] [--confirm]

PRESENTATION-CHOICE-0 (declared) fixed the target: the certified 1920x1080 composite, pixel for pixel, in a borderless
window covering the 1920x1080 screen at (0,0). This court implements it with two GDI calls, the call the only
variable: StretchDIBits at 1:1 and SetDIBitsToDevice. Frames render through the adopted LoopRenderer.

The pixel check is a HARD GATE, not a number: before the clock, for every sealed frame and each call, the window is
cleared to white (read back as white), the call presents the frame, and the composed screen under the window is read
back and must equal the certified blit bytes, byte for byte; after the court the last frame is checked again under
each call. Any mismatch, or a geometry other than a 1920x1080 client at (0,0) on a 1920x1080 screen (logical and
physical), refuses the court with no record.

The preregistered performance reading, on the envelope render-start -> frame-ready, the two calls interleaved ABBA in
the same run after 10 warm-up rounds, 1000 samples per cell:

    STRETCHDIBITS CHEAPER        iff  p99(StretchDIBits)     <= 950 permille x p99(SetDIBitsToDevice)
    SETDIBITSTODEVICE CHEAPER    iff  p99(SetDIBitsToDevice) <= 950 permille x p99(StretchDIBits)
    NO MATERIAL DIFFERENCE       otherwise

The adoption, read by --confirm: STRETCHDIBITS iff the run and its confirmation both read STRETCHDIBITS CHEAPER;
otherwise SETDIBITSTODEVICE, the simpler semantics (no stretch path at all). The 50 permille is an adoption margin, a
declared decision threshold, not an uncertainty. p50s, the call interval and frame-ready -> composited are reported
beside, never ruled on. HOST-STATE-0 snapshots are recorded beside and never read. Writes
shell/attest/presentexact-<host>.json (and presentexact-confirm-<host>.json) citing PRESENT-EXACT-0.
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
CALLS = ("stretchdibits", "setdibitstodevice")
PCT = ("p50", "p95", "p99", "max")
REQUIRED_PER_CELL = 1000
WARM_ROUNDS = 10
TAIL = 12
MARGIN_PERMILLE = 950
TARGET = [1920, 1080]
STRETCH, SETDIB, NEITHER = "STRETCHDIBITS CHEAPER", "SETDIBITSTODEVICE CHEAPER", "NO MATERIAL DIFFERENCE"


def _pct(x) -> bool:
    return (isinstance(x, dict) and all(isinstance(x.get(k), int) and not isinstance(x.get(k), bool) for k in PCT)
            and x["p50"] <= x["p95"] <= x["p99"] <= x["max"])


def check_raw(raw: dict, required_per_cell: int = REQUIRED_PER_CELL) -> dict:
    if raw.get("name") != "verdandi-presentexact":
        raise Refuse("not a verdandi-presentexact record")
    d = raw.get("data", {})
    g = d.get("geometry", {})
    if (g.get("client"), g.get("origin"), g.get("screen_logical"), g.get("screen_physical"), g.get("source")) != \
            (TARGET, [0, 0], TARGET, TARGET, TARGET):
        raise Refuse("the geometry is not the certified frame 1:1 at (0,0) on a 1920x1080 screen")
    rb = d.get("readback", {})
    n_frames = d.get("sequence_frames")
    if (not isinstance(n_frames, int) or rb.get("frames") != n_frames or rb.get("checks") != 2 * n_frames + 2
            or rb.get("bytes_compared") != rb.get("checks", 0) * TARGET[0] * TARGET[1] * 3 or rb.get("mismatched_bytes") != 0):
        raise Refuse("the screen readback did not check every sealed frame and the closing frame under both calls with no mismatch")
    if (d.get("block_order"), d.get("warm_rounds"), d.get("phase_origin"), d.get("production_threads"),
            d.get("render_entry")) != ("ABBA", WARM_ROUNDS, "locked", 8, "LoopRenderer"):
        raise Refuse("the block order, warm-up, phase origin, production T or render entry is not the registered one")
    n = d.get("samples_per_cell")
    if n != required_per_cell:
        raise Refuse(f"the run has {n} samples per cell; PRESENT-EXACT-0 is registered at {required_per_cell}")
    if tuple(d.get("calls", {}).keys()) != CALLS:
        raise Refuse("the calls are not StretchDIBits and SetDIBitsToDevice, in order")
    for c in CALLS:
        cd = d["calls"][c]
        env = cd.get("envelope", {})
        if env.get("samples") != n:
            raise Refuse(f"{c}: the cell is missing or partial")
        if not (_pct(env.get("render_us")) and _pct(env.get("call_us")) and _pct(env.get("present_us"))):
            raise Refuse(f"{c}: the intervals are not integer, ordered p50/p95/p99/max")
        t = cd.get("tail_render_us")
        if (not isinstance(t, list) or len(t) != min(TAIL, n) or not all(isinstance(x, int) for x in t)
                or t != sorted(t, reverse=True) or t[0] != env["render_us"]["max"]):
            raise Refuse(f"{c}: the tail is not the {TAIL} largest samples, largest first")
    if not isinstance(d.get("loop_renders"), int) or d["loop_renders"] < 2 * (n + WARM_ROUNDS):
        raise Refuse("the loop renderer did not render every warm-up and recorded sample")
    return d


def derive(cd: dict) -> dict:
    env = cd["envelope"]
    return {"render_p50_us": env["render_us"]["p50"], "render_p95_us": env["render_us"]["p95"],
            "render_p99_us": env["render_us"]["p99"], "render_max_us": env["render_us"]["max"],
            "call_p50_us": env["call_us"]["p50"], "call_p99_us": env["call_us"]["p99"],
            "composited_p50_us": env["present_us"]["p50"], "composited_p99_us": env["present_us"]["p99"],
            "tail_render_us": list(cd["tail_render_us"])}


def performance(dv: dict) -> tuple[str, dict]:
    """The preregistered rule. It reads the two calls' derived envelopes and nothing else."""
    s, d = dv["stretchdibits"]["render_p99_us"], dv["setdibitstodevice"]["render_p99_us"]
    if s <= 0 or d <= 0:
        raise Refuse("a zero p99; no ratio can be formed")
    if s * 1000 <= MARGIN_PERMILLE * d:
        label = STRETCH
    elif d * 1000 <= MARGIN_PERMILLE * s:
        label = SETDIB
    else:
        label = NEITHER
    beside = {"p99_stretch_permille_of_setdib": (s * 1000) // d, "p99_setdib_permille_of_stretch": (d * 1000) // s,
              "p50_stretch_minus_setdib_us": dv["stretchdibits"]["render_p50_us"] - dv["setdibitstodevice"]["render_p50_us"],
              "call_p50_stretch_minus_setdib_us": dv["stretchdibits"]["call_p50_us"] - dv["setdibitstodevice"]["call_p50_us"]}
    return label, beside


def adoption(first_label: str, confirm_label: str) -> str:
    return "STRETCHDIBITS" if first_label == STRETCH and confirm_label == STRETCH else "SETDIBITSTODEVICE"


def seal_presentexact(raw: dict, reg: dict, host: str, session: dict, build: dict, confirm_of: dict | None = None,
                      host_state: dict | None = None, required_per_cell: int = REQUIRED_PER_CELL) -> tuple[dict, str]:
    d = check_raw(raw, required_per_cell)
    dv = {c: derive(d["calls"][c]) for c in CALLS}
    label, beside = performance(dv)
    adopted = adoption(confirm_of["original_label"], label) if confirm_of is not None else None
    data = dict(d)
    data["derived"] = {"calls": dv, "between_calls": beside}
    data["rule"] = {"margin_permille": MARGIN_PERMILLE, "required_per_cell": required_per_cell, "runs": 2,
                    "default_call": "setdibitstodevice", "margin": "an adoption margin (a declared decision threshold), not an uncertainty"}
    # the adopted call is stated in the reading, never stored as a data key (RECORD-0 keeps verdicts out of data)
    # HOST-STATE-0 — recorded beside, attached only after the label and the adoption are fixed; no rule reads it
    data["host_state"] = host_state if host_state is not None else {"unavailable": "no host-state probe (a gate or synthetic seal)"}
    prov = {"tool": "shell presentexact-window (shell/presentexact.rs court over the borderless 1:1 GDI window with screen "
                    "readback, appended to shell/win32.rs) + verify/presentexact.py",
            "surface": raw.get("provenance", {}).get("tool", ""), "host": host, "session": session, "build": build,
            "raw_unix_seconds": raw.get("provenance", {}).get("unix_seconds"),
            "python": platform.python_version(), "os": platform.system(), "machine": platform.machine(),
            "preregistered": {"rung": "PRESENT-EXACT-0", "chain_hash": reg["PRESENT-EXACT-0"]["chain_hash"]},
            "presentation_choice": {"rung": "PRESENTATION-CHOICE-0", "chain_hash": reg["PRESENTATION-CHOICE-0"]["chain_hash"]},
            "host_state_preregistered": {"rung": "HOST-STATE-0", "chain_hash": reg["HOST-STATE-0"]["chain_hash"]}}
    s, t = dv["stretchdibits"], dv["setdibitstodevice"]
    rb = d["readback"]
    reading = (f"PRESENT-EXACT-0 on host {host} ({d['samples_per_cell']} samples per cell, ABBA). The composed screen read "
               f"back equal to the certified picture in all {rb['checks']} checks ({rb['bytes_compared']} bytes, 0 differing), "
               f"under both calls, in a borderless 1920x1080 window at (0,0). Envelope p99 StretchDIBits {s['render_p99_us']} "
               f"us, SetDIBitsToDevice {t['render_p99_us']} us: {label} (the margin: 950 permille). p50 StretchDIBits "
               f"{s['render_p50_us']} us, SetDIBitsToDevice {t['render_p50_us']} us (beside, not the rule). One run adopts "
               f"nothing: the adoption is read on --confirm. Not input-to-photon.")
    name = "verdandi-presentexact"
    if confirm_of is not None:
        name = "verdandi-presentexact-confirm"
        prov["confirms"] = confirm_of
        why = ("both runs read StretchDIBits cheaper by the margin" if adopted == "STRETCHDIBITS" else
               "StretchDIBits was not cheaper by the margin in both runs, so the simpler call is adopted")
        reading = (f"CONFIRMATION run — does NOT replace the sealed PRESENT-EXACT-0 record (chain {confirm_of['chain_hash'][:8]}). "
                   f"First run {confirm_of['original_label']}; this run {label}. ADOPTED CALL: {adopted} ({why}); the shell's "
                   f"1:1 presentation is locked to it in the following patch. ") + reading
    rec = envelope.seal(
        name, 1, "measured", prov,
        {"certifies": f"the certified composite presented 1:1 by StretchDIBits and by SetDIBitsToDevice in a borderless "
                      f"1920x1080 window at the screen's origin on host {host}, the composed screen read back before and "
                      f"after the court, uninstrumented envelopes interleaved ABBA, locked phase origin, "
                      f"{d['samples_per_cell']} samples per cell over {d['sequence_frames']} frames"
                      + (" (a confirmation run)" if confirm_of is not None else ""),
         "host": host},
        ["that the pixels reach the eye unchanged: the readback is the composed screen, before scan-out, the panel and any "
         "display-side colour processing",
         "that the readback holds between the checked frames: it is taken on the sealed frames before the clock and on the "
         "last frame after it, not on every sample",
         "an adoption from one run, from a comparator sealed in another run, or from the p50s",
         "that the recorded host state explains or caused a number: HOST-STATE-0 is recorded beside and never read",
         "input-to-photon latency, or a comparison with any emit p99",
         "any other host, screen size, scaling setting or GPU driver"],
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
            raise Refuse(f"PRESENT-EXACT-0 is registered at {REQUIRED_PER_CELL} samples per cell")
        reg = registry()
        name, confirm_of = f"presentexact-{a.host}.json", None
        if a.confirm:
            canon = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shell", "attest", name)
            if not os.path.exists(canon):
                raise Refuse(f"nothing to confirm — no sealed shell/attest/{name}; run without --confirm first")
            orig = envelope.read(canon)
            lab, _ = performance(orig["data"]["derived"]["calls"])
            confirm_of = {"of": f"shell/attest/{name}", "chain_hash": orig["chain_hash"], "original_label": lab}
            name = f"presentexact-confirm-{a.host}.json"
        probe: dict = {}
        raw, session, build = host_run("PRESENT-EXACT-0", "presentexact", a.host, a.session, a.per_cell, 2, probe=probe)
        missing = {"hoststate": "HOST-STATE-0", "version": 1, "unavailable": "not taken"}
        host_state = {"before": probe.get("before", missing), "after": probe.get("after", missing)}
        rec, label = seal_presentexact(raw, reg, a.host, session, build, confirm_of, host_state)
    except Refuse as e:
        print(f"REFUSE: {e}")
        return 2
    out = write_record(name, rec)
    dv = rec["data"]["derived"]["calls"]
    rb = rec["data"]["readback"]
    print(f"[presentexact] screen readback: {rb['checks']} checks, {rb['mismatched_bytes']} differing bytes")
    print(f"[presentexact] {label} — envelope p99 StretchDIBits {dv['stretchdibits']['render_p99_us']} us, SetDIBitsToDevice "
          f"{dv['setdibitstodevice']['render_p99_us']} us (the margin: 950 permille)")
    if confirm_of is not None:
        print(f"[presentexact] ADOPTED CALL: {adoption(confirm_of['original_label'], label)} (first run "
              f"{confirm_of['original_label']}; this run {label})")
    print(f"[presentexact] -> {os.path.relpath(out)}  (cites PRESENT-EXACT-0 {reg['PRESENT-EXACT-0']['chain_hash'][:8]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
