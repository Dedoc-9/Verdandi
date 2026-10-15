# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/studio_refs.py — STUDIO-1's references: what a tagged piece of the scene is, where it is, and how it stands to
# the others and to the walls, computed from the scene alone. Pure functions over a scene (art/dress.py's scene.json,
# as data); no file, no clock, no randomness. Standard library only.
#
# By the owner's ruling of 2026-10-11: "Metric geometry: For each referenced piece, include its world-space bounds in
# metres, position, dimensions, and orientation. State the coordinate convention." "Computed relationships: Include
# measured gaps, relative directions, facing, and nearest relevant wall face. Distinguish measured relationships from
# inferred ones; don't present an approximate facing test as an exact connection."
#
# AN OBJECT. The scene's dressing is axis-aligned boxes, each with an id `kind:place[:part]`. An object is a box whose id
# is not a part of another's, with its parts: an id is a part of the object whose id it extends by `:something`, when
# that object exists (a canopy's ribs `canopy:19,10-28,11:rib20`, its downlights and edge fixtures, a tower's cornice
# `…:cap`). `neon:11,14:n` is an object of its own, since no `neon:11,14` exists. A light belongs to the object whose
# id or part's id it shares. An object's identity is its id: the same id at another revision is the same object, and
# an object whose id is gone is gone (nothing is matched to it by likeness).
#
# MEASURED, here, means computed exactly from the scene's boxes and records, rounded to the millimetre (and the degree)
# for reading; INFERRED means a test that approximates, and says so.

import hashlib
import json
import math

PART_WORDS = ("rib", "light-edge", "light", "cap")


def objects(scene):
    """{object id: {"id", "kind", "region", "material", "by", "boxes": [box], "parts": {word: n}, "lights": [light]}}."""
    ids = {v["id"] for v in scene.get("visuals", [])}

    def root(i):
        r = i
        while r.count(":") >= 2 and r.rsplit(":", 1)[0] in ids:
            r = r.rsplit(":", 1)[0]
        return r
    out = {}
    for v in scene.get("visuals", []):
        r = root(v["id"])
        o = out.setdefault(r, {"id": r, "kind": r.split(":", 1)[0], "region": "city" if v["region"] == "*" else v["region"],
                               "material": "", "by": v["by"], "boxes": [], "parts": {}, "lights": []})
        o["boxes"].append([float(x) for x in v["box"]])
        if v["id"] == r:
            o["material"] = v["material"]
        else:
            tail = v["id"][len(r) + 1:]
            word = next((w for w in PART_WORDS if tail.startswith(w)), "part")
            o["parts"][word] = o["parts"].get(word, 0) + 1
    for L in scene.get("lights", []):
        r = root(L["id"]) if L["id"] in ids else L["id"]
        if r in out:
            out[r]["lights"].append({k: L[k] for k in sorted(L) if k not in ("by",)})
    return out


def address(o):
    kind, place = o["id"].split(":", 1)
    return "%s/%s/%s" % (o["region"], kind, place)


def fingerprint(o):
    """What the object is, as bytes: its boxes, its material, its parts and its lights (not its statement's hash, which
    every object a statement makes shares)."""
    doc = {"id": o["id"], "material": o["material"], "boxes": sorted(o["boxes"]), "parts": o["parts"],
           "lights": sorted(json.dumps(L, sort_keys=True) for L in o["lights"])}
    return hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def r3(x):
    return round(float(x) + 0.0, 3)


def bounds(o):
    b = o["boxes"]
    return [min(x[0] for x in b), min(x[1] for x in b), min(x[2] for x in b), max(x[3] for x in b), max(x[4] for x in b), max(x[5] for x in b)]


COMPASS = ("north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west")


def bearing(dx, dz):
    """Degrees, 0 north (-z), 90 east (+x), as the scene's yaw; and its compass word."""
    deg = math.degrees(math.atan2(dx, -dz)) % 360.0
    return round(deg, 1) % 360.0, COMPASS[int((deg + 22.5) // 45) % 8]


def geometry(o):
    b = bounds(o)
    size = [b[3] - b[0], b[4] - b[1], b[5] - b[2]]
    long_axis = "x (east-west)" if size[0] > size[2] else "z (north-south)" if size[2] > size[0] else "none (square in plan)"
    faces = []
    for L in o["lights"]:
        d = L.get("dir")
        if L.get("type") == "rect" and isinstance(d, list) and len(d) == 3 and (d[0] or d[2]):
            faces.append(bearing(d[0], d[2])[1])
    g = {"bounds_m": [r3(x) for x in b], "centre_m": [r3((b[0] + b[3]) / 2), r3((b[1] + b[4]) / 2), r3((b[2] + b[5]) / 2)],
         "size_m": [r3(x) for x in size], "underside_m": r3(b[1]), "top_m": r3(b[4]), "long_axis": long_axis,
         "orientation": "axis-aligned boxes; no rotation", "boxes": len(o["boxes"]), "parts": dict(sorted(o["parts"].items())),
         "lights": len(o["lights"])}
    if faces:
        g["faces"] = {"directions": sorted(set(faces)), "basis": "measured: the direction its lights point, as the scene records it"}
    return g


def box_gap(a, b):
    """The least distance between two boxes, in metres (0 if they touch or overlap), and its three axis gaps."""
    d = [max(0.0, b[i] - a[i + 3], a[i] - b[i + 3]) for i in range(3)]
    return math.sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]), d


def gap(A, B):
    return min(box_gap(a, b)[0] for a in A for b in B)


def relation(a, b, ta, tb):
    """How object b stands to object a: measured from their boxes; and, where a records a facing, an inferred test."""
    ba, bb = bounds(a), bounds(b)
    ca = [(ba[0] + ba[3]) / 2, (ba[2] + ba[5]) / 2]
    cb = [(bb[0] + bb[3]) / 2, (bb[2] + bb[5]) / 2]
    deg, word = bearing(cb[0] - ca[0], cb[1] - ca[1])
    ox = min(ba[3], bb[3]) - max(ba[0], bb[0])
    oz = min(ba[5], bb[5]) - max(ba[2], bb[2])
    g = gap(a["boxes"], b["boxes"])
    rel = {"from": ta, "to": tb,
           "measured": {"gap_m": r3(g), "touching": g == 0.0,
                        "plan_overlap_m": {"x": r3(ox), "z": r3(oz), "note": "negative: the gap between them along that axis"},
                        "direction_of_to": {"bearing_deg": deg, "compass": word, "centres_apart_m": r3(math.hypot(cb[0] - ca[0], cb[1] - ca[1]))},
                        "to_underside_minus_from_underside_m": r3(bb[1] - ba[1]), "to_top_minus_from_top_m": r3(bb[4] - ba[4]),
                        "same_kind": a["kind"] == b["kind"], "same_material": a["material"] == b["material"],
                        "same_statement": a["by"] == b["by"]},
           "basis": "measured: from the scene's boxes; a gap of 0 means the boxes touch or overlap, not that they are joined"}
    faces = [L.get("dir") for L in a["lights"] if L.get("type") == "rect" and isinstance(L.get("dir"), list)]
    if faces:
        d = faces[0]
        rel["inferred"] = {"from_faces_toward_to": (d[0] * (cb[0] - ca[0]) + d[2] * (cb[1] - ca[1])) > 0,
                           "basis": "inferred: whether the other's centre lies on the side %s's lights point to (a half-space "
                                    "test on centres; not a line of sight, not a connection)" % ta}
    return rel


def nearest_wall(o, scene):
    """The wall of the play geometry nearest the object in plan: which, on which side, how far (in plan and in space),
    and how high its top is. Measured from the boxes."""
    best = None
    for w in scene.get("collision", []):
        if w.get("kind") != "wall":
            continue
        wb = [float(x) for x in w["box"]]
        plan = min(math.hypot(box_gap(a, wb)[1][0], box_gap(a, wb)[1][2]) for a in o["boxes"])
        space = min(box_gap(a, wb)[0] for a in o["boxes"])
        key = (round(plan, 6), round(space, 6), w["id"])
        if best is None or key < best[0]:
            best = (key, w, wb)
    if best is None:
        return None
    (_k, w, wb) = best
    b = bounds(o)
    if wb[3] <= b[0]:
        side = "west"
    elif wb[0] >= b[3]:
        side = "east"
    elif wb[5] <= b[2]:
        side = "north"
    elif wb[2] >= b[5]:
        side = "south"
    else:
        side = "below" if wb[4] <= b[1] else "above" if wb[1] >= b[4] else "within its extent in plan"
    return {"wall": w["id"], "address": "play/wall/%s" % w["id"], "side": side, "plan_gap_m": r3(best[0][0]), "gap_m": r3(best[0][1]),
            "wall_top_m": r3(wb[4]), "basis": "measured: from the scene's boxes and the play geometry's walls"}


# what a revision of the statement that made an object can change, by its verb (art/README.md, The art file)
CHANGEABLE = {
    "canopy": "its own statement makes this slab alone: the material, the height (clear of the reach ceiling), the two corner "
              "cells (inside its region), deep D, ribs N, lit R,G,B CANDELAS, edgelit R,G,B CANDELAS",
    "tower": "its statement makes every tower of its region: the material, the least and greatest heights, mass",
    "neon": "its statement makes every neon strip of its region: the emissive material, the height, one face in EVERY",
    "lamp": "its statement makes every lamp of its region: the colour, the candelas, the spacing",
    "puddle": "its statement makes every puddle of its region: the material, the percentage of floor cells",
    "skyline": "its statement makes every skyline block: the material, the least and greatest heights",
    # FACADE-0 (0237)
    "building": "its statement makes this building alone, its mass and every bay of its facade: the material, the height, the two "
                "corner cells, face window|panel MATERIAL, storey M, bay N; one bay of one floor is changed by a bay statement of its "
                "own, named by the bay's place: bay x0,z0-x1,z1:SIDE-bK-fN window|panel [MATERIAL], or blank",
}
