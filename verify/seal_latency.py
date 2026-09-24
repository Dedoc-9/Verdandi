# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""seal_latency.py — seal the raw LATENCY-0 record the Windows shell wrote, under RECORD-0's envelope.

    python verify/seal_latency.py --record shell/attest/latency-<host>.json

The shell (shell/win32.rs playback_window --measure) writes the measurement but not the chain hash: sealing is
Python's, so the envelope has one implementation and one firewall. This reads the raw record, fills the
forbidden interpretations, cites LATENCY-0's preregistration entry by its real chain hash, and re-writes it
sealed. The record's `data` carries ONLY the measured numbers and the declared thresholds — the SOFTWARE-144-
BUDGET / HARDWARE-144 / SUSTAINED-144Hz verdicts are readings computed from those numbers, never keys in data.
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
    if raw.get("name") != "verdandi-latency":
        print("REFUSE: not a verdandi-latency record")
        return 2
    d = raw["data"]
    # sanity: the record must carry the present distribution, the refresh, and the declared thresholds
    for k in ("present_us", "refresh_period_us", "samples", "software_144_budget_us", "hardware_144_target_hz"):
        if k not in d:
            print(f"REFUSE: the latency record is missing {k}")
            return 2
    if d["software_144_budget_us"] != 6944 or d["hardware_144_target_hz"] != 144:
        print("REFUSE: the record's thresholds do not match the preregistered 6944 us / 144 Hz")
        return 2
    with open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8") as fh:
        reg = json.load(fh)
    latency0 = reg["entries"]["LATENCY-0"]["chain_hash"]
    prov = dict(raw["provenance"])
    prov["preregistered"] = {"rung": "LATENCY-0", "chain_hash": latency0}
    rec = envelope.seal(
        "verdandi-latency", 1, "measured", prov,
        {"certifies": raw["validity_scope"]["certifies"], "host": raw["validity_scope"]["host"]},
        ["input-to-photon latency: input transport, the present wait beyond composition and the panel need capture hardware",
         "renderer time (that is the kernel bench, kernel/attest/bench-<host>.json); this is only frame-ready -> composited",
         "SOFTWARE-144-BUDGET (p99 <= 6944 us) is a budget condition, not sustained-144Hz presentation and not a refresh-rate claim",
         "HARDWARE-144 is the measured DwmFlush refresh, never the monitor's nominal setting; SUSTAINED-144Hz needs BOTH",
         "any other host, scene, window state or interactive load; this is the fixed sealed reference session"],
        raw["data"], raw["reading"])
    envelope.write(a.record, rec)
    # print the readings computed from the sealed numbers (verdicts live here, never in data)
    p99 = d["present_us"]["p99"]
    refresh = d["refresh_period_us"]
    software = p99 <= 6944
    hardware = refresh <= 6944
    print(f"[seal] {os.path.relpath(a.record, ROOT)} sealed; cites LATENCY-0 {latency0[:8]}; chain {rec['chain_hash'][:12]}")
    print(f"       SOFTWARE-144-BUDGET: {'PASS' if software else 'FAIL'} (p99 {p99} us vs 6944 us)")
    print(f"       HARDWARE-144:        {'PASS' if hardware else 'FAIL'} (refresh {refresh} us vs 6944 us)")
    print(f"       SUSTAINED-144Hz:     {'PASS' if software and hardware else 'FAIL'} (A AND B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
