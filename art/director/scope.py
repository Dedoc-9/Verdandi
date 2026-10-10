# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/director/scope.py — DIRECTOR-0's scope protocol (version 0): one pure function and the rules it applies.
#
#   check_scope(intent, base, candidate, current, checks) -> verdict
#
# intent     a validated VERDANDI-INTENT document
# base       the scene (art/dress.py's scene.json, as data) at the head the candidate is checked against
# candidate  the scene after the candidate's revision and layout were applied to that head
# current    the three parts of that head: {art_sha256, world_sha256, exporter_sha256}
# checks     the art checks run on the candidate scene: a list of {name, ok}
#
# No reading of files, no clock, no randomness: the same inputs give the same verdict, byte for byte in the canonical
# form (art/director/intent.py). The conformance vectors (art/director/vectors.json) fix the rules below to bytes, so
# that a second implementation can be held to them without this one.
#
# ADDRESSES. Every piece of the scene has one:
#   <region>/<kind>/<place>   dressing and its light: plaza/tower/18,10, plaza/neon/13,17:s, city/skyline/0,0
#   play/<kind>/<id>          the play geometry, C's boxes: play/wall/c:0,0-7,2, play/ground/ground
#   material/<name>  env/<field>  view/<name>  asset/<name>  region/<name> (a region's bounds)
# A piece is identified by its kind and place (one fixture to a place); its region is where its statement put it.
#
# THE REFERENCE GRAPH. A piece references its material; a material may name a parent (no brief does yet). A material
# changed when the digest of its record changed (early cutoff: the same content, the same digest, nothing propagates),
# or when its parent changed. A piece that did not itself change, whose material changed, is AFFECTED. A cycle among
# materials, or a reference to a material that does not exist, refuses the candidate (GRAPH-CYCLE, GRAPH-DANGLING).
#
# SCOPE. The intent declares patterns. A pattern is '/'-separated segments; '*' matches one segment and '**' any
# number. A pattern whose first segment is '*' or '**' never matches play/, surface/, material/, env/, view/, asset/
# layout/ or region/: those are granted by name. Two kinds of grant are special:
#   layout/<region>   allows the layout to change cells inside that region (through the design tool), and with them
#                     the play geometry they rebuild
#   surface/<kind>    allows a change in the look of play geometry of that kind (its material), never its shape
#   play/...          can never be granted (SCOPE-RESERVED-GRANT)
#
# VERDICT. REFUSED if any of: a grant of play/ or a malformed pattern; the layout changed cells outside every
# layout grant (SCOPE-LAYOUT); the spawns or the grid changed, or play geometry changed with no cell changing
# (SCOPE-PLAY); a graph defect; a failed check (CHECK-FAILED). Otherwise LEAKAGE if anything changed or was affected
# that no pattern covers (SCOPE-LEAK), and CLEAN if not. HEAD-MOVED says the candidate was written against another
# head than the one it was checked against: the verdict is the new head's, never the old one's.

import intent as canon

PROTOCOL, VERSION = "DIRECTOR-0", "0"
NAMESPACES = ("play", "surface", "material", "env", "asset", "view", "layout", "region")
REFUSING = ("SCOPE-RESERVED-GRANT", "SCOPE-PATTERN", "SCOPE-LAYOUT", "SCOPE-PLAY", "GRAPH-CYCLE", "GRAPH-DANGLING", "CHECK-FAILED")


def fmt4(x) -> str:
    return "%.4f" % float(x)


def material_record(m: dict) -> dict:
    """The material's content in the canonical form: its numbers as text (%.4f), its colours as R,G,B."""
    rec = {"base": "%d,%d,%d" % tuple(int(v) for v in m["base"]), "roughness": fmt4(m["roughness"]), "metallic": fmt4(m["metallic"]),
           "emissive": "%d,%d,%d" % tuple(int(v) for v in m["emissive"]), "emissive_strength": fmt4(m["emissive_strength"])}
    if "parent" in m:
        rec["parent"] = m["parent"]
    return rec


def material_digest(m: dict) -> str:
    return canon.sha256(canon.dumps(material_record(m)))


def changed_materials(base: dict, cand: dict):
    """The materials whose content changed, closed over parents; and the graph's defects."""
    codes = set()
    for mats in (base, cand):
        for name, m in mats.items():
            p = m.get("parent")
            if p is not None and p not in mats:
                codes.add("GRAPH-DANGLING")
        # a cycle: follow parents from every material; a revisit within one walk is a cycle
        for name in mats:
            seen, at = set(), name
            while at is not None and at in mats:
                if at in seen:
                    codes.add("GRAPH-CYCLE")
                    break
                seen.add(at)
                at = mats[at].get("parent")
    direct = {n for n in set(base) | set(cand)
              if n not in base or n not in cand or material_digest(base[n]) != material_digest(cand[n])}
    if "GRAPH-CYCLE" in codes:
        return direct, codes
    out = set(direct)
    grew = True
    while grew:
        grew = False
        for n, m in cand.items():
            if n not in out and m.get("parent") in out:
                out.add(n)
                grew = True
    return out, codes


def _pieces(scene: dict) -> dict:
    """Every piece by its identity: {key: (address, material, comparable fields)}."""
    out = {}
    for b in scene.get("collision", []):
        key = "play/" + b["id"]
        out[key] = {"address": "play/%s/%s" % (b["kind"], b["id"]), "material": b["material"], "play": b["kind"],
                    "shape": {"kind": b["kind"], "cells": b["cells"], "box": b["box"]}, "light": None}
    for v in scene.get("visuals", []):
        kind, place = v["id"].split(":", 1)
        region = "city" if v["region"] == "*" else v["region"]
        out[v["id"]] = {"address": "%s/%s/%s" % (region, kind, place), "material": v["material"], "play": None,
                        "shape": {k: v[k] for k in sorted(v) if k not in ("id", "by", "material")}, "light": None}
    for L in scene.get("lights", []):
        if L["id"] not in out:
            kind, place = L["id"].split(":", 1)
            region = "city" if L["region"] == "*" else L["region"]
            out[L["id"]] = {"address": "%s/%s/%s" % (region, kind, place), "material": "", "play": None, "shape": {}, "light": None}
        out[L["id"]]["light"] = {k: L[k] for k in sorted(L) if k not in ("id", "by")}
    return out


def _light_view(piece, mats):
    """A light's fields for comparison. Its colour and candelas are left out when they are its material's emission:
    then they change with the material, and the piece is affected, not modified."""
    L = piece["light"]
    if L is None:
        return None
    m = mats.get(piece["material"])
    if m is not None and list(L.get("color", [])) == list(m["emissive"]) and float(L.get("candela", -1)) == float(m["emissive_strength"]):
        return {k: v for k, v in L.items() if k not in ("color", "candela")}
    return L


def match(pattern: str, address: str) -> bool:
    ps, xs = pattern.split("/"), address.split("/")
    if ps[0] in ("*", "**") and xs[0] in NAMESPACES:
        return False

    def m(i, j):
        if i == len(ps):
            return j == len(xs)
        if ps[i] == "**":
            return any(m(i + 1, k) for k in range(j, len(xs) + 1))
        if j == len(xs):
            return False
        return (ps[i] == "*" or ps[i] == xs[j]) and m(i + 1, j + 1)
    return m(0, 0)


def _cells(base, cand):
    g = base["grid"]
    w = int(g["w"])
    out = [(k // w, k % w) for k in range(len(base["tops"])) if base["tops"][k] != cand["tops"][k]]
    return ["%d,%d" % (x, z) for z, x in sorted(out)]


def check_scope(intent: dict, base: dict, cand: dict, current: dict, checks: list) -> dict:
    codes = set()
    patterns = list(intent["scope"])
    regions = base.get("regions", {})
    for p in patterns:
        segs = p.split("/")
        if any(s == "" for s in segs):
            codes.add("SCOPE-PATTERN")
        elif segs[0] == "play":
            codes.add("SCOPE-RESERVED-GRANT")
        elif segs[0] == "layout" and (len(segs) != 2 or segs[1] not in regions):
            codes.add("SCOPE-PATTERN")
        elif segs[0] == "surface" and len(segs) != 2:
            codes.add("SCOPE-PATTERN")
    # play: the grid and the spawns never change; cells change only where a layout grant allows
    if base["grid"] != cand["grid"] or base["spawns"] != cand["spawns"] or len(base["tops"]) != len(cand["tops"]):
        codes.add("SCOPE-PLAY")
        cells = []
    else:
        cells = _cells(base, cand)
    grants = [regions[p.split("/")[1]] for p in patterns if p.startswith("layout/") and p.split("/")[1:2] and p.split("/")[1] in regions]
    inside = lambda c: any(r[0] <= int(c.split(",")[0]) <= r[2] and r[1] <= int(c.split(",")[1]) <= r[3] for r in grants)
    if cells and not all(inside(c) for c in cells):
        codes.add("SCOPE-LAYOUT")
    # the reference graph
    bm, cm = base.get("materials", {}), cand.get("materials", {})
    mchanged, gcodes = changed_materials(bm, cm)
    codes |= gcodes
    P0, P1 = _pieces(base), _pieces(cand)
    for P, mats in ((P0, bm), (P1, cm)):
        if any(p["material"] and p["material"] not in mats for p in P.values()):
            codes.add("GRAPH-DANGLING")
    realized, affected = set(), set()
    play_shape, play_look = [], []   # (address, kind) of play pieces whose shape / look changed
    for key in sorted(set(P0) | set(P1)):
        a, b = P0.get(key), P1.get(key)
        if a is None or b is None or a["shape"] != b["shape"] or a["material"] != b["material"] or _light_view(a, bm) != _light_view(b, cm):
            for p in (a, b):
                if p is None:
                    continue
                realized.add(p["address"])
                if p["play"] is not None:
                    if a is None or b is None or a["shape"] != b["shape"]:
                        play_shape.append(p["address"])
                    else:
                        play_look.append((p["address"], p["play"]))
        elif b["material"] in mchanged:
            affected.add(b["address"])
            if b["play"] is not None:
                play_look.append((b["address"], b["play"]))
    realized |= {"material/" + n for n in mchanged}
    e0, e1 = dict(base.get("environment", {}), title=base.get("title", "")), dict(cand.get("environment", {}), title=cand.get("title", ""))
    realized |= {"env/" + k for k in set(e0) | set(e1) if e0.get(k) != e1.get(k)}
    for fam, ns in (("views", "view"), ("assets", "asset"), ("regions", "region")):
        x0, x1 = base.get(fam, {}), cand.get(fam, {})
        realized |= {"%s/%s" % (ns, k) for k in set(x0) | set(x1) if x0.get(k) != x1.get(k)}
    if play_shape and not cells:
        codes.add("SCOPE-PLAY")
    # coverage
    surfaces = {p.split("/", 1)[1] for p in patterns if p.startswith("surface/")}
    plain = [p for p in patterns if not p.startswith(("layout/", "surface/"))]
    shape_set = set(play_shape)
    look_kind = dict(play_look)
    used = set()

    def covered(addr):
        if addr in shape_set:
            ok = bool(cells) and bool(grants) and all(inside(c) for c in cells)
            if ok:
                used.update(p for p in patterns if p.startswith("layout/") and any(inside(c) for c in cells))
            return ok
        if addr in look_kind:
            k = look_kind[addr]
            if k in surfaces:
                used.add("surface/" + k)
                return True
            return False
        hit = [p for p in plain if match(p, addr)]
        used.update(hit)
        return bool(hit)
    unclaimed = sorted(a for a in realized | affected if not covered(a))
    for p in patterns:
        if p.startswith("layout/") and p.split("/")[1] in regions and cells:
            r = regions[p.split("/")[1]]
            if any(r[0] <= int(c.split(",")[0]) <= r[2] and r[1] <= int(c.split(",")[1]) <= r[3] for c in cells):
                used.add(p)
    phantom = sorted(set(patterns) - used)
    if unclaimed:
        codes.add("SCOPE-LEAK")
    failed = sorted(c["name"] for c in checks if not c["ok"])
    if failed:
        codes.add("CHECK-FAILED")
    written, checked = canon.head(intent["base"]), canon.head(current)
    if written != checked:
        codes.add("HEAD-MOVED")
    verdict = "REFUSED" if codes & set(REFUSING) else ("LEAKAGE" if "SCOPE-LEAK" in codes else "CLEAN")
    return {
        "protocol": PROTOCOL, "version": VERSION, "verdict": verdict, "codes": sorted(codes),
        "intent_sha256": canon.sha256(canon.dumps(intent)),
        "written_against": written, "checked_against": checked, "re_evaluated": written != checked,
        "declared": sorted(patterns), "realized": sorted(realized), "affected": sorted(affected),
        "unclaimed": unclaimed, "phantom": phantom, "cells_changed": cells,
        "materials_changed": sorted(mchanged), "failed_checks": failed,
    }
