# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""heirloom — the certified generational-growth law: a derived quantity, not persistent state (URDRHEI1).

THE NINTH GAME-LAYER VERTICAL SLICE, and the second certified ARITHMETIC LAW (after `combat`) rather than
a state transition. D24 §3's heirloom progression: an inherited quantity grows by a declared fraction each
generation, the direction and baseline enforced, a shrink reddening. The gateable sentence is "the growth
is deterministic and obeys the declared fraction"; "the progression is rewarding or balanced" is NOT
gateable (D24 §4), and this module is the gateable sentence and nothing more.

A DERIVED QUANTITY, NOT PERSISTENT STATE -- the transition settled by measurement, exactly as `combat`'s
was. The natural shape `persistent_retirement_state -> persistent_retirement_state'` needs a place to KEEP
the inherited quantity across generations, and the measurement found NONE: the game layer has no
persistence substrate (the `persist` rung is unbuilt, and the existing `persist.py`/URDRLAT5 is the
MMO/netcode rollback-window checkpoint, a different arc no game-layer module imports); `entity.FIELDS ==
(\"pos\",)` and the construction chain `entity.at(pos) -> entity.digest_at(pos) -> move.state_bytes` means a
progression field would BREAK `move` (the seam `combat` established); and the tree's direction-and-baseline
authority operates on module-level SOURCE CONSTANTS across GIT HISTORY (content-addressed blob baselines),
so it cannot hold a RUNTIME quantity. Making a container inside
`heirloom` would be architectural INVENTION, not implementation. So heirloom is the smaller, honest slice:
the transition `quantity -> quantity'` -- a PURE FUNCTION that persists nothing -- the way `combat`
generated a damage integer with no health to store it in and `loot` generated a drop with no inventory.
The quantity composes forward: `heirloom -> grown quantity -> a future persistence/entity-binding rung`.

A REGISTERED ARITHMETIC EXPERIMENT WITH AN EXPLICIT DECLARED INPUT, not a stat disguised as state. No
canonical quantity exists that heirloom could legitimately inherit (measured: `gamegen`'s seed/depth,
`entity`'s position, `rngstream`'s `(n, R_n)`, `loot`'s drop and `combat`'s damage are none of them a
persistable progression quantity), so `q` is a DECLARED integer input over the non-negative integers,
exactly as `magicdiv`/`horn`/`opcost`/`combat` are certified arithmetic laws over declared inputs. A later
rung binds a real retiring hero's quantity to this function.

THE FORMULA IS `heir(q) = q + (q * NUM) // DEN`, the smallest law that still GROWS BY A FRACTION. Minimality
forces every choice. AN INTEGER RATIO with FLOOR division, not a `Fraction` -- fractional arithmetic here is
`magicdiv`'s integer-division discipline, and `fractions.Fraction` appears in this tree only as an
ADVERSARIAL PLANT that other modules REFUSE (a cross-type-equality hazard), never as a canonical number.
MONOTONE NON-DECREASING, not a minimum-growth rule: `heir(q) >= q` for every `q`, and it is STRICTLY greater
only once the floor contribution turns positive (`q >= DEN/NUM`); below that threshold the floor legitimately
yields ZERO growth, which is the honest behaviour of the declared fraction and is asserted directly rather
than papered over with a `max(1, ...)` clamp (that minimum-growth rule is a DEFER, and its mutation reddens).
DETERMINISTIC -- no randomness and no `rngstream` edge; growth is a fixed function of the quantity. The
GENERATIONS are a pure SEQUENCE `q_0 -> q_1 -> q_2 -> ...` folded from a declared baseline, COMPUTED not
STORED, the way `rngstream.trace` folds a sequence without persisting it.

THE ORACLE IS STRUCTURALLY SEPARATE -- the neutral-ruler discipline. `heir` is `q + (q*NUM)//DEN` (add after
floor); the references are `(q * (DEN + NUM)) // DEN` (a SINGLE floor of a COMBINED numerator -- provably
equal because `q*DEN` is divisible by `DEN`, yet a different expression) and a COUNT-OF-MULTIPLES oracle
that uses NO floor division at all (it counts the multiples of `DEN` at or below `q*NUM`). A shrink, a
replace-not-grow, or an off-by-one in the numerator is caught by rulers that share none of `heir`'s
structure, plus a corpus of FROZEN LITERAL boundary tuples.

NO RESULT REPRESENTATION YET. A grown quantity is not named by anything, so it gets no `q:<n>` byte form --
the conformance corpus IS the identity, exactly as `combat`'s damage integer earned none. It is a PURE
STDLIB LEAF: imports only `hashlib`/`os`, no `entity`, `persist`, `rngstream`, the direction-and-baseline
register, or any game module (read off its AST), import-depth 0, hosting no REQUIRES chain -- so the
roadmap's earlier-predicted entity and direction-register dependencies are SUPERSEDED BY MEASUREMENT, the
way `combat`'s predicted `entity`/`rngstream` were. Malformed inputs (negative, non-int, bool) refuse typed HEIRLOOM-REFUSE.

GRADE (honest, D5). MEASURED: over the whole `0..CORPUS_MAX` corpus `heir` equals BOTH independent oracles;
the frozen boundary tuples match; growth never shrinks (`heir(q) >= q`); the generational sequence is
monotone non-decreasing; growth is strictly positive for `q >= DEN/NUM` and exactly zero below it.
ESTABLISHED: the four planted mutations (shrink, replace-not-grow, off-by-one, and the deferred
minimum-growth-1 rule) each disagree with an independent oracle; malformed or negative inputs refuse typed
HEIRLOOM-REFUSE; the module mutates nothing and its substrate is stdlib only. DECLARED: that the fraction is
`NUM/DEN = 1/8`, that the growth is monotone NON-DECREASING (with an intentional zero-growth region below the
floor threshold), and that a minimum-growth rule, where the quantity lives, entity binding, persistence and
multi-attribute progression are LATER rungs'. does_not_show: that the progression is rewarding, balanced or
fun (not gateable, D24 §4); WHERE the quantity is kept (there is no persistence substrate yet -- a future
rung's contract); that a hero inherits it (no entity binding); that growth is randomized; and nothing about
the direction-and-baseline register, whose machinery is over source constants across git history, a different substrate."""
import hashlib
import os as _os

_HERE = _os.path.dirname(_os.path.abspath(__file__))

MAGIC = b"URDRHEI1"

LAYER = "CORE"
D24_ANSWER = "affects canonical game state — the certified generational-growth law (a derived quantity)"
ALLOWED_IMPORTS = ("hashlib", "os")

#: DECLARED — the growth fraction NUM/DEN (an heirloom grows by 1/8 each generation). A proper integer
#: ratio, FROZEN: a change mints a new corpus. These are frozen arithmetic PARAMETERS — they appear only in
#: arithmetic, never in a comparison against a non-constant, so they are not historical direction-register state.
NUM = 1
DEN = 8

#: The exhaustive corpus bound. NOT a domain clamp — `heir` is total on the non-negative integers and its
#: OUTPUT may exceed this; this only bounds the pinned/enumerated corpus so growth is unbounded, not capped.
CORPUS_MAX = 255


class HeirloomError(Exception):
    def __init__(self, message):
        super().__init__(f"HEIRLOOM-REFUSE: {message}")
        self.code = "HEIRLOOM-REFUSE"


def _is_quantity(v):
    # a non-negative int; bool is a subclass of int and is excluded; there is NO upper clamp
    return type(v) is int and v >= 0


def _check(quantity):
    if not _is_quantity(quantity):
        raise HeirloomError(f"quantity must be a non-negative int, got {quantity!r}")


def heir(quantity):
    """THE LAW: `quantity' = quantity + (quantity * NUM) // DEN`. Pure and total over the non-negative
    integers — the same quantity yields the same successor on any host, and nothing is mutated or
    persisted. Monotone NON-DECREASING (never shrinks); strictly greater only for `quantity >= DEN/NUM`."""
    _check(quantity)
    return quantity + (quantity * NUM) // DEN


def generations(quantity, n):
    """The generational SEQUENCE `[q_0, q_1, ..., q_n]` folded from a declared baseline — computed, never
    stored. `q_{k+1} = heir(q_k)`."""
    _check(quantity)
    if not (type(n) is int and n >= 0):
        raise HeirloomError(f"n must be a non-negative int, got {n!r}")
    out = [quantity]
    for _ in range(n):
        quantity = heir(quantity)
        out.append(quantity)
    return out


# ---- the INDEPENDENT oracles (structurally separate: combined numerator; and no floor division at all) ---
def _oracle_combined(quantity):
    """Independent oracle 1: a SINGLE floor of a COMBINED numerator, `(q*(DEN+NUM))//DEN`. Provably equal to
    `heir` because `q*DEN` is divisible by `DEN`, but a different expression that shares no add-after-floor
    structure."""
    return (quantity * (DEN + NUM)) // DEN


def _oracle_count(quantity):
    """Independent oracle 2: NO floor division at all — count the multiples of `DEN` at or below `q*NUM`,
    which IS `(q*NUM)//DEN`, then add the quantity. A genuinely different algorithm."""
    g = sum(1 for k in range(1, quantity * NUM + 1) if k % DEN == 0)
    return quantity + g


def _threshold():
    """`ceil(DEN / NUM)` — the smallest quantity whose floor contribution is positive, so growth is strict
    at or above it. Computed (a BinOp), never a bare module constant, so it is not direction-register state."""
    return -(-DEN // NUM)


#: FROZEN LITERAL boundary corpus — hand-computed (q, q') expectations that share NO code with `heir`.
BOUNDARY = (
    (0, 0), (1, 1), (7, 7), (8, 9), (9, 10), (15, 16), (16, 18), (64, 72),
    (100, 112), (128, 144), (255, 286), (200, 225),
)


# ---- the laws / falsifiers ------------------------------------------------------------------------------
def heir_matches_the_independent_oracles():
    """MEASURED, exhaustively: `heir(q)` equals BOTH independent oracles for every `q` in the corpus — the
    combined-numerator floor and the count-of-multiples, neither sharing `heir`'s structure."""
    for q in range(CORPUS_MAX + 1):
        h = heir(q)
        if h != _oracle_combined(q) or h != _oracle_count(q):
            return False
    return True


def the_frozen_boundary_tuples_match():
    """MEASURED: the hand-computed boundary expectations hold — the corpus that shares no implementation
    with `heir`."""
    return all(heir(q) == qp for q, qp in BOUNDARY)


def growth_never_shrinks():
    """THE DIRECTION CLAIM: `heir(q) >= q` for every quantity — an heirloom never loses value across a
    generation. Monotone NON-DECREASING, not strictly increasing (the floor yields zero growth below the
    threshold), and a shrink anywhere reddens."""
    return all(heir(q) >= q for q in range(CORPUS_MAX + 1))


def the_generational_sequence_is_monotone():
    """The sequence `q_0 -> q_1 -> ...` is monotone non-decreasing at every step (a stronger reading of the
    direction than the pointwise law): each generation is at least the last."""
    seq = generations(1, 40) + generations(CORPUS_MAX, 5)
    prev = generations(8, 12)
    return (all(prev[i + 1] >= prev[i] for i in range(len(prev) - 1))
            and all(seq[i + 1] >= seq[i] for i in range(len(seq) - 1)))


def growth_is_strict_above_the_threshold():
    """The floor semantics, made a law in BOTH directions: growth is STRICTLY positive for `q >= ceil(DEN/
    NUM)` and EXACTLY zero below it — the intentional zero-growth region, asserted rather than hidden."""
    t = _threshold()
    strict = all(heir(q) > q for q in range(t, CORPUS_MAX + 1))
    zero_below = all(heir(q) == q for q in range(0, t))
    return strict and zero_below


def _mutants():
    """The four planted mutations, each at an EARNED boundary. Returned as callables so the non-vacuity
    witness can prove each one reddens against an independent oracle. The minimum-growth-1 variant is a
    DEFERRED law, planted here to show the measured zero-growth region is evidence for the current law."""
    return {
        "shrink":        lambda q: q - (q * NUM) // DEN,          # the direction
        "replace":       lambda q: (q * NUM) // DEN,              # grows nothing, replaces
        "off_by_one":    lambda q: q + (q * NUM + 1) // DEN,      # off-by-one in the numerator
        "min_growth_1":  lambda q: q + max(1, (q * NUM) // DEN),  # the DEFERRED minimum-growth rule
    }


def a_planted_mutation_reddens():
    """NON-VACUITY: each planted mutant DISAGREES with an independent oracle somewhere in the corpus, so the
    falsifier can bite. Returns True iff all four are caught."""
    caught = 0
    for _name, mut in _mutants().items():
        if any(mut(q) != _oracle_combined(q) for q in range(CORPUS_MAX + 1)):
            caught += 1
    return caught == len(_mutants())


def two_inputs_produce_different_results():
    """The zero-effect guard: the law is not constant — two declared inputs give different grown
    quantities, so a corpus of it certifies something."""
    return heir(64) != heir(200)


def refuse_is_total():
    """Every malformed quantity refuses typed HEIRLOOM-REFUSE — never a clamp, a cast or a silent default;
    and `generations` refuses a malformed count."""
    q_ref = 0
    for bad in (-1, 1.0, "5", None, True, -8):
        try:
            heir(bad)
        except HeirloomError as exc:
            q_ref += exc.code == "HEIRLOOM-REFUSE"
    n_ref = 0
    for bad in (-1, 1.0, "3", None, True):
        try:
            generations(10, bad)
        except HeirloomError as exc:
            n_ref += exc.code == "HEIRLOOM-REFUSE"
    return q_ref == 6, n_ref == 5


def the_module_is_a_stdlib_leaf():
    """The layer boundary, read off this module's OWN AST: module-scope imports are exactly
    `ALLOWED_IMPORTS` (stdlib only) — no `entity`, `persist`, `rngstream` or any game/verification module.
    heirloom is a pure arithmetic law, coupled to no arc, storing nothing."""
    import ast
    with open(_os.path.join(_HERE, "heirloom.py"), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    top = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            top.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            top.add((node.module or "").split(".")[0])
    return (top == set(ALLOWED_IMPORTS)
            and not ({"entity", "persist", "rngstream", "move", "gamegen"} & top))


# ---- scenes ---------------------------------------------------------------------------------------------
#: The pinned corpus: a declared grid of quantities plus the boundary tuples, each with its grown successor,
#: and a golden generational sequence. A coarse grid keeps the digest's preimage small; the exhaustive laws
#: cover every quantity.
GRID = tuple(range(0, CORPUS_MAX + 1, 17)) + (CORPUS_MAX,)
SCENES = ("table", "laws")


def scene_case(name):
    if name == "table":
        grid = "|".join("%d=%d" % (q, heir(q)) for q in GRID)
        bound = "|".join("%d=%d" % t for t in BOUNDARY)
        seq = ",".join(str(x) for x in generations(8, 10))
        return "num=%d|den=%d|grid=%s|bound=%s|seq8=%s" % (NUM, DEN, grid, bound, seq)
    if name == "laws":
        return ("oracles=%s|bound=%s|nonshrink=%s|seqmono=%s|floor=%s|mutants=%s|nonconst=%s|"
                "refuse=%s|leaf=%s") % (
            heir_matches_the_independent_oracles(),
            the_frozen_boundary_tuples_match(),
            growth_never_shrinks(),
            the_generational_sequence_is_monotone(),
            growth_is_strict_above_the_threshold(),
            a_planted_mutation_reddens(),
            two_inputs_produce_different_results(),
            refuse_is_total(),
            the_module_is_a_stdlib_leaf())
    raise HeirloomError(f"no scene named {name!r}")


def scene_result(name):
    return hashlib.sha256(MAGIC + b"|" + name.encode() + b"|"
                          + scene_case(name).encode()).hexdigest()


def heirloom_digest():
    return hashlib.sha256(MAGIC + b"|" + "|".join(scene_result(n)
                                                  for n in SCENES).encode()).hexdigest()


def golden(name):
    with open(_os.path.join(_HERE, "conformance_heirloom.txt"), encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                nm, dig = ln.split()
                if nm == name:
                    return dig
    raise HeirloomError(f"no golden named {name!r}")


def emitted_matches_pinned():
    return (all(scene_result(n) == golden(n) for n in SCENES)
            and heirloom_digest() == golden("heirloom"))


def an_unpinned_name_refuses():
    try:
        golden("not-a-scene")
    except HeirloomError as exc:
        return exc.code == "HEIRLOOM-REFUSE"
    return False


def main():
    print("HEIRLOOM — the certified generational-growth law: a derived quantity, not persistent state (URDRHEI1)")
    print("layer %s: %s | imports %s" % (LAYER, D24_ANSWER, ALLOWED_IMPORTS))
    print("formula: heir(q) = q + (q * %d) // %d   (grows by %d/%d each generation)" % (NUM, DEN, NUM, DEN))
    print()
    for q in (0, 7, 8, 16, 64, 255):
        print("  heir(%3d) = %d" % (q, heir(q)))
    print("  generations(8, 8) =", generations(8, 8))
    print()
    print("matches both independent oracles :", heir_matches_the_independent_oracles())
    print("frozen boundary tuples match     :", the_frozen_boundary_tuples_match())
    print("growth never shrinks             :", growth_never_shrinks())
    print("generational sequence monotone   :", the_generational_sequence_is_monotone())
    print("strict above threshold, 0 below  :", growth_is_strict_above_the_threshold())
    print("a planted mutation reddens       :", a_planted_mutation_reddens())
    print("not constant (two differ)        :", two_inputs_produce_different_results())
    print("refuse total (quantities, n)     :", refuse_is_total())
    print("stdlib leaf (no arc imports)     :", the_module_is_a_stdlib_leaf())
    print()
    for n in SCENES:
        print(n, scene_result(n))
    print("heirloom", heirloom_digest())
    print()
    print("does_not_show: that the progression is rewarding or balanced (not gateable, D24 §4); WHERE the")
    print("quantity is kept (no persistence substrate yet); that a hero inherits it (no entity binding);")
    print("randomized growth; and nothing about the source-constant direction register, over git history.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
