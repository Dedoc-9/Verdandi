# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/director/vectors_source.py — the inputs of DIRECTOR-0's conformance vectors, and the writer of vectors.json.
#
#   python art/director/vectors_source.py --write     (re)writes art/director/vectors.json from these inputs
#
# vectors.json is the contract a second implementation is held to: inputs and the exact expected outputs (canonical
# bytes in hex, verdicts as objects and as canonical bytes). The expected outputs were written by the Python reference
# and read through by hand; once published they are the protocol. Changing an expected output is a change of the
# protocol's version, not a fix. `python art/director.py vectors` checks that the reference still reproduces them.

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import intent as canon  # noqa: E402
import scope  # noqa: E402

H0 = {"art_sha256": "a" * 64, "world_sha256": "b" * 64, "exporter_sha256": "c" * 64}
H1 = {"art_sha256": "d" * 64, "world_sha256": "b" * 64, "exporter_sha256": "c" * 64}


def mat(base, rough, metal=0.0, emis=(0, 0, 0), strength=0.0, parent=None):
    m = {"base": list(base), "roughness": rough, "metallic": metal, "emissive": list(emis), "emissive_strength": strength}
    if parent:
        m["parent"] = parent
    return m


def scene(**over):
    """A 6 x 4 world: a rock rim, a 4 x 2 floor, one cover cell; a region 'yard' over the floor, 'gate' at its east."""
    tops = [4.0] * 24
    for z in (1, 2):
        for x in (1, 2, 3, 4):
            tops[z * 6 + x] = 0.0
    tops[2 * 6 + 2] = 1.0
    s = {
        "title": "vector world",
        "grid": {"w": 6, "h": 4, "cell": 2.0, "wall": 4.0},
        "tops": tops,
        "spawns": {"A": {"x": 3.0, "z": 3.0, "y": 0.0, "yaw": 90.0}},
        "regions": {"yard": [1, 1, 3, 2], "gate": [4, 1, 4, 2]},
        "collision": [
            {"id": "ground", "kind": "ground", "material": "floor", "cells": [0, 0, 5, 3], "box": [0.0, -0.5, 0.0, 12.0, 0.0, 8.0]},
            {"id": "c:0,0-5,0", "kind": "wall", "material": "stone", "cells": [0, 0, 5, 0], "box": [0.0, 0.0, 0.0, 12.0, 4.0, 2.0]},
            {"id": "c:2,2-2,2", "kind": "cover", "material": "stone", "cells": [2, 2, 2, 2], "box": [4.0, 0.0, 4.0, 6.0, 1.0, 6.0]},
        ],
        "visuals": [
            {"id": "tower:0,1", "by": "s1", "region": "yard", "asset": "cube", "material": "stone", "box": [0.0, 4.0, 2.0, 2.0, 12.0, 4.0]},
            {"id": "tower:5,1", "by": "s2", "region": "gate", "asset": "cube", "material": "stone", "box": [10.0, 4.0, 2.0, 12.0, 9.0, 4.0]},
            {"id": "neon:1,1:n", "by": "s3", "region": "yard", "asset": "cube", "material": "glow", "box": [2.3, 3.0, 2.0, 3.7, 3.12, 2.05]},
            {"id": "skyline:0,2", "by": "s4", "region": "*", "asset": "cube", "material": "stone", "box": [0.0, 4.0, 4.0, 4.0, 20.0, 8.0]},
        ],
        "lights": [
            {"id": "neon:1,1:n", "by": "s3", "region": "yard", "type": "rect", "pos": [3.0, 3.06, 2.13], "dir": [0, 0, 1],
             "color": [255, 40, 190], "candela": 45.0, "width": 1.4, "height": 0.12, "radius": 8.0},
        ],
        "materials": {"stone": mat((112, 110, 104), 0.86), "floor": mat((46, 47, 50), 0.16),
                      "glow": mat((255, 40, 190), 0.4, 0.0, (255, 40, 190), 45.0)},
        "environment": {"time": "night", "fog": {"density": 0.045, "color": [38, 54, 74], "volumetric": True}, "exposure": 1.5},
        "views": {"yard": {"x": 3.0, "y": 1.62, "z": 3.0, "yaw": 90.0, "pitch": 0.0}},
        "assets": {"cube": {"path": "/Engine/BasicShapes/Cube.Cube", "source": "engine", "licence": "Unreal Engine EULA"}},
    }
    s.update(over)
    return s


def clone(s):
    return json.loads(json.dumps(s))


def intent_doc(scope_patterns, revision=("= tower yard stone 4 12",), layout=(), base=H0, candidate="A"):
    return {"format": "VERDANDI-INTENT", "version": "0", "brief": "vector", "prompt": "make the yard more imposing",
            "candidate": candidate, "rationale": "a vector", "base": dict(base), "scope": list(scope_patterns),
            "revision": list(revision), "layout": list(layout)}


def scope_cases():
    out = []
    ok = [{"name": "play holds", "ok": True}]
    # 1. a new material for the yard's tower: clean
    b = scene()
    c = clone(b)
    c["materials"]["basalt"] = mat((60, 60, 64), 0.9)
    c["visuals"][0]["material"] = "basalt"
    out.append(("a new material retargets one tower: clean", intent_doc(["yard/tower/*", "material/basalt"]), b, c, H0, ok))
    # 2. a shared material changed for the yard: the gate's tower, the city and the play geometry are affected
    c = clone(b)
    c["materials"]["stone"] = mat((92, 92, 98), 0.86)
    out.append(("a shared material changed: what else uses it leaks", intent_doc(["yard/**", "material/stone"]), b, c, H0, ok))
    # 3. early cutoff: the material written differently, the same content
    c = clone(b)
    c["materials"]["stone"] = mat((112, 110, 104), 0.86000001)
    out.append(("the same content, written again: early cutoff, nothing realized", intent_doc(["material/stone"]), b, c, H0, ok))
    # 4. a grant of play is refused before anything else counts
    out.append(("a grant of play/ is refused", intent_doc(["play/**"]), b, clone(b), H0, ok))
    # 5. the layout closes a gate cell, inside a layout grant: the play boxes it rebuilds are covered
    c = clone(b)
    c["tops"][1 * 6 + 4] = 4.0
    c["collision"].append({"id": "c:4,1-4,1", "kind": "wall", "material": "stone", "cells": [4, 1, 4, 1], "box": [8.0, 0.0, 2.0, 10.0, 4.0, 4.0]})
    out.append(("the layout closes a cell inside its grant: clean", intent_doc(["layout/gate", "gate/**"], revision=(), layout=("close 4,1 4,1",)), b, c, H0, ok))
    # 6. the same change, granted for the yard only: refused
    out.append(("the layout closes a cell outside its grant: refused", intent_doc(["layout/yard", "gate/**"], revision=(), layout=("close 4,1 4,1",)), b, c, H0, ok))
    # 7. a surface grant covers a change in the look of the walls, never their shape
    c = clone(b)
    c["materials"]["granite"] = mat((80, 80, 80), 0.7)
    c["collision"][1]["material"] = "granite"
    out.append(("a surface grant covers the walls' new material", intent_doc(["surface/wall", "material/granite"]), b, c, H0, ok))
    # 8. the air is granted by name: '**' does not reach it
    c = clone(b)
    c["environment"]["fog"]["density"] = 0.08
    out.append(("'**' does not reach env/: the fog leaks", intent_doc(["**"]), b, c, H0, ok))
    out.append(("env/fog granted by name: clean", intent_doc(["env/fog"]), b, c, H0, ok))
    # 9. written against H0, checked against H1: the verdict is H1's
    c = clone(b)
    c["materials"]["basalt"] = mat((60, 60, 64), 0.9)
    c["visuals"][0]["material"] = "basalt"
    out.append(("written against one head, checked against another: re-evaluated", intent_doc(["yard/tower/*", "material/basalt"]), b, c, H1, ok))
    # 10. a failed check refuses
    out.append(("a failed check refuses", intent_doc(["yard/tower/*", "material/basalt"]), b, c, H0,
                [{"name": "play holds", "ok": True}, {"name": "no dressing where a player can be", "ok": False}]))
    # 11. materials that name each other as parents
    c = clone(b)
    c["materials"]["stone"] = mat((112, 110, 104), 0.86, parent="glow")
    c["materials"]["glow"] = mat((255, 40, 190), 0.4, 0.0, (255, 40, 190), 45.0, parent="stone")
    out.append(("materials in a cycle of parents: refused", intent_doc(["**", "material/stone", "material/glow"]), b, c, H0, ok))
    # 12. a neon's light follows its material's emission: affected, not modified
    c = clone(b)
    c["materials"]["glow"] = mat((255, 40, 190), 0.4, 0.0, (255, 40, 190), 70.0)
    c["lights"][0]["candela"] = 70.0
    out.append(("a neon's light follows its material: affected, and unclaimed", intent_doc(["material/glow"]), b, c, H0, ok))
    # 13. a spawn moved: play is never the art's
    c = clone(b)
    c["spawns"]["A"]["x"] = 5.0
    out.append(("a spawn moved: refused", intent_doc(["**"]), b, c, H0, ok))
    # 14. a declared pattern that touched nothing is reported, and a piece removed is realized
    c = clone(b)
    del c["visuals"][1]
    out.append(("a piece removed; a pattern that touched nothing", intent_doc(["gate/tower/*", "yard/neon/*"]), b, c, H0, ok))
    return out


VALUES = [
    ("members in ascending byte order of their keys", {"b": "2", "a": "1", "a_b": "3", "a0": "4"}),
    ("nested arrays, objects and booleans", {"k": [True, False, {"z": [], "y": {}}, "", "x"]}),
    ("escapes: quote, backslash, the five short forms, other controls, DEL; '/' as it is",
     {"s": "\"\\\b\t\n\f\r\u0001\u001f\u007f/"}),
    ("non-ASCII as \\u, lowercase; above U+FFFF as a surrogate pair", {"s": "Verðandi é → \U0001f600"}),
    ("an empty object", {}),
]
VALUE_ERRORS = [
    ("a number is not a value of this form", {"n": 1}, "INTENT-TYPE"),
    ("null is not a value of this form", {"n": None}, "INTENT-NULL"),
    ("a key outside [a-z][a-z0-9_]*", {"Key": "1"}, "INTENT-KEY"),
]
BYTES = [
    ("canonical bytes", b'{"a":"1","b":[true,false]}', None),
    ("whitespace outside strings", b'{"a": "1"}', "INTENT-NONCANONICAL"),
    ("members out of order", b'{"b":"1","a":"2"}', "INTENT-NONCANONICAL"),
    ("a key twice", b'{"a":"1","a":"2"}', "INTENT-DUPLICATE-KEY"),
    ("an integer", b'{"a":1}', "INTENT-NUMBER"),
    ("a fraction", b'{"a":1.5}', "INTENT-NUMBER"),
    ("null", b'{"a":null}', "INTENT-NULL"),
    ("a key with a capital", b'{"Key":"1"}', "INTENT-KEY"),
    ("a byte above 0x7f", b'{"a":"\xc3\xb0"}', "INTENT-BYTES"),
    ("an escape in capitals", b'{"a":"\\u00E9"}', "INTENT-NONCANONICAL"),
    ("an escaped solidus", b'{"a":"\\/"}', "INTENT-NONCANONICAL"),
    ("a lone surrogate", b'{"a":"\\ud800"}', "INTENT-STRING"),
    ("not JSON: a second value", b'{"a":"1"}{}', "INTENT-NOT-JSON"),
    ("not JSON: a bare word", b'{"a":yes}', "INTENT-NOT-JSON"),
]


def intents():
    good = intent_doc(["yard/tower/*"])
    out = [("a valid intent", good, None)]
    bad = dict(good, version="1")
    out.append(("an unknown version is refused, never translated", bad, "INTENT-VERSION"))
    bad = {k: v for k, v in good.items() if k != "rationale"}
    out.append(("a missing field", bad, "INTENT-FIELD"))
    bad = dict(good, extra="x")
    out.append(("an unknown field", bad, "INTENT-FIELD"))
    bad = dict(good, revision=["tower yard stone 4 12"])
    out.append(("a revision line without '=', '+' or '-'", bad, "INTENT-REVISION"))
    bad = dict(good, base=dict(H0, art_sha256="A" * 64))
    out.append(("a base hash in capitals", bad, "INTENT-FIELD"))
    bad = dict(good, layout=["widen the yard"])
    out.append(("a layout line that is not a design statement", bad, "INTENT-LAYOUT"))
    return out


PATTERNS = [
    ("yard/tower/*", "yard/tower/0,1", True), ("yard/tower/*", "yard/neon/1,1:n", False), ("yard/**", "yard/neon/1,1:n", True),
    ("**", "yard/tower/0,1", True), ("**", "material/stone", False), ("*/tower/*", "env/fog", False), ("**", "play/wall/c:0,0-5,0", False),
    ("material/*", "material/stone", True), ("yard/**/0,1", "yard/tower/0,1", True), ("yard/**", "yard", True),
    ("*/tower/*", "gate/tower/5,1", True), ("city/skyline/*", "city/skyline/0,2", True), ("yard/tower", "yard/tower/0,1", False),
]


def build():
    v = {"format": "VERDANDI-DIRECTOR-VECTORS", "protocol": scope.PROTOCOL, "version": scope.VERSION,
         "note": "Inputs and the exact expected outputs of DIRECTOR-0 version 0. Byte strings are hex. A second implementation reads this file and reproduces every expected output; it does not run the Python reference.",
         "dumps": [], "loads": [], "intents": [], "heads": [], "materials": [], "patterns": [], "scope": []}
    for name, val in VALUES:
        b = canon.dumps(val)
        v["dumps"].append({"name": name, "value": val, "expect": {"ok": True, "hex": b.hex(), "sha256": canon.sha256(b)}})
    for name, val, code in VALUE_ERRORS:
        try:
            canon.dumps(val)
            raise SystemExit("expected a refusal: " + name)
        except canon.IntentError as e:
            assert e.code == code, (name, e.code)
        v["dumps"].append({"name": name, "value": val, "expect": {"ok": False, "code": code}})
    for name, b, code in BYTES:
        try:
            val = canon.loads(b)
            assert code is None, name
            v["loads"].append({"name": name, "hex": b.hex(), "expect": {"ok": True, "value": val}})
        except canon.IntentError as e:
            assert e.code == code, (name, e.code, code)
            v["loads"].append({"name": name, "hex": b.hex(), "expect": {"ok": False, "code": code}})
    for name, doc, code in intents():
        b = canon.dumps(doc)
        try:
            canon.load_intent(b)
            assert code is None, name
            v["intents"].append({"name": name, "hex": b.hex(), "expect": {"ok": True, "sha256": canon.sha256(b)}})
        except canon.IntentError as e:
            assert e.code == code, (name, e.code, code)
            v["intents"].append({"name": name, "hex": b.hex(), "expect": {"ok": False, "code": code}})
    for parts in (H0, H1):
        v["heads"].append({"parts": parts, "expect": canon.head(parts)})
    for m in (mat((112, 110, 104), 0.86), mat((255, 40, 190), 0.4, 0.0, (255, 40, 190), 45.0), mat((1, 2, 3), 0.33335, 1.0, parent="stone")):
        rec = scope.material_record(m)
        v["materials"].append({"material": m, "expect": {"record_hex": canon.dumps(rec).hex(), "digest": scope.material_digest(m)}})
    for p, a, want in PATTERNS:
        assert scope.match(p, a) == want, (p, a)
        v["patterns"].append({"pattern": p, "address": a, "expect": want})
    for name, it, b, c, cur, checks in scope_cases():
        canon.validate(canon.loads(canon.dumps(it)))
        ver = scope.check_scope(it, b, c, cur, checks)
        vb = canon.dumps(ver)
        v["scope"].append({"name": name, "intent": it, "base": b, "candidate": c, "current": cur, "checks": checks,
                           "expect": {"verdict": ver, "hex": vb.hex(), "sha256": canon.sha256(vb)}})
    return v


def main(argv):
    v = build()
    path = os.path.join(HERE, "vectors.json")
    text = json.dumps(v, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if "--write" in argv:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("wrote %s: %d vectors" % (os.path.relpath(path), sum(len(v[k]) for k in ("dumps", "loads", "intents", "heads", "materials", "patterns", "scope"))))
        return 0
    for c in v["scope"]:
        print("%-62s %-8s %s" % (c["name"][:62], c["expect"]["verdict"]["verdict"], ",".join(c["expect"]["verdict"]["codes"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
