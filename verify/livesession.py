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

ADMIT-0: an edit admitted through the shell's admission seam carries an envelope beside it. This sealer never reads the
proposal language. It takes the envelope as typed values of the saved form and checks them against the chain: eight
text members, the language's name, 64 lower-case hex where an id, a digest, an identity or a head goes, the grant's
line, on an edit, naming the head before the event and the head after it, and no proposal id twice. The digest, the
id, the identities and the grant are the admitting shell's record: nothing in a saved file can check them.

DESIGN-EVENT-0: a batch admits N operations as N ordinary edits. Each carries the batch's envelope: ADMIT-0's eight
members and two more, its place and the batch's count. This sealer does not read the batch language either. Every
envelope still stands alone against the chain, as above; and a batch stands whole or the session is refused: its events
one after another with nothing between them, place 1 to place count in order, agreeing in language, proposal id,
digest, identities, grant and count. An envelope that is not exactly ten members naming the batch language is judged
as ADMIT-0 judges any envelope.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import platform
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envelope  # noqa: E402
import savedform  # noqa: E402
from diagcommon import Refuse, registry, write_record  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = ("kernel/mantle.rs", "kernel/formats.rs", "kernel/fast.rs", "kernel/hud.rs", "shell/present.rs")
# SIM-TICK-0: the sources that decide a frame at a free heading (the shell's BEARING_SOURCES, in its order)
BEARING_SOURCES = ("kernel/vocab.rs", "oracle/bearing_octant.txt", "kernel/bearing.rs", "kernel/bearingfast.rs")
TAGS = {"move": "M", "edit": "E", "look": "K", "sensitivity": "S"}
SEAL_KEY = b'\n "seal": "'
MAGIC = b"VRDNSW1"
# ADMIT-0: the envelope beside an admitted edit — its members, and the alphabets of their values
ENVELOPE_KEYS = ("language", "proposal", "digest", "renderer", "bearing", "parent", "head", "grant")
ENVELOPE_LANGUAGE = "VRDNP1"
# DESIGN-EVENT-0: a batch's envelope — ADMIT-0's eight members and two more, its place and the batch's count
BATCH_KEYS = ENVELOPE_KEYS + ("place", "count")
BATCH_LANGUAGE = "VRDNP2"
BATCH_SHARED = ("language", "proposal", "digest", "renderer", "bearing", "grant", "count")
COUNT = re.compile(r"[1-9][0-9]{0,3}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
GRANT_LINE = re.compile(r"[a-z0-9=,\- ]{1,96}\Z")


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


def batch_place(a, k: int):
    """DESIGN-EVENT-0: the place and count of a batch's envelope — exactly ten members naming the batch language — or
    None for every other envelope, which is then judged as ADMIT-0 judges it."""
    if not isinstance(a, dict) or len(a) != len(BATCH_KEYS) or a.get("language") != BATCH_LANGUAGE:
        return None
    if any(not isinstance(a.get(x), str) for x in BATCH_KEYS):
        raise Refuse("event %d: a batch's envelope is not its ten text members" % k)
    if not COUNT.match(a["place"]) or not COUNT.match(a["count"]) or not 1 <= int(a["place"]) <= int(a["count"]) <= 4096:
        raise Refuse("event %d: a batch envelope's place and count are not decimals with 1 <= place <= count <= 4096" % k)
    return int(a["place"]), int(a["count"])


def check_batches(log: list) -> int:
    """DESIGN-EVENT-0: a batch is whole or the session is refused — its events one after another with nothing between
    them, place 1 to place count in order, agreeing in what the batch shares. Returns how many batches the log holds."""
    batches, first, nxt = 0, None, 0
    for k, item in enumerate(log):
        a = item.get("admit")
        place = batch_place(a, k) if a is not None else None
        if first is None:
            if place is None:
                continue
            if place[0] != 1:
                raise Refuse("event %d: a batch's envelope does not begin at place 1" % k)
            batches += 1
            first, nxt = (a, 2) if place[1] > 1 else (None, 0)
            continue
        if place is None:
            raise Refuse("event %d: a batch's envelope is missing: an event that is not of the batch stands inside it" % k)
        if place[0] != nxt:
            raise Refuse("event %d: a batch's envelope is out of place: its places are not in order" % k)
        if any(a[x] != first[x] for x in BATCH_SHARED):
            raise Refuse("event %d: a batch's envelope does not agree with the batch in what it shares" % k)
        first, nxt = (first, nxt + 1) if nxt < place[1] else (None, 0)
    if first is not None:
        raise Refuse("event %d: a batch's envelope is missing: the log ends inside the batch" % len(log))
    return batches


def check_envelopes(log: list, hs: list) -> int:
    """ADMIT-0: every envelope in the log against the chain's heads; returns how many events were admitted."""
    seen = set()
    for k, item in enumerate(log):
        a = item.get("admit")
        if a is None:
            continue
        place = batch_place(a, k)   # DESIGN-EVENT-0: a batch's envelope has ten members and its own language
        if place is None and (not isinstance(a, dict) or len(a) != len(ENVELOPE_KEYS) or any(not isinstance(a.get(x), str) for x in ENVELOPE_KEYS)):
            raise Refuse("event %d: an envelope is not its eight text members" % k)
        if place is None and a["language"] != ENVELOPE_LANGUAGE:
            raise Refuse("event %d: an envelope's language is not VRDNP1" % k)
        if any(not HEX64.match(a[x]) for x in ("proposal", "digest", "renderer", "bearing", "parent", "head")):
            raise Refuse("event %d: an envelope's id, digest, identity or head is not 64 lower-case hex" % k)
        if not GRANT_LINE.match(a["grant"]):
            raise Refuse("event %d: an envelope's grant is not a grant's line" % k)
        if item.get("kind") != "edit":
            raise Refuse("event %d: its envelope is not on an edit" % k)
        if a["parent"] != hs[k]:
            raise Refuse("event %d: its envelope's parent is not the head before the event" % k)
        if a["head"] != hs[k + 1]:
            raise Refuse("event %d: its envelope's head is not the head after the event" % k)
        if (place is None or place[0] == 1) and a["proposal"] in seen:
            raise Refuse("event %d: its envelope's proposal id was already admitted" % k)
        seen.add(a["proposal"])
    check_batches(log)   # DESIGN-EVENT-0: after each envelope stands alone, the batches stand whole
    return len(seen)


def check_saved(raw: bytes, root: str = ROOT) -> dict:
    """The saved session's own integrity, without rendering: the seal, the shape, the base, the fold, the lineage."""
    if not seal_ok(raw):
        raise Refuse("the saved session's seal does not match its bytes")
    try:
        doc = savedform.read_document(raw)       # READER-COURT-0: the strict reader, never the json module
    except savedform.Refused as r:
        raise Refuse("the saved session is not in the saved form: %s" % r.line())
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
    check_envelopes(d["log"], hs)   # ADMIT-0: an envelope stands against the chain or the session is refused
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
    # MOUSE-LOOK-0: a session whose live block carries the look loop's counts ran under a tick source (shell look-window,
    # or look-selftest on the mock); it is the same saved form, and this entry is cited beside the others. The focus and
    # capture observation is not read here: it is recorded, never ruled on
    mouse = live.get("look")
    # ADMIT-0: the edits that came through the admission seam, counted from their envelopes (already checked against
    # the chain by check_saved); a session with none reads, cites and seals exactly as before
    admitted = sum(1 for x in d["log"] if x.get("admit") is not None)
    by_admission = live.get("ended") == "admission"
    # DESIGN-EVENT-0: the edits a batch admitted, counted from their ten-member envelopes, and the batches they make
    # (already held whole by check_saved); a session with none reads, cites and seals exactly as before
    batched = sum(1 for x in d["log"] if x.get("admit") is not None and len(x["admit"]) == len(BATCH_KEYS))
    batches = sum(1 for x in d["log"] if x.get("admit") is not None and len(x["admit"]) == len(BATCH_KEYS) and x["admit"]["place"] == "1")
    single = admitted - batched
    by_batch = by_admission and batched > 0 and d["log"][-1].get("admit") is not None and len(d["log"][-1]["admit"]) == len(BATCH_KEYS)
    lin = live.get("lineage")
    resumed = "a new session from its base" if lin is None else (
        "a continuation of the session whose head is %s... (its first %d events, from its %s)" % (lin["parent_head"][:12], lin["parent_events"], lin["source"]))
    reading = ("LIVE-SESSION-0 on host %s: a live session saved by the shell and verified there before it counted as saved "
               "(%d events: %d moves, %d edits%s; ended by %s), %s; its seal, base, fold%s check here, the workshop's own "
               "sessionwalk verifies the saved file itself (head %s...), and this checkout's renderer identity is %s the "
               "one it was made with." % (host, len(d["log"]), d["moves"], d["edits"],
                                         ("" if not looks else ", %d looks, %d frames at free headings recomputed by the reference before the save"
                                          % (looks, (live.get("certified") or {}).get("frames", 0)))
                                         + ("" if not single else ", %d of the edits admitted through ADMIT-0's seam from a proposal in "
                                            "VRDNP1, each envelope naming the chain's own heads around its event" % single)
                                         + ("" if not batched else ", %d of the edits admitted through DESIGN-EVENT-0's seam in %d batch%s, each "
                                            "batch whole and in order, each envelope naming the chain's own heads around its event"
                                            % (batched, batches, "" if batches == 1 else "es")),
                                         # MOUSE-LOOK-0a: said as what it was — a run under the tick source — and never
                                         # as having looked when the session holds no look
                                         live.get("ended") if mouse is None else "%s; run under MOUSE-LOOK-0's tick source at 64 Hz, %s (%s)" % (
                                             live.get("ended"), ("with %d looks" % looks) if looks else "holding no look",
                                             ", ".join("%s %s" % (k, mouse[k]) for k in sorted(mouse) if k != "rung")),
                                         resumed,
                                         "" if lin is None else " and lineage", d["head"][:12],
                                         "the same as" if same else "NOT the same as (replay, not identity, decides)"))
    prov = {"tool": ("shell design (shell/designevent.rs: the recognizer and the checks; shell/livesession.rs: the journal and the seal) "
                     "+ verify/livesession.py") if by_batch else
                    ("shell admit (shell/admit.rs: the recognizer and the checks; shell/livesession.rs: the journal and the seal) "
                     "+ verify/livesession.py") if by_admission else
                    ("shell livesession-window (shell/livesession.rs; the LIVE-SESSION-0 section appended to shell/win32.rs) "
                     "+ verify/livesession.py") if mouse is None else
                    ("shell look-window (shell/livesession.rs's go_look over shell/liveinput.rs under shell/mouselook.rs's tick "
                     "source; the MOUSE-LOOK-0 section appended to shell/win32.rs) + verify/livesession.py"), "host": host,
            "saved_sha256": hashlib.sha256(raw).hexdigest(), "run_id": live.get("run_id"),
            "renderer_now": now, "workshop": workshop, "python": platform.python_version(), "os": platform.system(),
            "preregistered": {"rung": "LIVE-SESSION-0", "chain_hash": reg["LIVE-SESSION-0"]["chain_hash"]},
            "loop": {"rung": "LIVE-INPUT-0", "chain_hash": reg["LIVE-INPUT-0"]["chain_hash"]}}
    if mouse is not None:
        prov["look"] = {"rung": "MOUSE-LOOK-0", "chain_hash": reg["MOUSE-LOOK-0"]["chain_hash"]}
        prov["ticks"] = {"rung": "SIM-TICK-0", "chain_hash": reg["SIM-TICK-0"]["chain_hash"]}
        prov["configuration"] = {"rung": "SIM-TICK-0a", "chain_hash": reg["SIM-TICK-0a"]["chain_hash"]}
    if single:
        prov["admission"] = {"rung": "ADMIT-0", "chain_hash": reg["ADMIT-0"]["chain_hash"]}
    if batched:
        prov["batches"] = {"rung": "DESIGN-EVENT-0", "chain_hash": reg["DESIGN-EVENT-0"]["chain_hash"], "batches": batches, "events": batched}
    data = dict(d)
    data["live"] = live
    return envelope.seal(
        "verdandi-session-walk", 1, "measured", prov,
        {"certifies": "a live session walked on host %s and saved by the shell: the session-walk over the frozen base "
                      "(W %s... M %s...) from %s, which replays in log order to head %s" % (host, d["base"]["W"][:12], d["base"]["M"][:12],
                                                                                      d["base"]["camera"], d["head"]),
         "host": host, "head": d["head"], "final_camera": d["final_camera"]},
        ["any timing or latency: the session carries no time" if mouse is None else
         "any latency, frame rate or feel: the session carries tick indices, not times, and an input's tick is the tick it was drained in",
         "that the renderer identity decides compatibility: it names sources, replay decides",
         "that the focus observation explains anything: it is recorded, never ruled on",
         "a second authority: the shell's session is the replay of this log, which the workshop verifies",
         "durability beyond the file system's promise, or on any other host"] + ([] if not admitted else [
             "that an envelope's digest, proposal id, identities or grant can be checked from this file: they are the "
             "admitting shell's record, the seal is a hash and not a signature, and the proposal's bytes are not kept",
             "that a model wrote the proposal, or that one could write a proposal worth admitting"]),
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
    cites = "LIVE-SESSION-0 %s" % reg["LIVE-SESSION-0"]["chain_hash"][:8]
    if "look" in rec["provenance"]:
        cites += ", MOUSE-LOOK-0 %s" % reg["MOUSE-LOOK-0"]["chain_hash"][:8]
    if "admission" in rec["provenance"]:
        cites += ", ADMIT-0 %s" % reg["ADMIT-0"]["chain_hash"][:8]
    print("[livesession] %s -> %s  (cites %s)" % (rec["reading"], os.path.relpath(out), cites))
    return 0


if __name__ == "__main__":
    sys.exit(main())
