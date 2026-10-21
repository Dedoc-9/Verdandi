# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/check.py — ART-GENERATION-0's checks: the art may be bold because it cannot touch play.
#
#   python art/check.py [NAME ...]          every brief in art/briefs/ when no name is given
#
# For each brief: exports the scene twice (the same bytes), then an independent verifier holds the scene to the
# graybox world it dresses, with its own reader and its own arithmetic:
#
#   play      the graybox map's own checks pass on W and C (walls, probes, routes, spawns)
#   collision the scene's collision boxes, laid back onto the grid, are C exactly; the ground is there; no box overlaps
#   envelope  no dressing stands where a player can be: each piece is inside rock, inside a solid top, flat on the
#             floor, flush on a rock face, or above the reach ceiling, which is recomputed here from C, the player, the
#             targets and the movers (REACH-1, 0229: art/README.md)
#   no lies   no dressing carries collision; the scene's player is sim.js's, its spawns and targets W's, and its own
#             reach ceiling the one recomputed here
#   sources   every mesh names its source and licence; every material a piece uses is declared
#   lineage   the lineage's hashes are the files' and the scene's own
#   rules     (0226, 0229) a scene names rules 3, which graybox/web/sim.js and graybox/tick_ref.py both implement (the
#             handshake), for the reach ceiling holds only under them; each mover is inside the rules' table and its
#             tunnelling bound, restated here, its policy stop or push (push along x or z); its travel stays in the
#             world, above every cell it crosses, clear of every spawn's and target's column and of every other mover's
#             travel; and no dressing stands in a mover's path but what lies flat on the floor
#
# Then it plants defects and requires the check that should catch each one to refuse it, and it makes two
# revisions in the owner's words: a look revision ("make the wet surfaces less reflective"), which may change the
# materials it names and nothing else; and a layout revision ("make this alley narrower"), compiled and admitted
# through the design tool, after which play must still hold and every piece of the scene that changed must stand
# next to a cell that changed. The layout revision needs the shell; without it the line says SKIPPED, never PASS.
#
# QUALITY-0 (art/quality.py, 0221) adds the exact checks of the scene's bytes to every verification (finite, one byte
# form, every field known and bounded, inside the native renderer's budgets), and here the frozen reference of each
# brief (art/references.jsonl): the same art at the same exporter must give the same bytes on every machine.
#
# Visual quality is not checked here and cannot be: these checks keep the art from lying about play. Whether the
# art is good is judged from rendered viewpoints, by a person; QUALITY-0's detectors on stills flag and prove nothing.
# Standard library only. Ends 0 when nothing failed.

import copy
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import dress  # noqa: E402
import quality  # noqa: E402
level = dress.level

_spec = importlib.util.spec_from_file_location("graybox_check", os.path.join(REPO, "graybox", "check.py"))
gcheck = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gcheck)


# ------------------------------------------------------------------------------------------------ the verifier
def travel_of(m):
    """A mover's box over its travel, computed again here: its box, and the box moved len/256 m along its axis."""
    b, d = m["box"], m["len"] / 256.0
    moved = [b[i] + m["axis"][i % 3] * d for i in range(6)]
    return [min(b[i], moved[i]) for i in range(3)] + [max(b[i + 3], moved[i + 3]) for i in range(3)]


def cells_under(b, g):
    """The cells under a box in plan, with some area."""
    c = g["cell"]
    return {(x, z) for x in range(g["w"]) for z in range(g["h"]) if x * c < b[3] and b[0] < (x + 1) * c and z * c < b[5] and b[2] < (z + 1) * c}


# REACH-1's plant (0257), set by the reach witness below alone: the pair test before 0257, the parabola's
REACH_PLANT = ""


def sim_tick():
    """The tick's length as graybox/web/sim.js declares it (const TICK = 1 / N)."""
    import re
    src = open(os.path.join(REPO, "graybox", "web", "sim.js"), encoding="utf-8").read()
    m = re.findall(r"const TICK = 1 / ([0-9]+);", src)
    if len(m) != 1:
        raise ValueError("graybox/web/sim.js declares its TICK not once as 1 / N")
    return 1.0 / float(m[0])


def ticks_onto(hi, lo, allowance, tick, jump, grav):
    """Apart from the exporter's last_tick (0257): the ticks a body jumping from feet at hi walks while the feet at a
    tick's start, with the allowance, still reach lo, or 0; the tick walks before it moves the feet and lets a body onto
    a surface by the feet it started at (its test top <= feet + step, in that form), its ground nowhere below 0, its
    arithmetic graybox/web/sim.js's: vy -= gravity * TICK, then feet += vy * TICK."""
    n, last, feet, vy = 0, 0, hi, 0.0
    while True:
        n = n + 1
        if lo <= feet + allowance:
            last = n
        elif n > 1 and vy <= 0.0:
            return last
        if n == 1:
            vy = jump
        vy = vy - grav * tick
        feet = feet + vy * tick
        if feet <= 0.0:
            return last


def reach_here(S):
    """The reach ceiling, REACH-1 (art/README.md), computed again from the scene's C, player, targets and movers, apart
    from the exporter's code (and with its arithmetic, operation for operation, so that the two give the same doubles):
    the places a body may stand (open cells, movers' tops over their travel, targets' tops), those reached from the
    spawns by jumps the tick allows (0257: played tick by tick, the tick sim.js's), and over each cell the highest head
    a body flying from one of them raises there."""
    import math
    g, P = S["grid"], S["player"]
    w, h, cell, wall, tops = g["w"], g["h"], g["cell"], g["wall"], S["tops"]
    r, step, speed, grav, v = P["radius"], P["step"], P["speed"], P["gravity"], P["jump"]
    apex = v * v / (2.0 * grav)
    tick = sim_tick()
    T = sim_target()
    places = {}   # name: (lo, hi, x0, z0, x1, z1, how far below its lowest the feet may be and still come onto it)
    for z in range(h):
        for x in range(w):
            if tops[z * w + x] < wall:
                places[("cell", x, z)] = (tops[z * w + x],) * 2 + (x * cell, z * cell, (x + 1) * cell, (z + 1) * cell, step)
    for m in S.get("movers", []):
        tb = travel_of(m)
        y_end = m["box"][4] + m["axis"][1] * (m["len"] / 256.0)
        places[("mover", m["id"])] = (min(m["box"][4], y_end), max(m["box"][4], y_end), tb[0], tb[2], tb[3], tb[5], step)
    for tid, t in S.get("targets", {}).items():
        top = t["y"] + T["targetHeight"]
        places[("target", tid)] = (top, top, t["x"] - T["targetRadius"], t["z"] - T["targetRadius"], t["x"] + T["targetRadius"], t["z"] + T["targetRadius"], 0.0)

    def apart(p, q):
        dx = max(q[2] - p[4], p[2] - q[4], 0.0)
        dz = max(q[3] - p[5], p[3] - q[5], 0.0)
        return math.sqrt(dx * dx + dz * dz)

    reached = {("cell", int(sp["x"] // cell), int(sp["z"] // cell)) for sp in S["spawns"].values()}
    reached &= set(places)
    todo, every = sorted(reached), sorted(places.items())
    onto = {}   # this call's own: each (p's highest, q's lowest, its allowance) played once
    while todo:
        p = places[todo.pop()]
        for name, q in every:
            if name in reached:
                continue
            if REACH_PLANT == "pair-parabola":
                need = q[0] - q[6] - p[1]   # the feet above p's highest when they cross onto q
                hit = need <= apex and apart(p, q) <= 2.0 * r + speed * ((v + math.sqrt(v * v - 2.0 * grav * need)) / grav)
            else:
                n = onto.get((p[1], q[0], q[6]))
                if n is None:
                    n = onto[(p[1], q[0], q[6])] = ticks_onto(p[1], q[0], q[6], tick, v, grav)
                hit = bool(n) and apart(p, q) <= 2.0 * r + n * (speed * tick)
            if hit:
                reached.add(name)
                todo.append(name)
    # each place with how far (in plan, along x or z) a body may fly from it before its feet would be below 0, and a
    # metre more: a cell farther than that from a place gets no head from it, and no rounding is asked to say so
    stand = [(places[n], 2.0 * r + speed * (v + math.sqrt(v * v + 2.0 * grav * max(places[n][1], 0.0))) / grav + 1.0) for n in sorted(reached)]
    out = []
    for z in range(h):
        for x in range(w):
            here = (0, 0, x * cell, z * cell, (x + 1) * cell, (z + 1) * cell)
            heads = []
            for p, far in stand:
                if max(here[2] - p[4], p[2] - here[4], here[3] - p[5], p[3] - here[5]) > far:
                    continue
                t = max(0.0, apart(p, here) - 2.0 * r) / speed
                if t <= v / grav:
                    heads.append(p[1] + apex + P["body"])
                elif p[1] + (v * t - 0.5 * grav * t * t) >= 0:
                    heads.append(p[1] + (v * t - 0.5 * grav * t * t) + P["body"])
            if heads:
                out.append(round(max(heads) + P["margin"], 4))
            else:
                out.append(round(tops[z * w + x] + P["body"] + apex + P["margin"], 4) if tops[z * w + x] < wall else None)
    return out


def check_collision(S, C):
    g = S["grid"]
    w, h, cell = g["w"], g["h"], g["cell"]
    if S["tops"] != C["tops"]:
        return False, "the scene's tops are not C's"
    ground = [b for b in S["collision"] if b["kind"] == "ground"]
    if len(ground) != 1 or ground[0]["box"][4] != 0 or ground[0]["box"][0] > 0 or ground[0]["box"][2] > 0 \
            or ground[0]["box"][3] < w * cell or ground[0]["box"][5] < h * cell:
        return False, "the ground is not one slab under the whole grid with its top at 0"
    top = [0.0] * (w * h)
    hits = [0] * (w * h)
    for b in S["collision"]:
        if b["kind"] == "ground":
            continue
        x0, y0, z0, x1, y1, z1 = b["box"]
        gx0, gz0, gx1, gz1 = x0 / cell, z0 / cell, x1 / cell, z1 / cell
        if y0 != 0 or any(abs(v - round(v)) > 1e-9 for v in (gx0, gz0, gx1, gz1)) or gx1 <= gx0 or gz1 <= gz0:
            return False, "the box %s is not a column of whole cells standing on the ground" % b["id"]
        for z in range(int(round(gz0)), int(round(gz1))):
            for x in range(int(round(gx0)), int(round(gx1))):
                if not (0 <= x < w and 0 <= z < h):
                    return False, "the box %s leaves the grid" % b["id"]
                hits[z * w + x] += 1
                top[z * w + x] = y1
    if any(n > 1 for n in hits):
        k = next(i for i, n in enumerate(hits) if n > 1)
        return False, "two boxes overlap at %d,%d" % (k % w, k // w)
    diff = [k for k in range(w * h) if abs(top[k] - C["tops"][k]) > 1e-9]
    if diff:
        return False, "%d cells' collision is not C's (first %d,%d: %s m, C says %s m)" % (len(diff), diff[0] % w, diff[0] // w, top[diff[0]], C["tops"][diff[0]])
    return True, "%d boxes and the ground lay back onto C, cell for cell" % (len(S["collision"]) - 1)


def check_envelope(S, reach):
    g, P = S["grid"], S["player"]
    w, h, cell, wall, tops = g["w"], g["h"], g["cell"], g["wall"], S["tops"]
    rock = lambda x, z: not (0 <= x < w and 0 <= z < h) or tops[z * w + x] >= wall
    paths = [(m["id"], travel_of(m)) for m in S.get("movers", [])]
    for v in S["visuals"]:
        x0, y0, z0, x1, y1, z1 = v["box"]
        if not (x1 > x0 and y1 > y0 and z1 > z0):
            return False, "%s is not a box" % v["id"]
        for mid, tb in paths:
            if x0 < tb[3] and tb[0] < x1 and y0 < tb[4] and tb[1] < y1 and z0 < tb[5] and tb[2] < z1:
                if not all(y1 <= tops[z * w + x] + P["flat"] + 1e-9 for x, z in cells_under(v["box"], g)):
                    return False, "%s stands in the path of the mover %s" % (v["id"], mid)
        for z in range(max(0, int(z0 // cell)), min(h, int(-(-z1 // cell)))):
            for x in range(max(0, int(x0 // cell)), min(w, int(-(-x1 // cell)))):
                cx0, cz0, cx1, cz1 = x * cell, z * cell, (x + 1) * cell, (z + 1) * cell
                ox0, ox1, oz0, oz1 = max(x0, cx0), min(x1, cx1), max(z0, cz0), min(z1, cz1)
                if ox1 - ox0 <= 1e-9 or oz1 - oz0 <= 1e-9 or rock(x, z):
                    continue   # no area over this cell, or the cell is rock
                t = tops[z * w + x]
                if y1 <= t + P["flat"] + 1e-9:
                    continue   # inside the solid, or flat on it
                if reach[z * w + x] is not None and y0 >= reach[z * w + x] - 1e-9:
                    continue   # above every head
                flush = ((ox1 - ox0 <= P["flush"] + 1e-9) and ((abs(ox0 - cx0) < 1e-9 and rock(x - 1, z)) or (abs(ox1 - cx1) < 1e-9 and rock(x + 1, z)))) \
                    or ((oz1 - oz0 <= P["flush"] + 1e-9) and ((abs(oz0 - cz0) < 1e-9 and rock(x, z - 1)) or (abs(oz1 - cz1) < 1e-9 and rock(x, z + 1))))
                if flush:
                    continue   # thin, against a rock face
                return False, "%s stands where a player can be, over %d,%d (%.2f to %.2f m; the floor's top %.2f, the reach ceiling %s)" % (
                    v["id"], x, z, y0, y1, t, reach[z * w + x])
    return True, "%d pieces: each inside rock, inside a solid, flat, flush on a rock face, or above every head" % len(S["visuals"])


def sim_player():
    """The player's constants as the graybox runtime declares them, read from graybox/web/sim.js itself."""
    import re
    src = open(os.path.join(REPO, "graybox", "web", "sim.js"), encoding="utf-8").read()
    m = re.search(r"const P = \{([^}]*)\}", src)
    if not m:
        raise ValueError("graybox/web/sim.js declares no player P")
    vals = dict((k, float(v)) for k, v in re.findall(r"(\w+):\s*([0-9.]+)", m.group(1)))
    return {k: vals[k] for k in ("radius", "eye", "step", "speed", "gravity", "jump")}


def sim_target():
    """A target's radius and height as graybox/web/sim.js declares them."""
    import re
    src = open(os.path.join(REPO, "graybox", "web", "sim.js"), encoding="utf-8").read()
    m = re.search(r"const P = \{([^}]*)\}", src)
    vals = dict((k, float(v)) for k, v in re.findall(r"(\w+):\s*([0-9.]+)", m.group(1))) if m else {}
    return {"targetRadius": vals.get("targetRadius", 0.0), "targetHeight": vals.get("targetHeight", 0.0)}


def check_no_lies(S, reach, W=None):
    sim = sim_player()
    off = [k for k, v in sim.items() if S["player"].get(k) != v]
    if off:
        return False, "the scene's player %s is %s; graybox/web/sim.js says %s" % (off[0], S["player"].get(off[0]), sim[off[0]])
    if W is not None:
        g = S["grid"]
        for k, sp in sorted(W["spawns"].items()):
            got = S["spawns"].get(k, {})
            if (got.get("x"), got.get("z"), got.get("yaw")) != (round((sp["x"] + 0.5) * g["cell"], 4), round((sp["z"] + 0.5) * g["cell"], 4), round(sp["yaw"], 4)):
                return False, "the scene's spawn %s is not W's" % k
        # 0229: the targets, whose tops the reach ceiling counts, are W's, each where W stands it
        want = {t["id"]: {"x": round((t["x"] + 0.5) * g["cell"], 4), "z": round((t["z"] + 0.5) * g["cell"], 4),
                          "y": S["tops"][t["z"] * g["w"] + t["x"]]} for t in W["targets"]}
        if S.get("targets") != want:
            diff = sorted(set(want) ^ set(S.get("targets") or {})) or sorted(k for k in want if want[k] != S["targets"][k])
            return False, "the scene's targets are not W's (%s)" % ", ".join(diff[:3])
    for name, vw in sorted(S.get("views", {}).items()):
        x, z = int(vw["x"] // S["grid"]["cell"]), int(vw["z"] // S["grid"]["cell"])
        if reach[z * S["grid"]["w"] + x] is None or S["tops"][z * S["grid"]["w"] + x] >= S["grid"]["wall"]:
            return False, "the view %s stands in rock" % name
    bad = [v["id"] for v in S["visuals"] if v.get("collision")]
    if bad:
        return False, "%s carries collision: only C decides where a player can go" % bad[0]
    diff = [k for k in range(len(reach)) if reach[k] != S["reach"][k]]
    if diff:
        w = S["grid"]["w"]
        return False, "the scene's reach ceiling at %d,%d is %s; recomputed here it is %s" % (diff[0] % w, diff[0] // w, S["reach"][diff[0]], reach[diff[0]])
    lit = [L["id"] for L in S["lights"] if any(k in L for k in ("box", "collision", "asset"))]
    if lit:
        return False, "the light %s carries geometry" % lit[0]
    return True, "no piece has collision; the player is sim.js's, the spawns and targets W's; the reach ceiling is the one recomputed here; lights are only light"


def sim_rules3():
    """What the simulation and its twin say of rules 3, read from their sources: (sim.js offers rules 3, its body and
    phase unit, its policies; tick_ref.py's rules-3 version, phase unit and body). None where a source no longer says it
    once."""
    import re
    js = open(os.path.join(REPO, "graybox", "web", "sim.js"), encoding="utf-8").read()
    py = open(os.path.join(REPO, "graybox", "tick_ref.py"), encoding="utf-8").read()
    offers = re.findall(r"rules === 3 \? 3 :", js)
    unit = re.findall(r"const BODY = ([0-9.]+), Q = 1 / ([0-9]+);", js)
    pol = re.findall(r'const POLICIES = RULES >= 3 \? \["stop", "push"\] : \["stop"\];', js)
    twin = re.findall(r"^RULES3 = ([0-9]+)(?:  +#[^\n]*)?$", py, re.M)
    tq = re.findall(r"^Q = 1\.0 / ([0-9]+)\.0$", py, re.M)
    tb = re.findall(r"^BODY = ([0-9.]+)$", py, re.M)
    return {"sim": 3 if len(offers) == 1 else None, "body": float(unit[0][0]) if len(unit) == 1 else None,
            "q": int(unit[0][1]) if len(unit) == 1 else None, "push": len(pol) == 1, "twin": int(twin[0]) if len(twin) == 1 else None,
            "twin_q": int(tq[0]) if len(tq) == 1 else None, "twin_body": float(tb[0]) if len(tb) == 1 else None}


def check_rules(S, W=None):
    """A scene's rules and movers (0226, 0229), held here apart from the exporter's code: the rules' handshake (every
    scene names rules 3), the rules' table for each mover, and every mover's travel against the world, the spawns, the
    targets and the other movers."""
    if S.get("rules") != 3 or isinstance(S.get("rules"), bool):
        return False, "the scene names rules %r: a scene is played under rules 3, whose walls and targets the reach ceiling counts on, and no other rules are offered here" % (S.get("rules"),)
    R = sim_rules3()
    if R["sim"] != 3 or R["twin"] != 3 or R["q"] != 256 or R["twin_q"] != 256 or R["body"] is None or R["body"] != R["twin_body"] or not R["push"]:
        return False, "the scene needs rules 3 (1/256 m units, the policies stop and push): graybox/web/sim.js says %s and graybox/tick_ref.py says %s" % (
            "rules 3 offered, Q 1/%s, push %s" % (R["q"], "offered" if R["push"] else "not offered") if R["sim"] == 3 else "no rules 3", "rules %s, Q 1/%s" % (R["twin"], R["twin_q"]))
    if "movers" not in S:
        return True, "rules 3, which sim.js and tick_ref.py both implement; no movers"
    if not isinstance(S["movers"], list) or not S["movers"]:
        return False, "the scene's movers are not a list of at least one mover"
    g, P = S["grid"], S["player"]
    w, h, cell, tops = g["w"], g["h"], g["cell"], S["tops"]
    radius, body = sim_player()["radius"], R["body"]
    seen, paths = set(), []
    for m in S["movers"]:
        mid = m.get("id")
        if not isinstance(mid, str) or mid in seen:
            return False, "a mover's id %r is not text, or not unique" % (mid,)
        seen.add(mid)
        b = m.get("box")
        if not (isinstance(b, list) and len(b) == 6 and all(isinstance(v, (int, float)) and abs(v) < 1024 and (v * 256) == int(v * 256) for v in b)):
            return False, "the mover %s's box is not six whole numbers of 1/256 m below 1,024 m" % mid
        if not (b[0] < b[3] and b[1] < b[4] and b[2] < b[5]):
            return False, "the mover %s's box has no extent on some axis" % mid
        a = m.get("axis")
        if not (isinstance(a, list) and len(a) == 3 and sorted(abs(v) for v in a) == [0, 0, 1] and all(v in (-1, 0, 1) for v in a)):
            return False, "the mover %s's axis is not one of x, y, z" % mid
        n, sp = m.get("len"), m.get("speed")
        if not (isinstance(n, int) and 1 <= n <= 2 ** 18 and isinstance(sp, int) and 0 <= sp <= n):
            return False, "the mover %s's len or speed is not whole and in range" % mid
        if m.get("policy") not in ("stop", "push"):
            return False, "the mover %s's policy is not stop or push" % mid
        if m["policy"] == "push" and a[1] != 0:
            return False, "the mover %s pushes along y, which rules 3 do not do" % mid
        if m.get("material") not in S["materials"]:
            return False, "the mover %s's material is not declared" % mid
        k = a.index(1) if 1 in a else a.index(-1)
        thick = b[k + 3] - b[k]
        bound = body + thick if k == 1 else 2 * radius + thick
        if not sp / 256.0 < bound:
            return False, "the mover %s moves %s m a tick, not less than its tunnelling bound %s m" % (mid, sp / 256.0, bound)
        tb = travel_of(m)
        if tb[0] < 0 or tb[2] < 0 or tb[1] < 0 or tb[3] > w * cell or tb[5] > h * cell or tb[4] >= 1024:
            return False, "the mover %s's travel leaves the world" % mid
        hit = sorted((x, z) for x, z in cells_under(tb, g) if tops[z * w + x] > tb[1])
        if hit:
            return False, "the mover %s's travel meets the solid of cell %d,%d" % ((mid,) + hit[0])
        for side, spn in sorted(S["spawns"].items()):
            px, pz = max(tb[0], min(spn["x"], tb[3])), max(tb[2], min(spn["z"], tb[5]))
            if (spn["x"] - px) ** 2 + (spn["z"] - pz) ** 2 < radius ** 2 and tb[4] > spn["y"] and tb[1] < spn["y"] + body:
                return False, "the mover %s's travel crosses spawn %s's column" % (mid, side)
        if W is not None:
            sp = sim_target()
            for t in W["targets"]:
                tx, tz, ty = (t["x"] + 0.5) * cell, (t["z"] + 0.5) * cell, tops[t["z"] * w + t["x"]]
                px, pz = max(tb[0], min(tx, tb[3])), max(tb[2], min(tz, tb[5]))
                if (tx - px) ** 2 + (tz - pz) ** 2 < sp["targetRadius"] ** 2 and tb[4] > ty and tb[1] < ty + sp["targetHeight"]:
                    return False, "the mover %s's travel crosses target %s's column" % (mid, t["id"])
        for oid, ob in paths:
            if all(tb[i] < ob[i + 3] and ob[i] < tb[i + 3] for i in range(3)):
                return False, "the movers %s and %s cross each other's travel" % (oid, mid)
        paths.append((mid, tb))
    return True, "rules 3, which sim.js and tick_ref.py both implement; %d mover(s), each within the rules' table and its tunnelling bound, its policy stop or push (push along x or z); each travel above the cells it crosses and clear of the spawns' columns%s and of each other" % (
        len(S["movers"]), ", the targets'" if W is not None else "")


def check_sources(S):
    for name, a in S["assets"].items():
        if a.get("source") not in dress.SOURCES or not a.get("licence", "").strip() or not a.get("path"):
            return False, "the asset %s does not name its path, its source and its licence" % name
    for v in S["visuals"]:
        if v["asset"] not in S["assets"]:
            return False, "%s uses the asset %s, which the scene does not declare" % (v["id"], v["asset"])
        if v["material"] not in S["materials"]:
            return False, "%s uses the material %s, which the scene does not declare" % (v["id"], v["material"])
    for b in S["collision"]:
        if b["material"] not in S["materials"]:
            return False, "%s uses the material %s, which the scene does not declare" % (b["id"], b["material"])
    return True, "%d asset(s), each with a source and a licence: %s" % (len(S["assets"]), ", ".join(
        "%s (%s, %s)" % (k, a["source"], a["licence"]) for k, a in sorted(S["assets"].items())))


def check_lineage(out, art_path, scene_bytes):
    L = out["lineage"]
    raw = open(art_path, "rb").read().replace(b"\r\n", b"\n") if art_path else None
    if art_path and dress.sha256(raw) != L["art_sha256"]:
        return False, "the art file's bytes are not the ones the lineage names"
    if dress.sha256(scene_bytes) != L["scene_sha256"]:
        return False, "the scene's bytes are not the ones the lineage names"
    if L["canonical_sha256"] != dress.sha256(level.canon(out["W"])) or L["collision_sha256"] != dress.sha256(level.canon(out["C"])):
        return False, "the lineage's world hashes are not W's and C's"
    exp = dress.sha256(open(os.path.join(HERE, "dress.py"), "rb").read().replace(b"\r\n", b"\n"))
    if L["exporter_sha256"] != exp:
        return False, "the lineage names another exporter"
    return True, "art %s, layout head %s, scene %s" % (L["art_sha256"][:12], (L["map_source"].get("layout_head") or "-")[:12], L["scene_sha256"][:12])


RULES_CHECK = "the rules: rules 3 hold the scene, its movers and their paths clear"


def verify(out, art_path, scene_bytes=None, D=None):
    S, W, C = out["scene"], out["W"], out["C"]
    scene_bytes = out["scene_bytes"] if scene_bytes is None else scene_bytes
    reach = reach_here(S)
    res = []
    D = D if D is not None else gcheck.source_rows(W)
    play = [(c, ok, d) for c, ok, d in gcheck.verify(D, W, C)]
    bad = [c for c, ok, _d in play if not ok]
    res.append(("play holds: the graybox map's own checks", not bad, "%d checks%s" % (len(play), (", failed: " + bad[0]) if bad else "")))
    res.append(("collision is C, exactly",) + check_collision(S, C))
    res.append(("no dressing where a player can be",) + check_envelope(S, reach))
    res.append(("the art carries no collision and no false ceiling",) + check_no_lies(S, reach, W))
    res.append(("every mesh names its source and licence",) + check_sources(S))
    res.append((RULES_CHECK,) + check_rules(S, W))
    res.append(("the lineage binds every input",) + check_lineage(out, art_path, scene_bytes))
    # QUALITY-0 (art/quality.py): the scene's bytes exact — finite, in their one byte form, every field known and in
    # its bounds, inside what the native renderer draws
    res += quality.check_scene(scene_bytes)[0]
    return res


# ------------------------------------------------------------------------------------------------ revisions
def revise(text: str, revision: str, fname: str) -> (str, list):
    """A look revision (VERDANDI-ART-REVISION 0): each statement replaces the art file's one statement with the
    same verb and first argument. Returns the new text and the replaced statements' (verb, name) keys."""
    lines = [ln for ln in revision.splitlines() if ln.split("#", 1)[0].strip()]
    if not lines or lines[0].split("#", 1)[0].strip() != "VERDANDI-ART-REVISION 0":
        raise dress.ArtError("%s: the first line is not 'VERDANDI-ART-REVISION 0'" % fname)
    out, keys = text.splitlines(), []
    for ln in lines[1:]:
        code = ln.split("#", 1)[0].split()
        key = (code[0], code[1] if len(code) > 1 else "")
        at = [i for i, o in enumerate(out) if o.split("#", 1)[0].split()[:2] == list(key)]
        if len(at) != 1:
            raise dress.ArtError("%s: %s %s names %d statements of the art file; a revision replaces exactly one" % (fname, key[0], key[1], len(at)))
        tail = (" #" + out[at[0]].split("#", 1)[1]) if "#" in out[at[0]] else ""
        out[at[0]] = " ".join(code) + tail
        keys.append(key)
    return "\n".join(out) + "\n", keys


def items(S):
    d = {}
    for fam in ("collision", "visuals", "lights"):
        for it in S[fam]:
            d[(fam, it["id"])] = it
    return d


def look_only(S0, S1, keys):
    """A look revision may change the materials it names and the environment statements it names, nothing else."""
    named_m = {k[1] for k in keys if k[0] == "material"}
    env = {k[0] for k in keys} & {"time", "moon", "sun", "fog", "exposure", "bloom", "rain"}
    for f in ("tops", "reach", "collision", "visuals", "lights", "spawns", "views", "grid", "player", "assets"):
        if S0[f] != S1[f]:
            return False, "the look revision changed the scene's %s" % f
    changed = sorted(m for m in set(S0["materials"]) | set(S1["materials"]) if S0["materials"].get(m) != S1["materials"].get(m))
    if not changed or set(changed) - named_m:
        return False, "materials changed: %s; the revision names %s" % (changed or "none", sorted(named_m))
    if S0["environment"] != S1["environment"] and not env:
        return False, "the environment changed and the revision names none of it"
    return True, "only %s changed; play, dressing and lights are byte for byte the same" % ", ".join(changed)


def layout_local(S0, S1, region):
    """After a layout revision: the cells that changed lie in the revision's region, and every piece of the scene that
    changed stands within one cell of a changed cell (a collision box: in a chunk holding one)."""
    g = S0["grid"]
    w, cell = g["w"], g["cell"]
    delta = {(k % w, k // w) for k in range(len(S0["tops"])) if S0["tops"][k] != S1["tops"][k]}
    if not delta:
        return False, "no cell changed"
    x0, z0, x1, z1 = region
    out = sorted(p for p in delta if not (x0 <= p[0] <= x1 and z0 <= p[1] <= z1))
    if out:
        return False, "the cell %d,%d changed, outside the revision's region" % out[0]
    zone = {(x + dx, z + dz) for x, z in delta for dx in (-1, 0, 1) for dz in (-1, 0, 1)}
    chunks = {(x // dress.CHUNK, z // dress.CHUNK) for x, z in delta}
    I0, I1 = items(S0), items(S1)
    moved = sorted(k for k in set(I0) | set(I1) if I0.get(k) != I1.get(k))
    for fam, iid in moved:
        it = I1.get((fam, iid)) or I0.get((fam, iid))
        if fam == "collision":
            cx0, cz0, cx1, cz1 = it["cells"]
            if it["kind"] == "ground" or not any((x // dress.CHUNK, z // dress.CHUNK) in chunks for x in (cx0, cx1) for z in (cz0, cz1)):
                return False, "the collision box %s changed, in a chunk where no cell changed" % iid
        else:
            if fam == "lights":
                px, pz = it["pos"][0], it["pos"][2]
                foot = {(int(px // cell), int(pz // cell))}
            else:
                b = it["box"]
                foot = {(x, z) for x in range(int(b[0] // cell), int(-(-b[3] // cell))) for z in range(int(b[2] // cell), int(-(-b[5] // cell)))}
            if not foot & zone:
                return False, "%s %s changed, away from every changed cell" % (fam, iid)
    fams = {}
    for fam, _i in moved:
        fams[fam] = fams.get(fam, 0) + 1
    return True, "%d cell(s) changed, all in the region; %d piece(s) changed, all beside them (%s); %d unchanged" % (
        len(delta), len(moved), ", ".join("%s %d" % kv for kv in sorted(fams.items())), len(set(I0) & set(I1)) - len([m for m in moved if m in I0 and m in I1]))


def compile_revision(base_design: bytes, revision: bytes):
    """The base layout's design and then the revision, admitted through the design tool in a project of its own.
    Returns (rows, head) of the revised world, or (None, reason)."""
    tool = os.path.join(REPO, "design", "design.py")
    tmp = tempfile.mkdtemp(prefix="art-revision-")

    def run(*a, inp=None):
        cp = subprocess.run([sys.executable, tool] + list(a) + ["--project", tmp], input=inp, capture_output=True, cwd=REPO)
        return cp.returncode, cp.stdout.decode("utf-8", "replace"), cp.stderr.decode("utf-8", "replace")
    try:
        for step in (("new",), ("grant", "--allow", "open,close", "--cells", "0,0,47,31")):
            rc, o, e = run(*step)
            if rc != 0:
                return None, "design.py %s: %s" % (step[0], (e or o).strip()[-160:])
        for text in (base_design, revision):
            for step in (("propose", "-"), ("preview",), ("admit",)):
                rc, o, e = run(*step, inp=text if step[0] == "propose" else None)
                if rc != 0:
                    code = "SHELL-COMPILE-EMPTY: " if "SHELL-COMPILE-EMPTY" in (e + o) else ""
                    return None, "design.py %s: %s%s" % (step[0], code, (e or o).strip()[-160:])
        rc, o, e = run("inspect", "--json")
        d = json.loads(o)
        grid = [ln[5:] for ln in d["top_view"][2:]]
        cx, cz = (int(v) for v in d["world"]["camera"].split(",")[:2])
        grid[cz] = grid[cz][:cx] + "." + grid[cz][cx + 1:]
        return grid, d["session"]["head"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def shell_available():
    if shutil.which("rustc"):
        return True
    return os.path.exists(os.path.join(REPO, "verify", "build", "shell")) or os.path.exists(os.path.join(REPO, "verify", "build", "shell.exe"))


# ------------------------------------------------------------------------------------------------ plants
def plants(out, art_path):
    """Defects the art could have, each planted in a copy; the named check must refuse it. [(plant, refused, by)]."""
    S, W, C = out["scene"], out["W"], out["C"]
    D = gcheck.source_rows(W)
    res = []

    def judged(label, S2, expect, scene_bytes=None):
        o2 = dict(out, scene=S2)
        failed = [c for c, ok, _d in verify(o2, art_path, scene_bytes=scene_bytes if scene_bytes is not None else out["scene_bytes"], D=D) if not ok]
        res.append((label, expect in failed, ("refused by: " + expect) if expect in failed else "NOT refused by %r (failed: %s)" % (expect, failed or "nothing")))

    w, cell = S["grid"]["w"], S["grid"]["cell"]
    S2 = copy.deepcopy(S)
    i = next(i for i, b in enumerate(S2["collision"]) if b["kind"] == "wall")
    dropped = S2["collision"].pop(i)
    judged("a wall's collision box dropped (%s): a wall you can walk through" % dropped["id"], S2, "collision is C, exactly")
    S2 = copy.deepcopy(S)
    b = next(b for b in S2["collision"] if b["kind"] == "cover")
    b["box"][4] = round(b["box"][4] + 1.0, 4)
    judged("a cover box made 1 m taller than C says (%s)" % b["id"], S2, "collision is C, exactly")
    sx, sz = S["spawns"]["A"]["x"], S["spawns"]["A"]["z"]
    gx, gz = int(sx // cell) + 2, int(sz // cell)
    S2 = copy.deepcopy(S)
    S2["visuals"].append({"id": "plant:wall", "by": "plant", "region": "*", "asset": "cube", "material": "concrete",
                          "box": [gx * cell, 0.0, gz * cell, (gx + 1) * cell, 2.5, (gz + 1) * cell]})
    judged("a decorative wall on open floor at %d,%d: the art deciding a wall" % (gx, gz), S2, "no dressing where a player can be")
    S2 = copy.deepcopy(S)
    can = next((v for v in S2["visuals"] if v["id"].startswith("canopy:")), None)
    if can:
        can["box"][1], can["box"][4] = 3.0, 3.4
        judged("a canopy lowered to 3.0 m, under the reach ceiling (%s)" % can["id"], S2, "no dressing where a player can be")
    S2 = copy.deepcopy(S)
    neon = next((v for v in S2["visuals"] if v["id"].startswith("neon:")), None)
    if neon:
        # a sign pulled 0.3 m off its wall: no longer flush
        if neon["box"][3] - neon["box"][0] < 0.1:
            if neon["id"].endswith(":w"):
                neon["box"][3] = round(neon["box"][0] + 0.3, 4)
            else:
                neon["box"][0] = round(neon["box"][3] - 0.3, 4)
        else:
            if neon["id"].endswith(":n"):
                neon["box"][5] = round(neon["box"][2] + 0.3, 4)
            else:
                neon["box"][2] = round(neon["box"][5] - 0.3, 4)
        judged("a neon sign standing 0.3 m off its wall (%s)" % neon["id"], S2, "no dressing where a player can be")
    S2 = copy.deepcopy(S)
    S2["visuals"][0] = dict(S2["visuals"][0], collision=True)
    judged("a piece of dressing given collision (%s)" % S2["visuals"][0]["id"], S2, "the art carries no collision and no false ceiling")
    S2 = copy.deepcopy(S)
    k = next(k for k, r in enumerate(S2["reach"]) if r is not None)
    S2["reach"][k] = round(S2["reach"][k] - 1.0, 4)
    judged("the scene's reach ceiling lowered 1 m at %d,%d, so a low canopy would pass" % (k % w, k // w), S2, "the art carries no collision and no false ceiling")
    S2 = copy.deepcopy(S)
    S2["player"] = dict(S2["player"], jump=6.0)
    S2["reach"] = reach_here(S2)
    judged("the scene's player jumps 6 m/s, not sim.js's 7, and its ceiling is lowered to match", S2, "the art carries no collision and no false ceiling")
    S2 = copy.deepcopy(S)
    S2["spawns"]["A"] = dict(S2["spawns"]["A"], x=round(S2["spawns"]["A"]["x"] + 2 * cell, 4))
    judged("the scene's spawn A moved a cell from W's", S2, "the art carries no collision and no false ceiling")
    S2 = copy.deepcopy(S)
    S2["assets"]["cube"] = dict(S2["assets"]["cube"], licence="")
    judged("a mesh with no licence", S2, "every mesh names its source and licence")
    S2 = copy.deepcopy(S)
    m0 = sorted(S2["materials"])[0]
    S2["materials"][m0] = dict(S2["materials"][m0], roughness=0.5 if S2["materials"][m0]["roughness"] != 0.5 else 0.6)
    tampered = (json.dumps(S2, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    judged("the scene changed after export, its lineage not (%s)" % m0, S2, "the lineage binds every input", scene_bytes=tampered)
    # through the exporter itself: statements it must refuse, appended to the brief as it stands (a plant must not
    # depend on the brief's own lines, which revisions change)
    text = open(art_path, encoding="utf-8").read().rstrip("\n") + "\nregion plant-r 19,10 28,21\n"
    for label, add in (
            ("neon of a material that does not emit", "neon plant-r concrete 3.1 2"),
            ("a canopy whose corners leave its region", "canopy plant-r concrete 5.2 17,10 28,11"),
            ("a tower in a region never declared", "tower harbour concrete 12 20"),
            ("a mesh from an unnamed source", "asset plant-mesh /Engine/BasicShapes/Cube.Cube somewhere unknown"),
            ("a view where no player can stand", "view plant-view 23,2 180 4"),
            ("two pieces of dressing in one place", "puddle plant-r puddle 100")):
        try:
            A = dress.parse(text + add + "\n", os.path.basename(art_path))
            A["name"], A["sha256"] = "plant", "-"
            dress.export(A)
            res.append(("the exporter refuses " + label, False, "the exporter took it"))
        except dress.ArtError as e:
            res.append(("the exporter refuses " + label, True, "refused: " + str(e)[:90]))
    # an option that adds dressing under a slab: the slab alone passes, and with the option it is refused, so that the
    # refusal is the option's (a slab that is itself too low proves nothing about its ribs or its lights). 0229: each
    # slab set just above the highest ceiling over its cells (REACH-1 raised them), the ribs 0.8 m below it and the edge
    # lights 0.06 m, so that the option, not the height chosen, is what is refused
    region_r = (19, 10, 28, 21)

    def over(x0, z0, x1, z1, plus):
        top = max(S["reach"][z * w + x] for z in range(z0, z1 + 1) for x in range(x0, x1 + 1) if S["reach"][z * w + x] is not None)
        return "%.2f" % (math.ceil((top + plus) * 100) / 100.0)
    for label, slab, option in (("a canopy clear of every head whose ribs are not", "canopy plant-r concrete %s" % over(*region_r, plus=0.1), "ribs 1"),
                                ("a canopy clear of every head whose edge lights are not", "canopy plant-r concrete %s 19,10 28,10" % over(19, 10, 28, 10, plus=0.03), "edgelit 255,180,120 100")):
        try:
            got = []
            for add in (slab, slab + " " + option):
                A = dress.parse(text + add + "\n", os.path.basename(art_path))
                A["name"], A["sha256"] = "plant", "-"
                o3 = dress.export(A)
                got.append("no dressing where a player can be" in [c for c, ok, _d in verify(o3, None, D=gcheck.source_rows(o3["W"])) if not ok])
            res.append((label, got == [False, True],
                        "the slab alone passes; with '%s' refused by: no dressing where a player can be" % option if got == [False, True] else
                        "NOT shown (the slab alone refused: %s; with the option refused: %s)" % tuple(got)))
        except dress.ArtError as e:
            res.append((label, False, "the exporter refused it before the checks could: " + str(e)[:90]))
    # 0226: the number grammar. The lamp alone passes; each variant of one of its numbers is refused for that number
    base = "lamp plant-r 255,200,150 100 5"
    try:
        A = dress.parse(text + base + "\n", os.path.basename(art_path))
        A["name"], A["sha256"] = "plant", "-"
        dress.export(A)
        base_ok = True
    except dress.ArtError as e:
        base_ok, why = False, str(e)
    for label, add, says in (
            ("an exponent ('1e2' candelas)", "lamp plant-r 255,200,150 1e2 5", "is not a number"),
            ("a '+' ('+100')", "lamp plant-r 255,200,150 +100 5", "is not a number"),
            ("an underscore ('1_00', which float() reads as 100)", "lamp plant-r 255,200,150 1_00 5", "is not a number"),
            ("Arabic-Indic digits (one, zero, zero)", "lamp plant-r 255,200,150 \u0661\u0660\u0660 5", "is not a number"),
            ("a fraction where a whole number goes ('5.5' cells, which int() cut to 5)", "lamp plant-r 255,200,150 100 5.5", "is not a whole number"),
            ("a superscript two in a colour, which str.isdigit() took", "lamp plant-r 255,\u00b200,150 100 5", "is not a colour")):
        if not base_ok:
            res.append(("the number grammar refuses " + label, False, "NOT shown: the lamp alone was refused: " + why[:80]))
            continue
        try:
            A = dress.parse(text + add + "\n", os.path.basename(art_path))
            A["name"], A["sha256"] = "plant", "-"
            dress.export(A)
            res.append(("the number grammar refuses " + label, False, "the exporter took it"))
        except dress.ArtError as e:
            res.append(("the number grammar refuses " + label, says in str(e), ("refused: " if says in str(e) else "refused for another reason: ") + str(e)[:90]))
        except Exception as e:   # noqa: BLE001  (a crash is not a refusal)
            res.append(("the number grammar refuses " + label, False, "the exporter crashed: %s: %s" % (type(e).__name__, e)))
    # 0226: movers the exporter must refuse, each beside one it takes, so that the refusal is the defect's
    good = "mover plant-ok concrete 40,0,30 42,0.25,32 along +y travel 2.25 speed 0.9375"
    slab = "canopy plant-r concrete 5.2 20,15 20,15"
    for label, ok_text, add, says in (
            ("a mover whose corner is not a whole number of 1/256 m", good, "mover plant-m concrete 40.1,0,30 42,0.25,32 along +y travel 2.25 speed 0.9375", "1/256 m"),
            ("a mover whose speed is not a whole number of 1/256 m a tick", good, "mover plant-m concrete 40,0,30 42,0.25,32 along +y travel 2.25 speed 1", "a tick"),
            ("a mover past the tunnelling bound (the rules' own table refuses it)", good, "mover plant-m concrete 40,0,30 40.25,2,32 along +x travel 6 speed 114.375", "RULES2-MOVER"),
            ("a mover whose travel goes through a wall", good, "mover plant-m concrete 40,0,30 42,0.5,32 along -z travel 24 speed 3.75", "solid"),
            ("a mover whose travel crosses a spawn", good, "mover plant-m concrete 10,0,30 12,0.5,32 along -x travel 4 speed 3.75", "spawn"),
            ("a mover whose travel crosses a target", good, "mover plant-m concrete 24,0,32 26,0.5,34 along -x travel 6 speed 3.75", "target"),
            ("two movers whose travels cross", good, good + "\nmover plant-m concrete 38,1,30 39,1.25,32 along +x travel 3 speed 3.75", "plant-ok"),
            ("a mover whose travel meets a piece of dressing (a slab at 5.2 m over a lift rising to 6.25 m)", slab + "\n" + good,
             slab + "\nmover plant-m concrete 40,0,30 42,0.25,32 along +y travel 6 speed 0.9375", "in the path"),
            ("a mover pushing along y (0229: rules 3 push along x or z)", good, "mover plant-m concrete 40,0,30 42,0.25,32 along +y travel 2.25 speed 0.9375 policy push", "pushes along y"),
            ("a mover with a policy rules 3 do not have", good, "mover plant-m concrete 40,0,30 42,0.25,32 along +y travel 2.25 speed 0.9375 policy pull", "policy takes")):
        try:
            got = []
            for t2 in (ok_text, add):
                A = dress.parse(text + t2 + "\n", os.path.basename(art_path))
                A["name"], A["sha256"] = "plant", "-"
                try:
                    dress.export(A)
                    got.append(None)
                except dress.ArtError as e:
                    got.append(str(e))
            ok = got[0] is None and got[1] is not None and says in got[1]
            res.append(("the exporter refuses " + label, ok, ("refused: " + got[1][:100]) if ok else "NOT shown (the good mover: %s; the defect: %s)" % (got[0] or "taken", got[1] or "taken")))
        except dress.ArtError as e:
            res.append(("the exporter refuses " + label, False, "the plant itself did not read: " + str(e)[:90]))
    # 0226: a canopy clear of every head on foot, not of a rider's: the slab alone passes, and with a lift under it, which
    # raises a rider's head to 5.775 m, the same slab is refused by the envelope (the exporter takes both). 0229: the slab
    # is one cell, 20,15, whose ceiling on foot REACH-1 puts at 4.275 m (a 1 m step two cells off), and 5.2 m high
    try:
        got = []
        for add in (slab, slab + "\n" + good):
            A = dress.parse(text + add + "\n", os.path.basename(art_path))
            A["name"], A["sha256"] = "plant", "-"
            o3 = dress.export(A)
            got.append("no dressing where a player can be" in [c for c, ok, _d in verify(o3, None, D=gcheck.source_rows(o3["W"])) if not ok])
        res.append(("a canopy clear of every head on foot, not of a rider's on a lift", got == [False, True],
                    "the slab alone passes; with a lift under it refused by: no dressing where a player can be" if got == [False, True] else
                    "NOT shown (the slab alone refused: %s; with the lift refused: %s)" % tuple(got)))
    except dress.ArtError as e:
        res.append(("a canopy clear of every head on foot, not of a rider's on a lift", False, "the exporter refused it before the checks could: " + str(e)[:90]))
    # 0229: REACH-1 against 0226's model. Beside the 2.6 m cover at 20,11, 0226's ceiling counted a head on the floor
    # alone (3.275 m), for a climb of the apex alone (1.225 m) never reached the cover; the simulation climbs its apex
    # and a step (1.745833 m, 0257: the tick's apex and a step) from the 1 m steps, stands on the cover and raises a
    # head to 5.625 m there. A slab at 4.5 m over 20,10: clear of 0226's ceiling, not of that head; and one at 6.0 m,
    # clear of both
    for label, add, refused in (("a slab at 4.5 m beside the 2.6 m cover: clear of 0226's ceiling, not of a head on the cover", "canopy plant-r concrete 4.5 20,10 20,10", True),
                                ("  a slab at 6.0 m there passes (the refusal is the height's)", "canopy plant-r concrete 6.0 20,10 20,10", False)):
        try:
            A = dress.parse(text + add + "\n", os.path.basename(art_path))
            A["name"], A["sha256"] = "plant", "-"
            o3 = dress.export(A)
            got = "no dressing where a player can be" in [c for c, ok, _d in verify(o3, None, D=gcheck.source_rows(o3["W"])) if not ok]
            res.append((label, got == refused, ("refused by: no dressing where a player can be" if got else "passed") + (" (the ceiling over 20,10 is %s m)" % o3["scene"]["reach"][10 * w + 20])))
        except dress.ArtError as e:
            res.append((label, False, "the exporter refused it before the checks could: " + str(e)[:90]))
    # 0226: the scene's movers held here apart from the exporter: the brief with a lift, exported, passes every check;
    # each defect planted in its scene is refused by the movers' check, or by the ceiling's
    try:
        A = dress.parse(text + good + "\n", os.path.basename(art_path))
        A["name"], A["sha256"] = "plant", "-"
        o3 = dress.export(A)
    except dress.ArtError as e:
        o3 = None
        res.append(("the brief with a lift passes every check", False, "the exporter refused it: " + str(e)[:90]))
    if o3 is not None:
        D3 = gcheck.source_rows(o3["W"])
        S3 = o3["scene"]
        base_fail = [c for c, ok, _d in verify(o3, None, D=D3) if not ok]
        res.append(("the brief with a lift passes every check", not base_fail, "it did not: " + ", ".join(base_fail) if base_fail else
                    "rules %s, %d mover(s); every check passed" % (S3.get("rules"), len(S3.get("movers", [])))))

        def judged(label, S4, expect):
            failed = [c for c, ok, _d in verify(dict(o3, scene=S4), None, scene_bytes=o3["scene_bytes"], D=D3) if not ok]
            res.append((label, expect in failed, ("refused by: " + expect) if expect in failed else "NOT refused by %r (failed: %s)" % (expect, failed or "nothing")))
        S4 = copy.deepcopy(S3)
        S4["rules"] = 4
        judged("the scene names rules 4, which neither sim.js nor tick_ref.py implements (the handshake)", S4, RULES_CHECK)
        S4 = copy.deepcopy(S3)
        S4["rules"] = 2
        judged("the scene names rules 2, under which a wall can be climbed and the ceiling does not hold", S4, RULES_CHECK)
        S4 = copy.deepcopy(S3)
        S4["movers"][-1]["policy"] = "push"
        judged("the lift given the policy push, along y, in the scene", S4, RULES_CHECK)
        S4 = copy.deepcopy(S3)
        tid = sorted(S4["targets"])[0]
        S4["targets"][tid] = dict(S4["targets"][tid], x=round(S4["targets"][tid]["x"] + cell, 4))
        S4["reach"] = reach_here(S4)
        judged("target %s moved a cell from W's, and the ceiling made to match" % tid, S4, "the art carries no collision and no false ceiling")
        S4 = copy.deepcopy(S3)
        S4["movers"][-1].update(box=[40.0, 0.0, 30.0, 40.25, 2.0, 32.0], axis=[1, 0, 0], len=1024, speed=244)
        S4["reach"] = reach_here(S4)
        judged("a mover past the tunnelling bound, in the scene", S4, RULES_CHECK)
        S4 = copy.deepcopy(S3)
        S4["movers"][-1].update(axis=[0, 0, -1], len=4096 * 3)
        S4["reach"] = reach_here(S4)
        judged("a mover's travel through a wall, in the scene", S4, RULES_CHECK)
        S4 = copy.deepcopy(S3)
        S4["movers"][-1]["box"][0] = 40.1
        judged("a mover's corner not a whole number of 1/256 m, in the scene", S4, RULES_CHECK)
        S4 = copy.deepcopy(S3)
        S4["reach"] = copy.deepcopy(S["reach"])
        judged("the lift's rider left out of the scene's reach ceiling", S4, "the art carries no collision and no false ceiling")
        S4 = copy.deepcopy(S3)
        S4["movers"][-1].update(box=[24.0, 0.0, 32.0, 26.0, 0.5, 34.0], axis=[-1, 0, 0], len=6 * 256)
        S4["reach"] = reach_here(S4)
        judged("a mover's travel through a target's column, in the scene", S4, RULES_CHECK)
        S4 = copy.deepcopy(S3)
        S4["movers"][-1].update(box=[24.0, 0.0, 32.0, 26.0, 0.5, 34.0], axis=[-1, 0, 0], len=6 * 256)
        S4["reach"] = reach_here(S4)
        failed = [c for c, ok, _d in verify(dict(o3, scene=S4, W=dict(o3["W"], targets=[])), None, scene_bytes=o3["scene_bytes"], D=D3) if not ok]
        res.append(("  the same scene over a world without targets passes the movers' check (the refusal is the target's)",
                    RULES_CHECK not in failed, "failed: %s" % (failed or "nothing")))
        S4 = copy.deepcopy(S3)
        del S4["rules"]
        judged("a scene that names no rules", S4, RULES_CHECK)
    return res


# ------------------------------------------------------------------------------------------------ main
def check_brief(name):
    art_path = os.path.join(dress.BRIEFS, name + ".art")
    lines, failed, skipped = [], 0, 0
    try:
        out = dress.export(dress.load(name))
        again = dress.export(dress.load(name))
    except (dress.ArtError, level.MapError) as e:
        print("FAIL %s: the exporter refused the brief: %s" % (name, e))
        return 1, 0
    print("== %s   scene %s   (%d play boxes, %d dressing pieces, %d lights%s)" % (
        name, out["lineage"]["scene_sha256"][:12], out["lineage"]["counts"]["collision"], out["lineage"]["counts"]["visuals"], out["lineage"]["counts"]["lights"],
        (", %d movers under rules %s" % (out["lineage"]["counts"]["movers"], out["scene"]["rules"])) if out["lineage"]["counts"].get("movers") else ""))
    lines.append(("the export is deterministic: the same files, the same bytes", out["scene_bytes"] == again["scene_bytes"] and out["lineage"] == again["lineage"], ""))
    lines += verify(out, art_path)
    try:
        lines.append(("quality: the scene is its frozen reference",) + quality.compare_reference(name, out["lineage"], out["scene_bytes"], quality.read_references()))
    except quality.QualityError as e:
        lines.append(("quality: the scene is its frozen reference", False, str(e)))
    for c, ok, d in lines:
        print("%s %s%s" % ("PASS" if ok else "FAIL", c, (" — " + d) if d else ""))
        failed += 0 if ok else 1
    for w, d in quality.check_scene(out["scene_bytes"])[1]:
        print("NOTE %s: %s" % (w, d))
    for p, refused, by in plants(out, art_path):
        print("%s plant: %s — %s" % ("PASS" if refused else "FAIL", p, by))
        failed += 0 if refused else 1
    # the look revision
    rpath = os.path.join(dress.BRIEFS, name + ".revise-look")
    if os.path.exists(rpath):
        text = open(art_path, encoding="utf-8").read()
        new, keys = revise(text, open(rpath, encoding="utf-8").read(), os.path.basename(rpath))
        A1 = dress.parse(new, name + ".art (revised)")
        A1["name"], A1["sha256"] = name, dress.sha256(new.encode("utf-8"))
        o1 = dress.export(A1)
        ok, d = look_only(out["scene"], o1["scene"], keys)
        print("%s the look revision (%s) changes only the look — %s" % ("PASS" if ok else "FAIL", os.path.basename(rpath), d))
        failed += 0 if ok else 1
        rest = [c for c, okk, _d in verify(o1, None, D=gcheck.source_rows(o1["W"])) if not okk and c != "the lineage binds every input"]
        print("%s the revised scene passes every check — %s" % ("PASS" if not rest else "FAIL", "none failed" if not rest else rest[0]))
        failed += 0 if not rest else 1
        S2 = copy.deepcopy(o1["scene"])
        L = next(L for L in S2["lights"] if L["type"] == "point")
        L["pos"][0] = round(L["pos"][0] + 1.0, 4)
        ok2, d2 = look_only(out["scene"], S2, keys)
        print("%s plant: the look revision also moves a lamp — %s" % ("PASS" if not ok2 else "FAIL", ("refused: " + d2) if not ok2 else "NOT refused"))
        failed += 0 if not ok2 else 1
    # the layout revision
    dpath = os.path.join(dress.BRIEFS, name + ".revise-layout.design")
    if os.path.exists(dpath):
        if not shell_available():
            print("SKIPPED the layout revision (%s): no rustc and no built shell to compile and admit it" % os.path.basename(dpath))
            skipped += 1
        else:
            W0 = out["W"]
            src = W0["source"]
            if "layout" not in src:
                print("FAIL the layout revision: the map's walls are not a design-tool layout")
                failed += 1
            else:
                rtext = open(dpath, "rb").read().replace(b"\r\n", b"\n")
                region = None
                for ln in rtext.decode("utf-8").splitlines():
                    if ln.startswith("# region "):
                        region = [int(v) for v in ln[len("# region "):].replace(",", " ").split()[:4]]
                base = open(os.path.join(level.MAPS, src["layout"].rsplit(".", 1)[0] + ".design"), "rb").read().replace(b"\r\n", b"\n")
                rows, head = compile_revision(base, rtext)
                if rows is None and "SHELL-COMPILE-EMPTY" in head:
                    # the layout already holds the revision (an admitted intent made the same change): nothing to test
                    print("SKIPPED the layout revision (%s): the admitted layout already holds it" % os.path.basename(dpath))
                    skipped += 1
                elif rows is None:
                    print("FAIL the layout revision could not be admitted: %s" % head)
                    failed += 1
                else:
                    tmp = tempfile.mkdtemp(prefix="art-maps-")
                    try:
                        for f in os.listdir(level.MAPS):
                            shutil.copy(os.path.join(level.MAPS, f), tmp)
                        with open(os.path.join(tmp, src["layout"]), "w", encoding="utf-8", newline="\n") as fh:
                            fh.write("; VERDANDI LAYOUT 0\n; a revision for art/check.py, admitted through the design tool\n; head     %s\n" % head)
                            fh.write("\n".join(rows) + "\n")
                        A = dress.load(name)
                        saved = level.MAPS
                        level.MAPS = tmp
                        try:
                            o2 = dress.export(A, maps_dir=tmp)
                            D2 = gcheck.source_rows(o2["W"])
                            res = verify(o2, art_path, D=D2)
                        finally:
                            level.MAPS = saved
                        bad = [c for c, okk, _d in res if not okk]
                        print("%s the layout revision (%s), admitted at head %s, keeps every check — %s" % (
                            "PASS" if not bad else "FAIL", os.path.basename(dpath), head[:12], "none failed" if not bad else bad[0]))
                        failed += 0 if not bad else 1
                        ok, d = layout_local(out["scene"], o2["scene"], region or [0, 0, 10 ** 6, 10 ** 6])
                        print("%s the layout revision stays local — %s" % ("PASS" if ok else "FAIL", d))
                        failed += 0 if ok else 1
                        S3 = copy.deepcopy(o2["scene"])
                        far = next(v for v in S3["visuals"] if v["id"].startswith("skyline:"))
                        far["box"][4] = round(far["box"][4] + 3.0, 4)
                        ok3, d3 = layout_local(out["scene"], S3, region or [0, 0, 10 ** 6, 10 ** 6])
                        print("%s plant: the layout revision also raises a skyline block far away (%s) — %s" % (
                            "PASS" if not ok3 else "FAIL", far["id"], ("refused: " + d3) if not ok3 else "NOT refused"))
                        failed += 0 if not ok3 else 1
                    finally:
                        shutil.rmtree(tmp, ignore_errors=True)
    return failed, skipped


# ------------------------------------------------------------------------------------------------ REACH-1's witness
WITNESS = os.path.join(HERE, "fixtures", "reach")


def check_reach_witness():
    """REACH-1's witness (0257; art/fixtures/reach/): a platform 3.8125 m high and a box 2.0 m high, its near edge off
    the platform's edge by the farthest gap on the 1/256 m grid the tick reaches from it, derived here from the rules.
    The tick lands on the box; both twins count it and keep the head from it under the ceiling; an exact tie is counted
    where the tick may miss it (said, the contract's conservative count, not the tick's own verdict); and the pair test
    before 0257, the parabola's, misses the box (a plant). The number of rows that failed."""
    import tick_ref
    K = tick_ref.K
    text = open(os.path.join(WITNESS, "reachpair.art"), encoding="utf-8").read()
    maps = os.path.join(WITNESS, "maps")

    def export(src):
        A = dress.parse(src, "reachpair.art")
        A["name"], A["sha256"] = "reachpair", dress.sha256(src.encode("utf-8"))
        return dress.export(A, maps)

    out = export(text)
    S = out["scene"]
    print("== reach-witness   scene %s   (art/fixtures/reach: REACH-1's pair test against the tick, 0257)" % out["lineage"]["scene_sha256"][:12])
    rows, failed = [], 0
    g = S["grid"]
    w, cell, tops = g["w"], g["cell"], S["tops"]
    hi = tops[1 * w + 0]
    edge = (1 + max(x for x in range(w) if tops[1 * w + x] == hi)) * cell
    box = S["movers"][0]["box"]
    lo, gap = box[4], box[0] - edge
    tick, P = sim_tick(), S["player"]
    n = ticks_onto(hi, lo, P["step"], tick, P["jump"], P["gravity"])
    far = 2.0 * P["radius"] + n * (P["speed"] * tick)
    derived = math.floor(far * 256) / 256.0
    parabola = 2.0 * P["radius"] + P["speed"] * ((P["jump"] + math.sqrt(P["jump"] ** 2 - 2.0 * P["gravity"] * (lo - P["step"] - hi))) / P["gravity"])
    rows.append(("the box stands off the platform by the farthest gap on the 1/256 m grid the tick reaches (derived from the rules)",
                 gap == derived and far * 256 != math.floor(far * 256) and parabola < gap,
                 "%d ticks, 2r + %d steps = %r m; the box at %r m; the parabola's limit %.6f m" % (n, n, far, gap, parabola)))

    world = tick_ref.World3({"collision": out["C"], "canonical": out["W"]},
                            [{k: m[k] for k in ("id", "box", "axis", "len", "speed", "policy")} for m in S["movers"]])
    x0 = edge + K.radius
    while not ((x0 - edge) * (x0 - edge) < K.radius * K.radius):
        x0 = math.nextafter(x0, 0.0)
    s = tick_ref.State2.new(world, "A")
    s.x, s.feet = x0, world.ground(x0, s.z)
    landed = None
    for k in range(1, 400):
        tick_ref.tick3(world, s, {"r": True, "jump": True} if k == 1 else {"r": True})
        if s.on_ground:
            landed = k if s.feet == lo else None
            break
    rows.append(("the tick lands on the box from the platform's farthest start (graybox/tick_ref.py tick3; r held, the jump at tick 1)",
                 landed == n, "landed at tick %s, x %r" % (landed, s.x) if landed else "it did not land on the box"))

    head, at = -1.0, None
    if landed:
        while s.x < 11.0:                      # the recorded reproduction's jump from the box
            tick_ref.tick3(world, s, {"r": True})
        tick_ref.tick3(world, s, {"jump": True})
        for _k in range(400):
            tick_ref.tick3(world, s, {})
            if s.feet + tick_ref.BODY > head:
                head, at = s.feet + tick_ref.BODY, (int(s.x // cell), int(s.z // cell))
            if s.on_ground:
                break

    def covered(reach):
        return at is not None and reach[at[1] * w + at[0]] is not None and head <= reach[at[1] * w + at[0]] - P["margin"]
    twin = reach_here(S)
    rows.append(("both twins count the box: their ceilings equal, the head from the box under the ceiling less the margin",
                 twin == S["reach"] and covered(S["reach"]),
                 "the head %.6f m over %s, the ceiling %s (less the margin %s)" % (head, at, S["reach"][at[1] * w + at[0]] if at else None, P["margin"])))

    # an exact tie, 2r + n steps = the gap in the reals: counted by both twins, where the tick may not land
    tie_box = "mover box grey 9.25,0,0 13,3.90625,6 along +x travel 0.00390625 speed 0"
    tie_text = "\n".join(tie_box if ln.startswith("mover box ") else ln for ln in text.split("\n"))
    o2 = export(tie_text)
    S2 = o2["scene"]
    n2 = ticks_onto(hi, 3.90625, P["step"], tick, P["jump"], P["gravity"])
    tie = 5 * round(5.25 * 256) == 64 * (14 + n2)
    over = S2["reach"][1 * w + 5]
    box_head = round(3.90625 + P["jump"] ** 2 / (2.0 * P["gravity"]) + P["body"] + P["margin"], 4)
    w2 = tick_ref.World3({"collision": o2["C"], "canonical": o2["W"]},
                         [{k: m[k] for k in ("id", "box", "axis", "len", "speed", "policy")} for m in S2["movers"]])
    s2 = tick_ref.State2.new(w2, "A")
    s2.x, s2.feet = x0, w2.ground(x0, s2.z)
    on = False
    for k in range(1, 400):
        tick_ref.tick3(w2, s2, {"r": True, "jump": True} if k == 1 else {"r": True})
        if s2.on_ground:
            on = s2.feet == 3.90625
            break
    rows.append(("an exact tie is counted (the contract's conservative count, not the tick's own verdict): a box 5.25 m off and 0.09375 m higher, 2r + %d steps exactly" % n2,
                 tie and over == box_head and reach_here(S2) == S2["reach"],
                 "both twins count it (the ceiling over 5,1 the box's head, %s); the tick from the farthest start %s (its binary64 rounding decides a tie)"
                 % (over, "lands on it" if on else "does not land on it")))
    for c, ok, d in rows:
        print("%s %s — %s" % ("PASS" if ok else "FAIL", c, d))
        failed += 0 if ok else 1

    global REACH_PLANT
    saved = (REACH_PLANT, dress.REACH_PLANT)
    REACH_PLANT = dress.REACH_PLANT = "pair-parabola"
    try:
        mv = dress._movers(dress.parse(text, "reachpair.art"), out["W"], out["C"])
        old, _st = dress.reach_ceiling(out["W"], out["C"], mv)
        old_twin = reach_here(S)
    finally:
        REACH_PLANT, dress.REACH_PLANT = saved
    caught = not covered(old) and not covered(old_twin)
    print("%s plant: the pair test before 0257, the parabola's, misses the box — %s" % (
        "PASS" if caught else "FAIL", ("refused: the head %.6f m over %s above the ceiling less the margin (%s, the twin's %s)" % (
            head, at, old[at[1] * w + at[0]], old_twin[at[1] * w + at[0]])) if caught else "NOT refused"))
    failed += 0 if caught else 1
    return failed


def main(argv) -> int:
    # 0242: a console that cannot write a character (a Windows pipe is cp1252; the number-grammar plant's refusal quotes
    # Arabic-Indic digits) writes it escaped rather than stopping the checks there
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    names = [a for a in argv if not a.startswith("--")] or sorted(f[:-4] for f in os.listdir(dress.BRIEFS) if f.endswith(".art"))
    failed = skipped = 0
    for name in names:
        f, s = check_brief(name)
        failed += f
        skipped += s
    if not [a for a in argv if not a.startswith("--")]:
        failed += check_reach_witness()
    verdict = "PASSED" if not failed else "FAILED (%d)" % failed
    print("ART CHECKS %s%s" % (verdict, (", %d SKIPPED" % skipped) if skipped else ""))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
