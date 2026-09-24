# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""seal_present.py — seal the raw present record the Windows shell wrote, under RECORD-0's envelope.

    python verify/seal_present.py --record shell/attest/present-<host>.json

The shell (shell/win32.rs) writes the measurement but not the chain hash: sealing is Python's, so the envelope
has one implementation and one firewall. This reads the raw record, checks the blit witness against the frozen
shell pins (the present number must be of a picture that passed through the kernel), fills the forbidden
interpretations, cites SHELL-0's preregistration entry by its real chain hash, and re-writes it sealed.
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
    ap.add_argument("--record", required=True)
    a = ap.parse_args()
    with open(a.record, encoding="utf-8") as fh:
        raw = json.load(fh)
    if raw.get("name") != "verdandi-present":
        print("REFUSE: not a verdandi-present record")
        return 2
    # the blit witness in the record must be one the shell pins vouch for (a kernel-made picture)
    pins = envelope.read(os.path.join(ROOT, "verify", "pins", "shell-1.json"))
    known = {s[t]["blit"] for s in pins["data"]["scenes"].values() for t in s}
    bw = raw["data"].get("blit_witness")
    if bw not in known:
        print(f"REFUSE: the present record's blit witness {bw!r} is not a kernel-made composite in shell-1.json")
        return 2
    with open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8") as fh:
        reg = json.load(fh)
    shell0 = reg["entries"]["SHELL-0"]["chain_hash"]
    prov = dict(raw["provenance"])
    prov["preregistered"] = {"rung": "SHELL-0", "chain_hash": shell0}
    rec = envelope.seal(
        "verdandi-present", 1, "measured", prov,
        {"certifies": raw["validity_scope"]["certifies"], "host": raw["validity_scope"]["host"]},
        ["input-to-photon latency: input transport, the present wait beyond composition and the panel need capture hardware",
         "renderer time (that is the kernel bench, kernel/attest/bench-<host>.json); this is only frame-ready -> composited",
         "a low-latency claim: a composed GDI present costs at least one refresh interval under DWM — this is the baseline a flip-model shell is measured against",
         "any other host, scene or window state"],
        raw["data"], raw["reading"])
    envelope.write(a.record, rec)
    print(f"[seal] {os.path.relpath(a.record, ROOT)} sealed; cites SHELL-0 {shell0[:8]}; chain {rec['chain_hash'][:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
