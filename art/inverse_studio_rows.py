# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/inverse_studio_rows.py — 0254's rows of STUDIO SELFTEST (python art/studio.py selftest) after ST1 and ST2 (those two
# are the restoration's, in art/page_dash.py): the frozen test matrix's ST4, ST5, GD9-fresh, GD9-stale, GD10, GD11, GD12
# and OU5 (art/director/inverse/0254-matrix.json, suite "STUDIO SELFTEST"), in that order, each printed with the name the
# matrix freezes. Every state is built in a scratch tree of its own (the fixture's world, art/binding_rows.py's Bench and
# World: a Live, its server and the scripted provider's gateway on the tree), its admissions made by the director's command
# line, never the working brief, ledger or tags. A row that is not a plant row never prints the word plant (R5,
# tools/rung.py, reads a bracketed row naming it as a planted defect); the one plant of these rows, kept-inverse-unbound
# (studio.ACCOUNT_PLANT), is set by its row alone and put back. Standard library only.

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import binding_rows  # noqa: E402 — the scratch trees, the worlds on them and their presses (0253's)

BRIEF = binding_rows.BRIEF
SCOPE = ["**", "env/**"]
N_LINE = "= lamp north-lane 255,170,90 500 4"            # #N: an '=' whose inverse is one '@=' line
M_LINE = "= lamp north-lane 255,170,90 500 4"            # GD10's #M (above #N's row)
N10_LINE = "= lamp south-flank 210,225,255 400 2"        # GD10's #N
PLUS_LINE = "+ lamp mid-west 255,170,90 600 2"               # GD12's '+'


class Ctx:
    def __init__(self, P, row):
        self.P, self.row = P, row
        self.B = binding_rows.Bench(P, row)
        self.D, self.S = self.B.D, self.B.S
        sys.path.insert(0, os.path.join(HERE, "director"))
        import inverse_freeze
        self.M, self.V, _l, self.problems = inverse_freeze.frozen()
        suite = [s for s in (self.M or {}).get("suites", []) if s["suite"] == "STUDIO SELFTEST"]
        self.rows = {r["id"]: r for r in suite[0]["rows"]} if suite else {}
        self.plants = {p["id"]: p for p in (self.M or {}).get("plants", []) if p["suite"] == "STUDIO SELFTEST"}

    def say(self, name, ok, detail, plant=False):
        detail = " ".join(str(detail).split())
        if not plant:
            detail = re.sub(r"\bplant\b", "switch", detail)
        self.row(name, ok, detail[:900])

    def ws(self, root):
        return self.D.Workspace(BRIEF, root)

    def tree(self, label, lines):
        """The fixture's world with `lines` admitted one by one by the command line (cmd_evaluate, cmd_admit with the
        self-test's still): (root, [admit events])."""
        d = self.B.fixture(label)
        ws, out = self.ws(d), []
        for n, ln in enumerate(lines):
            p = self.D.current_parts(ws)
            doc = {"base": {k: p[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}, "brief": BRIEF, "candidate": "N",
                   "format": "VERDANDI-INTENT", "layout": [], "prompt": "0254's rows (%s)" % label, "rationale": "a command line's admission",
                   "revision": [ln], "scope": list(SCOPE), "version": "0"}
            f = os.path.join(d, "n%d.intent" % n)
            open(f, "wb").write(self.D.canon.dumps(doc))
            r = self.S.quiet(self.D.cmd_evaluate, ws, [f], quiet=True)[0]
            if r[2] != "CLEAN":
                raise RuntimeError("the state's evaluation of %r is %s %s" % (ln, r[2], r[3]))
            out.append(self.S.quiet(self.D.cmd_admit, ws, r[4], chooser="a command line (0254's rows)", still=self.D.selftest_still()))
        return d, out

    def rebase(self, root, text, note):
        open(os.path.join(root, "art", "briefs", BRIEF + ".art"), "wb").write(text.encode("utf-8"))
        self.S.quiet(self.D.cmd_rebase, self.ws(root), note)

    @staticmethod
    def position(a):
        """The position the admission's one '@=' or '@+' inverse line records."""
        ln = a["inverse"][0]
        return int(json.loads(ln[3:])[0])

    def events(self, root):
        return self.D.led.read(os.path.join(root, "art", "ledger", BRIEF + ".ledger"))[0]

    def undo_get(self, w):
        return w.get("/undo.json?world=%s" % BRIEF)

    def press(self, w, u):
        return self.B.press(w, "/studio/undo", {k: u[k] for k in ("of", "scene") if k in u})


def st4(c):
    D, canon = c.D, c.D.canon
    d, (a,) = c.tree("st4", [N_LINE])
    ev = c.events(d)
    k = int(a["seq"])
    f, val = canon.inverse_form(ev[k]["inverse"][0])
    ev[k] = dict(ev[k], inverse=[canon.inverse_line(f, [val[0], val[1], val[2].replace(" 600 ", " 650 ")])])
    prev, lines = D.led.ZERO, []
    for e in ev:
        b = canon.dumps(dict(e, prev=prev))
        lines.append(b)
        prev = canon.sha256(b)
    open(os.path.join(d, "art", "ledger", BRIEF + ".ledger"), "wb").write(b"".join(x + b"\n" for x in lines))
    w = c.B.world(d)
    try:
        _code, u = c.undo_get(w)
        o = c.press(w, u)
    finally:
        c.B.shut(w)
    ok = u.get("can") is False and u.get("code") == "STUDIO-DIRECTOR-REFUSED" and u.get("director_code") == "LEDGER-INVERSE" \
        and o.code != 200 and o.ans.get("code") == "STUDIO-DIRECTOR-REFUSED" and o.ans.get("director_code") == "LEDGER-INVERSE" and o.delta == 0 and not o.changed
    return ok, "#%s's stored '@=' forged: GET /undo.json %s/%s; the press %s" % (a["seq"], u.get("code"), u.get("director_code"), o.said())


def st5(c):
    D, S = c.D, c.S
    d, (a,) = c.tree("st5", [N_LINE])
    w = c.B.world(d)
    try:
        path = os.path.join(w.certs, "%s.json" % a["seq"])
        made = os.path.exists(path)
        cert = json.loads(open(path, "rb").read().decode("utf-8")) if made else {}
        own = made and cert["ledger"]["seq"] == a["seq"] and cert["inverse"]["revision"] == a["inverse"]
        cert["inverse"] = dict(cert.get("inverse") or {}, revision=["- lamp zz"])
        body = (json.dumps(cert, sort_keys=True, indent=1, ensure_ascii=True) + "\n").encode("ascii")
        open(path, "wb").write(body)
        _c1, u = c.undo_get(w)
        honest = (u.get("undone_certificate") or {})
        S.ACCOUNT_PLANT = "kept-inverse-unbound"
        try:
            _c2, u2 = c.undo_get(w)
        finally:
            S.ACCOUNT_PLANT = ""
        planted = (u2.get("undone_certificate") or {})
        untouched = open(path, "rb").read() == body
    finally:
        c.B.shut(w)
    ok = own and honest.get("made", "").startswith("from the ledger now; not kept") and "another event's" in honest.get("made", "") \
        and honest.get("ok") is True and honest.get("exact") is True and untouched
    caught = planted.get("made") == "kept" and planted.get("ok") is False
    c.say(c.rows["ST5"]["printed"][0], ok, "#%s's kept certificate (its own at the start: %s) given another inverse, its sequence number and event sha256 its own: "
          "%s, ok %s, exact %s; the kept file untouched %s" % (a["seq"], own, honest.get("made"), honest.get("ok"), honest.get("exact"), untouched))
    p = c.plants.get("kept-inverse-unbound")
    c.say(p["printed"] if p else c.rows["ST5"]["printed"][1], caught,
          "the certificate given: %s, ok %s, codes %s (the ledger's own is exact)" % (planted.get("made"), planted.get("ok"), [x.split(":")[0] for x in planted.get("codes") or []]),
          plant=True)
    return None


def inserted(c, d, a, row, note):
    ws = c.ws(d)
    rows = ws.text().split("\n")
    rows.insert(c.position(a), row)
    c.rebase(d, "\n".join(rows), note)


def gd9_fresh(c):
    d, (a,) = c.tree("gd9-fresh", [N_LINE])
    w = c.B.world(d)
    try:
        inserted(c, d, a, "# a row inserted above #%s's (0254's GD9)" % a["seq"], "a comment row inserted above the admission's row")
        _code, u = c.undo_get(w)
        o = c.press(w, u)
        last = c.events(d)[-1]
    finally:
        c.B.shut(w)
    refused = last["kind"] == "evaluate" and last["verdict"]["verdict"] == "REFUSED" and last["verdict"]["codes"] == ["INTENT-APPLY"]
    ok = u.get("of") == a["seq"] and o.code != 200 and o.ans.get("code") == "STUDIO-NOT-UNDOABLE" and o.delta == 1 and refused and not o.changed
    return ok, "%s; the evaluation appended %s %s. A changed expectation, said: at 7dee210 this was undone, statements-not-bytes" % (
        o.said(), last["verdict"]["verdict"], last["verdict"]["codes"])


def gd9_stale(c):
    d, (a,) = c.tree("gd9-stale", [N_LINE])
    w = c.B.world(d)
    try:
        _code, u = c.undo_get(w)
        s0 = c.ws(d).export()[0]["lineage"]["scene_sha256"]
        inserted(c, d, a, "lamp mid-east 255,170,90 600 2", "a lamp statement inserted above the admission's row")
        s1 = c.ws(d).export()[0]["lineage"]["scene_sha256"]
        o = c.press(w, {"of": u.get("of"), "scene": u.get("scene")})
    finally:
        c.B.shut(w)
    b = o.ans.get("binding") or {}
    rec = o.ans.get("record") or {}
    not_reached = b.get("checked") is False and b.get("why") == "STUDIO-NOT-UNDOABLE" and isinstance(rec, dict) \
        and all(e.get("outcome") == "not reached" for e in rec.get("evidence", [])) and len(rec.get("evidence", [])) == 2
    ok = u.get("of") == a["seq"] and u.get("scene") == s0 and s1 != s0 and o.code != 200 and o.ans.get("code") == "STUDIO-NOT-UNDOABLE" \
        and o.delta == 1 and not_reached and not o.changed
    return ok, "declared of %s and the scene before the insertion (%s, now %s); %s; binding %s. A changed expectation, said: at 7dee210 BINDING-MISMATCH +1" % (
        u.get("of"), s0[:12], s1[:12], o.said(), b)


def gd10_11(c):
    d, (m, n) = c.tree("gd10", [M_LINE, N10_LINE])
    parent_n = c.D.replay(c.ws(d), c.events(d)[:int(n["seq"])])["art"]
    child_n = c.ws(d).text()
    w = c.B.world(d)
    try:
        inserted(c, d, n, "# a row inserted above #%s's and below #%s's (0254's GD10)" % (n["seq"], m["seq"]), "a comment row inserted above the latest admission's row")
        said = []
        for _i in range(2):
            _code, u = c.undo_get(w)
            o = c.press(w, u)
            last = c.events(d)[-1]
            names = "admission #%s " % n["seq"] in json.loads(last["intent"]).get("rationale", "") if last["kind"] == "evaluate" else False
            said.append((u.get("of"), o.ans.get("code"), o.delta, names, o))
        ok10 = all(of == n["seq"] and code == "STUDIO-NOT-UNDOABLE" and delta == 1 and names for of, code, delta, names, _o in said)
        c.say(c.rows["GD10"]["printed"][0], ok10, "#%s (latest) and #%s (earlier, its row untouched): %s" % (
            n["seq"], m["seq"], "; ".join("GET /undo.json of #%s, the press %s %+d, its evaluation of #%s's inverse %s" % (of, code, delta, n["seq"], names)
                                          for of, code, delta, names, _o in said)))
        c.rebase(d, child_n, "the inserted row taken away again")
        _code, u = c.undo_get(w)
        o = c.press(w, u)
        res = o.ans.get("restoration") or {}
        art = open(os.path.join(d, "art", "briefs", BRIEF + ".art"), "rb").read()
    finally:
        c.B.shut(w)
    ok11 = o.code == 200 and o.ans.get("of") == n["seq"] and art == parent_n.encode("utf-8") and res.get("art_bytes") is True
    c.say(c.rows["GD11"]["printed"][0], ok11, "%s; restoration %s, art bytes %s; the art #%s's parent byte for byte %s" % (
        o.said(), res.get("verdict"), res.get("art_bytes"), n["seq"], art == parent_n.encode("utf-8")))
    return None


def gd12(c):
    d, (a,) = c.tree("gd12", [PLUS_LINE])
    parent = c.D.replay(c.ws(d), c.events(d)[:int(a["seq"])])["art"]
    v = [x for x in c.V["guards"]["vectors"] if x["id"] == "G-KEY-EDITED"][0]
    w = c.B.world(d)
    try:
        text = c.ws(d).text()
        edited = text.replace("lamp mid-west 255,170,90 600 2", "lamp mid-west 255,170,90 500 2", 1)
        c.rebase(d, edited, "the added row edited in place")
        _code, u = c.undo_get(w)
        o = c.press(w, u)
        res = o.ans.get("restoration") or {}
        art = open(os.path.join(d, "art", "briefs", BRIEF + ".art"), "rb").read().decode("utf-8")
    finally:
        c.B.shut(w)
    ok = a["inverse"] == ["- lamp mid-west"] and edited != text and o.code == 200 and res.get("verdict") == "exact" and art == parent and "lamp mid-west" not in art \
        and v["expect"] == "equal to the parent"
    return ok, "#%s's inverse %s; its row edited and recorded; %s; restoration %s; the art the parent byte for byte %s, the recorded edit gone %s (G-KEY-EDITED: %s)" % (
        a["seq"], a["inverse"], o.said(), res.get("verdict"), art == parent, "lamp mid-west" not in art, v["expect"])


def ou5(c):
    S = c.S
    rid = "20261020T000000-0001"

    def response(line):
        return json.dumps({"format": S.RESPONSE, "version": S.VERSION, "id": rid, "provider": {"name": "selftest", "model": "m"},
                           "candidates": [{"title": "deeper", "rationale": "a revision", "revision": [line], "scope": ["plaza/canopy/*"], "preserve": []}],
                           "outcome": {"kind": "none", "unmet": [], "questions": [], "reason": "", "note": ""}}).encode("utf-8")
    control = "= canopy plaza concrete_slab 7.0 19,10 28,11 deep 2.6"
    S.read_response(response(control), rid)
    try:
        S.read_response(response('@= ["60","canopy plaza concrete_slab 7.0 19,10 28,11 deep 2.6","canopy plaza concrete_slab 7.0 19,10 28,11"]'), rid)
        got = "read"
    except S.StudioError as e:
        got = e.code
    return got == "STUDIO-RESPONSE-REVISION", "an ordinary line read; an '@=' line: %s" % got


ORDER = (("ST4", st4), ("ST5", st5), ("GD9-fresh", gd9_fresh), ("GD9-stale", gd9_stale), ("GD10", gd10_11), ("GD12", gd12), ("OU5", ou5))


def studio_rows(row, P):
    """0254's STUDIO rows (art/play.py's studio_selftest calls this with its row printer and the play module)."""
    saved_root = P.ROOT
    c = Ctx(P, row)
    try:
        for rid, fn in ORDER:
            names = (c.rows.get(rid) or {}).get("printed") or [rid]
            if c.problems or not c.rows:
                c.say(names[0], False, "the 0254 freeze does not read: %s" % "; ".join(c.problems)[:300])
                continue
            try:
                got = fn(c)
            except Exception as e:  # noqa: BLE001 — a row that raised fails, named by its type; the rows after it run
                got = (False, "raised %s: %s" % (type(e).__name__, str(e)[:300]))
                c.S.ACCOUNT_PLANT = ""
                if rid == "ST5":
                    c.say(names[0], False, got[1])
                    c.say(c.plants["kept-inverse-unbound"]["printed"], False, got[1], plant=True)
                    continue
                if rid == "GD10":
                    c.say(names[0], False, got[1])
                    c.say(c.rows["GD11"]["printed"][0], False, got[1])
                    continue
            if got is not None:
                c.say(names[0], got[0], got[1])
    finally:
        c.S.ACCOUNT_PLANT = ""
        c.B.close()
        P.ROOT = saved_root
