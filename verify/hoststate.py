# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""hoststate.py — HOST-STATE-0: record the host's observable state beside a court's number. Record, don't control.

PRESENT-STRETCH-0's confirmation ran with the default mode's blit p50 59% higher than its first run (7,274 -> 11,589 µs)
at a similar refresh, and no court could say why. This module records what the OS will report about the host, so a
later cross-run drift can be set beside a host-state change (or beside no change, which is also evidence that the
recorded state is insufficient). It is an apparatus, not an optimization: it changes nothing, and no court's rule reads
it.

    python verify/hoststate.py        # print one snapshot (a look, not a record: nothing is written)

A court opts in through `diagcommon.host_run(..., probe=dict)`, which takes one snapshot immediately before the window
court starts and one immediately after it ends, and never refuses because of them: `capture_safe` turns any failure
into an `unavailable` marker. Every value is an integer or a string (RECORD-0 allows no floats). Each field is captured
on its own; one that fails is recorded as unavailable with its reason, and the rest are still recorded.

Fields (Windows only; on any other platform each is recorded as unavailable):
  cpu      the model (registry), logical processors, and per-processor MHz as CallNtPowerInformation reports it
  power    AC line and battery status, battery saver, and the active power plan (`powercfg /getactivescheme`, a query)
  load     the system's CPU busy share over a 1000 ms window (GetSystemTimes)
  memory   memory load and physical memory (GlobalMemoryStatusEx)
  process  the sealing process's priority class and affinity (the court process is its child)
  display  the screen's logical and physical size, depth and nominal vertical refresh (GetDeviceCaps)
  uptime   milliseconds since boot (GetTickCount64)
  thermal  declared not captured: no reliable source without elevation

HOST-STATE-1 (version 2, appended; HOST-STATE-0's version 1 is unchanged and stays the default, so every court that
cites HOST-STATE-0 records exactly what it recorded before) adds two fields, read through the performance-counter
library (PDH, English counter names, so the paths do not depend on the display language), each over its own 1000 ms
window:
  clock    \Processor Information(_Total): Processor Frequency (the nominal MHz), % Processor Performance and
           % Processor Utility (uncapped: both exceed 100% under boost), and the effective-MHz estimate the OS's own
           arithmetic gives (nominal x performance); the counters as the OS computes them, not a measured clock
  faults   \Memory: Page Faults/sec, Page Reads/sec and Pages Input/sec — system-wide rates, hard faults are the reads
A court asks for version 2 explicitly (`capture(version=2)`); `python verify/hoststate.py` prints a version 2 look.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time

FIELDS = ("cpu", "power", "load", "memory", "process", "display", "uptime", "thermal")
LOAD_WINDOW_MS = 1000
NOT_WINDOWS = "not captured: HOST-STATE-0 reads a Windows host only"
THERMAL = "not captured: no reliable source without elevation (declared, not attempted)"
# HOST-STATE-1 (version 2): HOST-STATE-0's fields, then two appended; version 1 stays the default
FIELDS_V2 = FIELDS + ("clock", "faults")
COUNTER_WINDOW_MS = 1000
VERSIONS = {1: ("HOST-STATE-0", FIELDS), 2: ("HOST-STATE-1", FIELDS_V2)}
NOT_WINDOWS_V2 = "not captured: HOST-STATE-1 reads a Windows host only"
CLOCK_COUNTERS = (("processor_frequency_mhz", r"\Processor Information(_Total)\Processor Frequency", 1),
                  ("performance_permille", r"\Processor Information(_Total)\% Processor Performance", 10),
                  ("utility_permille", r"\Processor Information(_Total)\% Processor Utility", 10))
FAULT_COUNTERS = (("page_faults_per_s", r"\Memory\Page Faults/sec", 1),
                  ("page_reads_per_s", r"\Memory\Page Reads/sec", 1),
                  ("pages_input_per_s", r"\Memory\Pages Input/sec", 1))
PDH_FMT_DOUBLE, PDH_FMT_NOCAP100 = 0x00000200, 0x00008000


def cpu() -> dict:
    import ctypes
    import winreg
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
        model = str(winreg.QueryValueEx(key, "ProcessorNameString")[0]).strip()
    n = os.cpu_count() or 0
    out: dict = {"model": model, "logical_processors": n}

    class PPI(ctypes.Structure):
        _fields_ = [("Number", ctypes.c_ulong), ("MaxMhz", ctypes.c_ulong), ("CurrentMhz", ctypes.c_ulong),
                    ("MhzLimit", ctypes.c_ulong), ("MaxIdleState", ctypes.c_ulong), ("CurrentIdleState", ctypes.c_ulong)]

    try:
        arr = (PPI * max(n, 1))()
        pp = ctypes.WinDLL("powrprof")
        pp.CallNtPowerInformation.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong]
        pp.CallNtPowerInformation.restype = ctypes.c_long
        status = pp.CallNtPowerInformation(11, None, 0, ctypes.byref(arr), ctypes.sizeof(arr))  # 11 = ProcessorInformation
        if status != 0:
            out["mhz"] = {"unavailable": "CallNtPowerInformation status 0x%08x" % (status & 0xFFFFFFFF)}
        else:
            cur = sorted(int(p.CurrentMhz) for p in arr)
            out["mhz"] = {"current_min": cur[0], "current_median": cur[len(cur) // 2], "current_max": cur[-1],
                          "max": max(int(p.MaxMhz) for p in arr), "limit_min": min(int(p.MhzLimit) for p in arr),
                          "source": "CallNtPowerInformation(ProcessorInformation), as the OS reports it"}
    except Exception as e:  # the MHz are one sub-field; the model and count still stand
        out["mhz"] = {"unavailable": _why(e)}
    return out


def power() -> dict:
    import ctypes

    class SPS(ctypes.Structure):
        _fields_ = [("ACLineStatus", ctypes.c_ubyte), ("BatteryFlag", ctypes.c_ubyte), ("BatteryLifePercent", ctypes.c_ubyte),
                    ("SystemStatusFlag", ctypes.c_ubyte), ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]

    s = SPS()
    k32 = ctypes.WinDLL("kernel32")
    if not k32.GetSystemPowerStatus(ctypes.byref(s)):
        raise OSError("GetSystemPowerStatus failed")
    out: dict = {"ac_line_status": int(s.ACLineStatus), "battery_flag": int(s.BatteryFlag),
                 "battery_percent": int(s.BatteryLifePercent), "battery_saver": int(s.SystemStatusFlag),
                 "codes": "ac_line_status 0 offline, 1 online, 255 unknown; battery_percent 255 unknown"}
    try:
        cp = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True, text=True, timeout=10, errors="replace")
        m = re.search(r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\s*\((.*)\)", cp.stdout)
        out["plan"] = ({"guid": m.group(1).lower(), "name": m.group(2).strip()} if m
                       else {"unavailable": "the powercfg output was not recognised"})
    except Exception as e:
        out["plan"] = {"unavailable": _why(e)}
    return out


def load() -> dict:
    import ctypes

    class FT(ctypes.Structure):
        _fields_ = [("lo", ctypes.c_ulong), ("hi", ctypes.c_ulong)]

    k32 = ctypes.WinDLL("kernel32")

    def times():
        i, k, u = FT(), FT(), FT()
        if not k32.GetSystemTimes(ctypes.byref(i), ctypes.byref(k), ctypes.byref(u)):
            raise OSError("GetSystemTimes failed")
        return tuple((f.hi << 32) | f.lo for f in (i, k, u))

    i0, k0, u0 = times()
    time.sleep(LOAD_WINDOW_MS / 1000)
    i1, k1, u1 = times()
    total = (k1 - k0) + (u1 - u0)  # kernel time includes idle time
    busy = 0 if total <= 0 else ((total - (i1 - i0)) * 1000) // total
    return {"cpu_busy_permille": int(busy), "window_ms": LOAD_WINDOW_MS,
            "source": "GetSystemTimes over the window, all processors"}


def memory() -> dict:
    import ctypes

    class MSX(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

    m = MSX()
    m.dwLength = ctypes.sizeof(MSX)
    if not ctypes.WinDLL("kernel32").GlobalMemoryStatusEx(ctypes.byref(m)):
        raise OSError("GlobalMemoryStatusEx failed")
    return {"load_percent": int(m.dwMemoryLoad), "total_mb": int(m.ullTotalPhys) // (1 << 20),
            "available_mb": int(m.ullAvailPhys) // (1 << 20)}


def process() -> dict:
    import ctypes
    k32 = ctypes.WinDLL("kernel32")
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    k32.GetPriorityClass.argtypes = [ctypes.c_void_p]
    k32.GetPriorityClass.restype = ctypes.c_ulong
    k32.GetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
    h = k32.GetCurrentProcess()
    pc = int(k32.GetPriorityClass(h))
    pm, sm = ctypes.c_size_t(), ctypes.c_size_t()
    if not k32.GetProcessAffinityMask(h, ctypes.byref(pm), ctypes.byref(sm)):
        raise OSError("GetProcessAffinityMask failed")
    return {"priority_class": "0x%x" % pc, "affinity_mask": "0x%x" % pm.value, "system_affinity_mask": "0x%x" % sm.value,
            "of": "the sealing process; the court process is its child"}


def display() -> dict:
    import ctypes
    u32, g32 = ctypes.WinDLL("user32"), ctypes.WinDLL("gdi32")
    u32.GetDC.argtypes = [ctypes.c_void_p]
    u32.GetDC.restype = ctypes.c_void_p
    u32.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    g32.GetDeviceCaps.argtypes = [ctypes.c_void_p, ctypes.c_int]
    g32.GetDeviceCaps.restype = ctypes.c_int
    hdc = u32.GetDC(None)
    if not hdc:
        raise OSError("GetDC(NULL) failed")
    try:
        cap = lambda i: int(g32.GetDeviceCaps(hdc, i))  # noqa: E731
        return {"logical": [cap(8), cap(10)], "physical": [cap(118), cap(117)], "bits_per_pixel": cap(12),
                "vertical_refresh_hz": cap(116),
                "source": "GetDeviceCaps on the screen DC: the nominal mode, not the court's measured refresh"}
    finally:
        u32.ReleaseDC(None, hdc)


def uptime() -> dict:
    import ctypes
    k32 = ctypes.WinDLL("kernel32")
    k32.GetTickCount64.restype = ctypes.c_ulonglong
    return {"ms": int(k32.GetTickCount64())}


def _pdh(counters) -> dict:
    """Read `counters` ((name, English path, scale), ...) once over COUNTER_WINDOW_MS: two collections a window apart,
    each value formatted uncapped as a double, scaled and rounded to an integer. A counter that cannot be added or
    formatted is recorded as unavailable with its PDH status; the others still stand. Reads only."""
    import ctypes

    class FCV(ctypes.Structure):  # PDH_FMT_COUNTERVALUE: a status, then the 8-byte-aligned union read as a double
        _fields_ = [("CStatus", ctypes.c_ulong), ("doubleValue", ctypes.c_double)]

    pdh = ctypes.WinDLL("pdh")
    pdh.PdhOpenQueryW.argtypes = [ctypes.c_wchar_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p)]
    pdh.PdhAddEnglishCounterW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p)]
    pdh.PdhCollectQueryData.argtypes = [ctypes.c_void_p]
    pdh.PdhGetFormattedCounterValue.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(FCV)]
    pdh.PdhCloseQuery.argtypes = [ctypes.c_void_p]
    for f in (pdh.PdhOpenQueryW, pdh.PdhAddEnglishCounterW, pdh.PdhCollectQueryData, pdh.PdhGetFormattedCounterValue, pdh.PdhCloseQuery):
        f.restype = ctypes.c_long
    status = lambda st: "PDH status 0x%08x" % (st & 0xFFFFFFFF)  # noqa: E731
    q = ctypes.c_void_p()
    st = pdh.PdhOpenQueryW(None, 0, ctypes.byref(q))
    if st != 0:
        raise OSError("PdhOpenQueryW: " + status(st))
    try:
        handles, out = {}, {}
        for name, path, _ in counters:
            h = ctypes.c_void_p()
            st = pdh.PdhAddEnglishCounterW(q, path, 0, ctypes.byref(h))
            if st != 0:
                out[name] = {"unavailable": "PdhAddEnglishCounterW(%s): %s" % (path, status(st))}
            else:
                handles[name] = h
        st = pdh.PdhCollectQueryData(q)
        if st != 0:
            raise OSError("PdhCollectQueryData (first): " + status(st))
        time.sleep(COUNTER_WINDOW_MS / 1000)
        st = pdh.PdhCollectQueryData(q)
        if st != 0:
            raise OSError("PdhCollectQueryData (second): " + status(st))
        for name, path, scale in counters:
            if name not in handles:
                continue
            v = FCV()
            st = pdh.PdhGetFormattedCounterValue(handles[name], PDH_FMT_DOUBLE | PDH_FMT_NOCAP100, None, ctypes.byref(v))
            if st != 0 or v.CStatus not in (0, 1):  # PDH_CSTATUS_VALID_DATA or PDH_CSTATUS_NEW_DATA
                out[name] = {"unavailable": "PdhGetFormattedCounterValue(%s): %s, counter %s" % (path, status(st), status(v.CStatus))}
            else:
                out[name] = int(round(v.doubleValue * scale))
        return {name: out[name] for name, _, _ in counters}
    finally:
        pdh.PdhCloseQuery(q)


def clock() -> dict:
    out = _pdh(CLOCK_COUNTERS)
    f, p = out["processor_frequency_mhz"], out["performance_permille"]
    out["effective_mhz_estimate"] = ((f * p) // 1000 if isinstance(f, int) and isinstance(p, int)
                                     else {"unavailable": "needs processor_frequency_mhz and performance_permille"})
    out["window_ms"] = COUNTER_WINDOW_MS
    out["source"] = ("PDH \\Processor Information(_Total) over the window, uncapped; the estimate is nominal x performance, "
                     "as the OS computes its counters, not a measured clock")
    return out


def faults() -> dict:
    out = _pdh(FAULT_COUNTERS)
    out["window_ms"] = COUNTER_WINDOW_MS
    out["source"] = "PDH \\Memory rates over the window, system-wide; page reads are hard faults, not the court's own"
    return out


CAPTURE = {"cpu": cpu, "power": power, "load": load, "memory": memory, "process": process, "display": display,
           "uptime": uptime, "clock": clock, "faults": faults}


def _why(e: BaseException) -> str:
    return ("%s: %s" % (type(e).__name__, e))[:200]


def capture(windows: bool | None = None, version: int = 1) -> dict:
    """One snapshot. Each field is captured on its own; a failing field is recorded as unavailable with its reason.
    Version 1 is HOST-STATE-0's snapshot, unchanged; version 2 (HOST-STATE-1) appends clock and faults."""
    rung, names = VERSIONS[version]
    windows = (os.name == "nt") if windows is None else windows
    fields: dict = {}
    for name in names:
        if name == "thermal":
            fields[name] = {"unavailable": THERMAL}
        elif not windows:
            fields[name] = {"unavailable": NOT_WINDOWS if version == 1 else NOT_WINDOWS_V2}
        else:
            try:
                fields[name] = CAPTURE[name]()
            except Exception as e:
                fields[name] = {"unavailable": _why(e)}
    return {"hoststate": rung, "version": version, "unix_seconds": int(time.time()), "platform": sys.platform,
            "fields": fields}


def validate(snap: dict) -> dict:
    """A snapshot is integers, strings, lists and dicts only (no floats, no booleans), with every registered field."""
    def walk(x, where):
        if isinstance(x, bool) or isinstance(x, float) or x is None:
            raise ValueError("HOST-STATE-0 value at %s is %r: only integers and strings are recorded" % (where, x))
        if isinstance(x, dict):
            for k, v in x.items():
                if not isinstance(k, str):
                    raise ValueError("a non-string key at %s" % where)
                walk(v, where + "." + k)
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, "%s[%d]" % (where, i))
        elif not isinstance(x, (int, str)):
            raise ValueError("HOST-STATE-0 value at %s has type %s" % (where, type(x).__name__))
    walk(snap, "snapshot")
    ver = snap.get("version")
    if ver not in VERSIONS or snap.get("hoststate") != VERSIONS[ver][0] or tuple(snap.get("fields", {}).keys()) != VERSIONS[ver][1]:
        raise ValueError("not a HOST-STATE-0 (version 1) or HOST-STATE-1 (version 2) snapshot with its registered fields in order")
    return snap


def capture_safe(fn=None, version: int = 1) -> dict:
    """Never raises: a snapshot that fails to capture or to validate is recorded as unavailable, so recording can
    never block or alter a court."""
    try:
        return validate((fn or (lambda: capture(version=version)))())
    except Exception as e:
        return {"hoststate": VERSIONS.get(version, VERSIONS[1])[0], "version": version if version in VERSIONS else 1,
                "unavailable": _why(e)}


def main() -> int:
    print(json.dumps(capture_safe(version=2), indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
