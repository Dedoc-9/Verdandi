# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/scene_diff_test.py — HELD-0 (0235): the falsifiers of art/scene_diff.py (its theorems T1 to T9), with planted
# defects. Written by MIXER-C beside 0230 and 0231 and taken here with the shapes as MARK-0 keeps them (T9, the
# region's reach, is this build's).
#
#   python art/scene_diff.py selftest            the suite on the module as written, then every planted defect, then
#                                                HELD-0 and COMPARE-0 over HTTP with the scripted director (play.py)
#   python art/scene_diff.py selftest --quick    fewer random cases; --pure: without the HTTP rows
#
# Every property is checked against an oracle written here, apart from the module: projections of a scene for the
# badges, an area oracle (a signed triangle fan clipped by Sutherland-Hodgman) and a boundary-contact oracle for the
# containment test, per-face formulas worked by hand from MARK-0's frame table, and DIRECTOR-0's own scope protocol
# (art/director/scope.py) for which objects a candidate touched. A mutant is a planted defect; the run fails
# unless the suite passes on the module and fails on every mutant. Standard library only; seeded; no clock.

import copy
import hashlib
import importlib.util
import json
import os
import random
import subprocess
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ART = HERE
sys.path.insert(0, os.path.join(ART, "director"))
sys.path.insert(0, ART)
import scope as SCOPE  # noqa: E402  (DIRECTOR-0's scope protocol, the host's own account)
import studio_marks as SM  # noqa: E402  (MARK-0: a kept shape's form)

F = Fraction


def load_module(name="scene_diff_under_test"):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, "scene_diff.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def enc(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


# ------------------------------------------------------------------------------------------------ scenes
MATS = {
    "concrete": {"base": [92, 92, 98], "roughness": 0.86, "metallic": 0.0, "emissive": [0, 0, 0], "emissive_strength": 0.0},
    "stone": {"base": [120, 110, 100], "roughness": 0.9, "metallic": 0.0, "emissive": [0, 0, 0], "emissive_strength": 0.0},
    "glass": {"base": [40, 60, 80], "roughness": 0.1, "metallic": 0.2, "emissive": [0, 0, 0], "emissive_strength": 0.0},
    "housing": {"base": [30, 30, 30], "roughness": 0.5, "metallic": 0.5, "emissive": [0, 0, 0], "emissive_strength": 0.0},
    "neon_a": {"base": [255, 40, 190], "roughness": 0.4, "metallic": 0.0, "emissive": [255, 40, 190], "emissive_strength": 70.0},
}


def r4(x):
    return round(float(x), 4)


def gen_scene(rng):
    w, h, cell, wall = rng.randint(5, 8), rng.randint(5, 8), rng.choice([2.0, 2.5]), 4.0
    tops = [rng.choice([0.0, 0.0, 0.0, 1.0, 2.6, 4.0]) for _ in range(w * h)]
    by = lambda: "%012x" % rng.getrandbits(48)
    visuals, lights, used = [], [], set()

    def place():
        for _ in range(50):
            x, z = rng.randrange(w), rng.randrange(h)
            if (x, z) not in used:
                used.add((x, z))
                return x, z
        return None
    for _ in range(rng.randint(6, 14)):
        p = place()
        if p is None:
            break
        x, z = p
        kind = rng.choice(["tower", "tower", "lamp", "neon", "canopy", "puddle"])
        region = rng.choice(["plaza", "north"])
        s = by()
        if kind == "tower":
            visuals.append({"id": "tower:%d,%d" % (x, z), "by": s, "region": region, "asset": "cube", "material": rng.choice(["concrete", "stone", "glass"]),
                            "box": [r4(x * cell), wall, r4(z * cell), r4((x + 1) * cell), r4(rng.uniform(8, 30)), r4((z + 1) * cell)]})
        elif kind == "lamp":
            y = r4(rng.uniform(3.4, 5.9))
            cx, cz = (x + 0.5) * cell, (z + 0.5) * cell
            i = "lamp:%d,%d" % (x, z)
            visuals.append({"id": i, "by": s, "region": region, "asset": "cube", "material": "housing", "box": [r4(cx - 0.25), y, r4(cz - 0.25), r4(cx + 0.25), r4(y + 0.12), r4(cz + 0.25)]})
            lights.append({"id": i, "by": s, "region": region, "type": "point", "pos": [r4(cx), r4(y - 0.05), r4(cz)], "dir": [0, -1, 0],
                           "color": [255, 200, 150], "candela": r4(rng.uniform(100, 900)), "radius": r4(cell * 6)})
        elif kind == "neon":
            i = "neon:%d,%d:%s" % (x, z, rng.choice("nswe"))
            y = r4(rng.uniform(0.5, 3.0))
            box = [r4(x * cell + 0.3), y, r4(z * cell), r4((x + 1) * cell - 0.3), r4(y + 0.12), r4(z * cell + 0.05)]
            visuals.append({"id": i, "by": s, "region": region, "asset": "cube", "material": "neon_a", "box": box})
            lights.append({"id": i, "by": s, "region": region, "type": "rect", "pos": [r4((box[0] + box[3]) / 2), r4(y + 0.06), r4(box[5] + 0.08)], "dir": [0, 0, 1],
                           "color": [255, 40, 190], "candela": 70.0, "width": r4(cell - 0.6), "height": 0.12, "radius": r4(cell * 4)})
        elif kind == "puddle":
            visuals.append({"id": "puddle:%d,%d" % (x, z), "by": s, "region": region, "asset": "cube", "material": "glass",
                            "box": [r4(x * cell + 0.15), 0.001, r4(z * cell + 0.2), r4((x + 1) * cell - 0.3), 0.008, r4((z + 1) * cell - 0.15)]})
        else:
            x1, z1 = min(w - 1, x + rng.randint(1, 3)), min(h - 1, z + rng.randint(0, 2))
            cid = "canopy:%d,%d-%d,%d" % (x, z, x1, z1)
            y = r4(rng.uniform(5.5, 8.0))
            visuals.append({"id": cid, "by": s, "region": region, "asset": "cube", "material": "concrete",
                            "box": [r4(x * cell), y, r4(z * cell), r4((x1 + 1) * cell), r4(y + 0.4), r4((z1 + 1) * cell)]})
            for k in range(x, x1 + 2, 2):
                visuals.append({"id": "%s:rib%d" % (cid, k), "by": s, "region": region, "asset": "cube", "material": "concrete",
                                "box": [r4(max(k * cell - 0.25, x * cell)), r4(y - 0.8), r4(z * cell), r4(min(k * cell + 0.25, (x1 + 1) * cell)), y, r4((z1 + 1) * cell)]})
            for k in range(x, x1 + 1, 2):
                i = "%s:light%d" % (cid, k)
                px, pz = (k + 0.5) * cell, (z + z1 + 1) / 2.0 * cell
                visuals.append({"id": i, "by": s, "region": region, "asset": "cube", "material": "housing",
                                "box": [r4(px - 0.3), r4(y - 0.1), r4(pz - 0.3), r4(px + 0.3), y, r4(pz + 0.3)]})
                lights.append({"id": i, "by": s, "region": region, "type": "point", "pos": [r4(px), r4(y - 0.15), r4(pz)], "dir": [0, -1, 0],
                               "color": [255, 220, 180], "candela": 600.0, "radius": r4(cell * 7)})
    collision = [{"id": "ground", "kind": "ground", "material": "concrete", "cells": [0, 0, w - 1, h - 1], "box": [0.0, -0.5, 0.0, r4(w * cell), 0.0, r4(h * cell)]}]
    for k in range(rng.randint(1, 4)):
        x, z = rng.randrange(w), rng.randrange(h)
        x1, z1 = min(w - 1, x + rng.randint(0, 2)), z
        kind = rng.choice(["wall", "cover", "raised"])
        top = {"wall": wall, "cover": 2.6, "raised": 1.0}[kind]
        collision.append({"id": "c:%d,%d-%d,%d" % (x, z, x1, z1), "kind": kind, "material": rng.choice(["concrete", "stone"]), "cells": [x, z, x1, z1],
                          "box": [r4(x * cell), 0.0, r4(z * cell), r4((x1 + 1) * cell), top, r4((z1 + 1) * cell)]})
    seen, coll = set(), []
    for c in collision:
        if c["id"] not in seen:
            seen.add(c["id"])
            coll.append(c)
    scene = {"format": "VERDANDI-ART-SCENE", "name": "gen", "title": "A generated scene", "map": "tactical",
             "units": "metres; x east, z south, y up; yaw in degrees, 0 north (-z), 90 east (+x)",
             "grid": {"w": w, "h": h, "cell": cell, "wall": wall}, "tops": tops, "reach": [r4(t + 2.05) for t in tops],
             "player": {"radius": 0.35, "eye": 1.62, "step": 0.55}, "spawns": {"a": {"x": r4(cell / 2), "z": r4(cell / 2), "y": 0.0, "yaw": 90.0}},
             "views": {"hero": {"x": 1.0, "z": 1.0, "y": 1.62, "yaw": 45.0, "pitch": -5.0}},
             "regions": {"plaza": [0, 0, w - 1, h - 1], "north": [0, 0, w - 1, 1]},
             "environment": {"time": "night", "light": "sodium", "fog": 0.02, "exposure": 1.0, "bloom": 0.3, "rain": 0.0},
             "materials": copy.deepcopy(MATS), "assets": {"cube": {"source": "engine", "licence": "own"}},
             "collision": coll, "visuals": sorted(visuals, key=lambda v: v["id"]), "lights": sorted(lights, key=lambda v: v["id"]),
             "rules": 3, "targets": {"t1": {"x": r4(cell * 1.5), "z": r4(cell * 2.5), "y": 0.0}}}
    if rng.random() < 0.4:
        scene["movers"] = [{"id": "deck", "by": by(), "material": "stone", "box": [0.0, 0.0, 0.0, 2.0, 0.5, 2.0], "axis": [1, 0, 0],
                            "len": 512, "speed": 4, "policy": "stop"}]
    return json.loads(json.dumps(scene))


# mutation operators: (name, function(rng, scene) -> bool (applied))
def _pick(rng, lst):
    return rng.choice(lst) if lst else None


def op_vis_box(rng, s):
    v = _pick(rng, s["visuals"])
    if v is None:
        return False
    i = rng.randrange(6)
    v["box"][i] = r4(v["box"][i] + rng.choice([0.0001, -0.0001, 0.001, 1.0, -0.5]))
    if v["box"][i % 3 + 3] <= v["box"][i % 3]:
        v["box"][i % 3 + 3] = r4(v["box"][i % 3] + 0.5)
    return True


def op_vis_material(rng, s):
    v = _pick(rng, s["visuals"])
    if v is None:
        return False
    v["material"] = rng.choice([m for m in s["materials"] if m != v["material"]])
    return True


def op_vis_by(rng, s):
    v = _pick(rng, s["visuals"])
    if v is None:
        return False
    v["by"] = "%012x" % rng.getrandbits(48)
    return True


def op_vis_region(rng, s):
    v = _pick(rng, s["visuals"])
    if v is None:
        return False
    v["region"] = "north" if v["region"] != "north" else "plaza"
    for L in s["lights"]:
        if L["id"] == v["id"]:
            L["region"] = v["region"]
    return True


def op_vis_asset(rng, s):
    v = _pick(rng, s["visuals"])
    if v is None:
        return False
    v["asset"] = "bevel"
    s["assets"]["bevel"] = {"source": "own", "licence": "own"}
    return True


def op_vis_add(rng, s):
    g = s["grid"]
    for _ in range(30):
        x, z = rng.randrange(g["w"]), rng.randrange(g["h"])
        i = "tower:%d,%d" % (x, z)
        if all(v["id"] != i for v in s["visuals"]):
            c = g["cell"]
            s["visuals"].append({"id": i, "by": "%012x" % rng.getrandbits(48), "region": "plaza", "asset": "cube", "material": "stone",
                                 "box": [r4(x * c), 4.0, r4(z * c), r4((x + 1) * c), r4(rng.uniform(8, 20)), r4((z + 1) * c)]})
            return True
    return False


def op_canopy_add(rng, s):
    g = s["grid"]
    c = g["cell"]
    x, z = rng.randrange(g["w"] - 1), rng.randrange(g["h"])
    cid = "canopy:%d,%d-%d,%d" % (x, z, x + 1, z)
    if any(v["id"].startswith(cid) for v in s["visuals"]):
        return False
    y = 7.25
    s["visuals"].append({"id": cid, "by": "feedfeedfeed", "region": "plaza", "asset": "cube", "material": "concrete",
                         "box": [r4(x * c), y, r4(z * c), r4((x + 2) * c), r4(y + 0.4), r4((z + 1) * c)]})
    for k in (x, x + 2):
        s["visuals"].append({"id": "%s:rib%d" % (cid, k), "by": "feedfeedfeed", "region": "plaza", "asset": "cube", "material": "concrete",
                             "box": [r4(max(k * c - 0.25, x * c)), r4(y - 0.8), r4(z * c), r4(min(k * c + 0.25, (x + 2) * c)), y, r4((z + 1) * c)]})
    i = "%s:light%d" % (cid, x)
    s["visuals"].append({"id": i, "by": "feedfeedfeed", "region": "plaza", "asset": "cube", "material": "housing",
                         "box": [r4((x + 0.5) * c - 0.3), r4(y - 0.1), r4((z + 0.5) * c - 0.3), r4((x + 0.5) * c + 0.3), y, r4((z + 0.5) * c + 0.3)]})
    s["lights"].append({"id": i, "by": "feedfeedfeed", "region": "plaza", "type": "point", "pos": [r4((x + 0.5) * c), r4(y - 0.15), r4((z + 0.5) * c)],
                        "dir": [0, -1, 0], "color": [255, 220, 180], "candela": 600.0, "radius": r4(c * 7)})
    return True


def op_vis_remove(rng, s):
    v = _pick(rng, s["visuals"])
    if v is None:
        return False
    s["visuals"] = [x for x in s["visuals"] if x["id"] != v["id"]]
    s["lights"] = [L for L in s["lights"] if L["id"] != v["id"]]
    return True


def op_light_color(rng, s):
    L = _pick(rng, s["lights"])
    if L is None:
        return False
    L["color"] = [rng.randrange(256), rng.randrange(256), rng.randrange(256)]
    return True


def op_light_type(rng, s):
    L = _pick(rng, [x for x in s["lights"] if x["type"] == "rect"])
    if L is None:
        return False
    L["type"] = "point"
    del L["width"], L["height"]
    return True


def op_mat_change(rng, s):
    n = rng.choice(sorted(s["materials"]))
    m = s["materials"][n]
    m["roughness"] = r4(rng.uniform(0, 1))
    if n == "neon_a":                       # the neon's lights follow their material's emission, as the exporter's do
        m["emissive_strength"] = r4(rng.uniform(10, 90))
        for L in s["lights"]:
            if L["id"].startswith("neon:"):
                L["candela"] = m["emissive_strength"]
    return True


def op_mat_add(rng, s):
    s["materials"]["paint_%d" % rng.randrange(100)] = {"base": [1, 2, 3], "roughness": 0.5, "metallic": 0.0, "emissive": [0, 0, 0], "emissive_strength": 0.0}
    return True


def op_env(rng, s):
    s["environment"][rng.choice(["fog", "exposure", "bloom", "rain"])] = r4(rng.uniform(0, 2))
    return True


def op_env_int(rng, s):
    s["environment"]["rain"] = 0 if s["environment"]["rain"] == 0.0 and isinstance(s["environment"]["rain"], float) else 0.0
    return True


def op_title(rng, s):
    s["title"] = "Another title %d" % rng.randrange(1000)
    return True


def op_coll_box(rng, s):
    c = _pick(rng, s["collision"][1:])
    if c is None:
        return False
    c["box"][4] = r4(c["box"][4] + 0.5)
    return True


def op_coll_material(rng, s):
    c = _pick(rng, s["collision"])
    c["material"] = "stone" if c["material"] != "stone" else "concrete"
    return True


def op_coll_add(rng, s):
    g = s["grid"]
    i = "c:%d,%d-%d,%d" % (g["w"] - 1, g["h"] - 1, g["w"] - 1, g["h"] - 1)
    if any(c["id"] == i for c in s["collision"]):
        return False
    c0 = g["cell"]
    s["collision"].append({"id": i, "kind": "cover", "material": "concrete", "cells": [g["w"] - 1, g["h"] - 1, g["w"] - 1, g["h"] - 1],
                           "box": [r4((g["w"] - 1) * c0), 0.0, r4((g["h"] - 1) * c0), r4(g["w"] * c0), 2.6, r4(g["h"] * c0)]})
    return True


def op_tops(rng, s):
    k = rng.randrange(len(s["tops"]))
    s["tops"][k] = 2.6 if s["tops"][k] != 2.6 else 1.0
    return True


def op_tops_negzero(rng, s):
    ks = [k for k, t in enumerate(s["tops"]) if t == 0.0 and str(t) == "0.0"]
    if not ks:
        return False
    s["tops"][rng.choice(ks)] = -0.0
    return True


def op_target(rng, s):
    s["targets"]["t1"]["x"] = r4(s["targets"]["t1"]["x"] + s["grid"]["cell"])
    return True


def op_spawn(rng, s):
    s["spawns"]["a"]["yaw"] = r4(s["spawns"]["a"]["yaw"] + 90.0)
    return True


def op_mover_speed(rng, s):
    if not s.get("movers"):
        return False
    s["movers"][0]["speed"] += 1
    return True


def op_mover_material(rng, s):
    if not s.get("movers"):
        return False
    s["movers"][0]["material"] = "concrete"
    return True


def op_mover_by(rng, s):
    if not s.get("movers"):
        return False
    s["movers"][0]["by"] = "%012x" % rng.getrandbits(48)
    return True


def op_mover_add(rng, s):
    if s.get("movers"):
        return False
    s["movers"] = [{"id": "lift", "by": "abcdefabcdef", "material": "stone", "box": [2.0, 0.0, 2.0, 4.0, 0.5, 4.0], "axis": [0, 1, 0],
                    "len": 256, "speed": 2, "policy": "stop"}]
    return True


def op_rules(rng, s):
    s["rules"] = 2
    return True


def op_grid(rng, s):
    s["player"]["step"] = 0.6
    return True


def op_reach(rng, s):
    s["reach"][0] = r4(s["reach"][0] + 0.25)
    return True


def op_view(rng, s):
    s["views"]["hero"]["yaw"] = r4(s["views"]["hero"]["yaw"] + 10)
    return True


def op_region_bounds(rng, s):
    s["regions"]["north"] = [0, 0, s["grid"]["w"] - 1, 2]
    return True


OPS = [op_vis_box, op_vis_material, op_vis_by, op_vis_region, op_vis_asset, op_vis_add, op_canopy_add, op_vis_remove, op_light_color,
       op_light_type, op_mat_change, op_mat_add, op_env, op_env_int, op_title, op_coll_box, op_coll_material, op_coll_add, op_tops,
       op_tops_negzero, op_target, op_spawn, op_mover_speed, op_mover_material, op_mover_by, op_mover_add, op_rules, op_grid, op_reach,
       op_view, op_region_bounds]


def gen_pair(rng):
    a = gen_scene(rng)
    b = copy.deepcopy(a)
    names = []
    for _ in range(rng.choice([0, 1, 1, 1, 2, 3])):
        op = rng.choice(OPS)
        if op(rng, b):
            names.append(op.__name__)
    b["visuals"].sort(key=lambda v: v["id"])
    b["lights"].sort(key=lambda v: v["id"])
    return a, json.loads(json.dumps(b)), names


def shuffled(rng, s):
    t = copy.deepcopy(s)
    for k in ("visuals", "lights", "collision", "movers"):
        if k in t:
            rng.shuffle(t[k])
    return t


# ------------------------------------------------------------------------------------------------ oracles
NONPLAY = ("visuals", "lights", "materials", "environment", "views", "regions", "assets", "reach", "format", "name", "title", "units")


def o_look(s):
    return {"visuals": {v["id"]: v.get("material") for v in s.get("visuals", [])}, "collision": {c["id"]: c.get("material") for c in s.get("collision", [])},
            "movers": {m["id"]: m.get("material") for m in s.get("movers", [])}, "lights": {L["id"]: L for L in s.get("lights", [])},
            "materials": s.get("materials", {}), "environment": s.get("environment", {})}


def o_play(s):
    out = {"collision": {c["id"]: {k: c[k] for k in c if k != "material"} for c in s.get("collision", [])},
           "movers": {m["id"]: {k: m[k] for k in m if k not in ("material", "by")} for m in s.get("movers", [])}}
    for k in s:
        if k not in NONPLAY and k not in ("collision", "movers"):
            out[k] = s[k]
    return out


def o_place(s):
    return {v["id"]: {k: v[k] for k in v if k not in ("material", "by", "region")} for v in s.get("visuals", [])}


def o_ccw(t):
    a, b, c = t
    o = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return (o > 0) - (o < 0), (t if o > 0 else (a, c, b))


def o_clip_halfplane(poly, inside, cut):
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        ip, iq = inside(p), inside(q)
        if ip:
            out.append(p)
        if ip != iq:
            out.append(cut(p, q))
    return out


def o_clip_rect(poly, rect):
    x0, x1, y0, y1 = rect

    def cx(xv):
        return lambda p, q: (xv, p[1] + (q[1] - p[1]) * (xv - p[0]) / (q[0] - p[0]))

    def cy(yv):
        return lambda p, q: (p[0] + (q[0] - p[0]) * (yv - p[1]) / (q[1] - p[1]), yv)
    for inside, cut in ((lambda p: p[0] >= x0, cx(x0)), (lambda p: p[0] <= x1, cx(x1)), (lambda p: p[1] >= y0, cy(y0)), (lambda p: p[1] <= y1, cy(y1))):
        if not poly:
            return []
        poly = o_clip_halfplane(poly, inside, cut)
    return poly


def o_area(poly):
    n = len(poly)
    return abs(sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))) / 2 if n >= 3 else F(0)


def o_area_in_rect(P, rect):
    """|sum over the fan's triangles of sign * area(triangle clipped by the rectangle)|: the area of P in the rectangle
    for any simple polygon, convex or not (the fan's signed indicators sum to P's winding number)."""
    tot = F(0)
    for i in range(1, len(P) - 1):
        sgn, t = o_ccw((P[0], P[i], P[i + 1]))
        if sgn:
            tot += sgn * o_area(o_clip_rect(list(t), rect))
    return abs(tot)


def o_seg_seg(a, b, c, d):
    """Do closed segments ab and cd share a point? Solved parametrically, exactly."""
    r = (b[0] - a[0], b[1] - a[1])
    s = (d[0] - c[0], d[1] - c[1])
    den = r[0] * s[1] - r[1] * s[0]
    qp = (c[0] - a[0], c[1] - a[1])
    if den == 0:
        if qp[0] * r[1] - qp[1] * r[0] != 0:
            return False                       # parallel, apart
        rr = r[0] * r[0] + r[1] * r[1]
        if rr == 0:
            return a == c or a == d or (s[0] * s[0] + s[1] * s[1] > 0 and o_seg_seg(c, d, a, b))
        t0 = (qp[0] * r[0] + qp[1] * r[1]) / rr
        t1 = t0 + (s[0] * r[0] + s[1] * r[1]) / rr
        return max(F(0), min(t0, t1)) <= min(F(1), max(t0, t1))
    t = (qp[0] * s[1] - qp[1] * s[0]) / den
    u = (qp[0] * r[1] - qp[1] * r[0]) / den
    return 0 <= t <= 1 and 0 <= u <= 1


def o_rel2(P, closed, rect):
    x0, x1, y0, y1 = rect
    R4 = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    RE = [(R4[i], R4[(i + 1) % 4]) for i in range(4)]
    PE = [(P[i], P[(i + 1) % len(P)]) for i in range(len(P) if closed else len(P) - 1)]
    if not closed:
        meet = any(o_seg_seg(a, b, c, d) for a, b in PE for c, d in RE) or any(x0 <= a[0] <= x1 and y0 <= a[1] <= y1 for a, _b in PE)
        return False, False, meet
    A = o_area_in_rect(P, rect)
    inside = A == (x1 - x0) * (y1 - y0)
    overlap = A > 0
    meet = overlap or any(o_seg_seg(a, b, c, d) for a, b in PE for c, d in RE)
    return inside, overlap, meet


def o_simple(P):
    n = len(P)
    E = [(P[i], P[(i + 1) % n]) for i in range(n)]
    if any(a == b for a, b in E):
        return False
    for i in range(n):
        for j in range(i + 1, n):
            if j == i + 1 or (i == 0 and j == n - 1):
                continue
            if o_seg_seg(E[i][0], E[i][1], E[j][0], E[j][1]):
                return False
    return 2 * o_area(P) > 0


# per-face local coordinates worked by hand from SPEC's table (A the anchor box, B a world box): ranges of (a, b, t)
def o_local(face, A, B):
    if face == "+x":
        return (A[5] - B[5], A[5] - B[2]), (B[1] - A[1], B[4] - A[1]), (B[0] - A[3], B[3] - A[3])
    if face == "-x":
        return (B[2] - A[2], B[5] - A[2]), (B[1] - A[1], B[4] - A[1]), (A[0] - B[3], A[0] - B[0])
    if face == "+z":
        return (B[0] - A[0], B[3] - A[0]), (B[1] - A[1], B[4] - A[1]), (B[2] - A[5], B[5] - A[5])
    if face == "-z":
        return (A[3] - B[3], A[3] - B[0]), (B[1] - A[1], B[4] - A[1]), (A[2] - B[5], A[2] - B[2])
    if face == "+y":
        return (B[0] - A[0], B[3] - A[0]), (A[5] - B[5], A[5] - B[2]), (B[1] - A[4], B[4] - A[4])
    return (B[0] - A[0], B[3] - A[0]), (B[2] - A[2], B[5] - A[2]), (A[1] - B[4], A[1] - B[1])


OUTWARD = {"+x": (1, 0, 0), "-x": (-1, 0, 0), "+y": (0, 1, 0), "-y": (0, -1, 0), "+z": (0, 0, 1), "-z": (0, 0, -1)}


def o_classify(face, A, B, P, closed, T):
    (a0, a1), (b0, b1), (s0, s1) = o_local(face, A, B)
    inside2, overlap2, meet2 = o_rel2(P, closed, (a0, a1, b0, b1))
    T0, T1 = T
    if closed and inside2 and T0 <= s0 and s1 <= T1:
        return "inside"
    if overlap2 and min(s1, T1) - max(s0, T0) > 0:
        return "crossing"
    if meet2 and min(s1, T1) - max(s0, T0) >= 0:
        return "touching"
    return "outside"


# ------------------------------------------------------------------------------------------------ polygons
def mm(n):
    return F(n, 1000)


def gen_polygon(rng, W=6000, H=6000):
    """A simple polygon on the millimetre grid: star-shaped (often not convex), or an L, U or T of random size."""
    for _ in range(200):
        kind = rng.random()
        if kind < 0.55:
            k = rng.randint(3, 9)
            cx, cy = rng.randint(1500, W - 1500), rng.randint(1500, H - 1500)
            angs = sorted(rng.sample(range(0, 360), k))
            import math
            P = [(mm(cx + int(round(rr * math.cos(math.radians(t))))), mm(cy + int(round(rr * math.sin(math.radians(t))))))
                 for t, rr in ((t, rng.randint(200, 1500)) for t in angs)]
        else:
            x0, y0 = rng.randint(0, 1500), rng.randint(0, 1500)
            x3, y3 = rng.randint(x0 + 1500, W), rng.randint(y0 + 1500, H)
            x1, x2 = sorted(rng.sample(range(x0 + 1, x3), 2))
            y1 = rng.randint(y0 + 1, y3 - 1)
            shape = rng.choice("LUT")
            if shape == "L":
                pts = [(x0, y0), (x3, y0), (x3, y1), (x1, y1), (x1, y3), (x0, y3)]
            elif shape == "U":
                pts = [(x0, y0), (x3, y0), (x3, y3), (x2, y3), (x2, y1), (x1, y1), (x1, y3), (x0, y3)]
            else:
                pts = [(x0, y1), (x1, y1), (x1, y0), (x2, y0), (x2, y1), (x3, y1), (x3, y3), (x0, y3)]
            P = [(mm(x), mm(y)) for x, y in pts]
        if rng.random() < 0.5:
            P = P[::-1]
        if o_simple(P):
            return P
    raise RuntimeError("no simple polygon")


def gen_rect(rng, P):
    if rng.random() < 0.35:                  # a small rectangle about a point of the polygon's bounding box: often inside
        x0, x1 = min(p[0] for p in P), max(p[0] for p in P)
        y0, y1 = min(p[1] for p in P), max(p[1] for p in P)
        cx = x0 + (x1 - x0) * F(rng.randint(0, 1000), 1000)
        cy = y0 + (y1 - y0) * F(rng.randint(0, 1000), 1000)
        hw, hh = mm(rng.randint(1, 600)), mm(rng.randint(1, 600))
        return (cx - hw, cx + hw, cy - hh, cy + hh)
    xs = sorted({p[0] for p in P}) + [mm(rng.randint(0, 6000)) for _ in range(3)]
    ys = sorted({p[1] for p in P}) + [mm(rng.randint(0, 6000)) for _ in range(3)]
    for _ in range(100):
        a, b = rng.choice(xs) + mm(rng.choice([0, 0, 0, 1, -1, 250])), rng.choice(xs) + mm(rng.choice([0, 0, 1, -1, -250]))
        c, d = rng.choice(ys) + mm(rng.choice([0, 0, 0, 1, -1, 250])), rng.choice(ys) + mm(rng.choice([0, 0, 1, -1, -250]))
        if a != b and c != d:
            return (min(a, b), max(a, b), min(c, d), max(c, d))
    return (mm(0), mm(1), mm(0), mm(1))


# ------------------------------------------------------------------------------------------------ the suite
class Fail(Exception):
    pass


def check(cond, what):
    if not cond:
        raise Fail(what)


def t1_determinism(SD, rng, N):
    for _ in range(N):
        a, b, names = gen_pair(rng)
        d1, d2 = SD.diff(a, b), SD.diff(a, b)
        check(enc(d1) == enc(d2), "T1 diff twice differs")
        a2, b2 = shuffled(rng, a), shuffled(rng, b)
        check(enc(SD.diff(a2, b2)) == enc(d1), "T1 diff changes with the order of the scene's lists (%s)" % names)
        reg = region_for(SD, a, rng)
        if reg is not None:
            check(enc(SD.account(d1, a, b, reg)) == enc(SD.account(SD.diff(a2, b2), a2, b2, reg)), "T1 account changes with list order")


def t2_inverse(SD, rng, N):
    for _ in range(N):
        a, b, names = gen_pair(rng)
        d = SD.diff(a, b)
        check(enc(SD.invert(d)) == enc(SD.diff(b, a)), "T2 invert(diff(a,b)) != diff(b,a) (%s)" % names)
        check(enc(SD.invert(SD.invert(d))) == enc(d), "T2 invert is not an involution")


def t3_completeness(SD, rng, N):
    for _ in range(N):
        a, b, names = gen_pair(rng)
        d = SD.diff(a, b)
        out = SD.apply(d, a, verify=False)
        check(enc(SD.canon(out)) == enc(SD.canon(b)), "T3 apply(diff(a,b), a) != b (%s)" % names)
        check(enc(SD.apply_objects(d, SD.object_records(a))) == enc(SD.object_records(b)), "T3 objects(a) + diff != objects(b) (%s)" % names)
        if enc(SD.canon(a)) != enc(SD.canon(b)):
            try:
                SD.apply(d, b)
                check(False, "T3 a diff applied to the wrong base was not refused")
            except SD.DiffError as e:
                check(e.code == "SCENE-DIFF-STALE", "T3 wrong refusal %s" % e.code)


def sub_diff(rng, d):
    s = json.loads(json.dumps(d))
    for sec in list(s):
        if isinstance(s[sec], dict) and set(s[sec]) == {"added", "removed", "changed"}:
            for part in ("added", "removed", "changed"):
                for k in sorted(s[sec][part]):
                    if rng.random() < 0.5:
                        del s[sec][part][k]
                    elif part == "changed" and "fields" in s[sec][part][k]:
                        for f in sorted(s[sec][part][k]["fields"]):
                            if rng.random() < 0.5:
                                del s[sec][part][k]["fields"][f]
    for f in sorted(s.get("top", {})):
        if rng.random() < 0.5:
            del s["top"][f]
    return s


def t4_badges(SD, rng, N):
    seen = {"M": 0, "C": 0, "P": 0}
    for _ in range(N):
        a, b, names = gen_pair(rng)
        d = SD.diff(a, b)
        bd = SD.badges(d)
        want = {"M": enc(o_look(a)) != enc(o_look(b)), "C": enc(o_play(a)) != enc(o_play(b)), "P": enc(o_place(a)) != enc(o_place(b))}
        check(bd == want, "T4 badges %s, the projections say %s (%s)" % (bd, want, names))
        for k in seen:
            seen[k] += bd[k]
        for _r in range(3):
            sb = SD.badges(sub_diff(rng, d))
            check(all(sb[k] <= bd[k] for k in bd), "T4 a sub-diff raised a badge its diff does not (%s)" % names)
    return seen


def t5_containment_2d(SD, rng, N):
    counts = {}
    for _ in range(N):
        P = gen_polygon(rng)
        rect = gen_rect(rng, P)
        got = SD.rel2(P, True, rect)
        want = o_rel2(P, True, rect)
        check(tuple(got) == tuple(want), "T5 rel2 %s, oracle %s, P=%s rect=%s" % (got, want, [(str(x), str(y)) for x, y in P], [str(x) for x in rect]))
        key = "inside" if want[0] else "overlap" if want[1] else "meet" if want[2] else "apart"
        counts[key] = counts.get(key, 0) + 1
        path = P[:rng.randint(2, len(P))]
        g2, w2 = SD.rel2(path, False, rect), o_rel2(path, False, rect)
        check(tuple(g2) == tuple(w2), "T5 path rel2 %s, oracle %s" % (g2, w2))
    return counts


def t5_frames(SD, rng, N):
    counts = {}
    for _ in range(N):
        face = rng.choice(sorted(OUTWARD))
        A = [mm(rng.randint(0, 20000)), mm(rng.randint(0, 3000)), mm(rng.randint(0, 20000))]
        A += [A[0] + mm(rng.randint(500, 8000)), A[1] + mm(rng.randint(500, 6000)), A[2] + mm(rng.randint(500, 8000))]
        Af = [float(x) for x in A]                       # the scene's numbers (whole millimetres, exact as decimals)
        fr = SD.frame(Af, face)
        check(tuple(fr["n"]) == OUTWARD[face], "T5 frame %s: u x v = %s, not the outward normal" % (face, fr["n"]))
        lb = SD.local_box(fr, Af)
        (oa, ob, ot) = o_local(face, A, A)
        check(lb == (oa[0], oa[1], ob[0], ob[1], ot[0], ot[1]), "T5 frame %s: the anchor's own box reads %s" % (face, lb))
        check(lb[0] == 0 and lb[1] == fr["W"] and lb[2] == 0 and lb[3] == fr["H"] and lb[5] == 0, "T5 frame %s: the face is not [0,W]x[0,H] at t=0" % face)
        Wm, Hm = int(fr["W"] * 1000), int(fr["H"] * 1000)
        P = gen_polygon(rng, Wm, Hm) if Wm >= 3100 and Hm >= 3100 else [(mm(0), mm(0)), (mm(Wm), mm(0)), (mm(Wm // 2), mm(Hm))]
        for (u, v) in P[:3]:
            wp = SD.world(fr, (u, v))
            la = SD.local_point(fr, wp)
            check(la == (u, v, 0), "T5 frame %s: world() and local_point() disagree" % face)
        T = (mm(-rng.randint(0, 3000)), mm(rng.randint(0, 3000)))
        reg = {"name": "t", "frame": fr, "poly": P, "closed": True, "t": T}
        for _k in range(4):
            # a world box near the face: from the polygon's coordinates and the interval's ends, sometimes one mm off
            (ra0, ra1, rb0, rb1) = gen_rect(rng, P)
            s0 = rng.choice([T[0], T[1], mm(0), T[0] - mm(1), T[1] + mm(1), mm(rng.randint(-4000, 4000)), T[0], T[0] + mm(1)])
            s1 = s0 + mm(rng.choice([1, 500, 2000, 6000]))
            if rng.random() < 0.4 and T[1] > s0 >= T[0]:
                s1 = min(s1, T[1])                   # within the interval: an inside box possible
            B = to_world(face, A, (ra0, ra1), (rb0, rb1), (s0, s1))
            got = SD.classify([float(x) for x in B], reg)
            want = o_classify(face, A, B, P, True, T)
            check(got == want, "T5 classify %s on %s, the oracle %s" % (got, face, want))
            counts[want] = counts.get(want, 0) + 1
    return counts


def to_world(face, A, ar, br, tr):
    """The world box whose local ranges are ar, br, tr: o_local inverted, case by case."""
    (a0, a1), (b0, b1), (t0, t1) = ar, br, tr
    if face == "+x":
        return [A[3] + t0, A[1] + b0, A[5] - a1, A[3] + t1, A[1] + b1, A[5] - a0]
    if face == "-x":
        return [A[0] - t1, A[1] + b0, A[2] + a0, A[0] - t0, A[1] + b1, A[2] + a1]
    if face == "+z":
        return [A[0] + a0, A[1] + b0, A[5] + t0, A[0] + a1, A[1] + b1, A[5] + t1]
    if face == "-z":
        return [A[3] - a1, A[1] + b0, A[2] - t1, A[3] - a0, A[1] + b1, A[2] - t0]
    if face == "+y":
        return [A[0] + a0, A[4] + t0, A[5] - b1, A[0] + a1, A[4] + t1, A[5] - b0]
    return [A[0] + a0, A[1] - t1, A[2] + b0, A[0] + a1, A[1] - t0, A[2] + b1]


def t5_cases(SD):
    """Worked cases: a notch of an L (not convex), the exact decimals 0.1 + 0.2 = 0.3, a path, a light's point."""
    A = [0.1, 0.0, 0.0, 1.3, 1.0, 1.0]
    fr = SD.frame(A, "-y")                     # origin (0.1, 0, 0), u = +x, v = +z, n = -y
    sq = [(F(0), F(0)), (F("0.2"), F(0)), (F("0.2"), F("0.2")), (F(0), F("0.2"))]
    reg = {"name": "sq", "frame": fr, "poly": sq, "closed": True, "t": (F(-1), F(1))}
    check(SD.classify([0.3, -0.5, 0.05, 0.5, 0.5, 0.1], reg) == "touching", "T5 a box whose face is x = 0.3 touches a region ending at 0.1 + 0.2")
    check(SD.classify([0.29, -0.5, 0.05, 0.5, 0.5, 0.1], reg) == "crossing", "T5 a box from x = 0.29 crosses it")
    check(SD.classify([0.1, -0.5, 0.0, 0.3, 0.5, 0.2], reg) == "inside", "T5 the region's own footprint is inside it")
    L = [(F(0), F(0)), (F(4), F(0)), (F(4), F(1)), (F(1), F(1)), (F(1), F(4)), (F(0), F(4))]
    A2 = [0.0, 0.0, 0.0, 5.0, 5.0, 5.0]
    regL = {"name": "L", "frame": SD.frame(A2, "-y"), "poly": L, "closed": True, "t": (F(-1), F(1))}
    check(SD.classify([2.0, -0.5, 2.0, 3.0, 0.5, 3.0], regL) == "outside", "T5 a box in the notch of an L is outside it (its hull would hold it)")
    check(SD.classify([1.0, -0.5, 1.0, 3.0, 0.5, 3.0], regL) == "touching", "T5 a box at the L's inner corner touches it")
    check(SD.classify([0.0, -0.5, 0.0, 1.0, 0.5, 4.0], regL) == "inside", "T5 the L's west arm is inside it")
    path = {"name": "p", "frame": SD.frame(A2, "-y"), "poly": [(F(0), F(0)), (F(4), F(4))], "closed": False, "t": (F(-1), F(1))}
    check(SD.classify([1.0, -0.5, 1.0, 2.0, 0.5, 2.0], path) == "touching", "T5 a path through a box touches it")
    check(SD.classify([3.0, -0.5, 0.0, 4.0, 0.5, 1.0], path) == "outside", "T5 a path beside a box misses it")
    check(SD.classify([2.0, 0.0, 2.0, 2.0, 0.0, 2.0], path) == "touching", "T5 a point on a path touches it")
    check(SD.classify([0.5, 0.0, 0.5, 0.5, 0.0, 0.5], regL) == "inside", "T5 a light's point in the L is inside it")


def t5_path_never_inside(SD, rng, N):
    for _ in range(N):
        P = gen_polygon(rng)
        path = P[:rng.randint(2, len(P))]
        rect = gen_rect(rng, P)
        reg = {"name": "p", "frame": SD.frame([0.0, 0.0, 0.0, 9.0, 9.0, 9.0], "-y"), "poly": path, "closed": False, "t": (F(-1), F(1))}
        box = [float(rect[0]), -0.5, float(rect[2]), float(rect[1]), 0.5, float(rect[3])]
        check(SD.classify(box, reg) in ("touching", "outside"), "T5 a path held a box or crossed it")


def shape_on(piece, face, box, verts, op="region", within=True, reach=None):
    """A kept shape (VERDANDI-SHAPES 0, as art/studio_marks.py parse writes it): its box as exact decimals, its vertices
    in integer millimetres, its reach in millimetres or "" for the face's default."""
    return {"name": "s", "operation": op,
            "anchor": {"piece": piece, "face": face, "box": [SM.dec(SM.exact(x, "box")) for x in box], "scene": "", "view": {}},
            "vertices": [[str(SM.mm(u, "u")), str(SM.mm(v, "v"))] for u, v in verts],
            "constraints": {"within": within, "supports": False, "collision": False, "material": "keep", "clearance_mm": "",
                            "reach_mm": "" if reach is None else str(SM.mm(reach, "reach"))}, "note": ""}


def t6_shapes(SD, rng):
    a = gen_scene(rng)
    v = a["visuals"][0]
    s = shape_on(v["id"], "+y", v["box"], [[0, 0], [0.4, 0], [0.4, 0.4]])
    check(SD.shape_status(s, a) == "ok", "T6 a shape on the box it was marked on is not ok")
    b = copy.deepcopy(a)
    b["visuals"][0]["box"][0] = r4(b["visuals"][0]["box"][0] + 0.001)
    check(SD.shape_status(s, b) == "changed", "T6 an anchor moved 1 mm is not changed")
    try:
        SD.region(s, b)
        check(False, "T6 a changed shape was used as a region")
    except SD.DiffError as e:
        check(e.code == "STUDIO-SHAPE", "T6 wrong refusal %s" % e.code)
    c = copy.deepcopy(a)
    c["visuals"] = c["visuals"][1:]
    check(SD.shape_status(s, c) == "gone", "T6 an anchor that is gone is not gone")
    play = shape_on("play:ground", "+y", a["collision"][0]["box"], [[0, 0], [1, 0], [1, 1]])
    check(SD.shape_status(play, a) == "ok", "T6 a play anchor is not found")
    W = 0.4
    for verts, why in (([[0, 0], [W, W], [W, 0], [0, W]], "a bow tie"), ([[0, 0], [0.3, 0], [0.1, 0], [0.1, 0.3]], "a spike"),
                       ([[0, 0], [0.2, 0], [0.2, 0]], "a zero-length edge"), ([[0, 0], [0.1, 0], [0.2, 0]], "no area")):
        bad = shape_on(v["id"], "+y", v["box"], verts)
        try:
            SD.region(bad, a)
            check(False, "T6 %s was admitted as a shape" % why)
        except SD.DiffError as e:
            check(e.code == "STUDIO-SHAPE", "T6 %s: wrong refusal %s" % (why, e.code))
    big = shape_on(v["id"], "+y", v["box"], [[0, 0], [100, 0], [100, 100]])
    try:
        SD.region(big, a)
        check(False, "T6 a shape outside its face was admitted")
    except SD.DiffError:
        pass
    try:                                            # a vertex finer than a millimetre is refused by the form itself
        shape_on(v["id"], "+y", v["box"], [[0, 0], [0.1, 0], [0.1, 0.0005]])
        check(False, "T6 a vertex finer than a millimetre was kept")
    except SM.ShapeError:
        pass


def region_for(SD, scene, rng):
    """A region over the scene's ground: a random simple polygon on its top face, 6 m each side."""
    g = [c for c in scene["collision"] if c["id"] == "ground"][0]
    fr = SD.frame(g["box"], "+y")
    Wm, Hm = int(fr["W"] * 1000), int(fr["H"] * 1000)
    if Wm < 3100 or Hm < 3100:
        return None
    s = shape_on("play:ground", "+y", g["box"], [[float(u), float(v)] for u, v in gen_polygon(rng, Wm, Hm)])
    return SD.region(s, scene, t=("-1", "40"))


def t7_account(SD, rng):
    a = gen_scene(rng)
    g = [c for c in a["collision"] if c["id"] == "ground"][0]
    Wx, Hz = g["box"][3], g["box"][5]
    whole = SD.region(shape_on("play:ground", "+y", g["box"], [[0, 0], [Wx, 0], [Wx, Hz], [0, Hz]]), a, t=("-1", "60"))
    corner = SD.region(shape_on("play:ground", "+y", g["box"], [[0, Hz - 0.5], [0.5, Hz - 0.5], [0.5, Hz]]), a, t=("-1", "60"))
    b = copy.deepcopy(a)
    assert op_canopy_add(random.Random(5), b) or op_canopy_add(random.Random(6), b)
    b["visuals"].sort(key=lambda v: v["id"])
    b["lights"].sort(key=lambda v: v["id"])
    d = SD.diff(a, b)
    acc = SD.account(d, a, b, whole)
    added = [o for o in acc["objects"] if o.startswith("canopy:")]
    new = sorted({SD.root(v["id"], {x["id"] for x in b["visuals"]}) for v in b["visuals"]} - {SD.root(v["id"], {x["id"] for x in a["visuals"]}) for v in a["visuals"]})
    check(len(new) == 1 and added == new, "T7 an added canopy with its ribs and light is %s objects in the account, not one (%s)" % (len(added), added[:4]))
    check(acc["verdict"] == "held", "T7 an added canopy over the ground is not held by the ground's whole top (%s)" % acc["verdict"])
    acc2 = SD.account(d, a, b, corner)
    check(acc2["verdict"] != "held", "T7 a canopy away from a corner region is held by it")
    # a tower on the cell beside a one-cell region shares only a face with it: adjacent, not held
    c0 = a["grid"]["cell"]
    t = copy.deepcopy(a)
    t["visuals"] = [v for v in t["visuals"] if not v["id"].startswith("tower:1,1")]
    t2 = copy.deepcopy(t)
    t2["visuals"].append({"id": "tower:1,1", "by": "aaaaaaaaaaaa", "region": "plaza", "asset": "cube", "material": "stone",
                          "box": [c0, 4.0, c0, 2 * c0, 12.5, 2 * c0]})
    t2["visuals"].sort(key=lambda v: v["id"])
    cellreg = SD.region(shape_on("play:ground", "+y", g["box"], [[0, Hz - 2 * c0], [c0, Hz - 2 * c0], [c0, Hz - c0], [0, Hz - c0]]), t, t=("-1", "60"))
    r = SD.account(SD.diff(t, t2), t, t2, cellreg)
    check(r["verdict"] == "adjacent" and r["objects"]["tower:1,1"]["class"] == "adjacent",
          "T7 a tower beside a one-cell region is %s, not adjacent" % r["verdict"])
    c = copy.deepcopy(a)
    c["visuals"][0]["by"] = "000000000000"
    check(SD.account(SD.diff(a, c), a, c, whole)["verdict"] == "empty", "T7 a statement's hash alone touched something")
    e = copy.deepcopy(a)
    e["environment"]["fog"] = 0.5
    r = SD.account(SD.diff(a, e), a, e, whole)
    check(r["verdict"] == "outside" and r["global"] == ["environment/fog"], "T7 the air changed is not outside every region (%s)" % r["verdict"])
    m = copy.deepcopy(a)
    m["materials"]["concrete"]["roughness"] = 0.5
    r = SD.account(SD.diff(a, m), a, m, corner)
    users = {SD.root(v["id"], {x["id"] for x in a["visuals"]}) for v in a["visuals"] if v["material"] == "concrete"}
    check(users <= set(r["objects"]), "T7 a material changed did not account every object made of it")


def t8_scope_agreement(SD, rng, N):
    """The objects the account says a candidate touched are those DIRECTOR-0's scope protocol finds realized or
    affected (dressing addresses, rooted to their objects): two accounts of one change, written apart."""
    head = {"art_sha256": "0" * 64, "exporter_sha256": "0" * 64, "world_sha256": "0" * 64}
    agree = 0
    for _ in range(N):
        a, b, names = gen_pair(rng)
        it = {"scope": [], "base": head}
        v = SCOPE.check_scope(it, a, b, head, [])
        ids = {x["id"] for x in a["visuals"]} | {x["id"] for x in b["visuals"]}
        theirs = set()
        for addr in v["realized"] + v["affected"]:
            s = addr.split("/")
            if len(s) == 3 and s[0] not in SCOPE.NAMESPACES:
                theirs.add(SD.root(s[1] + ":" + s[2], ids))
        d = SD.diff(a, b)
        ours = {o for o, _w, _s, _p, _b in SD.footprint(d, a, b) if not o.startswith(("play:", "mover:", "light:"))}
        check(ours == theirs, "T8 the account touches %s, the scope protocol %s (%s)" % (sorted(ours - theirs)[:3], sorted(theirs - ours)[:3], names))
        agree += 1
    return agree


def t9_reach(SD, rng):
    """HELD-0's region: from the back of the anchor's box out to the shape's reach. On a top face the default reaches
    the sky (a tower standing on a marked floor is held); elsewhere 1 m (a sign on a marked wall is, a box 1.5 m out
    is not); a reach given is used; an opening's region runs through its anchor and on behind it."""
    a = gen_scene(rng)
    g = [c for c in a["collision"] if c["id"] == "ground"][0]
    Wx, Hz = g["box"][3], g["box"][5]
    sq = [[1, 1], [3, 1], [3, 3], [1, 3]]                      # on the top face: u east, v north (z falls as v grows)
    sky = SD.region(shape_on("play:ground", "+y", g["box"], sq), a)
    check(sky["t"][1] is None, "T9 a region on a top face does not reach the sky by default (%s)" % (sky["t"],))
    zN = Hz - 3                                                   # v from 1 to 3 is z from Hz-3 to Hz-1
    tower = [1.5, 0.0, zN + 0.5, 2.5, 300.0, zN + 1.5]
    check(SD.classify(tower, sky) == "inside", "T9 a tower 300 m tall standing on a marked floor is not held by it")
    check(SD.classify([1.5, -0.001, zN + 0.5, 2.5, 0.008, zN + 1.5], sky) == "inside", "T9 a puddle set 1 mm into the floor is not held")
    ten = SD.region(shape_on("play:ground", "+y", g["box"], sq, reach=10), a)
    check(SD.classify(tower, ten) == "crossing", "T9 a reach of 10 m holds a tower of 300 m")
    wall = {"id": "c:w", "kind": "wall", "material": "concrete", "cells": [0, 0, 0, 0], "box": [0.0, 0.0, 0.0, 4.0, 4.0, 0.5]}
    a2 = copy.deepcopy(a)
    a2["collision"].append(wall)
    front = SD.region(shape_on("play:c:w", "+z", wall["box"], [[1, 1], [3, 1], [3, 3], [1, 3]]), a2)
    check(front["t"] == (F(-1, 2), F(1)), "T9 a wall's region is not from its back to 1 m out (%s)" % (front["t"],))
    check(SD.classify([1.5, 1.5, 0.5, 2.5, 2.5, 1.0], front) == "inside", "T9 a sign 0.5 m out on a marked wall is not held")
    check(SD.classify([1.5, 1.5, 1.0, 2.5, 2.5, 2.0], front) == "crossing", "T9 a box from 0.5 m to 1.5 m out is held by a 1 m reach")
    two = SD.region(shape_on("play:c:w", "+z", wall["box"], [[1, 1], [3, 1], [3, 3], [1, 3]], reach=2), a2)
    check(SD.classify([1.5, 1.5, 1.0, 2.5, 2.5, 2.0], two) == "inside", "T9 a reach of 2 m does not hold a box 1.5 m out")
    behind = [1.5, 1.5, -0.8, 2.5, 2.5, 0.0]
    cut = SD.region(shape_on("play:c:w", "+z", wall["box"], [[1, 1], [3, 1], [3, 3], [1, 3]], op="subtract"), a2)
    check(SD.classify(behind, cut) == "inside" and SD.classify(behind, front) == "touching",
          "T9 an opening's region does not run through its wall and on behind it (%s, %s)" % (SD.classify(behind, cut), SD.classify(behind, front)))
    # what the studio keeps of a candidate: a stale shape says so; the badges are the diff's
    b = copy.deepcopy(a)
    op_canopy_add(random.Random(5), b) or op_canopy_add(random.Random(6), b)
    b["visuals"].sort(key=lambda v: v["id"])
    b["lights"].sort(key=lambda v: v["id"])
    gone = shape_on("tower:99,99", "+y", [0, 0, 0, 1, 1, 1], [[0, 0], [1, 0], [1, 1]])
    rep = SD.report(a, b, [shape_on("play:ground", "+y", g["box"], [[0, 0], [Wx, 0], [Wx, Hz], [0, Hz]]), gone])
    check(rep["badges"] == SD.badges(SD.diff(a, b)), "T9 the report's badges are not the diff's")
    check([x["verdict"] for x in rep["accounts"]] == ["held", "stale"], "T9 the report's accounts read %s" % [x["verdict"] for x in rep["accounts"]])
    check(all(x["relation"] == "inside" for x in rep["boxes"]) and rep["boxes"], "T9 the report's boxes are not related to its first region")


def workload_digest(SD):
    """A fixed seeded workload whose output must not depend on PYTHONHASHSEED."""
    rng = random.Random(4242)
    h = hashlib.sha256()
    for _ in range(25):
        a, b, _n = gen_pair(rng)
        for op in (op_vis_add, op_vis_add, op_vis_add, op_canopy_add, op_vis_material):
            op(rng, b)
        b["visuals"].sort(key=lambda v: v["id"])
        b["lights"].sort(key=lambda v: v["id"])
        d = SD.diff(a, b)
        h.update(enc(d).encode())
        reg = region_for(SD, a, rng)
        if reg is not None:
            h.update(enc(SD.account(d, a, b, reg)).encode())
    return h.hexdigest()


def t1_hashseed(mutant):
    outs = set()
    for seed in ("0", "1", "2", "3", "11"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "--child", mutant or "-"], capture_output=True, env=env, timeout=600)
        if r.returncode != 0:
            raise Fail("T1 the child run failed: %s" % r.stderr.decode()[-300:])
        outs.add(r.stdout.decode().strip())
    check(len(outs) == 1, "T1 the diff and account depend on PYTHONHASHSEED (%d different outputs over 5 seeds)" % len(outs))


def suite(SD, quick=False, mutant=None, stop=False):
    """Run every property; return (failures {property: message}, measurements)."""
    n = 40 if quick else 160
    fails, meas = {}, {}
    props = [("T1 determinism", lambda: t1_determinism(SD, random.Random(1), n // 2)),
             ("T1 hash seed", lambda: t1_hashseed(mutant)),
             ("T2 inverse", lambda: t2_inverse(SD, random.Random(2), n)),
             ("T3 completeness", lambda: t3_completeness(SD, random.Random(3), n)),
             ("T4 badges", lambda: t4_badges(SD, random.Random(4), n)),
             ("T5 2D exact", lambda: t5_containment_2d(SD, random.Random(5), 6 * n)),
             ("T5 frames", lambda: t5_frames(SD, random.Random(6), n)),
             ("T5 worked cases", lambda: t5_cases(SD)),
             ("T5 paths", lambda: t5_path_never_inside(SD, random.Random(7), n)),
             ("T6 shapes", lambda: t6_shapes(SD, random.Random(8))),
             ("T7 account", lambda: t7_account(SD, random.Random(9))),
             ("T8 scope agreement", lambda: t8_scope_agreement(SD, random.Random(10), n)),
             ("T9 reach", lambda: t9_reach(SD, random.Random(11)))]
    for name, f in props:
        try:
            meas[name] = f()
        except Fail as e:
            fails[name] = str(e)[:300]
        except Exception as e:      # a mutant that crashes is caught too, and said so
            fails[name] = "%s: %s" % (type(e).__name__, str(e)[:240])
        if stop and fails:
            break
    return fails, meas


# ------------------------------------------------------------------------------------------------ the mutants
def mutate(SD, name):
    """Plant one defect in a fresh copy of the module."""
    if name == "same-by-equality":                     # values compared by Python ==, not by their bytes
        SD.same = lambda x, y: x == y
    elif name == "account-unsorted":                   # the outside list built from a set
        orig = SD.account

        def account(d, a, b, reg, rows=None):
            r = orig(d, a, b, reg, rows)
            r["outside"] = list(set(r["outside"]))
            return r
        SD.account = account
    elif name == "boxes-in-scene-order":               # an object's boxes kept in the scene's list order
        def object_records(scene):
            O = SD.R.objects(scene)
            return {i: {"region": o["region"], "material": o["material"], "by": o["by"], "boxes": o["boxes"], "parts": o["parts"],
                        "lights": o["lights"]} for i, o in sorted(O.items())}
        SD.object_records = object_records
    elif name == "invert-keeps-changed":               # added and removed swapped, changed fields not
        SD.invert_keyed = lambda s: {"added": dict(s["removed"]), "removed": dict(s["added"]), "changed": dict(s["changed"])}
    elif name == "apply-keeps-dropped-fields":         # a field the target lacks is left in place
        orig = SD.apply_fields

        def apply_fields(fields, x):
            keep = {f: x[f] for f, e in fields.items() if "b" not in e and f in x}
            y = orig(fields, x)
            y.update(keep)
            return y
        SD.apply_fields = apply_fields
    elif name == "C-forgets-targets":
        orig = SD._badge
        SD._badge = lambda sec, f: "" if sec == "targets" else orig(sec, f)
    elif name == "M-forgets-the-air":
        orig = SD._badge
        SD._badge = lambda sec, f: "" if sec == "environment" else orig(sec, f)
    elif name == "P-not-monotone":                     # P said only when the look did not change
        orig = SD.badges

        def badges(d):
            b = orig(d)
            b["P"] = b["P"] and not b["M"]
            return b
        SD.badges = badges
    elif name == "frame-+x-u-flipped":                 # the +x face's u turned round (the table no longer right-handed)
        orig = SD.frame

        def frame(box, face):
            fr = orig(box, face)
            if face == "+x":
                fr = dict(fr, u=(0, 0, 1), origin=(fr["origin"][0], fr["origin"][1], fr["origin"][2] - fr["W"]))
                fr["n"] = SD.cross(fr["u"], fr["v"])
            return fr
        SD.frame = frame
    elif name == "convex-hull":                         # the polygon's hull in place of the polygon
        orig = SD.rel2

        def hull(P):
            pts = sorted(set(P))
            if len(pts) < 3:
                return pts

            def half(ps):
                h = []
                for p in ps:
                    while len(h) >= 2 and SD.orient(h[-2], h[-1], p) <= 0:
                        h.pop()
                    h.append(p)
                return h
            lo, up = half(pts), half(pts[::-1])
            return lo[:-1] + up[:-1]
        SD.rel2 = lambda P, closed, rect: orig(hull(P) if closed else P, closed, rect)
    elif name == "open-test-closed":                    # an edge on the rectangle's border taken for one inside it
        SD.seg_meets_open = lambda a, b, rect: SD.clip_seg(a, b, rect) is not None
    elif name == "binary-floats":                       # coordinates read as the binary float, not the decimal stated
        orig = SD.q
        SD.q = lambda x: Fraction(x) if isinstance(x, float) else orig(x)
    elif name == "status-to-the-centimetre":            # a shape's box compared to the centimetre
        def status(rec, scene):
            got = SM.box_in(scene, rec["anchor"]["piece"])
            if got is None or got == "ambiguous":
                return "gone", None
            return ("ok" if [round(float(x), 2) for x in got[0]] == [round(float(x), 2) for x in rec["anchor"]["box"]] else "changed"), got[0]
        SD.status = status
    elif name == "root-against-the-base":               # parts of an added object rooted against the base's ids alone
        orig = SD.footprint

        def footprint(d, a, b):
            ida = {v["id"] for v in a.get("visuals", [])}
            saved = SD.root
            SD.root = lambda i, ids: saved(i, ida)
            try:
                return orig(d, a, b)
            finally:
                SD.root = saved
        SD.footprint = footprint
    elif name == "path-has-volume":
        orig = SD.rel2
        SD.rel2 = lambda P, closed, rect: orig(P, True, rect) if len(P) >= 3 else orig(P, closed, rect)
    elif name == "hash-touches":                        # a statement's hash alone counted as a touch
        orig = SD.footprint

        def footprint(d, a, b):
            rows = orig(d, a, b)
            Va = {v["id"]: v for v in a.get("visuals", [])}
            ids = set(Va) | {v["id"] for v in b.get("visuals", [])}
            for i, c in d["visuals"]["changed"].items():
                if set(c.get("fields", {})) == {"by"}:
                    rows.append((SD.root(i, ids), "by", "a", i, [SD.q(x) for x in Va[i]["box"]]))
            return sorted(rows, key=lambda r: (r[0], r[1], r[3]))
        SD.footprint = footprint
    elif name == "non-adjacent-check-off":              # SPEC's simple-polygon rule dropped: a bow tie is a shape
        orig = SD.polygon_problems
        SD.polygon_problems = lambda poly, closed: [p for p in orig(poly, closed) if "meet" not in p]
    elif name == "reach-1m-everywhere":                # a top face's region ends 1 m up, as a wall's does
        SD.reach_of = lambda rec: Fraction(1)
    elif name == "opening-not-through":                # an opening's region stops at its anchor's back
        SD.BACK_MARGIN = Fraction(0)
    elif name == "touching-is-inside":                  # a box sharing a face with the region counted as held by it
        orig = SD.classify
        SD.classify = lambda box, reg: "inside" if orig(box, reg) == "touching" else orig(box, reg)
    else:
        raise KeyError(name)
    return SD


MUTANTS = ["same-by-equality", "account-unsorted", "boxes-in-scene-order", "invert-keeps-changed", "apply-keeps-dropped-fields",
           "C-forgets-targets", "M-forgets-the-air", "P-not-monotone", "frame-+x-u-flipped", "convex-hull", "open-test-closed",
           "binary-floats", "status-to-the-centimetre", "root-against-the-base", "path-has-volume", "hash-touches", "non-adjacent-check-off",
           "touching-is-inside", "reach-1m-everywhere", "opening-not-through"]


def main(argv):
    if argv[:1] == ["--child"]:
        SD = load_module()
        if argv[1] != "-":
            mutate(SD, argv[1])
        print(workload_digest(SD))
        return 0
    quick = "--quick" in argv
    SD = load_module()
    fails, meas = suite(SD, quick)
    for k, v in meas.items():
        if v is not None:
            print("MEASURED  %-20s %s" % (k, v))
    if fails:
        for k, v in fails.items():
            print("FAIL  %s: %s" % (k, v))
        print("SCENE-DIFF SELFTEST FAILED on the module as written")
        return 1
    print("the module: %d properties PASS" % 13)
    caught = 0
    for m in MUTANTS:
        f, _ = suite(mutate(load_module("mut_" + m.replace("-", "_").replace("+", "p")), m), True, mutant=m)
        if f:
            caught += 1
            k = sorted(f)[0]
            print("PLANT  %-28s CAUGHT by %s" % (m, ", ".join(sorted(f))))
            print("       %s" % f[k][:150])
        else:
            print("PLANT  %-28s NOT CAUGHT" % m)
    ok = caught == len(MUTANTS)
    print("SCENE-DIFF SELFTEST %s: %d of %d plants caught" % ("PASSED" if ok else "FAILED", caught, len(MUTANTS)))
    if "--pure" in argv:
        return 0 if ok else 1
    # HELD-0 and COMPARE-0 over HTTP, with the scripted director (art/play.py held_selftest)
    import play
    rows = []

    def row(name, good, detail):
        rows.append(bool(good))
        print("[%s] %s — %s" % ("PASS" if good else "FAIL", name, detail), flush=True)
    play.held_selftest(row)
    print("HELD SELFTEST %d/%d" % (sum(rows), len(rows)))
    return 0 if ok and rows and all(rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
