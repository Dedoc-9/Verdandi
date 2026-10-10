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
#
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
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("art_check", os.path.join(HERE, "check.py"))
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)
import intent as canon  # noqa: E402
import scope as scopemod  # noqa: E402
import ledger as led  # noqa: E402

level = dress.level


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

    def text(self):
        return open(self.art, "rb").read().replace(b"\r\n", b"\n").decode("utf-8")

    def export(self, text=None, maps=None):
        """The scene of an art text over a maps folder, with the parts of its head and its checks' results."""
        text = self.text() if text is None else text
        maps = maps or self.maps
        A = dress.parse(text, self.brief + ".art")
        A["name"], A["sha256"] = self.brief, canon.sha256(text.encode("utf-8"))
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


# -------------------------------------------------------------------------------------------- evaluation
def refused(it, current, code, detail):
    v = {"protocol": scopemod.PROTOCOL, "version": scopemod.VERSION, "verdict": "REFUSED", "codes": [code],
         "intent_sha256": canon.sha256(canon.dumps(it)), "written_against": canon.head(it["base"]), "checked_against": canon.head(current),
         "re_evaluated": canon.head(it["base"]) != canon.head(current), "declared": sorted(it["scope"]), "realized": [], "affected": [],
         "unclaimed": [], "phantom": [], "cells_changed": [], "materials_changed": [], "failed_checks": [], "detail": detail}
    return v


def evaluate_doc(ws, it, re_of=""):
    """One intent at the current head: its verdict, the head after it, and the stage timings."""
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
    if it["layout"]:
        dname, _d = ws.design(out0)
        maps, new_design, lhead = with_layout(ws, out0, it["layout"], layout_label(it))
        try:
            for f in (dname, out0["W"]["source"]["layout"]):
                shutil.copy(os.path.join(maps, f), os.path.join(ws.maps, f))
        finally:
            shutil.rmtree(maps, ignore_errors=True)
    with open(ws.art, "wb") as fh:
        fh.write(text1.encode("utf-8"))
    _o1, parts1, _c1 = ws.export()
    if parts1["art_sha256"] != ev["after"]["art_sha256"] or parts1["world_sha256"] != ev["after"]["world_sha256"]:
        raise SystemExit("the admitted files do not reach the head the evaluation predicted: stop and read the ledger")
    a = led.append(ws.ledger, "admit", {"evaluation": seq, "intent_sha256": ev["intent_sha256"], "head_before": head, "head_after": canon.head(parts1),
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
        for sub in ("art/briefs", "art/rounds", "graybox/maps"):
            shutil.copytree(os.path.join(REPO, sub), os.path.join(tmp, sub))
        ws = Workspace("plaza-night", tmp)
        rnd = os.path.join(tmp, "art", "rounds", "plaza-imposing")
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
        rc = cmd_reevaluate_quiet(ws, seqs["C"])
        results.append(("C, re-evaluated at the new head, is a new event naming the old (CLEAN, HEAD-MOVED)",
                        rc["verdict"]["verdict"] == "CLEAN" and "HEAD-MOVED" in rc["verdict"]["codes"] and rc["re_evaluation_of"] == seqs["C"], ",".join(rc["verdict"]["codes"])))
        events, _l, _h = led.read(ws.ledger)
        results.append(("the earlier evaluation of C is kept as it was", events[int(seqs["C"])]["verdict"]["re_evaluated"] is False, ""))
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
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = 0
    for name, ok, d in results:
        print("%s %s%s" % ("PASS" if ok else "FAIL", name, (" — " + d) if d else ""))
        failed += 0 if ok else 1
    print("DIRECTOR SELFTEST %s" % ("PASSED" if not failed else "FAILED (%d)" % failed))
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
    valued = ("--chooser", "--note", "--config", "--approver")
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
        ws = Workspace(pos[0])
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
