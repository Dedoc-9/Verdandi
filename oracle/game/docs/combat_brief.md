<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- brief-falsifier: combat-resolution -->
# `combat` — design brief (URDRCMB1, the certified damage-resolution law)

**Built**: 2026-09-18, one rung after `loot`, on the boundary measured from `entity`, `loot`, `rngstream`
and `move`. It is the **eighth game-layer vertical slice** and the first that is a **certified arithmetic
law** rather than a state transition — D24 §3's *combat arithmetic*, gateable as "damage calculation is
deterministic and obeys the declared formula" and never as §4's "this combat system is balanced".

## 0. What it is

A pure function over declared integer inputs:

    resolve(attack, defense) = max(0, attack - defense)      # attack, defense ∈ 0..STAT_MAX (=255)
    → damage

Nothing persists, nothing mutates, no randomness is consumed. The result is a bare integer.

## 1. The transition fork was settled B (a derived result, not a mutated entity)

The natural shape `(attacker, defender) → (attacker', defender')` needs **health to live on the entity
across actions**, and the measurement refused it. `entity.FIELDS == ("pos",)`, and the construction chain

    Entity.FIELDS → Entity(...) → entity.at(pos) → entity.digest_at(pos) → move.state_bytes

means adding an `hp` field would **break `move`'s position-only construction**, not merely extend it —
`entity`'s own forward-compat proof only tests *serialization* append, never *construction*. Persistent
health is therefore a **new canonical-state contract with upstream consequences**, deferred to the rung
where persistence is actually required. So combat is the smaller, honest slice: `resolve(a, d) → damage`,
a pure function — the way `loot` **generated** a drop with no inventory to hold it and `descend` computed a
successor level without editing the one it left. The integer composes forward: `combat → resolved damage →
a future health-bearing rung`.

## 2. A registered arithmetic experiment with explicit declared inputs

There is **no canonical source** for `attack` or `defense` anywhere in the tree (measured: zero RPG
numerics across 190 terrain modules; the only combat-shaped module, `hitbox`/URDRHIT1, is anti-cheat *hit
validation*, pure geometry, no stats). So this rung does **not** pretend those values already belong to
game state. `(attack, defense)` are its **declared integer inputs** over `0..STAT_MAX`, exactly as
`magicdiv`/`horn`/`opcost` are certified arithmetic laws over declared inputs. A later rung binds real
combatants to this function; disguising invented stats as entity fields is refused.

## 3. The formula is the smallest one that still mitigates

`damage = max(0, attack - defense)`. Minimality forces every choice:

- **subtraction, not division** — a divisive mitigation curve introduces truncation semantics this rung
  has not earned;
- **floor 0, not 1** — a minimum-damage rule ("every hit chips at least 1") is an *added* law, deferred; a
  fully-mitigated attack (`attack ≤ defense`) deals exactly zero;
- **deterministic** — no hit/miss roll and **no `rngstream` edge**, because the smallest law needs no
  randomness and importing the stream merely because it exists is refused (`loot` established *real action →
  consumption*, not *every action → consumption*).

Mitigation **is** present (defense reduces damage), which is what makes this combat arithmetic rather than a
bare number and what keeps the planted-mutation falsifier non-vacuous.

## 4. The oracle is structurally separate — the neutral-ruler discipline

A test of the form `assert resolve(a,d) == combat_formula(a,d)` is worthless if both share the same
implementation assumption. So the resolution is checked against rulers that could not inherit the same bug:

- an **exhaustive independent oracle** `a - min(a, d)` — saturating subtraction derived the *other* way
  (via `min`, not `max`), agreeing on the whole `256×256` square but sharing no structure;
- a **third loop oracle** (iterated saturating decrement) written in the test and the gate stage;
- a corpus of **frozen literal boundary tuples** — hand-computed constants, no algorithm at all.

A `+1`, a `<`-vs-`<=`, or a floor-clamp mutation is caught by all three. **Non-vacuity is proven**: three
planted mutations (`max(0,·)→max(1,·)`, `a-d → a-d+1`, dropped exact-tie damage) each disagree with the
independent oracle, and the law is not constant (two inputs give different results).

## 5. No result representation yet

`loot`'s drop earned a `URDRLOO1|item:<id>` identity because a drop is a thing the game will name; a damage
integer is **not** named by anything yet, so it gets no `dmg:<n>` byte form — the conformance corpus **is**
the identity. A representation is added the day a result must be content-addressed, not before.

## 6. Grade

**MEASURED**: over the full `0..STAT_MAX` square `resolve` equals the independent `min`-oracle; the frozen
boundary tuples match; damage is monotone (non-increasing in defense, non-decreasing in attack); for
`attack > defense` the damage is exactly `attack - defense`, and for `attack ≤ defense` it is exactly zero.
**ESTABLISHED**: the three planted mutations each disagree with the independent oracle so the falsifier
bites; malformed or out-of-range inputs (bool excluded) refuse typed `COMBAT-REFUSE`; the module mutates
nothing and its declared substrate is stdlib only — no `entity`, `move` or `rngstream`, read off its own
AST. **DECLARED**: that the formula is `max(0, attack - defense)` over `0..STAT_MAX`, that a minimum-damage
floor, divisive mitigation, hit/miss and randomness are later rungs', and that the result is a bare integer
with no canonical representation yet.

## does_not_show

That combat is balanced or fun (not gateable, D24 §4); that damage persists to any entity (there is no
health field — a future rung's contract); that a hit is randomized or can miss (deterministic here); that
`loot`'s item ids carry attack values (they are bare strings); and nothing about `rngstream`, which this
rung does not touch.

## Falsifier

`combat-resolution` (the declared formula `max(0, attack - defense)` is obeyed and checked against a neutral
ruler, not itself: exhaustive agreement with an independent `min`-oracle and a loop oracle, the frozen
literal tuples match, mitigation is exact subtraction above a floor of zero, damage is monotone, the law is
not constant, and each of three planted mutations reddens against the oracle), with `combat:scenes` (the two
scenes and the top digest reproduce, an unpinned name refuses) and `combat-isolation` (a pure stdlib leaf —
no `entity`/`move`/`rngstream`, no state mutation, no result representation, typed `COMBAT-REFUSE`)
alongside; `tests/test_combat.py`.
