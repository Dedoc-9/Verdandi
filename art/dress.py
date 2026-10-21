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

import decimal
import hashlib
import json
import math
import os
import re
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BRIEFS = os.path.join(HERE, "briefs")
BUILD = os.path.join(HERE, "build")
sys.path.insert(0, os.path.join(REPO, "graybox"))
import level  # noqa: E402  (the graybox converter: W and C)

FORMAT = "VERDANDI-ART 0"
SCENE = "VERDANDI-ART-SCENE 0"
LINEAGE = "VERDANDI-ART-LINEAGE 0"
# 0226: a scene with movers was played under the graybox's rules 2 (graybox/RULES-2.md), and said so (`rules`); the
# version is the handshake: the plaza plays a scene only under the rules it names, and art/check.py refuses a scene
# whose rules the simulation and its twin (graybox/web/sim.js, graybox/tick_ref.py) do not both implement. 0229: every
# scene names rules 3 (graybox/RULES-3.md), with movers or without, for the reach ceiling below holds only under them:
# a wall is never entered, a target has a top, and nobody stands where rules 1 and 2 let a body walk on the rock
RULES = 3
POLICIES = ("stop", "push")   # a mover's policies under rules 3; push moves along x or z only
QN = 256        # a mover's phase units a metre (RULES-2.md's Q = 1/256 m)
TICKS = 120     # the graybox's ticks a second
AXES = {"+x": [1, 0, 0], "-x": [-1, 0, 0], "+y": [0, 1, 0], "-y": [0, -1, 0], "+z": [0, 0, 1], "-z": [0, 0, -1]}

# the player, as the graybox runtime moves it (graybox/web/sim.js), and the art layer's own two assumptions
PLAYER = {"radius": 0.35, "eye": 1.62, "step": 0.55, "speed": 6.0, "gravity": 20.0, "jump": 7.0}
PLAYER["jump_apex"] = round(PLAYER["jump"] ** 2 / (2 * PLAYER["gravity"]), 4)   # 1.225 m
BODY = 1.80     # the head's height above the feet: the graybox has no head, so the art layer declares one
TARGET = {"radius": 0.4, "height": 1.9}   # a target's column, as graybox/web/sim.js stands it (restated; art/check.py reads sim.js)
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
# THE NUMBER GRAMMAR (0226). A number of the art file is ASCII digits, at most one '.' with digits on both sides, and a
# '-' in front when it is negative: 7, 0.82, -10, 2.5. Nothing else: Python's float() alone took '2_5' as 25, the
# Arabic-Indic digits six and two as 62, '25e-1' and '+2.5' as 2.5, '.5' and '5.' (MEASURED, 0221); each is now refused.
# A whole number (a spacing, a percentage, an 'every') is a number whose value is whole: '3' and '3.0', never '2.7',
# which int() cut to 2 without a word. A colour is three channels 0 to 255 without leading zeros, and a cell two runs of
# ASCII digits: str.isdigit() took '²', which int() then refused with an error the exporter did not catch.
NUMBER = re.compile(r"-?[0-9]+(?:\.[0-9]+)?")
CHANNEL = r"(?:0|[1-9][0-9]{0,2})"


def _num(tok, where, lo, hi, what):
    if not isinstance(tok, str) or not NUMBER.fullmatch(tok):
        raise ArtError("%s: %r is not a number (%s): ASCII digits, at most one '.' between digits, and '-' in front when "
                       "negative; no '+', '_', exponent or other digits" % (where, tok, what))
    v = float(tok)
    if not (lo <= v <= hi):
        raise ArtError("%s: %s %r is outside %s..%s" % (where, what, tok, lo, hi))
    return v


def _whole(tok, where, lo, hi, what):
    _num(tok, where, lo, hi, what)
    f = Fraction(tok)
    if f.denominator != 1:
        raise ArtError("%s: %s %r is not a whole number" % (where, what, tok))
    return int(f)


def _rgb(tok, where):
    if not isinstance(tok, str) or not re.fullmatch("%s,%s,%s" % (CHANNEL, CHANNEL, CHANNEL), tok) or any(int(p) > 255 for p in tok.split(",")):
        raise ArtError("%s: %r is not a colour R,G,B, each 0-255" % (where, tok))
    return [int(p) for p in tok.split(",")]


def _cell(tok, w, h, where):
    if not isinstance(tok, str) or not re.fullmatch(r"[0-9]+,[0-9]+", tok):
        raise ArtError("%s: %r is not a cell x,z" % (where, tok))
    x, z = (int(v) for v in tok.split(","))
    if not (0 <= x < w and 0 <= z < h):
        raise ArtError("%s: the cell %d,%d is outside the %d x %d grid" % (where, x, z, w, h))
    return x, z


RESERVED = ("play", "surface", "material", "env", "asset", "view", "layout", "city")
SINGLE = ("map", "title", "seed", "time", "fog", "exposure", "bloom", "rain", "skyline")


def statement_key(code) -> str:
    """The name a revision uses for a statement: one per brief. The verb alone for a statement that may appear once;
    the verb and its first word for the named ones; a canopy or a building adds its corners, since a region may hold
    several. A bay's first word is the place of the piece it makes (FACADE-0, 0237), so its key names that piece."""
    verb, args = code[0], code[1:]
    if verb in SINGLE:
        return verb
    if verb in ("moon", "sun"):
        return "light"
    if verb in ("canopy", "building") and len(args) >= 5 and is_cell(args[3]) and is_cell(args[4]):
        return "%s %s %s %s" % (verb, args[0], args[3], args[4])
    return "%s %s" % (verb, args[0] if args else "")


def is_cell(tok) -> bool:
    return re.fullmatch(r"[0-9]+,[0-9]+", tok) is not None


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
         "surfaces": {}, "regions": {}, "dressing": [], "views": [], "movers": []}
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
        elif verb == "mover":
            if not args or not re.fullmatch(r"[a-z][a-z0-9-]{0,31}", args[0]):
                raise ArtError("%s: a mover's name is a lowercase letter, then letters, digits or '-' (at most 32)" % where)
            A["movers"].append({"args": args, "where": where, "hash": A["statements"][-1]["hash"]})
        elif verb in ("skyline", "tower", "canopy", "neon", "lamp", "puddle", "building", "bay"):
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


def swept(m):
    """A mover's box over its whole travel (metres): its box at phase 0 stretched along its axis by len/256 m. Exact:
    every number is a whole number of 1/256 m below 2^11."""
    d = m["len"] / float(QN)
    b = list(m["box"])
    for i, a in enumerate(m["axis"]):
        if a > 0:
            b[i + 3] = b[i + 3] + d
        elif a < 0:
            b[i] = b[i] - d
    return b


def mover_top(m):
    """The highest a mover's top rises: its top at phase 0, or at the end of its travel when it travels up."""
    return m["box"][4] + (m["len"] / float(QN) if m["axis"][1] > 0 else 0.0)


def footprint(b, w, h, cell):
    """The cells a box covers in plan with some area (strictly), inside the grid."""
    return [(x, z) for z in range(h) if z * cell < b[5] and (z + 1) * cell > b[2] for x in range(w) if x * cell < b[3] and (x + 1) * cell > b[0]]


# REACH-1's plant (0257), set by art/check.py's reach witness alone: the pair test before 0257, the parabola's
REACH_PLANT = ""


def last_tick(hi, lo, allowance):
    """The last tick n of a jump from feet at hi at whose start the feet, with the allowance, still reach a surface's
    lowest lo (the step, or nothing for a target), or 0 if no tick's do: REACH-1's pair test as the tick plays it (0257).
    The tick (graybox/web/sim.js, and graybox/tick_ref.py's height3) walks before it moves the feet, and lets a body onto
    a surface by the feet it started at, so a body walks n ticks onto a surface it comes onto at tick n; its ground is
    nowhere below 0, so the flight ends at the first tick whose feet are at or below 0. The tick's own arithmetic,
    operation for operation: the jump at tick 1, then vy = vy - gravity * TICK and feet = feet + vy * TICK; and its own
    test, lo <= feet + allowance (a top within a step of the feet), never lo - allowance <= feet, which can round apart
    from it near equality. It ends: vy falls by gravity * TICK each tick, so past the apex the feet fall below the
    surface, or below 0, and while vy is no longer positive no later tick's feet are higher."""
    tick = 1.0 / TICKS
    feet, vy, n, last = hi, 0.0, 0, 0
    while True:
        n += 1
        if lo <= feet + allowance:
            last = n
        elif n > 1 and vy <= 0.0:
            return last
        if n == 1:
            vy = PLAYER["jump"]
        vy = vy - PLAYER["gravity"] * tick
        feet = feet + vy * tick
        if feet <= 0.0:
            return last


def reach_ceiling(W, C, movers=()):
    """For every cell, the height dressing above it must clear: the highest a player's head can rise over it, under
    the graybox's rules 3 (graybox/RULES-3.md), by REACH-1 (0229, 0257; art/README.md). Before 0229 a climb was the
    jump's apex alone and only to a neighbouring cell: the simulation climbs its apex and a step (1.745833 m: the tick's
    own apex, 1.195833 m, below the parabola's 1.225), crosses gaps, and stands on targets, and that model was below it.

    Surfaces a player may stand on: every open cell's top (a cell as high as the wall is rock, which rules 3 never let a
    body enter); every mover's top, over its whole travel in plan, from its lowest to its highest; every target's top
    (rules 3), over its column. From a surface s a player reaches a surface s2 when a jump from s's highest, played tick
    by tick as the graybox plays it (last_tick), still has s2's lowest within the step of the feet at some tick n's
    start (within nothing, for a target, which holds a body below its top), before the flight ends at the floor, and
    the gap between them is at most 2 radius + n ticks of walking. An exact tie (the gap equal to that in the reals)
    counts as reached: the tick's own verdict there turns on the binary64 rounding of where it starts and of its summed
    steps (on the 1/256 m grid it landed at 7,783 of 8,126 ties and not at 343, MEASURED 2026-10-21), so the test is the
    tick's but at a tie, where it counts more. What it is to certify (his ruling, 2026-10-21) is a sound envelope:
    every surface the tick can bring a body onto is counted, never exact attainability; off an axis, where a gap is an
    irrational distance, rounding at the boundary is not yet shown unable to leave one out, nor a mover's push of a
    body in flight unable to carry it past its walk. Before 0257 the test was the parabola's, t = (jump + sqrt(jump^2
    - 2 gravity need)) / gravity, which missed the tick a body walks before its feet are tested (a box 6.3984375 m off
    a platform's edge: the tick lands on it, and the parabola refused it). Nothing in between is asked to be open, which
    can only add surfaces. The standable surfaces are those reached so from the spawns' cells.

    The head over a cell: from each standable surface, the body flies the gap to the cell less two radii (its own
    circle at both ends) at the walking speed; within the rise the feet are at the surface's highest plus the apex, after
    it falling, and a fall below 0 is not counted (the body lands first, on a surface counted itself). The cell's ceiling
    is the highest head plus the margin; with no surface in range, an open cell's own top plus the body and the apex
    (as before), a rock cell none."""
    w, h, wall, tops, cell = C["w"], C["h"], W["wall"], C["tops"], C["cell"]
    P = PLAYER
    r, step, speed, g, v = P["radius"], P["step"], P["speed"], P["gravity"], P["jump"]
    apex, rise = P["jump_apex"], v / g
    # (lo, hi, x0, z0, x1, z1, allowance, the cell it is, if it is one)
    surf = []
    for z in range(h):
        for x in range(w):
            t = tops[z * w + x]
            if t < wall:
                surf.append((t, t, x * cell, z * cell, (x + 1) * cell, (z + 1) * cell, step, (x, z)))
    for m in movers:
        b, d = swept(m), m["len"] / float(QN)
        lo = m["box"][4] - (d if m["axis"][1] < 0 else 0.0)
        surf.append((lo, mover_top(m), b[0], b[2], b[3], b[5], step, None))
    for t in W["targets"]:
        # where the scene says it stands (to 0.1 mm), so that art/check.py, which reads the scene, counts the same top
        cx, cz, ty = r4((t["x"] + 0.5) * cell), r4((t["z"] + 0.5) * cell), r4(tops[t["z"] * w + t["x"]])
        top = ty + TARGET["height"]
        surf.append((top, top, cx - TARGET["radius"], cz - TARGET["radius"], cx + TARGET["radius"], cz + TARGET["radius"], 0.0, None))

    def gap(a, b):
        dx = max(0.0, a[2] - b[4], b[2] - a[4])
        dz = max(0.0, a[3] - b[5], b[3] - a[5])
        return math.sqrt(dx * dx + dz * dz)   # correctly rounded on every machine, as pow is not

    index = {s[7]: k for k, s in enumerate(surf) if s[7] is not None}
    todo = sorted({index[(sp["x"], sp["z"])] for sp in W["spawns"].values() if (sp["x"], sp["z"]) in index})
    ok = set(todo)
    ticks = {}   # this call's own: each (s's highest, s2's lowest, its allowance) played once
    while todo:
        k = todo.pop()
        a = surf[k]
        for j, b in enumerate(surf):
            if j in ok:
                continue
            if REACH_PLANT == "pair-parabola":
                need = b[0] - b[6] - a[1]
                if need > apex:
                    continue
                far = 2.0 * r + speed * ((v + math.sqrt(v * v - 2.0 * g * need)) / g)
            else:
                key = (a[1], b[0], b[6])
                n = ticks.get(key)
                if n is None:
                    n = ticks[key] = last_tick(*key)
                if not n:
                    continue
                far = 2.0 * r + n * (speed * (1.0 / TICKS))
            if gap(a, b) <= far:
                ok.add(j)
                todo.append(j)
    standable = {surf[k][7] for k in ok if surf[k][7] is not None}
    best = [None] * (w * h)
    for k in sorted(ok):
        a = surf[k]
        # beyond far the feet would be below 0; a cell more either way, so that no rounding decides what is looked at
        far = 2.0 * r + speed * (v + math.sqrt(v * v + 2.0 * g * max(0.0, a[1]))) / g + cell
        for z in range(max(0, int((a[3] - far) // cell)), min(h, int((a[5] + far) // cell) + 1)):
            for x in range(max(0, int((a[2] - far) // cell)), min(w, int((a[4] + far) // cell) + 1)):
                t = max(0.0, gap(a, (0, 0, x * cell, z * cell, (x + 1) * cell, (z + 1) * cell)) - 2.0 * r) / speed
                if t <= rise:
                    head = a[1] + apex + BODY
                else:
                    up = v * t - 0.5 * g * t * t
                    if a[1] + up < 0:
                        continue
                    head = a[1] + up + BODY
                if best[z * w + x] is None or head > best[z * w + x]:
                    best[z * w + x] = head
    reach = []
    for k, hd in enumerate(best):
        if hd is None:
            tt = tops[k]
            reach.append(r4(tt + BODY + apex + MARGIN) if tt < wall else None)
        else:
            reach.append(r4(hd + MARGIN))
    return reach, standable


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


def _options(toks, where, arity):
    """Named options after a statement's fixed words: each a name and its values, each name once."""
    out, i = {}, 0
    while i < len(toks):
        name = toks[i]
        if name not in arity:
            raise ArtError("%s: %r is not an option here (the options are %s)" % (where, name, ", ".join(sorted(arity))))
        if name in out:
            raise ArtError("%s: the option %s is given twice" % (where, name))
        vals = toks[i + 1:i + 1 + arity[name]]
        if len(vals) != arity[name]:
            raise ArtError("%s: the option %s takes %d value(s)" % (where, name, arity[name]))
        out[name] = vals
        i += 1 + arity[name]
    return out


def _masses(cells, cx, cz, lo, hi):
    """Rock cells joined into masses: rows of cells, rows of equal span stacked, each mass cut into at most five
    segments along its length, and each segment's height stepped by 2 m from the highest at the middle of its side of
    the region to the lowest at the ends. A massing that reads as a few large forms, highest at the centre of each
    side, where the per-cell prisms read as a comb. ([x0, z0, x1, z1], top) in a fixed order."""
    have = set(cells)
    rows = []
    for z in sorted({c[1] for c in cells}):
        xs = sorted(x for x, zz in cells if zz == z)
        i = 0
        while i < len(xs):
            j = i
            while j + 1 < len(xs) and xs[j + 1] == xs[j] + 1:
                j += 1
            rows.append([xs[i], z, xs[j], z])
            i = j + 1
    rects = []
    for r in rows:
        for q in rects:
            if q[0] == r[0] and q[2] == r[2] and q[3] == r[1] - 1:
                q[3] = r[1]
                break
        else:
            rects.append(list(r))
    segs = []
    for x0, z0, x1, z1 in rects:
        along_x = (x1 - x0) >= (z1 - z0)
        n0, n1 = (x0, x1) if along_x else (z0, z1)
        length = n1 - n0 + 1
        k = max(1, min(5, round(length / 3)))
        centre = cx if along_x else cz
        for s in range(k):
            a = n0 + length * s // k
            b = n0 + length * (s + 1) // k - 1
            segs.append(([a, z0, b, z1] if along_x else [x0, a, x1, b], abs((a + b + 1) / 2.0 - centre)))
    # the segment nearest the middle of its side is the highest, the farthest the lowest
    dmin, dmax = min(d for _r, d in segs), max(d for _r, d in segs)
    out = []
    for rect, d in segs:
        t = (d - dmin) / (dmax - dmin) if dmax > dmin else 0.0
        out.append((rect, r4(lo + 2 * int(((hi - lo) * (1 - t)) // 2))))
    assert all((x, z) in have for (x0, z0, x1, z1), _t in out for x in range(x0, x1 + 1) for z in range(z0, z1 + 1))
    return out


def _dec(f) -> str:
    """A whole number of 1/256 m, written exactly in decimal."""
    with decimal.localcontext() as ctx:
        ctx.prec = 40
        t = format(decimal.Decimal(f.numerator) / decimal.Decimal(f.denominator), "f")
    return t.rstrip("0").rstrip(".") if "." in t else t


def _qnum(tok, where, what, lo=-1024, hi=1024):
    """A number of the grammar that is a whole number of 1/256 m (RULES-2.md's integer semantics), as a Fraction."""
    _num(tok, where, lo, hi, what)
    f = Fraction(tok)
    if (f * QN).denominator != 1:
        a = Fraction(int((f * QN) // 1), QN)
        raise ArtError("%s: %s %r is not a whole number of 1/256 m (a mover's unit, graybox/RULES-2.md): the nearest are %s and %s"
                       % (where, what, tok, _dec(a), _dec(a + Fraction(1, QN))))
    return f


def _movers(A, W, C):
    """The art file's movers (0226), as rules 2 have them: each statement read, held to rules 2's own table (the twin's
    Mover, graybox/tick_ref.py: a box of whole 1/256 m below 1,024 m, an axis, len and speed whole, the tunnelling
    bound), and its travel held to the world: inside the grid, above every cell it crosses, clear of every spawn's
    column, of every target's column and of every other mover's travel. Refused, with its line, otherwise.

        mover NAME MATERIAL X0,Y0,Z0 X1,Y1,Z1 along AXIS travel METRES speed METRES-A-SECOND [policy stop|push]

    Two opposite corners (metres; x east, y up, z south); AXIS one of +x -x +y -y +z -z; it goes out by `travel` metres
    and back, again and again, at `speed` metres a second, which must be a whole number of 1/256 m a tick (a multiple of
    0.46875 m/s; 0 parks it, a static box). It carries a player who stands on it (RULES-2.md). Its policy (0229, rules 3,
    RULES-3.md) says what it does with a player in its way: stop (the default) holds it still; push, along x or z only,
    moves the player with it, and holds it still only when the player cannot go."""
    if not A["movers"]:
        return []
    import tick_ref   # the rules' second implementation: its Mover is rules 2's table of what a mover may be
    w, h, cell, tops = C["w"], C["h"], C["cell"], C["tops"]
    out, ids = [], set()
    for d in A["movers"]:
        args, where = d["args"], d["where"]
        if len(args) < 4:
            raise ArtError("%s: mover takes a name, a material, two corners X,Y,Z and 'along AXIS travel METRES speed M/S'" % where)
        name = args[0]
        if args[1] not in A["materials"]:
            raise ArtError("%s: no material %s" % (where, args[1]))
        corners = []
        for c in args[2:4]:
            parts = c.split(",")
            if len(parts) != 3:
                raise ArtError("%s: %r is not a corner X,Y,Z" % (where, c))
            corners.append([_qnum(v, where, "a corner's coordinate", -1023, 1023) for v in parts])
        lo = [min(corners[0][i], corners[1][i]) for i in range(3)]
        hi = [max(corners[0][i], corners[1][i]) for i in range(3)]
        if any(lo[i] == hi[i] for i in range(3)):
            raise ArtError("%s: the mover %s has no extent along %s" % (where, name, "xyz"[[lo[i] == hi[i] for i in range(3)].index(True)]))
        opts = _options(args[4:], where, {"along": 1, "travel": 1, "speed": 1, "policy": 1})
        miss = [k for k in ("along", "travel", "speed") if k not in opts]
        if miss:
            raise ArtError("%s: the mover %s needs %s" % (where, name, ", ".join(miss)))
        if opts["along"][0] not in AXES:
            raise ArtError("%s: along takes one of %s" % (where, " ".join(AXES)))
        travel = _qnum(opts["travel"][0], where, "travel", 0, 1024)
        if travel <= 0:
            raise ArtError("%s: the mover %s travels no distance (a static box is speed 0, with any travel)" % (where, name))
        _num(opts["speed"][0], where, 0, 1000, "speed")
        sp = Fraction(opts["speed"][0]) * QN / TICKS
        if sp.denominator != 1:
            k = int(sp // 1)
            raise ArtError("%s: speed %s m/s is not a whole number of 1/256 m a tick (a multiple of 0.46875 m/s): the nearest are %s and %s m/s"
                           % (where, opts["speed"][0], _dec(Fraction(k * TICKS, QN)), _dec(Fraction((k + 1) * TICKS, QN))))
        policy = opts["policy"][0] if "policy" in opts else "stop"
        if policy not in POLICIES:
            raise ArtError("%s: policy takes one of %s" % (where, " ".join(POLICIES)))
        if policy == "push" and AXES[opts["along"][0]][1] != 0:
            raise ArtError("%s: the mover %s pushes along y: rules 3 push along x or z only (along y a mover in a player's way "
                           "holds still, as stop does), so say policy stop" % (where, name))
        m = {"id": name, "by": d["hash"], "material": args[1], "box": [float(v) for v in lo + hi], "axis": list(AXES[opts["along"][0]]),
             "len": int(travel * QN), "speed": int(sp), "policy": policy}
        try:
            tick_ref.Mover({k: m[k] for k in ("id", "box", "axis", "len", "speed", "policy")}, ids, POLICIES)
        except tick_ref.MoverRefused as e:
            raise ArtError("%s: %s" % (where, e))
        ids.add(name)
        b = swept(m)
        if b[0] < 0 or b[2] < 0 or b[3] > w * cell or b[5] > h * cell or b[1] < 0 or b[4] >= 1024:
            raise ArtError("%s: the mover %s's travel (%s) leaves the world (x 0..%s, z 0..%s, y 0 up to 1,024)" % (
                where, name, ", ".join(_dec(Fraction(v)) for v in b), r4(w * cell), r4(h * cell)))
        for x, z in footprint(b, w, h, cell):
            if tops[z * w + x] > b[1]:
                raise ArtError("%s: the mover %s's travel meets the solid of cell %d,%d (its top %s m, above the mover's bottom "
                               "%s m): a mover rides above the cells it crosses" % (where, name, x, z, tops[z * w + x], _dec(Fraction(b[1]))))
        for k, sp_ in sorted(W["spawns"].items()):
            sx, sz, sy = (sp_["x"] + 0.5) * cell, (sp_["z"] + 0.5) * cell, tops[sp_["z"] * w + sp_["x"]]
            px, pz = max(b[0], min(sx, b[3])), max(b[2], min(sz, b[5]))
            if (sx - px) ** 2 + (sz - pz) ** 2 < PLAYER["radius"] ** 2 and b[4] > sy and b[1] < sy + BODY:
                raise ArtError("%s: the mover %s's travel crosses spawn %s's column (a player appears there)" % (where, name, k))
        for t in W["targets"]:
            tx, tz, ty = (t["x"] + 0.5) * cell, (t["z"] + 0.5) * cell, tops[t["z"] * w + t["x"]]
            px, pz = max(b[0], min(tx, b[3])), max(b[2], min(tz, b[5]))
            if (tx - px) ** 2 + (tz - pz) ** 2 < TARGET["radius"] ** 2 and b[4] > ty and b[1] < ty + TARGET["height"]:
                raise ArtError("%s: the mover %s's travel crosses target %s's column (the rules do not move targets: the box would pass through it)"
                               % (where, name, t["id"]))
        for o in out:
            ob = swept(o)
            if all(b[i] < ob[i + 3] and ob[i] < b[i + 3] for i in range(3)):
                raise ArtError("%s: the mover %s's travel crosses the mover %s's" % (where, name, o["id"]))
        out.append(m)
    return out


# FACADE-0 (0237): a building's facade. Each bay of each floor of each side that looks onto open cells is one piece, a window
# set in the bay or a panel filling it, standing out from the face by a few centimetres: thinner than FLUSH, so that it
# is flush on a rock face wherever a player can be, and art/check.py holds it there like any other piece. No opening,
# no mesh, no depth: the building's mass is a box on rock, and its facade is a grid of thin boxes on that box's faces.
ELEMENTS = ("window", "panel", "blank")
STOREY = 4.0                     # a floor's height when the building does not say (the graybox's wall height)
WINDOW = (0.35, 0.9, 0.45, 0.05)  # inset at each side of the bay, sill above the floor, head below the next, how far it stands out
PANEL = (0.03, 0.03, 0.03, 0.04)  # the joints round a panel, and how far it stands out
BAY = re.compile(r"(0|[1-9][0-9]*),(0|[1-9][0-9]*)-(0|[1-9][0-9]*),(0|[1-9][0-9]*):([nsew])-b(0|[1-9][0-9]*)-f(0|[1-9][0-9]*)")
assert max(WINDOW[3], PANEL[3]) < FLUSH


def _bay(d, A):
    """A bay statement read for form: bay PLACE window|panel [MATERIAL] | bay PLACE blank. Its place is the piece it
    makes, building:PLACE; whether a building has that bay is decided where the buildings are made."""
    args, where = d["args"], d["where"]
    if len(args) not in (2, 3) or not BAY.fullmatch(args[0]):
        raise ArtError("%s: bay takes a place x0,z0-x1,z1:SIDE-bK-fN (a building's corners, its side n, s, e or w, the bay "
                       "and the floor, whole numbers without leading zeros), an element (%s) and, but for blank, optionally "
                       "a material" % (where, ", ".join(ELEMENTS)))
    if args[1] not in ELEMENTS:
        raise ArtError("%s: %r is not an element of a bay (%s)" % (where, args[1], ", ".join(ELEMENTS)))
    if args[1] == "blank" and len(args) == 3:
        raise ArtError("%s: a blank bay has no element, so no material" % where)
    if len(args) == 3 and args[2] not in A["materials"]:
        raise ArtError("%s: no material %s" % (where, args[2]))
    return {"place": args[0], "element": args[1], "material": args[2] if len(args) == 3 else None, "by": d["hash"], "where": where}


def _facade(side, element, a, b, y0, y1, face):
    """The box of one bay's element: along the face from a to b, from the floor y0 to the next y1, on the face's plane."""
    i, lo, hi, d = WINDOW if element == "window" else PANEL
    a, b, y0, y1 = a + i, b - i, y0 + lo, y1 - hi
    if side == "s":
        return a, y0, face, b, y1, face + d
    if side == "n":
        return a, y0, face - d, b, y1, face
    if side == "e":
        return face, y0, a, face + d, y1, b
    return face - d, y0, a, face, y1, b


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
    movers = _movers(A, W, C)
    reach, standable = reach_ceiling(W, C, movers)
    seed = A["seed"]
    visuals, lights = [], []

    def material(name, where):
        if name not in A["materials"]:
            raise ArtError("%s: no material %s" % (where, name))
        return name

    def box(x0, y0, z0, x1, y1, z1):
        return [r4(x0), r4(y0), r4(z0), r4(x1), r4(y1), r4(z1)]

    # FACADE-0 (0237): the bay statements, by the place of the piece each makes; each is used where its building is made, and
    # one no building has is refused below
    bays = {}
    for d in A["dressing"]:
        if d["verb"] == "bay":
            b_ = _bay(d, A)
            bays[b_["place"]] = b_
    buildings = {}      # (x0, z0, x1, z1) -> {where, sides: {side: (bays, floors)}}
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
            if len(args) not in (4, 5) or (len(args) == 5 and args[4] != "mass"):
                raise ArtError("%s: tower takes a region, a material, a lowest and highest height, and optionally 'mass'" % where)
            x0, z0, x1, z1 = _region(A, args[0], w, h, where)
            mat = material(args[1], where)
            lo, hi = _num(args[2], where, wall, 400, "height"), _num(args[3], where, wall, 400, "height")
            cells = []
            for z in range(max(0, z0 - 1), min(h, z1 + 2)):
                for x in range(max(0, x0 - 1), min(w, x1 + 2)):
                    # a rock cell that borders the region's floor
                    if rock(x, z) and any(x0 <= a <= x1 and z0 <= b <= z1 and walk(a, b) for a in (x - 1, x, x + 1) for b in (z - 1, z, z + 1)):
                        cells.append((x, z))
            if len(args) == 4:
                # one prism a cell, each its own height: the first massing, which reads as a comb
                for x, z in cells:
                    steps = int(hi - lo)
                    top = lo + (pick(key(x, z)) % (steps + 1) if steps > 0 else 0)
                    visuals.append({"id": "tower:%d,%d" % (x, z), "by": sh, "region": args[0], "asset": "cube", "material": mat,
                                    "box": box(x * cell, wall, z * cell, (x + 1) * cell, top, (z + 1) * cell)})
            else:
                for (rx0, rz0, rx1, rz1), top in _masses(cells, (x0 + x1 + 1) / 2.0, (z0 + z1 + 1) / 2.0, lo, hi):
                    rid = "tower:%d,%d-%d,%d" % (rx0, rz0, rx1, rz1)
                    bx0, bz0, bx1, bz1 = rx0 * cell, rz0 * cell, (rx1 + 1) * cell, (rz1 + 1) * cell
                    visuals.append({"id": rid, "by": sh, "region": args[0], "asset": "cube", "material": mat,
                                    "box": box(bx0, wall, bz0, bx1, top, bz1)})
                    if top - wall >= 8:
                        # a cornice: the mass's last metre thrown out by 0.6 m, high above every head
                        visuals.append({"id": rid + ":cap", "by": sh, "region": args[0], "asset": "cube", "material": mat,
                                        "box": box(bx0 - 0.6, top - 1.0, bz0 - 0.6, bx1 + 0.6, top + 0.4, bz1 + 0.6)})
        elif verb == "canopy":
            if len(args) < 3:
                raise ArtError("%s: canopy takes a region, a material, a height, optionally two corners inside it, and options" % where)
            x0, z0, x1, z1 = _region(A, args[0], w, h, where)
            rx, rz = (x0 + x1 + 1) / 2.0, (z0 + z1 + 1) / 2.0
            rest = args[3:]
            if len(rest) >= 2 and is_cell(rest[0]) and is_cell(rest[1]):
                a, b = _cell(rest[0], w, h, where), _cell(rest[1], w, h, where)
                sx0, sz0, sx1, sz1 = min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])
                if not (x0 <= sx0 and sx1 <= x1 and z0 <= sz0 and sz1 <= z1):
                    raise ArtError("%s: the canopy's corners leave its region %s" % (where, args[0]))
                x0, z0, x1, z1 = sx0, sz0, sx1, sz1
                rest = rest[2:]
            mat = material(args[1], where)
            y = _num(args[2], where, 0.5, 200, "height")
            opts = _options(rest, where, {"deep": 1, "ribs": 1, "lit": 2, "edgelit": 2})
            deep = _num(opts["deep"][0], where, 0.2, 4.0, "depth") if "deep" in opts else 0.4
            cid = "canopy:%d,%d-%d,%d" % (x0, z0, x1, z1)
            visuals.append({"id": cid, "by": sh, "region": args[0], "asset": "cube", "material": mat,
                            "box": box(x0 * cell, y, z0 * cell, (x1 + 1) * cell, y + deep, (z1 + 1) * cell)})
            # the slab's long axis; ribs cross it and downlights run along its middle
            along_x = (x1 - x0) >= (z1 - z0)
            n0, n1 = (x0, x1) if along_x else (z0, z1)
            if "ribs" in opts:
                every = _whole(opts["ribs"][0], where, 1, 12, "rib spacing")
                for k in range(n0, n1 + 2, every):
                    c = k * cell
                    rb = box(max(c - 0.25, x0 * cell), y - 0.8, z0 * cell, min(c + 0.25, (x1 + 1) * cell), y, (z1 + 1) * cell) if along_x else \
                        box(x0 * cell, y - 0.8, max(c - 0.25, z0 * cell), (x1 + 1) * cell, y, min(c + 0.25, (z1 + 1) * cell))
                    visuals.append({"id": "%s:rib%d" % (cid, k), "by": sh, "region": args[0], "asset": "cube", "material": mat, "box": rb})
            if "lit" in opts:
                col = _rgb(opts["lit"][0], where)
                cd = _num(opts["lit"][1], where, 0, 100000, "candelas")
                if "housing" not in A["materials"]:
                    raise ArtError("%s: a downlight sits in a housing: declare the material 'housing'" % where)
                mid = ((z0 + z1 + 1) / 2.0 if along_x else (x0 + x1 + 1) / 2.0) * cell
                for k in range(n0, n1 + 1):
                    if (k - n0) % 2:
                        continue
                    c = (k + 0.5) * cell
                    px, pz = (c, mid) if along_x else (mid, c)
                    vid = "%s:light%d" % (cid, k)
                    visuals.append({"id": vid, "by": sh, "region": args[0], "asset": "cube", "material": "housing",
                                    "box": box(px - 0.3, y - 0.1, pz - 0.3, px + 0.3, y, pz + 0.3)})
                    lights.append({"id": vid, "by": sh, "region": args[0], "type": "point", "pos": [r4(px), r4(y - 0.15), r4(pz)],
                                   "dir": [0, -1, 0], "color": col, "candela": r4(cd), "radius": r4(cell * 7)})
            if "edgelit" in opts:
                # a narrow row of small fixtures along the edge that faces the region's middle, set back from it, one a
                # metre, each with its light; the rest of the underside is left dark
                col = _rgb(opts["edgelit"][0], where)
                cd = _num(opts["edgelit"][1], where, 0, 100000, "candelas")
                if "housing" not in A["materials"]:
                    raise ArtError("%s: an edge light sits in a housing: declare the material 'housing'" % where)
                if along_x:
                    toward = 1 if rz >= (z0 + z1 + 1) / 2.0 else -1
                    edge = ((z1 + 1) if toward > 0 else z0) * cell - toward * 0.35
                else:
                    toward = 1 if rx >= (x0 + x1 + 1) / 2.0 else -1
                    edge = ((x1 + 1) if toward > 0 else x0) * cell - toward * 0.35
                for j in range(int(round((n1 - n0 + 1) * cell))):
                    c = n0 * cell + 0.5 + j
                    px, pz = (c, edge) if along_x else (edge, c)
                    hx, hz = (0.25, 0.09) if along_x else (0.09, 0.25)
                    vid = "%s:light-edge%d" % (cid, j)
                    visuals.append({"id": vid, "by": sh, "region": args[0], "asset": "cube", "material": "housing",
                                    "box": box(px - hx, y - 0.06, pz - hz, px + hx, y, pz + hz)})
                    lights.append({"id": vid, "by": sh, "region": args[0], "type": "point", "pos": [r4(px), r4(y - 0.1), r4(pz)],
                                   "dir": [0, -1, 0], "color": col, "candela": r4(cd), "radius": r4(cell * 4)})
        elif verb == "neon":
            if len(args) != 4:
                raise ArtError("%s: neon takes a region, an emissive material, a height and 'every N' faces" % where)
            x0, z0, x1, z1 = _region(A, args[0], w, h, where)
            mat = material(args[1], where)
            if A["materials"][mat]["emissive_strength"] <= 0:
                raise ArtError("%s: the neon's material %s does not emit" % (where, mat))
            y = _num(args[2], where, 0.3, wall - 0.2, "height")
            every = _whole(args[3], where, 1, 64, "every")
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
            sp = _whole(args[3], where, 1, 48, "spacing")
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
            pct = _whole(args[2], where, 0, 100, "percentage")
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
        elif verb == "building":
            if len(args) < 5 or not (is_cell(args[3]) and is_cell(args[4])):
                raise ArtError("%s: building takes a region, a material, a height, two corner cells and options (face ELEMENT "
                               "MATERIAL, storey METRES, bay CELLS)" % where)
            gx0, gz0, gx1, gz1 = _region(A, args[0], w, h, where)
            mat = material(args[1], where)
            top = _num(args[2], where, wall + 1, 400, "height")
            a, b = _cell(args[3], w, h, where), _cell(args[4], w, h, where)
            x0, z0, x1, z1 = min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])
            soft = [(x, z) for z in range(z0, z1 + 1) for x in range(x0, x1 + 1) if not rock(x, z)]
            if soft:
                raise ArtError("%s: a building stands on rock, and the cell %d,%d is not" % ((where,) + soft[0]))
            ring = [(x, z0 - 1) for x in range(x0, x1 + 1)] + [(x, z1 + 1) for x in range(x0, x1 + 1)] + \
                   [(x0 - 1, z) for z in range(z0, z1 + 1)] + [(x1 + 1, z) for z in range(z0, z1 + 1)]
            if not any(gx0 <= x <= gx1 and gz0 <= z <= gz1 for x, z in ring):
                raise ArtError("%s: the building at %d,%d-%d,%d borders no cell of its region %s" % (where, x0, z0, x1, z1, args[0]))
            for (ox0, oz0, ox1, oz1), o in buildings.items():
                if x0 <= ox1 and ox0 <= x1 and z0 <= oz1 and oz0 <= z1:
                    raise ArtError("%s: the building at %d,%d-%d,%d shares cells with the building of %s" % (where, x0, z0, x1, z1, o["where"]))
            opts = _options(args[5:], where, {"face": 2, "storey": 1, "bay": 1})
            storey = Fraction(STOREY)
            if "storey" in opts:
                _num(opts["storey"][0], where, 2.5, 8, "storey height")
                storey = Fraction(opts["storey"][0])
            every = _whole(opts["bay"][0], where, 1, 8, "bay width in cells") if "bay" in opts else 1
            face = None
            if "face" in opts:
                if opts["face"][0] not in ("window", "panel"):
                    raise ArtError("%s: a building's face is window or panel, and a material" % where)
                face = (opts["face"][0], material(opts["face"][1], where))
            floors = int(Fraction(args[2]) // storey)
            info = buildings[(x0, z0, x1, z1)] = {"where": where, "sides": {}}
            bid = "building:%d,%d-%d,%d" % (x0, z0, x1, z1)
            visuals.append({"id": bid, "by": sh, "region": args[0], "asset": "cube", "material": mat,
                            "box": box(x0 * cell, wall, z0 * cell, (x1 + 1) * cell, top, (z1 + 1) * cell)})
            # the sides, each with its bays counted from its west or north end; a bay is drawn only where every cell in
            # front of it is open (a bay against rock would be inside it)
            for side, (n0, n1), front, plane in (("n", (x0, x1), lambda c: (c, z0 - 1), z0 * cell), ("s", (x0, x1), lambda c: (c, z1 + 1), (z1 + 1) * cell),
                                                 ("w", (z0, z1), lambda c: (x0 - 1, c), x0 * cell), ("e", (z0, z1), lambda c: (x1 + 1, c), (x1 + 1) * cell)):
                spans = [(c, min(n1, c + every - 1)) for c in range(n0, n1 + 1, every)]
                for k, (c0, c1) in enumerate(spans):
                    if not all(walk(*front(c)) for c in range(c0, c1 + 1)):
                        continue
                    info["sides"].setdefault(side, [[], floors])[0].append(k)
                    for f in range(floors):
                        place = "%d,%d-%d,%d:%s-b%d-f%d" % (x0, z0, x1, z1, side, k, f)
                        o = bays.pop(place, None)
                        if face is None and o is None:
                            continue
                        if face is None:
                            raise ArtError("%s: the building of %s has no face, so no bay to change: give it face ELEMENT MATERIAL" % (o["where"], where))
                        element, emat, by = (o["element"], o["material"] or face[1], o["by"]) if o else (face[0], face[1], sh)
                        if element == "blank":
                            continue
                        visuals.append({"id": "building:" + place, "by": by, "region": args[0], "asset": "cube", "material": emat,
                                        "box": box(*_facade(side, element, c0 * cell, (c1 + 1) * cell, float(f * storey), float((f + 1) * storey), plane))})
    # FACADE-0: a bay no building has is refused, with what the building it names does have
    for o in sorted(bays.values(), key=lambda o: int(o["where"].rsplit(" ", 1)[1])):
        m = BAY.fullmatch(o["place"])
        info = buildings.get(tuple(int(m.group(i)) for i in (1, 2, 3, 4)))
        if info is None:
            raise ArtError("%s: no building has the corners %s" % (o["where"], o["place"].split(":")[0]))
        have = "; ".join("%s: bays %s, floors 0-%d" % (sd, ",".join("b%d" % k for k in ks), fl - 1) for sd, (ks, fl) in sorted(info["sides"].items())) or "none"
        raise ArtError("%s: the building of %s has no bay %s (a bay is a side's run of cells that looks onto open cells, on a "
                       "floor below its height; it has %s)" % (o["where"], info["where"], o["place"].split(":")[1], have))
    # dressing in a mover's path would be cut by it as it passes: only a piece flat on the floor may lie under one
    for v in visuals:
        b = v["box"]
        for m in movers:
            mb = swept(m)
            if all(b[i] < mb[i + 3] and mb[i] < b[i + 3] for i in range(3)):
                flat = all(b[4] <= tops[z * w + x] + FLAT for x, z in footprint(b, w, h, cell))
                if not flat:
                    line = {s["hash"]: s["line"] for s in A["statements"]}
                    raise ArtError("%s: %s (from line %d) stands in the path of the mover %s (line %d)" % (
                        A["file"], v["id"], line.get(v["by"], 0), m["id"], line.get(m["by"], 0)))
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
    # 0229: every scene names the rules it is played under, rules 3, and its targets (whose tops the reach ceiling
    # counts); a scene carries movers when it has any
    scene["rules"] = RULES
    scene["targets"] = {t["id"]: {"x": r4((t["x"] + 0.5) * cell), "z": r4((t["z"] + 0.5) * cell), "y": r4(tops[t["z"] * w + t["x"]])}
                        for t in sorted(W["targets"], key=lambda t: t["id"])}
    if movers:
        scene["movers"] = movers
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
        "counts": dict({"collision": len(collision), "visuals": len(visuals), "lights": len(lights)}, **({"movers": len(movers)} if movers else {})),
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
        if kind in ("skyline", "tower", "building"):
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
    for m in S.get("movers", []):
        b, a = swept(m), m["box"]
        parts.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="none" stroke="#f0c040" stroke-width="1.2" stroke-dasharray="3 2"/>'
                     % (b[0] * sc, b[2] * sc, (b[3] - b[0]) * sc, (b[5] - b[2]) * sc))
        parts.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="#f0c040" fill-opacity="0.55"/><text x="%.2f" y="%.2f" fill="#fff" font-size="9">%s</text>'
                     % (a[0] * sc, a[2] * sc, (a[3] - a[0]) * sc, (a[5] - a[2]) * sc, a[0] * sc + 2, a[2] * sc - 2, m["id"]))
    for L in S["lights"]:
        if L["type"] == "point":
            parts.append('<circle cx="%.2f" cy="%.2f" r="5" fill="%s" fill-opacity="0.35"/><circle cx="%.2f" cy="%.2f" r="1.6" fill="%s"/>'
                         % (L["pos"][0] * sc, L["pos"][2] * sc, hexc(L["color"]), L["pos"][0] * sc, L["pos"][2] * sc, hexc(L["color"])))
    for k, sp in S["spawns"].items():
        parts.append('<circle cx="%.2f" cy="%.2f" r="5" fill="none" stroke="%s" stroke-width="2"/><text x="%.2f" y="%.2f" fill="#fff" font-size="9" text-anchor="middle">%s</text>'
                     % (sp["x"] * sc, sp["z"] * sc, "#ffb347" if k == "A" else "#47d1ff", sp["x"] * sc, sp["z"] * sc + 3, k))
    parts.append('<text x="8" y="%d" fill="#cfd6dd" font-size="12">%s — %d play boxes, %d dressing pieces, %d lights%s</text>'
                 % (h * px + 16, (S["title"] or S["name"]).replace("&", "&amp;").replace("<", "&lt;"), len(S["collision"]), len(S["visuals"]), len(S["lights"]),
                    (", %d movers (dashed: where each travels)" % len(S["movers"])) if S.get("movers") else ""))
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
        print("%s  scene %s  (%d play boxes, %d dressing pieces, %d lights%s)  ->  %s"
              % (name, L["scene_sha256"][:16], L["counts"]["collision"], L["counts"]["visuals"], L["counts"]["lights"],
                 (", %d movers, rules %d" % (L["counts"]["movers"], RULES)) if L["counts"].get("movers") else "", os.path.relpath(d, REPO)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
