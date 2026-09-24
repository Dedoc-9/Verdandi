# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""seal_walk.py — seal a canonical camera walk under RECORD-0's envelope (a reference-trajectory attestation).

    python verify/seal_walk.py --camera 34,28,W --commands LFFRFFBQE \
        --level oracle/levels/witness.lvl --tiles oracle/tiles/identity.tiles \
        --out workshop/attest/walk-demo.json

A walk head is a pure function of the frozen authority and the command log — no wall-clock, no host variance —
so the record is `established`, not `measured`: it is the same on any host. The seal anchors the reference
trajectory (its final camera, step and blocked counts, and the head hash chain) the same way as every other
record; `input verify` re-derives the head, and the gate's input-demo row cross-checks it with a Python twin.
The camera is projection-owned (WORKSHOP-0b), so the walk names, in its forbidden readings, that it never
touches W or M.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "verify"))
import envelope  # noqa: E402


def sha256_file(path: str) -> str:
    import hashlib

    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def build_input() -> tuple[str, str]:
    rustc = shutil.which("rustc")
    if rustc is None:
        print("REFUSE: rustc not found — cannot build workshop/input.rs")
        raise SystemExit(2)
    tmp = tempfile.mkdtemp(prefix="seal-walk-")
    exe = os.path.join(tmp, "input")
    cp = subprocess.run([rustc, "-O", os.path.join(ROOT, "workshop", "input.rs"), "-o", exe],
                        capture_output=True, text=True)
    if cp.returncode != 0:
        print("REFUSE: rustc failed: " + cp.stderr.strip().splitlines()[0])
        shutil.rmtree(tmp, ignore_errors=True)
        raise SystemExit(2)
    return exe, tmp


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", required=True)
    ap.add_argument("--commands", required=True)
    ap.add_argument("--level", default="oracle/levels/witness.lvl")
    ap.add_argument("--tiles", default="oracle/tiles/identity.tiles")
    ap.add_argument("--out", default=os.path.join("workshop", "attest", "walk-demo.json"))
    a = ap.parse_args()

    exe, tmp = build_input()
    try:
        lp = os.path.join(ROOT, a.level)
        tp = os.path.join(ROOT, a.tiles)
        cp = subprocess.run([exe, "replay", "--level", lp, "--tiles", tp, "--camera", a.camera, "--commands", a.commands],
                            capture_output=True, text=True)
        if cp.returncode != 0:
            print("REFUSE: replay failed: " + cp.stderr.strip())
            return 2
        lines = dict(ln.split(" ", 1) for ln in cp.stdout.strip().splitlines() if " " in ln)
        # "final camera 33 28 W" -> the value after "camera " is "33 28 W"
        fc = lines["final"].split()  # ["camera", "33", "28", "W"]
        final = "%s,%s,%s" % (fc[1], fc[2], fc[3])
        sb = lines["steps"].split()  # ["5", "blocked", "1"]  (key was "steps", value "5 blocked 1")
        steps, blocked = int(sb[0]), int(sb[2])
        head = lines["head"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    W, M = sha256_file(os.path.join(ROOT, a.level)), sha256_file(os.path.join(ROOT, a.tiles))
    data = {
        "level": a.level, "tiles": a.tiles, "W": W, "M": M,
        "camera": a.camera, "commands": a.commands,
        "final": final, "steps": steps, "blocked": blocked, "head": head,
    }
    rec = envelope.seal(
        "verdandi-walk", 1, "established",
        {"tool": "workshop/input.rs + verify/seal_walk.py", "oracle_authority": "witness/identity, frozen from Urðr"},
        {"certifies": "a fixed camera walk (commands %s from %s) over the frozen authority (W %s… M %s…) replays to this head; "
                      "the trajectory (final %s, %d steps, %d blocked) and every step's kernel URDRFB1 frame digest are "
                      "reproducible on any host" % (a.commands, a.camera, W[:12], M[:12], final, steps, blocked),
         "W": W, "M": M, "head": head},
        ["a wall-clock or any timing (a walk carries no time; it is a pure headless replay)",
         "an edit, or any change to W or M (the camera is projection-owned per WORKSHOP-0b; a walk reads the authority, never writes it)",
         "a skybox or physics (a walk moves the camera through the frozen geometry only — no new VIEW or CORE)",
         "the shell's key/mouse capture (that is INPUT-0b, host-run; this head is the headless command→camera→frame discipline)"],
        data, "")
    out = os.path.join(ROOT, a.out)
    envelope.write(out, rec)
    print("[seal] %s sealed; walk %s from %s; final %s (%d steps, %d blocked); head %s; chain %s"
          % (os.path.relpath(out, ROOT), a.commands, a.camera, final, steps, blocked, head[:12], rec["chain_hash"][:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
