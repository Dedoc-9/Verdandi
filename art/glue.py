# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/glue.py — GLUE-0 (0244): two edits written against one head, glued into one or not, exactly.
#
#   python art/glue.py selftest
#   python art/glue.py census [BRIEF]      every pair of a small set of the flagship's edits, glued or obstructed
#
# Two edits (revisions of the art text, as candidates carry them) made against the same head are two local sections of
# the world; they glue when they agree wherever both say something, and the glued world then says, everywhere, what
# each of them says (the sheaf condition). The scene is the space: its sections are its pieces, every box, light and
# mover by its id, every material by its name, the environment. For each edit, the pieces it changes from the base;
# for the pair:
#
#   commutes   both orders apply and give the same scene, byte for byte (the critical pair is joinable)
#   glues      it commutes, the glued scene changes exactly the union of what each changes, and on every piece both
#              change both give the same value as the glued one (they agree on the overlap)
#
# Otherwise the pair is OBSTRUCTED and its obstruction is an object, not a failure (as merges are pushouts in
# Mimram and Di Giusto's category of patches, a conflict there an object of its own): which orders would not apply and
# why, which pieces the two orders leave different, which pieces the two edits set differently; its sha256, taken
# over the pair's canonical form (the two edits in sorted order), is the same whichever edit is named first and on
# every machine. Composition here is of what edits ask for: a '+' of a statement already there word for word, or a
# '-' of one already gone, asks for nothing more (the studio's own admission stays as strict as it was). Exact: text,
# bytes and sha256; nothing measured. Standard library only.

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FORMAT, VERSION = "VERDANDI-GLUE", "0"
PLANT = ""
PLANTS = ("glue-sections-unchecked", "glue-fingerprint-ordered", "glue-repeat-refused")


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def enc(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compose(text, *revisions):
    """The text with each revision applied in turn ('+' of a statement already there word for word, and '-' of one
    already gone, ask for nothing), or (None, why)."""
    import director as D
    import dress
    for rev in revisions:
        lines = []
        for ln in rev:
            body = ln[2:].strip()
            rows = {dress.statement_key(r.split("#", 1)[0].split()): " ".join(r.split("#", 1)[0].split())
                    for r in text.split("\n") if r.split("#", 1)[0].split()}
            if PLANT != "glue-repeat-refused":
                if ln[0] == "+" and rows.get(dress.statement_key(body.split())) == " ".join(body.split()):
                    continue
                if ln[0] == "-" and body not in rows:
                    continue
            lines.append(ln)
        try:
            text, _inv = D.apply_revision(text, lines)
        except D.canon.IntentError as e:
            return None, "%s: %s" % (e.code, str(e).split(": ", 1)[-1][:120])
    return text, ""


def sections(scene_bytes):
    """The scene's sections: every piece by its id (collision, dressing, lights, movers), every material by its name,
    the environment; each its canonical JSON, less `by` (the hash of the statement that made the piece: provenance, not
    what the world is, so a building's statement rewritten does not by that alone change every bay it makes)."""
    S = json.loads(scene_bytes)
    out = {}
    for kind in ("collision", "visuals", "lights", "movers"):
        for x in S.get(kind, []):
            out["%s:%s" % (kind, x.get("id"))] = enc({k: v for k, v in x.items() if k != "by"})
    for name, m in sorted((S.get("materials") or {}).items()):
        out["material:" + name] = enc(m)
    out["environment"] = enc(S.get("environment"))
    return out


def changed(s0, s1):
    return sorted(k for k in set(s0) | set(s1) if s0.get(k) != s1.get(k))


def judge(text, a, b, scene):
    """The pair (a, b) of revisions against `text`, `scene(text)` giving the scene's bytes: {verdict, commutes, glues,
    support, overlap, obstruction, fingerprint}. See the head of this file."""
    s0 = sections(scene(text))
    ta, why_a = compose(text, a)
    tb, why_b = compose(text, b)
    tab, why_ab = compose(text, a, b)
    tba, why_ba = compose(text, b, a)
    obstruction = {}
    commutes = glues = False
    if tab is None or tba is None or ta is None or tb is None:
        obstruction["orders"] = {"a": why_a, "b": why_b, "ab": why_ab, "ba": why_ba}
    else:
        sa, sb = sections(scene(ta)), sections(scene(tb))
        sab_bytes, sba_bytes = scene(tab), scene(tba)
        sab, sba = sections(sab_bytes), sections(sba_bytes)
        commutes = sab_bytes == sba_bytes
        if not commutes:
            obstruction["orders_differ_on"] = changed(sab, sba)
        ca, cb, cg = set(changed(s0, sa)), set(changed(s0, sb)), set(changed(s0, sab))
        disagree = sorted(k for k in ca & cb if not (sa.get(k) == sb.get(k) == sab.get(k)))
        lost = sorted(k for k in ca - cb if sab.get(k) != sa.get(k)) + sorted(k for k in cb - ca if sab.get(k) != sb.get(k))
        extra = sorted(cg - (ca | cb))
        if PLANT == "glue-sections-unchecked":
            disagree, lost, extra = [], [], []
        if disagree:
            obstruction["disagree_on"] = [{"section": k, "a": sha256(sa.get(k, "").encode("ascii"))[:16], "b": sha256(sb.get(k, "").encode("ascii"))[:16],
                                           "glued": sha256(sab.get(k, "").encode("ascii"))[:16]} for k in disagree]
        if lost or extra:
            obstruction["not_their_union"] = {"lost": lost, "extra": extra}
        glues = commutes and not disagree and not lost and not extra
        support = {"a": sorted(ca), "b": sorted(cb)}
    ops = [sha256(enc(list(a)).encode("ascii")), sha256(enc(list(b)).encode("ascii"))]
    pair = ops if PLANT == "glue-fingerprint-ordered" else sorted(ops)
    if obstruction and ops != sorted(ops) and PLANT != "glue-fingerprint-ordered":
        # the obstruction said of (b, a) as of (a, b): the edits' roles swapped back
        obstruction = json.loads(json.dumps(obstruction).replace('"a"', '"@B"').replace('"b"', '"a"').replace('"@B"', '"b"')
                                 .replace('"ab"', '"@BA"').replace('"ba"', '"ab"').replace('"@BA"', '"ba"'))
    fp = sha256(enc({"format": FORMAT, "pair": pair, "obstruction": obstruction}).encode("ascii")) if obstruction else ""
    out = {"format": FORMAT, "version": VERSION, "verdict": "GLUE" if glues else "OBSTRUCTED", "commutes": commutes, "glues": glues,
           "obstruction": obstruction, "fingerprint": fp}
    if tab is not None and ta is not None and tb is not None:
        out["support"] = support
        out["overlap"] = sorted(set(support["a"]) & set(support["b"]))
        out["glued_text_sha256"] = sha256(tab.encode("utf-8")) if glues else ""
    return out


# ------------------------------------------------------------------------------------------------ the census
OPS = (("panel b3", ["+ bay 10,2-17,2:s-b3-f2 panel brick"]),
       ("blank b3", ["+ bay 10,2-17,2:s-b3-f2 blank"]),
       ("panel b4", ["+ bay 10,2-17,2:s-b4-f2 panel brick"]),
       ("face panels", ["= building north-lane brick 14 10,2 17,2 face panel steel_rust storey 3.5"]),
       ("raised 16 m", ["= building north-lane brick 16 10,2 17,2 face window glass_wired storey 3.5"]),
       ("lighter glass", ["= material glass_wired 92,108,118 0.10 0.0"]),
       ("lamps 300 cd", ["= lamp north-lane 255,172,96 300 4"]))


def scene_of(brief):
    import dress

    def scene(text):
        A = dress.parse(text, brief + ".art")
        A["name"], A["sha256"] = brief, sha256(text.encode("utf-8"))
        return dress.export(A)["scene_bytes"]
    return scene


def census(brief="foundry-yard"):
    text = open(os.path.join(HERE, "briefs", brief + ".art"), encoding="utf-8").read()
    scene = scene_of(brief)
    rows = []
    for i in range(len(OPS)):
        for j in range(i + 1, len(OPS)):
            r = judge(text, OPS[i][1], OPS[j][1], scene)
            rows.append({"a": OPS[i][0], "b": OPS[j][0], "verdict": r["verdict"], "commutes": r["commutes"], "overlap": r.get("overlap", []),
                         "kind": sorted(r["obstruction"]), "fingerprint": r["fingerprint"]})
    return rows


# ------------------------------------------------------------------------------------------------ self-test
def selftest():
    import time
    rows = []

    def row(n, ok, detail):
        rows.append((n, bool(ok)))
        if not PLANT:
            print("[%s] %s — %s" % ("PASS" if ok else "FAIL", n, detail))
    brief = "foundry-yard"
    text = open(os.path.join(HERE, "briefs", brief + ".art"), encoding="utf-8").read()
    scene = scene_of(brief)
    op = dict(OPS)
    g = judge(text, op["panel b3"], op["panel b4"], scene)
    row("two bays of the flagship, two edits: they commute and glue, the glued world changing exactly what each changes",
        g["verdict"] == "GLUE" and g["commutes"] and not g["overlap"] and len(g["support"]["a"]) == len(g["support"]["b"]) == 1 and g["glued_text_sha256"],
        "each changes %s and %s; nothing in common; glued text %s" % (g["support"]["a"], g["support"]["b"], g["glued_text_sha256"][:12]))
    o1, o2 = judge(text, op["panel b3"], op["blank b3"], scene), judge(text, op["blank b3"], op["panel b3"], scene)
    row("one bay, two values: OBSTRUCTED, the obstruction an object with one fingerprint whichever edit is named first",
        o1["verdict"] == o2["verdict"] == "OBSTRUCTED" and o1["fingerprint"] == o2["fingerprint"] != "" and "orders" in o1["obstruction"],
        "neither order applies (%s); fingerprint %s both ways" % (o1["obstruction"]["orders"]["ab"][:60], o1["fingerprint"][:16]))
    same = judge(text, op["panel b3"], op["panel b3"], scene)
    row("one bay, the same value twice: they agree on the overlap and glue (an edit already made asks for nothing)",
        same["verdict"] == "GLUE" and same.get("overlap") == same.get("support", {}).get("a"), "overlap %s, agreed" % same.get("overlap"))
    f = judge(text, op["face panels"], op["panel b3"], scene)
    row("the building's face and one of its bays: they commute (the bay's statement wins in either order) but do not glue: they set bay 3 differently",
        f["commutes"] and not f["glues"] and [d["section"] for d in f["obstruction"].get("disagree_on", [])] == ["visuals:building:10,2-17,2:s-b3-f2"],
        "commutes %s; disagree on %s" % (f["commutes"], [d["section"] for d in f["obstruction"].get("disagree_on", [])]))
    m = judge(text, op["lighter glass"], op["panel b3"], scene)
    row("a material and a bay: different sections, they glue", m["verdict"] == "GLUE" and not m["overlap"],
        "changes %d and %d sections; glued" % (len(m["support"]["a"]), len(m["support"]["b"])))
    if not PLANT:
        t0 = time.perf_counter()
        table = census(brief)
        secs = time.perf_counter() - t0
        again = census(brief)
        tally = {}
        for r in table:
            tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
        row("the census of the flagship's seven edits: every pair judged, the same table twice",
            len(table) == 21 and table == again,
            "%d pairs in %.1f s: %s; obstructed: %s" % (len(table), secs, tally, "; ".join("%s / %s (%s)" % (r["a"], r["b"], ",".join(r["kind"]))
                                                                                       for r in table if r["verdict"] == "OBSTRUCTED")))
    if PLANT:
        return rows
    caught = []
    for p in PLANTS:
        globals()["PLANT"] = p
        try:
            failed = [n for n, ok in selftest() if not ok]
        except Exception as e:  # noqa: BLE001 — a plant that breaks the run is caught by it
            failed = ["the run: %s" % type(e).__name__]
        finally:
            globals()["PLANT"] = ""
        caught.append(bool(failed))
        print("[%s] glue plant %s caught — %s" % ("PASS" if failed else "FAIL", p, ("by: " + "; ".join(f_[:70] for f_ in failed)) if failed else "NOT CAUGHT"))
    ok = all(o for _n, o in rows) and all(caught)
    print("GLUE SELFTEST %d/%d" % (sum(o for _n, o in rows) + sum(caught), len(rows) + len(caught)))
    return 0 if ok else 1


def main(argv):
    if argv[:1] == ["selftest"]:
        return selftest()
    if argv[:1] == ["census"]:
        for r in census(argv[1] if len(argv) > 1 else "foundry-yard"):
            print("%-14s %-14s %-10s %-8s %s %s" % (r["a"], r["b"], r["verdict"], "commutes" if r["commutes"] else "", ",".join(r["kind"]), r["fingerprint"][:16]))
        return 0
    print("usage: python art/glue.py selftest | census [BRIEF]")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
