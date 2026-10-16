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
#   statements token for token (`statements`: the same scene, another spelling of the text); neither: CERT-INVERSE.
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
PLANTS = ("cert-child-unhashed", "cert-statements-as-exact", "cert-heads-unchecked")


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
    """The statement keys a revision touches (DIRECTOR-0's: '= stmt' and '+ stmt' by their statement's key, '- key')."""
    import dress
    out = []
    for ln in revision:
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
        back, _again = D.apply_revision(child_text, cert["inverse"]["revision"])
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
def selftest():
    D = _director()
    rows = []

    def row(n, ok, detail):
        rows.append((n, bool(ok)))
        if not PLANT:
            print("[%s] %s — %s" % ("PASS" if ok else "FAIL", n, detail))
    text = open(os.path.join(HERE, "briefs", "foundry-yard.art"), encoding="utf-8").read()
    parts = {"art_sha256": sha256(text.encode("utf-8")), "exporter_sha256": "e" * 64, "world_sha256": "w" * 64}

    def admitted(rev, seq="7"):
        t1, inv = D.apply_revision(text, rev)
        p1 = dict(parts, art_sha256=sha256(t1.encode("utf-8")))
        ev = {"seq": seq, "evaluation": "6", "head_before": D.canon.head(parts), "head_after": D.canon.head(p1), "parts_after": p1, "inverse": inv}
        return make("foundry-yard", ev, rev, text, t1, {"producer": "selftest"}, "r", "A"), t1
    cases = (("a bay panelled ('+', a statement added)", ["+ bay 10,2-17,2:s-b3-f2 panel brick"], True),
             ("the lanes' lamps changed ('=', a statement written in single spaces)", ["= lamp north-lane 255,172,96 300 4"], True),
             ("the flagship raised to 16 m ('=', its statement written in aligned columns)", ["= building north-lane brick 16 10,2 17,2 face window glass_wired storey 3.5"], False),
             ("a lamp removed and a bay added ('-' and '+')", ["- lamp plaza", "+ bay 10,2-17,2:s-b3-f2 blank"], False))
    got = []
    for name, rev, want_exact in cases:
        cert, t1 = admitted(rev)
        r = check(cert, t1)
        got.append((name, r, want_exact))
    row("each admission's certificate: the inverse applied to the child gives the parent, byte for byte or (said) token for token",
        all(r["ok"] and r["exact"] == w and r["statements"] for _n, r, w in got),
        "; ".join("%s: %s" % (n, "exact" if r["exact"] else "statements only" if r["statements"] else "NOT") for n, r, _w in got))
    import dress
    scene = lambda t: dress.export(dict(dress.parse(t, "foundry-yard.art"), name="foundry-yard", sha256=sha256(t.encode("utf-8"))))["scene_bytes"]
    cert, t1 = admitted(["= building north-lane brick 16 10,2 17,2 face window glass_wired storey 3.5"])
    back, _x = D.apply_revision(t1, cert["inverse"]["revision"])
    cert4, t4 = admitted(["- lamp plaza", "+ bay 10,2-17,2:s-b3-f2 blank"])
    back4, _x = D.apply_revision(t4, cert4["inverse"]["revision"])
    s0 = scene(text)
    row("found: an '=' on a statement written in aligned columns, and a '-', are undone statement for statement but not byte for byte "
        "(the aligned line comes back in single spaces; the removed one comes back at the end, without its comment): the scene as before, the head not",
        sha256(back.encode("utf-8")) != parts["art_sha256"] and sha256(back4.encode("utf-8")) != parts["art_sha256"]
        and statements(back) == statements(text) == statements(back4) and scene(back) == s0 == scene(back4)
        and D.canon.head(dict(parts, art_sha256=sha256(back.encode("utf-8")))) != D.canon.head(parts),
        "the undone building reads %r; the lamp comes back on line %d of %d (it stood on line %d); both scenes the same bytes as before" % (
            [ln for ln in back.split("\n") if ln.startswith("building north-lane brick")][0][:44],
            [i for i, ln in enumerate(back4.split("\n"), 1) if ln.startswith("lamp plaza")][0], len(back4.split("\n")),
            [i for i, ln in enumerate(text.split("\n"), 1) if ln.startswith("lamp plaza")][0]))
    cert, t1 = admitted(["+ bay 10,2-17,2:s-b3-f2 panel brick"])
    bad_inv = json.loads(json.dumps(cert))
    bad_inv["inverse"]["revision"] = ["- bay 10,2-17,2:s-b4-f2"]
    bad_head = json.loads(json.dumps(cert))
    bad_head["parent"]["head"] = "0" * 64
    plants = [("a wrong inverse", check(bad_inv, t1), "CERT-INVERSE"), ("a child that is not the admitted text", check(cert, t1 + "# edited\n"), "CERT-CHILD"),
              ("a parent head that is not its parts'", check(bad_head, t1), "CERT-HEAD"),
              ("a layout's change", check(dict(cert, child=dict(cert["child"], parts=dict(cert["child"]["parts"], world_sha256="x" * 64),
                                                                head=D.canon.head(dict(cert["child"]["parts"], world_sha256="x" * 64)))), t1), "CERT-ART-ONLY")]
    row("planted: each defect refused with its code", all(not r["ok"] and any(c.startswith(code) for c in r["codes"]) for _n, r, code in plants),
        "; ".join("%s: %s" % (n, ",".join(c.split(":")[0] for c in r["codes"])) for n, r, _c in plants))
    c1, _t = admitted(["+ bay 10,2-17,2:s-b3-f2 panel brick"])
    c2, _t = admitted(["+ bay 10,2-17,2:s-b3-f2 panel brick"])
    row("a certificate is a function of its event and texts (canonical bytes)", D.canon.dumps(c1) == D.canon.dumps(c2) and c1["support"]["statement_keys"] == ["bay 10,2-17,2:s-b3-f2"],
        "%d bytes twice the same; support %s" % (len(D.canon.dumps(c1)), c1["support"]["statement_keys"]))
    if PLANT:
        return rows
    caught = []
    for p in PLANTS:
        globals()["PLANT"] = p
        try:
            failed = [n for n, ok in selftest() if not ok]
        finally:
            globals()["PLANT"] = ""
        caught.append(bool(failed))
        print("[%s] certificate plant %s caught — %s" % ("PASS" if failed else "FAIL", p, ("by: " + "; ".join(f[:70] for f in failed)) if failed else "NOT CAUGHT"))
    ok = all(o for _n, o in rows) and all(caught)
    print("CERT SELFTEST %d/%d" % (sum(o for _n, o in rows) + sum(caught), len(rows) + len(caught)))
    return 0 if ok else 1


def main(argv):
    if argv[:1] == ["selftest"]:
        return selftest()
    if argv[:1] == ["check"] and len(argv) == 3:
        r = check(json.load(open(argv[1], encoding="utf-8")), open(argv[2], encoding="utf-8").read().replace("\r\n", "\n"))
        print(json.dumps(r, sort_keys=True))
        return 0 if r["ok"] and r["exact"] else 1
    print("usage: python art/certificate.py selftest | check CERTIFICATE.json BRIEF.art")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
