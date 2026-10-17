# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/selftests.py — THROUGHPUT-0 (0236): every self-test of the art layer in one command, in parallel, timed and logged.
#
#   python art/selftests.py [--jobs N] [--repeat N] [--only NAME,...] [--log FILE]
#
# Each suite runs in a process of its own (this Python, PYTHONHASHSEED=0, PYTHONUTF8=1 so that a redirected output on
# Windows is not cp1252, no bytecode written), at most --jobs at once (the machine's processors by default), the
# longest first. Its result is its exit status and its summary line, both required: a suite that ends 0 without its
# summary, or prints one that is not a pass, fails. The log (art/build/selftests/<UTC time>.log unless --log) keeps,
# for every run, each suite's summary, its wall time and the whole of its output; --repeat runs the set again and fails
# unless every suite's summary is the same each time (the times are the machine's and are only recorded). Exit 0 when
# every suite of every run passed.
#
# What it is not: the gate. Nothing here runs verify/verify.py or reads its result, and a suite passing here says
# nothing of a row. The art layer has no row (AGENTS.md).

import datetime
import os
import re
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# (name, arguments after the Python, the summary line's pattern, the seconds measured in the container at 0236 —
# only an order: the longest start first)
SUITES = (
    ("held", ["art/scene_diff.py", "selftest"], r"^HELD SELFTEST (\d+)/(\d+)$", 72),
    ("director", ["art/director.py", "selftest"], r"^DIRECTOR SELFTEST (PASSED|FAILED)\b.*$", 70),
    ("app", ["art/studio_app.py", "selftest"], r"^STUDIO APP SELFTEST (\d+)/(\d+)$", 55),
    ("racetest", ["art/director.py", "racetest"], r"^DIRECTOR RACETEST (PASSED|FAILED)\b.*$", 50),
    ("crashtest", ["art/director.py", "crashtest"], r"^DIRECTOR CRASHTEST (PASSED|FAILED)\b.*$", 45),
    ("check", ["art/check.py"], r"^ART CHECKS (PASSED|FAILED)\b.*$", 40),
    ("facade", ["art/play.py", "--facade-selftest"], r"^FACADE SELFTEST (\d+)/(\d+)$", 40),       # FACADE-0 (0237)
    ("strict", ["art/play.py", "--strict-selftest"], r"^STRICT SELFTEST (\d+)/(\d+)$", 60),       # STRICT-0 (0238)
    ("impact", ["art/impact.py", "selftest"], r"^IMPACT SELFTEST (\d+)/(\d+)$", 3),               # IMPACT-0 (0239)
    ("impact-studio", ["art/play.py", "--impact-selftest"], r"^IMPACT-STUDIO SELFTEST (\d+)/(\d+)$", 60),
    ("preview", ["art/motion.py", "selftest"], r"^PREVIEW SELFTEST (\d+)/(\d+)$", 5),                # PREVIEW-0 (0240)
    ("preview-studio", ["art/play.py", "--preview-selftest"], r"^PREVIEW-STUDIO SELFTEST (\d+)/(\d+)$", 60),
    ("path", ["art/camera.py", "selftest"], r"^PATH SELFTEST (\d+)/(\d+)$", 35),                     # PATH-0 (0241)
    ("legible", ["art/legibility.py", "selftest"], r"^LEGIBLE SELFTEST (\d+)/(\d+)$", 15),            # LEGIBLE-0 (0241)
    ("flagship", ["art/play.py", "--flagship-selftest"], r"^FLAGSHIP SELFTEST (\d+)/(\d+)$", 90),      # FLAGSHIP-0 (0243)
    ("page", ["art/play.py", "--page-selftest"], r"^PAGE SELFTEST (\d+)/(\d+)$", 110),              # PAGE-0 (0246): a browser
    ("cert", ["art/certificate.py", "selftest"], r"^CERT SELFTEST (\d+)/(\d+)$", 5),                  # CERT-0 (0244)
    ("glue", ["art/glue.py", "selftest"], r"^GLUE SELFTEST (\d+)/(\d+)$", 40),                        # GLUE-0 (0244)
    ("queue", ["art/studio_queue.py", "selftest"], r"^STUDIO-2 SELFTEST (\d+)/(\d+)$", 37),
    ("studio", ["art/studio.py", "selftest"], r"^STUDIO SELFTEST (\d+)/(\d+)$", 30),
    ("quality", ["art/quality.py", "selftest"], r"^QUALITY SELFTEST (\d+)/(\d+)$", 20),
    ("live", ["art/play.py", "--selftest"], r"^LIVE SELFTEST (\d+)/(\d+)$", 17),
    ("marks", ["art/studio_marks.py", "selftest"], r"^MARKS SELFTEST (\d+)/(\d+)$", 12),
    ("txn", ["art/studio_txn.py", "selftest"], r"^STUDIO-TXN SELFTEST (PASSED|FAILED)\b.*$", 10),
    ("boundary", ["art/play.py", "--boundary-selftest"], r"^BOUNDARY SELFTEST (\d+)/(\d+)$", 5),
)
TIMEOUT = 1800


def passed(m):
    """A summary line's match reads as a pass: PASSED, or n/n with n > 0."""
    if m is None:
        return False
    g = m.groups()
    return g[0] == "PASSED" if len(g) == 1 else (g[0] == g[1] and int(g[1]) > 0)


def run_one(name, args, pattern, root):
    env = dict(os.environ, PYTHONHASHSEED="0", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    t = time.perf_counter()
    try:
        cp = subprocess.run([sys.executable] + args, cwd=root, env=env, capture_output=True, timeout=TIMEOUT)
        out, rc = (cp.stdout + cp.stderr).decode("utf-8", "replace"), cp.returncode
    except subprocess.TimeoutExpired as e:
        out, rc = ((e.stdout or b"") + (e.stderr or b"")).decode("utf-8", "replace") + "\n(stopped after %d s)" % TIMEOUT, -1
    secs = time.perf_counter() - t
    lines = [ln.strip() for ln in out.splitlines()]
    hits = [m for m in (re.match(pattern, ln) for ln in lines) if m]
    m = hits[-1] if hits else None
    return {"name": name, "rc": rc, "summary": m.group(0) if m else "", "ok": rc == 0 and passed(m), "seconds": secs, "output": out}


def run_all(suites, jobs, root, say):
    todo = sorted(suites, key=lambda s: -s[3])
    results, lock = {}, threading.Lock()

    def worker():
        while True:
            with lock:
                if not todo:
                    return
                name, args, pattern, _s = todo.pop(0)
            r = run_one(name, args, pattern, root)
            with lock:
                results[name] = r
                say("  %-9s %6.1f s  %s %s" % (name, r["seconds"], "ok  " if r["ok"] else "FAIL", r["summary"] or "(no summary; exit %s)" % r["rc"]))
    threads = [threading.Thread(target=worker) for _ in range(max(1, min(jobs, len(todo))))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return [results[s[0]] for s in suites]


def opt(argv, k, d=None):
    return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d


def main(argv):
    jobs = int(opt(argv, "--jobs", os.cpu_count() or 2))
    repeat = int(opt(argv, "--repeat", "1"))
    only = opt(argv, "--only")
    suites = [s for s in SUITES if not only or s[0] in only.split(",")]
    if not suites:
        print("no suite named %s; the suites: %s" % (only, ", ".join(s[0] for s in SUITES)))
        return 2
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log = opt(argv, "--log") or os.path.join(HERE, "build", "selftests", stamp + ".log")
    os.makedirs(os.path.dirname(os.path.abspath(log)), exist_ok=True)
    runs, walls = [], []
    with open(log, "w", encoding="utf-8", newline="\n") as fh:
        def say(s):
            print(s, flush=True)
            fh.write(s + "\n")
            fh.flush()
        say("ART SELFTESTS %s: %d suites, %d at once, %d run(s); Python %s" % (stamp, len(suites), jobs, repeat, sys.version.split()[0]))
        for k in range(repeat):
            say("run %d" % (k + 1))
            t = time.perf_counter()
            runs.append(run_all(suites, jobs, REPO, say))
            walls.append(time.perf_counter() - t)
            say("run %d: %d of %d suites passed, %.1f s wall" % (k + 1, sum(r["ok"] for r in runs[-1]), len(suites), walls[-1]))
        same = all([r["summary"] for r in run] == [r["summary"] for r in runs[0]] for run in runs)
        ok = all(r["ok"] for run in runs for r in run) and same
        for k, run in enumerate(runs):
            for r in run:
                fh.write("\n===== run %d: %s (exit %s, %.1f s)\n%s" % (k + 1, r["name"], r["rc"], r["seconds"], r["output"]))
        say("ART SELFTESTS %s: %d run(s), wall %s s%s; log %s" % (
            "PASSED" if ok else "FAILED", repeat, ", ".join("%.1f" % w for w in walls),
            "" if same else "; the summaries differ between runs", os.path.relpath(log, REPO) if log.startswith(REPO + os.sep) else log))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
