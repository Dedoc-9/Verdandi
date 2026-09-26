<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- brief-falsifier: statecanon-assembly -->
# `statecanon` — design brief (URDRSTC1, D24 §2: the assembled canonical identity `D_n`)

**Built**: 2026-09-19, one rung after `rerun`, on the boundary the statecanon measurement pass established. It
is the **fourteenth game-layer vertical slice** and D24 §2's **assembled-state** rung.

## 0. What it is

    d_n(level, entity, stream, log) -> the assembled canonical identity D_n (hex)
    d_n_preimage(level, entity, stream, log) -> the exact bytes d_n hashes

Every rung before it earned an identity for **one** component of a run. This rung earns **exactly one** new
authority — the single canonical identity `D_n` of the whole assembled run — by **composing** those four
already-earned identities. It reimplements none of them and adds no new state.

## 1. The law

    D_n = SHA-256( MAGIC | lvl:<level_digest> | ent:<entity_digest> | rng:<stream_digest> | log:<actionlog digest> )

Each component enters **only** through its own authority's identity function — `gamegen.level_digest`,
`entity.entity_digest`, `rngstream.stream_digest`, `actionlog.digest` — under a fixed label, delimited by the
reserved `|`. Every component identity is 64 hex characters and contains no `|`, so the labelled, fixed-width,
delimiter-framed preimage is **injective** in the four identities. `D_n` is the one and only new SHA-256 this
module mints: the composition itself.

## 2. The action history is part of the identity

`D_n` includes `actionlog.digest`, so it identifies the run **and how it arrived**, not merely the current
world state: two runs at the same `(level, entity, stream)` reached by **different** histories have
**different** `D_n`. Excluding the log would make `D_n` the pure current-state identity; D24 §2 lists the
history among the canonical state, so it is **included** (the ratified design choice).

## 3. No separate seed/depth field

The seed and depth are **not** separate components: `gamegen.level_digest` already commits to both (its canon
bytes open `URDRGEN1|s:<seed>|d:<depth>|…`), and the seed re-enters through the RNG root. A raw `seed` field
would be redundant, and is deliberately **absent**.

## 4. The authority / view boundary

A view-only quantity — a facing for animation, a camera, an interpolated position — cannot enter `entity`
(the record refuses any undeclared field; `entity.FIELDS == ("pos",)`), so it can never reach `entity_digest`
and therefore never reach `D_n`. `D_n` depends on the four component **identities** and on nothing else; a
quantity in none of them has no slot in the preimage.

## 5. Ownership stays crisp — none of the three laws absorbs another

| law | question it answers |
|---|---|
| `savegame` | *can I restore this artifact?* — stores the earned components **independently**, mints no assembled identity |
| `rerun` | *does this recovered history reproduce the independently stored state?* — a REPRODUCED/DIVERGED verdict |
| `statecanon` | *what is the canonical identity of this assembled state-and-history?* — a single digest |

`statecanon` exposes no serialize/restore/address (savegame's) and no replay/verdict/reconstruct_origin
(rerun's), imports neither module, and re-derives nothing they own.

## 6. It adds no authority beyond the composition

Read off the AST, the assembly (`d_n_preimage` + `d_n`) reaches **all four** component-identity authorities,
mints **exactly one** `sha256` (the composition), reaches **none** of the components' raw-serialization
functions (`canon_bytes`/`entity_bytes`/`stream_bytes`/`stream_of`), and advances no RNG. So a mutant that
reproduced the same `D_n` while **bypassing** one authority — inlining a component's own `sha256(preimage)`,
or hard-coding a digest — **reddens on the structure** even though its output matched. The gate establishes
that the implementation *composes the four earned identities*, not merely that it *emits the expected digest*.

## 7. Single-peer

This is the canonical identity of **one** run's assembled state. Cross-peer union canonicalization is
`lockstep.canon`'s `(tick, peer, seq)`, which game actions do not carry (**Slice A**), so this module imports
no `lockstep` and manufactures no such key.

## 8. Grade

**MEASURED**: over the corpus `D_n` equals SHA-256 of the labelled preimage built independently from the four
public component-identity functions; mutating **any** one of the four components changes `D_n`; two runs at
the same `(level, entity, stream)` with different histories have different `D_n`; `D_n` depends only on the
component identities, not on object instances. **ESTABLISHED**: a view-only field cannot enter `entity` and so
cannot reach `D_n`; the labelled fixed-width `|`-delimited framing is injective; the assembly composes the
four earned authorities and mints exactly one SHA and reaches no raw serialization (read off the AST); it
absorbs no neighbour (no savegame/rerun API, imports neither), and imports exactly its declared substrate and
no `lockstep`. **DECLARED**: the four components are the currently-earned canonical identities (world, entity,
RNG, history), the seed/depth ride inside `level_digest`, single-peer.

## does_not_show

Multi-entity rosters or health/inventory (unearned components — no slot yet); cross-peer order independence
(Slice A); whether a run is reachable or winnable (that is `move`/`descent`'s, not identity's); and anything
about observers, which stay KINEMA's.

## Falsifier

`statecanon-assembly` (`D_n` equals SHA-256 of the labelled preimage built independently from the four public
component identities; mutating any one component moves `D_n`; the history is in the identity; `D_n` depends
only on identity; and the assembly composes the four earned authorities and mints exactly one SHA — read off
the AST), with `statecanon:scenes` (the two scenes and the top digest reproduce, an unpinned name refuses
typed `STATECANON-REFUSE`) and `statecanon-boundary` (a view-only field cannot reach `D_n`, the labelled
framing is injective, and `statecanon` absorbs no neighbour — no savegame/rerun API and imports neither)
alongside; `tests/test_statecanon.py`.
