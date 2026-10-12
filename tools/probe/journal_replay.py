# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# tools/probe/journal_replay.py — experiment 5 of docs/STUDIO-CONTRACT.md §11, the journal-replay court: a writer makes
# one scripted promotion's records (art/studio_txn.py's scripts) with the studio's own writes — each journal line
# appended and flushed (art/director/durable.py: os.fsync, which is _commit on Windows), each pointer replaced whole
# (a temporary flushed, then MoveFileExW with WRITE_THROUGH) — and says ACK after each; it is killed (TerminateProcess)
# at a random moment. Then art/studio_txn.py's recover() reads the folder, and its decision must be the contract's for
# the records the writer had acknowledged, or for one more (the write in flight may have landed). Over 200 runs.
#
#   python tools\probe\journal_replay.py [RUNS]
#
# Kill criterion: any SAFE, any journal that is not a prefix of the script's bytes (a torn tail aside), or any decision
# not the contract's → the record form is revised before B2's promotion code. Runs on POSIX too, measuring that.

import os
import random
import shutil
import subprocess
import sys
import tempfile
import time

from common import Probe, REPO

WRITER = r'''
import json, os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "art")); sys.path.insert(0, os.path.join(sys.argv[1], "art", "director"))
import durable, studio_txn as T
d, k = sys.argv[2], int(sys.argv[3])
J = os.path.join(d, "promotions.log"); P = os.path.join(d, "active.json")
name, script = T.scripts()[k]
raw = b""
print("ready", flush=True)
for n, w in enumerate(script):
    if w[0] == "append":
        nxt = T.append_bytes(raw, w[1], w[2])
        durable.append(J, nxt[len(raw):])
        raw = nxt
    else:
        durable.write(P, T.pointer_bytes(w[1], w[2]))
    print("ACK %d" % (n + 1), flush=True)
print("DONE", flush=True)
'''


def main(argv):
    runs = int(argv[0]) if argv else 200
    p = Probe(5, "journal_replay")
    sys.path.insert(0, os.path.join(REPO, "art"))
    import studio_txn as T
    scripts = T.scripts()
    F = T.fs(T.ALL)
    rnd = random.Random(20261013)
    # the time a whole script takes here (journal flushes cost what this machine's disk costs), so kills fall inside it
    durs = []
    for k in range(6):
        d = tempfile.mkdtemp(prefix="vs-journal-")
        try:
            w = subprocess.Popen([sys.executable, "-B", "-c", WRITER, REPO, d, str(len(scripts) - 1 - k)], stdout=subprocess.PIPE, text=True)
            w.stdout.readline()
            t = time.perf_counter()
            w.stdout.read()
            w.wait()
            durs.append(time.perf_counter() - t)
        finally:
            shutil.rmtree(d, ignore_errors=True)
    span = sorted(durs)[len(durs) // 2]
    bad, safe, prefix_faults, completed, torn_tails = [], 0, 0, 0, 0
    at = {}
    t0 = time.time()
    for run in range(runs):
        k = rnd.randrange(len(scripts))
        name, script = scripts[k]
        d = tempfile.mkdtemp(prefix="vs-journal-")
        try:
            w = subprocess.Popen([sys.executable, "-B", "-c", WRITER, REPO, d, str(k)], stdout=subprocess.PIPE, text=True)
            w.stdout.readline()
            time.sleep(rnd.uniform(0.0, span * 1.1))
            w.kill()
            out = w.communicate()[0]
            acked = max([int(ln.split()[1]) for ln in out.splitlines() if ln.startswith("ACK ")] or [0])
            completed += "DONE" in out
            at[acked] = at.get(acked, 0) + 1
            J = open(os.path.join(d, "promotions.log"), "rb").read() if os.path.exists(os.path.join(d, "promotions.log")) else None
            P = open(os.path.join(d, "active.json"), "rb").read() if os.path.exists(os.path.join(d, "active.json")) else None
            full, Pf = b"", None
            for x in script:
                full, Pf = T.apply(full, Pf, [x])
            if J is not None and not full.startswith(J):
                prefix_faults += 1
                bad.append("%s: the journal is not a prefix of the script's bytes" % name)
                continue
            torn_tails += bool(J) and not J.endswith(b"\n")
            effects, action, rules = T.recover(J, P, F)
            got = ("safe",) if action[0] == "safe" else ("run" if action[0] == "run" else "trial", action[1])
            wants = []
            for m in (acked, acked + 1):
                Jm, Pm = b"", None
                for x in script[:m]:
                    Jm, Pm = T.apply(Jm, Pm, [x])
                wants.append(T.allowed(Jm, F) if Jm else ("safe",))
            if got == ("safe",) and ("safe",) not in wants:
                safe += 1
            if got not in wants:
                bad.append("%s killed after %d acknowledged writes: %s, the contract %s (%s)" % (name, acked, got, " or ".join(map(str, wants)), " ".join(rules)))
        finally:
            shutil.rmtree(d, ignore_errors=True)
    spread = " ".join("%d:%d" % kv for kv in sorted(at.items()))
    p.case("decision-is-the-contracts", "HELD" if not bad else "BROKEN", runs=runs, mismatches=len(bad), unexpected_safe=safe,
           journals_not_a_prefix=prefix_faults, torn_tails=torn_tails, completed=completed, script_ms=round(span * 1000, 1), platform=os.name,
           seconds=round(time.time() - t0, 1))
    print("  acknowledged writes at the kill (count:runs): " + spread, flush=True)
    for b in bad[:5]:
        print("  " + b, flush=True)
    return p.verdict(killed="the decision after a kill was not the contract's; the record form is revised before B2" if bad else None)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
