<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- brief-falsifier: move-authority -->
# `move` — design brief (URDRMOV1, the first authoritative transition)

**Built**: 2026-09-16, on the interfaces measured from `gamegen` and `descent` before a line was
written. It is the first game-layer rung that MOVES anything — the first authoritative
`D_n → D_{n+1}` in the tree, and therefore the first thing KINEMA (D25) will one day have to refine.

## 0. What it is

An entity at a cell takes **one step** under a movement command, and the authority answers **MOVED**
(it stepped onto a traversable cell) or **BLOCKED** (a wall or the grid edge denied it, so it stayed
put). Nothing else: no tick clock, no continuous motion, no second entity, no turn counter.

The rung is called the *transition* rung in the roadmap because it produces the authoritative
transition `D_n → D_{n+1}`; the module is named `move` because the kernel already owns the word
*transition* (the D1 §19 `transition_witness` primitive and its `tests/test_transition.py`), and the
tree keeps module basenames unique. The measurement finalized the name — exactly what "measure first,
then name" is for.

## 1. What it consumes — measured, not chosen

| # | question | answer |
|---|---|---|
| 1 | the entity representation | there was none; `gamegen.Level` has no entity, so `move` introduces the first field: an integer `(x, y)` |
| 2 | the traversability authority | `descent.traversable(level, x, y)` — **promoted to public** one change earlier for exactly this |
| 3 | did a position field already exist? | no — nothing to rename, a clean introduction |
| 4 | the command | one of four directions, `{N,S,E,W}`, which *are* `descent.STEPS` re-labelled |
| 5 | the spawn | `descent.endpoints(level)[0]` — the stairs-up, traversable by construction |
| 6 | identity | derived from `gamegen.level_digest`, not a parallel rule (§3) |

`move` **consumes `descent`'s authority; it does not reinvent it.** It never re-derives `cell in
TRAVERSABLE` and never reaches into a private — legality is single-sourced in `descent`, and a later
law that widens traversal (doors, keys, diagonals) changes it in one place and `move` inherits it.
The dependency runs one way: `move` imports `gamegen` and `descent`; neither knows `move` exists.

## 2. Three outcomes, and the distinction is load-bearing for KINEMA

    MOVED    the target is descent-traversable   →  D_{n+1} = entity at the target
    BLOCKED  the target is a wall or off-grid     →  D_{n+1} = D_n, the entity stayed
    REFUSE   the input is MALFORMED               →  typed MOVE-REFUSE

A wall step is **not** an error. It is an in-domain command whose authoritative outcome is "you do
not move" — a legal transition with `D_{n+1} = D_n`. Collapsing it into `REFUSE` would be wrong
twice: it would make walking into a wall a malformed input (the most ordinary thing a player does),
and it would leave **KINEMA's Plant A** (D25 §10) with nothing to consume — that plant is precisely
*"the authority refused a move, `D_n = D_{n+1} = A`, and a rendered `A→B` must be rejected"*, so the
authority has to **return** the blocked pair, not throw it. `REFUSE` is reserved for input outside
the domain of the question: a non-direction command, or an entity off the grid, on a wall, or not an
integer pair.

Legality is proved to track `descent`'s authority on a **counterexample**, not asserted:
`descent.seal_down` changes `descent.traversable`, and the same step that MOVED is now BLOCKED
wherever the seal walled its target — so `move` is a thin authority over `descent`'s predicate, and
`move-authority` re-checks that it has not drifted from it.

## 3. Identity, derived from the existing machinery

The canonical state is the level plus the entity position. The level's identity is **already**
`gamegen.level_digest` (SHA-256 of `URDRGEN1|s:|d:|WxH|rooms:…|rows`), so `move` **names the level by
that digest** — `worldbind`'s content-addressed precedent — and names the **entity** by its `entity.entity_digest` (the `entity` rung, URDRETY1, made the position a content-addressed component in the same vocabulary):

    state_digest = SHA-256( URDRMOV1|lvl:<level_digest>|ent:<entity_digest> )

No parallel identity rule and no second form: the level and the entity are both content-addressed, so `statecanon` composes them the same way. (When `move` first shipped it inlined `pos:x,y`; the `entity` rung one commit later replaced that with `ent:<entity_digest>` so there is one vocabulary through to `statecanon`.) A view-only quantity a later camera might carry — a fractional interpolated position, a
facing for animation — is not canonical and never reaches this digest; the integer cell is, because
it is what the next authoritative step reads. A MOVED step changes the digest; a BLOCKED step does
not.

## 4. Grade

**MEASURED**: over every corpus level, the four spawn outcomes and their state digests; each step
agrees with `descent.traversable` on its target; a walk into the bounded wall BLOCKS with a
well-formed fixed point; the sealed-mouth counterexample flips MOVED into BLOCKED; the identity
derivation reproduces. **ESTABLISHED**: `step` is a pure function of `(level, pos, command)` under a
hash-seed sweep; BLOCKED is a fixed point in position and digest while MOVED changes both; the REFUSE
domain is total. **DECLARED**: that a single orthogonal cell step is the movement model — widened by
a later law, not edited here — and that the entity is, for this rung, a bare position.

## does_not_show

That movement is timed or continuous — this is one discrete authoritative step, and KINEMA is the
rung that will make it *look* continuous by refining the `(D_n, D_{n+1})` this module produces. That
a BLOCKED step advances a turn counter or an action log (`actionlog`'s rung). That an entity is more
than a position (health, inventory, facing are later fields of D24 §2's entity state). And nothing
about **why** a level is traversable, which is `descent`'s claim and which `move` only consults.

## Falsifier

`move-authority` (every step agrees with `descent.traversable`, and the sealed-mouth counterexample
flips MOVED→BLOCKED), with `move:scenes`, `move-blocked` (a wall step is a fixed point; a walk blocks
at the wall; a moved step changes the digest) and `move-domain` (malformed REFUSE totality; the
derived identity) alongside; `tests/test_move.py`.
