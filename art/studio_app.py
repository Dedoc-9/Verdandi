# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/studio_app.py — the studio's supervisor (STUDIO-APP-0, B1): one desktop icon starts the plaza with its director in
# a window of its own, and closing the window stops everything it started. Standard library only.
#
#   pythonw art\studio_app.py [--brief B] [--director CONFIG.json] [--root DIR] [--state DIR] [--browser EXE]
#   python  art\studio_app.py shortcut [--director CONFIG.json]      a desktop shortcut that starts it (Windows)
#   python  art\studio_app.py selftest                               its lifecycle, with a stand-in browser
#
# What it does: takes the instance lock (a second start opens another window on the running studio and ends); on
# Windows puts itself in a job object with KILL_ON_JOB_CLOSE, so that play.py, the provider it runs and the browser all
# inherit it and end with it (experiment 2, on the owner's machine 2026-10-12: nested in his shell's job, every process
# gone 0.2 s after the job closed); starts art/play.py on a free port, without a console, and waits for /healthz;
# opens Edge (or Chrome) in application mode with a profile of its own (experiment 1: pointer lock and the keys held in
# --app); then watches. It stops the studio when the page says goodbye (its pagehide beacon) and does not speak again
# within a few seconds (a reload speaks again at once), when the page has not spoken for three minutes (a minimized
# window's timers are slowed to about one a minute, so a shorter limit would close it), or when play.py ends. Stopping
# is POST /studio/shutdown, then the job: Edge's own process outlives its last window by more than 20 s (experiment 1,
# twice), and the job ends it. What it does not do: choose or replace a generation (B2's stub and journal,
# docs/STUDIO-CONTRACT.md); install anything; read a key (ANTHROPIC_API_KEY is the user's environment's, never a file's).
#
# Its state is under %LOCALAPPDATA%\VerdandiStudio\state (elsewhere ~/.local/state/verdandi-studio): logs\, the
# browser's profile, the instance lock, and settings.json, which `shortcut` writes with the non-secret variables of
# the shell it ran in (VERDANDI_CLAUDE, VERDANDI_DIRECTOR_MODEL, VERDANDI_DIRECTOR_API), since an icon has no shell.

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
WINDOWS = os.name == "nt"
SETTINGS_KEYS = ("VERDANDI_CLAUDE", "VERDANDI_DIRECTOR_MODEL", "VERDANDI_DIRECTOR_API")
EXIT_OK, EXIT_NO_PLAY, EXIT_NO_WINDOW, EXIT_PLAY_ENDED, EXIT_USAGE = 0, 2, 3, 4, 5
NO_WINDOW = 0x08000000                       # CREATE_NO_WINDOW: play.py and its children without a console


def state_dir(opt=None):
    if opt:
        return os.path.abspath(opt)
    if WINDOWS:
        return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "VerdandiStudio", "state")
    return os.path.join(os.path.expanduser("~"), ".local", "state", "verdandi-studio")


class Log:
    def __init__(self, state, console):
        os.makedirs(os.path.join(state, "logs"), exist_ok=True)
        self.path = os.path.join(state, "logs", "supervisor.log")
        if os.path.exists(self.path) and os.path.getsize(self.path) > 1 << 20:
            os.replace(self.path, self.path + ".1")
        self.console = console

    def __call__(self, msg):
        line = "%s  %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        if self.console and sys.stdout is not None:
            print(line, flush=True)


def tell(msg, gui):
    """A message the person must see: a dialog when there is no console (pythonw), else standard error."""
    if gui and WINDOWS:
        import ctypes
        ctypes.WinDLL("user32").MessageBoxW(None, msg, "Verdandi Studio", 0x10)
    elif sys.stderr is not None:
        print(msg, file=sys.stderr, flush=True)


# ------------------------------------------------------------------------------------------------ the instance lock
class Instance:
    """The one studio of this state folder: an exclusive lock held while it runs, and where its server is."""

    def __init__(self, state):
        self.lock_path = os.path.join(state, "instance.lock")
        self.info_path = os.path.join(state, "instance.json")
        self.fh = None

    def take(self):
        fh = open(self.lock_path, "a+b")
        try:
            if WINDOWS:
                import msvcrt
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            fh.close()
            return False
        self.fh = fh
        return True

    def publish(self, url):
        with open(self.info_path, "w", encoding="utf-8") as f:
            json.dump({"url": url, "pid": os.getpid()}, f)

    def running_url(self):
        try:
            return json.load(open(self.info_path, encoding="utf-8")).get("url")
        except (OSError, ValueError):
            return None


# ------------------------------------------------------------------------------------------------ the job (Windows)
class Job:
    """This process and everything it starts, ended together: a job object with KILL_ON_JOB_CLOSE that this process
    joins, so its children inherit it; the last handle closes when this process ends."""

    def __init__(self):
        import ctypes
        from ctypes import wintypes
        self.ctypes, self.wintypes = ctypes, wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.k32 = k32

        class BASIC(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64), ("LimitFlags", wintypes.DWORD),
                        ("MinimumWorkingSetSize", ctypes.c_size_t), ("MaximumWorkingSetSize", ctypes.c_size_t),
                        ("ActiveProcessLimit", wintypes.DWORD), ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]

        class IO(ctypes.Structure):
            _fields_ = [(n, ctypes.c_ulonglong) for n in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                                                            "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class EXTENDED(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", BASIC), ("IoInfo", IO), ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]
        k32.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
        k32.CreateJobObjectW.restype = wintypes.HANDLE
        k32.SetInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
        k32.SetInformationJobObject.restype = wintypes.BOOL
        k32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
        k32.AssignProcessToJobObject.restype = wintypes.BOOL
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        k32.QueryInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p)
        k32.QueryInformationJobObject.restype = wintypes.BOOL
        self.handle = k32.CreateJobObjectW(None, None)
        if not self.handle:
            raise OSError(ctypes.get_last_error(), "CreateJobObjectW")
        info = EXTENDED()
        info.BasicLimitInformation.LimitFlags = 0x2000 | 0x400      # KILL_ON_JOB_CLOSE | DIE_ON_UNHANDLED_EXCEPTION
        if not k32.SetInformationJobObject(self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            raise OSError(ctypes.get_last_error(), "SetInformationJobObject")
        if not k32.AssignProcessToJobObject(self.handle, k32.GetCurrentProcess()):
            raise OSError(ctypes.get_last_error(), "AssignProcessToJobObject")

    def pids(self):
        """The processes in the job now (JobObjectBasicProcessIdList)."""
        ctypes = self.ctypes
        n = 256
        buf = (ctypes.c_size_t * (2 + n))()
        if not self.k32.QueryInformationJobObject(self.handle, 3, ctypes.byref(buf), ctypes.sizeof(buf), None):
            return []
        return [int(buf[2 + i]) for i in range(min(int(buf[1]), n))]


# ------------------------------------------------------------------------------------------------ the browser
def find_browser():
    if not WINDOWS:
        for exe in ("microsoft-edge", "google-chrome", "chromium", "chromium-browser"):
            p = shutil.which(exe)
            if p:
                return p
        return None
    import winreg
    for exe in ("msedge.exe", "chrome.exe"):
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\%s" % exe) as k:
                    v = (winreg.QueryValue(k, None) or "").strip('"')
                    if v and os.path.exists(v):
                        return v
            except OSError:
                pass
        sub = r"Microsoft\Edge\Application\msedge.exe" if exe == "msedge.exe" else r"Google\Chrome\Application\chrome.exe"
        for env in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
            base = os.environ.get(env)
            if base and os.path.exists(os.path.join(base, sub)):
                return os.path.join(base, sub)
    return None


def browser_argv(browser, url, state):
    prefix = [sys.executable, browser] if browser.endswith(".py") else [browser]
    return prefix + ["--app=%s" % url, "--user-data-dir=%s" % os.path.join(state, "browser"), "--no-first-run",
                     "--no-default-browser-check", "--window-size=1400,900"]


# ------------------------------------------------------------------------------------------------ play.py
def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def get_json(url, timeout=3):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except (urllib.error.URLError, OSError, ValueError):
        return None


def child_python():
    """The interpreter for play.py: pythonw beside python on Windows (no console), else this one."""
    if WINDOWS:
        w = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if os.path.exists(w):
            return w
    return sys.executable


def spawn(argv, log_path, env=None):
    kw = {"stdout": open(log_path, "ab"), "stderr": subprocess.STDOUT, "stdin": subprocess.DEVNULL, "cwd": REPO, "env": env}
    if WINDOWS:
        kw["creationflags"] = NO_WINDOW
    else:
        kw["start_new_session"] = True          # a group of its own, ended with it (the job's part, on POSIX)
    return subprocess.Popen(argv, **kw)


def end(p):
    if p is None or p.poll() is not None:
        return
    if WINDOWS:
        p.kill()
    else:
        import signal
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            pass
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass


# ------------------------------------------------------------------------------------------------ the supervisor
def run(opts, log, gui):
    state = opts["state"]
    inst = Instance(state)
    browser = opts.get("browser") or find_browser()
    if not inst.take():
        url = inst.running_url()
        log("another studio runs from this state folder (%s): a window on it" % url)
        if url and browser:
            subprocess.Popen(browser_argv(browser, url, state), cwd=REPO)
            return EXIT_OK
        tell("Verdandi Studio is already running, and its window could not be opened.", gui)
        return EXIT_NO_WINDOW
    if not browser:
        tell("Verdandi Studio needs Microsoft Edge or Google Chrome, and neither was found.", gui)
        return EXIT_NO_WINDOW
    job = None
    if WINDOWS and not opts.get("no_job"):
        job = Job()
        log("in a job of its own (KILL_ON_JOB_CLOSE): everything this studio starts ends with it")
    env = dict(os.environ)
    try:
        saved = json.load(open(os.path.join(state, "settings.json"), encoding="utf-8")).get("env", {})
        for k in SETTINGS_KEYS:
            if saved.get(k) and not env.get(k):
                env[k] = saved[k]
    except (OSError, ValueError):
        pass
    play_log = os.path.join(state, "logs", "play.log")
    play, port, h = None, None, None
    for attempt in range(3):
        port = free_port()
        argv = [child_python(), "-B", os.path.join(HERE, "play.py"), opts["brief"], "--no-browser", "--port", str(port)]
        if opts.get("director"):
            argv += ["--director", opts["director"]]
        if opts.get("root"):
            argv += ["--root", opts["root"]]
        log("play.py on port %d (%s)" % (port, " ".join(argv[3:])))
        play = spawn(argv, play_log, env)
        t = time.time()
        while time.time() - t < opts["start_wait"] and play.poll() is None:
            h = get_json("http://127.0.0.1:%d/healthz" % port)
            if h and h.get("ready"):
                break
            time.sleep(0.3)
        if h and h.get("ready"):
            break
        rc = play.poll()
        end(play)
        if rc != 70:                             # 70: the port was taken in the meantime; another is tried
            tail = open(play_log, "rb").read()[-600:].decode("utf-8", "replace")
            log("play.py did not start (exit %s): %s" % (rc, " ".join(tail.split())[-300:]))
            tell("Verdandi Studio could not start the plaza (play.py exit %s).\n\n%s\n\nThe log: %s" % (rc, tail.strip()[-500:], play_log), gui)
            return EXIT_NO_PLAY
    url = "http://127.0.0.1:%d/" % port
    inst.publish(url)
    log("ready: %s, version %s" % (url, h.get("version")))
    win = subprocess.Popen(browser_argv(browser, url, state), cwd=REPO, stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **({} if WINDOWS else {"start_new_session": True}))
    log("the window: %s (pid %d)" % (os.path.basename(browser), win.pid))
    opened, spoke, why, code = time.time(), False, "", EXIT_OK
    while True:
        time.sleep(opts["tick"])
        if play.poll() is not None:
            why, code = "play.py ended (exit %s)" % play.returncode, EXIT_PLAY_ENDED
            break
        h = get_json("http://127.0.0.1:%d/healthz" % port) or {}
        page, bye = h.get("page_age_s"), h.get("bye_age_s")
        spoke = spoke or page is not None
        if bye is not None and (page is None or page > bye) and bye >= opts["bye_grace"]:
            why = "the window was closed (the page said goodbye %.1f s ago and has not spoken since)" % bye
            break
        if spoke and page is not None and page > opts["page_timeout"]:
            why = "the page has not spoken for %.0f s" % page
            break
        if not spoke and time.time() - opened > opts["page_wait"]:
            why, code = "the window did not open: the page never spoke in %d s" % opts["page_wait"], EXIT_NO_WINDOW
            break
    log("stopping: " + why)
    token = None
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/play.html" % port, timeout=5) as r:
            token = re.search(r'data-studio="([0-9a-f]+)"', r.read().decode("utf-8")).group(1)
    except (urllib.error.URLError, OSError, AttributeError):
        pass
    if token and play.poll() is None:
        q = urllib.request.Request("http://127.0.0.1:%d/studio/shutdown" % port, data=b"{}", method="POST",
                                   headers={"Content-Type": "application/json", "X-Studio-Token": token})
        try:
            urllib.request.urlopen(q, timeout=5).read()
        except (urllib.error.URLError, OSError):
            pass
    try:
        play.wait(timeout=10)
        log("play.py stopped (exit %s)" % play.returncode)
    except subprocess.TimeoutExpired:
        end(play)
        log("play.py did not stop when asked: ended")
    if job is not None:
        left = [p for p in job.pids() if p != os.getpid()]
        log("processes left in the job at exit: %d (the browser's among them if it outlived its window); they end with this process" % len(left))
    else:
        end(win)
        log("the window's process group ended")
    if code == EXIT_NO_WINDOW:
        tell("Verdandi Studio stopped: %s.\nThe log: %s" % (why, log.path), gui)
    return code


# ------------------------------------------------------------------------------------------------ the shortcut
def shortcut(opts, log):
    if not WINDOWS:
        print("the shortcut is a Windows .lnk; elsewhere start `python art/studio_app.py` from a launcher of your own")
        return EXIT_USAGE
    state = opts["state"]
    os.makedirs(state, exist_ok=True)
    keep = {k: os.environ[k] for k in SETTINGS_KEYS if os.environ.get(k)}
    with open(os.path.join(state, "settings.json"), "w", encoding="utf-8") as f:
        json.dump({"env": keep}, f, indent=1)
    args = '"%s"' % os.path.join(HERE, "studio_app.py")
    if opts.get("director"):
        args += ' --director "%s"' % os.path.abspath(opts["director"])
    env = dict(os.environ, VS_TARGET=child_python(), VS_ARGS=args, VS_DIR=REPO, VS_NAME="Verdandi Studio.lnk")
    ps = ("$d = [Environment]::GetFolderPath('Desktop'); $p = Join-Path $d $env:VS_NAME; "
          "$s = (New-Object -ComObject WScript.Shell).CreateShortcut($p); $s.TargetPath = $env:VS_TARGET; "
          "$s.Arguments = $env:VS_ARGS; $s.WorkingDirectory = $env:VS_DIR; $s.Description = 'Verdandi Studio'; $s.Save(); Write-Output $p")
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], capture_output=True, text=True, env=env)
    if r.returncode != 0:
        print("the shortcut was not made: %s" % r.stderr.strip()[-300:])
        return EXIT_USAGE
    log("shortcut made: %s; settings kept: %s" % (r.stdout.strip(), ", ".join(sorted(keep)) or "none"))
    print("made %s\n  starts: %s %s\n  kept for it: %s (never a key: set ANTHROPIC_API_KEY as a user variable for the API provider)" % (
        r.stdout.strip(), child_python(), args, ", ".join(sorted(keep)) or "no variables"))
    return EXIT_OK


# ------------------------------------------------------------------------------------------------ the self-test
FAKE = r'''
# a stand-in for the browser: it reads the page as the page's own script would, then behaves as FAKE_MODE says
import json, os, re, sys, time, urllib.request
url = [a for a in sys.argv if a.startswith("--app=")][0][6:]
mode = os.environ.get("FAKE_MODE", "bye")
rec = os.environ.get("FAKE_RECORD")
if rec:
    open(rec, "a").write(json.dumps(sys.argv[1:]) + "\n")
if mode == "record":
    sys.exit(0)
tok = re.search(r'data-studio="([0-9a-f]+)"', urllib.request.urlopen(url + "play.html").read().decode()).group(1)
def alive():
    urllib.request.urlopen(urllib.request.Request(url + "studio/alive", data=b"{}", method="POST",
                           headers={"Content-Type": "application/json", "X-Studio-Token": tok})).read()
if mode == "mute":
    time.sleep(600)
alive()
if mode == "silent":
    time.sleep(600)                                  # spoke once, then nothing, and lingers
if mode == "reload":
    time.sleep(0.5)
    urllib.request.urlopen(urllib.request.Request(url + "studio/bye", data=tok.encode(), method="POST", headers={"Content-Type": "text/plain"})).read()
    time.sleep(0.3)
    for _ in range(600):                             # a reload: the page speaks again at once, and goes on
        alive(); time.sleep(0.5)
time.sleep(1.0)
urllib.request.urlopen(urllib.request.Request(url + "studio/bye", data=tok.encode(), method="POST", headers={"Content-Type": "text/plain"})).read()
time.sleep(600)                                      # as Edge does: the process outlives its window
'''


def selftest():
    tmp = tempfile.mkdtemp(prefix="studio-app-selftest-")
    rows = []

    def row(name, ok, detail):
        rows.append(ok)
        print("[%s] %s — %s" % ("PASS" if ok else "FAIL", name, detail), flush=True)

    def alive(pid):
        if WINDOWS:
            r = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/NH"], capture_output=True, text=True)
            return str(pid) in r.stdout
        try:
            os.kill(pid, 0)
            with open("/proc/%d/stat" % pid) as f:
                return f.read().split(") ")[-1][0] != "Z"
        except (OSError, IndexError):
            return False

    def supervisor(name, mode, extra=(), wait=True):
        state = os.path.join(tmp, name)
        fake = os.path.join(tmp, "fake_browser.py")
        open(fake, "w").write(FAKE)
        env = dict(os.environ, FAKE_MODE=mode, FAKE_RECORD=os.path.join(tmp, name + ".record"), PYTHONHASHSEED="0")
        argv = [sys.executable, "-B", os.path.abspath(__file__), "--state", state, "--browser", fake, "--console",
                "--bye-grace", "1", "--page-timeout", "4", "--page-wait", "25", "--tick", "0.25", "--root", root] + list(extra)
        p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
        if not wait:
            return p, state
        out, _ = p.communicate(timeout=240)
        return p.returncode, out

    def pids_in(out):
        win = re.search(r"\(pid (\d+)\)", out)
        return int(win.group(1)) if win else None

    root = os.path.join(tmp, "root")
    for sub in ("art/briefs", "art/ledger", "graybox/maps"):
        shutil.copytree(os.path.join(REPO, sub), os.path.join(root, sub))
    for f in os.listdir(os.path.join(root, "art", "ledger")):
        if f.endswith(".tags.json"):
            os.remove(os.path.join(root, "art", "ledger", f))
    try:
        t = time.time()
        rc, out = supervisor("bye", "bye")
        win = pids_in(out)
        time.sleep(0.5)
        row("the window closed: the page's goodbye heard, play.py stopped, the lingering browser ended with the studio",
            rc == EXIT_OK and "the window was closed" in out and "play.py stopped (exit 0)" in out and win and not alive(win),
            "exit %s in %.1f s; the stand-in browser (pid %s) %s" % (rc, time.time() - t, win, "ended" if win and not alive(win) else "STILL RUNNING"))
        rc, out = supervisor("silent", "silent")
        win = pids_in(out)
        time.sleep(0.5)
        row("the page silent past its limit: the studio stops, the browser ended", rc == EXIT_OK and "has not spoken for" in out and win and not alive(win),
            "exit %s; %s" % (rc, [ln for ln in out.splitlines() if "stopping" in ln][-1:]))
        rc, out = supervisor("mute", "mute", ["--page-wait", "6"])
        win = pids_in(out)
        time.sleep(0.5)
        row("the page never speaks: said, the studio stops (exit 3)", rc == EXIT_NO_WINDOW and "the window did not open" in out and win and not alive(win),
            "exit %s" % rc)
        p, state = supervisor("reload", "reload", wait=False)
        time.sleep(12)
        still = p.poll() is None
        row("a reload's goodbye followed at once by the page speaking again: the studio goes on", still, "running after 12 s" if still else "it stopped")
        url = json.load(open(os.path.join(state, "instance.json")))["url"]
        try:
            q = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--state", state, "--browser", os.path.join(tmp, "fake_browser.py"),
                                "--console", "--page-wait", "5", "--root", root], capture_output=True, text=True,
                               env=dict(os.environ, FAKE_MODE="record", FAKE_RECORD=os.path.join(tmp, "second.record")), timeout=120)
            rc2, out2 = q.returncode, q.stdout
        except subprocess.TimeoutExpired:
            rc2, out2 = None, ""
        rec = open(os.path.join(tmp, "second.record")).read() if os.path.exists(os.path.join(tmp, "second.record")) else ""
        row("a second start: a window on the running studio, and nothing else started", rc2 == EXIT_OK and ("--app=" + url) in rec and "another studio runs" in out2,
            "exit %s; the second asked for %s" % (rc2, url))
        if not still:
            raise RuntimeError("the studio stopped on a reload; the cases after it need it running")
        tok = re.search(r'data-studio="([0-9a-f]+)"', urllib.request.urlopen(url + "play.html").read().decode()).group(1)
        urllib.request.urlopen(urllib.request.Request(url + "studio/shutdown", data=b"{}", method="POST",
                                                      headers={"Content-Type": "application/json", "X-Studio-Token": tok})).read()
        out, _ = p.communicate(timeout=60)
        row("play.py stopped from elsewhere: the studio ends too (exit 4), the browser with it", p.returncode == EXIT_PLAY_ENDED and "play.py ended" in out,
            "exit %s" % p.returncode)
        rc, out = supervisor("nobrief", "record", ["--brief", "no-such-brief"])
        row("play.py cannot start: said (exit 2), no window opened", rc == EXIT_NO_PLAY and "did not start" in out and not os.path.exists(os.path.join(tmp, "nobrief.record")),
            "exit %s" % rc)
    except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as e:
        row("the self-test ran to its end", False, "%s: %s" % (type(e).__name__, str(e)[:120]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("STUDIO APP SELFTEST %d/%d" % (sum(rows), len(rows)))
    return 0 if all(rows) else 1


# ------------------------------------------------------------------------------------------------ the command line
def main(argv):
    def opt(k, d=None, cast=str):             # the last occurrence wins
        if k not in argv:
            return d
        i = len(argv) - 1 - argv[::-1].index(k)
        return cast(argv[i + 1]) if i + 1 < len(argv) else d
    if argv[:1] == ["selftest"]:
        return selftest()
    opts = {"brief": opt("--brief", "plaza-night"), "director": opt("--director"), "root": opt("--root"), "browser": opt("--browser"),
            "state": state_dir(opt("--state")), "no_job": "--no-job" in argv, "bye_grace": opt("--bye-grace", 3.0, float),
            "page_timeout": opt("--page-timeout", 180.0, float), "page_wait": opt("--page-wait", 90, int), "start_wait": opt("--start-wait", 120, int),
            "tick": opt("--tick", 0.5, float)}
    gui = sys.stdout is None or os.path.basename(sys.executable).lower() == "pythonw.exe"
    os.makedirs(opts["state"], exist_ok=True)
    log = Log(opts["state"], console="--console" in argv or not gui)
    if argv[:1] == ["shortcut"]:
        return shortcut(opts, log)
    try:
        return run(opts, log, gui)
    except Exception as e:  # noqa: BLE001 — the person sees why, and the log keeps it
        log("failed: %s: %s" % (type(e).__name__, e))
        tell("Verdandi Studio failed: %s: %s\nThe log: %s" % (type(e).__name__, e, log.path), gui)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
