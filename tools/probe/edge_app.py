# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# tools/probe/edge_app.py — experiment 1 of docs/STUDIO-CONTRACT.md §11: the plaza in Edge's application mode with a
# private profile. Measures: the browser found (App Paths, then the two usual folders; Chrome if Edge is absent); the
# page served and its heartbeat heard (/healthz); pointer lock and the keys (asked of the person at the keyboard: only
# a person can say the mouse looks around); and what closing the window does to the browser process it started.
#
#   python tools\probe\edge_app.py
#   python tools\probe\edge_app.py --job     only: Edge started inside a job object, and every one of its processes gone
#                                            when the job closes (what art/studio_app.py relies on; nothing to answer)
#
# Kill criterion: pointer lock does not engage in --app → WebView2 moves into B1. A browser that lingers after its last
# window is not a kill: the supervisor's heartbeat and job end it (it is recorded).

import os
import shutil
import subprocess
import sys
import tempfile
import time

from common import Probe, REPO, free_port, wait_health, health, page_token, post, windows_only


def find_browser():
    import winreg
    for exe in ("msedge.exe", "chrome.exe"):
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\%s" % exe) as k:
                    v = winreg.QueryValue(k, None)
                    if v and os.path.exists(v.strip('"')):
                        return exe, v.strip('"'), "App Paths"
            except OSError:
                pass
        sub = r"Microsoft\Edge\Application\msedge.exe" if exe == "msedge.exe" else r"Google\Chrome\Application\chrome.exe"
        for env in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
            base = os.environ.get(env)
            if base and os.path.exists(os.path.join(base, sub)):
                return exe, os.path.join(base, sub), "%" + env + "%"
    return None, None, None


HOLDER = r'''
import ctypes, subprocess, sys, time, json, urllib.request
from ctypes import wintypes
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
class BASIC(ctypes.Structure):
    _fields_ = [("a", ctypes.c_int64), ("b", ctypes.c_int64), ("LimitFlags", wintypes.DWORD), ("c", ctypes.c_size_t), ("d", ctypes.c_size_t),
                ("e", wintypes.DWORD), ("f", ctypes.c_size_t), ("g", wintypes.DWORD), ("h", wintypes.DWORD)]
class EXT(ctypes.Structure):
    _fields_ = [("Basic", BASIC), ("io", ctypes.c_ulonglong * 6), ("i", ctypes.c_size_t), ("j", ctypes.c_size_t), ("k", ctypes.c_size_t), ("l", ctypes.c_size_t)]
k32.CreateJobObjectW.restype = wintypes.HANDLE
k32.GetCurrentProcess.restype = wintypes.HANDLE
k32.SetInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
k32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
job = k32.CreateJobObjectW(None, None)
x = EXT(); x.Basic.LimitFlags = 0x2000
k32.SetInformationJobObject(job, 9, ctypes.byref(x), ctypes.sizeof(x))
ok = k32.AssignProcessToJobObject(job, k32.GetCurrentProcess())
edge, url, profile, port = sys.argv[1:5]
subprocess.Popen([edge, "--app=" + url, "--user-data-dir=" + profile, "--no-first-run", "--no-default-browser-check"])
t = time.time()
spoke = False
while time.time() - t < 60 and not spoke:
    try:
        spoke = json.loads(urllib.request.urlopen("http://127.0.0.1:%s/healthz" % port, timeout=3).read()).get("page")
    except Exception:
        pass
    time.sleep(0.5)
time.sleep(3)
print(json.dumps({"assigned": bool(ok), "spoke": bool(spoke)}), flush=True)
'''


def edge_processes(marker):
    # no double quote anywhere, so the command line needs no escaping: the filter's quotes doubled inside single ones
    ps = ("@(Get-CimInstance Win32_Process -Filter 'Name=''msedge.exe'' OR Name=''chrome.exe''' "
          "| Where-Object { $_.CommandLine -like '*%s*' }).Count" % marker)
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], capture_output=True, text=True)
    try:
        return int(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return -1


def job_case(p, path, port):
    import json
    import uuid
    profile = os.path.join(tempfile.gettempdir(), "vs-edge-job-" + uuid.uuid4().hex[:8])
    r = subprocess.run([sys.executable, "-c", HOLDER, path, "http://127.0.0.1:%d/" % port, profile, str(port)], capture_output=True, text=True, timeout=120)
    try:
        out = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        p.case("edge-in-a-job", "BROKEN", holder=r.stderr.strip()[-120:])
        return False
    t = time.time()
    n = edge_processes(os.path.basename(profile))
    while n > 0 and time.time() - t < 10:
        time.sleep(0.5)
        n = edge_processes(os.path.basename(profile))
    ok = out["assigned"] and out["spoke"] and n == 0
    p.case("edge-dies-with-its-job", "HELD" if ok else "BROKEN", page_spoke=out["spoke"], processes_left=n, seconds=round(time.time() - t, 1))
    shutil.rmtree(profile, ignore_errors=True)
    return ok


def ask(q):
    while True:
        a = input(q + " [y/n] ").strip().lower()
        if a in ("y", "n"):
            return a == "y"


def main():
    p = Probe(1, "edge_app")
    windows_only(p)
    exe, path, how = find_browser()
    if not p.case("browser-found", "HELD" if path else "BROKEN", browser=exe or "none", found_by=how or "-"):
        return p.verdict(killed="no Edge or Chrome: WebView2 moves into B1")
    port = free_port()
    profile = tempfile.mkdtemp(prefix="vs-edge-")
    server = subprocess.Popen([sys.executable, "-B", os.path.join(REPO, "art", "play.py"), "plaza-night", "--no-browser", "--port", str(port)],
                              cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    browser = None
    try:
        if not p.case("server-ready", "HELD" if wait_health(port) else "BROKEN", port=port):
            return p.verdict(incomplete="play.py did not answer /healthz")
        if "--job" in sys.argv:
            job_case(p, path, port)
            return p.verdict()
        t0 = time.time()
        browser = subprocess.Popen([path, "--app=http://127.0.0.1:%d/" % port, "--user-data-dir=%s" % profile, "--no-first-run",
                                    "--no-default-browser-check", "--window-size=1280,800"])
        h = wait_health(port, 60, lambda h: h.get("page"))
        p.case("page-heartbeat", "HELD" if h else "BROKEN", seconds=round(time.time() - t0, 1))
        print("\nIn the window that opened: click into the plaza, move the mouse, walk with W A S D, press E on a canopy,")
        print("then press Esc to free the mouse. Then answer here.\n")
        locked = ask("Did the mouse look around when you moved it (pointer lock engaged)?")
        p.case("pointer-lock", "HELD" if locked else "BROKEN")
        keys = ask("Did W A S D walk, and did E show a target frame on the canopy?")
        p.case("keys", "HELD" if keys else "BROKEN")
        print("\nNow close the window (its X). The probe watches the browser process it started.\n")
        t, last_alive, ended_at = time.time(), time.time(), None
        while time.time() - t < 180:
            hh = health(port)
            if hh and hh.get("page_age_s") is not None:
                last_alive = max(last_alive, time.time() - hh["page_age_s"])
            if ended_at is None and browser.poll() is not None:
                ended_at = time.time()
            if ended_at is not None or time.time() - last_alive > 20:
                break
            time.sleep(0.25)
        gap = None if ended_at is None else round(ended_at - last_alive, 1)
        # the page speaks every 5 s, so the window closed at most 5 s after its last word
        p.case("browser-ends-with-window", "HELD" if gap is not None and gap <= 10 else "BROKEN",
               ended_after_last_heartbeat_s=gap if gap is not None else "still-running-20s-after-the-last-heartbeat")
        if not locked:
            return p.verdict(killed="pointer lock does not engage in --app: WebView2 moves into B1")
        return p.verdict()
    finally:
        if browser and browser.poll() is None:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(browser.pid)], capture_output=True)
        tok = None
        try:
            tok = page_token(port)
        except Exception:  # noqa: BLE001
            pass
        if tok:
            post(port, "/studio/shutdown", tok)
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
