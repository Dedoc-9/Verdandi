<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- brief-falsifier: enact-dispatch -->
# `enact` — design brief (URDRENA1, D24 §2/§3: the typed action authority)

**Built**: 2026-09-19, one rung after `savegame`, on the boundary measured after `replay` was found blocked.
It is the **twelfth game-layer vertical slice** and the missing prerequisite between `actionlog` and
`replay`: the chain is now `actionlog → typed action authority → replay`.

## 0. What it is

A typed action vocabulary and a single dispatch to the transition authorities:

    encode(kind, payload=None) -> token bytes         # MOVE carries a direction; DESCEND/LOOT carry none
    decode(token) -> (kind, payload)                  # or ENACT-REFUSE on a malformed token
    dispatch((level, pos, stream), token) -> (state', info)   # binds to move.step/descend.descend/loot.loot

## 1. The kinds are exactly the state transitions

A canonical action takes a canonical state component and returns an updated one. A code sweep found exactly
three CORE modules that do that, and they are the whole vocabulary:

    MOVE     move.step(level, pos, command) -> (outcome, pos')     updates the entity position
    DESCEND  descend.descend(level, pos)    -> (level', pos')      updates the level and position (depth)
    LOOT     loot.loot(level, pos, stream)  -> (drop, stream')     updates the RNG stream

`combat` and `heirloom` are **deliberately outside** the vocabulary. Each is a certified arithmetic law that
takes **declared integer inputs** and returns a **derived number** (`resolve(attack, defense) -> damage`,
`heir(q) -> q'`), mutating nothing and holding no canonical component — both stdlib leaves that import no
`gamegen`/`entity`/`rngstream`, read off their own AST. They produce results a future health/inventory rung
will consume; they are not history actions. Including them would **manufacture** a state authority rather than
**discover** one — the single most important architectural result of the measurement.

## 2. The payload — three genuinely different shapes

    MOVE     payload = one direction in move.DIRECTIONS (N/S/E/W)   the only free choice
    DESCEND  payload = NONE                                          fully determined by the state
    LOOT     payload = NONE                                          the source is the state's (level, pos)

A single universal interpretation cannot substitute for these. A token is `KIND-tag byte | payload`:
`b"M"+dir`, `b"D"`, `b"L"`. The tokens **are** `actionlog` tokens (canonical bytes), so the vocabulary rides
on the history channel that already exists rather than minting a second one.

## 3. Dispatch binds, it does not reimplement

`dispatch` threads a bundle `(level, pos, stream)` — every field an already-earned canonical component,
nothing invented — decodes the kind, and calls the authority that owns it. Each
`*_dispatch_matches_the_authority` law proves the routed result **equals** calling
`move.step`/`descend.descend`/`loot.loot` directly, and `the_router_reimplements_nothing` reads the binding
off the AST (the router reaches the three authorities and mints no digest or state constructor of its own).

## 4. RNG semantics attach by kind, not by presence in the history

`rng_advances(LOOT) == 1` while `rng_advances(MOVE) == rng_advances(DESCEND) == 0`, measured by threading the
stream through a dispatch of each kind. A recorded action does **not** imply a draw; an interpretation that
made every action advance the stream reddens against `move` and `descend`, which advance nothing.

## 5. Ordering is `actionlog`'s append order

The only earned per-action sequence coordinate is `actionlog`'s append position (committed by `rngstream`'s
fold); `rngstream.Stream.n` counts only RNG-advancing actions, so it is not a universal index. Cross-peer
canonical ordering is a **different** authority — `lockstep.canon` (tools/netcode) sorts a delivered union by
`(peer, seq)` within a `tick` — but its ordering key is carried on netcode events and is **absent** from
every game action. So this rung binds `actionlog`'s append order and invents no key and no canonicalizer;
cross-peer reconciliation stays `replay`'s, and would need a later rung to earn `(tick, peer, seq)` before
`lockstep.canon` could apply here.

## 6. Ownership stays crisp

A malformed **token** (an unknown kind byte, a move token with a bad direction, a descend/loot token carrying
a payload, a non-bytes token) is this module's refusal, typed `ENACT-REFUSE`. A valid token dispatched
against a malformed **state** surfaces the **authority's** own code — `MOVE-REFUSE`, `DESCEND-REFUSE`,
`LOOT-REFUSE` — never `ENACT-REFUSE`.

## 7. The neutral ruler is `savegame`, independent of this module

`the_dispatch_reproduces_the_savegame_ruler` runs a single-floor token sequence through dispatch, stores the
resulting `(pos, stream)` and the tokens (as an `actionlog`) via `savegame` — which serialized them
**independently** of any dispatch — restores, decodes the restored tokens, re-dispatches from the origin, and
requires the reproduced level/entity/stream identities to **equal** what `savegame` stored. A **corrupted**
token diverges that reproduction, so the check is not vacuous. `savegame` is imported lazily so the declared
substrate stays the dispatch stack.

## 8. Single-peer, and it stops short on purpose

This rung defines the vocabulary and the dispatch. It does **not** capture actions into a live log (a wiring
rung), reconstruct a run from origin as an authoritative operation (`replay`, the next rung), reconcile a
cross-peer union (`lockstep.canon` needs coordinates game actions lack — **Slice A**), assemble the canonical
`D_n` (`statecanon`), or bind health/inventory to `combat`/`heirloom` (a persistence contract). A from-origin
replay across depth changes will also need an **origin anchor** that `savegame`'s end-state does not provide
(**Slice B**). Those are named DEFERs, not omissions.

## 9. Grade

**MEASURED**: a dispatched MOVE/DESCEND/LOOT equals its authority called directly; the stream advances only on
LOOT (0 for MOVE and DESCEND); a token round-trips through `encode`/`decode` and through an `actionlog` in
append order; the actionlog → decode → dispatch chain reproduces the state `savegame` stored independently,
while a corrupted token diverges it. **ESTABLISHED**: the kinds are exactly the three state transitions and
`combat`/`heirloom` are pure derivations excluded (read off their imports); the router binds and reimplements
no transition (read off the AST); a malformed token refuses typed `ENACT-REFUSE` while a bad state surfaces
the authority's code; the declared substrate is the dispatch stack + stdlib. **DECLARED**: the vocabulary is
exactly these three kinds with these payloads, single-peer, and live capture, from-origin replay, cross-peer
reconciliation, the assembled `D_n` and health/inventory binding are later rungs'.

## does_not_show

That a token stream is `replay`'s sole input (replay is unbuilt); cross-peer order independence
(`lockstep.canon`'s coordinates are unearned here); the assembled canonical state (`statecanon`'s); and
nothing about the transition math itself, which stands in `move`/`descend`/`loot` and imports no `enact`.

## Falsifier

`enact-dispatch` (a dispatched MOVE/DESCEND/LOOT equals its authority called directly, the stream advances
only on LOOT, a malformed token refuses `ENACT-REFUSE` while a bad state surfaces the authority's code, and
the router reimplements no transition), with `enact:scenes` (the two scenes and the top digest reproduce, an
unpinned name refuses) and `enact-neutral` (the actionlog → decode → dispatch chain reproduces the state
`savegame` stored independently, and a corrupted token diverges it) alongside; `tests/test_enact.py`.
