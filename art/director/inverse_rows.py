# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/director/inverse_rows.py — 0254's rows of DIRECTOR SELFTEST (python art/director.py selftest): the frozen test
# matrix's suite "DIRECTOR SELFTEST" (art/director/inverse/0254-matrix.json), rows FZ1 to OU9, each printed with the name
# the matrix freezes and every expectation read only through inverse_freeze.frozen() (the vectors, the matrix, the
# legacy ledger copy, each held to its sha256). DS1, the matrix's first row, is the lifecycle's own four rows (cmd_selftest).
#
# THE RULE (the matrix's 'the rule', spec §8): the rows run once honest, every one required to pass, and then once per
# value of the switch director.INVERSE_PLANT the matrix names for this suite: under each, the row that catches it fails,
# every row before it passes, and the rows after it that fail are exactly the frozen list of later failures, no more and
# no fewer. A plant is printed "PASS plant: <id> — caught by <row id>; …" (R5, tools/rung.py, keys it by "plant: <id>");
# no other row of these names that word. Every row catches whatever it raises; an exception that is neither an
# IntentError nor a LedgerError is that row's failure, named by its type, so that no plant ends the suite.
#
# Every state is built in a scratch tree of its own (the director's selftest_tree: the fixture's world), never the
# working brief, ledger or tags. A mismatch with the frozen lists is a new freeze, never an edit to them. Standard library
# only.

import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import binding  # noqa: E402
import inverse_freeze as IF  # noqa: E402

SUITE = "DIRECTOR SELFTEST"
BRIEF = "plaza-night"
# N_TREE (the matrix's readings): #N an admission of '-' of a statement that is not the last
N_LINE = "- lamp north-lane"
# OU9's #M and #N: two statements that are not the last, with a row between them after both are gone
M9_LINE, N9_LINE = "- lamp north-lane", "- lamp north-flank"
OTHER_LINE = "- lamp south-lane"


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def quiet(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **k)


class Ctx:
    """One run of the rows: the director (module), the freeze as frozen() read it, a scratch folder, the plant set."""

    def __init__(self, D, M, V, L):
        self.D, self.M, self.V, self.L = D, M, V, L
        self.canon, self.led = D.canon, D.led
        self.tmp = tempfile.mkdtemp(prefix="inverse-rows-")
        self.n = 0
        self.P = {k: v["text"] for k, v in V["parents"].items()}
        self.by_id = {}
        for sec in ("revisions", "cr", "guards", "only", "legacy", "legacy-inverses", "forms"):
            for v in V[sec]["vectors"]:
                self.by_id[v["id"]] = (sec, v)
        self.bases = {}

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def path(self, label):
        self.n += 1
        return os.path.join(self.tmp, "%02d-%s" % (self.n, label))

    def v(self, vid):
        return self.by_id[vid][1]

    # trees
    def tree(self, label):
        d = self.path(label)
        return self.D.selftest_tree(d)

    def copy(self, ws, label):
        d = self.path(label)
        shutil.copytree(ws.root, d)
        return self.D.Workspace(BRIEF, d)

    def intent(self, ws, revision, cand="X", scope=("**",)):
        p = self.D.current_parts(ws)
        return {"base": {k: p[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}, "brief": ws.brief, "candidate": cand,
                "format": "VERDANDI-INTENT", "layout": [], "prompt": "0254's rows", "rationale": "0254's rows", "revision": list(revision),
                "scope": list(scope), "version": "0"}

    def write(self, ws, revision, cand="X"):
        f = os.path.join(ws.root, "%s-%d.intent" % (cand, self.n))
        self.n += 1
        with open(f, "wb") as fh:
            fh.write(self.canon.dumps(self.intent(ws, revision, cand)))
        return f

    def evaluate(self, ws, revision, cand="X", inverse_of=""):
        """cmd_evaluate of one intent: (verdict, codes, seq)."""
        r = quiet(self.D.cmd_evaluate, ws, [self.write(ws, revision, cand)], quiet=True, inverse_of=inverse_of)[0]
        return r[2], r[3], r[4]

    def admit_one(self, ws, line):
        """An admission of `line` by cmd_evaluate and cmd_admit with the self-test's still."""
        verdict, codes, seq = self.evaluate(ws, [line], "N")
        if verdict != "CLEAN":
            raise RuntimeError("the state's evaluation of %r is %s %s" % (line, verdict, codes))
        return quiet(self.D.cmd_admit_still, ws, seq)

    def n_tree(self):
        """N_TREE: the fixture's world and #N, '- lamp north-lane' admitted with a still (built once per run)."""
        if "n" not in self.bases:
            ws = self.tree("n-base")
            parent = ws.text()
            a = self.admit_one(ws, N_LINE)
            self.bases["n"] = (ws, a, parent)
        ws, a, parent = self.bases["n"]
        return self.copy(ws, "n"), a, parent

    def events(self, ws):
        return self.led.read(ws.ledger)[0]

    def rehash(self, ws, events):
        prev, lines = self.led.ZERO, []
        for ev in events:
            b = self.canon.dumps(dict(ev, prev=prev))
            lines.append(b)
            prev = self.canon.sha256(b)
        open(ws.ledger, "wb").write(b"".join(x + b"\n" for x in lines))

    def stills(self, ws):
        return sorted(os.listdir(ws.stills)) if os.path.isdir(ws.stills) else []

    def undone(self, label):
        """OU3's state: N_TREE, #N's stored inverse evaluated with inverse_of N and admitted with inverse_of N."""
        ws, a, parent = self.n_tree()
        verdict, codes, seq = self.evaluate(ws, a["inverse"], "U", inverse_of=a["seq"])
        au = quiet(self.D.cmd_admit, ws, seq, inverse_of=a["seq"]) if verdict == "CLEAN" else None
        return ws, a, parent, (verdict, codes, seq), au

    def recordless(self, ws, revision, cand="Y"):
        """A record-less evaluation of `revision` appended with led.append at the files' head, its verdict CLEAN (its
        verdict's shape an honest evaluation's at that head), and its admission written by commit_admission with no
        evidence and the files left as they are."""
        D = self.D
        tpl, _a, _t, _o1, _o0, _x, _r = D.evaluate_doc(ws, self.canon.load_intent(self.canon.dumps(self.intent(ws, [OTHER_LINE], "T"))))
        raw = self.canon.dumps(self.intent(ws, revision, cand))
        verdict = dict(json.loads(json.dumps(tpl)), verdict="CLEAN", codes=[], checked_against=self.canon.head(D.current_parts(ws)))
        fields = D.evaluation_fields(raw, verdict, {"art_sha256": "", "world_sha256": "", "layout_head": ""}, {}, None)
        fields.pop("record", None)
        e = self.led.append(ws.ledger, "evaluate", fields)
        return D.selftest_admission(ws, e["seq"], inverse=[], apply=False, chooser="past the director (0254's rows)")

    def verify_code(self, ws):
        """cmd_verify's answer: 'verifies', or the LedgerError's text."""
        try:
            quiet(self.D.cmd_verify, ws)
            return "verifies"
        except self.led.LedgerError as e:
            return str(e)


def code_of(text):
    return text.split(":", 1)[0]


# ------------------------------------------------------------------------------------------------ the rows
def r_fz1(c):
    m, v, l, probs = IF.frozen()
    first = not probs and m is not None and v is not None and l is not None
    d = c.path("fz1")
    shutil.copytree(IF.FOLDER, d)
    vp = os.path.join(d, "0254-vectors.json")
    doc = json.loads(open(vp, "rb").read().decode("utf-8"))
    vec = doc["revisions"]["vectors"][0]
    vec["inverse"] = [vec["inverse"][0].replace("1,2,3", "1,2,4")]
    body = binding.canonical(doc)
    open(vp, "wb").write(body)
    rec = [json.loads(ln) for ln in open(os.path.join(d, IF.RECORD), "rb").read().decode("ascii").split("\n") if ln]
    recorded = [r["sha256"] for r in rec if r["file"] == "0254-vectors.json"][0]
    probs2 = IF.frozen(d)[3]
    named = [p for p in probs2 if "0254-vectors.json" in p and sha256(body) in p and recorded in p]
    return first and bool(named), "the freeze: %s; the copy (%s's first inverse altered): %s" % (
        "no problem" if first else "; ".join(probs)[:200], vec["id"], (named or probs2 or ["NOT refused"])[0][:200])


def blank_skipping(canon, line):
    """The validator vectors-from-code's copy takes its verdict from: the blanks between the form and its array skipped."""
    try:
        canon.inverse_form(line[:2] + " " + line[2:].lstrip(" \t"))
        return True, ""
    except canon.IntentError as e:
        return False, e.code


def r_gr0(c):
    D, canon, M = c.D, c.canon, c.M
    forms = c.V["forms"]["vectors"]
    pin = M["vectors.json at 7dee210"]
    n0 = pin["intents before the append"]
    probs, added = IF.vectors_json_problems(M, len(forms))
    raw = open(IF.VECTORS_JSON, "rb").read()
    doc = json.loads(raw.decode("utf-8"))
    if D.INVERSE_PLANT == "vectors-from-code":
        # an in-memory copy whose F-R21 and F-R22 take a blank-skipping validator's verdict (vectors_source's assertion
        # against the freeze not made); read only here
        for e in doc["intents"][n0:]:
            rev = json.loads(bytes.fromhex(e["hex"]).decode("ascii"))["revision"]
            if rev and rev[0] in [f["line"] for f in forms if f["id"] in ("F-R21", "F-R22")]:
                ok, code = blank_skipping(canon, rev[0])
                e["expect"] = {"ok": True, "sha256": canon.sha256(bytes.fromhex(e["hex"]))} if ok else {"ok": False, "code": code}
    tail = doc["intents"][n0:]
    bad = []
    early = [i for i, e in enumerate(doc["intents"][:n0]) if any(isinstance(x, str) and x[:1] == "@" for x in json.loads(bytes.fromhex(e["hex"]).decode("ascii")).get("revision", []))]
    if len(tail) != len(forms):
        bad.append("%d intents appended, %d forms frozen" % (len(tail), len(forms)))
    for e, f in zip(tail, forms):
        b = bytes.fromhex(e["hex"])
        it = json.loads(b.decode("ascii"))
        same = it.get("revision") == [f["line"]] and it.get("version") == "0" and it.get("format") == "VERDANDI-INTENT"
        verdict = (e["expect"]["ok"], e["expect"].get("code", "")) == (f["ok"], f["code"]) and (not f["ok"] or e["expect"].get("sha256") == canon.sha256(b))
        if not (same and verdict):
            bad.append(f["id"])
    total = sum(len(doc[k]) for k in ("dumps", "loads", "intents", "heads", "materials", "patterns", "scope"))
    if total != pin["vectors"] + len(forms):
        bad.append("%d vectors in all, not %d" % (total, pin["vectors"] + len(forms)))
    # two-sided: a copy with one existing expected output altered (a material's digest), regenerated so that cmd_vectors
    # still reproduces it, held to the same pin
    cp = os.path.join(c.path("gr0"), "vectors.json")
    os.makedirs(os.path.dirname(cp))
    alt = json.loads(raw.decode("utf-8"))
    mat = alt["materials"][0]
    mat["material"]["base"] = [mat["material"]["base"][0] + 1] + mat["material"]["base"][1:]
    mat["expect"] = {"digest": D.scopemod.material_digest(mat["material"]), "record_hex": canon.dumps(D.scopemod.material_record(mat["material"])).hex()}
    open(cp, "wb").write((json.dumps(alt, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"))
    # the altered entry reproduced by the reference as cmd_vectors judges a material (its record's bytes and its digest),
    # so that only the pin can refuse the copy
    m2 = json.loads(open(cp, "rb").read().decode("utf-8"))["materials"][0]
    bad2 = [] if canon.dumps(D.scopemod.material_record(m2["material"])).hex() == m2["expect"]["record_hex"]         and D.scopemod.material_digest(m2["material"]) == m2["expect"]["digest"] else ["material"]
    cut = dict(alt, intents=alt["intents"][:n0])
    cut_sha = sha256((json.dumps(cut, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"))
    probs3, _a3 = IF.vectors_json_problems(M, len(forms), path=cp)
    refused = [p for p in probs3 if cut_sha in p and pin["sha256"] in p]
    ok = not probs and added == len(forms) and not bad and not early and not bad2 and bool(refused)
    return ok, "cut to its %d intents: %s; %d forms appended, %s; the altered copy reproduced by the reference (%s) and %s" % (
        n0, "7dee210's bytes" if not probs else "; ".join(probs)[:160], added if added is not None else -1,
        ("every one with the freeze's verdict" if not bad else "differing: " + ", ".join(bad)) + ("" if not early else "; '@' among the first seven"),
        "yes" if not bad2 else "no: " + ", ".join(bad2[:2]), ("refused naming the pin: " + refused[0][:110]) if refused else "NOT refused")


def r_gr1(c):
    n, bad = c.D.cmd_vectors(quiet=True)
    want = c.M["vectors.json at 7dee210"]["vectors"] + len(c.V["forms"]["vectors"])
    return not bad and n == want, "VECTORS %d / %d (expected %d)%s" % (n - len(bad), n, want, ("; failed: " + ", ".join(bad[:5])) if bad else "")


def r_ou0(c):
    D, bad, said = c.D, [], []
    for v in c.V["only"]["vectors"]:
        try:
            child, _inv = D.apply_revision(v["text"], v["revision"])
            got = "applies" if child == v.get("child") else "applies, another child"
        except c.canon.IntentError as e:
            got = e.code
        said.append("%s %s" % (v["id"], got))
        if got != v["expect"]:
            bad.append(v["id"])
    return not bad, "; ".join(said)


def ex_rows(c, ids):
    D, bad = c.D, []
    for vid in ids:
        v = c.v(vid)
        parent = c.P[v["parent"]]
        child, inv = D.apply_revision(parent, v["revision"])
        back, redo = D.apply_revision(child, inv, undo=True)
        again, _r = D.apply_revision(parent, redo, undo=True)
        why = [k for k, ok in (("child", child == v["child"]), ("inverse", inv == v["inverse"]), ("back", back == parent == v["back"]),
                               ("redo", redo == v["redo"]), ("child again", again == child)) if not ok]
        if why:
            bad.append("%s (%s)" % (vid, ", ".join(why)))
    return bad


def r_ex(ids, extra=None):
    def run(c):
        bad = ex_rows(c, ids(c))
        if extra:
            bad += extra(c)
        return not bad, ("%d vectors: child, inverse, parent byte for byte, redo and child again as frozen" % len(ids(c))) if not bad else "not as frozen: " + "; ".join(bad)[:400]
    return run


def p_ok_exact(c):
    v = c.v("P-OK")
    _ch, inv = c.D.apply_revision(c.P[v["parent"]], v["revision"])
    return [] if inv == ["- lamp b"] == v["inverse"] else ["P-OK's inverse %r" % (inv,)]


def r_lg1(c):
    D, bad = c.D, []
    for v in c.V["legacy"]["vectors"]:
        back, _x = D.apply_revision(v["text"], v["stored"])
        if back != v["back"]:
            bad.append(v["id"])
    for v in c.V["legacy-inverses"]["vectors"]:
        child, _inv = D.apply_revision(c.P[v["parent"]], v["revision"])
        back, _x = D.apply_revision(child, v["inverse"])
        if (child, back) != (v["child"], v["restores"]):
            bad.append(v["id"])
    rp = c.V["legacy"]["replay"]
    p = os.path.join(c.path("lg1"), "copy.ledger")
    os.makedirs(os.path.dirname(p))
    open(p, "wb").write(c.L)
    got = "?"
    try:
        events, head = c.led.chain(p)
        st = D.replay(None, events)
        got = (len(events), head, st["head"], sha256(st["art"].encode("utf-8")), sha256(st["design"].encode("utf-8")))
        want = (rp["events"], rp["chain head"], rp["replayed files head"], rp["replayed art sha256"], rp["replayed design sha256"])
        if sha256(c.L) != rp["sha256"] or got != want:
            bad.append("LG-COPY (%d events, heads %s)" % (got[0], ", ".join(x[:12] for x in got[1:])))
    except c.led.LedgerError as e:
        bad.append("LG-COPY: " + str(e)[:140])
    return not bad, ("each back and each restored text 7dee210's; the copy: %d events, chain %s, files head %s" % (got[0], got[1][:12], got[2][:12])) \
        if not bad else "not 7dee210's: " + "; ".join(bad)


def r_fw1(c):
    D, bad = c.D, []
    ids = [r for r in c.M["suites"][0]["rows"] if r["id"] == "FW1"][0]["vectors"]
    for vid in ids:
        sec, v = c.by_id[vid]
        if sec == "only":
            got = D.apply_revision(v["text"], v["revision"])[0] == v["child"]
        elif sec == "legacy":
            got = D.apply_revision(c.P[v["parent"]], v["revision"])[0] == v["text"] and D.apply_revision(v["text"], v["stored"])[0] == v["back"]
        else:
            got = D.apply_revision(c.P[v["parent"]], v["revision"])[0] == v["child"]
        if not got:
            bad.append(vid)
    return not bad, ("%d children (and the legacy backs) the frozen ones" % len(ids)) if not bad else "differing: " + ", ".join(bad)


def r_gd(ids):
    def run(c):
        D, bad, said = c.D, [], []
        for vid in ids:
            v = c.v(vid)
            form = [x[:2] for x in v["inverse"] if x[:1] == "@"]
            try:
                back, _r = D.apply_revision(v["over"], v["inverse"], undo=True)
                got = "equal to the parent" if back == c.P[v["parent"]] else "not the parent"
                if v["expect"] != "INTENT-APPLY" and back != v["back"]:
                    got += ", not the frozen back"
                said.append("%s %s" % (vid, got))
            except c.canon.IntentError as e:
                got = e.code
                if form and form[-1] not in str(e) and form[0] not in str(e):
                    got += " not naming its form"
                said.append("%s %s" % (vid, str(e)[:90]))
            if got != v["expect"]:
                bad.append(vid)
        return not bad, "; ".join(said)[:700]
    return run


def r_ou1(c):
    ws = c.tree("ou1")
    verdict, codes, _s = c.evaluate(ws, c.v("OY-EQ")["revision"], "Q")
    return (verdict, codes) == ("REFUSED", "INTENT-INVERSE-ONLY"), "evaluate without --inverse-of: %s %s" % (verdict, codes)


def r_ou2(c):
    ws, a, _p = c.n_tree()
    got = [c.evaluate(ws, c.v("OY-EQ")["revision"], "Q", inverse_of=a["seq"]), c.evaluate(ws, [OTHER_LINE], "O", inverse_of=a["seq"])]
    return all(g[:2] == ("REFUSED", "INTENT-INVERSE-ONLY") for g in got), "with --inverse-of %s: an inverse form %s %s; ordinary lines %s %s" % (
        a["seq"], got[0][0], got[0][1], got[1][0], got[1][1])


def r_ou3(c):
    ws, a, parent, (verdict, codes, seq), au = c.undone("ou3")
    st = c.D.replay(ws, c.events(ws)[:int(a["seq"])])
    ok = verdict == "CLEAN" and au is not None and au["evidence"]["inverse_of"] == a["seq"] and ws.text() == parent \
        and sha256(ws.text().encode("utf-8")) == st["parts"]["art_sha256"]
    return ok, "#%s's inverse %s; evaluated %s %s; %s; the art #%s's parent byte for byte: %s" % (
        a["seq"], a["inverse"], verdict, codes, ("admitted as #%s naming #%s" % (au["seq"], au["evidence"]["inverse_of"])) if au else "not admitted",
        a["seq"], ws.text() == parent)


def r_ou3b(c):
    D = c.D
    ws, a, parent = c.n_tree()
    N = a["seq"]
    verdict, codes, seq = c.evaluate(ws, a["inverse"], "U", inverse_of=N)
    with open(ws.art, "ab") as fh:
        fh.write(b"# rebased\n")
    quiet(D.cmd_rebase, ws, "a comment appended (0254's OU3b)")
    n0 = open(ws.ledger, "rb").read()
    try:
        quiet(D.cmd_admit, ws, seq, inverse_of=N)
        moved = "admitted"
    except SystemExit as e:
        moved = str(e)
    first = moved.startswith("REFUSED (HEAD-MOVED)") and ("reevaluate %s %s --inverse-of %s" % (BRIEF, seq, N)) in moved and open(ws.ledger, "rb").read() == n0
    rn = quiet(D.cmd_reevaluate, ws, seq)
    second = rn["verdict"]["verdict"] == "REFUSED" and rn["verdict"]["codes"] == ["INTENT-INVERSE-ONLY"] and rn["re_evaluation_of"] == seq
    ry = quiet(D.cmd_reevaluate, ws, seq, inverse_of=N)
    third = ry["verdict"]["verdict"] == "CLEAN" and "HEAD-MOVED" in ry["verdict"]["codes"] and ry["re_evaluation_of"] == seq
    au = quiet(D.cmd_admit, ws, ry["seq"], inverse_of=N) if third else None
    fourth = au is not None and au["evidence"]["inverse_of"] == N and ws.text() == parent + "# rebased\n"
    v = c.verify_code(ws)
    return verdict == "CLEAN" and first and second and third and fourth and v == "verifies", \
        "admit: %s; reevaluate without the flag: %s %s; with it: %s %s; admitted %s; the art N's parent with the comment kept %s; verify %s" % (
            " ".join(moved.split())[:150], rn["verdict"]["verdict"], rn["verdict"]["codes"], ry["verdict"]["verdict"], ry["verdict"]["codes"],
            ("#%s naming #%s" % (au["seq"], au["evidence"]["inverse_of"])) if au else "no", fourth, v[:60])


def r_ou4(c):
    D = c.D
    ws, a, _p = c.n_tree()
    verdict, codes, seq = c.evaluate(ws, a["inverse"], "U", inverse_of=a["seq"])
    before = (open(ws.ledger, "rb").read(), open(ws.art, "rb").read(), c.stills(ws))
    try:
        quiet(D.cmd_admit_still, ws, seq)
        said = "admitted"
    except SystemExit as e:
        said = str(e)
    same = (open(ws.ledger, "rb").read(), open(ws.art, "rb").read(), c.stills(ws)) == before
    return verdict == "CLEAN" and said.startswith("REFUSED (INTENT-INVERSE-ONLY): ") and same, "evaluated %s; admitted without --inverse-of, with a still: %s; ledger, files and stills unchanged %s" % (
        verdict, " ".join(said.split())[:120], same)


def r_ou6(c):
    D = c.D
    ws, a, _p = c.n_tree()
    verdict, codes, seq = c.evaluate(ws, a["inverse"], "U", inverse_of=a["seq"])
    rung = (c.events(ws)[int(seq)].get("record") or {}).get("rung")
    D.selftest_admission(ws, seq, still=D.selftest_still(), undo=True, chooser="past admit_checks (0254's OU6)")
    try:
        quiet(D.cmd_verify, ws)
        got = "verifies"
    except c.led.LedgerError as e:
        got = "LedgerError " + str(e)
    except c.canon.IntentError as e:
        got = "IntentError " + str(e)
    return verdict == "CLEAN" and rung == "A" and got.startswith("LedgerError LEDGER-INVERSE-ONLY:"), "the inverse evaluated %s, rung %s; written by the commit naming no inverse_of; verify: %s" % (
        verdict, rung, got[:140])


def _verify_raised(c, ws):
    try:
        quiet(c.D.cmd_verify, ws)
        return "verifies"
    except c.led.LedgerError as e:
        return "LedgerError " + str(e)
    except c.canon.IntentError as e:
        return "IntentError " + str(e)


def r_ou6b(c):
    ws = c.tree("ou6b")
    c.recordless(ws, c.v("OY-EQ")["revision"])
    got = _verify_raised(c, ws)
    return got.startswith("LedgerError LEDGER-INVERSE-ONLY:"), "verify: " + got[:140]


def r_ou6c(c):
    ws, a, parent, (verdict, codes, seq), au = c.undone("ou6c")
    c.recordless(ws, c.v("OY-EQ")["revision"])
    got = _verify_raised(c, ws)
    return au is not None and got.startswith("LedgerError LEDGER-INVERSE-ONLY:"), "after the recorded undo %s: verify: %s" % (
        ("#%s" % au["seq"]) if au else "(not admitted)", got[:140])


def r_ou6d(c):
    D, canon = c.D, c.canon
    ws, a, _p = c.n_tree()
    N = a["seq"]
    verdict, codes, e1 = c.evaluate(ws, a["inverse"], "U", inverse_of=N)
    events = c.events(ws)
    X = len(events)
    Y = X + 2
    it = canon.load_intent(events[int(e1)]["intent"].encode("ascii"))
    head0 = canon.head(D.current_parts(ws))
    text1, inv1 = D.apply_revision(ws.text(), it["revision"], undo=True)
    _o, parts1, _c = ws.export(text1)
    obs = {"at": "2026-10-20T00:00:00Z", "chooser": "past the director (0254's OU6d)", "note": ""}
    c.led.append(ws.ledger, "admit", {"evaluation": e1, "intent_sha256": events[int(e1)]["intent_sha256"], "head_before": head0,
                                      "head_after": canon.head(parts1), "parts_after": parts1, "accepted_leakage": False, "inverse": inv1,
                                      "design_lines": [], "observed": obs,
                                      "evidence": {"accepted_leakage": False, "still_sha256": "", "detectors": {}, "despite_detectors": False, "inverse_of": str(Y)}})
    raw = canon.dumps(c.intent(ws, [N_LINE], "R"))
    tpl = events[int(e1)]["verdict"]
    fields = D.evaluation_fields(raw, dict(json.loads(json.dumps(tpl)), verdict="CLEAN", codes=[], checked_against=canon.head(parts1)),
                                 {"art_sha256": "", "world_sha256": "", "layout_head": ""}, {}, None)
    fields.pop("record", None)
    e2 = c.led.append(ws.ledger, "evaluate", fields)
    text2, inv2 = D.apply_revision(text1, [N_LINE])
    _o2, parts2, _c2 = ws.export(text2)
    y = c.led.append(ws.ledger, "admit", {"evaluation": e2["seq"], "intent_sha256": e2["intent_sha256"], "head_before": canon.head(parts1),
                                          "head_after": canon.head(parts2), "parts_after": parts2, "accepted_leakage": False, "inverse": inv2,
                                          "design_lines": [], "observed": obs})
    got = _verify_raised(c, ws)
    return y["seq"] == str(Y) and inv2 == list(it["revision"]) and got.startswith("LedgerError LEDGER-EVIDENCE: #%d " % X), \
        "#%d names #%s (later, its inverse equal to #%d's revision: %s); verify: %s" % (X, Y, X, inv2 == list(it["revision"]), got[:140])


def r_ou7(c):
    D, canon = c.D, c.canon
    v = c.v("L-ST2")
    parent = c.P[v["parent"]]

    def aligned(label):
        ws = c.tree(label)
        open(ws.art, "wb").write(parent.encode("utf-8"))
        quiet(D.cmd_rebase, ws, "the canopy's statement written aligned (0254's OU7)")
        return ws
    ws = aligned("ou7")
    verdict, codes, seq = c.evaluate(ws, v["revision"], "A")
    a = quiet(D.cmd_admit_still, ws, seq)
    events = c.events(ws)
    k = int(a["seq"])
    stored = list(events[k]["inverse"])
    alt = []
    for x in stored:
        if x[:3] == "@= ":
            f, val = canon.inverse_form(x)
            alt.append(canon.inverse_line(f, [val[0], val[1], val[2].replace("7.0", "7.5")]))
        else:
            alt.append(x.replace("7.0", "7.5"))
    events[k] = dict(events[k], inverse=alt)
    c.rehash(ws, events)
    got = _verify_raised(c, ws)
    first = verdict == "CLEAN" and len(stored) == 1 and stored[0][:3] == "@= " and got.startswith("LedgerError LEDGER-INVERSE: #%s's stored inverse" % a["seq"])
    # the control: a pre-0254 admission, L-ST2's inverse verbatim from the freeze, written by the director's commit
    w2 = aligned("ou7-control")
    row_ok = w2.text() == parent and sha256(parent.encode("utf-8")) == v["parent sha256"]
    verdict2, codes2, seq2 = c.evaluate(w2, v["revision"], "A")
    D.selftest_admission(w2, seq2, inverse=list(v["inverse"]), still=D.selftest_still(), chooser="a pre-0254 admission (0254's OU7)")
    got2 = _verify_raised(c, w2)
    return first and row_ok and verdict2 == "CLEAN" and got2 == "verifies", "the stored '@=' with its restored row altered: %s; the control (L-ST2's inverse %s): %s" % (
        got[:120], v["inverse"], got2[:100])


def r_ou8(c):
    D, canon = c.D, c.canon
    ws, a, _p = c.n_tree()
    N = a["seq"]
    forged = ['@~ ["1","3"]']
    events = c.events(ws)
    events[int(N)] = dict(events[int(N)], inverse=forged)
    c.rehash(ws, events)
    n0 = open(ws.ledger, "rb").read()
    calls = []
    real = D.apply_revision

    def spy(text, lines, undo=False):
        if any(x in forged for x in lines):
            calls.append(list(lines))
        return real(text, lines, undo)
    D.apply_revision = spy
    try:
        it = canon.load_intent(canon.dumps(c.intent(ws, forged, "F")))
        try:
            D.evaluate_doc(ws, it, undo_of=N)
            first = "no refusal"
        except c.led.LedgerError as e:
            first = str(e)
        direct = (first.startswith("LEDGER-INVERSE:"), len(calls), open(ws.ledger, "rb").read() == n0)
        del calls[:]
        try:
            c.evaluate(ws, forged, "F", inverse_of=N)
            second = "no refusal"
        except c.led.LedgerError as e:
            second = str(e)
        line = (second.startswith("LEDGER-INVERSE:"), len(calls), open(ws.ledger, "rb").read() == n0)
    finally:
        D.apply_revision = real
    return direct == (True, 0, True) and line == (True, 0, True), "evaluate_doc(undo_of=%s): %s (the forged line applied %d times, nothing appended %s); the command line: %s (applied %d times, nothing appended %s)" % (
        N, first[:70], direct[1], direct[2], second[:50], line[1], line[2])


def r_ou9(c):
    D = c.D
    ws = c.tree("ou9")
    m = c.admit_one(ws, M9_LINE)
    n = c.admit_one(ws, N9_LINE)
    rows = ws.text().split("\n")
    key = N9_LINE[2:]
    # #N's '@+' position (the row its successor stands at); the comment goes there, after #M's position
    import intent as _c
    try:
        iN = int(_c.inverse_form(n["inverse"][0])[1][0]) if n["inverse"] and n["inverse"][0][:1] == "@" else None
    except _c.IntentError:
        iN = None
    if iN is None:
        iN = [i for i, r in enumerate(rows) if r.startswith("lamp south-flank")][0]
    rows.insert(iN, "# a row between #%s's and #%s's (0254's OU9)" % (m["seq"], n["seq"]))
    open(ws.art, "wb").write("\n".join(rows).encode("utf-8"))
    quiet(D.cmd_rebase, ws, "a comment between two admissions' rows (0254's OU9)")
    verdict, codes, seq = c.evaluate(ws, m["inverse"], "U", inverse_of=m["seq"])
    au = quiet(D.cmd_admit, ws, seq, inverse_of=m["seq"]) if verdict == "CLEAN" else None
    return verdict == "CLEAN" and au is not None and au["evidence"]["inverse_of"] == m["seq"], "#%s (%s) undone after #%s (%s), a row between: %s %s; %s" % (
        m["seq"], M9_LINE, n["seq"], key, verdict, codes, ("admitted naming #%s" % au["evidence"]["inverse_of"]) if au else "not admitted")


def ids_of(rid):
    return lambda c: [r for r in c.M["suites"][0]["rows"] if r["id"] == rid][0]["vectors"]


ROWS = {"FZ1": r_fz1, "GR0": r_gr0, "GR1": r_gr1, "OU0": r_ou0,
        "EX1": r_ex(ids_of("EX1")), "EX2": r_ex(ids_of("EX2")), "EX3": r_ex(ids_of("EX3"), p_ok_exact), "EX4": r_ex(ids_of("EX4")),
        "EX6": r_ex(ids_of("EX6")), "LG1": r_lg1, "FW1": r_fw1,
        "GD2a": None, "GD2b": None, "GD3": None, "GD4": None, "GD5": None, "GD6": None, "GD7": None,
        "OU1": r_ou1, "OU2": r_ou2, "OU3": r_ou3, "OU3b": r_ou3b, "OU4": r_ou4, "OU6": r_ou6, "OU6b": r_ou6b, "OU6c": r_ou6c,
        "OU6d": r_ou6d, "OU7": r_ou7, "OU8": r_ou8, "OU9": r_ou9}


def run_rows(D, M, V, L, order):
    """Every 0254 row in the matrix's order: [(id, name, ok, detail)]."""
    import intent as canon
    c = Ctx(D, M, V, L)
    out = []
    try:
        for r in order:
            fn = ROWS.get(r["id"]) or r_gd(r["vectors"])
            try:
                ok, detail = fn(c)
            except (canon.IntentError, D.led.LedgerError) as e:
                ok, detail = False, "%s: %s" % (type(e).__name__, str(e)[:200])
            except Exception as e:  # noqa: BLE001 — the matrix's 'exceptions': named by its type, the suite goes on
                ok, detail = False, "raised %s: %s" % (type(e).__name__, str(e)[:200])
            except SystemExit as e:
                ok, detail = False, "raised SystemExit: %s" % " ".join(str(e).split())[:200]
            out.append((r["id"], r["printed"][0], bool(ok), detail))
    finally:
        c.close()
    return out


def set_plant(D, p):
    import intent as canon
    D.INVERSE_PLANT = p
    canon.PLANT_OF = (lambda: D.INVERSE_PLANT) if p else (lambda: "")
    IF.PLANT_OF = (lambda: D.INVERSE_PLANT) if p else (lambda: "")


def director_rows(D):
    """The rows (name, ok, detail) cmd_selftest prints: FZ1 to OU9 once honest, then a row per plant."""
    M, V, L, problems = IF.frozen()
    if problems or M is None or V is None or L is None:
        return [("0254: the freeze read through frozen()", False, "; ".join(problems)[:400])]
    suite = [s for s in M["suites"] if s["suite"] == SUITE][0]
    order = [r for r in suite["rows"] if r["id"] != "DS1"]
    results = []
    set_plant(D, "")
    honest = run_rows(D, M, V, L, order)
    for _i, name, ok, detail in honest:
        results.append((name, ok, detail))
    pos = {r["id"]: i for i, r in enumerate(order)}
    for p in [p for p in M["plants"] if p["suite"] == SUITE]:
        set_plant(D, p["value"])
        try:
            got = run_rows(D, M, V, L, order)
        finally:
            set_plant(D, "")
        failed = [i for i, _n, ok, _d in got if not ok]
        k = pos[p["caught_by"]]
        before = [i for i in failed if pos[i] < k]
        after = sorted((i for i in failed if pos[i] > k), key=pos.get)
        want = sorted(p["fails_later"], key=pos.get)
        caught = p["caught_by"] in failed and not before and after == want
        why = [d for i, _n, ok, d in got if i == p["caught_by"]][0]
        detail = "caught by %s; %s" % (p["caught_by"], " ".join(why.split())[:160]) if caught else \
            "NOT caught as frozen: %s failed%s; earlier rows failing %s; later rows failing %s, frozen %s" % (
                p["caught_by"], "" if p["caught_by"] in failed else " NOT", before or "none", after or "none", want or "none")
        if caught:
            detail += "; later rows failing, as frozen: %s" % (", ".join(after) or "none")
        results.append((p["printed"], caught, detail))
    return results
