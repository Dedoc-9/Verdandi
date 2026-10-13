# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/director.py — DIRECTOR-0: a prompt answered by candidates, each checked against the head it meets, admitted or
# refused by a person, and every step kept in an append-only ledger.
#
#   python art/director.py genesis  BRIEF                      start the brief's ledger at the current head
#   python art/director.py lens     BRIEF REGION               what a proposer reads: the region, its pieces, their materials
#   python art/director.py evaluate BRIEF FILE...              check candidate intents at the current head; a contact sheet
#   python art/director.py reevaluate BRIEF SEQ                check an earlier evaluation's intent again, at the current head
#   python art/director.py admit    BRIEF SEQ [--accept-leakage] [--chooser NAME] [--note TEXT]
#   python art/director.py refuse   BRIEF SEQ [--chooser NAME] [--note TEXT]
#   python art/director.py rebase   BRIEF --note TEXT          record a change made outside the loop (a hand edit, a new exporter)
#   python art/director.py approve  BRIEF VIEW IMAGE --config TEXT [--approver NAME] [--note TEXT]
#   python art/director.py verify   BRIEF                      the ledger's chain, replayed to the files as they stand
#   python art/director.py vectors                             the reference against the conformance vectors
#   python art/director.py selftest                            the vectors, and the whole lifecycle in a scratch copy
#   python art/director.py crashtest                           an admission killed at each of its writes, then recovered
#   python art/director.py racetest                            writers at once: the content lock, the fence, recovery that waits
#   (every command but vectors takes --root DIR: the tree whose brief and ledger it uses; the repository by default)
#
# Crash safety (B1, docs/STUDIO-CONTRACT.md): every command starts by recovering (recover()). An admission writes, in
# order: the old and the new bytes of every file it changes, into <ledger>.pending/, then that folder's manifest; the
# admit event (the commit: an admission counts once its line is flushed); the new files, each replaced whole; and last
# the manifest's removal. Recovery finds a manifest and either completes the admission (its event is in the ledger) or
# puts the old bytes back (it is not), so the files are the ledger's parent or its child, never between. A torn last
# line of the ledger is set aside first. What it does not claim: an operating-system crash or a power loss.
# One writer at a time (fix 1, the owner's ruling of 2026-10-13): every writer of a tree's ledgers, briefs, tags and
# maps holds the tree's content lock (art/director/durable.py), an admission from before its first write to after its
# last, and under it reads the head again (the fence); recovery takes the same lock and, while another writer holds
# it, refuses and changes nothing (LEDGER-BUSY), so it never undoes an admission that is alive.
# What each part proves, and what it does not:
#   scope   (art/director/scope.py) is pure: the same intent, head and scenes give the same verdict, byte for byte.
#   ledger  (art/director/ledger.py) proves recorded lineage: which text, at which head, with which verdict, chosen by
#           whom. It proves nothing about artistic quality, and an approved still records that a person accepted an
#           image under recorded conditions, not that another machine reproduces it.
#   layout  changes only through the design tool: the shell's compiler and admission make the layout, the graybox's
#           converter makes C from it. Nothing here writes a wall or a collision box.

import copy
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "director"))
import dress  # noqa: E402
import durable  # noqa: E402
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("art_check", os.path.join(HERE, "check.py"))
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)
import intent as canon  # noqa: E402
import scope as scopemod  # noqa: E402
import ledger as led  # noqa: E402

level = dress.level
# One export at a time in a process: Workspace.export points the module-global level.MAPS at the maps folder it reads
# (a candidate's layout is drawn over a folder of its own). Two threads exporting at once, one over the repository's
# maps and one over a candidate's, failed on the first export (the converter read the other folder's layout; MEASURED
# in the container, 2026-10-13); `racetest` keeps that case and its plant.
import threading  # noqa: E402
EXPORT_LOCK = threading.RLock()      # every swap of level.MAPS in this process holds it (art/play.py's compile_scene too)
NO_LOCK = __import__("contextlib").nullcontext()       # the race court's plant "no-export-lock" only


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ms(t0):
    return str(int(round((time.perf_counter() - t0) * 1000)))


class Workspace:
    """Where a brief's files live: the repository, or a scratch copy of it for the self-test."""

    def __init__(self, brief, root=REPO):
        self.brief, self.root = brief, root
        self.art = os.path.join(root, "art", "briefs", brief + ".art")
        self.ledger = os.path.join(root, "art", "ledger", brief + ".ledger")
        self.maps = os.path.join(root, "graybox", "maps")
        self.build = os.path.join(root, "art", "build", brief, "director")
        self.pending = self.ledger + ".pending"

    def text(self):
        return open(self.art, "rb").read().replace(b"\r\n", b"\n").decode("utf-8")

    def export(self, text=None, maps=None):
        """The scene of an art text over a maps folder, with the parts of its head and its checks' results."""
        text = self.text() if text is None else text
        maps = maps or self.maps
        A = dress.parse(text, self.brief + ".art")
        A["name"], A["sha256"] = self.brief, canon.sha256(text.encode("utf-8"))
        with EXPORT_LOCK if durable.PLANT != "no-export-lock" else NO_LOCK:   # level.MAPS is one global
            saved = level.MAPS
            level.MAPS = maps
            try:
                out = dress.export(A, maps_dir=maps)
                D = check.gcheck.source_rows(out["W"])
                res = check.verify(out, None, D=D)
            finally:
                level.MAPS = saved
        L = out["lineage"]
        parts = {"art_sha256": A["sha256"], "world_sha256": L["canonical_sha256"], "exporter_sha256": L["exporter_sha256"]}
        return out, parts, [{"name": c, "ok": bool(ok)} for c, ok, _d in res if c != "the lineage binds every input"]

    def design(self, out):
        src = out["W"]["source"]
        if "layout" not in src:
            return None, None
        name = src["layout"].rsplit(".", 1)[0] + ".design"
        return name, open(os.path.join(self.maps, name), "rb").read().replace(b"\r\n", b"\n").decode("utf-8")


# -------------------------------------------------------------------------------------------- revisions and layout
def apply_revision(text, lines):
    """The art text with the revision applied, and its exact inverse. '= stmt' replaces the statement with the same
    key, '+ stmt' appends one whose key is new, '- key' removes the statement with that key. Refuses (INTENT-APPLY)
    a line that names no statement, or a '+' whose key exists."""
    rows = text.split("\n")
    keyed = lambda ln: dress.statement_key(ln.split("#", 1)[0].split()) if ln.split("#", 1)[0].split() else None
    inverse = []
    for ln in lines:
        op, body = ln[0], ln[2:].strip()
        if op in "=+":
            code = body.split()
            if not code:
                raise canon.IntentError("INTENT-APPLY", "an empty statement")
            key = dress.statement_key(code)
        else:
            key = body
        at = [i for i, r in enumerate(rows) if keyed(r) == key]
        if op == "=":
            if len(at) != 1:
                raise canon.IntentError("INTENT-APPLY", "'= %s' names no statement of the brief" % key)
            old = rows[at[0]].split("#", 1)[0].strip()
            tail = ("  #" + rows[at[0]].split("#", 1)[1]) if "#" in rows[at[0]] else ""
            rows[at[0]] = " ".join(body.split()) + tail
            inverse.append("= " + old)
        elif op == "+":
            if at:
                raise canon.IntentError("INTENT-APPLY", "'+ %s': the brief already has a statement %r" % (body, key))
            while rows and rows[-1] == "":
                rows.pop()
            rows += [" ".join(body.split()), ""]
            inverse.append("- " + key)
        else:
            if len(at) != 1:
                raise canon.IntentError("INTENT-APPLY", "'- %s' names no statement of the brief" % key)
            inverse.append("+ " + rows[at[0]].split("#", 1)[0].strip())
            del rows[at[0]]
    return "\n".join(rows), list(reversed(inverse))


def compile_design(text):
    """A whole design text admitted through the design tool in a project of its own: (rows, parent, head)."""
    tool = os.path.join(REPO, "design", "design.py")
    tmp = tempfile.mkdtemp(prefix="director-design-")

    def run(*a, inp=None):
        cp = subprocess.run([sys.executable, tool] + list(a) + ["--project", tmp], input=inp, capture_output=True, cwd=REPO)
        return cp.returncode, cp.stdout.decode("utf-8", "replace"), cp.stderr.decode("utf-8", "replace")
    try:
        rc, o, e = run("new")
        if rc:
            raise RuntimeError("design.py new: " + (e or o).strip()[-200:])
        d = json.loads(run("inspect", "--json")[1])
        w, h, parent = d["world"]["width"], d["world"]["rows"], d["session"]["head"]
        for step in (("grant", "--allow", "open,close", "--cells", "0,0,%d,%d" % (w - 1, h - 1)), ("propose", "-"), ("preview",), ("admit",)):
            rc, o, e = run(*step, inp=text.encode("utf-8") if step[0] == "propose" else None)
            if rc:
                raise RuntimeError("design.py %s: %s" % (step[0], (e or o).strip()[-200:]))
        d = json.loads(run("inspect", "--json")[1])
        grid = [ln[5:] for ln in d["top_view"][2:]]
        cx, cz = (int(v) for v in d["world"]["camera"].split(",")[:2])
        grid[cz] = grid[cz][:cx] + "." + grid[cz][cx + 1:]
        return grid, parent, d["session"]["head"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def layout_bytes(design_name, design_text, rows, parent, head):
    hdr = ["; VERDANDI LAYOUT 0",
           "; the walls and floor of %s, compiled by the shell's compiler (shell design-compile) and admitted" % design_name,
           "; by its admission (shell design) through design/design.py, read back with `inspect --json`; written by",
           "; art/director.py when an intent's layout was admitted. '#' rock, '.' floor, '<' '>' stairs.",
           "; design   sha256 %s" % canon.sha256(design_text.encode("utf-8")),
           "; parent   %s" % parent, "; head     %s" % head, "; size     %d x %d" % (len(rows[0]), len(rows))]
    return ("\n".join(hdr + rows) + "\n").encode("utf-8")


def layout_label(it):
    """The comment an admitted layout carries in the design file: the same at evaluation, admission and replay."""
    return "DIRECTOR-0 intent %s: %s (candidate %s)" % (canon.sha256(canon.dumps(it))[:12], it["prompt"], it["candidate"])


def with_layout(ws, out, lines, label):
    """A scratch maps folder holding the design text with the intent's layout lines appended, compiled and written."""
    dname, dtext = ws.design(out)
    if dname is None:
        raise canon.IntentError("INTENT-LAYOUT", "this map's walls are not a design-tool layout")
    new = dtext.rstrip("\n") + "\n# %s\n" % label + "\n".join(lines) + "\n"
    rows, parent, head = compile_design(new)
    tmp = tempfile.mkdtemp(prefix="director-maps-")
    for f in os.listdir(ws.maps):
        if os.path.isfile(os.path.join(ws.maps, f)):
            shutil.copy(os.path.join(ws.maps, f), tmp)
    with open(os.path.join(tmp, dname), "wb") as fh:
        fh.write(new.encode("utf-8"))
    with open(os.path.join(tmp, out["W"]["source"]["layout"]), "wb") as fh:
        fh.write(layout_bytes(dname, new, rows, parent, head))
    return tmp, new, head


# -------------------------------------------------------------------------------------------- crash safety
PENDING = "DIRECTOR-PENDING"
TMP_NAME = __import__("re").compile(r"\..+\.[0-9]+\.tmp\Z")


def _abs(ws, rel):
    return os.path.join(ws.root, *rel.split("/"))


def recover(ws, wait=None):
    """Bring the brief's files and ledger to a state the ledger accounts for: a torn last line set aside; an admission
    left half done completed (its event is in the ledger) or undone (it is not). Returns what was done, as lines.

    Only under the content lock (the owner's ruling of 2026-10-13: "recover() refuses rather than clears"): a pending
    folder, a temporary or a torn line seen while the lock is held by this process is one whose writer is dead, since
    every writer holds the lock from before its first write to after its last. If another writer holds it for the whole
    wait, nothing is recovered or changed: LEDGER-BUSY. A lock is never taken from a holder that is alive."""
    if durable.PLANT == "recover-ignores-lock":
        return _recover(ws)
    try:
        with durable.locked(led.lock_path(ws.ledger), wait):
            return _recover(ws)
    except durable.Busy:
        raise led.LedgerError("LEDGER-BUSY: another writer holds this tree's content lock (%s), an admission in progress; "
                              "nothing was recovered or changed. Try again when it ends"
                              % os.path.relpath(led.lock_path(ws.ledger), ws.root))


def _recover(ws):
    done = []
    stale = 0                                    # the temporaries of writes that died before their rename (durable.write)
    for d in {os.path.dirname(ws.art), os.path.dirname(ws.ledger), ws.maps}:
        for f in (os.listdir(d) if os.path.isdir(d) else []):
            if TMP_NAME.match(f):
                os.remove(os.path.join(d, f))
                stale += 1
    if stale:
        done.append("RECOVERED %d temporary file%s of a write that did not finish, removed" % (stale, "" if stale == 1 else "s"))
    aside = led.set_aside_torn(ws.ledger)
    if aside:
        done.append("RECOVERED the ledger's torn last line, kept in %s" % os.path.relpath(aside, ws.root))
    if not os.path.isdir(ws.pending):
        return done
    mpath = os.path.join(ws.pending, "manifest.json")
    if not os.path.exists(mpath):
        durable.remove_tree(ws.pending)        # prepared no further than its files, or already finished: the files are the ledger's
        done.append("RECOVERED a pending folder without its manifest (an admission not yet prepared, or already finished); removed")
        return done
    m = canon.loads(open(mpath, "rb").read())
    if m.get("protocol") != PENDING:
        raise led.LedgerError("PENDING-UNKNOWN: %s is not a %s manifest; read it, then move it aside" % (mpath, PENDING))
    events, _l, _h = led.read(ws.ledger)
    i = int(m["ledger_seq"])
    committed = (i < len(events) and events[i]["kind"] == "admit" and events[i]["evaluation"] == m["evaluation"]
                 and events[i]["intent_sha256"] == m["intent_sha256"])
    side = "new" if committed else "old"
    todo = []
    for n, f in enumerate(m["files"]):
        target, want = _abs(ws, f["path"]), f[side + "_sha256"]
        if (canon.sha256(open(target, "rb").read()) if os.path.exists(target) else "") != want:
            data = open(os.path.join(ws.pending, "%s.%d" % (side, n)), "rb").read()
            if canon.sha256(data) != want:
                raise led.LedgerError("PENDING-DAMAGED: %s.%d is not the bytes its manifest names; nothing was changed by recovery" % (side, n))
            todo.append((n, target, data))
    for n, target, data in todo:                 # every file checked before any is written
        durable.write(target, data)
        durable.point("recover:file-%d" % n)
    _finish(ws)
    done.append("RECOVERED %s: the admission of evaluation #%s %s" % (
        "ledger #%s" % i if committed else "no admit event", m["evaluation"], "completed" if committed else "undone, the files as they were"))
    return done


def _finish(ws):
    os.remove(os.path.join(ws.pending, "manifest.json"))
    durable.point("pending:manifest-removed")
    durable.remove_tree(ws.pending)


MAP_LINE = re.compile(r"\s*map\s+(\S+)")


def briefs_on_map(ws, name):
    """The other briefs of this tree that play the map `name` (each brief's first `map` line, comments aside). A brief
    that cannot be read is counted among them: what it plays is not known, so nothing is assumed."""
    d, out = os.path.dirname(ws.art), []
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if not f.endswith(".art") or f == ws.brief + ".art":
            continue
        try:
            text = open(os.path.join(d, f), "rb").read().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            out.append(f[:-4] + " (unreadable)")
            continue
        for ln in text.splitlines():
            m = MAP_LINE.match(ln.split("#", 1)[0])
            if m:
                if m.group(1) == name:
                    out.append(f[:-4])
                break
    return out


def commit_admission(ws, evaluation, intent_sha256, files, fields):
    """Admit with crash safety: files is [(absolute path, new bytes)], fields the admit event's (with head_before, the
    head the caller checked). See recover().

    The fence (fix 1 of the owner's ruling of 2026-10-13; Kleppmann: the store checks the token at the write): the
    whole admission holds the content lock, and under it the head is computed again from the files and compared with
    head_before before anything is written — the caller's own check was made before the lock, and another admission
    may have landed between the two. Every caller is fenced here, whoever it is."""
    durable.point("admit:lock-wait")
    try:
        with durable.locked(led.lock_path(ws.ledger)):
            return _commit_locked(ws, evaluation, intent_sha256, files, fields)
    except durable.Busy:
        raise SystemExit("REFUSED (BUSY): another writer held this tree's content lock for the whole wait (%g s); nothing was "
                         "changed. Admit again when it ends" % durable.WAIT)


def _commit_locked(ws, evaluation, intent_sha256, files, fields):
    if os.path.exists(ws.pending):               # this process holds the lock: the folder's writer is dead
        for ln in _recover(ws):
            print(ln)
    out_now, cur, _c = ws.export()
    if durable.PLANT != "no-fence" and canon.head(cur) != fields["head_before"]:
        raise SystemExit("REFUSED (HEAD-MOVED): the head moved to %s while this admission waited for the lock (it was checked "
                         "against %s); nothing was changed. Re-evaluate it first" % (canon.head(cur)[:12], fields["head_before"][:12]))
    # fix 2 of the review of 2026-10-13: briefs share the graybox's maps, so a layout admitted in one world would change
    # every world that plays its map (write skew between worlds). Until each world has a map of its own (pinned
    # revisions, later), a layout change is refused while another brief plays the map; art changes are not affected
    if durable.PLANT != "no-shared-map" and any(os.path.dirname(os.path.abspath(f)) == os.path.abspath(ws.maps) for f, _b in files):
        others = briefs_on_map(ws, out_now["scene"]["map"])
        if others:
            raise SystemExit("REFUSED (SHARED-MAP): %s also play%s the map %s, so this layout change would change %s too; nothing was "
                             "changed. A layout is changed only in a world whose map no other world plays, until each world keeps a "
                             "map of its own (pinned revisions, to come); changes to the art are admitted as before" % (
                                 ", ".join(others), "s" if len(others) == 1 else "", out_now["scene"]["map"], "that world" if len(others) == 1 else "those worlds"))
    events, _l, _h = led.read(ws.ledger)
    os.makedirs(ws.pending)
    prepared = False
    try:
        entries = []
        for n, (target, new) in enumerate(files):
            old = open(target, "rb").read()
            durable.write(os.path.join(ws.pending, "old.%d" % n), old)
            durable.write(os.path.join(ws.pending, "new.%d" % n), new)
            entries.append({"path": os.path.relpath(target, ws.root).replace(os.sep, "/"), "old_sha256": canon.sha256(old), "new_sha256": canon.sha256(new)})
            durable.point("pending:file-%d" % n)
        durable.write(os.path.join(ws.pending, "manifest.json"), canon.dumps(
            {"protocol": PENDING, "version": "0", "ledger_seq": str(len(events)), "evaluation": evaluation,
             "intent_sha256": intent_sha256, "files": entries}))
        prepared = True
        durable.point("pending:manifest")
        a = led.append(ws.ledger, "admit", fields)
        for n, (target, new) in enumerate(files):
            durable.write(target, new)
            durable.point("install:file-%d" % n)
        _finish(ws)
        return a
    except BaseException:
        if not prepared:
            # nothing a recovery needs: the files and the ledger are untouched, so the folder goes (the owner's addition:
            # no pending folder left behind by a failure)
            durable.remove_tree(ws.pending)
        else:
            # prepared: the folder is this admission's redo and undo, never removed blindly. Finished now, under the
            # lock, as a recovery would: completed if the admit event is in the ledger, undone if it is not
            try:
                for ln in _recover(ws):
                    print(ln)
            except Exception:                    # noqa: BLE001 — left for the next recovery, which refuses what it cannot account for
                pass
        raise


# The self-tests' world (the owner's run of 2026-10-13: after he had admitted his own edits through the studio, the
# studio's self-test failed four rows and stopped in the references' self-test, every one of them reading his working
# brief and ledger): the plaza's brief and its layout as art/fixtures/selftest/ keeps them — the bytes committed when
# those self-tests were written — and a ledger started on them. Never the owner's working files, which are his world.
FIXTURE = os.path.join(HERE, "fixtures", "selftest")


def selftest_tree(root):
    """Lay a self-test's world under root: the graybox's own maps (nothing in art/ writes them), the fixture's brief,
    design and layout, and a ledger started at their head. Returns the brief's workspace."""
    os.makedirs(os.path.join(root, "art", "briefs"), exist_ok=True)
    os.makedirs(os.path.join(root, "graybox", "maps"), exist_ok=True)
    for f in os.listdir(os.path.join(REPO, "graybox", "maps")):
        if f.endswith(".gbx"):
            shutil.copy(os.path.join(REPO, "graybox", "maps", f), os.path.join(root, "graybox", "maps", f))
    for f, to in (("plaza-night.art", "art/briefs"), ("tactical.design", "graybox/maps"), ("tactical.layout", "graybox/maps")):
        shutil.copy(os.path.join(FIXTURE, f), os.path.join(root, *to.split("/"), f))
    ws = Workspace("plaza-night", root)
    cmd_genesis_quiet(ws)
    return ws


def say_recovered(ws):
    for ln in recover(ws):
        print(ln)


# -------------------------------------------------------------------------------------------- evaluation
def refused(it, current, code, detail):
    v = {"protocol": scopemod.PROTOCOL, "version": scopemod.VERSION, "verdict": "REFUSED", "codes": [code],
         "intent_sha256": canon.sha256(canon.dumps(it)), "written_against": canon.head(it["base"]), "checked_against": canon.head(current),
         "re_evaluated": canon.head(it["base"]) != canon.head(current), "declared": sorted(it["scope"]), "realized": [], "affected": [],
         "unclaimed": [], "phantom": [], "cells_changed": [], "materials_changed": [], "failed_checks": [], "detail": detail}
    return v


def evaluate_doc(ws, it, re_of="", on_candidate=None):
    """One intent at the current head: its verdict, the head after it, and the stage timings. on_candidate(out1, maps),
    if given, is called with the candidate's export and the maps folder it was made over, while that folder exists
    (art/play.py converts the candidate's map there to play it)."""
    t0 = time.perf_counter()
    timings = {}
    t = time.perf_counter()
    out0, cur, _c = ws.export()
    timings["base_export"] = ms(t)
    after = {"art_sha256": "", "world_sha256": "", "layout_head": ""}
    tmp = None
    try:
        if it["brief"] != ws.brief:
            return refused(it, cur, "INTENT-BRIEF", "the intent is for %r" % it["brief"]), after, timings, None, out0, None
        t = time.perf_counter()
        try:
            text1, _inv = apply_revision(ws.text(), it["revision"])
        except canon.IntentError as e:
            return refused(it, cur, e.code, str(e)), after, timings, None, out0, None
        maps = None
        if it["layout"]:
            try:
                maps, _new, head = with_layout(ws, out0, it["layout"], layout_label(it))
                tmp = maps
                after["layout_head"] = head
            except (RuntimeError, canon.IntentError) as e:
                return refused(it, cur, "LAYOUT-REFUSED", str(e)[:300]), after, timings, None, out0, None
        timings["apply"] = ms(t)
        t = time.perf_counter()
        try:
            out1, parts1, checks = ws.export(text1, maps)
        except (dress.ArtError, level.MapError) as e:
            return refused(it, cur, "ART-REFUSED", str(e)[:300]), after, timings, None, out0, None
        timings["candidate_export_and_checks"] = ms(t)
        if on_candidate is not None:
            on_candidate(out1, maps or ws.maps)
        t = time.perf_counter()
        verdict = scopemod.check_scope(it, out0["scene"], out1["scene"], cur, checks)
        timings["scope"] = ms(t)
        after.update({"art_sha256": parts1["art_sha256"], "world_sha256": parts1["world_sha256"]})
        return verdict, after, timings, out1, out0, text1
    finally:
        timings["total"] = ms(t0)
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


def cmd_evaluate(ws, files, quiet=False):
    events, _l, _h = led.read(ws.ledger)
    if not events:
        raise SystemExit("no ledger for %s: run genesis first" % ws.brief)
    rows, sheet = [], []
    for f in files:
        raw = open(f, "rb").read()
        try:
            it = canon.load_intent(raw)
        except canon.IntentError as e:
            ev = led.append(ws.ledger, "refuse_input", {"input_sha256": canon.sha256(raw), "file": os.path.basename(f), "code": e.code,
                                                        "detail": str(e)[:300], "observed": {"at": now()}})
            rows.append((os.path.basename(f), "-", "REFUSED", e.code, ev["seq"], {}))
            continue
        verdict, after, timings, out1, out0, _text1 = evaluate_doc(ws, it)
        ev = led.append(ws.ledger, "evaluate", {"intent": raw.decode("ascii"), "intent_sha256": canon.sha256(raw), "re_evaluation_of": "",
                                                "verdict": verdict, "after": after, "observed": {"at": now(), "ms": timings}})
        rows.append((os.path.basename(f), it["candidate"], verdict["verdict"], ",".join(verdict["codes"]) or "-", ev["seq"], timings))
        sheet.append((it, verdict, out0, out1, ev["seq"], timings))
    if not quiet:
        for r in rows:
            print("%-26s %-3s %-8s %-40s ledger #%s  %s ms" % (r[0], r[1], r[2], r[3][:40], r[4], r[5].get("total", "-")))
        if sheet:
            p = contact_sheet(ws, sheet)
            print("contact sheet: %s" % os.path.relpath(p, ws.root))
    return rows


def cmd_reevaluate(ws, seq):
    events, _l, _h = led.read(ws.ledger)
    ev = events[int(seq)]
    if ev["kind"] != "evaluate":
        raise SystemExit("#%s is not an evaluation" % seq)
    it = canon.load_intent(ev["intent"].encode("ascii"))
    verdict, after, timings, out1, out0, _t = evaluate_doc(ws, it)
    new = led.append(ws.ledger, "evaluate", {"intent": ev["intent"], "intent_sha256": ev["intent_sha256"], "re_evaluation_of": seq,
                                             "verdict": verdict, "after": after, "observed": {"at": now(), "ms": timings}})
    print("candidate %s re-evaluated at the current head: %s %s (ledger #%s; it was %s at #%s)" % (
        it["candidate"], verdict["verdict"], ",".join(verdict["codes"]) or "-", new["seq"], ev["verdict"]["verdict"], seq))
    if out0 is not None:
        print("contact sheet: %s" % os.path.relpath(contact_sheet(ws, [(it, verdict, out0, out1, new["seq"], timings)]), ws.root))
    return new


def current_parts(ws):
    _o, parts, _c = ws.export()
    return parts


def cmd_admit(ws, seq, accept_leakage=False, chooser="the owner", note=""):
    events, _l, _h = led.read(ws.ledger)
    ev = events[int(seq)]
    if ev["kind"] != "evaluate":
        raise SystemExit("REFUSED: #%s is not an evaluation" % seq)
    v = ev["verdict"]
    out0, cur, _c = ws.export()
    head = canon.head(cur)
    if v["checked_against"] != head:
        raise SystemExit("REFUSED (HEAD-MOVED): #%s was checked against %s; the head is now %s. Re-evaluate it first: "
                         "python art/director.py reevaluate %s %s" % (seq, v["checked_against"][:12], head[:12], ws.brief, seq))
    if v["verdict"] == "REFUSED":
        raise SystemExit("REFUSED: #%s's verdict is REFUSED (%s); a refused candidate is never admitted" % (seq, ",".join(v["codes"])))
    if v["verdict"] == "LEAKAGE" and not accept_leakage:
        raise SystemExit("REFUSED: #%s leaks (%s); admit it only with --accept-leakage, which the ledger records" % (seq, ", ".join(v["unclaimed"][:6])))
    it = canon.load_intent(ev["intent"].encode("ascii"))
    text1, inverse = apply_revision(ws.text(), it["revision"])
    files, maps = [], None
    try:
        if it["layout"]:
            dname, _d = ws.design(out0)
            maps, _new_design, _lhead = with_layout(ws, out0, it["layout"], layout_label(it))
            for f in (dname, out0["W"]["source"]["layout"]):
                files.append((os.path.join(ws.maps, f), open(os.path.join(maps, f), "rb").read()))
        # the head the files will have, computed before any of them is touched
        _o1, parts1, _c1 = ws.export(text1, maps)
    finally:
        if maps:
            shutil.rmtree(maps, ignore_errors=True)
    if parts1["art_sha256"] != ev["after"]["art_sha256"] or parts1["world_sha256"] != ev["after"]["world_sha256"]:
        raise SystemExit("the admitted files would not reach the head the evaluation predicted: stop and read the ledger")
    files.append((ws.art, text1.encode("utf-8")))
    files = [(f, b) for f, b in files if open(f, "rb").read() != b]
    a = commit_admission(ws, seq, ev["intent_sha256"], files, {
        "evaluation": seq, "intent_sha256": ev["intent_sha256"], "head_before": head, "head_after": canon.head(parts1),
        "parts_after": parts1, "accepted_leakage": bool(accept_leakage), "inverse": inverse,
        "design_lines": list(it["layout"]), "observed": {"at": now(), "chooser": chooser, "note": note}})
    print("ADMITTED candidate %s (#%s) at head %s -> %s (ledger #%s)" % (it["candidate"], seq, head[:12], canon.head(parts1)[:12], a["seq"]))
    return a


def cmd_refuse(ws, seq, chooser="the owner", note=""):
    events, _l, _h = led.read(ws.ledger)
    ev = events[int(seq)]
    if ev["kind"] != "evaluate":
        raise SystemExit("#%s is not an evaluation" % seq)
    r = led.append(ws.ledger, "refuse", {"evaluation": seq, "intent_sha256": ev["intent_sha256"], "observed": {"at": now(), "chooser": chooser, "note": note}})
    print("REFUSED by %s: #%s (ledger #%s)" % (chooser, seq, r["seq"]))
    return r


def cmd_genesis(ws):
    if os.path.exists(ws.ledger):
        raise SystemExit("%s exists: a ledger is started once" % os.path.relpath(ws.ledger, ws.root))
    out, parts, _c = ws.export()
    dname, dtext = ws.design(out)
    g = led.append(ws.ledger, "genesis", {"brief": ws.brief, "map": out["scene"]["map"], "parts": parts, "head": canon.head(parts),
                                          "art_text": ws.text(), "design_name": dname or "", "design_text": dtext or "",
                                          "observed": {"at": now()}})
    print("ledger started: %s at head %s" % (os.path.relpath(ws.ledger, ws.root), g["head"][:12]))
    return g


def cmd_rebase(ws, note):
    events, _l, _h = led.read(ws.ledger)
    state = replay(ws, events)
    out, parts, _c = ws.export()
    dname, dtext = ws.design(out)
    r = led.append(ws.ledger, "rebase", {"head_before": state["head"], "head_after": canon.head(parts), "parts_after": parts, "art_text": ws.text(),
                                         "design_text": dtext or "", "observed": {"at": now(), "note": note}})
    print("rebased: %s -> %s (ledger #%s)" % (state["head"][:12], r["head_after"][:12], r["seq"]))
    return r


def cmd_approve(ws, view, image, config, approver="the owner", note=""):
    out, parts, _c = ws.export()
    if view not in out["scene"]["views"]:
        raise SystemExit("no view %r in the scene" % view)
    a = led.append(ws.ledger, "approve", {"view": view, "image_sha256": hashlib.sha256(open(image, "rb").read()).hexdigest(),
                                          "render_config": config, "head": canon.head(parts),
                                          "observed": {"at": now(), "approver": approver, "note": note}})
    print("approved: view %s, image %s, at head %s (ledger #%s; provenance, not a reproducibility claim)" % (view, a["image_sha256"][:12], a["head"][:12], a["seq"]))
    return a


# -------------------------------------------------------------------------------------------- verification
def replay(ws, events):
    """The ledger replayed from its genesis: the art text, the design text and the head after the last event.
    Refuses (raising LedgerError) any event that does not follow from the ones before it."""
    E = led.LedgerError
    g = events[0]
    st = {"art": g["art_text"], "design": g["design_text"], "parts": dict(g["parts"]), "head": g["head"]}
    if canon.head(g["parts"]) != g["head"] or canon.sha256(g["art_text"].encode("utf-8")) != g["parts"]["art_sha256"]:
        raise E("LEDGER-GENESIS: the genesis's head is not its own text's")
    for ev in events[1:]:
        k = ev["kind"]
        if k == "evaluate":
            if canon.sha256(ev["intent"].encode("ascii")) != ev["intent_sha256"]:
                raise E("LEDGER-INTENT: #%s's intent is not the bytes it names" % ev["seq"])
            if ev["verdict"]["checked_against"] != st["head"]:
                raise E("LEDGER-HEAD: #%s was checked against %s, but the head was %s" % (ev["seq"], ev["verdict"]["checked_against"][:12], st["head"][:12]))
            if ev["re_evaluation_of"]:
                prior = events[int(ev["re_evaluation_of"])]
                if prior["kind"] != "evaluate" or prior["intent_sha256"] != ev["intent_sha256"]:
                    raise E("LEDGER-REEVAL: #%s re-evaluates #%s, which is not the same intent" % (ev["seq"], ev["re_evaluation_of"]))
        elif k == "admit":
            src = events[int(ev["evaluation"])]
            if src["kind"] != "evaluate" or src["intent_sha256"] != ev["intent_sha256"]:
                raise E("LEDGER-ADMIT: #%s admits #%s, which is not that evaluation" % (ev["seq"], ev["evaluation"]))
            if src["verdict"]["checked_against"] != st["head"] or ev["head_before"] != st["head"]:
                raise E("LEDGER-STALE: #%s admits an evaluation made at another head" % ev["seq"])
            if src["verdict"]["verdict"] == "REFUSED" or (src["verdict"]["verdict"] == "LEAKAGE" and not ev["accepted_leakage"]):
                raise E("LEDGER-VERDICT: #%s admits a %s candidate" % (ev["seq"], src["verdict"]["verdict"]))
            it = canon.load_intent(src["intent"].encode("ascii"))
            st["art"], _inv = apply_revision(st["art"], it["revision"])
            if canon.sha256(st["art"].encode("utf-8")) != src["after"]["art_sha256"] != "":
                raise E("LEDGER-REPLAY: #%s's text does not reach the art the evaluation recorded" % ev["seq"])
            if it["layout"]:
                st["design"] = st["design"].rstrip("\n") + "\n# %s\n" % layout_label(it) + "\n".join(it["layout"]) + "\n"
            if canon.head(ev["parts_after"]) != ev["head_after"] or ev["parts_after"]["art_sha256"] != canon.sha256(st["art"].encode("utf-8")):
                raise E("LEDGER-REPLAY: #%s's head after is not its own parts'" % ev["seq"])
            st["parts"], st["head"] = dict(ev["parts_after"]), ev["head_after"]
        elif k == "rebase":
            if ev["head_before"] != st["head"]:
                raise E("LEDGER-STALE: #%s rebases from another head" % ev["seq"])
            st["art"], st["design"] = ev["art_text"], ev["design_text"]
            st["parts"], st["head"] = dict(ev["parts_after"]), ev["head_after"]
        elif k == "refuse":
            if events[int(ev["evaluation"])]["kind"] != "evaluate":
                raise E("LEDGER-REFUSE: #%s refuses something that is not an evaluation" % ev["seq"])
        elif k == "approve":
            if ev["head"] != st["head"]:
                raise E("LEDGER-HEAD: #%s approves a still at another head" % ev["seq"])
    return st


def cmd_verify(ws, quiet=False):
    events, head = led.chain(ws.ledger)
    st = replay(ws, events)
    out, parts, _c = ws.export()
    dname, dtext = ws.design(out)
    if st["art"] != ws.text():
        raise led.LedgerError("UNLOGGED-CHANGE: the art file is not the text the ledger replays to; record it with rebase, or restore it")
    if (dtext or "") != st["design"]:
        raise led.LedgerError("UNLOGGED-CHANGE: %s is not the design text the ledger replays to" % dname)
    if canon.head(parts) != st["head"]:
        raise led.LedgerError("UNLOGGED-CHANGE: the head is %s, the ledger's %s (the world or the exporter changed outside the loop; record it with rebase)" % (canon.head(parts)[:12], st["head"][:12]))
    kinds = {}
    for e in events:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    if not quiet:
        print("LEDGER VERIFIED  %d events (%s), head %s; the files are the head %s" % (
            len(events), ", ".join("%s %d" % kv for kv in sorted(kinds.items())), head[:12], st["head"][:12]))
    return events, st


# -------------------------------------------------------------------------------------------- the lens
def cmd_lens(ws, region):
    out, parts, _c = ws.export()
    S = out["scene"]
    if region not in S["regions"]:
        raise SystemExit("no region %r; the brief's regions: %s" % (region, ", ".join(sorted(S["regions"]))))
    x0, z0, x1, z1 = S["regions"][region]
    g = S["grid"]
    w, h, wall = g["w"], g["h"], g["wall"]
    pieces = scopemod._pieces(S)
    print("LENS %s / %s  cells %d,%d to %d,%d  head %s" % (ws.brief, region, x0, z0, x1, z1, canon.head(parts)[:12]))
    print("  the grid, two cells around (x across, z down): '#' rock, '.' floor, a digit the top in half metres, '*' the region")
    xa, xb, za, zb = max(0, x0 - 2), min(w - 1, x1 + 2), max(0, z0 - 2), min(h - 1, z1 + 2)
    print("       " + "".join(str(x % 10) for x in range(xa, xb + 1)))
    for z in range(za, zb + 1):
        row = ""
        for x in range(xa, xb + 1):
            t = S["tops"][z * w + x]
            ch = "#" if t >= wall else ("." if t == 0 else str(min(9, int(round(t * 2)))))
            if x0 <= x <= x1 and z0 <= z <= z1 and ch == ".":
                ch = "*"
            row += ch
        print("  %3d  %s" % (z, row))
    here = sorted((p["address"], p) for p in pieces.values() if p["address"].startswith(region + "/"))
    print("  pieces in %s: %d" % (region, len(here)))
    kinds = {}
    for a, p in here:
        kinds.setdefault(a.split("/")[1], []).append((a, p))
    for k, lst in sorted(kinds.items()):
        mats = sorted({p["material"] for _a, p in lst if p["material"]})
        hs = [p["shape"]["box"][4] for _a, p in lst if p["shape"].get("box")]
        print("    %-7s %3d   %s/%s/*   material %s%s" % (k, len(lst), region, k, ", ".join(mats) or "-",
                                                         ("   top %.1f to %.1f m" % (min(hs), max(hs))) if hs else ""))
    used = sorted({p["material"] for _a, p in here if p["material"]})
    print("  their materials, and everything else that uses them (a change to one reaches all of these):")
    for m in used:
        others = sorted({p["address"].rsplit("/", 1)[0] + "/*" for p in pieces.values() if p["material"] == m and not p["address"].startswith(region + "/")})
        print("    material/%-16s %s   also: %s" % (m, scopemod.material_digest(S["materials"][m])[:12], ", ".join(others) or "nothing else"))
    reach = [S["reach"][z * w + x] for z in range(z0, z1 + 1) for x in range(x0, x1 + 1) if S["reach"][z * w + x] is not None]
    print("  dressing over this region must clear %.2f to %.2f m (the reach ceiling), or sit in rock, flat, or flush" % (min(reach), max(reach)))
    views = [n for n, v in S["views"].items() if x0 <= int(v["x"] // g["cell"]) <= x1 and z0 <= int(v["z"] // g["cell"]) <= z1]
    print("  views here: %s" % (", ".join(sorted(views)) or "none"))
    print("  head parts: art %s, world %s, exporter %s" % (parts["art_sha256"][:12], parts["world_sha256"][:12], parts["exporter_sha256"][:12]))


# -------------------------------------------------------------------------------------------- the contact sheet
def boxes_by_address(scene):
    out = {}
    pieces = scopemod._pieces(scene)
    for key, p in pieces.items():
        b = p["shape"].get("box")
        if b is None:
            L = p.get("light")
            if L:
                b = [L["pos"][0] - 0.3, 0, L["pos"][2] - 0.3, L["pos"][0] + 0.3, 0, L["pos"][2] + 0.3]
        if b:
            out[p["address"]] = b
    return out


def diff_svg(out1, out0, verdict):
    svg = dress.plan_svg(out1).rstrip()
    assert svg.endswith("</svg>")
    sc = 14 / out1["scene"]["grid"]["cell"]
    b1, b0 = boxes_by_address(out1["scene"]), boxes_by_address(out0["scene"])
    marks = []
    for a in verdict["realized"]:
        b = b1.get(a) or b0.get(a)
        if b:
            col = "#3ad16b" if a in b1 and a not in b0 else ("#ff4d4d" if a not in b1 else "#ffb020")
            marks.append((b, col, "none"))
    for a in verdict["affected"]:
        b = b1.get(a)
        if b:
            marks.append((b, "#4da6ff", "3,2"))
    for a in verdict["unclaimed"]:
        b = b1.get(a) or b0.get(a)
        if b:
            marks.append((b, "#ff2bd6", "1,1"))
    for c in verdict["cells_changed"]:
        x, z = (int(v) for v in c.split(","))
        cell = out1["scene"]["grid"]["cell"]
        marks.append(([x * cell, 0, z * cell, (x + 1) * cell, 0, (z + 1) * cell], "#ffffff", "2,2"))
    rects = "".join('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" stroke="%s" stroke-width="1.6" stroke-dasharray="%s"/>'
                    % (b[0] * sc, b[2] * sc, max(2, (b[3] - b[0]) * sc), max(2, (b[5] - b[2]) * sc), col, dash) for b, col, dash in marks)
    return svg[:-len("</svg>")] + rects + "</svg>"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def contact_sheet(ws, items):
    os.makedirs(ws.build, exist_ok=True)
    base_out = items[0][2]
    colour = {"CLEAN": "#2e9d5b", "LEAKAGE": "#c98a12", "REFUSED": "#c23b3b"}
    cards = []
    for it, v, out0, out1, seq, timings in items:
        lists = "".join("<p><b>%s</b> %s</p>" % (k, esc(", ".join(v[k][:14]) + (" … +%d" % (len(v[k]) - 14) if len(v[k]) > 14 else "")) if v[k] else "—")
                        for k in ("declared", "realized", "affected", "unclaimed", "phantom", "cells_changed", "failed_checks"))
        pic = diff_svg(out1, out0, v) if out1 is not None else "<p class=none>no scene: refused before export</p>"
        cards.append('<section><h2>%s · <span style="background:%s">%s</span></h2><p class=r>%s</p><p class=c>%s</p>%s<div class=pic>%s</div>'
                     '<p class=t>ledger #%s · intent %s · checked against %s%s · %s ms</p></section>' % (
                         esc(it["candidate"]), colour[v["verdict"]], v["verdict"], esc(it["rationale"]), esc(" ".join(v["codes"]) or "no codes"),
                         lists, pic, seq, v["intent_sha256"][:12], v["checked_against"][:12], " (re-evaluated)" if v["re_evaluated"] else "", timings.get("total", "-")))
    html = """<!doctype html><meta charset=utf-8><title>DIRECTOR-0 contact sheet</title>
<style>body{background:#0d1014;color:#d8dee4;font:13px/1.45 system-ui,sans-serif;margin:16px}h1{font-size:18px}h2{font-size:15px;margin:0 0 4px}
h2 span{color:#fff;padding:1px 6px;border-radius:3px;font-size:12px}section{border:1px solid #2a3139;border-radius:6px;padding:10px;margin:0 0 14px}
p{margin:2px 0}.r{color:#fff}.c{color:#9aa7b4;font-family:monospace}.t{color:#7f8a95;font-size:11px}.pic svg{max-width:100%%;height:auto}
.key span{display:inline-block;margin-right:12px}</style>
<h1>DIRECTOR-0 · %s · “%s”</h1>
<p class=key><span style=color:#ffb020>▭ modified</span><span style=color:#3ad16b>▭ added</span><span style=color:#ff4d4d>▭ removed</span>
<span style=color:#4da6ff>⋯ affected through a material</span><span style=color:#ff2bd6>⋯ unclaimed</span><span>⋯ white: a cell the layout changed</span></p>
<p class=t>Plan views, not renders. A rendered still from Unreal is PROVISIONAL_PREVIEW: a person judges it; nothing here hashes pixels as truth.</p>
<section><h2>before</h2><div class=pic>%s</div></section>%s""" % (esc(ws.brief), esc(items[0][0]["prompt"]), dress.plan_svg(base_out), "".join(cards))
    p = os.path.join(ws.build, "index.html")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    return p


# -------------------------------------------------------------------------------------------- vectors and self-test
def cmd_vectors(path=None, quiet=False):
    path = path or os.path.join(HERE, "director", "vectors.json")
    V = json.load(open(path, encoding="utf-8"))
    bad, n = [], 0

    def judge(name, ok):
        nonlocal n
        n += 1
        if not ok:
            bad.append(name)
    for c in V["dumps"]:
        try:
            b = canon.dumps(c["value"])
            judge("dumps: " + c["name"], c["expect"]["ok"] and b.hex() == c["expect"]["hex"] and canon.sha256(b) == c["expect"]["sha256"])
        except canon.IntentError as e:
            judge("dumps: " + c["name"], not c["expect"]["ok"] and e.code == c["expect"]["code"])
    for c in V["loads"]:
        try:
            val = canon.loads(bytes.fromhex(c["hex"]))
            judge("loads: " + c["name"], c["expect"]["ok"] and val == c["expect"]["value"])
        except canon.IntentError as e:
            judge("loads: " + c["name"], not c["expect"]["ok"] and e.code == c["expect"]["code"])
    for c in V["intents"]:
        b = bytes.fromhex(c["hex"])
        try:
            canon.load_intent(b)
            judge("intent: " + c["name"], c["expect"]["ok"] and canon.sha256(b) == c["expect"]["sha256"])
        except canon.IntentError as e:
            judge("intent: " + c["name"], not c["expect"]["ok"] and e.code == c["expect"]["code"])
    for c in V["heads"]:
        judge("head", canon.head(c["parts"]) == c["expect"])
    for c in V["materials"]:
        judge("material", canon.dumps(scopemod.material_record(c["material"])).hex() == c["expect"]["record_hex"] and scopemod.material_digest(c["material"]) == c["expect"]["digest"])
    for c in V["patterns"]:
        judge("pattern %s ~ %s" % (c["pattern"], c["address"]), scopemod.match(c["pattern"], c["address"]) == c["expect"])
    for c in V["scope"]:
        v = scopemod.check_scope(c["intent"], c["base"], c["candidate"], c["current"], c["checks"])
        b = canon.dumps(v)
        judge("scope: " + c["name"], v == c["expect"]["verdict"] and b.hex() == c["expect"]["hex"] and canon.sha256(b) == c["expect"]["sha256"])
    if not quiet:
        for b in bad:
            print("FAIL vector: " + b)
        print("VECTORS %d / %d reproduced by the Python reference (verdicts and canonical bytes)" % (n - len(bad), n))
    return n, bad


def cmd_selftest():
    n, bad = cmd_vectors(quiet=True)
    results = [("the conformance vectors, reproduced by the reference (%d)" % n, not bad, ", ".join(bad[:3]))]
    tmp = tempfile.mkdtemp(prefix="director-selftest-")
    try:
        for sub in ("art/rounds", "graybox/maps"):         # the checkout's briefs are not the test's: the round's base alone
            shutil.copytree(os.path.join(REPO, sub), os.path.join(tmp, sub))
        os.makedirs(os.path.join(tmp, "art", "briefs"))
        ws = Workspace("plaza-night", tmp)
        rnd = os.path.join(tmp, "art", "rounds", "plaza-imposing")
        # The fixture is the head the round was written against, kept in the round's base/, never the live brief:
        # once a candidate is admitted for real the live brief has moved on, and A's '+ material' no longer applies.
        for f, to in (("plaza-night.art", "art/briefs"), ("tactical.design", "graybox/maps"), ("tactical.layout", "graybox/maps")):
            shutil.copy(os.path.join(rnd, "base", f), os.path.join(tmp, to, f))
        # The files are the round's; the exporter is today's (it is the program under test, and a new one moves every
        # head), so the fixture is held to the art and the world the round was written against, not to the exporter.
        base = canon.load_intent(open(os.path.join(rnd, "A.intent"), "rb").read())["base"]
        now = current_parts(ws)
        same = now["art_sha256"] == base["art_sha256"] and now["world_sha256"] == base["world_sha256"]
        results.append(("the scratch copy holds the art and the world the round was written against (%s, %s)" % (base["art_sha256"][:12], base["world_sha256"][:12]),
                        same, "art %s, world %s" % (now["art_sha256"][:12], now["world_sha256"][:12])))
        files = sorted(os.path.join(rnd, f) for f in os.listdir(rnd) if f.endswith(".intent"))
        cmd_genesis_quiet(ws)
        rows = cmd_evaluate(ws, files, quiet=True)
        got = {r[1] if r[1] != "-" else r[0]: (r[2], r[3], r[4]) for r in rows}
        want = {"A": "CLEAN", "B": "CLEAN", "C": "CLEAN", "D": "LEAKAGE", "E": "REFUSED", "F": "REFUSED"}
        for c, w in want.items():
            results.append(("candidate %s evaluates %s at the first head" % (c, w), got.get(c, ("?",))[0] == w, "%s %s" % got.get(c, ("?", "?"))[:2]))
        for f, code in (("G-unknown-version.intent", "INTENT-VERSION"), ("H-malformed.intent", "INTENT-NUMBER")):
            results.append(("%s is refused on input (%s)" % (f, code), got.get(f, ("?", "?"))[:2] == ("REFUSED", code), "%s %s" % got.get(f, ("?", "?"))[:2]))
        seqs = {k: v[2] for k, v in got.items()}
        # admission rules
        for label, s, kw, code in (("a REFUSED candidate is never admitted", seqs["E"], {}, "REFUSED"),
                                   ("a LEAKAGE candidate is not admitted without --accept-leakage", seqs["D"], {}, "leaks")):
            try:
                cmd_admit_quiet(ws, s, **kw)
                results.append((label, False, "it was admitted"))
            except SystemExit as e:
                results.append((label, code in str(e), str(e)[:80]))
        cmd_admit_quiet(ws, seqs["A"], chooser="selftest")
        try:
            cmd_admit_quiet(ws, seqs["C"], chooser="selftest")
            results.append(("a candidate checked at the old head is not admitted at the new one", False, "it was admitted"))
        except SystemExit as e:
            results.append(("a candidate checked at the old head is not admitted at the new one", "HEAD-MOVED" in str(e), str(e)[:80]))
        before = canon.dumps(led.read(ws.ledger)[0][int(seqs["C"])])
        rc = cmd_reevaluate_quiet(ws, seqs["C"])
        results.append(("C, re-evaluated at the new head, is a new event naming the old (CLEAN, HEAD-MOVED)",
                        rc["verdict"]["verdict"] == "CLEAN" and "HEAD-MOVED" in rc["verdict"]["codes"] and rc["re_evaluation_of"] == seqs["C"], ",".join(rc["verdict"]["codes"])))
        events, _l, _h = led.read(ws.ledger)
        results.append(("the earlier evaluation of C is kept as it was, byte for byte", canon.dumps(events[int(seqs["C"])]) == before, ""))
        cmd_admit_quiet(ws, rc["seq"], chooser="selftest")
        cmd_refuse_quiet(ws, seqs["D"], chooser="selftest", note="it reaches the bases and every wall")
        rb = cmd_reevaluate_quiet(ws, seqs["B"])
        results.append(("B (a layout change), re-evaluated after A and C, is still CLEAN", rb["verdict"]["verdict"] == "CLEAN", ",".join(rb["verdict"]["codes"]) + " cells " + ",".join(rb["verdict"]["cells_changed"])))
        cmd_admit_quiet(ws, rb["seq"], chooser="selftest")
        try:
            cmd_verify(ws, quiet=True)
            results.append(("the ledger replays to the files: genesis, evaluations, re-evaluations, admissions, a refusal", True, ""))
        except led.LedgerError as e:
            results.append(("the ledger replays to the files", False, str(e)))
        # plants: each must be refused by verify
        for label, plant in (
                ("a hand edit of the art file, unlogged", lambda: open(ws.art, "ab").write(b"# a hand edit\n")),
                ("a ledger line changed after it was written", lambda: _tamper(ws.ledger)),
        ):
            saved_art, saved_led = open(ws.art, "rb").read(), open(ws.ledger, "rb").read()
            plant()
            try:
                cmd_verify(ws, quiet=True)
                results.append(("plant: %s is refused" % label, False, "verify passed"))
            except led.LedgerError as e:
                results.append(("plant: %s is refused" % label, True, str(e)[:90]))
            open(ws.art, "wb").write(saved_art)
            open(ws.ledger, "wb").write(saved_led)
        open(ws.art, "ab").write(b"# a hand edit, recorded\n")
        cmd_rebase_quiet(ws, "a hand edit")
        try:
            cmd_verify(ws, quiet=True)
            results.append(("a hand edit recorded with rebase verifies", True, ""))
        except led.LedgerError as e:
            results.append(("a hand edit recorded with rebase verifies", False, str(e)))

        # fix 2 of the review of 2026-10-13: a second world on the same map. Its head must not move when the first world
        # admits: a layout change is refused (SHARED-MAP), an art change admitted; the plant shows what the refusal prevents
        root2 = os.path.join(tmp, "shared")
        for sub in ("art/rounds", "graybox/maps"):
            shutil.copytree(os.path.join(REPO, sub), os.path.join(root2, sub))
        os.makedirs(os.path.join(root2, "art", "briefs"))
        rnd2 = os.path.join(root2, "art", "rounds", "plaza-imposing")
        for f, to in (("plaza-night.art", "art/briefs"), ("tactical.design", "graybox/maps"), ("tactical.layout", "graybox/maps")):
            shutil.copy(os.path.join(rnd2, "base", f), os.path.join(root2, to, f))
        shutil.copy(os.path.join(rnd2, "base", "plaza-night.art"), os.path.join(root2, "art", "briefs", "plaza-twin.art"))
        ws2, twin = Workspace("plaza-night", root2), Workspace("plaza-twin", root2)
        cmd_genesis_quiet(ws2)
        rows2 = cmd_evaluate(ws2, [os.path.join(rnd2, "A.intent"), os.path.join(rnd2, "B.intent")], quiet=True)
        s_a, s_b = rows2[0][4], rows2[1][4]
        twin0, mine0 = canon.head(current_parts(twin)), canon.head(current_parts(ws2))
        try:
            cmd_admit_quiet(ws2, s_b, chooser="selftest")
            results.append(("a layout admission refused while another world plays its map (SHARED-MAP)", False, "it was admitted"))
        except SystemExit as e:
            results.append(("a layout admission refused while another world plays its map (SHARED-MAP); nothing changed in either world",
                            "SHARED-MAP" in str(e) and "plaza-twin" in str(e) and canon.head(current_parts(twin)) == twin0
                            and canon.head(current_parts(ws2)) == mine0, " ".join(str(e).split())[:110]))
        cmd_admit_quiet(ws2, s_a, chooser="selftest")
        mine1 = canon.head(current_parts(ws2))
        results.append(("an art admission in the same world: admitted, the other world's head as it was", mine1 != mine0
                        and canon.head(current_parts(twin)) == twin0, "this world %s -> %s; the other %s" % (mine0[:12], mine1[:12], twin0[:12])))
        durable.PLANT = "no-shared-map"
        try:
            rb2 = cmd_reevaluate_quiet(ws2, s_b)
            cmd_admit_quiet(ws2, rb2["seq"], chooser="selftest")
            twin1 = canon.head(current_parts(twin))
            results.append(("plant: no shared-map check — the layout admitted, and the other world's head moved with it", twin1 != twin0,
                            "the other world %s -> %s, though nothing was admitted there" % (twin0[:12], twin1[:12])))
        except SystemExit as e:
            results.append(("plant: no shared-map check — the layout admitted", False, str(e)[:110]))
        finally:
            durable.PLANT = os.environ.get("VERDANDI_PLANT", "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = 0
    for name, ok, d in results:
        print("%s %s%s" % ("PASS" if ok else "FAIL", name, (" — " + d) if d else ""))
        failed += 0 if ok else 1
    print("DIRECTOR SELFTEST %s" % ("PASSED" if not failed else "FAILED (%d)" % failed))
    return 0 if not failed else 1


def cmd_crashtest():
    """An admission killed at each of its writes (a real process, ended by os._exit at the point), then recovered by the
    next command: the files and the ledger are the parent or the child, never between, and the ledger verifies. And a
    recovery killed in the middle, recovered again. In a scratch copy, with the round's candidate B (a lamp and a
    layout: three files change)."""
    tmp = tempfile.mkdtemp(prefix="director-crashtest-")
    results = []
    me = os.path.abspath(__file__)
    env0 = {k: v for k, v in os.environ.items() if k != "VERDANDI_CRASH_AT"}

    def run(args, point=None):
        env = dict(env0, **({"VERDANDI_CRASH_AT": point} if point else {}))
        r = subprocess.run([sys.executable, me] + args + ["--root", tmp], capture_output=True, text=True, env=env, timeout=600)
        return r.returncode, r.stdout + r.stderr
    try:
        for sub in ("art/rounds", "graybox/maps"):         # the checkout's briefs are not the test's: the round's base alone
            shutil.copytree(os.path.join(REPO, sub), os.path.join(tmp, sub))
        os.makedirs(os.path.join(tmp, "art", "briefs"))
        ws = Workspace("plaza-night", tmp)
        rnd = os.path.join(tmp, "art", "rounds", "plaza-imposing")
        for f, to in (("plaza-night.art", "art/briefs"), ("tactical.design", "graybox/maps"), ("tactical.layout", "graybox/maps")):
            shutil.copy(os.path.join(rnd, "base", f), os.path.join(tmp, to, f))
        cmd_genesis_quiet(ws)
        rows = _quiet(cmd_evaluate, ws, [os.path.join(rnd, "B.intent")], quiet=True)
        seq = rows[0][4]
        ev = led.read(ws.ledger)[0][int(seq)]
        parent = current_parts(ws)
        child = {"art_sha256": ev["after"]["art_sha256"], "world_sha256": ev["after"]["world_sha256"]}
        watched = [ws.art, ws.ledger] + [os.path.join(ws.maps, f) for f in ("tactical.design", "tactical.layout")]
        snap = {f: open(f, "rb").read() for f in watched}

        def restore():
            durable.remove_tree(ws.pending)
            for f in os.listdir(os.path.dirname(ws.ledger)):
                if ".torn." in f:
                    os.remove(os.path.join(os.path.dirname(ws.ledger), f))
            for f, b in snap.items():
                open(f, "wb").write(b)

        def where():
            p = current_parts(ws)
            pair = {"art_sha256": p["art_sha256"], "world_sha256": p["world_sha256"]}
            kinds = [e["kind"] for e in led.read(ws.ledger)[0]]
            at = "parent" if pair == {k: parent[k] for k in pair} else "child" if pair == child else "between"
            return at, kinds[-1]
        rc, out = run(["admit", "plaza-night", seq, "--chooser", "crashtest"])
        changed = [f for f in watched if f != ws.ledger and open(f, "rb").read() != snap[f]]
        results.append(("an admission run to its end reaches the child and leaves no pending folder (%d files change)" % len(changed),
                        rc == 0 and where() == ("child", "admit") and not os.path.exists(ws.pending), out.strip()[-120:]))
        k = len(changed)
        points = (["pending:file-%d" % n for n in range(k)] + ["pending:manifest", "torn:admit", "ledger:admit"]
                  + ["install:file-%d" % n for n in range(k)] + ["pending:manifest-removed"])
        for point in points:
            restore()
            want = "parent" if point.startswith(("pending:file", "pending:manifest")) and point != "pending:manifest-removed" or point == "torn:admit" else "child"
            rc, out = run(["admit", "plaza-night", seq, "--chooser", "crashtest"], point)
            died = rc == durable.CRASH_EXIT
            rc2, out2 = run(["verify", "plaza-night"])
            at, last = where()
            ok = died and rc2 == 0 and "LEDGER VERIFIED" in out2 and at == want and last == ("admit" if want == "child" else "evaluate") \
                and not os.path.exists(ws.pending)
            detail = "died %s; then verify %d, the files at the %s, the ledger's last event %s; %s" % (
                "yes" if died else "NO (%d)" % rc, rc2, at, last, " ".join(ln for ln in out2.splitlines() if ln.startswith("RECOVERED"))[:150])
            if point == "torn:admit":
                kept = [f for f in os.listdir(os.path.dirname(ws.ledger)) if ".torn." in f]
                ok = ok and len(kept) == 1
                detail += "; the torn bytes kept in %s" % (kept[0] if kept else "nothing")
            if want == "parent" and ok:
                rc3, _o3 = run(["admit", "plaza-night", seq, "--chooser", "crashtest"])
                ok = rc3 == 0 and where() == ("child", "admit")
                detail += "; admitted again: %s" % ("the child" if ok else "FAILED")
            results.append(("killed at %s: recovered to the %s" % (point, want), ok, detail))
        # a recovery killed in the middle: the admission committed, nothing installed; the recovery dies after one file
        restore()
        run(["admit", "plaza-night", seq, "--chooser", "crashtest"], "ledger:admit")
        rc, _o = run(["verify", "plaza-night"], "recover:file-0")
        rc2, out2 = run(["verify", "plaza-night"])
        at, last = where()
        results.append(("a recovery killed after its first file, recovered again: the child", rc == durable.CRASH_EXIT and rc2 == 0 and at == "child"
                        and last == "admit" and not os.path.exists(ws.pending), "first recovery %d, second %d, the files at the %s" % (rc, rc2, at)))
        # a write killed before its rename leaves a temporary beside its target: the next start removes it
        restore()
        planted = os.path.join(os.path.dirname(ws.art), ".plaza-night.art.99999.tmp")
        open(planted, "wb").write(b"half of a write")
        rc, out = run(["verify", "plaza-night"])
        results.append(("a temporary left by a write killed before its rename is removed at the next start", rc == 0 and not os.path.exists(planted)
                        and "temporary file" in out, " ".join(ln for ln in out.splitlines() if ln.startswith("RECOVERED"))[:120]))
        # a pending folder whose bytes were changed is refused, not trusted
        restore()
        run(["admit", "plaza-night", seq, "--chooser", "crashtest"], "ledger:admit")
        with open(os.path.join(ws.pending, "new.0"), "ab") as fh:
            fh.write(b"# changed\n")
        rc, out = run(["verify", "plaza-night"])
        results.append(("a pending file changed after it was written is refused (PENDING-DAMAGED), nothing written", rc != 0 and "PENDING-DAMAGED" in out,
                        out.strip().splitlines()[-1][:120] if out.strip() else ""))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = 0
    for name, ok, d in results:
        print("%s %s%s" % ("PASS" if ok else "FAIL", name, (" — " + d) if d else ""))
        failed += 0 if ok else 1
    print("DIRECTOR CRASHTEST %s (%d cases)" % ("PASSED" if not failed else "FAILED (%d)" % failed, len(results)))
    return 0 if not failed else 1


def cmd_racetest():
    """The race court (S1, with fix 1 of the owner's ruling of 2026-10-13): writers at once, and a second writer at every
    point an admission writes — another thread's admission, another process's recovery. Each case has the plant it
    must catch. In a scratch copy, with the round's candidates A (the brief alone) and B (a lamp and a layout: three
    files), both evaluated at one head."""
    import contextlib
    import io
    import threading
    tmp = tempfile.mkdtemp(prefix="director-racetest-")
    results = []
    me = os.path.abspath(__file__)
    env0 = {k: v for k, v in os.environ.items() if k not in ("VERDANDI_CRASH_AT", "VERDANDI_PLANT", "VERDANDI_LOCK_WAIT")}
    saved_plant, saved_hook = durable.PLANT, durable.HOOK
    lib = os.path.join(HERE, "director")

    def res(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    def run(args, **env):
        r = subprocess.run([sys.executable, "-B", me] + args + ["--root", tmp], capture_output=True, text=True,
                           env=dict(env0, **env), timeout=600)
        return r.returncode, r.stdout + r.stderr
    try:
        for sub in ("art/rounds", "graybox/maps"):         # the checkout's briefs are not the test's: the round's base alone
            shutil.copytree(os.path.join(REPO, sub), os.path.join(tmp, sub))
        os.makedirs(os.path.join(tmp, "art", "briefs"))
        lock = led.lock_path(os.path.join(tmp, "art", "ledger", "plaza-night.ledger"))

        # 1. two writers of one ledger, as threads and as processes
        race_led = os.path.join(tmp, "art", "ledger", "race.ledger")

        def fresh():
            if os.path.exists(race_led):
                os.remove(race_led)
            led.append(race_led, "genesis", {"note": "the race court's ledger"})

        def whole():
            try:
                ev, _h = led.chain(race_led)
                return len(ev) == 51
            except led.LedgerError:
                return False

        def thread_trials(plant, trials=5):
            broken = 0
            durable.PLANT = plant
            try:
                for _t in range(trials):
                    fresh()
                    go, errs = threading.Barrier(2), []

                    def writer(k):
                        go.wait()
                        try:
                            for i in range(25):
                                led.append(race_led, "evaluate", {"note": "%d-%d" % (k, i)})
                        except Exception as e:           # noqa: BLE001 — a broken ledger refuses the next append
                            errs.append(e)
                    th = [threading.Thread(target=writer, args=(k,)) for k in (1, 2)]
                    for t in th:
                        t.start()
                    for t in th:
                        t.join()
                    broken += 0 if (whole() and not errs) else 1
            finally:
                durable.PLANT = saved_plant
            return broken
        b0, b1 = thread_trials(""), thread_trials("no-lock")
        res("two threads append 25 events each to one ledger: the chain whole, 51 events, in every trial", b0 == 0, "broken in %d of 5" % b0)
        res("plant: the lock holds nothing — the chain breaks", b1 > 0, "broken in %d of 5" % b1)
        child = ("import os, sys, time\nsys.path.insert(0, %r)\nimport ledger as led\np, go, k = sys.argv[1], sys.argv[2], sys.argv[3]\n"
                 "while not os.path.exists(go):\n    time.sleep(0.001)\n"
                 "for i in range(25):\n    led.append(p, 'evaluate', {'note': '%%s-%%d' %% (k, i)})\n") % lib

        def process_trials(plant, trials=3):
            broken = 0
            for t in range(trials):
                fresh()
                go = os.path.join(tmp, "go.%s.%d" % (plant or "lock", t))
                env = dict(env0, **({"VERDANDI_PLANT": plant} if plant else {}))
                ps = [subprocess.Popen([sys.executable, "-B", "-c", child, race_led, go, str(k)], env=env,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE) for k in (1, 2)]
                time.sleep(0.5)
                open(go, "w").close()
                rcs = [p.communicate(timeout=300) and p.returncode for p in ps]
                broken += 0 if (whole() and rcs == [0, 0]) else 1
            return broken
        p0, p1 = process_trials(""), process_trials("no-lock")
        res("two processes append 25 events each to one ledger: the chain whole in every trial (the system's lock)", p0 == 0, "broken in %d of 3" % p0)
        res("plant: the lock holds nothing — two processes break the chain", p1 > 0, "broken in %d of 3" % p1)
        os.remove(race_led)

        # the brief, its ledger and the two candidates at one head
        ws = Workspace("plaza-night", tmp)
        rnd = os.path.join(tmp, "art", "rounds", "plaza-imposing")
        for f, to in (("plaza-night.art", "art/briefs"), ("tactical.design", "graybox/maps"), ("tactical.layout", "graybox/maps")):
            shutil.copy(os.path.join(rnd, "base", f), os.path.join(tmp, to, f))
        cmd_genesis_quiet(ws)
        rows = _quiet(cmd_evaluate, ws, [os.path.join(rnd, "A.intent"), os.path.join(rnd, "B.intent")], quiet=True)
        seq_a, seq_b = rows[0][4], rows[1][4]
        evs = led.read(ws.ledger)[0]
        parent = current_parts(ws)
        pair = lambda p: {"art_sha256": p["art_sha256"], "world_sha256": p["world_sha256"]}  # noqa: E731
        child_a, child_b = pair(evs[int(seq_a)]["after"]), pair(evs[int(seq_b)]["after"])

        # 2. two exports at once over different maps (a candidate's layout is drawn over a folder of its own)
        it_b = canon.load_intent(evs[int(seq_b)]["intent"].encode("ascii"))
        out0, base_parts, _c = ws.export()
        maps_b, _n, _h = with_layout(ws, out0, it_b["layout"], layout_label(it_b))
        _o, b_parts, _c = ws.export(None, maps_b)

        def export_trials(plant, n=20):
            wrong = [0]
            durable.PLANT = plant

            def one(maps, want):
                for _i in range(n):
                    try:
                        wrong[0] += ws.export(None, maps)[1] != want
                    except Exception:                    # noqa: BLE001 — the converter read the other folder
                        wrong[0] += 1
            try:
                th = [threading.Thread(target=one, args=(None, base_parts)), threading.Thread(target=one, args=(maps_b, b_parts))]
                for t in th:
                    t.start()
                for t in th:
                    t.join()
            finally:
                durable.PLANT = saved_plant
            return wrong[0]
        e0, e1 = export_trials(""), export_trials("no-export-lock")
        shutil.rmtree(maps_b, ignore_errors=True)
        res("two threads export at once, over the brief's maps and over a candidate's: every head right (40 exports)", e0 == 0, "%d wrong" % e0)
        res("plant: no export lock — an export reads the other's maps", e1 > 0, "%d of 40 wrong or failed" % e1)

        # 3. an admission with a second writer at each of its points
        watched = [ws.art, ws.ledger] + [os.path.join(ws.maps, f) for f in ("tactical.design", "tactical.layout")]
        snap = {f: open(f, "rb").read() for f in watched}

        def restore():
            durable.HOOK = None
            durable.remove_tree(ws.pending)
            for f in os.listdir(os.path.dirname(ws.ledger)):
                if ".torn." in f:
                    os.remove(os.path.join(os.path.dirname(ws.ledger), f))
            for f, b in snap.items():
                with open(f, "wb") as fh:
                    fh.write(b)

        def tree():
            t = {f: open(f, "rb").read() for f in watched}
            if os.path.isdir(ws.pending):
                for f in sorted(os.listdir(ws.pending)):
                    t["pending/" + f] = open(os.path.join(ws.pending, f), "rb").read()
            return t

        def where():
            p = pair(current_parts(ws))
            at = "parent" if p == pair(parent) else "A" if p == child_a else "B" if p == child_b else "between"
            kinds = [e["kind"] for e in led.read(ws.ledger)[0]]
            return at, kinds.count("admit"), kinds[-1]

        def verified():
            try:
                _quiet(cmd_verify, ws, quiet=True)
                return True
            except led.LedgerError:
                return False

        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            cmd_admit(ws, seq_b, chooser="racetest")
        k = sum(1 for f in watched if f != ws.ledger and open(f, "rb").read() != snap[f])
        res("B admitted alone reaches its child (%d files change), no pending folder" % k, where() == ("B", 1, "admit") and not os.path.isdir(ws.pending) and verified())
        points = (["pending:file-%d" % n for n in range(k)] + ["pending:manifest", "ledger:admit"]
                  + ["install:file-%d" % n for n in range(k)] + ["pending:manifest-removed"])

        def contest(point, plant="", recover_plant=""):
            """B admitted by one thread; at `point` another process recovers and another thread admits A."""
            restore()
            st = {"first": None, "second": None, "busy": None, "same": None, "started": False}
            reached = threading.Event()

            def second():
                try:
                    cmd_admit(ws, seq_a, chooser="racetest-second")
                    st["second"] = "ADMITTED"
                except SystemExit as e:
                    st["second"] = "REFUSED: " + " ".join(str(e).split())[:110]
                except Exception as e:                   # noqa: BLE001 — a read of a tree half installed
                    st["second"] = "ERROR: %s" % (" ".join(str(e).split())[:110])
                finally:
                    reached.set()

            def hook(name):
                me_ = threading.current_thread().name
                if me_ == "race-second" and name == "admit:lock-wait":
                    reached.set()
                elif me_ == "race-first" and name == point and not st["started"]:
                    st["started"] = True
                    before = tree()
                    env = {"VERDANDI_LOCK_WAIT": "0.3"}
                    if recover_plant:
                        env["VERDANDI_PLANT"] = recover_plant
                    st["busy"] = run(["verify", "plaza-night"], **env)
                    st["same"] = tree() == before
                    t2 = threading.Thread(target=second, name="race-second")
                    t2.start()
                    st["t2"] = t2
                    reached.wait(300)

            def first():
                try:
                    cmd_admit(ws, seq_b, chooser="racetest")
                    st["first"] = "ADMITTED"
                except SystemExit as e:
                    st["first"] = "REFUSED: " + " ".join(str(e).split())[:110]
                except Exception as e:                   # noqa: BLE001
                    st["first"] = "ERROR: %s" % (" ".join(str(e).split())[:110])
            durable.HOOK, durable.PLANT = hook, plant
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    t1 = threading.Thread(target=first, name="race-first")
                    t1.start()
                    t1.join()
                    if st.get("t2"):
                        st["t2"].join()
            finally:
                durable.HOOK, durable.PLANT = None, saved_plant
            return st

        before_install = ("pending:", "ledger:")
        for point in points:
            st = contest(point)
            at, admits, last = where()
            rc, out = st["busy"] or (None, "")
            fenced = st["second"] is not None and st["second"] != "ADMITTED" and (
                not point.startswith(before_install) or point == "pending:manifest-removed" or "HEAD-MOVED" in st["second"])
            ok = (st["first"] == "ADMITTED" and fenced and (at, admits, last) == ("B", 1, "admit") and verified()
                  and not os.path.isdir(ws.pending))
            res("at %s: the second admission %s, the files B's child, one admit event" % (
                point, "waits for the lock and is refused by the fence" if point.startswith(before_install) and point != "pending:manifest-removed"
                else "is refused"), ok, "second: %s; the files at %s, %d admit event%s" % (st["second"], at, admits, "" if admits == 1 else "s"))
            res("at %s: another process's recovery refuses (LEDGER-BUSY) and changes nothing" % point,
                rc == 1 and "LEDGER-BUSY" in out and st["same"] is True, "exit %s; %s" % (rc, (out.strip().splitlines() or [""])[-1][:110]))
        st = contest("pending:manifest", plant="no-fence")
        at, admits, last = where()
        res("plant: no fence — the second admission writes over the first", st["second"] == "ADMITTED" or admits != 1 or at != "B" or not verified(),
            "second: %s; the files at %s, %d admit events, the ledger %s" % (st["second"], at, admits, "verifies" if verified() else "does not verify"))
        st = contest("pending:manifest", recover_plant="recover-ignores-lock")
        res("plant: a recovery that ignores the lock changes the tree under a live admission", st["same"] is False,
            "the tree %s while the admission held the lock; first: %s" % ("unchanged" if st["same"] else "changed", st["first"]))

        # 4. a holder that dies holding the lock: the system releases it (the lease)
        hold = ("import os, sys\nsys.path.insert(0, %r)\nimport durable\nwith durable.locked(sys.argv[1]):\n"
                "    print('held', flush=True)\n    os._exit(77)\n") % lib
        r = subprocess.run([sys.executable, "-B", "-c", hold, lock], capture_output=True, text=True, env=env0, timeout=120)
        t0 = time.monotonic()
        try:
            with durable.locked(lock, 10):
                took = time.monotonic() - t0
        except durable.Busy:
            took = None
        res("a holder that dies holding the lock: the system releases it, no timeout needed", r.returncode == 77 and "held" in r.stdout and took is not None,
            "the holder exit %d; the lock taken %s" % (r.returncode, "after %.2f s" % took if took is not None else "NOT within 10 s"))

        # 5. a failure inside the admission (the owner's addition): no pending folder left; a prepared one finished at once
        for point, want in (("pending:file-1", ("parent", 0, "evaluate")), ("pending:manifest", ("parent", 0, "evaluate")),
                            ("install:file-1", ("B", 1, "admit"))):
            restore()

            def boom(name, point=point):
                if name == point:
                    raise RuntimeError("planted failure at " + point)
            durable.HOOK = boom
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    cmd_admit(ws, seq_b, chooser="racetest")
                raised = False
            except RuntimeError:
                raised = True
            finally:
                durable.HOOK = None
            ok = raised and where() == want and not os.path.isdir(ws.pending) and verified() and (want[0] == "B" or open(ws.ledger, "rb").read() == snap[ws.ledger])
            res("a failure at %s: the error raised, no pending folder left, the files at the %s" % (
                point, "parent and the ledger as it was" if want[0] == "parent" else "child (the admit event was written; finished at once)"), ok,
                "the files at %s, %d admit event%s" % (where()[0], where()[1], "" if where()[1] == 1 else "s"))

        # 6. an orphan pending folder met by the next admission: recovered under the lock, then that admission completes
        restore()
        rc, _o = run(["admit", "plaza-night", seq_b, "--chooser", "racetest"], VERDANDI_CRASH_AT="pending:manifest")
        orphan = os.path.isdir(ws.pending)
        sink = io.StringIO()
        try:
            with contextlib.redirect_stdout(sink):
                cmd_admit(ws, seq_a, chooser="racetest")
            outcome = "admitted"
        except SystemExit as e:
            outcome = "refused: %s" % e
        res("an orphan pending folder (its writer killed) met by the next admission: undone under the lock, then A admitted",
            rc == durable.CRASH_EXIT and orphan and outcome == "admitted" and where() == ("A", 1, "admit") and not os.path.isdir(ws.pending)
            and "RECOVERED" in sink.getvalue() and verified(), "the killed writer %d; %s; %s" % (rc, outcome, " ".join(
                ln for ln in sink.getvalue().splitlines() if ln.startswith("RECOVERED"))[:110]))
    finally:
        durable.HOOK, durable.PLANT = saved_hook, saved_plant
        shutil.rmtree(tmp, ignore_errors=True)
    failed = 0
    for name, ok, d in results:
        print("%s %s%s" % ("PASS" if ok else "FAIL", name, (" — " + d) if d else ""))
        failed += 0 if ok else 1
    print("DIRECTOR RACETEST %s (%d cases)" % ("PASSED" if not failed else "FAILED (%d)" % failed, len(results)))
    return 0 if not failed else 1


def _tamper(path):
    raw = open(path, "rb").read()
    i = raw.index(b'"chooser":"selftest"')
    open(path, "wb").write(raw[:i] + b'"chooser":"selftesT"' + raw[i + len(b'"chooser":"selftest"'):])


def _quiet(fn, *a, **k):
    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **k)


cmd_genesis_quiet = lambda ws: _quiet(cmd_genesis, ws)
cmd_admit_quiet = lambda ws, s, **k: _quiet(cmd_admit, ws, s, **k)
cmd_reevaluate_quiet = lambda ws, s: _quiet(cmd_reevaluate, ws, s)
cmd_refuse_quiet = lambda ws, s, **k: _quiet(cmd_refuse, ws, s, **k)
cmd_rebase_quiet = lambda ws, n: _quiet(cmd_rebase, ws, n)


def opt(argv, k, d=None):
    return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d


def main(argv):
    if not argv:
        print(__doc__ if __doc__ else open(__file__, encoding="utf-8").read().split("\n\n")[0])
        return 2
    cmd, args = argv[0], [a for a in argv[1:]]
    flags = ("--accept-leakage",)
    valued = ("--chooser", "--note", "--config", "--approver", "--root")
    pos = []
    i = 0
    while i < len(args):
        if args[i] in valued:
            i += 2
            continue
        if args[i] not in flags:
            pos.append(args[i])
        i += 1
    try:
        if cmd == "vectors":
            n, bad = cmd_vectors(pos[0] if pos else None)
            return 0 if not bad else 1
        if cmd == "selftest":
            return cmd_selftest()
        if cmd == "crashtest":
            return cmd_crashtest()
        if cmd == "racetest":
            return cmd_racetest()
        ws = Workspace(pos[0], os.path.abspath(opt(args, "--root", REPO)))
        say_recovered(ws)
        if cmd == "genesis":
            cmd_genesis(ws)
        elif cmd == "lens":
            cmd_lens(ws, pos[1])
        elif cmd == "evaluate":
            cmd_evaluate(ws, pos[1:])
        elif cmd == "reevaluate":
            cmd_reevaluate(ws, pos[1])
        elif cmd == "admit":
            cmd_admit(ws, pos[1], "--accept-leakage" in args, opt(args, "--chooser", "the owner"), opt(args, "--note", ""))
        elif cmd == "refuse":
            cmd_refuse(ws, pos[1], opt(args, "--chooser", "the owner"), opt(args, "--note", ""))
        elif cmd == "rebase":
            cmd_rebase(ws, opt(args, "--note", ""))
        elif cmd == "approve":
            cmd_approve(ws, pos[1], pos[2], opt(args, "--config", ""), opt(args, "--approver", "the owner"), opt(args, "--note", ""))
        elif cmd == "verify":
            cmd_verify(ws)
        else:
            print("unknown command %r" % cmd)
            return 2
    except led.LedgerError as e:
        print("LEDGER REFUSED: %s" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
