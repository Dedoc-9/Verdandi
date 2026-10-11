# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# graybox/tick_ref.py — a second implementation of the graybox's tick (rules 1, graybox/RULES-1.md), in Python, and
# the verifier of what a browser played.
#
#   python graybox/tick_ref.py verify TRACE.json
#   python graybox/tick_ref.py selftest TRACE.json
#   python graybox/tick_ref.py cases [RESULTS.json]
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

    def top(self, i, j):
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
        s.targets = [Target(tid, (tx + 0.5) * c, world.top(tx, tz), (tz + 0.5) * c, True, 0.0) for tid, tx, tz in world.target_cells]
        spawn(world, s, side)
        return s


def spawn(world, s, side):
    sx, sz, yaw_degrees = world.spawns[side]
    c = world.cell
    s.side = side
    s.x, s.z = (sx + 0.5) * c, (sz + 0.5) * c
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
        i, j = floor(s.x / world.cell), floor(s.z / world.cell)
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


def main(argv):
    if len(argv) == 2 and argv[0] == "verify":
        return cmd_verify(argv[1])
    if len(argv) == 2 and argv[0] == "selftest":
        return cmd_selftest(argv[1])
    if len(argv) in (1, 2) and argv[0] == "cases":
        return cmd_cases(argv[1] if len(argv) == 2 else None)
    print("usage: python graybox/tick_ref.py verify TRACE.json | selftest TRACE.json | cases [RESULTS.json]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
