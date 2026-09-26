<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- brief-falsifier: kinema-refine -->
# `kinema` — design brief (URDRKIN1, D25: the one-way observer-space refinement membrane)

**Built**: 2026-09-19, one rung after `statecanon`, on the boundary the D25 measurement pass established. It is
the **fifteenth game-layer vertical slice**, D25's **cinematic membrane**, and the **first game-layer VIEW
module** — every rung before it *affects* canonical game state; this one only *produces a view* of it.

## 0. What it is

    classify(level_n, pos_n, level_m, pos_m) -> MOVED | FIXED | LEVELCUT   (or KINEMA-REFUSE on a forgery)
    frames(level_n, pos_n, w_n, level_m, pos_m, w_m, source_tick, k) -> (Frame, …)

It is **handed** a real authoritative transition — `enact.dispatch` produces consecutive canonical states
`Dₙ → Dₙ₊₁`, `statecanon` identifies both ends — and refines **between** the two endpoints. It never computes
the successor it observes.

## 1. The refinement is of the position, in observer space, never the digest

`Dₙ` is a 64-hex SHA — arithmetic on it is meaningless. The interpolable quantity is the entity **position**
(integer cell coordinates), refined in the **frozen Q32.32 substrate** (`field.ONE`, the FIELDFP radix,
consumed not reinvented):

    before = A·ONE ;  after = B·ONE
    refined = before + ((α · (after − before)) // ONE)        (D25 §6; floor via // ONE)

`α = 0` lands on `A` exactly, `α = ONE` lands on `B` exactly. The arithmetic is graded **reference**
(unbounded-integer) on the frozen radix; a bounded-i64 model is a **declared cross-placement obligation**
(D25 §6), not claimed here — the same grade the FIELDFP substrate carries until its C/Rust placements.

## 2. Three transition shapes, only one spatially refined

| class | condition | refinement |
|---|---|---|
| **MOVED** | same level, orthogonally adjacent, both cells `descent.traversable` | interpolated in Q32.32 |
| **FIXED** | same level, same cell (a BLOCKED move, or a LOOT) | a spatial fixed point (every sample = A) |
| **LEVELCUT** | the level identity differs (a DESCEND) | a **discrete** two-frame cut, never interpolated |

Interpolating a position across a level change is a fiction (the two positions live on different levels), so a
LEVELCUT emits only its two endpoint frames.

## 3. Containment consumes the real topology; the forged pair is the falsifier

`descent.traversable` is the one traversability authority; this module asks it rather than inventing a weaker
one. A MOVED refinement is admitted only over a legal move edge (both endpoints traversable and adjacent),
single-sourced in `descent` exactly as `move` single-sources it, and every sample floors into `{A, B}`.
Everything else is a **false visual witness** and refuses typed `KINEMA-REFUSE`:

- **Plant A** — a BLOCKED move presented as motion: the target is a **wall** (the refused boundary), so
  `descent.traversable` is False.
- **Plant B (realizable form)** — a forged **non-adjacent / wall-crossing** endpoint pair the authority never
  produced.

With the currently earned **single-cell** MOVE vocabulary there is no cell *between* two adjacent cells, so the
literal `A─X─B` intermediate-wall plant has no realizable instance. Manufacturing a multi-cell move solely to
give it one would invent gameplay authority, so it is **deferred**, and non-vacuity is carried by the real
topology against forged endpoint claims instead.

## 4. The membrane is one-way, and the output is disposable

A `Frame{source_tick, α, refined, witness_n, witness_m, cls}` carries **both endpoint witnesses verbatim** —
the D15 `terrain_view` pattern: a view carries the authority witness and may never write back into it. Nothing
produced feeds a canonical component (a view field cannot even enter `entity`; `statecanon` already proves it
never reaches `Dₙ`).

## 5. The structural guard is a fourth layer (D25 §11), stronger than the tree's existing ones

`the_membrane_is_one_way` reads this module's **own full AST** — **function-local imports included** — and is
**direction-aware**: it imports exactly `ALLOWED_IMPORTS`, imports **none** of the authority modules
(`move`/`descend`/`loot`/`enact`/`statecanon`/`rerun`/`lockstep`) in any scope, and reaches no
`.step`/`.dispatch`/`.apply` mutator, so it can never manufacture the successor it observes. This deliberately
closes the **function-local escape hatch** the tree's existing top-level-only import guards leave open (the one
`terrain_bridge` exploits). It carries a **positive control** — a synthetic module that sneaks a function-local
`enact` import and a `.dispatch` call is rejected — so the checker is shown to bite.

## 6. The observer-presence differential (D25 §14)

The gate stage runs the stronger, whole-tree question: the canonical component digests and the `rerun` replay
verdict are **byte-identical whether or not `kinema` is exercised**, and no CORE module imports `kinema`. Plant
D's local half (the sample count is view-only) lives in the module; this is the global half — *does the
existence of the observer alter the certified simulation at all?* — and the answer is measured, not asserted.

## 7. Grade

**MEASURED**: endpoints land exactly; every sample of a permitted transition is contained in `{A, B}`; a FIXED
transition is stationary; a LEVELCUT is a discrete two-frame cut; the sample count is view-only (2/6/60/144
samples, same endpoints, all contained); the endpoint witnesses are carried verbatim. **ESTABLISHED**: a
wall-target and a non-adjacent/wall-crossing forged pair refuse `KINEMA-REFUSE` against `descent.traversable`;
the module is one-way (full-AST, direction-aware, with a positive control); the observer-presence differential
holds. **DECLARED**: the cell coordinate is the position (no world-coordinate lift this slice); the sample set
is `α_i = i·ONE//(k−1)`; the arithmetic is reference on the frozen radix; single transition, single peer.

## does_not_show

What a view should *look like* (D25 §12); a bounded-i64 model (§6, a cross-placement obligation); multi-cell or
curved trajectories, smooth-height interpolation, camera/pose (`gaze`/`vantage`'s), a voxel/observer scene,
developer-mode authoring, network/replay connection, and any wall-clock or frame budget (§13, off-gate by
rule).

## Falsifier

`kinema-refine` (the refinement law: endpoints land exactly, every sample of a real `descent`-traversable move
edge is contained in `{A, B}`, a LEVELCUT is a discrete cut and a FIXED transition is stationary, computed over
live `enact` transitions in the gate stage), with `kinema:scenes` (the two scenes and the top digest reproduce,
an unpinned name refuses typed `KINEMA-REFUSE`) and `kinema-membrane` (forged wall-crossing and non-adjacent
pairs refuse; the full-AST direction-aware one-way guard bites with its positive control; no CORE module
imports `kinema`; and the observer-presence differential leaves the canonical transcript byte-identical)
alongside; `tests/test_kinema.py`.
