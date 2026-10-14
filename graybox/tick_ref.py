# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# graybox/tick_ref.py — a second implementation of the graybox's tick (rules 1, graybox/RULES-1.md), in Python, and
# the verifier of what a browser played.
#
#   python graybox/tick_ref.py verify TRACE.json
#   python graybox/tick_ref.py selftest TRACE.json
#   python graybox/tick_ref.py cases [RESULTS.json]
#   python graybox/tick_ref.py rules2 [RESULTS.json]
#
# By the owner's ruling of 2026-10-11: "implement a second, independent version of the full simulation tick in
# Python", where "Browser JavaScript records the input sequence", "Python independently advances the authoritative
# simulation", "Each tick's expected snapshot is compared with the browser's snapshot", "The first mismatch identifies
# the tick and state field", and "The reference implementation does not call into the browser simulation or trust its
# computed result" — "independent in structure, not merely a line-for-line translation". It is written from
# RULES-1.md, not from sim.js: its own state (classes, not a walked object), its own world, its own collision and ray
# walks, its own snapshot writer and reader. What the two share is the specification, and the arithmetic it names:
# the sine, cosine and atan2 are fdlibm's (from graybox/rules_ref.py, itself a separate implementation), and the
# square root and hypot are computed here with Python's integer square root. Every formula is the specification's,
# operation for operation, since two programs reach the same bits only by the same roundings.
#
# `verify` reads a trace written by graybox/trace.py (any engine), converts the map it names with graybox/level.py and
# holds the trace to it (the manifest's digests), then plays each rules-1 run from its start with the browser's inputs
# and compares every tick's snapshot with the browser's, byte for byte, naming the first tick and the fields that
# differ. It makes the stress run's inputs again from integers and its start from the map, and requires both to be the
# browser's. It trusts nothing the browser computed but the inputs (and the starts of the runs a bot made, which it
# reads back exactly). `selftest` plants defects in a copy of the trace and in this implementation, and requires each
# to be found where it was planted.
#
# The input contract (RULES-1.md, *The input*; INPUT-CONTRACT-0, the owner's ruling of 2026-10-11): `tick` admits its
# input or refuses it, whole, before anything of the state is touched. `cases` plays the shared table of hostile inputs
# (web/input_cases.json) here and holds it to each step's required outcome, with four plants that must break it; given
# the results a browser sent (graybox/trace.py run --cases), it holds them to the table and to Python, step by step,
# the outcome and the state.
#
# Rules 2 (graybox/RULES-2.md, 0225): movers, written here from RULES-2.md in this file's own shape — a Mover and its
# pose, the body against boxes, the mover step, the height step with a ceiling, the identity-bound FNV-1a 64 hash.
# `rules2` plays rules 2's table (web/rules2_cases.json) here and holds each case to the values its working gives by
# hand, and holds the case of no movers to rules 1 played here; given the results a JavaScript engine sent (graybox/
# trace.py run --rules2), it holds them to the same values and to Python, every tick's snapshot and hash.
#
# What it does not show: that a server built on it is secure, that inputs from a malicious client are bounded, or
# anything about a network. Standard library only; it writes nothing.

import importlib.util
import json
import math
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import level  # noqa: E402

_spec = importlib.util.spec_from_file_location("rules_ref", os.path.join(HERE, "rules_ref.py"))
arith = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(arith)


# ------------------------------------------------------------------------------------------------ the arithmetic
def sin(x):
    return arith.xsin(x)


def cos(x):
    return arith.xcos(x)


def _parts(x):
    b = struct.unpack(">Q", struct.pack(">d", x))[0] & 0x7fffffffffffffff
    e, f = b >> 52, b & ((1 << 52) - 1)
    return (f, -1074) if e == 0 else (f | (1 << 52), e - 1075)


def _round(q, ex, inexact):
    """The double nearest to (q + d) * 2^ex for some d in [0, 1), d > 0 when inexact; ties to even."""
    lead = ex + q.bit_length() - 1
    unit = lead - 52 if lead >= -1022 else -1074
    drop = unit - ex
    assert drop >= 2
    kept, rest, half = q >> drop, q & ((1 << drop) - 1), 1 << (drop - 1)
    if rest > half or (rest == half and (inexact or kept & 1)):
        kept += 1
    if kept == 1 << 53:
        kept, unit = 1 << 52, unit + 1
    if unit > 971:
        return math.inf
    return math.ldexp(kept, unit)   # exact: kept has at most 53 bits and unit is the result's last place


def hypot(a, b):
    """sqrt(a*a + b*b), correctly rounded: the squares summed exactly, the root by Python's integer square root."""
    if math.isinf(a) or math.isinf(b):
        return math.inf
    if a != a or b != b:
        return math.nan
    terms = [_parts(v) for v in (a, b) if v != 0]
    if not terms:
        return 0.0
    low = min(e for _m, e in terms)
    total = sum((m * m) << (2 * (e - low)) for m, e in terms)
    shift = max(0, 112 - total.bit_length())
    shift += shift & 1
    n = total << shift
    root = math.isqrt(n)
    return _round(root, low - shift // 2, root * root != n)


def floor(x):
    return x if x == 0 or not math.isfinite(x) else float(math.floor(x))


def js_max(a, b):
    if a != a or b != b:
        return math.nan
    if a == 0 and b == 0:
        return a if math.copysign(1, a) > 0 else b
    return a if a > b else b


def js_min(a, b):
    if a != a or b != b:
        return math.nan
    if a == 0 and b == 0:
        return a if math.copysign(1, a) < 0 else b
    return a if a < b else b


PI = struct.unpack(">d", bytes.fromhex("400921fb54442d18"))[0]
TWO_PI = 2.0 * PI
TICK = 1.0 / 120.0


# ------------------------------------------------------------------------------------------------ the constants
class K:
    radius, eye, step, speed, gravity, jump = 0.35, 1.62, 0.55, 6.0, 20.0, 7.0
    fire_cooldown, target_radius, target_height, target_down, ray_range = 0.12, 0.4, 1.9, 2.5, 200.0
    pitch_limit, stand_again = 1.45, 1e-9


# ------------------------------------------------------------------------------------------------ the world
class World:
    def __init__(self, conv):
        C, W = conv["collision"], conv["canonical"]
        self.w, self.h, self.cell = C["w"], C["h"], float(C["cell"])
        self.rows = [[float(C["tops"][j * C["w"] + i]) for i in range(C["w"])] for j in range(C["h"])]
        self.spawns = {k: (v["x"], v["z"], float(v["yaw"])) for k, v in W["spawns"].items()}
        self.objective = tuple(W["objective"]["rect"]) if W.get("objective") else None
        self.target_cells = [(t["id"], t["x"], t["z"]) for t in W["targets"]]
        self.oi = self.oj = 0   # ORT-1 (0227): the origin, whole cells; only a rules-2 world has another

    def top(self, i, j):
        i, j = i + self.oi, j + self.oj   # the map's cell, through the origin
        if 0 <= i < self.w and 0 <= j < self.h:
            return self.rows[int(j)][int(i)]
        return math.inf

    def cells_near(self, x, z, r):
        """The cells a circle of radius r at (x, z) overlaps, strictly."""
        c = self.cell
        i = floor((x - r) / c)
        while i <= floor((x + r) / c):
            j = floor((z - r) / c)
            while j <= floor((z + r) / c):
                px = js_max(i * c, js_min(x, (i + 1) * c))
                pz = js_max(j * c, js_min(z, (j + 1) * c))
                dx, dz = x - px, z - pz
                if dx * dx + dz * dz < r * r:
                    yield i, j
                j += 1
            i += 1

    def ground(self, x, z):
        g = 0.0
        for i, j in self.cells_near(x, z, K.radius):
            t = self.top(i, j)
            if t > g:
                g = t
        return g


# ------------------------------------------------------------------------------------------------ the state
class Target:
    __slots__ = ("id", "x", "y", "z", "up", "down_for")

    def __init__(self, tid, x, y, z, up, down_for):
        self.id, self.x, self.y, self.z, self.up, self.down_for = tid, x, y, z, up, down_for


class State:
    __slots__ = ("tick", "side", "x", "z", "feet", "vy", "yaw", "pitch", "on_ground", "cooldown", "score", "shots",
                 "on_objective", "targets")

    @classmethod
    def new(cls, world, side):
        s = cls()
        s.tick = s.x = s.z = s.feet = s.vy = s.yaw = s.pitch = s.cooldown = s.score = s.shots = 0.0
        s.side, s.on_ground, s.on_objective = side, True, False
        c = world.cell
        s.targets = [Target(tid, (tx - world.oi + 0.5) * c, world.top(tx - world.oi, tz - world.oj), (tz - world.oj + 0.5) * c, True, 0.0)
                     for tid, tx, tz in world.target_cells]
        spawn(world, s, side)
        return s


def spawn(world, s, side):
    sx, sz, yaw_degrees = world.spawns[side]
    c = world.cell
    s.side = side
    s.x, s.z = (sx - world.oi + 0.5) * c, (sz - world.oj + 0.5) * c
    s.feet = world.ground(s.x, s.z)
    s.vy, s.on_ground = 0.0, True
    s.yaw, s.pitch = yaw_degrees * PI / 180.0, 0.0


# the snapshot: the specification's JSON, written and read here
FIELDS = (("cooldown", "cooldown"), ("feet", "feet"), ("onGround", "on_ground"), ("onObjective", "on_objective"),
          ("pitch", "pitch"), ("score", "score"), ("shots", "shots"), ("side", "side"), ("tick", "tick"),
          ("vy", "vy"), ("x", "x"), ("yaw", "yaw"), ("z", "z"))
TARGET_FIELDS = (("downFor", "down_for"), ("id", "id"), ("up", "up"), ("x", "x"), ("y", "y"), ("z", "z"))


def _enc(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return '"f%s"' % struct.pack(">d", v).hex()
    if isinstance(v, str):
        return json.dumps("s" + v, ensure_ascii=False)
    raise TypeError("the state holds a %s" % type(v).__name__)


def write_snapshot(s):
    out = []
    for name, attr in FIELDS[:8]:
        out.append('"%s":%s' % (name, _enc(getattr(s, attr))))
    out.append('"targets":[%s]' % ",".join("{%s}" % ",".join('"%s":%s' % (n, _enc(getattr(t, a))) for n, a in TARGET_FIELDS) for t in s.targets))
    for name, attr in FIELDS[8:]:
        out.append('"%s":%s' % (name, _enc(getattr(s, attr))))
    return "{" + ",".join(out) + "}"


def _dec(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, str) and v[:1] == "f" and len(v) == 17:
        return struct.unpack(">d", bytes.fromhex(v[1:]))[0]
    if isinstance(v, str) and v[:1] == "s":
        return v[1:]
    raise ValueError("not a snapshot value: %r" % (v,))


def read_snapshot(text):
    d = json.loads(text)
    s = State()
    for name, attr in FIELDS:
        setattr(s, attr, _dec(d[name]))
    s.targets = [Target(*(_dec(t[n]) for n in ("id", "x", "y", "z", "up", "downFor"))) for t in d["targets"]]
    if set(d) != {n for n, _a in FIELDS} | {"targets"}:
        raise ValueError("the snapshot holds fields the specification does not: %s" % sorted(set(d) - {n for n, _a in FIELDS} - {"targets"}))
    return s


# ------------------------------------------------------------------------------------------------ one tick
def truthy(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, float):
        return v == v and v != 0
    if isinstance(v, str):
        return v != ""
    return v is not None


def number(inp, key):
    v = inp.get(key)
    return v if isinstance(v, float) and v == v and v != 0 else 0.0


def is_blocked(world, s, x, z, feet):
    if any(world.top(i, j) > feet + K.step for i, j in world.cells_near(x, z, K.radius)):
        return True
    rr = K.radius + K.target_radius
    for t in s.targets:
        if t.up:
            dx, dz = x - t.x, z - t.z
            if dx * dx + dz * dz < rr * rr and feet < t.y + K.target_height:
                return True
    return False


def move(world, s, dx, dz):
    if not is_blocked(world, s, s.x + dx, s.z + dz, s.feet):
        s.x, s.z = s.x + dx, s.z + dz
        return
    halvings = 6
    while halvings:
        halvings -= 1
        dx, dz = dx / 2.0, dz / 2.0
        if not is_blocked(world, s, s.x + dx, s.z + dz, s.feet):
            s.x, s.z = s.x + dx, s.z + dz


def wall_distance(world, ox, oy, oz, dx, dy, dz, reach):
    c = world.cell
    i, j = floor(ox / c), floor(oz / c)
    si, sj = (1.0 if dx > 0 else -1.0), (1.0 if dz > 0 else -1.0)
    tdx = abs(c / dx) if dx != 0 else math.inf
    tdz = abs(c / dz) if dz != 0 else math.inf
    tmx = (((i + 1) * c - ox) if dx > 0 else (ox - i * c)) / abs(dx) if dx != 0 else math.inf
    tmz = (((j + 1) * c - oz) if dz > 0 else (oz - j * c)) / abs(dz) if dz != 0 else math.inf
    t0, steps = 0.0, 0
    while steps < 10000 and t0 < reach:
        steps += 1
        t1 = js_min(js_min(tmx, tmz), reach)
        top = world.top(i, j)
        if top == math.inf:
            return t0
        if oy + dy * t0 <= top:
            return t0
        if oy + dy * t1 <= top:
            return (top - oy) / dy
        if tmx < tmz:
            i, t0, tmx = i + si, tmx, tmx + tdx
        else:
            j, t0, tmz = j + sj, tmz, tmz + tdz
    return reach


def box_entry(o, d, lo, hi):
    near, far = -math.inf, math.inf
    for a in range(3):
        if d[a] == 0:
            if o[a] < lo[a] or o[a] > hi[a]:
                return math.inf
            continue
        ta, tb = (lo[a] - o[a]) / d[a], (hi[a] - o[a]) / d[a]
        if ta > tb:
            ta, tb = tb, ta
        if ta > near:
            near = ta
        if tb < far:
            far = tb
        if near > far:
            return math.inf
    return math.inf if far < 0 else js_max(near, 0.0)


def shoot(world, s):
    s.shots = s.shots + 1.0
    cp = cos(s.pitch)
    d = (cp * sin(s.yaw), sin(s.pitch), (-cp) * cos(s.yaw))
    o = (s.x, s.feet + K.eye, s.z)
    best, best_t = None, wall_distance(world, o[0], o[1], o[2], d[0], d[1], d[2], K.ray_range)
    r = K.target_radius
    for t in s.targets:
        if not t.up:
            continue
        tt = box_entry(o, d, (t.x - r, t.y, t.z - r), (t.x + r, t.y + K.target_height, t.z + r))
        if tt < best_t:
            best, best_t = t, tt
    if best is not None:
        best.up, best.down_for = False, K.target_down
        s.score = s.score + 1.0


def turn(world, s, inp):
    if truthy(inp.get("side")):
        spawn(world, s, inp["side"])
    elif truthy(inp.get("reset")):
        spawn(world, s, s.side)
    s.yaw = math.fmod(math.fmod(s.yaw + number(inp, "dyaw"), TWO_PI) + TWO_PI, TWO_PI)
    p = s.pitch + number(inp, "dpitch")
    s.pitch = -K.pitch_limit if p < -K.pitch_limit else K.pitch_limit if p > K.pitch_limit else p


def walk(world, s, inp):
    fwd = (1.0 if truthy(inp.get("f")) else 0.0) - (1.0 if truthy(inp.get("b")) else 0.0)
    side = (1.0 if truthy(inp.get("r")) else 0.0) - (1.0 if truthy(inp.get("l")) else 0.0)
    sy, cy = sin(s.yaw), cos(s.yaw)
    mx, mz = fwd * sy + side * cy, (-fwd) * cy + side * sy
    length = hypot(mx, mz)
    if length > 0:
        move(world, s, mx / length * K.speed * TICK, 0.0)
        move(world, s, 0.0, mz / length * K.speed * TICK)


def fall(world, s, inp):
    was = s.on_ground
    if truthy(inp.get("jump")) and s.on_ground:
        s.vy, s.on_ground = K.jump, False
    s.vy = s.vy - K.gravity * TICK
    s.feet = s.feet + s.vy * TICK
    land(world, s, was)


def land(world, s, was):
    g = world.ground(s.x, s.z)
    if s.feet <= g or (was and s.vy <= 0 and s.feet - g <= K.step):
        s.feet, s.vy, s.on_ground = g, 0.0, True
    else:
        s.on_ground = False


def weapon(world, s, inp):
    s.cooldown = js_max(0.0, s.cooldown - TICK)
    if truthy(inp.get("fire")) and s.cooldown == 0:
        s.cooldown = K.fire_cooldown
        shoot(world, s)


def stand_again(world, s, inp):
    for t in s.targets:
        if not t.up:
            t.down_for = t.down_for - TICK
            if t.down_for <= K.stand_again:
                t.up, t.down_for = True, 0.0


def objective(world, s, inp):
    if world.objective is None:
        s.on_objective = False
    else:
        i0, j0, i1, j1 = world.objective
        i, j = floor(s.x / world.cell) + world.oi, floor(s.z / world.cell) + world.oj
        s.on_objective = i0 <= i <= i1 and j0 <= j <= j1


PHASES = ("turn", "walk", "fall", "weapon", "stand_again", "objective")


def tick(world, s, inp):
    """One tick of rules 1 (RULES-1.md, *One tick*), on s in place: its phases in their order, on the input as the
    contract admits it (*The input*). A refused input raises InputRefused before anything of s is touched."""
    a = admit(inp)
    if isinstance(a, str):
        raise InputRefused(a)
    advance(world, s, a)


def advance(world, s, a):
    """The tick itself, on an admitted input."""
    s.tick = s.tick + 1.0
    for name in PHASES:
        globals()[name](world, s, a)


# ------------------------------------------------------------------------------------------------ rules 2 (RULES-2.md)
RULES2 = 2
Q = 1.0 / 256.0
BODY = 1.8
FNV_OFFSET, FNV_PRIME, FNV_MASK = 0xcbf29ce484222325, 0x100000001b3, (1 << 64) - 1


class MoverRefused(Exception):
    pass


class Mover:
    """One mover of the world, as RULES-2.md's table admits it."""
    __slots__ = ("id", "x0", "y0", "z0", "x1", "y1", "z1", "ax", "ay", "az", "length", "speed", "policy")

    def __init__(self, d, ids):
        mid = d.get("id") if isinstance(d, dict) else None
        if not isinstance(mid, str) or not mid or mid in ids:
            raise MoverRefused("RULES2-MOVER: mover %r: its id is not text, or not unique" % (mid,))

        def q(v):
            return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and abs(v) < 1024 and float(v) * 256.0 == floor(float(v) * 256.0)
        box = d.get("box")
        if not (isinstance(box, list) and len(box) == 6 and all(q(v) for v in box)):
            raise MoverRefused("RULES2-MOVER: mover %r: its box is not six multiples of 1/256 m below 1,024 m" % mid)
        self.x0, self.y0, self.z0, self.x1, self.y1, self.z1 = (float(v) for v in box)
        if not (self.x0 < self.x1 and self.y0 < self.y1 and self.z0 < self.z1):
            raise MoverRefused("RULES2-MOVER: mover %r: its box has no extent on some axis" % mid)
        axis = d.get("axis")
        if not (isinstance(axis, list) and len(axis) == 3 and all(v in (-1, 0, 1) and not isinstance(v, bool) for v in axis)
                and sum(abs(v) for v in axis) == 1):
            raise MoverRefused("RULES2-MOVER: mover %r: its axis is not one of x, y, z, either way" % mid)
        self.ax, self.ay, self.az = (float(v) for v in axis)

        def integer(v, lo, hi):
            return isinstance(v, int) and not isinstance(v, bool) and lo <= v <= hi
        if not integer(d.get("len"), 1, 1 << 18):
            raise MoverRefused("RULES2-MOVER: mover %r: its len is not an integer from 1 to 2^18" % mid)
        if not integer(d.get("speed"), 0, d["len"]):
            raise MoverRefused("RULES2-MOVER: mover %r: its speed is not an integer from 0 to its len" % mid)
        self.length, self.speed = float(d["len"]), float(d["speed"])
        if d.get("policy") != "stop":
            raise MoverRefused("RULES2-MOVER: mover %r: its policy is not stop" % mid)
        self.id, self.policy = mid, "stop"
        # the tunnelling bound: less than the body's depth plus the box's own, along its axis
        t = (self.x1 - self.x0) if self.ax else (self.y1 - self.y0) if self.ay else (self.z1 - self.z0)
        bound = (BODY + t) if self.ay else (2.0 * K.radius + t)
        if not self.speed * Q < bound:
            raise MoverRefused("RULES2-MOVER: mover %r: %r m a tick is not less than the tunnelling bound %r m" % (mid, self.speed * Q, bound))

    def pose(self, phase):
        o = phase if phase < self.length else 2.0 * self.length - phase
        d = o * Q
        return (self.x0 + self.ax * d, self.y0 + self.ay * d, self.z0 + self.az * d,
                self.x1 + self.ax * d, self.y1 + self.ay * d, self.z1 + self.az * d)


class MoverState:
    __slots__ = ("phase", "stopped")

    def __init__(self, phase, stopped):
        self.phase, self.stopped = phase, stopped


ORIGIN_MAX = 1 << 20   # ORT-1: an origin's cells, either way


class World2(World):
    """A world of rules 2: rules 1's, with its movers, its origin (ORT-1, 0227; (0, 0) unless given) and the identity
    its hashes start from."""

    def __init__(self, conv, movers, origin=(0, 0)):
        World.__init__(self, conv)
        if not (isinstance(origin, (list, tuple)) and len(origin) == 2
                and all(isinstance(v, int) and not isinstance(v, bool) and -ORIGIN_MAX <= v <= ORIGIN_MAX for v in origin)):
            raise MoverRefused("ORT-ORIGIN: the origin is not two whole numbers of cells, each at most 2^20")
        self.oi, self.oj = int(origin[0]), int(origin[1])
        self.conv = conv
        ids = set()
        self.movers = []
        for d in movers:
            m = Mover(d, ids)
            ids.add(m.id)
            self.movers.append(m)
        C, W = conv["collision"], conv["canonical"]
        self.identity = identity_text(C, W, self.movers, (self.oi, self.oj))
        self.identity_state = fnv64(FNV_OFFSET, self.identity.encode("utf-8"))


class State2(State):
    __slots__ = ("movers",)

    @classmethod
    def new(cls, world, side):
        s = super().new(world, side)
        s.movers = [MoverState(0.0, False) for _m in world.movers]
        return s


def fnv64(h, data):
    for b in data:
        h = ((h ^ b) * FNV_PRIME) & FNV_MASK
    return h


def _idenc(v):
    if isinstance(v, bool):
        raise TypeError("the identity holds no booleans")
    if isinstance(v, (int, float)):
        return "f" + struct.pack(">d", float(v)).hex()
    if isinstance(v, str):
        return "s" + v
    if v is None:
        return None
    if isinstance(v, (list, tuple)):
        return [_idenc(x) for x in v]
    return {k: _idenc(v[k]) for k in v}


def identity_text(C, W, movers, origin=(0, 0)):
    """RULES-2.md, *The state's hash*: the rules, every constant and the world, as one document; a rebased world's
    origin with it (ORT-1), and at the origin (0, 0) the document as rules 2 first wrote it."""
    doc = {
        "P": {"radius": K.radius, "eye": K.eye, "step": K.step, "speed": K.speed, "gravity": K.gravity, "jump": K.jump,
              "fireCooldown": K.fire_cooldown, "targetRadius": K.target_radius, "targetHeight": K.target_height,
              "targetDown": K.target_down, "range": K.ray_range, "height": BODY},
        "Q": Q, "TICK": TICK, "input": float(INPUT), "pitch": K.pitch_limit, "rules": float(RULES2), "stand": K.stand_again,
        "world": {"cell": float(C["cell"]), "h": float(C["h"]), "w": float(C["w"]), "tops": [float(t) for t in C["tops"]],
                  "movers": [[m.id, m.x0, m.y0, m.z0, m.x1, m.y1, m.z1, m.ax, m.ay, m.az, m.length, m.speed, m.policy] for m in movers],
                  "objective": list(W["objective"]["rect"]) if W.get("objective") else None,
                  "spawns": {k: [v["x"], v["z"], v["yaw"]] for k, v in W["spawns"].items()},
                  "targets": [[t["id"], t["x"], t["z"]] for t in W["targets"]]},
    }
    if origin[0] != 0 or origin[1] != 0:
        doc["world"]["origin"] = [float(origin[0]), float(origin[1])]
    return "VERDANDI-RULES 2\n" + json.dumps(_idenc(doc), separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def hash2(world, s):
    nums = [s.tick, s.x, s.z, s.feet, s.vy, s.yaw, s.pitch, 1.0 if s.on_ground else 0.0, s.cooldown, s.score, s.shots,
            1.0 if s.on_objective else 0.0]
    for t in s.targets:
        nums += [1.0 if t.up else 0.0, t.down_for]
    for mv in s.movers:
        nums += [mv.phase, 1.0 if mv.stopped else 0.0]
    h = fnv64(world.identity_state, b"".join(struct.pack("<d", v) for v in nums))
    return "%016x%s" % (h, s.side)


def write_snapshot2(s):
    """Rules 1's snapshot with `movers` in its place among the sorted keys (after `feet`)."""
    base = write_snapshot(s)
    movers = '"movers":[%s]' % ",".join('{"phase":%s,"stopped":%s}' % (_enc(m.phase), _enc(m.stopped)) for m in s.movers)
    at = base.index('"onGround":')
    return base[:at] + movers + "," + base[at:]


def plan_over(x, z, b):
    """The circle of the player's radius at (x, z) overlaps box b in plan, strictly."""
    px = js_max(b[0], js_min(x, b[3]))
    pz = js_max(b[2], js_min(z, b[5]))
    dx, dz = x - px, z - pz
    return dx * dx + dz * dz < K.radius * K.radius


def poses(world, s, k=None, bk=None):
    return [bk if i == k else m.pose(s.movers[i].phase) for i, m in enumerate(world.movers)]


def is_blocked2(world, s, x, z, feet, k=None, bk=None):
    if is_blocked(world, s, x, z, feet):
        return True
    return any(plan_over(x, z, b) and b[4] > feet + K.step and b[1] < feet + BODY for b in poses(world, s, k, bk))


def move2(world, s, dx, dz):
    if not is_blocked2(world, s, s.x + dx, s.z + dz, s.feet):
        s.x, s.z = s.x + dx, s.z + dz
        return
    for _ in range(6):
        dx, dz = dx / 2.0, dz / 2.0
        if not is_blocked2(world, s, s.x + dx, s.z + dz, s.feet):
            s.x, s.z = s.x + dx, s.z + dz


def respawn2(world, s, inp):
    if truthy(inp.get("side")):
        spawn(world, s, inp["side"])
    elif truthy(inp.get("reset")):
        spawn(world, s, s.side)


def movers2(world, s, inp):
    for k, m in enumerate(world.movers):
        st = s.movers[k]
        if m.speed == 0:
            st.stopped = False
            continue
        n = st.phase + m.speed
        if n >= 2.0 * m.length:
            n = n - 2.0 * m.length
        a, b = m.pose(st.phase), m.pose(n)
        dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        rider = s.on_ground and s.feet == a[4] and plan_over(s.x, s.z, a)
        if rider:
            nx, nz, nf = s.x + dx, s.z + dz, s.feet + dy
            if is_blocked2(world, s, nx, nz, nf, k, b):
                st.stopped = True
            else:
                st.phase, st.stopped = n, False
                s.x, s.z, s.feet = nx, nz, nf
        elif plan_over(s.x, s.z, b) and b[4] > s.feet and b[1] < s.feet + BODY:
            st.stopped = True
        else:
            st.phase, st.stopped = n, False


def aim2(world, s, inp):
    s.yaw = math.fmod(math.fmod(s.yaw + number(inp, "dyaw"), TWO_PI) + TWO_PI, TWO_PI)
    p = s.pitch + number(inp, "dpitch")
    s.pitch = -K.pitch_limit if p < -K.pitch_limit else K.pitch_limit if p > K.pitch_limit else p


def walk2(world, s, inp):
    fwd = (1.0 if truthy(inp.get("f")) else 0.0) - (1.0 if truthy(inp.get("b")) else 0.0)
    side = (1.0 if truthy(inp.get("r")) else 0.0) - (1.0 if truthy(inp.get("l")) else 0.0)
    sy, cy = sin(s.yaw), cos(s.yaw)
    mx, mz = fwd * sy + side * cy, (-fwd) * cy + side * sy
    length = hypot(mx, mz)
    if length > 0:
        move2(world, s, mx / length * K.speed * TICK, 0.0)
        move2(world, s, 0.0, mz / length * K.speed * TICK)


def height2(world, s, inp):
    was, before = s.on_ground, s.feet
    if truthy(inp.get("jump")) and s.on_ground:
        s.vy, s.on_ground = K.jump, False
    s.vy = s.vy - K.gravity * TICK
    s.feet = s.feet + s.vy * TICK
    boxes = poses(world, s)
    c = math.inf
    for b in boxes:
        if plan_over(s.x, s.z, b) and b[1] >= before + BODY and b[1] < c:
            c = b[1]
    if s.feet + BODY > c:
        s.feet = c - BODY
        if s.vy > 0:
            s.vy = 0.0
    g = world.ground(s.x, s.z)
    for b in boxes:
        if plan_over(s.x, s.z, b) and b[4] <= before + K.step and b[4] > g:
            g = b[4]
    if s.feet <= g or (was and s.vy <= 0 and s.feet - g <= K.step):
        s.feet, s.vy, s.on_ground = g, 0.0, True
    else:
        s.on_ground = False


PHASES2 = (respawn2, movers2, aim2, walk2, height2, weapon, stand_again, objective)


def tick2(world, s, inp):
    """One tick of rules 2 (RULES-2.md, *One tick*), on an input the contract admits."""
    a = admit(inp)
    if isinstance(a, str):
        raise InputRefused(a)
    s.tick = s.tick + 1.0
    for phase in PHASES2:
        phase(world, s, a)


# ------------------------------------------------------------------------------------------------ the input (contract 1)
INPUT = 1
FLAGS = ("b", "f", "fire", "jump", "l", "r", "reset")
TURNS = ("dpitch", "dyaw")


class InputRefused(Exception):
    def __init__(self, category):
        super().__init__(category)
        self.category = category


def utf16(name):
    return name.encode("utf-16-be")


def admit(inp, lax=()):
    """RULES-1.md, *The input*: a copy of the record if the contract admits it, else the category of its first fault
    (the record, then its fields in the order of their names by UTF-16 code units). `lax` is for the plants alone."""
    if type(inp) is not dict:
        return "INPUT-NOT-RECORD"
    if not all(type(k) is str for k in inp):
        return "INPUT-UNKNOWN-FIELD"
    a = {}
    for k in sorted(inp, key=utf16):
        v = inp[k]
        if k in FLAGS:
            if type(v) is not bool:
                return "INPUT-FLAG"
        elif k == "side":
            if type(v) is not str or v not in ("A", "B"):
                return "INPUT-SIDE"
        elif k in TURNS:
            if type(v) is not float:
                return "INPUT-NUMBER"
            if not math.isfinite(v) and not ("nan" in lax and v != v):
                return "INPUT-NOT-FINITE"
        elif "unknown" in lax:
            continue
        else:
            return "INPUT-UNKNOWN-FIELD"
        a[k] = v
    return a


# ------------------------------------------------------------------------------------------------ inputs
def read_input(text):
    out = {}
    for k, v in json.loads(text):
        out[k] = struct.unpack(">d", bytes.fromhex(v[1:]))[0] if isinstance(v, str) and len(v) == 17 and v[:1] == "f" else v
    return out


def write_input(inp):
    pairs = []
    for k in sorted(inp):
        v = inp[k]
        pairs.append([k, "f" + struct.pack(">d", v).hex() if isinstance(v, float) else v])
    return json.dumps(pairs, separators=(",", ":"), ensure_ascii=False)


def stress_inputs(n):
    """The stress run's inputs, made from integers (sim.js's stressInputs, as RULES-1.md says)."""
    st, hold, cur, out = 0x9e3779b9, 0, None, []

    def nxt():
        nonlocal st
        st = (st * 1664525 + 1013904223) & 0xffffffff
        return st

    for k in range(n):
        if hold == 0:
            a = nxt()
            cur = {"f": (a & 1) == 1, "b": (a & 3) == 2, "l": (a & 4) == 4, "r": (a & 12) == 8}
            hold = 10 + nxt() % 50
        hold -= 1
        a = nxt()
        inp = dict(cur, dyaw=float(a % 2049 - 1024) / 8192.0, dpitch=float((a >> 11) % 257 - 128) / 16384.0)
        if (a >> 20) % 97 == 0:
            inp["jump"] = True
        if (a >> 24) % 23 == 0:
            inp["fire"] = True
        if k == n >> 1:
            inp["side"] = "B"
        out.append(inp)
    return out


# ------------------------------------------------------------------------------------------------ verification
def fields_of(text):
    d = json.loads(text)
    out = {k: v for k, v in d.items() if k != "targets"}
    for n, t in enumerate(d.get("targets", [])):
        for k, v in t.items():
            out["targets[%d].%s" % (n, k)] = v
    return out


def show(v):
    if isinstance(v, str) and v[:1] == "f" and len(v) == 17:
        return repr(struct.unpack(">d", bytes.fromhex(v[1:]))[0])
    return json.dumps(v)


def ulps(a, b):
    def o(h):
        u = int(h, 16)
        return u if u < 1 << 63 else -(u - (1 << 63))
    return abs(o(a[1:]) - o(b[1:]))


def play(world, run):
    """Play a run's inputs from its start; the first tick whose snapshot is not the browser's, or None."""
    s = read_snapshot(run["start"])
    if write_snapshot(s) != run["start"]:
        return {"tick": 0, "what": "the start does not read back to the same bytes"}
    for n, (inp, theirs) in enumerate(zip(run["inputs"], run["snaps"])):
        tick(world, s, read_input(inp))
        mine = write_snapshot(s)
        if mine != theirs:
            a, b = fields_of(mine), fields_of(theirs)
            diff = [(k, a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]
            return {"tick": n + 1, "fields": diff}
    if len(run["inputs"]) != len(run["snaps"]):
        return {"tick": min(len(run["inputs"]), len(run["snaps"])), "what": "the inputs and the snapshots are not as many"}
    return None


def load_trace(path):
    with open(path, encoding="utf-8") as fh:
        T = json.load(fh)
    if T.get("format") != "VERDANDI-TRACE" or T.get("version") != "1" or "1" not in T.get("rules", {}):
        raise SystemExit("TICK-REF: %s is not a VERDANDI-TRACE 1 file with a rules-1 section" % path)
    return T


def check_trace(T, out):
    """The map the trace names, converted here and held to the trace's manifest; the world; problems found."""
    name = T.get("map", "")
    if not re.fullmatch(r"[a-z0-9_-]+", name):
        raise SystemExit("TICK-REF: the trace names no map")
    conv = level.convert(name)
    mine, theirs = conv["manifest"], T.get("manifest") or {}
    same = all(mine.get(k) == theirs.get(k) for k in ("canonical_sha256", "collision_sha256"))
    out.append(("the map", same, "%s converted here: canonical %s, collision %s%s" % (
        name, mine["canonical_sha256"][:12], mine["collision_sha256"][:12], "" if same else "; the trace's are %s, %s" % (
            str(theirs.get("canonical_sha256"))[:12], str(theirs.get("collision_sha256"))[:12]))))
    return World(conv)


def verify(T, world, rows):
    runs = T["rules"]["1"]["runs"]
    total, bad = 0, 0
    for run in runs:
        r = play(world, run)
        if r is None:
            total += len(run["inputs"])
            rows.append(("run " + run["name"], True, "%d ticks: every snapshot the same bytes as the browser's" % len(run["inputs"])))
        else:
            bad += 1
            if "what" in r:
                rows.append(("run " + run["name"], False, "at tick %d: %s" % (r["tick"], r["what"])))
            else:
                rows.append(("run " + run["name"], False, "FIRST DIFFERENT at tick %d, in %s" % (r["tick"], "; ".join(
                    "%s: here %s, the browser %s%s" % (k, show(a), show(b), (", %d ulp" % ulps(a, b)) if isinstance(a, str) and isinstance(b, str) and a[:1] == b[:1] == "f" else "")
                    for k, a, b in r["fields"][:6]))))
    stress = [r for r in runs if r["name"] == "the stress"]
    if stress:
        made = [write_input(i) for i in stress_inputs(len(stress[0]["inputs"]))]
        start = write_snapshot(State.new(world, "A"))
        rows.append(("the stress run's inputs and start, made again here", made == stress[0]["inputs"] and start == stress[0]["start"],
                     "%d inputs from integers%s; the start, a new state at spawn A, %s" % (
                         len(made), "" if made == stress[0]["inputs"] else " NOT the browser's", "the browser's" if start == stress[0]["start"] else "NOT the browser's")))
    return total, bad


def engine(T):
    rt = T.get("runtime") or {}
    return rt.get("userAgent", "?")


def cmd_verify(path):
    T = load_trace(path)
    rows = []
    world = check_trace(T, rows)
    total, _bad = verify(T, world, rows)
    print("TICK-REF  %s  map %s  rules 1  (%s)" % (os.path.basename(path), T["map"], engine(T)))
    for name, ok, detail in rows:
        print("%s %s — %s" % ("PASS" if ok else "FAIL", name, detail))
    ok = all(r[1] for r in rows)
    print("TICK REFERENCE %s  %d ticks of %d runs played here and compared" % ("VERIFIED" if ok else "FAILED", total, len(T["rules"]["1"]["runs"])))
    return 0 if ok else 1


# ------------------------------------------------------------------------------------------------ the input contract's cases
CASES = os.path.join(HERE, "web", "input_cases.json")


def load_cases():
    with open(CASES, encoding="utf-8") as fh:
        table = json.load(fh)
    if table.get("format") != "VERDANDI-INPUT-CASES" or table.get("version") != "1" or table.get("contract") != str(INPUT):
        raise SystemExit("TICK-REF: %s is not a VERDANDI-INPUT-CASES 1 table of contract %d" % (CASES, INPUT))
    return table


def case_value(v):
    """A value as the table writes it: true, false, null; "f" and a number's bits; "s" and a string; a list; a record."""
    if v is None or isinstance(v, bool):
        return v
    if isinstance(v, str):
        if len(v) == 17 and v[:1] == "f":
            return struct.unpack(">d", bytes.fromhex(v[1:]))[0]
        if v[:1] == "s":
            return v[1:]
    if isinstance(v, dict) and set(v) == {"list"}:
        return [case_value(x) for x in v["list"]]
    if isinstance(v, dict) and set(v) == {"record"}:
        return {k: case_value(x) for k, x in v["record"]}
    raise ValueError("not a value of the table: %r" % (v,))


def ticked(world, s, inp):
    """The contract's outcome of one step: None when the tick ran, else the category."""
    try:
        tick(world, s, inp)
    except InputRefused as e:
        return e.category
    return None


def run_cases(world, table, step=ticked):
    out = []
    for c in table["cases"]:
        s = State.new(world, "A")
        start, steps = write_snapshot(s), []
        for st in c["steps"]:
            try:
                r = step(world, s, case_value(st["input"]))
                got = "tick" if r is None else str(r)
            except Exception as e:   # noqa: BLE001 (a plant, or a defect: recorded, never carried on)
                got = "THREW %s" % type(e).__name__
            steps.append({"got": got, "snap": write_snapshot(s)})
        out.append({"name": c["name"], "start": start, "steps": steps})
    return out


def case_faults(table, results):
    """What the table requires: each step's outcome, a refused step's state as before it, same_as."""
    if len(results) != len(table["cases"]):
        return ["the results hold %d cases, the table %d" % (len(results), len(table["cases"]))]
    faults, last = [], {}
    for c, r in zip(table["cases"], results):
        if r.get("name") != c["name"] or len(r.get("steps", [])) != len(c["steps"]):
            faults.append("%s: not the table's case" % c["name"])
            continue
        for k, (st, got) in enumerate(zip(c["steps"], r["steps"])):
            before = r["steps"][k - 1]["snap"] if k else r["start"]
            if got["got"] != st["expect"]:
                faults.append("%s, step %d: %s, not %s" % (c["name"], k + 1, got["got"], st["expect"]))
            elif st["expect"] != "tick" and got["snap"] != before:
                faults.append("%s, step %d: refused, and the state changed" % (c["name"], k + 1))
        last[c["name"]] = r["steps"][-1]["snap"]
    for c in table["cases"]:
        if c.get("same_as") and last.get(c["name"]) != last.get(c["same_as"]):
            faults.append("%s: does not end where %s ends" % (c["name"], c["same_as"]))
    return faults


def _after_begun(world, s, inp):
    s.tick = s.tick + 1.0
    a = admit(inp)
    if isinstance(a, str):
        return a
    s.tick = s.tick - 1.0
    advance(world, s, a)


def _lax(*how):
    def step(world, s, inp):
        a = admit(inp, how)
        if isinstance(a, str):
            return a
        advance(world, s, a)
    return step


def _side_first(world, s, inp):
    if type(inp) is dict and inp.get("side") in ("A", "B"):
        spawn(world, s, inp["side"])
    return ticked(world, s, inp)


CASE_PLANTS = [
    ("the check made after the tick has begun", _after_begun),
    ("NaN admitted", _lax("nan")),
    ("an unknown field ignored", _lax("unknown")),
    ("a side applied before the rest is checked", _side_first),
]


def cmd_cases(path=None):
    table = load_cases()
    world = World(level.convert(table["map"]))
    rows = []
    mine = run_cases(world, table)
    faults = case_faults(table, mine)
    n_steps = sum(len(c["steps"]) for c in table["cases"])
    rows.append(("Python against the table", not faults, ("FAULTS: " + "; ".join(faults[:3])) if faults else
                 "%d cases, %d steps: every admitted step ticked, every refused one refused with its category and the state as it was; "
                 "the runs with refusals among them end where the runs without them end" % (len(table["cases"]), n_steps)))
    for label, plant in CASE_PLANTS:
        f = case_faults(table, run_cases(world, table, plant))
        rows.append(("plant: " + label, bool(f), ("refused, %d faults, the first: %s" % (len(f), f[0])) if f else "NOT refused"))
    engine_line = None
    if path:
        with open(path, encoding="utf-8") as fh:
            R = json.load(fh)
        if R.get("format") != "VERDANDI-INPUT-RESULTS" or R.get("version") != "1" or R.get("error"):
            raise SystemExit("TICK-REF: %s is not a VERDANDI-INPUT-RESULTS 1 file%s" % (path, (": " + R["error"]) if R.get("error") else ""))
        engine_line = (R.get("runtime") or {}).get("userAgent", "?")
        conv = level.convert(table["map"])
        same_map = R.get("map") == table["map"] and all((R.get("manifest") or {}).get(k) == conv["manifest"][k] for k in ("canonical_sha256", "collision_sha256"))
        rows.append(("the browser's map", same_map, "%s, its digests as converted here" % R.get("map") if same_map else "NOT the table's map as converted here"))
        rows.append(("the browser's contract", R.get("contract") == str(INPUT) and R.get("table") == str(INPUT), "contract %s, the table's %s" % (R.get("contract"), R.get("table"))))
        theirs = case_faults(table, R.get("results", []))
        rows.append(("the browser against the table", not theirs, ("FAULTS: " + "; ".join(theirs[:3])) if theirs else "every step as the table requires"))
        first = None
        for c, a, b in zip(table["cases"], mine, R.get("results", [])):
            if a["start"] != b.get("start"):
                first = "%s: the start differs" % c["name"]
                break
            for k, (x, y) in enumerate(zip(a["steps"], b.get("steps", []))):
                if x["got"] != y.get("got"):
                    first = "%s, step %d: here %s, the browser %s" % (c["name"], k + 1, x["got"], y.get("got"))
                elif x["snap"] != y.get("snap"):
                    fa, fb = fields_of(x["snap"]), fields_of(y["snap"])
                    first = "%s, step %d: the state, in %s" % (c["name"], k + 1, ", ".join(f for f in sorted(set(fa) | set(fb)) if fa.get(f) != fb.get(f))[:80])
                if first:
                    break
            if first:
                break
        rows.append(("the browser against Python", first is None, "every outcome and every state the same, %d steps" % n_steps if first is None else "FIRST DIFFERENT: " + first))
    print("TICK-REF CASES  %s  contract %d  map %s%s" % (os.path.basename(CASES), INPUT, table["map"], ("  (" + engine_line + ")") if engine_line else ""))
    for name, ok, detail in rows:
        print("%s %s — %s" % ("PASS" if ok else "FAIL", name, detail))
    ok = all(r[1] for r in rows)
    print("INPUT CONTRACT %s%s" % ("HELD" if ok else "NOT HELD", " BY PYTHON AND THE BROWSER" if path and ok else ""))
    return 0 if ok else 1


# ------------------------------------------------------------------------------------------------ the self-test
def cmd_selftest(path):
    import copy
    T = load_trace(path)
    rows = []
    world = check_trace(T, rows)

    def found(label, ok, detail):
        rows.append((label, ok, detail))

    base = []
    total, bad = verify(T, world, base)
    found("the trace verifies", bad == 0 and all(r[1] for r in base), "%d ticks of %d runs" % (total, len(T["rules"]["1"]["runs"])))
    # the specification's numbers are sim.js's (its P, as art/check.py reads it)
    src = open(os.path.join(HERE, "web", "sim.js"), encoding="utf-8").read()
    m = re.search(r"const P = \{([^}]*)\}", src)
    declared = dict((k, float(v)) for k, v in re.findall(r"(\w+): ([0-9.]+)", m.group(1))) if m else {}
    mine = {"radius": K.radius, "eye": K.eye, "step": K.step, "speed": K.speed, "gravity": K.gravity, "jump": K.jump,
            "fireCooldown": K.fire_cooldown, "targetRadius": K.target_radius, "targetHeight": K.target_height,
            "targetDown": K.target_down, "range": K.ray_range}
    found("the constants are sim.js's", declared == mine, "%d numbers, each as sim.js declares it" % len(mine))
    runs = {r["name"]: r for r in T["rules"]["1"]["runs"]}
    stress = runs.get("the stress")
    walk = T["rules"]["1"]["runs"][0]

    # plants in the trace: the comparison names the tick and the field
    if stress and len(stress["snaps"]) > 1200:
        B = copy.deepcopy(stress)
        d = json.loads(B["snaps"][999])
        h = d["x"][1:]
        d["x"] = "f" + h[:-1] + "%x" % (int(h[-1], 16) ^ 1)
        B["snaps"][999] = json.dumps(d, separators=(",", ":"))
        r = play(world, B)
        found("plant: the browser's x one bit off at tick 1000", r is not None and r.get("tick") == 1000 and [f[0] for f in r.get("fields", [])] == ["x"],
              "found at tick %s, in %s" % (r and r.get("tick"), r and [f[0] for f in r.get("fields", [])]))
    if len(walk["inputs"]) > 400:
        B = copy.deepcopy(walk)
        inp = read_input(B["inputs"][299])
        inp["dyaw"] = inp.get("dyaw", 0.0) + 0.25
        B["inputs"][299] = write_input(inp)
        r = play(world, B)
        found("plant: one input of the walk turned a quarter radian more at tick 300", r is not None and r.get("tick") == 300,
              "found at tick %s, in %s" % (r and r.get("tick"), r and [f[0] for f in r.get("fields", [])]))
    # plants in this implementation: a defect here must show as a difference from the browser's states
    for label, name, mutant in MUTANTS:
        g = globals()
        saved = g[name] if name in g else None
        saved_cells, saved_stand = World.cells_near, K.stand_again
        try:
            if name == "cells_near":
                World.cells_near = mutant
            elif name == "K.stand_again":
                K.stand_again = mutant
            else:
                g[name] = mutant
            where = None
            for run in T["rules"]["1"]["runs"]:
                r = play(world, run)
                if r is not None:
                    where = "%s, tick %d" % (run["name"], r["tick"])
                    break
            found("plant in the reference: " + label, where is not None, ("found: " + where) if where else "NOT found: every run the same")
        finally:
            if saved is not None:
                g[name] = saved
            World.cells_near, K.stand_again = saved_cells, saved_stand
    for name, ok, detail in rows:
        print("%s %s — %s" % ("PASS" if ok else "FAIL", name, detail))
    ok = all(r[1] for r in rows)
    print("TICK-REF SELFTEST %s" % ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


# the plants in the reference (each a defect a second implementation could have)
def _fall_wrong_order(world, s, inp):
    was = s.on_ground
    if truthy(inp.get("jump")) and s.on_ground:
        s.vy, s.on_ground = K.jump, False
    s.feet = s.feet + s.vy * TICK
    s.vy = s.vy - K.gravity * TICK
    land(world, s, was)


def _move_five(world, s, dx, dz):
    if not is_blocked(world, s, s.x + dx, s.z + dz, s.feet):
        s.x, s.z = s.x + dx, s.z + dz
        return
    for _ in range(5):
        dx, dz = dx / 2.0, dz / 2.0
        if not is_blocked(world, s, s.x + dx, s.z + dz, s.feet):
            s.x, s.z = s.x + dx, s.z + dz


def _shoot_sign(world, s):
    s.shots = s.shots + 1.0
    cp = cos(s.pitch)
    d = (cp * sin(s.yaw), sin(s.pitch), cp * cos(s.yaw))
    o = (s.x, s.feet + K.eye, s.z)
    best, best_t = None, wall_distance(world, o[0], o[1], o[2], d[0], d[1], d[2], K.ray_range)
    r = K.target_radius
    for t in s.targets:
        if t.up:
            tt = box_entry(o, d, (t.x - r, t.y, t.z - r), (t.x + r, t.y + K.target_height, t.z + r))
            if tt < best_t:
                best, best_t = t, tt
    if best is not None:
        best.up, best.down_for = False, K.target_down
        s.score = s.score + 1.0


def _cells_from_centre(self, x, z, r):
    c = self.cell
    i = floor(x / c)
    while i <= floor((x + r) / c):
        j = floor(z / c)
        while j <= floor((z + r) / c):
            px = js_max(i * c, js_min(x, (i + 1) * c))
            pz = js_max(j * c, js_min(z, (j + 1) * c))
            dx, dz = x - px, z - pz
            if dx * dx + dz * dz < r * r:
                yield i, j
            j += 1
        i += 1


def _sin_short(x):
    """The sine with its kernel's polynomial cut after x^5: a defect large enough to reach every run's state. (A defect
    of one place in the last bit can be absorbed by a run, as the plain root of the sum for hypot, or a reduction
    without its tail, are on the witness level's runs; that is why rules_ref.py holds the arithmetic itself, result by
    result, and this file holds the tick.)"""
    def k_sin(r):
        z = r * r
        return r + r * z * (arith.S1 + z * arith.S2)
    if abs(x) <= PI / 4:
        return k_sin(x)
    n, a, b = arith.rem_pio2(x)
    return (k_sin(a), arith.k_cos(a, b), -k_sin(a), -arith.k_cos(a, b))[n & 3]


MUTANTS = [
    ("the height's two updates in the wrong order", "fall", _fall_wrong_order),
    ("the halving five times, not six", "move", _move_five),
    ("the shot's direction with cos(yaw) of the wrong sign", "shoot", _shoot_sign),
    ("a target standing again at downFor <= 0", "K.stand_again", 0.0),
    ("the sine's polynomial cut after x^5", "sin", _sin_short),
    ("the cells scanned from the centre, not from x - r and z - r", "cells_near", _cells_from_centre),
]


# ------------------------------------------------------------------------------------------------ rules 2's cases
RULES2_CASES = os.path.join(HERE, "web", "rules2_cases.json")
SET2 = {"feet": "feet", "onGround": "on_ground", "pitch": "pitch", "vy": "vy", "x": "x", "yaw": "yaw", "z": "z"}


def play2(conv, case):
    """A case of rules 2's table played here: its identity, start, every tick's snapshot and hash; or why the world
    was refused."""
    r = {"name": case["name"]}
    try:
        world = World2(conv, case.get("movers") or [])
    except MoverRefused as e:
        r["refused"] = str(e)
        return r
    s = State2.new(world, (case.get("start") or {}).get("side", "A"))
    for k, v in sorted(((case.get("start") or {}).get("set") or {}).items()):
        setattr(s, SET2[k], v if isinstance(v, bool) else float(v))
    r.update(identity="%016x" % world.identity_state, start=write_snapshot2(s), snaps=[], hashes=[])
    inside = 0
    for seg in case.get("inputs") or []:
        for inp in (stress_inputs(seg["stress"]) if seg.get("stress") else [dict(seg.get("in") or {}) for _ in range(seg["n"])]):
            tick2(world, s, inp)
            r["snaps"].append(write_snapshot2(s))
            r["hashes"].append(hash2(world, s))
            # the invariant stop and blocked give: the body never ends a tick inside a box, but standing on its top
            if any(plan_over(s.x, s.z, b) and b[4] > s.feet and b[1] < s.feet + BODY for b in poses(world, s)):
                inside += 1
    r["inside"] = inside
    return r


def play1_like(conv, case):
    """The same start and inputs under rules 1, for the case of no movers: every snapshot."""
    world = World(conv)
    s = State.new(world, (case.get("start") or {}).get("side", "A"))
    for k, v in sorted(((case.get("start") or {}).get("set") or {}).items()):
        setattr(s, SET2[k], v if isinstance(v, bool) else float(v))
    out = []
    for seg in case.get("inputs") or []:
        for _ in range(seg["n"]):
            tick(world, s, dict(seg.get("in") or {}))
            out.append(write_snapshot(s))
    return out


def expect_faults(case, r):
    """Where a played case parts from the values worked by hand (its 'expect', its 'expect_refused')."""
    out = []
    want = case.get("expect_refused")
    if want is not None:
        got = r.get("refused")
        if want is False and got:
            out.append("refused (%s), and the working admits it" % got[:80])
        elif want and not (got or "").startswith(want):
            out.append("not refused %s (%s)" % (want, (got or "admitted")[:80]))
        return out
    if r.get("refused"):
        return ["refused: %s" % r["refused"][:100]]
    for e in case.get("expect") or []:
        t = e["tick"]
        if t > len(r["snaps"]):
            out.append("no tick %d" % t)
            continue
        d = json.loads(r["snaps"][t - 1])
        for k, v in e.items():
            if k == "tick":
                continue
            if k == "movers":
                got = [{"phase": _dec(m["phase"]), "stopped": m["stopped"]} for m in d["movers"]]
                wantm = [{"phase": float(m["phase"]), "stopped": m["stopped"]} for m in v]
                if got != wantm:
                    out.append("tick %d: movers %s, worked %s" % (t, got, wantm))
            else:
                gv = _dec(d[k])
                wv = v if isinstance(v, bool) else float(v)
                if type(gv) is not type(wv) or gv != wv:
                    out.append("tick %d: %s %r, worked %r" % (t, k, gv, wv))
    return out


def run_table2(conv, table):
    """Every case played here, with its faults against the working, and the case of no movers against rules 1."""
    rows, mine = [], {}
    for case in table["cases"]:
        r = play2(conv, case)
        mine[case["name"]] = r
        faults = expect_faults(case, r)
        if case.get("invariant") == "never inside" and r.get("inside"):
            faults.append("%d tick(s) ended with the body inside a box" % r["inside"])
        if case.get("rules1_equal") and not r.get("refused"):
            ones = play1_like(conv, case)
            strip = lambda t: t.replace('"movers":[],', "", 1)
            bad = [n + 1 for n, (a, b) in enumerate(zip(ones, r["snaps"])) if a != strip(b)]
            if bad or len(ones) != len(r["snaps"]):
                faults.append("parts from rules 1 at tick %s" % (bad[:1] or ["count"])[0])
            else:
                faults = faults or []
                case = dict(case, _rules1="every one of %d ticks the same bytes as rules 1's, but for the empty movers" % len(ones))
        rows.append((case["name"], not faults, "; ".join(faults)[:240] if faults else (case.get("_rules1") or (
            "refused as worked: %s" % r["refused"][:70] if r.get("refused") else ("%d ticks; no tick ended with the body inside a box" % len(r["snaps"])
                                                                                 if case.get("invariant") else "%d ticks; every value worked by hand held" % len(r.get("snaps", [])))))))
    return rows, mine


def _plant(name):
    """A mutant of this file's rules 2, by name, for rules2's own check that the worked values bite: returns undo."""
    g = globals()
    saved = {k: g[k] for k in ("movers2", "height2", "Mover", "PHASES2")}

    def undo():
        g.update(saved)
    if name == "no carry":
        def m2(world, s, inp):
            on = s.on_ground
            s.on_ground = False                 # no rider is ever seen
            saved["movers2"](world, s, inp)
            s.on_ground = on
        g["movers2"] = m2
    elif name == "wrap at more than 2 len":
        def m2(world, s, inp):
            for k, m in enumerate(world.movers):
                st = s.movers[k]
                n = st.phase + m.speed
                if n > 2.0 * m.length:
                    n = n - 2.0 * m.length
                st.phase, st.stopped = n, False
        g["movers2"] = m2
    elif name == "no stop":
        def m2(world, s, inp):
            for k, m in enumerate(world.movers):
                st = s.movers[k]
                if m.speed == 0:
                    continue
                n = st.phase + m.speed
                if n >= 2.0 * m.length:
                    n = n - 2.0 * m.length
                st.phase, st.stopped = n, False
        g["movers2"] = m2
    elif name == "no ceiling":
        def h2(world, s, inp):
            was, before = s.on_ground, s.feet
            if truthy(inp.get("jump")) and s.on_ground:
                s.vy, s.on_ground = K.jump, False
            s.vy = s.vy - K.gravity * TICK
            s.feet = s.feet + s.vy * TICK
            g_ = world.ground(s.x, s.z)
            for b in poses(world, s):
                if plan_over(s.x, s.z, b) and b[4] <= before + K.step and b[4] > g_:
                    g_ = b[4]
            if s.feet <= g_ or (was and s.vy <= 0 and s.feet - g_ <= K.step):
                s.feet, s.vy, s.on_ground = g_, 0.0, True
            else:
                s.on_ground = False
        g["height2"] = h2
    elif name == "no tunnelling bound":
        class M(saved["Mover"]):
            def __init__(self, d, ids):
                d = dict(d)
                sp = d.get("speed")
                d["speed"] = 0
                saved["Mover"].__init__(self, d, ids)
                self.speed = float(sp)
        g["Mover"] = M
    g["PHASES2"] = (respawn2, g["movers2"], aim2, walk2, g["height2"], weapon, stand_again, objective)
    return undo


PLANTS2 = ("no carry", "wrap at more than 2 len", "no stop", "no ceiling", "no tunnelling bound")


def cmd_rules2(path=None):
    with open(RULES2_CASES, encoding="utf-8") as fh:
        table = json.load(fh)
    conv = level.convert(table["map"])
    print("RULES2  %s  map %s  rules 2 (RULES-2.md), %d cases" % (os.path.relpath(RULES2_CASES), table["map"], len(table["cases"])))
    rows, mine = run_table2(conv, table)
    for name, ok, detail in rows:
        print("%s %s — %s" % ("PASS" if ok else "FAIL", name, detail))
    caught = 0
    for p in PLANTS2:
        undo = _plant(p)
        try:
            prow, _m = run_table2(conv, table)
        finally:
            undo()
        bit = [n for n, ok, _d in prow if not ok]
        caught += 1 if bit else 0
        print("%s plant: %s — %s" % ("PASS" if bit else "FAIL", p, ("caught by " + ", ".join(b.split(" ")[0] for b in bit)) if bit else "NOT caught by any worked value"))
    ok = all(r[1] for r in rows) and caught == len(PLANTS2)
    engine_ok = True
    if path:
        with open(path, encoding="utf-8") as fh:
            R = json.load(fh)
        theirs = {r["name"]: r for r in R.get("results", [])}
        eng = (R.get("runtime") or {}).get("userAgent", "?")
        print("held to the results of %s (%s)" % (os.path.basename(path), eng[:90]))
        for case in table["cases"]:
            t, m = theirs.get(case["name"]), mine[case["name"]]
            if t is None:
                print("FAIL %s — not in the results" % case["name"])
                engine_ok = False
                continue
            faults = expect_faults(case, t)
            if bool(t.get("refused")) != bool(m.get("refused")):
                faults.append("refused there %r, here %r" % (t.get("refused"), m.get("refused")))
            elif not m.get("refused"):
                if t.get("identity") != m["identity"]:
                    faults.append("identity there %s, here %s" % (t.get("identity"), m["identity"]))
                if t.get("start") != m["start"]:
                    faults.append("the start differs")
                for n, (a, b) in enumerate(zip(m["snaps"], t.get("snaps", []))):
                    if a != b:
                        fa, fb = fields_of(a), fields_of(b)
                        diff = [k for k in sorted(set(fa) | set(fb)) if fa.get(k) != fb.get(k)]
                        faults.append("FIRST DIFFERENT at tick %d: %s" % (n + 1, ", ".join(diff[:5])))
                        break
                hb = [n + 1 for n, (a, b) in enumerate(zip(m["hashes"], t.get("hashes", []))) if a != b]
                if hb:
                    faults.append("hash first different at tick %d (here %s, there %s)" % (hb[0], m["hashes"][hb[0] - 1], t["hashes"][hb[0] - 1]))
                if len(t.get("snaps", [])) != len(m["snaps"]):
                    faults.append("%d ticks there, %d here" % (len(t.get("snaps", [])), len(m["snaps"])))
            engine_ok = engine_ok and not faults
            print("%s %s — %s" % ("PASS" if not faults else "FAIL", case["name"], "; ".join(faults)[:240] if faults else (
                "refused there as here" if m.get("refused") else "%d ticks: every snapshot and hash the same, identity %s" % (len(m["snaps"]), m["identity"]))))
    held = ok and engine_ok
    print("RULES 2 %s%s" % ("HELD BY PYTHON" if ok else "NOT HELD", (" AND THE ENGINE" if engine_ok else "; THE ENGINE PARTS") if path else ""))
    return 0 if held else 1


MAKES = {"verify": "python graybox/trace.py run tactical --browser msedge", "selftest": "python graybox/trace.py run tactical --browser msedge",
         "cases": "python graybox/trace.py run tactical --cases --browser msedge", "rules2": "python graybox/trace.py run tactical --rules2 --browser msedge"}


def main(argv):
    # a results file named and not there is said before anything is played (0226: his run of 0225 met a traceback,
    # the table played first, when the browser's run had not been made yet)
    if len(argv) == 2 and argv[0] in MAKES and not os.path.isfile(argv[1]):
        print("TICK-REF: there is no file %s: a browser writes it, so run first:  %s" % (argv[1], MAKES[argv[0]]), file=sys.stderr)
        return 2
    if len(argv) in (1, 2) and argv[0] == "rules2":
        return cmd_rules2(argv[1] if len(argv) == 2 else None)
    if len(argv) == 2 and argv[0] == "verify":
        return cmd_verify(argv[1])
    if len(argv) == 2 and argv[0] == "selftest":
        return cmd_selftest(argv[1])
    if len(argv) in (1, 2) and argv[0] == "cases":
        return cmd_cases(argv[1] if len(argv) == 2 else None)
    print("usage: python graybox/tick_ref.py verify TRACE.json | selftest TRACE.json | cases [RESULTS.json] | rules2 [RESULTS.json]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
