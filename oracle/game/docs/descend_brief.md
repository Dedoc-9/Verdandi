<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- brief-falsifier: descend-transition -->
# `descend` — design brief (URDRDEP1, the authoritative depth transition)

**Built**: 2026-09-17, one rung after `rngstream`, on the boundary measured from `gamegen`, `descent`
and `move` before a line was written. It is the single `D_n → D_{n+1}` that changes **depth** — the run
was stuck on one floor, and this is how it moves to the next.

## 0. What it is

An entity standing on the **down-stairs** of the level at depth `d` arrives at the level at depth `d+1`,
at that level's own **stairs-up**. Nothing else moves depth in the game layer: `gamegen` makes one level
from `(seed, depth)`, `descent` witnesses connectivity, `move` steps *within* a level, `entity` names the
position, `rngstream` holds the stream — none of them advances `depth`.

## 1. The transition, and why the old position has no authority

    precondition   pos == descent.endpoints(level).down
    transition     level' = gamegen.generate(level.seed, level.depth + 1)
                   pos'   = descent.endpoints(level').up
    postcondition  pos' == move.spawn(level')

The measurement fixed the arrival. The successor's layout is generated **independently** from
`(seed, d+1)`, so the old down-stairs coordinate has no standing in the new level — it is not even
reliably traversable there (measured: a wall in some successors). Carrying the entity to its old `(x, y)`
would drop it in a wall. The only authoritative successor position is the new level's stairs-up, which is
`move.spawn(level')`, traversable by construction. So descend is not a "teleport" rule invented here; it
is the existing spawn rule, consumed — and descend deliberately does **not** re-prove that the successor
up-stairs is traversable, because `descent`/`gamegen` already establish that invariant.

## 2. It consumes authority it does not own, and owns exactly one new thing

- **Depth** is `gamegen`'s. The bound `DEPTH_MAX`, the admission of `d+1` and the ceiling refusal are all
  `gamegen.check_params`. Descend **names no `DEPTH_MAX`** of its own (checked on its AST) and adds no
  second depth law.
- **The successor level** is `gamegen.generate(seed, d+1)` — same seed, one deeper — its identity the
  unchanged `gamegen.level_digest`.
- **The stairs** are `descent.endpoints`: the unique down-stairs (precondition) and the successor's unique
  up-stairs (arrival). Descend re-locates and re-proves neither.
- **The one new thing** is the depth transition itself and its single precondition: you may descend only
  from the down-stairs. `DESCEND-REFUSE` iff the supplied position is not the level's unique down endpoint.

The successor's canonical identity is composed in the **one existing `(level, entity)` vocabulary** —
`move.state_digest(level', pos')` — so descend introduces no second serialization: the state it lands in
is named the way every canonical `(level, entity)` state is.

## 3. Ownership stays crisp

    malformed / invalid level         → descent / gamegen (their refusals)
    invalid command                   → move
    blocked movement (D_{n+1} = D_n)  → move (never an arrival on the down-stairs)
    depth ceiling (d = DEPTH_MAX)     → gamegen (GAMEGEN-REFUSE, inherited)
    valid arrival on the down-stairs  → descend
    descend off the down-stairs       → descend (DESCEND-REFUSE)

A malformed level (no unique down) is outside `descent`'s domain, so descend's precondition surfaces
`descent`'s `DESCENT-REFUSE`, never ours — the malformed-input refusal stays with the authority that owns
the shape.

## 4. The ceiling, and the ordering that is the claim

The most important negative witness is not merely `d == DEPTH_MAX`; it is that **DOWN at `DEPTH_MAX`
refuses without generating a successor and without mutating canonical state**. Descend asks
`gamegen.check_params(seed, d+1)` *first*, so at the ceiling it raises `GAMEGEN-REFUSE` before `generate`
is reached — the boundary ordering, not merely a propagated refusal. It is proved three ways: the code is
gamegen's; the input level is unchanged after the refused call; and descend's source names no `DEPTH_MAX`
literal. The complementary **positive** witness tests the other side: from `DEPTH_MAX − 1` a descent
produces depth `DEPTH_MAX`, its identity exactly `gamegen.generate(seed, DEPTH_MAX)`.

## 5. RNG is untouched

The successor is fully determined by `(seed, d+1)`, so no draw is consumed: descend never receives or
returns a stream, imports no `rngstream`, and a law reads that off its AST. The independence is structural
— descend cannot advance a stream it never holds.

## 6. Grade

**MEASURED**: over the corpus, a descent from the down-stairs produces `gamegen.generate(seed, d+1)` with
the entity at that level's stairs-up, and the successor identity is exactly the existing canonical
vocabulary for `(level', spawn)`; at `DEPTH_MAX − 1` the successor is depth `DEPTH_MAX`, matching
`gamegen.generate(seed, DEPTH_MAX)`. **ESTABLISHED**: the arrival equals `move.spawn(level')`; the ceiling
refuses through `gamegen`'s authority without generating a successor or mutating the input, and this module
names no `DEPTH_MAX`; descending off the down-stairs refuses typed `DESCEND-REFUSE` while a malformed level
surfaces `descent`'s `DESCENT-REFUSE`; this module imports no `rngstream`. **DECLARED**: that a descent
begins at the successor's stairs-up — a fresh floor from the top, the FATE model — and that there is no
ascent in this rung (a later law, if earned).

## does_not_show

Whether the successor level is worth playing or reachable (`gamegen`'s and `descent`'s claims, unchanged);
that the entity carries anything but its position across the transition (health, inventory are later
fields, and descend touches none of them); that the RNG advances on a descent (it does not, and whether
any real action ever advances the stream is `rngstream`'s and `loot`'s question); and any relation between
two floors beyond seed and `depth + 1`.

## Falsifier

`descend-transition` (from the down-stairs, the successor is `gamegen.generate(seed, d+1)` at
`move.spawn(level')`, its identity the one `move` vocabulary; off the down-stairs refuses `DESCEND-REFUSE`,
a malformed level is `descent`'s refusal, and no `rngstream` is imported), with `descend:scenes` (the three
scenes and the top digest reproduce, an unpinned name refuses) and `descend-boundary` (the ceiling refuses
`GAMEGEN-REFUSE` before generating, with no `DEPTH_MAX` of its own, and `DEPTH_MAX − 1` descends to
`DEPTH_MAX`) alongside; `tests/test_descend.py`.
