# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
r"""livesession.py — LIVE-SESSION-0: a saved live session made a committed record (off-gate, host).

    python verify/livesession.py --host NAME --session build/sessions/<run_id>/session.json

The shell saves every live session under build/sessions/ (gitignored) and verifies it before counting it saved. This
sealer turns one saved session into evidence the owner commits. It reads the file the shell wrote and never modifies
it: it checks the seal (the sha256 of the bytes before the seal line), the base files' W and M, that the stored head is
the fold of the stored witnesses, and that a lineage names a head on the session's own chain; it recomputes the
renderer identity from this checkout's rendering sources and says whether it is the one the session was made with (an
identity mismatch alone is not corruption: replay decides); and it has the workshop's own sessionwalk verify the saved
file itself. It then writes shell/attest/livesession-<host>-<head12>.json: a RECORD-0 envelope around the same
session-walk data, with the live block inside it, which shell playback and the workshop both replay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envelope  # noqa: E402
from diagcommon import Refuse, registry, write_record  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = ("kernel/mantle.rs", "kernel/formats.rs", "kernel/fast.rs", "kernel/hud.rs", "shell/present.rs")
# SIM-TICK-0: the sources that decide a frame at a free heading (the shell's BEARING_SOURCES, in its order)
BEARING_SOURCES = ("kernel/vocab.rs", "oracle/bearing_octant.txt", "kernel/bearing.rs", "kernel/bearingfast.rs")
TAGS = {"move": "M", "edit": "E", "look": "K", "sensitivity": "S"}
SEAL_KEY = b'\n "seal": "'
MAGIC = b"VRDNSW1"


def renderer_id(root: str = ROOT) -> str:
    """The shell's renderer identity, from this checkout's rendering sources (line endings as the repository keeps them)."""
    lines = ""
    for rel in SOURCES:
        with open(os.path.join(root, *rel.split("/")), "rb") as fh:
            lines += "%s %s\n" % (rel, hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest())
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def bearing_id(root: str = ROOT) -> str:
    """SIM-TICK-0: the shell's bearing renderer identity, formed as the renderer identity is."""
    lines = ""
    for rel in BEARING_SOURCES:
        with open(os.path.join(root, *rel.split("/")), "rb") as fh:
            lines += "%s %s\n" % (rel, hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest())
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def free_heading(token: str) -> bool:
    """SIM-TICK-0: whether a camera token carries a heading id (a free heading) rather than a facing letter."""
    return token.rsplit(",", 1)[-1] not in ("N", "E", "S", "W")


def seal_ok(raw: bytes) -> bool:
    i = raw.rfind(SEAL_KEY)
    if i < 0:
        return False
    tail = raw[i + len(SEAL_KEY):]
    return tail == hashlib.sha256(raw[:i + 1]).hexdigest().encode("ascii") + b'"\n}\n'


def heads(content: str, camera: str, log: list) -> list:
    """The chain's heads from the base: the genesis, then one per event (the workshop's fold)."""
    h = hashlib.sha256(MAGIC + content.encode("utf-8") + b"@" + camera.encode("utf-8")).hexdigest()
    out = [h]
    for item in log:
        tag = TAGS[item["kind"]]
        if tag == "S":
            # SIM-TICK-0a: a sensitivity event is configuration, not a world event: it folds nothing
            out.append(h)
            continue
        # SIM-TICK-0: a look folds its camera token with its witness
        wit = item["camera"] + ":" + item["witness"] if tag == "K" else item["witness"]
        h = hashlib.sha256(("%s:%s:%s" % (h, tag, wit)).encode("utf-8")).hexdigest()
        out.append(h)
    return out


def check_saved(raw: bytes, root: str = ROOT) -> dict:
    """The saved session's own integrity, without rendering: the seal, the shape, the base, the fold, the lineage."""
    if not seal_ok(raw):
        raise Refuse("the saved session's seal does not match its bytes")
    doc = json.loads(raw.decode("utf-8"))
    d, live = doc.get("data", {}), doc.get("live", {})
    if doc.get("name") != "verdandi-session-walk" or d.get("magic") != "VRDNSW1" or live.get("log") != "LIVE-SESSION-0":
        raise Refuse("not a LIVE-SESSION-0 session-walk")
    b = d["base"]
    with open(os.path.join(root, b["level"]), "rb") as fh:
        lv = fh.read()
    with open(os.path.join(root, b["tiles"]), "rb") as fh:
        tl = fh.read()
    content = hashlib.sha256(hashlib.sha256(lv).digest() + hashlib.sha256(tl).digest()).hexdigest()
    if (hashlib.sha256(lv).hexdigest(), hashlib.sha256(tl).hexdigest(), content) != (b["W"], b["M"], b["content"]):
        raise Refuse("the base files are not the W and M the session was made over")
    hs = heads(b["content"], b["camera"], d["log"])
    if hs[-1] != d["head"]:
        raise Refuse("the stored head is not the fold of the stored witnesses")
    moves = sum(1 for x in d["log"] if x["kind"] == "move")
    looks = sum(1 for x in d["log"] if x["kind"] == "look")
    settings = sum(1 for x in d["log"] if x["kind"] == "sensitivity")
    if (d["moves"], d["edits"], d.get("looks", 0), d.get("sensitivity_changes", 0)) != (moves, len(d["log"]) - moves - looks - settings, looks, settings):
        raise Refuse("the move, edit, look and sensitivity counts are not the log's")
    lin = live.get("lineage")
    if lin is not None:
        n = lin.get("parent_events")
        if not isinstance(n, int) or not 0 <= n <= len(d["log"]) or hs[n] != lin.get("parent_head"):
            raise Refuse("the lineage names a parent head that is not on this session's own chain")
    return doc


def workshop_verify(path: str, root: str = ROOT) -> str:
    """The workshop's own sessionwalk, built here, verifies the saved file itself."""
    rustc = shutil.which("rustc")
    if rustc is None:
        raise Refuse("rustc not found")
    exe = os.path.join(root, "verify", "build", "sessionwalk-livesession" + (".exe" if os.name == "nt" else ""))
    os.makedirs(os.path.dirname(exe), exist_ok=True)
    cp = subprocess.run([rustc, "-O", os.path.join(root, "workshop", "sessionwalk.rs"), "-o", exe], capture_output=True, text=True)
    if cp.returncode != 0:
        raise Refuse("rustc failed:\n" + cp.stderr)
    cp = subprocess.run([exe, "verify", "--session", os.path.abspath(path)], capture_output=True, text=True, cwd=root)
    if cp.returncode != 0 or "SESSIONWALK verify OK" not in cp.stdout:
        raise Refuse("the workshop's sessionwalk does not verify the saved session: " + (cp.stderr.strip() or cp.stdout.strip()))
    return cp.stdout.strip()


def seal_livesession(raw: bytes, reg: dict, host: str, workshop: str, root: str = ROOT) -> dict:
    doc = check_saved(raw, root)
    d, live = doc["data"], doc["live"]
    now = renderer_id(root)
    same = now == live.get("renderer")
    # SIM-TICK-0: a frame at a free heading is the bearing kernels'; their identity counts only if there is one
    looks = d.get("looks", 0)
    free = sum(1 for x in d["log"] if x["kind"] in ("move", "look") and free_heading(x["camera"]))
    if free:
        same = same and bearing_id(root) == live.get("bearing")
    lin = live.get("lineage")
    resumed = "a new session from its base" if lin is None else (
        "a continuation of the session whose head is %s... (its first %d events, from its %s)" % (lin["parent_head"][:12], lin["parent_events"], lin["source"]))
    reading = ("LIVE-SESSION-0 on host %s: a live session saved by the shell and verified there before it counted as saved "
               "(%d events: %d moves, %d edits%s; ended by %s), %s; its seal, base, fold%s check here, the workshop's own "
               "sessionwalk verifies the saved file itself (head %s...), and this checkout's renderer identity is %s the "
               "one it was made with." % (host, len(d["log"]), d["moves"], d["edits"],
                                         "" if not looks else ", %d looks, %d frames at free headings recomputed by the reference before the save"
                                         % (looks, (live.get("certified") or {}).get("frames", 0)),
                                         live.get("ended"), resumed,
                                         "" if lin is None else " and lineage", d["head"][:12],
                                         "the same as" if same else "NOT the same as (replay, not identity, decides)"))
    prov = {"tool": "shell livesession-window (shell/livesession.rs; the LIVE-SESSION-0 section appended to shell/win32.rs) "
                    "+ verify/livesession.py", "host": host,
            "saved_sha256": hashlib.sha256(raw).hexdigest(), "run_id": live.get("run_id"),
            "renderer_now": now, "workshop": workshop, "python": platform.python_version(), "os": platform.system(),
            "preregistered": {"rung": "LIVE-SESSION-0", "chain_hash": reg["LIVE-SESSION-0"]["chain_hash"]},
            "loop": {"rung": "LIVE-INPUT-0", "chain_hash": reg["LIVE-INPUT-0"]["chain_hash"]}}
    data = dict(d)
    data["live"] = live
    return envelope.seal(
        "verdandi-session-walk", 1, "measured", prov,
        {"certifies": "a live session walked on host %s and saved by the shell: the session-walk over the frozen base "
                      "(W %s... M %s...) from %s, which replays in log order to head %s" % (host, d["base"]["W"][:12], d["base"]["M"][:12],
                                                                                      d["base"]["camera"], d["head"]),
         "host": host, "head": d["head"], "final_camera": d["final_camera"]},
        ["any timing or latency: the session carries no time",
         "that the renderer identity decides compatibility: it names sources, replay decides",
         "that the focus observation explains anything: it is recorded, never ruled on",
         "a second authority: the shell's session is the replay of this log, which the workshop verifies",
         "durability beyond the file system's promise, or on any other host"],
        data, reading)


def main() -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--session", required=True)
    a = ap.parse_args()
    try:
        reg = registry()
        with open(a.session, "rb") as fh:
            raw = fh.read()
        check_saved(raw)
        workshop = workshop_verify(a.session)
        rec = seal_livesession(raw, reg, a.host, workshop)
    except (Refuse, OSError, ValueError, KeyError) as e:
        print("REFUSE: %s" % e)
        return 2
    out = write_record("livesession-%s-%s.json" % (a.host, rec["data"]["head"][:12]), rec)
    print("[livesession] %s -> %s  (cites LIVE-SESSION-0 %s)" % (rec["reading"], os.path.relpath(out), reg["LIVE-SESSION-0"]["chain_hash"][:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
