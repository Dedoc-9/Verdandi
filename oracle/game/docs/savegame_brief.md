<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- brief-falsifier: savegame-roundtrip -->
# `savegame` — design brief (URDRSAV1, D24 §3 persistence: persist stores state)

**Built**: 2026-09-18, one rung after `actionlog`, on the boundary measured against the existing
`persist.py`. It is the **eleventh game-layer vertical slice** and D24 §3's **persistence** rung (chain role
"persist"). It gets its own module name and glyph because the collision is real, not superficial.

## 0. What it is

A durable, content-addressed serialization of the earned canonical components:

    serialize(seed, depth, pos, stream, log) -> record bytes
    restore(record) -> (seed, depth, level, entity, stream, log)   # usable typed objects, or SAVEGAME-REFUSE

## 1. Why not `persist.py`

`persist.py` is **URDRLAT5**, the MMO Stage-H rollback-window checkpoint: its `checkpoint`/`restore` call
`storecost.serialize`/`deserialize`, its one generic piece (`_verified`) is private, and it imports
`storecost` + `horizon`. Its public contract is bound to the N-actor glide model, so it is **not reusable as
a game-state API**, and importing it would drag in the whole MMO arc. What **is** reused is the tree's
**universal content-addressing vocabulary** — `SHA-256(MAGIC | content) = identity`, a trailing-digest
verify, reconstruct-or-refuse — a discipline ~25 modules share (attest, sealwrit, testament, lease,
perception, …), not `persist.py`'s property. This module imports no `persist.py`.

The name collision forced a distinct module (`persist.py` and the whole `URDRLAT*` family are occupied): the
tree-wide scan confirmed `savegame.py` / `URDRSAV1` genuinely free. The rung's conceptual name stays "persist"
(§3); its concrete artifact is the savegame.

## 2. Persist stores state; replay derives it

The advertised "serialize/restore/re-bind bit-identically" must not become "replay the actions". `actionlog`
records **opaque tokens**, including actions with different RNG-consumption behaviour (a `move` command does
not advance the stream at all), so folding the log does **not** reproduce the run's RNG state in general.
Therefore every canonical component is serialized **independently** and reconstructed **directly** — never by
replaying the log. Re-deriving state from the action history is `replay`'s rung (10), across this boundary.
The prototype and gate make it concrete: a log that folds to a *different* stream still restores the **stored**
stream.

## 3. The snapshot (each component independently recoverable)

    seed              the generative root
    depth             with seed, REGENERATES the level via gamegen.generate (no cells stored)
    pos               RECONSTRUCTS the entity via entity.at(pos)
    (n, R_n)          RECONSTRUCTS via rngstream.Stream(n, R_n) — stored DIRECTLY
    actionlog entries RECONSTRUCTS via actionlog.from_actions

This is **not** the assembled canonical `D_n`. The record is a durable serialization of currently-earned
components; assembling seed + world + entity + RNG + history into one canonical-state identity is
`statecanon`'s rung (11), later. This rung earns no assembled digest.

## 4. The record (length-framed — no ambiguous concatenation)

    record = MAGIC(8) | seed(8) | depth(8) | pos_x(8, signed) | pos_y(8, signed) | n(8) | R_n(32)
           | log_count(4) | (len(4) | token)*log_count
           | level_digest(32) | entity_digest(32) | stream_digest(32) | actionlog_digest(32)   # check-block
           | SHA-256(preceding)(32)

The components' native encodings are variable-length and delimiter-based (`|pos:x,y`, `|n:…|r:…`, opaque
tokens), so composition without ambiguity requires explicit **length framing**. A token that mimics a
component encoding round-trips exactly, because framing is by length, never delimiter.

## 5. Two-layer integrity

`restore` verifies the trailing digest first (`SHA-256(buf[:-32]) == buf[-32:]`), so **every single-byte
flip and every truncation refuses** typed `SAVEGAME-REFUSE` before anything is reconstructed. Then it
**reconstructs usable typed state** and requires each reconstructed component's digest to equal the
check-block, so a validly **re-sealed** record whose seed/pos/stream/token was altered to a different
component **still refuses** per-component. Restoration produces objects, never mere digest equality.

## 6. A pure bytes law

Serialize and restore are deterministic functions of bytes; there is **no filesystem** here. Actual disk I/O
(digest-named files) is a **declared application discipline**, not part of the certification law — exactly as
`persist.py` treats its store medium — because nondeterministic I/O has no place in a byte-identical gate.

## 7. Grade

**MEASURED**: the record round-trips bit-for-bit; restore yields usable typed state whose component digests
match; the level is regenerated (the record carries no cells and its size is independent of level dimensions);
length framing round-trips even a token that mimics a component encoding. **ESTABLISHED**: persist is not
replay (the stream is restored directly, and a log that folds to a different stream still restores the stored
stream); every byte flip and truncation refuses; a re-sealed wrong-component refuses per-component; malformed
inputs refuse typed `SAVEGAME-REFUSE`; the module imports no `persist.py`/`storecost`/`horizon` and mints no
new identity mechanism. **DECLARED**: that the snapshot is the earned components (seed, depth, pos, (n,R_n),
actionlog) and **not** the assembled canonical `D_n`, and that disk I/O, `statecanon`'s assembled identity,
replay-based reconstruction, multi-entity rosters and manifests/windows are later rungs'.

## does_not_show

The assembled canonical-state identity (statecanon's); that a restored run is reachable or winnable;
wall-clock or crash-atomicity of any real write; and nothing about the MMO rollback window, whose `persist.py`
this module does not touch.

## Falsifier

`savegame-roundtrip` (persist stores state, restore re-binds it, and persist is not replay: the record
round-trips bit-for-bit, restore yields usable typed objects each verified against its own identity authority,
the level regenerates from `(seed, depth)`, length framing is unambiguous, and the stream is restored directly
— a log that folds to a different stream still restores the stored stream), with `savegame:scenes` (the two
scenes and the top digest reproduce, an unpinned name refuses) and `savegame-isolation` (two-layer integrity —
every flip/truncation and a re-sealed wrong-component refuse typed; imports no `persist.py`/`storecost`/
`horizon`, mints one identity, is not the assembled `D_n`) alongside; `tests/test_savegame.py`.
