# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/director/binding.py — BINDING-0 (0252): the binding contract's register, read and checked. Nothing here enforces
# the contract: its enforcement is 0253's, and until then no admission reads it.
#
#   python art/director/binding.py check      BINDING-0 REGISTERED version 0 sha256 … (exit 0), or each problem (exit 1)
#
# The owner's ruling (2026-10-18), registered before the code that enforces it: an admission that relies on a still, a
# preview or an undo account bound to another scene than the exact candidate being admitted is refused, and an unknown
# binding with it. The contract that makes his ruling exact is a file per version under art/director/bindings/
# (BINDING-0.v0.json: the identities, the comparison rule, the outcomes, the order, the five cases in his words with
# their expected results, the decision record, what is deferred); register.jsonl names each registered version's file
# and its sha256, one line each, appended and never rewritten.
#
# check() holds the files to the register: every registered file present, in its one canonical form, its sha256 its
# line's; every line well formed, a (contract, version) registered once and a file once, each contract's versions from 0
# without a gap; no contract file in the folder that no line registers; and in every registered contract his five cases
# first (B1 to B5, each with his words), any later case with an id of its own, every case with an explicit expected
# result, and the closed outcomes MATCH, MISMATCH and UNKNOWN. What files
# alone cannot show: a line rewritten together with its file (history shows that, and the classifier's pushed tree).
# Standard library only.

import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.join(HERE, "bindings")
REGISTER = "register.jsonl"
LINE_KEYS = ("contract", "file", "patch", "registered", "sha256", "version")
CASE_IDS = ("B1", "B2", "B3", "B4", "B5")
OUTCOMES = ("MATCH", "MISMATCH", "UNKNOWN")
CONTRACT_FILE = re.compile(r"\A([A-Z][A-Z0-9-]*)\.v(0|[1-9][0-9]*)\.json\Z")


def canonical(doc):
    """A contract's one byte form: sorted keys, one space of indent, UTF-8, a closing newline."""
    return (json.dumps(doc, sort_keys=True, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def register_line(rec):
    """A register line's one form: sorted keys, no spaces, ASCII."""
    return json.dumps(rec, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def contract_problems(doc, name):
    """What a contract lacks of what every BINDING contract must hold: his five cases first, in order, each with his
    words; any case after them with an id of its own; every case with an explicit expected result; the closed outcomes."""
    out = []
    cases = doc.get("cases") if isinstance(doc, dict) else None
    ids = [c.get("id") for c in cases] if isinstance(cases, list) and all(isinstance(c, dict) for c in cases) else None
    later = ids[len(CASE_IDS):] if ids else []
    if (ids is None or ids[:len(CASE_IDS)] != list(CASE_IDS) or not all(isinstance(i, str) and i for i in later)
            or len(set(later)) != len(later) or set(later) & set(CASE_IDS)):
        out.append("BINDING-CASES: %s's cases are %s, not %s first, then cases of ids of their own" % (name, ids, ", ".join(CASE_IDS)))
    else:
        for c in cases:
            words, exp = c.get("his words"), c.get("expected")
            if c["id"] in CASE_IDS and (not isinstance(words, str) or not words.strip()):
                out.append("BINDING-CASES: %s's case %s has no words of his" % (name, c["id"]))
            if not isinstance(exp, dict) or not exp or not all(isinstance(v, str) and v.strip() for v in exp.values()):
                out.append("BINDING-CASES: %s's case %s has no explicit expected result" % (name, c["id"]))
    outcomes = ((doc.get("comparison") or {}).get("outcomes") if isinstance(doc, dict) else None) or {}
    if sorted(outcomes) != sorted(OUTCOMES):
        out.append("BINDING-OUTCOMES: %s's outcomes are %s, not %s" % (name, sorted(outcomes), ", ".join(OUTCOMES)))
    return out


def check(folder=FOLDER):
    """(the registered versions, each {contract, version, file, sha256}, in the register's order; the problems, empty when
    every registered contract is registered as it stands)."""
    problems, seen = [], []
    try:
        with open(os.path.join(folder, REGISTER), "rb") as fh:
            raw = fh.read()
    except OSError as e:
        return [], ["BINDING-REGISTER: the register cannot be read: %s" % e]
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError:
        return [], ["BINDING-REGISTER: the register is not ASCII"]
    if not text.endswith("\n") or "\r" in text:
        problems.append("BINDING-REGISTER: the register's lines are not LF-ended")
    keys, files, versions = set(), set(), {}
    for n, ln in enumerate(text.split("\n")[:-1] if text.endswith("\n") else text.split("\n"), 1):
        try:
            rec = json.loads(ln)
        except ValueError:
            problems.append("BINDING-REGISTER: line %d is not JSON" % n)
            continue
        if not isinstance(rec, dict) or tuple(sorted(rec)) != LINE_KEYS or register_line(rec) != ln:
            problems.append("BINDING-REGISTER: line %d is not a register line in its one form (%s)" % (n, ", ".join(LINE_KEYS)))
            continue
        c, v, f, h = rec["contract"], rec["version"], rec["file"], rec["sha256"]
        m = CONTRACT_FILE.match(f) if isinstance(f, str) else None
        if (not isinstance(v, int) or isinstance(v, bool) or not m or m.group(1) != c or int(m.group(2)) != v
                or not re.fullmatch(r"[0-9a-f]{64}", h or "") or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", rec["registered"] or "")
                or not re.fullmatch(r"\d{4}", rec["patch"] or "")):
            problems.append("BINDING-REGISTER: line %d's fields are not well formed" % n)
            continue
        if (c, v) in keys or f in files:
            problems.append("BINDING-TWICE: line %d registers %s version %d (%s) again" % (n, c, v, f))
            continue
        keys.add((c, v))
        files.add(f)
        versions.setdefault(c, []).append(v)
        try:
            with open(os.path.join(folder, f), "rb") as fh:
                body = fh.read()
        except OSError:
            problems.append("BINDING-ABSENT: %s, registered on line %d, is not there" % (f, n))
            continue
        if sha256(body) != h:
            problems.append("BINDING-STALE: %s is not the contract registered on line %d (its sha256 %s, registered %s)" % (f, n, sha256(body)[:16], h[:16]))
            continue
        try:
            doc = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            problems.append("BINDING-UNREADABLE: %s is not JSON" % f)
            continue
        if canonical(doc) != body:
            problems.append("BINDING-NOT-CANONICAL: %s is not in its one byte form" % f)
        if not isinstance(doc, dict) or doc.get("contract") != c or doc.get("version") != v:
            problems.append("BINDING-REGISTER: %s names itself %s version %s, its line %s version %d" % (
                f, doc.get("contract") if isinstance(doc, dict) else "?", doc.get("version") if isinstance(doc, dict) else "?", c, v))
        problems += contract_problems(doc, f)
        seen.append({"contract": c, "version": v, "file": f, "sha256": h})
    for c, vs in versions.items():
        if vs != list(range(len(vs))):
            problems.append("BINDING-REGISTER: %s's versions are %s, not 0 to %d in order" % (c, vs, len(vs) - 1))
    for f in sorted(os.listdir(folder)):
        if CONTRACT_FILE.match(f) and f not in files:
            problems.append("BINDING-UNREGISTERED: %s is in the folder and no line registers it" % f)
    if not seen and not problems:
        problems.append("BINDING-REGISTER: nothing is registered")
    return seen, problems


def main(argv):
    if argv[:1] == ["check"]:
        seen, problems = check(argv[1] if len(argv) > 1 else FOLDER)
        for p in problems:
            print(p)
        for s in seen:
            print("%s %s version %d sha256 %s (%s)" % (s["contract"], "REGISTERED" if not problems else "READ", s["version"], s["sha256"], s["file"]))
        return 0 if not problems else 1
    print("usage: python art/director/binding.py check [FOLDER]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
