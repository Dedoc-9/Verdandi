<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- brief-falsifier: rngstream-advance -->
# `rngstream` — design brief (URDRRNG1, the canonical RNG stream)

**Built**: 2026-09-17, one rung after `entity`, on the boundary measured from `move`, `entity` and
`gamegen` before a line was written. It is the game layer's **first stateful canonical component** —
the first whose state *advances*.

## 0. What it is

Canonical randomness that is *consumed*. `gamegen` draws statelessly — a draw is
`SHA-256(MAGIC|seed|depth|tag|i)`, order-independent, "there is no RNG object" — which is right for
generation and wrong for a run's randomness, because a run needs a stream whose *advancing is itself a
change to canonical state*. D24 §2 lists exactly that field: **"RNG state: the deterministic stream,
advanced only by canonical actions."** This module is it, and its identity participates in the
canonical state digest — the reason a stateless draw could not have carried this field.

## 1. Stateful, where `gamegen` is stateless — and that is the point

`gamegen`'s draw depends only on its own preimage, so generation reproduces anywhere in any order. The
stream is the opposite by design:

    R_{n+1} = SHA-256( "rngstream/v1" | "adv" | R_n | action )

so `R_n` **commits to the ordered action history** (D24 §2's "authoritative action history — the
ordered inputs replay consumes"). That commitment is the whole value: the same seed and the same
actions reproduce the same stream, and a *different* action sequence diverges — replay depends on
*which* actions, not only how many. This is the design the deterministic-netcode literature converges
on for replayable randomness, and it is why the RNG is a separate field from `gamegen`'s draws rather
than a reuse of them.

## 2. One stream, rooted at the run's seed — not a second seed

§2 says "the deterministic stream" (singular) and lists `seed` as "the run's generative root", so the
stream roots at the **same** `seed` `gamegen` uses, through a **domain-separated** root so it can never
be mistaken for a `gamegen` derivation of that seed:

    R_0 = SHA-256( "rngstream/v1" | "s:" | seed )

The domain tag is part of the **law**, not an incident of the implementation: drop it and `R_0`
collapses toward a rootless hash of the seed (a falsifier proves the tag is load-bearing).
`SEED_MAX`/`SEED_BITS` mirror `gamegen`'s and a law pins them equal by import, so "same seed" is
single-sourced rather than a copied constant.

## 3. The state carries an explicit index — `(n, R_n)`, not merely `R_n`

Two runs that happen to hold the same stream value after different numbers of actions must not be able
to masquerade as the same canonical state, so the sequence coordinate is bound into the identity:

    I_n = SHA-256( URDRRNG1|n:<n>|r:<R_n as hex> )

A falsifier fabricates the same `R` at a different `n` and requires a different `I`.

## 4. Advance is an action; a read never advances — by construction

`Stream` is immutable: `advance` returns a **new** `Stream`, and every read (`stream_bytes`,
`stream_digest`, `peek`) takes a `Stream` and returns a **value**. So a read cannot advance the stream,
because it has no handle that could — D24 §2's "advanced only by canonical actions" made *structural*,
the same firewall `entity` used to keep view fields out of the digest. The preimages are tag-separated
(`adv` for the chain, `draw` for `peek`), so a consumer's draw label can never collide with the
advance that threads the stream.

The synthetic action is **verification-only** (tokens `v0`…`v3`): it exists solely to make the advance
law non-vacuously testable now. This module declares **no gameplay action vocabulary** of its own —
that is `move`'s `DIRECTIONS`, and `loot`'s / `combat`'s draws to come.

## 5. `move` is not contaminated

`move` consumes no randomness today, and this rung does not change that: `move` neither imports this
module (read from its AST, not promised) nor carries a stream, so a move action **cannot** advance the
stream. A boundary law measures it — a reference assembly `(level, entity, stream)` stepped by `move`
leaves the stream a fixed point while the entity moves — as a **compatibility invariant for the current
`move` contract**, not a universal claim that movement can never consume randomness. A later rung that
changes that revises the boundary explicitly rather than moving `move` underneath this one.

## 6. Grade

**MEASURED**: over a corpus of seeds and a fixed synthetic action sequence, the root, the advance
chain, every prefix state and the top digest reproduce byte-identical across a hash-seed sweep of fresh
interpreters; identical `(seed, actions)` reproduce the whole trace; a different action sequence
diverges; a reference `move` assembly leaves the stream fixed while the entity moves. **ESTABLISHED**:
malformed seeds, actions, bounds and streams refuse typed; a read leaves `(n, R_n)` unchanged;
incremental and batch advancement agree at every prefix; the same `R` at different `n` has a different
identity; the root is domain-separated from a `gamegen` derivation of the same seed. **DECLARED**: that
the URDRRNG1 serialization is v1 and is **FROZEN** — the golden vectors are its representation lock, and
a format change mints v2 rather than editing v1.

## does_not_show

**Which** real canonical actions advance the stream — the synthetic action is verification-only,
`move` advances nothing, and `loot` (rung 5) is the first real consumer. Independent **sub-stream
domains** for decoupling subsystem draw order (a counter-based `derive(R_n, domain)` so `loot` and
`combat` draw without a global draw-order dependency) — earned by those rungs, not built here. The
**statistical quality** of the draws beyond determinism — SHA-256 is chosen for portability and
reproducibility, not for a distribution claim. And the assembly of the full `D_n` snapshot, which is
`statecanon`'s.

## Falsifier

`rngstream-advance` (the stream law: domain-separated root single-sourced with `gamegen` and provably
not its derivation; advance moves `(n, R_n)` and commits to the action; a read never advances;
incremental == every prefix; the index is bound; refusal is total), with `rngstream:scenes` (the three
scenes and the top digest reproduce, an unpinned name refuses) and `rngstream-isolation` (a reference
`move` assembly leaves the stream a fixed point while the entity moves, `move` decoupled by AST)
alongside; `tests/test_rngstream.py`.
