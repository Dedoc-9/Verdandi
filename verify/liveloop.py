# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""liveloop.py — LIVE-LOOP-0: the sealed session walked live, every composition rendered and presented (off-gate, host).

    python verify/liveloop.py --host NAME [--session workshop/attest/sessionwalk-demo.json]

The first per-frame loop in the shipped shell. The state is the sealed session's, stepped at a fixed dwell (24
compositions per step), the last step held for 150 compositions; every composition is rendered through the adopted
LoopRenderer from the current step, compared with that step's verified bytes, and presented by SetDIBitsToDevice in
the presenter's borderless 1920x1080 window at (0,0). The composed screen is read back on the first composition of
every step and every 75th composition of the hold; a differing screen is counted and logged, and the loop goes on.
No authoring input, no camera, no clock, no latency claim: counts only.

The sealer checks the raw record's counts against the registered walk (steps x 24 + 150 compositions, each rendered,
byte-checked and presented; steps + 2 screen readbacks), the geometry, the fixed call and entry, and that the sealed
session file's hash is the same before and after the run, then writes shell/attest/liveloop-<host>.json citing
LIVE-LOOP-0. The reading says whether the screen was exact at every readback.
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
DWELL, HOLD, RECHECK = 24, 150, 75
TARGET = [1920, 1080]


def readbacks_for(steps: int) -> int:
    """The registered number of screen readbacks: one per step, and one every RECHECK compositions of the hold."""
    return steps + HOLD // RECHECK


def _int(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def check_raw(raw: dict) -> dict:
    if raw.get("name") != "verdandi-liveloop":
        raise Refuse("not a verdandi-liveloop record")
    d = raw.get("data", {})
    steps = d.get("steps")
    if not _int(steps) or steps < 1:
        raise Refuse("the walk has no steps")
    if (d.get("dwell"), d.get("hold"), d.get("recheck")) != (DWELL, HOLD, RECHECK):
        raise Refuse("the dwell, hold or recheck is not the registered one")
    total = steps * DWELL + HOLD
    if not all(_int(d.get(k)) for k in ("compositions", "frames_rendered", "frames_presented", "byte_checks", "loop_renders",
                                         "screen_readbacks", "screen_differed")):
        raise Refuse("a count is not an integer")
    if (d["compositions"], d["frames_rendered"], d["frames_presented"], d["byte_checks"], d["loop_renders"]) != (total,) * 5:
        raise Refuse(f"the walk is not {total} compositions, each rendered through the loop, byte-checked and presented")
    if d["screen_readbacks"] != readbacks_for(steps) or not 0 <= d["screen_differed"] <= d["screen_readbacks"]:
        raise Refuse("the screen was not read back on every step and in the hold as registered")
    g = d.get("geometry", {})
    if (g.get("client"), g.get("origin"), g.get("screen_logical"), g.get("screen_physical"), g.get("source")) != \
            (TARGET, [0, 0], TARGET, TARGET, TARGET):
        raise Refuse("the geometry is not the certified frame 1:1 at (0,0) on a 1920x1080 screen")
    if (d.get("call"), d.get("render_entry")) != ("setdibitstodevice", "LoopRenderer"):
        raise Refuse("the call is not SetDIBitsToDevice or the entry is not the LoopRenderer")
    s = d.get("session", {})
    if not s.get("sha256_before") or s.get("sha256_before") != s.get("sha256_after"):
        raise Refuse("the sealed session file changed during the run (or its hash is missing)")
    return d


def seal_liveloop(raw: dict, reg: dict, host: str, session: dict, build: dict) -> dict:
    d = check_raw(raw)
    exact = d["screen_differed"] == 0
    screen = ("the composed screen read back exact at every one of its %d readbacks" % d["screen_readbacks"] if exact else
              "the composed screen differed at %d of its %d readbacks (each counted and logged; the loop went on)"
              % (d["screen_differed"], d["screen_readbacks"]))
    reading = (f"LIVE-LOOP-0 on host {host}: the sealed session's {d['steps']} steps walked live — {d['compositions']} "
               f"compositions, each rendered through the LoopRenderer from the current step, byte-checked against the "
               f"step's verified bytes and presented by SetDIBitsToDevice; {screen}; the session file unchanged "
               f"(sha256 {d['session']['sha256_before'][:12]}...). Counts only: no timing, no latency claim.")
    prov = {"tool": "shell liveloop-window (shell/liveloop.rs over the borderless 1:1 GDI window, appended to shell/win32.rs) "
                    "+ verify/liveloop.py",
            "surface": raw.get("provenance", {}).get("tool", ""), "host": host, "session": session, "build": build,
            "raw_unix_seconds": raw.get("provenance", {}).get("unix_seconds"),
            "python": platform.python_version(), "os": platform.system(), "machine": platform.machine(),
            "preregistered": {"rung": "LIVE-LOOP-0", "chain_hash": reg["LIVE-LOOP-0"]["chain_hash"]},
            "presenter": {"rung": "PRESENT-EXACT-0", "chain_hash": reg["PRESENT-EXACT-0"]["chain_hash"]}}
    return envelope.seal(
        "verdandi-liveloop", 1, "measured", prov,
        {"certifies": f"the sealed session walked live on host {host}: {d['steps']} steps x {DWELL} compositions + {HOLD} held, "
                      f"every composition rendered through the LoopRenderer from the current step and presented by "
                      f"SetDIBitsToDevice in a borderless 1920x1080 window at (0,0), the screen read back at every step",
         "host": host},
        ["any timing or latency: the run takes no clock",
         "that the screen was exact between readbacks: the byte check covers what the loop handed the call, the readback "
         "what reached the composed screen at its compositions only",
         "that a held readback distinguishes a fresh present from a stale one: the loop does not clear between compositions",
         "authoring, input or camera control: the state is the sealed session's steps",
         "input-to-photon latency, or any other host, screen size, scaling setting or GPU driver"],
        dict(d), reading)


def main() -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--session", default=DEFAULT_SESSION)
    a = ap.parse_args()
    try:
        reg = registry()
        raw, session, build = host_run("LIVE-LOOP-0", "liveloop", a.host, a.session, 0, 0)
        rec = seal_liveloop(raw, reg, a.host, session, build)
    except Refuse as e:
        print(f"REFUSE: {e}")
        return 2
    out = write_record(f"liveloop-{a.host}.json", rec)
    d = rec["data"]
    print(f"[liveloop] {d['compositions']} compositions rendered and presented; screen readbacks {d['screen_readbacks']}, "
          f"differed {d['screen_differed']} -> {os.path.relpath(out)}  (cites LIVE-LOOP-0 {reg['LIVE-LOOP-0']['chain_hash'][:8]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
