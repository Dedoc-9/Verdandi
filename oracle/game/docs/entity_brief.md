<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- brief-falsifier: entity-identity -->
# `entity` — design brief (URDRETY1, the canonical entity in one identity vocabulary)

**Built**: 2026-09-16, one rung after `move`, on the interface `move` had already forced. It MOVES
nothing — it NAMES something: the entity becomes a content-addressed record so the whole game layer
speaks one identity vocabulary from the level through the entity to `statecanon`.

## 0. What it is

An entity is a **record** with a canonical digest. Today it carries exactly one field — a position —
because that is the only field any rung has earned. `move` (URDRMOV1) produced the first authoritative
`D_n → D_{n+1}` and, for want of an entity, inlined the entity's sole field into its state identity:
`URDRMOV1|lvl:<level_digest>|pos:x,y`. This rung makes the entity a first-class component in the same
content-addressed idiom the level already used, and `move`'s state now names it by digest:

    state_digest = SHA-256( URDRMOV1|lvl:<level_digest>|ent:<entity_digest> )

Nothing else: no health, no inventory, no facing, no second entity — those are later rungs' fields, and
the record refuses them until they are earned.

## 1. Why a component and not an inline field — the measured decision

The entity rung began as a measurement, not an implementation. `move` already had an identity, and
`statecanon` (rung 11) will assemble `D_n` from content-addressed components — "world identity, the way
`worldbind` names a chunk by its digest" (D24 §2). Two shapes were possible:

| shape | consequence |
|---|---|
| **wrap** — `move` keeps its inline `pos:x,y`, and a separate entity component carries a digest | TWO serializations of one entity: `move`'s `D_n` and `statecanon`'s would disagree on the entity's canonical form, and reconciling them means recomputing one from the other — exactly the translation the content-addressed rule exists to forbid |
| **become** — `move`'s identity *is* the entity-derived component | ONE serialization: `move` names the entity by `entity.entity_digest`, `statecanon` composes the same digest, nothing translates |

The second is the only one that keeps the invariant the whole ladder rests on: **one canonical identity
vocabulary through to `statecanon`.** So `move`'s identity *became* the entity-derived component — a
one-commit refactor of `move.state_bytes` from `|pos:x,y` to `|ent:<entity_digest>`, re-pinning only
`move`'s `moves` scene and top digest, no test of `move`'s authority touched. `entity-identity` is the
row that holds it: it reads `move`'s state bytes and checks they name the entity by its digest, carry no
inline `pos:`, and that the position `move` spawns is the position the record holds.

## 2. Only position is earned, and the record says so

D24 §2 lists position, health, inventory, equipment, progression and transformation for entity state.
Only **position** has been earned, by `move`. So `FIELDS == ("pos",)` and nothing more — the record is
**not** a catch-all schema for fields no rung has built. Each declared field owns exactly one serializer,
where its canonical form is decided once; a later rung that earns a field (health from `combat`,
inventory from `loot`, progression from `heirloom`) appends its key to `FIELDS` and its serializer beside
it, and `move`'s `D_n` reflects the new field through the same digest, unchanged in shape.

That the record is a bare position today is **DECLARED**, not hidden: it is a choice the next rung
widens, labelled as such, rather than a limitation dressed as completeness.

## 3. Forward-compatible, so growth costs no re-mint

`a_new_field_does_not_reformat_position` is the proof: simulate a later rung earning an `hp` field, in
copies of `FIELDS`/`_SERIALIZERS`, rebuild the bytes, and the `pos:x,y` segment is **byte-identical** to
what it is today — only a new `|hp:…` segment is appended. So a pinned entity digest does not move when
the vocabulary grows around it, and the tree does not pay a re-mint for every future field. Growth is
append-only in the serialization, which is what lets `move`'s already-pinned identity survive it.

## 4. View quantities are excluded by construction

`entity_bytes` walks `FIELDS` in declared order and serializes each; nothing outside `FIELDS` can enter,
and the constructor refuses an undeclared keyword typed (`ENTITY-REFUSE`). So a facing kept only for
animation, an interpolated sub-cell position, a highlight — D24 §2's "not canonical" list — **cannot
reach the digest**, because it is not a declared field, not because a comment asks it not to. That is the
same firewall `move` drew (a view-only quantity never reaches the state digest) made structural in the
record itself. Two entities with equal declared fields are the same entity; a difference in any field
moves it.

## 5. The record depends on nothing under `tools/`

The entity **record** — the constructor, `entity_bytes`, `entity_digest` — imports only the standard
library (`hashlib`, `os`); its module-scope imports are exactly `ALLOWED_IMPORTS`. Only the **scene
corpus**, which pins digests on the eight real `gamegen` spawns read through `descent`, reaches for those
modules, and it does so **lazily**, inside a function — so the record is not coupled to any game module
at load, and the dependency runs one way: `move` imports `entity`; `entity` imports neither `move` nor,
at module scope, `gamegen` or `descent`. `entity-laws` reads this off the AST: module-scope imports are
stdlib, the game modules appear only in the full walk.

## 6. Grade

**MEASURED**: the digest of a position-only entity reproduces across a hash-seed sweep of fresh
interpreters; equal declared fields give equal digests and any position change moves it; `move`'s state
names this component and the position `move` carries equals the one the record holds; a MOVED step moves
the entity digest while a BLOCKED step is a fixed point in it. **ESTABLISHED**: the constructor refuses a
malformed or undeclared field typed; the fields are walked in declared order; appending a field to a copy
of the vocabulary extends the bytes without reformatting the position; the layer boundary holds (the
record's substrate is stdlib, read from the AST). **DECLARED**: that the entity is, today, a bare
position — `FIELDS = ("pos",)` — and that later fields are earned by later rungs and appended here.

## does_not_show

That an entity has health, inventory, equipment, progression or any field beyond position — none is
earned yet, and the record refuses to pretend otherwise. That an entity is placed **legally** on a level
(whether its position is on a traversable cell is `move`'s claim, via `descent`; the record holds fields,
not legality). That two entities interact (`combat`'s rung). And nothing about **which** entities a run
contains — a roster is `statecanon`'s to assemble; this is the record one entity canonicalizes to.

## Falsifier

`entity-identity` (`move` names the entity by its `entity_digest`, no inline `pos:`, the spawn is the
record's position, and the entity digest tracks a MOVED step while a BLOCKED step leaves it fixed), with
`entity:scenes` (the two scenes and the top digest reproduce; an unpinned name refuses) and `entity-laws`
(only position declared; an undeclared or malformed field refuses typed; the declared-order walk; the
forward-compatibility proof; and the stdlib-only record substrate read from the AST) alongside;
`tests/test_entity.py`.
