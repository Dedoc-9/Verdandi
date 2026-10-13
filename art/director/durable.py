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
#                             (os._exit, no cleanup), which is how `art/director.py crashtest` kills it; HOOK, when
#                             set, is called there first (how `art/director.py racetest` starts a second writer)
#   locked(path, wait)        the content lock (B1's fix 1, the owner's ruling of 2026-10-13): held by every writer of
#                             a tree's ledgers, briefs, tags and maps, and by recovery. In this process a reentrant
#                             lock (threads); between processes the operating system's lock on the file at `path`
#                             (msvcrt.locking on Windows, flock elsewhere), which the system releases when its holder
#                             ends — the lease: no timeout ever takes the lock from a holder that is alive. A writer
#                             that cannot have it within `wait` seconds raises Busy and has changed nothing.
#
# What it relies on, and does not prove: that a flushed write survives the end of the process (the operating system
# keeps it); that the rename leaves the old file or the new at the name. Both are the axioms of
# docs/STUDIO-APP.md §5.2 (A1, A2); an operating-system crash or a power loss is not claimed. Windows releases a dead
# holder's lock "depends upon available system resources" later (LockFileEx), which `wait` absorbs.

import contextlib
import os
import sys
import threading
import time

CRASH = os.environ.get("VERDANDI_CRASH_AT", "")
CRASH_EXIT = 77
HOOK = None                      # the race court's: called with each death point's name before anything else there
WAIT = float(os.environ.get("VERDANDI_LOCK_WAIT", "60"))
# a planted defect for the race court only (art/director.py racetest): "no-lock" (locked() holds nothing),
# "no-fence" (an admission does not read the head again under the lock), "recover-ignores-lock"
PLANT = os.environ.get("VERDANDI_PLANT", "")


def point(name):
    """End the process here if the crash test asked for this point (the race court's hook first)."""
    if HOOK is not None:
        HOOK(name)
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


# ------------------------------------------------------------------------------------------------ the content lock
class Busy(Exception):
    """The content lock was held by another writer for the whole wait."""


class _Lock:
    def __init__(self, path):
        self.path, self.rlock, self.depth, self.fh = path, threading.RLock(), 0, None

    def acquire(self, wait):
        deadline = time.monotonic() + max(0.0, wait)
        got = self.rlock.acquire(timeout=wait) if wait > 0 else self.rlock.acquire(blocking=False)
        if not got:
            raise Busy(self.path)
        if self.depth == 0:                      # the outermost holder in this process takes the system's lock
            try:
                self.fh = self._os_lock(deadline)
            except BaseException:
                self.rlock.release()
                raise
        self.depth += 1

    def _os_lock(self, deadline):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        fh = open(self.path, "a+b")
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return fh
            except OSError:
                if time.monotonic() >= deadline:
                    fh.close()
                    raise Busy(self.path)
                time.sleep(0.02)

    def release(self):
        self.depth -= 1
        if self.depth == 0:
            fh, self.fh = self.fh, None
            try:
                if os.name == "nt":
                    import msvcrt
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            finally:
                fh.close()
        self.rlock.release()


_LOCKS = {}
_LOCKS_GUARD = threading.Lock()


@contextlib.contextmanager
def locked(path, wait=None):
    """Hold the content lock whose file is `path` (reentrant in the thread that holds it)."""
    if PLANT == "no-lock":
        yield
        return
    path = os.path.abspath(path)
    with _LOCKS_GUARD:
        lk = _LOCKS.setdefault(os.path.normcase(path), _Lock(path))
    lk.acquire(WAIT if wait is None else wait)
    try:
        yield
    finally:
        lk.release()
