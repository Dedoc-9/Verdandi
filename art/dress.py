# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/dress.py — ART-GENERATION-0's exporter: an art file and an admitted graybox world to one engine scene.
#
#   python art/dress.py NAME [--out DIR]          art/briefs/NAME.art  ->  art/build/NAME/{scene.json, lineage.json, plan.svg}
#
# Four worlds, one authority each:
#
#   W  the canonical world (graybox/level.py): walls and floor from the admitted layout, heights, cover, spawns
#   C  the collision world: every cell's solid top. The player moves against C alone
#   A  the art file (VERDANDI-ART 0, art/briefs/*.art): the look. Written by a model or a person; it proposes
#   S  the scene this file writes: C as play geometry, the look as materials, dressing and lights
#
# The rule that makes the art safe to be bold: the scene's collision is C, exactly, and nothing the art adds has
# collision or stands where a player can be. Dressing sits inside rock, inside a solid top, flat on the floor, flush
# on a wall face, or above the highest point a player's head can reach. art/check.py holds every scene to that.
#
# Deterministic: the same files give the same bytes. Each dressing choice is a hash of its statement and its cell,
# never a running random sequence, so an edit in one place cannot reshuffle the art anywhere else. Standard library
# only. Units are metres; x runs east, z south (the graybox's x across and z down) and y up.

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BRIEFS = os.path.join(HERE, "briefs")
BUILD = os.path.join(HERE, "build")
sys.path.insert(0, os.path.join(REPO, "graybox"))
import level  # noqa: E402  (the graybox converter: W and C)

FORMAT = "VERDANDI-ART 0"
SCENE = "VERDANDI-ART-SCENE 0"
LINEAGE = "VERDANDI-ART-LINEAGE 0"

# the player, as the graybox runtime moves it (graybox/web/sim.js), and the art layer's own two assumptions
PLAYER = {"radius": 0.35, "eye": 1.62, "step": 0.55, "speed": 6.0, "gravity": 20.0, "jump": 7.0}
PLAYER["jump_apex"] = round(PLAYER["jump"] ** 2 / (2 * PLAYER["gravity"]), 4)   # 1.225 m
BODY = 1.80     # the head's height above the feet: the graybox has no head, so the art layer declares one
MARGIN = 0.25   # clearance kept above the highest reachable head
FLAT = 0.02     # dressing this close to a solid top is flat on it (a puddle, a decal)
FLUSH = 0.08    # dressing this thin, against a rock face, is flush on the wall (a sign, a neon strip)
CHUNK = 8       # collision boxes merge only inside 8 x 8 cell chunks, so a change stays in its chunk

CLASSES = ("ground", "floor", "stair", "raised", "cover", "wall")
SOURCES = ("engine", "cc0", "fab", "generated", "own")


class ArtError(Exception):
    """An art file the exporter refuses, with the file and line it names."""


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def pick(key: str) -> int:
    """A stable choice: the first 32 bits of the sha256 of the key."""
    return int(sha256(key.encode("utf-8"))[:8], 16)


def r4(v: float) -> float:
    return round(float(v), 4)


# ------------------------------------------------------------------------------------------------ the art file
def _num(tok, where, lo, hi, what):
    try:
        v = float(tok)
    except ValueError:
        raise ArtError("%s: %r is not a number (%s)" % (where, tok, what))
    if not (lo <= v <= hi):
        raise ArtError("%s: %s %r is outside %s..%s" % (where, what, tok, lo, hi))
    return v


def _rgb(tok, where):
    parts = tok.split(",")
    if len(parts) != 3 or not all(p.isdigit() and (p == "0" or not p.startswith("0")) and int(p) <= 255 for p in parts):
        raise ArtError("%s: %r is not a colour R,G,B, each 0-255" % (where, tok))
    return [int(p) for p in parts]


def _cell(tok, w, h, where):
    try:
        x, z = (int(v) for v in tok.split(","))
    except ValueError:
        raise ArtError("%s: %r is not a cell x,z" % (where, tok))
    if not (0 <= x < w and 0 <= z < h):
        raise ArtError("%s: the cell %d,%d is outside the %d x %d grid" % (where, x, z, w, h))
    return x, z


RESERVED = ("play", "surface", "material", "env", "asset", "view", "layout", "city")
SINGLE = ("map", "title", "seed", "time", "fog", "exposure", "bloom", "rain", "skyline")


def statement_key(code) -> str:
    """The name a revision uses for a statement: one per brief. The verb alone for a statement that may appear once;
    the verb and its first word for the named ones; a canopy adds its corners, since a region may hold several."""
    verb, args = code[0], code[1:]
    if verb in SINGLE:
        return verb
    if verb in ("moon", "sun"):
        return "light"
    if verb == "canopy" and len(args) == 5:
        return "canopy %s %s %s" % (args[0], args[3], args[4])
    return "%s %s" % (verb, args[0] if args else "")


def parse(text: str, fname: str) -> dict:
    """The art file's statements, read and checked for form. The world is not consulted yet."""
    stmts = []
    for n, ln in enumerate(text.splitlines(), start=1):
        code = ln.split("#", 1)[0].split()
        if code:
            stmts.append((n, code))
    if not stmts or " ".join(stmts[0][1]) != FORMAT:
        raise ArtError("%s: the first line is not %r" % (fname, FORMAT))
    A = {"file": fname, "statements": [], "map": None, "title": "", "seed": "verdandi", "time": "night",
         "light": None, "fog": None, "exposure": 0.0, "bloom": 0.6, "rain": 0.0, "assets": {}, "materials": {},
         "surfaces": {}, "regions": {}, "dressing": [], "views": []}
    for n, code in stmts[1:]:
        where = "%s line %d" % (fname, n)
        verb, args = code[0], code[1:]
        norm = " ".join(code)
        skey = statement_key(code)
        if any(st["key"] == skey for st in A["statements"]):
            raise ArtError("%s: a second statement %r: a brief names each statement once" % (where, skey))
        A["statements"].append({"line": n, "text": norm, "hash": sha256(norm.encode("utf-8"))[:12], "key": skey})
        if verb == "map":
            if len(args) != 1 or A["map"]:
                raise ArtError("%s: map takes one name, once" % where)
            A["map"] = args[0]
        elif verb == "title":
            A["title"] = " ".join(args)
        elif verb == "seed":
            A["seed"] = " ".join(args)
        elif verb == "time":
            if args not in (["night"], ["dusk"], ["day"]):
                raise ArtError("%s: time is night, dusk or day" % where)
            A["time"] = args[0]
        elif verb in ("moon", "sun"):
            if len(args) != 4 or A["light"]:
                raise ArtError("%s: %s takes azimuth, elevation, lux and a colour, once" % (where, verb))
            A["light"] = {"kind": verb, "azimuth": _num(args[0], where, 0, 360, "azimuth"), "elevation": _num(args[1], where, -10, 90, "elevation"),
                          "lux": _num(args[2], where, 0, 150000, "lux"), "color": _rgb(args[3], where)}
        elif verb == "fog":
            if len(args) not in (2, 3) or (len(args) == 3 and args[2] != "volumetric"):
                raise ArtError("%s: fog takes a density, a colour and optionally 'volumetric'" % where)
            A["fog"] = {"density": _num(args[0], where, 0, 1, "fog density"), "color": _rgb(args[1], where), "volumetric": len(args) == 3}
        elif verb == "exposure":
            A["exposure"] = _num(args[0] if args else "", where, -8, 8, "exposure bias")
        elif verb == "bloom":
            A["bloom"] = _num(args[0] if args else "", where, 0, 8, "bloom")
        elif verb == "rain":
            A["rain"] = _num(args[0] if args else "", where, 0, 1, "rain")
        elif verb == "asset":
            if len(args) < 4:
                raise ArtError("%s: asset takes a name, an engine path, a source and a licence" % where)
            name, path, source, licence = args[0], args[1], args[2], " ".join(args[3:])
            if source not in SOURCES:
                raise ArtError("%s: the asset's source is one of %s" % (where, ", ".join(SOURCES)))
            if name in A["assets"]:
                raise ArtError("%s: the asset %s is declared twice" % (where, name))
            A["assets"][name] = {"path": path, "source": source, "licence": licence}
        elif verb == "material":
            if len(args) not in (4, 7) or (len(args) == 7 and args[4] != "emissive"):
                raise ArtError("%s: material takes a name, a colour, roughness, metallic, and optionally 'emissive' R,G,B strength" % where)
            m = {"base": _rgb(args[1], where), "roughness": _num(args[2], where, 0, 1, "roughness"),
                 "metallic": _num(args[3], where, 0, 1, "metallic"), "emissive": [0, 0, 0], "emissive_strength": 0.0}
            if len(args) == 7:
                m["emissive"] = _rgb(args[5], where)
                m["emissive_strength"] = _num(args[6], where, 0, 1000, "emissive strength")
            if args[0] in A["materials"]:
                raise ArtError("%s: the material %s is declared twice" % (where, args[0]))
            A["materials"][args[0]] = m
        elif verb == "surface":
            if len(args) != 2 or args[0] not in CLASSES:
                raise ArtError("%s: surface takes one of %s and a material" % (where, ", ".join(CLASSES)))
            A["surfaces"][args[0]] = args[1]
        elif verb == "region":
            if len(args) != 3:
                raise ArtError("%s: region takes a name and two corners" % where)
            if args[0] in A["regions"]:
                raise ArtError("%s: the region %s is declared twice" % (where, args[0]))
            if args[0] in RESERVED:
                raise ArtError("%s: %s is a word the addresses reserve, not a region's name" % (where, args[0]))
            A["regions"][args[0]] = {"corners": args[1:], "where": where}
        elif verb == "view":
            if len(args) != 4:
                raise ArtError("%s: view takes a name, a cell, a yaw and a pitch in degrees" % where)
            if any(v["name"] == args[0] for v in A["views"]):
                raise ArtError("%s: the view %s is declared twice" % (where, args[0]))
            A["views"].append({"name": args[0], "cell": args[1], "yaw": _num(args[2], where, 0, 360, "yaw"),
                               "pitch": _num(args[3], where, -89, 89, "pitch"), "where": where})
        elif verb in ("skyline", "tower", "canopy", "neon", "lamp", "puddle"):
            A["dressing"].append({"verb": verb, "args": args, "where": where, "hash": A["statements"][-1]["hash"], "skey": A["statements"][-1]["key"]})
        else:
            raise ArtError("%s: %r is not a statement of %s" % (where, verb, FORMAT))
    if not A["map"]:
        raise ArtError("%s: no map names the world to dress" % fname)
    return A


# ------------------------------------------------------------------------------------------------ the world
def world(name: str, maps_dir=None) -> dict:
    """The graybox map's W and C, through the graybox converter. `maps_dir` points it at a copy (a revision)."""
    saved = level.MAPS
    if maps_dir:
        level.MAPS = maps_dir
    try:
        return level.convert(name)
    finally:
        level.MAPS = saved


def reach_ceiling(W, C):
    """For every cell, the height dressing above it must clear: the highest head a player can raise over it.

    A cell is standable when a player can get onto it from a spawn: over C, a step to a neighbour may climb at most
    the jump's apex (and drop any height). The head over a cell reaches the highest standable top among the cell and
    its eight neighbours (the player's radius leans into the next cell), plus the body, the jump and a margin."""
    w, h, wall, tops = C["w"], C["h"], W["wall"], C["tops"]
    apex = PLAYER["jump_apex"]
    seen = set()
    frontier = [(sp["x"], sp["z"]) for _k, sp in sorted(W["spawns"].items())]
    seen.update(frontier)
    while frontier:
        nxt = []
        for x, z in frontier:
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = x + dx, z + dz
                if 0 <= a < w and 0 <= b < h and (a, b) not in seen:
                    t = tops[b * w + a]
                    if t < wall and t - tops[z * w + x] <= apex:
                        seen.add((a, b))
                        nxt.append((a, b))
        frontier = nxt
    reach = []
    for z in range(h):
        for x in range(w):
            best = None
            for dz in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    a, b = x + dx, z + dz
                    if 0 <= a < w and 0 <= b < h and (a, b) in seen:
                        t = tops[b * w + a]
                        best = t if best is None else max(best, t)
            if best is None:
                t = tops[z * w + x]
                best = t if t < wall else None
            reach.append(None if best is None else r4(best + BODY + apex + MARGIN))
    return reach, seen


# ------------------------------------------------------------------------------------------------ the scene
def _collision(W, C, surfaces):
    """C as boxes: equal (kind, top) cells merged in runs and then rows, inside each chunk; plus the ground."""
    w, h, cell = C["w"], C["h"], C["cell"]
    kinds = [c[1] for c in W["cells"]]
    out = [{"id": "ground", "kind": "ground", "material": surfaces["ground"], "cells": [0, 0, w - 1, h - 1],
            "box": [0.0, -0.5, 0.0, r4(w * cell), 0.0, r4(h * cell)]}]
    for cz0 in range(0, h, CHUNK):
        for cx0 in range(0, w, CHUNK):
            cx1, cz1 = min(cx0 + CHUNK, w), min(cz0 + CHUNK, h)
            runs = []   # (z, x0, x1, kind, top)
            for z in range(cz0, cz1):
                x = cx0
                while x < cx1:
                    k = z * w + x
                    top, kind = C["tops"][k], kinds[k]
                    if top <= 0:
                        x += 1
                        continue
                    x1 = x
                    while x1 + 1 < cx1 and C["tops"][z * w + x1 + 1] == top and kinds[z * w + x1 + 1] == kind:
                        x1 += 1
                    runs.append([z, x, x1, kind, top])
                    x = x1 + 1
            boxes = []  # [x0, z0, x1, z1, kind, top]
            for z, x0, x1, kind, top in runs:
                for b in boxes:
                    if b[0] == x0 and b[2] == x1 and b[3] == z - 1 and b[4] == kind and b[5] == top:
                        b[3] = z
                        break
                else:
                    boxes.append([x0, z, x1, z, kind, top])
            for x0, z0, x1, z1, kind, top in boxes:
                out.append({"id": "c:%d,%d-%d,%d" % (x0, z0, x1, z1), "kind": kind, "material": surfaces.get(kind, surfaces["wall"]),
                            "cells": [x0, z0, x1, z1],
                            "box": [r4(x0 * cell), 0.0, r4(z0 * cell), r4((x1 + 1) * cell), r4(top), r4((z1 + 1) * cell)]})
    return out


def _region(A, name, w, h, where):
    if name not in A["regions"]:
        raise ArtError("%s: no region %s" % (where, name))
    r = A["regions"][name]
    a = _cell(r["corners"][0], w, h, r["where"])
    b = _cell(r["corners"][1], w, h, r["where"])
    return min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])


def export(A: dict, maps_dir=None) -> dict:
    """The scene and its lineage for a parsed art file."""
    conv = world(A["map"], maps_dir)
    W, C, M = conv["canonical"], conv["collision"], conv["manifest"]
    w, h, cell, wall, tops = C["w"], C["h"], C["cell"], W["wall"], C["tops"]
    rock = lambda x, z: tops[z * w + x] >= wall
    walk = lambda x, z: 0 <= x < w and 0 <= z < h and not rock(x, z)
    for m in list(A["surfaces"].values()):
        if m not in A["materials"]:
            raise ArtError("%s: a surface names the material %s, which is not declared" % (A["file"], m))
    for cls in CLASSES:
        if cls not in A["surfaces"]:
            raise ArtError("%s: no surface for %s" % (A["file"], cls))
    for need in ("cube",):
        if need not in A["assets"]:
            raise ArtError("%s: the asset %r is not declared (every mesh names its source and licence)" % (A["file"], need))
    reach, standable = reach_ceiling(W, C)
    seed = A["seed"]
    visuals, lights = [], []

    def material(name, where):
        if name not in A["materials"]:
            raise ArtError("%s: no material %s" % (where, name))
        return name

    def box(x0, y0, z0, x1, y1, z1):
        return [r4(x0), r4(y0), r4(z0), r4(x1), r4(y1), r4(z1)]

    for d in A["dressing"]:
        verb, args, where, sh, skey = d["verb"], d["args"], d["where"], d["hash"], d["skey"]
        # a choice is keyed by the statement's name and the cell, not by its text: a revision of a statement's
        # numbers changes what the numbers say and keeps every other choice it made
        key = lambda *parts: "|".join([seed, skey] + [str(p) for p in parts])
        if verb == "skyline":
            if len(args) != 3:
                raise ArtError("%s: skyline takes a material and a lowest and highest height" % where)
            mat = material(args[0], where)
            lo, hi = _num(args[1], where, wall, 400, "height"), _num(args[2], where, wall, 400, "height")
            # 2 x 2 blocks of rock, none of whose cells borders floor: the city beyond the walls
            for z in range(0, h - 1, 2):
                for x in range(0, w - 1, 2):
                    blk = [(x, z), (x + 1, z), (x, z + 1), (x + 1, z + 1)]
                    if not all(rock(a, b) for a, b in blk):
                        continue
                    if any(walk(a + dx, b + dz) for a, b in blk for dx in (-1, 0, 1) for dz in (-1, 0, 1)):
                        continue
                    steps = int(hi - lo)
                    top = lo + (pick(key(x, z)) % (steps + 1) if steps > 0 else 0)
                    visuals.append({"id": "skyline:%d,%d" % (x, z), "by": sh, "region": "*", "asset": "cube", "material": mat,
                                    "box": box(x * cell, wall, z * cell, (x + 2) * cell, top, (z + 2) * cell)})
        elif verb == "tower":
            if len(args) != 4:
                raise ArtError("%s: tower takes a region, a material and a lowest and highest height" % where)
            x0, z0, x1, z1 = _region(A, args[0], w, h, where)
            mat = material(args[1], where)
            lo, hi = _num(args[2], where, wall, 400, "height"), _num(args[3], where, wall, 400, "height")
            done = set()
            for z in range(max(0, z0 - 1), min(h, z1 + 2)):
                for x in range(max(0, x0 - 1), min(w, x1 + 2)):
                    if not rock(x, z) or (x, z) in done:
                        continue
                    # a rock cell that borders the region's floor
                    if not any(x0 <= a <= x1 and z0 <= b <= z1 and walk(a, b) for a in (x - 1, x, x + 1) for b in (z - 1, z, z + 1)):
                        continue
                    done.add((x, z))
                    steps = int(hi - lo)
                    top = lo + (pick(key(x, z)) % (steps + 1) if steps > 0 else 0)
                    visuals.append({"id": "tower:%d,%d" % (x, z), "by": sh, "region": args[0], "asset": "cube", "material": mat,
                                    "box": box(x * cell, wall, z * cell, (x + 1) * cell, top, (z + 1) * cell)})
        elif verb == "canopy":
            if len(args) not in (3, 5):
                raise ArtError("%s: canopy takes a region, a material, a height and optionally two corners inside it" % where)
            x0, z0, x1, z1 = _region(A, args[0], w, h, where)
            if len(args) == 5:
                a, b = _cell(args[3], w, h, where), _cell(args[4], w, h, where)
                sx0, sz0, sx1, sz1 = min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])
                if not (x0 <= sx0 and sx1 <= x1 and z0 <= sz0 and sz1 <= z1):
                    raise ArtError("%s: the canopy's corners leave its region %s" % (where, args[0]))
                x0, z0, x1, z1 = sx0, sz0, sx1, sz1
            mat = material(args[1], where)
            y = _num(args[2], where, 0.5, 200, "height")
            visuals.append({"id": "canopy:%d,%d-%d,%d" % (x0, z0, x1, z1), "by": sh, "region": args[0], "asset": "cube", "material": mat,
                            "box": box(x0 * cell, y, z0 * cell, (x1 + 1) * cell, y + 0.4, (z1 + 1) * cell)})
        elif verb == "neon":
            if len(args) != 4:
                raise ArtError("%s: neon takes a region, an emissive material, a height and 'every N' faces" % where)
            x0, z0, x1, z1 = _region(A, args[0], w, h, where)
            mat = material(args[1], where)
            if A["materials"][mat]["emissive_strength"] <= 0:
                raise ArtError("%s: the neon's material %s does not emit" % (where, mat))
            y = _num(args[2], where, 0.3, wall - 0.2, "height")
            every = int(_num(args[3], where, 1, 64, "every"))
            col = A["materials"][mat]["emissive"]
            for z in range(z0, z1 + 1):
                for x in range(x0, x1 + 1):
                    if not walk(x, z):
                        continue
                    # each face between this floor cell and a rock neighbour: west, east, north, south
                    for face, (dx, dz) in (("w", (-1, 0)), ("e", (1, 0)), ("n", (0, -1)), ("s", (0, 1))):
                        a, b = x + dx, z + dz
                        if not (0 <= a < w and 0 <= b < h) or not rock(a, b):
                            continue
                        if pick(key(x, z, face)) % every:
                            continue
                        cx0, cz0, cx1, cz1 = x * cell, z * cell, (x + 1) * cell, (z + 1) * cell
                        t = 0.05
                        if face == "w":
                            bx, nrm = box(cx0, y, cz0 + 0.3, cx0 + t, y + 0.12, cz1 - 0.3), [1, 0, 0]
                        elif face == "e":
                            bx, nrm = box(cx1 - t, y, cz0 + 0.3, cx1, y + 0.12, cz1 - 0.3), [-1, 0, 0]
                        elif face == "n":
                            bx, nrm = box(cx0 + 0.3, y, cz0, cx1 - 0.3, y + 0.12, cz0 + t), [0, 0, 1]
                        else:
                            bx, nrm = box(cx0 + 0.3, y, cz1 - t, cx1 - 0.3, y + 0.12, cz1), [0, 0, -1]
                        vid = "neon:%d,%d:%s" % (x, z, face)
                        visuals.append({"id": vid, "by": sh, "region": args[0], "asset": "cube", "material": mat, "box": bx})
                        px = r4((bx[0] + bx[3]) / 2 + nrm[0] * 0.08)
                        pz = r4((bx[2] + bx[5]) / 2 + nrm[2] * 0.08)
                        lights.append({"id": vid, "by": sh, "region": args[0], "type": "rect", "pos": [px, r4(y + 0.06), pz], "dir": nrm,
                                       "color": col, "candela": r4(A["materials"][mat]["emissive_strength"]), "width": r4(cell - 0.6),
                                       "height": 0.12, "radius": r4(cell * 4)})
        elif verb == "lamp":
            if len(args) != 4:
                raise ArtError("%s: lamp takes a region, a colour, candelas and a spacing in cells" % where)
            x0, z0, x1, z1 = _region(A, args[0], w, h, where)
            col = _rgb(args[1], where)
            cd = _num(args[2], where, 0, 100000, "candelas")
            sp = int(_num(args[3], where, 1, 48, "spacing"))
            if "housing" not in A["materials"]:
                raise ArtError("%s: a lamp hangs in a housing: declare the material 'housing'" % where)
            for z in range(z0, z1 + 1):
                for x in range(x0, x1 + 1):
                    # an absolute lattice, so a lamp's place does not depend on the region's corners
                    if x % sp or z % sp or not walk(x, z):
                        continue
                    y = max(reach[z * w + x] + 0.1, 3.4)
                    cx, cz = (x + 0.5) * cell, (z + 0.5) * cell
                    vid = "lamp:%d,%d" % (x, z)
                    visuals.append({"id": vid, "by": sh, "region": args[0], "asset": "cube", "material": "housing",
                                    "box": box(cx - 0.25, y, cz - 0.25, cx + 0.25, y + 0.12, cz + 0.25)})
                    lights.append({"id": vid, "by": sh, "region": args[0], "type": "point", "pos": [r4(cx), r4(y - 0.05), r4(cz)],
                                   "dir": [0, -1, 0], "color": col, "candela": r4(cd), "radius": r4(cell * 6)})
        elif verb == "puddle":
            if len(args) != 3:
                raise ArtError("%s: puddle takes a region, a material and a percentage of its floor cells" % where)
            x0, z0, x1, z1 = _region(A, args[0], w, h, where)
            mat = material(args[1], where)
            pct = int(_num(args[2], where, 0, 100, "percentage"))
            for z in range(z0, z1 + 1):
                for x in range(x0, x1 + 1):
                    k = z * w + x
                    if tops[k] != 0 or W["cells"][k][1] not in ("floor", "stair"):
                        continue
                    hv = pick(key(x, z))
                    if hv % 100 >= pct:
                        continue
                    ix, iz = 0.15 + (hv >> 8) % 40 / 100.0, 0.15 + (hv >> 16) % 40 / 100.0
                    ex, ez = 0.15 + (hv >> 20) % 40 / 100.0, 0.15 + (hv >> 26) % 40 / 100.0
                    visuals.append({"id": "puddle:%d,%d" % (x, z), "by": sh, "region": args[0], "asset": "cube", "material": mat,
                                    "box": box(x * cell + ix, 0.001, z * cell + iz, (x + 1) * cell - ex, 0.008, (z + 1) * cell - ez)})
    # one fixture to a place: a place is the kind and the cell (and face) a piece of dressing stands on, whatever
    # region or statement made it. Two pieces in one place are coplanar copies that flicker in an engine, and an
    # address that names two things names neither (DIRECTOR-0's addresses rest on this).
    line_of = {s["hash"]: s["line"] for s in A["statements"]}
    placed = {}
    for v in visuals:
        kind, place = v["id"].split(":", 1)
        if (kind, place) in placed:
            raise ArtError("%s: two pieces of dressing in one place, %s at %s: from line %d and line %d" % (
                A["file"], kind, place, line_of.get(placed[(kind, place)], 0), line_of.get(v["by"], 0)))
        placed[(kind, place)] = v["by"]
    collision = _collision(W, C, A["surfaces"])
    used = {v["asset"] for v in visuals} | {"cube"}
    spawns = {k: {"x": r4((sp["x"] + 0.5) * cell), "z": r4((sp["z"] + 0.5) * cell), "y": r4(tops[sp["z"] * w + sp["x"]]), "yaw": r4(sp["yaw"])}
              for k, sp in sorted(W["spawns"].items())}
    views = {}
    for v in A["views"]:
        x, z = _cell(v["cell"], w, h, v["where"])
        if (x, z) not in standable:
            raise ArtError("%s: the view %s stands at %d,%d, where no player can stand" % (v["where"], v["name"], x, z))
        views[v["name"]] = {"x": r4((x + 0.5) * cell), "z": r4((z + 0.5) * cell), "y": r4(tops[z * w + x] + PLAYER["eye"]),
                            "yaw": r4(v["yaw"]), "pitch": r4(v["pitch"])}
    scene = {
        "format": SCENE, "name": A["name"], "title": A["title"], "map": A["map"],
        "units": "metres; x east, z south, y up; yaw in degrees, 0 north (-z), 90 east (+x)",
        "grid": {"w": w, "h": h, "cell": cell, "wall": wall},
        "tops": tops, "reach": reach,
        "player": dict(PLAYER, body=BODY, margin=MARGIN, flat=FLAT, flush=FLUSH),
        "spawns": spawns, "views": views,
        "regions": {k: list(_region(A, k, w, h, A["file"])) for k in sorted(A["regions"])},
        "environment": {"time": A["time"], "light": A["light"], "fog": A["fog"], "exposure": A["exposure"], "bloom": A["bloom"], "rain": A["rain"]},
        "materials": A["materials"],
        "assets": {k: v for k, v in sorted(A["assets"].items()) if k in used},
        "collision": collision, "visuals": sorted(visuals, key=lambda v: v["id"]), "lights": sorted(lights, key=lambda v: v["id"]),
    }
    scene_bytes = (json.dumps(scene, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    lineage = {
        "format": LINEAGE, "name": A["name"],
        "art_file": A["file"], "art_sha256": A["sha256"],
        "map": M["map"], "map_source": M["source"], "graybox_converter_sha256": M["converter_sha256"],
        "canonical_sha256": M["canonical_sha256"], "collision_sha256": M["collision_sha256"],
        "exporter_sha256": sha256(open(os.path.abspath(__file__), "rb").read().replace(b"\r\n", b"\n")),
        "scene_sha256": sha256(scene_bytes),
        "assets": scene["assets"],
        "statements": A["statements"],
        "counts": {"collision": len(collision), "visuals": len(visuals), "lights": len(lights)},
    }
    return {"scene": scene, "scene_bytes": scene_bytes, "lineage": lineage, "W": W, "C": C}


def load(name: str, path=None) -> dict:
    path = path or os.path.join(BRIEFS, name + ".art")
    raw = open(path, "rb").read().replace(b"\r\n", b"\n")
    A = parse(raw.decode("utf-8"), os.path.basename(path))
    A["name"], A["sha256"] = name, sha256(raw)
    return A


# ------------------------------------------------------------------------------------------------ the plan view
def plan_svg(out: dict) -> str:
    """A top view of the scene, for a person to read: the play geometry, the dressing and the lights."""
    S = out["scene"]
    w, h, cell, wall = S["grid"]["w"], S["grid"]["h"], S["grid"]["cell"], S["grid"]["wall"]
    px = 14
    hexc = lambda c: "#%02x%02x%02x" % tuple(c)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" font-family="sans-serif">'
             % (w * px, h * px + 40, w * px, h * px + 40), '<rect width="100%%" height="100%%" fill="#0d1014"/>']
    for z in range(h):
        for x in range(w):
            t = S["tops"][z * w + x]
            if t >= wall:
                f = "#20252b"
            elif t == 0:
                f = "#5b6168"
            else:
                g = int(110 + 60 * min(t, 3) / 3)
                f = "#%02x%02x%02x" % (g, g, g - 6)
            parts.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"/>' % (x * px, z * px, px, px, f))
    sc = px / cell
    for v in S["visuals"]:
        b = v["box"]
        kind = v["id"].split(":")[0]
        m = S["materials"][v["material"]]
        if kind in ("skyline", "tower"):
            hgt = b[4]
            a = min(1.0, 0.25 + hgt / 40)
            fill, op = "#9aa7b4", a
        elif kind == "neon":
            fill, op = hexc(m["emissive"]), 1.0
        elif kind == "puddle":
            fill, op = "#2a4d6e", 0.85
        elif kind == "canopy":
            fill, op = "#c8b8a0", 0.35
        else:
            fill, op = "#e0e0e0", 0.9
        parts.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s" fill-opacity="%.2f"/>'
                     % (b[0] * sc, b[2] * sc, max(0.6, (b[3] - b[0]) * sc), max(0.6, (b[5] - b[2]) * sc), fill, op))
    for L in S["lights"]:
        if L["type"] == "point":
            parts.append('<circle cx="%.2f" cy="%.2f" r="5" fill="%s" fill-opacity="0.35"/><circle cx="%.2f" cy="%.2f" r="1.6" fill="%s"/>'
                         % (L["pos"][0] * sc, L["pos"][2] * sc, hexc(L["color"]), L["pos"][0] * sc, L["pos"][2] * sc, hexc(L["color"])))
    for k, sp in S["spawns"].items():
        parts.append('<circle cx="%.2f" cy="%.2f" r="5" fill="none" stroke="%s" stroke-width="2"/><text x="%.2f" y="%.2f" fill="#fff" font-size="9" text-anchor="middle">%s</text>'
                     % (sp["x"] * sc, sp["z"] * sc, "#ffb347" if k == "A" else "#47d1ff", sp["x"] * sc, sp["z"] * sc + 3, k))
    parts.append('<text x="8" y="%d" fill="#cfd6dd" font-size="12">%s — %d play boxes, %d dressing pieces, %d lights</text>'
                 % (h * px + 16, (S["title"] or S["name"]).replace("&", "&amp;").replace("<", "&lt;"), len(S["collision"]), len(S["visuals"]), len(S["lights"])))
    parts.append('<text x="8" y="%d" fill="#7f8a95" font-size="10">scene %s · plan view, not a render</text>' % (h * px + 32, out["lineage"]["scene_sha256"][:16]))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def write(out: dict, dest: str):
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "scene.json"), "wb") as fh:
        fh.write(out["scene_bytes"])
    with open(os.path.join(dest, "lineage.json"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out["lineage"], indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    with open(os.path.join(dest, "plan.svg"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(plan_svg(out))


def main(argv) -> int:
    names = [a for a in argv if not a.startswith("--")]
    if not names:
        print("usage: python art/dress.py NAME [--out DIR]   (art/briefs/NAME.art)")
        return 2
    dest = None
    if "--out" in argv:
        i = argv.index("--out")
        dest = argv[i + 1] if i + 1 < len(argv) else None
        names = [n for n in names if n != dest]
    for name in names:
        try:
            out = export(load(name))
        except (ArtError, level.MapError) as e:
            print("REFUSED %s: %s" % (name, e))
            return 1
        d = dest or os.path.join(BUILD, name)
        write(out, d)
        L = out["lineage"]
        print("%s  scene %s  (%d play boxes, %d dressing pieces, %d lights)  ->  %s"
              % (name, L["scene_sha256"][:16], L["counts"]["collision"], L["counts"]["visuals"], L["counts"]["lights"], os.path.relpath(d, REPO)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
