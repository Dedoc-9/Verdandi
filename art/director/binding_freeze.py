# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/director/binding_freeze.py — BINDING-0's 0253 freeze read and checked: the test matrix (0253-matrix.json) and the
# conformance vectors (0253-vectors.json), each in BINDING-0 version 0's one byte form, held to the sha256 recorded for
# it in frozen-0253.jsonl (a record of its own, outside register.jsonl: neither file is a contract version, and neither
# name matches the register's contract pattern). Nothing here enforces anything, and nothing here defines a match: v0
# is the authority, the vectors its prose made executable, and this reader checks only that the files are the ones
# recorded and that every vector is well formed and agrees with itself (a record's bytes its record's one form, a
# piece's and a press's outcome the precedence over the outcomes it lists, a preview id the sha256 of its object's one
# form), that every item the freeze resolved says it was read from v0's text and quotes v0's words as they stand in the
# registered file, and that no matrix row is left open.
#
#   python art/director/binding_freeze.py check     BINDING-0 0253 FREEZE FROZEN ... (exit 0), or each problem (exit 1)
#
# Standard library only.

import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import binding  # noqa: E402 — the register's own reader: its canonical form and its contract pattern, never redefined

FOLDER = binding.FOLDER
RECORD = "frozen-0253.jsonl"
FILES = {"0253-matrix.json": "matrix", "0253-vectors.json": "vectors"}
LINE_KEYS = ("contract", "contract_sha256", "file", "of", "patch", "sha256", "status", "version")
STATUSES = ("frozen",)
READ_FROM_V0 = "read from v0's text, never a new rule"
HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")
SEQ = re.compile(r"\A(0|[1-9][0-9]*)\Z")
OUTCOMES = ("MATCH", "MISMATCH", "UNKNOWN")
RECORD_KEYS = ("candidate", "contract", "decision", "director_code", "evidence", "intent_sha256", "of", "operation", "sha256", "version")
ENTRY_KEYS = ("declared", "expected", "field", "kind", "outcome")
FIELD_ORDER = {"still": ("scene",), "undo": ("of", "scene")}


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def compact(doc):
    return json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def piece(outs):
    return "UNKNOWN" if "UNKNOWN" in outs else "MISMATCH" if "MISMATCH" in outs else "MATCH"


def press(entries):
    for code, out in (("BINDING-UNKNOWN", "UNKNOWN"), ("BINDING-MISMATCH", "MISMATCH")):
        for e in entries:
            if e["outcome"] == out:
                return code, "%s.%s" % (e["kind"], e["field"])
    return None, ""


def preview_rank(field):
    """the place of a named preview's field in v0's precedence: the name, its recorded candidate scene, then its
    candidate-side stills by pose as an integer; None for a field that is none of these"""
    if field == "preview":
        return (0, 0)
    if field == "candidate_sha":
        return (1, 0)
    m = re.fullmatch(r"candidate-(0|[1-9][0-9]*)", field)
    return (2, int(m.group(1))) if m else None


def evidence_problems(vid, entries, not_reached_ok):
    """an evidence list in v0's precedence (still, then the named preview's fields, then an undo's of and scene), its
    entries well formed"""
    out, last = [], None
    kinds_rank = {"still": 0, "preview": 1, "undo": 2}
    for e in entries:
        if not isinstance(e, dict) or tuple(sorted(e)) != ENTRY_KEYS or not all(isinstance(e[k], str) for k in ENTRY_KEYS):
            out.append("FREEZE-VECTOR: %s has an evidence entry not of v0's five string fields" % vid)
            continue
        if e["kind"] not in kinds_rank:
            out.append("FREEZE-VECTOR: %s names a kind %r" % (vid, e["kind"]))
            continue
        if e["outcome"] not in OUTCOMES + (("not reached",) if not_reached_ok else ()):
            out.append("FREEZE-VECTOR: %s's entry %s.%s has the outcome %r" % (vid, e["kind"], e["field"], e["outcome"]))
        if e["outcome"] == "not reached" and e["expected"] != "":
            out.append("FREEZE-VECTOR: %s's entry %s.%s is not reached and expects %r" % (vid, e["kind"], e["field"], e["expected"]))
        if e["kind"] == "preview":
            r = preview_rank(e["field"])
        else:
            r = (FIELD_ORDER[e["kind"]].index(e["field"]), 0) if e["field"] in FIELD_ORDER[e["kind"]] else None
        if r is None:
            out.append("FREEZE-VECTOR: %s's entry names the field %r of a %s" % (vid, e["field"], e["kind"]))
            continue
        key = (kinds_rank[e["kind"]],) + r
        if last is not None and key <= last:
            out.append("FREEZE-VECTOR: %s's entries are not in v0's precedence at %s.%s" % (vid, e["kind"], e["field"]))
        last = key
    return out


def v0_words(v0, path, words):
    """whether `words` stand, exactly, in the registered contract's field `path` (dotted by '/'; a list's items searched)"""
    node = v0
    try:
        for p in path.split("/"):
            node = node[int(p)] if isinstance(node, list) else node[p]
    except (KeyError, IndexError, ValueError, TypeError):
        return False
    texts = node if isinstance(node, list) else [node]
    return isinstance(words, str) and bool(words) and any(isinstance(t, str) and words in t for t in texts)


def vectors_problems(doc, v0_sha):
    out, ids = [], []
    facts = doc.get("facts") or {}
    if not facts or not all(isinstance(f, dict) and HEX64.match(f.get("value", "")) and f.get("label") for f in facts.values()):
        out.append("FREEZE-VECTOR: the facts are not each a label and 64 lower hex")
    for v in doc["keeping"]["vectors"]:
        ids.append(v.get("id"))
        if not isinstance(v.get("scene_query"), str) or not isinstance(v.get("kept"), str) or (v["kept"] and not HEX64.match(v["kept"])):
            out.append("FREEZE-VECTOR: keeping %s is not a query and a kept value (\"\" or 64 lower hex)" % v.get("id"))
    for v in (doc.get("preview id") or {}).get("vectors") or []:
        ids.append(v.get("id"))
        obj, b = v.get("object"), v.get("bytes")
        ok = isinstance(obj, dict) and sorted(obj) == ["binding", "drawn", "report_sha256"] and isinstance(obj.get("binding"), dict) and \
            sorted(obj["binding"]) == ["base_sha", "candidate_sha", "head"] and all(HEX64.match(x) if isinstance(x, str) else False for x in obj["binding"].values()) and \
            isinstance(obj.get("drawn"), dict) and all(re.fullmatch(r"(base|candidate)-(0|[1-9][0-9]*)", k) and isinstance(x, str) and (x == "" or HEX64.match(x))
                                                       for k, x in obj["drawn"].items()) and HEX64.match(obj.get("report_sha256") or "")
        if not ok or not isinstance(b, str) or compact(obj) != b or b.endswith("\n") or sha256(b.encode("ascii")) != v.get("preview_id"):
            out.append("FREEZE-VECTOR: preview id %s is not the sha256 of its object's one form ({binding, drawn, report_sha256}, sorted keys, "
                       "',' and ':', ASCII, nothing added)" % v.get("id"))
    for v in doc["field"]["vectors"]:
        ids.append(v.get("id"))
        d, o, e = v.get("declared"), v.get("outcome"), v.get("entry")
        if not isinstance(d, dict) or not isinstance(d.get("present"), bool) or (d["present"] != ("value" in d)):
            out.append("FREEZE-VECTOR: field %s's declared is not {present, value}" % v.get("id"))
            continue
        if o == "no entry":
            if e is not None or d["present"] or (v.get("kind"), v.get("field")) != ("preview", "preview"):
                out.append("FREEZE-VECTOR: field %s has no entry but is not a preview's absent name" % v.get("id"))
            continue
        if o not in OUTCOMES or not isinstance(e, dict):
            out.append("FREEZE-VECTOR: field %s's outcome is %r" % (v.get("id"), o))
            continue
        out += evidence_problems(v["id"], [e], False)
        val = d.get("value")
        if (e.get("kind"), e.get("field"), e.get("outcome")) != (v.get("kind"), v.get("field"), o) or e.get("declared") != (val if isinstance(val, str) else ""):
            out.append("FREEZE-VECTOR: field %s's entry is not its declared value and outcome (a JSON string as it is, else \"\")" % v["id"])
        if (v["kind"], v["field"]) == ("preview", "preview"):
            fin = v.get("finished_previews_of_candidate")
            named = isinstance(val, str) and HEX64.match(val) and isinstance(fin, list) and val in fin
            if (o == "MATCH") != bool(named) or e.get("expected") != (val if named else ""):
                out.append("FREEZE-VECTOR: field %s's name is MATCH, expecting itself, exactly when it names a finished preview of the candidate" % v["id"])
        else:
            form = SEQ if (v["kind"], v["field"]) == ("undo", "of") else HEX64
            exp = v.get("expected")
            want = "UNKNOWN" if not (isinstance(val, str) and form.match(val)) else "MATCH" if val == exp else "MISMATCH"
            if o != want or e.get("expected") != exp:
                out.append("FREEZE-VECTOR: field %s says %s; its declared and expected values give %s" % (v["id"], o, want))
    for v in doc["piece"]["vectors"]:
        ids.append(v.get("id"))
        outs = [f.get("outcome") for f in v.get("fields") or []]
        if not outs or not all(x in OUTCOMES for x in outs) or v.get("piece") != piece(outs):
            out.append("FREEZE-VECTOR: piece %s's outcome is not the precedence over its fields'" % v.get("id"))
    for v in doc["piece"]["order"]:
        ids.append(v.get("id"))
        want = ["preview", "candidate_sha"] + ["candidate-%d" % k for k in sorted(int(x.split("-", 1)[1]) for x in v.get("drawn", []) if x.startswith("candidate-"))]
        if v.get("fields") != want:
            out.append("FREEZE-VECTOR: order %s is not the name, the candidate scene, then the candidate side's poses as integers" % v.get("id"))
    for v in doc["press"]["vectors"]:
        ids.append(v.get("id"))
        ents = v.get("entries") or []
        code, names = press(ents)
        if (code or "none: no binding refusal") != v.get("answer") or names != v.get("names") or not all(e.get("outcome") in OUTCOMES for e in ents):
            out.append("FREEZE-VECTOR: press %s's answer is not the precedence over its entries" % v.get("id"))
    for v in doc["record"]["vectors"]:
        ids.append(v.get("id"))
        rec, b = v.get("record"), v.get("bytes")
        if not isinstance(rec, dict) or tuple(sorted(rec)) != RECORD_KEYS:
            out.append("FREEZE-VECTOR: record %s does not have v0's ten fields" % v.get("id"))
            continue
        if not isinstance(b, str) or compact(rec) != b or sha256(b.encode("ascii")) != v.get("sha256"):
            out.append("FREEZE-VECTOR: record %s's bytes are not its record's one form, or its sha256 not theirs" % v["id"])
        if (rec["contract"], rec["version"], rec["sha256"]) != ("BINDING-0", 0, v0_sha) or rec["operation"] not in ("admit", "undo"):
            out.append("FREEZE-VECTOR: record %s does not name BINDING-0 version 0 by its sha256, or an operation" % v["id"])
        ev = rec["evidence"] if isinstance(rec["evidence"], list) else []
        out += evidence_problems(v["id"], ev, True)
        nr = [e for e in ev if isinstance(e, dict) and e.get("outcome") == "not reached"]
        if nr and len(nr) != len(ev):
            out.append("FREEZE-VECTOR: record %s has entries both reached and not reached" % v["id"])
        if not nr:
            code, _n = press(ev)
            want = code or ("ADMIT" if rec["operation"] == "admit" else "UNDONE")
            if rec["decision"] != want:
                out.append("FREEZE-VECTOR: record %s decides %s where its outcomes give %s" % (v["id"], rec["decision"], want))
        elif rec["decision"] in ("ADMIT", "UNDONE", "BINDING-MISMATCH", "BINDING-UNKNOWN"):
            out.append("FREEZE-VECTOR: record %s was not reached and decides %s" % (v["id"], rec["decision"]))
        if rec["decision"].startswith("BINDING-") and rec["director_code"] != "":
            out.append("FREEZE-VECTOR: record %s is a binding refusal with a director code" % v["id"])
        if rec["operation"] == "undo" and (rec["candidate"], rec["intent_sha256"]) != ("", ""):
            out.append("FREEZE-VECTOR: record %s is an undo naming a candidate or an intent" % v["id"])
    if len(set(ids)) != len(ids) or not all(isinstance(i, str) and i for i in ids):
        out.append("FREEZE-VECTOR: the vectors' ids are not each its own")
    return out, len(ids)


def matrix_problems(doc, v0):
    out = []
    rows = doc.get("rows") or []
    ids = [r.get("id") for r in rows]
    if [i for i in ids if re.fullmatch(r"M\d+", i or "")] != ["M%d" % k for k in range(1, 26)] or len(set(ids)) != len(ids):
        out.append("FREEZE-MATRIX: the rows are not M1 to M25 in order, each once, with their sub-rows")
    names, plants = [], []
    for r in rows:
        for x in r.get("runs") or []:
            n = x.get("row")
            if not isinstance(n, str) or not n or " — " in n or "\n" in n or n != n.strip():
                out.append("FREEZE-MATRIX: %s has a row whose name is empty, cut by R5 at ' — ', or not stripped" % r.get("id"))
                continue
            names.append(n)
            if x.get("plant") is True:
                plants.append(n)
                if not n.startswith("BINDING plant: ") or not x.get("caught when"):
                    out.append("FREEZE-MATRIX: %s's plant row %r does not begin 'BINDING plant: ' or says not when it is caught" % (r["id"], n))
            elif re.search(r"\bplant\b", n):
                out.append("FREEZE-MATRIX: %s's row %r is no plant row and names a plant" % (r["id"], n))
            for k in ("switches", "answer", "director_code", "record", "ledger", "brief", "certificate"):
                if k not in x:
                    out.append("FREEZE-MATRIX: %s's row %r has no %s" % (r["id"], n, k))
    if len(set(names)) != len(names):
        out.append("FREEZE-MATRIX: two rows share a name")
    pr = doc.get("plant rows") or {}
    if pr.get("names") != plants or pr.get("k") != len(plants) or len(set(plants)) != len(plants):
        out.append("FREEZE-MATRIX: the plant rows listed are not the matrix's, in its order, k their number")
    census = doc.get("R5 census on 1381b31")
    if census is not None and census.get("this matrix's plant keys among them") != 0:
        out.append("FREEZE-MATRIX: a plant name is a key R5 reads on 1381b31")
    opens = [o.get("id") for o in doc.get("open") or []]
    for r in rows:
        if "status" in r:
            out.append("FREEZE-MATRIX: %s carries a status of its own (%r): a frozen row is frozen whole" % (r["id"], r["status"]))
    resolved = doc.get("resolved") or []
    rids = [x.get("id") for x in resolved]
    if len(set(rids + opens)) != len(rids + opens) or not all(isinstance(i, str) and re.fullmatch(r"OPEN-[A-Z0-9]+", i) for i in rids + opens):
        out.append("FREEZE-MATRIX: the resolved and open items are not each an OPEN-id of its own")
    for x in resolved:
        quotes = x.get("v0's words") if x.get("id") != "OPEN-Q" else x.get("v0 agrees")
        if x.get("id") != "OPEN-Q" and x.get("status") != READ_FROM_V0:
            out.append("FREEZE-MATRIX: %s is resolved without saying it is %s" % (x.get("id"), READ_FROM_V0))
        if x.get("id") == "OPEN-Q" and not all(isinstance(w, str) and w for w in (x.get("his words") or {}).values()):
            out.append("FREEZE-MATRIX: OPEN-Q is resolved without his words")
        if not quotes or not all(isinstance(q, dict) and v0_words(v0, q.get("v0", ""), q.get("words")) for q in quotes):
            out.append("FREEZE-MATRIX: %s quotes words that do not stand in BINDING-0 version 0 as registered" % x.get("id"))
    for x in doc.get("open") or []:
        if not x.get("why") or not x.get("what"):
            out.append("FREEZE-MATRIX: %s is open without saying what and why" % x.get("id"))
    return out, len(names), len(plants), opens


def check(folder=FOLDER):
    problems = []
    seen, reg_problems = binding.check(folder)
    if reg_problems or [(s["contract"], s["version"]) for s in seen] != [("BINDING-0", 0)]:
        return ["FREEZE-REGISTER: the register does not hold BINDING-0 version 0 as it stands: " + "; ".join(reg_problems)[:300]], None
    v0_sha = seen[0]["sha256"]
    with open(os.path.join(folder, seen[0]["file"]), "rb") as fh:
        v0 = json.loads(fh.read().decode("utf-8"))
    try:
        raw = open(os.path.join(folder, RECORD), "rb").read()
        text = raw.decode("ascii")
    except (OSError, UnicodeDecodeError) as e:
        return ["FREEZE-RECORD: %s cannot be read as ASCII: %s" % (RECORD, e)], None
    if not text.endswith("\n") or "\r" in text:
        problems.append("FREEZE-RECORD: %s's lines are not LF-ended" % RECORD)
    lines, status = {}, set()
    for n, ln in enumerate(text.split("\n")[:-1], 1):
        try:
            rec = json.loads(ln)
        except ValueError:
            problems.append("FREEZE-RECORD: line %d is not JSON" % n)
            continue
        if not isinstance(rec, dict) or tuple(sorted(rec)) != LINE_KEYS or compact(rec) != ln:
            problems.append("FREEZE-RECORD: line %d is not a record line in its one form (%s)" % (n, ", ".join(LINE_KEYS)))
            continue
        if (rec["contract"], rec["version"], rec["contract_sha256"], rec["patch"]) != ("BINDING-0", 0, v0_sha, "0253") or \
                FILES.get(rec["file"]) != rec["of"] or rec["status"] not in STATUSES or not HEX64.match(rec["sha256"]) or rec["file"] in lines:
            problems.append("FREEZE-RECORD: line %d does not record one of %s once, against BINDING-0 version 0 %s" % (n, sorted(FILES), v0_sha[:16]))
            continue
        lines[rec["file"]] = rec["sha256"]
        status.add(rec["status"])
    if sorted(lines) != sorted(FILES):
        problems.append("FREEZE-RECORD: %s records %s, not %s" % (RECORD, sorted(lines), sorted(FILES)))
    docs = {}
    for f in sorted(FILES):
        if binding.CONTRACT_FILE.match(f):
            problems.append("FREEZE-NAME: %s matches the register's contract pattern" % f)
        try:
            body = open(os.path.join(folder, f), "rb").read()
        except OSError:
            problems.append("FREEZE-ABSENT: %s is not there" % f)
            continue
        if f in lines and sha256(body) != lines[f]:
            problems.append("FREEZE-STALE: %s is not the file recorded (its sha256 %s, recorded %s)" % (f, sha256(body)[:16], lines[f][:16]))
        try:
            doc = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            problems.append("FREEZE-UNREADABLE: %s is not JSON" % f)
            continue
        if binding.canonical(doc) != body:
            problems.append("FREEZE-NOT-CANONICAL: %s is not in v0's one byte form" % f)
        c = doc.get("cites") if isinstance(doc, dict) else None
        if not isinstance(c, dict) or (c.get("contract"), c.get("version"), c.get("sha256")) != ("BINDING-0", 0, v0_sha) or \
                not c.get("rulings") or not all(HEX64.match(r.get("sha256", "")) and r.get("file") for r in c["rulings"]):
            problems.append("FREEZE-CITES: %s does not cite BINDING-0 version 0 by its sha256 and his rulings by theirs" % f)
        docs[FILES[f]] = doc
    counts = {}
    if "vectors" in docs:
        p, counts["vectors"] = vectors_problems(docs["vectors"], v0_sha)
        problems += p
    if "matrix" in docs:
        p, counts["rows"], counts["plants"], counts["open"] = matrix_problems(docs["matrix"], v0)
        counts["entries"] = len(docs["matrix"].get("rows") or [])
        problems += p
    return problems, {"lines": lines, "status": status, "counts": counts, "v0": v0_sha}


def main(argv):
    if argv[:1] == ["check"]:
        problems, info = check(argv[1] if len(argv) > 1 else FOLDER)
        for p in problems:
            print(p)
        if info:
            for f, h in sorted(info["lines"].items()):
                print("%s sha256 %s" % (f, h))
            k = info["counts"]
            opens = k.get("open", [])
            print("BINDING-0 0253 FREEZE %s: %d vectors, %d matrix entries naming %d rows (%d plant rows) against BINDING-0 version 0 sha256 %s; %s" % (
                "READ" if problems else "FROZEN",
                k.get("vectors", 0), k.get("entries", 0), k.get("rows", 0), k.get("plants", 0), info["v0"],
                ("open, no row or vector deciding it: %s" % ", ".join(opens)) if opens else "nothing open"))
        return 0 if not problems else 1
    print("usage: python art/director/binding_freeze.py check [FOLDER]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
