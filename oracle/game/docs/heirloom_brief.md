<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- brief-falsifier: heirloom-growth -->
# `heirloom` — design brief (URDRHEI1, the certified generational-growth law)

**Built**: 2026-09-18, one rung after `combat`, on the boundary measured from `entity`, `ratchet`, the
existing `persist.py`, and the whole game-layer chain. It is the **ninth game-layer vertical slice** and the
second **certified arithmetic law** (after `combat`) rather than a state transition — D24 §3's *heirloom
progression*, gateable as "the growth is deterministic and obeys the declared fraction" and never §4's "the
progression is rewarding or balanced".

## 0. What it is

A pure function over a declared non-negative integer quantity:

    heir(q) = q + (q * NUM) // DEN         # NUM/DEN = 1/8
    → q'

Nothing persists, nothing mutates, no randomness is consumed. Generations are a computed sequence.

## 1. The transition was settled `quantity → quantity'`, by measurement (like combat)

The natural shape `persistent_retirement_state → persistent_retirement_state'` needs somewhere to **keep**
the inherited quantity across generations, and the measurement found **none**:

- **No game-layer persistence substrate.** The `persist` rung is chain rung 9, unbuilt; the existing
  `persist.py` (URDRLAT5) is the **MMO/netcode** rollback-window durable checkpoint — a different arc, and
  **no game-layer module imports it** (verified across gamegen…combat).
- **No entity container.** `entity.FIELDS == ("pos",)`, and the construction chain
  `entity.at(pos) → entity.digest_at(pos) → move.state_bytes` means a progression field would **break
  `move`** — the seam `combat` established.
- **No direction-register container.** The tree's direction-and-baseline authority operates on module-level
  **source constants across git history** (content-addressed blob baselines); it cannot hold a *runtime*
  quantity.

So **making a container inside `heirloom` would be architectural invention, not implementation.** heirloom is
the smaller, honest slice: `heir(q) → q'`, a pure function, the way `combat` generated a damage integer with
no health to store it in and `loot` generated a drop with no inventory. The quantity composes forward:
`heirloom → grown quantity → a future persistence / entity-binding rung`.

## 2. A registered arithmetic experiment with a declared input

No canonical quantity exists that heirloom could inherit (`gamegen`'s seed/depth, `entity`'s position,
`rngstream`'s `(n, R_n)`, `loot`'s drop, `combat`'s damage — none is a persistable progression quantity). So
`q` is a **declared integer input** over the non-negative integers, exactly as `magicdiv`/`horn`/`opcost`/
`combat` are certified arithmetic laws over declared inputs. A later rung binds a real retiring hero's
quantity to this function.

## 3. The formula is the smallest one that still grows by a fraction

`heir(q) = q + (q * NUM) // DEN`. Minimality forces every choice:

- **an integer ratio with floor division**, not a `Fraction` — fractional arithmetic here is `magicdiv`'s
  integer-division discipline, and `fractions.Fraction` appears in this tree *only as an adversarial plant
  other modules refuse* (a cross-type-equality hazard), never as a canonical number;
- **monotone non-decreasing**, not a minimum-growth rule: `heir(q) ≥ q` for every `q`, strictly greater only
  once the floor contribution turns positive (`q ≥ DEN/NUM = 8`); below that threshold the floor legitimately
  yields **zero growth** — the honest behaviour of the declared fraction, asserted directly rather than
  papered over with a `max(1, …)` clamp (that minimum-growth rule is a **defer**, and its mutation reddens);
- **deterministic** — no randomness, no `rngstream` edge.

The **generations** are a pure sequence `q₀ → q₁ → q₂ …` folded from a declared baseline, **computed, not
stored** — the way `rngstream.trace` folds a sequence without persisting it.

## 4. The oracle is structurally separate — the neutral-ruler discipline

`heir` is `q + (q*NUM)//DEN` (add after floor). The rulers share none of its structure:

- an **independent combined-numerator oracle** `(q*(DEN+NUM))//DEN` (a single floor of a combined numerator —
  provably equal because `q*DEN` is divisible by `DEN`, yet a different expression);
- a **count-of-multiples oracle** that uses **no floor division at all** (it counts the multiples of `DEN` at
  or below `q*NUM`);
- a third **loop-accrual oracle** written in the test and the gate stage;
- a corpus of **frozen literal boundary tuples** — constants, no algorithm.

A shrink, a replace-not-grow, or an off-by-one is caught by all of them. **Non-vacuity is proven**: four
planted mutations (shrink, replace, off-by-one, and the deferred minimum-growth-1) each disagree with an
independent oracle, and the law is not constant.

## 5. No result representation yet

A grown quantity is not named by anything, so it gets no `q:<n>` byte form — the conformance corpus **is** the
identity, exactly as `combat`'s damage integer earned none. A representation is added the day a result must be
content-addressed.

## 6. A stdlib leaf — the predicted dependencies are superseded by measurement

heirloom imports **only** `hashlib`/`os` — no `entity`, `persist`, `rngstream`, the direction-and-baseline
register, or any game module (read off its AST), import-depth 0, hosting no REQUIRES chain. The roadmap's
earlier-predicted `entity` + direction-register dependencies are **superseded by measurement**, the way
`combat`'s predicted `entity`/`rngstream` were. Notably, heirloom does not even mention the direction register
in a way that couples it: it makes its own monotonicity claim over a runtime quantity, a categorically
different object from a source-constant debt.

## 7. Grade

**MEASURED**: over the whole `0..CORPUS_MAX` corpus `heir` equals both independent oracles; the frozen
boundary tuples match; growth never shrinks; the generational sequence is monotone non-decreasing; growth is
strictly positive for `q ≥ DEN/NUM` and exactly zero below it. **ESTABLISHED**: the four planted mutations
each disagree with an independent oracle; malformed or negative inputs (bool excluded) refuse typed
`HEIRLOOM-REFUSE`; the module mutates nothing and its substrate is stdlib only. **DECLARED**: that the
fraction is `NUM/DEN = 1/8`, that the growth is monotone non-decreasing (with an intentional zero-growth
region below the floor threshold), and that a minimum-growth rule, where the quantity lives, entity binding,
persistence and multi-attribute progression are later rungs'.

## does_not_show

That the progression is rewarding, balanced or fun (not gateable, D24 §4); **where** the quantity is kept
(there is no persistence substrate yet — a future rung's contract); that a hero inherits it (no entity
binding); that growth is randomized; and nothing about the direction-and-baseline register, whose machinery is
over source constants in git history, a different substrate.

## Falsifier

`heirloom-growth` (the declared fraction `q + (q*NUM)//DEN` is obeyed and checked against neutral rulers, not
itself: exhaustive agreement with an independent combined-numerator oracle, a count-of-multiples oracle and a
loop-accrual oracle, the frozen literal tuples matching; growth is monotone non-decreasing, strictly positive
above the floor threshold and exactly zero below it; the generational sequence is monotone and unbounded; and
each of four planted mutations reddens against the oracle), with `heirloom:scenes` (the two scenes and the top
digest reproduce, an unpinned name refuses) and `heirloom-isolation` (a pure stdlib leaf — no
`entity`/`persist`/`rngstream`, no state mutation, no result representation, typed `HEIRLOOM-REFUSE`)
alongside; `tests/test_heirloom.py`.
