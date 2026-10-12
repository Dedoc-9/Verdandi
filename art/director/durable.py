# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/director/durable.py — the content path's writes, made to survive the death of the process that makes them
# (STUDIO-APP-0's B1; docs/STUDIO-CONTRACT.md). Standard library only.
#
#   append(path, data)        add bytes to the end of a file, flushed to the disk before it returns
#   write(path, data)         replace a file's bytes whole: a temporary file beside it, flushed, then renamed over it
#                             (MoveFileExW with REPLACE_EXISTING | WRITE_THROUGH on Windows, retried while another
#                             process holds the file; os.replace and a flush of the directory elsewhere)
#   point(name)               a death point: when VERDANDI_CRASH_AT names it, the process ends there at once
#                             (os._exit, no cleanup), which is how `art/director.py crashtest` kills it
#
# What it relies on, and does not prove: that a flushed write survives the end of the process (the operating system
# keeps it); that the rename leaves the old file or the new at the name. Both are the axioms of
# docs/STUDIO-APP.md §5.2 (A1, A2); an operating-system crash or a power loss is not claimed.

import os
import sys
import time

CRASH = os.environ.get("VERDANDI_CRASH_AT", "")
CRASH_EXIT = 77


def point(name):
    """End the process here if the crash test asked for this point."""
    if CRASH and CRASH == name:
        sys.stdout.flush()
        os._exit(CRASH_EXIT)


def torn(name):
    """True if the crash test asked for a torn write at this point (the caller writes half, then calls die())."""
    return bool(CRASH) and CRASH == "torn:" + name


def die():
    os._exit(CRASH_EXIT)


def _fsync_dir(path):
    if os.name == "nt":
        return                        # a directory cannot be opened for flushing here; its entries pre-exist (A3)
    try:
        fd = os.open(path or ".", os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _MoveFileExW = _k32.MoveFileExW
    _MoveFileExW.argtypes = (wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD)
    _MoveFileExW.restype = wintypes.BOOL
    _REPLACE_EXISTING, _WRITE_THROUGH = 0x1, 0x8
    _SHARING, _DENIED = 32, 5

    def _rename(src, dst):
        for i in range(40):              # another process (an editor, an antivirus) may hold dst for a moment
            if _MoveFileExW(src, dst, _REPLACE_EXISTING | _WRITE_THROUGH):
                return
            err = ctypes.get_last_error()
            if err not in (_SHARING, _DENIED) or i == 39:
                raise OSError(err, "MoveFileExW %s -> %s failed (Windows error %d)" % (src, dst, err))
            time.sleep(0.05)
else:
    def _rename(src, dst):
        os.replace(src, dst)
        _fsync_dir(os.path.dirname(os.path.abspath(dst)))


def append(path, data):
    """Append data and flush it to the disk. The file is created if it is missing (and its directory flushed)."""
    new = not os.path.exists(path)
    if new:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "ab") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    if new:
        _fsync_dir(os.path.dirname(os.path.abspath(path)))


def write(path, data):
    """Replace path's bytes with data: the old bytes or the new are at the name, whenever the process ends."""
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    tmp = os.path.join(d, ".%s.%d.tmp" % (os.path.basename(path), os.getpid()))
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    _rename(tmp, path)


def remove_tree(path):
    """Remove a directory this module's caller owns (a finished pending transaction)."""
    import shutil
    shutil.rmtree(path, ignore_errors=True)
