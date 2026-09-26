# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""gamegen — SEED + DEPTH -> CANONICAL LEVEL -> DIGEST, and nothing else (URDRGEN1).

THE FIRST GAME-LAYER VERTICAL SLICE, and the first module admitted under D24. D24 §1 asks one
question of every module — does this affect canonical game state, or is it a view of it? — and this
module answers: IT AFFECTS CANONICAL GAME STATE. It is CORE. It imports `hashlib` and `os` and
nothing under `tools/`; it renders nothing; it needs no window, no clock, no input device and no
audio; and it produces the same bytes on the verification host that it would produce anywhere else.
That last clause is D24 §6's dependency boundary doing work on the first module written for it.

THIS IS NOT THE FATE GENERATOR. It is the authority boundary and ONE generator behind it — the
smallest slice that can be forced through §1 and made to answer. The contract was written first
(`docs/gamegen_brief.md` §1) and the module was held to it.

THE CONTRACT, IN ONE LINE EACH.
    input      (seed, depth): 0 <= seed < 2**64, 1 <= depth <= DEPTH_MAX; anything else REFUSES typed
    output     a Level: a fixed 48 x 32 grid over the alphabet `# . < >`, plus the rooms, SORTED
    identity   canon_bytes(level) = URDRGEN1|s:|d:|48x32|rooms:...|row|row|...  — nothing else enters
    digest     SHA-256 of the identity bytes: REPRODUCIBILITY ONLY, never the correctness oracle
    reproduces canon_bytes(generate(seed, depth)), every host, every hash seed, every interpreter

DEPTH IS THREE CLAIMS, KEPT APART. D24 gives the bound, 2 147 483 647, because that is what a signed
32-bit integer holds. (1) REPRESENTATION: `DEPTH_MAX` is COMPUTED from the width and a falsifier
holds it equal to the literal. (2) ADMISSION: depth 0 and DEPTH_MAX + 1 refuse, DEPTH_MAX is
admitted. (3) GENERATION: the deepest admissible level actually GENERATES — it is in the corpus, its
digest is pinned, its structure is clean, and it costs the same draws as depth 1 because depth enters
only the preimage of each draw. A generator that merely stores a legal integer gets no credit here;
the question the original never asked is answered for this generator by running it.

THE ALGORITHM IS STATELESS, IN `heightfield`'s IDIOM. There is no RNG object. A draw is
SHA-256(MAGIC | seed | depth | tag | i), and it depends on nothing that happened before it, so no
evaluation order can reach the output. Up to ROOM_TRIES attempts place non-overlapping rooms inside
the border (fewer than ROOMS_MIN kept is the ADMISSION CONDITION, a typed refusal, measured over a
sweep rather than assumed away); consecutive kept rooms are joined by an L-shaped corridor whose bend
is one draw; stairs up sit at the first room's centre and stairs down at the last's. The rooms are
SORTED before they enter identity, so the order the generator placed them in can never reach the
digest — and that is planted as an INERT plant, reported as inert, alongside plants that move it.

THE DIGEST IS NOT THE ORACLE. A wrong level reproduces its digest exactly as faithfully as a right
one, so structure has its own predicates — the border is wall, rooms are inside and disjoint and
floored, exactly one stairs of each kind and each inside a room, the count within bounds, the rooms
sorted, the alphabet closed — and each has a PLANTED violation the predicate must catch by name.

GRADE (honest, D5). MEASURED: eight pinned levels reproduce raw; three fresh interpreters under
different hash seeds print one digest (the gate's row, since a subprocess needs imports this module
does not carry); the structural predicates hold over the corpus and a sweep with the refusal count
REPORTED; refusal is total over the listed inputs; every plant behaves as declared, the inert one
included. ESTABLISHED: DEPTH_MAX is derived and equals its literal; the deepest level generates; the
imports are exactly the declared substrate (checked from OUTSIDE, by the gate and the suite, because
a module that grades its own imports would need `ast`). DECLARED: the grid size, the room bounds, the
try budget, the draw's modular bias, that rooms belong to the structure, and the layer.
does_not_show — its first clause first: A LEVEL THAT REPRODUCES IS NOT A LEVEL WORTH PLAYING. That
the stairs down are reachable from the stairs up: the corridors join consecutive rooms, so by
construction they are, and CONSTRUCTION IS NOT A WITNESS — the witness and its planted sealed room are
a separate law and are not asserted here. That the placement draw is unbiased (it is `draw mod n`,
declared). That any second implementation reproduces the corpus — the raw pins exist so one can, and
none has. And nothing about canonical GAME STATE: this is one level, not a run; D24 §2's shape is
what a later rung constructs, and this module supplies exactly one of its fields."""
import hashlib
import os as _os

_HERE = _os.path.dirname(_os.path.abspath(__file__))

MAGIC = b"URDRGEN1"

#: D24 §1, answered as DATA rather than inferred from prose. The gate reads these.
LAYER = "CORE"
D24_ANSWER = "affects canonical game state"
#: The whole import surface, declared where the gate and the suite can hold the AST to it.
ALLOWED_IMPORTS = ("hashlib", "os")

#: The canon's constants — NOT inputs. Changing any of them mints a new canon.
W, H = 48, 32
WALL, FLOOR, UP, DOWN = b"#", b".", b"<", b">"
ALPHABET = WALL + FLOOR + UP + DOWN
ROOM_TRIES = 64
ROOMS_MIN, ROOMS_MAX = 2, 8
ROOM_W = (4, 10)                    # inclusive
ROOM_H = (3, 7)                     # inclusive

#: The domain. SEED is a 64-bit word. DEPTH is what a signed 32-bit integer holds, COMPUTED from the
#: width rather than written as a literal — the literal is what the falsifier holds it to.
SEED_BITS = 64
SEED_MAX = (1 << SEED_BITS) - 1
DEPTH_BITS = 32 - 1
DEPTH_MAX = (1 << DEPTH_BITS) - 1


class GamegenError(Exception):
    def __init__(self, message):
        super().__init__(f"GAMEGEN-REFUSE: {message}")
        self.code = "GAMEGEN-REFUSE"


def _refuse(message):
    raise GamegenError(message)


def _is_int(v):
    return type(v) is int           # bool is a subclass of int — excluded on purpose


def check_params(seed, depth):
    """Membership in the admitted domain: a typed refusal at either end, never a clamp."""
    if not (_is_int(seed) and 0 <= seed <= SEED_MAX):
        _refuse(f"seed must be an int in 0..{SEED_MAX}, got {seed!r}")
    if not (_is_int(depth) and 1 <= depth <= DEPTH_MAX):
        _refuse(f"depth must be an int in 1..{DEPTH_MAX}, got {depth!r}")


# ---- the draw ------------------------------------------------------------------------------------------
def _draw(seed, depth, tag, i):
    """Stateless: the draw depends on its own preimage and on nothing that happened before it."""
    d = hashlib.sha256(b"%s|%d|%d|%s|%d" % (MAGIC, seed, depth, tag.encode(), i)).digest()
    return int.from_bytes(d[:8], "big")


def _below(seed, depth, tag, i, n):
    """A draw in 0..n-1 — `draw mod n`, declared: the bias is part of the canon."""
    return _draw(seed, depth, tag, i) % n


# ---- the level -------------------------------------------------------------------------------------------
class Level:
    """The canonical output. Immutable by convention: `cells` is a tuple of `bytes` rows and `rooms`
    a tuple of (x, y, w, h) in SORTED order. Rooms are STRUCTURE, not decoration, because the next
    structural law will need to name one."""
    __slots__ = ("seed", "depth", "w", "h", "cells", "rooms")

    def __init__(self, seed, depth, w, h, cells, rooms):
        self.seed, self.depth, self.w, self.h = seed, depth, w, h
        self.cells, self.rooms = tuple(cells), tuple(rooms)

    def cell(self, x, y):
        return self.cells[y][x:x + 1]

    def replaced(self, **kw):
        """A copy with fields replaced — how every plant is built, so the original is never edited."""
        vals = {k: getattr(self, k) for k in self.__slots__}
        vals.update(kw)
        return Level(**vals)


def _center(room):
    x, y, w, h = room
    return x + w // 2, y + h // 2


def _overlaps(a, b, margin=1):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (ax + aw + margin <= bx or bx + bw + margin <= ax
                or ay + ah + margin <= by or by + bh + margin <= ay)


def _carve(grid, x, y):
    if grid[y][x:x + 1] == WALL:
        grid[y][x:x + 1] = FLOOR


def generate(seed, depth, tries=ROOM_TRIES, defect=False):
    """The generator. `tries` and `defect` exist ONLY for plants — the reference always passes the
    defaults — and neither is an input to the canon."""
    check_params(seed, depth)
    rooms = []
    for i in range(tries):
        rw = ROOM_W[0] + _below(seed, depth, "room-w", i, ROOM_W[1] - ROOM_W[0] + 1)
        rh = ROOM_H[0] + _below(seed, depth, "room-h", i, ROOM_H[1] - ROOM_H[0] + 1)
        x = 1 + _below(seed, depth, "room-x", i, W - 1 - rw)      # x + rw <= W - 1
        y = 1 + _below(seed, depth, "room-y", i, H - 1 - rh)      # y + rh <= H - 1
        cand = (x, y, rw, rh)
        if any(_overlaps(cand, r) for r in rooms):
            continue
        rooms.append(cand)
        if len(rooms) == ROOMS_MAX:
            break
    if len(rooms) < ROOMS_MIN:
        _refuse(f"seed {seed} depth {depth}: {len(rooms)} room(s) kept in {tries} tries, "
                f"fewer than ROOMS_MIN={ROOMS_MIN} — the admission condition")
    grid = [bytearray(WALL * W) for _y in range(H)]
    for (x, y, rw, rh) in rooms:
        for yy in range(y, y + rh):
            grid[yy][x:x + rw] = FLOOR * rw
    for k in range(len(rooms) - 1):
        ax, ay = _center(rooms[k])
        bx, by = _center(rooms[k + 1])
        bend = _below(seed, depth, "bend", k, 2)
        if defect:
            bend ^= 1
        if bend == 0:                                           # horizontal first, at row ay
            for xx in range(min(ax, bx), max(ax, bx) + 1):
                _carve(grid, xx, ay)
            for yy in range(min(ay, by), max(ay, by) + 1):
                _carve(grid, bx, yy)
        else:                                                   # vertical first, at column ax
            for yy in range(min(ay, by), max(ay, by) + 1):
                _carve(grid, ax, yy)
            for xx in range(min(ax, bx), max(ax, bx) + 1):
                _carve(grid, xx, by)
    ux, uy = _center(rooms[0])
    dx, dy = _center(rooms[-1])
    grid[uy][ux:ux + 1] = UP
    grid[dy][dx:dx + 1] = DOWN
    return Level(seed, depth, W, H, (bytes(r) for r in grid), sorted(rooms))


# ---- identity --------------------------------------------------------------------------------------------
def canon_bytes(level):
    """The identity bytes. Rooms are SORTED here, so placement order cannot enter; nothing else does."""
    rooms = ";".join("%d,%d,%d,%d" % r for r in sorted(level.rooms)).encode()
    head = b"%s|s:%d|d:%d|%dx%d|rooms:%s" % (MAGIC, level.seed, level.depth, level.w, level.h, rooms)
    return head + b"|" + b"|".join(level.cells)


def level_digest(level):
    return hashlib.sha256(canon_bytes(level)).hexdigest()


def digest_of(seed, depth):
    return level_digest(generate(seed, depth))


def render(level):
    """The level as text — for a human, and for nothing else; not identity."""
    return "\n".join(row.decode("ascii") for row in level.cells)


# ---- structure: the predicates that are NOT the digest ------------------------------------------------------
def problems(level):
    """Every way a level can be malformed, as (kind, detail). Empty for a well-formed level."""
    bad = []
    if level.w != W or level.h != H or len(level.cells) != H or any(len(r) != W for r in level.cells):
        bad.append(("size", "the grid is not %dx%d" % (W, H)))
        return bad
    for y, row in enumerate(level.cells):
        for x in range(W):
            if row[x:x + 1] not in (WALL, FLOOR, UP, DOWN):
                bad.append(("alphabet", "cell (%d,%d) is %r" % (x, y, row[x:x + 1])))
    for x in range(W):
        if level.cells[0][x:x + 1] != WALL or level.cells[H - 1][x:x + 1] != WALL:
            bad.append(("border", "column %d breaches the top or bottom border" % x))
            break
    for y in range(H):
        if level.cells[y][0:1] != WALL or level.cells[y][W - 1:W] != WALL:
            bad.append(("border", "row %d breaches the left or right border" % y))
            break
    n = len(level.rooms)
    if not (ROOMS_MIN <= n <= ROOMS_MAX):
        bad.append(("rooms-count", "%d rooms, outside %d..%d" % (n, ROOMS_MIN, ROOMS_MAX)))
    if tuple(level.rooms) != tuple(sorted(level.rooms)):
        bad.append(("rooms-sorted", "the rooms are not in canonical order"))
    for i, (x, y, rw, rh) in enumerate(level.rooms):
        if not (1 <= x and x + rw <= W - 1 and 1 <= y and y + rh <= H - 1
                and ROOM_W[0] <= rw <= ROOM_W[1] and ROOM_H[0] <= rh <= ROOM_H[1]):
            bad.append(("room-bounds", "room %d = %r is outside the interior or its size bounds"
                        % (i, (x, y, rw, rh))))
            continue
        for yy in range(y, y + rh):
            if WALL in level.cells[yy][x:x + rw]:
                bad.append(("room-floor", "room %d has a wall cell inside it" % i))
                break
    for i in range(n):
        for j in range(i + 1, n):
            if _overlaps(level.rooms[i], level.rooms[j]):
                bad.append(("room-overlap", "rooms %d and %d overlap or touch" % (i, j)))
    ups = [(x, y) for y, row in enumerate(level.cells) for x in range(W) if row[x:x + 1] == UP]
    downs = [(x, y) for y, row in enumerate(level.cells) for x in range(W) if row[x:x + 1] == DOWN]
    if len(ups) != 1 or len(downs) != 1:
        bad.append(("stairs-count", "%d stairs up and %d stairs down" % (len(ups), len(downs))))
    for kind, pts in (("up", ups), ("down", downs)):
        for (x, y) in pts:
            if not any(rx <= x < rx + rw and ry <= y < ry + rh for (rx, ry, rw, rh) in level.rooms):
                bad.append(("stairs-in-room", "stairs %s at (%d,%d) is in no room" % (kind, x, y)))
    return bad


def is_well_formed(level):
    return not problems(level)


def _set(level, x, y, glyph):
    rows = [bytearray(r) for r in level.cells]
    rows[y][x:x + 1] = glyph
    return level.replaced(cells=tuple(bytes(r) for r in rows))


def _first_wall_outside_rooms(level):
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if level.cell(x, y) == WALL and not any(
                    rx <= x < rx + rw and ry <= y < ry + rh for (rx, ry, rw, rh) in level.rooms):
                return x, y
    raise GamegenError("no wall cell outside every room — the plant has nowhere to stand")


def plants(level):
    """(kind expected, planted level). Every plant edits a COPY of the input; none edits a predicate."""
    ux = uy = None
    for y, row in enumerate(level.cells):
        if UP in row:
            ux, uy = row.index(UP), y
            break
    wx, wy = _first_wall_outside_rooms(level)
    x0, y0, w0, h0 = level.rooms[0]
    out = (
        ("border", _set(level, 0, 0, FLOOR)),
        ("room-overlap", level.replaced(rooms=sorted(level.rooms + ((x0 + 1, y0, w0, h0),)))),
        ("stairs-count", _set(level, x0, y0, UP)),
        ("stairs-in-room", _set(_set(level, ux, uy, FLOOR), wx, wy, UP)),
        ("room-bounds", level.replaced(rooms=sorted(level.rooms + ((W - 3, 1, ROOM_W[1], ROOM_H[0]),)))),
        ("rooms-sorted", level.replaced(rooms=tuple(reversed(level.rooms)))),
    )
    return out


def every_plant_is_caught_by_name(level):
    """(kind, caught). A plant that reddens the wrong predicate is not evidence about the right one."""
    return tuple((kind, any(k == kind for k, _d in problems(planted)))
                 for kind, planted in plants(level))


def the_room_order_is_inert(level):
    """THE INERT PLANT, declared inert: reversing the rooms before serialisation moves NOTHING,
    because identity sorts them. Reported, never hidden — a suite whose every plant bites has not
    shown that a plant CAN fail to bite."""
    return level_digest(level.replaced(rooms=tuple(reversed(level.rooms)))) == level_digest(level)


def a_moved_cell_is_observable(level):
    """One cell changed, digest moved."""
    wx, wy = _first_wall_outside_rooms(level)
    return level_digest(_set(level, wx, wy, FLOOR)) != level_digest(level)


def the_mutated_generator_diverges(seed, depth):
    """`heightfield`'s corpus law, applied: a generator with the opposite corridor bend is a
    plausible generator and MUST move the digest. Reported per member; the corpus row demands all."""
    return level_digest(generate(seed, depth, defect=True)) != digest_of(seed, depth)


def the_admission_condition_is_real(seed=0, depth=1):
    """One try keeps one room, and one room is fewer than ROOMS_MIN: a typed refusal."""
    try:
        generate(seed, depth, tries=1)
    except GamegenError as exc:
        return exc.code == "GAMEGEN-REFUSE" and "admission condition" in str(exc)
    return False


# ---- the domain ------------------------------------------------------------------------------------------
REFUSED_INPUTS = ((-1, 1), (SEED_MAX + 1, 1), (0, 0), (0, DEPTH_MAX + 1), (True, 1), (0, True),
                  (1.0, 1), (0, 1.0), ("0", 1), (0, None))
ADMITTED_CORNERS = ((0, 1), (SEED_MAX, 1), (0, DEPTH_MAX), (SEED_MAX, DEPTH_MAX))


def refusal_is_total():
    """(refused, admitted): every listed bad input refuses typed, every corner is admitted."""
    refused = 0
    for s, d in REFUSED_INPUTS:
        try:
            check_params(s, d)
        except GamegenError as exc:
            refused += exc.code == "GAMEGEN-REFUSE"
    admitted = 0
    for s, d in ADMITTED_CORNERS:
        check_params(s, d)
        admitted += 1
    return refused == len(REFUSED_INPUTS), admitted == len(ADMITTED_CORNERS)


def depth_max_is_derived_not_restated():
    """The representation claim, on its own: the computed bound equals the literal the original
    used, and DEPTH_MAX + 1 does not fit the width it was derived from."""
    return DEPTH_MAX == 2147483647 and DEPTH_MAX == (1 << (32 - 1)) - 1 \
        and (DEPTH_MAX + 1) >> DEPTH_BITS == 1


# ---- the corpus ------------------------------------------------------------------------------------------
#: Eight (seed, depth) pairs, pinned RAW in the conformance file so a second implementation can match
#: one level without reproducing a scene. Both DEPTH_MAX members are the generation claim, run.
CORPUS = ((0, 1), (1, 1), (1, 2), (12345, 1), (0xDEADBEEF, 100), (SEED_MAX, 1),
          (7, DEPTH_MAX), (SEED_MAX, DEPTH_MAX))


def corpus_name(seed, depth):
    return "level-%d-%d" % (seed, depth)


def corpus_digests():
    return tuple((corpus_name(s, d), digest_of(s, d)) for s, d in CORPUS)


def the_corpus_is_distinct():
    ds = [d for _n, d in corpus_digests()]
    return len(set(ds)) == len(ds)


def neighbours_differ(seed=1, depth=1):
    """(s, d) vs (s, d+1) and (s, d) vs (s+1, d)."""
    base = digest_of(seed, depth)
    return base != digest_of(seed, depth + 1) and base != digest_of(seed + 1, depth)


def the_deepest_level_generates():
    """The generation claim: both DEPTH_MAX members generate, are well-formed, and cost the same
    number of tries as depth 1 — which is to say depth reaches nothing but the preimage."""
    out = []
    for s, d in CORPUS:
        if d == DEPTH_MAX:
            lv = generate(s, d)
            out.append((s, is_well_formed(lv), len(lv.rooms)))
    return tuple(out)


def sweep(seeds=range(128), depth=1):
    """(generated, refused, malformed, min_rooms, max_rooms) — the admission condition MEASURED."""
    gen = ref = mal = 0
    lo, hi = ROOMS_MAX + 1, 0
    for s in seeds:
        try:
            lv = generate(s, depth)
        except GamegenError:
            ref += 1
            continue
        gen += 1
        mal += not is_well_formed(lv)
        lo, hi = min(lo, len(lv.rooms)), max(hi, len(lv.rooms))
    return gen, ref, mal, lo, hi


# ---- scenes ---------------------------------------------------------------------------------------------------
SCENES = ("corpus", "structure", "plants")


def scene_case(name):
    if name == "corpus":
        return "|".join("%s=%s" % nd for nd in corpus_digests()) + "|distinct=%s|neighbours=%s" % (
            the_corpus_is_distinct(), neighbours_differ())
    if name == "structure":
        return "sweep1=%s|sweepmax=%s|deepest=%s|derived=%s|refusal=%s" % (
            sweep(), sweep(range(16), DEPTH_MAX), the_deepest_level_generates(),
            depth_max_is_derived_not_restated(), refusal_is_total())
    if name == "plants":
        lv = generate(*CORPUS[0])
        return "caught=%s|inert=%s|moved=%s|mutated=%s|admission=%s" % (
            every_plant_is_caught_by_name(lv), the_room_order_is_inert(lv),
            a_moved_cell_is_observable(lv),
            tuple(the_mutated_generator_diverges(s, d) for s, d in CORPUS),
            the_admission_condition_is_real())
    raise GamegenError(f"no scene named {name!r}")


def scene_result(name):
    return hashlib.sha256(MAGIC + b"|" + name.encode() + b"|"
                          + scene_case(name).encode()).hexdigest()


def gamegen_digest():
    return hashlib.sha256(MAGIC + b"|" + "|".join(scene_result(n)
                                                  for n in SCENES).encode()).hexdigest()


def golden(name):
    """READ from the committed corpus. An unpinned name REFUSES typed rather than returning a default."""
    with open(_os.path.join(_HERE, "conformance_gamegen.txt"), encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                nm, dig = ln.split()
                if nm == name:
                    return dig
    raise GamegenError(f"no golden named {name!r}")


def emitted_matches_pinned():
    """Scenes AND the eight raw level pins. The corpus is what this module EMITS, frozen rather than
    regenerated by the gate, because a golden the gate rewrites cannot detect drift."""
    return (all(scene_result(n) == golden(n) for n in SCENES)
            and gamegen_digest() == golden("gamegen")
            and all(golden(n) == d for n, d in corpus_digests()))


def an_unpinned_name_refuses():
    try:
        golden("not-a-pinned-level")
    except GamegenError as exc:
        return exc.code == "GAMEGEN-REFUSE"
    return False


def main():
    print("GAMEGEN — seed + depth -> canonical level -> digest, and nothing else (URDRGEN1)")
    print("layer %s: %s | imports %s" % (LAYER, D24_ANSWER, ALLOWED_IMPORTS))
    print("depth bound derived %d == literal 2147483647: %s"
          % (DEPTH_MAX, depth_max_is_derived_not_restated()))
    print()
    lv = generate(*CORPUS[0])
    print(render(lv))
    print("seed %d depth %d rooms %d digest %s" % (lv.seed, lv.depth, len(lv.rooms), level_digest(lv)))
    print()
    for n, d in corpus_digests():
        print("%-32s %s" % (n, d))
    print("distinct               :", the_corpus_is_distinct())
    print("deepest generates      :", the_deepest_level_generates())
    print("sweep depth 1          :", sweep())
    print("sweep depth DEPTH_MAX  :", sweep(range(16), DEPTH_MAX))
    print("refusal total          :", refusal_is_total())
    print("plants caught by name  :", every_plant_is_caught_by_name(lv))
    print("room order INERT       :", the_room_order_is_inert(lv))
    print("moved cell observable  :", a_moved_cell_is_observable(lv))
    print("mutated generator moves:", tuple(the_mutated_generator_diverges(s, d) for s, d in CORPUS))
    print("admission condition    :", the_admission_condition_is_real())
    print()
    for n in SCENES:
        print(n, scene_result(n))
    print("gamegen", gamegen_digest())
    print()
    print("does_not_show: a level that reproduces is not a level worth playing; reachability")
    print("(construction is not a witness); an unbiased draw; any second implementation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
