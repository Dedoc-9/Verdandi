# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# tools/probe/job_object.py — experiment 2 of docs/STUDIO-CONTRACT.md §11: a Windows job object made from Python with
# ctypes (KILL_ON_JOB_CLOSE | DIE_ON_UNHANDLED_EXCEPTION). A holder process makes the job, puts itself in it (a job
# inside the shell's own job: nested jobs), starts play.py and a provider-like grandchild (which inherit the job),
# reports their process ids, and ends. Its handle is the job's last: every process in the job must be gone.
#
#   python tools\probe\job_object.py
#
# Kill criterion: the holder cannot put itself in a job under this shell (AssignProcessToJobObject refused) → the stub
# starts the supervisor with CREATE_BREAKAWAY_FROM_JOB, and the design says so.

import json
import os
import subprocess
import sys
import time

from common import Probe, REPO, free_port, windows_only

HOLDER = r'''
import ctypes, json, os, subprocess, sys, time
from ctypes import wintypes
k32 = ctypes.WinDLL("kernel32", use_last_error=True)

class BASIC(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64), ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t), ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]

class IO(ctypes.Structure):
    _fields_ = [(n, ctypes.c_ulonglong) for n in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                                                    "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

class EXTENDED(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", BASIC), ("IoInfo", IO), ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

k32.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR); k32.CreateJobObjectW.restype = wintypes.HANDLE
k32.SetInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD); k32.SetInformationJobObject.restype = wintypes.BOOL
k32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE); k32.AssignProcessToJobObject.restype = wintypes.BOOL
k32.GetCurrentProcess.restype = wintypes.HANDLE
k32.IsProcessInJob.argtypes = (wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)); k32.IsProcessInJob.restype = wintypes.BOOL

out = {}
inner = wintypes.BOOL()
k32.IsProcessInJob(k32.GetCurrentProcess(), None, ctypes.byref(inner))
out["holder_was_in_a_job"] = bool(inner.value)
job = k32.CreateJobObjectW(None, None)
info = EXTENDED()
info.BasicLimitInformation.LimitFlags = 0x2000 | 0x400          # KILL_ON_JOB_CLOSE | DIE_ON_UNHANDLED_EXCEPTION
out["set_limits"] = bool(k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)))   # JobObjectExtendedLimitInformation
ok = k32.AssignProcessToJobObject(job, k32.GetCurrentProcess())
out["assigned"] = bool(ok)
out["assign_error"] = 0 if ok else ctypes.get_last_error()
if ok:
    port = sys.argv[2]
    server = subprocess.Popen([sys.executable, "-B", os.path.join(sys.argv[1], "art", "play.py"), "plaza-night", "--no-browser", "--no-watch", "--port", port],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    grand = subprocess.Popen([sys.executable, "-c", "import subprocess, sys, time; p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)']); "
                              "print(p.pid, flush=True); time.sleep(600)"], stdout=subprocess.PIPE, text=True)
    out["pids"] = {"server": server.pid, "provider": grand.pid, "providers_child": int(grand.stdout.readline())}
    time.sleep(8)                                                   # let the server start serving
print(json.dumps(out), flush=True)
'''


def alive(pid):
    import ctypes
    from ctypes import wintypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    k32.CloseHandle.argtypes = (wintypes.HANDLE,)
    h = k32.OpenProcess(0x1000, False, pid)                        # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    code = wintypes.DWORD()
    k32.GetExitCodeProcess(h, ctypes.byref(code))
    k32.CloseHandle(h)
    return code.value == 259                                        # STILL_ACTIVE


def main():
    p = Probe(2, "job_object")
    windows_only(p)
    port = free_port()
    r = subprocess.run([sys.executable, "-c", HOLDER, REPO, str(port)], capture_output=True, text=True, timeout=120)
    try:
        out = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        p.case("holder-ran", "BROKEN", stderr=r.stderr.strip()[-160:])
        return p.verdict(incomplete="the holder did not report")
    p.case("limits-set", "HELD" if out["set_limits"] else "BROKEN")
    if not p.case("nested-assign", "HELD" if out["assigned"] else "BROKEN", shell_job=out["holder_was_in_a_job"], error=out["assign_error"]):
        return p.verdict(killed="AssignProcessToJobObject refused under this shell: the stub breaks away (CREATE_BREAKAWAY_FROM_JOB)")
    t = time.time()
    left = dict(out["pids"])
    while time.time() - t < 5 and left:
        left = {k: v for k, v in left.items() if alive(v)}
        time.sleep(0.2)
    p.case("all-gone-when-the-job-closes", "HELD" if not left else "BROKEN", seconds=round(time.time() - t, 1),
           processes=len(out["pids"]), still_running=",".join(left) or "none")
    for v in left.values():
        subprocess.run(["taskkill", "/F", "/PID", str(v)], capture_output=True)
    return p.verdict()


if __name__ == "__main__":
    sys.exit(main())
