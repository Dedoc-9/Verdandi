# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""descend — the authoritative depth transition: stand on the down-stairs, arrive at the next floor
(URDRDEP1).

THE SIXTH GAME-LAYER VERTICAL SLICE. `gamegen` makes one level from `(seed, depth)`; `descent`
witnesses that its stairs connect; `move` steps an entity within a level; `entity` names it; `rngstream`
holds the run's stream. None of them CHANGES DEPTH — the run is stuck on one floor. This rung is the
single authoritative `D_n -> D_{n+1}` that advances it: an entity standing on the down-stairs of the
level at depth `d` arrives at the level at depth `d+1`, at that level's own stairs-up.

IT CONSUMES AUTHORITY IT DOES NOT OWN, AND OWNS EXACTLY ONE NEW THING.
  * DEPTH is `gamegen`'s. The bound `DEPTH_MAX`, the admission of `d+1`, and the ceiling refusal are all
    `gamegen.check_params`; this module NAMES no `DEPTH_MAX` of its own (checked on its AST) and adds no
    second depth law. It ASKS `gamegen` whether `d+1` is admissible BEFORE it generates anything.
  * THE SUCCESSOR LEVEL is `gamegen`'s: `gamegen.generate(seed, d+1)`, the same seed, one deeper. Its
    identity is `gamegen.level_digest`, unchanged.
  * THE STAIRS are `descent`'s: `descent.endpoints(level)` locates the unique down-stairs (the precondition)
    and the successor's unique up-stairs (the arrival). This module re-locates and re-proves neither.
  * THE ARRIVAL POSITION is the successor's authoritative SPAWN — `descent.endpoints(level').up`, which is
    `move.spawn(level')` — traversable by construction, so descend does NOT re-prove it traversable; it
    consumes the spawn rule rather than inventing a teleport.
  * THE ONE NEW THING is the depth transition itself and its single precondition: you may descend only from
    the down-stairs. `DESCEND-REFUSE` iff the supplied position is not the level's unique down endpoint.

WHY THE OLD POSITION HAS NO AUTHORITY IN THE NEW LEVEL — the measurement that fixed the arrival. The
successor's layout is generated INDEPENDENTLY from `(seed, d+1)`, so the old down-stairs coordinate is not
even reliably traversable there (measured: it is a wall in some successors). Carrying the entity to its old
`(x, y)` would land it in a wall. The only authoritative successor position is the new level's stairs-up,
which is why the arrival is `move.spawn(level')` and nothing else.

OWNERSHIP STAYS CRISP, WHICH IS THE POINT OF A NARROW LAW.
    malformed / invalid level      -> `descent` / `gamegen` (their refusals)
    invalid command                -> `move`
    blocked movement (D_{n+1}=D_n) -> `move` (never an arrival on the down-stairs)
    depth ceiling (d = DEPTH_MAX)  -> `gamegen` (GAMEGEN-REFUSE, inherited)
    valid arrival on the down-stairs -> `descend`
    descend invoked off the down-stairs -> `descend` (DESCEND-REFUSE)

RNG IS UNTOUCHED. The successor is fully determined by `(seed, d+1)`, so no draw is consumed: `descend`
never receives or returns a stream, and imports no `rngstream` — the independence is structural, and a law
reads it off this module's AST.

GRADE (honest, D5). MEASURED: over the corpus, a descent from the down-stairs produces `gamegen.generate(
seed, d+1)` with the entity at that level's stairs-up, and the successor identity is exactly the existing
canonical state vocabulary for `(level', spawn)`; at `DEPTH_MAX - 1` the successor is depth `DEPTH_MAX`,
matching `gamegen.generate(seed, DEPTH_MAX)`. ESTABLISHED: the arrival equals `move.spawn(level')`; the
ceiling (`d = DEPTH_MAX`) refuses through `gamegen`'s authority WITHOUT generating a successor and without
mutating the input, and this module names no `DEPTH_MAX`; descending off the down-stairs refuses typed
DESCEND-REFUSE while a malformed level surfaces `descent`'s DESCENT-REFUSE; this module imports no
`rngstream`. DECLARED: that a descent begins at the successor's stairs-up — a fresh floor from the top, the
FATE model — and that there is no ascent in this rung (a later law, if earned). does_not_show: that the
successor level is worth playing or reachable (`gamegen`'s and `descent`'s claims, unchanged); that the
entity carries anything but its position across the transition (health/inventory are later fields, and
descend touches none of them); that the RNG advances on a descent (it does not, and whether any real action
ever advances it is `rngstream`'s and `loot`'s question); and that two floors relate in any way beyond
seed and depth+1."""
import hashlib
import os as _os

_HERE = _os.path.dirname(_os.path.abspath(__file__))
if _HERE not in __import__("sys").path:
    __import__("sys").path.insert(0, _HERE)
import gamegen as _G                                                      # noqa: E402
import descent as _D                                                     # noqa: E402

MAGIC = b"URDRDEP1"

LAYER = "CORE"
D24_ANSWER = "affects canonical game state — the authoritative depth transition"
ALLOWED_IMPORTS = ("hashlib", "os", "gamegen", "descent")


class DescendError(Exception):
    def __init__(self, message):
        super().__init__(f"DESCEND-REFUSE: {message}")
        self.code = "DESCEND-REFUSE"


def _require_on_down(level, pos):
    """The ONE new precondition, and the only refusal this module owns. `descent.endpoints` is the
    authority: it raises `DESCENT-REFUSE` for a malformed level (absent or doubled stairs — not this
    module's to answer), and otherwise returns the unique down-stairs. You may descend only from it."""
    _up, down = _D.endpoints(level)              # DESCENT-REFUSE for a malformed level — descent's
    if pos != down:
        raise DescendError(f"descend requires the entity on the down-stairs {down}, got {pos!r}")
    return down


def descend(level, pos):
    """THE AUTHORITATIVE DEPTH TRANSITION. From the down-stairs of the level at depth `d`, return the
    successor `(level', pos')`: the level at depth `d+1` from the SAME seed, with the entity at that
    level's stairs-up. The ceiling is asked of `gamegen` BEFORE anything is generated, so at
    `d = DEPTH_MAX` this refuses `GAMEGEN-REFUSE` without building a successor and without a `DEPTH_MAX`
    of its own."""
    _require_on_down(level, pos)
    # THE CEILING, EXPLICIT AND INHERITED: gamegen's depth law decides admissibility, and it decides it
    # WITHOUT generating. At d = DEPTH_MAX this raises GAMEGEN-REFUSE here, before `generate` is reached.
    _G.check_params(level.seed, level.depth + 1)
    level_next = _G.generate(level.seed, level.depth + 1)
    pos_next = _D.endpoints(level_next)[0]        # the successor's stairs-up — its authoritative spawn
    return level_next, pos_next


# ---- identity, in the ONE existing canonical-state vocabulary --------------------------------------------
def successor_state_digest(level, pos):
    """The successor's canonical identity, composed in the SAME vocabulary `move` uses for a `(level,
    entity)` state — `move.state_digest(level', pos')` — so descend introduces no second serialization:
    the state it lands in is named the way every canonical `(level, entity)` state is. `move` is imported
    lazily so this module's declared substrate stays `(gamegen, descent)`."""
    import move as _M
    level_next, pos_next = descend(level, pos)
    return _M.state_digest(level_next, pos_next)


# ---- the laws / falsifiers -----------------------------------------------------------------------------
def _down_of(seed, depth):
    lv = _G.generate(seed, depth)
    return lv, _D.endpoints(lv)[1]


def the_successor_position_is_the_authoritative_spawn(seed, depth):
    """The arrival is the successor's stairs-up, which IS `move.spawn(level')` — consumed, not re-proved.
    So descend re-derives no spawn rule and re-checks no traversability; it inherits both."""
    import move as _M
    lv, down = _down_of(seed, depth)
    level_next, pos_next = descend(lv, down)
    return (pos_next == _D.endpoints(level_next)[0]
            and pos_next == _M.spawn(level_next)
            and _D.traversable(level_next, *pos_next))


def the_successor_reproduces_gamegen(seed, depth):
    """The successor level is `gamegen`'s own, one deeper, same seed — its identity is
    `gamegen.level_digest`, unchanged, and the seed is preserved."""
    lv, down = _down_of(seed, depth)
    level_next, _pos = descend(lv, down)
    return (_G.level_digest(level_next) == _G.digest_of(seed, depth + 1)
            and level_next.seed == seed and level_next.depth == depth + 1)


def the_ceiling_refuses_without_generating(seed):
    """At `d = DEPTH_MAX`, descend refuses `GAMEGEN-REFUSE` (gamegen's authority, not a code of ours),
    and it does so BEFORE generating a successor — the boundary ORDERING, not merely that a refusal
    propagates. Proved three ways: the code is gamegen's; the input level is unchanged after the refused
    call (no mutation); and this module's source contains no `DEPTH_MAX` literal, so it holds no second
    depth law. Returns (refused_gamegen, input_unchanged, no_depth_max_literal)."""
    lv, down = _down_of(seed, _G.DEPTH_MAX)
    before = _G.level_digest(lv)
    refused = False
    try:
        descend(lv, down)
    except _G.GamegenError as exc:
        refused = exc.code == "GAMEGEN-REFUSE"
    unchanged = _G.level_digest(lv) == before
    import ast
    with open(_os.path.join(_HERE, "descend.py"), encoding="utf-8") as fh:
        names = {n.id for n in ast.walk(ast.parse(fh.read())) if isinstance(n, ast.Name)}
    no_literal = "DEPTH_MAX" not in names
    return refused, unchanged, no_literal


def the_boundary_below_the_ceiling_descends(seed=7):
    """The complementary POSITIVE witness at the other side of the boundary: from `DEPTH_MAX - 1` a
    descent produces depth `DEPTH_MAX`, and the successor identity is exactly `gamegen.generate(seed,
    DEPTH_MAX)`. Tests the boundary on both sides rather than only its refusal."""
    lv, down = _down_of(seed, _G.DEPTH_MAX - 1)
    level_next, _pos = descend(lv, down)
    return (level_next.depth == _G.DEPTH_MAX
            and _G.level_digest(level_next) == _G.digest_of(seed, _G.DEPTH_MAX))


def descending_off_the_down_stairs_refuses(seed, depth):
    """The one new refusal: from any cell that is not the down-stairs — the stairs-up, and a plain floor
    cell — descend refuses typed DESCEND-REFUSE. A malformed level (no unique down) is NOT this module's
    refusal; it surfaces `descent`'s DESCENT-REFUSE, checked separately below."""
    lv = _G.generate(seed, depth)
    up, down = _D.endpoints(lv)
    # a floor cell that is neither stair
    floor = None
    for y in range(lv.h):
        for x in range(lv.w):
            if lv.cells[y][x:x + 1] == _G.FLOOR:
                floor = (x, y)
                break
        if floor:
            break
    refused = 0
    for bad in (up, floor):
        try:
            descend(lv, bad)
        except DescendError as exc:
            refused += exc.code == "DESCEND-REFUSE"
    return refused == 2


def a_malformed_level_is_descents_refusal_not_ours(seed=0, depth=1):
    """OWNERSHIP: a level with no down-stairs is outside `descent`'s domain, so descend's precondition
    surfaces DESCENT-REFUSE (descent's), never DESCEND-REFUSE — the malformed-input refusal stays with
    the authority that owns the shape."""
    lv = _G.generate(seed, depth)
    _up, down = _D.endpoints(lv)
    no_down = lv.replaced(cells=tuple(
        bytes(bytearray(r).replace(_G.DOWN, _G.FLOOR)) for r in lv.cells))
    try:
        descend(no_down, down)
    except _D.DescentError as exc:
        return exc.code == "DESCENT-REFUSE"
    except DescendError:
        return False
    return False


def this_module_touches_no_rng():
    """The independence constraint, STRUCTURAL: descend imports no `rngstream` (declared substrate and
    full AST both), so a descent cannot consume or mutate the stream — it never holds one."""
    if "rngstream" in ALLOWED_IMPORTS:
        return False
    import ast
    with open(_os.path.join(_HERE, "descend.py"), encoding="utf-8") as fh:
        found = set()
        for node in ast.walk(ast.parse(fh.read())):
            if isinstance(node, ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                found.add((node.module or "").split(".")[0])
    return "rngstream" not in found


def refuse_is_total(seed=0, depth=1):
    """(off_stairs, malformed_is_descents, ceiling_is_gamegens): each malformed invocation refuses to
    the authority that owns it, never inventing a parallel code."""
    return (descending_off_the_down_stairs_refuses(seed, depth),
            a_malformed_level_is_descents_refusal_not_ours(),
            the_ceiling_refuses_without_generating(seed)[0])


# ---- scenes --------------------------------------------------------------------------------------------
#: The corpus is `gamegen`'s. Members with depth < DEPTH_MAX descend to a successor; the two DEPTH_MAX
#: members exercise the ceiling refusal. A synthetic DEPTH_MAX-1 member is the positive boundary witness.
CORPUS = _G.CORPUS
SCENES = ("transition", "boundary", "laws")


def transition_row(seed, depth):
    """From the down-stairs at (seed, depth), the successor depth, its stairs-up, and the successor's
    canonical state identity in the one vocabulary — a compact, reproducible witness of one descent."""
    lv, down = _down_of(seed, depth)
    level_next, pos_next = descend(lv, down)
    return (_G.corpus_name(seed, depth), level_next.depth, pos_next,
            successor_state_digest(lv, down)[:16])


def scene_case(name):
    if name == "transition":
        rows = []
        for s, d in CORPUS:
            if d >= _G.DEPTH_MAX:
                continue                                     # ceiling members go in `boundary`
            n, dep, pos, dig = transition_row(s, d)
            rows.append("%s->d%d@%d,%d:%s" % (n, dep, pos[0], pos[1], dig))
        return "|".join(rows)
    if name == "boundary":
        ceil = []
        for s, d in CORPUS:
            if d == _G.DEPTH_MAX:
                ceil.append("%s:ceiling=%s" % (_G.corpus_name(s, d),
                                               the_ceiling_refuses_without_generating(s)))
        return "below=%s|%s" % (the_boundary_below_the_ceiling_descends(), "|".join(ceil))
    if name == "laws":
        base = [(s, d) for s, d in CORPUS if d < _G.DEPTH_MAX]
        return "spawn=%s|reproduces=%s|offstairs=%s|malformed=%s|norng=%s|refuse=%s" % (
            tuple(the_successor_position_is_the_authoritative_spawn(s, d) for s, d in base),
            tuple(the_successor_reproduces_gamegen(s, d) for s, d in base),
            tuple(descending_off_the_down_stairs_refuses(s, d) for s, d in base),
            a_malformed_level_is_descents_refusal_not_ours(),
            this_module_touches_no_rng(), refuse_is_total())
    raise DescendError(f"no scene named {name!r}")


def scene_result(name):
    return hashlib.sha256(MAGIC + b"|" + name.encode() + b"|"
                          + scene_case(name).encode()).hexdigest()


def descend_digest():
    return hashlib.sha256(MAGIC + b"|" + "|".join(scene_result(n)
                                                  for n in SCENES).encode()).hexdigest()


def golden(name):
    with open(_os.path.join(_HERE, "conformance_descend.txt"), encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                nm, dig = ln.split()
                if nm == name:
                    return dig
    raise DescendError(f"no golden named {name!r}")


def emitted_matches_pinned():
    return (all(scene_result(n) == golden(n) for n in SCENES)
            and descend_digest() == golden("descend"))


def an_unpinned_name_refuses():
    try:
        golden("not-a-scene")
    except DescendError as exc:
        return exc.code == "DESCEND-REFUSE"
    return False


def main():
    print("DESCEND — the authoritative depth transition: from the down-stairs to the next floor (URDRDEP1)")
    print("layer %s: %s | imports %s" % (LAYER, D24_ANSWER, ALLOWED_IMPORTS))
    print()
    lv, down = _down_of(0, 1)
    level_next, pos_next = descend(lv, down)
    print("descend (seed 0, depth 1) from down-stairs %s -> depth %d at stairs-up %s"
          % (down, level_next.depth, pos_next))
    print("successor identity (one vocabulary):", successor_state_digest(lv, down)[:16])
    print()
    print("successor is the authoritative spawn :", the_successor_position_is_the_authoritative_spawn(0, 1))
    print("successor reproduces gamegen         :", the_successor_reproduces_gamegen(0, 1))
    print("ceiling refuses w/o generating       :", the_ceiling_refuses_without_generating(7))
    print("DEPTH_MAX-1 descends to DEPTH_MAX     :", the_boundary_below_the_ceiling_descends())
    print("off the down-stairs refuses          :", descending_off_the_down_stairs_refuses(0, 1))
    print("malformed level is descent's refusal :", a_malformed_level_is_descents_refusal_not_ours())
    print("this module touches no rng           :", this_module_touches_no_rng())
    print()
    for n in SCENES:
        print(n, scene_result(n))
    print("descend", descend_digest())
    print()
    print("does_not_show: whether the successor is worth playing or reachable (gamegen's/descent's); that")
    print("the entity carries anything but position; that the RNG advances on a descent (it does not);")
    print("and any relation between floors beyond seed and depth+1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
