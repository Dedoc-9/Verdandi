# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/page_test.py — PAGE-0 (0246): the studio page executed by a test, in a real browser, through its own controls.
#
#   python art/play.py --page-selftest [--browser EXE] [--headed]       (python art/page_test.py selftest, the same)
#
# Before it no test ran the page's script: the suites called the studio's routes from Python and gave it synthetic
# stills, so whatever the page itself does (its keys, its buttons, the still it takes of its own canvas, the preview it
# draws with the native renderer) was held by nothing (docs/CAPABILITY-MATRIX.md, F-5; lesson 75). Here the flagship's
# edit (FLAGSHIP-0) is made through the page's own controls, in the order a person makes it: a browser opens the page,
# headless (--browser EXE or VERDANDI_BROWSER; else on Windows Edge, then Chrome; elsewhere microsoft-edge, google-chrome,
# chromium or chromium-browser, the first on PATH); art/web/page_test.js, in a page of the same origin that holds the
# studio page in a frame, takes the host's steps one at a time and does each with the page's own controls — Enter summons
# the director, the shape's tag goes into the prompt, Strict is ticked, Ask is pressed, the card's Preview, Admit and Show,
# the drawer's Undo and Original — each pressed where it is (the point hit-tested first: a control something covers is
# said, never clicked through). The key and the click are synthetic events, not a person's hand, and the camera for the
# admission's still is put on the request's path by a hook (PLAY.cam).
#
# The page decides nothing here, as it decides nothing in the studio. After each step the host reads its own state —
# the request, the ledger, the certificate, the preview's report, the scenes it serves, the stills the page gave it, read
# as PNG — and holds the step to it (every step but the opening, which rests on what the page reports); what the page
# reports is what it showed a person (its status line, its toasts, a card's buttons and chips, the preview's badge), and
# a row holds that the page said what happened. The stills are the first in any suite drawn by
# the native renderer (art/web/scene_render.js): the preview's sixteen by the page's thumbnailer, the admission's from its
# canvas; their detectors are read by the host and printed (OBSERVED: a detector proves nothing).
#
# Its plants. Through the page, in the honest run (each must show its code in the page and leave the world as it was):
# a region refused (the column's card: strict FAIL, Admit cannot be pressed); a failing preview (one run's state carried
# into the next: the page's window says the states differ); a still the host never received (the page says
# STUDIO-NO-STILL); a stale head (the brief edited after the preview: STUDIO-STALE). Of the harness itself, each a whole run
# with its rows silenced, caught when the row it breaks fails: the page's Admit unwired (a control whose handler is gone)
# and a page that skips its still, each caught by the admission's row; and (0247) the host's wait for the live loop taken
# away, caught by the Show and Original row. The browser's name and its GPU as the browser reports them are printed as OBSERVED
# context, never as a claim. Standard library only.

import json
import os
import queue
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

WINDOWS = os.name == "nt"
PLANT = ""
LAST = {}                            # what the last run met at the Show and Original row (the live plant's count reads it)
PLANTS = ("page-admit-unwired", "page-still-skipped", "page-live-unwaited")
# the planted copies of play.js: (the text replaced, its replacement); each must occur exactly once. page-live-unwaited
# (0247) is the harness's own: the host's wait for the live loop taken away, nothing of the page changed
PLANT_EDITS = {
    "page-admit-unwired": ("const admitWithStill = function (rid, c) {", "const admitWithStill = function (rid, c) { return;"),
    "page-still-skipped": (".then(function () { return takeStill(rid, c.letter); })", ".then(function () { return { ok: true, still: \"\", flags: [] }; })"),
}
# the row each harness plant must fail
PLANT_ROWS = {"page-admit-unwired": "page: Admit pressed", "page-still-skipped": "page: Admit pressed",
              "page-live-unwaited": "page: Show pressed"}
VIEW = (960, 540)                    # the page's canvas (?w=&h=): the admission's still is this size
WINDOW = (1700, 1000)                # the browser's window; the page under test is a 1600 x 900 frame in it


class PageLost(RuntimeError):
    """The page stopped answering, its browser ended, or the run's time is spent: the run ends at once (its later steps
    would each wait out their whole time, past the full check's limit)."""


class Channel:
    """The host's steps and the page's answers, one at a time. The page posts its last result and is answered the next
    step (or "wait" after 20 s, and asks again); the host puts a step and waits for the answer that names it. A step the
    page does not answer, a browser that has ended (alive), or a run past its deadline raises PageLost, and every step
    after it too."""

    def __init__(self, deadline, alive=None):
        self.steps, self.results, self.n = queue.Queue(), queue.Queue(), 0
        self.deadline, self.alive, self.lost = deadline, alive or (lambda: True), ""

    def exchange(self, body):
        r = body.get("result") if isinstance(body, dict) else None
        if isinstance(r, dict):
            self.results.put(r)
        try:
            return dict(self.steps.get(timeout=20), ok=True)
        except queue.Empty:
            return {"ok": True, "do": "wait"}

    def do(self, step, timeout):
        if self.lost:
            raise PageLost(self.lost)
        self.n += 1
        n, what = self.n, step.get("do", "?")
        left = self.deadline - time.time()
        if left <= 0:
            self.lost = "the run's time was spent before step %d (%s)" % (n, what)
            raise PageLost(self.lost)
        timeout = min(timeout, left)
        self.steps.put(dict(step, n=n, timeout_ms=int(timeout * 1000)))
        end = time.time() + timeout + 30
        while time.time() < end:
            try:
                r = self.results.get(timeout=1.0)
            except queue.Empty:
                if not self.alive():
                    self.lost = "the browser ended before the page answered step %d (%s)" % (n, what)
                    raise PageLost(self.lost)
                continue
            if r.get("n") == n:
                return r
        self.lost = "no answer from the page to step %d (%s) in %d s" % (n, what, timeout + 30)
        raise PageLost(self.lost)


# ------------------------------------------------------------------------------------------------ the browser
def find_browser(argv=()):
    """--browser EXE, VERDANDI_BROWSER, or the desktop studio's own finder (on Windows Edge, then Chrome; elsewhere the first
    of microsoft-edge, google-chrome, chromium and chromium-browser on PATH)."""
    if "--browser" in argv and argv.index("--browser") + 1 < len(argv):
        return argv[argv.index("--browser") + 1]
    if os.environ.get("VERDANDI_BROWSER"):
        return os.environ["VERDANDI_BROWSER"]
    import studio_app
    return studio_app.find_browser()


def launch(browser, url, profile, headed, log_path):
    argv = [browser, "--user-data-dir=%s" % profile, "--no-first-run", "--no-default-browser-check", "--disable-extensions",
            "--disable-background-networking", "--disable-sync", "--disable-component-update", "--window-size=%d,%d" % WINDOW,
            "--enable-logging=stderr", "--log-level=0"]
    if headed:
        # a window of its own: kept drawing when covered or in the background (a hidden page draws no frame, and the
        # page's still and preview wait on frames)
        argv += ["--disable-backgrounding-occluded-windows", "--disable-renderer-backgrounding", "--disable-background-timer-throttling"]
    else:
        argv += ["--headless=new"]
    if not WINDOWS:
        argv += ["--enable-unsafe-swiftshader"]
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            argv += ["--no-sandbox"]
    if WINDOWS:
        # the browser started by a holder in a job of its own (KILL_ON_JOB_CLOSE, the desktop studio's Job): every process
        # the browser starts is in it whatever its parent, and ends when the holder does. (taskkill /T, before it, left
        # one of the tree's processes standing 20 s after, once, with twenty-five suites run sixteen at once; under that
        # load the job's processes were gone by 14.5 s and 15.2 s after, in two runs: upper bounds, the time of the first
        # look that found none, the looks a 1 s pause and a query apart. So end_browser waits 60 s)
        return subprocess.Popen([sys.executable, "-B", "-c", HOLDER, HERE, log_path] + argv + [url], stdin=subprocess.PIPE,
                                stdout=subprocess.DEVNULL, stderr=open(log_path, "ab"))
    # elsewhere a session of its own, ended as a group below; on Linux also ended by the kernel if this process ends without
    # ending it (killed at a suite's timeout, it runs no finally): PR_SET_PDEATHSIG, resolved here, called in the child
    pre = None
    if sys.platform.startswith("linux"):
        try:
            import ctypes
            prctl = ctypes.CDLL(None, use_errno=True).prctl
            pre = lambda: prctl(1, 9)                       # noqa: E731 — PR_SET_PDEATHSIG, SIGKILL
        except (OSError, AttributeError):
            pre = None
    return subprocess.Popen(argv + [url], stdout=open(log_path, "ab"), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                            start_new_session=True, preexec_fn=pre)


# the holder: joins a job of its own, starts the browser in it, and ends when its input closes (or when it is ended), its
# job then closing and the browser's every process with it; or when nothing but itself is left in its job, the browser
# having ended on its own (its first process hands off to another and ends at once: Edge, OBSERVED once, not kept)
HOLDER = r'''
import os, subprocess, sys, threading, time
sys.path.insert(0, sys.argv[1])
import studio_app
job = studio_app.Job()
p = subprocess.Popen(sys.argv[3:], stdout=open(sys.argv[2], "ab"), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
threading.Thread(target=lambda: (sys.stdin.read(), os._exit(0)), daemon=True).start()
me = os.getpid()
while True:
    time.sleep(0.5)
    left = job.pids()
    if left is not None and not [x for x in left if x != me]:
        os._exit(3)
'''


def leftovers(marker, kill=False):
    """The processes whose command line names the test's own profile folder, each as 'pid name'; ["unknown"] when the
    query could not be made or did not succeed (a failed query is never 'nothing left'). The query reads every process's
    command line; only those naming the marker are kept, and nothing else of them. With kill, those it finds are ended in
    the same query (so that a pid is never ended after it could be another's)."""
    try:
        if WINDOWS:
            # the query's own process names the marker too: it is left out ($PID)
            q = "Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -like '*%s*' }" % marker
            q += " | ForEach-Object { '{0} {1}' -f $_.ProcessId, $_.Name; %s }" % ("[void](Invoke-CimMethod -InputObject $_ -MethodName Terminate)" if kill else "")
            cp = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", q], capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
            if cp.returncode != 0:
                return ["unknown"]
            return [ln.strip() for ln in cp.stdout.decode("utf-8", "replace").splitlines() if ln.strip()[:1].isdigit() and ln.split()[0] != str(os.getpid())]
        if kill:
            subprocess.run(["pkill", "-KILL", "-f", marker], capture_output=True, timeout=30, stdin=subprocess.DEVNULL)
            return []
        cp = subprocess.run(["ps", "-eo", "pid=,comm=,args="], capture_output=True, timeout=30, stdin=subprocess.DEVNULL)
        if cp.returncode != 0:
            return ["unknown"]
        return [" ".join(ln.split()[:2]) for ln in cp.stdout.decode("utf-8", "replace").splitlines() if marker in ln and "ps -eo" not in ln]
    except (OSError, subprocess.SubprocessError):
        return ["unknown"]


def end_browser(p, marker):
    """The browser's whole tree ended: on Windows the holder's input closed (its job ends the tree), and the holder ended
    if it has not; elsewhere the browser's session killed. Returns (what is left after up to 60 s, each 'pid name'; what
    stood at the first look; the seconds it took). What is left is then ended, and said all the same."""
    t0 = time.time()
    if p is not None and p.poll() is None:
        try:
            if WINDOWS:
                p.stdin.close()
                try:
                    p.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    p.kill()
            else:
                import signal
                os.killpg(p.pid, signal.SIGKILL)
        except (OSError, subprocess.SubprocessError):
            pass
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
    left = leftovers(marker)
    first = list(left)
    while left and time.time() - t0 < 60:
        time.sleep(1)
        left = leftovers(marker)
    took = time.time() - t0
    if left:
        leftovers(marker, kill=True)          # not to pass the row (it has failed): so that nothing of the run outlives it
    return left, first, took


def png_size(path):
    """(width, height) of a PNG file, from its header; None if it is not one."""
    try:
        with open(path, "rb") as fh:
            b = fh.read(33)
        if b[:8] != b"\x89PNG\r\n\x1a\n" or b[12:16] != b"IHDR":
            return None
        return struct.unpack(">II", b[16:24])
    except OSError:
        return None


# ------------------------------------------------------------------------------------------------ the run
def run(browser, headed, argv_plant="", say=None):
    """One run of the page through the flagship's edit (and, honest, the plants through the page). [(name, ok, detail)],
    [OBSERVED lines]."""
    import play
    import motion
    import quality
    import flagship
    rows, seen = [], []
    LAST.clear()

    def row(name, ok, detail):
        rows.append((name, bool(ok), detail))
        if say:
            say("[%s] %s — %s" % ("PASS" if ok else "FAIL", name, detail))
    tmp = tempfile.mkdtemp(prefix="page-selftest-")
    marker = "page-test-profile-" + os.path.basename(tmp)
    profile = os.path.join(tmp, marker)
    saved = (play.ROOT, motion.PLANT, play.studio_still, dict(play.FILES))
    live = srv = proc = live_gate = None
    alive = []
    D = play.director()
    W = flagship.WORLD
    try:
        os.makedirs(os.path.join(tmp, "art", "briefs"))
        os.makedirs(os.path.join(tmp, "graybox", "maps"))
        for f in os.listdir(os.path.join(REPO, "graybox", "maps")):
            shutil.copy(os.path.join(REPO, "graybox", "maps", f), os.path.join(tmp, "graybox", "maps", f))
        art = os.path.join(tmp, "art", "briefs", W + ".art")
        original = open(os.path.join(HERE, "briefs", W + ".art"), "rb").read().replace(b"\r\n", b"\n")
        open(art, "wb").write(original)
        ws = D.Workspace(W, tmp)
        D.cmd_genesis_quiet(ws)
        if argv_plant in PLANT_EDITS:
            old, new = PLANT_EDITS[argv_plant]
            js = open(play.FILES["/play.js"][0], "rb").read().decode("utf-8")
            if js.count(old) != 1:
                raise RuntimeError("the plant %s's text occurs %d times in play.js, not once" % (argv_plant, js.count(old)))
            planted = os.path.join(tmp, "play.js")
            open(planted, "wb").write(js.replace(old, new).encode("utf-8"))
            play.FILES["/play.js"] = (planted, play.FILES["/play.js"][1])
        play.ROOT = tmp
        live = play.Live(W, art, [], poll=0.15, root=tmp)
        # 0247: the live loop serves a write of the files one compile after it sees it (it is eventually the files'). His
        # run of 0246 read the world it served before the loop caught up with the undo, and the row failed; a trace on his
        # machine, by the agent, met the same race in an ordinary run, its read 0.13 s too soon (MEASURED once). Its recompiles now pass through a gate the honest run holds closed from the
        # undo until it has read the world served (the admitted scene still), so that the race is met in every run; then
        # it opens the gate and waits for the loop to serve the files' head before anything is compared against it
        live_gate = threading.Event()
        live_gate.set()
        real_recompile = live.recompile

        def gated(only=None):
            live_gate.wait(600)
            return real_recompile(only)
        live.recompile = gated
        threading.Thread(target=live.watch, kwargs={"say": lambda s_: None}, daemon=True).start()
        play.start_studio(live, os.path.join(HERE, "providers", "scripted.json"), say=lambda s_: None)
        srv = play.server(live)
        base = "http://127.0.0.1:%d" % srv.server_address[1]
        tok = live.hub.token
        http = flagship.Http(base, tok)
        if not argv_plant:
            # unarmed, the studio serves no driver and keeps no step: the page test is not part of the product's surface
            try:
                with urllib.request.urlopen(base + "/page_test.html", timeout=30) as r_:
                    unarmed_page = r_.status
            except urllib.error.HTTPError as e:
                unarmed_page = e.code
            c_u, r_u = http.post("/studio/page-test", {"result": None})
            row("page: unarmed, the studio serves no driver (/page_test.html 404) and its channel is refused (STUDIO-ROUTE)",
                unarmed_page == 404 and c_u == 404 and r_u.get("code") == "STUDIO-ROUTE", "the driver %s; the channel %s %s" % (unarmed_page, c_u, r_u.get("code")))
        # the honest run's 900 s and each of the three plants' 200 s, 1,500 s, inside the full check's 1800 s for the whole
        # suite with room for each run's start and end (alone the honest run takes about a minute; under sixteen suites at
        # once it took up to about three)
        ch = Channel(time.time() + (200 if argv_plant else 900), alive=lambda: proc is not None and proc.poll() is None)
        live.hub.page_test = ch

        def snapshot():
            out, parts, _c = ws.export()
            return {"head": D.canon.head(parts), "brief_sha256": flagship.sha256(open(art, "rb").read()), "scene_sha256": flagship.sha256(out["scene_bytes"]),
                    "admits": [e for e in D.led.read(ws.ledger)[0] if e["kind"] == "admit"], "ledger_bytes": len(open(ws.ledger, "rb").read())}
        world = lambda w: {k: w[k] for k in ("head", "brief_sha256", "scene_sha256")} if w else {}

        def served_head(limit):
            """(whether the live loop serves the files' own scene in slot 0 within `limit` s, the seconds waited); never past
            the run's own deadline"""
            limit = min(limit, max(0.0, ch.deadline - time.time()))
            t0 = time.time()
            while True:
                if (live.slot(0) or {}).get("sha") == snapshot()["scene_sha256"]:
                    return True, time.time() - t0
                if time.time() - t0 > limit:
                    return False, time.time() - t0
                time.sleep(0.2)

        def get(path):
            try:
                with urllib.request.urlopen(base + path, timeout=60) as r:
                    return json.loads(r.read())
            except (urllib.error.URLError, OSError, ValueError):
                return {}

        def cand(title):
            st = live.studio.state()["request"] or {}
            return next((c for c in st.get("candidates", []) if c["title"] == title), None), st

        def wait_version(v):
            t0 = time.time()
            while live.version == v and time.time() - t0 < 120:
                time.sleep(0.1)

        if not browser:
            row("page: a browser to drive the page (Edge or Chrome; elsewhere Edge, Chrome or Chromium on PATH; --browser EXE)", False, "none found")
            return rows, seen
        proc = launch(browser, base + "/page_test.html", profile, headed, os.path.join(tmp, "browser.log"))
        t_open = time.time()
        r = ch.do({"do": "open", "url": "/play.html?world=%s&slot=0&w=%d&h=%d" % (W, VIEW[0], VIEW[1])}, 180)
        seen.append("OBSERVED page: the browser %s" % r.get("ua", "?"))
        seen.append("OBSERVED page: WebGL as the browser reports it: %s" % r.get("gpu", "?"))
        seen.append("OBSERVED page: opened and its shell built in %.1f s" % (time.time() - t_open))
        # the query that finds what is left must find the browser while it runs: a process of it, not the holder alone
        alive = [x for x in leftovers(marker) if x == "unknown" or not x.split()[-1].lower().startswith("python")]
        title = ws.export()[0]["scene"]["title"] + " — Verðandi Studio"
        row("page: the studio page opened in a real browser, its shell built (its title the brief's), its director read",
            r.get("ok") and r.get("title") == title and "scripted" in r.get("provider", "") and r.get("canvas") == list(VIEW) and r.get("slot") == 0,
            "%s; %s; canvas %s" % (r.get("title", r.get("error", "")), r.get("provider", ""), r.get("canvas")))
        if not r.get("ok"):
            return rows, seen

        # mark: the shape saved as FLAGSHIP-0 saves it (the page's own drawing of a region is MARK-0's), listed by the page
        mass = next(v for v in ws.export()[0]["scene"]["visuals"] if v["id"] == flagship.FLAGSHIP)
        c_s, r_s = http.post("/studio/shapes/save", {"shape": {"name": "bay", "operation": "region",
                                                               "anchor": {"piece": flagship.FLAGSHIP, "face": "+z", "box": mass["box"], "scene": live.slot(0)["sha"], "view": {}},
                                                               "vertices": flagship.VERTICES, "constraints": {"within": True, "supports": False, "collision": False, "material": "keep"}}})
        r = ch.do({"do": "shapes", "name": "bay"}, 30)
        row("page: the shape saved on the warehouse's face is listed in the page's drawer, as ok",
            c_s == 200 and (r_s.get("shape") or {}).get("status") == "ok" and r.get("ok") and r.get("tag") == "#bay" and not r.get("gone"),
            "saved %s %s; the page lists %s%s" % (c_s, (r_s.get("shape") or {}).get("status"), r.get("tag", r.get("error", "")), " (gone)" if r.get("gone") else ""))

        # the request, through the page
        head0 = snapshot()["head"]
        r = ch.do({"do": "ask", "words": "panel ", "shape": "bay", "strict": True}, 240)
        st = live.studio.state()["request"] or {}
        drawn = [c_ for c_ in st.get("candidates", []) if c_.get("slot") is not None]
        row("page: asked through the page (Enter, the shape's tag, Strict, Ask): the request strict, at the head it was asked at, its candidates drawn; the page says so",
            r.get("ok") and r.get("tag") == "pressed" and r.get("ask") == "pressed" and r.get("strict") is True and r.get("prompt", "").strip() == "panel #bay"
            and (r.get("status") or {}).get("good") and "asked" in (r.get("status") or {}).get("text", "") and (r.get("request") or {}).get("id") == st.get("id")
            and st.get("state") == "done" and st.get("strict") is True and st.get("head") == head0 and len(drawn) >= 1,
            "prompt %r; the page: %s; the drawer: %s; the host: request %s %s, strict %s, %d drawn" % (
                r.get("prompt"), (r.get("status") or {}).get("text", r.get("error", "")), r.get("drawer"), st.get("id"), st.get("state"), st.get("strict"), len(drawn)))
        rid = st.get("id")
        c1, _st = cand("Panelled bay")
        if c1 is None:
            raise RuntimeError("the request drew no Panelled bay")
        r = ch.do({"do": "card", "title": "Panelled bay"}, 30)
        chips = [x["text"] for x in r.get("chips", [])]
        imp = c1.get("impact") or {}
        held = ((c1.get("held") or {}).get("accounts") or [{}])[0].get("verdict")
        row("page: the Panelled bay's card shows strict PASS and its Admit can be pressed; the host holds it in the region, strict, with its impact",
            r.get("ok") and "strict PASS" in chips and not r.get("buttons", {}).get("Admit", {}).get("disabled", True)
            and held == "held" and (c1.get("strict") or {}).get("ok") is True and "delta" in imp and not imp.get("error"),
            "the card: %s, %s, Admit %s; the host: %s, strict %s, impact %s" % (r.get("badge", r.get("error", "")), chips,
                                                                             "disabled" if r.get("buttons", {}).get("Admit", {}).get("disabled", True) else "enabled",
                                                                             held, (c1.get("strict") or {}).get("ok"), "present" if "delta" in imp else imp.get("error")))
        letter = c1["letter"]

        def toasted(r_, bad, part):
            """a toast the page showed for the step (the word a person sees: the drawer's line is closed then), bad or not, naming part"""
            return any(bool(t.get("bad")) == bad and part in t.get("text", "") for t in r_.get("toasts") or [])
        if not argv_plant:
            # the preview, drawn by the page with the native renderer
            t_pv = time.time()
            r = ch.do({"do": "press", "title": "Panelled bay", "button": "Preview"}, 600)
            seen.append("OBSERVED page: the preview's sixteen stills drawn and the window shown in %.1f s" % (time.time() - t_pv))
            rep = get("/preview.json?world=%s&id=%s&candidate=%s" % (W, rid, letter))
            sdir = os.path.join(live.studio.records, rid, letter + ".stills")
            stills = sorted(os.listdir(sdir)) if os.path.isdir(sdir) else []
            sizes = {png_size(os.path.join(sdir, f)) for f in stills}
            differ = sum(1 for k in range(8) if os.path.exists(os.path.join(sdir, "base-%d.png" % k)) and os.path.exists(os.path.join(sdir, "candidate-%d.png" % k))
                         and open(os.path.join(sdir, "base-%d.png" % k), "rb").read() != open(os.path.join(sdir, "candidate-%d.png" % k), "rb").read())
            flags = {}
            for f in stills:
                try:
                    _m, fl = quality.detect_png(open(os.path.join(sdir, f), "rb").read())
                except quality.QualityError as e:
                    fl = ["NOT READ: %s" % e]
                for x in fl:
                    flags[x.split(":")[0]] = flags.get(x.split(":")[0], 0) + 1
            seen.append("OBSERVED page: the preview's stills' detectors (a detector proves nothing): %s" % (flags or "nothing flagged"))
            fr = rep.get("framing") or {}
            row("page: the preview drawn by the page's renderer: 16 stills of 480 x 270 given to the host, the bay's stills unlike the window's at every pose; replayed, verified, framed; the page's window says state verified",
                r.get("ok") and r.get("modal") and (r.get("badge") or {}).get("text") == "state verified" and len(stills) == 16 and sizes == {(480, 270)} and differ == 8
                and rep.get("replayed") and rep.get("state_verified") and (fr.get("base") or {}).get("met") and (fr.get("candidate") or {}).get("met")
                and (rep.get("path_check") or {}).get("base") == [] and (rep.get("path_check") or {}).get("candidate") == [],
                "the page: %s %r; the host: %d stills %s, %d of 8 poses unlike, replayed %s, verified %s, framed %s/%s" % (
                    "window" if r.get("modal") else "no window", (r.get("badge") or {}).get("text", r.get("error", "")), len(stills), sorted(sizes, key=str), differ,
                    rep.get("replayed"), rep.get("state_verified"), (fr.get("base") or {}).get("met"), (fr.get("candidate") or {}).get("met")))
        # the admission, from the page's canvas, framed as the request's path frames the bay
        pose = (((live.studio.req or {}).get("path") or {}).get("poses") or [None])[0]
        if not (pose and all(k in pose for k in ("x", "y", "z", "yaw_deg", "pitch_deg"))):
            raise RuntimeError("the request's path has no first pose to put the camera at: %r" % (pose,))
        ch.do(dict({"do": "camera"}, **{k: pose[k] for k in ("x", "y", "z", "yaw_deg", "pitch_deg")}), 30)

        def at_pose(cam):
            """the view's camera is the path's first pose (the page holds yaw and pitch in radians)"""
            import math
            try:
                return (cam["x"] == pose["x"] and cam["y"] == pose["y"] and cam["z"] == pose["z"]
                        and abs(cam["yaw"] - pose["yaw_deg"] * math.pi / 180) < 1e-9 and abs(cam["pitch"] - pose["pitch_deg"] * math.pi / 180) < 1e-9)
            except (KeyError, TypeError):
                return False
        before = snapshot()
        r = ch.do({"do": "press", "title": "Panelled bay", "button": "Admit"}, 45 if argv_plant in PLANT_EDITS else 240)
        after = snapshot()
        last = live.studio.state().get("last") or {}
        new = after["admits"][len(before["admits"]):]
        a = new[0] if len(new) == 1 else {}
        still = ((a.get("evidence") or {}).get("still_sha256")) or ""
        spath = os.path.join(ws.stills, still + ".png") if still else ""
        size = png_size(spath) if spath else None
        cert = last.get("certificate") or {}
        if still:
            seen.append("OBSERVED page: the admission's still, taken from the page's canvas: %s, its detectors %s" % (
                size, (a.get("evidence") or {}).get("detectors", {}).get("flags")))
        row("page: Admit pressed: the still taken from the page's canvas (960 x 540), the view at the request's first pose before and after; admitted, the ledger's admit from the request's head, its receipt, its certificate exact; the page says admitted, and its toast",
            r.get("ok") and at_pose(r.get("cam_before")) and at_pose(r.get("cam_after")) and (r.get("status") or {}).get("good") and (r.get("status") or {}).get("text", "").startswith("admitted:") and toasted(r, False, "Admitted " + letter) and len(new) == 1
            and a.get("head_before") == st.get("head") and a.get("head_after") == after["head"] != before["head"] and (a.get("region") or {}).get("receipt")
            and cert.get("ok") is True and cert.get("exact") is True and size == VIEW,
            "the page: %s, toasts %s, the view at the pose %s/%s; the host: %d new admission%s%s, the still %s %s, certificate %s" % (
                (r.get("status") or {}).get("text", r.get("error", "")), [t.get("text", "")[:40] for t in r.get("toasts") or []],
                at_pose(r.get("cam_before")), at_pose(r.get("cam_after")), len(new), "" if len(new) == 1 else "s",
                (" #%s %s -> %s" % (a.get("seq"), (a.get("head_before") or "")[:12], (a.get("head_after") or "")[:12])) if a else "", still[:12], size,
                "exact" if cert.get("exact") else cert))
        full = argv_plant in ("", "page-live-unwaited")     # a run that goes on past the undo
        if full:
            # the admission's scene served first, then the loop held behind what the undo will write
            served_admitted, _w = served_head(120)
            live_gate.clear()
        r = ch.do({"do": "undo"}, 45 if argv_plant in PLANT_EDITS else 240)
        u = snapshot()
        last = live.studio.state().get("last") or {}
        row("page: Undo pressed: the head, the brief and the scene as before the admission, the head restored, its certificate ok; the page says undone, and its toast",
            r.get("ok") and (r.get("status") or {}).get("good") and (r.get("status") or {}).get("text", "").startswith("undone:") and toasted(r, False, "Undone") and world(u) == world(before)
            and last.get("what") == "undone" and last.get("head_restored") is True and (last.get("certificate") or {}).get("ok") is True,
            "the page: %s; the host: the world as before %s, head restored %s" % ((r.get("status") or {}).get("text", r.get("error", "")), world(u) == world(before), last.get("head_restored")))
        if not full:
            return rows, seen

        # ---- the plants through the page: a second request, at the head the undo gave back
        r = ch.do({"do": "ask", "words": "panel ", "shape": "bay", "strict": True}, 240)
        st = live.studio.state()["request"] or {}
        rid2 = st.get("id")
        if not r.get("ok") or st.get("state") != "done" or not rid2 or rid2 == rid or (r.get("request") or {}).get("id") != rid2:
            raise RuntimeError("the second request, for the plants, did not end done: %s %s (the page: %s)" % (rid2, st.get("state"), r.get("error", "")))
        c2, _st = cand("Panelled bay")
        held_sha, head_sha = (live.slot(0) or {}).get("sha"), snapshot()["scene_sha256"]   # read while the loop is held
        live_gate.set()
        if argv_plant == "page-live-unwaited":
            caught_up, waited = True, None    # the plant: the world read the moment the loop is let go, nothing waited for
        else:
            caught_up, waited = served_head(120)
            seen.append(("OBSERVED page: the live loop, let go, served the files' head %.1f s later (polled every 0.2 s)" if caught_up
                         else "OBSERVED page: the live loop, let go, did not serve the files' head in %.0f s") % waited)
        s_world, s_cand = (live.slot(0) or {}).get("sha"), (live.slot(c2["slot"]) or {}).get("sha") if c2 and c2.get("slot") else None
        wants = {} if argv_plant == "page-live-unwaited" else {"want_cand": s_cand, "want_world": s_world}
        r = ch.do(dict({"do": "original", "title": "Panelled bay"}, **wants), 120)
        row("page: Show pressed on a card, then Original: the view drew the candidate's scene, then the world's own, the files' head; the live loop, held behind the undo, served the admitted scene until let go, then the head",
            r.get("ok") and r.get("show") == "pressed" and r.get("original") == "pressed" and s_cand and s_world and s_cand != s_world
            and served_admitted and held_sha == after["scene_sha256"] != head_sha and caught_up and s_world == head_sha
            and (r.get("shown") or {}).get("sha") == s_cand and (r.get("back") or {}).get("k") == 0 and (r.get("back") or {}).get("sha") == s_world
            and (r.get("shown") or {}).get("swapped") and (r.get("back") or {}).get("swapped"),
            "held: the loop served %s, the files %s; let go: %s; the page drew %s then %s; the host serves %s in the candidate's slot and %s in the world's" % (
                (held_sha or "")[:12], (head_sha or "")[:12], "not waited for (the plant)" if waited is None else "the head in %.1f s" % waited if caught_up else "NOT the head in %.0f s" % waited,
                ((r.get("shown") or {}).get("sha") or r.get("error", ""))[:12], ((r.get("back") or {}).get("sha") or "")[:12], (s_cand or "")[:12], (s_world or "")[:12]))
        LAST.update(hold_met=bool(served_admitted and held_sha == after["scene_sha256"] != head_sha), stale_read=bool(s_world and s_world != head_sha))
        if argv_plant:
            return rows, seen
        w0 = snapshot()
        r = ch.do({"do": "press", "title": "Panelled column", "button": "Admit"}, 30)
        chips = [x["text"] for x in (r.get("card") or {}).get("chips", [])]
        w1 = snapshot()
        col, _st = cand("Panelled column")
        col_s = (col or {}).get("strict") or {}
        refused = col is not None and col.get("slot") is not None and col_s.get("ok") is False and col_s.get("code") == "ADMIT-OUTSIDE" and (col_s.get("outside_count") or 0) >= 1
        row("page plant: a region refused — the host's strict check refuses the column (ADMIT-OUTSIDE), its card shows strict FAIL and its Admit cannot be pressed; nothing reached the host",
            r.get("ok") and r.get("pressed") == "disabled" and "strict FAIL" in chips and refused
            and w1["ledger_bytes"] == w0["ledger_bytes"] and world(w1) == world(w0),
            "the card: %s, Admit %s; the host: %s, %s outside; the ledger %s" % (chips, r.get("pressed", r.get("error")), col_s.get("code", col_s.get("ok")),
                                                                              col_s.get("outside_count"), "unchanged" if w1["ledger_bytes"] == w0["ledger_bytes"] else "CHANGED"))
        motion.PLANT = "preview-shared-state"
        motion._SHARED.clear()
        try:
            r = ch.do({"do": "press", "title": "Panelled bay", "button": "Preview"}, 600)
        finally:
            motion.PLANT = saved[1]
            motion._SHARED.clear()
        c2, _st = cand("Panelled bay")
        rep = get("/preview.json?world=%s&id=%s&candidate=%s" % (W, rid2, c2["letter"] if c2 else "A"))
        w2 = snapshot()
        row("page plant: a failing preview (one run's state carried into the next) — the page's window says the states differ; nothing admitted",
            r.get("ok") and r.get("modal") and (r.get("badge") or {}).get("text") == "states differ" and rep.get("state_verified") is False
            and w2["ledger_bytes"] == w0["ledger_bytes"],
            "the page: %r; the host: verified %s, first difference %s" % ((r.get("badge") or {}).get("text", r.get("error", "")), rep.get("state_verified"), rep.get("first_difference")))

        def lost(*_a, **_k):
            return 409, {"ok": False, "code": "STUDIO-NO-STILL", "message": "planted: the still never reached the host"}
        play.studio_still = lost
        try:
            r = ch.do({"do": "press", "title": "Panelled bay", "button": "Admit"}, 120)
        finally:
            play.studio_still = saved[2]
        w3 = snapshot()
        row("page plant: a still the host never received — the page says STUDIO-NO-STILL, in its toast too, and admits nothing",
            r.get("ok") and (r.get("status") or {}).get("bad") and "STUDIO-NO-STILL" in (r.get("status") or {}).get("text", "") and toasted(r, True, "STUDIO-NO-STILL")
            and w3["ledger_bytes"] == w0["ledger_bytes"] and world(w3) == world(w0),
            "the page: %s; the ledger %s" % ((r.get("status") or {}).get("text", r.get("error", "")), "unchanged" if w3["ledger_bytes"] == w0["ledger_bytes"] else "CHANGED"))
        v = live.version
        open(art, "ab").write(b"material plant_stale 10,20,30 0.5 0.0\n")
        wait_version(v)
        w4 = snapshot()
        r = ch.do({"do": "press", "title": "Panelled bay", "button": "Admit"}, 240)
        w5 = snapshot()
        row("page plant: a stale head (the brief edited after the preview) — the page says STUDIO-STALE, in its toast too, and admits nothing; the world as the edit left it",
            r.get("ok") and (r.get("status") or {}).get("bad") and "STUDIO-STALE" in (r.get("status") or {}).get("text", "") and toasted(r, True, "STUDIO-STALE")
            and world(w5) == world(w4) and len(w5["admits"]) == len(w4["admits"]) and w5["ledger_bytes"] == w4["ledger_bytes"],
            "the page: %s; nothing appended %s" % ((r.get("status") or {}).get("text", r.get("error", "")), w5["ledger_bytes"] == w4["ledger_bytes"]))
        v = live.version
        open(art, "wb").write(original)              # the brief as the ledger holds it again
        wait_version(v)
    except Exception as e:  # noqa: BLE001 — the self-test says what stopped it
        import traceback
        if not argv_plant:
            traceback.print_exc()
        row("page: the self-test ran to its end", False, "%s: %s" % (type(e).__name__, str(e)[:200]))
        if isinstance(e, PageLost):
            seen.append("OBSERVED page: the run ended early: %s" % e)
    finally:
        if live_gate is not None:
            live_gate.set()                   # never leave the live loop held
        try:
            if live is not None and getattr(live, "hub", None) is not None and getattr(live.hub, "page_test", None) is not None:
                live.hub.page_test.steps.put({"do": "end"})
                time.sleep(1.0)
        except Exception:  # noqa: BLE001
            pass
        left, first, took = end_browser(proc, marker) if proc is not None else ([], [], 0.0)
        if proc is not None:
            row("page: the browser ended, and nothing of it is left (the query that says so found the browser's processes while it ran)",
                not left and bool(alive) and alive != ["unknown"], "while it ran: %d process%s; left: %s" % (
                    len(alive) if alive != ["unknown"] else 0, "" if len(alive) == 1 else "es", left or "nothing"))
            seen.append("OBSERVED page: the browser ended in %.1f s%s" % (took, ("; standing at the first look: %s" % first) if first else ""))
            log = os.path.join(tmp, "browser.log")
            if os.path.exists(log):
                lines = open(log, "rb").read().decode("utf-8", "replace").splitlines()
                errs = [ln for ln in lines if ":CONSOLE" in ln and ("Uncaught" in ln or "Error" in ln)]
                for ln in errs[:5]:
                    seen.append("OBSERVED page: the browser's console: %s" % ln[-240:])
                if not all(ok for _n, ok, _d in rows):
                    # something failed: the browser's own last words (it may not have started), kept before its tree is removed
                    for ln in [x for x in lines if ":CONSOLE" not in x and x.strip()][-5:]:
                        seen.append("OBSERVED page: the browser's log: %s" % ln[-240:])
        play.ROOT, motion.PLANT, play.studio_still = saved[0], saved[1], saved[2]
        play.FILES.clear()
        play.FILES.update(saved[3])
        if live:
            live.stopping = True
            if live.studio:
                live.studio.shutdown()
        if srv:
            srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    return rows, seen


def selftest(argv=()):
    """PAGE SELFTEST n/n: the honest run's rows (the page's flow and its plants through the page), then each harness
    plant's run, caught when the row it breaks fails (a plant whose text is not in play.js once is not planted, and fails)."""
    if WINDOWS:
        try:
            import studio_app
            studio_app.Job()            # whatever this process starts ends with it, the browser's tree among it
        except (OSError, ImportError, AttributeError):
            pass
    try:
        sys.stdout.reconfigure(errors="backslashreplace")
    except (AttributeError, ValueError):
        pass
    browser, headed = find_browser(argv), "--headed" in argv
    rows, seen = run(browser, headed, say=lambda s_: print(s_, flush=True))
    for ln in seen:
        print(ln)
    caught = []
    js = open(os.path.join(HERE, "web", "play.js"), "rb").read().decode("utf-8")
    opened = any(n.startswith("page: the studio page opened") and ok for n, ok, _d in rows)
    for p in PLANTS:
        if not opened:
            caught.append(False)
            print("[FAIL] page plant %s caught — NOT RUN: the page did not open in the honest run" % p, flush=True)
            continue
        if p in PLANT_EDITS and js.count(PLANT_EDITS[p][0]) != 1:
            caught.append(False)
            print("[FAIL] page plant %s caught — NOT PLANTED: its text occurs %d times in play.js, not once" % (p, js.count(PLANT_EDITS[p][0])))
            continue
        globals()["PLANT"] = p
        try:
            prow, _s = run(browser, headed, p)
        finally:
            globals()["PLANT"] = ""
        failed = [n for n, ok, _d in prow if not ok]
        # caught by the row the plant breaks (a run that failed elsewhere, its browser left standing or the run stopped,
        # does not catch it); the live plant only when its admission and undo passed, the hold was met and the world was
        # read stale, so that it is caught by the wait taken away and by nothing else
        by_row = any(n.startswith(PLANT_ROWS[p]) for n in failed)
        if p == "page-live-unwaited":
            passed = {n.split(":")[1].strip().split(" ")[0] for n, ok, _d in prow if ok and n.startswith("page: ")}
            by_row = by_row and {"Admit", "Undo"} <= passed and LAST.get("hold_met") is True and LAST.get("stale_read") is True
        caught.append(browser is not None and by_row)
        print("[%s] page plant %s caught — %s" % ("PASS" if caught[-1] else "FAIL", p, ("by: " + "; ".join(f[:70] for f in failed)) if failed else "NOT CAUGHT"), flush=True)
        for n, ok, d in prow:
            if not ok and n.startswith(PLANT_ROWS[p]):
                print("  its row's detail — %s" % d, flush=True)
                break
    ok = all(o for _n, o, _d in rows) and all(caught)
    print("PAGE SELFTEST %d/%d" % (sum(o for _n, o, _d in rows) + sum(caught), len(rows) + len(caught)))
    return 0 if ok else 1


def main(argv):
    if argv[:1] == ["selftest"]:
        return selftest(argv[1:])
    print("usage: python art/page_test.py selftest [--browser EXE] [--headed]   (or python art/play.py --page-selftest)")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
