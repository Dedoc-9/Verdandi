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


CAPTURE = {"cpu": cpu, "power": power, "load": load, "memory": memory, "process": process, "display": display,
           "uptime": uptime}


def _why(e: BaseException) -> str:
    return ("%s: %s" % (type(e).__name__, e))[:200]


def capture(windows: bool | None = None) -> dict:
    """One snapshot. Each field is captured on its own; a failing field is recorded as unavailable with its reason."""
    windows = (os.name == "nt") if windows is None else windows
    fields: dict = {}
    for name in FIELDS:
        if name == "thermal":
            fields[name] = {"unavailable": THERMAL}
        elif not windows:
            fields[name] = {"unavailable": NOT_WINDOWS}
        else:
            try:
                fields[name] = CAPTURE[name]()
            except Exception as e:
                fields[name] = {"unavailable": _why(e)}
    return {"hoststate": "HOST-STATE-0", "version": 1, "unix_seconds": int(time.time()), "platform": sys.platform,
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
    if snap.get("hoststate") != "HOST-STATE-0" or tuple(snap.get("fields", {}).keys()) != FIELDS:
        raise ValueError("not a HOST-STATE-0 snapshot with the registered fields in order")
    return snap


def capture_safe(fn=None) -> dict:
    """Never raises: a snapshot that fails to capture or to validate is recorded as unavailable, so recording can
    never block or alter a court."""
    try:
        return validate((fn or capture)())
    except Exception as e:
        return {"hoststate": "HOST-STATE-0", "version": 1, "unavailable": _why(e)}


def main() -> int:
    print(json.dumps(capture_safe(), indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
