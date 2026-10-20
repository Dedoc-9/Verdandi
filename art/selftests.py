# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/selftests.py — THROUGHPUT-0 (0236): every self-test of the art layer in one command, in parallel, timed and logged.
#
#   python art/selftests.py [--jobs N] [--repeat N] [--only NAME,...] [--log FILE]
#   python art/selftests.py --schedule-selftest      SCHEDULE (0251): the scheduler's law, with stand-in suites
#
# Each suite runs in a process of its own (this Python, PYTHONHASHSEED=0, PYTHONUTF8=1 so that a redirected output on
# Windows is not cp1252, no bytecode written), at most --jobs at once (the machine's processors by default), the
# longest first. Its result is its exit status and its summary line, both required: a suite that ends 0 without its
# summary, or prints one that is not a pass, fails. The log (art/build/selftests/<UTC time>.log unless --log) keeps,
# for every run, each suite's summary, its wall time and the whole of its output; --repeat runs the set again and fails
# unless every suite's summary is the same each time (the times are the machine's and are only recorded). Exit 0 when
# every suite of every run passed.
#
# The browser lane (BROWSER-SERIALIZATION-0, 0251, the owner's ruling): the suites that start a page test's browser
# (BROWSER, the register) run one at a time, in that order, beside the others, which keep their parallelism: at most
# --jobs suites at once all the same, the browser suite counted. A record of its own (Lane) holds the law in every run: a
# browser suite entering while another holds the lane, spans that meet, this run's page-test browser standing when the
# next starts or after the last, a look that cannot be made twice (one retry; never nothing), another order, or a browser
# ended by a suite outside the lane fails the run. Every suite is told it runs in the full check, and only the browser
# suite holding the lane is given the run's token: art/page_test.py's launch refuses a browser to a suite without it
# (BROWSER-OUTSIDE-LANE) and a profile that does not carry it (BROWSER-UNTOKENED), so that every page test's browser
# profile carries it, by which the lane's look finds this run's browsers. SCHEDULE's register row reads, from the code,
# the entries that reach launch (what it reads and what it does not: browser_suites), and fails when that is not BROWSER.
# A suite's failure stops no other, the
# browser suites' as before. Nothing here changes a suite's timeout (1800 s) or a suite's own bounds (the browser's 60 s
# end).
#
# What it is not: the gate. Nothing here runs verify/verify.py or reads its result, and a suite passing here says
# nothing of a row. The art layer has no row (AGENTS.md).

import ast
import datetime
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# (name, arguments after the Python, the summary line's pattern, the seconds expected: measured in the container at 0236
# for the suites then, estimated for those added since (page, page-cards and page-worlds need a browser and never ran
# there), STUDIO's measured again on his machine at 0253 — only an order: the longest start first; the browser suites'
# order is BROWSER's)
SUITES = (
    ("held", ["art/scene_diff.py", "selftest"], r"^HELD SELFTEST (\d+)/(\d+)$", 72),
    ("director", ["art/director.py", "selftest"], r"^DIRECTOR SELFTEST (PASSED|FAILED)\b.*$", 373),       # 0254: 373 s alone (its 0254 rows run once per plant; 81 s before)
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
    ("page-cards", ["art/play.py", "--cards-selftest"], r"^PAGE-CARDS SELFTEST (\d+)/(\d+)$", 150),  # DASHBOARD-0 (0249): a browser
    ("page-worlds", ["art/play.py", "--worlds-selftest"], r"^PAGE-WORLDS SELFTEST (\d+)/(\d+)$", 120),  # DASHBOARD-0 (0250): a browser
    ("cert", ["art/certificate.py", "selftest"], r"^CERT SELFTEST (\d+)/(\d+)$", 5),                  # CERT-0 (0244)
    ("glue", ["art/glue.py", "selftest"], r"^GLUE SELFTEST (\d+)/(\d+)$", 40),                        # GLUE-0 (0244)
    ("queue", ["art/studio_queue.py", "selftest"], r"^STUDIO-2 SELFTEST (\d+)/(\d+)$", 37),
    ("studio", ["art/studio.py", "selftest"], r"^STUDIO SELFTEST (\d+)/(\d+)$", 315),     # 0253: 314 s alone on his machine (190 rows)
    ("quality", ["art/quality.py", "selftest"], r"^QUALITY SELFTEST (\d+)/(\d+)$", 20),
    ("live", ["art/play.py", "--selftest"], r"^LIVE SELFTEST (\d+)/(\d+)$", 17),
    ("marks", ["art/studio_marks.py", "selftest"], r"^MARKS SELFTEST (\d+)/(\d+)$", 12),
    ("txn", ["art/studio_txn.py", "selftest"], r"^STUDIO-TXN SELFTEST (PASSED|FAILED)\b.*$", 10),
    ("boundary", ["art/play.py", "--boundary-selftest"], r"^BOUNDARY SELFTEST (\d+)/(\d+)$", 5),
    ("schedule", ["art/selftests.py", "--schedule-selftest"], r"^SCHEDULE SELFTEST (\d+)/(\d+)$", 255),  # BROWSER-SERIALIZATION-0 (0251)
)
TIMEOUT = 1800

# BROWSER-SERIALIZATION-0 (0251), the owner's ruling: "LOCK: PAGE, PAGE-CARDS, and PAGE-WORLDS are mutually exclusive in
# the full check. All other suites remain parallel. The 60-second browser-end bound is unchanged." The browser suites,
# the register, in the order they run, one at a time: the order the estimates above started them in before 0251, now
# written down.
BROWSER = ("page-cards", "page-worlds", "page")
# the full check's word to every suite, and its browser lane's token to the browser suite that holds the lane, as
# art/page_test.py reads them: launch refuses a page test's browser inside the full check to a suite without the token
# (BROWSER-OUTSIDE-LANE) and a profile that does not carry it (BROWSER-UNTOKENED), and a page test's scratch folder, so its
# browser's profile, carries it, by which the lane's look finds this run's browsers and nothing else
FULL_CHECK, LANE_TOKEN = "VERDANDI_FULL_CHECK", "VERDANDI_LANE_TOKEN"
# planted defects for SCHEDULE's rows only (python art/selftests.py --schedule-selftest), each in the code the full check
# runs and each caught by its own row for its own reason (PLANT_ROWS): the browser suites run as any other (as before
# 0251); the lane's order reversed; the lane in the order the suites are listed in; every worker held while a browser
# suite runs; the verdict blind to the lane; the
# record blinded (its holding check and the spans' overlap, one fact read twice); the lane stopped at a browser suite's
# failure; the lane not released when the runner raises; the register's reader following calls inside one module only;
# the reader resolving a name to any function or method of that name (a flat table); the reader taking only the first
# branch that names an argument; the reader skipping every main(); the reader blind to module-level bindings; the reader
# blind to a dispatcher in `if __name__ == "__main__":`; the reader resolving a function's own local to a module-level
# binding of its name; the reader reading of a main() called with constants only the branches they name; a browser suite
# left out of the
# register; the witness of a browser outside the lane blinded; the look at an entry ignored; a look that could not be made
# read as nothing; the look after the last browser suite skipped; a suite's process given this process's environment, not
# its own (as before 0251); the lane's token given to every suite; launch's guard taken away, and its check of the
# profile's token (art/page_test.py's lane_refusal, by VERDANDI_PLANT); the look by the profile's prefix alone, without the
# run's token; a page test's scratch folder made without the token (art/page_test.py's scratch, by VERDANDI_PLANT)
SCHEDULE_PLANTS = ("browsers-parallel", "browsers-reversed", "lane-listed-order", "all-serial", "verdict-ignores-law", "record-blind",
                   "lane-stops-on-failure", "lane-not-released-on-raise", "reader-local", "reader-flat", "reader-first-branch",
                   "reader-skips-main", "reader-no-assign", "reader-no-dunder-main", "reader-unscoped", "reader-main-branches-only",
                   "browser-unregistered", "witness-blind",
                   "look-ignored", "look-unknown-as-nothing", "closing-look-skipped", "env-dropped", "token-to-all", "guard-off",
                   "launch-untokened", "look-generic", "scratch-untokened")
SCHEDULE_PLANT = ""
SCHEDULING_ONLY = False          # SCHEDULE's own runs: a real suite is never started from them
# the lines a suite prints when it has ended a page test's browser (page_test.end_browser's row and its OBSERVED line)
BROWSER_LINE = re.compile(r"^(\[(PASS|FAIL)\] \S+: the browser ended, and nothing of it is left|OBSERVED \S+: the browser ended in )")


def standing(token):
    """This run's page-test browser processes: those whose command line names a page test's profile carrying the run's
    token (page-test-profile-<scratch with the token>-, art/page_test.py's scratch), each as 'pid name', read and never
    ended; ["unknown"] when the query could not be made (a failed query is never nothing)."""
    generic = SCHEDULE_PLANT == "look-generic"
    if not generic and not re.fullmatch(r"[0-9a-f]{8,32}", token or ""):
        return ["unknown"]
    pat = "page-test-profile-" if generic else "page-test-profile-*-%s-" % token
    try:
        if os.name == "nt":
            q = ("Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -like '*%s*' }"
                 " | ForEach-Object { '{0} {1}' -f $_.ProcessId, $_.Name }" % pat)
            cp = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", q], capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
            if cp.returncode != 0:
                return ["unknown"]
            return [ln.strip() for ln in cp.stdout.decode("utf-8", "replace").splitlines() if ln.strip()[:1].isdigit()]
        rx = re.compile(re.escape(pat).replace(r"\*", ".*"))
        cp = subprocess.run(["ps", "-eo", "pid=,comm=,args="], capture_output=True, timeout=30, stdin=subprocess.DEVNULL)
        if cp.returncode != 0:
            return ["unknown"]
        return [" ".join(ln.split()[:2]) for ln in cp.stdout.decode("utf-8", "replace").splitlines() if rx.search(ln) and "ps -eo" not in ln]
    except (OSError, subprocess.SubprocessError):
        return ["unknown"]


class Lane:
    """BROWSER-SERIALIZATION-0 (0251): the browser suites' one resource, and the record that tells when the scheduler did
    not keep them apart. The record has its own lock and state, and the scheduler decides nothing by it: the worker enters
    it just before every registered browser suite's process starts, whatever the scheduler decided, and leaves it just
    after the process has ended. A violation, any of which fails the run: entering while another holds it (and two spans
    that meet: the same fact read again from the spans, kept so that neither alone is the law's only words); this run's
    page-test browser processes standing at an entry (an earlier suite's browser alive) or after the last browser suite; a
    look that could not be made, twice (never nothing); the spans in another order than the register's, or a suite twice;
    a suite outside the lane whose output says it ended a browser. What it cannot see: a browser that is not a page test's,
    or whose processes do not name its profile."""

    def __init__(self, order, look=None):
        self.order, self.look = tuple(order), look
        self.lock, self.t0 = threading.Lock(), time.perf_counter()
        self.holding, self.spans, self.violations, self.looks = [], [], [], []

    def _look(self, when):
        if self.look is None:
            return []
        seen = self.look()
        if seen == ["unknown"]:
            seen = self.look()
            with self.lock:
                self.looks.append("the look %s could not be made, and %s" % (when, "not the second either" if seen == ["unknown"] else "the second could"))
        return seen

    def _judge(self, seen, what):
        if seen == ["unknown"]:
            if SCHEDULE_PLANT != "look-unknown-as-nothing":
                self.violations.append("%s: the look could not be made (unknown, never nothing)" % what)
        elif seen and SCHEDULE_PLANT != "look-ignored":
            self.violations.append("%s while this run's page-test browser processes stood: %s" % (what, ", ".join(seen[:4])))

    def enter(self, name):
        seen = self._look("at %s's entry" % name)
        with self.lock:
            if self.holding and SCHEDULE_PLANT != "record-blind":
                self.violations.append("%s entered while %s held the browser lane" % (name, ", ".join(self.holding)))
            self._judge(seen, "%s entered" % name)
            self.holding.append(name)
            self.spans.append([name, time.perf_counter() - self.t0, None])

    def leave(self, name):
        with self.lock:
            if name in self.holding:
                self.holding.remove(name)
            for sp in reversed(self.spans):
                if sp[0] == name and sp[2] is None:
                    sp[2] = time.perf_counter() - self.t0
                    break

    def close(self):
        """The look after the last browser suite has ended: a browser of this run that outlived its suite."""
        if not self.spans or SCHEDULE_PLANT == "closing-look-skipped":
            return
        seen = self._look("after the last browser suite")
        with self.lock:
            self._judge(seen, "after the last browser suite")

    def witness(self, name, output):
        """A suite outside the lane that ended a browser (its own lines say so) broke the law, registered or not."""
        if name in self.order or SCHEDULE_PLANT == "witness-blind":
            return
        if any(BROWSER_LINE.match(ln.strip()) for ln in (output or "").splitlines()):
            with self.lock:
                self.violations.append("%s, a suite outside the browser lane, ended a browser" % name)

    def verdict(self, selected):
        """The run's violations, and the law read again from the spans: none meeting, each selected browser suite once, in
        the register's order."""
        with self.lock:
            out, spans = list(self.violations), sorted((list(sp) for sp in self.spans), key=lambda sp: sp[1])
        end = lambda sp: sp[2] if sp[2] is not None else float("inf")      # noqa: E731
        if SCHEDULE_PLANT != "record-blind":
            out += ["%s and %s overlapped (%s, %s)" % (a[0], b[0], self.span(a), self.span(b))
                    for i, a in enumerate(spans) for b in spans[i + 1:] if b[1] < end(a)]
        want = [b for b in self.order if b in selected]
        got = [sp[0] for sp in spans]
        if got != want:
            out.append("the browser suites ran %s, not the registered %s" % (" then ".join(got) or "not at all", " then ".join(want) or "none"))
        return out

    @staticmethod
    def span(sp):
        return "%.1f-%s s" % (sp[1], "%.1f" % sp[2] if sp[2] is not None else "?")

    def line(self):
        with self.lock:
            spans = sorted(self.spans, key=lambda sp: sp[1])
        return ", ".join("%s %s" % (sp[0], self.span(sp)) for sp in spans) or "no browser suite"


def passed(m):
    """A summary line's match reads as a pass: PASSED, or n/n with n > 0."""
    if m is None:
        return False
    g = m.groups()
    return g[0] == "PASSED" if len(g) == 1 else (g[0] == g[1] and int(g[1]) > 0)


def suite_env(name, token):
    """A suite's environment: this one's, PYTHONHASHSEED=0, PYTHONUTF8=1 and no bytecode written; the full check's word;
    and the browser lane's token for a registered browser suite only."""
    env = dict(os.environ, PYTHONHASHSEED="0", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    env[FULL_CHECK] = "1"
    env.pop(LANE_TOKEN, None)
    if token and (name in BROWSER or SCHEDULE_PLANT == "token-to-all"):
        env[LANE_TOKEN] = token
    return env


def run_one(name, args, pattern, root, env=None):
    if SCHEDULING_ONLY and any(list(args) == list(s[1]) for s in SUITES):
        raise RuntimeError("the scheduling self-test starts no suite of the full check (%s)" % name)
    if SCHEDULE_PLANT == "env-dropped":
        env = dict(os.environ, PYTHONHASHSEED="0", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    t = time.perf_counter()
    try:
        cp = subprocess.run([sys.executable] + args, cwd=root, env=env or suite_env(name, ""), capture_output=True, timeout=TIMEOUT)
        out, rc = (cp.stdout + cp.stderr).decode("utf-8", "replace"), cp.returncode
    except subprocess.TimeoutExpired as e:
        out, rc = ((e.stdout or b"") + (e.stderr or b"")).decode("utf-8", "replace") + "\n(stopped after %d s)" % TIMEOUT, -1
    secs = time.perf_counter() - t
    lines = [ln.strip() for ln in out.splitlines()]
    hits = [m for m in (re.match(pattern, ln) for ln in lines) if m]
    m = hits[-1] if hits else None
    return {"name": name, "rc": rc, "summary": m.group(0) if m else "", "ok": rc == 0 and passed(m), "seconds": secs, "output": out}


def run_all(suites, jobs, root, say, runner=None, lane=None, parallel_browsers=False, token=""):
    """One run of the set: (the results in `suites`' order, the lane). The browser suites in BROWSER's order, one at a time,
    each taken first by the next free worker whenever none runs; the others longest first, as before; at most `jobs` at
    once, the browser suite counted. Every registered browser suite enters the lane's record, and is given `token`. A
    runner that raises is a failed result (its traceback its output), and the lane is let go all the same; a suite's
    failure stops no other. `parallel_browsers` runs the browser suites as any other (a self-test's way to make the
    record see an overlap)."""
    runner = runner or run_one
    plant = SCHEDULE_PLANT
    parallel = parallel_browsers or plant == "browsers-parallel"
    lane = lane if lane is not None else Lane(BROWSER)
    names = [s[0] for s in suites]
    order = list(reversed(BROWSER)) if plant == "browsers-reversed" else list(BROWSER)
    lane_q = [] if parallel else [next(s for s in suites if s[0] == b) for b in order if b in names]
    if plant == "lane-listed-order":
        lane_q = [s for s in suites if s[0] in BROWSER]
    queued = {s[0] for s in lane_q}
    todo = sorted((s for s in suites if s[0] not in queued), key=lambda s: -s[3])
    results, cond = {}, threading.Condition()
    state = {"browser": False}

    def worker():
        while True:
            with cond:
                while True:
                    if plant == "all-serial" and state["browser"]:
                        cond.wait(1.0)
                        continue
                    if lane_q and not state["browser"]:
                        item, mine = lane_q.pop(0), True
                        state["browser"] = True
                        break
                    if todo:
                        item, mine = todo.pop(0), False
                        break
                    if not lane_q:
                        return
                    cond.wait(1.0)
            name, args, pattern, _s = item
            held = name in lane.order                  # the lane's record holds every registered browser suite, scheduled or not
            r = None
            try:
                if held:
                    lane.enter(name)
                r = runner(name, args, pattern, root, env=suite_env(name, token))
            except BaseException as e:  # noqa: BLE001 — the suite's result says what stopped it; the lane is let go below
                if plant == "lane-not-released-on-raise" and mine:
                    raise
                r = {"name": name, "rc": None, "summary": "", "ok": False, "seconds": 0.0,
                     "output": "the runner raised %s: %s\n%s" % (type(e).__name__, e, traceback.format_exc())}
            finally:
                if not (plant == "lane-not-released-on-raise" and mine and r is None):
                    with cond:                         # the span ended, the lane left, then released, then the others told
                        if held:
                            lane.leave(name)
                        if mine:
                            state["browser"] = False
                            if plant == "lane-stops-on-failure" and not (r and r["ok"]):
                                del lane_q[:]
                        cond.notify_all()
            lane.witness(name, r["output"])
            with cond:
                results[name] = r
                say("  %-9s %6.1f s  %s %s" % (name, r["seconds"], "ok  " if r["ok"] else "FAIL", r["summary"] or "(no summary; exit %s)" % r["rc"]))
    threads = [threading.Thread(target=worker, daemon=True) for _ in range(max(1, min(jobs, len(suites))))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    lane.close()
    missing = {"name": "", "rc": None, "summary": "", "ok": False, "seconds": 0.0, "output": "not run (the scheduler ended without it)"}
    return [results.get(s[0], dict(missing, name=s[0])) for s in suites], lane


def opt(argv, k, d=None):
    return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d


def main(argv, suites_set=None, runner=None, look=standing, parallel_browsers=False):
    if "--schedule-selftest" in argv:
        return schedule_selftest()
    jobs = int(opt(argv, "--jobs", os.cpu_count() or 2))
    repeat = int(opt(argv, "--repeat", "1"))
    only = opt(argv, "--only")
    every = suites_set if suites_set is not None else SUITES
    suites = [s for s in every if not only or s[0] in only.split(",")]
    if not suites:
        print("no suite named %s; the suites: %s" % (only, ", ".join(s[0] for s in every)))
        return 2
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log = opt(argv, "--log") or os.path.join(HERE, "build", "selftests", stamp + ".log")
    os.makedirs(os.path.dirname(os.path.abspath(log)), exist_ok=True)
    runs, walls, laws = [], [], []
    with open(log, "w", encoding="utf-8", newline="\n") as fh:
        def say(s):
            print(s, flush=True)
            fh.write(s + "\n")
            fh.flush()
        say("ART SELFTESTS %s: %d suites, %d at once, %d run(s); Python %s" % (stamp, len(suites), jobs, repeat, sys.version.split()[0]))
        for k in range(repeat):
            say("run %d" % (k + 1))
            t = time.perf_counter()
            token = secrets.token_hex(8)             # this run's browser lane (never in a seed, a state or a result)
            lane = Lane(BROWSER, look=(lambda tok=token: look(tok)) if look else None)
            run, lane = run_all(suites, jobs, REPO, say, runner=runner, lane=lane, parallel_browsers=parallel_browsers, token=token)
            runs.append(run)
            walls.append(time.perf_counter() - t)
            broken = lane.verdict({s[0] for s in suites})
            laws.append(broken)
            say("run %d: %d of %d suites passed, %.1f s wall; the browser lane %s: %s%s" % (
                k + 1, sum(r["ok"] for r in run), len(suites), walls[-1], "BROKEN" if broken else "held, one at a time in order", lane.line(),
                "".join("; " + v for v in broken) + "".join("; " + ln for ln in lane.looks)))
        same = all([r["summary"] for r in run] == [r["summary"] for r in runs[0]] for run in runs)
        held = SCHEDULE_PLANT == "verdict-ignores-law" or not any(laws)
        ok = all(r["ok"] for run in runs for r in run) and same and held
        for k, run in enumerate(runs):
            for r in run:
                fh.write("\n===== run %d: %s (exit %s, %.1f s)\n%s" % (k + 1, r["name"], r["rc"], r["seconds"], r["output"]))
        say("ART SELFTESTS %s: %d run(s), wall %s s%s%s; log %s" % (
            "PASSED" if ok else "FAILED", repeat, ", ".join("%.1f" % w for w in walls),
            "" if same else "; the summaries differ between runs",
            "" if held else "; the browser suites' law broken in run %s" % ", ".join(str(k + 1) for k, v in enumerate(laws) if v),
            os.path.relpath(log, REPO) if log.startswith(REPO + os.sep) else log))
    return 0 if ok else 1


# ------------------------------------------------------------------------------------------------ SCHEDULE (0251)
def browser_suites(suites=SUITES, art=HERE):
    """(the entries of `suites` that start a page test's browser, the entries it could not read), read from the code and
    never from a name. An entry with an argument starts from every branch of its module's dispatcher (its main(), or
    without one its `if __name__ == "__main__":` block) whose test holds the argument as a constant (`"--page-selftest" in
    argv`, `argv[:1] == ["selftest"]`, `cmd == "selftest"`); an entry of art/play.py with none is not read; any other entry
    with none starts from its whole module. From there every reference is followed, a call or not (a function passed, a
    lambda, getattr with a constant name): a bare name to its own module's top-level function, class or variable (a class's
    whole body, its methods with it; a function's whole body, its nested functions with it; a variable's value), never
    a name the function or lambda around it binds for itself (a parameter, a local); a module's name or an imported name
    to that module's top-level one, the imports and aliases of the modules at art/NAME.py resolved (a module elsewhere is
    not read). A call of a module's main() with a constant list of arguments follows all of it but the branches whose
    tests name strings and none of that list (main([]) none of them); any other reference to a main() follows it whole.
    The entry starts a browser
    when the walk meets art/page_test.py's launch. Not followed: another process started by a command line, a name
    computed at run time, a method called on an object, a module-level binding to a target that is not a plain name;
    inside the full check launch itself refuses a browser to a suite outside the lane (BROWSER-OUTSIDE-LANE)."""
    mods = {}
    plant = SCHEDULE_PLANT

    def mod(name):
        if name not in mods:
            path = os.path.join(art, name + ".py")
            try:
                with open(path, "rb") as fh:                   # bytes: a BOM or a coding line read as Python reads them
                    tree = ast.parse(fh.read(), filename=path)
            except (OSError, SyntaxError, ValueError):
                mods[name] = None
                return None
            defs, alias, frm = {}, {}, {}
            for n in ast.walk(tree):
                if isinstance(n, ast.Import):
                    for a in n.names:
                        alias[a.asname or a.name] = a.name.split(".")[-1]
                elif isinstance(n, ast.ImportFrom) and n.module:
                    for a in n.names:
                        frm[a.asname or a.name] = (n.module.split(".")[-1], a.name)
            if plant == "reader-flat":                         # every function and method of the module by its bare name
                for n in ast.walk(tree):
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        defs.setdefault(n.name, []).append(n)
            todo = [] if plant == "reader-flat" else list(tree.body)
            while todo:                                        # the module's own top-level ones (inside if, try, with too)
                n = todo.pop(0)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    defs.setdefault(n.name, []).append(n)
                elif isinstance(n, (ast.Assign, ast.AnnAssign)) and n.value is not None and plant != "reader-no-assign":
                    for t in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                        if isinstance(t, ast.Name) and isinstance(n.value, ast.Name) and n.value.id in alias:
                            alias[t.id] = alias[n.value.id]   # a module named again
                        elif isinstance(t, ast.Name):
                            defs.setdefault(t.id, []).append(n.value)
                else:
                    for f in ("body", "orelse", "finalbody", "handlers"):
                        todo += [x for x in getattr(n, f, None) or [] if isinstance(x, ast.AST)]
            mods[name] = (tree, defs, alias, frm)
        return mods[name]

    def bound_in(f):
        """the names a function or lambda binds for itself (its parameters, the names it stores, its nested functions and
        classes; not its imports, not those it declares global or nonlocal, not a nested function's own)"""
        a = f.args
        names = {x.arg for x in a.posonlyargs + a.args + a.kwonlyargs + [v for v in (a.vararg, a.kwarg) if v is not None]}
        declared, stack = set(), list(f.body) if isinstance(f.body, list) else [f.body]
        while stack:
            n = stack.pop()
            if isinstance(n, (ast.Global, ast.Nonlocal)):
                declared |= set(n.names)
            elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
                names.add(n.id)
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(n.name)
            elif not isinstance(n, ast.Lambda):
                stack.extend(ast.iter_child_nodes(n))
        return names - declared

    def refs(m, node, bound=frozenset()):
        """(module, name) of everything node references; (module, "main", flags) for a module's main(), flags the constant
        arguments of a call of it, or None (all of it). A bare name a function or lambda binds for itself is its own, never
        the module's (`bound`: the names bound around node)"""
        _t, defs, alias, frm = mod(m)
        local = plant == "reader-local"
        scoped = plant != "reader-unscoped"
        flags = {}
        for n in ast.walk(node):
            if isinstance(n, ast.Call):
                a = n.args[0] if n.args else None
                const = isinstance(a, (ast.List, ast.Tuple)) and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in a.elts)
                flags[id(n.func)] = tuple(e.value for e in a.elts) if const else None
        out = set()

        def add(key, n):
            out.add(key + (flags.get(id(n)),) if key[1] == "main" else key)
        todo = [(node, frozenset(bound))]
        while todo:
            n, bnd = todo.pop()
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) and scoped:
                bnd = bnd | bound_in(n)
            if isinstance(n, ast.Name) and (isinstance(n.ctx, ast.Load) or not scoped) and not (scoped and n.id in bnd):
                if n.id in defs:
                    add((m, n.id), n)
                if n.id in frm and not local:
                    add(frm[n.id], n)
            elif isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in alias and not local:
                add((alias[n.value.id], n.attr), n)
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "getattr" and len(n.args) >= 2 and not local
                    and isinstance(n.args[0], ast.Name) and n.args[0].id in alias
                    and isinstance(n.args[1], ast.Constant) and isinstance(n.args[1].value, str)):
                add((alias[n.args[0].id], n.args[1].value), n.args[1])
            todo += [(c, bnd) for c in ast.iter_child_nodes(n)]
        return out

    def dispatcher(m):
        got = mod(m)
        main_ = next((n for n in (got[1].get("main", []) if got else []) if isinstance(n, ast.FunctionDef)), None)
        if main_ is not None or got is None or plant == "reader-no-dunder-main":
            return main_
        return next((n for n in got[0].body if isinstance(n, ast.If) and isinstance(n.test, ast.Compare)
                     and isinstance(n.test.left, ast.Name) and n.test.left.id == "__name__"), None)

    def scope(d):
        return bound_in(d) if isinstance(d, ast.FunctionDef) else frozenset()

    def dispatch(m, arg):
        """the statements of every branch of m's dispatcher whose test holds arg as a constant, or None"""
        d = dispatcher(m)
        hits = [n for n in (ast.walk(d) if d is not None else []) if isinstance(n, ast.If) and n is not d
                and any(isinstance(c, ast.Constant) and c.value == arg for c in ast.walk(n.test))]
        out = [x for n in (hits[:1] if plant == "reader-first-branch" else hits) for x in n.body]
        return out or None

    def entered(stmts, given):
        """main's statements a call with the constant arguments `given` can run: every one, but for the body of an if whose
        test names strings and none of them given (its test and its elif or else read all the same)"""
        out = []
        for st in stmts:
            if isinstance(st, ast.If):
                strs = {c.value for c in ast.walk(st.test) if isinstance(c, ast.Constant) and isinstance(c.value, str)}
                out.append(st.test)
                if not strs or strs & set(given):
                    out += entered(st.body, given)
                out += entered(st.orelse, given)
            else:
                out.append(st)
        return out

    def reaches(m, nodes, bound=frozenset()):
        todo, seen = [r for n in nodes for r in refs(m, n, bound)], set()
        while todo:
            key = todo.pop()
            if key[:2] == ("page_test", "launch"):
                return True
            if key in seen or (key[1] == "main" and plant == "reader-skips-main"):
                continue
            seen.add(key)
            got = mod(key[0])
            if got is None:
                continue
            if key[1] == "main" and key[2] is not None:
                d = next((n for n in got[1].get("main", []) if isinstance(n, ast.FunctionDef)), None)
                if d is not None and plant == "reader-main-branches-only":
                    for flag in key[2]:
                        for st in dispatch(key[0], flag) or []:
                            todo += list(refs(key[0], st, scope(d)))
                elif d is not None:
                    for st in entered(d.body, key[2]):
                        todo += list(refs(key[0], st, scope(d)))
                continue
            for d in got[1].get(key[1], []):
                todo += list(refs(key[0], d))
        return False
    found, unread = [], []
    for name, args, _p, _s in suites:
        path = (args[0] if args else "").replace("\\", "/")
        m = path[4:-3] if path.startswith("art/") and path.endswith(".py") and "/" not in path[4:] else None
        if m is None or mod(m) is None:
            unread.append(name)
            continue
        body = dispatch(m, args[1]) if len(args) > 1 else None
        if body is None and m == "play":
            unread.append(name)
        elif reaches(m, body, scope(dispatcher(m))) if body is not None else reaches(m, [mod(m)[0]]):
            found.append(name)
    return found, unread


# launch asked in a process with a suite's environment: argv[2] is "made" (a profile made by page_test's own scratch and
# profile_of), "scratch" (the scratch folder itself) or a profile's path; nothing is ever started (the first touch of
# subprocess stops the process)
GUARD = r'''
import shutil, sys
sys.path.insert(0, sys.argv[1])
import page_test


class NoStart:
    def __getattr__(self, k):
        print("LET THROUGH: launch went on to start its process (stopped here)")
        sys.exit(0)
tmp = None
if sys.argv[2] == "made":
    tmp = page_test.scratch("page-cards-")
    prof = page_test.profile_of(tmp)[1]
elif sys.argv[2] == "scratch":
    tmp = prof = page_test.scratch("page-cards-")
else:
    prof = sys.argv[2]
page_test.subprocess = NoStart()
try:
    page_test.launch("no-such-browser", "about:blank", prof, False, sys.argv[3])
except RuntimeError as e:
    print(str(e))
finally:
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
'''
# a page test's profile as its own code makes it, in a process with a suite's environment (the name only: the folder is
# removed at once)
PROFILE = r'''
import shutil, sys
sys.path.insert(0, sys.argv[1])
import page_test
tmp = page_test.scratch("page-cards-")
print(page_test.profile_of(tmp)[1])
shutil.rmtree(tmp, ignore_errors=True)
'''
# what a suite's process was given (the full check's word, the lane's token)
ENV_PROBE = ("import os\nprint('FULL=%s TOKEN=%s' % (os.environ.get('VERDANDI_FULL_CHECK', ''), os.environ.get('VERDANDI_LANE_TOKEN', '')))\n"
             "print('STUB 1/1')\n")

READER = {      # the register reader's fixture: a page_test with launch, the shapes a browser suite's entry can take, and
                # shapes that must not be counted
    "page_test.py": ("def launch(*a):\n    pass\n\n\ndef run():\n    return launch()\n\n\n"
                     "def main(argv):\n    if argv[:1] == [\"selftest\"]:\n        return run()\n    return 0\n"),
    "page_x.py": "import page_test as PT\n\n\ndef cards(argv):\n    return PT.run()\n\n\ndef selftest():\n    return cards([])\n",
    "page_y.py": "import threading\nfrom page_test import launch as start\n\n\ndef go(argv):\n    threading.Thread(target=start).start()\n",
    "page_z.py": "import page_test\n\n\ndef go(argv):\n    f = getattr(page_test, \"launch\")\n    return f()\n",
    "page_w.py": ("import page_test as PT\n\n\nclass T:\n    def a(self):\n        return self.b()\n\n    def b(self):\n        return PT.launch()\n\n\n"
                  "def go(argv):\n    return T().a()\n"),
    # module-level bindings: a name bound to launch, a partial of it, the module named again
    "page_v.py": ("import functools\nimport page_test as PT\nSTART = PT.launch\nOPEN = functools.partial(PT.launch, \"x\")\nPT2 = PT\n\n\n"
                  "def go(argv):\n    return START()\n\n\ndef go2(argv):\n    return OPEN()\n\n\ndef go3(argv):\n    return PT2.launch()\n"),
    # a module whose main() is its whole body, delegated to (as art/scene_diff.py hands HELD to scene_diff_test.main)
    "page_u.py": "import page_test\n\n\ndef main(argv):\n    return page_test.launch()\n",
    "dl.py": "def main(argv):\n    if argv[:1] == [\"selftest\"]:\n        import page_u\n        return page_u.main(argv[1:])\n    return 0\n",
    "quiet.py": "def go(argv):\n    return 0\n",
    # a method named as the builtin it shares a module with (open), a parameter named as another function's nested def
    # (row), a call of play's main(): none starts a browser
    "quiet2.py": ("import page_test\n\n\nclass G:\n    def open(self):\n        return page_test.launch()\n\n\n"
                  "def outer():\n    def row():\n        return page_test.launch()\n    return row\n\n\n"
                  "def go(argv):\n    with open(argv[0]) as fh:\n        fh.read()\n    return 0\n\n\ndef go2(row):\n    return row(1)\n"),
    "quiet4.py": "import play\n\n\ndef go(argv):\n    return play.main([])\n",
    # a module whose own main() names its commands: one starts a browser, the other does not
    "quiet5.py": ("import page_test\n\n\ndef selftest():\n    return 0\n\n\ndef page_command(argv):\n    return page_test.launch()\n\n\n"
                  "def main(argv):\n    if argv[:1] == [\"selftest\"]:\n        return selftest()\n    if argv[:1] == [\"page\"]:\n        return page_command(argv)\n"),
    # the same, its commands in its `if __name__ == "__main__":` block (as art/motion.py's are)
    "quiet6.py": ("import sys\nimport page_test\n\n\ndef selftest():\n    return 0\n\n\ndef capture(argv):\n    return page_test.launch()\n\n\n"
                  "if __name__ == \"__main__\":\n    if sys.argv[1:2] == [\"capture\"]:\n        sys.exit(capture(sys.argv[2:]))\n"
                  "    if sys.argv[1:2] == [\"selftest\"]:\n        sys.exit(selftest())\n"),
    # a module-level binding in the `__main__` block named as another function's local (out)
    "quiet7.py": ("import sys\nimport page_test\n\n\ndef capture(argv):\n    return page_test.launch()\n\n\n"
                  "def selftest():\n    out = 0\n    return out\n\n\n"
                  "if __name__ == \"__main__\":\n    if sys.argv[1:2] == [\"capture\"]:\n        out = capture(sys.argv[2:])\n"
                  "        sys.exit(0 if out else 1)\n    if sys.argv[1:2] == [\"selftest\"]:\n        sys.exit(selftest())\n"),
    # a main whose command is its default path (a flag read outside an if)
    "quiet8.py": "import page_test\n\n\ndef main(argv):\n    quick = \"--quick\" in argv\n    if not argv:\n        quick = True\n    return page_test.launch(quick)\n",
    "play.py": ("import sys\n\n\ndef here(argv):\n    return 0\n\n\ndef main(argv):\n"
                "    if any(f in argv for f in (\"--a\", \"--b\")):\n        sys.stdout.flush()\n"
                "    if \"--a\" in argv:\n        import page_x\n        rc = page_x.cards(argv)\n        return rc\n"
                "    if \"--b\" in argv:\n        import page_y\n        return int(page_y.go(argv) or 0)\n"
                "    if \"--c\" in argv:\n        import page_z\n        sys.exit(page_z.go(argv))\n"
                "    if \"--d\" in argv:\n        import page_w\n        return (lambda: page_w.go(argv))()\n"
                "    if \"--e\" in argv:\n        import quiet\n        return quiet.go(argv) + here(argv)\n"
                "    if \"--o\" in argv:\n        import quiet2\n        return quiet2.go(argv) + quiet2.go2(print)\n"
                "    if \"--m\" in argv:\n        import quiet4\n        return quiet4.go(argv)\n"
                "    if \"--v\" in argv:\n        import page_v\n        return page_v.go(argv)\n"
                "    if \"--v2\" in argv:\n        import page_v\n        return page_v.go2(argv)\n"
                "    if \"--v3\" in argv:\n        import page_v\n        return page_v.go3(argv)\n"
                "    if \"--t\" in argv:\n        import page_test\n        return page_test.main([\"selftest\"] + argv)\n"
                "    if \"--k1\" in argv:\n        import quiet8\n        return quiet8.main([\"--quick\"])\n"
                "    if \"--k0\" in argv:\n        import quiet8\n        return quiet8.main([])\n"
                "    if \"--p5\" in argv:\n        import quiet5\n        return quiet5.main([\"page\"])\n"
                "    if \"--s5m\" in argv:\n        import quiet5\n        return quiet5.main([\"selftest\"])\n"
                "    return 0\n"),
}
READER_SUITES = tuple((n, a, "", 0) for n, a in (
    ("a", ["art/play.py", "--a"]), ("b", ["art/play.py", "--b"]), ("c", ["art/play.py", "--c"]), ("d", ["art/play.py", "--d"]),
    ("e", ["art/play.py", "--e"]), ("g", ["art/play.py", "--g"]), ("o", ["art/play.py", "--o"]), ("m", ["art/play.py", "--m"]),
    ("v", ["art/play.py", "--v"]), ("v2", ["art/play.py", "--v2"]), ("v3", ["art/play.py", "--v3"]), ("t", ["art/play.py", "--t"]),
    ("bs", ["art\\page_x.py", "selftest"]), ("q", ["art/quiet.py"]), ("dl", ["art/dl.py", "selftest"]),
    ("s5", ["art/quiet5.py", "selftest"]), ("s6", ["art/quiet5.py", "page"]),
    ("u5", ["art/quiet6.py", "selftest"]), ("u6", ["art/quiet6.py", "capture"]),
    ("u7", ["art/quiet7.py", "selftest"]), ("c7", ["art/quiet7.py", "capture"]),
    ("k1", ["art/play.py", "--k1"]), ("k0", ["art/play.py", "--k0"]), ("p5", ["art/play.py", "--p5"]), ("s5m", ["art/play.py", "--s5m"])))
READER_WANT = ["a", "b", "bs", "c", "c7", "d", "dl", "k0", "k1", "p5", "s6", "t", "u6", "v", "v2", "v3"]


def schedule_selftest():
    """SCHEDULE SELFTEST n/n: the scheduler's law, with stand-in suites (no suite's process, no browser) through run_all's
    and main's own code; the register's reader, on the tree and on a fixture of shapes; the witness, the looks at an entry
    and after the last, an unmade look; the guard at launch (a process of its own); the real look at this machine's
    processes, with decoys; then each plant, caught only by its own row, for its own reason, with every row before it
    passed. Browser stand-ins hold, each, until another browser stand-in is inside or HOLD seconds pass, so that two
    dispatched together are certainly inside at once (the overlap induced, not read from a log's order); three non-browser
    stand-ins meet the same way (for up to NHOLD), so that a scheduler that serialized them is seen."""
    global SCHEDULE_PLANT, SCHEDULING_ONLY
    SCHEDULING_ONLY = True
    HOLD, NHOLD, JOBS = 2.0, 15.0, 4
    # the order the stand-ins are listed in: neither the lane's nor its reverse, so that no row passes on the list's order
    LISTED = ("page", "page-cards", "page-worlds")
    assert sorted(LISTED) == sorted(BROWSER) and LISTED not in (tuple(BROWSER), tuple(reversed(BROWSER)))
    tmp = tempfile.mkdtemp(prefix="schedule-selftest-")
    rows, caught = [], []

    class Meeting:
        def __init__(self, parties):
            self.parties, self.cond, self.inside, self.met = parties, threading.Condition(), set(), False

        def hold(self, name, secs):
            end = time.monotonic() + secs
            with self.cond:
                self.inside.add(name)
                if len(self.inside) >= self.parties:
                    self.met = True
                    self.cond.notify_all()
                while not self.met and time.monotonic() < end:
                    self.cond.wait(max(0.0, end - time.monotonic()))
                self.inside.discard(name)

    def fixture(fail=(), raises=(), outputs=None, meet=True):
        """the stand-ins: the three browser suites the longest (as the real estimates have them), three non-browser that meet,
        three more short; a run's concurrency, its intervals and its meetings recorded"""
        stubs = [(b, ["<stub:%s>" % b], r"^STUB (\d+)/(\d+)$", 200 - i) for i, b in enumerate(LISTED)]
        stubs += [("n%d" % i, ["<stub:n%d>" % i], r"^STUB (\d+)/(\d+)$", 100 - i) for i in range(1, 7)]
        rec = {"now": 0, "max": 0, "spans": [], "lock": threading.Lock(), "t0": time.perf_counter()}
        mb, mn = Meeting(2), Meeting(3)

        def runner(name, args, pattern, root, env=None):
            with rec["lock"]:
                rec["now"] += 1
                rec["max"] = max(rec["max"], rec["now"])
                t = time.perf_counter() - rec["t0"]
            try:
                if meet and name in BROWSER:
                    mb.hold(name, HOLD)
                elif meet and name in ("n1", "n2", "n3"):
                    mn.hold(name, NHOLD)
                else:
                    time.sleep(0.05)
                if name in raises:
                    raise RuntimeError("planted: the runner raised for %s" % name)
                ok = name not in fail
                out = (outputs or {}).get(name, "a stand-in's output\n") + ("STUB 1/1\n" if ok else "STUB 0/1\n")
                return {"name": name, "rc": 0 if ok else 1, "summary": "STUB %s/1" % (1 if ok else 0), "ok": ok, "seconds": 0.0, "output": out}
            finally:
                with rec["lock"]:
                    rec["now"] -= 1
                    rec["spans"].append((name, t, time.perf_counter() - rec["t0"]))
        return stubs, runner, rec, mb, mn

    def bounded(fn, secs=60):
        box = {}
        th = threading.Thread(target=lambda: box.setdefault("v", fn()), daemon=True)
        th.start()
        th.join(secs)
        return box.get("v")                                # None: it did not end inside its bound (a hang)

    def quiet(_s):
        pass

    def lane_run(stubs, runner, look=None, parallel=False, secs=60):
        got = bounded(lambda: run_all(stubs, JOBS, tmp, quiet, runner=runner, lane=Lane(BROWSER, look=look), parallel_browsers=parallel), secs)
        if got is None:
            return None, None, None
        res, lane = got
        return res, lane, lane.verdict({s[0] for s in stubs})

    def scenario_main(parallel=False, look=lambda tok: [], meet=True, extra=(), keep=None):
        stubs, runner, rec, _mb, _mn = fixture(meet=meet)
        if keep is not None:
            keep.update(rec)
        log = os.path.join(tmp, "main-%d.log" % len(os.listdir(tmp)))
        out = []
        saved = sys.stdout

        class Grab:
            def write(self, s):
                out.append(s)

            def flush(self):
                pass
        sys.stdout = Grab()
        try:
            rc = bounded(lambda: main(["--jobs", str(JOBS), "--log", log] + list(extra), suites_set=stubs, runner=runner, look=look, parallel_browsers=parallel))
        finally:
            sys.stdout = saved
        text = "".join(out)
        last = [ln for ln in text.splitlines() if ln.startswith("ART SELFTESTS ") and ("PASSED" in ln or "FAILED" in ln)][-1:] or [""]
        return rc, last[0], text

    rows_spec = []

    def row(name, fn):
        rows_spec.append((name, fn))

    def r_honest():
        stubs, runner, rec, mb, mn = fixture()
        res, lane, broken = lane_run(stubs, runner, secs=90)
        if res is None:
            return False, "the run did not end in 90 s"
        bspans = [(n, a, b) for n, a, b in rec["spans"] if n in BROWSER]
        beside = any(n not in BROWSER and a < bb and b > ba for n, a, b in rec["spans"] for _x, ba, bb in bspans)
        ok = not broken and all(r["ok"] for r in res) and not mb.met and mn.met and rec["max"] == JOBS and beside
        return ok, "the law %s; the lane %s; the browsers met %s; three others met %s; at most %d at once (jobs %d); another beside a browser %s" % (
            "held" if not broken else "BROKEN: " + "; ".join(broken), lane.line(), mb.met, mn.met, rec["max"], JOBS, beside)

    def r_main():
        rc, last, text = scenario_main(meet=False)
        ok = rc == 0 and last.startswith("ART SELFTESTS PASSED") and "the browser lane held, one at a time in order" in text
        return ok, "exit %s; %s" % (rc, last[:90])

    def r_main_verdict():
        rc, last, text = scenario_main(parallel=True)
        if rc is None:
            return False, "main() did not end in 60 s"
        held, over = "held the browser lane" in text, "overlapped" in text
        ok = rc == 1 and last.startswith("ART SELFTESTS FAILED") and "the browser suites' law broken in run 1" in last and held and over
        return ok, "the browser suites run as any other: exit %s; the record: entered while held %s, overlapped %s; %s" % (rc, held, over, last[:110])

    def r_failing():
        stubs, runner, _rec, _mb, _mn = fixture(fail=("page-cards",), outputs={"page-cards": "a planted failure's own words\n"}, meet=False)
        res, lane, broken = lane_run(stubs, runner)
        if res is None:
            return False, "the run did not end in 60 s"
        by = {r["name"]: r for r in res}
        ran = {n: by[n]["output"] != "not run (the scheduler ended without it)" for n in ("page-worlds", "page")}
        kept = "a planted failure's own words" in by["page-cards"]["output"]
        ok = by["page-cards"]["rc"] == 1 and not by["page-cards"]["ok"] and kept and by["page-worlds"]["ok"] and by["page"]["ok"] and not broken
        return ok, "page-cards exit %s, its output kept %s; then page-worlds %s, page %s%s; the law %s" % (
            by["page-cards"]["rc"], kept, by["page-worlds"]["summary"] if ran["page-worlds"] else "not run", by["page"]["summary"] if ran["page"] else "not run",
            " (no suite stops another)" if all(ran.values()) else " (the lane stopped after page-cards)", "held" if not broken else "BROKEN")

    def r_raising():
        stubs, runner, _rec, _mb, _mn = fixture(raises=("page-worlds",), meet=False)
        res, lane, broken = lane_run(stubs, runner, secs=20)
        if res is None:
            return False, "the run did not end in 20 s: the lane was never let go"
        by = {r["name"]: r for r in res}
        ok = by["page-worlds"]["rc"] is None and "planted: the runner raised" in by["page-worlds"]["output"] and by["page"]["ok"] and not broken
        return ok, "page-worlds: exit %s, %s; then page %s; the law %s" % (by["page-worlds"]["rc"], by["page-worlds"]["output"].splitlines()[0][:60],
                                                                            by["page"]["summary"], "held" if not broken else "BROKEN")

    def r_only():
        rec = {}
        rc, last, text = scenario_main(meet=False, extra=("--only", "page,n4,page-worlds"), keep=rec)
        if rc is None:
            return False, "main() did not end in 60 s"
        order = [n for n, _a, _b in sorted(rec["spans"], key=lambda x: x[1]) if n in BROWSER]
        first = [b for b in LISTED if b in ("page", "page-worlds")][0]
        return rc == 0 and order == ["page-worlds", "page"], "through main(), --only page,n4,page-worlds (listed %s first): exit %s; the lane ran %s" % (
            first, rc, " then ".join(order))

    def r_one_job():
        stubs, runner, rec, _mb, _mn = fixture(meet=False)
        got = bounded(lambda: run_all(stubs, 1, tmp, quiet, runner=runner, lane=Lane(BROWSER)))
        if got is None:
            return False, "the run did not end in 60 s"
        res, lane = got
        broken = lane.verdict({s[0] for s in stubs})
        return rec["max"] == 1 and not broken and all(r["ok"] for r in res), "--jobs 1: at most %d at once; the law %s" % (
            rec["max"], "held" if not broken else "BROKEN")

    def r_reader():
        fx = os.path.join(tmp, "reader")
        os.makedirs(fx, exist_ok=True)
        for f, text in READER.items():
            with open(os.path.join(fx, f), "wb") as fh:
                fh.write(text.encode("utf-8"))
        written = sorted(f for f in os.listdir(fx) if f.endswith(".py")) == sorted(READER)
        found, unread = browser_suites(READER_SUITES, art=fx)
        missed, wrong = sorted(set(READER_WANT) - set(found)), sorted(set(found) - set(READER_WANT))
        return written and not missed and not wrong and unread == ["g"], "the fixture written %s; found %s; missed: %s; counted wrongly: %s; not read: %s (a flag play.py's main() has no branch for)" % (
            written, ", ".join(sorted(found)) or "none", ", ".join(missed) or "none", ", ".join(wrong) or "none", ", ".join(unread) or "none")

    def r_register():
        reg = [b for b in BROWSER if SCHEDULE_PLANT != "browser-unregistered" or b != "page"]
        found, unread = browser_suites(SUITES)
        alias, _u = browser_suites((("alias", ["art/page_test.py", "selftest"], "", 0),))
        extra, short = sorted(set(found) - set(reg)), sorted(set(reg) - set(found))
        ok = not unread and not extra and not short and alias == ["alias"]
        return ok, "read from the code, the suites that start a page test's browser: %s; the register: %s; read and not registered: %s; registered and not read: %s; entries not read: %s; art/page_test.py selftest read as one: %s" % (
            ", ".join(sorted(found)), ", ".join(sorted(reg)), ", ".join(extra) or "none", ", ".join(short) or "none", ", ".join(unread) or "none", bool(alias))

    def r_witness():
        stubs, runner, _rec, _mb, _mn = fixture(meet=False, outputs={"n5": "OBSERVED stub: the browser ended in 1.0 s\n"})
        res, lane, broken = lane_run(stubs, runner)
        if res is None:
            return False, "the run did not end in 60 s"
        seen = [v for v in broken if "outside the browser lane" in v]
        return any("n5, a suite outside the browser lane, ended a browser" in v for v in seen), "a suite outside the lane that ended a browser: %s" % (
            "; ".join(seen) or "not seen")

    def r_look():
        stubs, runner, _rec, _mb, _mn = fixture(meet=False)
        looks = iter([[], ["4242 msedge.exe"], []])
        res, lane, broken = lane_run(stubs, runner, look=lambda: next(looks, []))
        if res is None:
            return False, "the run did not end in 60 s"
        seen = [v for v in broken if "processes stood" in v]
        return any("entered while this run's page-test browser processes stood: 4242 msedge.exe" in v for v in seen), \
            "a browser of an earlier suite standing when the next entered: %s" % ("; ".join(seen) or "not seen")

    def r_unknown():
        rc, last, text = scenario_main(look=lambda tok: ["unknown"], meet=False)
        if rc is None:
            return False, "main() did not end in 60 s"
        ok = rc == 1 and last.startswith("ART SELFTESTS FAILED") and "the look could not be made (unknown, never nothing)" in text
        return ok, "every look unknown: exit %s; %s" % (rc, last[:100])

    def r_close():
        stubs, runner, _rec, _mb, _mn = fixture(meet=False)
        looks = iter([[], [], [], ["4343 msedge.exe"]])
        res, lane, broken = lane_run(stubs, runner, look=lambda: next(looks, []))
        if res is None:
            return False, "the run did not end in 60 s"
        seen = [v for v in broken if v.startswith("after the last browser suite")]
        return any("4343 msedge.exe" in v for v in seen), "a browser of this run standing after the last browser suite: %s" % ("; ".join(seen) or "not seen")

    def r_env():
        tok = secrets.token_hex(8)
        probe = os.path.join(tmp, "env_probe.py")
        with open(probe, "wb") as fh:
            fh.write(ENV_PROBE.encode("utf-8"))
        stubs = [("page", [probe], r"^STUB (\d+)/(\d+)$", 2), ("n1", [probe], r"^STUB (\d+)/(\d+)$", 1)]
        got = bounded(lambda: run_all(stubs, JOBS, tmp, quiet, lane=Lane(BROWSER), token=tok), 120)
        if got is None:
            return False, "the run did not end in 120 s"
        by = {r["name"]: r for r in got[0]}

        def given(name):
            m = re.search(r"^FULL=(\S*) TOKEN=(\S*)$", by[name]["output"].replace("\r", ""), re.M)
            return (m.group(1) == "1", m.group(2)) if m else (None, None)
        (pw, pt), (nw, nt) = given("page"), given("n1")
        ok = pw is True and pt == tok and nw is True and nt == "" and all(r["ok"] for r in got[0])
        return ok, "run_one's processes: page: the full check's word %s, the run's token %s; n1: the full check's word %s, a token %s" % (
            "given" if pw else "not given", "given" if pt == tok else "not given", "given" if nw else "not given", "given" if nt else "not given")

    def r_guard():
        tok = secrets.token_hex(8)
        prof = os.path.join(tmp, "page-test-profile-page-cards-x")                    # made by hand: no token

        def ask(name, profile):
            env = suite_env(name, tok)
            if SCHEDULE_PLANT in ("guard-off", "launch-untokened"):
                env["VERDANDI_PLANT"] = SCHEDULE_PLANT
            try:
                cp = subprocess.run([sys.executable, "-B", "-c", GUARD, HERE, profile, os.path.join(tmp, "guard.log")], env=env,
                                    capture_output=True, timeout=120, stdin=subprocess.DEVNULL)
            except (OSError, subprocess.SubprocessError) as e:
                return "the guard's process failed: %s" % e
            lines = [ln.strip() for ln in cp.stdout.decode("utf-8", "replace").splitlines() if ln.strip()]
            return lines[-1] if lines else "nothing said (exit %s): %s" % (cp.returncode, cp.stderr.decode("utf-8", "replace")[-160:])
        out_n, out_b, out_u, out_s = ask("n1", "made"), ask("page", "made"), ask("page", prof), ask("page", "scratch")
        ok = (out_n.startswith("BROWSER-OUTSIDE-LANE") and out_b.startswith("LET THROUGH") and out_u.startswith("BROWSER-UNTOKENED")
              and out_s.startswith("BROWSER-UNTOKENED"))
        return ok, "launch (art/page_test.py) in a process with a suite's environment: outside the lane: %s; a browser suite, its profile made by page_test: %s; a browser suite, a profile without the token: %s; a browser suite, its scratch folder (the token, not profile_of's name) as the profile: %s" % (
            out_n[:60], out_b[:30], out_u[:40], out_s[:40])

    def r_look_real():
        tok, other = secrets.token_hex(8), secrets.token_hex(8)
        env = suite_env("page-cards", tok)
        if SCHEDULE_PLANT == "scratch-untokened":
            env["VERDANDI_PLANT"] = "scratch-untokened"
        try:
            cp = subprocess.run([sys.executable, "-B", "-c", PROFILE, HERE], env=env, capture_output=True, timeout=120, stdin=subprocess.DEVNULL)
            prof = (cp.stdout.decode("utf-8", "replace").strip().splitlines() or [""])[-1]
        except (OSError, subprocess.SubprocessError) as e:
            return False, "the profile's process failed: %s" % e
        if "page-test-profile-" not in prof:
            return False, "page_test made no profile: %r" % prof[:120]
        exe = getattr(sys, "_base_executable", None) or sys.executable    # one process each (a venv's python.exe is two)

        def sleeper(arg):
            return subprocess.Popen([exe, "-c", "import time; time.sleep(120)", arg], stdin=subprocess.DEVNULL,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        def look():
            seen = standing(tok)
            return standing(tok) if seen == ["unknown"] else seen
        mine = sleeper("--user-data-dir=" + prof)                                                          # this run's, as page_test makes it
        decoys = [sleeper("--user-data-dir=" + os.path.join(tmp, "page-test-profile-page-cards-%s-x2" % other)),   # another run's
                  sleeper("rg -n page-test-profile- ."),                                                           # a search
                  sleeper("--root=" + os.path.join(tmp, "page-cards-%s-x3" % tok))]                                # this run's, no profile
        try:
            seen = look()
        finally:
            for p in [mine] + decoys:
                p.kill()
                p.wait()
        after = look()
        if seen == ["unknown"] or after == ["unknown"]:
            return False, "the look could not be made, twice (unknown, never nothing)"
        pids = [x.split()[0] for x in seen]
        counted = sorted({str(d.pid) for d in decoys} & set(pids))
        ok = pids == [str(mine.pid)] and after == []
        return ok, "this run's browser found %s; a decoy counted %s; gone after it ended %s (its profile as page_test made it: %s; seen %s)" % (
            str(mine.pid) in pids, bool(counted), after == [], os.path.basename(prof), ", ".join(seen) or "nothing")

    row("schedule: the browser suites one at a time in the registered order, the others beside them, at most --jobs at once (the honest lane)", r_honest)
    row("schedule: through main(), the honest lane passes and says it held", r_main)
    row("schedule: through main(), browser suites run together are a failed run (exit 1, FAILED, the law named; one entered while another held, and their spans overlapped)", r_main_verdict)
    row("schedule: a failing browser suite keeps its exit status and its output, and the next still runs (no suite stops another)", r_failing)
    row("schedule: a browser suite whose runner raises is a failed result, and the lane is let go (the run ends)", r_raising)
    row("schedule: through main(), --only keeps the registered order, whatever order the suites are listed in", r_only)
    row("schedule: --jobs 1 runs one suite at a time, the lane's law held", r_one_job)
    row("schedule: the register's reader follows a browser through the shapes an entry can take, and counts none of the shapes that start none (a fixture)", r_reader)
    row("schedule: the register is every suite the code shows starting a page test's browser", r_register)
    row("schedule: a browser ended by a suite outside the lane breaks the law (the witness)", r_witness)
    row("schedule: this run's page-test browser standing at the next entry breaks the law (the look)", r_look)
    row("schedule: a look that cannot be made fails the run (unknown, never nothing)", r_unknown)
    row("schedule: this run's page-test browser standing after the last browser suite breaks the law (the closing look)", r_close)
    row("schedule: run_one gives every suite's process the full check's word, and the run's token to a browser suite only", r_env)
    row("schedule: inside the full check launch refuses a page test's browser to a suite outside the lane and a profile not made by scratch and profile_of, and lets a browser suite's own through", r_guard)
    row("schedule: the look finds this run's browser, its profile made by page_test's own code, and no decoy (this machine's processes)", r_look_real)
    # each plant's row (its index in rows_spec) and the words its row's detail must hold: its own reason
    PLANT_ROWS = {"browsers-parallel": (0, "held the browser lane"), "browsers-reversed": (0, "ran page then page-worlds then page-cards, not the registered"),
                  "lane-listed-order": (0, "ran %s, not the registered" % " then ".join(LISTED)),
                  "all-serial": (0, "another beside a browser False"),
                  "verdict-ignores-law": (2, "exit 0; the record: entered while held True, overlapped True"),
                  "record-blind": (2, "entered while held False, overlapped False"),
                  "lane-stops-on-failure": (3, "page-worlds not run"), "lane-not-released-on-raise": (4, "did not end in 20 s"),
                  "reader-local": (7, "missed: a, b, bs"), "reader-flat": (7, "counted wrongly: o"),
                  "reader-first-branch": (7, "missed: a, b; counted wrongly: none"), "reader-skips-main": (7, "missed: dl, k0, k1, p5, t; counted wrongly: none"),
                  "reader-no-assign": (7, "missed: v, v2, v3; counted wrongly: none"), "reader-no-dunder-main": (7, "missed: none; counted wrongly: u5"),
                  "reader-unscoped": (7, "missed: none; counted wrongly: u7"), "reader-main-branches-only": (7, "missed: k0, k1; counted wrongly: none"),
                  "browser-unregistered": (8, "read and not registered: page;"),
                  "witness-blind": (9, "a suite outside the lane that ended a browser: not seen"),
                  "look-ignored": (10, "standing when the next entered: not seen"), "look-unknown-as-nothing": (11, "every look unknown: exit 0"),
                  "closing-look-skipped": (12, "after the last browser suite: not seen"),
                  "env-dropped": (13, "the run's token not given"), "token-to-all": (13, "n1: the full check's word given, a token given"),
                  "guard-off": (14, "outside the lane: LET THROUGH"), "launch-untokened": (14, "a profile without the token: LET THROUGH"),
                  "look-generic": (15, "this run's browser found True; a decoy counted True"),
                  "scratch-untokened": (15, "this run's browser found False; a decoy counted False")}

    def run_rows(stop_at=None, show=True):
        out = []
        for i, (name, fn) in enumerate(rows_spec):
            try:
                ok, detail = fn()
            except Exception as e:  # noqa: BLE001 — a row that raised fails, and says why
                ok, detail = False, "raised %s: %s" % (type(e).__name__, str(e)[:160])
            out.append((name, bool(ok), detail))
            if show:
                print("[%s] %s — %s" % ("PASS" if ok else "FAIL", name, detail), flush=True)
            if stop_at is not None and i >= stop_at:
                break
        return out
    hook = threading.excepthook
    try:
        rows = run_rows()
        # the raise lane-not-released-on-raise plants is the plant's own; any other thread's is printed as ever
        threading.excepthook = lambda a: None if "planted: the runner raised" in str(a.exc_value) else hook(a)
        for plant in SCHEDULE_PLANTS:
            SCHEDULE_PLANT = plant
            k, why = PLANT_ROWS[plant]
            try:
                got = run_rows(stop_at=k, show=False)
            finally:
                SCHEDULE_PLANT = ""
            ok = len(got) == k + 1 and not got[k][1] and why in got[k][2] and all(x[1] for x in got[:k])
            caught.append(ok)
            print("[%s] schedule plant %s caught — %s" % ("PASS" if ok else "FAIL", plant,
                                                         ("by: %s — %s" % (got[k][0][:80], got[k][2][:220])) if ok else
                                                         "NOT CAUGHT (its row must fail saying %r): " % why +
                                                         "; ".join("%s %s — %s" % ("PASS" if x[1] else "FAIL", x[0][:50], x[2][:160]) for x in got[max(0, k - 1):])), flush=True)
    finally:
        threading.excepthook = hook
        SCHEDULE_PLANT = ""
        SCHEDULING_ONLY = False
        shutil.rmtree(tmp, ignore_errors=True)
    n = sum(1 for r in rows if r[1]) + sum(caught)
    print("SCHEDULE SELFTEST %d/%d" % (n, len(rows) + len(SCHEDULE_PLANTS)))
    return 0 if n == len(rows) + len(SCHEDULE_PLANTS) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
