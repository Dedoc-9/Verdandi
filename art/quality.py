# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/quality.py — QUALITY-0: exact checks on a scene's bytes, frozen references, and detectors on stills.
#
#   python art/quality.py check [NAME ...]          the exact checks and the frozen reference of each brief
#   python art/quality.py freeze NAME --note TEXT   append the brief's reference at this exporter (never rewritten)
#   python art/quality.py still FILE.png ...        the detectors on stills (a detector is not a proof)
#   python art/quality.py selftest                  every check against the defect planted for it
#
# By the owner's ruling of 2026-10-13: "Cheap exact quality checks. Validate finite and bounded scene values, budgets,
# and stored reference outputs. Add renderer-independent image checks such as pure-white pixel fraction and other
# carefully chosen clipping or black-frame indicators", with its conditions: reference images are frozen evidence
# identified by digest; image thresholds are detectors, not proofs.
#
# EXACT, on the scene's bytes (art/dress.py's scene.json), each a yes or a no:
#   form      the bytes are UTF-8 JSON in the exporter's one byte form (sorted keys, indent 1, one LF at the end); no
#             NaN, no Infinity, no number that overflows to one (json.loads('1e999') gives inf without a word, and
#             parse_constant never sees it), no key twice in an object, no integer a browser cannot hold exactly (above
#             2^53 - 1)
#   bounds    every field the scene format has is known here, with its type and its range, restated here and not
#             imported from the exporter, so a change to either shows as a disagreement; a field this checker does not
#             know is refused, not passed over (a scene that grows a field needs this checker to grow it too); boxes
#             have extent on every axis and lie inside the world; every coordinate is under 1024 m, where the renderer's
#             float32 keeps the scene's 0.1 mm steps apart (above it, two of them can become one number)
#   movers    (0226) a scene with movers names the rules it is played under, 2 and no other, and carries each mover as
#             rules 2 have it: an id, its statement, a declared material, a box of whole 1/256 m (as a double holds them
#             exactly) inside the world, an axis, len and speed whole and in range, the policy stop, and its travel too
#             inside the world and under 1,024 m; a scene has both fields or neither
#   budgets   what the native renderer (art/web/scene_render.js) can draw: it draws the first 160 lights and drops the
#             rest without a word, and it keeps a light's visibility in a texture one texel to a cell, which WebGL 2
#             guarantees only up to 2048 wide (OpenGL ES 3.0's minimum MAX_TEXTURE_SIZE as recalled, INFERRED: the
#             specification was not re-read for this; web3dsurvey.com reports no device below 4096, OBSERVED, which
#             is a survey, not a guarantee); both numbers are read from the renderer's source, and a source that no
#             longer says them refuses. Two budgets are chosen, not derived: 4,096 boxes and 4 MiB of scene, ten times
#             and about twenty-eight times today's largest brief.
#   notices   drawn differently by the native renderer, said and not refused: a light above 2,000 cd keeps its full
#             light but its glare is drawn at 2,000.
# FROZEN, art/references.jsonl: one line to a (brief, art_sha256, exporter_sha256), with the scene's sha256 and the
#   sha256 of each of its top-level fields. The check compares and never writes; freeze appends and refuses to write a
#   second line for the same inputs, and refuses outright if the same inputs now give other bytes (that would be the
#   exporter not being deterministic, not a new reference). When the exporter changes (a rebase in every world's
#   ledger), the check fails until the new references are frozen by a person, and it says which fields the new
#   exporter moved, against the newest reference of the same art: the golden regression a change to the exporter owes.
# DETECTORS, on stills (PNG, 8-bit RGB or RGBA, not interlaced; anything else is not checked, and says so): the
#   fraction of white pixels (every channel at 250 or above; at 255 is said beside it), of pure black ones, of pixels
#   with any channel at 255, the number of distinct colours, and the mean luma. A detector flags; it does not refuse, and it proves nothing: a snowfield may be white
#   and a still may be wrong at every threshold. The thresholds were chosen with 16 stills of the two briefs in view
#   (docs/ROADMAP.md), which is calibration on a handful, not a measured rate of misses or false alarms.
#
# Standard library only.

import hashlib
import json
import math
import os
import re
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RENDERER = os.path.join(HERE, "web", "scene_render.js")
REFERENCES = os.path.join(HERE, "references.jsonl")

SCENE_FORMAT = "VERDANDI-ART-SCENE 0"
REFERENCE_FORMAT = "VERDANDI-ART-REFERENCE 0"
JS_SAFE = 2 ** 53 - 1
F32_LIMIT = 1024.0                 # every coordinate's magnitude below this: float32's step there is 2^-14 m < 0.1 mm
WEBGL2_MIN_TEXTURE = 2048          # OpenGL ES 3.0's minimum MAX_TEXTURE_SIZE, which WebGL 2 inherits (as recalled; INFERRED)
BUDGET_BOXES = 4096                # chosen, not derived
BUDGET_BYTES = 4 * 1024 * 1024     # chosen, not derived
TIMES = ("night", "dusk", "day")
LIGHT_KINDS = ("moon", "sun")
SCENE_LIGHT_TYPES = ("point", "rect")
PIECE_KINDS = ("ground", "floor", "stair", "raised", "cover", "wall")
SCENE_RULES = (2,)                 # the rules a scene with movers may name (graybox/RULES-2.md)
AXES = ([1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1])

# the detectors' thresholds (a flag, not a refusal; chosen with 16 stills in view)
DETECT = {"near": 250, "white": 0.05, "black": 0.95, "clipped": 0.25, "flat": 4}


class QualityError(Exception):
    def __init__(self, code, msg):
        Exception.__init__(self, "%s: %s" % (code, msg))
        self.code = code


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------------------------------------ form
def _const(name):
    raise QualityError("QUALITY-NONFINITE", "the constant %s is not a number JSON has" % name)


def _float(s):
    v = float(s)
    if not math.isfinite(v):
        raise QualityError("QUALITY-NONFINITE", "%s overflows to %r" % (s[:40], v))
    return v


def _int(s):
    v = int(s)
    if abs(v) > JS_SAFE:
        raise QualityError("QUALITY-INTEGER", "%s is beyond 2^53 - 1: a browser reads another number" % s[:40])
    return v


def _pairs(pairs):
    seen = set()
    for k, _v in pairs:
        if k in seen:
            raise QualityError("QUALITY-DUPLICATE-KEY", "the key %r twice in one object (readers disagree on which wins)" % k)
        seen.add(k)
    return dict(pairs)


def scene_form(b: bytes):
    """The scene from its bytes, which must be the exporter's one byte form of finite JSON."""
    try:
        text = b.decode("utf-8")
    except UnicodeDecodeError as e:
        raise QualityError("QUALITY-FORM", "not UTF-8 (%s)" % e)
    try:
        S = json.loads(text, parse_constant=_const, parse_float=_float, parse_int=_int, object_pairs_hook=_pairs)
    except ValueError as e:
        if isinstance(e, QualityError):
            raise
        raise QualityError("QUALITY-FORM", "not JSON (%s)" % e)
    again = (json.dumps(S, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    if again != b:
        i = next((k for k in range(min(len(again), len(b))) if again[k] != b[k]), min(len(again), len(b)))
        raise QualityError("QUALITY-FORM", "not the one byte form (sorted keys, indent 1, one LF): it differs from byte %d" % i)
    return S


# ------------------------------------------------------------------------------------------------ bounds
def _isnum(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _isint(v):
    return isinstance(v, int) and not isinstance(v, bool)


class Bounds:
    """One walk over the scene, every problem kept (where, what)."""

    def __init__(self, S):
        self.S, self.bad = S, []
        g = S.get("grid") if isinstance(S, dict) else None
        ok = isinstance(g, dict) and _isint(g.get("w")) and _isint(g.get("h")) and _isnum(g.get("cell")) and g.get("w", 0) > 0 and g.get("h", 0) > 0 and g.get("cell", 0) > 0
        self.X = g["w"] * g["cell"] if ok else None
        self.Z = g["h"] * g["cell"] if ok else None

    def no(self, where, what):
        self.bad.append((where, what))
        return False

    def keys(self, where, d, required, optional=()):
        if not isinstance(d, dict):
            return self.no(where, "is not an object")
        miss = [k for k in required if k not in d]
        extra = [k for k in d if k not in required and k not in optional]
        if miss:
            self.no(where, "has no " + ", ".join(miss))
        if extra:
            self.no(where, "has a field this checker does not know: " + ", ".join(sorted(extra)) + " (not checked is not passed)")
        return not miss and not extra

    def num(self, where, v, lo, hi, lo_open=False):
        if not _isnum(v):
            return self.no(where, "%r is not a number" % (v,))
        if not math.isfinite(v):
            return self.no(where, "%r is not finite" % (v,))
        if (v <= lo if lo_open else v < lo) or v > hi:
            return self.no(where, "%r is outside %s%s..%s]" % (v, "(" if lo_open else "[", lo, hi))
        return True

    def integer(self, where, v, lo, hi):
        if not _isint(v):
            return self.no(where, "%r is not an integer" % (v,))
        return self.num(where, v, lo, hi)

    def text(self, where, v):
        return True if isinstance(v, str) else self.no(where, "%r is not text" % (v,))

    def colour(self, where, v):
        if not (isinstance(v, list) and len(v) == 3):
            return self.no(where, "%r is not a colour of three channels" % (v,))
        return all([self.integer(where + "[%d]" % i, c, 0, 255) for i, c in enumerate(v)])

    def coord(self, where, v, axis):
        if not self.num(where, v, -F32_LIMIT, F32_LIMIT):
            return False
        if abs(v) >= F32_LIMIT:
            return self.no(where, "%r is at or above %s m, where float32 merges the scene's 0.1 mm steps" % (v, F32_LIMIT))
        if axis == "x" and self.X is not None and not (0 <= v <= self.X):
            return self.no(where, "%r is outside the world, x 0..%s" % (v, self.X))
        if axis == "z" and self.Z is not None and not (0 <= v <= self.Z):
            return self.no(where, "%r is outside the world, z 0..%s" % (v, self.Z))
        return True

    def point(self, where, p):
        if not (isinstance(p, list) and len(p) == 3):
            return self.no(where, "%r is not a point x, y, z" % (p,))
        return all([self.coord(where + ".x", p[0], "x"), self.coord(where + ".y", p[1], "y"), self.coord(where + ".z", p[2], "z")])

    def box(self, where, b):
        if not (isinstance(b, list) and len(b) == 6):
            return self.no(where, "%r is not a box x0, y0, z0, x1, y1, z1" % (b,))
        ok = all([self.coord(where + "[%d]" % i, b[i], "xyz"[i % 3]) for i in range(6)])
        if ok and not (b[0] < b[3] and b[1] < b[4] and b[2] < b[5]):
            return self.no(where, "%r has no extent on some axis" % (b,))
        return ok

    def walk(self):
        S = self.S
        top = ("assets", "collision", "environment", "format", "grid", "lights", "map", "materials", "name", "player", "reach",
               "regions", "spawns", "title", "tops", "units", "views", "visuals")
        if not self.keys("scene", S, top, ("movers", "rules")):
            if not isinstance(S, dict):
                return self.bad
        if S.get("format") != SCENE_FORMAT:
            self.no("format", "%r is not %s" % (S.get("format"), SCENE_FORMAT))
        for k in ("map", "name", "title", "units"):
            self.text(k, S.get(k))
        g = S.get("grid")
        if self.keys("grid", g, ("w", "h", "cell", "wall")):
            self.integer("grid.w", g["w"], 1, 4096)
            self.integer("grid.h", g["h"], 1, 4096)
            self.num("grid.cell", g["cell"], 0, 64, lo_open=True)
            self.num("grid.wall", g["wall"], 0, 64, lo_open=True)
        n = (g["w"] * g["h"]) if self.X is not None else None
        for k, nullable in (("tops", False), ("reach", True)):
            arr = S.get(k)
            if not isinstance(arr, list) or (n is not None and len(arr) != n):
                self.no(k, "is not a list of one value to each of the grid's %s cells" % n)
            else:
                for i, v in enumerate(arr):
                    if v is None and nullable:
                        continue
                    self.coord("%s[%d]" % (k, i), v, "y")
        p = S.get("player")
        if self.keys("player", p, ("radius", "eye", "step", "speed", "gravity", "jump", "jump_apex", "body", "margin", "flat", "flush")):
            for k in sorted(p):
                self.num("player." + k, p[k], 0, 1000, lo_open=True)
        sp = S.get("spawns")
        if isinstance(sp, dict):
            for k in sorted(sp):
                w = "spawns." + k
                if self.keys(w, sp[k], ("x", "y", "z", "yaw")):
                    self.coord(w + ".x", sp[k]["x"], "x"); self.coord(w + ".y", sp[k]["y"], "y"); self.coord(w + ".z", sp[k]["z"], "z")
                    self.num(w + ".yaw", sp[k]["yaw"], 0, 360)
        else:
            self.no("spawns", "is not an object")
        vw = S.get("views")
        if isinstance(vw, dict):
            for k in sorted(vw):
                w = "views." + k
                if self.keys(w, vw[k], ("x", "y", "z", "yaw", "pitch")):
                    self.coord(w + ".x", vw[k]["x"], "x"); self.coord(w + ".y", vw[k]["y"], "y"); self.coord(w + ".z", vw[k]["z"], "z")
                    self.num(w + ".yaw", vw[k]["yaw"], 0, 360)
                    self.num(w + ".pitch", vw[k]["pitch"], -89, 89)
        else:
            self.no("views", "is not an object")
        rg = S.get("regions")
        if isinstance(rg, dict):
            for k in sorted(rg):
                r = rg[k]
                if not (isinstance(r, list) and len(r) == 4):
                    self.no("regions." + k, "%r is not x0, z0, x1, z1" % (r,))
                    continue
                gw = g["w"] if self.X is not None else 4096
                gh = g["h"] if self.X is not None else 4096
                ok = all([self.integer("regions.%s[%d]" % (k, i), r[i], 0, (gw if i % 2 == 0 else gh) - 1) for i in range(4)])
                if ok and not (r[0] <= r[2] and r[1] <= r[3]):
                    self.no("regions." + k, "%r has its corners crossed" % (r,))
        else:
            self.no("regions", "is not an object")
        e = S.get("environment")
        if self.keys("environment", e, ("time", "light", "fog", "exposure", "bloom", "rain")):
            if e["time"] not in TIMES:
                self.no("environment.time", "%r is not one of %s" % (e["time"], ", ".join(TIMES)))
            L = e["light"]
            if L is not None and self.keys("environment.light", L, ("kind", "azimuth", "elevation", "lux", "color")):
                if L["kind"] not in LIGHT_KINDS:
                    self.no("environment.light.kind", "%r is not moon or sun" % (L["kind"],))
                self.num("environment.light.azimuth", L["azimuth"], 0, 360)
                self.num("environment.light.elevation", L["elevation"], -10, 90)
                self.num("environment.light.lux", L["lux"], 0, 150000)
                self.colour("environment.light.color", L["color"])
            F = e["fog"]
            if F is not None and self.keys("environment.fog", F, ("density", "color", "volumetric")):
                self.num("environment.fog.density", F["density"], 0, 1)
                self.colour("environment.fog.color", F["color"])
                if not isinstance(F["volumetric"], bool):
                    self.no("environment.fog.volumetric", "is not true or false")
            self.num("environment.exposure", e["exposure"], -8, 8)
            self.num("environment.bloom", e["bloom"], 0, 8)
            self.num("environment.rain", e["rain"], 0, 1)
        M = S.get("materials")
        if isinstance(M, dict):
            for k in sorted(M):
                w = "materials." + k
                if self.keys(w, M[k], ("base", "roughness", "metallic", "emissive", "emissive_strength")):
                    self.colour(w + ".base", M[k]["base"]); self.colour(w + ".emissive", M[k]["emissive"])
                    self.num(w + ".roughness", M[k]["roughness"], 0, 1); self.num(w + ".metallic", M[k]["metallic"], 0, 1)
                    self.num(w + ".emissive_strength", M[k]["emissive_strength"], 0, 1000)
        else:
            self.no("materials", "is not an object")
            M = {}
        A = S.get("assets")
        if isinstance(A, dict):
            for k in sorted(A):
                if self.keys("assets." + k, A[k], ("path", "source", "licence")):
                    for f in ("path", "source", "licence"):
                        self.text("assets.%s.%s" % (k, f), A[k][f])
        else:
            self.no("assets", "is not an object")
            A = {}
        for fam, req, opt in (("collision", ("id", "kind", "material", "cells", "box"), ()),
                              ("visuals", ("id", "by", "region", "asset", "material", "box"), ())):
            arr = S.get(fam)
            if not isinstance(arr, list):
                self.no(fam, "is not a list")
                continue
            seen = set()
            for i, v in enumerate(arr):
                w = "%s[%d]" % (fam, i)
                if not self.keys(w, v, req, opt):
                    continue
                if v["id"] in seen:
                    self.no(w, "the id %r twice" % (v["id"],))
                seen.add(v["id"])
                self.box(w + ".box", v["box"])
                if v["material"] not in M:
                    self.no(w + ".material", "%r is not a declared material" % (v["material"],))
                if fam == "visuals" and v["asset"] not in A:
                    self.no(w + ".asset", "%r is not a declared asset" % (v["asset"],))
                if fam == "collision" and v["kind"] not in PIECE_KINDS:
                    self.no(w + ".kind", "%r is not a kind of play geometry" % (v["kind"],))
        if ("movers" in S) != ("rules" in S):
            self.no("movers" if "movers" in S else "rules", "a scene has movers and the rules they are played under together, or neither")
        if "rules" in S and (not _isint(S["rules"]) or S["rules"] not in SCENE_RULES):
            self.no("rules", "%r is not rules %s" % (S["rules"], " or ".join(str(r) for r in SCENE_RULES)))
        if "movers" in S:
            arr = S["movers"]
            if not isinstance(arr, list) or not arr:
                self.no("movers", "is not a list of at least one mover")
                arr = []
            seen = set()
            for i, m in enumerate(arr):
                w = "movers[%d]" % i
                if not self.keys(w, m, ("id", "by", "material", "box", "axis", "len", "speed", "policy")):
                    continue
                if self.text(w + ".id", m["id"]) and m["id"] in seen:
                    self.no(w, "the id %r twice" % (m["id"],))
                seen.add(m["id"])
                self.text(w + ".by", m["by"])
                if m["material"] not in M:
                    self.no(w + ".material", "%r is not a declared material" % (m["material"],))
                if self.box(w + ".box", m["box"]):
                    for k, v in enumerate(m["box"]):
                        if float(v) * 256.0 != math.floor(float(v) * 256.0):
                            self.no(w + ".box[%d]" % k, "%r is not a whole number of 1/256 m" % (v,))
                if not (isinstance(m["axis"], list) and m["axis"] in AXES and all(_isint(a) for a in m["axis"])):
                    self.no(w + ".axis", "%r is not one of x, y, z, either way" % (m["axis"],))
                ok_len = self.integer(w + ".len", m["len"], 1, 2 ** 18)
                if ok_len:
                    self.integer(w + ".speed", m["speed"], 0, m["len"])
                if m["policy"] != "stop":
                    self.no(w + ".policy", "%r is not stop" % (m["policy"],))
                if ok_len and isinstance(m["box"], list) and len(m["box"]) == 6 and m["axis"] in AXES and all(_isnum(v) for v in m["box"]):
                    d = m["len"] / 256.0
                    tb = [m["box"][k] + m["axis"][k % 3] * d for k in range(6)]
                    for k in range(6):
                        self.coord(w + ".travel[%d]" % k, tb[k], "xyz"[k % 3])
        arr = S.get("lights")
        if not isinstance(arr, list):
            self.no("lights", "is not a list")
        else:
            seen = set()
            for i, L in enumerate(arr):
                w = "lights[%d]" % i
                t = L.get("type") if isinstance(L, dict) else None
                req = ("id", "by", "region", "type", "pos", "dir", "color", "candela", "radius") + (("width", "height") if t == "rect" else ())
                if not self.keys(w, L, req):
                    continue
                if t not in SCENE_LIGHT_TYPES:
                    self.no(w + ".type", "%r is not point or rect" % (t,))
                if L["id"] in seen:
                    self.no(w, "the id %r twice" % (L["id"],))
                seen.add(L["id"])
                self.point(w + ".pos", L["pos"])
                d = L["dir"]
                if not (isinstance(d, list) and len(d) == 3 and all(_isnum(c) and math.isfinite(c) for c in d) and any(c != 0 for c in d)):
                    self.no(w + ".dir", "%r is not a direction" % (d,))
                self.colour(w + ".color", L["color"])
                self.num(w + ".candela", L["candela"], 0, 100000)
                self.num(w + ".radius", L["radius"], 0, F32_LIMIT, lo_open=True)
                if t == "rect":
                    self.num(w + ".width", L["width"], 0, F32_LIMIT, lo_open=True)
                    self.num(w + ".height", L["height"], 0, F32_LIMIT, lo_open=True)
        return self.bad


def scene_bounds(S):
    return Bounds(S).walk()


# ------------------------------------------------------------------------------------------------ budgets
def renderer_limits(js_text=None):
    """The native renderer's own numbers, read from its source: the lights it draws, and the candela its glare stops at.
    A source that does not say each exactly once refuses (QUALITY-RENDERER): the budget would be a guess."""
    if js_text is None:
        js_text = open(RENDERER, "rb").read().decode("utf-8")
    cap = re.findall(r"S\.lights\.slice\(0,\s*([0-9]+)\)", js_text)
    glare = re.findall(r"Math\.min\(L\.candela,\s*([0-9]+)\)", js_text)
    vis = re.findall(r"this\.tex2D\(gl\.R8,\s*wh,\s*NL,", js_text)
    movers = re.findall(r"const MAX_MOVERS = ([0-9]+);", js_text)
    if len(cap) != 1 or len(glare) != 1 or len(vis) != 1 or len(movers) != 1:
        raise QualityError("QUALITY-RENDERER", "the renderer's source no longer says its light cap, its glare cap, its "
                           "visibility texture and its mover cap once each (%d, %d, %d, %d found): the budgets need restating" % (len(cap), len(glare), len(vis), len(movers)))
    return {"lights": int(cap[0]), "glare_candela": int(glare[0]), "cells": WEBGL2_MIN_TEXTURE, "movers": int(movers[0])}


def scene_budgets(S, nbytes, limits=None):
    """(refusals, notices): what the renderer cannot draw as the scene says it, and what it draws differently."""
    lim = limits or renderer_limits()
    bad, note = [], []
    lights = S.get("lights", [])
    if len(lights) > lim["lights"]:
        bad.append(("lights", "%d lights: the native renderer draws the first %d and drops the rest" % (len(lights), lim["lights"])))
    g = S.get("grid", {})
    cells = g.get("w", 0) * g.get("h", 0)
    if cells > lim["cells"]:
        bad.append(("grid", "%d cells: the visibility texture is one texel to a cell, and WebGL 2 guarantees %d" % (cells, lim["cells"])))
    movers = S.get("movers", []) if isinstance(S.get("movers"), list) else []
    if len(movers) > lim["movers"]:
        bad.append(("movers", "%d movers: the native renderer draws the first %d and drops the rest" % (len(movers), lim["movers"])))
    boxes = len(S.get("collision", [])) + len(S.get("visuals", [])) + len(movers)
    if boxes > BUDGET_BOXES:
        bad.append(("boxes", "%d boxes, above the budget of %d (a budget chosen, not a limit of the renderer)" % (boxes, BUDGET_BOXES)))
    if nbytes > BUDGET_BYTES:
        bad.append(("bytes", "%d bytes, above the budget of %d (chosen)" % (nbytes, BUDGET_BYTES)))
    hot = [L["id"] for L in lights if isinstance(L, dict) and _isnum(L.get("candela")) and L["candela"] > lim["glare_candela"]]
    if hot:
        note.append(("lights", "%d light(s) above %d cd: their glare is drawn at %d cd (%s)" % (len(hot), lim["glare_candela"], lim["glare_candela"], ", ".join(hot[:3]))))
    return bad, note


def check_scene(scene_bytes, limits=None):
    """The exact checks of one scene: [(name, ok, detail)] and the notices. Each check is a yes or a no."""
    res = []
    try:
        S = scene_form(scene_bytes)
        res.append(("quality: the scene's bytes are finite JSON in its one byte form", True, "%d bytes" % len(scene_bytes)))
    except QualityError as e:
        res.append(("quality: the scene's bytes are finite JSON in its one byte form", False, str(e)))
        res.append(("quality: every field is known and inside its bounds", False, "not checked: the bytes did not read"))
        res.append(("quality: the scene is inside the native renderer's budgets", False, "not checked: the bytes did not read"))
        return res, []
    bad = scene_bounds(S)
    res.append(("quality: every field is known and inside its bounds", not bad,
                "%d problem(s), the first: %s %s" % (len(bad), bad[0][0], bad[0][1]) if bad else "every field"))
    try:
        over, notes = scene_budgets(S, len(scene_bytes), limits)
    except QualityError as e:
        res.append(("quality: the scene is inside the native renderer's budgets", False, str(e)))
        return res, []
    res.append(("quality: the scene is inside the native renderer's budgets", not over,
                "; ".join("%s: %s" % o for o in over) if over else "%d lights, %d boxes, %d bytes" % (
                    len(S["lights"]), len(S["collision"]) + len(S["visuals"]) + len(S.get("movers", [])), len(scene_bytes))))
    return res, notes


# ------------------------------------------------------------------------------------------------ references
def field_digests(scene_bytes):
    S = json.loads(scene_bytes.decode("utf-8"))
    return {k: sha256(json.dumps(S[k], sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")) for k in sorted(S)}


def reference_line(entry) -> bytes:
    return json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def read_references(path=REFERENCES):
    """Every frozen reference, each line its own one byte form; a line that is not refuses the whole file."""
    if not os.path.exists(path):
        return []
    raw = open(path, "rb").read()
    if raw and not raw.endswith(b"\n"):
        raise QualityError("QUALITY-REFERENCES", "%s: the last line has no LF" % os.path.basename(path))
    out, keys = [], set()
    for i, ln in enumerate(raw.split(b"\n")[:-1] if raw else []):
        try:
            e = json.loads(ln.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_const, parse_float=_float)
        except (ValueError, UnicodeDecodeError) as x:
            raise QualityError("QUALITY-REFERENCES", "line %d does not read (%s)" % (i + 1, x))
        if reference_line(e) != ln or e.get("format") != REFERENCE_FORMAT:
            raise QualityError("QUALITY-REFERENCES", "line %d is not a reference in its one byte form" % (i + 1))
        k = (e["brief"], e["art_sha256"], e["exporter_sha256"])
        if k in keys:
            raise QualityError("QUALITY-REFERENCES", "line %d freezes the same inputs twice" % (i + 1))
        keys.add(k)
        out.append(e)
    return out


def compare_reference(name, lineage, scene_bytes, refs):
    """(ok, detail): this scene against its frozen reference. Read-only."""
    art, exp, got = lineage["art_sha256"], lineage["exporter_sha256"], sha256(scene_bytes)
    same = [e for e in refs if e["brief"] == name and e["art_sha256"] == art and e["exporter_sha256"] == exp]
    if same:
        e = same[0]
        if e["scene_sha256"] == got:
            return True, "scene %s, as frozen on %s" % (got[:12], e["frozen_at"])
        fd = field_digests(scene_bytes)
        moved = sorted(k for k in set(fd) | set(e["fields"]) if fd.get(k) != e["fields"].get(k))
        return False, "the same inputs now give scene %s, frozen as %s: fields %s differ (the exporter is not deterministic here, or the platform differs)" % (
            got[:12], e["scene_sha256"][:12], ", ".join(moved))
    older = [e for e in refs if e["brief"] == name and e["art_sha256"] == art]
    hint = "freeze it, a person's act: python art/quality.py freeze %s --note TEXT" % name
    if older:
        e = older[-1]
        fd = field_digests(scene_bytes)
        moved = sorted(k for k in set(fd) | set(e["fields"]) if fd.get(k) != e["fields"].get(k))
        return False, "no reference at exporter %s; against the newest of the same art (exporter %s) the fields that moved: %s; %s" % (
            exp[:12], e["exporter_sha256"][:12], ", ".join(moved) or "none (the bytes are the same)", hint)
    return False, "no reference for this art (%s) at this exporter (%s); %s" % (art[:12], exp[:12], hint)


def freeze(name, note, path=REFERENCES, at=None):
    """Append the brief's reference. Refuses a scene that fails an exact check, and refuses to write the same inputs twice."""
    import datetime
    sys.path.insert(0, HERE)
    import dress
    out = dress.export(dress.load(name))
    res, _n = check_scene(out["scene_bytes"])
    bad = [c for c, ok, _d in res if not ok]
    if bad:
        raise QualityError("QUALITY-FREEZE", "%s fails %s: a failing scene is not a reference" % (name, bad[0]))
    L = out["lineage"]
    refs = read_references(path)
    for e in refs:
        if (e["brief"], e["art_sha256"], e["exporter_sha256"]) == (name, L["art_sha256"], L["exporter_sha256"]):
            if e["scene_sha256"] == L["scene_sha256"]:
                return e, False
            raise QualityError("QUALITY-REFERENCE-MOVED", "%s: the same inputs give scene %s, frozen as %s; that is not a new reference" % (
                name, L["scene_sha256"][:12], e["scene_sha256"][:12]))
    e = {"format": REFERENCE_FORMAT, "brief": name, "art_sha256": L["art_sha256"], "exporter_sha256": L["exporter_sha256"],
         "world_sha256": L["canonical_sha256"], "scene_sha256": L["scene_sha256"], "scene_bytes": len(out["scene_bytes"]),
         "fields": field_digests(out["scene_bytes"]), "note": note,
         "frozen_at": at or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    with open(path, "ab") as fh:
        fh.write(reference_line(e) + b"\n")
        fh.flush()
        os.fsync(fh.fileno())
    return e, True


# ------------------------------------------------------------------------------------------------ stills
def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def decode_png(b: bytes):
    """(width, height, rgb bytes) of an 8-bit RGB or RGBA PNG, not interlaced. Anything else refuses with
    QUALITY-STILL-UNREAD: the detectors did not run on it, which is not a pass."""
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        raise QualityError("QUALITY-STILL-UNREAD", "not a PNG")
    i, ihdr, idat, end = 8, None, [], False
    while i + 8 <= len(b):
        n, typ = struct.unpack(">I4s", b[i:i + 8])
        data = b[i + 8:i + 8 + n]
        crc = b[i + 8 + n:i + 12 + n]
        if len(data) != n or len(crc) != 4 or struct.unpack(">I", crc)[0] != zlib.crc32(typ + data) & 0xffffffff:
            raise QualityError("QUALITY-STILL-UNREAD", "a %s chunk is cut or its CRC is wrong" % typ.decode("latin-1"))
        if typ == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", data)
        elif typ == b"IDAT":
            idat.append(data)
        elif typ == b"IEND":
            end = True
            break
        i += 12 + n
    if ihdr is None or not end:
        raise QualityError("QUALITY-STILL-UNREAD", "no IHDR or no IEND")
    w, h, depth, ctype, _comp, _filt, inter = ihdr
    if depth != 8 or ctype not in (2, 6) or inter != 0:
        raise QualityError("QUALITY-STILL-UNREAD", "bit depth %d, colour type %d, interlace %d: only 8-bit RGB or RGBA, not interlaced, is read" % (depth, ctype, inter))
    if not (0 < w <= 16384 and 0 < h <= 16384):
        raise QualityError("QUALITY-STILL-UNREAD", "%d x %d is not a still this reads" % (w, h))
    bpp = 3 if ctype == 2 else 4
    stride = w * bpp
    try:
        raw = zlib.decompress(b"".join(idat))
    except zlib.error as e:
        raise QualityError("QUALITY-STILL-UNREAD", "the image data does not inflate (%s)" % e)
    if len(raw) != h * (stride + 1):
        raise QualityError("QUALITY-STILL-UNREAD", "%d bytes of image data, not %d" % (len(raw), h * (stride + 1)))
    out = bytearray(w * h * 3)
    prev = bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        if f == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                line[x] = (line[x] + ((line[x - bpp] if x >= bpp else 0) + prev[x]) // 2) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                c = prev[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + _paeth(a, prev[x], c)) & 255
        elif f != 0:
            raise QualityError("QUALITY-STILL-UNREAD", "row %d has filter %d, which PNG does not have" % (y, f))
        if bpp == 3:
            out[y * w * 3:(y + 1) * w * 3] = line
        else:
            out[y * w * 3:(y + 1) * w * 3] = bytes(v for k, v in enumerate(line) if k % 4 != 3)
        prev = line
    return w, h, bytes(out)


def detect(w, h, rgb):
    """The detectors' measures and flags on one still. Alpha is not read (a canvas still is opaque)."""
    n = w * h
    white = near = black = clipped = 0
    lo = DETECT["near"]
    luma = 0.0
    colours = set()
    for k in range(0, n * 3, 3):
        r, g, b = rgb[k], rgb[k + 1], rgb[k + 2]
        if r >= lo and g >= lo and b >= lo:
            near += 1
            if r == 255 and g == 255 and b == 255:
                white += 1
        elif r == 0 and g == 0 and b == 0:
            black += 1
        if r == 255 or g == 255 or b == 255:
            clipped += 1
        luma += 0.2126 * r + 0.7152 * g + 0.0722 * b
        if len(colours) <= DETECT["flat"]:
            colours.add((r, g, b))
    m = {"pixels": n, "white": white / n, "near_white": near / n, "black": black / n, "clipped": clipped / n,
         "colours": len(colours), "mean_luma": luma / n / 255.0}
    flags = []
    if m["near_white"] > DETECT["white"]:
        flags.append("BLOWN: %.1f%% of the pixels white, every channel at %d or above (%.1f%% at 255; flagged above %.0f%%)" % (
            100 * m["near_white"], lo, 100 * m["white"], 100 * DETECT["white"]))
    if m["black"] > DETECT["black"]:
        flags.append("BLACK: %.1f%% of the pixels pure black (flagged above %.0f%%)" % (100 * m["black"], 100 * DETECT["black"]))
    if m["clipped"] > DETECT["clipped"]:
        flags.append("CLIPPED: %.1f%% of the pixels with a channel at 255 (flagged above %.0f%%)" % (100 * m["clipped"], 100 * DETECT["clipped"]))
    if m["colours"] <= DETECT["flat"]:
        flags.append("FLAT: %d colour(s) in the whole still (flagged at %d or fewer): nothing may have been drawn" % (m["colours"], DETECT["flat"]))
    return m, flags


def detect_png(b: bytes):
    w, h, rgb = decode_png(b)
    return detect(w, h, rgb)


def detector_fields(m, flags):
    """The detectors as the ledger's restricted form holds them: text, no numbers."""
    return {"pixels": str(m["pixels"]), "white": "%.4f" % m["white"], "near_white": "%.4f" % m["near_white"], "black": "%.4f" % m["black"], "clipped": "%.4f" % m["clipped"],
            "colours": str(m["colours"]) + ("+" if m["colours"] > DETECT["flat"] else ""), "mean_luma": "%.4f" % m["mean_luma"],
            "flags": [f.split(":", 1)[0] for f in flags], "thresholds": "white (every channel %s or above) %s, black %s, clipped %s, flat %s" % (
                DETECT["near"], DETECT["white"], DETECT["black"], DETECT["clipped"], DETECT["flat"])}


# ------------------------------------------------------------------------------------------------ commands
def cmd_check(names):
    sys.path.insert(0, HERE)
    import dress
    names = names or sorted(f[:-4] for f in os.listdir(dress.BRIEFS) if f.endswith(".art"))
    failed = 0
    refs = read_references()
    for name in names:
        out = dress.export(dress.load(name))
        res, notes = check_scene(out["scene_bytes"])
        res.append(("quality: the scene is its frozen reference",) + compare_reference(name, out["lineage"], out["scene_bytes"], refs))
        print("== %s   scene %s" % (name, out["lineage"]["scene_sha256"][:12]))
        for c, ok, d in res:
            print("%s %s — %s" % ("PASS" if ok else "FAIL", c, d))
            failed += 0 if ok else 1
        for w, d in notes:
            print("NOTE %s: %s" % (w, d))
    print("QUALITY CHECKS %s" % ("PASSED" if not failed else "FAILED (%d)" % failed))
    return 0 if not failed else 1


def cmd_still(files):
    flagged = 0
    for f in files:
        try:
            m, flags = detect_png(open(f, "rb").read())
        except QualityError as e:
            print("NOT CHECKED %s — %s" % (f, e))
            flagged += 1
            continue
        print("%s %s — white %.2f%% (%.2f%% at 255), black %.2f%%, a channel at 255 %.2f%%, %s colours, mean luma %.3f" % (
            "FLAGGED" if flags else "no flag", f, 100 * m["near_white"], 100 * m["white"], 100 * m["black"], 100 * m["clipped"],
            ("%d" % m["colours"]) if m["colours"] <= DETECT["flat"] else "more than %d" % DETECT["flat"], m["mean_luma"]))
        for fl in flags:
            print("        " + fl)
        flagged += 1 if flags else 0
    print("A detector flags; it does not prove a still right or wrong.")
    return 0 if not flagged else 1


# ------------------------------------------------------------------------------------------------ self-test
def png_bytes(w, h, rgb, filters=(0,), alpha=False, interlace=0, depth=8, ctype=None):
    """A PNG of the given pixels, each row with the next of `filters` (the self-test's encoder, every filter type)."""
    bpp = 4 if alpha else 3
    rows = []
    prev = bytes(w * bpp)
    for y in range(h):
        px = bytearray()
        for x in range(w):
            k = (y * w + x) * 3
            px += rgb[k:k + 3] + (b"\xff" if alpha else b"")
        f = filters[y % len(filters)]
        enc = bytearray(len(px))
        for x in range(len(px)):
            a = px[x - bpp] if x >= bpp else 0
            c = prev[x - bpp] if x >= bpp else 0
            pred = (0, a, prev[x], (a + prev[x]) // 2, _paeth(a, prev[x], c))[f]
            enc[x] = (px[x] - pred) & 255
        rows.append(bytes([f]) + bytes(enc))
        prev = bytes(px)

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    ct = ctype if ctype is not None else (6 if alpha else 2)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, depth, ct, 0, 0, interlace)) + \
        chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b"")


def f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


def cmd_selftest():
    import copy
    import tempfile
    sys.path.insert(0, HERE)
    import dress
    rows = []

    def row(name, ok, detail=""):
        rows.append(ok)
        print("%s %s%s" % ("PASS" if ok else "FAIL", name, (" — " + detail) if detail else ""))

    def scene_of(S):
        return (json.dumps(S, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")

    out = dress.export(dress.load("plaza-night"))
    S0, B0 = out["scene"], out["scene_bytes"]
    res, notes = check_scene(B0)
    row("the plaza's scene passes every exact check", all(ok for _c, ok, _d in res), "; ".join(d for _c, _ok, d in res))

    def refused_by(label, b, want):
        r, _n = check_scene(b)
        bad = [(c, d) for c, ok, d in r if not ok]
        ok = bool(bad) and want in bad[0][1] if want else bool(bad)
        row("plant: %s — refused" % label, ok, bad[0][1][:150] if bad else "NOT refused")

    # form
    refused_by("NaN in the bytes", B0.replace(b'"exposure": 1.5', b'"exposure": NaN', 1), "QUALITY-NONFINITE")
    refused_by("Infinity in the bytes", B0.replace(b'"exposure": 1.5', b'"exposure": Infinity', 1), "QUALITY-NONFINITE")
    refused_by("1e999, which json.loads reads as inf without a word", B0.replace(b'"exposure": 1.5', b'"exposure": 1e999', 1), "QUALITY-NONFINITE")
    row("  (json.loads('1e999') is inf here, and parse_constant is never called for it)", json.loads("1e999") == float("inf"))
    refused_by("-1e999", B0.replace(b'"rain": 0.8', b'"rain": -1e999', 1), "QUALITY-NONFINITE")
    refused_by("an integer above 2^53 - 1", B0.replace(b'"w": 48', b'"w": 9007199254740993', 1), "QUALITY-INTEGER")
    refused_by("a key twice in one object", B0.replace(b'"exposure": 1.5,', b'"exposure": 1.5,\n  "exposure": 9.0,', 1), "QUALITY-DUPLICATE-KEY")
    refused_by("the same scene in another byte form", json.dumps(S0, sort_keys=True).encode("utf-8") + b"\n", "QUALITY-FORM")
    refused_by("a byte that is not UTF-8", B0.replace(b"Rain-soaked", b"Rain\xff-soaked", 1), "QUALITY-FORM")

    # bounds
    def plant(label, fn, want=""):
        S = copy.deepcopy(S0)
        fn(S)
        refused_by(label, scene_of(S), want)
    plant("a colour channel of 256", lambda S: S["materials"]["concrete"].__setitem__("base", [256, 0, 0]), "outside")
    plant("a colour channel of 12.5", lambda S: S["materials"]["concrete"].__setitem__("base", [12.5, 0, 0]), "not an integer")
    plant("a negative candela", lambda S: S["lights"][0].__setitem__("candela", -1.0), "outside")
    plant("a sun of 150,001 lux", lambda S: S["environment"]["light"].__setitem__("lux", 150001.0), "outside")
    plant("a box with no width", lambda S: S["visuals"][0]["box"].__setitem__(3, S["visuals"][0]["box"][0]), "no extent")
    plant("a box outside the world", lambda S: S["visuals"][0]["box"].__setitem__(3, 96.5), "outside the world")
    plant("a tower 1,024 m tall", lambda S: S["visuals"][0]["box"].__setitem__(4, 1024.0), "")
    plant("a light inside no world", lambda S: S["lights"][0]["pos"].__setitem__(2, -0.1), "outside the world")
    plant("a field the checker does not know (doors)", lambda S: S.__setitem__("doors", []), "does not know")
    plant("a light with a field the checker does not know", lambda S: S["lights"][0].__setitem__("cone", 30.0), "does not know")
    plant("a visual whose material is not declared", lambda S: S["visuals"][0].__setitem__("material", "chrome"), "not a declared material")
    plant("an id twice", lambda S: S["visuals"][1].__setitem__("id", S["visuals"][0]["id"]), "twice")
    plant("a pitch of 90", lambda S: next(iter(S["views"].values())).__setitem__("pitch", 90.0), "outside")
    plant("a light type the renderer has not (spot)", lambda S: S["lights"][0].__setitem__("type", "spot"), "")
    plant("true for a number (a bool is not a number here)", lambda S: S["environment"].__setitem__("rain", True), "not a number")
    # the float32 rule, both ways: below 1024 m every 0.1 mm step stays its own float32; above, some do not
    below = all(f32(round(1023.0 + k / 10000.0, 4)) != f32(round(1023.0 + (k + 1) / 10000.0, 4)) for k in range(10000))
    above = [k for k in range(10000) if f32(round(1024.0 + k / 10000.0, 4)) == f32(round(1024.0 + (k + 1) / 10000.0, 4))]
    row("float32 keeps every 0.1 mm step apart from 1023 m to 1024 m, and merges some from 1024 m (%d pairs of the next 10,000)" % len(above),
        below and len(above) > 0)

    # 0226: movers. The world with a lift and a deck passes; each defect in its movers is refused
    outm = dress.export(dress.load("harbor-lift"))
    SM, BM = outm["scene"], outm["scene_bytes"]
    res, _n = check_scene(BM)
    row("harbor-lift's scene, with %d movers under rules %s, passes every exact check" % (len(SM.get("movers", [])), SM.get("rules")),
        all(ok for _c, ok, _d in res) and SM.get("rules") == 2 and len(SM.get("movers", [])) == 2, "; ".join(d for _c, _ok, d in res))

    def mplant(label, fn, want=""):
        S = copy.deepcopy(SM)
        fn(S)
        refused_by(label, scene_of(S), want)
    mplant("movers without the rules they are played under", lambda S: S.__delitem__("rules"), "together")
    mplant("rules without movers", lambda S: S.__delitem__("movers"), "together")
    mplant("rules 3, which no scene may name", lambda S: S.__setitem__("rules", 3), "is not rules 2")
    mplant("rules 2.0, a number but not an integer", lambda S: S.__setitem__("rules", 2.0), "is not rules 2")
    mplant("a mover's corner not a whole number of 1/256 m", lambda S: S["movers"][0]["box"].__setitem__(0, 20.1), "1/256 m")
    mplant("a mover whose travel leaves the world", lambda S: S["movers"][0].__setitem__("len", 4096 * 20), "outside the world")
    mplant("a lift whose travel rises to 1,024 m", lambda S: S["movers"][1].__setitem__("len", 1024 * 256), "")
    mplant("a mover's speed above its len", lambda S: S["movers"][1].__setitem__("speed", 577), "outside")
    mplant("a mover's axis that is two axes", lambda S: S["movers"][0].__setitem__("axis", [1, 0, 1]), "either way")
    mplant("a mover's policy other than stop", lambda S: S["movers"][0].__setitem__("policy", "push"), "not stop")
    mplant("a mover with a field the checker does not know", lambda S: S["movers"][0].__setitem__("phase", 3), "does not know")
    mplant("a mover whose material is not declared", lambda S: S["movers"][0].__setitem__("material", "chrome"), "not a declared material")
    mplant("an empty list of movers", lambda S: S.__setitem__("movers", []), "at least one")

    # budgets
    lim = renderer_limits()
    row("the renderer's own numbers, read from its source", lim["lights"] == 160 and lim["glare_candela"] == 2000 and lim["movers"] == 64, json.dumps(lim, sort_keys=True))
    S = copy.deepcopy(SM)
    while len(S["movers"]) <= lim["movers"]:
        S["movers"].append(dict(copy.deepcopy(SM["movers"][1]), id="plant-%d" % len(S["movers"])))
    refused_by("%d movers, one more than the renderer draws" % len(S["movers"]), scene_of(S), "drops the rest")
    S = copy.deepcopy(S0)
    while len(S["lights"]) <= lim["lights"]:
        L = copy.deepcopy(S0["lights"][len(S["lights"]) % len(S0["lights"])])
        L["id"] = "lamp:plant:%d" % len(S["lights"])
        S["lights"].append(L)
    refused_by("%d lights, one more than the renderer draws" % len(S["lights"]), scene_of(S), "drops the rest")
    S = copy.deepcopy(S0)
    S["lights"] = S["lights"][:lim["lights"]] if len(S["lights"]) > lim["lights"] else S["lights"]
    r, _n = check_scene(scene_of(S))
    row("  and the scene at the cap passes the budget", all(ok for _c, ok, _d in r))
    S = copy.deepcopy(S0)
    S["visuals"] += [dict(copy.deepcopy(S0["visuals"][0]), id="plant:%d" % k) for k in range(BUDGET_BOXES)]
    refused_by("more boxes than the budget", scene_of(S), "budget")
    S = copy.deepcopy(S0)
    S["lights"][0]["candela"] = 2500.0
    r, n = check_scene(scene_of(S))
    row("a lamp of 2,500 cd passes and is noticed (its glare drawn at 2,000)", all(ok for _c, ok, _d in r) and n and "2000" in n[0][1], n[0][1] if n else "no notice")
    js = open(RENDERER, "rb").read().decode("utf-8")
    try:
        renderer_limits(js.replace("S.lights.slice(0, 160)", "S.lights.slice(0, LIGHTS)"))
        row("plant: a renderer whose cap is no longer a number in its source — refused", False, "NOT refused")
    except QualityError as e:
        row("plant: a renderer whose cap is no longer a number in its source — refused", e.code == "QUALITY-RENDERER", str(e)[:120])
    try:
        renderer_limits(js + "\nconst again = S.lights.slice(0, 200);\n")
        row("plant: a renderer that says its cap twice — refused", False, "NOT refused")
    except QualityError as e:
        row("plant: a renderer that says its cap twice — refused", e.code == "QUALITY-RENDERER")

    # references: compare reads only; freeze appends once, and refuses the same inputs giving other bytes
    tmp = tempfile.mkdtemp(prefix="quality-")
    try:
        p = os.path.join(tmp, "references.jsonl")
        ok, d = compare_reference("plaza-night", out["lineage"], B0, read_references(p))
        row("no reference: the comparison fails and writes nothing", not ok and not os.path.exists(p), d[:110])
        e, wrote = freeze("plaza-night", "self-test", p, at="2026-10-13T00:00:00Z")
        e2, wrote2 = freeze("plaza-night", "self-test again", p, at="2026-10-13T00:00:01Z")
        row("freeze appends one line, and a second freeze of the same inputs writes nothing", wrote and not wrote2 and open(p, "rb").read().count(b"\n") == 1)
        ok, d = compare_reference("plaza-night", out["lineage"], B0, read_references(p))
        row("the scene is its frozen reference", ok, d)
        S = copy.deepcopy(S0)
        S["visuals"][0]["box"][4] = round(S["visuals"][0]["box"][4] + 0.5, 4)
        ok, d = compare_reference("plaza-night", out["lineage"], scene_of(S), read_references(p))
        row("plant: other bytes from the same inputs — refused, naming the field", not ok and "visuals" in d and "lights" not in d.split("fields ")[1].split(" differ")[0], d[:140])
        L2 = dict(out["lineage"], exporter_sha256="e" * 64)
        S["lights"][0]["candela"] = 41.0
        ok, d = compare_reference("plaza-night", L2, scene_of(S), read_references(p))
        row("plant: a new exporter with no reference — refused, with the fields it moved", not ok and "lights, visuals" in d, d[:150])
        raw = open(p, "rb").read()
        line = json.loads(raw)
        line["scene_sha256"] = "0" * 64
        with open(p, "ab") as fh:
            fh.write(reference_line(dict(line, frozen_at="x")) + b"\n")
        try:
            read_references(p)
            row("plant: the same inputs frozen twice in the file — refused", False, "NOT refused")
        except QualityError as x:
            row("plant: the same inputs frozen twice in the file — refused", x.code == "QUALITY-REFERENCES")
        with open(p, "wb") as fh:
            fh.write(raw.replace(b'","', b'", "', 1))
        try:
            read_references(p)
            row("plant: a reference not in its one byte form — refused", False, "NOT refused")
        except QualityError as x:
            row("plant: a reference not in its one byte form — refused", x.code == "QUALITY-REFERENCES")
        with open(p, "wb") as fh:
            fh.write(raw.replace(e["scene_sha256"].encode(), b"1" * 64))
        try:
            freeze("plaza-night", "self-test", p, at="2026-10-13T00:00:02Z")
            row("plant: a frozen scene the same inputs no longer give — freeze refuses to write over it", False, "NOT refused")
        except QualityError as x:
            row("plant: a frozen scene the same inputs no longer give — freeze refuses to write over it", x.code == "QUALITY-REFERENCE-MOVED" and open(p, "rb").read().count(b"\n") == 1)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    # stills: the decoder, each filter, and the detectors on stills whose answer is known by construction
    w, h = 23, 7
    px = bytes((x * 11 + y * 37 + c * 5) % 256 for y in range(h) for x in range(w) for c in range(3))
    for f in range(5):
        dw, dh, d = decode_png(png_bytes(w, h, px, filters=(f,)))
        row("the decoder reads filter %d back to the same pixels" % f, (dw, dh, d) == (w, h, px))
    row("the decoder reads RGBA with every filter in turn", decode_png(png_bytes(w, h, px, filters=(0, 1, 2, 3, 4), alpha=True))[2] == px)
    for label, kw in (("a 16-bit", {"depth": 16}), ("a palette", {"ctype": 3}), ("an interlaced", {"interlace": 1})):
        try:
            decode_png(png_bytes(w, h, px, **kw))
            row("plant: %s PNG — not checked, and said" % label, False, "read as if checked")
        except QualityError as x:
            row("plant: %s PNG — not checked, and said" % label, x.code == "QUALITY-STILL-UNREAD")
    # the predictor the encoder above shares with the decoder, held to answers worked by hand from the PNG
    # specification's definition (p = a + b - c; the nearest of a, b, c to p, ties to a, then b), so that the two cannot
    # agree on a mistake: (a, b, c) -> the prediction
    paeth_by_hand = {(1, 2, 3): 1, (3, 1, 3): 1, (10, 20, 15): 15, (7, 7, 7): 7, (25, 10, 20): 10, (0, 255, 255): 0, (255, 0, 128): 128}
    row("the Paeth predictor gives the answers worked by hand from the specification", all(_paeth(*k) == v for k, v in paeth_by_hand.items()),
        ", ".join("%s->%d" % (k, _paeth(*k)) for k in sorted(paeth_by_hand)))
    good = png_bytes(w, h, px)
    for label, at in (("one bit of its image data flipped", 40), ("one bit of its last CRC flipped (only the CRC can see it)", len(good) - 1)):
        bad = bytearray(good)
        bad[at] ^= 1
        try:
            decode_png(bytes(bad))
            row("plant: a PNG with %s — not checked, and said" % label, False, "read as if checked")
        except QualityError as x:
            row("plant: a PNG with %s — not checked, and said" % label, x.code == "QUALITY-STILL-UNREAD", str(x)[:80])
    W2, H2 = 40, 25
    half = bytes(255 if (i // 3) < W2 * H2 // 2 else (i % 7) * 20 for i in range(W2 * H2 * 3))
    m, fl = detect(W2, H2, half)
    row("a still half pure white: BLOWN, at 50%", abs(m["white"] - 0.5) < 1e-9 and fl and fl[0].startswith("BLOWN"), fl[0] if fl else "no flag")
    m, fl = detect(W2, H2, bytes(W2 * H2 * 3))
    row("a black frame: BLACK and FLAT", [f.split(":")[0] for f in fl] == ["BLACK", "FLAT"])
    m, fl = detect(W2, H2, bytes([40, 50, 60]) * (W2 * H2))
    row("a frame of one grey: FLAT only", [f.split(":")[0] for f in fl] == ["FLAT"])
    m, fl = detect(w, h, px)
    row("a still of many colours, none white or black: no flag", not fl and m["colours"] > DETECT["flat"])
    df = detector_fields(m, fl)
    row("the detectors in the ledger's form (text, no numbers)", all(isinstance(v, (str, list)) for v in df.values()), json.dumps(df, sort_keys=True)[:120])

    n, k = len(rows), sum(1 for r in rows if r)
    print("QUALITY SELFTEST %d/%d" % (k, n))
    return 0 if k == n else 1


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__ or open(__file__, encoding="utf-8").read().split("\n\n")[0])
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "selftest":
        return cmd_selftest()
    if cmd == "check":
        return cmd_check([a for a in rest if not a.startswith("--")])
    if cmd == "still":
        return cmd_still(rest)
    if cmd == "freeze":
        if not rest or "--note" not in rest or rest.index("--note") + 1 >= len(rest):
            print("python art/quality.py freeze NAME --note TEXT")
            return 2
        note = rest[rest.index("--note") + 1]
        try:
            e, wrote = freeze(rest[0], note)
        except QualityError as x:
            print("REFUSED %s" % x)
            return 1
        print(("FROZEN %s: scene %s at exporter %s (art/references.jsonl)" if wrote else "ALREADY FROZEN %s: scene %s at exporter %s") % (
            rest[0], e["scene_sha256"][:12], e["exporter_sha256"][:12]))
        return 0
    print("unknown command %r" % cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
