# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
r"""runledger.py — RUN-LEDGER-0's reader: validate the run ledger, count the runs, and join them to the refusal log.
Reads only.

    python verify/runledger.py [LEDGER [REFUSALS]]
        # LEDGER defaults to $VERDANDI_RUN_LEDGER, else build/runs.log;
        # REFUSALS to $VERDANDI_REFUSAL_LOG, else build/refusals.log

The ledger is the shell's (shell/runledger.rs): one JSON line per admitted run — a PRESENT-EXACT-0 court run or a
presenter run — appended when the run ends, refused or not, so a clean run is counted too. It is the denominator the
refusal log lacks: with it, "refused in N of M runs" can be said instead of "N runs that refused". Like the refusal
log it is an observation, not evidence: not sealed, not chained, not committed, and read by no rule. This reader never
writes, never repairs and never interprets. It checks each line, counts runs by (operation, surface, exit_code) with
their compared and differing readbacks, and joins the two files on run_id: a run whose `refusals` differs from the
refusal records carrying its run_id, or a refusal record whose run has no ledger line, is reported, not explained.
"""
from __future__ import annotations

import json
import os
import sys

import refusallog

LOG = "RUN-LEDGER-0"
ENV = "VERDANDI_RUN_LEDGER"
DEFAULT_PATH = os.path.join("build", "runs.log")
KEYS = ("log", "run_id", "operation", "surface", "readbacks_checked", "differed", "refusals", "exit_code",
        "unix_ms_start", "unix_ms_end")
INTS = ("readbacks_checked", "differed", "refusals", "exit_code", "unix_ms_start", "unix_ms_end")


def default_path() -> str:
    return os.environ.get(ENV) or DEFAULT_PATH


def problem(rec) -> str | None:
    """Why `rec` is not a RUN-LEDGER-0 line, or None if it is one."""
    if not isinstance(rec, dict) or tuple(rec) != KEYS:
        return "not the line's keys in order"
    if rec["log"] != LOG:
        return "not a %s line" % LOG
    for k in ("run_id", "operation", "surface"):
        if not isinstance(rec[k], str) or not rec[k]:
            return "%s is not a non-empty string" % k
    for k in INTS:
        if not isinstance(rec[k], int) or isinstance(rec[k], bool) or rec[k] < 0:
            return "%s is not a non-negative integer" % k
    if rec["differed"] > rec["readbacks_checked"] or rec["unix_ms_end"] < rec["unix_ms_start"]:
        return "more readbacks differed than were checked, or the run ended before it began"
    return None


def read(path: str) -> tuple[list[dict], list[tuple[int, str]]]:
    """The runs in file order and the lines that are not runs ((line number, why)). A missing ledger is empty."""
    if not os.path.exists(path):
        return [], []
    runs, bad, seen = [], [], set()
    with open(path, encoding="utf-8") as fh:
        for n, raw in enumerate(fh, 1):
            try:
                rec = json.loads(raw)
            except ValueError:
                bad.append((n, "not JSON"))
                continue
            why = problem(rec) or ("run %s appears twice" % rec["run_id"] if rec["run_id"] in seen else None)
            if why:
                bad.append((n, why))
            else:
                seen.add(rec["run_id"])
                runs.append(rec)
    return runs, bad


def join(runs: list[dict], refusals: list[dict]) -> list[str]:
    """Where the two files disagree on run_id: reported, never explained."""
    by_run: dict = {}
    for r in refusals:
        by_run[r["run_id"]] = by_run.get(r["run_id"], 0) + 1
    out, ledger = [], {r["run_id"] for r in runs}
    for r in runs:
        if by_run.get(r["run_id"], 0) != r["refusals"]:
            out.append("run %s: the ledger says %d refusal(s), the refusal log holds %d" % (r["run_id"], r["refusals"], by_run.get(r["run_id"], 0)))
    for run_id in sorted(set(by_run) - ledger):
        out.append("run %s: %d refusal record(s) with no ledger line" % (run_id, by_run[run_id]))
    return out


def tally(runs: list[dict]) -> list[dict]:
    """Runs by (operation, surface, exit_code), with their compared and differing readbacks and how many refused."""
    groups: dict = {}
    for r in runs:
        g = groups.setdefault((r["operation"], r["surface"], r["exit_code"]), {"runs": 0, "checked": 0, "differed": 0, "refused": 0})
        g["runs"] += 1
        g["checked"] += r["readbacks_checked"]
        g["differed"] += r["differed"]
        g["refused"] += 1 if r["refusals"] else 0
    return [dict(operation=k[0], surface=k[1], exit_code=k[2], **g) for k, g in sorted(groups.items())]


def main(argv: list[str]) -> int:
    path = argv[1] if len(argv) > 1 else default_path()
    rpath = argv[2] if len(argv) > 2 else refusallog.default_path()
    runs, bad = read(path)
    refusals, _ = refusallog.read(rpath)
    print("%s: %d run(s)%s" % (path, len(runs), "" if os.path.exists(path) else " (no ledger yet)"))
    for t in tally(runs):
        print("  %-18s %-5s exit=%d runs=%d refused=%d readbacks=%d differed=%d"
              % (t["operation"], t["surface"], t["exit_code"], t["runs"], t["refused"], t["checked"], t["differed"]))
    for n, why in bad:
        print("  not a run (line %d): %s" % (n, why))
    for d in join(runs, refusals):
        print("  join (%s): %s" % (rpath, d))
    print("counts are observations, not causes; a run with no refusals is not proof that a refusal cannot occur")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
