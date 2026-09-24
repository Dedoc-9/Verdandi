# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""seal_sessionwalk.py — seal a canonical interleaved session-walk under RECORD-0 (a reference-session attestation).

    python verify/seal_sessionwalk.py --camera 28,28,N \
        --events "edit:cell:28,27,.;move:F;move:F;edit:tile:floor,96,80,64;move:L;move:F" \
        --out workshop/attest/sessionwalk-demo.json

The head of a session-walk is a pure function of the frozen authority and the ordered event log — no clock, no
host variance — so the record is `established`, the same on any host. The seal wraps the session the binary
wrote (its base, its interleaved log with per-event witnesses, and the single head) in RECORD-0's envelope, the
way every other record is anchored. The gate's sessionwalk-demo row re-derives the head with `verify` and a
Python twin.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "verify"))
import envelope  # noqa: E402


def build_input() -> tuple[str, str]:
    rustc = shutil.which("rustc")
    if rustc is None:
        print("REFUSE: rustc not found — cannot build workshop/sessionwalk.rs")
        raise SystemExit(2)
    tmp = tempfile.mkdtemp(prefix="seal-sw-")
    exe = os.path.join(tmp, "sessionwalk")
    cp = subprocess.run([rustc, "-O", os.path.join(ROOT, "workshop", "sessionwalk.rs"), "-o", exe],
                        capture_output=True, text=True)
    if cp.returncode != 0:
        print("REFUSE: rustc failed: " + cp.stderr.strip().splitlines()[0])
        shutil.rmtree(tmp, ignore_errors=True)
        raise SystemExit(2)
    return exe, tmp


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", required=True)
    ap.add_argument("--events", required=True, help="semicolon list: move:F | edit:cell:X,Z,C | edit:tile:CLASS,R,G,B")
    ap.add_argument("--level", default="oracle/levels/witness.lvl")
    ap.add_argument("--tiles", default="oracle/tiles/identity.tiles")
    ap.add_argument("--out", default=os.path.join("workshop", "attest", "sessionwalk-demo.json"))
    a = ap.parse_args()

    exe, tmp = build_input()
    try:
        sp = os.path.join(tmp, "session.json")
        lp, tp = os.path.join(ROOT, a.level), os.path.join(ROOT, a.tiles)
        cp = subprocess.run([exe, "new", "--level", lp, "--tiles", tp, "--camera", a.camera, "--out", sp],
                            capture_output=True, text=True)
        if cp.returncode != 0:
            print("REFUSE: new failed: " + cp.stderr.strip())
            return 2
        for token in a.events.split(";"):
            token = token.strip()
            if not token:
                continue
            kind, param = token.split(":", 1)
            if kind == "move":
                args = ["move", "--session", sp, "--command", param]
            elif kind == "edit":
                args = ["edit", "--session", sp, "--edit", param]
            else:
                print("REFUSE: unknown event kind " + kind)
                return 2
            cp = subprocess.run([exe] + args, capture_output=True, text=True)
            if cp.returncode != 0:
                print("REFUSE: %s failed: %s" % (token, cp.stderr.strip()))
                return 2
        with open(sp, encoding="utf-8") as fh:
            session = json.load(fh)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    d = session["data"]
    base = d["base"]
    rec = envelope.seal(
        "verdandi-session-walk", 1, "established",
        {"tool": "workshop/sessionwalk.rs + verify/seal_sessionwalk.py", "oracle_authority": "witness/identity, frozen from Urðr"},
        {"certifies": "a fixed interleaved session (%d moves, %d edits from camera %s) over the frozen authority (W %s… M %s…) "
                      "replays, in log order, to this head; every event's witness (a frame digest for a move, a content digest for "
                      "an edit) and the single fold are reproducible on any host"
                      % (d["moves"], d["edits"], base["camera"], base["W"][:12], base["M"][:12]),
         "W": base["W"], "M": base["M"], "head": d["head"], "final_camera": d["final_camera"]},
        ["a wall-clock or any timing (a session-walk carries no time; the 144Hz/batch scheduler is a LATENCY-0 hypothesis, not this)",
         "two independent authorities (walk_head and edit_head are DERIVED projections of this one interleaved chain, never sealed apart)",
         "a skybox or physics (the log holds only cell/tile edits and camera moves the frozen oracle certifies)",
         "a predicted consequence (each witness is MEASURED at the event, never declared at queue time)",
         "tamper-proofing beyond replay: the chain catches a changed event under replay and is anchored by this seal and by git"],
        d, "")
    out = os.path.join(ROOT, a.out)
    envelope.write(out, rec)
    print("[seal] %s sealed; %d moves + %d edits from %s; final %s; head %s; chain %s"
          % (os.path.relpath(out, ROOT), d["moves"], d["edits"], base["camera"], d["final_camera"], d["head"][:12], rec["chain_hash"][:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
