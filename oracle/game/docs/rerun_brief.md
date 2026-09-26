<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- brief-falsifier: rerun-reproduce -->
# `rerun` — design brief (URDRRRN1, D24 §3: from-origin replay certification)

**Built**: 2026-09-19, one rung after `enact`, on the boundary the replay measurement pass established. It is
the **thirteenth game-layer vertical slice** and D24 §3's **replay** rung. It is a **certification layer**,
not a new simulation authority.

## 0. What it is

    reconstruct_origin(seed, depth, log) -> (level0, pos0, stream0)   # or RERUN-REFUSE on underflow
    replay(record) -> (verdict, (level, pos, stream))                 # verdict REPRODUCED | DIVERGED

From a saved run it reconstructs the run's origin, folds the recovered history through `enact`, and certifies
the fold reproduces the state `savegame` stored **independently**. The new law is exactly that agreement.

## 1. The origin reconstructs from earned state (Slice B, closed)

A run's origin is `(level0, pos0, stream0)`, and every part derives from what a savegame already holds:

    seed     stored directly
    depth0   = savegame.depth − (DESCEND count in the actionlog)   # depth moves ONLY via descend, +1
    level0   = gamegen.generate(seed, depth0)
    pos0     = move.spawn(level0)                                   # the authoritative starting position
    stream0  = rngstream.root(seed)

`savegame.depth` is the **current** depth, not the origin — that was the whole of Slice B — and it recovers
by subtracting the history's DESCEND count, because depth is a pure function of that count (MOVE and LOOT
keep depth; DESCEND is the only mover, `+1`; no ascent). **No origin field is added to `savegame`, and no
hidden origin record is minted.**

## 2. Reconstructed, then verified — never trusted

Because `depth0` is derived from the stored depth, the fold's final depth equals the stored depth **by
construction** — so depth equality is **tautological** and is *not* the ruler. The discriminating comparison
is the canonical **mutable** state — the entity **position** and the RNG **stream** — against the
independently stored `(pos, stream)`. Even the "runs originate at spawn" convention is confirmed per record:
a run that began elsewhere would not fold from spawn to the stored state.

## 3. The verdict

    REPRODUCED   the fold's (pos, stream) equal the stored (pos, stream)
    DIVERGED     they do not — an envelope-valid record whose history does not reproduce its stored state

`DIVERGED` is a **return**, not a refusal (the `move` MOVED/BLOCKED pattern). `savegame` stores the log and
the state **independently** (its own `persist_is_not_replay`), so a log inconsistent with the stored state is
a valid savegame — and catching it is exactly the binding this rung performs and `savegame` declines to.

## 4. Ownership

Replay owns the record+log pairing arithmetic and the verdict. Every other fault surfaces its owning
authority: a malformed record is `savegame`'s `SAVEGAME-REFUSE`; a malformed token is `enact`'s
`ENACT-REFUSE`; a DESCEND that cannot dispatch mid-fold (not on the down-stairs) is `descend`'s
`DESCEND-REFUSE`, through `enact`. The one refusal replay **owns** is **origin underflow** — a log whose
DESCEND count exceeds the stored depth, so no origin depth ≥ 1 exists — typed `RERUN-REFUSE`.

## 5. It adds no authority

The fold **is** `enact.apply` (checked on the AST), so replay re-derives no transition and advances no RNG
of its own — the stream moves only through `loot` via `enact`, so a replayed run's `stream.n` equals its LOOT
count. Replay mints no action vocabulary and no identity mechanism.

## 6. Single-peer

This is the from-origin fold of **one** recovered history. Cross-peer union reconciliation is a different
authority: `lockstep.canon` (tools/netcode) canonicalizes a delivered union by `(tick, peer, seq)`, and game
actions carry none of those coordinates (**Slice A**), so replay imports no `lockstep` and manufactures no
such key.

## 7. Grade

**MEASURED**: over the corpus the origin reconstructs from earned state and the fold reproduces the
independently stored savegame bit-for-bit (multi-floor and deep single-floor, so arbitrary start depth is not
tied to depth 1); corrupt, reorder and delete **diverge**; an envelope-valid record whose log does not fold
to its stored state **diverges**; the empty log replays to the origin snapshot. **ESTABLISHED**: origin
underflow refuses `RERUN-REFUSE`; a bogus DESCEND surfaces `DESCEND-REFUSE`, a malformed token
`ENACT-REFUSE`, a malformed record `SAVEGAME-REFUSE`; the fold is `enact.apply` and replay mints no
transition or RNG authority (read off the AST); the discriminator is `(pos, stream)` while depth equality is
structural. **DECLARED**: a run originates at `move.spawn`; the verdict is REPRODUCED/DIVERGED; single-peer.

## does_not_show

That a savegame+log pair is the run a player **actually** played — only that the pair is **internally
consistent** (the log folds the reconstructed origin to the stored state); cross-peer order independence
(Slice A, unearned); the assembled canonical `D_n` (statecanon's); and anything about observers, which stay
KINEMA's.

## Falsifier

`rerun-reproduce` (a saved run's origin reconstructs from earned state and the fold reproduces the
independently stored savegame bit-for-bit — multi-floor and deep single-floor — and the empty log replays to
the origin snapshot), with `rerun:scenes` (the two scenes and the top digest reproduce, an unpinned name
refuses) and `rerun-bind` (the certification binding: corrupt/reorder/delete and an envelope-valid
inconsistent pair all DIVERGE against the independently stored state, the discriminator being `(pos, stream)`
with depth tautological; underflow refuses `RERUN-REFUSE` and a bogus descend / malformed token / malformed
record surface their owning authority's code; the fold adds no authority) alongside; `tests/test_rerun.py`.
