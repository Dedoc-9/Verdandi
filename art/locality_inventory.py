# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/locality_inventory.py — LOCALITY-1's frozen inputs: the rule that makes its inventory of 2,418 perturbations from
# the fixtures' text alone, and the checks that hold every frozen input to its bytes. It comes before the harness that
# measures with them (art/locality.py), so that the inventory and its rule precede any result. LOCALITY-1 was admitted
# under the working name LOCALITY-0, which is the registered floor-tile court's: the frozen inputs keep that name in
# their bytes, and there it means LOCALITY-1 (SHEET-v3.md).
#
#   python art/locality_inventory.py     FROZEN.sha256 and what it names, the six fixtures and FIXTURES.sha256, and the
#                                        inventory made again from the fixtures, equal to INVENTORY.jsonl byte for byte
#
# It exports nothing, converts no map and computes no scene: it parses the briefs with art/dress.py's parser, whose
# statement keys and hashes are the exporter's, and nothing more. The rule was first run, before any result, as a
# scratch generator over git at BASE (make_inventory.py, recorded by its sha256 in the batch sheet, SHEET.md); this is
# the same rule over the fixtures, its byte copies, and it makes the same bytes. Standard library only; writes nothing.

import hashlib
import json
import os
import sys
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import dress  # noqa: E402  (the parser and the number grammar only; nothing is exported)

FIX = os.path.join(HERE, "fixtures", "locality")
SPEC_SHA256 = "a4424d7e2d503c49837437ebdea4fc67dee275e126ee94123763039556da7a31"
INVENTORY_SHA256 = "455af6c829f85f76b491a8bd1774b7f22b24eb306d65621e19353e7c3aadd45d"
FIXTURES_SHA256 = "cf61fcd30e2013c87b0015e1d557cce63323bf0edeaea291ab95154115863214"
FROZEN_SHA256 = "7f70115501564f0f127dd13e1debd1eb2d5b922f1ef76abc68a17162e4782d45"   # FROZEN.sha256: the sha256 of FIXTURES.sha256, INVENTORY.jsonl, SHEET.md and SPEC.md


class Refusal(Exception):
    """LOCALITY-INVENTORY, LOCALITY-FIXTURE, LOCALITY-HASHSEED: the run refused before anything is exported."""
    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code, self.detail = code, detail


def sha256(b):
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------------------------------------ the inventory
# SPEC.md §2, as make_inventory.py made it before the run (from git at BASE; here from the fixtures, its byte copies).
BASE = "de91aaf07f109bb688668a18fe4bc32fa7e650a8"
BRIEFS = ("foundry-yard", "harbor-day", "harbor-lift", "plaza-night")
MAPS = ("tactical.gbx", "tactical.layout")
SEEDS = tuple("locality-%d" % k for k in range(1, 8))
INV_FORMAT = "VERDANDI-LOCALITY-INVENTORY 0"
CLASSES = ("NOOP", "DEL", "NUM+", "NUM-", "SHIFT+x", "SHIFT-x", "SHIFT+z", "SHIFT-z", "MAT", "SEED")
EXCLUDED = {"map": "selects the world (W and C); LOCALITY-0 measures the dressing of one world"}   # frozen bytes: the working name (SHEET-v3.md)
TEXT = ("title", "seed", "asset", "time")       # their values are words: deleted, never edited token by token
MATPOS = {"skyline": (0,), "tower": (1,), "canopy": (1,), "neon": (1,), "puddle": (1,), "building": (1,),
          "mover": (1,), "surface": (1,), "bay": (2,)}
OPTIONS = {"canopy": {"deep": "SIZE", "ribs": "LATTICE", "lit": "APPEARANCE", "edgelit": "APPEARANCE"},
           "building": {"face": None, "storey": "SIZE", "bay": "LATTICE"},
           "mover": {"along": None, "travel": "SIZE", "speed": "MOTION", "policy": None}}
ROLE = {"sun": {0: "APPEARANCE", 1: "APPEARANCE", 2: "APPEARANCE", 3: "APPEARANCE"},
        "fog": {0: "APPEARANCE", 1: "APPEARANCE"},
        "exposure": {0: "APPEARANCE"}, "bloom": {0: "APPEARANCE"}, "rain": {0: "APPEARANCE"},
        "region": {1: "POSITION", 2: "POSITION"},
        "material": {1: "APPEARANCE", 2: "APPEARANCE", 3: "APPEARANCE", 5: "APPEARANCE", 6: "APPEARANCE"},
        "view": {1: "POSITION", 2: "VIEW", 3: "VIEW"},
        "skyline": {1: "SIZE", 2: "SIZE"},
        "tower": {2: "SIZE", 3: "SIZE"},
        "canopy": {2: "SIZE", 3: "POSITION", 4: "POSITION"},
        "neon": {2: "SIZE", 3: "LATTICE"},
        "lamp": {1: "APPEARANCE", 2: "APPEARANCE", 3: "LATTICE"},
        "puddle": {2: "LATTICE"},
        "building": {2: "SIZE", 3: "POSITION", 4: "POSITION"},
        "mover": {2: "POSITION", 3: "POSITION"}}
ROLE["moon"] = ROLE["sun"]


def numeric(tok):
    """The token's parts if it is a number or comma-joined numbers (a cell, a colour, a corner), else None."""
    parts = tok.split(",")
    return parts if all(dress.NUMBER.fullmatch(p) for p in parts) else None


def step(p, sign):
    """One unit of the last decimal place the number is written to, added or taken away, written to that place."""
    d = len(p.split(".")[1]) if "." in p else 0
    return str(Decimal(p) + sign * Decimal(1).scaleb(-d))


def role(verb, args, i):
    opts = OPTIONS.get(verb, {})
    for j in range(i, -1, -1):
        if args[j] in opts and j < i:
            r = opts[args[j]]
            if r is None:
                raise Refusal("LOCALITY-INVENTORY", "a number after the option %r of %s, which takes none" % (args[j], verb))
            return r
    r = ROLE.get(verb, {}).get(i)
    if r is None:
        raise Refusal("LOCALITY-INVENTORY", "no role for %s's argument %d (%r): the role table is not total" % (verb, i, args[i]))
    return r


def statements(text):
    """[(line, verb, args)] of the brief's statements, the format line excepted."""
    out = []
    for n, ln in enumerate(text.split("\n"), start=1):
        code = ln.split("#", 1)[0].split()
        if code:
            out.append((n, code[0], code[1:]))
    return out[1:]


def edits(verb, args, materials):
    """(class, token, part, role, new args) for one statement, in a fixed order."""
    out = []
    if verb in EXCLUDED:
        return out
    out.append(("DEL", -1, -1, "", None))
    if verb in TEXT:
        return out
    for i, t in enumerate(args):
        parts = numeric(t)
        if parts is None:
            continue
        r = role(verb, args, i)
        for k in range(len(parts)):
            for cls, sign in (("NUM+", 1), ("NUM-", -1)):
                q = list(parts)
                q[k] = step(parts[k], sign)
                a = list(args)
                a[i] = ",".join(q)
                out.append((cls, i, k, r, a))
    cells = [i for i, t in enumerate(args) if dress.is_cell(t)]
    if verb == "mover":
        corners = [i for i in (2, 3) if i < len(args) and numeric(args[i]) and len(args[i].split(",")) == 3]
        for cls, k, d in (("SHIFT+x", 0, 1), ("SHIFT-x", 0, -1), ("SHIFT+z", 2, 1), ("SHIFT-z", 2, -1)):
            a = list(args)
            for i in corners:
                q = a[i].split(",")
                q[k] = str(Decimal(q[k]) + d)
                a[i] = ",".join(q)
            out.append((cls, -1, -1, "POSITION", a))
    elif len(cells) >= 2:
        for cls, dx, dz in (("SHIFT+x", 1, 0), ("SHIFT-x", -1, 0), ("SHIFT+z", 0, 1), ("SHIFT-z", 0, -1)):
            a = list(args)
            for i in cells:
                x, z = (int(v) for v in a[i].split(","))
                a[i] = "%d,%d" % (x + dx, z + dz)
            out.append((cls, -1, -1, "POSITION", a))
    names = sorted(materials)
    pos = list(MATPOS.get(verb, ()))
    if verb == "building" and "face" in args:
        pos.append(args.index("face") + 2)
    for i in pos:
        if i < len(args) and args[i] in materials and len(names) > 1:
            a = list(args)
            a[i] = names[(names.index(args[i]) + 1) % len(names)]
            out.append(("MAT", i, -1, "", a))
    return out


def noop_lines(text):
    lines = text.split("\n")
    for line, verb, args in statements(text):
        lines[line - 1] = "  ".join([verb] + args) + "  # locality-0 no-op"   # hashed into the frozen inventory; kept
    return lines


def fixture(rel):
    return open(os.path.join(FIX, rel), "rb").read()


def check_fixtures():
    """H2: FIXTURES.sha256 is the frozen one, every fixture is the bytes it names, and SPEC.md is the frozen spec."""
    man = fixture("FIXTURES.sha256")
    if sha256(man) != FIXTURES_SHA256:
        raise Refusal("LOCALITY-FIXTURE", "FIXTURES.sha256 is %s, not the frozen %s" % (sha256(man)[:12], FIXTURES_SHA256[:12]))
    want = ["briefs/%s.art" % b for b in BRIEFS] + ["maps/%s" % m for m in MAPS]
    lines = man.decode("ascii").splitlines()
    if [ln.split(" ", 1)[1] for ln in lines] != want:
        raise Refusal("LOCALITY-FIXTURE", "FIXTURES.sha256 does not name the six fixtures in order")
    for ln in lines:
        h, rel = ln.split(" ", 1)
        if sha256(fixture(rel)) != h:
            raise Refusal("LOCALITY-FIXTURE", "%s is not the bytes FIXTURES.sha256 names" % rel)
    spec = fixture("SPEC.md")
    if sha256(spec) != SPEC_SHA256:
        raise Refusal("LOCALITY-FIXTURE", "SPEC.md is not the frozen spec %s" % SPEC_SHA256[:12])
    # the frozen spec states the inventory's, the manifest's and every fixture's sha256: the constants here are held to
    # its text, so that an edit of the rule, the constants and the files together cannot pass while the spec says otherwise
    stated = spec.decode("utf-8")
    for h in [INVENTORY_SHA256, FIXTURES_SHA256] + [ln.split(" ", 1)[0] for ln in lines]:
        if h not in stated:
            raise Refusal("LOCALITY-FIXTURE", "SPEC.md does not state the sha256 %s" % h[:12])
    return "6 fixtures and SPEC.md (%s) are the frozen bytes; the spec states every sha256 held here" % SPEC_SHA256[:12]


def inventory():
    """The inventory's bytes, made from the fixtures' text alone (SPEC.md §2): nothing is exported."""
    man = fixture("FIXTURES.sha256")
    rows, n = [], 0
    for name in BRIEFS:
        raw = fixture("briefs/%s.art" % name)
        if b"\r" in raw:
            raise Refusal("LOCALITY-FIXTURE", "%s.art holds a CR" % name)
        text = raw.decode("utf-8")
        A = dress.parse(text, name + ".art")
        keys = {s["line"]: s for s in A["statements"]}
        lines = text.split("\n")
        found = []

        def entry(cls, line, verb, tok, part, rl, new_lines, before, after):
            body = "\n".join(new_lines).encode("utf-8")
            st = keys.get(line)
            found.append({"n": None, "brief": name, "class": cls, "line": line, "verb": verb,
                          "key": st["key"] if st else "", "hash": st["hash"] if st else "",
                          "token": tok, "part": part, "role": rl, "before": before, "after": after,
                          "brief_sha256": sha256(body)})

        entry("NOOP", 0, "", -1, -1, "", noop_lines(text), "", "")
        stmts = statements(text)
        for line, verb, args in stmts:
            before = " ".join([verb] + args)
            if keys[line]["text"] != before:
                raise Refusal("LOCALITY-INVENTORY", "%s line %d: the parser reads another text" % (name, line))
            for cls, tok, part, rl, a in edits(verb, args, A["materials"]):
                new = list(lines)
                after = "" if a is None else " ".join([verb] + a)
                new[line - 1] = after
                entry(cls, line, verb, tok, part, rl, new, before, after)
        seed_line = [line for line, verb, _a in stmts if verb == "seed"]
        if len(seed_line) != 1:
            raise Refusal("LOCALITY-INVENTORY", "%s has %d seed statements, not one" % (name, len(seed_line)))
        for s in SEEDS:
            new = list(lines)
            new[seed_line[0] - 1] = "seed " + s
            entry("SEED", seed_line[0], "seed", -1, -1, "", new, keys[seed_line[0]]["text"], "seed " + s)
        seen = {}
        for e in found:
            if e["brief_sha256"] in seen:
                raise Refusal("LOCALITY-INVENTORY", "two entries make one brief")
            seen[e["brief_sha256"]] = e
        if sha256(raw) in seen:
            raise Refusal("LOCALITY-INVENTORY", "an entry makes the fixture itself")
        order = {c: i for i, c in enumerate(CLASSES)}
        found.sort(key=lambda e: (e["line"], order[e["class"]], e["token"], e["part"], e["after"]))
        for e in found:
            e["n"] = n
            n += 1
        rows += found
    head = {"format": INV_FORMAT, "base": BASE, "briefs": list(BRIEFS), "maps": list(MAPS), "seeds": list(SEEDS),
            "classes": list(CLASSES), "excluded": EXCLUDED, "fixtures_sha256": sha256(man), "entries": len(rows)}
    body = json.dumps(head, sort_keys=True, ensure_ascii=True) + "\n" + \
        "".join(json.dumps(r, sort_keys=True, ensure_ascii=True) + "\n" for r in rows)
    return body.encode("ascii")


def check_inventory():
    """H1: the inventory made again equals INVENTORY.jsonl byte for byte, and that is the frozen one."""
    made, kept = inventory(), fixture("INVENTORY.jsonl")
    if sha256(kept) != INVENTORY_SHA256:
        raise Refusal("LOCALITY-INVENTORY", "INVENTORY.jsonl is %s, not the frozen %s" % (sha256(kept)[:12], INVENTORY_SHA256[:12]))
    if made != kept:
        raise Refusal("LOCALITY-INVENTORY", "the inventory made from the fixtures (%s) is not INVENTORY.jsonl" % sha256(made)[:12])
    lines = kept.decode("ascii").splitlines()
    return json.loads(lines[0]), [json.loads(x) for x in lines[1:]]


def brief_bytes(e, text):
    """The entry's brief, made again from the fixture and the entry; held to the sha256 the inventory recorded."""
    lines = noop_lines(text) if e["class"] == "NOOP" else text.split("\n")
    if e["class"] != "NOOP":
        lines[e["line"] - 1] = e["after"]
    b = "\n".join(lines).encode("utf-8")
    if sha256(b) != e["brief_sha256"]:
        raise Refusal("LOCALITY-INVENTORY", "entry %d does not make the brief the inventory recorded" % e["n"])
    return b


def check_frozen():
    """FROZEN.sha256 is the frozen one, and every file it names is the bytes it names: the batch sheet, the spec, the
    inventory and the fixtures' manifest."""
    man = fixture("FROZEN.sha256")
    if sha256(man) != FROZEN_SHA256:
        raise Refusal("LOCALITY-FIXTURE", "FROZEN.sha256 is %s, not the frozen %s" % (sha256(man)[:12], FROZEN_SHA256[:12]))
    lines = man.decode("ascii").splitlines()
    if [ln.split(" ", 1)[1] for ln in lines] != ["FIXTURES.sha256", "INVENTORY.jsonl", "SHEET.md", "SPEC.md"]:
        raise Refusal("LOCALITY-FIXTURE", "FROZEN.sha256 does not name the four frozen inputs in order")
    for ln in lines:
        h, rel = ln.split(" ", 1)
        if sha256(fixture(rel)) != h:
            raise Refusal("LOCALITY-FIXTURE", "%s is not the bytes FROZEN.sha256 names" % rel)
    return "SHEET.md, SPEC.md, INVENTORY.jsonl and FIXTURES.sha256 are the bytes FROZEN.sha256 (%s) names" % FROZEN_SHA256[:12]


def main():
    try:
        said = [check_fixtures()]
        head, entries = check_inventory()
        said.append(check_frozen())
        texts = {b: fixture("briefs/%s.art" % b).decode("utf-8") for b in BRIEFS}
        for e in entries:
            brief_bytes(e, texts[e["brief"]])
    except Refusal as e:
        print("LOCALITY REFUSED %s" % e)
        return 2
    for s in said:
        print(s)
    print("every entry makes again the brief whose sha256 it records")
    print("LOCALITY INVENTORY HELD: %d entries, sha256 %s" % (len(entries), INVENTORY_SHA256))
    return 0


if __name__ == "__main__":
    sys.exit(main())
