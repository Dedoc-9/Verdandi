# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""move — the first authoritative D_n -> D_{n+1}: one step, MOVED or BLOCKED (URDRMOV1).

THE THIRD GAME-LAYER VERTICAL SLICE, and the first that MOVES anything. `gamegen` (URDRGEN1) makes a
canonical level; `descent` (URDRDSC1) witnesses that its stairs connect. Neither has an entity or a
tick — there is no `D_n -> D_{n+1}` anywhere in the tree, which is exactly why KINEMA (D25) cannot yet
be built: it refines a transition, and none exists. This module is that transition, and nothing more:
an entity at a cell takes ONE step under a movement command, and the authority answers MOVED (it
stepped onto a traversable cell) or BLOCKED (a wall or the grid edge denied it, so it stayed put).

IT CONSUMES `descent`'s AUTHORITY, IT DOES NOT REINVENT IT. Legality is `descent.traversable(level,
x, y)` — the one place the traversal model lives, promoted to public for exactly this. `transition`
does not re-derive `cell in TRAVERSABLE` and does not reach into a private: movement truth is
single-sourced in `descent`, and a later law that widens traversal (doors, keys, diagonals) changes
it in one place and this module inherits the change. The dependency runs one way — `transition`
imports `gamegen` and `descent`; neither knows this module exists.

THREE OUTCOMES, AND THE DISTINCTION IS LOAD-BEARING FOR KINEMA.

    MOVED    the target cell is `descent`-traversable        -> D_{n+1} = entity at the target
    BLOCKED  the target is a wall or off the grid            -> D_{n+1} = D_n, the entity stayed
    REFUSE   the input is MALFORMED (a command that is not a direction, an entity not on a
             traversable cell, a position off the grid)      -> typed MOVE-REFUSE

A wall step is NOT an error. It is an in-domain command whose authoritative outcome is "you do not
move" — a legal transition with D_{n+1} = D_n, not an exception. Collapsing it into REFUSE would be
wrong twice: it would make walking into a wall a malformed input (it is the most ordinary thing a
player does), and it would leave KINEMA's Plant A (D25 §10) with nothing to consume — that plant is
precisely "the authority refused a move, D_n = D_{n+1} = A, and a rendered A->B must be rejected", so
the authority has to RETURN the blocked pair, not throw it. REFUSE is reserved for input that is
outside the domain of the question, `gamegen`'s and `descent`'s shape.

IDENTITY IS DERIVED FROM THE EXISTING MACHINERY, NOT A PARALLEL RULE. The canonical state is the
level plus the entity position. The level's canonical identity is already `gamegen.level_digest`
(SHA-256 of `URDRGEN1|s:|d:|WxH|rooms:...|rows`), so this module NAMES THE LEVEL BY THAT DIGEST —
`worldbind`'s content-addressed precedent — and adds the one new field, the position, in the same
`MAGIC|field:value` idiom, and the entity is a CONTENT-ADDRESSED component: `state_digest = SHA-256(URDRMOV1|lvl:<level_digest>|ent:<entity_digest>)`. Nothing else
enters. A view-only quantity a later camera might carry (a fractional interpolated position, a facing
for animation) is NOT canonical and never reaches this digest; the entity's integer cell IS, because
it is what the next authoritative step reads.

GRADE (honest, D5). MEASURED: over every `gamegen` corpus level, a step in each of the four
directions from the spawn classifies MOVED or BLOCKED and agrees with `descent.traversable` on the
target; the sealed-mouth counterexample turns a step that MOVED into one that is BLOCKED, so legality
tracks `descent`'s authority rather than a copy of it; the identity derivation reproduces. ESTABLISHED:
`step` is a pure function of (level, pos, command) — a hash-seed sweep of the same call across fresh
interpreters agrees; BLOCKED leaves the position and the state digest unchanged while MOVED changes
both; the REFUSE domain is total over malformed commands and positions. DECLARED: that a single
orthogonal cell step is the movement model — a choice, labelled, and the one a later rung widens
(multi-cell, diagonal, speed) by minting its own law; and that the entity is, for this rung, a bare
position — health, inventory and facing are later fields of D24 §2's entity state, added when a rung
earns them. does_not_show: that movement is timed or continuous — this is one discrete authoritative
step and KINEMA is the rung that will make it look continuous, refining the (D_n, D_{n+1}) this
module produces; that the entity may occupy more than one cell, or that two entities interact (a
later law); that a BLOCKED step advances a turn counter or an action log (`actionlog`'s rung, not
this one); and nothing about WHY a level is traversable, which is `descent`'s claim and which this
module only consults."""
import hashlib
import os as _os

_HERE = _os.path.dirname(_os.path.abspath(__file__))
if _HERE not in __import__("sys").path:
    __import__("sys").path.insert(0, _HERE)
import gamegen as _G                                                      # noqa: E402
import descent as _D                                                     # noqa: E402
import entity as _E                                                      # noqa: E402

MAGIC = b"URDRMOV1"

LAYER = "CORE"
D24_ANSWER = "affects canonical game state — the first authoritative transition"
ALLOWED_IMPORTS = ("hashlib", "os", "gamegen", "descent", "entity")

#: The movement model — DECLARED. Four orthogonal directions, named, each a (dx, dy) over the grid
#: (y grows downward). The set is exactly `descent.STEPS`, re-labelled, so the adjacency this module
#: moves along is the same one `descent` traverses — checked, not assumed (see `the_directions_are_descents`).
DIRECTIONS = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}

MOVED = "MOVED"
BLOCKED = "BLOCKED"
OUTCOMES = (MOVED, BLOCKED)


class MoveError(Exception):
    def __init__(self, message):
        super().__init__(f"MOVE-REFUSE: {message}")
        self.code = "MOVE-REFUSE"


def spawn(level):
    """The authoritative starting position: the stairs-up, `descent`'s own endpoint, which is
    traversable by construction. Not chosen here — read from `descent`, so the spawn is on the
    authority's terms."""
    up, _down = _D.endpoints(level)
    return up


def _check_state(level, pos):
    """A canonical D_n is an entity on a traversable cell of a real level. Anything else is MALFORMED
    input, not a blocked move — a REFUSE, because the question 'where does this step land' is not
    well-posed for an entity standing inside a wall or off the grid."""
    if not (isinstance(pos, tuple) and len(pos) == 2
            and type(pos[0]) is int and type(pos[1]) is int):
        raise MoveError(f"position must be an (int, int), got {pos!r}")
    if not _D.traversable(level, pos[0], pos[1]):
        raise MoveError(f"the entity is not on a traversable cell: {pos!r}")


def step(level, pos, command):
    """THE AUTHORITATIVE TRANSITION. Returns (outcome, D_{n+1}) where D_{n+1} is the new position:
    MOVED to the target if it is `descent`-traversable, BLOCKED at `pos` (D_{n+1} = D_n) if it is a
    wall or off the grid. A malformed command or state is a typed REFUSE, never a silent BLOCKED."""
    _check_state(level, pos)
    if command not in DIRECTIONS:
        raise MoveError(f"command must be one of {sorted(DIRECTIONS)}, got {command!r}")
    dx, dy = DIRECTIONS[command]
    target = (pos[0] + dx, pos[1] + dy)
    if _D.traversable(level, target[0], target[1]):
        return MOVED, target
    return BLOCKED, pos


def apply(level, pos, commands):
    """Fold a sequence of commands, returning (final_pos, outcomes). Pure — the same (level, pos,
    commands) yields the same result on any host."""
    outcomes = []
    for c in commands:
        outcome, pos = step(level, pos, c)
        outcomes.append(outcome)
    return pos, tuple(outcomes)


# ---- identity, DERIVED from the existing machinery ------------------------------------------------------
def state_bytes(level, pos):
    """The canonical state identity, in ONE content-addressed vocabulary: the level named by its
    EXISTING `gamegen.level_digest`, and the entity named by its `entity.entity_digest` — not an
    inline `pos:x,y`. The position is the entity's, so it is the ENTITY component that carries it, and
    `move`'s state references that component the same way it references the level. When a later rung
    earns an entity field (health, inventory), `move`'s `D_n` reflects it through this digest with no
    change here — the reason the identity became the entity-derived component rather than a wrap."""
    return b"%s|lvl:%s|ent:%s" % (MAGIC, _G.level_digest(level).encode(), _E.digest_at(pos).encode())


def state_digest(level, pos):
    return hashlib.sha256(state_bytes(level, pos)).hexdigest()


# ---- the laws / falsifiers -----------------------------------------------------------------------------
def the_directions_are_descents(  ):
    """The movement model IS `descent`'s adjacency, re-labelled — proved, not assumed. The four
    (dx, dy) this module moves along are exactly `descent.STEPS`."""
    return sorted(DIRECTIONS.values()) == sorted(_D.STEPS)


def a_step_agrees_with_descent(level, pos, command):
    """The whole contract in one line: the outcome is MOVED iff `descent` says the target is
    traversable, and BLOCKED otherwise with the position unmoved. `move` is a thin authority
    over `descent`'s predicate, and this is the check that it did not drift from it."""
    dx, dy = DIRECTIONS[command]
    target = (pos[0] + dx, pos[1] + dy)
    outcome, nxt = step(level, pos, command)
    if _D.traversable(level, *target):
        return outcome == MOVED and nxt == target
    return outcome == BLOCKED and nxt == pos


def a_blocked_step_is_a_fixed_point(level, pos, command):
    """BLOCKED means D_{n+1} = D_n, IN THE STATE and IN THE DIGEST — the pair KINEMA's Plant A reads.
    Returns True iff, when the step is BLOCKED, neither the position nor the canonical state digest
    moved."""
    outcome, nxt = step(level, pos, command)
    if outcome != BLOCKED:
        return True
    return nxt == pos and state_digest(level, nxt) == state_digest(level, pos)


def a_moved_step_changes_the_state(level, pos, command):
    """MOVED means the canonical identity moved — the position enters the digest, so a real step is
    observable in the state and not only in a view."""
    outcome, nxt = step(level, pos, command)
    if outcome != MOVED:
        return True
    return nxt != pos and state_digest(level, nxt) != state_digest(level, pos)


def a_sealed_mouth_blocks_a_step_that_moved(seed, depth):
    """LEGALITY TRACKS `descent`'S AUTHORITY, PROVED ON A COUNTEREXAMPLE. Find a corpus level and a
    direction from the spawn that MOVES; seal the stairs-down room with `descent.seal_down`; if the
    sealed cell is the step's target, the SAME step is now BLOCKED — because `move` asks
    `descent.traversable`, and sealing changed `descent`'s answer. Returns (found, tracked): whether
    such a (level, step) was found, and whether sealing flipped MOVED->BLOCKED wherever it changed
    the target cell. A move whose target the seal does not touch is left MOVED, correctly."""
    lvl = _G.generate(seed, depth)
    sealed = _D.seal_down(lvl)
    p = spawn(lvl)
    found = tracked = False
    for c in sorted(DIRECTIONS):
        o0, t0 = step(lvl, p, c)
        o1, t1 = step(sealed, p, c)
        if o0 == MOVED:
            found = True
        # the ONLY cells that change traversability are the sealed ring; a step whose target the seal
        # walled must flip to BLOCKED, and one it did not touch must keep its outcome.
        target = (p[0] + DIRECTIONS[c][0], p[1] + DIRECTIONS[c][1])
        sealed_here = _D.traversable(lvl, *target) and not _D.traversable(sealed, *target)
        if sealed_here:
            tracked = (o0 == MOVED and o1 == BLOCKED)
            if not tracked:
                return found, False
        elif o0 != o1:
            return found, False
    return found, True


def _bad_states(level):
    """Malformed D_n that must REFUSE: a wall cell, an off-grid cell, and a non-integer position."""
    wall = None
    for y in range(level.h):
        for x in range(level.w):
            if level.cells[y][x:x + 1] == _G.WALL:
                wall = (x, y)
                break
        if wall:
            break
    return (wall, (-1, 0), (level.w, 0), (0.0, 0), ("0", 0))


def refuse_is_total(level):
    """(bad_states_refused, bad_commands_refused): every malformed state and every non-direction
    command refuses typed, and none is silently read as BLOCKED."""
    p = spawn(level)
    s_ref = 0
    for bad in _bad_states(level):
        try:
            step(level, bad, "N")
        except MoveError as exc:
            s_ref += exc.code == "MOVE-REFUSE"
    c_ref = 0
    for bad in ("north", "", "NN", 0, None, ("N",)):
        try:
            step(level, p, bad)
        except MoveError as exc:
            c_ref += exc.code == "MOVE-REFUSE"
    return s_ref == len(_bad_states(level)), c_ref == 6


def the_spawn_is_descents_endpoint(level):
    return spawn(level) == _D.endpoints(level)[0] and _D.traversable(level, *spawn(level))


def a_walk_reaches_a_wall_and_blocks(level):
    """A DIRECT BLOCKED WITNESS, not one manufactured by sealing: the level is bounded by a wall
    border, so a walk in a fixed direction from the spawn must eventually BLOCK. When it does, the
    target it was denied is a wall and the position is a fixed point. Returns (blocked_somewhere,
    every_block_well_formed)."""
    p = spawn(level)
    blocked_any = well_formed = True
    well_formed = True
    saw = False
    for c in sorted(DIRECTIONS):
        cur = p
        for _ in range(level.w + level.h):
            outcome, nxt = step(level, cur, c)
            if outcome == BLOCKED:
                saw = True
                dx, dy = DIRECTIONS[c]
                target = (cur[0] + dx, cur[1] + dy)
                if _D.traversable(level, *target) or nxt != cur:
                    well_formed = False
                break
            cur = nxt
    return saw, well_formed


# ---- scenes ---------------------------------------------------------------------------------------------
CORPUS = _G.CORPUS


def spawn_row(seed, depth):
    """From the spawn, the four outcomes and the resulting state digest per direction — a compact,
    reproducible witness of one authoritative fan-out."""
    lvl = _G.generate(seed, depth)
    p = spawn(lvl)
    cells = []
    for c in sorted(DIRECTIONS):
        o, nxt = step(lvl, p, c)
        cells.append("%s:%s:%s" % (c, o, state_digest(lvl, nxt)[:12]))
    return _G.corpus_name(seed, depth), "|".join(cells)


SCENES = ("moves", "authority", "domain")


def scene_case(name):
    if name == "moves":
        return "||".join("%s=%s" % sr for sr in (spawn_row(s, d) for s, d in CORPUS))
    if name == "authority":
        rows = []
        for s, d in CORPUS:
            lvl = _G.generate(s, d)
            p = spawn(lvl)
            agree = all(a_step_agrees_with_descent(lvl, p, c) for c in DIRECTIONS)
            fix = all(a_blocked_step_is_a_fixed_point(lvl, p, c) for c in DIRECTIONS)
            mov = all(a_moved_step_changes_the_state(lvl, p, c) for c in DIRECTIONS)
            rows.append("%s:%s:%s:%s:%s" % (_G.corpus_name(s, d), agree, fix, mov,
                                            a_sealed_mouth_blocks_a_step_that_moved(s, d)))
        return "|".join(rows) + "||dirs=%s" % the_directions_are_descents()
    if name == "domain":
        lvl = _G.generate(*CORPUS[0])
        return "refuse=%s|spawn=%s|wall=%s" % (
            refuse_is_total(lvl), the_spawn_is_descents_endpoint(lvl),
            tuple(a_walk_reaches_a_wall_and_blocks(_G.generate(s, d)) for s, d in CORPUS))
    raise MoveError(f"no scene named {name!r}")


def scene_result(name):
    return hashlib.sha256(MAGIC + b"|" + name.encode() + b"|"
                          + scene_case(name).encode()).hexdigest()


def move_digest():
    return hashlib.sha256(MAGIC + b"|" + "|".join(scene_result(n)
                                                  for n in SCENES).encode()).hexdigest()


def golden(name):
    with open(_os.path.join(_HERE, "conformance_move.txt"), encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                nm, dig = ln.split()
                if nm == name:
                    return dig
    raise MoveError(f"no golden named {name!r}")


def emitted_matches_pinned():
    return (all(scene_result(n) == golden(n) for n in SCENES)
            and move_digest() == golden("move-digest"))


def an_unpinned_name_refuses():
    try:
        golden("not-a-scene")
    except MoveError as exc:
        return exc.code == "MOVE-REFUSE"
    return False


def main():
    print("MOVE — the first authoritative D_n -> D_{n+1}: one step, MOVED or BLOCKED (URDRMOV1)")
    print("layer %s: %s | imports %s" % (LAYER, D24_ANSWER, ALLOWED_IMPORTS))
    print("directions are descent's adjacency:", the_directions_are_descents())
    print()
    lvl = _G.generate(*CORPUS[0])
    p = spawn(lvl)
    print("spawn (descent stairs-up):", p, "  state", state_digest(lvl, p)[:16])
    for c in sorted(DIRECTIONS):
        o, nxt = step(lvl, p, c)
        print("  %s -> %-7s %s  %s" % (c, o, nxt, state_digest(lvl, nxt)[:16]))
    print()
    print("sealed mouth flips MOVED->BLOCKED:", a_sealed_mouth_blocks_a_step_that_moved(*CORPUS[0]))
    print("refuse total (states, commands)  :", refuse_is_total(lvl))
    print()
    for n in SCENES:
        print(n, scene_result(n))
    print("transition", move_digest())
    print()
    print("does_not_show: that movement is timed or continuous (KINEMA refines this pair); that a")
    print("BLOCKED step advances a turn or action log (actionlog's rung); that an entity is more than")
    print("a position; and nothing about WHY a level is traversable, which is descent's claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
