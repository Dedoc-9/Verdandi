# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/director.py — DIRECTOR-0: a prompt answered by candidates, each checked against the head it meets, admitted or
# refused by a person, and every step kept in an append-only ledger.
#
#   python art/director.py genesis  BRIEF                      start the brief's ledger at the current head
#   python art/director.py lens     BRIEF REGION               what a proposer reads: the region, its pieces, their materials
#   python art/director.py evaluate BRIEF FILE... [--inverse-of N]
#                                                              check candidate intents at the current head; a contact sheet
#                                                              (0254: an intent holding an inverse form, '@=', '@+' or '@~', is
#                                                              evaluated only with --inverse-of N, its revision admission #N's
#                                                              stored inverse; otherwise REFUSED, INTENT-INVERSE-ONLY)
#   python art/director.py reevaluate BRIEF SEQ [--inverse-of N]
#                                                              check an earlier evaluation's intent again, at the current head
#   python art/director.py admit    BRIEF SEQ --still FILE.png [--despite-detectors] [--accept-leakage] [--chooser NAME] [--note TEXT]
#                                                              (ADMISSION-0, 0222: the evaluation's record must be complete and what
#                                                              it requires present; --inverse-of SEQ in place of a still for an undo)
#   python art/director.py record   BRIEF SEQ                  an evaluation's record: its rung and why, what it certifies, what it did
#                                                              not check, what an admission needs, what it rests on
#   python art/director.py refuse   BRIEF SEQ [--chooser NAME] [--note TEXT]
#   python art/director.py rebase   BRIEF --note TEXT          record a change made outside the loop (a hand edit, a new exporter)
#   python art/director.py approve  BRIEF VIEW IMAGE --config TEXT [--approver NAME] [--note TEXT] [--despite-detectors]
#   python art/director.py verify   BRIEF                      the ledger's chain, replayed to the files as they stand
#   python art/director.py vectors                             the reference against the conformance vectors
#   python art/director.py selftest                            the vectors, and the whole lifecycle in a scratch copy
#   python art/director.py memotest                            THROUGHPUT-0 (0236): the export memo against the export itself, and its plants
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
# No event over a head the ledger does not hold (LEDGER-SAFE-0, 0245): an event that names the head it was checked
# against (an evaluation, an admission, an approval) is appended only under the content lock, and only while the files
# are the head the ledger replays to and that head is the one it was checked against. Otherwise it is refused and
# nothing is appended: LEDGER-UNLOGGED (the files changed outside the loop: record them with rebase first) or
# HEAD-MOVED (another admission landed meanwhile: evaluate again). Before it, one evaluation over a hand edit or a new
# exporter appended an event that replay, and therefore rebase, refused for good (MEASURED, 2026-10-16, on a copy of
# the checkout's plaza-night). A rebase is recorded only for files that pass the art checks, under the lock.
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
import contract  # noqa: E402
import quality  # noqa: E402
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
# that plant's two exports meet twice (0246): once both have pointed level.MAPS at their folders, and once both have
# exported, so that both are inside the window the lock closes at once, whatever else the machine runs (whether one then
# reads the other's folder is still the interleaving's). A sleep held the window open from 0241, and the race still went
# unmet once, 0 of 40, with twenty-five suites run sixteen at once.
PLANT_MEET = threading.Barrier(2)


def _plant_meet():
    try:
        PLANT_MEET.wait(30)
    except threading.BrokenBarrierError:      # its partner never came: an export alone goes on, and the next pair meets
        PLANT_MEET.reset()


# THROUGHPUT-0 (0236): an exact memo of Workspace.export. An export is a function of its text, its brief's name, the maps folder it
# is pointed at, and the files it reads; the memo keeps one result per (brief, text, maps folder) with the sha256 of
# every file the export opened and of every folder it listed, recorded as it ran (PEP 578's audit events "open",
# "os.listdir" and "os.scandir", in the exporting thread only), and a result is used again only when every one of them
# is byte for byte as it was; a path it tried and did not find must still be absent. A result is never shared: it is
# kept as its pickle and every use takes a copy of its own, so that a caller that changes what it was given changes
# nothing another sees. Not kept: an export that raised, wrote a file, opened something not named by a path, or ran
# while a file it read changed (its stat before and after); none while a plant of durable is set, or with
# VERDANDI_EXPORT_MEMO=0. What it does not see: a branch on whether a file exists that opens nothing (os.path.exists
# and the like raise no audit event; the export reads none, VERIFIED by reading dress.py, graybox/level.py, graybox/check.py's
# source_rows, check.verify and quality.check_scene).
import collections  # noqa: E402
import pickle  # noqa: E402
MEMO = {"on": os.environ.get("VERDANDI_EXPORT_MEMO", "1") != "0", "max": 24, "plant": ""}
MEMO_STATS = collections.Counter()
_memo = collections.OrderedDict()     # key -> (inputs {path: sha256}, listings {path: sha256}, absent [path], blob)
_reading = threading.local()
_HOOKED = []


def _audit(event, args):
    rec = getattr(_reading, "rec", None)
    if rec is None or event not in ("open", "os.listdir", "os.scandir"):
        return
    path = args[0]
    if event != "open":
        if path is None:
            path = "."
        if not isinstance(path, (str, bytes)):
            rec["bad"] = "a folder listed by descriptor"
            return
        rec["dirs"].add(os.path.realpath(os.fsdecode(path)))
        return
    if not isinstance(path, (str, bytes)):
        rec["bad"] = "a file opened by descriptor"
        return
    mode, flags = args[1], args[2] if len(args) > 2 else 0
    writes = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (mode is None and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
    p = os.path.realpath(os.fsdecode(path))
    if writes:
        rec["bad"] = "it wrote %s" % p
    elif p not in rec["files"]:
        try:
            st = os.stat(p)
            rec["files"][p] = (st.st_mtime_ns, st.st_size, st.st_ino)
        except OSError:
            rec["files"][p] = None


def _digest(p):
    try:
        with open(p, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return None


def _listing(p):
    try:
        return hashlib.sha256("\n".join(sorted(os.listdir(p))).encode("utf-8", "surrogateescape")).hexdigest()
    except OSError:
        return None


def _still(entry):
    """Is every input of a kept result as it was?"""
    inputs, dirs, absent = entry[:3]
    if MEMO["plant"] == "memo-no-validate":
        return True
    return all(_digest(p) == h for p, h in inputs.items()) and all(_listing(p) == h for p, h in dirs.items()) \
        and not any(os.path.exists(p) for p in absent)


def memo_call(key, compute):
    """compute() once per key while its inputs stand: the result, a copy of its own on every call."""
    if not MEMO["on"] or durable.PLANT:
        MEMO_STATS["off"] += 1
        return compute()
    with EXPORT_LOCK:
        entry = _memo.get(key)
        if entry is not None:
            if _still(entry):
                _memo.move_to_end(key)
                MEMO_STATS["hit"] += 1
                return pickle.loads(entry[3]) if MEMO["plant"] != "memo-shares" else entry[4]
            del _memo[key]
            MEMO_STATS["stale"] += 1
        if not _HOOKED:
            sys.addaudithook(_audit)
            _HOOKED.append(True)
        rec = {"files": {}, "dirs": set(), "bad": ""}
        saved, _reading.rec = getattr(_reading, "rec", None), rec
        try:
            result = compute()
        finally:
            _reading.rec = saved
        MEMO_STATS["miss"] += 1
        if rec["bad"] and MEMO["plant"] != "memo-keeps-writes":
            MEMO_STATS["not kept"] += 1
            return result
        inputs, absent = {}, []
        for p, st in sorted(rec["files"].items()):
            if st is None:
                if os.path.exists(p):
                    MEMO_STATS["not kept"] += 1     # absent when it was opened, present now: it changed while the export ran
                    return result
                absent.append(p)
                continue
            try:
                now_ = os.stat(p)
            except OSError:
                MEMO_STATS["not kept"] += 1
                return result
            if (now_.st_mtime_ns, now_.st_size, now_.st_ino) != st:
                MEMO_STATS["not kept"] += 1         # written while the export read it: the bytes it read are not known
                return result
            inputs[p] = _digest(p)
        dirs = {d: _listing(d) for d in sorted(rec["dirs"])}
        blob = pickle.dumps(result, protocol=pickle.HIGHEST_PROTOCOL)
        _memo[key] = (inputs, dirs, absent, blob) + ((result,) if MEMO["plant"] == "memo-shares" else ())
        while len(_memo) > MEMO["max"]:
            _memo.popitem(last=False)
        return pickle.loads(blob) if MEMO["plant"] != "memo-shares" else result


def memo_clear():
    with EXPORT_LOCK:
        _memo.clear()
    MEMO_STATS.clear()


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
        self.stills = self.ledger + ".stills"       # ADMISSION-0's evidence: each admission's still, by its sha256

    def text(self):
        return open(self.art, "rb").read().replace(b"\r\n", b"\n").decode("utf-8")

    def export(self, text=None, maps=None):
        """The scene of an art text over a maps folder, with the parts of its head and its checks' results. THROUGHPUT-0 (0236):
        through the memo above, which gives the same result as computing it again, or computes it again."""
        text = self.text() if text is None else text
        maps = maps or self.maps
        key = (self.brief, canon.sha256(text.encode("utf-8")), os.path.realpath(maps)) if MEMO["plant"] != "memo-key-text" else (self.brief, os.path.realpath(maps))
        return memo_call(key, lambda: self._export(text, maps))

    def _export(self, text, maps):
        A = dress.parse(text, self.brief + ".art")
        A["name"], A["sha256"] = self.brief, canon.sha256(text.encode("utf-8"))
        with EXPORT_LOCK if durable.PLANT != "no-export-lock" else NO_LOCK:   # level.MAPS is one global
            saved = level.MAPS
            level.MAPS = maps
            planted = durable.PLANT == "no-export-lock"
            if planted:
                _plant_meet()       # the race court's plant only: both folders pointed at before either export reads
            try:
                out = dress.export(A, maps_dir=maps)
                D = check.gcheck.source_rows(out["W"])
                res = check.verify(out, None, D=D)
            finally:
                if planted:
                    _plant_meet()   # and both exports read before either folder is put back
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
# 0254's switch (spec §8, the frozen matrix's 'the rule'): one named value at a time, set only by cmd_selftest's 0254 rows
# (inverse_rows) and put back after them; "" everywhere else. Each value is read only where it is named: in apply_revision,
# inverse_of_ok, evaluate_doc, admit_checks and replay here, and, through the hooks those rows point at it, in
# art/director/intent.py's inverse_form and art/director/inverse_freeze.py's frozen()
INVERSE_PLANT = ""


def apply_revision(text, lines, undo=False):
    """The art text with the revision applied, and its exact inverse. '= stmt' replaces the statement with the same
    key, '+ stmt' appends one whose key is new, '- key' removes the statement with that key. Refuses (INTENT-APPLY)
    a line that names no statement, or a '+' whose key exists. The three are applied byte for byte as before 0254; only
    what they record changed (0254, his ruling: "Ruling: (a). 0254 records the inverse of = and - as the exact row at its
    position (and the trailing blank lines of +), applied only by undo, frozen first and built second, against BINDING-0
    v0 unchanged."). A row is an element of text.split("\n"), a position a 0-based index into the rows as they stand when
    its line is applied. '=' at row I records '@= [I, the row as written, the old row verbatim]'; '-' of row I records
    '@+ [I, the row verbatim, the row that followed it, or false when it was the last]'; '+' records '- key', and after it
    '@~ ["1","K"]' when it took K != 1 trailing empty rows away. The inverse is each line's record, in reverse line order
    (their syntax: art/director/intent.py inverse_form).
    Exact (T-0254, narrowed by a review finding: the frozen spec's §5 says "any revision of ordinary lines that
    apply_revision(P, r) accepts", which its own first falsifier refutes): the undo over the child returns P byte for byte
    for a revision whose ordinary lines pass intent.validate (no '#', no LF) and whose '+' lines add no lone verb outside
    SINGLE, moon and sun (whose statement key, 'V ', is not its own strip: its '- V ' names no row). Every revision a caller
    passes has passed intent.validate, and the exporter refuses every such lone verb (ART-REFUSED), so no admission reaches
    either case; given straight to this function, '+ tower' and '+ lamp b#c 1,2,3 100 1' are accepted and their undo
    refused INTENT-APPLY (docs/CAPABILITY-MATRIX.md, 2026-10-20).
    The '@' forms are applied only with undo=True: otherwise the revision is refused whole, INTENT-INVERSE-ONLY (the one
    enforcement point; its callers pass undo=True only where inverse_of_ok holds, and certificate.check in memory). Each
    is applied under its guard, refused INTENT-APPLY naming the form, the position and what it found, never retried by
    key or in another form:
      '@= [I,W,R]'  rows[I] is W byte for byte, W and R of one statement key: rows[I] := R; records '@= [I,R,W]'
      '@+ [I,R,S]'  R holds a statement whose key no row holds; and S false with I the number of rows, or S false, I 0 and
                    the rows [""] (the text "" a '-' of every row leaves: the rows become [R]), or rows[I] is S: R
                    inserted at I; records '- key'
      '@~ [A,B]'    the rows end in exactly A empty rows: those taken away, B appended; records '@~ [B,A]'"""
    rows = text.split("\n")
    keyed = lambda ln: dress.statement_key(ln.split("#", 1)[0].split()) if ln.split("#", 1)[0].split() else None
    P = INVERSE_PLANT          # the 0254 rows' switch (cmd_selftest); "" everywhere else
    parent_rows = list(rows)   # read only under the plant inverse-parent-positions
    if not undo and P != "inverse-anywhere":
        for ln in lines:
            if ln[:1] == "@":
                raise canon.IntentError("INTENT-INVERSE-ONLY", "%r is an inverse form, applied only by an undo naming the admission that "
                                                               "recorded it (inverse_of)" % (ln[:2],))
    inverse = []
    for ln in lines:
        if ln[:1] == "@":
            form, v = canon.inverse_form(ln)
            i = int(v[0])
            if form == "@=":
                w, r = v[1], v[2]
                held = i < len(rows) and (keyed(rows[i]) == keyed(w) if P == "guard-key-not-bytes" else rows[i] == w)
                if not held and P == "inverse-key-fallback":
                    found = [j for j, x in enumerate(rows) if keyed(x) == keyed(w) and x == w]
                    if len(found) == 1:
                        i, held = found[0], True
                if P != "guard-skipped-replace" and i >= len(rows):
                    raise canon.IntentError("INTENT-APPLY", "'@=' at row %d: the text has %d rows" % (i, len(rows)))
                if P != "guard-skipped-replace" and not held:
                    raise canon.IntentError("INTENT-APPLY", "'@=' at row %d: found %r, not the row the admission wrote" % (i, rows[i][:120]))
                if P != "guard-rekey-skipped" and (keyed(w) is None or keyed(w) != keyed(r)):
                    raise canon.IntentError("INTENT-APPLY", "'@=' at row %d: the row it restores, %r, is not of the statement key of the row it "
                                                            "replaces (%r)" % (i, r[:120], keyed(w)))
                rows[i] = r
                inverse.append([canon.inverse_line("@=", [v[0], r, w])])
            elif form == "@+":
                r, s = v[1], v[2]
                key = keyed(r)
                if key is None:
                    raise canon.IntentError("INTENT-APPLY", "'@+' at row %d: the row it restores, %r, holds no statement" % (i, r[:120]))
                if any(keyed(x) == key for x in rows):
                    raise canon.IntentError("INTENT-APPLY", "'@+' at row %d: the brief already has a statement %r" % (i, key))
                if s is False and i == 0 and rows == [""] and P != "empty-child-insert":
                    rows = [r]
                elif P == "guard-skipped-insert":
                    rows.insert(i, r)
                elif s is False and i == len(rows):
                    rows.insert(i, r)
                elif s is not False and i < len(rows) and rows[i] == s:
                    rows.insert(i, r)
                else:
                    raise canon.IntentError("INTENT-APPLY", "'@+' at row %d: found %s, not %s" % (
                        i, ("%r" % rows[i][:120]) if i < len(rows) else "the end of the text" if i == len(rows) else "no row (the text has %d)" % len(rows),
                        ("%r" % s[:120]) if s is not False else "the end of the text"))
                inverse.append(["- " + key])
            else:
                n = 0
                while n < len(rows) and rows[len(rows) - 1 - n] == "":
                    n += 1
                if n != i and P != "guard-skipped-tail":
                    raise canon.IntentError("INTENT-APPLY", "'@~': the text ends in %d empty rows, not %d" % (n, i))
                del rows[len(rows) - i:]
                rows += [""] * int(v[1])
                inverse.append([canon.inverse_line("@~", [v[1], v[0]])])
            continue
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
            old = rows[at[0]]
            tail = ("  #" + rows[at[0]].split("#", 1)[1]) if "#" in rows[at[0]] else ""
            rows[at[0]] = (body if P == "legacy-spacing-kept" else " ".join(body.split())) + tail
            if P == "inverse-statement-form":
                inverse.append(["= " + old.split("#", 1)[0].strip()])
            else:
                inverse.append([canon.inverse_line("@=", [_planted_position(P, parent_rows, keyed, key, at[0]), rows[at[0]], old])])
        elif op == "+":
            if at:
                raise canon.IntentError("INTENT-APPLY", "'+ %s': the brief already has a statement %r" % (body, key))
            k = 0
            while rows and rows[-1] == "":
                rows.pop()
                k += 1
            rows += [" ".join(body.split()), ""]
            tail_kept = (k != 1 and P != "plus-tail-dropped") or P == "plus-tail-always"
            inverse.append(["- " + key] + ([canon.inverse_line("@~", ["1", str(k)])] if tail_kept else []))
        else:
            if len(at) != 1:
                raise canon.IntentError("INTENT-APPLY", "'- %s' names no statement of the brief" % key)
            i = at[0]
            r = rows[i]
            del rows[i]
            if P == "inverse-statement-form":
                inverse.append(["+ " + r.split("#", 1)[0].strip()])
            else:
                inverse.append([canon.inverse_line("@+", [_planted_position(P, parent_rows, keyed, key, i), r, rows[i] if i < len(rows) else False])])
    return "\n".join(rows), [x for group in reversed(inverse) for x in group]


def _planted_position(P, parent_rows, keyed, key, i):
    """The position an '=' or a '-' records: its row's index at the moment of its line (0254); under the 0254 rows' plant
    inverse-parent-positions, the index the key's row had in the parent (the moment's when the parent has none)."""
    if P == "inverse-parent-positions":
        at = [j for j, x in enumerate(parent_rows) if keyed(x) == key]
        if len(at) == 1:
            return str(at[0])
    return str(i)


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


# -------------------------------------------------------------------------------------------- the head the ledger holds
class Refusal(SystemExit):
    """A refusal with its code kept apart (LEDGER-SAFE-0, 0245): `refusal` is the code, so that the studio passes it on
    (art/studio.py quiet()). Still a SystemExit, as every refusal of a command here is: the command line prints
    'REFUSED (CODE): ...' and ends as before. (Not `code`: a SystemExit's code is its exit status.)"""

    def __init__(self, code, detail):
        SystemExit.__init__(self, "REFUSED (%s): %s" % (code, detail))
        self.refusal, self.detail = code, detail


# the self-test's planted defects of LEDGER-SAFE-0 (cmd_selftest), never set otherwise: "no-held-check" (an event is
# appended whatever head the ledger holds), "rebase-unchecked" (a rebase is recorded whatever its checks say)
SAFE_PLANT = ""


def held_head(ws, events, checked=None):
    """The ledger's state replayed (replay()), refused unless the files are the head it holds and, given `checked` (the
    head an event about to be appended was checked against), unless that is the same head: LEDGER-UNLOGGED or
    HEAD-MOVED, as Refusal. A ledger that does not replay raises its LedgerError: nothing is appended to a broken chain."""
    if not events:
        raise Refusal("LEDGER-NONE", "%s has no ledger: run genesis first" % ws.brief)
    st = replay(ws, events)
    if SAFE_PLANT == "no-held-check":
        return st
    _o, parts, _c = ws.export()
    files = canon.head(parts)
    if files != st["head"]:
        root = "" if os.path.abspath(ws.root) == os.path.abspath(REPO) else ' --root "%s"' % ws.root
        raise Refusal("LEDGER-UNLOGGED", "record the change first, after reading it: python art/director.py rebase %s%s --note TEXT. "
                                         "Nothing was appended: the files are the head %s, the ledger's %s (the world or the exporter "
                                         "changed outside the loop), and an event checked against them would leave a ledger that replay, "
                                         "and so rebase, refuses for good" % (ws.brief, root, files[:12], st["head"][:12]))
    if checked is not None and checked != st["head"]:
        raise Refusal("HEAD-MOVED", "this was checked against %s, and the ledger's head is now %s (an admission landed meanwhile); "
                                    "nothing was appended. Evaluate it again" % (checked[:12], st["head"][:12]))
    return st


def append_checked(ws, kind, fields, checked):
    """Append an event checked against the head `checked`, under the content lock, only while held_head() holds."""
    try:
        with durable.locked(led.lock_path(ws.ledger)):
            if os.path.exists(ws.pending):       # this process holds the lock: the folder's writer is dead (as _commit_locked)
                for ln in _recover(ws):
                    print(ln)
            events, _l, _h = led.read(ws.ledger)
            held_head(ws, events, checked)
            durable.point("append:held")
            return led.append(ws.ledger, kind, fields)
    except durable.Busy:
        raise Refusal("BUSY", "another writer held this tree's content lock for the whole wait (%g s); nothing was appended" % durable.WAIT)


def append_evaluation(ws, raw, verdict, after, timings, record, re_of=""):
    """An evaluate event, appended only at the head the ledger holds (see append_checked)."""
    return append_checked(ws, "evaluate", evaluation_fields(raw, verdict, after, timings, record, re_of), verdict["checked_against"])


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


def commit_admission(ws, evaluation, intent_sha256, files, fields, stills=(), gate=None):
    """Admit with crash safety: files is [(absolute path, new bytes)], fields the admit event's (with head_before, the
    head the caller checked). See recover().

    The fence (fix 1 of the owner's ruling of 2026-10-13; Kleppmann: the store checks the token at the write): the
    whole admission holds the content lock, and under it the head is computed again from the files and compared with
    head_before before anything is written — the caller's own check was made before the lock, and another admission
    may have landed between the two. Every caller is fenced here, whoever it is.

    BINDING-0 (0253): `gate`, when given (art/studio.py, the studio's admission and undo), is called under the lock
    after every check of the commit and before its first write, the place BINDING-0 version 0's order names for the
    binding check ("after cmd_admit's checks and the commit's own under the content lock, and before the admission's
    first write"); it raises to refuse, and then nothing of the admission is written. The command line passes none."""
    durable.point("admit:lock-wait")
    try:
        with durable.locked(led.lock_path(ws.ledger)):
            return _commit_locked(ws, evaluation, intent_sha256, files, fields, stills, gate)
    except durable.Busy:
        raise SystemExit("REFUSED (BUSY): another writer held this tree's content lock for the whole wait (%g s); nothing was "
                         "changed. Admit again when it ends" % durable.WAIT)


def shared_map(ws, out_now, files):
    """SHARED-MAP, raised as SystemExit when `files` change the maps and another brief plays the map (the commit's check,
    and admit_dry's)."""
    # fix 2 of the review of 2026-10-13: briefs share the graybox's maps, so a layout admitted in one world would change
    # every world that plays its map (write skew between worlds). Until each world has a map of its own (pinned
    # revisions, later), a layout change is refused while another brief plays the map; art changes are not affected
    if any(os.path.dirname(os.path.abspath(f)) == os.path.abspath(ws.maps) for f, _b in files):
        others = briefs_on_map(ws, out_now["scene"]["map"])
        if others:
            raise SystemExit("REFUSED (SHARED-MAP): %s also play%s the map %s, so this layout change would change %s too; nothing was "
                             "changed. A layout is changed only in a world whose map no other world plays, until each world keeps a "
                             "map of its own (pinned revisions, to come); changes to the art are admitted as before" % (
                                 ", ".join(others), "s" if len(others) == 1 else "", out_now["scene"]["map"], "that world" if len(others) == 1 else "those worlds"))


def _commit_locked(ws, evaluation, intent_sha256, files, fields, stills=(), gate=None):
    if os.path.exists(ws.pending):               # this process holds the lock: the folder's writer is dead
        for ln in _recover(ws):
            print(ln)
    out_now, cur, _c = ws.export()
    if durable.PLANT != "no-fence" and canon.head(cur) != fields["head_before"]:
        raise SystemExit("REFUSED (HEAD-MOVED): the head moved to %s while this admission waited for the lock (it was checked "
                         "against %s); nothing was changed. Re-evaluate it first" % (canon.head(cur)[:12], fields["head_before"][:12]))
    if durable.PLANT != "no-shared-map":
        shared_map(ws, out_now, files)
    events, _l, _h = led.read(ws.ledger)
    # LEDGER-SAFE-0 (0245): the fence above holds the files to the head the admission was checked against; the ledger must
    # hold that head too, or the admit event would be one that replay refuses (a hand change back to an older head, say).
    # Part of the fence: the race court's plant "no-fence" takes it away with the rest
    if durable.PLANT != "no-fence":
        held_head(ws, events, fields["head_before"])
    # BINDING-0 (0253): the studio's binding check, after every check above and before the first write below
    if gate is not None:
        gate()
    # the admission's still (ADMISSION-0), kept by its sha256 before anything else is written: content-addressed, so a
    # still left by an admission that then failed names nothing and harms nothing, and the event never names a still
    # that is not on the disk
    for path, b in stills:
        if not (os.path.exists(path) and canon.sha256(open(path, "rb").read()) == os.path.basename(path)[:-4]):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            durable.write(path, b)
    durable.point("admit:stills")
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
# the round the self-tests play (0229): art/rounds/plaza-imposing's candidates over its base with the two slabs at 6.0 m,
# which REACH-1 clears (art/fixtures/round/README.md); laid where the round lay, art/rounds/plaza-imposing
ROUND = os.path.join(HERE, "fixtures", "round")


def lay_round(root):
    """The graybox's own maps and the self-tests' round under root."""
    shutil.copytree(os.path.join(REPO, "graybox", "maps"), os.path.join(root, "graybox", "maps"))
    shutil.copytree(ROUND, os.path.join(root, "art", "rounds", "plaza-imposing"))


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


# ADMISSION-0 (0222): the components a verdict rests on, by sha256 as the files stand when it is made (CRLF read as LF)
TRUSTED = ("art/check.py", "art/quality.py", "art/director.py", "art/director/scope.py", "art/director/contract.py",
           "art/director/intent.py", "art/director/ledger.py", "graybox/check.py", "art/web/scene_render.js",
           "graybox/web/sim.js", "graybox/tick_ref.py")


def trusted_components(parts):
    out = [("art/dress.py (the exporter)", parts["exporter_sha256"])]
    for rel in TRUSTED:
        try:
            out.append((rel, canon.sha256(open(os.path.join(REPO, rel), "rb").read().replace(b"\r\n", b"\n"))))
        except OSError:
            out.append((rel, "missing"))
    return out


def evaluation_fields(raw, verdict, after, timings, record, re_of=""):
    """The fields of an evaluate event: the intent's bytes, its verdict, the head it predicts, and its record."""
    raw = raw if isinstance(raw, bytes) else raw.encode("ascii")
    return {"intent": raw.decode("ascii"), "intent_sha256": canon.sha256(raw), "re_evaluation_of": re_of,
            "verdict": verdict, "after": after, "record": record, "observed": {"at": now(), "ms": timings}}


def inverse_of_ok(events, i, it, before):
    """Whether the intent `it` is the exact inverse of admission #i, as an undo of it (0254: one predicate, for the
    evaluation, the admission and replay): i a sequence number before `before` (len(events) at an evaluation and an
    admission, the admit event's own seq in replay: an undo never names a later admission, its own redo among them), of
    an admit event whose stored inverse is the intent's revision line for line, and the intent changes no layout."""
    i = str(i or "")
    # the number read as 7dee210 read it (its isdigit() and int(); isdecimal() is exactly the strings both accept), so that
    # every ledger 7dee210 wrote and verified replays as it is (spec §4.1): an ASCII-only rule had refused an --inverse-of
    # given in other decimal digits, which 7dee210's command line accepted and wrote (a review finding)
    return i.isdecimal() and (int(i) < int(before) or INVERSE_PLANT == "inverse-of-unbounded") and int(i) < len(events) \
        and events[int(i)]["kind"] == "admit" and (list(events[int(i)]["inverse"]) == list(it["revision"]) or INVERSE_PLANT == "undo-flag-unchecked") \
        and it["layout"] == []


def evaluate_doc(ws, it, re_of="", on_candidate=None, undo_of=None):
    """One intent at the current head: its verdict, the head after it, the stage timings, the scenes and the candidate's
    text, and its ADMISSION-0 record (art/director/contract.py: rung, certifies, not_checked, horizon, trusted, requires).
    on_candidate(out1, maps),
    if given, is called with the candidate's export and the maps folder it was made over, while that folder exists
    (art/play.py converts the candidate's map there to play it).
    undo_of (0254), the sequence number of the admission the intent undoes (the studio's Undo, the command line's
    --inverse-of): the ledger replayed to that admission first (events[:N+1]: a stored inverse holding an '@' line that is
    not the one its revision records is refused there, LEDGER-INVERSE, raised as the LedgerError, before anything is
    applied; one with no '@' line, recorded before 0254, a '- key' alone, or an '@' inverse rewritten by a writer of the
    ledger in the statement form, is not compared, and is applied as #N's inverse as it stands: spec §9); then the
    intent held to be its exact inverse (inverse_of_ok; otherwise REFUSED, INTENT-INVERSE-ONLY); only then its revision
    applied with undo=True. Without it, an '@' line is refused by apply_revision (INTENT-INVERSE-ONLY)."""
    t0 = time.perf_counter()
    timings = {}
    t = time.perf_counter()
    out0, cur, _c = ws.export()
    timings["base_export"] = ms(t)
    after = {"art_sha256": "", "world_sha256": "", "layout_head": ""}
    tmp = None
    trusted = trusted_components(cur)
    regions = set(out0["scene"].get("regions", {}))
    no = lambda v: (v, after, timings, None, out0, None, contract.record(it, v, None, trusted, False, regions))
    try:
        if it["brief"] != ws.brief:
            return no(refused(it, cur, "INTENT-BRIEF", "the intent is for %r" % it["brief"]))
        undo = undo_of not in (None, "")
        if undo:
            events, _l, _h = led.read(ws.ledger)
            n = str(undo_of)
            if events and n.isdecimal() and INVERSE_PLANT != "inverse-unverified":
                replay(ws, events[:int(n) + 1])
            if not inverse_of_ok(events, n, it, len(events)):
                return no(refused(it, cur, "INTENT-INVERSE-ONLY", "the intent is said to undo #%s, and it is not that admission's stored inverse, "
                                                                   "or #%s is no admission before it" % (n, n)))
        t = time.perf_counter()
        try:
            text1, _inv = apply_revision(ws.text(), it["revision"], undo=undo or INVERSE_PLANT == "undo-flag-always")
        except canon.IntentError as e:
            return no(refused(it, cur, e.code, str(e)))
        if undo and INVERSE_PLANT == "inverse-unverified" and events and n.isdecimal():
            replay(ws, events[:int(n) + 1])
        maps = None
        if it["layout"]:
            try:
                maps, _new, head = with_layout(ws, out0, it["layout"], layout_label(it))
                tmp = maps
                after["layout_head"] = head
            except (RuntimeError, canon.IntentError) as e:
                return no(refused(it, cur, "LAYOUT-REFUSED", str(e)[:300]))
        timings["apply"] = ms(t)
        t = time.perf_counter()
        try:
            out1, parts1, checks = ws.export(text1, maps)
        except (dress.ArtError, level.MapError) as e:
            return no(refused(it, cur, "ART-REFUSED", str(e)[:300]))
        timings["candidate_export_and_checks"] = ms(t)
        if on_candidate is not None:
            on_candidate(out1, maps or ws.maps)
        t = time.perf_counter()
        verdict = scopemod.check_scope(it, out0["scene"], out1["scene"], cur, checks)
        timings["scope"] = ms(t)
        after.update({"art_sha256": parts1["art_sha256"], "world_sha256": parts1["world_sha256"]})
        rec = contract.record(it, verdict, checks, trusted, True, regions | set(out1["scene"].get("regions", {})),
                              movers=len(out1["scene"].get("movers", [])))
        return verdict, after, timings, out1, out0, text1, rec
    finally:
        timings["total"] = ms(t0)
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


def cmd_evaluate(ws, files, quiet=False, inverse_of=""):
    events, _l, _h = led.read(ws.ledger)
    if not events:
        raise SystemExit("no ledger for %s: run genesis first" % ws.brief)
    held_head(ws, events)          # LEDGER-SAFE-0: said before anything is appended; each evaluation is held again as it is
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
        verdict, after, timings, out1, out0, _text1, rec = evaluate_doc(ws, it, undo_of=inverse_of or None)
        ev = append_evaluation(ws, raw, verdict, after, timings, rec)
        rows.append((os.path.basename(f), it["candidate"], verdict["verdict"], ",".join(verdict["codes"]) or "-", ev["seq"], timings, rec))
        sheet.append((it, verdict, out0, out1, ev["seq"], timings))
    if not quiet:
        for r in rows:
            print("%-26s %-3s %-8s %-40s ledger #%s  %s ms%s" % (r[0], r[1], r[2], r[3][:40], r[4], r[5].get("total", "-"),
                                                               ("  rung %s" % r[6]["rung"]) if len(r) > 6 else ""))
        print("Each evaluation's record says what it certifies, what it did not check, its rung and what an admission needs: "
              "python art/director.py record %s SEQ" % ws.brief)
        if sheet:
            p = contact_sheet(ws, sheet)
            print("contact sheet: %s" % os.path.relpath(p, ws.root))
    return rows


def cmd_reevaluate(ws, seq, inverse_of=""):
    events, _l, _h = led.read(ws.ledger)
    ev = events[int(seq)]
    if ev["kind"] != "evaluate":
        raise SystemExit("#%s is not an evaluation" % seq)
    it = canon.load_intent(ev["intent"].encode("ascii"))
    held_head(ws, events)
    verdict, after, timings, out1, out0, _t, rec = evaluate_doc(ws, it, undo_of=inverse_of or None)
    new = append_evaluation(ws, ev["intent"], verdict, after, timings, rec, re_of=seq)
    print("candidate %s re-evaluated at the current head: %s %s (ledger #%s; it was %s at #%s)" % (
        it["candidate"], verdict["verdict"], ",".join(verdict["codes"]) or "-", new["seq"], ev["verdict"]["verdict"], seq))
    if out0 is not None:
        print("contact sheet: %s" % os.path.relpath(contact_sheet(ws, [(it, verdict, out0, out1, new["seq"], timings)]), ws.root))
    return new


def current_parts(ws):
    _o, parts, _c = ws.export()
    return parts


def admission_evidence(ws, events, it, still=None, despite=False, inverse_of="", accept_leakage=False):
    """(evidence, still bytes or None, inverse_ok): what an admission brings to its evaluation's record (ADMISSION-0).
    The still's detectors are read here, by the host, from the file's bytes; never taken from a page or a caller."""
    ev = {"accepted_leakage": bool(accept_leakage), "still_sha256": "", "detectors": {}, "despite_detectors": bool(despite), "inverse_of": str(inverse_of or "")}
    raw = None
    if still is not None:
        raw = still if isinstance(still, bytes) else open(still, "rb").read()
        ev["still_sha256"] = canon.sha256(raw)
        try:
            m, flags = quality.detect_png(raw)
            ev["detectors"] = quality.detector_fields(m, flags)
        except quality.QualityError as e:
            ev["detectors"] = {"not_checked": str(e)[:200]}
    ok = bool(ev["inverse_of"]) and inverse_of_ok(events, ev["inverse_of"], it, len(events))
    return ev, raw, ok


def cmd_record(ws, seq):
    """An evaluation's ADMISSION-0 record, as a person reads it."""
    events, _l, _h = led.read(ws.ledger)
    ev = events[int(seq)]
    if ev["kind"] != "evaluate":
        raise SystemExit("#%s is not an evaluation" % seq)
    r = ev.get("record")
    if r is None:
        print("#%s has no ADMISSION-0 record: it was evaluated before 0222. Evaluate it again to have one: python art/director.py reevaluate %s %s" % (seq, ws.brief, seq))
        return None
    it = canon.load_intent(ev["intent"].encode("ascii"))
    print("evaluation #%s: candidate %s, %s %s, rung %s" % (seq, it["candidate"], ev["verdict"]["verdict"], ",".join(ev["verdict"]["codes"]) or "-", r["rung"]))
    for title, k in (("why this rung (computed by the host from what changed)", "rung_basis"), ("certifies", "certifies"),
                     ("did not check", "not_checked"), ("an admission needs", "requires"), ("rests on", "trusted")):
        print("  %s:" % title)
        for x in r[k]:
            print("    - " + x)
    print("  horizon: %s ticks (%s)" % (r["horizon"]["ticks"], r["horizon"]["why"]))
    return r


def cmd_admit(ws, seq, accept_leakage=False, chooser="the owner", note="", still=None, despite=False, inverse_of="", region=None, gate=None):
    """Admit an evaluation. ADMISSION-0 (0222): its record must be complete and every item it requires present — for
    rung A a still of the candidate (a file, or its bytes), its detectors read here; a flagged one only with despite —
    or, for an undo, inverse_of naming the admission it is the exact inverse of. STRICT-0 (0238): `region`, from a
    strict request (art/studio.py), is refused unless its check passed, and is recorded with the admission: the shapes'
    sha256, the receipt (every box the change touches, each with the regions that hold it) and the inverse receipt.
    BINDING-0 (0253): `gate` is passed to the commit (commit_admission), the studio's binding check; the command line
    passes none (it is outside BINDING-0 version 0)."""
    region_refusal(seq, region)
    events, _l, _h = led.read(ws.ledger)
    ev = events[int(seq)]
    p = admit_checks(ws, events, ev, seq, accept_leakage, still, despite, inverse_of)
    head, it, evidence, still_bytes, files, parts1, inverse = (p[k] for k in ("head", "it", "evidence", "still_bytes", "files", "parts1", "inverse"))
    stills = [(os.path.join(ws.stills, evidence["still_sha256"] + ".png"), still_bytes)] if still_bytes is not None else []
    a = commit_admission(ws, seq, ev["intent_sha256"], files, {
        "evaluation": seq, "intent_sha256": ev["intent_sha256"], "head_before": head, "head_after": canon.head(parts1),
        "parts_after": parts1, "accepted_leakage": bool(accept_leakage), "inverse": inverse,
        "design_lines": list(it["layout"]), "evidence": evidence, "observed": {"at": now(), "chooser": chooser, "note": note},
        **({"region": region} if region is not None else {})}, stills, gate)
    det = evidence["detectors"]
    print("ADMITTED candidate %s (#%s) at head %s -> %s (ledger #%s; %s)" % (
        it["candidate"], seq, head[:12], canon.head(parts1)[:12], a["seq"],
        ("the exact inverse of #%s" % evidence["inverse_of"]) if evidence["inverse_of"] else
        "still %s, %s" % (evidence["still_sha256"][:12], ("despite the detectors: " + ", ".join(det.get("flags") or [det.get("not_checked", "")])) if evidence["despite_detectors"] else "the detectors flag nothing")))
    return a


def region_refusal(seq, region):
    """STRICT-0: a strict request's region that did not pass, or brings no receipt, is refused (cmd_admit's first check)."""
    if region is not None and region.get("strict") and not (region.get("ok") is True and "receipt" in region and "inverse_receipt" in region):
        raise SystemExit("REFUSED (ADMIT-OUTSIDE): #%s comes from a strict request whose check did not pass, or brings no receipt" % seq)


def admit_checks(ws, events, ev, seq, accept_leakage=False, still=None, despite=False, inverse_of=""):
    """The checks cmd_admit makes before it writes, in its order and with its refusals (SystemExit); returns what the
    commit goes on with. DASHBOARD-0 (0249): one predicate, run by cmd_admit on an evaluation the ledger holds and by
    admit_dry on one not yet appended, so that the studio's account of a candidate's admission (art/studio.py) is the
    director's own checks, never a second policy."""
    if ev["kind"] != "evaluate":
        raise SystemExit("REFUSED: #%s is not an evaluation" % seq)
    v = ev["verdict"]
    # 0254 (a review finding): the brief read once, and the head, the application and the stored inverse all taken from
    # those bytes. The commit's fence holds the files to this head and held_head the ledger to it, so the inverse stored is
    # the one replay recomputes over the text the ledger holds; read twice, a writer outside the content lock that changed
    # the brief between the reads and put it back before the fence would leave an inverse of other bytes, and a ledger that
    # replay refuses (LEDGER-INVERSE) for good. The race court's plant "admit-reads-twice" reads it again for the application
    text0 = ws.text()
    out0, cur, _c = ws.export(text0)
    head = canon.head(cur)
    if v["checked_against"] != head:
        try:
            undoes = any(x[:1] == "@" for x in canon.load_intent(ev["intent"].encode("ascii"))["revision"])
        except canon.IntentError:
            undoes = False
        raise SystemExit("REFUSED (HEAD-MOVED): #%s was checked against %s; the head is now %s. Re-evaluate it first: "
                         "python art/director.py reevaluate %s %s%s" % (seq, v["checked_against"][:12], head[:12], ws.brief, seq,
                                                                        (" --inverse-of %s" % inverse_of) if undoes and inverse_of else
                                                                        " --inverse-of N (N the admission it undoes)" if undoes else ""))
    if v["verdict"] == "REFUSED":
        raise SystemExit("REFUSED: #%s's verdict is REFUSED (%s); a refused candidate is never admitted" % (seq, ",".join(v["codes"])))
    if v["verdict"] == "LEAKAGE" and not accept_leakage:
        raise SystemExit("REFUSED: #%s leaks (%s); admit it only with --accept-leakage, which the ledger records" % (seq, ", ".join(v["unclaimed"][:6])))
    it = canon.load_intent(ev["intent"].encode("ascii"))
    evidence, still_bytes, inverse_ok = admission_evidence(ws, events, it, still, despite, inverse_of, accept_leakage)
    lack = contract.missing(ev.get("record"), v, evidence, inverse_ok)
    if lack:
        raise SystemExit("REFUSED (ADMISSION-0): #%s cannot be admitted yet: %s" % (seq, "; ".join(lack)))
    try:
        text1, inverse = apply_revision(ws.text() if durable.PLANT == "admit-reads-twice" else text0, it["revision"],
                                        undo=inverse_ok or INVERSE_PLANT == "admit-inverse-anywhere")
    except canon.IntentError as e:
        if e.code != "INTENT-INVERSE-ONLY":
            raise
        raise SystemExit("REFUSED (INTENT-INVERSE-ONLY): #%s's revision holds an inverse form, which only an undo of the admission that recorded "
                         "it applies: admit it with --inverse-of that admission; nothing was written" % seq)
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
    return {"out0": out0, "head": head, "it": it, "evidence": evidence, "still_bytes": still_bytes, "files": files, "parts1": parts1, "inverse": inverse}


def admit_dry(ws, events, fields, still=None, despite=False, region=None, inverse_of=""):
    """DASHBOARD-0 (0249): the refusal an admission of the evaluation `fields` (evaluation_fields(): what
    append_evaluation would append) would meet now, nothing written: append_evaluation's guard (held_head at the head it
    was checked against), cmd_admit's checks (region_refusal and admit_checks, the evaluation taken as the ledger's next
    event) and the commit's shared map, in that order. Raises as they raise (SystemExit, Refusal, LedgerError); returns
    None when none refuses. It is of the files and the ledger as read now, without the content lock: an admission is
    checked again under it (the commit's fence), and a writer that holds it (BUSY) is not foreseen. The shared map reads
    the other briefs of the tree, which the studio's revision does not watch; it cannot refuse a studio candidate, whose
    layout is always empty (art/studio.py intent_doc), and a layout candidate would need them in the revision."""
    held_head(ws, events, fields["verdict"]["checked_against"])
    seq = str(len(events))
    ev = dict(fields, kind="evaluate", seq=seq)
    region_refusal(seq, region)
    p = admit_checks(ws, events + [ev], ev, seq, still=still, despite=despite, inverse_of=inverse_of)
    shared_map(ws, p["out0"], p["files"])
    return None


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
    """Record a change made outside the loop (a hand edit, a new exporter) as the head. LEDGER-SAFE-0 (0245): the ledger
    read, replayed and appended to under the content lock, so that an admission cannot land between; and only for files
    that pass every art check (REBASE-CHECKS) and that the exporter takes (REBASE-EXPORT), the checks kept in the event.
    A rebase records a change; it never admits one that the checks refuse."""
    try:
        with durable.locked(led.lock_path(ws.ledger)):
            if os.path.exists(ws.pending):       # a dead writer's half-done admission, finished or undone before anything is read
                for ln in _recover(ws):
                    print(ln)
            events, _l, _h = led.read(ws.ledger)
            state = replay(ws, events)
            text = ws.text()
            try:
                out, parts, checks = ws.export(text)
            except (dress.ArtError, level.MapError) as e:
                raise Refusal("REBASE-EXPORT", "the exporter refuses %s as it stands (%s); nothing was appended" % (ws.brief, " ".join(str(e).split())[:200]))
            failed = [c["name"] for c in checks if not c["ok"]]
            if failed and SAFE_PLANT != "rebase-unchecked":
                raise Refusal("REBASE-CHECKS", "%s as it stands fails %d of the art checks (%s), so it is not recorded as the head; nothing was "
                                               "appended. Correct it, or restore it" % (ws.brief, len(failed), "; ".join(failed)[:240]))
            dname, dtext = ws.design(out)
            r = led.append(ws.ledger, "rebase", {"head_before": state["head"], "head_after": canon.head(parts), "parts_after": parts, "art_text": text,
                                                 "design_text": dtext or "", "checks": [{"name": c["name"], "ok": bool(c["ok"])} for c in checks],
                                                 "observed": {"at": now(), "note": note}})
    except durable.Busy:
        raise Refusal("BUSY", "another writer held this tree's content lock for the whole wait (%g s); nothing was appended" % durable.WAIT)
    print("rebased: %s -> %s (ledger #%s; %d art checks passed)" % (state["head"][:12], r["head_after"][:12], r["seq"], len(checks)))
    return r


def cmd_approve(ws, view, image, config, approver="the owner", note="", despite=False):
    """A person's acceptance of a still at the head, with QUALITY-0's detectors read on it (0221). A still the detectors
    flag, or could not read, is approved only with despite=True (--despite-detectors), which the ledger records: a
    detector proves nothing either way, so it cannot refuse, and it cannot be passed over in silence either."""
    out, parts, _c = ws.export()
    if view not in out["scene"]["views"]:
        raise SystemExit("no view %r in the scene" % view)
    raw = open(image, "rb").read()
    try:
        m, flags = quality.detect_png(raw)
        det, why = quality.detector_fields(m, flags), "; ".join(flags)
    except quality.QualityError as e:
        det, why = {"not_checked": str(e)[:200]}, "the detectors did not run: %s" % e
    if why and not despite:
        raise SystemExit("REFUSED: %s. A detector proves nothing, so the still can still be approved: with --despite-detectors, "
                         "which the ledger records" % why)
    a = append_checked(ws, "approve", {"view": view, "image_sha256": hashlib.sha256(raw).hexdigest(),
                                       "render_config": config, "head": canon.head(parts),
                                       "detectors": det, "despite_detectors": bool(why),
                                       "observed": {"at": now(), "approver": approver, "note": note}}, canon.head(parts))
    print("approved: view %s, image %s, at head %s (ledger #%s; provenance, not a reproducibility claim)%s" % (
        view, a["image_sha256"][:12], a["head"][:12], a["seq"], ("; despite the detectors: " + why) if why else "; the detectors flag nothing"))
    return a


# -------------------------------------------------------------------------------------------- verification
def replay(ws, events):
    """The ledger replayed from its genesis: the art text, the design text and the head after the last event.
    Refuses (raising LedgerError) any event that does not follow from the ones before it."""
    E = led.LedgerError
    g = events[0]
    st = {"art": g["art_text"], "design": g["design_text"], "parts": dict(g["parts"]), "head": g["head"]}
    inv_ok = False              # set afresh for every admit event below; carried over only under the plant replay-undo-carried
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
            # 0254: whether this admission undoes an earlier one, set afresh for every admit event (nothing carries over)
            if INVERSE_PLANT != "replay-undo-carried":
                inv_ok = False
            # ADMISSION-0 (0222): an evaluation with a record is admitted only with the evidence it requires; one from
            # before the record (a legacy admission) carries none, and an admission of one carries none either
            if "record" in src:
                evd = ev.get("evidence")
                if evd is None or bool(evd.get("accepted_leakage")) != bool(ev["accepted_leakage"]):
                    raise E("LEDGER-EVIDENCE: #%s admits a recorded evaluation without its evidence" % ev["seq"])
                i = evd.get("inverse_of", "")
                inv_ok = bool(i) and inverse_of_ok(events, i, it, int(ev["seq"]))
                lack = contract.missing(src["record"], src["verdict"], evd, inv_ok)
                if lack:
                    raise E("LEDGER-EVIDENCE: #%s admits #%s lacking %s" % (ev["seq"], ev["evaluation"], "; ".join(lack)))
            elif "evidence" in ev:
                raise E("LEDGER-EVIDENCE: #%s carries evidence for an evaluation that has no record" % ev["seq"])
            try:
                st["art"], _inv = apply_revision(st["art"], it["revision"], undo=inv_ok or INVERSE_PLANT == "replay-inverse-anywhere")
            except canon.IntentError as e:
                if e.code != "INTENT-INVERSE-ONLY":
                    raise
                raise E("LEDGER-INVERSE-ONLY: #%s applies an inverse form without being an undo of the admission that recorded it" % ev["seq"])
            # 0254: a stored inverse holding an '@' line is the one its revision records over the text it was admitted on
            # (one without, recorded before 0254 or a '- key' alone, is not compared: old ledgers replay as they are)
            stored = list(ev.get("inverse") or [])
            if (any(isinstance(x, str) and x[:1] == "@" for x in stored) or INVERSE_PLANT == "inverse-compared-always") and stored != list(_inv) \
                    and INVERSE_PLANT != "replay-inverse-unchecked":
                raise E("LEDGER-INVERSE: #%s's stored inverse is not the one its revision records over the text it was admitted on" % ev["seq"])
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
            # LEDGER-SAFE-0 (0245): the text a rebase records is the art its parts name, and its head is its parts'
            if canon.sha256(ev["art_text"].encode("utf-8")) != ev["parts_after"]["art_sha256"] or canon.head(ev["parts_after"]) != ev["head_after"]:
                raise E("LEDGER-REPLAY: #%s's text or head is not its own parts'" % ev["seq"])
            if any(not c.get("ok") for c in ev.get("checks", [])):
                raise E("LEDGER-REBASE: #%s records a head whose art checks failed" % ev["seq"])
            st["art"], st["design"] = ev["art_text"], ev["design_text"]
            st["parts"], st["head"] = dict(ev["parts_after"]), ev["head_after"]
        elif k == "refuse":
            if events[int(ev["evaluation"])]["kind"] != "evaluate":
                raise E("LEDGER-REFUSE: #%s refuses something that is not an evaluation" % ev["seq"])
        elif k == "approve":
            if ev["head"] != st["head"]:
                raise E("LEDGER-HEAD: #%s approves a still at another head" % ev["seq"])
    return st


def check_stills(ws, events, deep=True):
    """ADMISSION-0's evidence read back: every admission's still is on the disk with the bytes it names, and (deep) its
    detectors, read again from those bytes, are the ones recorded. Returns how many stills; raises LedgerError."""
    n = 0
    for ev in events:
        evd = ev.get("evidence") if ev["kind"] == "admit" else None
        if not evd or not evd.get("still_sha256"):
            continue
        p = os.path.join(ws.stills, evd["still_sha256"] + ".png")
        if not os.path.exists(p):
            raise led.LedgerError("LEDGER-STILL: #%s's still %s is not in %s: the evidence of that admission is gone" % (ev["seq"], evd["still_sha256"][:12], os.path.relpath(ws.stills, ws.root)))
        raw = open(p, "rb").read()
        if canon.sha256(raw) != evd["still_sha256"]:
            raise led.LedgerError("LEDGER-STILL: #%s's still is not the bytes it names" % ev["seq"])
        if deep:
            try:
                m, flags = quality.detect_png(raw)
                det = quality.detector_fields(m, flags)
            except quality.QualityError as e:
                det = {"not_checked": str(e)[:200]}
            if det != evd["detectors"]:
                raise led.LedgerError("LEDGER-STILL: #%s's detectors, read again from its still, are not the ones recorded" % ev["seq"])
        n += 1
    return n


def cmd_verify(ws, quiet=False, deep=True):
    """The ledger's chain, replayed to the files as they stand, and every admission's still (deep: its detectors read
    again). Deep by default: the command, and the launcher's look and /worlds.json (play.py's Hub.inspect) too; the
    import's commit checks the chain again not deep (corrected 0250: this said the launcher's look was not deep)."""
    events, head = led.chain(ws.ledger)
    st = replay(ws, events)
    stills = check_stills(ws, events, deep)
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
        print("LEDGER VERIFIED  %d events (%s), head %s; the files are the head %s; %d still%s, %s" % (
            len(events), ", ".join("%s %d" % kv for kv in sorted(kinds.items())), head[:12], st["head"][:12], stills,
            "" if stills == 1 else "s", "each the bytes it names, its detectors read again" if deep else "each the bytes it names"))
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
        lay_round(tmp)                                     # the checkout's briefs are not the test's: the round's base alone
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
        results += safe_rows(ws, rnd)

        # ADMISSION-0 (0222): every evaluation's record complete; an admission needs what its record requires
        events, _l, _h = led.read(ws.ledger)
        last_eval = [e for e in events if e["kind"] == "evaluate"][-1]
        r0 = last_eval.get("record") or {}
        results.append(("an evaluation carries its record: rung A from what changed, every expected check certified, what was not checked, what it rests on",
                        r0.get("rung") == "A" and all("check: " + n in r0.get("certifies", []) for n in contract.EXPECTED_CHECKS)
                        and all(x in r0.get("not_checked", []) for x in contract.NEVER_CHECKED) and len(r0.get("trusted", [])) == len(TRUSTED) + 1
                        and r0.get("horizon", {}).get("ticks") == "0",
                        "rung %s; %d certified, %d not checked, %d trusted" % (r0.get("rung"), len(r0.get("certifies", [])), len(r0.get("not_checked", [])), len(r0.get("trusted", [])))))
        # 0226: a mover is play. An intent that adds one is refused whatever its scope, and its record says the mover was
        # not played
        mdoc = {"base": {k: current_parts(ws)[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}, "brief": ws.brief, "candidate": "M",
                "format": "VERDANDI-INTENT", "layout": [], "prompt": "add a lift", "rationale": "a mover through an intent",
                "revision": ["+ mover selftest-lift concrete 40,0,30 42,0.25,32 along +y travel 2.25 speed 0.9375"], "scope": ["**", "material/concrete"],
                "version": "0"}
        vM, _aM, _tM, outM, _oM, _xM, recM = evaluate_doc(ws, canon.load_intent(canon.dumps(mdoc)))
        results.append(("an intent that adds a mover (play) is refused whatever it grants (SCOPE-PLAY); its record says the mover was not played",
                        vM["verdict"] == "REFUSED" and "SCOPE-PLAY" in vM["codes"] and "play/mover/selftest-lift" in vM["realized"] and outM is not None
                        and len(outM["scene"].get("movers", [])) == 1 and recM["horizon"]["why"].startswith("the scene's 1 mover")
                        and any(x.startswith("anything over time: the scene's 1 mover") for x in recM["not_checked"])
                        and "check: the rules: rules 3 hold the scene, its movers and their paths clear" in recM["certifies"],
                        "%s %s; realized %s" % (vM["verdict"], ",".join(vM["codes"]), ", ".join(vM["realized"])[:60])))
        adm = [e for e in events if e["kind"] == "admit" and not e["design_lines"]][-1]
        src = canon.load_intent(events[int(adm["evaluation"])]["intent"].encode("ascii"))
        inv_doc = {"base": {k: current_parts(ws)[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}, "brief": ws.brief, "candidate": "U",
                   "format": "VERDANDI-INTENT", "layout": [], "prompt": "undo: " + src["prompt"], "rationale": "the exact inverse of #%s" % adm["seq"],
                   "revision": list(adm["inverse"]), "scope": list(src["scope"]), "version": "0"}
        inv_path = os.path.join(tmp, "U.intent")
        with open(inv_path, "wb") as fh:
            fh.write(canon.dumps(inv_doc))
        su = cmd_evaluate(ws, [inv_path], quiet=True, inverse_of=adm["seq"])[0][4]
        n0 = len(led.read(ws.ledger)[0])
        for label, kw, want in (("without a still", {"still": None}, "no still of the candidate"),
                                ("said to undo an admission it is not the inverse of", {"still": None, "inverse_of": rb["seq"]}, "not that admission's exact inverse")):
            try:
                cmd_admit_quiet(ws, su, chooser="selftest", **kw)
                results.append(("an admission %s is refused" % label, False, "it was admitted"))
            except SystemExit as e:
                results.append(("an admission %s is refused (ADMISSION-0), nothing written" % label, "ADMISSION-0" in str(e) and want in str(e)
                                and len(led.read(ws.ledger)[0]) == n0, " ".join(str(e).split())[:110]))
        au = cmd_admit_quiet(ws, su, chooser="selftest", still=None, inverse_of=adm["seq"])
        results.append(("the exact inverse of an admission (an undo) is admitted without a still, naming it", au["evidence"]["inverse_of"] == adm["seq"]
                        and au["evidence"]["still_sha256"] == "", json.dumps(au["evidence"], sort_keys=True)[:110]))
        sc = cmd_reevaluate_quiet(ws, rc["seq"])["seq"]
        Wb, Hb = 32, 18
        white = quality.png_bytes(Wb, Hb, bytes(255 if (i // 3) % Wb < 24 else 40 + (i % 11) * 9 for i in range(Wb * Hb * 3)))
        n0 = len(led.read(ws.ledger)[0])
        try:
            cmd_admit_quiet(ws, sc, chooser="selftest", still=white)
            results.append(("a still the detectors flag is not admitted without despite", False, "it was admitted"))
        except SystemExit as e:
            results.append(("a still the detectors flag is not admitted without despite, nothing written", "flag" in str(e) and "BLOWN" in str(e)
                            and len(led.read(ws.ledger)[0]) == n0, " ".join(str(e).split())[:110]))
        ac = cmd_admit_quiet(ws, sc, chooser="selftest", still=white, despite=True)
        kept = os.path.join(ws.stills, ac["evidence"]["still_sha256"] + ".png")
        results.append(("  and with despite, admitted: the still kept by its sha256 beside the ledger, its detectors and the despite recorded",
                        os.path.exists(kept) and open(kept, "rb").read() == white and ac["evidence"]["despite_detectors"] is True
                        and "BLOWN" in ac["evidence"]["detectors"]["flags"], json.dumps(ac["evidence"]["detectors"].get("flags"))))
        try:
            cmd_verify(ws, quiet=True)
            results.append(("the ledger with its evidence verifies, each still read again", True, ""))
        except led.LedgerError as e:
            results.append(("the ledger with its evidence verifies", False, str(e)))
        # plants on the evidence: each must be refused by verify
        saved_led = open(ws.ledger, "rb").read()
        events, _l, _h = led.read(ws.ledger)
        forged = json.loads(json.dumps(events[-1]))
        forged["evidence"]["detectors"]["flags"] = []
        try:
            check_stills(ws, [forged])
            results.append(("plant: an admission whose recorded detectors are not its still's — refused", False, "not refused"))
        except led.LedgerError as e:
            results.append(("plant: an admission whose recorded detectors are not its still's — refused", "LEDGER-STILL" in str(e), str(e)[:100]))
        os.rename(kept, kept + ".gone")
        try:
            cmd_verify(ws, quiet=True)
            results.append(("plant: an admission's still taken away — refused", False, "verify passed"))
        except led.LedgerError as e:
            results.append(("plant: an admission's still taken away — refused", "LEDGER-STILL" in str(e), str(e)[:100]))
        os.rename(kept + ".gone", kept)
        ev_all = led.read(ws.ledger)[0]
        last_adm = [e for e in ev_all if e["kind"] == "admit"][-1]
        src2 = canon.load_intent(ev_all[int(last_adm["evaluation"])]["intent"].encode("ascii"))
        inv2 = dict(inv_doc, base={k: current_parts(ws)[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")},
                    revision=list(last_adm["inverse"]), scope=list(src2["scope"]), rationale="the exact inverse of #%s" % last_adm["seq"])
        with open(inv_path, "wb") as fh:
            fh.write(canon.dumps(inv2))
        sd = cmd_evaluate(ws, [inv_path], quiet=True, inverse_of=last_adm["seq"])[0][4]
        lid = len(led.read(ws.ledger)[0])
        led.append(ws.ledger, "admit", {"evaluation": sd, "intent_sha256": led.read(ws.ledger)[0][int(sd)]["intent_sha256"],
                                        "head_before": canon.head(current_parts(ws)), "head_after": "x",
                                        "parts_after": current_parts(ws), "accepted_leakage": False, "inverse": [], "design_lines": [],
                                        "observed": {"at": "2026-10-13T00:00:00Z", "chooser": "a forger", "note": ""}})
        try:
            replay(ws, led.read(ws.ledger)[0])
            results.append(("plant: an admit event written past the director, with no evidence — refused by replay", False, "replay passed"))
        except led.LedgerError as e:
            results.append(("plant: an admit event written past the director, with no evidence — refused by replay (#%d)" % lid,
                            "LEDGER-EVIDENCE" in str(e), str(e)[:100]))
        open(ws.ledger, "wb").write(saved_led)
        # the classifier: what it does with what an intent cannot make today, and with a skipped check
        v0 = dict(last_eval["verdict"], realized=["plaza/mover/3,4"], affected=[])
        rk, why = contract.classify(v0, True, {"plaza"})
        rec_c = contract.record(None, v0, [{"name": n, "ok": True} for n in contract.EXPECTED_CHECKS], [], True, {"plaza"})
        results.append(("an address of a kind the classifier does not know (plaza/mover/3,4) classifies C, and the director will not admit it",
                        rk == "C" and contract.missing(rec_c, v0, {"still_sha256": "x", "detectors": {"flags": []}})[0].startswith("rung C"), why[0][:100]))
        rk, why = contract.classify(dict(v0, codes=["ART-REFUSED"]), False, {"plaza"})
        results.append(("a candidate that did not export classifies D: unknown classifies at the top", rk == "D", why[0][:100]))
        skipped = [{"name": n, "ok": True} for n in contract.EXPECTED_CHECKS if not n.startswith("quality: every field")]
        rec_s = contract.record(None, last_eval["verdict"], skipped, [], True, set(ws.export()[0]["scene"]["regions"]))
        lack = contract.missing(rec_s, last_eval["verdict"], {"still_sha256": "x", "detectors": {"flags": []}})
        results.append(("a check that did not run is said (not checked) and keeps the admission out: a skip is not a pass",
                        any(x.startswith("did not run: quality: every field") for x in rec_s["not_checked"]) and any("not passed or not run" in x for x in lack),
                        "; ".join(lack)[:110]))
        rl = contract.record(None, dict(last_eval["verdict"], verdict="CLEAN"), [{"name": n, "ok": True} for n in contract.EXPECTED_CHECKS], [], True,
                             set(ws.export()[0]["scene"]["regions"]))
        results.append(("an evaluation from before the record (none) cannot be admitted: it is evaluated again",
                        contract.missing(None, last_eval["verdict"], {})[0].startswith("the evaluation has no ADMISSION-0 record")
                        and contract.missing(rl, dict(last_eval["verdict"], verdict="CLEAN"), {"still_sha256": "x", "detectors": {"flags": []}}) == [], ""))

        # QUALITY-0 (0221): a still approved with its detectors; a flagged or unread still only with --despite-detectors
        view = sorted(ws.export()[0]["scene"]["views"])[0]
        W_, H_ = 32, 18
        clean = bytes((x * 7 + y * 13 + c * 50) % 240 for y in range(H_) for x in range(W_) for c in range(3))
        blown = bytes(255 if (i // 3) % W_ < W_ * 2 // 3 else (i % 5) * 30 for i in range(W_ * H_ * 3))
        for label, pix in (("clean", clean), ("blown", blown)):
            with open(os.path.join(tmp, label + ".png"), "wb") as fh:
                fh.write(quality.png_bytes(W_, H_, pix))
        with open(os.path.join(tmp, "still.jpg"), "wb") as fh:
            fh.write(b"\xff\xd8\xff\xe0 not a png")
        a1 = _quiet(cmd_approve, ws, view, os.path.join(tmp, "clean.png"), "selftest")
        results.append(("a still the detectors do not flag is approved, its detectors in the ledger",
                        a1["detectors"].get("flags") == [] and a1["despite_detectors"] is False, json.dumps(a1["detectors"], sort_keys=True)[:100]))
        for label, f in (("a still mostly white", "blown.png"), ("a still the detectors cannot read", "still.jpg")):
            n0 = len(led.read(ws.ledger)[0])
            try:
                _quiet(cmd_approve, ws, view, os.path.join(tmp, f), "selftest")
                results.append(("%s is not approved without --despite-detectors" % label, False, "it was approved"))
            except SystemExit as e:
                results.append(("%s is not approved without --despite-detectors; nothing written" % label,
                                "--despite-detectors" in str(e) and len(led.read(ws.ledger)[0]) == n0, " ".join(str(e).split())[:100]))
            a2 = _quiet(cmd_approve, ws, view, os.path.join(tmp, f), "selftest", despite=True)
            results.append(("  and with it, approved and recorded as despite the detectors", a2["despite_detectors"] is True,
                            json.dumps(a2["detectors"], sort_keys=True)[:100]))
        try:
            cmd_verify(ws, quiet=True)
            results.append(("the ledger with its approvals verifies", True, ""))
        except led.LedgerError as e:
            results.append(("the ledger with its approvals verifies", False, str(e)))

        # fix 2 of the review of 2026-10-13: a second world on the same map. Its head must not move when the first world
        # admits: a layout change is refused (SHARED-MAP), an art change admitted; the plant shows what the refusal prevents
        root2 = os.path.join(tmp, "shared")
        lay_round(root2)
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
    # 0254: the frozen matrix's rows (art/director/inverse/0254-matrix.json, DIRECTOR SELFTEST, FZ1 to OU9), their
    # expectations read only through inverse_freeze.frozen(), run once honest and once per INVERSE_PLANT value
    import inverse_rows
    results += inverse_rows.director_rows(sys.modules[__name__])
    results += memo_rows()
    failed = 0
    for name, ok, d in results:
        print("%s %s%s" % ("PASS" if ok else "FAIL", name, (" — " + d) if d else ""))
        failed += 0 if ok else 1
    print("DIRECTOR SELFTEST %s" % ("PASSED" if not failed else "FAILED (%d)" % failed))
    return 0 if not failed else 1


def _safe_plant(p):
    global SAFE_PLANT
    SAFE_PLANT = p


def safe_rows(ws, rnd):
    """LEDGER-SAFE-0 (0245), in the self-test's tree at a head its ledger holds: no event over a head the ledger does not
    hold, and a rebase only of files that pass the checks; each refusal with nothing appended, and each guard's plant
    showing what it prevents. The tree is put back as it was after each case. [(name, ok, detail)]"""
    rows = []
    c_intent = os.path.join(rnd, "C.intent")
    saved_art, saved_led = open(ws.art, "rb").read(), open(ws.ledger, "rb").read()
    saved_maps = {f: open(os.path.join(ws.maps, f), "rb").read() for f in os.listdir(ws.maps) if os.path.isfile(os.path.join(ws.maps, f))}
    n_of = lambda: len(led.read(ws.ledger)[0])
    flat = lambda e: " ".join(str(e).split())[:110]

    def put_back():
        _safe_plant("")
        open(ws.art, "wb").write(saved_art)
        open(ws.ledger, "wb").write(saved_led)
        for f, b in saved_maps.items():
            open(os.path.join(ws.maps, f), "wb").write(b)

    def after(fns):
        """What verify, then rebase, say of the ledger: their codes, or 'passed'."""
        out = []
        for fn in fns:
            try:
                fn()
                out.append("passed")
            except (led.LedgerError, SystemExit) as e:
                out.append(getattr(e, "refusal", "") or str(e).split(":")[0])
        return out
    verify_then_rebase = (lambda: cmd_verify(ws, quiet=True), lambda: cmd_rebase_quiet(ws, "the repair"))
    try:
        # 1. an evaluation over a hand edit the ledger does not hold (the defect MEASURED on 2026-10-16)
        open(ws.art, "ab").write(b"# a hand edit, not recorded\n")
        n0 = n_of()
        try:
            cmd_evaluate(ws, [c_intent], quiet=True)
            rows.append(("an evaluation over a hand edit the ledger does not hold is refused (LEDGER-UNLOGGED)", False, "it was appended"))
        except Refusal as e:
            rows.append(("an evaluation over a hand edit the ledger does not hold is refused (LEDGER-UNLOGGED), nothing appended",
                         e.refusal == "LEDGER-UNLOGGED" and n_of() == n0 and "rebase" in str(e), flat(e)))
        _safe_plant("no-held-check")
        try:
            cmd_evaluate(ws, [c_intent], quiet=True)
            said = after(verify_then_rebase)
            rows.append(("plant: no held-head check, over a hand edit — the evaluation appended, and the ledger refused for good after", said == ["LEDGER-HEAD", "LEDGER-HEAD"],
                         "verify, then rebase: %s" % ", ".join(said)))
        except SystemExit as e:
            rows.append(("plant: no held-head check, over a hand edit — the evaluation appended", False, flat(e)))
        put_back()
        # 2. an evaluation made at a head the ledger then leaves before it is appended (the studio's admit, reject and undo
        # evaluate before they take the lock): here the ledger moves by a recorded change
        it_c = canon.load_intent(open(c_intent, "rb").read())
        v_c, a_c, t_c, _o1, _o0, _x, r_c = evaluate_doc(ws, it_c)
        open(ws.art, "ab").write(b"# meanwhile, a change recorded\n")
        cmd_rebase_quiet(ws, "meanwhile")
        n0 = n_of()
        try:
            append_evaluation(ws, open(c_intent, "rb").read(), v_c, a_c, t_c, r_c)
            rows.append(("an evaluation made at a head the ledger has since left is refused (HEAD-MOVED)", False, "it was appended"))
        except Refusal as e:
            rows.append(("an evaluation made at a head the ledger has since left is refused (HEAD-MOVED), nothing appended", e.refusal == "HEAD-MOVED" and n_of() == n0, flat(e)))
        _safe_plant("no-held-check")
        try:
            append_evaluation(ws, open(c_intent, "rb").read(), v_c, a_c, t_c, r_c)
            said = after(verify_then_rebase[:1])
            rows.append(("plant: no held-head check, a late evaluation — appended, and the ledger refused after", said == ["LEDGER-HEAD"], "verify: %s" % ", ".join(said)))
        except SystemExit as e:
            rows.append(("plant: no held-head check, a late evaluation — appended", False, flat(e)))
        put_back()
        # 3. an admission whose files are its head by a hand change back, the ledger holding another head
        stmt = " ".join([ln for ln in saved_art.decode("utf-8").split("\n") if ln.startswith("material ")][0].split("#", 1)[0].split())
        sdoc = {"base": {k: current_parts(ws)[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}, "brief": ws.brief, "candidate": "S",
                "format": "VERDANDI-INTENT", "layout": [], "prompt": "a material set as it is", "rationale": "LEDGER-SAFE-0's admission case",
                "revision": ["= " + stmt], "scope": ["material/" + stmt.split()[1]], "version": "0"}
        s_path = os.path.join(ws.root, "S.intent")
        with open(s_path, "wb") as fh:
            fh.write(canon.dumps(sdoc))
        s_row = cmd_evaluate(ws, [s_path], quiet=True)[0]
        sv = {"seq": s_row[4], "verdict": {"verdict": s_row[2]}}
        held_art, held_led = open(ws.art, "rb").read(), open(ws.ledger, "rb").read()
        open(ws.art, "ab").write(b"# a change recorded, then undone by hand\n")
        cmd_rebase_quiet(ws, "a change")
        open(ws.art, "wb").write(held_art)
        n0 = n_of()
        if sv["verdict"]["verdict"] != "CLEAN":
            rows.append(("an admission over a hand change back to its own head is refused (LEDGER-UNLOGGED)", False, "no CLEAN evaluation to admit: %s" % sv["verdict"]["verdict"]))
        else:
            try:
                cmd_admit_quiet(ws, sv["seq"], chooser="selftest")
                rows.append(("an admission over a hand change back to its own head is refused (LEDGER-UNLOGGED)", False, "it was admitted"))
            except Refusal as e:
                rows.append(("an admission over a hand change back to its own head is refused at the fence (LEDGER-UNLOGGED), nothing written",
                             e.refusal == "LEDGER-UNLOGGED" and n_of() == n0 and open(ws.art, "rb").read() == held_art and not os.path.exists(ws.pending), flat(e)))
            _safe_plant("no-held-check")
            try:
                cmd_admit_quiet(ws, sv["seq"], chooser="selftest")
                said = after(verify_then_rebase[:1])
                rows.append(("plant: no held-head check at the fence — the admission written, and the ledger refused after", said == ["LEDGER-STALE"], "verify: %s" % ", ".join(said)))
            except SystemExit as e:
                rows.append(("plant: no held-head check at the fence — the admission written", False, flat(e)))
        put_back()
        # 4. a rebase of files that fail an art check (the exporter takes them)
        open(ws.art, "ab").write(b"canopy plaza concrete 3.0\n")
        n0 = n_of()
        try:
            cmd_rebase_quiet(ws, "a canopy where a player can be")
            rows.append(("a rebase of files that fail an art check is refused (REBASE-CHECKS)", False, "it was recorded"))
        except Refusal as e:
            rows.append(("a rebase of files that fail an art check is refused (REBASE-CHECKS), nothing appended", e.refusal == "REBASE-CHECKS" and n_of() == n0, flat(e)))
        _safe_plant("rebase-unchecked")
        try:
            cmd_rebase_quiet(ws, "a canopy where a player can be")
            said = after(verify_then_rebase[:1])
            rows.append(("plant: a rebase unchecked — the failing files recorded as the head, and replay refuses them after", said == ["LEDGER-REBASE"], "verify: %s" % ", ".join(said)))
        except SystemExit as e:
            rows.append(("plant: a rebase unchecked — the failing files recorded", False, flat(e)))
        put_back()
        # 5. a rebase line written past the director, its text not the art its parts name
        events = led.read(ws.ledger)[0]
        st = replay(ws, events)
        led.append(ws.ledger, "rebase", {"head_before": st["head"], "head_after": st["head"], "parts_after": st["parts"],
                                         "art_text": st["art"] + "# not the art its parts name\n", "design_text": st["design"],
                                         "observed": {"at": "2026-10-16T00:00:00Z", "note": "a forger"}})
        try:
            replay(ws, led.read(ws.ledger)[0])
            rows.append(("plant: a rebase event written past the director, its text not its parts' — refused by replay", False, "replay passed"))
        except led.LedgerError as e:
            rows.append(("plant: a rebase event written past the director, its text not its parts' — refused by replay", "LEDGER-REPLAY" in str(e), flat(e)))
        put_back()
    finally:
        put_back()
    return rows


MEMO_PLANTS = ("memo-shares", "memo-no-validate", "memo-key-text", "memo-keeps-writes")


def memo_rows(plant=""):
    """THROUGHPUT-0 (0236): the export memo held to the export itself. Each row compares what the memo gives with the export
    computed with the memo off (the oracle), in a scratch copy of the fixture's world; then each of the memo's four
    plants is set in turn and must fail a row. [(name, ok, detail)]."""
    tmp = tempfile.mkdtemp(prefix="memo-selftest-")
    saved, rows = dict(MEMO), []
    try:
        ws = selftest_tree(tmp)
        oracle = lambda text=None: (MEMO.update(on=False), ws.export(text), MEMO.update(on=True))[1]
        MEMO.update(on=True, plant=plant)
        memo_clear()
        ref = oracle()
        r1, r2 = ws.export(), ws.export()
        rows.append(("memo: a result used again is the result computed again", r1 == ref and r2 == ref and MEMO_STATS["hit"] == 1 and MEMO_STATS["miss"] == 1,
                     "one miss, then one hit equal to the export computed with the memo off (%s)" % dict(MEMO_STATS)))
        r2[0]["scene"]["visuals"].clear()
        r2[1]["art_sha256"] = "0" * 64
        r2[2].append({"name": "planted", "ok": False})
        r3 = ws.export()
        rows.append(("memo: a caller that changes what it was given changes nothing another is given", r3 == ref,
                     "the scene's visuals cleared, the head's art sha256 and the checks changed in one copy; the next is the oracle's"))
        entry = next(iter(_memo.values()))
        want = [os.path.join(HERE, "dress.py"), os.path.join(REPO, "graybox", "level.py"), os.path.join(REPO, "graybox", "web", "sim.js"),
                os.path.join(REPO, "graybox", "tick_ref.py"), os.path.join(ws.maps, "tactical.gbx"), os.path.join(ws.maps, "tactical.layout")]
        lack = [os.path.relpath(w_, tmp if w_.startswith(tmp) else REPO) for w_ in want if os.path.realpath(w_) not in entry[0]]
        rows.append(("memo: every file the export read is recorded", not lack,
                     "%d files, %d listings, %d absent; the exporter, the converter, sim.js, tick_ref.py, the map and its layout among them%s"
                     % (len(entry[0]), len(entry[1]), len(entry[2]), (": MISSING " + ", ".join(lack)) if lack else "")))
        text2 = ws.text() + "material memo_test 1,2,3 0.5 0.0\n"
        r4 = ws.export(text2)
        rows.append(("memo: another text is another result", r4 == oracle(text2) and r4 != ref, "a material appended: the oracle's result, not the base's"))
        gbx = os.path.join(ws.maps, "tactical.gbx")
        with open(gbx, "ab") as fh:
            fh.write(b"# a byte the memo must see\n")
        r5, ref5 = ws.export(), oracle()
        rows.append(("memo: a byte changed in the maps folder is a miss", r5 == ref5 and r5 != ref and MEMO_STATS["stale"] >= 1,
                     "a comment appended to the map: the map's sha256 in the world moves, and the memo computes again (%s)" % dict(MEMO_STATS)))
        f = os.path.join(tmp, "written.txt")
        n0 = MEMO_STATS["not kept"]
        memo_call(("memo-write",), lambda: open(f, "w").write("x"))
        memo_call(("memo-write",), lambda: open(f, "w").write("x"))
        rows.append(("memo: an export that writes a file is not kept", MEMO_STATS["not kept"] - n0 == 2, "twice, computed twice"))
        g = os.path.join(tmp, "read.txt")
        open(g, "w").write("before")

        def read_then_changed():
            v = open(g).read()
            t = threading.Thread(target=lambda: (time.sleep(0.01), open(g, "w").write("after, and longer")))
            t.start()
            t.join()
            return v
        n0 = MEMO_STATS["not kept"]
        memo_call(("memo-race",), read_then_changed)
        again = memo_call(("memo-race",), read_then_changed)
        rows.append(("memo: a file written while the export read it is not kept", MEMO_STATS["not kept"] - n0 == 2 and again == "after, and longer",
                     "another thread wrote it during the computation: its stat moved, so the result was not kept"))
        gone = os.path.join(tmp, "absent.txt")

        def try_read():
            try:
                return open(gone).read()
            except OSError:
                return "absent"
        a1 = memo_call(("memo-absent",), try_read)
        open(gone, "w").write("present")
        a2 = memo_call(("memo-absent",), try_read)
        rows.append(("memo: a path the export did not find must stay absent", a1 == "absent" and a2 == "present", "%s, then %s" % (a1, a2)))
        durable.PLANT, n0 = "no-fence", MEMO_STATS["off"]
        try:
            ws.export()
            ws.export()
        finally:
            durable.PLANT = os.environ.get("VERDANDI_PLANT", "")
        rows.append(("memo: off while a plant of the director is set", MEMO_STATS["off"] - n0 == 2, "two exports under the plant no-fence, both computed"))
    finally:
        MEMO.clear()
        MEMO.update(saved)
        memo_clear()
        shutil.rmtree(tmp, ignore_errors=True)
    if plant:
        return rows
    for p_ in MEMO_PLANTS:
        caught = [n for n, ok, _d in memo_rows(p_) if not ok]
        rows.append(("memo plant %s caught" % p_, bool(caught), ("by: " + "; ".join(c[6:] for c in caught)) if caught else "NOT CAUGHT"))
    return rows


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
        if args and args[0] == "admit":
            args = args + ["--still", selftest_still_file(tmp)]
        r = subprocess.run([sys.executable, me] + args + ["--root", tmp], capture_output=True, text=True, env=env, timeout=600)
        return r.returncode, r.stdout + r.stderr
    try:
        lay_round(tmp)                                     # the checkout's briefs are not the test's: the round's base alone
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
        points = (["admit:stills"] + ["pending:file-%d" % n for n in range(k)] + ["pending:manifest", "torn:admit", "ledger:admit"]
                  + ["install:file-%d" % n for n in range(k)] + ["pending:manifest-removed"])
        for point in points:
            restore()
            want = "parent" if point.startswith(("pending:file", "pending:manifest")) and point != "pending:manifest-removed" or point in ("torn:admit", "admit:stills") else "child"
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
        if args and args[0] == "admit":
            args = args + ["--still", selftest_still_file(tmp)]
        r = subprocess.run([sys.executable, "-B", me] + args + ["--root", tmp], capture_output=True, text=True,
                           env=dict(env0, **env), timeout=600)
        return r.returncode, r.stdout + r.stderr
    try:
        lay_round(tmp)                                     # the checkout's briefs are not the test's: the round's base alone
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
            # the two threads start together and switch finely, and under the plant their exports meet (_export, PLANT_MEET):
            # both folders pointed at before either reads, and both read before either is put back, so that both are inside
            # the window whatever else the machine runs (with chance alone the race was missed: 0 of 40 once at 0239, under
            # two suites at once; again at 0241 after the 0239 repair; and at 0246 after 0241's 20 ms window: OBSERVED).
            # The memo off for both trials, and every export counted (0246): with it on, both keys were kept just above and
            # the honest trial's 40 exports were 40 kept results, so the lock it pairs with the plant was never what it held,
            # from 0236 to 0246. Now the trials differ only by the plant: the lock taken away, and the two exports made to
            # meet in the window it leaves open (the honest trial has no meeting, so its pass alone does not show the lock
            # is needed; the plant's row does).
            wrong, refused, done, done_lock = [0], [0], [0], threading.Lock()
            gate, si, maps0, memo0 = threading.Barrier(2), sys.getswitchinterval(), level.MAPS, MEMO["on"]
            real = ws._export

            def counted(text, maps):
                with done_lock:
                    done[0] += 1
                return real(text, maps)
            durable.PLANT, MEMO["on"], ws._export = plant, False, counted
            sys.setswitchinterval(1e-5)

            def one(maps, want):
                gate.wait()
                for _i in range(n):
                    try:
                        bad, refusal = ws.export(None, maps)[1] != want, 0
                    except Exception:                    # noqa: BLE001 — refused: the layout read again is not what the converter read
                        bad, refusal = True, 1
                    with done_lock:                      # 0246: two threads add to one count; without a lock an addition was lost
                        wrong[0] += bad
                        refused[0] += refusal
            try:
                th = [threading.Thread(target=one, args=(None, base_parts)), threading.Thread(target=one, args=(maps_b, b_parts))]
                for t in th:
                    t.start()
                for t in th:
                    t.join()
            finally:
                durable.PLANT, MEMO["on"] = saved_plant, memo0
                del ws._export
                sys.setswitchinterval(si)
                level.MAPS = maps0          # the plant's crossed restores leave the global wherever the last one put it
            return wrong[0], refused[0], done[0]
        (e0, _r0, d0), (e1, r1, d1) = export_trials(""), export_trials("no-export-lock")
        shutil.rmtree(maps_b, ignore_errors=True)
        res("two threads export at once, over the brief's maps and over a candidate's: every head right (40 exports, each computed under the lock)",
            e0 == 0 and d0 == 40, "%d wrong; %d computed" % (e0, d0))
        res("plant: no export lock — an export reads the other's maps", e1 > 0 and d1 == 40, "%d of 40 wrong or failed (%d refused); %d computed" % (e1, r1, d1))

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
            cmd_admit_still(ws, seq_b, chooser="racetest")
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
                    cmd_admit_still(ws, seq_a, chooser="racetest-second")
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
                    cmd_admit_still(ws, seq_b, chooser="racetest")
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
                    cmd_admit_still(ws, seq_b, chooser="racetest")
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
                cmd_admit_still(ws, seq_a, chooser="racetest")
            outcome = "admitted"
        except SystemExit as e:
            outcome = "refused: %s" % e
        res("an orphan pending folder (its writer killed) met by the next admission: undone under the lock, then A admitted",
            rc == durable.CRASH_EXIT and orphan and outcome == "admitted" and where() == ("A", 1, "admit") and not os.path.isdir(ws.pending)
            and "RECOVERED" in sink.getvalue() and verified(), "the killed writer %d; %s; %s" % (rc, outcome, " ".join(
                ln for ln in sink.getvalue().splitlines() if ln.startswith("RECOVERED"))[:110]))

        # 7. 0254 (a review finding): an editor's save of the brief (a writer outside the content lock) between the
        # admission's read of it and the commit, put back before the fence. The fence and held_head pass (the files and the
        # ledger are at the head again), so the admit event is written; its stored inverse must be the one replay
        # recomputes over the text the ledger holds, or every later evaluation, admission, rebase and undo is refused
        # LEDGER-INVERSE for good. The save changes only spacing in the row a '-' deletes, so the child is the same
        for plant in ("", "admit-reads-twice"):
            rt = os.path.join(tmp, "inverse-race-%s" % (plant or "honest"))
            with contextlib.redirect_stdout(io.StringIO()):
                wsr = selftest_tree(rt)
            p0 = current_parts(wsr)
            fi = os.path.join(rt, "A.intent")
            with open(fi, "wb") as fh:
                fh.write(canon.dumps({"base": {k: p0[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}, "brief": wsr.brief,
                                      "candidate": "A", "format": "VERDANDI-INTENT", "layout": [], "prompt": "the race court's",
                                      "rationale": "a '-' whose row an editor respaces", "revision": ["- lamp north-lane"], "scope": ["**"],
                                      "version": "0"}))
            seq_r = _quiet(cmd_evaluate, wsr, [fi], quiet=True)[0][4]
            t1 = open(wsr.art, "rb").read()
            t2 = t1.replace(b"lamp north-lane 255,170,90 600 4\n", b"lamp north-lane  255,170,90 600 4\n")
            st = {"saved": False, "reverted": False}
            text_of = wsr.text

            def text_hook(text_of=text_of, st=st, wsr=wsr, t2=t2):
                t = text_of()
                if not st["saved"] and sys._getframe(1).f_code.co_name == "admit_checks":
                    with open(wsr.art, "wb") as fh:    # the editor saves after the admission's read
                        fh.write(t2)
                    st["saved"] = True
                return t

            def put_back(name, st=st, wsr=wsr, t1=t1):
                if name == "admit:lock-wait" and st["saved"] and not st["reverted"]:
                    with open(wsr.art, "wb") as fh:    # and saves it back before the commit's fence
                        fh.write(t1)
                    st["reverted"] = True
            wsr.text, durable.HOOK, durable.PLANT = text_hook, put_back, plant
            try:
                a = _quiet(cmd_admit_still, wsr, seq_r, chooser="racetest")
                outcome = "admitted #%s" % a["seq"]
            except SystemExit as e:
                outcome = "refused: %s" % str(e)[:80]
            finally:
                wsr.text, durable.HOOK, durable.PLANT = text_of, None, saved_plant
            try:
                _quiet(cmd_verify, wsr)
                ver = "verify passes"
            except (led.LedgerError, SystemExit) as e:
                ver = "verify: %s" % str(e)[:90]
            fired = st["saved"] and st["reverted"] and t2 != t1
            if not plant:
                res("an editor's save between the admission's read of the brief and its commit, put back before the fence: the "
                    "admission's stored inverse the one replay recomputes (the brief read once)", fired and ver == "verify passes",
                    "%s; %s" % (outcome, ver))
            else:
                res("plant: the admission reads the brief twice — its stored inverse is of other bytes than the head, and replay "
                    "refuses the ledger LEDGER-INVERSE for good", fired and outcome.startswith("admitted") and "LEDGER-INVERSE" in ver,
                    "%s; %s" % (outcome, ver))
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


def selftest_still():
    """The still the self-tests' admissions bring (ADMISSION-0): synthetic, and the detectors flag nothing. It is not a
    picture of the candidate, which these tests never draw: they test the admission's mechanism, not a look."""
    w, h = 32, 18
    return quality.png_bytes(w, h, bytes((x * 7 + y * 13 + c * 50) % 240 for y in range(h) for x in range(w) for c in range(3)))


def selftest_admission(ws, seq, inverse=None, still=None, inverse_of="", undo=False, apply=True, chooser="a self-test", note=""):
    """A self-test's admission of evaluation #seq written by the director's own writer (commit_admission) past
    admit_checks: its revision applied with `undo` as given (or, apply False, the files left as they are), and the event's
    stored inverse `inverse` verbatim, or the one that application records. Its evidence (a still, inverse_of) is
    admission_evidence's, and carried only when the evaluation has a record. OPEN-2(a), his ruling ("Ruling: Option (a) —
    Freeze a pre-0254 verification fixture, then append a clean `5a` row."): a pre-0254 admission is written this way, its
    inverse verbatim from the 0254 freeze's legacy-inverses (7dee210's own records); 0254's rows write this way past the
    director's checks to show replay refusing what they let through. Self-tests only: no command and no route calls it."""
    events, _l, _h = led.read(ws.ledger)
    ev = events[int(seq)]
    it = canon.load_intent(ev["intent"].encode("ascii"))
    evidence, still_bytes, _ok = admission_evidence(ws, events, it, still, False, inverse_of)
    text0 = ws.text()
    text1, inv = apply_revision(text0, it["revision"], undo=undo) if apply else (text0, [])
    _o1, parts1, _c1 = ws.export(text1)
    head = canon.head(ws.export(text0)[1])      # the head of the bytes applied, as admit_checks (read once)
    stills = [(os.path.join(ws.stills, evidence["still_sha256"] + ".png"), still_bytes)] if still_bytes is not None and "record" in ev else []
    files = [(ws.art, text1.encode("utf-8"))] if open(ws.art, "rb").read() != text1.encode("utf-8") else []
    fields = {"evaluation": str(seq), "intent_sha256": ev["intent_sha256"], "head_before": head, "head_after": canon.head(parts1),
              "parts_after": parts1, "accepted_leakage": False, "inverse": list(inv if inverse is None else inverse), "design_lines": [],
              "observed": {"at": now(), "chooser": chooser, "note": note}}
    if "record" in ev:
        fields["evidence"] = evidence
    return _quiet(commit_admission, ws, str(seq), ev["intent_sha256"], files, fields, stills)


def selftest_still_file(root):
    p = os.path.join(root, "selftest-still.png")
    if not os.path.exists(p):
        with open(p, "wb") as fh:
            fh.write(selftest_still())
    return p


cmd_genesis_quiet = lambda ws: _quiet(cmd_genesis, ws)
cmd_admit_quiet = lambda ws, s, **k: _quiet(cmd_admit, ws, s, **dict({"still": selftest_still()}, **k))
cmd_admit_still = lambda ws, s, **k: cmd_admit(ws, s, **dict({"still": selftest_still()}, **k))
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
    flags = ("--accept-leakage", "--despite-detectors")
    valued = ("--chooser", "--note", "--config", "--approver", "--root", "--still", "--inverse-of")
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
        if cmd == "memotest":
            rows = memo_rows()
            for name, ok, d in rows:
                print("%s %s%s" % ("PASS" if ok else "FAIL", name, (" — " + d) if d else ""))
            bad = sum(1 for _n, ok, _d in rows if not ok)
            print("MEMO SELFTEST %s" % ("PASSED" if not bad else "FAILED (%d)" % bad))
            return 0 if not bad else 1
        ws = Workspace(pos[0], os.path.abspath(opt(args, "--root", REPO)))
        say_recovered(ws)
        if cmd == "genesis":
            cmd_genesis(ws)
        elif cmd == "lens":
            cmd_lens(ws, pos[1])
        elif cmd == "evaluate":
            cmd_evaluate(ws, pos[1:], inverse_of=opt(args, "--inverse-of", ""))
        elif cmd == "reevaluate":
            cmd_reevaluate(ws, pos[1], inverse_of=opt(args, "--inverse-of", ""))
        elif cmd == "record":
            cmd_record(ws, pos[1])
        elif cmd == "admit":
            cmd_admit(ws, pos[1], "--accept-leakage" in args, opt(args, "--chooser", "the owner"), opt(args, "--note", ""),
                      still=opt(args, "--still"), despite="--despite-detectors" in args, inverse_of=opt(args, "--inverse-of", ""))
        elif cmd == "refuse":
            cmd_refuse(ws, pos[1], opt(args, "--chooser", "the owner"), opt(args, "--note", ""))
        elif cmd == "rebase":
            cmd_rebase(ws, opt(args, "--note", ""))
        elif cmd == "approve":
            cmd_approve(ws, pos[1], pos[2], opt(args, "--config", ""), opt(args, "--approver", "the owner"), opt(args, "--note", ""),
                        despite="--despite-detectors" in args)
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
