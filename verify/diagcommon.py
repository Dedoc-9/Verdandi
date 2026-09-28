# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""diagcommon.py — the shared host flow of the host courts (PRESENT-STRETCH-0, ALLOC-REUSE-0, ALLOC-REUSE-1).

Each court's sealer supplies its own check/seal functions; this module holds only what they do identically: build the
window shell with LATENCY-0's flags, check the sealed session, run the headless court on THIS build (witnesses first),
run the window court with its output streamed to the console, and write the sealed record (or a --confirm record).

HOST-STATE-0: a court that passes `probe=dict` gets one host-state snapshot immediately before its window court and
one immediately after, through `hoststate.capture_safe`, which never raises. The probe is optional (the diagnostic
courts do not pass one), it cannot refuse a run, and no rule reads what it records. The snapshot is HOST-STATE-0's
version 1 unless the court's own entry asks for HOST-STATE-1's version 2 through `hoststate_version` (DRIFT-0 does).

DRIFT-0: a window court that refuses raises CourtRefused (a Refuse), so a sealer that keeps refused runs can tell a
run that happened and refused from a run that never started; every other sealer treats it as the Refuse it always was."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "verify"))
import envelope  # noqa: E402
import hoststate  # noqa: E402


class Refuse(Exception):
    pass


class CourtRefused(Refuse):
    """The window court ran and refused (or wrote nothing): a run that happened."""


def registry() -> dict:
    with open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8") as fh:
        return json.load(fh)["entries"]


def host_run(rung: str, cmd: str, host: str, session_path: str, per_cell: int, selftest_per_cell: int,
             probe: dict | None = None, hoststate_version: int = 1) -> tuple[dict, dict, dict]:
    """Build, witnesses first, run the window court -> (raw record, session provenance, build provenance). With `probe`,
    host-state snapshots (HOST-STATE-0's version 1 unless the court's entry asks for version 2) are taken just before
    and just after the window court (recorded, never ruled on)."""
    run = dict(capture_output=True, text=True, encoding="utf-8", errors="replace")
    if os.name != "nt":
        raise Refuse(f"{rung} is Windows-only (the instrument is the GDI/DWM window)")
    if rung not in registry():
        raise Refuse(f"{rung} is not preregistered — no number before the method")
    rustc = shutil.which("rustc")
    if rustc is None:
        raise Refuse("rustc not found")
    build_dir = os.path.join(ROOT, "verify", "build")
    os.makedirs(build_dir, exist_ok=True)
    exe = os.path.join(build_dir, f"shell-{cmd}.exe")
    flags = ["-O", "--cfg", "shell_window"]
    cp = subprocess.run([rustc] + flags + [os.path.join(ROOT, "shell", "main.rs"), "-o", exe], **run)
    if cp.returncode != 0:
        raise Refuse("rustc failed:\n" + cp.stderr)
    build = {"rustc": subprocess.run([rustc, "--version"], **run).stdout.strip(), "flags": flags}
    srec = envelope.read(os.path.join(ROOT, session_path))
    session = {"path": session_path, "chain_hash": srec["chain_hash"], "head": srec["data"]["head"]}
    cp = subprocess.run([exe, f"{cmd}-selftest", "--session", session_path, "--per-cell", str(selftest_per_cell)], cwd=ROOT, **run)
    if cp.returncode != 0 or f"{cmd} court OK" not in cp.stdout:
        raise Refuse("the headless court did not reproduce the sealed witnesses — no number is taken\n" + cp.stdout + cp.stderr)
    raw_path = os.path.join(build_dir, f"{cmd}-raw-{host}.json")
    if os.path.exists(raw_path):
        os.remove(raw_path)
    if probe is not None:
        probe["before"] = hoststate.capture_safe(version=hoststate_version)
    sys.stdout.flush()
    rc = subprocess.run([exe, f"{cmd}-window", "--session", session_path, "--per-cell", str(per_cell), "--host", host,
                         "--out", raw_path], cwd=ROOT).returncode
    if probe is not None:
        probe["after"] = hoststate.capture_safe(version=hoststate_version)
    if rc != 0 or not os.path.exists(raw_path):
        raise CourtRefused("the window court refused or wrote nothing (its reason is printed above)")
    with open(raw_path, encoding="utf-8") as fh:
        raw = json.load(fh)
    os.remove(raw_path)
    return raw, session, build


def write_record(name: str, rec: dict) -> str:
    out_dir = os.path.join(ROOT, "shell", "attest")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name)
    envelope.write(out, rec)
    return out
