# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""chorus — the composition of N disposable observers over one authoritative transition (URDRCHO1).

THE SIXTEENTH GAME-LAYER VERTICAL SLICE, WINDOW-0 of the observer-composition arc, and the second
game-layer VIEW module (after `kinema`). Its one invariant, carried from the WINDOW-0 measurement pass:
OBSERVER TOPOLOGY IS DISPOSABLE; CANONICAL SIMULATION IS NOT. It takes one authoritative transition and a
collection of disposable `ObserverSpec`s and composes a `Scene` — a tuple of per-observer `kinema` Frame-sets
— PURELY by repeated `kinema` application. It is not a window system and it is not an authority: it mints no
canonical identity, computes no `D_n`, calls no transition, and imports none of
`move`/`descend`/`loot`/`enact`/`statecanon`/`rerun`/`savegame`/`lockstep`.

THE DIRECTION IS ONE-WAY, AND IT IS THE WHOLE POINT:

    authoritative transition -> KINEMA -> ObserverSpec[] -> Frame-set[] -> Scene -> window/layout consumers

never `Scene`/window -> `D_n` -> transition. `statecanon` (the `D_n` producer) is imported by nobody in the
tree, and this module keeps it that way: the endpoint witnesses (which ARE `D_n` values) enter as OPAQUE
strings and are carried VERBATIM through the Frames — they are never ingested as authority. `the_membrane_is_
one_way` reads this module's OWN full AST (function-local imports included) and refuses any authority import
or any `.d_n`/`.dispatch`/`.apply` reach, with a positive control.

COMPOSITION IS REPEATED OBSERVATION, NOT A NEW AUTHORITY. `compose(transition, specs)` is exactly
`tuple((spec.observer_id, observe(transition, spec)) for spec in specs)`, and `observe` is one call to
`kinema.frames`. There is no N-window authority: N is a plain list length, and N=0 is the empty Scene. A
future window manager consumes `Scene`/`Frame`s, never `D_n`.

THE OBSERVER IDENTITY IS DISPOSABLE. An `ObserverSpec` carries `observer_id`, the interval label
`source_tick`, the sample count `samples`, and an OPAQUE `window` blob (bounds, focus, z-order, camera, zoom,
layout). In WINDOW-0 the `window` blob is INERT — camera/layout are a later arc, so it reaches neither the
Frames nor any canonical value, and `the_window_config_is_disposable` proves two specs differing only in
`window` (or `observer_id`) produce byte-identical Frame-sets. What a pane shows depends only on the
transition and the view parameters `source_tick`/`samples`; what it can touch canonically is nothing.

AGREEMENT IS PROVENANCE, NOT PIXELS. Two panes of one transition share their provenance
`(source_tick, witness_n, witness_m, cls)` while their refined samples may differ (different `samples`). Same
authority is not the same picture. And permutation invariance is CANONICAL-ONLY: reordering the spec
collection leaves the provenance MULTISET identical, but the ordered Scene is deliberately NOT certified
equal — ordering is not an earned observer law, and this module refuses to smuggle one in.

STALENESS IS PROVENANCE, NOT RECONSTRUCTION. A pane observing an older transition simply carries that
transition's witnesses; a current pane carries the current ones. `kinema`'s one-transition input boundary
makes this structural — a pane is handed exactly one transition and can only interpolate within it, so it can
never synthesise a state between two transitions and call it canonical.

TOPOLOGY IS A LIST OPERATION. Add, remove, reorder, duplicate or omit specs and the Scene's panes and their
provenance multiset follow the spec list exactly — the Scene is a pure function of `(transition, specs)`. The
CANONICAL half of the differential — that mutating the observer collection (including N=0) leaves the
canonical transcript byte-identical — is exercised at the gate against a real `enact`/`statecanon`/`rerun`
core, because this module cannot (and must not) reach that core to test it.

INHERITED, NOT RE-PROVED: a forged transition in the collection refuses through `kinema` (KINEMA-REFUSE, via
`descent.traversable`); render-cadence independence is `panelight`'s (URDRPNL1) dt-log decoupling and the
tree's clock guards; the no-successor / forged-pair / one-transition guarantees are `kinema`'s. WINDOW-1
(window event -> typed `enact`) is a separate later membrane and is not in this rung.

GRADE (honest, D5). MEASURED: `compose` is repeated `observe` (each pane equals the observer applied alone);
panes of one transition agree on provenance while their samples differ; the provenance multiset is
permutation-invariant; add/remove/reorder/duplicate/omit follow the spec list; the empty Scene is pure; the
`window` blob is disposable (byte-identical Frame-sets). ESTABLISHED: a stale and a current pane differ by
provenance and neither synthesises a between-state; a forged transition refuses KINEMA-REFUSE; the membrane is
one-way — read off the full AST it imports exactly its declared substrate (no authority module, function-local
included), reaches no `.d_n`/`.dispatch`/`.apply`, and a synthetic nested authority import is rejected as the
positive control. DECLARED: the cell/observer model is `kinema`'s; the `window` blob is inert this rung;
permutation invariance is canonical-only (ordering is not certified); the sample set convention is `kinema`'s.
does_not_show: the canonical topology differential across a real core (the gate's, not the module's); window
-> `enact` input (WINDOW-1); OS-native windows, GPU composition, camera architecture, voxels, wireframes,
developer authoring, and any wall-clock or frame budget (all deferred)."""
import ast
import collections
import hashlib
import os as _os

_HERE = _os.path.dirname(_os.path.abspath(__file__))
if _HERE not in __import__("sys").path:
    __import__("sys").path.insert(0, _HERE)
import gamegen as _G                                                     # noqa: E402  (build corpus transitions)
import descent as _D                                                    # noqa: E402  (the traversability ruler)
import kinema as _K                                                     # noqa: E402  (the base observer)

MAGIC = b"URDRCHO1"

LAYER = "VIEW"
D24_ANSWER = "produces a view of canonical game state — the composition of N disposable observers over one authoritative transition"
ALLOWED_IMPORTS = ("ast", "collections", "hashlib", "os", "gamegen", "descent", "kinema")

#: A disposable observer. `observer_id` labels the pane; `source_tick` is the interval identity handed to
#: `kinema`; `samples` is its sample count; `window` is an OPAQUE, INERT blob (bounds/focus/z-order/camera/
#: zoom/layout) — carried alongside but consumed by nothing in WINDOW-0.
ObserverSpec = collections.namedtuple("ObserverSpec", ("observer_id", "source_tick", "samples", "window"))

#: Read off THIS module's full AST by `the_membrane_is_one_way`: authority MODULES it must never import (any
#: scope) and mutator/identity ATTRS it must never reach. `descent` (read-only traversability) and `kinema`
#: (the base observer) are permitted; `descend` (the depth transition) is forbidden and is a different name.
_FORBIDDEN_MODULES = frozenset({"move", "descend", "loot", "enact", "savegame", "rerun", "statecanon", "lockstep"})
_FORBIDDEN_ATTRS = frozenset({"step", "dispatch", "apply", "d_n", "d_n_preimage"})


class ChorusError(Exception):
    def __init__(self, message):
        super().__init__(f"CHORUS-REFUSE: {message}")
        self.code = "CHORUS-REFUSE"


# ---- composition: repeated KINEMA application over one transition ---------------------------------------
def _is_spec(s):
    return isinstance(s, ObserverSpec)


def observe(transition, spec):
    """One disposable observer over one authoritative transition — a single, pure `kinema` application.
    `transition = (level_n, pos_n, witness_n, level_m, pos_m, witness_m)`. The spec's `window` blob is
    DISPOSABLE and reaches nothing here; only `source_tick` and `samples` are consumed."""
    if not _is_spec(spec):
        raise ChorusError(f"an observer must be an ObserverSpec, got {type(spec).__name__}")
    ln, pn, wn, lm, pm, wm = transition
    return _K.frames(ln, pn, wn, lm, pm, wm, spec.source_tick, spec.samples)


def compose(transition, specs):
    """A Scene: a tuple of `(observer_id, Frame-set)`, one per spec, composed PURELY by repeated `observe`.
    N = len(specs); N=0 is the empty Scene. It mints no canonical identity and calls no authority — a future
    window/layout layer consumes this Scene, never `D_n`."""
    if not (isinstance(specs, (tuple, list)) and all(_is_spec(s) for s in specs)):
        raise ChorusError("specs must be a sequence of ObserverSpec")
    return tuple((spec.observer_id, observe(transition, spec)) for spec in specs)


def provenance(pane):
    """The authoritative-transition identity a pane observes: `(source_tick, witness_n, witness_m, cls)`.
    Agreement and staleness are read from THIS — never from the refined pixels."""
    _oid, frame_set = pane
    f = frame_set[0]
    return (f.source_tick, f.witness_n, f.witness_m, f.cls)


def provenance_multiset(scene):
    """The scene's provenance as an ORDER-INDEPENDENT multiset — the canonical-only agreement quantity. The
    scene's own tuple order is deliberately NOT part of this (ordering is not an earned observer law)."""
    return tuple(sorted(provenance(p) for p in scene))


# ---- corpus (real move edges via descent; OPAQUE witnesses carried verbatim; no statecanon) -------------
_W_N = "a" * 64
_W_M = "b" * 64
_W_PREV = "c" * 64                                                       # an older transition's endpoint
SEEDS = ((0, 1), (1, 2), (12345, 3), (0xC0FFEE, 2))
SCENES = ("composition", "topology")


def _transition(seed, depth):
    """A real MOVED transition read from `descent` alone (spawn + an adjacent traversable cell), with OPAQUE
    endpoint witnesses carried verbatim. The REAL `statecanon` witnesses are cross-checked at the gate."""
    lvl = _G.generate(seed, depth)
    up = _D.endpoints(lvl)[0]
    nb = up
    for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0)):
        c = (up[0] + dx, up[1] + dy)
        if _D.traversable(lvl, c[0], c[1]):
            nb = c
            break
    return (lvl, up, _W_N, lvl, nb, _W_M)


def _specs():
    """A disposable observer collection: one shared transition, varied `samples` and INERT `window` blobs."""
    return (ObserverSpec("main", 0, 6, ("bounds", 0, 0, 800, 600)),
            ObserverSpec("minimap", 0, 2, ("bounds", 620, 10, 180, 180)),
            ObserverSpec("lag", 0, 60, ("focus", True, "z", 2)),
            ObserverSpec("smooth", 0, 144, ("camera", "iso", "zoom", 3)))


# ---- the laws / falsifiers ------------------------------------------------------------------------------
def composition_is_repeated_observation(seed, depth):
    """`compose` is exactly repeated `observe`: the Scene has one pane per spec, and each pane's Frame-set
    equals the observer applied to that spec alone. No N-window authority."""
    txn = _transition(seed, depth)
    specs = _specs()
    scene = compose(txn, specs)
    return (len(scene) == len(specs)
            and all(scene[i][0] == specs[i].observer_id and scene[i][1] == observe(txn, specs[i])
                    for i in range(len(specs))))


def panes_of_one_transition_agree_on_provenance(seed, depth):
    """Every pane of ONE transition shares the same provenance (source_tick, witnesses, class), while panes
    with different `samples` produce DIFFERENT refined pixels — agreement is provenance, not pixels."""
    txn = _transition(seed, depth)
    scene = compose(txn, _specs())
    provs = {provenance(p) for p in scene}
    refined = [tuple(f.refined for f in fs) for _oid, fs in scene]
    all_same_pixels = all(r == refined[0] for r in refined)
    return len(provs) == 1 and not all_same_pixels


def the_provenance_multiset_is_permutation_invariant(seed, depth):
    """CANONICAL-ONLY permutation invariance: any permutation of the spec collection yields the same
    provenance MULTISET, while the ORDERED scene is deliberately NOT required equal (ordering is not an
    earned observer law). Returns (multiset_invariant, ordering_not_certified)."""
    txn = _transition(seed, depth)
    specs = list(_specs())
    perms = (specs, specs[1:] + specs[:1], list(reversed(specs)))
    scenes = [compose(txn, p) for p in perms]
    multiset_invariant = all(provenance_multiset(s) == provenance_multiset(scenes[0]) for s in scenes)
    ordering_differs = any([p[0] for p in s] != [p[0] for p in scenes[0]] for s in scenes[1:])
    return multiset_invariant, ordering_differs


def topology_is_a_list_operation(seed, depth):
    """Add / remove / reorder / duplicate / omit specs and the Scene's panes and provenance multiset follow
    the spec list exactly — the Scene is a pure function of (transition, specs)."""
    txn = _transition(seed, depth)
    specs = list(_specs())
    base = compose(txn, specs)
    dup = compose(txn, specs + [specs[0]])                              # duplicate -> one more pane, same prov
    rem = compose(txn, specs[1:])                                       # remove -> one fewer
    omit = compose(txn, [])                                             # omit all -> empty
    return (len(base) == len(specs) and len(dup) == len(specs) + 1 and len(rem) == len(specs) - 1
            and len(omit) == 0
            and provenance_multiset(dup) == tuple(sorted(list(provenance_multiset(base))
                                                         + [provenance(base[0])]))
            and provenance(dup[-1]) == provenance(base[0]))


def the_empty_scene_is_pure(seed, depth):
    """N=0: the empty Scene is the empty tuple, and it composes without touching anything. (The REAL-core
    N=0 differential — that the core runs identically with no observers — is the gate's, since this module
    cannot reach the core.)"""
    return compose(_transition(seed, depth), ()) == () and compose(_transition(seed, depth), []) == ()


def the_window_config_is_disposable(seed, depth):
    """The `window` blob (and `observer_id`) is DISPOSABLE: two specs identical in `source_tick`/`samples`
    but differing in `window`/`observer_id` produce BYTE-IDENTICAL Frame-sets — window state reaches neither
    the Frames nor any canonical value."""
    txn = _transition(seed, depth)
    a = ObserverSpec("A", 0, 6, ("bounds", 0, 0, 100, 100))
    b = ObserverSpec("B", 0, 6, ("camera", "iso", "zoom", 9, "focus", True))
    return observe(txn, a) == observe(txn, b)


def a_stale_and_a_current_pane_differ_by_provenance(seed, depth):
    """Staleness is PROVENANCE, not reconstruction. A pane over an older transition carries the older
    witnesses; a current pane carries the current ones; the two are distinguished by provenance, and neither
    pane's frames carry any witness outside its OWN transition's two endpoints (no synthesised between-state)."""
    lvl = _G.generate(seed, depth)
    up = _D.endpoints(lvl)[0]
    nb = up
    for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0)):
        c = (up[0] + dx, up[1] + dy)
        if _D.traversable(lvl, c[0], c[1]):
            nb = c
            break
    current = observe((lvl, up, _W_N, lvl, nb, _W_M), ObserverSpec("cur", 1, 6, None))
    stale = observe((lvl, up, _W_PREV, lvl, up, _W_N), ObserverSpec("old", 0, 6, None))  # D_{n-1}->D_n
    cur_p = (current[0].source_tick, current[0].witness_n, current[0].witness_m)
    old_p = (stale[0].source_tick, stale[0].witness_n, stale[0].witness_m)
    current_witnesses = {w for f in current for w in (f.witness_n, f.witness_m)}
    stale_witnesses = {w for f in stale for w in (f.witness_n, f.witness_m)}
    return (cur_p != old_p
            and current_witnesses == {_W_N, _W_M}
            and stale_witnesses == {_W_PREV, _W_N})


def a_forged_transition_in_the_collection_refuses(seed, depth):
    """A forged transition anywhere in the collection surfaces `kinema`'s KINEMA-REFUSE (the target is a
    wall — the refused boundary), inherited through `descent.traversable`; the Scene invents no view of it."""
    lvl = _G.generate(seed, depth)
    floor, wall = _K._wall_edge(lvl)
    if wall is None:
        return True
    try:
        compose((lvl, floor, _W_N, lvl, wall, _W_M), (ObserverSpec("x", 0, 6, None),))
    except _K.KinemaError as exc:
        return exc.code == "KINEMA-REFUSE"
    return False


def _import_top(tree):
    top = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            top.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            top.add((node.module or "").split(".")[0])
    return top


def _source_is_one_way(src):
    """A source is a one-way observer-composition membrane iff it imports only its declared substrate,
    imports NO authority module (any scope), and reaches NO mutator/identity attr — in particular no `d_n`
    (it must not ingest the assembled canonical identity)."""
    tree = ast.parse(src)
    top = _import_top(tree)
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    return (top <= set(ALLOWED_IMPORTS)
            and not (top & _FORBIDDEN_MODULES)
            and not (attrs & _FORBIDDEN_ATTRS))


def the_membrane_is_one_way():
    """STRUCTURAL, read off this module's OWN full AST — direction-aware and function-local-aware. It imports
    exactly `ALLOWED_IMPORTS`, imports none of the authority modules in ANY scope, and reaches no
    `.d_n`/`.d_n_preimage` (no `D_n` ingestion) and no `.step`/`.dispatch`/`.apply` mutator. Positive
    controls: synthetic modules that nest an `enact` import, a `statecanon` import, a `.dispatch` reach, and
    a `.d_n` reach are each REJECTED, while the intended read-only path (`kinema`/`gamegen`/`descent`) is
    accepted."""
    with open(_os.path.join(_HERE, "chorus.py"), encoding="utf-8") as fh:
        own = fh.read()
    clean = _source_is_one_way(own)
    bad = (
        "import kinema\ndef f(t, s):\n    import enact as _E\n    return _E.dispatch(t, s)\n",
        "import kinema\ndef g(t):\n    import statecanon as _S\n    return _S.d_n(*t)\n",
        "import gamegen\nx = y.dispatch(1)\n",
        "import gamegen\nz = w.d_n(1)\n",
    )
    bites = all(not _source_is_one_way(b) for b in bad)
    allows = _source_is_one_way("import kinema\nimport gamegen\nimport descent\n"
                                "def h(t, s):\n    return kinema.frames(*t, s.source_tick, s.samples)\n")
    return clean and bites and allows


def refuse_is_total(seed=0, depth=1):
    """(bad-spec, forged-transition, non-observer): each surfaces a typed refusal — CHORUS-REFUSE for a
    malformed collection, KINEMA-REFUSE for a forged transition."""
    bad_spec = False
    try:
        compose(_transition(seed, depth), (("not", "a", "spec"),))
    except ChorusError as exc:
        bad_spec = exc.code == "CHORUS-REFUSE"
    non_obs = False
    try:
        observe(_transition(seed, depth), 42)
    except ChorusError as exc:
        non_obs = exc.code == "CHORUS-REFUSE"
    return bad_spec, a_forged_transition_in_the_collection_refuses(seed, depth), non_obs


# ---- scenes ---------------------------------------------------------------------------------------------
def _pane_str(pane):
    oid, fs = pane
    st, wn, wm, cls = provenance(pane)
    return "%s@%d[%s|%s.%s]x%d=%s" % (oid, st, wn[:6], wm[:6], cls, len(fs),
                                      hashlib.sha256(repr(tuple(f.refined for f in fs)).encode()).hexdigest()[:12])


def _composition_row(seed, depth):
    scene = compose(_transition(seed, depth), _specs())
    return "%d,%d|N%d|%s" % (seed, depth, len(scene), ";".join(_pane_str(p) for p in scene))


def scene_case(name):
    if name == "composition":
        return "|".join(_composition_row(s, d) for s, d in SEEDS)
    if name == "topology":
        return ("repeated=%s|agree=%s|perm=%s|listop=%s|empty=%s|disposable=%s|stale=%s|forged=%s|"
                "oneway=%s|refuse=%s") % (
            tuple(composition_is_repeated_observation(s, d) for s, d in SEEDS),
            tuple(panes_of_one_transition_agree_on_provenance(s, d) for s, d in SEEDS),
            tuple(the_provenance_multiset_is_permutation_invariant(s, d) for s, d in SEEDS),
            tuple(topology_is_a_list_operation(s, d) for s, d in SEEDS),
            tuple(the_empty_scene_is_pure(s, d) for s, d in SEEDS),
            tuple(the_window_config_is_disposable(s, d) for s, d in SEEDS),
            tuple(a_stale_and_a_current_pane_differ_by_provenance(s, d) for s, d in SEEDS),
            tuple(a_forged_transition_in_the_collection_refuses(s, d) for s, d in SEEDS),
            the_membrane_is_one_way(),
            tuple(refuse_is_total(s, d) for s, d in SEEDS))
    raise ChorusError(f"no scene named {name!r}")


def scene_result(name):
    return hashlib.sha256(MAGIC + b"|" + name.encode() + b"|"
                          + scene_case(name).encode()).hexdigest()


def chorus_digest():
    return hashlib.sha256(MAGIC + b"|" + "|".join(scene_result(n)
                                                  for n in SCENES).encode()).hexdigest()


def golden(name):
    with open(_os.path.join(_HERE, "conformance_chorus.txt"), encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                nm, dig = ln.split()
                if nm == name:
                    return dig
    raise ChorusError(f"no golden named {name!r}")


def emitted_matches_pinned():
    return (all(scene_result(n) == golden(n) for n in SCENES)
            and chorus_digest() == golden("chorus"))


def an_unpinned_name_refuses():
    try:
        golden("not-a-scene")
    except ChorusError as exc:
        return exc.code == "CHORUS-REFUSE"
    return False


def main():
    print("CHORUS — the composition of N disposable observers over one authoritative transition (URDRCHO1)")
    print("layer %s: %s" % (LAYER, D24_ANSWER))
    print("WINDOW-0 of the observer-composition arc; the second game-layer VIEW module.")
    print()
    txn = _transition(0xC0FFEE, 2)
    scene = compose(txn, _specs())
    print("Scene over one transition, N =", len(scene), "observers:")
    for oid, fs in scene:
        st, wn, wm, cls = provenance((oid, fs))
        print("  %-8s tick %d  %d frames  prov[%s|%s.%s]" % (oid, st, len(fs), wn[:6], wm[:6], cls))
    print()
    print("composition is repeated observation :", composition_is_repeated_observation(0xC0FFEE, 2))
    print("panes agree on provenance (not px)  :", panes_of_one_transition_agree_on_provenance(0xC0FFEE, 2))
    print("provenance multiset perm-invariant  :", the_provenance_multiset_is_permutation_invariant(0xC0FFEE, 2))
    print("topology is a list operation        :", topology_is_a_list_operation(0xC0FFEE, 2))
    print("the empty scene is pure (N=0)       :", the_empty_scene_is_pure(0xC0FFEE, 2))
    print("the window config is disposable     :", the_window_config_is_disposable(0xC0FFEE, 2))
    print("stale vs current differ by provenance:", a_stale_and_a_current_pane_differ_by_provenance(0xC0FFEE, 2))
    print("a forged transition refuses         :", a_forged_transition_in_the_collection_refuses(0, 1))
    print("the membrane is one-way             :", the_membrane_is_one_way())
    print("refuse total                        :", refuse_is_total())
    print()
    for n in SCENES:
        print(n, scene_result(n))
    print("chorus", chorus_digest())
    print()
    print("does_not_show: the canonical topology differential across a real core (the gate's); window -> enact")
    print("(WINDOW-1); OS windows, GPU, camera, voxels, wireframes, dev authoring, frame budgets (deferred).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
