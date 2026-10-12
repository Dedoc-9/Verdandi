# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# tools/probe/pointer_swap.py — experiment 3 of docs/STUDIO-CONTRACT.md §11: a writer replaces a pointer file whole,
# again and again, with art/director/durable.py's write (a temporary file flushed, then MoveFileExW with
# REPLACE_EXISTING | WRITE_THROUGH), and is killed (TerminateProcess) at a random moment; 200 times. After each kill the
# pointer must read as one of the two documents, whole. This measures process-kill consistency only, against axiom A1.
#
#   python tools\probe\pointer_swap.py [RUNS]
#
# Kill criterion: none for correctness (the contract's R7 rebuilds an unreadable pointer from the journal); a torn read
# is recorded against A1. Runs on POSIX too (os.replace), where it measures that platform instead.

import os
import random
import shutil
import subprocess
import sys
import tempfile
import time

from common import Probe, REPO

WRITER = r'''
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "art", "director"))
import durable
path = sys.argv[2]
docs = [open(sys.argv[3], "rb").read(), open(sys.argv[4], "rb").read()]
print("ready", flush=True)
i = 0
while True:
    durable.write(path, docs[i % 2])
    i += 1
'''


def main(argv):
    runs = int(argv[0]) if argv else 200
    p = Probe(3, "pointer_swap")
    d = tempfile.mkdtemp(prefix="vs-pointer-")
    try:
        sys.path.insert(0, os.path.join(REPO, "art"))
        import studio_txn as T
        a = T.pointer_bytes(T.GEN["G0"], 0)
        b = T.pointer_bytes(T.GEN["G1"], 5) + b" " * 300          # unequal lengths: a torn read cannot pass for either
        fa, fb = os.path.join(d, "a"), os.path.join(d, "b")
        open(fa, "wb").write(a)
        open(fb, "wb").write(b)
        path = os.path.join(d, "active.json")
        open(path, "wb").write(a)
        torn, readable, tmp_left = 0, 0, 0
        rnd = random.Random(20261012)
        t0 = time.time()
        for _ in range(runs):
            w = subprocess.Popen([sys.executable, "-c", WRITER, REPO, path, fa, fb], stdout=subprocess.PIPE, text=True)
            w.stdout.readline()
            time.sleep(rnd.uniform(0.001, 0.05))
            w.kill()                                                    # TerminateProcess on Windows, SIGKILL elsewhere
            w.wait()
            got = open(path, "rb").read()
            if got in (a, b):
                readable += 1
            else:
                torn += 1
            tmp_left += sum(1 for f in os.listdir(d) if f.endswith(".tmp"))
            for f in os.listdir(d):
                if f.endswith(".tmp"):
                    os.remove(os.path.join(d, f))
        p.case("pointer-whole-after-kill", "HELD" if torn == 0 else "BROKEN", runs=runs, whole=readable, torn=torn,
               temporaries_left=tmp_left, platform=os.name, seconds=round(time.time() - t0, 1))
        return p.verdict()
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
