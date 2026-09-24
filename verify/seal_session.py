# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""seal_session.py — seal a WORKSHOP-1 session under RECORD-0's envelope (a committed snapshot attestation).

    python verify/seal_session.py --session workshop/attest/session-demo.json

The working session (written by workshop/session.rs) carries its own hash-chain head as its integrity; sealing
adds the outer envelope (claim_class, scope, forbidden readings, chain hash) so the committed snapshot is
anchored the same way as every other record. The session's own head is left in `data` untouched.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "verify"))
import envelope  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    a = ap.parse_args()
    with open(a.session, encoding="utf-8") as fh:
        raw = json.load(fh)
    if raw.get("name") != "verdandi-session":
        print("REFUSE: not a verdandi-session")
        return 2
    data = raw["data"]
    base = data["base"]
    rec = envelope.seal(
        "verdandi-session", 1, "measured",
        {"tool": "workshop/session.rs + verify/seal_session.py", "base_level": base["level"], "base_tiles": base["tiles"], "edits": len(data["log"])},
        {"certifies": "an ordered cell/tile edit log over the base authority (W %s… M %s…), its per-entry content and full digests, and the head hash chain — the session replays to this head" % (base["W"][:12], base["M"][:12]),
         "base_W": base["W"], "base_M": base["M"], "head": data["head"]},
        ["a wall-clock (a session carries no time; it replays deterministically)",
         "a skybox or physics: the log holds only cell (walls/ground) and tile (texture) edits the frozen oracle certifies",
         "tamper-proofing beyond replay: a hash chain catches a changed entry under replay and is anchored by this seal and by git; it does not prove timing or non-membership",
         "any camera or view: the camera is projection-owned (INPUT-0), never in the authoring log"],
        data, raw.get("reading", ""))
    envelope.write(a.session, rec)
    print("[seal] %s sealed; head %s; chain %s" % (os.path.relpath(a.session, ROOT), data["head"][:12], rec["chain_hash"][:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
