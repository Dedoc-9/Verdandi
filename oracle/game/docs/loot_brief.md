<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- brief-falsifier: loot-consume -->
# `loot` — design brief (URDRLOO1, the first canonical consumer of the RNG stream)

**Built**: 2026-09-17, one rung after `descend`, on the boundary measured from `rngstream`, `move` and
`gamegen`. It is the **first real consumer** of the `URDRRNG1` stream — the rung that finally spends
randomness in a gameplay action, and the first concrete answer to the question `rngstream` deliberately
left open: *which real canonical actions advance the stream?* A loot event does.

## 0. What it is

From a canonical **source** `(level, pos)` and the current stream `R_n`, produce a deterministic **drop**
and the successor stream:

    S       = move.state_digest(level, pos)          # the source identity, in the ONE vocabulary
    i       = rngstream.peek(R_n, S, len(TABLE))     # a READ of R_n; peek does not advance
    drop    = TABLE[i]                               # a uniform selection from the frozen table
    R_{n+1} = rngstream.advance(R_n, b"loot:" + S)   # ONE advance CONSUMES the event
    → (drop, R_{n+1})

`peek` **determines what happens**; `advance` **records that the randomness was consumed**. That split is
the architecture.

## 1. The transition is `(source, R_n) → (drop, R_{n+1})`, not `seed → drop`

Because the stream is stateful, the **same source at a different stream position must give a different
drop** — the seed roots the stream (`R_0`) and enters only there; every drop reads whatever `R_n` the run
has reached. So the reproducibility object is the source *together with the stream state*, and a proposal
of the form `seed + level + source → drop` is too strong: it would silently bypass the stream. This is the
adversarial trap the measurement caught, made a test.

## 2. `loot` owns the advance

`loot` returns the successor stream, so the operation that *claims* to consume randomness is the one that
*actually* changes it. The alternative — `loot` returns a drop while a future `actionlog` performs the
advance — splits the claim from the effect and makes replay, omission and double-consumption bugs easy to
write. Here `actionlog` will *record* an already-produced transition, not perform it. A second sequential
loot therefore consumes `R_{n+1}`, never reuses `R_n`.

## 3. The source is `(level, pos)`, folded into the advance

No chest or monster object exists, and a room or tile has no standalone digest, so the smallest
canonically-identified source is a level-and-position, whose identity is `move.state_digest(level, pos)`
— which already encodes the level (seed, depth, layout) and the exact position, in one vocabulary, with no
new `source_id` invented. Folding `b"loot:" + S` into the advance makes two events at *different* sources
distinguishable at the transition layer, and namespaces the loot action kind from any other future action
that might also fold a state digest.

**Any canonical `(level, pos)` is a source — traversability is not required, on purpose.** Nothing
measured establishes that only traversable cells hold loot; gating on `descent.traversable` would invent a
gameplay rule this rung did not earn and conflate *source identity* with *gameplay eligibility*. A wall is
a well-defined canonical `(level, pos)`, so it is an eligible source for this primitive even if the game
later decides walls hold nothing. This module imports no `descent`.

## 4. What is earned: one uniform selection

A uniform single selection from a **frozen** table, and nothing more. No rarity, no weighting, no
quantity, no multiple draws — the primitive supports them, but the rung contract does not require them, so
they are absent until a later rung earns them (the way `entity` shipped position-only). The `TABLE` is a
**declared, frozen, canonical input** (like `gamegen`'s generation constants), non-degenerate so the
mutation falsifier bites; a change to it mints a new drop corpus. The drop's canonical representation is
`URDRLOO1|item:<id>` — the item **alone**; the source and stream produced it but belong to the
*transition*, not the identity of the *result*.

## 5. No inventory, no mutation, no second RNG

`entity` has earned only a position, so a drop cannot enter canonical inventory yet: `loot` **generates** a
drop the way `gamegen` generates a level, and its **only** canonical state change is the stream advance. It
mutates neither the level nor the position, and it uses no randomness but the one `URDRRNG1` stream — and
`rngstream` imports no `loot`, so the two authorities have **separable failure surfaces**: breaking the
loot table cannot touch the RNG law, and breaking the RNG advance breaks loot.

## 6. Grade

**MEASURED**: over a corpus of sources and stream states, the selection and successor stream reproduce; the
same source at a different `R_n` gives a different drop; a table mutation at the **selected** slot changes
the drop while a mutation elsewhere does not; the selected index equals an **independent** re-derivation
straight from the SHA construction, not via this module. **ESTABLISHED**: a second sequential loot consumes
`R_{n+1}`; `peek` does not advance; two distinct `(level, pos)` sources at one `R_n` do not collapse; the
level and position are unchanged and only the RNG advances; a replay from the same `R_0` reconstructs the
same drops and streams; malformed level, position or stream refuse typed `LOOT-REFUSE`. **DECLARED**: that
the table is uniform and frozen and a drop is a single item selection — rarity, weighting and quantity are
later rungs'.

## does_not_show

That a drop enters inventory (there is no inventory field yet); that only traversable cells hold loot (any
canonical `(level, pos)` is a source); that loot is weighted or yields more than one item; and nothing
about `rngstream`'s own law, which stands on its own frozen vectors and does not depend on this module.

## Falsifier

`loot-consume` (the transition is `(source, R_n) → (drop, R_{n+1})`: `peek` derives a uniform selection,
one `advance` folding the source consumes it, loot owns the advance; a second call consumes the successor;
distinct sources do not collapse; the selection matches an independent SHA oracle; a replay reconstructs
drops and streams; a wall is a valid source; `rngstream` imports no `loot`), with `loot:scenes` (the three
scenes and the top digest reproduce, an unpinned name refuses) and `loot-isolation` (only the RNG advances,
the drop is item-only, a table mutation changes only the selected slot, and the layer imports no `descent`)
alongside; `tests/test_loot.py`.
