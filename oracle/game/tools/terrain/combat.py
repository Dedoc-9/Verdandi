# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""combat — the certified damage-resolution law: a derived result, not persistent state (URDRCMB1).

THE EIGHTH GAME-LAYER VERTICAL SLICE, and the first that is a CERTIFIED ARITHMETIC LAW rather than a
state transition. D24 §3 lists exactly this rung — "combat arithmetic: damage, mitigation and hit
resolution obey the declared formula exactly; the formula is data, the resolution is checked against it,
and a planted off-by-one reddens" — and draws the sharp line: gateable is "damage calculation is
deterministic and obeys the declared formula", NOT "this combat system is balanced". This module is the
gateable sentence and nothing more.

A DERIVED RESULT, NOT A MUTATED ENTITY — the transition fork settled by measurement. The natural shape
`(attacker, defender) -> (attacker', defender')` requires HEALTH to live on the entity across actions,
and the measurement refused it: `entity.FIELDS == ("pos",)`, and the construction chain
`Entity.FIELDS -> Entity(...) -> entity.at(pos) -> entity.digest_at(pos) -> move.state_bytes` means
adding an `hp` field would BREAK `move`'s existing position-only construction, not merely extend it.
Persistent health is therefore a NEW canonical-state contract with upstream consequences, and it belongs
at the rung where persistence is actually required — not here. So combat is the smaller, honest slice:

    resolve(attack, defense) -> damage          # a pure function; nothing persists, nothing mutates

the way `loot` GENERATED a drop without an inventory to put it in, and `descend` computed a successor
level without editing the one it left. The resolved integer composes forward — `combat -> resolved
damage -> a future health-bearing rung` — rather than forcing this rung to invent HP, an entity-schema
migration, attack/defense state, damage, RNG combat semantics and persistence all at once.

A REGISTERED ARITHMETIC EXPERIMENT WITH EXPLICIT DECLARED INPUTS. There is no canonical source for
`attack` or `defense` anywhere in the tree (measured: zero RPG numerics across the terrain modules), so
this rung does NOT pretend those values already belong to game state. `(attack, defense)` are the
DECLARED INPUTS to this law, integers in `0..STAT_MAX`, exactly as `magicdiv`/`horn`/`opcost` are
certified arithmetic laws over declared integer inputs. A later rung binds real combatants to this
function; disguising invented stats as entity fields is refused.

THE FORMULA, AND IT IS THE SMALLEST ONE THAT STILL MITIGATES:

    damage = max(0, attack - defense)

Minimality forces every choice. SUBTRACTION, not division — a divisive mitigation curve introduces
truncation semantics this rung has not earned. FLOOR 0, not 1 — a minimum-damage rule ("every hit
chips at least 1") is an ADDED law, deferred; a fully-mitigated attack deals exactly zero. DETERMINISTIC
— no hit/miss roll and no `rngstream` edge, because the smallest law needs no randomness and importing
the stream merely because it exists is refused; a later rung that earns a random hit/damage revises this
explicitly. Mitigation IS present (defense reduces damage), which is what makes this combat arithmetic
rather than a bare number and what keeps the planted-mutation falsifier non-vacuous.

NO RESULT DIGEST YET. `loot`'s drop earned a `URDRLOO1|item:<id>` identity because a drop is a thing the
game will name; a damage integer is not named by anything yet, so it gets no `dmg:<n>` representation —
the conformance corpus IS the identity. A representation is added the day a result must be
content-addressed, not before.

THE INDEPENDENT ORACLE IS STRUCTURALLY SEPARATE — the neutral-ruler discipline. A test of the form
`assert resolve(a,d) == combat_formula(a,d)` is worthless if both share the same implementation
assumption. So the reference here is `a - min(a, d)` — saturating subtraction derived the OTHER way
(via `min`, not `max`), agreeing with `resolve` on the whole domain but sharing none of its structure —
and the gate/tests additionally pin a corpus of FROZEN LITERAL boundary tuples that share no code with
`resolve` at all. A `+1`, a `<`-vs-`<=`, or a floor-clamp mutation is caught by BOTH.

GRADE (honest, D5). MEASURED: over the full `0..STAT_MAX` square, `resolve` equals the independent
`min`-oracle; the frozen boundary tuples match; damage is monotone non-increasing in defense and
non-decreasing in attack; for `attack > defense` the damage is exactly `attack - defense`; a
fully-mitigated attack (`attack <= defense`) is exactly zero. ESTABLISHED: the three planted mutations
(`max(0,.)->max(1,.)`, `a-d -> a-d+1`, the dropped exact-tie damage) each disagree with the independent
oracle, so the falsifier bites; malformed or out-of-range inputs refuse typed COMBAT-REFUSE; the module
mutates nothing and its declared substrate is stdlib only (no `entity`, no `move`, no `rngstream`, read
off its own AST). DECLARED: that the formula is `max(0, attack - defense)` over `0..STAT_MAX`, that a
minimum-damage floor, division-based mitigation, hit/miss and randomness are LATER rungs', and that the
result is a bare integer with no canonical representation yet. does_not_show: that combat is balanced or
fun (not gateable, D24 §4); that damage persists to any entity (there is no health field — a future
rung's contract); that a hit is randomized or can miss (deterministic here); that loot's item ids carry
attack values (they are bare strings); and nothing about `rngstream`, which this rung does not touch."""
import hashlib
import os as _os

_HERE = _os.path.dirname(_os.path.abspath(__file__))

MAGIC = b"URDRCMB1"

LAYER = "CORE"
D24_ANSWER = "affects canonical game state — the certified damage-resolution law (a derived result)"
ALLOWED_IMPORTS = ("hashlib", "os")

#: DECLARED — the input domain for a combat stat: a non-negative byte. This is the rung's declared
#: operand vocabulary, NOT a field smuggled onto any entity; a later rung that binds a real combatant's
#: numbers to this law supplies them from wherever it earns them. Big enough that the exhaustive
#: agreement and the mutation falsifier are non-degenerate.
STAT_MAX = 255


class CombatError(Exception):
    def __init__(self, message):
        super().__init__(f"COMBAT-REFUSE: {message}")
        self.code = "COMBAT-REFUSE"


def _is_stat(v):
    # a plain int in 0..STAT_MAX; bool is a subclass of int and is excluded
    return type(v) is int and 0 <= v <= STAT_MAX


def _check(attack, defense):
    """MALFORMED-ONLY refusal: each of `attack`, `defense` must be an int in `0..STAT_MAX`. A float, a
    bool, a string, a negative or an over-range value refuses typed — never a clamp or a silent cast."""
    if not _is_stat(attack):
        raise CombatError(f"attack must be an int in 0..{STAT_MAX}, got {attack!r}")
    if not _is_stat(defense):
        raise CombatError(f"defense must be an int in 0..{STAT_MAX}, got {defense!r}")


def resolve(attack, defense):
    """THE LAW: `damage = max(0, attack - defense)`. Pure and total over the declared domain — the same
    `(attack, defense)` yields the same damage on any host, and nothing is mutated or persisted."""
    _check(attack, defense)
    return max(0, attack - defense)


# ---- the INDEPENDENT oracle (structurally separate: `min`, not `max`) -----------------------------------
def _oracle(attack, defense):
    """A DELIBERATELY INDEPENDENT reference: saturating subtraction as `attack - min(attack, defense)` —
    "remove the mitigated portion (capped at attack) from attack". It agrees with `resolve` on the whole
    domain but shares none of its structure, so a mutation to `resolve` (a `+1`, a floor change, a
    comparison flip) makes the two disagree. Used only by the laws below; a test re-derives its own
    oracle and its own frozen tuples so the check does not rest on this one function."""
    return attack - min(attack, defense)


#: FROZEN LITERAL boundary corpus — hand-computed expectations that share NO code with `resolve`. The
#: strongest neutral ruler: a mutation is caught by comparison against constants.
BOUNDARY = (
    (0, 0, 0), (5, 5, 0), (6, 5, 1), (5, 6, 0), (10, 3, 7), (0, 5, 0), (7, 0, 7),
    (1, 0, 1), (255, 0, 255), (0, 255, 0), (255, 255, 0), (255, 254, 1), (128, 64, 64),
)


# ---- the laws / falsifiers ------------------------------------------------------------------------------
def resolve_matches_the_independent_oracle():
    """MEASURED, exhaustively: `resolve(a,d) == a - min(a,d)` for every `(a,d)` in the declared square.
    The two are different derivations of saturating subtraction, so equality across the whole domain is
    evidence the law is right, not that one copied the other."""
    for a in range(STAT_MAX + 1):
        for d in range(STAT_MAX + 1):
            if resolve(a, d) != _oracle(a, d):
                return False
    return True


def the_frozen_boundary_tuples_match():
    """MEASURED: the hand-computed boundary expectations hold — the corpus that shares no implementation
    with `resolve`."""
    return all(resolve(a, d) == dmg for a, d, dmg in BOUNDARY)


def a_fully_mitigated_attack_is_exactly_zero():
    """The clamp is a FLOOR OF ZERO, not one: for every `attack <= defense`, damage is exactly 0 — a hit
    that does not overcome defense deals nothing, and no minimum-damage rule is in force."""
    for a in range(STAT_MAX + 1):
        for d in range(a, STAT_MAX + 1):     # d >= a
            if resolve(a, d) != 0:
                return False
    return True


def an_overcoming_attack_is_exactly_the_difference():
    """For every `attack > defense`, damage is exactly `attack - defense` — no rounding, no bonus, no
    minimum. The mitigation is pure subtraction above the floor."""
    for a in range(STAT_MAX + 1):
        for d in range(0, a):                 # d < a
            if resolve(a, d) != a - d:
                return False
    return True


def damage_is_monotone():
    """Structural sanity that a bare table could not fake: more defense never RAISES damage, more attack
    never LOWERS it. Checked on a coarse grid across the domain (the exhaustive laws above already pin
    the values; this pins the SHAPE)."""
    step = 15
    grid = list(range(0, STAT_MAX + 1, step)) + [STAT_MAX]
    for a in grid:
        for d in grid:
            if d + step <= STAT_MAX and resolve(a, d) < resolve(a, d + step):
                return False
            if a + step <= STAT_MAX and resolve(a + step, d) < resolve(a, d):
                return False
    return True


def _mutants():
    """The three planted mutations of the law, each an off-by-one at an EARNED boundary. Returned as
    callables so the non-vacuity witness can prove each one reddens against the independent oracle."""
    return {
        "floor_0_to_1": lambda a, d: max(1, a - d),          # the clamp floor
        "off_by_one":   lambda a, d: max(0, a - d + 1),      # the subtraction
        "drop_the_tie": lambda a, d: (a - d) if a - d > 1 else 0,   # a-d+1==1 tie damage dropped
    }


def a_planted_mutation_reddens():
    """NON-VACUITY, and it is the point of the rung: each planted mutant DISAGREES with the independent
    oracle somewhere in the declared domain, so the falsifier can actually bite. Returns True iff all
    three mutants are caught — a mutant that agreed everywhere would mean the law was untestable."""
    caught = 0
    for _name, mut in _mutants().items():
        if any(mut(a, d) != _oracle(a, d)
               for a in range(STAT_MAX + 1) for d in range(STAT_MAX + 1)):
            caught += 1
    return caught == len(_mutants())


def two_inputs_produce_different_results():
    """The zero-effect guard: the law is not constant — at least two declared inputs give different
    damages, so a corpus of it certifies something."""
    return resolve(10, 3) != resolve(5, 5)


def refuse_is_total():
    """(attacks, defenses): each malformed or out-of-range argument refuses typed COMBAT-REFUSE — never
    a clamp, a cast or a silent default."""
    a_ref = 0
    for bad in (-1, STAT_MAX + 1, 1.0, "5", None, True):
        try:
            resolve(bad, 0)
        except CombatError as exc:
            a_ref += exc.code == "COMBAT-REFUSE"
    d_ref = 0
    for bad in (-1, STAT_MAX + 1, 1.0, "5", None, False):
        try:
            resolve(0, bad)
        except CombatError as exc:
            d_ref += exc.code == "COMBAT-REFUSE"
    return a_ref == 6, d_ref == 6


def the_module_is_a_stdlib_leaf():
    """The layer boundary, read off this module's OWN AST: module-scope imports are exactly
    `ALLOWED_IMPORTS` (stdlib only) — no `entity`, no `move`, no `rngstream`. Combat is a pure arithmetic
    law, coupled to no game module, consuming no stream."""
    import ast
    with open(_os.path.join(_HERE, "combat.py"), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    top = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            top.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            top.add((node.module or "").split(".")[0])
    return (top == set(ALLOWED_IMPORTS)
            and not ({"entity", "move", "rngstream", "gamegen", "descent"} & top))


# ---- scenes ---------------------------------------------------------------------------------------------
#: The pinned corpus: a declared grid of (attack, defense) pairs plus the boundary tuples, each with its
#: resolved damage. A coarse grid (every 17th value) keeps the digest's preimage small while covering the
#: domain; the exhaustive laws above cover every pair.
GRID = tuple(range(0, STAT_MAX + 1, 17)) + (STAT_MAX,)
SCENES = ("table", "laws")


def table_row(a, d):
    return "%d,%d=%d" % (a, d, resolve(a, d))


def scene_case(name):
    if name == "table":
        grid = "|".join(table_row(a, d) for a in GRID for d in GRID)
        bound = "|".join("%d,%d=%d" % t for t in BOUNDARY)
        return "max=%d|grid=%s|bound=%s" % (STAT_MAX, grid, bound)
    if name == "laws":
        return ("oracle=%s|bound=%s|floor=%s|diff=%s|mono=%s|mutants=%s|nonconst=%s|refuse=%s|leaf=%s") % (
            resolve_matches_the_independent_oracle(),
            the_frozen_boundary_tuples_match(),
            a_fully_mitigated_attack_is_exactly_zero(),
            an_overcoming_attack_is_exactly_the_difference(),
            damage_is_monotone(),
            a_planted_mutation_reddens(),
            two_inputs_produce_different_results(),
            refuse_is_total(),
            the_module_is_a_stdlib_leaf())
    raise CombatError(f"no scene named {name!r}")


def scene_result(name):
    return hashlib.sha256(MAGIC + b"|" + name.encode() + b"|"
                          + scene_case(name).encode()).hexdigest()


def combat_digest():
    return hashlib.sha256(MAGIC + b"|" + "|".join(scene_result(n)
                                                  for n in SCENES).encode()).hexdigest()


def golden(name):
    with open(_os.path.join(_HERE, "conformance_combat.txt"), encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                nm, dig = ln.split()
                if nm == name:
                    return dig
    raise CombatError(f"no golden named {name!r}")


def emitted_matches_pinned():
    return (all(scene_result(n) == golden(n) for n in SCENES)
            and combat_digest() == golden("combat"))


def an_unpinned_name_refuses():
    try:
        golden("not-a-scene")
    except CombatError as exc:
        return exc.code == "COMBAT-REFUSE"
    return False


def main():
    print("COMBAT — the certified damage-resolution law: a derived result, not persistent state (URDRCMB1)")
    print("layer %s: %s | imports %s" % (LAYER, D24_ANSWER, ALLOWED_IMPORTS))
    print("formula: damage = max(0, attack - defense)  over 0..%d" % STAT_MAX)
    print()
    for a, d in ((10, 3), (5, 5), (6, 5), (5, 6), (255, 254)):
        print("  resolve(attack=%3d, defense=%3d) = %d" % (a, d, resolve(a, d)))
    print()
    print("matches independent min-oracle :", resolve_matches_the_independent_oracle())
    print("frozen boundary tuples match   :", the_frozen_boundary_tuples_match())
    print("fully-mitigated is exactly 0   :", a_fully_mitigated_attack_is_exactly_zero())
    print("overcoming is exactly a-d      :", an_overcoming_attack_is_exactly_the_difference())
    print("damage is monotone             :", damage_is_monotone())
    print("a planted mutation reddens     :", a_planted_mutation_reddens())
    print("not constant (two differ)      :", two_inputs_produce_different_results())
    print("refuse total (attacks, defenses):", refuse_is_total())
    print("stdlib leaf (no game imports)  :", the_module_is_a_stdlib_leaf())
    print()
    for n in SCENES:
        print(n, scene_result(n))
    print("combat", combat_digest())
    print()
    print("does_not_show: that combat is balanced (not gateable, D24 §4); that damage persists to an")
    print("entity (no health field — a later rung's contract); that a hit is randomized or can miss")
    print("(deterministic here); that loot's item ids carry attack values; nothing about rngstream.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
