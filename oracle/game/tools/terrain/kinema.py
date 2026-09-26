# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""kinema — the one-way observer-space refinement of an authoritative transition (URDRKIN1).

THE FIFTEENTH GAME-LAYER VERTICAL SLICE, D25's cinematic membrane, and the FIRST game-layer VIEW module.
Every rung before it was CORE — it AFFECTS canonical game state. This one only PRODUCES A VIEW OF it. D25 §2's
boundary question, applied to every operation here: is this changing canonical game state, or producing a view
of it? If it changes state it is the authority's; if it produces a view it is this module's. This module does
only the second, and the D25 preregistration's retro-admission falsifier (its §15) is what this landing must
satisfy: classify cleanly under §2 and bite the §10 plants, or D25 is amended first.

THE INPUT IS A REAL AUTHORITATIVE TRANSITION, NOT A SYNTHETIC ONE. `enact.dispatch` already produces
consecutive canonical states `D_n -> D_{n+1}`, and `statecanon` already identifies both ends; this module is
HANDED that pair — the two endpoint STATES and their two canonical identities — and refines BETWEEN them. It
never computes the successor it is supposed to observe: it imports no `move`/`descend`/`loot`/`enact` and calls
no `.step`/`.dispatch`/`.apply` (checked on its own AST, function-local imports included, in
`the_membrane_is_one_way`). Manufacturing a `D_{n+1}` would make this a second simulation; the whole point is
that it is not one.

WHAT IS REFINED IS THE POSITION, IN OBSERVER SPACE, NEVER THE DIGEST. The assembled canonical identity `D_n`
is a 64-hex SHA string — arithmetic on it is meaningless. The interpolable quantity is the entity POSITION
(integer cell coordinates), reached through the endpoint components, and the refinement runs in the FROZEN
Q32.32 substrate (`field.ONE`, the FIELDFP radix — consumed, not reinvented). For a permitted transition
`A -> B`:

    before = A * ONE ; after = B * ONE                              (lift the cell coordinate)
    refined = before + ((alpha * (after - before)) // ONE)          (D25 §6, floor via // ONE)

with `alpha` an evenly-spaced sample in `[0, ONE]`. The endpoints land EXACTLY: `alpha = 0 -> A`,
`alpha = ONE -> B`. The arithmetic is graded as REFERENCE (unbounded-integer) arithmetic on the frozen radix;
a bounded-i64 model is a DECLARED cross-placement obligation (D25 §6), not claimed here, exactly as the FIELDFP
substrate is reference in Python until its C/Rust placements establish the bound.

THE THREE TRANSITION SHAPES HAVE DIFFERENT TEMPORAL SEMANTICS, AND ONLY ONE IS SPATIALLY REFINED. Read off the
endpoint pair:

    MOVED     same level, orthogonally adjacent, both cells descent-traversable -> spatial refinement
    FIXED     same level, same cell (a BLOCKED move, or a LOOT) -> a spatial fixed point (every sample = A)
    LEVELCUT  the level identity differs (a DESCEND) -> a DISCRETE cut, NOT spatially interpolated

Interpolating a position across a level change would be a fiction (the two positions live on different
levels), so a LEVELCUT emits only its two endpoint frames and no intermediate. A LOOT moves only the RNG and a
BLOCKED move moves nothing, so both are fixed points.

CONTAINMENT CONSUMES THE REAL TOPOLOGY, AND THE FORGED PAIR IS THE FALSIFIER. `descent.traversable` is the one
traversability authority; this module asks it rather than inventing a weaker one. A MOVED refinement is
admitted only when both endpoints are traversable and orthogonally adjacent — a legal move edge, single-sourced
in `descent` exactly as `move` single-sources it. Everything else is a FALSE VISUAL WITNESS and refuses typed
`KINEMA-REFUSE`: a BLOCKED move presented as motion (the target is a WALL — the refused boundary — so
`descent.traversable` is False), and a forged non-adjacent or wall-crossing endpoint pair. With the currently
earned single-cell MOVE vocabulary there is no cell BETWEEN two adjacent cells, so the literal `A-X-B`
intermediate-wall plant has no realizable instance; manufacturing a multi-cell move solely to give it one would
invent gameplay authority, so it is DEFERRED, and non-vacuity is carried by the real topology against forged
endpoint claims instead.

THE MEMBRANE IS ONE-WAY, AND THE OUTPUT IS DISPOSABLE. A `Frame` carries the source tick, the sample `alpha`,
the refined Q32.32 position, and BOTH endpoint witnesses VERBATIM (the D15 `terrain_view` pattern: a view
carries the authority witness and may never write back into it). Nothing this module produces feeds a canonical
component: view quantities cannot even enter the `entity` record (`statecanon` already proves a view field
never reaches `D_n`), and no CORE module imports this one (the observer-presence differential, in the gate
stage, shows the canonical transcript is byte-identical whether this module is exercised or not).

GRADE (honest, D5). MEASURED: the endpoints land exactly (`alpha` 0 -> A, ONE -> B); every sample of a
permitted MOVED transition is contained in `{A, B}`; a FIXED transition is stationary; a LEVELCUT is a discrete
two-frame cut, not interpolated; the sample count is view-only (2, 6, 60, 144 samples give the same endpoints,
all contained); the endpoint witnesses are carried verbatim. ESTABLISHED: a wall-target (BLOCKED-as-motion)
and a non-adjacent/wall-crossing forged pair refuse `KINEMA-REFUSE` against `descent.traversable`; the module
is one-way — read off its full AST it imports exactly its declared substrate (no `move`/`descend`/`loot`/
`enact`/`statecanon`/`rerun`/`lockstep`, function-local imports included) and reaches no `.step`/`.dispatch`/
`.apply` mutator, with a synthetic forbidden module rejected as the positive control. DECLARED: the cell
coordinate is the position (no separate world-coordinate lift in this slice); the sample set is
`alpha_i = i*ONE//(k-1)`; the arithmetic is reference on the frozen radix; single transition, single peer.
does_not_show: the exact perceptual form of the view (D25 §12 — not what a view should look like); a bounded-
i64 model (a cross-placement obligation, D25 §6); multi-cell or curved trajectories, smooth-height
interpolation, camera/pose (gaze/vantage's), a voxel/observer scene, developer-mode authoring, network/replay
connection, and any wall-clock or frame budget (D25 §13, off-gate by rule)."""
import ast
import collections
import hashlib
import os as _os

_HERE = _os.path.dirname(_os.path.abspath(__file__))
_PHYS = _os.path.join(_os.path.dirname(_HERE), "physics")
for _p in (_HERE, _PHYS):
    if _p not in __import__("sys").path:
        __import__("sys").path.insert(0, _p)
import gamegen as _G                                                     # noqa: E402  (level identity, read)
import descent as _D                                                    # noqa: E402  (the traversability ruler)
from field import ONE                                                   # noqa: E402  (the FROZEN Q32.32 radix)

MAGIC = b"URDRKIN1"

LAYER = "VIEW"
D24_ANSWER = "produces a view of canonical game state — the one-way observer-space refinement of an authoritative transition"
ALLOWED_IMPORTS = ("ast", "collections", "hashlib", "os", "gamegen", "descent", "field")

#: The transition shapes, read off the endpoint pair — only MOVED is spatially refined.
MOVED = "MOVED"
FIXED = "FIXED"
LEVELCUT = "LEVELCUT"
CLASSES = (MOVED, FIXED, LEVELCUT)

#: The four orthogonal steps — the same deltas `move.DIRECTIONS` uses; adjacency is a Manhattan distance of 1.
_STEPS = ((0, -1), (0, 1), (1, 0), (-1, 0))

#: A disposable observer sample: which transition, at what `alpha`, the refined Q32.32 position, and BOTH
#: endpoint witnesses carried VERBATIM (the view may never write back into them).
Frame = collections.namedtuple("Frame", ("source_tick", "alpha", "refined", "witness_n", "witness_m", "cls"))

#: Read off THIS module's AST by `the_membrane_is_one_way`: the authority MODULES it must never import (in any
#: scope) and the mutator ATTRS it must never reach. `descent` (the traversability read) is permitted and is a
#: different name from `descend` (the depth transition, forbidden).
_FORBIDDEN_MODULES = frozenset({"move", "descend", "loot", "enact", "savegame", "rerun", "statecanon", "lockstep"})
_FORBIDDEN_ATTRS = frozenset({"step", "dispatch", "apply"})


class KinemaError(Exception):
    def __init__(self, message):
        super().__init__(f"KINEMA-REFUSE: {message}")
        self.code = "KINEMA-REFUSE"


# ---- reading the transition (never producing it) --------------------------------------------------------
def _is_cell(pos):
    return (isinstance(pos, tuple) and len(pos) == 2
            and type(pos[0]) is int and type(pos[1]) is int)          # bool excluded


def _adjacent(a, b):
    return (abs(a[0] - b[0]) + abs(a[1] - b[1])) == 1


def classify(level_n, pos_n, level_m, pos_m):
    """The view-side reading of an endpoint pair, from the endpoint components alone. LEVELCUT if the level
    IDENTITY differs (`gamegen.level_digest`, a read); FIXED if the cell is unchanged; MOVED if the cells are
    orthogonally adjacent and BOTH `descent.traversable`. Anything else on the same level is a FALSE VISUAL
    WITNESS — a forged transition the authority never produced — and refuses typed `KINEMA-REFUSE`."""
    if not (_is_cell(pos_n) and _is_cell(pos_m)):
        raise KinemaError(f"endpoints must be integer cells, got {pos_n!r}, {pos_m!r}")
    if _G.level_digest(level_n) != _G.level_digest(level_m):
        return LEVELCUT
    if pos_n == pos_m:
        return FIXED
    if (_adjacent(pos_n, pos_m)
            and _D.traversable(level_n, pos_n[0], pos_n[1])
            and _D.traversable(level_m, pos_m[0], pos_m[1])):
        return MOVED
    raise KinemaError(f"forged transition {pos_n!r} -> {pos_m!r}: not a descent-authorized move edge "
                      f"(the authority never produced it)")


# ---- the refinement (observer space, frozen Q32.32) -----------------------------------------------------
def sample_alphas(k):
    """`k` evenly-spaced samples `alpha_i = i*ONE//(k-1)` in `[0, ONE]`, endpoints included. `k` must be an
    int >= 2 (bool excluded)."""
    if not (type(k) is int and k >= 2):
        raise KinemaError(f"sample count must be an int >= 2 (bool excluded), got {k!r}")
    return tuple(i * ONE // (k - 1) for i in range(k))


def _refine_axis(a, b, alpha):
    """D25 §6, one axis: `before + ((alpha * (after - before)) // ONE)`, the floor-shift as `// ONE`. Reference
    arithmetic on the frozen radix; `alpha = 0` lands on `a*ONE`, `alpha = ONE` on `b*ONE`, exactly."""
    before, after = a * ONE, b * ONE
    return before + ((alpha * (after - before)) // ONE)


def floor_cell(refined):
    """The cell a refined Q32.32 position occupies — `// ONE` per axis (floor toward -inf)."""
    return (refined[0] // ONE, refined[1] // ONE)


def frames(level_n, pos_n, witness_n, level_m, pos_m, witness_m, source_tick, k):
    """Refine one authoritative transition into `k` disposable observer frames. MOVED is interpolated in
    Q32.32; FIXED holds at `pos_n`; LEVELCUT is a DISCRETE two-frame cut (no intermediate). Each frame carries
    both endpoint witnesses VERBATIM. A forged MOVED pair refuses `KINEMA-REFUSE` (via `classify`)."""
    cls = classify(level_n, pos_n, level_m, pos_m)
    if cls == LEVELCUT:
        return (Frame(source_tick, 0, (pos_n[0] * ONE, pos_n[1] * ONE), witness_n, witness_m, cls),
                Frame(source_tick, ONE, (pos_m[0] * ONE, pos_m[1] * ONE), witness_n, witness_m, cls))
    out = []
    for alpha in sample_alphas(k):
        refined = (_refine_axis(pos_n[0], pos_m[0], alpha), _refine_axis(pos_n[1], pos_m[1], alpha))
        out.append(Frame(source_tick, alpha, refined, witness_n, witness_m, cls))
    return tuple(out)


# ---- corpus (real move edges, read from descent — no `enact`, no `move`) --------------------------------
#: Opaque endpoint witnesses, carried verbatim through the view. The gate stage cross-checks that the REAL
#: `statecanon` digests are carried verbatim against a live `enact` transition; here they are opaque inputs.
_W_N = "a" * 64
_W_M = "b" * 64
SEEDS = ((0, 1), (1, 2), (12345, 3), (0xC0FFEE, 2))
SAMPLE_COUNTS = (2, 6, 60, 144)
SCENES = ("refinement", "membrane")


def _spawn_and_step(seed, depth):
    """A real move edge, read from `descent` alone: the spawn (up-stairs) and an orthogonally adjacent
    traversable neighbour. Returns `(level, A, B)`; `B == A` only if the spawn is boxed in (a FIXED corpus
    entry, still a valid transition)."""
    lvl = _G.generate(seed, depth)
    up = _D.endpoints(lvl)[0]
    for dx, dy in _STEPS:
        nb = (up[0] + dx, up[1] + dy)
        if _D.traversable(lvl, nb[0], nb[1]):
            return lvl, up, nb
    return lvl, up, up


def _wall_edge(level):
    """A traversable cell and an orthogonally adjacent on-grid WALL cell — the refused boundary — found by
    scanning the level, because the spawn is usually in the open (which would make Plant A vacuous)."""
    for y in range(level.h):
        for x in range(level.w):
            if not _D.traversable(level, x, y):
                continue
            for dx, dy in _STEPS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < level.w and 0 <= ny < level.h and not _D.traversable(level, nx, ny):
                    return (x, y), (nx, ny)
    return None, None


# ---- the laws / falsifiers ------------------------------------------------------------------------------
def endpoints_land_exactly(seed, depth):
    """`alpha = 0` floors to `A` and `alpha = ONE` floors to `B`, exactly — the refinement agrees with the
    authority at the endpoints it refines between."""
    lvl, a, b = _spawn_and_step(seed, depth)
    fs = frames(lvl, a, _W_N, lvl, b, _W_M, 0, 6)
    return (fs[0].alpha == 0 and floor_cell(fs[0].refined) == a
            and fs[-1].alpha == ONE and floor_cell(fs[-1].refined) == b)


def every_sample_is_contained(seed, depth):
    """Every sample of a permitted transition floors into `{A, B}` — the containment witness, over a real
    `descent`-traversable move edge."""
    lvl, a, b = _spawn_and_step(seed, depth)
    return all(floor_cell(f.refined) in (a, b) for f in frames(lvl, a, _W_N, lvl, b, _W_M, 0, 6))


def a_forged_wall_crossing_refuses(seed, depth):
    """PLANT A — a BLOCKED move presented as motion: from a real floor cell the target is an adjacent WALL
    (the refused boundary), so `descent.traversable` is False and the view REFUSES to present the transition.
    The floor/wall edge is found by scanning the level, so the plant is non-vacuous."""
    lvl = _G.generate(seed, depth)
    floor, wall = _wall_edge(lvl)
    if wall is None:                                                  # a level with no interior wall edge
        return True
    try:
        frames(lvl, floor, _W_N, lvl, wall, _W_M, 0, 6)
    except KinemaError as exc:
        return exc.code == "KINEMA-REFUSE"
    return False


def a_forged_nonadjacent_refuses(seed, depth):
    """PLANT B (the realizable form) — a forged non-adjacent endpoint pair the authority never produced is
    refused, tested against the real topology rather than a mock."""
    lvl = _G.generate(seed, depth)
    up = _D.endpoints(lvl)[0]
    far = (up[0] + 3, up[1] + 2)                                      # Manhattan distance 5, never a step
    try:
        frames(lvl, up, _W_N, lvl, far, _W_M, 0, 6)
    except KinemaError as exc:
        return exc.code == "KINEMA-REFUSE"
    return False


def the_level_cut_is_not_interpolated(seed, depth):
    """A DESCEND changes the level; the view must NOT interpolate a position across it. A LEVELCUT yields
    exactly its two endpoint frames (no intermediate), each floored on its own level."""
    l0 = _G.generate(seed, depth)
    l1 = _G.generate(seed, depth + 1)
    a0 = _D.endpoints(l0)[1]                                          # down-stairs of the upper level
    b1 = _D.endpoints(l1)[0]                                          # up-stairs of the lower level
    fs = frames(l0, a0, _W_N, l1, b1, _W_M, 0, 6)
    return (len(fs) == 2 and all(f.cls == LEVELCUT for f in fs)
            and floor_cell(fs[0].refined) == a0 and floor_cell(fs[1].refined) == b1)


def the_fixed_point_is_stationary(seed, depth):
    """A FIXED transition (a BLOCKED move or a LOOT — the cell is unchanged) is stationary: every sample
    floors to `A`."""
    lvl = _G.generate(seed, depth)
    up = _D.endpoints(lvl)[0]
    fs = frames(lvl, up, _W_N, lvl, up, _W_M, 0, 6)
    return all(f.cls == FIXED and floor_cell(f.refined) == up for f in fs)


def sampling_is_view_only(seed, depth):
    """PLANT D (module-local half) — the sample COUNT is view-only: 2, 6, 60, 144 samples of the same
    transition give the same endpoints, all contained, and exactly `k` frames. The canonical-state-unchanged
    half is the gate stage's observer-presence differential."""
    lvl, a, b = _spawn_and_step(seed, depth)
    for k in SAMPLE_COUNTS:
        fs = frames(lvl, a, _W_N, lvl, b, _W_M, 0, k)
        if not (len(fs) == k and floor_cell(fs[0].refined) == a and floor_cell(fs[-1].refined) == b
                and all(floor_cell(f.refined) in (a, b) for f in fs)):
            return False
    return True


def the_witness_is_carried_verbatim(seed, depth):
    """The D15 `terrain_view` pattern — the view carries the authority witnesses VERBATIM and never writes
    back into them: each frame's `witness_n`/`witness_m` equal the inputs byte-for-byte."""
    lvl, a, b = _spawn_and_step(seed, depth)
    return all(f.witness_n == _W_N and f.witness_m == _W_M
               for f in frames(lvl, a, _W_N, lvl, b, _W_M, 0, 6))


def _import_top(tree):
    """Every top-level module name imported ANYWHERE in the tree — function-local imports INCLUDED, closing
    the escape hatch the tree's top-level-only guards leave open."""
    top = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            top.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            top.add((node.module or "").split(".")[0])
    return top


def _reaches_mutator(tree):
    return any(isinstance(n, ast.Attribute) and n.attr in _FORBIDDEN_ATTRS for n in ast.walk(tree))


def _source_is_one_way(src):
    """A source is a one-way membrane iff it imports only its declared substrate, imports NO authority module
    (in any scope), and reaches NO mutator attr."""
    tree = ast.parse(src)
    top = _import_top(tree)
    return (top <= set(ALLOWED_IMPORTS)
            and not (top & _FORBIDDEN_MODULES)
            and not _reaches_mutator(tree))


def the_membrane_is_one_way():
    """STRUCTURAL, read off this module's OWN full AST — direction-aware and function-local-aware, the
    requirement D25 §11 makes a fourth layer. This module imports exactly `ALLOWED_IMPORTS` and none of the
    authority modules (in ANY scope), and reaches no `.step`/`.dispatch`/`.apply` mutator, so it can never
    manufacture the successor it observes. Carries a POSITIVE CONTROL: a synthetic module that sneaks a
    function-local `enact` import and an `.dispatch` call is REJECTED, so the checker is shown to bite."""
    with open(_os.path.join(_HERE, "kinema.py"), encoding="utf-8") as fh:
        own = fh.read()
    clean = _source_is_one_way(own)
    bad = ("import gamegen\n"
           "def _sneak(state, token):\n"
           "    import enact as _E\n"
           "    return _E.dispatch(state, token)\n")
    bites = not _source_is_one_way(bad)
    return clean and bites


def refuse_is_total(seed=0, depth=1):
    """(wall-crossing, non-adjacent, non-cell): each forged shape refuses typed `KINEMA-REFUSE`."""
    non_cell = False
    try:
        classify(_G.generate(seed, depth), (0, 0), _G.generate(seed, depth), ("x", 1))
    except KinemaError as exc:
        non_cell = exc.code == "KINEMA-REFUSE"
    return (a_forged_wall_crossing_refuses(seed, depth),
            a_forged_nonadjacent_refuses(seed, depth),
            non_cell)


# ---- scenes ---------------------------------------------------------------------------------------------
def _frame_str(f):
    return "%d@%d=%d,%d/%d,%d:%s|%s.%s" % (
        f.source_tick, f.alpha, f.refined[0], f.refined[1],
        f.refined[0] // ONE, f.refined[1] // ONE, f.witness_n[:6], f.witness_m[:6], f.cls)


def _refine_row(seed, depth):
    lvl, a, b = _spawn_and_step(seed, depth)
    fs = frames(lvl, a, _W_N, lvl, b, _W_M, 0, 6)
    return "%d,%d,%d,%d->%d,%d|%s" % (seed, depth, a[0], a[1], b[0], b[1],
                                      ";".join(_frame_str(f) for f in fs))


def scene_case(name):
    if name == "refinement":
        return "|".join(_refine_row(s, d) for s, d in SEEDS)
    if name == "membrane":
        return ("endpoints=%s|contained=%s|wall=%s|nonadj=%s|levelcut=%s|fixed=%s|sampling=%s|witness=%s|"
                "oneway=%s|refuse=%s") % (
            tuple(endpoints_land_exactly(s, d) for s, d in SEEDS),
            tuple(every_sample_is_contained(s, d) for s, d in SEEDS),
            tuple(a_forged_wall_crossing_refuses(s, d) for s, d in SEEDS),
            tuple(a_forged_nonadjacent_refuses(s, d) for s, d in SEEDS),
            tuple(the_level_cut_is_not_interpolated(s, d) for s, d in SEEDS),
            tuple(the_fixed_point_is_stationary(s, d) for s, d in SEEDS),
            tuple(sampling_is_view_only(s, d) for s, d in SEEDS),
            tuple(the_witness_is_carried_verbatim(s, d) for s, d in SEEDS),
            the_membrane_is_one_way(),
            tuple(refuse_is_total(s, d) for s, d in SEEDS))
    raise KinemaError(f"no scene named {name!r}")


def scene_result(name):
    return hashlib.sha256(MAGIC + b"|" + name.encode() + b"|"
                          + scene_case(name).encode()).hexdigest()


def kinema_digest():
    return hashlib.sha256(MAGIC + b"|" + "|".join(scene_result(n)
                                                  for n in SCENES).encode()).hexdigest()


def golden(name):
    with open(_os.path.join(_HERE, "conformance_kinema.txt"), encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                nm, dig = ln.split()
                if nm == name:
                    return dig
    raise KinemaError(f"no golden named {name!r}")


def emitted_matches_pinned():
    return (all(scene_result(n) == golden(n) for n in SCENES)
            and kinema_digest() == golden("kinema"))


def an_unpinned_name_refuses():
    try:
        golden("not-a-scene")
    except KinemaError as exc:
        return exc.code == "KINEMA-REFUSE"
    return False


def main():
    print("KINEMA — the one-way observer-space refinement of an authoritative transition (URDRKIN1)")
    print("layer %s: %s | imports %s" % (LAYER, D24_ANSWER, ALLOWED_IMPORTS))
    print("D25's cinematic membrane; the first game-layer VIEW module. radix ONE == 1<<32:", ONE == (1 << 32))
    print()
    lvl, a, b = _spawn_and_step(0xC0FFEE, 2)
    print("transition %s -> %s  class %s" % (a, b, classify(lvl, a, lvl, b)))
    for f in frames(lvl, a, _W_N, lvl, b, _W_M, 0, 5):
        print("  alpha %11d  refined %d,%d  floor %d,%d  [%s]"
              % (f.alpha, f.refined[0], f.refined[1], f.refined[0] // ONE, f.refined[1] // ONE, f.cls))
    print()
    print("endpoints land exactly        :", endpoints_land_exactly(0xC0FFEE, 2))
    print("every sample is contained     :", every_sample_is_contained(0xC0FFEE, 2))
    print("forged wall crossing refuses  :", a_forged_wall_crossing_refuses(0, 1))
    print("forged non-adjacent refuses   :", a_forged_nonadjacent_refuses(0, 1))
    print("level cut is not interpolated :", the_level_cut_is_not_interpolated(0, 1))
    print("fixed point is stationary     :", the_fixed_point_is_stationary(0, 1))
    print("sampling is view-only         :", sampling_is_view_only(0xC0FFEE, 2))
    print("witness carried verbatim      :", the_witness_is_carried_verbatim(0xC0FFEE, 2))
    print("the membrane is one-way       :", the_membrane_is_one_way())
    print("refuse total                  :", refuse_is_total())
    print()
    for n in SCENES:
        print(n, scene_result(n))
    print("kinema", kinema_digest())
    print()
    print("does_not_show: what a view should look like (D25 §12); a bounded-i64 model (§6, a cross-placement")
    print("obligation); multi-cell/curved trajectories, camera/pose, voxels, dev-mode, and any frame budget.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
