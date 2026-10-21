# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# graybox/tick_ref.py — a second implementation of the graybox's tick (rules 1, graybox/RULES-1.md), in Python, and
# the verifier of what a browser played.
#
#   python graybox/tick_ref.py verify TRACE.json
#   python graybox/tick_ref.py selftest TRACE.json
#   python graybox/tick_ref.py doortest TRACE.json
#   python graybox/tick_ref.py cases [RESULTS.json]
#   python graybox/tick_ref.py rules2 [RESULTS.json]
#   python graybox/tick_ref.py rules3 [RESULTS.json]
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
# differ. Before it plays, the door (VERIFY-DOOR-0, below): the runs must be the ones sim.js's makeRuns makes for the
# map, in its order and each once, and each run's start and inputs the ones made here from the map alone (the walk by
# graybox/bot_ref.py, the fight by a reading of lines() and makeRuns, the stress run from integers), as many snapshots
# as inputs, every number finite; each refusal a FAIL row with its own code, and the verdict FAILED. It trusts nothing
# the browser computed, nor which runs it chose to send. `selftest` plants defects in a copy of the trace and in this
# implementation, and requires each to be found where it was planted. `doortest` makes the attacks that the verifier
# accepted before the door from a trace of the browser's own runs, requires each refused by its own code, plants
# defects in the door's reading of the fight, and switches the door off to show that the door is what refuses them.
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
# Rules 3 (graybox/RULES-3.md, 0228): rules 2 with solid walls, targets with a top, a target that waits for a clear
# column, and a mover's policy push; written here from RULES-3.md as rules 2 were. `rules3` plays its table
# (web/rules3_cases.json) as `rules2` plays rules 2's.
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

    def __init__(self, d, ids, policies=("stop",)):
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
        if d.get("policy") not in policies:
            raise MoverRefused("RULES2-MOVER: mover %r: its policy is not %s" % (mid, " or ".join(policies)))
        self.id, self.policy = mid, d["policy"]
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
    RULES = 2
    POLICIES = ("stop",)

    def __init__(self, conv, movers, origin=(0, 0)):
        World.__init__(self, conv)
        if not (isinstance(origin, (list, tuple)) and len(origin) == 2
                and all(isinstance(v, int) and not isinstance(v, bool) and -ORIGIN_MAX <= v <= ORIGIN_MAX for v in origin)):
            raise MoverRefused("ORT-ORIGIN: the origin is not two whole numbers of cells, each at most 2^20")
        self.oi, self.oj = int(origin[0]), int(origin[1])
        self.conv = conv
        ids = set()
        self.movers = []
        wall = self._wall(conv["canonical"])
        if wall is not None:   # rules 3 alone read it; a rules-2 world keeps the fields it had (ORT-1 declares each)
            self.wall = wall
        for d in movers:
            m = Mover(d, ids, self.POLICIES)
            ids.add(m.id)
            self.movers.append(m)
        C, W = conv["collision"], conv["canonical"]
        self.identity = identity_text(C, W, self.movers, (self.oi, self.oj), self.RULES, wall)
        self.identity_state = fnv64(FNV_OFFSET, self.identity.encode("utf-8"))

    def _wall(self, W):
        return None   # rules 2 do not read the wall's height


RULES3 = 3   # rules 3's version (RULES-3.md); art/check.py reads it from here, the handshake (0229)


class World3(World2):
    """A world of rules 3 (RULES-3.md): rules 2's, with the wall's height read, and push among the policies."""
    RULES = RULES3
    POLICIES = ("stop", "push")

    def _wall(self, W):
        v = W.get("wall")
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not (K.step < v < math.inf):
            raise MoverRefused("RULES3-WALL: the world's wall height is not a number above the step")
        return float(v)


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


def identity_text(C, W, movers, origin=(0, 0), rules=RULES2, wall=None):
    """RULES-2.md, *The state's hash*: the rules, every constant and the world, as one document; a rebased world's
    origin with it (ORT-1), and at the origin (0, 0) the document as rules 2 first wrote it. Rules 3 (RULES-3.md):
    their number, and the wall's height in the world."""
    doc = {
        "P": {"radius": K.radius, "eye": K.eye, "step": K.step, "speed": K.speed, "gravity": K.gravity, "jump": K.jump,
              "fireCooldown": K.fire_cooldown, "targetRadius": K.target_radius, "targetHeight": K.target_height,
              "targetDown": K.target_down, "range": K.ray_range, "height": BODY},
        "Q": Q, "TICK": TICK, "input": float(INPUT), "pitch": K.pitch_limit, "rules": float(rules), "stand": K.stand_again,
        "world": {"cell": float(C["cell"]), "h": float(C["h"]), "w": float(C["w"]), "tops": [float(t) for t in C["tops"]],
                  "movers": [[m.id, m.x0, m.y0, m.z0, m.x1, m.y1, m.z1, m.ax, m.ay, m.az, m.length, m.speed, m.policy] for m in movers],
                  "objective": list(W["objective"]["rect"]) if W.get("objective") else None,
                  "spawns": {k: [v["x"], v["z"], v["yaw"]] for k, v in W["spawns"].items()},
                  "targets": [[t["id"], t["x"], t["z"]] for t in W["targets"]]},
    }
    if origin[0] != 0 or origin[1] != 0:
        doc["world"]["origin"] = [float(origin[0]), float(origin[1])]
    if rules >= 3:
        doc["world"]["wall"] = wall
    return "VERDANDI-RULES %d\n" % rules + json.dumps(_idenc(doc), separators=(",", ":"), sort_keys=True, ensure_ascii=False)


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


# ------------------------------------------------------------------------------------------------ rules 3 (RULES-3.md)
def walled(world, x, z):
    """A cell as high as the wall's height under the circle: a wall, at any height."""
    return any(world.top(i, j) >= world.wall for i, j in world.cells_near(x, z, K.radius))


def in_column(t, x, z, feet):
    rr = K.radius + K.target_radius
    dx, dz = x - t.x, z - t.z
    return dx * dx + dz * dz < rr * rr and feet < t.y + K.target_height


def is_blocked3(world, s, x, z, feet, k=None, bk=None):
    return walled(world, x, z) or is_blocked2(world, s, x, z, feet, k, bk)


def move3(world, s, dx, dz):
    if not is_blocked3(world, s, s.x + dx, s.z + dz, s.feet):
        s.x, s.z = s.x + dx, s.z + dz
        return
    for _ in range(6):
        dx, dz = dx / 2.0, dz / 2.0
        if not is_blocked3(world, s, s.x + dx, s.z + dz, s.feet):
            s.x, s.z = s.x + dx, s.z + dz


def movers3(world, s, inp):
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
        if s.on_ground and s.feet == a[4] and plan_over(s.x, s.z, a):          # a rider: carried, or the mover stops
            nx, nz, nf = s.x + dx, s.z + dz, s.feet + dy
            if is_blocked3(world, s, nx, nz, nf, k, b):
                st.stopped = True
            else:
                st.phase, st.stopped = n, False
                s.x, s.z, s.feet = nx, nz, nf
        elif plan_over(s.x, s.z, b) and b[4] > s.feet and b[1] < s.feet + BODY:  # in its way
            if push(world, s, k, m, b, dx, dz):
                st.phase, st.stopped = n, False
            else:
                st.stopped = True
        else:
            st.phase, st.stopped = n, False


def push(world, s, k, m, b, dx, dz):
    """A player in mover k's way, it at b: policy push along x or z moves the player by its displacement, unless that
    place is blocked; anything else holds the mover still. True when the player was moved."""
    if m.policy != "push" or m.ay != 0:
        return False
    nx, nz = s.x + dx, s.z + dz
    if is_blocked3(world, s, nx, nz, s.feet, k, b):
        return False
    s.x, s.z = nx, nz
    return True


def walk3(world, s, inp):
    fwd = (1.0 if truthy(inp.get("f")) else 0.0) - (1.0 if truthy(inp.get("b")) else 0.0)
    side = (1.0 if truthy(inp.get("r")) else 0.0) - (1.0 if truthy(inp.get("l")) else 0.0)
    sy, cy = sin(s.yaw), cos(s.yaw)
    mx, mz = fwd * sy + side * cy, (-fwd) * cy + side * sy
    length = hypot(mx, mz)
    if length > 0:
        move3(world, s, mx / length * K.speed * TICK, 0.0)
        move3(world, s, 0.0, mz / length * K.speed * TICK)


def height3(world, s, inp):
    was, before = s.on_ground, s.feet
    if truthy(inp.get("jump")) and s.on_ground:
        s.vy, s.on_ground = K.jump, False
    s.vy = s.vy - K.gravity * TICK
    s.feet = s.feet + s.vy * TICK
    boxes = poses(world, s)
    c = min([b[1] for b in boxes if plan_over(s.x, s.z, b) and b[1] >= before + BODY] + [math.inf])
    if s.feet + BODY > c:
        s.feet = c - BODY
        if s.vy > 0:
            s.vy = 0.0
    tops = [world.ground(s.x, s.z)]
    tops += [b[4] for b in boxes if plan_over(s.x, s.z, b) and b[4] <= before + K.step]
    tops += target_tops(s, s.x, s.z, before)
    g = max(tops)
    if s.feet <= g or (was and s.vy <= 0 and s.feet - g <= K.step):
        s.feet, s.vy, s.on_ground = g, 0.0, True
    else:
        s.on_ground = False


def target_tops(s, x, z, before):
    """The tops of the standing targets whose columns the body is in, as high as a step above before."""
    rr = K.radius + K.target_radius
    return [t.y + K.target_height for t in s.targets
            if t.up and (x - t.x) * (x - t.x) + (z - t.z) * (z - t.z) < rr * rr and t.y + K.target_height <= before + K.step]


def stand_again3(world, s, inp):
    for t in s.targets:
        if not t.up:
            t.down_for = t.down_for - TICK
            if t.down_for <= K.stand_again:
                t.up = not in_column(t, s.x, s.z, s.feet)   # a body in its column: it waits
                t.down_for = 0.0


PHASES3 = (respawn2, movers3, aim2, walk3, height3, weapon, stand_again3, objective)


def tick3(world, s, inp):
    """One tick of rules 3 (RULES-3.md), on an input the contract admits."""
    a = admit(inp)
    if isinstance(a, str):
        raise InputRefused(a)
    s.tick = s.tick + 1.0
    for phase in PHASES3:
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
    ts = d.get("targets")
    listed = isinstance(ts, list) and all(isinstance(t, dict) for t in ts)   # else "targets" is a field like any other
    out = {k: v for k, v in d.items() if k != "targets" or not listed}
    for n, t in enumerate(ts if listed else []):
        for k, v in t.items():
            out["targets[%d].%s" % (n, k)] = v
    return out


def show(v):
    d = as_double(v)
    return repr(d) if d is not None else json.dumps(v)


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
    with open(path, "rb") as fh:
        return parse_trace(fh.read(), path)


def parse_trace(data, path):
    """A trace's bytes read as VERDANDI-TRACE 1 with a rules-1 section, or SystemExit saying why not (never a traceback:
    JSON nested past the reader's depth is not JSON here)."""
    try:
        T = json.loads(data.decode("utf-8"))
    except (ValueError, RecursionError) as e:
        raise SystemExit("TICK-REF: %s is not a VERDANDI-TRACE 1 file: not JSON (%s: %s)" % (path, type(e).__name__, str(e)[:200]))
    if not isinstance(T, dict) or T.get("format") != "VERDANDI-TRACE" or T.get("version") != "1" \
            or not isinstance(T.get("rules"), dict) or "1" not in T["rules"]:
        raise SystemExit("TICK-REF: %s is not a VERDANDI-TRACE 1 file with a rules-1 section" % path)
    return T


def check_trace(T, out):
    """The map the trace names, converted here and held to the trace's manifest (the row VERIFY-MAP); the world, or None
    when the map cannot be converted here (the row then a FAIL)."""
    name = T.get("map", "")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9_-]+", name):
        raise SystemExit("TICK-REF: the trace names no map")
    try:
        conv = level.convert(name)
    except (OSError, ValueError, KeyError, level.MapError) as e:
        why = "%s of %s" % (e.strerror, os.path.basename(e.filename or "")) if isinstance(e, OSError) else str(e)[:200]
        out.append(("VERIFY-MAP the map", False, "%s cannot be converted here (%s: %s): nothing of the trace can be held to it" % (
            name, type(e).__name__, why)))
        return None
    mine, theirs = conv["manifest"], T.get("manifest") if isinstance(T.get("manifest"), dict) else {}
    same = all(mine.get(k) == theirs.get(k) for k in ("canonical_sha256", "collision_sha256"))
    out.append(("VERIFY-MAP the map", same, "%s converted here: canonical %s, collision %s%s" % (
        name, mine["canonical_sha256"][:12], mine["collision_sha256"][:12], "" if same else "; the trace's are %s, %s" % (
            str(theirs.get("canonical_sha256"))[:12], str(theirs.get("collision_sha256"))[:12]))))
    return World(conv)


# ------------------------------------------------------------------------------------------------ the door (VERIFY-DOOR-0)
# What a trace must be before its snapshots are worth comparing. Before the door, `verify` played whatever runs a trace
# held and checked only that each start read back to its own bytes, so that a trace of no runs, a run cut short, the
# stress run renamed, or a start forged (its snapshots made by this very tick) was VERIFIED (MEASURED, 2026-10-19). Now
# the host makes every run the browser was to play, from the map alone, and refuses, each with its own code and in this
# order, whatever is not what it made:
#
#   VERIFY-MAP        the map named cannot be converted here, or, converted here, is not the one the trace's manifest
#                     names (its canonical and collision digests)
#   VERIFY-FORM       the rules-1 section is not exactly {calls, runs}, its calls a list and its runs a list of exactly
#                     {name, start, inputs, snaps}, a name and a start that are strings and inputs and snapshots that
#                     are lists of strings, every start and snapshot a JSON object and every input a list of [field,
#                     value] pairs, none nested deeper than the writing's (3 and 2) nor past the JSON reader's depth,
#                     a start's or snapshot's targets, when present, a list of JSON objects, and no value a string of
#                     17 characters that begins "f" and is not a number of the writing ("f" and 16 hex digits: the
#                     readers would take it for one and could not read it); or inputs_from is neither absent nor
#                     exactly {engine, inputs}, two strings. No row follows it
#   VERIFY-NO-RUNS    the trace holds no run under rules 1
#   VERIFY-RUN-SET    the runs' names are not, in order and each once, the runs sim.js's makeRuns makes for the map:
#                     "the walk" if the bot walks a route of it (made here by graybox/bot_ref.py, walk-1), "the fight"
#                     if lines() finds an open line to a target (read here, `fight_line`), and "the stress" always. A
#                     trace given the Python walk (inputs_from.engine "bot-ref-walk-1": trace.py --inputs BOT.json)
#                     holds the walk alone; one given another trace's runs holds makeRuns' set, or the walk alone
#   VERIFY-GIVEN      inputs_from names inputs other than the sha256 of the runs the trace holds, as trace.py names them
#   VERIFY-NONFINITE  a number in a start, an input or a snapshot is not finite, as the readers read it (`as_double`: the
#                     hex in either case), or a bare JSON NaN or Infinity
#   VERIFY-START      a run's start is not, byte for byte, the start made here
#   VERIFY-LENGTH     a run's inputs are not as many as the host makes for it, or its snapshots not as many as its inputs
#   VERIFY-INPUTS     a run's inputs are not, byte for byte, the inputs made here
#   VERIFY-PLAY       a run is played only when its name, start and inputs are the ones made here (any other: FAIL, not
#                     played: the tick is never given a start or an input the trace made, so that an infinite or very
#                     large start, which never ends in cells_near, is refused by its rows and printed); then a snapshot
#                     that is not the Python tick's (the comparison itself, as before the door), or a run that cannot be
#                     played (an input the contract refuses, a run that cannot be read), a FAIL row where before the door
#                     it was a traceback
#
# The verdict is VERIFIED only when every row passes. The starts and inputs are made by this file and bot_ref.py, never
# read from the trace. The fight is a reading of sim.js's lines() and makeRuns by one author (written for the door):
# it is held by the browsers' own fight starts on tactical (a recorded trace refuses a reading that makes another start
# there, at VERIFY-START, or none, at VERIFY-RUN-SET; a wrong reading that makes the same start, as a two-argument hypot
# does on tactical and on witness, is not refused: agreement, not truth, G23; no browser's runs of witness have been
# compared through the door, NOT_MEASURED) and by plants in `doortest` that change the reading and must make a
# recorded trace refuse (each run only on a map where it changes the fight). Not held, because nothing of rules 1's
# numbers rests on them: the runtime (the engine a trace names is the page's own report), inputs_from's engine but for
# the Python walk's name, the rules-1 calls but for being a list (the engine's Math called under rules 1, as the page
# recorded it: trace.py compares them), the rules-0 section, the manifest but for its two digests, and the file's other
# keys. A trace that cannot be read (not JSON, or nested past the reader's depth) is refused before the door.
DOOR = True   # switched off only by doortest's harness plant, to show that the attacks are refused because of it
RUN_ORDER = ("the walk", "the fight", "the stress")
STRESS_TICKS = 3600   # makeRuns: stressInputs(3600)
AIM = 1.2             # lines() and makeRuns: the target's point aimed at, metres above its foot
_WALKS = {}


def made_walk(name):
    """The walk, as bot_ref.py makes it from the map (WALK-1.md): (start, inputs), or None when no route walks."""
    if name not in _WALKS:
        import bot_ref   # here, not above: bot_ref.py imports this file
        try:
            W, _tried = bot_ref.make(name)
            _WALKS[name] = (W["runs"][0]["start"], list(W["runs"][0]["inputs"]))
        except bot_ref.BotTraceError as e:
            if e.code != "BOT-REF-NO-WALK":
                raise
            _WALKS[name] = None
    return _WALKS[name]


def given_walk_engine():
    import bot_ref
    return bot_ref.GIVEN


def fight_line(world, aim=AIM, rows_first=True):
    """sim.js's lines(world).shot: for each target of a new state at spawn A in order, the floor cells row by row (j,
    then i), the first 4 to 30 m from it whose line from the eye to the target's point AIM above its foot no wall stops.
    (target, x, z) or None. aim and rows_first are for doortest's plants alone. Equivalent mutants, MEASURED 2026-10-20:
    on tactical every aim from about 0.52 m to 5.02 m finds the same cell (T1, 11.0, 17.0), so a plant of the aim inside
    that range shows nothing there (0.5 m finds (T1, 5.0, 19.0), about 0.018 m below that bound: it refuses only in
    this map's state); on witness the cells searched column by column find the same cell as row by row (T1, 63.0,
    53.0), so that plant is not run there (doortest says so); and the line's length by a hypot of two arguments and not
    three finds the same cell on tactical and on witness, an equivalent mutant on both, not kept as a plant."""
    c = world.cell
    s0 = State.new(world, "A")
    if rows_first:
        order = [(i, j) for j in range(world.h) for i in range(world.w)]
    else:
        order = [(i, j) for i in range(world.w) for j in range(world.h)]
    for t in s0.targets:
        for i, j in order:
            if world.top(i, j) != 0:
                continue
            x, z = (i + 0.5) * c, (j + 0.5) * c
            dist = hypot(t.x - x, t.z - z)
            if dist < 4 or dist > 30:
                continue
            oy, ty = K.eye, t.y + aim
            dx, dz, dy = t.x - x, t.z - z, ty - oy
            L = arith.xhypot(dx, dy, dz)
            if wall_distance(world, x, oy, z, dx / L, dy / L, dz / L, K.ray_range) > L:
                return t, x, z
    return None


def made_fight(world, pitch_aim=AIM, **plant):
    """makeRuns' fight: its start from the line above, with rules 1's hypot and atan2, and its scripted inputs.
    pitch_aim (the point makeRuns' pitch aims at) and plant (fight_line's) are for doortest's plants alone."""
    shot = fight_line(world, **plant)
    if shot is None:
        return None
    t, x, z = shot
    s = State.new(world, "A")
    s.x, s.z = x, z
    s.feet = world.ground(x, z)
    tgt = [q for q in s.targets if q.id == t.id][0]
    dx, dz = tgt.x - s.x, tgt.z - s.z
    s.yaw = math.fmod(math.fmod(arith.xatan2(dx, -dz), TWO_PI) + TWO_PI, TWO_PI)
    s.pitch = arith.xatan2(tgt.y + pitch_aim - (s.feet + K.eye), hypot(dx, dz))
    out = []

    def add(n, inp):
        for k in range(n):
            out.append(inp(k) if callable(inp) else dict(inp))
    add(1, {"fire": True})
    add(20, {})
    add(1, {"fire": True})
    add(1, {"jump": True})
    add(8, {})
    add(1, {"fire": True, "dyaw": 0.02})
    add(60, lambda k: {"f": True, "dyaw": 0.01, "dpitch": -0.002, "fire": k % 25 == 0})
    add(math.ceil(K.target_down / TICK) + 10, {})
    add(1, {"side": "B"})
    add(30, {"f": True, "r": True})
    add(1, {"fire": True})
    add(1, {"reset": True})
    add(1, {"side": "A"})
    add(40, lambda k: {"b": True, "l": True, "jump": k % 15 == 0})
    return write_snapshot(s), [write_input(i) for i in out]


def made_runs(T, world):
    """Every run the host makes for the trace's map: {name: (start, inputs)}."""
    made = {}
    w = made_walk(T["map"])
    if w is not None:
        made["the walk"] = w
    f = globals()["made_fight"](world)   # by name, so that doortest's plants of the reading reach it
    if f is not None:
        made["the fight"] = f
    made["the stress"] = (write_snapshot(State.new(world, "A")), [write_input(i) for i in stress_inputs(STRESS_TICKS)])
    return made


def depth(v):
    """How deep v nests (a scalar 0, [] or {} 1), counted without recursion so that no depth of a trace's JSON ends in a
    traceback here."""
    deepest, stack = 0, [(v, 1)]
    while stack:
        x, d = stack.pop()
        if isinstance(x, (dict, list)):
            deepest = max(deepest, d)
            stack.extend((y, d + 1) for y in (x.values() if isinstance(x, dict) else x))
    return deepest


DEPTH = {dict: 3, list: 2}   # a start or snapshot: {.., "targets": [{..}]}; an input: [[field, value], ..]


def form_faults(T):
    sec = T["rules"]["1"]
    if not isinstance(sec, dict) or not isinstance(sec.get("runs"), list):
        return ["the rules-1 section holds no list of runs"]
    if set(sec) != {"calls", "runs"} or not isinstance(sec["calls"], list):
        return ["the rules-1 section is not exactly {calls, runs} with its calls a list (it holds %s)" % ", ".join(sorted(map(str, sec)))]
    src = T.get("inputs_from")
    if src is not None and not (isinstance(src, dict) and set(src) == {"engine", "inputs"} and all(isinstance(v, str) for v in src.values())):
        return ["inputs_from is not {engine, inputs}, two strings"]
    for n, run in enumerate(sec["runs"]):
        where = "run %d" % (n + 1)
        if not isinstance(run, dict) or set(run) != {"name", "start", "inputs", "snaps"}:
            return ["%s is not {name, start, inputs, snaps}" % where]
        if not (isinstance(run["name"], str) and isinstance(run["start"], str) and isinstance(run["inputs"], list) and isinstance(run["snaps"], list)):
            return ["%s: its name and start are not strings, or its inputs and snapshots not lists" % where]
        texts = [("its start", run["start"], dict)] + [("input %d" % (k + 1), v, list) for k, v in enumerate(run["inputs"])] \
            + [("snapshot %d" % (k + 1), v, dict) for k, v in enumerate(run["snaps"])]
        for what, text, kind in texts:
            try:
                v = json.loads(text) if isinstance(text, str) else None
            except (ValueError, RecursionError):
                v = None
            if not isinstance(v, kind) or (kind is list and not all(isinstance(p, list) and len(p) == 2 and isinstance(p[0], str) for p in v)):
                return ["%s (%s), %s, is not %s" % (where, run["name"], what, "a JSON object" if kind is dict else "a list of [field, value] pairs")]
            if depth(v) > DEPTH[kind]:
                return ["%s (%s), %s, nests %d deep, deeper than any %s of the trace's writing (%d)" % (
                    where, run["name"], what, depth(v), "start or snapshot" if kind is dict else "input", DEPTH[kind])]
            ts = v.get("targets") if kind is dict else None
            if kind is dict and "targets" in v and not (isinstance(ts, list) and all(isinstance(t, dict) for t in ts)):
                return ["%s (%s), %s, holds targets that are not a list of JSON objects (it holds %s)" % (
                    where, run["name"], what, json.dumps(ts)[:80])]
            bad = misread(v)
            if bad is not None:
                return ["%s (%s), %s, holds %s, which the readers take for a number and is not one (\"f\" and 16 hex "
                        "digits)" % (where, run["name"], what, json.dumps(bad))]
    return []


def misread(v):
    """The first string in v, walked without recursion in the order written, of 17 characters beginning "f" that is not a
    number of the trace's writing (`as_double` None): the readers (read_input, _dec, show) take such a string for a
    number and raise on it; or None."""
    stack = [v]
    while stack:
        x = stack.pop()
        if isinstance(x, str) and len(x) == 17 and x[:1] == "f" and as_double(x) is None:
            return x
        if isinstance(x, (dict, list)):
            stack.extend(reversed(list(x.values() if isinstance(x, dict) else x)))
    return None


def as_double(v):
    """v as this file's readers read a number of the trace's writing (read_input, _dec, show: a string of 17 characters,
    "f" and what bytes.fromhex makes 8 bytes of, upper case and lower), or None when it is not one: a string of that
    shape that is not one, on which the readers raise, VERIFY-FORM refuses (`misread`)."""
    if not (isinstance(v, str) and len(v) == 17 and v[:1] == "f"):
        return None
    try:
        return struct.unpack(">d", bytes.fromhex(v[1:]))[0]
    except (ValueError, struct.error):
        return None


def nonfinite(v):
    """A number anywhere in v that is not finite, as the readers read it (`as_double`: the trace's writing, in either
    case), or a bare JSON number (Python's json reads NaN, Infinity and -Infinity, which no engine's JSON writes); or
    None. Walked without recursion, in the order written."""
    stack = [v]
    while stack:
        x = stack.pop()
        if isinstance(x, float) and not math.isfinite(x):
            return repr(x)
        d = as_double(x)
        if d is not None and not math.isfinite(d):
            return x
        if isinstance(x, (dict, list)):
            stack.extend(reversed(list(x.values() if isinstance(x, dict) else x)))
    return None


def given_digest(runs):
    """trace.py's name for runs it gives a browser (and bot_ref.py's for a walk): the sha256 of their names, starts and
    inputs."""
    import hashlib
    return hashlib.sha256(json.dumps([{"name": r["name"], "start": r["start"], "inputs": r["inputs"]} for r in runs],
                                     sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def first_difference(mine, theirs):
    a, b = fields_of(mine), fields_of(theirs)
    return "; ".join("%s: here %s, the trace %s" % (k, show(a[k]) if k in a else "-", show(b[k]) if k in b else "-")
                     for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)) or SAME_FIELDS


SAME_FIELDS = "the same fields and values, in other bytes (an order, a key twice, a writing of their own)"


def ulp_note(a, b):
    """", N ulp" when a and b are both numbers of the trace's writing (`as_double`), else "": ulps reads only those."""
    return (", %d ulp" % ulps(a, b)) if as_double(a) is not None and as_double(b) is not None else ""


def played(world, run, rows):
    """VERIFY-PLAY: the run played here from its start with its inputs, each snapshot held to the trace's; ticks the
    same, or 0."""
    label = "VERIFY-PLAY run " + str(run["name"])
    try:
        r = play(world, run)
    except InputRefused as e:
        rows.append((label, False, "an input is refused by the input contract (%s): the run cannot be played" % e.category))
        return 0
    except (ValueError, KeyError, TypeError, AttributeError, IndexError, struct.error) as e:
        rows.append((label, False, "the run cannot be read: %s: %s" % (type(e).__name__, e)))
        return 0
    if r is None:
        rows.append((label, True, "%d ticks: every snapshot the same bytes as the browser's" % len(run["inputs"])))
        return len(run["inputs"])
    if "what" in r:
        rows.append((label, False, "at tick %d: %s" % (r["tick"], r["what"])))
    else:
        rows.append((label, False, "FIRST DIFFERENT at tick %d, in %s" % (r["tick"], "; ".join(
            "%s: here %s, the browser %s%s" % (k, show(a), show(b), ulp_note(a, b))
            for k, a, b in r["fields"][:6]) or SAME_FIELDS)))
    return 0


def verify(T, world, rows):
    """The door's rows in their order, then every run played and compared; (ticks played the same, rows failed)."""
    if not DOOR:
        return verify_without_door(T, world, rows)
    before = len(rows)

    def failed():
        return sum(1 for r in rows[before:] if not r[1])
    faults = form_faults(T)
    rows.append(("VERIFY-FORM the trace's form", not faults, (faults[0] + "; no row after this one is written: the door's "
                 "other rows read only a trace of this form") if faults else
                 "rules 1's {calls, runs}; runs of {name, start, inputs, snaps}; every start and snapshot a JSON object, every input a list of "
                 "[field, value] pairs, none nested deeper than the writing's"))
    if faults:
        return 0, failed()
    runs, src = T["rules"]["1"]["runs"], T.get("inputs_from")
    rows.append(("VERIFY-NO-RUNS a run at least", len(runs) > 0, "%d runs" % len(runs) if runs else "the trace holds no run under rules 1"))
    made = made_runs(T, world)
    own = [n for n in RUN_ORDER if n in made]
    if src is None:
        allowed, kind = [own], "the browser's own runs, makeRuns' for this map"
    elif src["engine"] == given_walk_engine():
        allowed, kind = ([["the walk"]] if "the walk" in made else []), "the Python walk, given (trace.py --inputs BOT.json): the walk alone"
    else:
        allowed = [own] + ([["the walk"]] if "the walk" in made and own != ["the walk"] else [])
        kind = "the runs of %s, given: makeRuns' for this map, or the walk alone" % src["engine"]
    names = [r["name"] for r in runs]
    ok = names in allowed
    rows.append(("VERIFY-RUN-SET the runs, in order, each once", ok, "%s; %s: %s%s" % (
        kind, "the trace's" if ok else "NOT the trace's, which are", ", ".join(names) or "none",
        "" if ok else "; made here: %s" % (" or ".join("[%s]" % ", ".join(a) for a in allowed) or "none"))))
    if src is None:
        rows.append(("VERIFY-GIVEN the runs' source", True, "none given: the browser made its own runs"))
    else:
        d = given_digest(runs)
        rows.append(("VERIFY-GIVEN the runs' source", src["inputs"] == d, "given the runs of %s, inputs %s: %s" % (
            src["engine"], src["inputs"][:16], "the sha256 of the runs it holds" if src["inputs"] == d else "NOT the sha256 of the runs it holds (%s)" % d[:16])))
    found = None
    for run in runs:
        for what, texts in (("its start", [run["start"]]), ("input", run["inputs"]), ("snapshot", run["snaps"])):
            for k, text in enumerate(texts):
                v = nonfinite(json.loads(text))
                if v is not None and found is None:
                    found = "%s: %s%s holds %s (%s)" % (run["name"], what, "" if what == "its start" else " %d" % (k + 1), v, show(v))
    rows.append(("VERIFY-NONFINITE every number finite", found is None, found or "every number of every start, input and snapshot"))
    mine = [r for r in runs if r["name"] in made]
    starts = [(r["name"], first_difference(made[r["name"]][0], r["start"])) for r in mine if r["start"] != made[r["name"]][0]]
    rows.append(("VERIFY-START each start made here", not starts, "; ".join("%s: NOT the start made here (%s)" % (n, d[:400]) for n, d in starts) if starts else
                 "%s: the same bytes as made here" % (", ".join(r["name"] for r in mine) or "no run")))
    lengths = [(r["name"], len(r["inputs"]), len(made[r["name"]][1]), len(r["snaps"])) for r in mine]
    short = [x for x in lengths if not x[1] == x[2] == x[3]]
    rows.append(("VERIFY-LENGTH each run's ticks", not short, "; ".join("%s: %d inputs and %d snapshots, NOT the %d made here" % (n, a, s, m) for n, a, m, s in short) if short else
                 ", ".join("%s %d" % (n, a) for n, a, _m, _s in lengths) or "no run"))
    differ = []
    for r in mine:
        theirs, ours = r["inputs"], made[r["name"]][1]
        k = next((k for k, (a, b) in enumerate(zip(theirs, ours)) if a != b), None)
        if k is not None:
            differ.append("%s: tick %d, the trace's %s, made here %s" % (r["name"], k + 1, theirs[k], ours[k]))
        elif len(theirs) != len(ours):
            differ.append("%s: the trace's first %d, of the %d made here" % (r["name"], len(theirs), len(ours)))
    rows.append(("VERIFY-INPUTS each run's inputs made here", not differ, "; ".join(differ) if differ else
                 "every input of %s the same bytes as made here" % (", ".join(r["name"] for r in mine) or "no run")))
    total = 0
    for run in runs:
        m = made.get(run["name"])
        if m is not None and run["start"] == m[0] and run["inputs"] == m[1]:
            total += played(world, run, rows)
        else:
            rows.append(("VERIFY-PLAY run " + run["name"], False, "not played: its %s (refused above); the tick is given only a "
                         "start and inputs made here" % ("name is not one made here" if m is None else "start is not the one made here"
                                                         if run["start"] != m[0] else "inputs are not the ones made here")))
    return total, failed()


def verify_without_door(T, world, rows):
    """The verifier's rows before the door (the runs played as they are; the stress run's start and inputs made again
    only if a run has its name), for doortest's harness plant alone. Each run is played through `played`, which writes a
    run that cannot be played as a FAIL row under VERIFY-PLAY: an input the input contract refuses (InputRefused), or a
    run that cannot be read. The verifier before the door raised these: of doortest's attacks, the two with a walk input
    of dyaw NaN (in lower and in upper-case hex) ended in a traceback at e759213, InputRefused: INPUT-NOT-FINITE; the
    other eight it refused, it refused there by the play (six) or by its row of the stress run (two), as here. It plays
    every run it is given: never give it an attack whose start is far away (cells_near never ends there), which is why
    BOUNDS is not among the attacks it plays."""
    runs = T["rules"]["1"]["runs"]
    before = len(rows)
    total = sum(played(world, run, rows) for run in runs)
    stress = [r for r in runs if r["name"] == "the stress"]
    if stress:
        made = [write_input(i) for i in stress_inputs(len(stress[0]["inputs"]))]
        start = write_snapshot(State.new(world, "A"))
        rows.append(("the stress run's inputs and start, made again here", made == stress[0]["inputs"] and start == stress[0]["start"],
                     "%d inputs from integers%s; the start, a new state at spawn A, %s" % (
                         len(made), "" if made == stress[0]["inputs"] else " NOT the browser's", "the browser's" if start == stress[0]["start"] else "NOT the browser's")))
    return total, sum(1 for r in rows[before:] if not r[1])


def engine(T):
    rt = T.get("runtime") or {}
    return rt.get("userAgent", "?") if isinstance(rt, dict) else "?"


def run_count(T):
    sec = T["rules"]["1"]
    return len(sec["runs"]) if isinstance(sec, dict) and isinstance(sec.get("runs"), list) else 0


def legible(s):
    """s with every character that is not printable (a line break, a carriage return, an escape, a lone surrogate) written
    as \\uXXXX (\\UXXXXXXXX past U+FFFF): nothing a trace holds makes a line of its own, moves the terminal's cursor or
    fails to be encoded. It makes the start of every line and the exit status honest, not a search for a phrase anywhere
    in a line (a name holding "TICK REFERENCE VERIFIED" still holds it, escaped, inside its row), nor a line a terminal
    wraps at its width."""
    return "".join(c if c.isprintable() else ("\\u%04x" if ord(c) <= 0xFFFF else "\\U%08x") % ord(c) for c in s)


def cmd_verify(path):
    T = load_trace(path)
    rows = []
    world = check_trace(T, rows)
    total, _bad = verify(T, world, rows) if world is not None else (0, 1)
    for line in verdict_lines(path, T, rows, total):
        print(line)
    return 0 if all(r[1] for r in rows) else 1


def verdict_lines(path, T, rows, total):
    """What `verify` prints: the header, a line for each row, the verdict last; every line legible."""
    ok = all(r[1] for r in rows)
    return [legible("TICK-REF  %s  map %s  rules 1  (%s)" % (os.path.basename(path), T["map"], engine(T)))] + [
        legible("%s %s — %s" % ("PASS" if good else "FAIL", name, detail)) for name, good, detail in rows] + [
        "TICK REFERENCE %s  %d ticks of %d runs played here and compared" % ("VERIFIED" if ok else "FAILED", total, run_count(T))]


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
def print_rows(rows):
    """PASS, FAIL, or SKIP for a row that was not run (ok None: its detail says why); a SKIP fails nothing."""
    for name, ok, detail in rows:
        print(legible("%s %s — %s" % ("SKIP" if ok is None else "PASS" if ok else "FAIL", name, detail)))


def cmd_selftest(path):
    import copy
    T = load_trace(path)
    rows = []
    world = check_trace(T, rows)
    if world is None:
        print_rows(rows)
        print("TICK-REF SELFTEST FAILED")
        return 1

    def found(label, ok, detail):
        rows.append((label, ok, detail))

    base = []
    total, bad = verify(T, world, base)
    found("the trace verifies", bad == 0 and all(r[1] for r in base), "%d ticks of %d runs" % (total, run_count(T)))
    if not rows[-1][1]:
        rows.extend((r[0], r[1], legible(r[2])) for r in base if not r[1])
        print_rows(rows)
        print("TICK-REF SELFTEST FAILED  (its plants not run: they play the trace's own runs, which the door refuses)")
        return 1
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
    # a plant at the door (the whole set is `doortest`): the stress run renamed and cut to 2, VERIFIED before the door
    if T.get("inputs_from") is None and [r["name"] for r in T["rules"]["1"]["runs"]] == list(RUN_ORDER):
        rows_a, first, _t = judged(attacked(T, world, _stress_renamed_cut), world)
        refused = first is not None and code_of(rows_a[first]) == "VERIFY-RUN-SET"
        found("plant at the door: the stress run renamed and cut to 2", refused, "refused by VERIFY-RUN-SET, every row before it passed" if refused else
              "NOT refused by VERIFY-RUN-SET: %s" % ("VERIFIED" if first is None else code_of(rows_a[first])))
    else:
        found("plant at the door: the stress run renamed and cut to 2", None, "not run: the plant is made from a trace of the browser's own "
              "runs (%s, none given), and this trace holds %s%s; `doortest` on a trace of the browser's own three runs, none given, "
              "that verifies, holds the door" % (
                  ", ".join(RUN_ORDER), ", ".join(r["name"] for r in T["rules"]["1"]["runs"]) or "no run",
                  ", given by %s" % T["inputs_from"]["engine"] if isinstance(T.get("inputs_from"), dict) else ""))
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
    print_rows(rows)
    ok = all(r[1] is not False for r in rows)
    skipped = sum(1 for r in rows if r[1] is None)
    print("TICK-REF SELFTEST %s%s" % ("PASSED" if ok else "FAILED", "  (%d not run, said above)" % skipped if skipped else ""))
    return 0 if ok else 1


# ------------------------------------------------------------------------------------------------ the door's own test
# `doortest TRACE` (a trace of a browser's own runs: the walk, the fight and the stress run): the trace verifies through
# the door; each attack below, made from it, is refused by its own code with every row before that code passed (the
# self-consistent ones carry snapshots made by this file's own tick, so that only the door can refuse them); plants in
# the door's reading of the fight make the honest trace refuse (one that makes the same fight on the trace's map, an
# equivalent mutant measured there, is not run and says so: on witness the column search); four inputs that ended in a
# traceback before the door's review are each refused by its own code; the bounds, found by the review of its repair
# (2026-10-20), are each judged in bounded time with nothing raised, the tick never given a start or inputs the host did
# not make, and every line verify would print legible; the readers of a detail read every value without raising; and
# the harness plant, the door switched off, makes every attack the verifier accepted before the door VERIFIED again, so
# that the refusals are the door's doing. Its rows are not R5's: none opens "plant: " and they print unbracketed.
def replayed(world, start, inputs):
    """Snapshots made by this file's tick from a start and inputs: what a forger who has this file can write."""
    s = read_snapshot(start)
    out = []
    for inp in inputs:
        tick(world, s, read_input(inp))
        out.append(write_snapshot(s))
    return out


def _runs(T):
    return T["rules"]["1"]["runs"]


def _run(T, name):
    return [r for r in _runs(T) if r["name"] == name][0]


def _no_runs(T, world):
    T["rules"]["1"]["runs"] = []


def _run_removed(T, world):
    T["rules"]["1"]["runs"] = [r for r in _runs(T) if r["name"] != "the fight"]


def _run_renamed(T, world):
    _run(T, "the walk")["name"] = "the stroll"


def _run_twice(T, world):
    import copy
    _runs(T).append(copy.deepcopy(_run(T, "the stress")))


def _stress_renamed_cut(T, world):
    r = _run(T, "the stress")
    r["name"], r["inputs"], r["snaps"] = "the strain", r["inputs"][:2], r["snaps"][:2]


def _walk_fight_cut(T, world):
    for name in ("the walk", "the fight"):
        r = _run(T, name)
        r["inputs"], r["snaps"] = r["inputs"][:10], r["snaps"][:10]


def _forged_fight(T, world):
    r = _run(T, "the fight")
    s = read_snapshot(r["start"])
    sy, cy = sin(s.yaw), cos(s.yaw)
    for n, t in enumerate(s.targets):   # every target on the line of fire, 2 m apart from 2 m out
        d = 2.0 + 2.0 * n
        t.x, t.z, t.y = s.x + d * sy, s.z - d * cy, s.feet
    s.score = 40.0
    r["start"] = write_snapshot(s)
    r["snaps"] = replayed(world, r["start"], r["inputs"])


def _airborne_walk(T, world):
    r = _run(T, "the walk")
    s = read_snapshot(r["start"])
    s.feet, s.on_ground, s.score = s.feet + 3.0, False, 1e6
    r["start"] = write_snapshot(s)
    r["snaps"] = replayed(world, r["start"], r["inputs"])


def _fight_from_nan(T, world):
    r = _run(T, "the fight")
    s = read_snapshot(r["start"])
    s.x = math.nan
    r["start"] = write_snapshot(s)
    r["snaps"] = replayed(world, r["start"], r["inputs"])


def _fight_without_shots(T, world):
    r = _run(T, "the fight")
    out = []
    for text in r["inputs"]:
        inp = read_input(text)
        if inp.get("fire") is True:
            inp["fire"] = False
        out.append(write_input(inp))
    r["inputs"] = out
    r["snaps"] = replayed(world, r["start"], r["inputs"])


def _nan_input(T, world):
    r = _run(T, "the walk")
    inp = read_input(r["inputs"][99])
    inp["dyaw"] = math.nan
    r["inputs"][99] = write_input(inp)


def _given_forged(T, world):
    T["rules"]["1"]["runs"] = [_run(T, "the walk")]
    T["inputs_from"] = {"engine": given_walk_engine(), "inputs": "0" * 64}


NAN_UPPER = "f7FF8000000000000"   # a NaN in the trace's writing with its hex in upper case, which the readers read


def _snapshot_field(text, field, value):
    """A snapshot's text with one top-level field's value replaced, every other byte kept (the writing is compact JSON,
    which json.dumps writes again byte for byte: held before the change)."""
    d = json.loads(text)
    assert json.dumps(d, separators=(",", ":"), ensure_ascii=False) == text and field in d
    d[field] = value
    return json.dumps(d, separators=(",", ":"), ensure_ascii=False)


def _nan_start_upper(T, world):
    r = _run(T, "the fight")
    r["start"] = _snapshot_field(r["start"], "x", NAN_UPPER)


def _nan_input_upper(T, world):
    r = _run(T, "the walk")
    r["inputs"][99] = json.dumps([[k, NAN_UPPER if k == "dyaw" else v] for k, v in json.loads(r["inputs"][99])], separators=(",", ":"))
    assert any(k == "dyaw" for k, _v in json.loads(r["inputs"][99]))


def _nan_snapshot_upper(T, world):
    r = _run(T, "the stress")
    r["snaps"][0] = _snapshot_field(r["snaps"][0], "x", NAN_UPPER)


def _rules1_extra_key(T, world):
    T["rules"]["1"]["note"] = "a key the browser's worker never writes"


def _calls_not_list(T, world):
    T["rules"]["1"]["calls"] = {"cos": 0}


def _snapshot_nested(T, world):
    r = _run(T, "the stress")
    r["snaps"][0] = _snapshot_field(r["snaps"][0], "score", json.loads("[" * 50 + "]" * 50))


def _start_reordered(T, world):
    r = _run(T, "the fight")
    d = json.loads(r["start"])
    r["start"] = json.dumps(dict(reversed(list(d.items()))), separators=(",", ":"))


# (label, the attack, the code that must refuse it, what the verifier without the door does with it: None, VERIFIED)
ATTACKS = [
    ("no runs", _no_runs, "VERIFY-NO-RUNS", None),
    ("a run removed (the fight)", _run_removed, "VERIFY-RUN-SET", None),
    ("a run renamed (the walk as the stroll)", _run_renamed, "VERIFY-RUN-SET", None),
    ("a run twice (the stress)", _run_twice, "VERIFY-RUN-SET", None),
    ("the stress run renamed and cut to 2", _stress_renamed_cut, "VERIFY-RUN-SET", None),
    ("the walk and the fight cut to 10", _walk_fight_cut, "VERIFY-LENGTH", None),
    ("the fight's start forged: every target on the line of fire, the score preset to 40", _forged_fight, "VERIFY-START", None),
    ("the walk's start airborne (feet 3 m up, not on the ground), the score 1e6", _airborne_walk, "VERIFY-START", None),
    ("the fight from x = NaN", _fight_from_nan, "VERIFY-NONFINITE", None),
    ("the fight's inputs with its shots removed", _fight_without_shots, "VERIFY-INPUTS", None),
    ("an input of the walk with dyaw NaN (tick 100), the browser's snapshots kept", _nan_input, "VERIFY-NONFINITE", "VERIFY-PLAY"),
    ("the walk alone, said given by the Python walk under a digest not its own", _given_forged, "VERIFY-GIVEN", None),
    # found by the review of the door (2026-10-19): a NaN written in upper-case hex, which the readers read, passed
    # VERIFY-NONFINITE and was refused later under another code; the rules-1 section's other keys were not held; a
    # value nested past the writing's depth was not held by the form; a start in other bytes was refused without a word
    ("the fight's start with x NaN in upper-case hex, the browser's snapshots kept", _nan_start_upper, "VERIFY-NONFINITE", "VERIFY-PLAY"),
    ("an input of the walk with dyaw NaN in upper-case hex (tick 100), the browser's snapshots kept", _nan_input_upper, "VERIFY-NONFINITE", "VERIFY-PLAY"),
    ("a snapshot of the stress with x NaN in upper-case hex (tick 1)", _nan_snapshot_upper, "VERIFY-NONFINITE", "VERIFY-PLAY"),
    ("a key more in the rules-1 section", _rules1_extra_key, "VERIFY-FORM", None),
    ("the rules-1 calls not a list", _calls_not_list, "VERIFY-FORM", None),
    ("a snapshot of the stress with its score nested 50 deep (tick 1)", _snapshot_nested, "VERIFY-FORM", "VERIFY-PLAY"),
    ("the fight's start with its fields in another order, every value kept", _start_reordered, "VERIFY-START", "VERIFY-PLAY"),
]

def _stress_start_forged(T, world):
    r = _run(T, "the stress")
    s = read_snapshot(r["start"])
    s.score = 7.0
    r["start"] = write_snapshot(s)
    r["snaps"] = replayed(world, r["start"], r["inputs"])


def _input_forged(name):
    def attack(T, world):
        r = _run(T, name)
        inp = read_input(r["inputs"][99])
        inp["dyaw"] = inp.get("dyaw", 0.0) + 0.25
        r["inputs"][99] = write_input(inp)
        r["snaps"] = replayed(world, r["start"], r["inputs"])
    attack.__name__ = "_%s_input_forged" % name.split()[-1]
    return attack


def _stress_snapshot_dropped(T, world):
    _run(T, "the stress")["snaps"].pop()


def _given_fight_alone(T, world):
    T["rules"]["1"]["runs"] = [_run(T, "the fight")]
    T["inputs_from"] = {"engine": "another engine", "inputs": given_digest(T["rules"]["1"]["runs"])}


def _run_extra_field(T, world):
    _run(T, "the walk")["every"] = 30


def _inputs_from_malformed(T, world):
    T["inputs_from"] = {"engine": "x"}


def _snapshot_bare_nan(T, world):
    r = _run(T, "the stress")
    r["snaps"][0] = r["snaps"][0].replace('"score":"f0000000000000000"', '"score":NaN', 1)
    assert '"score":NaN' in r["snaps"][0]


STRESS_AGAIN = "the stress run's inputs and start, made again here"   # verify_without_door's row
ATTACKS += [
    ("the stress's start forged (its score 7), its snapshots replayed", _stress_start_forged, "VERIFY-START", STRESS_AGAIN),
    ("the stress's input 100 turned a quarter radian more, its snapshots replayed", _input_forged("the stress"), "VERIFY-INPUTS", STRESS_AGAIN),
    ("the walk's input 100 turned a quarter radian more, its snapshots replayed", _input_forged("the walk"), "VERIFY-INPUTS", None),
    ("the stress's last snapshot removed", _stress_snapshot_dropped, "VERIFY-LENGTH", "VERIFY-PLAY"),
    ("the fight alone, said given by another engine under its own digest", _given_fight_alone, "VERIFY-RUN-SET", None),
    ("a run with a field more", _run_extra_field, "VERIFY-FORM", None),
    ("inputs_from without its inputs", _inputs_from_malformed, "VERIFY-FORM", None),
    ("a snapshot of the stress with a bare JSON NaN for its score (tick 1)", _snapshot_bare_nan, "VERIFY-NONFINITE", "VERIFY-PLAY"),
]

# what the row that refuses an attack must also say (its detail never empty when the bytes differ)
MUST_SAY = {_start_reordered: SAME_FIELDS}

# plants in the door's reading of the fight (lines() and makeRuns): each must make the honest trace refuse at its start
# (label, the plant, the maps where it makes the same fight, an equivalent mutant in that map's state, MEASURED
# 2026-10-20): there it is not run and says so; anywhere else a plant that makes the same fight is a FAIL (a defect in
# the plant's switch, or a map whose equivalence nobody has measured), as is one declared equivalent that is not; at
# least one plant must run)
READING_PLANTS = [
    ("lines() aimed 0.5 m above the target's foot, not 1.2 (the pitch at 1.2)", {"aim": 0.5}, ()),
    ("makeRuns' pitch aimed 1.0 m above the target's foot, not 1.2", {"pitch_aim": 1.0}, ()),
    ("the fight's floor cells searched column by column", {"rows_first": False}, ("witness",)),
]


def code_of(row):
    word = row[0].split(" ", 1)[0]
    return word if word.startswith("VERIFY-") else row[0]


def judged(T, world):
    """The rows verify gives T (the map's first), the first that failed (its index) or None, and the ticks played."""
    rows = []
    check_trace(T, rows)
    total, _bad = verify(T, world, rows)
    first = next((k for k, r in enumerate(rows) if not r[1]), None)
    return rows, first, total


def attacked(T, world, attack):
    import copy
    A = copy.deepcopy(T)
    attack(A, world)
    return A


def last_score(run):
    return read_snapshot(run["snaps"][-1]).score if run["snaps"] else None


def door_rows(T, world):
    """doortest's rows: (label, ok, detail)."""
    global DOOR
    out = []
    rows, first, total = judged(T, world)
    codes = [code_of(r) for r in rows]
    names = [r["name"] for r in _runs(T)]
    honest = first is None and names == list(RUN_ORDER) and T.get("inputs_from") is None
    out.append(("the trace verifies through the door", honest, "%d ticks of %s; the rows %s" % (
        total, ", ".join(names), ", ".join(dict.fromkeys(codes))) if honest else
        "NOT a trace of the browser's own three runs that verifies: %s" % ("; ".join("%s %s" % (r[0], r[2]) for r in rows if not r[1])[:600] or ", ".join(names))))
    if not honest:
        return out
    open_outcomes = []
    for label, attack, code, without in ATTACKS:
        A = attacked(T, world, attack)
        try:
            rows, first, _total = judged(A, world)
        except Exception as e:   # noqa: the row is that nothing is raised
            rows, first = [("raised", False, "%s: %s" % (type(e).__name__, str(e)[:200]))], 0
        ok = first is not None and code_of(rows[first]) == code and MUST_SAY.get(attack, "") in rows[first][2]
        out.append(("attack: " + label, ok, ("refused by %s — %s; every row before it passed (%s)" % (
            code, rows[first][2][:300], ", ".join(code_of(r) for r in rows[:first]))) if ok else
            "NOT refused by %s%s: %s" % (code, " saying %r" % MUST_SAY[attack] if attack in MUST_SAY else "",
                                         "VERIFIED" if first is None else "the first row failed is %s — %s" % (code_of(rows[first]), rows[first][2][:300]))))
        DOOR = False
        try:
            rows_off, first_off, total_off = judged(A, world)
        finally:
            DOOR = True
        open_outcomes.append((label, code, without, first_off, rows_off, total_off, A))
    for label, kw, equivalent_on in READING_PLANTS:
        g = globals()
        saved = g["made_fight"]
        same = saved(world, **kw) == saved(world)
        if same and T["map"] in equivalent_on:   # an equivalent mutant on this map, as measured: it can show nothing here
            out.append(("plant in the door's reading: " + label, None, "not run: on the map %s this plant makes the same fight "
                        "start and inputs as the reading without it (an equivalent mutant in this map's state, measured), so it "
                        "can show nothing of the reading here; at least one plant of the reading must run" % T["map"]))
            continue
        if same or T["map"] in equivalent_on:
            out.append(("plant in the door's reading: " + label, False, ("NOT a plant here: on the map %s it makes the same fight "
                        "start and inputs as the reading without it, which no measurement declared (a switch that changes "
                        "nothing, or a map whose equivalence nobody measured)" if same else "declared an equivalent mutant on "
                        "the map %s, and it changes the fight there: the declaration is wrong") % T["map"]))
            continue
        g["made_fight"] = lambda w, kw=kw: saved(w, **kw)
        try:
            rows, first, _total = judged(T, world)
        finally:
            g["made_fight"] = saved
        ok = first is not None and code_of(rows[first]) == "VERIFY-START" and "the fight" in rows[first][2] and \
            not any(n in rows[first][2] for n in ("the walk:", "the stress:"))
        out.append(("plant in the door's reading: " + label, ok, ("the honest trace refused by VERIFY-START — %s" % rows[first][2][:300]) if ok else
                    "NOT refused at the fight's start: %s" % ("VERIFIED" if first is None else "%s — %s" % (code_of(rows[first]), rows[first][2][:300]))))
    out.extend(refusal_rows(T, world))
    out.extend(bound_rows(T, world))
    out.extend(reader_rows())
    # the harness plant: the door switched off; every attack's own row must then fail, and each attack the verifier
    # accepted before the door must be VERIFIED again (the cause); the ten it never accepted are refused by the play
    # (eight: two of them, the walk input of dyaw NaN in lower and in upper-case hex, by a FAIL row where the verifier
    # at e759213 raised InputRefused) or by its row of the stress run made again (two), as at e759213 (MEASURED there,
    # 2026-10-20)
    wrong, accepted = [], []
    for label, code, without, first_off, rows_off, total_off, A in open_outcomes:
        outcome = None if first_off is None else code_of(rows_off[first_off])
        if outcome != without or outcome == code:
            wrong.append("%s: %s, not %s" % (label, outcome or "VERIFIED", without or "VERIFIED"))
        if outcome is None:
            extra = ""
            if label.startswith("the fight's start forged"):
                extra = ", its final score %s against the browser's %s" % (show(last_score(_run(A, "the fight"))), show(last_score(_run(T, "the fight"))))
            accepted.append("%s (%d ticks of %d runs%s)" % (label, total_off, len(_runs(A)), extra))
    out.append(("harness plant: the door switched off", not wrong and len(accepted) == sum(1 for a in ATTACKS if a[3] is None),
                ("caught: every attack's row would fail; %d of %d VERIFIED without the door: %s; and %s" % (
                    len(accepted), len(ATTACKS), "; ".join(accepted), "; ".join("%s refused only by %s" % (a[0], a[3]) for a in ATTACKS if a[3]))) if not wrong else
                "NOT as the verifier was before the door: " + "; ".join(wrong)))
    return out


def refusal_rows(T, world):
    """Inputs that ended in a traceback before the review (2026-10-19), each now a refusal by its own code, with every
    row before it passed: a map that cannot be converted here; a snapshot, and a whole trace, nested 100,000 deep (past
    Python's json reader's depth); and a snapshot with a key twice, whose refusal must say what differs."""
    import copy
    out = []
    deep = "[" * 100000 + "]" * 100000
    A = copy.deepcopy(T)
    A["map"] = "nosuchmap"
    rows = []
    try:
        w = check_trace(A, rows)
        ok = w is None and len(rows) == 1 and not rows[0][1] and code_of(rows[0]) == "VERIFY-MAP"
        detail = rows[0][2] if rows else "no row"
    except Exception as e:   # noqa: the row is that nothing is raised
        ok, detail = False, "raised %s: %s" % (type(e).__name__, e)
    out.append(("refusal: the map named is none here (nosuchmap)", ok, ("refused by VERIFY-MAP, the world none — %s" % detail[:300]) if ok else
                "NOT refused by VERIFY-MAP alone: %s" % detail[:300]))
    for label, change, code, must in (
            ("a snapshot of the stress nested 100,000 deep (tick 1)", lambda A: _run(A, "the stress")["snaps"].__setitem__(0, deep), "VERIFY-FORM", "is not a JSON object"),
            ("a snapshot of the stress with its key x written twice (tick 1)", lambda A: _run(A, "the stress")["snaps"].__setitem__(
                0, _run(A, "the stress")["snaps"][0][:-1] + ',"x":' + json.dumps(json.loads(_run(A, "the stress")["snaps"][0])["x"]) + "}"), "VERIFY-PLAY", SAME_FIELDS)):
        try:
            rows, first, _total = judged(attacked(T, world, lambda A, w, change=change: change(A)), world)
            ok = first is not None and code_of(rows[first]) == code and must in rows[first][2]
            detail = "VERIFIED" if first is None else rows[first][2][:300] if ok else "%s — %s" % (code_of(rows[first]), rows[first][2][:300])
        except Exception as e:   # noqa: the row is that nothing is raised
            ok, detail = False, "raised %s: %s" % (type(e).__name__, str(e)[:200])
        out.append(("refusal: " + label, ok, ("refused by %s — %s" % (code, detail)) if ok else "NOT refused by %s saying %r: %s" % (code, must, detail)))
    try:
        parse_trace(deep.encode("utf-8"), "a trace nested 100,000 deep")
        ok, detail = False, "read as a trace"
    except SystemExit as e:
        ok, detail = "not JSON" in str(e), str(e)[:300]
    except Exception as e:   # noqa: the row is that nothing is raised
        ok, detail = False, "raised %s: %s" % (type(e).__name__, str(e)[:200])
    out.append(("refusal: a whole trace nested 100,000 deep", ok, ("refused before the door, not JSON here — %s" % detail) if ok else
                "NOT refused as not JSON: %s" % detail))
    return out


REFUSALS = 4   # refusal_rows' rows


class Unmade(Exception):
    """doortest's guard: the tick was given a start or inputs the host did not make."""


def _start_at(name, field, value):
    def attack(T, world):
        r = _run(T, name)
        s = read_snapshot(r["start"])
        setattr(s, field, value)
        r["start"] = write_snapshot(s)
    return attack


def _start_text(name, field, value):
    def attack(T, world):
        r = _run(T, name)
        r["start"] = _snapshot_field(r["start"], field, value)
    return attack


def _stress_snapshot_x(value):
    def attack(T, world):
        r = _run(T, "the stress")
        r["snaps"][0] = _snapshot_field(r["snaps"][0], "x", value)
    return attack


def _stress_snapshot_target_x(value):
    def attack(T, world):
        r = _run(T, "the stress")
        d = json.loads(r["snaps"][0])
        assert json.dumps(d, separators=(",", ":"), ensure_ascii=False) == r["snaps"][0]
        d["targets"][0]["x"] = value
        r["snaps"][0] = json.dumps(d, separators=(",", ":"), ensure_ascii=False)
    return attack


def _renamed_far(name, new):
    def attack(T, world):
        r = _run(T, name)
        s = read_snapshot(r["start"])
        s.z = 1e17
        r["name"], r["start"] = new, write_snapshot(s)
    return attack


def _walk_named(name):
    def attack(T, world):
        _run(T, "the walk")["name"] = name
    return attack


def _user_agent(text, then=None):
    def attack(T, world):
        T["runtime"] = dict(T.get("runtime") or {}, userAgent=text)
        if then is not None:
            then(T, world)
    return attack


VERDICT_FORGED = "TICK REFERENCE VERIFIED  5863 ticks of 3 runs played here and compared"
# (label, the attack, the code that must refuse it or None for VERIFIED, what its row must say, what it must not say):
# each judged in bounded time, nothing raised, by its own code with every row before it passed, and every line verify
# would print legible. Found by the review of the door's repair (2026-10-20): a start far away or infinite hung verify
# for ever in cells_near (the door's rows written and never printed); a value the readers take for a number and cannot
# read, or targets that are not a list of objects, ended in a traceback; a run's name or the userAgent printed raw
# could print a verdict line of its own, a carriage return or an escape, or raise on a lone surrogate.
BOUNDS = [
    ("the fight's start at x = 1e17 (finite), the browser's snapshots kept", _start_at("the fight", "x", 1e17), "VERIFY-START", "", ""),
    ("the fight's start at x = +Infinity, the browser's snapshots kept", _start_at("the fight", "x", math.inf), "VERIFY-NONFINITE", "", ""),
    ("the walk's start at x = -Infinity, the browser's snapshots kept", _start_at("the walk", "x", -math.inf), "VERIFY-NONFINITE", "", ""),
    ("the stress's start at z = 1e17, the browser's snapshots kept", _start_at("the stress", "z", 1e17), "VERIFY-START", "", ""),
    ("the walk renamed the stroll, its start at z = 1e17", _renamed_far("the walk", "the stroll"), "VERIFY-RUN-SET", "", ""),
    ("the stress renamed the strain, its start at z = 1e17", _renamed_far("the stress", "the strain"), "VERIFY-RUN-SET", "", ""),
    ("a stress snapshot's x 'f' and sixteen characters that are not hex (tick 1)", _stress_snapshot_x("f" + "Z" * 16), "VERIFY-FORM", "", ""),
    ("a stress snapshot's x 'f7ff8', ten zeros and two spaces, 7 bytes to fromhex (tick 1)", _stress_snapshot_x("f7ff8" + "00" * 5 + "  "), "VERIFY-FORM", "", ""),
    ("a stress snapshot's x 'f 7ff00000000000 ', spaced hex (tick 1)", _stress_snapshot_x("f 7ff00000000000 "), "VERIFY-FORM", "", ""),
    ("the fight's start's x 'f' and sixteen characters that are not hex", _start_text("the fight", "x", "f" + "z" * 16), "VERIFY-FORM", "", ""),
    ("the fight's start with its targets an object", _start_text("the fight", "targets", {"T0": 1}), "VERIFY-FORM", "", ""),
    ("the fight's start with its targets a number", _start_text("the fight", "targets", 5), "VERIFY-FORM", "", ""),
    ("the stress's start with its targets a list of a number", _start_text("the stress", "targets", [1]), "VERIFY-FORM", "", ""),
    ("the walk's start with its targets a list of numbers", _start_text("the walk", "targets", [1, 2]), "VERIFY-FORM", "", ""),
    ("a stress snapshot's x the string 'fxyz' (tick 1)", _stress_snapshot_x("fxyz"), "VERIFY-PLAY", "FIRST DIFFERENT", "ulp"),
    ("a stress snapshot's x the string 'fg' (tick 1)", _stress_snapshot_x("fg"), "VERIFY-PLAY", "FIRST DIFFERENT", "ulp"),
    ("a stress snapshot's x the string 'f' (tick 1)", _stress_snapshot_x("f"), "VERIFY-PLAY", "FIRST DIFFERENT", "ulp"),
    ("a stress snapshot's x the string 'f-1', no ulp count read from it (tick 1)", _stress_snapshot_x("f-1"), "VERIFY-PLAY", "FIRST DIFFERENT", "ulp"),
    ("a stress snapshot's first target's x the string 'fg' (tick 1)", _stress_snapshot_target_x("fg"), "VERIFY-PLAY", "FIRST DIFFERENT", "ulp"),
    ("the walk's name holding a line break, a verdict, a carriage return and an escape", _walk_named(
        "the walk" + chr(10) + VERDICT_FORGED + chr(13) + chr(27) + "[8m"), "VERIFY-RUN-SET", "", ""),
    ("the walk's name holding a lone surrogate", _walk_named("the walk" + chr(0xD800)), "VERIFY-RUN-SET", "", ""),
    ("the fight's start forged and the userAgent holding a line break, a forged PASS row, a verdict and an escape",
     _user_agent("Mozilla/5.0)" + chr(10) + "PASS VERIFY-MAP the map" + chr(10) + VERDICT_FORGED + chr(27) + "[8m", _forged_fight),
     "VERIFY-START", "", ""),
    ("the userAgent (the header) holding a line break, a verdict and an escape, the trace honest",
     _user_agent("Mozilla/5.0" + chr(10) + VERDICT_FORGED + chr(27) + "[8m"), None, "", ""),
    ("the userAgent (the header) holding a lone surrogate, the trace honest", _user_agent("Mozilla/5.0 " + chr(0xD800)), None, "", ""),
    ("the userAgent (the header) holding U+2028, U+0085 and U+E0001, the trace honest",
     _user_agent("Mozilla/5.0" + chr(0x2028) + chr(0x85) + chr(0xE0001)), None, "", ""),
]


def printable_lines(lines):
    """Every line printable and encodable as UTF-8, and none but the last beginning "TICK REFERENCE "."""
    try:
        for line in lines:
            line.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return all(line.isprintable() for line in lines) and not any(line.startswith("TICK REFERENCE ") for line in lines[:-1])


def bound_rows(T, world):
    """Each of BOUNDS judged with nothing raised and the tick never given a start or inputs the host did not make (a
    start 1e17 or Infinity away loops in cells_near for ever: MEASURED, 2026-10-20): refused by its own code with every
    row before it passed and the verdict FAILED, or, for an honest trace, VERIFIED; and every line verify would print
    legible: one line per row, the verdict alone and last."""
    out = []
    made = made_runs(T, world)
    g = globals()
    real = g["play"]

    def guarded(world_, run):
        m = made.get(run["name"])
        if m is None or run["start"] != m[0] or run["inputs"] != m[1]:
            raise Unmade(run["name"])
        return real(world_, run)
    g["play"] = guarded
    try:
        for label, attack, code, must, never in BOUNDS:
            A = attacked(T, world, attack)
            try:
                rows, first, total = judged(A, world)
                lines = verdict_lines("a trace", A, rows, total)
                fit = printable_lines(lines)
                if code is None:
                    ok = first is None and fit and lines[-1].startswith("TICK REFERENCE VERIFIED")
                    detail = ("VERIFIED, every line legible — %s" % lines[0][:200]) if ok else "NOT VERIFIED with every line legible: %s%s" % (
                        "VERIFIED" if first is None else "%s — %s" % (code_of(rows[first]), legible(rows[first][2])[:200]),
                        "" if fit else "; a line not legible")
                else:
                    said = first is not None and must in rows[first][2] and not (never and never in rows[first][2])
                    ok = first is not None and code_of(rows[first]) == code and said and fit and lines[-1].startswith("TICK REFERENCE FAILED")
                    detail = ("refused by %s — %s" % (code, legible(rows[first][2])[:200])) if ok else "NOT refused by %s%s%s with every line legible: %s%s" % (
                        code, " saying %r" % must if must else "", " and not %r" % never if never else "",
                        "VERIFIED" if first is None else "%s — %s" % (code_of(rows[first]), legible(rows[first][2])[:200]),
                        "" if fit else "; a line not legible")
            except Unmade as e:
                ok, detail = False, "the tick was given the start or the inputs of %s, which the host did not make" % legible(str(e))
            except Exception as e:   # noqa: the row is that nothing is raised
                ok, detail = False, "raised %s: %s" % (type(e).__name__, legible(str(e))[:200])
            out.append(("bound: " + label, ok, detail))
    finally:
        g["play"] = real
    return out


# what the detail readers are given, those the form refuses before verify reaches them included
UNREAD_VALUES = ["f" + "Z" * 16, "f7ff8" + "00" * 5 + "  ", "f 7ff00000000000 ", "fxyz", "f", "fg", "f-1", 5, None, [1, 2], {"a": 1}]
UNREAD_STARTS = ['{"targets":{"a":1}}', '{"targets":5}', '{"targets":[1,2]}', '{"targets":"x"}', '{"targets":null}',
                 '{"x":"fzzzzzzzzzzzzzzzz"}']


def reader_rows():
    """The readers of a detail (show, ulp_note, fields_of and first_difference) read every value without raising, those
    the form refuses included: VERIFY-FORM keeps them from verify, so that a defect in show or fields_of shows in no
    bound row (an equivalent mutant there), and these rows hold the readers themselves (the `cases`, `rules2` and
    `rules3` tables read with fields_of too)."""
    out = []
    honest = "f401c0583a8156df2"
    for label, call in (
            ("show reads every value", lambda: [show(v) for v in UNREAD_VALUES]),
            ("ulp_note reads every pair, and counts only two numbers of the writing", lambda: [
                ulp_note(v, honest) for v in UNREAD_VALUES] + [ulp_note(honest, v) for v in UNREAD_VALUES]),
            ("fields_of and first_difference read every start", lambda: [fields_of(t) for t in UNREAD_STARTS] + [
                first_difference(t, '{"x":"f401c0583a8156df2"}') for t in UNREAD_STARTS])):
        try:
            got = call()
            ok = not (label.startswith("ulp_note") and any(got))
            detail = "%d read, nothing raised%s" % (len(got), "" if ok else "; a count read from a value that is not a number: %r" % [x for x in got if x])
        except Exception as e:   # noqa: the row is that nothing is raised
            ok, detail = False, "raised %s: %s" % (type(e).__name__, legible(str(e))[:200])
        out.append(("reader: " + label, ok, detail))
    return out


def door_total():
    return 2 + len(ATTACKS) + len(READING_PLANTS) + REFUSALS + len(BOUNDS) + READERS


READERS = 3   # reader_rows' rows


def cmd_doortest(path):
    T = load_trace(path)
    rows = []
    world = check_trace(T, rows)
    if world is None:
        print_rows(rows)
        print("DOOR SELFTEST 0/%d" % door_total())
        return 1
    out = door_rows(T, world)
    print_rows(out)
    n = sum(1 for r in out if r[1])
    skipped = sum(1 for r in out if r[1] is None)
    total = door_total()
    print("DOOR SELFTEST %d/%d%s" % (n, total, "  (%d not run, said above)" % skipped if skipped else ""))
    return 0 if len(out) == total and n + skipped == total and skipped < len(READING_PLANTS) else 1


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


SET_TARGET = {"downFor": "down_for", "up": "up"}


def play2(conv, case, rules=2):
    """A case of rules 2's table (or rules 3's) played here: its identity, start, every tick's snapshot and hash; or
    why the world was refused."""
    r = {"name": case["name"]}
    if case.get("world"):   # a case may set the world's wall height, and nothing else of it
        if set(case["world"]) != {"wall"}:
            raise ValueError("a case can set the world's wall alone")
        conv = dict(conv, canonical=dict(conv["canonical"], wall=case["world"]["wall"]))
    try:
        world = (World3 if rules == 3 else World2)(conv, case.get("movers") or [])
    except MoverRefused as e:
        r["refused"] = str(e)
        return r
    r["identity_text"] = world.identity
    s = State2.new(world, (case.get("start") or {}).get("side", "A"))
    for k, v in sorted(((case.get("start") or {}).get("set") or {}).items()):
        setattr(s, SET2[k], v if isinstance(v, bool) else float(v))
    for tid, kv in sorted(((case.get("start") or {}).get("targets") or {}).items()):
        t = [t for t in s.targets if t.id == tid][0]
        for k, v in sorted(kv.items()):
            setattr(t, SET_TARGET[k], v if isinstance(v, bool) else float(v))
    r.update(identity="%016x" % world.identity_state, start=write_snapshot2(s), snaps=[], hashes=[])
    inside = 0
    step = tick3 if rules == 3 else tick2
    for seg in case.get("inputs") or []:
        for inp in (stress_inputs(seg["stress"]) if seg.get("stress") else [dict(seg.get("in") or {}) for _ in range(seg["n"])]):
            step(world, s, inp)
            r["snaps"].append(write_snapshot2(s))
            r["hashes"].append(hash2(world, s))
            # the invariant stop and blocked give: the body never ends a tick inside a box, but standing on its top;
            # under rules 3 not inside a standing target below its top, nor over a wall's cell either
            if any(plan_over(s.x, s.z, b) and b[4] > s.feet and b[1] < s.feet + BODY for b in poses(world, s)):
                inside += 1
            elif rules == 3 and (any(t.up and in_column(t, s.x, s.z, s.feet) for t in s.targets)
                                 or any(world.top(i, j) >= world.wall for i, j in world.cells_near(s.x, s.z, K.radius))):
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
            elif k == "targets":   # rules 3's table: a target's up and downFor
                for tid, want in sorted(v.items()):
                    got = [x for x in d["targets"] if x["id"] == "s" + tid]
                    gotv = {"up": got[0]["up"], "downFor": _dec(got[0]["downFor"])} if got else None
                    wantv = {"up": want["up"], "downFor": float(want["downFor"])} if "downFor" in want else {"up": want["up"]}
                    if gotv is not None and "downFor" not in want:
                        gotv = {"up": gotv["up"]}
                    if gotv != wantv:
                        out.append("tick %d: target %s %s, worked %s" % (t, tid, gotv, wantv))
            elif k == "about":     # a value worked to within a stated bound (a sum of steps no double holds exactly)
                for f, (wv, tol) in sorted(v.items()):
                    gv = _dec(d[f])
                    if not abs(gv - wv) <= tol:
                        out.append("tick %d: %s %r, worked %r within %g" % (t, f, gv, wv, tol))
            else:
                gv = _dec(d[k])
                wv = v if isinstance(v, bool) else float(v)
                if type(gv) is not type(wv) or gv != wv:
                    out.append("tick %d: %s %r, worked %r" % (t, k, gv, wv))
    return out


def rules2_case(case):
    """A rules-3 case as rules 2 are held to it: its expect_rules2 and expect_rules2_refused in the places of expect
    and expect_refused."""
    c = dict(case, expect=case.get("expect_rules2") or [])
    c.pop("expect_refused", None)
    if case.get("expect_rules2_refused"):
        c["expect_refused"] = case["expect_rules2_refused"]
    return c


def run_table2(conv, table, rules=2):
    """Every case played here, with its faults against the working, and the case of no movers against rules 1; under
    rules 3, a case's values under rules 2 (expect_rules2), its snapshots equal to rules 2's (rules2_equal) and its
    identity's text (identity_has) as well."""
    rows, mine = [], {}
    for case in table["cases"]:
        r = play2(conv, case, rules)
        mine[case["name"]] = r
        faults = expect_faults(case, r)
        if rules == 3 and not r.get("refused"):
            for part in case.get("identity_has") or []:
                if part not in r["identity_text"]:
                    faults.append("the identity does not hold %r" % part)
        if rules == 3 and (case.get("expect_rules2") or case.get("rules2_equal") or case.get("expect_rules2_refused")):
            r2 = r["rules2"] = play2(conv, case, 2)
            faults += ["under rules 2, " + f for f in expect_faults(rules2_case(case), r2)]
            if not r.get("refused"):
                if case.get("rules2_equal"):
                    bad = [n + 1 for n, (a, b) in enumerate(zip(r2.get("snaps", []), r["snaps"])) if a != b]
                    if bad or len(r2.get("snaps", [])) != len(r["snaps"]):
                        faults.append("parts from rules 2 at tick %s" % (bad[:1] or ["count"])[0])
                    elif not faults:
                        case = dict(case, _rules1="every one of %d ticks the same bytes as rules 2's (the identity apart)" % len(r["snaps"]))
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
            "refused as worked: %s" % r["refused"][:70] if r.get("refused") else ("%d ticks; no tick ended with the body inside a box%s" % (len(r["snaps"]), ", a standing target or a wall's cell" if rules == 3 else "")
                                                                                 if case.get("invariant") else "%d ticks; every value worked by hand held%s" % (len(r.get("snaps", [])), ", and under rules 2 theirs" if case.get("expect_rules2") else ""))))))
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
            def __init__(self, d, ids, *policies):
                d = dict(d)
                sp = d.get("speed")
                d["speed"] = 0
                saved["Mover"].__init__(self, d, ids, *policies)
                self.speed = float(sp)
        g["Mover"] = M
    g["PHASES2"] = (respawn2, g["movers2"], aim2, walk2, g["height2"], weapon, stand_again, objective)
    return undo


PLANTS2 = ("no carry", "wrap at more than 2 len", "no stop", "no ceiling", "no tunnelling bound")


def _plant3(name):
    """A mutant of this file's rules 3, by name, for rules3's own check that the worked values bite: returns undo."""
    g = globals()
    saved = {k: g[k] for k in ("walled", "target_tops", "stand_again3", "push", "identity_text", "PHASES3")}
    wall_of = World3._wall

    def undo():
        g.update(saved)
        World3._wall = wall_of
    if name == "walls by height alone":
        g["walled"] = lambda world, x, z: False
    elif name == "no target top":
        g["target_tops"] = lambda s, x, z, before: []
    elif name == "a target's top at any height":
        g["target_tops"] = lambda s, x, z, before: saved["target_tops"](s, x, z, math.inf)
    elif name == "any wall height":
        World3._wall = lambda self, W: float(W.get("wall"))
    elif name == "a target stands at once":
        g["stand_again3"] = stand_again
    elif name == "push as stop":
        g["push"] = lambda world, s, k, m, b, dx, dz: False
    elif name == "push into a wall":
        def p3(world, s, k, m, b, dx, dz):
            if m.policy != "push" or m.ay != 0:
                return False
            s.x, s.z = s.x + dx, s.z + dz
            return True
        g["push"] = p3
    elif name == "push along y":
        def p3(world, s, k, m, b, dx, dz):
            if m.policy != "push":
                return False
            nx, nz = s.x + dx, s.z + dz
            if is_blocked3(world, s, nx, nz, s.feet, k, b):
                return False
            s.x, s.z = nx, nz
            return True
        g["push"] = p3
    elif name == "the wall left out of the identity":
        g["identity_text"] = lambda *a: re.sub(r',"wall":"f[0-9a-f]{16}"', "", saved["identity_text"](*a))
    g["PHASES3"] = (respawn2, movers3, aim2, walk3, height3, weapon, g["stand_again3"], objective)
    return undo


PLANTS3 = ("walls by height alone", "no target top", "a target's top at any height", "a target stands at once", "push as stop",
           "push into a wall", "push along y", "the wall left out of the identity", "any wall height")
RULES3_CASES = os.path.join(HERE, "web", "rules3_cases.json")


def engine_faults(case, t, m):
    """Where an engine's run of a case (t) parts from the values worked by hand, or from this file's run of it (m)."""
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
    return faults


def cmd_rules2(path=None):
    return cmd_rules(path, 2)


def cmd_rules3(path=None):
    return cmd_rules(path, 3)


def cmd_rules(path, rules):
    where, plants, plant = (RULES3_CASES, PLANTS3, _plant3) if rules == 3 else (RULES2_CASES, PLANTS2, _plant)
    with open(where, encoding="utf-8") as fh:
        table = json.load(fh)
    conv = level.convert(table["map"])
    print("RULES%d  %s  map %s  rules %d (RULES-%d.md), %d cases" % (rules, os.path.relpath(where), table["map"], rules, rules, len(table["cases"])))
    rows, mine = run_table2(conv, table, rules)
    for name, ok, detail in rows:
        print("%s %s — %s" % ("PASS" if ok else "FAIL", name, detail))
    caught = 0
    for p in plants:
        undo = plant(p)
        try:
            prow, _m = run_table2(conv, table, rules)
        finally:
            undo()
        bit = [n for n, ok, _d in prow if not ok]
        caught += 1 if bit else 0
        print("%s plant: %s — %s" % ("PASS" if bit else "FAIL", p, ("caught by " + ", ".join(b.split(" ")[0] for b in bit)) if bit else "NOT caught by any worked value"))
    ok = all(r[1] for r in rows) and caught == len(plants)
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
            faults = engine_faults(case, t, m)
            if "rules2" in m:   # rules 3's table: the engine's run of the same case under rules 2, held likewise
                if not isinstance(t.get("rules2"), dict):
                    faults.append("no run under rules 2 there")
                else:
                    faults += ["under rules 2, " + f for f in engine_faults(rules2_case(case), t["rules2"], m["rules2"])]
            engine_ok = engine_ok and not faults
            print("%s %s — %s" % ("PASS" if not faults else "FAIL", case["name"], "; ".join(faults)[:240] if faults else (
                "refused there as here" if m.get("refused") else "%d ticks: every snapshot and hash the same, identity %s" % (len(m["snaps"]), m["identity"]))))
    held = ok and engine_ok
    print("RULES %d %s%s" % (rules, "HELD BY PYTHON" if ok else "NOT HELD", (" AND THE ENGINE" if engine_ok else "; THE ENGINE PARTS") if path else ""))
    return 0 if held else 1


MAKES = {"verify": "python graybox/trace.py run tactical --browser msedge", "selftest": "python graybox/trace.py run tactical --browser msedge",
         "doortest": "python graybox/trace.py run tactical --browser msedge",
         "cases": "python graybox/trace.py run tactical --cases --browser msedge", "rules2": "python graybox/trace.py run tactical --rules2 --browser msedge",
         "rules3": "python graybox/trace.py run tactical --rules3 --browser msedge"}


def main(argv):
    # a results file named and not there is said before anything is played (0226: his run of 0225 met a traceback,
    # the table played first, when the browser's run had not been made yet)
    if len(argv) == 2 and argv[0] in MAKES and not os.path.isfile(argv[1]):
        print("TICK-REF: there is no file %s: a browser writes it, so run first:  %s" % (argv[1], MAKES[argv[0]]), file=sys.stderr)
        return 2
    if len(argv) in (1, 2) and argv[0] == "rules2":
        return cmd_rules2(argv[1] if len(argv) == 2 else None)
    if len(argv) in (1, 2) and argv[0] == "rules3":
        return cmd_rules3(argv[1] if len(argv) == 2 else None)
    if len(argv) == 2 and argv[0] == "verify":
        return cmd_verify(argv[1])
    if len(argv) == 2 and argv[0] == "selftest":
        return cmd_selftest(argv[1])
    if len(argv) == 2 and argv[0] == "doortest":
        return cmd_doortest(argv[1])
    if len(argv) in (1, 2) and argv[0] == "cases":
        return cmd_cases(argv[1] if len(argv) == 2 else None)
    print("usage: python graybox/tick_ref.py verify TRACE.json | selftest TRACE.json | doortest TRACE.json | cases [RESULTS.json] | rules2 [RESULTS.json] | rules3 [RESULTS.json]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
