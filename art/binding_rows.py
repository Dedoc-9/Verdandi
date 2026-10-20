# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/binding_rows.py — BINDING-0 (0253): STUDIO's rows of the frozen test matrix.
#
#   (run by STUDIO: python art/studio.py selftest, which runs art/play.py's studio_selftest; never by PAGE-CARDS)
#
# BINDING-0 version 0 (art/director/bindings/BINDING-0.v0.json, registered in 0252) is enforced from 0253 by the host's
# binding check (art/studio.py). Its test matrix and its conformance vectors were frozen before the check was built
# (0253-matrix.json and 0253-vectors.json, each held to its sha256 in frozen-0253.jsonl); every row here prints the
# exact name the frozen matrix gives it, and reads what the row must observe from the matrix itself: the answer, the
# director's code, the ledger's delta, the brief, the certificate, the decision record (its symbols replaced by this
# run's own values) and the field the answer names. Nothing here redefines a match: the conformance rows hold the host's
# pure functions to the frozen vectors, and every live row is held to the matrix.
#
# BIND-CAUSAL-0 (his ruling, 2026-10-18: "With enforcement removed, the motivating wrong-scene admission must reproduce.
# With enforcement restored, the same case must refuse for the binding-specific reason. A positive-only plant proves
# execution, not causality."): a state is built once in a tree of its own, the tree copied byte for byte, a Live and a
# Gateway started on each copy (the request restored, the same still posted), the host's own readings required equal
# across the copies before either press, and the same press made with the binding check removed in one copy and in
# force in the other.
#
# The values the matrix marks "per today" (an existing refusal's ledger delta, a code or a certificate of 1381b31's
# behaviour) were measured on 1381b31, the tree before 0253, and are held equal here (TODAY). Every plant row's name
# begins "BINDING plant: " (R5, tools/rung.py, reads it as a planted defect); no other row printed here contains that
# word, and a plant row is caught only where its honest twin answers as the matrix says. The matrix's M21, M22 and M25
# are measurements of the delivery, not rows; for M25 (v0 acceptance 4) each decision record the matrix lists is printed
# beside its case, "BINDING-0 RECORD <row> (<case>) sha256 <hex> <bytes>" (v0 decision record.self-test), for two runs
# to be compared. Standard library only; writes only in a scratch folder of its own.

import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

BRIEF = "plaza-night"
PIECE = "canopy:19,10-28,11"
CAM = {"x": 40.0, "y": 1.62, "z": 30.0, "yaw_deg": 0.0, "pitch_deg": 12.0}
BINDINGS = os.path.join(HERE, "director", "bindings")
FROZEN = "frozen-0253.jsonl"
CONSTANT = ("contract", "version", "sha256")

# What 1381b31 answers in the states the matrix marks "per today" or "as today" (MEASURED on the owner's machine by the
# agent, 2026-10-19, in a clone of 1381b31 with this file's own state builders and presses, case_outside,
# case_undo_unlogged, case_kept_removed and case_undo_bound: the same answers on the 0253 tree), held equal here: the
# ledger's delta of B4-OUTSIDE and of ADMIT-OUTSIDE (each +0: the strict check refuses before the evaluation is
# appended), of B4-UNDO-UNLOGGED (+0: append_evaluation's guard refuses LEDGER-UNLOGGED), M24's answer and delta
# (STUDIO-FAILED, FileNotFoundError, +0), and the certificates an undo through the host writes (one, the undo's own).
TODAY = {"B4-OUTSIDE ledger": 0, "ADMIT-OUTSIDE ledger": 0, "B4-UNDO-UNLOGGED ledger": 0, "M24 answer": "STUDIO-FAILED", "M24 ledger": 0,
         "undo certificates": 1}
# M12's B4-FLAGGED under binding-sufficient: the director's own code for a flagged still not admitted despite (MEASURED
# on the 0253 tree, the same day: STUDIO-DIRECTOR-REFUSED, ADMISSION-0, +1)
M12_FLAGGED_DIRECTOR = "ADMISSION-0"
TRIES = 12                  # the requests a preview's state asks at most for one with a camera path (States.previewed)


def sha256(b):
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------------------------------------ the frozen files
def frozen():
    """The frozen matrix and vectors, each held to the sha256 its line in frozen-0253.jsonl records: (matrix, vectors,
    problems). A file that is not its recorded bytes is a problem, and every row read from it then fails."""
    problems, docs = [], {}
    try:
        lines = [json.loads(x) for x in open(os.path.join(BINDINGS, FROZEN), "rb").read().decode("ascii").splitlines() if x.strip()]
    except (OSError, ValueError) as e:
        return {}, {}, ["%s does not read: %s" % (FROZEN, e)]
    for ln in lines:
        try:
            raw = open(os.path.join(BINDINGS, ln["file"]), "rb").read()
        except OSError as e:
            problems.append("%s: %s" % (ln.get("file"), e))
            continue
        if sha256(raw) != ln.get("sha256") or ln.get("status") != "frozen":
            problems.append("%s is not the bytes frozen-0253.jsonl records (%s, not %s)" % (ln["file"], sha256(raw)[:12], str(ln.get("sha256"))[:12]))
        docs[ln.get("of")] = json.loads(raw.decode("utf-8"))
    return docs.get("matrix", {}), docs.get("vectors", {}), problems


def register_v0():
    """The register's version-0 line of BINDING-0 (art/director/bindings/register.jsonl), or None."""
    try:
        for x in open(os.path.join(BINDINGS, "register.jsonl"), "rb").read().decode("ascii").splitlines():
            r = json.loads(x)
            if r.get("contract") == "BINDING-0" and r.get("version") == 0:
                return r
    except (OSError, ValueError):
        return None
    return None


# ------------------------------------------------------------------------------------------------ a world on a tree
class World:
    """One tree, its Live, its server and its gateway (the scripted provider unless another is named)."""

    def __init__(self, P, root, cfg, watch=False):
        self.P, self.root = P, root
        P.ROOT = root
        # the tree's own brief (a Live given no art file compiles the checkout's: art/dress.py BRIEFS)
        self.live = P.Live(BRIEF, os.path.join(root, "art", "briefs", BRIEF + ".art"), [], poll=0.15, root=root)
        self.srv = P.server(self.live)
        self.port = self.srv.server_address[1]
        self.base = "http://127.0.0.1:%d" % self.port
        self.tok = self.live.token
        if watch:
            threading.Thread(target=self.live.watch, kwargs={"say": lambda s: None}, daemon=True).start()
        self.g = P.start_studio(self.live, cfg, say=lambda s: None)
        self.art = os.path.join(root, "art", "briefs", BRIEF + ".art")
        self.ledger = os.path.join(root, "art", "ledger", BRIEF + ".ledger")
        self.records = os.path.join(root, "art", "build", "studio", BRIEF)
        self.certs = os.path.join(self.records, "certificates")
        self.log = os.path.join(self.records, "requests.jsonl")

    def ws(self):
        return self.P.workspace(BRIEF, self.root)

    def _send(self, rq):
        try:
            with urllib.request.urlopen(rq, timeout=300) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            raw = e.read() or b""
            try:
                return e.code, json.loads(raw)
            except ValueError:
                return e.code, {"body": raw[:200].decode("utf-8", "replace")}

    def post(self, path, body):
        return self._send(urllib.request.Request(self.base + path, data=json.dumps(body).encode("utf-8"), method="POST",
                                                 headers={"Content-Type": "application/json", "X-Studio-Token": self.tok}))

    def post_png(self, path_query, png):
        return self._send(urllib.request.Request(self.base + path_query, data=png, method="POST",
                                                 headers={"Content-Type": "image/png", "X-Studio-Token": self.tok}))

    def get(self, path):
        return self._send(urllib.request.Request(self.base + path))

    def still(self, rid, letter, scene=None, png=None, raw_query=None):
        """POST /studio/still for the candidate: `scene` sent url-quoted as the first and only scene parameter, None for
        no scene parameter at all, or `raw_query` appended as it is."""
        png = self.P.director().selftest_still() if png is None else png
        q = "/studio/still?id=%s&candidate=%s" % (urllib.parse.quote(rid, safe=""), letter)
        if raw_query is not None:
            q += ("&" + raw_query) if raw_query else ""
        elif scene is not None:
            q += "&scene=" + urllib.parse.quote(scene, safe="")
        return self.post_png(q, png)

    def ask(self, prompt="heavier", strict=False, piece=PIECE, cam=CAM):
        rid = self.g.ask(prompt, piece, cam, strict=strict)
        t = time.time()
        while time.time() - t < 300:
            r = self.g.state()["request"]
            if r and r["id"] == rid and r["state"] != "running":
                return rid
            time.sleep(0.05)
        raise RuntimeError("request %s did not end" % rid)

    def cand(self, rid, letter):
        with self.g.lock:
            r = self.g.req
            if not r or r.get("id") != rid:
                return None
            got = [c for c in r["candidates"] if c["letter"] == letter]
            return got[0] if got else None

    def lines(self):
        try:
            return open(self.log, "rb").read().splitlines()
        except OSError:
            return []

    def snap(self):
        st = self.ws().stills
        return {"ledger": open(self.ledger, "rb").read(), "art": open(self.art, "rb").read(),
                "certs": sorted(os.listdir(self.certs)) if os.path.isdir(self.certs) else [], "log": self.lines(),
                "stills": sorted(os.listdir(st)) if os.path.isdir(st) else []}

    def close(self):
        self.live.stopping = True
        self.live.acc_seen = 0.0
        try:
            self.srv.shutdown()
            self.srv.server_close()
        except OSError:
            pass


class Obs:
    """One press observed: the HTTP status and answer, the tree before the POST and after the answer, and the director's
    durable points reached while the POST ran (`points`, in order)."""

    def __init__(self, code, ans, before, after, points=()):
        self.code, self.ans, self.before, self.after = code, ans, before, after
        self.points = list(points)
        self.delta = after["ledger"].count(b"\n") - before["ledger"].count(b"\n")
        self.changed = after["art"] != before["art"]
        self.new_certs = sorted(set(after["certs"]) - set(before["certs"]))
        self.new_log = after["log"][len(before["log"]):] if after["log"][:len(before["log"])] == before["log"] else None

    def said(self):
        a = self.ans
        what = a.get("what") if self.code == 200 else "%s%s" % (a.get("code"), ("/" + a["director_code"]) if a.get("director_code") else "")
        rec = a.get("record")
        ev = ", ".join("%s.%s %s" % (e["kind"], e["field"], e["outcome"]) for e in rec["evidence"]) if isinstance(rec, dict) else "no record"
        return "%d %s; ledger %+d; brief %s; certificate%s %s; %s" % (
            self.code, what, self.delta, "changed" if self.changed else "same", "s" if len(self.new_certs) != 1 else "",
            ", ".join(self.new_certs) or "none", ev)


# ------------------------------------------------------------------------------------------------ the matrix's columns
def expand(tpl, sym):
    """A matrix record with its symbols replaced by this run's own values, its pose-wise entries expanded (n poses, pose K
    in its place)."""
    sub = lambda v: sym[v] if isinstance(v, str) and v in sym else v
    out = {k: sub(v) for k, v in tpl.items() if k != "evidence"}
    ev, entries = [], list(tpl["evidence"])
    K = [e for e in entries if e["field"] == "candidate-K"]
    for e in entries:
        f = e["field"]
        if f == "candidate-K" and any(x["field"].startswith("candidate-k, each pose k != K") for x in entries):
            continue                          # placed with its poses, in its place
        if f.startswith("candidate-k, each pose"):
            for k in range(sym["n"]):
                src = K[0] if (k == sym.get("K") and "!= K" in f) else e
                ev.append({"kind": "preview", "field": "candidate-%d" % k, "declared": sub(src["declared"]), "expected": sub(src["expected"]),
                           "outcome": src["outcome"]})
            continue
        x = {"kind": e["kind"], "field": "candidate-%d" % sym["K"] if f == "candidate-K" else f, "declared": sub(e["declared"]),
             "expected": sub(e["expected"]), "outcome": e["outcome"]}
        if x["outcome"] == "UNKNOWN or as compared":
            x["outcome"] = sym["compare"](x)
        ev.append(x)
    out["evidence"] = ev
    return out


# The points the director's commit reaches only once it has begun to write the admission (art/director.py
# _commit_locked: the still in the ledger's stills folder, the pending folder's files and manifest, the admit event, the
# files installed). Named exactly: a recovery inside the POST that finishes a dead writer's folder reaches
# pending:manifest-removed and recover:file-N, which is legitimate before a refusal (M23).
FIRST_WRITES = re.compile(r"^(admit:stills|pending:file-\d+|pending:manifest|ledger:admit|install:file-\d+)$")


def wrote_before_refusal(o):
    """v0 order.rule: a binding refusal comes "before the admission's first write (its still in the ledger's stills
    folder, the pending folder, the admit event, the files)". For a press not answered admitted or undone: [problems]
    when the commit reached a point of its first writes, or the ledger's stills folder changed. It adds no row and no
    plant (the frozen matrix's k is unchanged); its power is MEASURED (the gate moved below pending:manifest in a copy of
    the tree: fifteen refusals that every row passed reached these points), not held by a plant row."""
    if o.code == 200 and o.ans.get("what") in ("admitted", "undone"):
        return []
    p = []
    reached = [x for x in o.points if FIRST_WRITES.match(x)]
    if reached:
        p.append("the press refused after the admission's first write: %s" % ", ".join(reached))
    if o.after.get("stills") != o.before.get("stills"):
        p.append("the press refused with the ledger's stills folder changed (%s)" % ", ".join(
            sorted(set(o.after.get("stills") or ()) ^ set(o.before.get("stills") or ()))))
    return p


def hold(S, run, o, sym, over=None, log_check=True):
    """The press `o` against the matrix's run: [problems]. `over` gives the measured value where the matrix says "per
    today" or "as M6b", and the run's own reading of a column the matrix words (M23, M16's HEAD-MOVED). A press refused
    is held, besides, to nothing of the admission written (wrote_before_refusal)."""
    over = over or {}
    p = wrote_before_refusal(o)
    a = o.ans
    ans = over.get("answer", run["answer"])
    if ans.startswith("admitted"):
        if not (o.code == 200 and a.get("what") == "admitted"):
            p.append("answered %s, not admitted" % o.said().split(";")[0])
    elif ans.startswith("undone"):
        if not (o.code == 200 and a.get("what") == "undone"):
            p.append("answered %s, not undone" % o.said().split(";")[0])
        elif "(#N" in ans and a.get("of") != sym["N"]:
            p.append("undid #%s, not #%s" % (a.get("of"), sym["N"]))
    elif ans == "BINDING-MISMATCH or BINDING-UNKNOWN":
        if a.get("code") not in S.BINDING_CODES:
            p.append("answered %s, not BINDING-*" % a.get("code"))
    elif ans:
        if not (o.code == 409 and a.get("code") == ans):
            p.append("answered %d %s, not %s" % (o.code, a.get("code") or a.get("what"), ans))
    dc = over.get("director_code", run["director_code"])
    if ans and not ans.startswith(("admitted", "undone")) and run["director_code"] is not None and a.get("director_code", "") != dc:
        p.append("director code %r, not %r" % (a.get("director_code", ""), dc))
    led_ = over.get("ledger", run["ledger"])
    m = re.match(r"\+(\d+)", led_ or "")
    if m and o.delta != int(m.group(1)):
        p.append("ledger %+d, not +%s" % (o.delta, m.group(1)))
    br = over.get("brief", run["brief"])
    if br.startswith("same") and o.changed:
        p.append("the brief changed")
    if br == "changed" and not o.changed:
        p.append("the brief did not change")
    ce = over.get("certificate", run["certificate"])
    if isinstance(ce, str) and ce.startswith(("as M6b", "as today")):
        ce = TODAY["undo certificates"]
    if ce == "written" and not o.new_certs:
        p.append("no certificate written")
    if ce == "none" and o.new_certs:
        p.append("a certificate written (%s)" % ", ".join(o.new_certs))
    if isinstance(ce, int) and len(o.new_certs) != ce:
        p.append("%d certificates written, not %d as today" % (len(o.new_certs), ce))
    rec = run["record"]
    if isinstance(rec, dict):
        want = expand(rec, sym)
        got = a.get("record")
        if not isinstance(got, dict):
            p.append("no decision record on the answer")
        else:
            pin = {k: got.get(k) for k in CONSTANT}
            v0 = register_v0() or {}
            if pin != {"contract": "BINDING-0", "version": 0, "sha256": v0.get("sha256")}:
                p.append("the record's constant fields %s are not the register's version-0 line" % pin)
            # not_checked explicit (his safeguard; spec §5): where an earlier check refused, the answer says the binding
            # was not reached and why; where the check ran, that it was checked
            b = a.get("binding")
            if all(e["outcome"] == "not reached" for e in want["evidence"]):
                if b != {"checked": False, "why": want["decision"]}:
                    p.append("the answer's binding is %s, not checked false and why %s" % (b, want["decision"]))
            elif not (isinstance(b, dict) and b.get("checked") is True):
                p.append("the answer's binding is %s, not checked" % (b,))
            core = {k: v for k, v in got.items() if k not in CONSTANT}
            if core != want:
                p.append("record %s, not %s" % (json.dumps(core, sort_keys=True)[:600], json.dumps(want, sort_keys=True)[:600]))
            pure = S.record_bytes(S.record(want["operation"], want["candidate"], want["intent_sha256"], want["of"], want["evidence"], want["decision"],
                                           want["director_code"]))
            if S.record_bytes(got) != pure:
                p.append("the record's bytes are not the host's record function over this run's values")
            if log_check:
                nl = o.new_log
                if nl is None or len(nl) != 1:
                    p.append("%s lines written to the request's log for the press, not one" % ("not appended" if nl is None else len(nl)))
                else:
                    ln = json.loads(nl[0])
                    if not isinstance(ln.get("record"), dict) or S.record_bytes(ln["record"]) != S.record_bytes(got):
                        p.append("the log line's record is not the answer's, byte for byte")
                    if "at" not in ln or (want["operation"] == "admit" and ln.get("id") != sym.get("rid")):
                        p.append("the log line has not the request's id and the clock beside the record")
    elif isinstance(rec, str) and rec.startswith("none"):
        if "record" in a or "binding" in a:
            p.append("a record or binding on the answer, where the switch removes the check that makes it")
    names = run.get("names")
    if names and "candidate-K" in names:
        names = names.replace("candidate-K", "candidate-%d" % sym["K"])
    if names:
        b = a.get("binding") or {}
        if b.get("names") != names:
            p.append("the answer names %r, not %r" % (b.get("names"), names))
        msg = a.get("message", "")
        if names not in msg:
            p.append("the message does not name %s" % names)
        got = a.get("record") or {}
        e = [x for x in got.get("evidence", []) if "%s.%s" % (x["kind"], x["field"]) == names]
        if a.get("code") == "BINDING-MISMATCH" and (not e or e[0]["declared"] not in msg or e[0]["expected"] not in msg):
            p.append("the message does not give the declared and the expected value")
        if a.get("code") == "BINDING-UNKNOWN" and "absent or not well formed" not in msg:
            p.append("the message does not say the value is absent or not well formed")
    return p


# ------------------------------------------------------------------------------------------------ the rows
class Bench:
    """The scratch folder the rows build their states in, and the worlds open on it."""

    def __init__(self, P, row):
        import studio
        self.P, self.S, self.D, self.row = P, studio, P.director(), row
        self.tmp = tempfile.mkdtemp(prefix="binding-rows-")
        self.n = 0
        self.open = []
        self.scripted = os.path.join(REPO, "art", "providers", "scripted.json")
        self.printed = set()
        self.records = []           # (matrix id, case, record bytes): v0 decision record.self-test

    def path(self, label):
        self.n += 1
        return os.path.join(self.tmp, "%03d-%s" % (self.n, label))

    def cfg(self, name, code):
        f = os.path.join(self.tmp, name + ".py")
        open(f, "wb").write(code.encode("utf-8") + b"\n")
        c = os.path.join(self.tmp, name + ".json")
        open(c, "wb").write(json.dumps({"provider": "cli", "argv": [sys.executable, f], "model": name, "timeout_s": 60, "max_output_bytes": 262144}).encode("utf-8"))
        return c

    def fixture(self, label, extra=()):
        """The fixture's world (art/fixtures/selftest/), with `extra` statements after its brief, and a ledger started."""
        d = self.path(label)
        if not extra:
            self.D.selftest_tree(d)
            return d
        os.makedirs(os.path.join(d, "art", "briefs"))
        os.makedirs(os.path.join(d, "graybox", "maps"))
        for f in os.listdir(os.path.join(REPO, "graybox", "maps")):
            if f.endswith(".gbx"):
                shutil.copy(os.path.join(REPO, "graybox", "maps", f), os.path.join(d, "graybox", "maps", f))
        for f in ("tactical.design", "tactical.layout"):
            shutil.copy(os.path.join(self.D.FIXTURE, f), os.path.join(d, "graybox", "maps", f))
        raw = open(os.path.join(self.D.FIXTURE, BRIEF + ".art"), "rb").read().replace(b"\r\n", b"\n") + ("\n".join(extra) + "\n").encode("ascii")
        open(os.path.join(d, "art", "briefs", BRIEF + ".art"), "wb").write(raw)
        self.D.cmd_genesis_quiet(self.D.Workspace(BRIEF, d))
        return d

    def copy(self, src, label):
        d = self.path(label)
        shutil.copytree(src, d)
        return d

    def world(self, root, cfg=None, watch=False):
        w = World(self.P, root, cfg or self.scripted, watch=watch)
        self.open.append(w)
        return w

    def shut(self, w):
        w.close()
        if w in self.open:
            self.open.remove(w)

    def close(self):
        for w in list(self.open):
            self.shut(w)
        self.S.BINDING_PLANT = ""
        self.D.durable.HOOK = None
        shutil.rmtree(self.tmp, ignore_errors=True)

    # what a row prints
    def say(self, name, ok, detail):
        """Print a row as STUDIO prints it. R5 (tools/rung.py) keys a plant row by its name up to its first " — ": a
        name with that dash, a newline or whitespace at either end, or a detail whose first line is blank (R5 would key
        the row with its dash), is refused, the row failed; a row that is not a plant row never names that word."""
        first = (detail or "").strip().splitlines()[0].strip() if (detail or "").strip() else ""
        if not first or " — " in name or "\n" in name or name != name.strip():
            ok, first = False, "refused: a row of this matrix needs a name without the dash and a detail that is not blank (%r)" % (first,)
        if not name.startswith("BINDING plant: "):
            first = re.sub(r"\bplant\b", "switch", first)     # R5 reads a row naming that word as a planted defect
        self.printed.add(name)
        self.row(name, ok, first[:900])

    def keep(self, mid, case, o):
        """A run's decision record beside its case (v0 decision record.self-test), for acceptance 4's comparison."""
        rec = o.ans.get("record")
        if isinstance(rec, dict):
            self.records.append((mid, case, self.S.record_bytes(rec)))

    def press(self, w, path, body, plant=""):
        """POST `path` with `body`, the plant `plant` set while it runs; every durable point the director reaches while it
        runs is recorded (the hook already set, M16's other writer, called after it, and put back)."""
        before = w.snap()
        prev, seen = self.D.durable.HOOK, []

        def hook(name):
            seen.append(name)
            if prev is not None:
                prev(name)
        self.D.durable.HOOK = hook
        self.S.BINDING_PLANT = plant
        try:
            code, ans = w.post(path, body)
        finally:
            self.S.BINDING_PLANT = ""
            self.D.durable.HOOK = prev
        return Obs(code, ans, before, w.snap(), seen)

    def readings(self, w, rid=None, letter="A", preview=False, undo=False):
        """The host's own readings of a world (never rev.id, rev.files, rev.live or rev.process), and its files' hashes."""
        out = {}
        if rid:
            _c, ev = w.get("/evidence.json?world=%s&id=%s&candidate=%s" % (BRIEF, urllib.parse.quote(rid, safe=""), letter))
            it = ev.get("items") or {}
            st = it.get("still") or {}
            out["evidence"] = {"still": {"sha256": st.get("sha256", ""), "scene": st.get("scene", "")}, "head": it.get("head"), "scene": it.get("scene"),
                               "base_sha": it.get("base_sha")}
        if preview:
            c = w.cand(rid, letter) or {}
            with w.g.lock:
                out["previews"] = json.loads(json.dumps(c.get("previews") or {}, sort_keys=True))
        if undo:
            _c, u = w.get("/undo.json?world=%s" % BRIEF)
            out["undo"] = {k: u.get(k) for k in ("of", "scene", "from_head")}
        _c, lv = w.get("/live?world=%s" % BRIEF)
        w.live.acc_seen = 0.0           # the accounts' worker that /live wakes is let go: these rows read no account
        out["live"] = [(s.get("k"), s.get("sha"), s.get("head")) for s in ((lv.get("rev") or {}).get("slots") or [])]
        files = {}
        for top in ("art/briefs", "art/ledger", "graybox/maps"):
            d = os.path.join(w.root, *top.split("/"))
            for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
                p = os.path.join(d, f)
                if os.path.isfile(p):
                    files[top + "/" + f] = sha256(open(p, "rb").read())
        out["files"] = files
        return out

    def equal(self, a, b):
        """Whether two copies' readings are equal, and what was compared."""
        same = json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
        diff = [k for k in sorted(set(a) | set(b)) if json.dumps(a.get(k), sort_keys=True) != json.dumps(b.get(k), sort_keys=True)]
        return same, "readings %s across the copies (%s; %d files hashed)%s" % ("equal" if same else "NOT equal", ", ".join(sorted(a)), len(a.get("files", {})),
                                                                                 "" if same else ": " + ", ".join(diff))


# ------------------------------------------------------------------------------------------------ the states
# A provider that answers as the scripted one does, its "Panelled column" made candidate A (the strict request whose
# regions do not hold A: B4-OUTSIDE, and the order state ADMIT-OUTSIDE)
COLUMN_FIRST = (
    "import json, subprocess, sys\n"
    "raw = sys.stdin.buffer.read()\n"
    "out = subprocess.run([sys.executable, %r], input=raw, capture_output=True, timeout=50).stdout\n"
    "d = json.loads(out)\n"
    "d['candidates'] = sorted(d.get('candidates') or [], key=lambda c: c.get('title') != 'Panelled column')\n"
    "sys.stdout.write(json.dumps(d))\n") % os.path.join(REPO, "art", "providers", "scripted.py")
# B2's move (M13's state): an admission of the other canopy, a statement A's revision does not name, which the exporter
# carries into the scene; the other canopy, as M13u's hand edit makes it (a statement #N's inverse neither restores nor
# removes)
OTHER_CANOPY = "canopy plaza concrete_slab 7.0 19,20 28,21"
MOVE = "= " + OTHER_CANOPY + " deep 2.6"
COMMENT = b"# BINDING-0's rows: a comment line recorded through the director\n"


class States:
    """The matrix's states, each built in a tree of its own: a base tree made once (a request asked, previews finished,
    admissions made), then copied byte for byte for each run, a Live and a Gateway started on the copy and the request
    restored (restore draws its candidates again at the head as the files stand, which is the head they were asked at)."""

    def __init__(self, B):
        self.B, self.D, self.S = B, B.D, B.S
        self.bases = {}

    def base(self, key, make):
        if key not in self.bases:
            self.bases[key] = make()
        return self.bases[key]

    # the request: plain (STUDIO's fixture, the scripted provider's three canopies)
    def plain(self):
        def make():
            d = self.B.fixture("plain")
            w = self.B.world(d)
            rid = w.ask()
            self.B.shut(w)
            return d, rid
        return self.base("plain", make)

    def at(self, key, label, watch=False):
        d, rid = getattr(self, key)()
        w = self.B.world(self.B.copy(d, label), self.cfg_one_bad() if key == "one_bad" else None, watch=watch)
        w.g.restore(rid)
        return w, rid

    def unlogged(self):
        def make():
            d = self.B.fixture("unlogged")
            open(os.path.join(d, "art", "briefs", BRIEF + ".art"), "ab").write(b"# a hand edit, not recorded\n")
            w = self.B.world(d)
            rid = w.ask()
            self.B.shut(w)
            return d, rid
        return self.base("unlogged", make)

    def one_bad(self):
        def make():
            d = self.B.fixture("one-bad")
            w = self.B.world(d, self.cfg_one_bad())
            rid = w.ask()
            self.B.shut(w)
            return d, rid
        return self.base("one_bad", make)

    def cfg_one_bad(self):
        if "one_bad_cfg" not in self.bases:
            self.bases["one_bad_cfg"] = self.B.cfg("one_bad", self.B.P.TEST_PROVIDERS["one_bad.py"])
        return self.bases["one_bad_cfg"]

    def strict_tree(self):
        """STRICT-0's world (two buildings on the north lane) with the shape `bay` marked on the first one's face."""
        def make():
            P = self.B.P
            d = self.B.fixture("strict", P.STRICT_LINES)
            w = self.B.world(d)
            out0 = w.ws().export()[0]
            mass = next(v for v in out0["scene"]["visuals"] if v["id"] == "building:10,2-17,2")
            shape = {"name": "bay", "operation": "region", "anchor": {"piece": mass["id"], "face": "+z", "box": mass["box"], "scene": w.live.slot(0)["sha"], "view": {}},
                     "vertices": [[6, 3], [8, 3], [8, 6.5], [6, 6.5]], "constraints": {"within": True, "supports": False, "collision": False, "material": "keep"}}
            c, r = w.post("/studio/shapes/save", {"shape": shape})
            self.B.shut(w)
            if c != 200:
                raise RuntimeError("the shape was not saved: %s %s" % (c, r))
            return d
        return self.base("strict", make)

    def strict(self, label):
        """A strict request whose regions do not hold A (its "Panelled column"), asked in a copy of its own (a request
        restored is not strict again, so each run asks)."""
        if "column_cfg" not in self.bases:
            self.bases["column_cfg"] = self.B.cfg("column_first", COLUMN_FIRST)
        w = self.B.world(self.B.copy(self.strict_tree(), label), self.bases["column_cfg"])
        rid = w.ask("close #bay", strict=True, piece=None, cam=None)
        c = w.cand(rid, "A") or {}
        if (c.get("strict") or {}).get("code") != "ADMIT-OUTSIDE":
            raise RuntimeError("the strict request's A is not outside its regions: %s" % (c.get("strict"),))
        return w, rid

    def still_syms(self, w, rid, letter="A"):
        """A's identities: S_base (the world's scene as the files stand), S_A (the scene the admission's own evaluation
        exports, at a head that has not moved the scene A was drawn with), I_A (its intent's sha256 as the gateway keeps
        it); and what does not hold of them."""
        c = w.cand(rid, letter)
        ws = w.ws()
        s_base = ws.export()[0]["lineage"]["scene_sha256"]
        o1 = self.D.evaluate_doc(ws, self.D.canon.load_intent(c["intent"]))[3]
        s_a = o1["lineage"]["scene_sha256"] if o1 is not None else ""
        kept = open(os.path.join(w.records, rid, letter + ".intent"), "rb").read()
        bad = []
        if s_base != c.get("base_sha"):
            bad.append("S_base %s is not the card's base %s" % (s_base[:12], (c.get("base_sha") or "")[:12]))
        if not s_a or s_a != c.get("scene"):
            bad.append("S_A %s is not the scene the candidate was drawn with %s" % (s_a[:12], (c.get("scene") or "")[:12]))
        if s_a == s_base:
            bad.append("S_A equals S_base")
        if kept != c["intent"]:
            bad.append("the intent the gateway keeps is not the recorded one")
        return {"S_base": s_base, "S_A": s_a, "I_A": sha256(c["intent"]), "I_C": sha256(c["intent"]), "rid": rid}, bad

    def flagged_png(self):
        Q = self.D.quality
        return Q.png_bytes(32, 18, bytes(255 if (i // 3) % 32 < 24 else 40 + (i % 11) * 9 for i in range(32 * 18 * 3)))

    def recorded(self, w, note="BINDING-0's rows"):
        """A comment line of the art recorded through the director (cmd_rebase): the head moves, the scene does not."""
        open(w.art, "ab").write(COMMENT)
        self.S.quiet(self.D.cmd_rebase, w.ws(), note)

    def move(self, w):
        """B2's move: the other canopy made deeper by an admission through the studio's ledger, made as page_dash's
        aligned_admission makes its own (evaluate_doc, append_evaluation, cmd_admit with the self-test's still)."""
        D, ws = self.D, w.ws()
        _o, parts, _c = ws.export()
        doc = {"base": {k: parts[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}, "brief": BRIEF, "candidate": "A",
               "format": "VERDANDI-INTENT", "layout": [], "prompt": "the other canopy deeper (BINDING-0's B2)", "rationale": "another admission",
               "revision": [MOVE], "scope": ["plaza/canopy/*"], "version": "0"}
        raw = D.canon.dumps(doc)
        verdict, after, timings, _o1, _o0, _t, rec = D.evaluate_doc(ws, D.canon.load_intent(raw))
        ev = self.S.quiet(D.append_evaluation, ws, raw, verdict, after, timings, rec)
        a = self.S.quiet(D.cmd_admit, ws, ev["seq"], chooser="another admission (BINDING-0's rows)", still=D.selftest_still())
        return verdict["verdict"], a

    def scene_now(self, w, rid, letter="A"):
        """The scene the admission's own evaluation of the candidate exports at the head as the files stand now, and
        that evaluation's verdict."""
        c = w.cand(rid, letter)
        v, _a, _t, o1, _o0, _x, _r = self.D.evaluate_doc(w.ws(), self.D.canon.load_intent(c["intent"]))
        return (o1["lineage"]["scene_sha256"] if o1 is not None else ""), v

    # the previews
    def preview(self, w, rid, k_base=None, scene_a=None, scene_base=None, letter="A"):
        """A's preview through the routes: planned, a still of each side at each pose (each candidate-side still naming
        A's scene but pose `k_base`, naming the base scene), finished. Returns (plan, finish answer, its log line)."""
        c, plan = w.post("/studio/preview", {"id": rid, "candidate": letter})
        if c != 200:
            raise RuntimeError("PREVIEW: %s %s" % (plan.get("code"), plan.get("message", "")[:100]))
        n = len(plan["still_ticks"])
        png = self.D.selftest_still()
        for k in range(n):
            for side, sc in (("base", scene_base), ("candidate", scene_base if k == k_base else scene_a)):
                q = "/studio/preview/still?id=%s&candidate=%s&side=%s&k=%d&scene=%s" % (urllib.parse.quote(rid, safe=""), letter, side, k, sc)
                cc, a = w.post_png(q, png)
                if cc != 200 or a.get("scene") != sc:
                    raise RuntimeError("a preview still was not kept: %s %s" % (cc, a))
        c, fin = w.post("/studio/preview/finish", {"id": rid, "candidate": letter})
        if c != 200:
            raise RuntimeError("PREVIEW finish: %s %s" % (fin.get("code"), fin.get("message", "")[:100]))
        lines = [json.loads(x) for x in w.lines()]
        line = [x for x in lines if x.get("decision") == "preview" and x.get("id") == rid][-1]
        return plan, fin, line

    def previewed(self, key, k_base):
        """A request with a camera path (asked again with a new id until preview_plan finds one, up to TRIES times), A
        previewed and finished (pose `k_base` naming the base scene, or none): (tree, rid, facts). A request's path is
        seeded by its id, which carries the UTC second: in this fixture about a third of ids give none (MEASURED, 96 of
        300), so that four tries failed about once in a hundred builds (STUDIO 180/198 once in a full check); twelve fail
        about once in a million."""
        def make():
            d = self.B.fixture(key)
            w = self.B.world(d)
            tries, rid = 0, None
            while tries < TRIES and rid is None:
                tries += 1
                rid = w.ask()
                try:
                    w.g.preview_plan(rid, "A")
                except self.S.StudioError as e:
                    if e.code != "PREVIEW-NO-PATH":
                        raise
                    rid = None
            if rid is None:
                raise RuntimeError("no request of %d had a camera path (PREVIEW-NO-PATH)" % TRIES)
            sy, bad = self.still_syms(w, rid)
            plan, fin, line = self.preview(w, rid, k_base=k_base, scene_a=sy["S_A"], scene_base=sy["S_base"])
            rep = open(os.path.join(w.records, rid, "A.preview.report.json"), "rb").read()
            facts = {"tries": tries, "plan": plan, "fin": fin, "line": line, "report_sha256": sha256(rep), "syms": sy, "bad": bad}
            self.B.shut(w)
            return d, rid, facts
        return self.base(key, make)

    @staticmethod
    def preview_id_rule(binding, drawn, report_sha256):
        """v0's rule for a preview's id, written out here (never the host's function): the sha256 of the canonical form of
        {binding, drawn, report_sha256}."""
        obj = {"binding": {k: binding[k] for k in ("head", "base_sha", "candidate_sha")}, "drawn": dict(drawn), "report_sha256": report_sha256}
        return sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii"))

    # the undos
    def admitted(self, key, n_admissions):
        """`n_admissions` studio admissions (each a request asked and its first CLEAN candidate that changes the scene
        admitted with a still that declares its scene): (tree, [their admit sequence numbers])."""
        def make():
            d = self.B.fixture(key)
            w = self.B.world(d)
            seqs = []
            for i in range(n_admissions):
                rid = w.ask("heavier" if i == 0 else "deeper still")
                r = w.g.state()["request"]
                # the first CLEAN candidate drawn that changes the scene (the scripted provider's first may restate what an
                # earlier admission made)
                letter = next(c["letter"] for c in r["candidates"] if c["verdict"] == "CLEAN" and c["slot"] is not None and c["scene"] != c["base_sha"])
                c, s = w.still(rid, letter, w.cand(rid, letter)["scene"])
                c, a = w.post("/studio/admit", {"id": rid, "candidate": letter, "still": s.get("still", "")})
                if c != 200:
                    raise RuntimeError("an admission of the state was refused: %s %s" % (a.get("code"), a.get("message", "")[:120]))
                seqs.append(a["ledger"][1])
            self.B.shut(w)
            return d, seqs
        return self.base(key, make)

    def undo_world(self, tree, label):
        d, seqs = tree
        return self.B.world(self.B.copy(d, label)), seqs

    def undo_syms(self, w, seqs):
        """N (the undo target's sequence number, read from the ledger) and M (the admission before it), S_w (the scene at
        the undo: the files' exported scene, computed here apart), and GET /undo.json's answer."""
        _c, u = w.get("/undo.json?world=%s" % BRIEF)
        s_w = w.ws().export()[0]["lineage"]["scene_sha256"]
        events = self.D.led.read(w.ledger)[0]
        admits = [e["seq"] for e in events if e["kind"] == "admit"]
        sy = {"N": admits[-1] if admits else "", "M": seqs[0] if len(seqs) > 1 else "", "S_w": s_w, "u": u}
        return sy

    def layout_tree(self):
        """An art admission #M through the studio, then a layout admission #N through the director (a layout intent at
        the files' head, evaluated by cmd_evaluate and admitted by cmd_admit with the self-test's still): the latest
        admission not undone is a layout one."""
        def make():
            d, seqs = self.admitted("one-admission", 1)
            d2 = self.B.copy(d, "layout")
            D = self.D
            ws = D.Workspace(BRIEF, d2)
            _o, parts, _c = ws.export()
            doc = {"base": {k: parts[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}, "brief": BRIEF, "candidate": "L",
                   "format": "VERDANDI-INTENT", "layout": ["close 24,7 24,9"], "prompt": "close the north flank (BINDING-0's rows)", "rationale": "a layout target",
                   "revision": [], "scope": ["layout/north-flank"], "version": "0"}
            f = os.path.join(self.B.tmp, "L.intent")
            open(f, "wb").write(D.canon.dumps(doc))
            rows = self.S.quiet(D.cmd_evaluate, ws, [f], quiet=True)
            a = self.S.quiet(D.cmd_admit, ws, rows[0][4], chooser="the director (BINDING-0's rows)", still=D.selftest_still())
            ev = D.led.read(ws.ledger)[0]
            if not ev[-1].get("design_lines"):
                raise RuntimeError("the layout admission wrote no design lines")
            return d2, [seqs[0], ev[-1]["seq"]]
        return self.base("layout", make)

    def not_clean_tree(self):
        """Two studio admissions, #M then #N, both of the canopy A's request targets; then that canopy's statement taken
        out by a hand edit recorded through the director, so that #N's inverse (an '=' of it) is not CLEAN."""
        def make():
            d, seqs = self.admitted("two-admissions", 2)
            d2 = self.B.copy(d, "not-clean")
            art = os.path.join(d2, "art", "briefs", BRIEF + ".art")
            lines = open(art, "rb").read().decode("utf-8").split("\n")
            kept = [x for x in lines if not (x.startswith("canopy plaza ") and " 19,10 28,11" in x)]
            if len(kept) != len(lines) - 1:
                raise RuntimeError("the canopy's statement was not found once")
            open(art, "wb").write("\n".join(kept).encode("utf-8"))
            self.S.quiet(self.D.cmd_rebase, self.D.Workspace(BRIEF, d2), "the canopy taken out (BINDING-0's rows)")
            return d2, seqs
        return self.base("not_clean", make)


# ------------------------------------------------------------------------------------------------ the presses "per today"
# The states whose expected values the matrix marks "per today" (or "as today"), built and pressed by one function each,
# so that the measurement (this file copied into the art/ of a clone of 1381b31, and Bench, States and these functions
# called by a driver that is not in the tree) and the row on this tree build and press them alike.
def case_outside(B, St, declare, label, plant=""):
    """B4-OUTSIDE (declare "S_A") and the order state ADMIT-OUTSIDE (declare "S_base"): a strict request whose regions do
    not hold A, its still declaring `declare`."""
    w, rid = St.strict(label)
    sy, bad = St.still_syms(w, rid)
    _c, s = w.still(rid, "A", sy[declare])
    return B.press(w, "/studio/admit", {"id": rid, "candidate": "A", "still": s.get("still", "")}, plant), sy, bad, w


def case_undo_unlogged(B, St, label, plant=""):
    """B4-UNDO-UNLOGGED: one studio admission #N, then a hand edit the ledger does not hold; of and scene as GET
    /undo.json gave them, its scene required to be S_w, computed apart (an export of the files after the hand edit)."""
    w, seqs = St.undo_world(St.admitted("one-admission", 1), label)
    open(w.art, "ab").write(b"# a hand edit, not recorded\n")
    sy = St.undo_syms(w, seqs)
    u = sy["u"]
    bad = [] if (u.get("scene") == sy["S_w"] and sy["S_w"] and u.get("of") == sy["N"] and u.get("code") == "STUDIO-DIRECTOR-REFUSED") else \
        ["GET /undo.json gave of %s scene %s code %s; S_w %s, the target #%s" % (u.get("of"), (u.get("scene") or "")[:12], u.get("code"), sy["S_w"][:12], sy["N"])]
    return B.press(w, "/studio/undo", {"of": u.get("of"), "scene": u.get("scene")}, plant), sy, bad, w


def case_kept_removed(B, St, label, plant=""):
    """M24: A's still posted declaring the base scene, then its kept file removed."""
    w, rid = St.at("plain", label)
    sy, bad = St.still_syms(w, rid)
    _c, s = w.still(rid, "A", sy["S_base"])
    os.remove(w.cand(rid, "A")["still"]["path"])
    return B.press(w, "/studio/admit", {"id": rid, "candidate": "A", "still": s.get("still", "")}, plant), sy, bad, w


def case_undo_bound(B, St, label, plant="", of="N", scene="S_w"):
    """§4's undo: two studio admissions, #M then #N; GET /undo.json read; an undo declaring `of` and `scene` (symbols,
    None for a key not sent)."""
    w, seqs = St.undo_world(St.admitted("two-admissions", 2), label)
    sy = St.undo_syms(w, seqs)
    u = sy["u"]
    bad = [] if (u.get("of") == sy["N"] and u.get("scene") == sy["S_w"] and sy["S_w"] and int(sy["M"]) <= int(sy["N"]) - 2) else \
        ["GET /undo.json gave of %s scene %s; the target #%s (M #%s), the files' scene %s" % (u.get("of"), (u.get("scene") or "")[:12], sy["N"], sy["M"], sy["S_w"][:12])]
    body = {}
    if of is not None:
        body["of"] = sy[of] if of in sy else of
    if scene is not None:
        body["scene"] = sy[scene] if scene in sy else scene
    return B.press(w, "/studio/undo", body, plant), sy, bad, w


def case_flagged(B, St, label, plant=""):
    """B4-FLAGGED: A's still flagged by the detectors, Admit not despite them; the still declaring S_A."""
    w, rid = St.at("plain", label)
    sy, bad = St.still_syms(w, rid)
    _c, s = w.still(rid, "A", sy["S_A"], png=St.flagged_png())
    return B.press(w, "/studio/admit", {"id": rid, "candidate": "A", "still": s.get("still", "")}, plant), sy, bad, w


# ------------------------------------------------------------------------------------------------ the rows
def switched(run):
    """The plant a run's switches name, as art/studio.py's BINDING_PLANT takes it: "" (enforcement on), a name, or a set."""
    sw = run.get("switches") or []
    return "" if not sw else sw[0] if len(sw) == 1 else set(sw)


def claims(x):
    """Whether an account says a binding was checked or matched: a key `binding`, a `checked` true, an `outcome` MATCH."""
    if isinstance(x, dict):
        if "binding" in x or x.get("checked") is True or x.get("outcome") == "MATCH":
            return True
        return any(claims(v) for v in x.values())
    if isinstance(x, list):
        return any(claims(v) for v in x)
    return False


class Rows:
    """The matrix's STUDIO rows, in groups that share their states; a group that raises fails each of its rows not yet
    printed, and the rows after it run."""

    def __init__(self, B, St, M, V):
        self.B, self.St, self.M, self.V, self.S, self.D = B, St, M, V, B.S, B.D
        self.byid = {r["id"]: r for r in M.get("rows", [])}
        self.m4_ids = []            # the finished previews whose ids M20's id row holds: (label, plan, finish, line, report sha256)
        self.answered = {}          # (matrix id, run) -> its press, for the plant rows that are caught against their honest twin

    def run(self, mid, i=0):
        return self.byid[mid]["runs"][i]

    def twin(self, mid, i, code):
        """For a plant row: [] when its honest twin (mid, i) was answered `code` in this run, else the reason it is not
        caught (a plant is caught only where the honest run answers as the matrix says)."""
        o = self.answered.get((mid, i))
        got = None if o is None else (o.ans.get("code") or o.ans.get("what"))
        return [] if got == code else ["its honest twin (%s) answered %s, not %s" % (mid, got, code)]

    def check(self, mid, i, o, sym, over=None, extra=(), log_check=True, case=None):
        """Print one run's row: the press held to the matrix's run, and `extra`, the state's own requirements."""
        run = self.run(mid, i)
        self.answered[(mid, i)] = o
        p = list(extra) + hold(self.S, run, o, sym, over, log_check)
        self.B.say(run["row"], not p, o.said() + ("; " + "; ".join(p) if p else ""))
        if case:
            self.B.keep(mid, case, o)
        return not p

    def press(self, w, path, body, mid, i):
        return self.B.press(w, path, body, switched(self.run(mid, i)))

    def group(self, mids, fn):
        try:
            fn()
        except Exception as e:  # noqa: BLE001 — a group that raised fails its rows; the rows after it run
            import traceback
            traceback.print_exc()
            for mid in mids:
                for r in self.byid[mid]["runs"]:
                    if r["row"] not in self.B.printed and not r["row"].startswith("("):
                        self.B.say(r["row"], False, "its state raised %s: %s" % (type(e).__name__, str(e)[:300]))
        finally:
            self.S.BINDING_PLANT = ""
            self.D.durable.HOOK = None
            for w in list(self.B.open):
                self.B.shut(w)

    # ---------------------------------------------------------------------------------------------- BIND-CAUSAL-0, the still
    def still_pair(self, declare, label):
        """Two byte-identical copies of the request's tree, each with a Live and a Gateway and the request restored, the
        same still posted declaring `declare` in each; the host's readings of the two, and whether they are equal."""
        out = []
        for i in range(2):
            w, rid = self.St.at("plain", "%s-%d" % (label, i))
            sy, bad = self.St.still_syms(w, rid)
            _c, s = w.still(rid, "A", sy[declare])
            out.append((w, rid, sy, bad, s))
        same, said = self.B.equal(self.B.readings(out[0][0], out[0][1]), self.B.readings(out[1][0], out[1][1]))
        return out, same, said

    def g_still(self):
        St, B = self.St, self.B
        # M1 / M2: the motivating admission, enforced and removed, from equal starts
        cps, same, said = self.still_pair("S_base", "m1")
        (w1, rid, sy1, bad1, s1), (w2, _r, sy2, bad2, s2) = cps
        o2 = self.press(w2, "/studio/admit", {"id": rid, "candidate": "A", "still": s2["still"]}, "M1", 0)
        o1 = self.press(w1, "/studio/admit", {"id": rid, "candidate": "A", "still": s1["still"]}, "M2", 0)
        req = ([] if same else [said]) + bad2 + ([] if sy1 == sy2 else ["the copies' identities differ"])
        self.check("M1", 0, o2, sy2, extra=req, case="B1 still, honest")
        m1_refused = o2.code == 409 and o2.ans.get("code") == "BINDING-MISMATCH"
        self.check("M2", 0, o1, sy1, extra=req + ([] if m1_refused else ["the enforced copy (M1) did not refuse BINDING-MISMATCH"]))
        # M3 / M3r: the candidate scene declared, enforced and removed
        cps, same, said = self.still_pair("S_A", "m3")
        (w1, rid, sy1, bad1, s1), (w2, _r, sy2, bad2, s2) = cps
        o2 = self.press(w2, "/studio/admit", {"id": rid, "candidate": "A", "still": s2["still"]}, "M3", 0)
        o1 = self.press(w1, "/studio/admit", {"id": rid, "candidate": "A", "still": s1["still"]}, "M3r", 0)
        req = ([] if same else [said]) + bad2
        self.check("M3", 0, o2, sy2, extra=req, case="B5 still, honest")
        self.check("M3r", 0, o1, sy1, extra=req)
        # M3s: each send replaces the one before (the same bytes, two scenes)
        for i, order in enumerate((("S_base", "S_A"), ("S_A", "S_base"))):
            w, rid = St.at("plain", "m3s-%d" % i)
            sy, bad = St.still_syms(w, rid)
            sent = [w.still(rid, "A", sy[k]) for k in order]
            same_bytes = sent[0][1].get("still") == sent[1][1].get("still")
            o = self.press(w, "/studio/admit", {"id": rid, "candidate": "A", "still": sent[1][1]["still"]}, "M3s", i)
            self.check("M3s", i, o, sy, extra=bad + ([] if same_bytes else ["the two sends were not the same still"]),
                       case="B5 still, each send replaces" if i == 0 else "B1 still, each send replaces")
        # M8: a still sent with no scene parameter (kept ""), enforced and removed
        for i in range(2):
            w, rid = St.at("plain", "m8-%d" % i)
            sy, bad = St.still_syms(w, rid)
            _c, s = w.still(rid, "A", None)
            kept = s.get("scene")
            o = self.press(w, "/studio/admit", {"id": rid, "candidate": "A", "still": s["still"]}, "M8", i)
            self.check("M8", i, o, sy, extra=bad + ([] if kept == "" else ["the still's scene was kept as %r, not \"\"" % kept])
                       + (self.twin("M8", 0, "BINDING-UNKNOWN") if i else []),
                       case="B3 still, honest" if i == 0 else None)
        # M20's switched comparisons on M1's and M8's states
        for i, declare in ((6, "S_base"), (10, "S_base"), (7, None)):
            w, rid = St.at("plain", "m20-%d" % i)
            sy, bad = St.still_syms(w, rid)
            _c, s = w.still(rid, "A", sy[declare] if declare else None)
            o = self.press(w, "/studio/admit", {"id": rid, "candidate": "A", "still": s["still"]}, "M20", i)
            self.check("M20", i, o, sy, extra=bad)

    # ---------------------------------------------------------------------------------------------- the preview
    def preview_copies(self, key, k_base, n_copies, label):
        """`n_copies` byte-identical copies of a tree whose request's A has a finished preview (pose `k_base` naming the
        base scene, or none), each with a Live and a Gateway, the request restored and the admission's still posted
        declaring S_A; the readings of each."""
        d, rid, f = self.St.previewed(key, k_base)
        out = []
        for i in range(n_copies):
            w = self.B.world(self.B.copy(d, "%s-%d" % (label, i)))
            w.g.restore(rid)
            sy = dict(f["syms"], n=len(f["plan"]["still_ticks"]), K=k_base, P_A=f["fin"]["preview_id"])
            _c, s = w.still(rid, "A", sy["S_A"])
            out.append((w, rid, sy, s, self.B.readings(w, rid, preview=True)))
        bad = list(f["bad"]) + ([] if 4 <= len(f["plan"]["still_ticks"]) <= 8 else ["the preview has %d poses" % len(f["plan"]["still_ticks"])])
        if f["tries"] > 1:
            pass                    # said in the row's detail below
        return d, rid, f, out, bad

    def g_preview(self):
        B, St = self.B, self.St
        # M4 / M5 (and a third copy for M25): one candidate-side still naming the base scene
        d, rid, f, cps, bad = self.preview_copies("preview-k", 1, 3, "m4")
        self.m4_ids.append(("M4's state", f))
        same = all(json.dumps(c[4], sort_keys=True) == json.dumps(cps[0][4], sort_keys=True) for c in cps)
        req = bad + ([] if same else ["readings NOT equal across the copies"])
        body = lambda c: {"id": rid, "candidate": "A", "still": c[3]["still"], "preview": c[2]["P_A"]}
        o2 = self.press(cps[1][0], "/studio/admit", body(cps[1]), "M4", 0)
        o3 = self.press(cps[2][0], "/studio/admit", body(cps[2]), "M4", 0)
        o1 = self.press(cps[0][0], "/studio/admit", body(cps[0]), "M5", 0)
        third = o3.ans.get("record") == o2.ans.get("record") and isinstance(o2.ans.get("record"), dict)
        tries = "; asked %d time%s for a camera path" % (f["tries"], "" if f["tries"] == 1 else "s")
        self.check("M4", 0, o2, cps[1][2], extra=req + ([] if third else ["a third copy pressed alike made another record"]))
        m4_refused = o2.ans.get("code") == "BINDING-MISMATCH"
        self.check("M5", 0, o1, cps[0][2], extra=req + ([] if m4_refused else ["the enforced copy (M4) did not refuse BINDING-MISMATCH"]))
        self.tries = tries
        # M4b / M4br, M9 (two runs), M20's unknown-as-match on M9: every candidate-side still bound
        d, rid, f, cps, bad = self.preview_copies("preview-all", None, 5, "m4b")
        self.m4_ids.append(("M4b's state", f))
        for (mid, i), c, preview in ((("M4b", 0), cps[0], "P_A"), (("M4br", 0), cps[1], "P_A"), (("M9", 0), cps[2], None), (("M9", 1), cps[3], None),
                                     (("M20", 8), cps[4], None)):
            o = self.press(c[0], "/studio/admit", {"id": rid, "candidate": "A", "still": c[3]["still"], "preview": c[2][preview] if preview else None}, mid, i)
            self.check(mid, i, o, c[2], extra=bad + (self.twin("M9", 0, "BINDING-UNKNOWN") if (mid, i) == ("M9", 1) else []),
                       case={("M9", 0): "B3 preview, honest"}.get((mid, i)))
        # M4k: two finished previews of A, each kept under its id
        d, rid, f = St.previewed("preview-k", 1)
        w = B.world(B.copy(d, "m4k"))
        w.g.restore(rid)
        sy = dict(f["syms"], n=len(f["plan"]["still_ticks"]), K=1, P_A=f["fin"]["preview_id"])
        plan2, fin2, line2 = St.preview(w, rid, k_base=None, scene_a=sy["S_A"], scene_base=sy["S_base"])
        rep2 = sha256(open(os.path.join(w.records, rid, "A.preview.report.json"), "rb").read())
        self.m4_ids.append(("M4k's second preview", {"plan": plan2, "fin": fin2, "line": line2, "report_sha256": rep2}))
        sy["P_A2"] = fin2.get("preview_id")
        own = [] if (sy["P_A2"] and sy["P_A2"] != sy["P_A"] and sy["P_A2"] == St.preview_id_rule(line2["binding"], line2["drawn"], rep2)) else \
            ["P_A2 %s is P_A or not its own id" % (sy["P_A2"] or "")[:12]]
        _c, s = w.still(rid, "A", sy["S_A"])
        o1 = self.press(w, "/studio/admit", {"id": rid, "candidate": "A", "still": s["still"], "preview": sy["P_A"]}, "M4k", 0)
        self.check("M4k", 0, o1, sy, extra=own)
        o2 = self.press(w, "/studio/admit", {"id": rid, "candidate": "A", "still": s["still"], "preview": sy["P_A2"]}, "M4k", 1)
        self.check("M4k", 1, o2, sy, extra=own + ([] if o1.ans.get("code") == "BINDING-MISMATCH" else ["the press naming P_A was not refused first"]))

    # ---------------------------------------------------------------------------------------------- the undo
    def g_undo(self):
        B, St = self.B, self.St
        # M6 / M7: an undo declaring #M, from equal starts
        cps = []
        for i in range(2):
            w, seqs = St.undo_world(St.admitted("two-admissions", 2), "m6-%d" % i)
            sy = St.undo_syms(w, seqs)
            cps.append((w, sy))
        same, said = B.equal(B.readings(cps[0][0], undo=True), B.readings(cps[1][0], undo=True))
        state = lambda sy: [] if (sy["u"].get("of") == sy["N"] and sy["u"].get("scene") == sy["S_w"] and sy["S_w"] and sy["M"]
                                   and int(sy["M"]) <= int(sy["N"]) - 2) else \
            ["GET /undo.json gave of %s scene %s; the target #%s (M #%s), the files' scene %s" % (
                sy["u"].get("of"), (sy["u"].get("scene") or "")[:12], sy["N"], sy["M"], sy["S_w"][:12])]
        o2 = self.press(cps[1][0], "/studio/undo", {"of": cps[1][1]["M"], "scene": cps[1][1]["S_w"]}, "M6", 0)
        o1 = self.press(cps[0][0], "/studio/undo", {"of": cps[0][1]["M"], "scene": cps[0][1]["S_w"]}, "M7", 0)
        req = ([] if same else [said]) + state(cps[1][1])
        self.check("M6", 0, o2, cps[1][1], extra=req, case="B1 undo, honest")
        refused = o2.ans.get("code") == "BINDING-MISMATCH"
        self.check("M7", 0, o1, cps[0][1],
                   extra=req + ([] if refused else ["the enforced copy (M6) did not refuse BINDING-MISMATCH"]))
        # M6b, M6br, M10 (two runs), M10b, M20's unknown-as-match on M10
        for (mid, i), of, scene, case in ((("M6b", 0), "N", "S_w", "B5 undo, honest"), (("M6br", 0), "N", "S_w", None), (("M10", 0), None, "S_w", "B3 undo of, honest"),
                                          (("M10", 1), None, "S_w", None), (("M10b", 0), "N", None, "B3 undo scene, honest"), (("M20", 9), None, "S_w", None)):
            o, sy, bad, _w = case_undo_bound(B, St, "%s-%d" % (mid.lower(), i), switched(self.run(mid, i)), of=of, scene=scene)
            self.check(mid, i, o, sy, extra=bad + (self.twin("M10", 0, "BINDING-UNKNOWN") if (mid, i) == ("M10", 1) else []), case=case)
        # M23's first run: Undo pressed before GET /undo.json is read (the page sends of "" and scene ""), then again
        # after a fresh read
        w, seqs = St.undo_world(St.admitted("two-admissions", 2), "m23-0")
        sy = St.undo_syms(w, seqs)
        sy["S_sent"] = ""
        sy["compare"] = lambda x: self.S.compare("undo", x["field"], {"present": True, "value": x["declared"]}, x["expected"])["outcome"]
        o1 = B.press(w, "/studio/undo", {"of": "", "scene": ""})
        _c, u = w.get("/undo.json?world=%s" % BRIEF)
        o2 = B.press(w, "/studio/undo", {k: u[k] for k in ("of", "scene") if k in u})
        run = self.run("M23", 0)
        p1 = hold(self.S, run, o1, sy, over={"answer": "BINDING-UNKNOWN", "ledger": "+1", "brief": "same", "certificate": "none"})
        p2 = hold(self.S, dict(run, record="", names=None), o2, sy, over={"answer": "undone", "ledger": "+2", "brief": "changed",
                                                                          "certificate": TODAY["undo certificates"]})
        B.say(run["row"], not (p1 + p2), "the first press: %s; after a fresh read: %s%s" % (o1.said(), o2.said(), ("; " + "; ".join(p1 + p2)) if p1 + p2 else ""))
        B.keep("M23", "the window, Undo before the read", o1)

    # ---------------------------------------------------------------------------------------------- BIND-NOTSUFFICIENT-0
    def g_b4(self):
        B, St = self.B, self.St

        def admit_state(kind, i):
            """B4's admission states, every binding declared bound (the still declaring S_A); `i` the run's index."""
            label = "m11-%d" % i
            if kind == "OUTSIDE":
                return case_outside(B, St, "S_A", label, switched(self.run("M11", i)))[:3]
            if kind == "FLAGGED":
                return case_flagged(B, St, label, switched(self.run("M11", i)))[:3]
            w, rid = St.at("unlogged" if kind == "UNLOGGED" else "plain", label)
            sy, bad = St.still_syms(w, rid)
            _c, s = w.still(rid, "A", sy["S_A"])
            if kind == "STALE":
                St.recorded(w)
                if St.scene_now(w, rid)[0] != sy["S_A"]:
                    bad.append("the comment line moved A's scene")
            return self.press(w, "/studio/admit", {"id": rid, "candidate": "A", "still": s["still"]}, "M11", i), sy, bad

        def undo_state(kind, i):
            label = "m11-%d" % i
            plant = switched(self.run("M11", i))
            if kind == "UNDO-UNLOGGED":
                return case_undo_unlogged(B, St, label, plant)[:3]
            tree = St.layout_tree() if kind == "UNDO-LAYOUT" else St.not_clean_tree()
            w, seqs = St.undo_world(tree, label)
            sy = St.undo_syms(w, seqs)
            u, bad = sy["u"], []
            if kind == "UNDO-LAYOUT":
                # OPEN-5: of the target's sequence number (read from the ledger) and scene S_wL, the files' exported scene,
                # held equal to the world's slot as served (GET /undo.json answers before its dry run there)
                sy["S_wL"] = sy["S_w"]
                served = w.live.slot(0)["sha"]
                if served != sy["S_wL"] or u.get("can") is not False or u.get("scene") != "":
                    bad.append("S_wL %s, the world's slot %s; GET /undo.json can %s scene %r" % (sy["S_wL"][:12], served[:12], u.get("can"), u.get("scene")))
                body = {"of": sy["N"], "scene": sy["S_wL"]}
            else:
                if u.get("of") != sy["N"] or u.get("scene") != sy["S_w"] or u.get("code") != "STUDIO-NOT-UNDOABLE":
                    bad.append("GET /undo.json gave of %s scene %s code %s" % (u.get("of"), (u.get("scene") or "")[:12], u.get("code")))
                body = {"of": u.get("of"), "scene": u.get("scene")}
            return B.press(w, "/studio/undo", body, plant), sy, bad

        kinds = ["OUTSIDE", "STALE", "FLAGGED", "UNLOGGED", "UNDO-LAYOUT", "UNDO-NOT-CLEAN", "UNDO-UNLOGGED"]
        today = {"OUTSIDE": TODAY["B4-OUTSIDE ledger"], "UNDO-UNLOGGED": TODAY["B4-UNDO-UNLOGGED ledger"]}
        for j, kind in enumerate(kinds):
            got = []
            for i in (2 * j, 2 * j + 1):
                got.append((undo_state if kind.startswith("UNDO") else admit_state)(kind, i))
            (oh, syh, badh), (oo, syo, bado) = got
            same = (oh.ans.get("code"), oh.ans.get("director_code", ""), oh.delta) == (oo.ans.get("code"), oo.ans.get("director_code", ""), oo.delta)
            eq = [] if same else ["on and switched off differ: %s/%s %+d against %s/%s %+d" % (
                oh.ans.get("code"), oh.ans.get("director_code", ""), oh.delta, oo.ans.get("code"), oo.ans.get("director_code", ""), oo.delta)]
            over = {"ledger": "+%d" % today[kind]} if kind in today else {}
            self.check("M11", 2 * j, oh, syh, over=over, extra=badh + eq, case="B4 %s, honest" % kind)
            self.check("M11", 2 * j + 1, oo, syo, over=over, extra=bado + eq)
        # M12: binding-sufficient on B4-OUTSIDE, B4-FLAGGED and B4-STALE
        o, sy, bad, _w = case_outside(B, St, "S_A", "m12-0", switched(self.run("M12", 0)))
        self.check("M12", 0, o, sy, extra=bad + self.twin("M11", 0, "ADMIT-OUTSIDE"))
        o, sy, bad, _w = case_flagged(B, St, "m12-1", switched(self.run("M12", 1)))
        self.check("M12", 1, o, sy, over={"director_code": M12_FLAGGED_DIRECTOR}, extra=bad + self.twin("M11", 4, "STUDIO-STILL-FLAGGED"))
        w, rid = St.at("plain", "m12-2")
        sy, bad = St.still_syms(w, rid)
        _c, s = w.still(rid, "A", sy["S_A"])
        St.recorded(w)
        o = self.press(w, "/studio/admit", {"id": rid, "candidate": "A", "still": s["still"]}, "M12", 2)
        self.check("M12", 2, o, sy, extra=bad + self.twin("M11", 2, "STUDIO-STALE"))

    # ---------------------------------------------------------------------------------------------- BIND-ORDER-0: B2
    def b2_world(self, label, preview=False):
        """B2's state: A drawn at H0 (restored there), its still sent declaring S_A0 (and for B2-preview, A previewed at
        H0, every candidate-side still naming S_A0); then the other canopy admitted, moving the files and the ledger to H1.
        S_A1 from the admission's own evaluation of A at H1, required to differ from S_A0."""
        St = self.St
        if preview:
            d, rid, f = St.previewed("preview-all", None)
            w = self.B.world(self.B.copy(d, label))
            w.g.restore(rid)
        else:
            w, rid = St.at("plain", label)
            f = None
        sy, bad = St.still_syms(w, rid)
        sy["S_A0"] = sy["S_A"]
        _c, s = w.still(rid, "A", sy["S_A0"])
        v, _a = St.move(w)
        sy["S_A1"], v1 = St.scene_now(w, rid)
        if v != "CLEAN" or sy["S_A1"] == sy["S_A0"] or not sy["S_A1"] or v1["verdict"] != "CLEAN" or "HEAD-MOVED" not in v1["codes"]:
            bad.append("B2's state did not hold: the move %s; S_A0 %s, S_A1 %s; A at H1 %s %s" % (v, sy["S_A0"][:12], sy["S_A1"][:12], v1["verdict"], ",".join(v1["codes"])))
        body = {"id": rid, "candidate": "A", "still": s["still"]}
        if f is not None:
            sy.update(n=len(f["plan"]["still_ticks"]), P_A0=f["fin"]["preview_id"])
            body["preview"] = sy["P_A0"]
        return w, sy, bad, body

    def g_b2(self):
        B, St = self.B, self.St
        for mid, i, case in (("M13", 0, "B2 still, stale first"), ("M14", 0, "B2 still, stale neutralized"), ("M15", 0, None), ("M17", 10, None),
                             ("M18", 0, None)):
            w, sy, bad, body = self.b2_world("%s-%d" % (mid.lower(), i))
            o = self.press(w, "/studio/admit", body, mid, i)
            extra = list(bad) + {"M14": self.twin("M13", 0, "STUDIO-STALE"), "M15": self.twin("M14", 0, "BINDING-MISMATCH"),
                                 "M17": self.twin("M13", 0, "STUDIO-STALE"), "M18": self.twin("M13", 0, "STUDIO-STALE")}.get(mid, [])
            if mid == "M18":
                e = [x for x in (o.ans.get("record") or {}).get("evidence", []) if x["kind"] == "still" and x["field"] == "scene"]
                if not (e and e[0]["outcome"] == "MATCH" and e[0]["expected"] == e[0]["declared"]):
                    extra.append("the record's still.scene entry is %s, not a MATCH" % (e[0] if e else "absent"))
            self.check(mid, i, o, sy, extra=extra, case=case)
        for i in range(3):
            w, sy, bad, body = self.b2_world("m13p-%d" % i, preview=True)
            o = self.press(w, "/studio/admit", body, "M13p", i)
            self.check("M13p", i, o, sy, extra=bad + ([], self.twin("M13p", 0, "STUDIO-STALE"), self.twin("M13p", 1, "BINDING-MISMATCH"))[i])
        # M13u: one admission #N; GET /undo.json read (S_w0); then the other canopy's statement edited by hand and recorded
        # (cmd_rebase): the target stays #N, the scene at the undo becomes S_w1
        for i in range(2):
            w, seqs = St.undo_world(St.admitted("one-admission", 1), "m13u-%d" % i)
            sy = St.undo_syms(w, seqs)
            sy["S_w0"] = sy["S_w"]
            bad = [] if (sy["u"].get("of") == sy["N"] and sy["u"].get("scene") == sy["S_w0"]) else ["GET /undo.json gave of %s scene %s" % (sy["u"].get("of"), sy["u"].get("scene"))]
            txt = open(w.art, "rb").read().decode("utf-8")
            if txt.count(OTHER_CANOPY + "\n") != 1:
                bad.append("the other canopy's statement is not in the brief once")
            open(w.art, "wb").write(txt.replace(OTHER_CANOPY + "\n", OTHER_CANOPY + " deep 2.6\n", 1).encode("utf-8"))
            self.S.quiet(self.D.cmd_rebase, w.ws(), "the other canopy deeper, by hand (BINDING-0's B2-undo)")
            sy["S_w1"] = w.ws().export()[0]["lineage"]["scene_sha256"]
            if sy["S_w1"] == sy["S_w0"]:
                bad.append("the hand edit did not move the scene")
            rebased = open(w.art, "rb").read()
            o = self.press(w, "/studio/undo", {"of": sy["N"], "scene": sy["S_w0"]}, "M13u", i)
            if i == 0 and open(w.art, "rb").read() != rebased:
                bad.append("the brief is not the rebased bytes")
            self.check("M13u", i, o, sy, extra=bad + (self.twin("M13u", 0, "BINDING-MISMATCH") if i else []), case="B2 undo, honest" if i == 0 else None)

    # ---------------------------------------------------------------------------------------------- BIND-ORDER-0: the order states
    def order_state(self, k, mid, i):
        """§7's order state `k` (M16's index), each with a binding failing too, pressed with run (mid, i)'s switches."""
        B, St = self.B, self.St
        label = "%s-%d" % (mid.lower(), i)
        plant = switched(self.run(mid, i))
        if k == 0:                  # no still sent; Admit names a still the host does not keep
            w, rid = St.at("plain", label)
            sy, bad = St.still_syms(w, rid)
            return B.press(w, "/studio/admit", {"id": rid, "candidate": "A", "still": sha256(self.D.selftest_still())}, plant), sy, bad, {}
        if k == 1:                  # STUDIO's drawn LEAKAGE candidate C, its still declaring the base scene
            w, rid = St.at("one_bad", label)
            sy, bad = St.still_syms(w, rid, "C")
            sy["S_base"] = w.ws().export()[0]["lineage"]["scene_sha256"]
            c = w.cand(rid, "C") or {}
            bad = [b for b in bad if not b.startswith("S_A")]
            if c.get("verdict") != "LEAKAGE" or c.get("slot") is None:
                bad.append("C is %s, drawn %s" % (c.get("verdict"), c.get("slot") is not None))
            _c, s = w.still(rid, "C", sy["S_base"])
            return B.press(w, "/studio/admit", {"id": rid, "candidate": "C", "still": s.get("still", "")}, plant), sy, bad, {}
        if k == 2:
            o, sy, bad, _w = case_outside(B, St, "S_base", label, plant)
            return o, sy, bad, {"ledger": "+%d" % TODAY["ADMIT-OUTSIDE ledger"]}
        if k in (3, 4, 5, 9):
            w, rid = St.at("unlogged" if k == 4 else "plain", label)
            sy, bad = St.still_syms(w, rid)
            _c, s = w.still(rid, "A", sy["S_base"], png=St.flagged_png() if k == 3 else None)
            if k == 5:
                St.recorded(w)
            over, hooked = {}, []
            if k == 9:
                def hook(name):
                    if name == "admit:lock-wait" and not hooked:
                        hooked.append(name)
                        open(w.art, "ab").write(COMMENT)
                        self.S.quiet(self.D.cmd_rebase, w.ws(), "another writer (BINDING-0's rows)")
                self.D.durable.HOOK = hook
            try:
                o = B.press(w, "/studio/admit", {"id": rid, "candidate": "A", "still": s["still"]}, plant)
            finally:
                self.D.durable.HOOK = None
            if k == 9 and not plant:
                events = self.D.led.read(w.ledger)[0]
                new = events[len(events) - o.delta:] if o.delta > 0 else []
                kinds = [e["kind"] for e in new]
                files_head = self.D.canon.head(w.ws().export()[1])
                after = o.after["art"]
                if not hooked or kinds != ["evaluate", "rebase"] or new[-1].get("head_after") != files_head:
                    bad.append("the commit fence's state: hooked %s, the new lines %s, the rebase's head_after %s the files' head" % (
                        bool(hooked), kinds, "is" if new and new[-1].get("head_after") == files_head else "is NOT"))
                if after != o.before["art"] + COMMENT or (new and new[-1].get("art_text", "").encode("utf-8") != after):
                    bad.append("the brief is not the brief before the press and the other writer's line, the rebase's art_text")
                if os.path.isdir(w.ledger + ".pending"):
                    bad.append("a pending folder was left")
                over = {"brief": "", "ledger": "+2"}
            return o, sy, bad, over
        if k in (6, 7):             # STUDIO-NOT-UNDOABLE: a layout target / an inverse not CLEAN; of declaring #M
            w, seqs = St.undo_world(St.layout_tree() if k == 6 else St.not_clean_tree(), label)
            sy = St.undo_syms(w, seqs)
            u, bad = sy["u"], []
            scene = "" if k == 6 else u.get("scene")
            if (k == 6 and (u.get("scene") != "" or u.get("code") != "STUDIO-NOT-UNDOABLE")) or \
                    (k == 7 and (u.get("scene") != sy["S_w"] or not sy["S_w"] or u.get("code") != "STUDIO-NOT-UNDOABLE")):
                bad.append("GET /undo.json gave scene %r code %s" % (u.get("scene"), u.get("code")))
            return B.press(w, "/studio/undo", {"of": sy["M"], "scene": scene}, plant), sy, bad, {}
        if k == 8:                  # no target: of declaring a sequence number, scene "" as GET /undo.json gives it
            w = B.world(B.copy(self.St.base("fresh", lambda: B.fixture("fresh")), label))
            _c, u = w.get("/undo.json?world=%s" % BRIEF)
            sy = {"M_any": "1"}
            bad = [] if (u.get("code") == "STUDIO-NOTHING-TO-UNDO" and u.get("scene") == "") else ["GET /undo.json gave code %s scene %r" % (u.get("code"), u.get("scene"))]
            return B.press(w, "/studio/undo", {"of": sy["M_any"], "scene": u.get("scene", "")}, plant), sy, bad, {}
        raise ValueError(k)

    def g_order(self):
        for k in range(10):
            o, sy, bad, over = self.order_state(k, "M16", k)
            self.check("M16", k, o, sy, over=over, extra=bad, case="the order state %d, honest" % k)
            want = self.run("M16", k)["answer"]
            o, sy, bad, over = self.order_state(k, "M17", k)
            self.check("M17", k, o, sy, extra=bad + self.twin("M16", k, want))

    # ---------------------------------------------------------------------------------------------- the account
    def g_account(self):
        B, St = self.B, self.St
        for i in range(2):
            plant = switched(self.run("M19", i))
            w, rid = St.at("plain", "m19-%d" % i, watch=True)
            wu, _s = St.undo_world(St.admitted("one-admission", 1), "m19u-%d" % i)
            self.S.BINDING_PLANT = plant
            try:
                seen = {"Gateway.account": w.g.account(rid, "A"), "/evidence.json's admission": (w.get("/evidence.json?world=%s&id=%s&candidate=A" % (
                    BRIEF, urllib.parse.quote(rid, safe="")))[1].get("admission")), "undo_target (/undo.json)": wu.get("/undo.json?world=%s" % BRIEF)[1],
                    "undo_target (nothing to undo)": w.get("/undo.json?world=%s" % BRIEF)[1]}
                t, acc = time.time(), None
                while time.time() - t < 120:
                    st = w.get("/live?world=%s" % BRIEF)[1]
                    a = st.get("accounts") or {}
                    if a.get("rev") == (st.get("rev") or {}).get("id") and a.get("request") == rid and "A" in (a.get("by_letter") or {}):
                        acc = a["by_letter"]
                        break
                    time.sleep(0.1)
                seen["/live's accounts"] = acc
            finally:
                self.S.BINDING_PLANT = ""
                w.live.acc_seen = 0.0
            said = [k for k, v in seen.items() if claims(v)]
            read = [k for k, v in seen.items() if v is not None]
            if not plant:
                B.say(self.run("M19", i)["row"], not said and len(read) == len(seen),
                      "read %s; none says a binding checked or matched%s" % (", ".join(read), "" if not said else ": NOT SO, " + ", ".join(said)))
            else:
                B.say(self.run("M19", i)["row"], bool(said), "the accounts that say a binding was checked and matched before any press: %s" % (", ".join(said) or "none"))

    # ---------------------------------------------------------------------------------------------- the registered rule the authority
    def g_conformance(self):
        B, S, V = self.B, self.S, self.V
        bad, n = [], 0
        for v in V["field"]["vectors"]:
            n += 1
            e = S.compare(v["kind"], v["field"], v["declared"], v.get("expected", ""), finished=v.get("finished_previews_of_candidate"))
            if e != v["entry"]:
                bad.append("%s: %s, not %s" % (v["id"], e, v["entry"]))
        B.say(self.run("M20", 2)["row"], n and not bad, "%d field vectors, every entry the frozen one%s" % (n, ("; " + "; ".join(bad))[:600] if bad else ""))
        bad, n = [], 0
        for v in V["piece"]["vectors"]:
            n += 1
            if S.piece(v["fields"]) != v["piece"]:
                bad.append("%s: %s" % (v["id"], S.piece(v["fields"])))
        for v in V["piece"]["order"]:
            n += 1
            if S.preview_order({k: "" for k in v["drawn"]}) != v["fields"]:
                bad.append("%s: %s" % (v["id"], S.preview_order({k: "" for k in v["drawn"]})))
        B.say(self.run("M20", 3)["row"], n and not bad, "%d piece and order vectors held%s" % (n, ("; " + "; ".join(bad)) if bad else ""))
        bad, n = [], 0
        for v in V["press"]["vectors"]:
            n += 1
            got = S.press(v["entries"])
            want = ("", v["names"]) if v["answer"].startswith("none") else (v["answer"], v["names"])
            if got != want:
                bad.append("%s: %s, not %s" % (v["id"], got, want))
        B.say(self.run("M20", 4)["row"], n and not bad, "%d press vectors held%s" % (n, ("; " + "; ".join(bad)) if bad else ""))
        bad, n = [], 0
        for v in V["record"]["vectors"]:
            n += 1
            r = v["record"]
            b = S.record_bytes(S.record(r["operation"], r["candidate"], r["intent_sha256"], r["of"], r["evidence"], r["decision"], r["director_code"]))
            if b != v["bytes"].encode("ascii") or sha256(b) != v["sha256"]:
                bad.append("%s: %s" % (v["id"], b[:80]))
        B.say(self.run("M20", 5)["row"], n and not bad, "%d record vectors held byte for byte, each its sha256%s" % (n, ("; " + "; ".join(bad)) if bad else ""))
        # the preview id: the vectors, then every finished preview of M4's, M4b's and M4k's states, through its finish's
        # answer and its log line, against v0's rule written out here
        bad, n = [], 0
        for v in V["preview id"]["vectors"]:
            n += 1
            o = v["object"]
            got = S.preview_id(o["binding"], o["drawn"], o["report_sha256"])
            rule = self.St.preview_id_rule(o["binding"], o["drawn"], o["report_sha256"])
            if not (got == rule == v["preview_id"] == sha256(v["bytes"].encode("ascii"))):
                bad.append("%s: %s" % (v["id"], got[:12]))
        for label, f in self.m4_ids:
            n += 1
            ln, fin = f["line"], f["fin"]
            rule = self.St.preview_id_rule(ln.get("binding") or {}, ln.get("drawn") or {}, f["report_sha256"])
            ok = (fin.get("preview_id") == ln.get("preview_id") == rule == S.preview_id(ln["binding"], ln["drawn"], f["report_sha256"])
                  and ln.get("files", {}).get("preview.report.json") == f["report_sha256"] and ln.get("binding") == f["plan"].get("binding")
                  and set(ln.get("drawn") or {}) == {"%s-%d" % (s_, k) for s_ in ("base", "candidate") for k in range(len(f["plan"]["still_ticks"]))})
            if not ok:
                bad.append("%s: the finish's %s, the line's %s, the rule's %s" % (label, (fin.get("preview_id") or "")[:12], (ln.get("preview_id") or "")[:12], rule[:12]))
        B.say(self.run("M20", 1)["row"], len(self.m4_ids) >= 3 and not bad,
              "%d ids held: the %d vectors, and the finished previews of %s, each its finish's preview_id and its log line's equal to the rule over its "
              "recorded binding, drawn scenes and report's sha256%s%s" % (n, len(V["preview id"]["vectors"]), ", ".join(x[0] for x in self.m4_ids) or "none",
                                                                          getattr(self, "tries", ""), ("; " + "; ".join(bad)) if bad else ""))

    def g_keeping(self):
        """The keeping vectors through POST /studio/still and POST /studio/preview/still (the kept value in the route's
        answer and in the host's own state), and the keeping case-folded."""
        B, St, V = self.B, self.St, self.V
        d, rid, _f = St.previewed("preview-all", None)          # a request with a camera path
        w = B.world(B.copy(d, "m20-0"))
        w.g.restore(rid)
        c, plan = w.post("/studio/preview", {"id": rid, "candidate": "A"})
        bad, n = [], 0
        if c != 200:
            bad.append("no preview plan (%s): POST /studio/preview/still not held" % plan.get("code"))
        png = self.D.selftest_still()
        for v in V["keeping"]["vectors"]:
            n += 1
            q = v["scene_query"]
            _c, a = w.still(rid, "A", raw_query=q)
            held = (w.cand(rid, "A").get("still") or {}).get("scene")
            if a.get("scene") != v["kept"] or held != v["kept"]:
                bad.append("%s: /studio/still kept %r (the host's state %r), not %r" % (v["id"], a.get("scene"), held, v["kept"]))
            if c == 200:
                _c2, a2 = w.post_png("/studio/preview/still?id=%s&candidate=A&side=candidate&k=0%s" % (urllib.parse.quote(rid, safe=""), ("&" + q) if q else ""), png)
                drawn = (w.cand(rid, "A").get("preview") or {}).get("drawn", {}).get("candidate-0")
                if a2.get("scene") != v["kept"] or drawn != v["kept"]:
                    bad.append("%s: /studio/preview/still kept %r (the host's state %r), not %r" % (v["id"], a2.get("scene"), drawn, v["kept"]))
        B.say(self.run("M20", 0)["row"], n and not bad, "%d keeping vectors through both routes, each the frozen value in the answer and in the host's state%s" % (
            n, ("; " + "; ".join(bad))[:700] if bad else ""))
        k1 = [v for v in V["keeping"]["vectors"] if v["id"] == "K1"][0]
        self.S.BINDING_PLANT = switched(self.run("M20", 11))
        try:
            _c, a = w.still(rid, "A", raw_query=k1["scene_query"])
        finally:
            self.S.BINDING_PLANT = ""
        B.say(self.run("M20", 11)["row"], a.get("scene") not in (None, k1["kept"]), "K1's upper-case scene kept as %r where the rule keeps %r" % (a.get("scene"), k1["kept"]))

    def g_pin(self):
        B, S = self.B, self.S

        def problems():
            v0 = register_v0()
            pin = S.binding_pin()
            if v0 is None:
                return ["the register has no version-0 line of BINDING-0"]
            out = []
            if (pin["contract"], pin["version"], pin["sha256"]) != (v0["contract"], v0["version"], v0["sha256"]):
                out.append("the host pins %s version %s sha256 %s; the register's line %s version %s sha256 %s" % (
                    pin["contract"], pin["version"], pin["sha256"], v0["contract"], v0["version"], v0["sha256"]))
            if S.BINDING_VERSION != v0["version"]:
                out.append("BINDING_VERSION %s" % S.BINDING_VERSION)
            return out
        p = problems()
        B.say(self.run("M20p", 0)["row"], not p, "; ".join(p) or "BINDING-0 version 0 sha256 %s, the host's pin and the register's line" % S.BINDING_SHA256[:16])
        S.BINDING_PLANT = switched(self.run("M20p", 1))
        try:
            p = problems()
        finally:
            S.BINDING_PLANT = ""
        B.say(self.run("M20p", 1)["row"], bool(p), "refused: " + ("; ".join(p) or "nothing"))

    # ---------------------------------------------------------------------------------------------- the window, and M24
    def g_window(self):
        B, St = self.B, self.St
        # M23's second run: a dead writer's pending folder whose recovery writes none of the brief's files (no manifest)
        w, seqs = St.undo_world(St.admitted("one-admission", 1), "m23-1")
        os.makedirs(w.ledger + ".pending")
        open(os.path.join(w.ledger + ".pending", "old.0"), "wb").write(b"prepared, never committed (BINDING-0's rows)")
        sy = St.undo_syms(w, seqs)
        u = sy["u"]
        sy["S_u"] = sy["S_w"]
        bad = [] if (u.get("can") is None and u.get("of") == sy["N"] and u.get("scene") == "") else ["GET /undo.json gave can %s of %s scene %r" % (u.get("can"), u.get("of"), u.get("scene"))]
        o = B.press(w, "/studio/undo", {"of": "", "scene": ""})
        self.check("M23", 1, o, sy, extra=bad, case="the window, a dead writer's pending folder")
        # M24: a still's kept file removed after it was posted
        o, sy, bad, _w = case_kept_removed(B, St, "m24", "")
        sy["the code answered"] = TODAY["M24 answer"]
        self.check("M24", 0, o, sy, over={"answer": TODAY["M24 answer"], "ledger": "+%d" % TODAY["M24 ledger"]}, extra=bad, case="a kept still removed")


# ------------------------------------------------------------------------------------------------ STUDIO's entry
def studio_rows(row, P):
    """BINDING-0's rows of the 0253 matrix, in scratch trees of their own (art/play.py's studio_selftest calls this with
    its row printer and the play module). Every matrix row is printed, failed when it was not run; the self-test's
    decision records are printed beside their cases (v0 decision record.self-test) for acceptance 4's comparison."""
    saved_root = P.ROOT
    B = Bench(P, row)
    M, V, problems = frozen()
    try:
        if problems:
            raise RuntimeError("; ".join(problems))
        St = States(B)
        R = Rows(B, St, M, V)
        R.group(["M20p"], R.g_pin)
        R.group(["M1", "M2", "M3", "M3r", "M3s", "M8", "M20"], R.g_still)
        R.group(["M4", "M5", "M4b", "M4br", "M4k", "M9", "M20"], R.g_preview)
        R.group(["M6", "M7", "M6b", "M6br", "M10", "M10b", "M20", "M23"], R.g_undo)
        R.group(["M11", "M12"], R.g_b4)
        R.group(["M13", "M14", "M15", "M13p", "M13u", "M17", "M18"], R.g_b2)
        R.group(["M16", "M17"], R.g_order)
        R.group(["M19"], R.g_account)
        R.group(["M20"], R.g_conformance)
        R.group(["M20"], R.g_keeping)
        R.group(["M23", "M24"], R.g_window)
    except Exception as e:  # noqa: BLE001 — the frozen files did not hold: every row fails, said
        for r in M.get("rows", []):
            for x in r["runs"]:
                if x["row"] not in B.printed and not x["row"].startswith("("):
                    B.say(x["row"], False, "%s: %s" % (type(e).__name__, str(e)[:300]))
    finally:
        for r in M.get("rows", []):
            for x in r["runs"]:
                if x["row"] not in B.printed and not x["row"].startswith("("):
                    B.say(x["row"], False, "not run")
        for mid, case, raw in B.records:
            print("BINDING-0 RECORD %s (%s) sha256 %s %s" % (mid, case, sha256(raw), raw.decode("ascii")))
        B.close()
        P.ROOT = saved_root
