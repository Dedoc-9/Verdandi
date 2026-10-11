# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# graybox/bot_ref.py — the walk made in Python from the map alone (the bot's policy walk-1, graybox/WALK-1.md), and
# what holds it.
#
#   python graybox/bot_ref.py make MAP [--out FILE]       (--out - writes the walk to standard output)
#   python graybox/bot_ref.py check BOT.json
#   python graybox/bot_ref.py compare BOT.json TRACE.json
#   python graybox/bot_ref.py selftest TRACE.json
#
# By the owner's ruling of 2026-10-11 (BOT-REF-0): the map, the bot's policy and rules 1 make an input trace in
# Python, and tick_ref.py advances it, so that "a browser is no longer needed to originate the reference walk, while
# browser runs remain independent evidence that the reference model agrees with the actual engine". Written from
# WALK-1.md, not ported from sim.js: the plan is a breadth-first search a layer at a time, and a decision is a pure
# function of the path, the bot's own memory and an observation of the present state (x, z and yaw), which is all
# of the game it is given. It never sees a later state, a browser's decision or another trace. The tick that
# advances the state is tick_ref.py's, the only thing here that writes a game state.
#
# `make` writes the walk (VERDANDI-BOT-TRACE 1: the map's identity, the start's bytes, the rules and the policy, the
# number of ticks and each tick's input) to graybox/build/bot/MAP-walk.json. `check` reads one, refusing the whole
# file on any malformed or mismatched part, makes it again here and requires the same bytes, and holds it to what a
# walk is for (its inputs, its path, and its replay through the tick). `compare` sets it beside a browser's trace
# (graybox/trace.py): the start, each tick's input, and each tick's state as the Python tick makes it against the
# browser's snapshot, naming the first differing tick and fields. `selftest` makes the walk twice more in fresh
# processes under other hash seeds, and plants defects (in the policy, in a byte of an input, in the map's identity,
# in the file's form, in a tick's result, and walks that break what a walk is held to), each required to be found.
#
# What it does not show. That walk-1 is the walk a player would make: the checks hold it to what a walk of a route is
# for, nothing more. That the browsers agree: only their traces show that. A server, a protocol, inputs from a
# malicious client. Standard library only; it writes only the walk `make` is asked for.

import hashlib
import importlib.util
import json
import math
import os
import re
import struct
import subprocess
import sys
from collections import namedtuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import level  # noqa: E402
import tick_ref as ref  # noqa: E402  the tick: the only thing here that advances a game state


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


arith = _load("bot_ref_arith", "rules_ref.py")   # the rules' atan2 and hypot (RULES-1.md), the bot's arithmetic

FORMAT, VERSION, RULES, POLICY, RUN = "VERDANDI-BOT-TRACE", "1", "1", "walk-1", "the walk"
GIVEN = "bot-ref-walk-1"   # how trace.py names a browser run played from a walk made here
KEYS = {"digest", "format", "manifest", "map", "policy", "route", "rules", "runs", "version"}
RUN_KEYS = {"inputs", "name", "start", "ticks"}
OUT = os.path.join(HERE, "build", "bot")
PI = struct.unpack(">d", bytes.fromhex("400921fb54442d18"))[0]
TWO_PI = 2.0 * PI
INF = math.inf


class BotTraceError(Exception):
    def __init__(self, code, message):
        super().__init__("%s: %s" % (code, message))
        self.code = code


# ------------------------------------------------------------------------------------------------ walk-1's choices
class W1:
    """The policy's numbers (WALK-1.md, What walk-1 assumes)."""
    reach = 0.3                       # a cell is reached within this many metres of its centre
    patience = 180                    # ticks without progress before the walk fails
    progress = 1e-6                   # how much closer counts as progress
    per_cell, spare = 120, 600        # the limit: decisions a path cell, and more
    neighbours = ((1, 0), (-1, 0), (0, 1), (0, -1))
    climb = 0.55                      # the most a path climbs from one cell's top to the next's


def route_order(names):
    """By UTF-16 code units, as JavaScript sorts strings (not quite Python's order above U+FFFF)."""
    return sorted(names, key=lambda n: n.encode("utf-16-be"))


# ------------------------------------------------------------------------------------------------ the plan
class Plan:
    """What the bot knows before it moves: the map, never a state."""

    def __init__(self, conv):
        C, D = conv["collision"], conv["canonical"]
        self.cell = float(C["cell"])
        self.tops = {(i, j): float(C["tops"][j * C["w"] + i]) for j in range(C["h"]) for i in range(C["w"])}
        self.wall = float(D["wall"])
        self.closed = {(t["x"], t["z"]) for t in D["targets"]}
        self.routes = {name: [tuple(p) for p in r["cells"]] for name, r in D["routes"].items()}

    def top(self, c):
        return self.tops.get(c, INF)

    def open(self, c):
        return self.top(c) < self.wall and c not in self.closed

    def leg(self, a, b):
        """From a to b, breadth-first a layer at a time; a cell keeps the cell it was first reached from."""
        came, layer = {a: None}, [a]
        while layer and b not in came:
            following = []
            for c in layer:
                for di, dj in W1.neighbours:
                    n = (c[0] + di, c[1] + dj)
                    if n in came or not self.open(n) or self.top(n) - self.top(c) > W1.climb:
                        continue
                    came[n] = c
                    following.append(n)
            layer = following
        if b not in came:
            return None
        back, c = [], b
        while c is not None:
            back.append(c)
            c = came[c]
        return back[::-1]

    def path(self, name):
        """The route's path, or None and the waypoint no leg reaches."""
        pts = self.routes[name]
        path = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            leg = self.leg(a, b)
            if leg is None:
                return None, b
            path.extend(leg[1:])
        return path, None


# ------------------------------------------------------------------------------------------------ the decisions
Observation = namedtuple("Observation", "x z yaw")   # all the bot is given of the game, before each input
Memory = namedtuple("Memory", "k best still n dist")  # the bot's own state (WALK-1.md, Walking a path)


def wrap(a):
    return math.fmod(math.fmod(a, TWO_PI) + TWO_PI, TWO_PI)


def short_way(d):
    return d - TWO_PI if d > PI else d


def centre(c, size):
    return (c[0] + 0.5) * size, (c[1] + 0.5) * size


def choose(path, size, limit, mem, obs):
    """One decision: an input, or the walk's end, or its failure. It reads the path, its memory and the observation."""
    while True:
        if mem.n >= limit:
            return mem, ("fails", "the limit, %d decisions" % limit)
        if mem.k >= len(path):
            return mem, ("ends", None)
        tx, tz = centre(path[mem.k], size)
        dx, dz = tx - obs.x, tz - obs.z
        dist = arith.xhypot(dx, dz)
        if dist < W1.reach:
            mem = Memory(mem.k + 1, INF, 0, mem.n + 1, None)
            continue
        d = short_way(wrap(arith.xatan2(dx, -dz) - obs.yaw))
        return mem._replace(dist=dist), ("input", {"dyaw": d, "f": True})


def after_tick(mem):
    """The progress a tick made, by the distance measured before it; True when the walk has stalled."""
    if mem.dist < mem.best - W1.progress:
        mem = mem._replace(best=mem.dist, still=0)
    else:
        mem = mem._replace(still=mem.still + 1)
        if mem.still > W1.patience:
            return mem, True
    return mem._replace(n=mem.n + 1, dist=None), False


# ------------------------------------------------------------------------------------------------ the walk
def start_state(world, first):
    s = ref.State.new(world, "A")
    s.x, s.z = centre(first, world.cell)
    s.feet = world.ground(s.x, s.z)
    return s


def walk_path(world, path, tick):
    """The bot and the tick in turn: the start's bytes, the inputs, and how the walk came out."""
    s = start_state(world, path[0])
    start = ref.write_snapshot(s)
    limit = W1.per_cell * len(path) + W1.spare
    mem, inputs = Memory(1, INF, 0, 0, None), []
    while True:
        mem, (what, inp) = choose(path, world.cell, limit, mem, Observation(s.x, s.z, s.yaw))
        if what != "input":
            return start, inputs, what, inp
        inputs.append(inp)
        tick(world, s, inp)
        mem, stalled = after_tick(mem)
        if stalled:
            return start, inputs, "fails", "more than %d ticks without progress" % W1.patience


def make(name, tick=None):
    """The walk of the first route, in order, whose walk ends; and what became of each route tried."""
    tick = tick or ref.tick
    conv = level.convert(name)
    world, plan = ref.World(conv), Plan(conv)
    tried = []
    for route in route_order(plan.routes):
        path, unreached = plan.path(route)
        if path is None:
            tried.append((route, "passed over: no path reaches the waypoint %d,%d" % unreached))
            continue
        start, inputs, what, why = walk_path(world, path, tick)
        if what == "ends":
            tried.append((route, "walked: a path of %d cells, %d ticks" % (len(path), len(inputs))))
            return seal(body(name, conv, route, start, inputs)), tried
        tried.append((route, "the walk failed after %d ticks: %s" % (len(inputs), why)))
    raise BotTraceError("BOT-REF-NO-WALK", "no route of %s can be walked (%s)" % (name, "; ".join("%s %s" % t for t in tried)))


# ------------------------------------------------------------------------------------------------ the trace
def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def encode_input(inp):
    pairs = []
    for k in sorted(inp, key=lambda n: n.encode("utf-16-be")):
        v = inp[k]
        if isinstance(v, bool) or (isinstance(v, str) and not (len(v) == 17 and v[:1] == "f")):
            pairs.append([k, v])
        elif isinstance(v, float):
            pairs.append([k, "f" + struct.pack(">d", v).hex()])
        else:
            raise ValueError("an input's %s is %r" % (k, v))
    return json.dumps(pairs, separators=(",", ":"), ensure_ascii=False)


def decode_input(text):
    pairs = json.loads(text)
    if not isinstance(pairs, list) or not all(isinstance(p, list) and len(p) == 2 and isinstance(p[0], str) for p in pairs):
        raise ValueError("not a list of [field, value] pairs")
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError("the field %s twice" % k)
        if isinstance(v, str) and len(v) == 17 and v[:1] == "f" and re.fullmatch(r"f[0-9a-f]{16}", v):
            v = struct.unpack(">d", bytes.fromhex(v[1:]))[0]
        elif not isinstance(v, (bool, str)):
            raise ValueError("the field %s holds %r" % (k, v))
        out[k] = v
    return out


def body(name, conv, route, start, inputs):
    return {"format": FORMAT, "version": VERSION, "map": name,
            "manifest": {k: conv["manifest"][k] for k in ("canonical_sha256", "collision_sha256")},
            "rules": RULES, "policy": POLICY, "route": route,
            "runs": [{"name": RUN, "start": start, "ticks": len(inputs), "inputs": [encode_input(i) for i in inputs]}]}


def seal(obj):
    b = {k: v for k, v in obj.items() if k != "digest"}
    return dict(b, digest=hashlib.sha256(canon(b).encode("utf-8")).hexdigest())


def to_bytes(T):
    return (canon(T) + "\n").encode("utf-8")


def read(data):
    """A walk's bytes, refused whole unless every rule of WALK-1.md's trace holds: the walk and the map's conversion."""
    try:
        text = data.decode("utf-8")
        T = json.loads(text)
    except (UnicodeDecodeError, ValueError) as e:
        raise BotTraceError("BOT-REF-BYTES", "not JSON in UTF-8 (%s)" % e)
    if not isinstance(T, dict) or T.get("format") != FORMAT or T.get("version") != VERSION:
        raise BotTraceError("BOT-REF-FORMAT", "not a %s %s file (%s)" % (FORMAT, VERSION, "format %r version %r" % (
            T.get("format"), T.get("version")) if isinstance(T, dict) else type(T).__name__))
    if set(T) != KEYS:
        raise BotTraceError("BOT-REF-KEYS", "the keys are %s, not %s" % (sorted(T), sorted(KEYS)))
    if canon(T) + "\n" != text:
        raise BotTraceError("BOT-REF-BYTES", "not written as a walk is written (keys sorted, no spaces, one newline at the end)")
    if not (isinstance(T["digest"], str) and re.fullmatch(r"[0-9a-f]{64}", T["digest"])) or seal(T)["digest"] != T["digest"]:
        raise BotTraceError("BOT-REF-DIGEST", "the digest is not the sha256 of the rest")
    if T["rules"] != RULES:
        raise BotTraceError("BOT-REF-RULES", "rules %r; a walk is of rules %s" % (T["rules"], RULES))
    if T["policy"] != POLICY:
        raise BotTraceError("BOT-REF-POLICY", "policy %r; this is %s" % (T["policy"], POLICY))
    name = T["map"]
    if not (isinstance(name, str) and re.fullmatch(r"[a-z0-9_-]+", name)):
        raise BotTraceError("BOT-REF-MAP", "the map is named %r" % (name,))
    try:
        conv = level.convert(name)
    except (level.MapError, OSError) as e:
        raise BotTraceError("BOT-REF-MAP", "the map %s does not convert here (%s)" % (name, e))
    M = T["manifest"]
    if not isinstance(M, dict) or set(M) != {"canonical_sha256", "collision_sha256"} or any(M[k] != conv["manifest"][k] for k in M):
        raise BotTraceError("BOT-REF-MAP", "the walk's map is not %s as it converts here (canonical %s, collision %s)" % (
            name, conv["manifest"]["canonical_sha256"][:12], conv["manifest"]["collision_sha256"][:12]))
    if not isinstance(T["route"], str) or T["route"] not in conv["canonical"]["routes"]:
        raise BotTraceError("BOT-REF-ROUTE", "%s has no route %r" % (name, T["route"]))
    runs = T["runs"]
    if not (isinstance(runs, list) and len(runs) == 1 and isinstance(runs[0], dict) and set(runs[0]) == RUN_KEYS and runs[0]["name"] == RUN):
        raise BotTraceError("BOT-REF-RUN", "a walk holds one run, %r, with %s" % (RUN, sorted(RUN_KEYS)))
    run = runs[0]
    if type(run["ticks"]) is not int or not isinstance(run["inputs"], list) or run["ticks"] != len(run["inputs"]):
        raise BotTraceError("BOT-REF-TICKS", "ticks %r and %s inputs" % (run["ticks"], len(run["inputs"]) if isinstance(run["inputs"], list) else "no"))
    for n, t in enumerate(run["inputs"]):
        try:
            same = isinstance(t, str) and encode_input(decode_input(t)) == t
        except ValueError:
            same = False
        if not same:
            raise BotTraceError("BOT-REF-INPUT", "the input of tick %d is not written as an input is written: %r" % (n + 1, t))
    try:
        same = isinstance(run["start"], str) and ref.write_snapshot(ref.read_snapshot(run["start"])) == run["start"]
    except (ValueError, KeyError, TypeError, struct.error):
        same = False
    if not same:
        raise BotTraceError("BOT-REF-START", "the start is not written as a snapshot is written")
    return T, conv


def given_runs(T):
    """The walk as trace.py gives runs to a browser."""
    return [{"name": r["name"], "start": r["start"], "inputs": r["inputs"]} for r in T["runs"]]


def given_digest(T):
    return hashlib.sha256(json.dumps(given_runs(T), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


# ------------------------------------------------------------------------------------------------ what a walk is held to
class Held:
    """WALK-1.md, What a walk is held to: the checks' own numbers, apart from the policy's."""
    reach = 0.3
    step = 0.55
    per_cell, spare = 120, 600


def held_inputs(run):
    for n, t in enumerate(run["inputs"]):
        inp = decode_input(t)
        d = inp.get("dyaw")
        if set(inp) != {"dyaw", "f"} or inp["f"] is not True or not isinstance(d, float) or not math.isfinite(d) or not -PI < d <= PI:
            return False, "tick %d: %s" % (n + 1, t)
    return True, "%d inputs, each forward and a turn in (-pi, pi], nothing else" % len(run["inputs"])


def held_path(conv, route, path):
    C, D = conv["collision"], conv["canonical"]
    w, h, tops, wall = C["w"], C["h"], C["tops"], D["wall"]
    targets = {(t["x"], t["z"]) for t in D["targets"]}
    pts = [tuple(p) for p in D["routes"][route]["cells"]]
    if not path:
        return False, "no path"
    if path[0] != pts[0] or path[-1] != pts[-1]:
        return False, "the path runs from %s to %s, the route from %s to %s" % (path[0], path[-1], pts[0], pts[-1])
    at = 0
    for p in pts:
        if p not in path[at:]:
            return False, "the waypoint %s is not on the path after %s" % (p, path[at])
        at = path.index(p, at)
    for i, j in path:
        if not (0 <= i < w and 0 <= j < h):
            return False, "the cell %d,%d is off the grid" % (i, j)
        if not tops[j * w + i] < wall:
            return False, "the cell %d,%d is a wall's height (%s)" % (i, j, tops[j * w + i])
        if (i, j) in targets:
            return False, "the cell %d,%d is a target's" % (i, j)
    for (i, j), (k, l) in zip(path, path[1:]):
        if abs(i - k) + abs(j - l) != 1:
            return False, "from %d,%d to %d,%d is not a step to a neighbour" % (i, j, k, l)
        if tops[l * w + k] - tops[j * w + i] > Held.step:
            return False, "from %d,%d to %d,%d climbs %s" % (i, j, k, l, tops[l * w + k] - tops[j * w + i])
    return True, "%d cells from %s to %s, the route's %d waypoints in order, each step to a neighbour, open and at most %s up" % (
        len(path), pts[0], pts[-1], len(pts), Held.step)


def replay(world, run, tick):
    s = ref.read_snapshot(run["start"])
    out = []
    for t in run["inputs"]:
        tick(world, s, ref.read_input(t))
        out.append((ref.write_snapshot(s), s.x, s.z))
    return out


def held_walk(world, conv, route, run, path_len, tick):
    pts = [tuple(p) for p in conv["canonical"]["routes"][route]["cells"]]
    c = world.cell
    s = ref.read_snapshot(run["start"])
    places = [(s.x, s.z)] + [(x, z) for _snap, x, z in replay(world, run, tick)]
    at = 0
    for x, z in places:
        cur = (int(math.floor(x / c)), int(math.floor(z / c)))
        while at < len(pts) and cur == pts[at]:
            at += 1
    tx, tz = (pts[-1][0] + 0.5) * c, (pts[-1][1] + 0.5) * c
    end = ref.hypot(tx - places[-1][0], tz - places[-1][1])
    limit = Held.per_cell * path_len + Held.spare
    ok = at == len(pts) and end < Held.reach and len(run["inputs"]) < limit
    return ok, "%d of %d waypoints' cells stood in, in order; the end %.3f m from the last waypoint's centre (under %s); %d ticks (under %d)" % (
        at, len(pts), end, Held.reach, len(run["inputs"]), limit)


def first_input_difference(a, b):
    for n, (x, y) in enumerate(zip(a, b)):
        if x != y:
            ia, ib = decode_input(x), decode_input(y)
            keys = sorted(set(ia) | set(ib))
            return n + 1, ["%s: %s and %s" % (k, ia.get(k), ib.get(k)) for k in keys if ia.get(k) != ib.get(k)]
    if len(a) != len(b):
        return min(len(a), len(b)) + 1, ["%d inputs and %d" % (len(a), len(b))]
    return None, []


def held(T, conv, data, tick=None):
    """The rows a read walk is held to: made again here the same, and what a walk is for."""
    tick = tick or ref.tick
    rows, run = [], T["runs"][0]
    world, plan = ref.World(conv), Plan(conv)
    try:
        mine, _tried = make(T["map"], tick)
        same = to_bytes(mine) == data
        if same:
            detail = "the same bytes, digest %s" % mine["digest"][:16]
        elif mine["route"] != T["route"] or mine["runs"][0]["start"] != run["start"]:
            detail = "here the route %s from %s" % (mine["route"], "the same start" if mine["runs"][0]["start"] == run["start"] else "another start")
        else:
            n, fields = first_input_difference(mine["runs"][0]["inputs"], run["inputs"])
            detail = "FIRST DIFFERENT at tick %s: %s" % (n, "; ".join(fields)) if n else "the same inputs, other bytes"
    except BotTraceError as e:
        same, detail = False, str(e)
    rows.append(("made again here", same, detail))
    rows.append(("held: the inputs",) + held_inputs(run))
    path, _unreached = plan.path(T["route"])
    rows.append(("held: the path",) + held_path(conv, T["route"], path))
    rows.append(("held: the walk",) + (held_walk(world, conv, T["route"], run, len(path), tick) if path else (False, "no path")))
    return rows


# ------------------------------------------------------------------------------------------------ beside a browser's trace
def _trace_module():
    return _load("bot_ref_trace", "trace.py")


def against(T, conv, B, tick=None, label="the browser"):
    """The walk beside a browser trace's walk: the map, the start, each input, and each state as the Python tick makes it."""
    tick = tick or ref.tick
    rows, run = [], T["runs"][0]
    bm = B.get("manifest") or {}
    same_map = B.get("map") == T["map"] and all(bm.get(k) == T["manifest"][k] for k in T["manifest"])
    rows.append(("the map", same_map, "%s, the trace's %s" % (T["map"], B.get("map"))))
    theirs = [r for r in B["rules"]["1"]["runs"] if r["name"] == RUN]
    if not same_map or not theirs:
        if same_map:
            rows.append(("the browser's walk", False, "the trace holds no run %r under rules 1" % RUN))
        return rows
    W = theirs[0]
    src = B.get("inputs_from")
    if not src:
        made = "recorded by the browser's own bot (sim.js), not given"
    elif src.get("engine") == GIVEN and src.get("inputs") == given_digest(T):
        made = "played from this walk's inputs, given to it"
    else:
        made = "played from the runs of %s, given to it" % src.get("engine")
    rows.append(("the browser's walk", True, "%d ticks, %s" % (len(W["inputs"]), made)))
    rows.append(("the start", W["start"] == run["start"], "the same bytes" if W["start"] == run["start"] else "NOT the same bytes"))
    n, fields = first_input_difference(run["inputs"], W["inputs"])
    rows.append(("the inputs", n is None, "the same at every tick (%d)" % len(run["inputs"]) if n is None else
                 "FIRST DIFFERENT at tick %d: %s (here, then %s)" % (n, "; ".join(fields), label)))
    world = ref.World(conv)
    mine = [snap for snap, _x, _z in replay(world, run, tick)]
    diff = None
    for k, (a, b) in enumerate(zip(mine, W["snaps"])):
        if a != b:
            fa, fb = ref.fields_of(a), ref.fields_of(b)
            diff = (k + 1, [(f, fa.get(f), fb.get(f)) for f in sorted(set(fa) | set(fb)) if fa.get(f) != fb.get(f)])
            break
    if diff is None and len(mine) != len(W["snaps"]):
        diff = (min(len(mine), len(W["snaps"])) + 1, [("the number of ticks", str(len(mine)), str(len(W["snaps"])))])
    rows.append(("the states, the Python tick on this walk's inputs against %s's snapshots" % label, diff is None,
                 "every snapshot the same bytes (%d)" % len(mine) if diff is None else "FIRST DIFFERENT at tick %d, in %s" % (
                     diff[0], "; ".join("%s: here %s, %s %s%s" % (f, ref.show(a) if a is not None else "-", label, ref.show(b) if b is not None else "-",
                                        (", %d ulp" % ref.ulps(a, b)) if isinstance(a, str) and isinstance(b, str) and a[:1] == b[:1] == "f" and len(a) == len(b) == 17 else "")
                                        for f, a, b in diff[1][:6]))))
    return rows


# ------------------------------------------------------------------------------------------------ commands
def show_rows(rows):
    for name, ok, detail in rows:
        print("%s %s — %s" % ("PASS" if ok else "FAIL", name, detail))
    return all(r[1] for r in rows)


def cmd_make(name, out):
    if not re.fullmatch(r"[a-z0-9_-]+", name):
        print("BOT-REF: a map's name is lower-case letters, digits, - and _", file=sys.stderr)
        return 2
    log = sys.stderr if out == "-" else sys.stdout
    try:
        T, tried = make(name)
    except BotTraceError as e:
        print("BOT-REF  %s" % e, file=sys.stderr)
        return 1
    except (level.MapError, OSError) as e:
        print("BOT-REF-MAP: %s" % e, file=sys.stderr)
        return 2
    data = to_bytes(T)
    print("BOT-REF  map %s  policy %s  rules %s  (canonical %s, collision %s)" % (
        name, POLICY, RULES, T["manifest"]["canonical_sha256"][:12], T["manifest"]["collision_sha256"][:12]), file=log)
    for route, what in tried:
        print("  route %-8s %s" % (route, what), file=log)
    if out == "-":
        sys.stdout.buffer.write(data)
        sys.stdout.flush()
        return 0
    path = out or os.path.join(OUT, "%s-walk.json" % name)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)
    print("WALK MADE  route %s, %d ticks, digest %s, sha256 of the file %s" % (
        T["route"], T["runs"][0]["ticks"], T["digest"][:16], hashlib.sha256(data).hexdigest()[:16]))
    print("written %s" % path)
    return 0


def read_file(path):
    with open(path, "rb") as fh:
        data = fh.read()
    T, conv = read(data)
    return T, conv, data


def cmd_check(path):
    try:
        T, conv, data = read_file(path)
    except BotTraceError as e:
        print("BOT TRACE REFUSED  %s" % e)
        return 1
    run = T["runs"][0]
    print("BOT-REF  %s  map %s  policy %s  rules %s  route %s  %d ticks" % (os.path.basename(path), T["map"], T["policy"], T["rules"], T["route"], run["ticks"]))
    rows = [("the trace reads", True, "the map's identity as it converts here (canonical %s, collision %s), the start, every input, the digest %s" % (
        T["manifest"]["canonical_sha256"][:12], T["manifest"]["collision_sha256"][:12], T["digest"][:16]))]
    rows += held(T, conv, data)
    ok = show_rows(rows)
    print("BOT TRACE %s" % ("CHECKED" if ok else "FAILED"))
    return 0 if ok else 1


def cmd_compare(bot_path, trace_path):
    try:
        T, conv, _data = read_file(bot_path)
    except BotTraceError as e:
        print("BOT TRACE REFUSED  %s" % e)
        return 1
    B = ref.load_trace(trace_path)
    tm = _trace_module()
    rt = B.get("runtime") or {}
    print("BOT-REF COMPARE  %s against %s" % (os.path.basename(bot_path), os.path.basename(trace_path)))
    print("the walk   map %s, policy %s, rules %s, route %s, %d ticks" % (T["map"], T["policy"], T["rules"], T["route"], T["runs"][0]["ticks"]))
    print("the trace  %s, engine family %s: %s" % (tm.engine_tag(rt), tm.engine_family(rt), rt.get("userAgent", "?")))
    ok = show_rows(against(T, conv, B))
    print("BOT TRACE %s THE BROWSER'S WALK  (%s)" % ("AGREES WITH" if ok else "DIFFERS FROM", tm.engine_tag(rt)))
    return 0 if ok else 1


# ------------------------------------------------------------------------------------------------ the self-test
class patched:
    def __init__(self, obj, attr, value):
        self.obj, self.attr, self.value = obj, attr, value

    def __enter__(self):
        self.saved = getattr(self.obj, self.attr)
        setattr(self.obj, self.attr, self.value)

    def __exit__(self, *exc):
        setattr(self.obj, self.attr, self.saved)


def flip_last_bit(v):
    b = struct.unpack(">Q", struct.pack(">d", v))[0] ^ 1
    return struct.unpack(">d", struct.pack(">Q", b))[0]


def perturbed_tick(at):
    """The reference tick with one result perturbed: x one bit off at the tick named."""
    def tick(world, s, inp):
        ref.tick(world, s, inp)
        if s.tick == float(at):
            s.x = flip_last_bit(s.x)
    return tick


def resealed(T, change):
    U = json.loads(canon(T))
    change(U)
    return to_bytes(seal(U))


def refused(data):
    try:
        read(data)
    except BotTraceError as e:
        return e.code
    return None


def _start_facing_north(world, first):
    s = _start_state(world, first)
    s.yaw = 0.0
    return s


_start_state = start_state
_PLAIN = type("plain", (), {"xhypot": staticmethod(lambda a, b: math.sqrt(a * a + b * b)), "xatan2": staticmethod(arith.xatan2)})
_PLATFORM = type("platform", (), {"xhypot": staticmethod(arith.xhypot), "xatan2": staticmethod(math.atan2)})


def policy_plants():
    """Defects a second implementation of the policy could have, each required to change the walk (found against the
    browser's walk or by what a walk is held to); and, apart, choices of walk-1 this walk does not exercise or defects
    it absorbs, reported and not required (the platform's atan2 depends on the machine's C library)."""
    here = sys.modules[__name__]
    required = [
        ("a cell reached within 0.35 m, not 0.3", W1, "reach", 0.35),
        ("the neighbours searched z before x", W1, "neighbours", ((0, 1), (0, -1), (1, 0), (-1, 0))),
        ("the turn not taken the short way", here, "short_way", lambda d: d),
        ("the routes in reverse order", here, "route_order", lambda names: sorted(names, reverse=True)),
        ("a climb of up to 1.0 m planned", W1, "climb", 1.0),
        ("the start facing north, not as spawn A", here, "start_state", _start_facing_north),
    ]
    noted = [
        ("the neighbours searched -x before +x", W1, "neighbours", ((-1, 0), (1, 0), (0, 1), (0, -1))),
        ("the targets' cells left open", Plan, "open", lambda self, c: self.top(c) < self.wall),
        ("a stall after 18 ticks, not 180", W1, "patience", 18),
        ("the distance by the plain root of the sum, sqrt(dx*dx + dz*dz)", here, "arith", _PLAIN),
        ("the platform's atan2 (CPython's math.atan2)", here, "arith", _PLATFORM),
    ]
    return required, noted


def form_apart(data):
    """The file's form as WALK-1.md states it, checked without the writer's code: keys in order at every level, the
    digest the sha256 of the text with its own member taken out, one newline at the end."""
    text = data.decode("utf-8")
    orders = []
    json.loads(text, object_pairs_hook=lambda pairs: orders.append([k for k, _v in pairs]) or dict(pairs))
    unsorted = [o for o in orders if o != sorted(o, key=lambda n: n.encode("utf-16-be"))]
    m = re.match(r'\{"digest":"([0-9a-f]{64})",', text)
    if not m or not text.endswith("}\n") or text.count("\n") != 1:
        return False, "it does not begin with the digest and end with one newline"
    rest = "{" + text[m.end():-1]
    ok = not unsorted and hashlib.sha256(rest.encode("utf-8")).hexdigest() == m.group(1)
    return ok, "%d objects, each with its keys in order%s; the digest the sha256 of the rest of the text: %s" % (
        len(orders), "" if not unsorted else " but %s" % unsorted[0], "yes" if hashlib.sha256(rest.encode("utf-8")).hexdigest() == m.group(1) else "NO")


def cmd_selftest(trace_path):
    B = ref.load_trace(trace_path)
    name = B.get("map", "")
    rows = []

    def found(label, ok, detail):
        rows.append((label, ok, detail))

    T, _tried = make(name)
    data = to_bytes(T)
    conv = level.convert(name)
    found("the walk's form, read apart from the writer", *form_apart(data))
    # the same bytes from fresh processes, under other hash seeds
    seeds = []
    for seed in ("0", "4242"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        p = subprocess.run([sys.executable, os.path.abspath(__file__), "make", name, "--out", "-"], env=env, capture_output=True)
        seeds.append((seed, p.returncode == 0 and p.stdout == data))
    found("made three times, the same bytes", all(ok for _s, ok in seeds), "here and in two fresh processes (PYTHONHASHSEED %s): %s; sha256 %s" % (
        " and ".join(s for s, _ok in seeds), ", ".join("the same" if ok else "DIFFERENT" for _s, ok in seeds), hashlib.sha256(data).hexdigest()[:16]))
    try:
        read(data)
        found("the walk made reads", True, "route %s, %d ticks" % (T["route"], T["runs"][0]["ticks"]))
    except BotTraceError as e:
        found("the walk made reads", False, str(e))
    for label, ok, detail in held(T, conv, data):
        found("the walk made: " + label, ok, detail)
    base = against(T, conv, B)
    for label, ok, detail in base:
        found("against the trace: " + label, ok, detail)
    if not all(r[1] for r in base):
        return finish(rows)
    W = [r for r in B["rules"]["1"]["runs"] if r["name"] == RUN][0]

    # plants in the policy: found against the browser's walk, or by what a walk is held to
    notes = []
    required_plants, noted_plants = policy_plants()
    for plants, required in ((required_plants, True), (noted_plants, False)):
        for label, obj, attr, value in plants:
            with patched(obj, attr, value):
                try:
                    M, _t = make(name)
                    mrows = against(M, conv, B) + held(M, conv, to_bytes(M))[1:]
                    where = [r[0].split(",")[0] + " (" + r[2][:90] + ")" for r in mrows if not r[1]]
                except BotTraceError as e:
                    where = ["no walk made (%s)" % e.code]
            detail = "found: " + "; ".join(where[:3]) if where else "NOT found: the same walk"
            if required:
                found("plant in the policy: " + label, bool(where), detail)
            else:
                notes.append("NOTE plant in the policy, not required: %s — %s" % (label, "found: " + "; ".join(where[:1]) if where else "the same walk, byte for byte"))

    # one byte of an input changed: the digest refuses it; resealed, it is made again otherwise and the browser's differs
    run = T["runs"][0]
    k = min(299, len(run["inputs"]) - 1)
    tampered = run["inputs"][k]
    i = tampered.index('"f') + 17
    tampered = tampered[:i] + "%x" % (int(tampered[i], 16) ^ 1) + tampered[i + 1:]
    raw = data.replace(run["inputs"][k].replace('"', '\\"').encode("utf-8"), tampered.replace('"', '\\"').encode("utf-8"), 1)
    code = refused(raw)
    found("plant: one byte of tick %d's input changed" % (k + 1), code == "BOT-REF-DIGEST", "refused: %s" % code)

    def change_input(U):
        U["runs"][0]["inputs"][k] = tampered
    raw = resealed(T, change_input)
    U, _c = read(raw)
    again = held(U, conv, raw)[0]
    side = first_input_difference(U["runs"][0]["inputs"], W["inputs"])[0]
    states = against(U, conv, B)[-1]
    found("plant: the same, its digest made again", again[1] is False and "tick %d" % (k + 1) in again[2] and side == k + 1,
          "made again here: %s; against the browser's walk: the inputs first differ at tick %s; the states: %s" % (
              again[2][:60], side, "the same at every tick (the change absorbed)" if states[1] else states[2][:70]))

    # the map's identity
    def other_digest(U):
        h = U["manifest"]["canonical_sha256"]
        U["manifest"]["canonical_sha256"] = h[:-1] + ("0" if h[-1] != "0" else "1")

    def other_map(U):
        U["map"] = "witness" if name != "witness" else "tactical"
    for label, change in (("the map's digest changed", other_digest), ("the map's name changed, its digests kept", other_map)):
        code = refused(resealed(T, change))
        found("plant: " + label, code == "BOT-REF-MAP", "refused: %s" % code)

    # the file's form
    def add_key(U):
        U["note"] = "x"

    def set_(key, value):
        def f(U):
            U[key] = value
        return f

    def run_set(key, fn):
        def f(U):
            U["runs"][0][key] = fn(U["runs"][0][key])
        return f
    forms = [
        ("a space after the first comma", data.replace(b",", b", ", 1), "BOT-REF-BYTES"),
        ("a key added", resealed(T, add_key), "BOT-REF-KEYS"),
        ("version 2", resealed(T, set_("version", "2")), "BOT-REF-FORMAT"),
        ("rules 0", resealed(T, set_("rules", "0")), "BOT-REF-RULES"),
        ("policy walk-2", resealed(T, set_("policy", "walk-2")), "BOT-REF-POLICY"),
        ("a route the map lacks", resealed(T, set_("route", "nowhere")), "BOT-REF-ROUTE"),
        ("the run renamed", resealed(T, run_set("name", lambda v: "the fight")), "BOT-REF-RUN"),
        ("one tick more than the inputs", resealed(T, run_set("ticks", lambda v: v + 1)), "BOT-REF-TICKS"),
        ("an input's fields out of order", resealed(T, run_set("inputs", lambda v: [json.dumps(json.loads(v[0])[::-1], separators=(",", ":"))] + v[1:])), "BOT-REF-INPUT"),
        ("the start without its yaw", resealed(T, run_set("start", lambda v: json.dumps({a: b for a, b in json.loads(v).items() if a != "yaw"}, separators=(",", ":")))), "BOT-REF-START"),
    ]
    for label, raw, want in forms:
        code = refused(raw)
        found("plant: " + label, code == want, "refused: %s" % code)

    # a tick's result perturbed: x one bit off at tick 1000 of the reference tick
    at = min(1000, len(run["inputs"]))
    tick = perturbed_tick(at)
    r = against(T, conv, B, tick=tick)[-1]
    found("plant: the Python tick's x one bit off at tick %d" % at, (not r[1]) and ("at tick %d, in x:" % at) in r[2], r[2][:110])
    try:
        P, _t = make(name, tick=tick)
        n = first_input_difference(P["runs"][0]["inputs"], W["inputs"])[0]
        detail = "the walk made with it: its inputs %s" % ("the same at every tick (the bot's decisions absorbed it)" if n is None else "first differ at tick %d" % n)
    except BotTraceError as e:
        detail = "no walk made with it (%s)" % e.code
    found("plant: the same, while the walk is made", True, detail + " (an observation, not a requirement)")

    # walks that break what a walk is held to, each caught by that check alone
    def turn_at(v):
        out = list(v)
        out[min(499, len(out) - 1)] = encode_input({"dyaw": 3.5, "f": True})
        return out

    def fire_at(v):
        out = list(v)
        inp = decode_input(out[min(499, len(out) - 1)])
        inp["fire"] = True
        out[min(499, len(out) - 1)] = encode_input(inp)
        return out

    def cut(U):
        U["runs"][0]["inputs"] = U["runs"][0]["inputs"][:-5]
        U["runs"][0]["ticks"] = len(U["runs"][0]["inputs"])
    others = [r for r in route_order(Plan(conv).routes) if r != T["route"] and Plan(conv).routes[r][0] == Plan(conv).routes[T["route"]][0]
              and Plan(conv).routes[r][-1] == Plan(conv).routes[T["route"]][-1]]
    plants = [("a turn of 3.5 rad", resealed(T, run_set("inputs", turn_at)), "held: the inputs"),
              ("a shot in the walk", resealed(T, run_set("inputs", fire_at)), "held: the inputs"),
              ("the last 5 ticks cut, the last waypoint's cell reached", resealed(T, cut), "held: the walk")]
    if others:
        with patched(sys.modules[__name__], "route_order", lambda names: [others[0]]):
            O, _t = make(name)

        def named(U):
            U["route"] = T["route"]
        plants.append(("the %s route's walk, named %s (the same ends)" % (others[0], T["route"]), resealed(O, named), "held: the walk"))
    for label, raw, row in plants:
        U, _c = read(raw)
        got = dict((r[0], r) for r in held(U, conv, raw))[row]
        found("plant in a walk: " + label, not got[1], "%s refuses it: %s" % (row, got[2][:90]))

    # a start wrong only where the first tick writes over it: the states cannot show it, the start's bytes do
    def start_on_objective(v):
        d = json.loads(v)
        d["onObjective"] = True
        return json.dumps(d, separators=(",", ":"))
    raw = resealed(T, run_set("start", start_on_objective))
    U, _c = read(raw)
    got = dict((r[0], r) for r in against(U, conv, B))
    states = [r for k, r in got.items() if k.startswith("the states")][0]
    found("plant: the start's onObjective true, overwritten at tick 1", not got["the start"][1] and states[1],
          "the start: %s; the states: %s" % (got["the start"][2], "the same at every tick" if states[1] else states[2][:60]))
    with patched(Plan, "open", lambda self, c: self.top(c) < INF and c not in self.closed), patched(W1, "climb", INF):
        p, _u = Plan(conv).path(T["route"])
    ok, detail = held_path(conv, T["route"], p)
    found("plant in a walk: a path planned through walls and over any height", not ok, "held: the path refuses it: %s" % detail[:90])
    return finish(rows, notes)


def finish(rows, notes=()):
    ok = show_rows(rows)
    for line in notes:
        print(line)
    print("BOT-REF SELFTEST %s" % ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


def main(argv):
    if len(argv) in (2, 4) and argv[0] == "make" and (len(argv) == 2 or argv[2] == "--out"):
        return cmd_make(argv[1], argv[3] if len(argv) == 4 else None)
    if len(argv) == 2 and argv[0] == "check":
        return cmd_check(argv[1])
    if len(argv) == 3 and argv[0] == "compare":
        return cmd_compare(argv[1], argv[2])
    if len(argv) == 2 and argv[0] == "selftest":
        return cmd_selftest(argv[1])
    print("usage: python graybox/bot_ref.py make MAP [--out FILE | --out -] | check BOT.json | compare BOT.json TRACE.json | selftest TRACE.json",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
