# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# graybox/ort_ref.py — ORT-1 (graybox/ORT-1.md, 0227) in Python, written from the document apart from graybox/web/ort.js:
# a rules-2 world's origin moved between two ticks, as a transition bound to the exact state it was prepared from.
#
#   python graybox/ort_ref.py                  the table (web/ort_cases.json) played here: held to the values worked by
#                                              hand, every committed rebase held to conservation with exact fractions,
#                                              and the plants, each refused with its own code
#   python graybox/ort_ref.py RESULTS.json     and then a browser's run of the same table (trace.py run --ort) held to
#                                              the worked values and to this one, byte for byte
#
# Three answers, by his review of ORT-0 (2026-10-14): the values worked by hand (fixed before either program ran), this
# program, and ort.js in a browser. The expected state after a rebase is built here from the state before it and the
# hand-worked numbers, never from either program's rebase. Standard library only.

import json
import math
import os
import struct
import sys
from fractions import Fraction
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import level  # noqa: E402
import tick_ref as T  # noqa: E402

FORMAT, EVENT, RECEIPT = "VERDANDI-ORT 1", "VERDANDI-ORT-EVENT 1", "VERDANDI-ORT-RECEIPT 1"
ORIGIN_MAX, TICK_MAX = 1 << 20, (1 << 53) - 1
NONE = "0" * 64
CASES = os.path.join(HERE, "web", "ort_cases.json")

# the frame table: every leaf of the snapshot ('*' an index), moved along x, along z, or not ('-')
FRAME = {"x": "x", "z": "z", "targets.*.x": "x", "targets.*.z": "z",
         "cooldown": "-", "feet": "-", "movers.*.phase": "-", "movers.*.stopped": "-", "onGround": "-", "onObjective": "-",
         "pitch": "-", "score": "-", "shots": "-", "side": "-", "targets.*.downFor": "-", "targets.*.id": "-", "targets.*.up": "-",
         "targets.*.y": "-", "tick": "-", "vy": "-", "yaw": "-"}
# where each moved leaf lives in the Python state
ATTR = {"x": "x", "z": "z"}
# the world's own fields, each declared: global (read through the origin), the origin, the movers (local, moved), or
# made from the rest; a field not named here refuses (ORT-UNDECLARED)
WORLD = {"cell": "global", "conv": "global", "h": "global", "identity": "made", "identity_state": "made", "movers": "moved",
         "objective": "global", "oi": "origin", "oj": "origin", "rows": "global", "spawns": "global", "target_cells": "global",
         "w": "global"}


class Refused(Exception):
    def __init__(self, code, why):
        Exception.__init__(self, "%s: %s" % (code, why))
        self.code, self.why = code, why


def sha(b):
    return hashlib.sha256(b).hexdigest()


def basis_bytes(world, s):
    """VERDANDI-ORT 1, then the world's identity and the state's snapshot, each framed by its byte count."""
    ident, snap = world.identity.encode("utf-8"), T.write_snapshot2(s).encode("utf-8")
    return b"%s\nidentity %d\n%s\nstate %d\n%s\n" % (FORMAT.encode("ascii"), len(ident), ident, len(snap), snap)


def digest(world, s):
    return sha(basis_bytes(world, s))


def leaves(v, path=()):
    if isinstance(v, dict):
        out = []
        for k in sorted(v):
            out += leaves(v[k], path + (k,))
        return out
    if isinstance(v, list):
        out = []
        for i, x in enumerate(v):
            out += leaves(x, path + (i,))
        return out
    return [path]


def frame_of(path, frame):
    return frame.get(".".join("*" if isinstance(k, int) else k for k in path))


def exact_sub(p, d):
    """(p - d, whether it is exact): the subtraction's rounding error by TwoSum, 0 when exact."""
    r = p - d
    bb = r - p
    err = (p - (r - bb)) + (-d - bb)
    return r, err == 0 and math.isfinite(r)


def whole(v, lo, hi):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v == math.floor(v) and lo <= v <= hi


def event_fault(e):
    if not isinstance(e, dict):
        return "the event is not a record"
    if sorted(e) != ["di", "dj", "tick"]:
        return "the event's fields are %s, not di, dj and tick" % sorted(e)
    if not whole(e["tick"], 0, TICK_MAX):
        return "its tick is not a whole number from 0"
    if not whole(e["di"], -ORIGIN_MAX, ORIGIN_MAX) or not whole(e["dj"], -ORIGIN_MAX, ORIGIN_MAX):
        return "di and dj are not whole numbers of cells, each at most 2^20"
    return None


def dec(v):
    return "%d" % int(v)


def event_bytes(e):
    return "%s\ntick %s\ndi %s\ndj %s\n" % (EVENT, dec(e["tick"]), dec(e["di"]), dec(e["dj"]))


def copy_state(s):
    """A copy of every slot the state has (whatever slots it gains), its targets and movers copied too."""
    t = T.State2()
    for k in T.State.__slots__ + T.State2.__slots__:
        v = getattr(s, k)
        if k == "targets":
            v = [T.Target(g.id, g.x, g.y, g.z, g.up, g.down_for) for g in v]
        elif k == "movers":
            v = [T.MoverState(m.phase, m.stopped) for m in v]
        setattr(t, k, v)
    return t


def get_leaf(s, path):
    if path[0] == "targets":
        return getattr(s.targets[path[1]], path[2])
    return getattr(s, ATTR[path[0]])


def set_leaf(s, path, v):
    if path[0] == "targets":
        setattr(s.targets[path[1]], path[2], v)
    else:
        setattr(s, ATTR[path[0]], v)


class Owner:
    """The tick owner: one published record of its world, its state and its movers, replaced whole; its receipts and
    the id of the last (the history a transition must have been prepared at). Single-threaded."""

    def __init__(self, world, s, movers):
        self.cur, self.seq, self.last, self.receipts, self.committed = (world, s, movers), 0, NONE, [], set()

    world = property(lambda self: self.cur[0])
    state = property(lambda self: self.cur[1])
    movers = property(lambda self: self.cur[2])

    def step(self, inp):
        T.tick2(self.cur[0], self.cur[1], inp)


class Prepared:
    __slots__ = ("tick", "prev", "pre", "post", "event", "receipt", "id", "world", "state", "movers")


def prepare(ow, event, frame=FRAME, guard=True, selfcheck=True, extra=None):
    """A candidate transition, or Refused. Writes nothing: the owner's world and state are only read."""
    world, s = ow.world, ow.state
    if not isinstance(world, T.World2):
        raise Refused("ORT-RULES", "the world is not a rules-2 world")
    if not (world.cell == math.floor(world.cell) and 1 <= world.cell <= 64):
        raise Refused("ORT-CELL", "the cell is %r m, not a whole number of metres from 1 to 64" % world.cell)
    f = event_fault(event)
    if f:
        raise Refused("ORT-EVENT", f)
    if event["tick"] != s.tick:
        raise Refused("ORT-STALE-TICK", "the event is for tick %s; the state is at tick %s" % (event["tick"], s.tick))
    oi, oj = world.oi + int(event["di"]), world.oj + int(event["dj"])
    if abs(oi) > ORIGIN_MAX or abs(oj) > ORIGIN_MAX:
        raise Refused("ORT-ORIGIN", "the origin would be %d, %d: beyond 2^20 cells" % (oi, oj))
    snap = json.loads(T.write_snapshot2(s))
    paths = leaves(snap)
    for p in paths:
        if frame_of(p, frame) is None:
            raise Refused("ORT-UNDECLARED", "the state's leaf %s is not in the frame table" % ".".join(str(k) for k in p))
    for k in sorted(vars(world)):
        if k not in WORLD:
            raise Refused("ORT-UNDECLARED", "the world's field %s is not in the frame table" % k)
    dx, dz = float(event["di"]) * world.cell, float(event["dj"]) * world.cell
    moved = []
    for p in paths:
        f = frame_of(p, frame)
        if f == "-":
            continue
        v = get_leaf(s, p)
        r, ok = exact_sub(v, dx if f == "x" else dz)
        if guard and not ok:
            raise Refused("ORT-INEXACT", "the state's %s = %r less %r m is not a double" % (".".join(str(k) for k in p), v, dx if f == "x" else dz))
        moved.append((p, r))
    movers = []
    for m in ow.movers:
        b = list(m["box"])
        for i, d in ((0, dx), (3, dx), (2, dz), (5, dz)):
            r, ok = exact_sub(float(b[i]), d)
            if guard and not ok:
                raise Refused("ORT-INEXACT", "the mover %s's box[%d] less %r m is not a double" % (m["id"], i, d))
            b[i] = r
        movers.append(dict(m, box=b))
    try:
        world2 = T.World2(world.conv, movers, (oi, oj))
    except T.MoverRefused as e:
        raise Refused("ORT-MOVER" if str(e).startswith("RULES2-MOVER") else "ORT-WORLD", str(e))
    s2 = copy_state(s)
    for p, v in moved:
        set_leaf(s2, p, v)
    if extra:   # a plant: a transform that also moves what it should not
        extra(s2)
    # the candidate held to what it should be: every leaf the old one's, but the moved ones, each moved as computed
    if selfcheck:
        want = {".".join(str(k) for k in p): "f" + struct.pack(">d", v).hex() for p, v in moved}
        snap2 = json.loads(T.write_snapshot2(s2))
        paths2 = leaves(snap2)
        if paths2 != paths:
            raise Refused("ORT-SELF", "the candidate's leaves are not the state's")
        for p in paths:
            a, b = snap, snap2
            for k in p:
                a, b = a[k], b[k]
            key = ".".join(str(k) for k in p)
            if (b != want[key]) if key in want else (a != b):
                raise Refused("ORT-SELF", "the candidate's %s is not what the rebase computed" % key)
    P = Prepared()
    P.tick, P.prev, P.pre, P.post = s.tick, ow.last, digest(world, s), digest(world2, s2)
    P.event = event_bytes(event)
    P.receipt = "%s\nseq %d\nprev %s\ntick %s\npre %s\nevent %s\npost %s\n" % (RECEIPT, ow.seq + 1, ow.last, dec(event["tick"]), P.pre,
                                                                         sha(P.event.encode("ascii")), P.post)
    P.id = sha(P.receipt.encode("ascii"))
    P.world, P.state, P.movers = world2, s2, movers
    return P


def commit(ow, P, check_basis=True, check_replay=True, check_history=True, check_candidate=True):
    if check_replay and P.id in ow.committed:
        raise Refused("ORT-REPLAY", "this transition was committed already")
    if ow.state.tick != P.tick:
        raise Refused("ORT-STALE-TICK", "prepared at tick %s; the owner is at tick %s" % (P.tick, ow.state.tick))
    if check_basis and digest(ow.world, ow.state) != P.pre:
        raise Refused("ORT-STALE-BASIS", "prepared from another basis")
    # the same bytes are not the same basis: a world moved there and back has its old bytes and a longer history (ABA)
    if check_history and ow.last != P.prev:
        raise Refused("ORT-STALE-BASIS", "prepared after another history")
    lines = P.receipt.split("\n")
    if check_candidate and (sha(P.receipt.encode("ascii")) != P.id or digest(P.world, P.state) != P.post or lines[2] != "prev " + P.prev
                            or lines[4] != "pre " + P.pre or lines[6] != "post " + P.post):
        raise Refused("ORT-TAMPERED", "the candidate or its receipt is not what was prepared")
    ow.cur = (P.world, P.state, P.movers)   # one assignment: the world and the state together, between two ticks
    ow.seq += 1
    ow.last = P.id
    ow.receipts.append(P.receipt)
    ow.committed.add(P.id)
    return P.receipt


# ------------------------------------------------------------------------------------------------ conservation, exactly
def conserved(w0, s0, w1, s1):
    """Every moved leaf's global position, origin * cell + local, before and after, in exact fractions; None if all
    are equal, or the first that is not."""
    c = Fraction(w0.cell)
    pairs = [("x", w0.oi, w1.oi, s0.x, s1.x), ("z", w0.oj, w1.oj, s0.z, s1.z)]
    for k, (a, b) in enumerate(zip(s0.targets, s1.targets)):
        pairs += [("targets.%d.x" % k, w0.oi, w1.oi, a.x, b.x), ("targets.%d.z" % k, w0.oj, w1.oj, a.z, b.z)]
    for k, (m0, m1) in enumerate(zip(w0.movers, w1.movers)):
        pairs += [("movers.%d.x0" % k, w0.oi, w1.oi, m0.x0, m1.x0), ("movers.%d.x1" % k, w0.oi, w1.oi, m0.x1, m1.x1),
                  ("movers.%d.z0" % k, w0.oj, w1.oj, m0.z0, m1.z0), ("movers.%d.z1" % k, w0.oj, w1.oj, m0.z1, m1.z1)]
    for what, o0, o1, p0, p1 in pairs:
        if o0 * c + Fraction(p0) != o1 * c + Fraction(p1):
            return what
    return None


# ------------------------------------------------------------------------------------------------ the table
SET = {"x": "x", "z": "z", "feet": "feet", "onGround": "on_ground", "vy": "vy", "yaw": "yaw", "pitch": "pitch"}


def play(conv, case, frame=FRAME, guard=True, check_basis=True, check_replay=True, mutate=False, check_history=True, check_candidate=True,
         selfcheck=True, extra=None):
    pk = dict(frame=frame, guard=guard, selfcheck=selfcheck, extra=extra)
    ck = dict(check_basis=check_basis, check_replay=check_replay, check_history=check_history, check_candidate=check_candidate)
    r = {"name": case["name"], "snaps": [], "hashes": [], "events": []}
    try:
        movers = case.get("movers") or []
        world = T.World2(conv, movers)
        s = T.State2.new(world, (case.get("start") or {}).get("side", "A"))
        for k, v in sorted(((case.get("start") or {}).get("set") or {}).items()):
            setattr(s, SET[k], v if isinstance(v, bool) else float(v))
        ow = Owner(world, s, [dict(m) for m in movers])
        held = {}
        r["start"] = basis_bytes(ow.world, ow.state).decode("utf-8")
        inside = 0

        def attempt(label, fn):
            before, w0, s0, n0, q0, l0 = digest(ow.world, ow.state), ow.world, ow.state, len(ow.receipts), ow.seq, ow.last
            if mutate:   # a plant: a rebase that writes into the live state before it is checked
                ow.state.cooldown = ow.state.cooldown + 1.0
            ev = {"label": label, "at": ow.state.tick}
            try:
                receipt = fn()
                ev.update(ok=True, receipt=receipt, bytes=basis_bytes(ow.world, ow.state).decode("utf-8"),
                          conserved=conserved(w0, s0, ow.world, ow.state) or "every moved leaf")
            except Refused as e:
                ev.update(ok=False, code=e.code, why=e.why,
                          unchanged=digest(ow.world, ow.state) == before and ow.world is w0 and ow.state is s0 and len(ow.receipts) == n0
                          and ow.seq == q0 and ow.last == l0)
            r["events"].append(ev)

        for seg in case.get("inputs") or []:
            if "rebase" in seg:
                di, dj = seg["rebase"]
                attempt("rebase %d,%d" % (di, dj), lambda: commit(ow, prepare(ow, {"tick": ow.state.tick, "di": di, "dj": dj}, **pk), **ck))
            elif "event" in seg:
                attempt("event", lambda: commit(ow, prepare(ow, seg["event"], **pk), **ck))
            elif "prepare" in seg:
                di, dj = seg["prepare"]
                ev = {"label": "prepare " + seg["as"], "at": ow.state.tick}
                try:
                    P = prepare(ow, {"tick": ow.state.tick, "di": di, "dj": dj}, **pk)
                    held[seg["as"]] = P
                    ev.update(ok=True, receipt=P.receipt)
                except Refused as e:
                    ev.update(ok=False, code=e.code)
                r["events"].append(ev)
            elif "world_field" in seg:   # a field the frame table does not name (the hand-worked case O14)
                setattr(ow.world, seg["world_field"], [7.0, 31.0])
            elif "poke" in seg:     # the live state written outside a tick and a commit (the hand-worked case O13)
                ow.state.x = ow.state.x + float(seg["poke"])
            elif "tamper" in seg:   # a candidate changed after it was prepared (the hand-worked case O12)
                held[seg["tamper"]].state.x = held[seg["tamper"]].state.x + 1.0
            elif "commit" in seg:
                attempt("commit " + seg["commit"], lambda: commit(ow, held[seg["commit"]], **ck))
            else:
                for inp in (T.stress_inputs(seg["stress"]) if seg.get("stress") else [dict(seg.get("in") or {}) for _ in range(seg["n"])]):
                    ow.step(inp)
                    r["snaps"].append(T.write_snapshot2(ow.state))
                    r["hashes"].append(T.hash2(ow.world, ow.state))
                    if any(T.plan_over(ow.state.x, ow.state.z, b) and b[4] > ow.state.feet and b[1] < ow.state.feet + T.BODY for b in T.poses(ow.world, ow.state)):
                        inside += 1
        r["inside"] = inside
        r["end"] = basis_bytes(ow.world, ow.state).decode("utf-8")
        r["receipts"] = list(ow.receipts)
    except Exception as e:   # noqa: BLE001 — a case that cannot be played says why; the checks below fail it
        r["error"] = "%s: %s" % (type(e).__name__, e)
    return r


def split_basis(b):
    """(identity text, snapshot text) of a basis's canonical bytes; ValueError for bytes not in ORT-1's framing."""
    import re
    raw = b.encode("utf-8")
    m = re.match(rb"VERDANDI-ORT 1\nidentity (0|[1-9][0-9]*)\n", raw)
    if not m:
        raise ValueError("not ORT-1's framing (its head)")
    n, at = int(m.group(1)), m.end()
    ident = raw[at:at + n]
    m2 = re.match(rb"\nstate (0|[1-9][0-9]*)\n", raw[at + n:])
    if len(ident) != n or not m2:
        raise ValueError("not ORT-1's framing (the identity's count)")
    k, at2 = int(m2.group(1)), at + n + m2.end()
    snap = raw[at2:at2 + k]
    if len(snap) != k or raw[at2 + k:] != b"\n":
        raise ValueError("not ORT-1's framing (the state's count)")
    return ident.decode("utf-8"), snap.decode("utf-8")


def framed(ident, snap):
    i, s = ident.encode("utf-8"), snap.encode("utf-8")
    return (b"%s\nidentity %d\n%s\nstate %d\n%s\n" % (FORMAT.encode("ascii"), len(i), i, len(s), s)).decode("utf-8")


def before(r, idx):
    """The basis rebase `idx` was tried on: the last committed rebase's at the same tick, or the state after the last
    tick (or the start) with the identity the world had then."""
    tried = [e for e in r["events"] if not e["label"].startswith("prepare ")]
    at = int(tried[idx]["at"])
    ident = split_basis(r["start"])[0]
    for e in tried[:idx]:
        if e["ok"]:
            ident = split_basis(e["bytes"])[0]
    for e in reversed(tried[:idx]):
        if e["ok"] and e["at"] == at:
            return e["bytes"]
    snap = r["snaps"][at - 1] if at > 0 else split_basis(r["start"])[1]
    return framed(ident, snap)


def faults(case, r):
    """Where a played case parts from the values worked by hand."""
    try:
        return _faults(case, r)
    except (ValueError, KeyError, IndexError, TypeError) as e:
        return ["the results do not read: %s: %s" % (type(e).__name__, e)]


def _faults(case, r):
    out = []
    if r.get("error"):
        return ["the case did not play: " + r["error"]]
    tried = [e for e in r["events"] if not e["label"].startswith("prepare ")]
    want = case.get("expect_rebase") or []
    if case.get("invariant") is None and len(want) != len(tried):
        out.append("%d rebases tried, %d worked by hand" % (len(tried), len(want)))
    enc = lambda v: "f" + struct.pack(">d", float(v)).hex()
    for k, (w, e) in enumerate(zip(want, tried)):
        if e["at"] != w["at"]:
            out.append("rebase %d at tick %s, worked at %s" % (k + 1, e["at"], w["at"]))
        if "refused" in w:
            if e["ok"] or e.get("code") != w["refused"]:
                out.append("rebase %d: %s, worked refused %s" % (k + 1, "admitted" if e["ok"] else e.get("code"), w["refused"]))
            elif not e.get("unchanged"):
                out.append("rebase %d refused, and the owner's world or state changed" % (k + 1))
            continue
        if not e["ok"]:
            out.append("rebase %d refused (%s: %s), worked admitted" % (k + 1, e.get("code"), e.get("why", "")[:80]))
            continue
        if e.get("conserved") != "every moved leaf":
            out.append("rebase %d: %s not conserved" % (k + 1, e.get("conserved")))
        ident, snap = split_basis(e["bytes"])
        doc = json.loads(ident.split("\n", 1)[1])
        org = [Fraction(T._dec(v)) for v in doc["world"]["origin"]] if "origin" in doc["world"] else [Fraction(0), Fraction(0)]
        if org != [Fraction(v) for v in w["origin"]]:
            out.append("rebase %d: origin %s, worked %s" % (k + 1, [str(v) for v in org], w["origin"]))
        # the state after, against the one built here from the state before and the worked numbers alone
        pre = json.loads(split_basis(before(r, k))[1])
        if "set" in w:
            setv = w["set"]
        else:
            mx, mz = (Fraction(v) for v in w["moved"])
            ex = lambda v, d: Fraction(T._dec(v)) + d
            setv = {"x": ex(pre["x"], mx), "z": ex(pre["z"], mz), "targets": [[ex(t["x"], mx), ex(t["z"], mz)] for t in pre["targets"]]}
        bad = [key for key, v in (("x", setv["x"]), ("z", setv["z"])) if Fraction(float(v)) != Fraction(v)]
        if bad:
            out.append("rebase %d: the worked %s is not a double" % (k + 1, bad[0]))
        exp = dict(pre)
        exp["targets"] = [dict(t) for t in pre["targets"]]
        exp["x"], exp["z"] = enc(setv["x"]), enc(setv["z"])
        for j, (tx, tz) in enumerate(setv["targets"]):
            exp["targets"][j]["x"], exp["targets"][j]["z"] = enc(tx), enc(tz)
        got = json.loads(snap)
        if got != exp:
            diff = sorted(key for key in set(got) | set(exp) if got.get(key) != exp.get(key))
            out.append("rebase %d: the state after is not the one built from the state before and the worked numbers (at %s)" % (k + 1, ", ".join(diff)))
        if "movers" in w:
            gm = [[Fraction(T._dec(m[i])) for i in (1, 3, 4, 6)] for m in doc["world"]["movers"]]
            if gm != [[Fraction(v) for v in g] for g in w["movers"]]:
                out.append("rebase %d: movers %s, worked %s" % (k + 1, [[str(v) for v in g] for g in gm], w["movers"]))
    if case.get("expect_round_trip"):
        done = [e for e in tried if e["ok"]]
        if not done or done[-1]["bytes"] != before(r, tried.index(done[0])):
            out.append("there and back: the bytes after are not the bytes before")
    for e in case.get("expect") or []:
        t = e["tick"]
        if t > len(r["snaps"]):
            out.append("no tick %d" % t)
            continue
        d = json.loads(r["snaps"][t - 1])
        for key, v in e.items():
            if key == "tick":
                continue
            if key == "movers":
                gm = [{"phase": T._dec(m["phase"]), "stopped": m["stopped"]} for m in d["movers"]]
                if gm != [{"phase": float(m["phase"]), "stopped": m["stopped"]} for m in v]:
                    out.append("tick %d: movers %s, worked %s" % (t, gm, v))
                continue
            gv = T._dec(d[key]) if isinstance(d[key], str) else d[key]
            if isinstance(v, bool) or isinstance(gv, bool):
                if gv is not v:
                    out.append("tick %d: %s %r, worked %r" % (t, key, gv, v))
            elif Fraction(gv) != Fraction(v):
                out.append("tick %d: %s %r, worked %r" % (t, key, gv, v))
    if case.get("invariant") == "never inside":
        if r.get("inside"):
            out.append("%d ticks ended with the body inside a box" % r["inside"])
        for e in tried:
            if e["ok"] and e.get("conserved") != "every moved leaf":
                out.append("a rebase at tick %s: %s not conserved" % (e["at"], e.get("conserved")))
    return out


# ------------------------------------------------------------------------------------------------ the commands
def run_table(conv, table, **plant):
    rows, mine = [], {}
    for case in table["cases"]:
        r = play(conv, case, **plant)
        mine[case["name"]] = r
        fs = faults(case, r)
        n = len(r.get("snaps", []))
        tried = [e for e in r.get("events", []) if not e["label"].startswith("prepare ")]
        rows.append((case["name"], not fs, "; ".join(fs)[:240] if fs else "%d ticks, %d rebases tried (%d committed, %d refused, each writing nothing); every worked value held" % (
            n, len(tried), sum(1 for e in tried if e["ok"]), sum(1 for e in tried if not e["ok"]))))
    return rows, mine


def _feet_too(s):
    s.feet = s.feet + 0.25


PLANTS = {
    "the basis checked by its bytes alone, not its history (ABA)": dict(check_history=False),
    "commit without checking the candidate against what was prepared": dict(check_candidate=False),
    "a transform that also moves the feet (the candidate's self-check refuses it)": dict(extra=_feet_too),
    "a transform that also moves the feet, without the self-check": dict(extra=_feet_too, selfcheck=False),
    "no exactness guard (a rebase that rounds)": dict(guard=False),
    "no basis check at commit": dict(check_basis=False),
    "no replay check at commit": dict(check_replay=False),
    "a rebase that writes into the live state before it is checked": dict(mutate=True),
    "the frame table without targets' z": dict(frame={k: v for k, v in FRAME.items() if k != "targets.*.z"}),
    "the frame table with targets' z frame-independent": dict(frame=dict(FRAME, **{"targets.*.z": "-"})),
}


def _plant_origin_off():
    """A plant in the world: the objective read without the origin. Returns the undo."""
    old = T.objective

    def objective(world, s, inp):
        if world.objective is None:
            s.on_objective = False
        else:
            i0, j0, i1, j1 = world.objective
            i, j = math.floor(s.x / world.cell), math.floor(s.z / world.cell)
            s.on_objective = i0 <= i <= i1 and j0 <= j <= j1
    T.objective = objective
    T.PHASES2 = tuple(objective if p is old else p for p in T.PHASES2)

    def undo():
        T.objective = old
        T.PHASES2 = tuple(old if p is objective else p for p in T.PHASES2)
    return undo


def engine_rows(table, mine, res):
    """Each case of an engine's results against this program's: [(name, faults, ticks, events)]."""
    theirs = {x["name"]: x for x in res[1:]}
    out = []
    for case in table["cases"]:
        t, m = theirs.get(case["name"]), mine[case["name"]]
        fs = []
        if t is None:
            fs.append("not in the results")
        else:
            fs += ["by hand: " + f for f in faults(case, t)]
            if t.get("start") != m.get("start"):
                fs.append("the start's bytes differ")
            for n, (a, b) in enumerate(zip(m["snaps"], t.get("snaps", []))):
                if a != b:
                    fs.append("FIRST DIFFERENT snapshot at tick %d" % (n + 1))
                    break
            if len(m["snaps"]) != len(t.get("snaps", [])):
                fs.append("%d ticks there, %d here" % (len(t.get("snaps", [])), len(m["snaps"])))
            hb = [n + 1 for n, (a, b) in enumerate(zip(m["hashes"], t.get("hashes", []))) if a != b]
            if hb:
                fs.append("hash first different at tick %d" % hb[0])
            for k, (a, b) in enumerate(zip(m["events"], t.get("events", []))):
                for key in ("label", "at", "ok", "code", "receipt", "bytes", "conserved", "unchanged"):
                    if a.get(key) != b.get(key):
                        fs.append("event %d (%s): %s differs (here %s, there %s)" % (k + 1, a.get("label"), key, str(a.get(key))[:40], str(b.get(key))[:40]))
                        break
            if len(m["events"]) != len(t.get("events", [])):
                fs.append("%d events there, %d here" % (len(t.get("events", [])), len(m["events"])))
            if t.get("end") != m.get("end") or t.get("receipts") != m.get("receipts"):
                fs.append("the end's bytes or the receipts differ")
        out.append((case["name"], fs, len(m.get("snaps", [])), len(m.get("events", []))))
    return out


def _tamper_snapshot(res):
    r = res[3]
    r["snaps"][-1] = r["snaps"][-1].replace('"onGround":true', '"onGround":false', 1) if '"onGround":true' in r["snaps"][-1] else r["snaps"][-1] + " "
    return "O3's last snapshot, onGround"


def _tamper_code(res):
    for r in res[1:]:
        for e in r["events"]:
            if not e["ok"] and e.get("code") == "ORT-STALE-BASIS":
                e["code"] = "ORT-STALE-TICK"
                return "%s: a stale basis reported as a stale tick" % r["name"].split(" ")[0]


def _tamper_framing(res):
    r = res[1]
    e = [x for x in r["events"] if x["ok"]][0]
    e["bytes"] = e["bytes"].replace("\nidentity ", "\nidentity  ", 1)
    return "O1's rebase: its framing given one byte more"


def _tamper_receipt(res):
    r = res[9]
    r["receipts"][0] = r["receipts"][0].replace("seq 1", "seq 2")
    return "O9's receipt: seq 1 as 2"


def _tamper_digit(res):
    r = res[2]
    e = [x for x in r["events"] if x["ok"]][0]
    i = e["bytes"].index('"x":"f') + 7
    e["bytes"] = e["bytes"][:i] + ("1" if e["bytes"][i] == "0" else "0") + e["bytes"][i + 1:]
    return "O2's first rebase: one bit of x"


ENGINE_PLANTS = [("one snapshot changed", _tamper_snapshot), ("a refusal's code changed", _tamper_code), ("a rebase's framing changed", _tamper_framing),
                 ("a receipt changed", _tamper_receipt), ("one bit of a moved number changed", _tamper_digit)]


def _plant_world_field():
    """A plant in the world: a field of world-space metres the frame table does not name. Returns the undo."""
    init = T.World2.__init__

    def patched(self, *a, **k):
        init(self, *a, **k)
        self.spawn_metres = [7.0, 31.0]
    T.World2.__init__ = patched

    def undo():
        T.World2.__init__ = init
    return undo


def main(argv):
    if argv and not os.path.isfile(argv[0]):
        print("ORT-REF: there is no file %s: a browser writes it, so run first:  python graybox/trace.py run tactical --ort --browser msedge" % argv[0], file=sys.stderr)
        return 2
    with open(CASES, encoding="utf-8") as fh:
        table = json.load(fh)
    conv = level.convert(table["map"])
    print("ORT-REF  %s  map %s  ORT-1 (graybox/ORT-1.md) under rules 2, %d cases" % (os.path.relpath(CASES), table["map"], len(table["cases"])))
    ok = True
    kat = [(b"abc", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
           (b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq", "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1")]
    good = all(sha(m) == h for m, h in kat)
    print("%s SHA-256 against FIPS 180-2's two answers (abc; the two-block message)" % ("PASS" if good else "FAIL"))
    ok = ok and good
    rows, mine = run_table(conv, table)
    for name, good, detail in rows:
        print("%s %s — %s" % ("PASS" if good else "FAIL", name, detail))
        ok = ok and good
    for label, plant in sorted(PLANTS.items()):
        prow, _m = run_table(conv, table, **plant)
        bit = [n.split(" ")[0] for n, g, _d in prow if not g]
        print("%s plant: %s — %s" % ("PASS" if bit else "FAIL", label, ("caught by " + ", ".join(bit)) if bit else "NOT caught by any worked value"))
        ok = ok and bool(bit)
    for label, make in (("the objective read without the origin", _plant_origin_off),
                        ("the world given a field no table declares (a rebase must refuse, not leave it behind)", _plant_world_field)):
        undo = make()
        try:
            prow, _m = run_table(conv, table)
        finally:
            undo()
        bit = [n.split(" ")[0] for n, g, _d in prow if not g]
        print("%s plant: %s — %s" % ("PASS" if bit else "FAIL", label, ("caught by " + ", ".join(bit)) if bit else "NOT caught by any worked value"))
        ok = ok and bool(bit)
    engine_ok = True
    if argv:
        with open(argv[0], encoding="utf-8") as fh:
            R = json.load(fh)
        if R.get("format") != "VERDANDI-ORT-RESULTS":
            print("FAIL %s is not ORT-1's results" % argv[0])
            return 1
        res = R.get("results", [])
        js_sha = res[0] if res and res[0].get("name") == "sha256" else {}
        good = js_sha.get("abc") == kat[0][1] and js_sha.get("two") == kat[1][1] and js_sha.get("empty") == sha(b"")
        print("held to the results of %s (%s)" % (os.path.basename(argv[0]), ((R.get("runtime") or {}).get("userAgent") or "?")[:90]))
        print("%s the engine's SHA-256 against FIPS 180-2's answers and the empty message" % ("PASS" if good else "FAIL"))
        engine_ok = engine_ok and good
        rows = engine_rows(table, mine, res)
        for name, fs, n_snaps, n_events in rows:
            engine_ok = engine_ok and not fs
            print("%s %s — %s" % ("PASS" if not fs else "FAIL", name, "; ".join(fs)[:240] if fs else
                                  "%d ticks, %d rebases: every snapshot, hash, rebase's bytes and receipt the same" % (n_snaps, n_events)))
        # the comparison's own plants: the engine's results changed in one place each, every change found
        for label, tamper in ENGINE_PLANTS:
            res2 = json.loads(json.dumps(res))
            where = tamper(res2)
            bit = [name for name, fs, _a, _b in engine_rows(table, mine, res2) if fs]
            print("%s plant: %s — %s" % ("PASS" if bit else "FAIL", label + (" (%s)" % where if where else ""), ("found in " + ", ".join(b.split(" ")[0] for b in bit)) if bit else "NOT found"))
            engine_ok = engine_ok and bool(bit)
    print("ORT-1 %s%s" % ("HELD BY PYTHON" if ok else "NOT HELD", (" AND THE ENGINE" if engine_ok else "; THE ENGINE PARTS") if argv else ""))
    return 0 if ok and engine_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
