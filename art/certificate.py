# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/certificate.py — CERT-0 (0244): every admission's certificate, and the exact check of its inverse.
#
#   python art/certificate.py selftest
#   python art/certificate.py check CERTIFICATE.json BRIEF.art     the certificate against the brief as it stands
#
# An admission moves a world from one head to another by an operation (a revision of the art text) and records the
# operation's inverse (DIRECTOR-0's ledger: the admit event's `inverse`). The certificate puts that morphism in one
# canonical document: the parent (the head before and its parts), the operation, the inverse, the child (the head after
# and its parts), the statement keys the operation touches, the provenance, and the ledger event it is made from (its
# sequence number and sha256). The ledger stays the authority; a certificate is derived from it, never the other way.
#
# THE CHECK (exact: bytes and sha256, nothing measured). Given the child's text (the brief as admitted), and without
# exporting or replaying the world:
#   CERT-CHILD     the text is the child's (its sha256 is the child's art part)
#   CERT-HEAD      each head is the sha256 of its own parts (DIRECTOR-0's head)
#   CERT-ART-ONLY  the operation changed the art alone (the world's and the exporter's parts the same on both sides);
#                  a layout's change is the design tool's, and its inverse is not this check's
#   the inverse applied to the child gives the parent's text byte for byte (`exact`), or failing that the parent's
#   statements token for token (`statements`: the same statements, another spelling of the text; not always the same
#   scene); neither: CERT-INVERSE. The inverse is applied as an undo applies it (0254: apply_revision with undo=True,
#   its inverse forms under their guards), in memory, writing nothing.
#   Corrected in place by 0254 (OPEN-6, his ruling: "Record as Dated Findings, correct the single misleading comment,
#   repair nothing else."): this said `statements` was "the same scene", which is false for movers. The exporter keeps
#   movers in file order, so on harbor-lift an undo of '- mover deck' that comes back statement for statement gives
#   another scene (MEASURED, 2026-10-20, the 0254 census).
# A state-captured inverse is an isomorphism only when `exact` holds: the head after the undo is then the head before.
# Standard library only.

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

FORMAT, VERSION = "VERDANDI-CERTIFICATE", "0"
PLANT = ""
PLANTS = ("cert-child-unhashed", "cert-statements-as-exact", "cert-heads-unchecked", "keys-misread")   # keys-misread: 0254


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def _director():
    import director
    return director


def statements(text):
    """The text's statements, token for token and in sorted order, comments and spacing left out: what the exporter
    reads of it (its statements are keyed, so their order in the file says nothing)."""
    rows = sorted(" ".join(ln.split("#", 1)[0].split()) for ln in text.split("\n"))
    return "\n".join(r for r in rows if r) + "\n"


def keys(revision):
    """The statement keys a revision touches (DIRECTOR-0's: '= stmt' and '+ stmt' by their statement's key, '- key';
    0254: an inverse form's '@= [I,W,R]' and '@+ [I,R,S]' by their row's statement key, '@~' by none, so that an undo's
    certificate names the admission's support)."""
    import dress
    D = _director()
    out = []
    for ln in revision:
        if ln[:1] == "@" and PLANT != "keys-misread":
            form, v = D.canon.inverse_form(ln)
            code = v[2].split("#", 1)[0].split() if form == "@=" else v[1].split("#", 1)[0].split() if form == "@+" else []
            if code:
                out.append(dress.statement_key(code))
            continue
        body = ln[2:].strip()
        out.append(dress.statement_key(body.split()) if ln[0] in "=+" else body)
    return sorted(set(out))


def make(world, event, revision, parent_text, child_text, provenance, request="", candidate=""):
    """The certificate of one admit event (a dict from the ledger), its operation `revision`, and the brief's text before
    and after it."""
    D = _director()
    parts1 = dict(event["parts_after"])
    parts0 = dict(parts1, art_sha256=sha256(parent_text.encode("utf-8")))
    return {"format": FORMAT, "version": VERSION, "world": world, "request": request, "candidate": candidate,
            "ledger": {"seq": event["seq"], "evaluation": event["evaluation"], "event_sha256": sha256(D.canon.dumps(event))},
            "parent": {"head": event["head_before"], "parts": parts0, "statements_sha256": sha256(statements(parent_text).encode("utf-8"))},
            "op": {"revision": list(revision), "sha256": sha256(json.dumps(list(revision), ensure_ascii=True).encode("ascii"))},
            "inverse": {"revision": list(event["inverse"]), "sha256": sha256(json.dumps(list(event["inverse"]), ensure_ascii=True).encode("ascii"))},
            "child": {"head": event["head_after"], "parts": parts1},
            "support": {"statement_keys": keys(revision)},
            "provenance": provenance or {},
            "verification": {"method": "certificate", "signer": "studio", "signature": ""}}


def check(cert, child_text):
    """The certificate against the child's text: {ok, exact, statements, codes}. See the head of this file."""
    D = _director()
    codes = []
    if sha256(child_text.encode("utf-8")) != cert["child"]["parts"]["art_sha256"] and PLANT != "cert-child-unhashed":
        codes.append("CERT-CHILD")
    if PLANT != "cert-heads-unchecked" and (D.canon.head(cert["child"]["parts"]) != cert["child"]["head"]
                                           or D.canon.head(cert["parent"]["parts"]) != cert["parent"]["head"]):
        codes.append("CERT-HEAD")
    p0, p1 = cert["parent"]["parts"], cert["child"]["parts"]
    if p0["world_sha256"] != p1["world_sha256"] or p0["exporter_sha256"] != p1["exporter_sha256"]:
        codes.append("CERT-ART-ONLY")
    exact = same = False
    try:
        back, _again = D.apply_revision(child_text, cert["inverse"]["revision"], undo=True)
        exact = sha256(back.encode("utf-8")) == p0["art_sha256"]
        same = sha256(statements(back).encode("utf-8")) == cert["parent"]["statements_sha256"]
        if PLANT == "cert-statements-as-exact":
            exact = same
    except D.canon.IntentError as e:
        codes.append("CERT-INVERSE-APPLY: " + str(e)[:120])
    if not same:
        codes.append("CERT-INVERSE")
    return {"ok": not codes, "exact": exact, "statements": same, "codes": codes}


# ------------------------------------------------------------------------------------------------ self-test
# 0254 (spec §7.2, the frozen matrix's suite "CERT SELFTEST", art/director/inverse/0254-matrix.json): seven rows, CT1 to
# CT7, each printed with the name the matrix freezes, their cases and expectations read only through
# inverse_freeze.frozen() (the parents embedded in the freeze, never art/briefs/, which is the owner's world). The plant
# loop is tightened: a plant counts as caught only when the row the matrix names fails, every row before it passes, and
# the rows after it that fail are exactly its frozen list (none, for each of the four).
def _freeze():
    sys.path.insert(0, os.path.join(HERE, "director"))
    import inverse_freeze
    m, v, _l, problems = inverse_freeze.frozen()
    return m, v, problems


def _rows(M, V):
    """[(id, name, ok, detail)] in the matrix's order; every row catches what it raises (named by its type)."""
    D = _director()
    import dress
    suite = [s for s in M["suites"] if s["suite"] == "CERT SELFTEST"][0]
    spec = {r["id"]: r for r in suite["rows"]}
    by_id = {}
    for sec in ("revisions", "cr", "legacy-inverses"):
        for v in V[sec]["vectors"]:
            by_id[v["id"]] = v
    parents = V["parents"]
    P = lambda v: parents[v["parent"]]["text"]
    own = lambda v: sha256(P(v).encode("utf-8")) == parents[v["parent"]]["sha256"]
    E, W = "e" * 64, "w" * 64

    def cert_of(parent, child, op, inverse, seq="7"):
        p0 = {"art_sha256": sha256(parent.encode("utf-8")), "exporter_sha256": E, "world_sha256": W}
        p1 = dict(p0, art_sha256=sha256(child.encode("utf-8")))
        ev = {"seq": seq, "evaluation": "6", "head_before": D.canon.head(p0), "head_after": D.canon.head(p1), "parts_after": p1, "inverse": list(inverse)}
        return make("foundry-yard", ev, op, parent, child, {"producer": "selftest"}, "r", "A")

    def admitted(parent, rev):
        child, inv = D.apply_revision(parent, rev)
        return cert_of(parent, child, rev, inv), child
    yard = parents["brief:foundry-yard"]["text"]
    scene = lambda t: dress.export(dict(dress.parse(t, "foundry-yard.art"), name="foundry-yard", sha256=sha256(t.encode("utf-8"))))["scene_bytes"]

    def ct1():
        got = []
        for vid in spec["CT1"]["vectors"]:
            v = by_id[vid]
            cert, child = admitted(P(v), v["revision"])
            r = check(cert, child)
            got.append((vid, own(v) and child == v["child"], r))
        return all(o and r["ok"] and r["exact"] and r["statements"] for _i, o, r in got), \
            "; ".join("%s: %s" % (i, "exact" if (o and r["exact"]) else "statements only" if r["statements"] else "NOT") for i, o, r in got)

    def ct2():
        got = []
        for vid in spec["CT2"]["vectors"]:
            v = by_id[vid]
            child, _inv = D.apply_revision(P(v), v["revision"])
            cert = cert_of(P(v), child, v["revision"], v["inverse"])
            r = check(cert, child)
            back, _x = D.apply_revision(child, v["inverse"], undo=True)
            got.append((vid, own(v) and child == v["child"] and back == v["restores"], r, scene(back) == scene(P(v)),
                        D.canon.head(dict(cert["parent"]["parts"], art_sha256=sha256(back.encode("utf-8")))) != cert["parent"]["head"]))
        return all(o and r["ok"] and not r["exact"] and r["statements"] and s and h for _i, o, r, s, h in got), \
            "; ".join("%s (its inverse 7dee210's, %r): %s, the scene %s, the head %s" % (
                i, by_id[i]["inverse"][0][:40], "statements only" if (r["statements"] and not r["exact"]) else "exact" if r["exact"] else "NOT",
                "the same bytes as the parent's" if s else "OTHER", "not the parent's" if h else "the parent's") for i, o, r, s, h in got)

    def ct3():
        cert, t1 = admitted(yard, ["+ bay 10,2-17,2:s-b3-f2 panel brick"])
        bad_inv = json.loads(json.dumps(cert))
        bad_inv["inverse"]["revision"] = ["- bay 10,2-17,2:s-b4-f2"]
        bad_head = json.loads(json.dumps(cert))
        bad_head["parent"]["head"] = "0" * 64
        planted = [("a wrong inverse", check(bad_inv, t1), "CERT-INVERSE"), ("a child that is not the admitted text", check(cert, t1 + "# edited\n"), "CERT-CHILD"),
                   ("a parent head that is not its parts'", check(bad_head, t1), "CERT-HEAD"),
                   ("a layout's change", check(dict(cert, child=dict(cert["child"], parts=dict(cert["child"]["parts"], world_sha256="x" * 64),
                                                                     head=D.canon.head(dict(cert["child"]["parts"], world_sha256="x" * 64)))), t1), "CERT-ART-ONLY")]
        return all(not r["ok"] and any(c.startswith(code) for c in r["codes"]) for _n, r, code in planted), \
            "; ".join("%s: %s" % (n, ",".join(c.split(":")[0] for c in r["codes"])) for n, r, _c in planted)

    def ct4():
        c1, _t = admitted(yard, ["+ bay 10,2-17,2:s-b3-f2 panel brick"])
        c2, _t = admitted(yard, ["+ bay 10,2-17,2:s-b3-f2 panel brick"])
        return D.canon.dumps(c1) == D.canon.dumps(c2) and c1["support"]["statement_keys"] == ["bay 10,2-17,2:s-b3-f2"], \
            "%d bytes twice the same; support %s" % (len(D.canon.dumps(c1)), c1["support"]["statement_keys"])

    def ct5():
        got = [(vid, keys(by_id[vid]["inverse"])) for vid in spec["CT5"]["vectors"]]
        want = [["lamp a"], ["lamp a"], ["lamp b"]]
        v = by_id["E-ALIGN"]
        undo = cert_of(v["child"], v["back"], v["inverse"], v["redo"], seq="8")
        fwd, _c = admitted(P(v), v["revision"])
        return [g for _i, g in got] == want and undo["support"]["statement_keys"] == fwd["support"]["statement_keys"], \
            "%s; the undo's support %s, the admission's %s" % ("; ".join("%s %s" % g for g in got), undo["support"]["statement_keys"], fwd["support"]["statement_keys"])

    def ct6():
        bad = []
        for vid in spec["CT6"]["vectors"]:
            v = by_id[vid]
            cert = cert_of(v["child"], v["back"], v["inverse"], v["redo"], seq="8")
            r = check(cert, v["back"])
            if not (r["ok"] and r["exact"] and v["back"] == P(v)):
                bad.append(vid)
        return not bad, ("%d undos' certificates exact over the back" % len(spec["CT6"]["vectors"])) if not bad else "not exact: " + ", ".join(bad)

    def ct7():
        import tempfile
        import contextlib
        import io
        v = [x for x in V["cr"]["vectors"] if x["id"] == "E-CR-END"][0]
        cert, child = admitted(P(v), v["revision"])
        d = tempfile.mkdtemp(prefix="cert-ct7-")
        try:
            cp, bp = os.path.join(d, "c.json"), os.path.join(d, "b.art")
            open(cp, "wb").write(json.dumps(cert).encode("utf-8"))
            raw = child.replace("\n", "\r\n").encode("utf-8")
            open(bp, "wb").write(raw)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = main(["check", cp, bp])
            r = json.loads(buf.getvalue())
            text_mode = open(bp, encoding="utf-8").read()
        finally:
            import shutil
            shutil.rmtree(d, ignore_errors=True)
        lone = any(x.endswith("\r") for x in child.split("\n"))
        return rc == 0 and r["exact"] is True and lone and text_mode != child, \
            "a brief of CR LF lines, one row ending in a lone CR (E-CR-END's child): exit %d, exact %s; read in text mode it is another text: %s" % (
                rc, r["exact"], text_mode != child)
    out = []
    for rid, fn in (("CT1", ct1), ("CT2", ct2), ("CT3", ct3), ("CT4", ct4), ("CT5", ct5), ("CT6", ct6), ("CT7", ct7)):
        try:
            ok, detail = fn()
        except Exception as e:  # noqa: BLE001 — a row that raised fails, named by its type; the suite goes on
            ok, detail = False, "raised %s: %s" % (type(e).__name__, str(e)[:200])
        out.append((rid, spec[rid]["printed"][0], bool(ok), detail))
    return out


def selftest():
    global PLANT
    M, V, problems = _freeze()
    if problems or M is None or V is None:
        print("[FAIL] the 0254 freeze read through frozen() — %s" % "; ".join(problems)[:300])
        print("CERT SELFTEST 0/1")
        return 1
    rows = _rows(M, V)
    for _i, name, ok, detail in rows:
        print("[%s] %s — %s" % ("PASS" if ok else "FAIL", name, detail))
    order = [i for i, _n, _o, _d in rows]
    caught = []
    for p in [p for p in M["plants"] if p["suite"] == "CERT SELFTEST"]:
        PLANT = p["value"]
        try:
            got = _rows(M, V)
        finally:
            PLANT = ""
        failed = [i for i, _n, ok, _d in got if not ok]
        k = order.index(p["caught_by"])
        ok = p["caught_by"] in failed and not [i for i in failed if order.index(i) < k] \
            and sorted(i for i in failed if order.index(i) > k) == sorted(p["fails_later"])
        caught.append(ok)
        name = [n for i, n, _o, _d in got if i == p["caught_by"]][0]
        print("[%s] %s — %s" % ("PASS" if ok else "FAIL", p["printed"], ("by: " + name[:90]) if ok else "NOT CAUGHT as frozen: failing %s, frozen %s then %s" % (
            failed or "none", p["caught_by"], p["fails_later"] or "nothing")))
    good = all(o for _i, _n, o, _d in rows) and all(caught)
    print("CERT SELFTEST %d/%d" % (sum(o for _i, _n, o, _d in rows) + sum(caught), len(rows) + len(caught)))
    return 0 if good else 1


def main(argv):
    if argv[:1] == ["selftest"]:
        return selftest()
    if argv[:1] == ["check"] and len(argv) == 3:
        # the brief read by Workspace.text()'s rule (0254): its bytes, CR LF read as LF, never in text mode (which reads a
        # lone CR as a line's end too)
        r = check(json.load(open(argv[1], encoding="utf-8")), open(argv[2], "rb").read().replace(b"\r\n", b"\n").decode("utf-8"))
        print(json.dumps(r, sort_keys=True))
        return 0 if r["ok"] and r["exact"] else 1
    print("usage: python art/certificate.py selftest | check CERTIFICATE.json BRIEF.art")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
