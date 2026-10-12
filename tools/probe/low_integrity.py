# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# tools/probe/low_integrity.py — experiment 4 of docs/STUDIO-CONTRACT.md §11: Windows' Mandatory Integrity Control as the
# capability boundary of a candidate. A copy of the code is made in a folder labelled Low (icacls /setintegritylevel);
# a process is started at low integrity (DuplicateTokenEx, SetTokenInformation(TokenIntegrityLevel, S-1-16-4096),
# CreateProcessAsUserW, as Microsoft's "Designing applications to run at a low integrity level" describes); from there
# it writes in its own folder, tries to write a medium file standing for studio\active.json, and runs the art checks
# and the studio's self-test in the copy. A suite that fails at low integrity is run again at medium, to say which.
#
#   python tools\probe\low_integrity.py
#
# Kill criterion: a suite passes at medium and fails at low integrity → the capability boundary is downgraded to
# tamper-evidence, written as such, and the Try window runs at medium against a scratch copy. A write to the medium file
# that succeeds from low integrity is a broken boundary, and says so.

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

from common import Probe, REPO, windows_only

CHILD = r'''
import json, os, subprocess, sys
low, medium_file, out = sys.argv[1], sys.argv[2], {}
try:
    open(os.path.join(low, "written-at-low.txt"), "w").write("ok")
    out["write_own_folder"] = True
except OSError as e:
    out["write_own_folder"] = "%s" % e
try:
    open(medium_file, "a").write("a candidate's write")
    out["write_medium_refused"] = False
except OSError as e:
    out["write_medium_refused"] = True
    out["write_medium_error"] = type(e).__name__
env = dict(os.environ, TEMP=os.path.join(low, "tmp"), TMP=os.path.join(low, "tmp"), PYTHONHASHSEED="0")
os.makedirs(env["TEMP"], exist_ok=True)
for name, args in (("art-checks", ["art/check.py"]), ("studio-selftest", ["art/studio.py", "selftest"])):
    try:
        r = subprocess.run([sys.executable, "-B"] + args, cwd=os.path.join(low, "repo"), env=env, capture_output=True, text=True, timeout=900)
        last = (r.stdout.strip().splitlines() or [""])[-1]
        out[name] = {"rc": r.returncode, "last": last[:120], "err": r.stderr.strip()[-200:]}
    except Exception as e:
        out[name] = {"rc": -1, "last": "", "err": "%s: %s" % (type(e).__name__, e)}
open(os.path.join(low, "results.json"), "w").write(json.dumps(out))
'''


def start_low(cmdline, cwd):
    """Start cmdline at low integrity; returns its exit code, or raises OSError with the Windows error."""
    import ctypes
    from ctypes import wintypes
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class SID_AND_ATTRIBUTES(ctypes.Structure):
        _fields_ = [("Sid", ctypes.c_void_p), ("Attributes", wintypes.DWORD)]

    class TOKEN_MANDATORY_LABEL(ctypes.Structure):
        _fields_ = [("Label", SID_AND_ATTRIBUTES)]

    class STARTUPINFOW(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR), ("lpDesktop", wintypes.LPWSTR), ("lpTitle", wintypes.LPWSTR),
                    ("dwX", wintypes.DWORD), ("dwY", wintypes.DWORD), ("dwXSize", wintypes.DWORD), ("dwYSize", wintypes.DWORD),
                    ("dwXCountChars", wintypes.DWORD), ("dwYCountChars", wintypes.DWORD), ("dwFillAttribute", wintypes.DWORD),
                    ("dwFlags", wintypes.DWORD), ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD), ("lpReserved2", ctypes.c_void_p),
                    ("hStdInput", wintypes.HANDLE), ("hStdOutput", wintypes.HANDLE), ("hStdError", wintypes.HANDLE)]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE), ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD)]

    k32.GetCurrentProcess.restype = wintypes.HANDLE
    adv.OpenProcessToken.argtypes = (wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE))
    adv.OpenProcessToken.restype = wintypes.BOOL
    adv.DuplicateTokenEx.argtypes = (wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.POINTER(wintypes.HANDLE))
    adv.DuplicateTokenEx.restype = wintypes.BOOL
    adv.ConvertStringSidToSidW.argtypes = (wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p))
    adv.ConvertStringSidToSidW.restype = wintypes.BOOL
    adv.GetLengthSid.argtypes = (ctypes.c_void_p,)
    adv.GetLengthSid.restype = wintypes.DWORD
    adv.SetTokenInformation.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
    adv.SetTokenInformation.restype = wintypes.BOOL
    adv.CreateProcessAsUserW.argtypes = (wintypes.HANDLE, wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p, wintypes.BOOL,
                                         wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR, ctypes.POINTER(STARTUPINFOW), ctypes.POINTER(PROCESS_INFORMATION))
    adv.CreateProcessAsUserW.restype = wintypes.BOOL
    k32.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    k32.WaitForSingleObject.restype = wintypes.DWORD
    k32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    k32.CloseHandle.argtypes = (wintypes.HANDLE,)
    k32.LocalFree.argtypes = (ctypes.c_void_p,)

    def check(ok, what):
        if not ok:
            err = ctypes.get_last_error()
            raise OSError(err, "%s failed (Windows error %d)" % (what, err))
    tok, low = wintypes.HANDLE(), wintypes.HANDLE()
    check(adv.OpenProcessToken(k32.GetCurrentProcess(), 0x0001 | 0x0002 | 0x0008 | 0x0080, ctypes.byref(tok)), "OpenProcessToken")
    check(adv.DuplicateTokenEx(tok, 0, None, 2, 1, ctypes.byref(low)), "DuplicateTokenEx")       # SecurityImpersonation, TokenPrimary
    sid = ctypes.c_void_p()
    check(adv.ConvertStringSidToSidW("S-1-16-4096", ctypes.byref(sid)), "ConvertStringSidToSidW")   # the low mandatory level
    tml = TOKEN_MANDATORY_LABEL()
    tml.Label.Sid, tml.Label.Attributes = sid, 0x20                                              # SE_GROUP_INTEGRITY
    check(adv.SetTokenInformation(low, 25, ctypes.byref(tml), ctypes.sizeof(tml) + adv.GetLengthSid(sid)), "SetTokenInformation")  # TokenIntegrityLevel
    si, pi = STARTUPINFOW(), PROCESS_INFORMATION()
    si.cb = ctypes.sizeof(si)
    buf = ctypes.create_unicode_buffer(cmdline)
    try:
        check(adv.CreateProcessAsUserW(low, None, buf, None, None, False, 0x08000000, None, cwd, ctypes.byref(si), ctypes.byref(pi)),
              "CreateProcessAsUserW")                                                            # CREATE_NO_WINDOW
        k32.WaitForSingleObject(pi.hProcess, 1800 * 1000)
        code = wintypes.DWORD()
        k32.GetExitCodeProcess(pi.hProcess, ctypes.byref(code))
        k32.CloseHandle(pi.hThread)
        k32.CloseHandle(pi.hProcess)
        return code.value
    finally:
        k32.LocalFree(sid)
        k32.CloseHandle(low)
        k32.CloseHandle(tok)


def main():
    p = Probe(4, "low_integrity")
    windows_only(p)
    low = tempfile.mkdtemp(prefix="vs-low-")
    medium = tempfile.mkdtemp(prefix="vs-medium-")
    try:
        r = subprocess.run(["icacls", low, "/setintegritylevel", "(OI)(CI)Low"], capture_output=True, text=True)
        if not p.case("folder-labelled-low", "HELD" if r.returncode == 0 else "BROKEN", icacls=r.returncode):
            return p.verdict(incomplete="icacls could not label the folder")
        ignore = shutil.ignore_patterns("build", "__pycache__", "unreal", "work")
        for sub in ("art", "graybox", "design"):
            shutil.copytree(os.path.join(REPO, sub), os.path.join(low, "repo", sub), ignore=ignore)
        for f in ("shell.exe", "shell"):
            src = os.path.join(REPO, "verify", "build", f)
            if os.path.exists(src):
                os.makedirs(os.path.join(low, "repo", "verify", "build"), exist_ok=True)
                shutil.copy(src, os.path.join(low, "repo", "verify", "build", f))
        os.makedirs(os.path.join(medium, "studio"))
        medium_file = os.path.join(medium, "studio", "active.json")
        open(medium_file, "w").write('{"stands for": "the active pointer"}')
        before = open(medium_file, "rb").read()
        child = os.path.join(low, "child.py")
        open(child, "w").write(CHILD)
        cmd = subprocess.list2cmdline([sys.executable, "-B", child, low, medium_file])
        t0 = time.time()
        try:
            rc = start_low(cmd, low)
        except OSError as e:
            p.case("start-at-low-integrity", "BROKEN", error=e.errno, what=str(e)[:80])
            return p.verdict(incomplete="a low-integrity process could not be started here")
        p.case("start-at-low-integrity", "HELD" if rc == 0 else "BROKEN", exit=rc, seconds=round(time.time() - t0, 1))
        res = json.loads(open(os.path.join(low, "results.json")).read())
        p.case("write-own-folder", "HELD" if res.get("write_own_folder") is True else "BROKEN")
        refused = res.get("write_medium_refused") is True and open(medium_file, "rb").read() == before
        p.case("write-to-medium-refused", "HELD" if refused else "BROKEN", error=res.get("write_medium_error", "-"))
        killed = None
        for name, args in (("art-checks", ["art/check.py"]), ("studio-selftest", ["art/studio.py", "selftest"])):
            r_ = res.get(name, {})
            if r_.get("rc") == 0:
                p.case(name + "-at-low", "HELD", last=r_.get("last", ""))
                continue
            env = dict(os.environ, PYTHONHASHSEED="0")
            m = subprocess.run([sys.executable, "-B"] + args, cwd=os.path.join(low, "repo"), env=env, capture_output=True, text=True, timeout=900)
            p.case(name + "-at-low", "BROKEN", last=r_.get("last", ""), err=r_.get("err", "")[-80:], at_medium_rc=m.returncode)
            if m.returncode == 0:
                killed = "%s passes at medium and fails at low integrity: the boundary is tamper-evidence only" % name
        if not refused:
            killed = killed or "a low-integrity process wrote the medium file: no capability boundary"
        return p.verdict(killed=killed)
    finally:
        shutil.rmtree(low, ignore_errors=True)
        shutil.rmtree(medium, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
