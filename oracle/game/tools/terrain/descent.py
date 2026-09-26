# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""descent — the stairs are connected, or they are not, and the witness is a PATH (URDRDSC1).

THE SECOND GAME-LAYER VERTICAL SLICE, and D24 §3's topology row made a law. `gamegen` (URDRGEN1)
produces a canonical level and says NOTHING about whether it can be walked — its own `does_not_show`
opens "a level that reproduces is not a level worth playing" and adds that the stairs down are
reachable from the stairs up ONLY BY CONSTRUCTION, and construction is not a witness. This module is
the witness. It reads a `gamegen` level, finds the two stairs, and produces a concrete PATH from one
to the other, or reports that none exists.

IT CONSUMES `gamegen`; `gamegen` DOES NOT KNOW IT EXISTS. The dependency runs one way — `descent`
imports `gamegen`, and `gamegen` was sealed one rung earlier importing only `hashlib` and `os`. A
topology witness that fed anything back into the generator would put the generator on the wrong side
of D24 §1.

THE GRID IS THE GRAPH, MEASURED, NOT INVENTED. A level is a 48 x 32 grid of cells; a cell is
TRAVERSABLE iff it is floor, stairs-up or stairs-down; two orthogonally adjacent traversable cells
share an edge. That adjacency is DERIVED from the grid on every call and stored nowhere — there is no
second canonical representation of the dungeon, because the level already is one. (Over 256 ordinary
levels the entire floor is a single connected component; that is a MEASUREMENT about the generator,
not this law, and it is exactly why the stairs connect by construction.)

THE OUTPUT IS A PATH, AND THE PATH IS VERIFIED INDEPENDENTLY OF THE SEARCH. `descent_path` runs a
deterministic BFS — neighbours in a fixed order, parent pointers, the shortest path reconstructed —
and `verify_path` checks the result WITHOUT re-running the search: every step orthogonally adjacent,
every cell traversable, the ends the two stairs. The expensive half is the search and the trusted
half is checking a walk, `cutpin`'s shape: a witness you can believe by reading it. The canonical
path (its length and its digest) is pinned, so the witness reproduces bit-for-bit.

THE INPUT DOMAIN IS EXPLICIT AND NARROWER THAN "ANY GRID". The witness refuses, typed, any level
without EXACTLY ONE stairs-up and EXACTLY ONE stairs-down — an endpoint that is absent or doubled is
outside what a reachability question even means, and a witness that guessed would be answering a
question it was not asked. Every `gamegen` level is in the domain; a level need not be a `gamegen`
level to be, which is what lets the counterexample in.

THE COUNTEREXAMPLE IS A SEALED ROOM, and it is sharp because of what it does NOT break. `seal_down`
walls the one-cell margin around the stairs-down room, severing every corridor mouth while leaving
the room interior, both stairs, the border and the alphabet untouched. The sealed level is INSIDE
this witness's input domain (two stairs, each in a room) and OUTSIDE the generator's ordinary output
(the generator never seals) — and it still passes EVERY ONE of `gamegen`'s structural predicates:
`gamegen.is_well_formed(sealed)` is True. A LEVEL CAN BE GENERATION-CORRECT IN EVERY WAY THE
GENERATOR'S ORACLE CAN SEE AND STILL BE UNTRAVERSABLE. That is why topology is a separate law and not
a corollary of generation: the two oracles do not collapse into each other, and `descent-oracles`
asserts it on every run rather than in this paragraph.

GRADE (honest, D5). MEASURED: over the eight-level corpus and a 128-level sweep, the stairs connect
and the returned path verifies independently; the sealed counterexample severs them while staying in
the domain and well-formed under `gamegen`; the path digests reproduce. ESTABLISHED: `verify_path`
accepts a walk iff it is one (a broken step, a wall step, a wrong endpoint each rejected); the domain
refusals are total over absent and doubled endpoints; the two-oracle separation. DECLARED: that
orthogonal 4-adjacency over {floor, up, down} is the traversal model — a choice, labelled, and the
one a later movement rung may widen (diagonals, doors, keys) by minting a new law rather than editing
this one. does_not_show: that a reachable level is worth playing; that the WHOLE level is connected —
the witness proves the STAIRS connect and nothing more, even though the generator happens to produce
fully-connected levels, because proving more than the claim is how a witness starts lying; that the
path is the SHORTEST such (it is BFS's, but shortest-ness is not the claim); that traversal in the
game will use this adjacency (a door or a locked gate is a later law); and nothing about `gamegen`'s
correctness, which is its own rung's and which this witness deliberately cannot see."""
import collections
import hashlib
import os as _os

_HERE = _os.path.dirname(_os.path.abspath(__file__))
if _HERE not in __import__("sys").path:
    __import__("sys").path.insert(0, _HERE)
import gamegen as _G                                                      # noqa: E402

MAGIC = b"URDRDSC1"

LAYER = "CORE"
D24_ANSWER = "affects canonical game state — a property of a generated level"
ALLOWED_IMPORTS = ("collections", "hashlib", "os", "gamegen")

#: The traversal model — DECLARED. A cell is traversable iff its glyph is one of these; edges are
#: orthogonal. A later movement law may widen this (diagonals, doors) by minting a new glyph.
TRAVERSABLE = (_G.FLOOR, _G.UP, _G.DOWN)
STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))     # fixed order: the BFS is deterministic


class DescentError(Exception):
    def __init__(self, message):
        super().__init__(f"DESCENT-REFUSE: {message}")
        self.code = "DESCENT-REFUSE"


def traversable(level, x, y):
    """THE AUTHORITATIVE TRAVERSABILITY PREDICATE — public, so a movement law consumes it rather
    than re-deriving `cell in TRAVERSABLE` in a second place. A cell is traversable iff it is on the
    grid and its glyph is floor, stairs-up or stairs-down. This is the one place the traversal model
    lives; `move` (URDRMOV1) asks this rather than reinventing it, which is what keeps movement
    truth single-sourced."""
    return 0 <= x < level.w and 0 <= y < level.h \
        and level.cells[y][x:x + 1] in TRAVERSABLE


def endpoints(level):
    """The unique stairs-up and stairs-down, or a typed refusal. The input domain is EXACTLY the
    levels with one of each — an absent or doubled endpoint is outside what reachability means."""
    ups, downs = [], []
    for y, row in enumerate(level.cells):
        for x in range(level.w):
            c = row[x:x + 1]
            if c == _G.UP:
                ups.append((x, y))
            elif c == _G.DOWN:
                downs.append((x, y))
    if len(ups) != 1 or len(downs) != 1:
        raise DescentError(f"reachability needs exactly one stairs-up and one stairs-down, "
                           f"got {len(ups)} up and {len(downs)} down")
    return ups[0], downs[0]


def descent_path(level):
    """A concrete shortest path from stairs-up to stairs-down as a tuple of (x, y), or `None` if the
    two are not connected. Deterministic: neighbours in `STEPS` order, parent pointers, reconstructed
    from the goal. The SEARCH — the expensive half; `verify_path` is the trusted half."""
    up, down = endpoints(level)
    parent = {up: up}
    dq = collections.deque([up])
    while dq:
        cur = dq.popleft()
        if cur == down:
            break
        cx, cy = cur
        for dx, dy in STEPS:
            nxt = (cx + dx, cy + dy)
            if nxt not in parent and traversable(level, *nxt):
                parent[nxt] = cur
                dq.append(nxt)
    if down not in parent:
        return None
    path = [down]
    while path[-1] != up:
        path.append(parent[path[-1]])
    path.reverse()
    return tuple(path)


def verify_path(level, path):
    """Accept a path IFF it is a genuine walk from stairs-up to stairs-down — checked WITHOUT
    re-running the search: every step orthogonally adjacent, every cell traversable, the ends the two
    stairs. A witness you can believe by reading it (`cutpin`'s shape). Returns (ok, reason)."""
    if not path:
        return False, "empty"
    try:
        up, down = endpoints(level)
    except DescentError as exc:
        return False, str(exc)
    if path[0] != up:
        return False, f"does not start at stairs-up {up}"
    if path[-1] != down:
        return False, f"does not end at stairs-down {down}"
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        if (abs(ax - bx), abs(ay - by)) not in ((1, 0), (0, 1)):
            return False, f"step {(ax, ay)}->{(bx, by)} is not an orthogonal move"
    for (x, y) in path:
        if not traversable(level, x, y):
            return False, f"cell {(x, y)} is not traversable"
    return True, "a verified walk"


def is_connected(level):
    """The claim, as a bool: does a verified path exist? The path is found AND checked, so a search
    that returned a bad path would be caught here rather than trusted."""
    p = descent_path(level)
    return p is not None and verify_path(level, p)[0]


def path_digest(level):
    """The canonical witness digest — over the path coordinates, so it reproduces bit-for-bit. A
    level with no path digests the empty witness, which is a distinct, stable value."""
    p = descent_path(level) or ()
    body = b";".join(b"%d,%d" % (x, y) for (x, y) in p)
    return hashlib.sha256(MAGIC + b"|path|" + body).hexdigest()


# ---- the counterexample --------------------------------------------------------------------------------
def _down_room(level):
    _up, down = endpoints(level)
    for r in level.rooms:
        rx, ry, rw, rh = r
        if rx <= down[0] < rx + rw and ry <= down[1] < ry + rh:
            return r
    raise DescentError("stairs-down is in no room — not a gamegen level")


def seal_down(level):
    """THE COUNTEREXAMPLE. Wall the one-cell margin around the stairs-down room, severing every
    corridor mouth while leaving the room interior, both stairs, the border and the alphabet intact.
    The result is INSIDE this witness's domain (two stairs, each in a room) and OUTSIDE the
    generator's ordinary output — and it stays `gamegen`-well-formed, which is the whole point."""
    rx, ry, rw, rh = _down_room(level)
    rows = [bytearray(r) for r in level.cells]
    for x in range(rx - 1, rx + rw + 1):
        for y in range(ry - 1, ry + rh + 1):
            if rx <= x < rx + rw and ry <= y < ry + rh:
                continue                                    # inside the down room: leave it
            if 0 <= x < level.w and 0 <= y < level.h:
                rows[y][x:x + 1] = _G.WALL
    return level.replaced(cells=tuple(bytes(r) for r in rows))


def the_sealed_room_is_rejected(level):
    """Both directions on one level: the ordinary level connects with a verified path, the sealed one
    does not, and the sealed one is still in the domain (endpoints resolve)."""
    ok_before = is_connected(level)
    sealed = seal_down(level)
    endpoints(sealed)                                       # in the domain, or this raises
    ok_after = is_connected(sealed)
    return ok_before and not ok_after


def the_oracles_do_not_collapse(level):
    """THE SHARP ONE. A sealed level FAILS this witness while PASSING every one of `gamegen`'s
    structural predicates — generation-correct and untraversable at once — so topology is not a
    corollary of generation and the two oracles are provably distinct. Returns
    (gamegen_ok, descent_fails)."""
    sealed = seal_down(level)
    return _G.is_well_formed(sealed), not is_connected(sealed)


# ---- the domain refusals -------------------------------------------------------------------------------
def _blank_domain_probes(level):
    """Levels just outside the domain: no stairs-down, and two stairs-up. Built from a real level so
    only the endpoint count differs."""
    up, down = endpoints(level)
    no_down = _set(level, down[0], down[1], _G.FLOOR)
    two_up = _set(level, down[0], down[1], _G.UP)
    return no_down, two_up


def _set(level, x, y, glyph):
    rows = [bytearray(r) for r in level.cells]
    rows[y][x:x + 1] = glyph
    return level.replaced(cells=tuple(bytes(r) for r in rows))


def domain_is_total(level):
    """(refused_absent, refused_doubled): a missing endpoint and a doubled one each refuse typed."""
    no_down, two_up = _blank_domain_probes(level)
    out = []
    for probe in (no_down, two_up):
        try:
            endpoints(probe)
            out.append(False)
        except DescentError as exc:
            out.append(exc.code == "DESCENT-REFUSE")
    return tuple(out)


def verify_rejects_a_forgery(level):
    """`verify_path` is not a rubber stamp: a broken step, a wall step and a wrong endpoint are each
    rejected, so a search that returned garbage could not pass. Returns a tuple of bools."""
    good = descent_path(level)
    up, down = endpoints(level)
    broken = good[:2] + good[3:] if len(good) > 3 else good          # skip a cell: a jump
    walls = list(good)
    for y in range(level.h):                                          # find any wall to step onto
        for x in range(level.w):
            if level.cells[y][x:x + 1] == _G.WALL:
                walls = [up, (x, y), down]
                break
        else:
            continue
        break
    wrong_end = good[:-1] if len(good) > 1 else good
    return (verify_path(level, good)[0],
            not verify_path(level, broken)[0],
            not verify_path(level, walls)[0],
            not verify_path(level, wrong_end)[0])


# ---- scenes ---------------------------------------------------------------------------------------------
#: The corpus is `gamegen`'s corpus, read through this witness. Same eight (seed, depth) levels, so a
#: drift in either module moves a pin.
CORPUS = _G.CORPUS


def witness_row(seed, depth):
    lv = _G.generate(seed, depth)
    p = descent_path(lv)
    return (_G.corpus_name(seed, depth), len(p) if p else 0, path_digest(lv))


def witness_rows():
    return tuple(witness_row(s, d) for s, d in CORPUS)


SCENES = ("descent", "sealed", "domain")


def scene_case(name):
    if name == "descent":
        return "|".join("%s:%d:%s" % wr for wr in witness_rows()) + "|all=%s" % (
            all(is_connected(_G.generate(s, d)) for s, d in CORPUS))
    if name == "sealed":
        return "|".join("%s:sealed=%s:oracles=%s" % (
            _G.corpus_name(s, d), the_sealed_room_is_rejected(_G.generate(s, d)),
            the_oracles_do_not_collapse(_G.generate(s, d))) for s, d in CORPUS)
    if name == "domain":
        lv = _G.generate(*CORPUS[0])
        return "total=%s|verify=%s" % (domain_is_total(lv), verify_rejects_a_forgery(lv))
    raise DescentError(f"no scene named {name!r}")


def scene_result(name):
    return hashlib.sha256(MAGIC + b"|" + name.encode() + b"|"
                          + scene_case(name).encode()).hexdigest()


def descent_digest():
    return hashlib.sha256(MAGIC + b"|" + "|".join(scene_result(n)
                                                  for n in SCENES).encode()).hexdigest()


def golden(name):
    """READ from the committed corpus. An unpinned name REFUSES typed rather than returning a default."""
    with open(_os.path.join(_HERE, "conformance_descent.txt"), encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                nm, dig = ln.split()
                if nm == name:
                    return dig
    raise DescentError(f"no golden named {name!r}")


def emitted_matches_pinned():
    return (all(scene_result(n) == golden(n) for n in SCENES)
            and descent_digest() == golden("descent-digest"))


def an_unpinned_name_refuses():
    try:
        golden("not-a-scene")
    except DescentError as exc:
        return exc.code == "DESCENT-REFUSE"
    return False


def main():
    print("DESCENT — the stairs are connected, or they are not, and the witness is a PATH (URDRDSC1)")
    print("layer %s: %s | imports %s" % (LAYER, D24_ANSWER, ALLOWED_IMPORTS))
    print()
    lv = _G.generate(*CORPUS[0])
    p = descent_path(lv)
    print("seed %d depth %d: path of %d cells, verifies %s"
          % (lv.seed, lv.depth, len(p), verify_path(lv, p)))
    print("path digest:", path_digest(lv))
    print()
    for n, ln, dg in witness_rows():
        print("%-32s path=%-4d %s" % (n, ln, dg))
    print()
    print("sealed room rejected (all corpus)   :", all(the_sealed_room_is_rejected(_G.generate(s, d)) for s, d in CORPUS))
    print("oracles do NOT collapse (all corpus):", all(the_oracles_do_not_collapse(_G.generate(s, d)) for s, d in CORPUS))
    print("domain total (absent, doubled)      :", domain_is_total(lv))
    print("verify rejects forgeries            :", verify_rejects_a_forgery(lv))
    print()
    for n in SCENES:
        print(n, scene_result(n))
    print("descent-digest", descent_digest())
    print()
    print("does_not_show: that a reachable level is worth playing; that the WHOLE level is connected")
    print("(the witness proves the STAIRS connect, nothing more); that the path is shortest; and")
    print("nothing about gamegen's correctness, which this witness deliberately cannot see.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
