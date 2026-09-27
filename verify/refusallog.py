# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
r"""refusallog.py — REFUSAL-LOG-0's reader: validate the unsealed refusal log and count what recurs. Reads only.

    python verify/refusallog.py [PATH]    # PATH defaults to $VERDANDI_REFUSAL_LOG, else build/refusals.log

The log is the shell's (shell/refusallog.rs): one JSON line per refusal event on the present path — the PRESENT-EXACT-0
court's refusals and the locked presenter's refusals and differing screen readbacks — appended and never rewritten.
It is an observation about execution, not evidence: it is not sealed, not chained and not committed, and no rule reads
it. This reader never writes, never repairs and never interprets. It checks each line against the record's shape,
reports a line that is not a record by its number without guessing, and counts records by (operation, surface,
reason_code, attribution) with the number of distinct runs each came from. A count is not a cause, and zero records
is not proof that a refusal cannot occur.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

LOG = "REFUSAL-LOG-0"
ENV = "VERDANDI_REFUSAL_LOG"
DEFAULT_PATH = os.path.join("build", "refusals.log")
KEYS = ("log", "refusal_id", "run_id", "seq", "unix_ms", "operation", "surface", "reason_code", "attribution", "context",
        "context_digest")
STRINGS = ("refusal_id", "run_id", "operation", "surface", "reason_code", "attribution", "context_digest")


def default_path() -> str:
    return os.environ.get(ENV) or DEFAULT_PATH


def context_digest(ctx: dict) -> str:
    """The sha256 of the context object's JSON as the shell writes it (compact, keys in order, non-ASCII as is)."""
    return hashlib.sha256(json.dumps(ctx, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def problem(rec) -> str | None:
    """Why `rec` is not a REFUSAL-LOG-0 record, or None if it is one."""
    if not isinstance(rec, dict) or tuple(rec) != KEYS:
        return "not the record's keys in order"
    if rec["log"] != LOG:
        return "not a %s line" % LOG
    for k in ("seq", "unix_ms"):
        if not isinstance(rec[k], int) or isinstance(rec[k], bool) or rec[k] < 0:
            return "%s is not a non-negative integer" % k
    for k in STRINGS:
        if not isinstance(rec[k], str) or not rec[k]:
            return "%s is not a non-empty string" % k
    ctx = rec["context"]
    if not isinstance(ctx, dict) or any(not isinstance(v, (int, str)) or isinstance(v, bool) for v in ctx.values()):
        return "the context is not integers and strings"
    if rec["refusal_id"] != "%s/%d" % (rec["run_id"], rec["seq"]):
        return "refusal_id is not run_id/seq"
    if rec["context_digest"] != context_digest(ctx):
        return "context_digest is not the context's sha256"
    return None


def read(path: str) -> tuple[list[dict], list[tuple[int, str]]]:
    """The records in file order and the lines that are not records ((line number, why)). A missing log is empty."""
    if not os.path.exists(path):
        return [], []
    records, bad = [], []
    with open(path, encoding="utf-8") as fh:
        for n, raw in enumerate(fh, 1):
            try:
                rec = json.loads(raw)
            except ValueError:
                bad.append((n, "not JSON"))
                continue
            why = problem(rec)
            if why:
                bad.append((n, why))
            else:
                records.append(rec)
    seen: dict = {}
    for rec in records:  # within a run, the sequence is 0, 1, 2, … in file order
        want = seen.get(rec["run_id"], 0)
        if rec["seq"] != want:
            bad.append((0, "run %s: seq %d where %d was next" % (rec["run_id"], rec["seq"], want)))
        seen[rec["run_id"]] = rec["seq"] + 1
    return records, bad


def tally(records: list[dict]) -> list[dict]:
    """Counts by (operation, surface, reason_code, attribution), with the distinct runs each came from. Counting only."""
    groups: dict = {}
    for r in records:
        key = (r["operation"], r["surface"], r["reason_code"], r["attribution"])
        g = groups.setdefault(key, {"count": 0, "runs": set()})
        g["count"] += 1
        g["runs"].add(r["run_id"])
    return [{"operation": k[0], "surface": k[1], "reason_code": k[2], "attribution": k[3], "count": g["count"],
             "runs": len(g["runs"])} for k, g in sorted(groups.items())]


def main(argv: list[str]) -> int:
    path = argv[1] if len(argv) > 1 else default_path()
    records, bad = read(path)
    runs = len({r["run_id"] for r in records})
    print("%s: %d record(s) from %d run(s)%s" % (path, len(records), runs, "" if os.path.exists(path) else " (no log yet)"))
    for t in tally(records):
        print("  %-18s %-5s %-34s %-20s count=%d runs=%d" % (t["operation"], t["surface"], t["reason_code"], t["attribution"],
                                                           t["count"], t["runs"]))
    for n, why in bad:
        print("  not a record%s: %s" % (" (line %d)" % n if n else "", why))
    print("counts are observations, not causes; zero records is not proof that a refusal cannot occur")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
