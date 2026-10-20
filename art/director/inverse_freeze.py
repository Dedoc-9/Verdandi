# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/director/inverse_freeze.py — 0254's freeze read and checked: the exact inverse's conformance vectors
# (inverse/0254-vectors.json), its test matrix (inverse/0254-matrix.json), the specification as he ruled it
# (inverse/0254-spec.md, his ruling files embedded whole) and a frozen copy of 7dee210's plaza-night ledger
# (inverse/legacy/plaza-night.7dee210.ledger), each held to the sha256 recorded for it in inverse/frozen-0254.jsonl,
# against BINDING-0 version 0 unchanged. Nothing here enforces anything and nothing here defines the revision
# language: art/director.py's apply_revision is the application, art/director/intent.py the grammar; this reader checks
# that the files are the ones recorded, that the vectors are well formed and each named by a matrix row, that every
# frozen child (of revisions, cr and guards, and of each 'only' vector that applies) is the tree's own forward child, that
# the matrix's plants and rows are in their suites' order with names R5 can count and each plant on the switch spec §8
# names for its suite, that every OPEN item a row or a vector cites is resolved with his words (each resolved entry's
# words exactly its own item's section of his ruling file), and that art/director/vectors.json, cut to the intents it
# had at 7dee210, is 7dee210's file byte for byte (the matrix's 'vectors.json at 7dee210', his OPEN-9).
#
#   python art/director/inverse_freeze.py check     INVERSE-0254 FREEZE FROZEN ... (exit 0), or READ and each problem (exit 1)
#
# frozen() is how every 0254 row of every suite gets its expectations (as binding_rows.frozen() serves 0253): it holds
# each file's bytes to its sha256 and its status and returns (matrix, vectors, ledger_copy, problems); on any problem
# every such row fails, naming the file and the two hashes.
#
# Where director.py is 7dee210's own (sha256 5300fb78…, commit 1), `check` also recomputes the legacy sections with
# that tree's own code and replays the frozen ledger copy; on any other director.py it says the recomputation was not
# reached, never passing silently. Standard library only.

import hashlib
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
FOLDER = os.path.join(HERE, "inverse")
sys.path.insert(0, HERE)
import binding  # noqa: E402 — the register's own reader: its canonical form, never redefined
import intent as canon  # noqa: E402 — the canonical reader of VERDANDI-CANON 0, never redefined

RECORD = "frozen-0254.jsonl"
FILES = {"0254-matrix.json": "matrix", "0254-spec.md": "spec", "0254-vectors.json": "vectors", "legacy/plaza-night.7dee210.ledger": "ledger copy"}
LINE_KEYS = ("contract", "contract_sha256", "file", "of", "patch", "sha256", "status", "version")
STATUSES = ("frozen",)
DIRECTOR_7DEE210 = "5300fb78826e0650bcd4a29a650a35e21955c5b3df61285da79e586828bd9f46"
PROVENANCES = ("by hand", "computed by spec254/model.py, read by hand", "computed by 7dee210")
HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")
INT = re.compile(r"\A(0|[1-9][0-9]{0,18})\Z")
OPEN_ID = re.compile(r"OPEN-[0-9]+")
SUITE_PLANT = {"DIRECTOR SELFTEST": re.compile(r"\Aplant: [a-z0-9-]+\Z"), "STUDIO SELFTEST": re.compile(r"\Aplant [a-z0-9-]+: \S.*\Z")}
# spec §8: each plant one named value of one switch, read only where it is named; the suites that hold no plant have none
SUITE_SWITCH = {"DIRECTOR SELFTEST": "director.INVERSE_PLANT", "CERT SELFTEST": "certificate.PLANT", "STUDIO SELFTEST": "studio.ACCOUNT_PLANT"}
VECTORS_JSON = os.path.join(HERE, "vectors.json")


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def compact(doc):
    return json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _record(folder, v0_sha):
    """The record's lines, {file: (of, sha256, status)}, and its problems."""
    out, problems = {}, []
    try:
        text = open(os.path.join(folder, RECORD), "rb").read().decode("ascii")
    except (OSError, UnicodeDecodeError) as e:
        return out, ["FREEZE-RECORD: %s cannot be read as ASCII: %s" % (RECORD, e)]
    if not text.endswith("\n") or "\r" in text:
        problems.append("FREEZE-RECORD: %s's lines are not LF-ended" % RECORD)
    for n, ln in enumerate(text.split("\n")[:-1], 1):
        try:
            rec = json.loads(ln)
        except ValueError:
            problems.append("FREEZE-RECORD: line %d is not JSON" % n)
            continue
        if not isinstance(rec, dict) or tuple(sorted(rec)) != LINE_KEYS or compact(rec) != ln:
            problems.append("FREEZE-RECORD: line %d is not a record line in its one form (%s)" % (n, ", ".join(LINE_KEYS)))
            continue
        if (rec["contract"], rec["version"], rec["contract_sha256"], rec["patch"]) != ("BINDING-0", 0, v0_sha, "0254") or \
                FILES.get(rec["file"]) != rec["of"] or not HEX64.match(rec["sha256"]) or rec["file"] in out:
            problems.append("FREEZE-RECORD: line %d does not record one of %s once, against BINDING-0 version 0 %s" % (n, sorted(FILES), v0_sha[:16]))
            continue
        if rec["status"] not in STATUSES:
            problems.append("FREEZE-STATUS: %s's status is %r, not frozen" % (rec["file"], rec["status"]))
        out[rec["file"]] = (rec["of"], rec["sha256"], rec["status"])
    if sorted(out) != sorted(FILES):
        problems.append("FREEZE-RECORD: %s records %s, not %s" % (RECORD, sorted(out), sorted(FILES)))
    return out, problems


def frozen(folder=FOLDER):
    """(matrix, vectors, ledger_copy, problems): each recorded file held to its sha256 and status; the two JSON files read
    in BINDING-0 v0's one byte form. A file with a problem is returned as None."""
    seen, reg = binding.check(binding.FOLDER)
    if reg or [(s["contract"], s["version"]) for s in seen] != [("BINDING-0", 0)]:
        return None, None, None, ["FREEZE-REGISTER: the register does not hold BINDING-0 version 0 as it stands: " + "; ".join(reg)[:300]]
    v0_sha = seen[0]["sha256"]
    lines, problems = _record(folder, v0_sha)
    got = {}
    for f in sorted(FILES):
        try:
            body = open(os.path.join(folder, *f.split("/")), "rb").read()
        except OSError:
            problems.append("FREEZE-ABSENT: %s is not there" % f)
            continue
        if f not in lines:
            continue
        if sha256(body) != lines[f][1]:
            problems.append("FREEZE-STALE: %s is not the file recorded (its sha256 %s, recorded %s)" % (f, sha256(body), lines[f][1]))
            continue
        if lines[f][2] != "frozen":
            continue
        if f.endswith(".json"):
            try:
                doc = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                problems.append("FREEZE-UNREADABLE: %s is not JSON" % f)
                continue
            if binding.canonical(doc) != body:
                problems.append("FREEZE-NOT-CANONICAL: %s is not in BINDING-0 v0's one byte form" % f)
                continue
            got[FILES[f]] = doc
        else:
            got[FILES[f]] = body
    return got.get("matrix"), got.get("vectors"), got.get("ledger copy"), problems


# ------------------------------------------------------------------------------------------------ well formed
def line_shape(ln):
    """A revision line the freeze holds as a stored inverse or redo: an ordinary one ('= ', '+ ', '- ', no LF, no '#'), or
    one of the three inverse-only forms of spec §2.1 (its rest its own canonical bytes, its array of the form's shape).
    The freeze's own data check; the grammar's authority is art/director/intent.py."""
    if not isinstance(ln, str) or "\n" in ln:
        return False
    if ln[:2] in ("= ", "+ ", "- "):
        return "#" not in ln
    if ln[:3] not in ("@= ", "@+ ", "@~ "):
        return False
    try:
        v = canon.loads(ln[3:].encode("ascii"))
    except (canon.IntentError, UnicodeEncodeError):
        return False
    if not isinstance(v, list):
        return False
    row = lambda x: isinstance(x, str) and "\n" not in x
    if ln[:2] == "@=":
        return len(v) == 3 and row(v[0]) and bool(INT.match(v[0])) and row(v[1]) and row(v[2])
    if ln[:2] == "@+":
        return len(v) == 3 and row(v[0]) and bool(INT.match(v[0])) and row(v[1]) and (v[2] is False or row(v[2]))
    return len(v) == 2 and all(row(x) and INT.match(x) for x in v)


def vectors_problems(doc, v0_sha):
    out, ids, hand = [], [], 0
    parents = doc.get("parents") or {}
    for pid, p in parents.items():
        if not isinstance(p, dict) or not isinstance(p.get("text"), str) or sha256(p["text"].encode("utf-8")) != p.get("sha256") or not p.get("from"):
            out.append("FREEZE-VECTOR: parent %s is not a text with its own sha256 and where it comes from" % pid)
    ptext = lambda pid: (parents.get(pid) or {}).get("text")

    def common(sec, v, fields):
        nonlocal hand
        ids.append(v.get("id"))
        if v.get("provenance") not in PROVENANCES:
            out.append("FREEZE-VECTOR: %s %s's provenance is %r" % (sec, v.get("id"), v.get("provenance")))
        hand += v.get("provenance") == "by hand"
        for k in fields:
            if k not in v:
                out.append("FREEZE-VECTOR: %s %s has no %s" % (sec, v.get("id"), k))
                return False
        return True

    def lines_ok(sec, v, keys, ordinary=False):
        for k in keys:
            ls = v.get(k)
            if not isinstance(ls, list) or not all(line_shape(x) and (not ordinary or x[:1] != "@") for x in ls):
                out.append("FREEZE-VECTOR: %s %s's %s is not a list of %s revision lines" % (sec, v.get("id"), k, "ordinary" if ordinary else "well-formed"))

    for v in (doc.get("forms") or {}).get("vectors") or []:
        if common("forms", v, ("line", "ok", "code", "version")):
            if not isinstance(v["line"], str) or not isinstance(v["ok"], bool) or v["code"] != ("" if v["ok"] else "INTENT-REVISION") or v["version"] != "0":
                out.append("FREEZE-VECTOR: forms %s is not a line, its validity and its code under version \"0\"" % v["id"])
    for sec in ("revisions", "cr"):
        for v in (doc.get(sec) or {}).get("vectors") or []:
            if common(sec, v, ("parent", "revision", "child", "inverse", "back", "redo")):
                if ptext(v["parent"]) is None or v["back"] != ptext(v["parent"]) or not isinstance(v["child"], str):
                    out.append("FREEZE-VECTOR: %s %s's back is not its parent's text, or its parent is none of 'parents'" % (sec, v["id"]))
                lines_ok(sec, v, ("revision",), True)
                lines_ok(sec, v, ("inverse", "redo"))
    for v in (doc.get("guards") or {}).get("vectors") or []:
        if common("guards", v, ("parent", "revision", "child", "inverse", "over", "expect")):
            lines_ok("guards", v, ("revision",), True)
            lines_ok("guards", v, ("inverse",))
            want = v["expect"]
            if ptext(v["parent"]) is None or not isinstance(v["over"], str) or want not in ("INTENT-APPLY", "not the parent", "equal to the parent") or \
                    (want == "INTENT-APPLY") != ("back" not in v) or ("back" in v and (v["back"] == ptext(v["parent"])) != (want == "equal to the parent")):
                out.append("FREEZE-VECTOR: guards %s's expectation is not INTENT-APPLY or a back that is, or is not, its parent as it says" % v["id"])
    for v in (doc.get("only") or {}).get("vectors") or []:
        if common("only", v, ("text", "revision", "undo", "expect")):
            lines_ok("only", v, ("revision",))
            has_at = any(x[:1] == "@" for x in v["revision"]) if isinstance(v["revision"], list) else True
            if v["undo"] is not False or v["expect"] != ("INTENT-INVERSE-ONLY" if has_at else "applies") or (v["expect"] == "applies") != ("child" in v):
                out.append("FREEZE-VECTOR: only %s is not refused INTENT-INVERSE-ONLY exactly when it holds an '@' line" % v["id"])
    leg = doc.get("legacy") or {}
    for v in leg.get("vectors") or []:
        if common("legacy", v, ("parent", "revision", "text", "stored", "back", "exact", "statements")):
            lines_ok("legacy", v, ("revision", "stored"), True)
            if ptext(v["parent"]) is None or v["exact"] != (v["back"] == ptext(v["parent"])) or v["provenance"] != "computed by 7dee210":
                out.append("FREEZE-VECTOR: legacy %s's exactness is not its back against its parent, or it is not 7dee210's" % v["id"])
    rp = leg.get("replay") or {}
    ids.append(rp.get("id"))
    if rp.get("file") != "legacy/plaza-night.7dee210.ledger" or not all(HEX64.match(str(rp.get(k, ""))) for k in
                                                                          ("sha256", "chain head", "replayed files head", "replayed art sha256", "replayed design sha256")) \
            or not isinstance(rp.get("events"), int) or rp.get("provenance") != "computed by 7dee210":
        out.append("FREEZE-VECTOR: the legacy replay does not pin the copy, its event count and its heads in full")
    for v in (doc.get("legacy-inverses") or {}).get("vectors") or []:
        if common("legacy-inverses", v, ("parent", "parent sha256", "revision", "child", "inverse", "restores", "exact", "statements")):
            lines_ok("legacy-inverses", v, ("revision", "inverse"), True)
            if (parents.get(v["parent"]) or {}).get("sha256") != v["parent sha256"] or v["exact"] is not False or v["provenance"] != "computed by 7dee210":
                out.append("FREEZE-VECTOR: legacy-inverses %s is not keyed by its parent's sha256, or not 7dee210's inexact record" % v["id"])
    if len(set(ids)) != len(ids) or not all(isinstance(i, str) and i for i in ids):
        out.append("FREEZE-VECTOR: the vectors' ids are not each its own")
    c = doc.get("cites") or {}
    if (c.get("contract"), c.get("version"), c.get("sha256")) != ("BINDING-0", 0, v0_sha):
        out.append("FREEZE-CITES: 0254-vectors.json does not cite BINDING-0 version 0 by its sha256")
    return out, ids, hand


def children_problems(doc, D):
    """Every frozen child of revisions, cr and guards, and of each 'only' vector that applies, against the tree's own
    apply_revision(text, revision)[0] (the forward call)."""
    out, n = [], 0
    parents = doc.get("parents") or {}
    cases = [(sec, v, parents[v["parent"]]["text"]) for sec in ("revisions", "cr", "guards") for v in (doc.get(sec) or {}).get("vectors") or []]
    cases += [("only", v, v.get("text")) for v in (doc.get("only") or {}).get("vectors") or [] if v.get("expect") == "applies"]
    for sec, v, text in cases:
        try:
            child = D.apply_revision(text, v["revision"])[0]
        except Exception as e:  # noqa: BLE001 — any refusal of the forward is the finding
            out.append("FREEZE-CHILD: %s %s's forward is refused by this tree: %s: %s" % (sec, v.get("id"), type(e).__name__, str(e)[:120]))
            continue
        if child != v.get("child"):
            out.append("FREEZE-CHILD: %s %s's frozen child is not this tree's forward child" % (sec, v["id"]))
        else:
            n += 1
    return out, n


def vectors_json_problems(doc, n_forms, path=VECTORS_JSON):
    """art/director/vectors.json held to the matrix's 'vectors.json at 7dee210': cut to the intents it had then and
    written in its writer's form, its bytes are 7dee210's (every section, the top-level fields and those intents byte for
    byte); after them, nothing (commit 1) or one entry per frozen form (commit 2, where GR0 compares each).
    Returns (problems, the number of intents appended or None)."""
    pin = doc.get("vectors.json at 7dee210") or {}
    n0 = pin.get("intents before the append")
    if pin.get("file") != "art/director/vectors.json" or not HEX64.match(str(pin.get("sha256", ""))) or not isinstance(n0, int) \
            or isinstance(n0, bool) or n0 < 0 or not isinstance(pin.get("bytes"), int) or "OPEN-9" not in (pin.get("cites") or []):
        return ["FREEZE-VECTORS-JSON: the matrix does not pin art/director/vectors.json at 7dee210 (its sha256, its bytes, its intents, OPEN-9)"], None
    try:
        cur = json.loads(open(path, "rb").read().decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as e:
        return ["FREEZE-VECTORS-JSON: art/director/vectors.json cannot be read: %s" % str(e)[:120]], None
    if not isinstance(cur, dict) or not isinstance(cur.get("intents"), list) or len(cur["intents"]) < n0:
        return ["FREEZE-VECTORS-JSON: art/director/vectors.json holds fewer intents than it did at 7dee210"], None
    added = len(cur["intents"]) - n0
    cut = dict(cur, intents=cur["intents"][:n0])
    body = (json.dumps(cut, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    out = []
    if sha256(body) != pin["sha256"] or len(body) != pin["bytes"]:
        out.append("FREEZE-VECTORS-JSON: art/director/vectors.json cut to its first %d intents is not 7dee210's (its sha256 %s, pinned %s): an "
                   "existing expected output changed" % (n0, sha256(body), pin["sha256"]))
    if added not in (0, n_forms):
        out.append("FREEZE-VECTORS-JSON: art/director/vectors.json appends %d intents after 7dee210's, neither none nor the %d forms" % (added, n_forms))
    return out, added


def ruling_section(text, oid):
    """One OPEN item's section of his ruling file, by its structure: the one line beginning 'OPEN-N:', any blank lines,
    then its run of '* ' lines, ending before the first blank line after them (or at the end); None if not found once."""
    lines = text.split("\n")
    hs = [i for i, ln in enumerate(lines) if ln.startswith(oid + ":")]
    if len(hs) != 1:
        return None
    i, seen = hs[0], False
    for j in range(i + 1, len(lines)):
        if lines[j].startswith("* "):
            seen = True
        elif lines[j] == "" and seen:
            return "\n".join(lines[i:j])
        elif lines[j] != "" and not seen:
            return None
    return "\n".join(lines[i:]) if seen else None


def legacy_problems(doc, D, folder):
    """At 7dee210 (director.py 5300fb78…): the legacy sections and the revisions' 'at 7dee210' records recomputed with that
    tree's own apply_revision, and the frozen copy chained and replayed."""
    out = []
    parents = doc.get("parents") or {}
    for v in (doc.get("revisions") or {}).get("vectors") or []:
        at = v.get("at 7dee210") or {}
        child, inv = D.apply_revision(parents[v["parent"]]["text"], v["revision"])
        if at.get("inverse") != inv or at.get("exact") != (D.apply_revision(child, inv)[0] == parents[v["parent"]]["text"]):
            out.append("FREEZE-LEGACY: revisions %s's record at 7dee210 is not that tree's" % v["id"])
    for v in (doc.get("legacy") or {}).get("vectors") or []:
        child, inv = D.apply_revision(parents[v["parent"]]["text"], v["revision"])
        if (child, inv) != (v["text"], v["stored"]) or D.apply_revision(child, inv)[0] != v["back"]:
            out.append("FREEZE-LEGACY: legacy %s is not 7dee210's text, record and back" % v["id"])
    for v in (doc.get("legacy-inverses") or {}).get("vectors") or []:
        child, inv = D.apply_revision(parents[v["parent"]]["text"], v["revision"])
        if (child, inv) != (v["child"], v["inverse"]) or D.apply_revision(child, inv)[0] != v["restores"]:
            out.append("FREEZE-LEGACY: legacy-inverses %s is not 7dee210's child, record and restored text" % v["id"])
    rp = (doc.get("legacy") or {}).get("replay") or {}
    try:
        events, head = D.led.chain(os.path.join(folder, *rp["file"].split("/")))
        st = D.replay(None, events)
        got = (len(events), head, st["head"], sha256(st["art"].encode("utf-8")), sha256(st["design"].encode("utf-8")))
        want = (rp["events"], rp["chain head"], rp["replayed files head"], rp["replayed art sha256"], rp["replayed design sha256"])
        if got != want:
            out.append("FREEZE-LEGACY: the copy replays to %r, not the pinned %r" % (got, want))
    except Exception as e:  # noqa: BLE001
        out.append("FREEZE-LEGACY: the copy does not replay: %s: %s" % (type(e).__name__, str(e)[:160]))
    return out


# ------------------------------------------------------------------------------------------------ the matrix
def rulings_in_spec(spec):
    """{file: (sha256, text)} of the ruling files embedded whole in 0254-spec.md (section 13)."""
    out = {}
    for m in re.finditer(r"(?m)^~~~~(\S+)\n(.*?)^~~~~$", spec, re.S):
        out[m.group(1)] = (sha256(m.group(2).encode("utf-8")), m.group(2))
    return out


def strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from strings(v)


def matrix_problems(doc, vdoc, vector_ids, v0_sha, spec):
    out = []
    c = doc.get("cites") or {}
    if (c.get("contract"), c.get("version"), c.get("sha256")) != ("BINDING-0", 0, v0_sha):
        out.append("FREEZE-CITES: 0254-matrix.json does not cite BINDING-0 version 0 by its sha256")
    embedded = rulings_in_spec(spec)
    cited = {}
    for d, name in ((doc, "0254-matrix.json"), (vdoc, "0254-vectors.json")):
        for r in ((d.get("cites") or {}).get("rulings") or []):
            cited[r.get("file")] = r.get("sha256")
            if not r.get("file") or embedded.get(r.get("file"), ("",))[0] != r.get("sha256"):
                out.append("FREEZE-CITES: %s cites %s by a sha256 that is not the file embedded in 0254-spec.md" % (name, r.get("file")))
    if not cited:
        out.append("FREEZE-CITES: no ruling file is cited")
    suites = doc.get("suites") or []
    order, rows_n, named = {}, 0, set()
    for s in suites:
        if s.get("switch") != SUITE_SWITCH.get(s.get("suite")):
            out.append("FREEZE-PLANT: %s's switch %r is not the one spec section 8 names for it" % (s.get("suite"), s.get("switch")))
        rid = [r.get("id") for r in s.get("rows") or []]
        if not rid or len(set(rid)) != len(rid):
            out.append("FREEZE-MATRIX: %s's rows are not each an id of its own" % s.get("suite"))
        order[s.get("suite")] = rid
        rows_n += len(rid)
        for r in s.get("rows") or []:
            named.update(r.get("vectors") or [])
            for vid in r.get("vectors") or []:
                if vid not in vector_ids:
                    out.append("FREEZE-MATRIX: %s %s names a vector %r the freeze does not hold" % (s.get("suite"), r.get("id"), vid))
            printed = r.get("printed")
            if not isinstance(printed, list) or (not printed and not r.get("printed by reference")):
                out.append("FREEZE-MATRIX: %s %s prints no name" % (s.get("suite"), r.get("id")))
                continue
            for n in printed:
                kept = r.get("kept byte for byte from 7dee210") or (r.get("id") == "DS1")
                if not isinstance(n, str) or not n or n != n.strip() or "\n" in n or (" — " in n and not kept):
                    out.append("FREEZE-MATRIX: %s %s's name %r is empty, not stripped, or cut by R5 at ' — '" % (s.get("suite"), r.get("id"), n))
    for vid in vector_ids:
        if vid not in named:
            out.append("FREEZE-VECTOR: %s is named by no matrix row" % vid)
    plants = doc.get("plants") or []
    plant_names = {}
    for p in plants:
        su, rows = p.get("suite"), order.get(p.get("suite"), [])
        if su not in order or p.get("caught_by") not in rows or not p.get("switch") or p.get("switch") != SUITE_SWITCH.get(su) \
                or p.get("value") != p.get("id") or not p.get("what"):
            out.append("FREEZE-PLANT: %s is not one named value of a switch caught by a row of its suite" % p.get("id"))
            continue
        at = rows.index(p["caught_by"])
        if not all(x in rows and rows.index(x) > at for x in p.get("fails_later") or []):
            out.append("FREEZE-PLANT: %s's later failures are not rows of %s after %s" % (p["id"], su, p["caught_by"]))
        if su in SUITE_PLANT and not SUITE_PLANT[su].match(p.get("printed") or "") or " — " in (p.get("printed") or "-"):
            out.append("FREEZE-PLANT: %s's row name %r is not one R5 counts as its suite prints it" % (p["id"], p.get("printed")))
        plant_names.setdefault(su, []).append(p.get("printed"))
    for s in suites:
        for r in s.get("rows") or []:
            for n in r.get("printed") or []:
                if re.search(r"\bplant\b", n or "") and n not in plant_names.get(s.get("suite"), []) and r.get("id") != "DS1":
                    out.append("FREEZE-MATRIX: %s %s's row %r is no plant row and names a plant" % (s.get("suite"), r.get("id"), n))
    new_r5 = [p for p in plants if p.get("new in 0254") and p.get("suite") in SUITE_PLANT]
    pr = doc.get("plant rows") or {}
    prefix = {s.get("suite"): s.get("R5 key prefix", "") for s in suites}
    keys = [prefix[p["suite"]] + p["printed"] for p in new_r5]
    if pr.get("k") != len(new_r5) or pr.get("names") != [p["printed"] for p in new_r5] or pr.get("R5 keys") != keys or len(set(keys)) != len(keys):
        out.append("FREEZE-MATRIX: the plant rows listed are not the matrix's new R5 plants, in its order, k their number, each key its own")
    if (doc.get("R5 census on 7dee210") or {}).get("this matrix's new plant keys among them") != 0:
        out.append("FREEZE-MATRIX: a new plant key is a key R5 reads on 7dee210")
    # OPEN: every id cited by a row, a plant or a vector is resolved, with his words in a ruling file embedded and cited
    resolved = {x.get("id"): x for x in doc.get("resolved") or []}
    opens = [x.get("id") for x in doc.get("open") or []]
    for oid, x in resolved.items():
        f = x.get("ruling file")
        text = embedded.get(f, ("", ""))[1]
        if not isinstance(x.get("his words"), str) or not x["his words"] or x["his words"] != ruling_section(text, oid) \
                or cited.get(f) != x.get("ruling sha256") or embedded.get(f, ("",))[0] != x.get("ruling sha256"):
            out.append("FREEZE-OPEN: %s is resolved without his words, its own item's section as it stands in a cited ruling file" % oid)
    for x in doc.get("open") or []:
        if not x.get("what") or not x.get("why"):
            out.append("FREEZE-OPEN: %s is open without saying what and why" % x.get("id"))
    if len(set(list(resolved) + opens)) != len(resolved) + len(opens):
        out.append("FREEZE-OPEN: an item is both resolved and open, or listed twice")
    citers = [("row", s.get("suite") + " " + str(r.get("id")), r) for s in suites for r in s.get("rows") or []] + \
             [("plant", str(p.get("id")), p) for p in plants] + \
             [("vector", str(v.get("id")), v) for sec in ("forms", "revisions", "cr", "guards", "only", "legacy-inverses")
              for v in (vdoc.get(sec) or {}).get("vectors") or []] + [("vector", str(v.get("id")), v) for v in (vdoc.get("legacy") or {}).get("vectors") or []]
    for kind, name, x in citers:
        for oid in set(OPEN_ID.findall(" ".join(strings(x)))) | set(x.get("cites") or []):
            if oid not in resolved:
                out.append("FREEZE-OPEN: %s %s cites %s, which is not resolved with his words%s" % (kind, name, oid, " (it is open)" if oid in opens else ""))
    return out, rows_n, len(suites), len(plants), len(new_r5), opens


# ------------------------------------------------------------------------------------------------ check
def load_director():
    path = os.path.join(ART, "director.py")
    raw = open(path, "rb").read()
    mod = sys.modules.get("director")
    if mod is None or os.path.abspath(getattr(mod, "__file__", "")) != os.path.abspath(path):
        sys.path.insert(0, ART)
        spec = importlib.util.spec_from_file_location("director", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["director"] = mod
        spec.loader.exec_module(mod)
    return mod, sha256(raw)


def check(folder=FOLDER):
    matrix, vectors, copy, problems = frozen(folder)
    info = {"vectors": 0, "hand": 0, "rows": 0, "suites": 0, "plants": 0, "k": 0, "open": [], "children": 0, "director": "", "legacy": ""}
    seen, _reg = binding.check(binding.FOLDER)
    v0_sha = seen[0]["sha256"] if seen else ""
    info["v0"] = v0_sha
    lines, _p = _record(folder, v0_sha) if v0_sha else ({}, [])
    info["lines"] = {f: x[1] for f, x in lines.items()}
    if vectors is None or matrix is None or copy is None:
        return problems, info
    try:
        spec = open(os.path.join(folder, "0254-spec.md"), "rb").read().decode("utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return problems + ["FREEZE-SPEC: 0254-spec.md cannot be read: %s" % e], info
    p, vids, info["hand"] = vectors_problems(vectors, v0_sha)
    problems += p
    info["vectors"] = len(vids)
    p, info["rows"], info["suites"], info["plants"], info["k"], info["open"] = matrix_problems(matrix, vectors, set(vids), v0_sha, spec)
    problems += p
    D, dsha = load_director()
    info["director"] = dsha
    p, info["children"] = children_problems(vectors, D)
    problems += p
    p, added = vectors_json_problems(matrix, len((vectors.get("forms") or {}).get("vectors") or []))
    problems += p
    if added is not None:
        info["vectors.json"] = "art/director/vectors.json cut to its intents at 7dee210 is 7dee210's byte for byte: %s; %d intents appended after them" % (
            "NOT equal" if any("is not 7dee210's" in x for x in p) else "equal", added)
    if dsha == DIRECTOR_7DEE210:
        p = legacy_problems(vectors, D, folder)
        problems += p
        info["legacy"] = "the legacy sections, the revisions' records at 7dee210 and the copy's replay recomputed by director.py %s's own code: %s" % (
            dsha[:8] + "…", "equal" if not p else "NOT equal")
    else:
        info["legacy"] = "legacy recomputation not reached (director.py is not 5300fb78…)"
    return problems, info


def main(argv):
    if argv[:1] == ["check"]:
        problems, info = check(argv[1] if len(argv) > 1 else FOLDER)
        for p in problems:
            print(p)
        for f, h in sorted(info.get("lines", {}).items()):
            print("%s sha256 %s" % (f, h))
        if info.get("legacy"):
            print(info["legacy"])
        if info.get("vectors.json"):
            print(info["vectors.json"])
        opens = info.get("open") or []
        print("INVERSE-0254 FREEZE %s: %d vectors (%d by hand), %d matrix rows in %d suites, %d plants (%d new keys for R5), against BINDING-0 "
              "version 0 sha256 %s; children equal to director.py %s's: %d; nothing open%s" % (
                  "READ" if problems else "FROZEN", info["vectors"], info["hand"], info["rows"], info["suites"], info["plants"], info["k"],
                  info.get("v0", ""), info.get("director", ""), info["children"],
                  (" that a row or a vector decides (open, deciding nothing: %s)" % ", ".join(opens)) if opens else ""))
        return 0 if not problems else 1
    print("usage: python art/director/inverse_freeze.py check [FOLDER]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
