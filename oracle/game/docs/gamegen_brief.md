<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- brief-falsifier: gamegen-canon -->
# `gamegen` — design brief (URDRGEN1, the first game-layer vertical slice)

**Built**: 2026-09-15, one commit after D24 registered the boundary it is admitted under. The
contract in §1 was written before the module and the module was held to it; nothing in §1 was
amended to fit what got built.

## 0. What it is

**`seed + depth → canonical level → digest`, and nothing else.** One executable dungeon generator,
the smallest slice that can be forced through D24 §1 — *does this affect canonical game state, or
is it a view of it?* — and made to answer. It answers: **it affects canonical game state.** It is
CORE. It imports the standard library and nothing under `tools/`, it renders nothing, it needs no
window, no clock, no input device and no audio, and it runs on the verification host to the same
bytes it would produce anywhere else. If that last sentence holds, D24 §6's dependency boundary is
doing work on the first module it was written for.

This is not the FATE generator. It is the authority boundary and one generator behind it.

## 1. The contract

**Canonical input.** Exactly two integers.

| parameter | domain | outside the domain |
|---|---|---|
| `seed` | `0 <= seed < 2**64` (`SEED_BITS = 64`) | `GAMEGEN-REFUSE`, typed, never clamped |
| `depth` | `1 <= depth <= DEPTH_MAX` | `GAMEGEN-REFUSE`, typed, never clamped |

`bool` is not an int here, as in `heightfield`. There are no other generation parameters: the grid
size, the room bounds and the try budget are **constants of the canon**, not inputs, so a level's
identity is a function of `(seed, depth)` and of this module's declared arithmetic.

**Canonical output.** A `Level` — a fixed `48 x 32` grid of cells drawn from a four-letter alphabet
(`#` wall, `.` floor, `<` stairs up, `>` stairs down), plus the list of rooms as `(x, y, w, h)`
rectangles **in sorted order**. Rooms are part of the structure because the next structural law
will need to name one (D24 §3: a planted sealed room); they are sorted so that the order in which
the generator happened to place them can never enter identity.

**Identity.** The bytes of `canon_bytes(level)`:

    URDRGEN1|s:<seed>|d:<depth>|48x32|rooms:x,y,w,h;x,y,w,h;...|<row 0>|<row 1>|...|<row 31>

Rows are the raw cell bytes. Nothing else enters: no provenance, no timestamp, no host, no
interpreter, no placement order. Two levels with these bytes equal are the same level.

**Digest.** `level_digest(level) = SHA-256(canon_bytes(level))`, hex. The digest establishes
**identity and reproducibility only**. It is not the generator's correctness oracle — a wrong level
reproduces its digest exactly as faithfully as a right one — which is why §3 has its own
predicates with their own falsifiers.

**What must reproduce bit-for-bit.** `canon_bytes(generate(seed, depth))`, for every admitted
`(seed, depth)`, on every host, under every hash seed and interpreter version. Eight levels are
pinned raw in the corpus and re-derived every run; the deepest admissible level is one of them.

**What is deliberately not claimed.** That the level is worth playing. That the stairs down are
reachable from the stairs up — the corridors are carved between consecutive rooms, so by
construction they are, and construction is not a witness; the reachability witness and its planted
sealed room are their own law and are not asserted here. That the room-placement draw is unbiased —
it is `draw mod n`, declared as such, and the bias is part of the canon. That any second
implementation reproduces the corpus — the raw pins exist so that one can, and none has. Nothing
about monsters, loot, combat, companions, fishing, persistence, replay or rendering: every one of
those is a *consumer* of a canonical level, and none exists.

## 2. Depth is three claims, kept apart

D24 gives the bound: **2 147 483 647**, because that is what a signed 32-bit integer holds. The
bound must not quietly become "and therefore the generator works there". Three questions, three
falsifiers:

1. **Representation.** `DEPTH_MAX` is *computed* — `(1 << (32 - 1)) - 1` — and a falsifier asserts
   it equals the literal `2147483647`. A bound written as a literal is a bound that can drift from
   its own derivation.
2. **Admission.** `depth = 0` and `depth = DEPTH_MAX + 1` refuse typed. `depth = DEPTH_MAX` is
   admitted. The domain is closed at both ends by a test, not by a comment.
3. **Generation.** `generate(seed, DEPTH_MAX)` actually generates: it is in the corpus, its digest is
   pinned, it satisfies every structural predicate in §3, and it costs the same number of draws as
   depth 1, because depth enters only the preimage of each draw. A generator that merely *stores* a
   legal integer gets no credit here; the question FATE never asked — does the deepest level
   generate, or does something overflow first? — is answered for this generator by running it.

## 3. The algorithm, declared

Integer-only, stateless, host-independent, in `heightfield`'s idiom: there is no RNG object.

- **A draw** is `SHA-256(MAGIC | seed | depth | tag | i)`, first eight bytes, big-endian. `tag`
  names what the draw is for (`room`, `bend`), `i` numbers it. The draw depends on nothing that
  happened before it, so nothing about evaluation order can reach the output.
- **Rooms.** Up to `ROOM_TRIES = 64` attempts, each drawing a width in `4..10`, a height in `3..7`
  and a position strictly inside the border; an attempt is kept if it overlaps no kept room with a
  one-cell margin; placement stops at `ROOMS_MAX = 8`. Fewer than `ROOMS_MIN = 2` kept rooms is a
  typed refusal — the admission condition — and how often the sweep meets it is *measured*, not
  assumed (§4).
- **Corridors.** Each kept room is joined to the next kept room by an L-shaped corridor between
  their centres; one draw (`bend`) chooses horizontal-first or vertical-first. Corridors carve floor
  through wall and never through stairs, because stairs are placed last.
- **Stairs.** `<` at the centre of the first kept room, `>` at the centre of the last. Two kept
  rooms cannot share a centre, so the two stairs cannot coincide.
- **The border** is wall on all four sides, always.

## 4. Falsifiers — cheap, and each can go red

| claim | falsifier |
|---|---|
| same input, same bytes | the eight corpus digests reproduce every run; a mutated generator (one more try) moves every one |
| identity is a function of the input alone | three fresh interpreters under `PYTHONHASHSEED` 0, 1, 2 print one digest; shuffling the room list before serialisation is an **inert** plant (declared inert, reported as such); moving one room cell is an **observable** plant |
| different input, different bytes | all eight pinned digests are pairwise distinct; `(s, d)` and `(s, d+1)` differ; `(s, d)` and `(s+1, d)` differ |
| the domain is closed | seed `-1`, seed `2**64`, depth `0`, depth `DEPTH_MAX + 1`, a `bool`, a `float` — each refuses `GAMEGEN-REFUSE`; the four corners are admitted |
| the deepest level generates | `(7, DEPTH_MAX)` and `(2**64 - 1, DEPTH_MAX)` are corpus members with pinned digests and clean structure |
| structure, not digest | `problems(level)` over the corpus and a 128-level sweep is empty; a breached border, an overlapping room, a second stairs-up, a stairs on wall and a room hanging off the grid are each **planted** and each caught by name |
| the admission condition is real | a generation with one try keeps one room and refuses; the sweep's refusal count is reported |
| CORE, not VIEW | the module's imports, read from its own AST, are exactly `hashlib` and `os`; `LAYER == "CORE"`; the D24 §1 answer is bound as data |

The corpus is what the module *emits*, frozen in `conformance_gamegen.txt`, never regenerated by the
gate. Every plant substitutes input or a parameter; none edits the detector.

## 5. Admission under D24

D24 §8 said the first game-layer module either classifies cleanly under §1 or D24 is amended before
the module is graded. This module classified without amendment: it affects canonical game state, it
is CORE, and the row `gamegen-layer` checks the two things §6 rule 1 makes checkable — that it
imports nothing the gate does not already run on, and that its layer is declared as data rather than
inferred from prose. D24 §9 records the admission.

## 6. Grade

**MEASURED**: the eight pinned levels reproduce; the hash-seed sweep agrees across three fresh
interpreters; the structural predicates hold over the corpus and a 128-level sweep with the refusal
count reported; the refusals are total over the listed inputs; every plant behaves as declared, the
inert one included. **ESTABLISHED**: `DEPTH_MAX` is derived and equals its literal; the deepest
admissible level generates; the imports are exactly the declared substrate. **DECLARED**: the grid
size, the room bounds, the try budget, the draw's modular bias, and that rooms belong to the
structure — each a choice, each labelled.

## does_not_show

Its first clause first: **a level that reproduces is not a level worth playing**, and nothing here
says otherwise. That the stairs down are reachable from the stairs up (construction is not a
witness). That the placement draw is unbiased. That any other implementation reproduces the corpus.
That `48 x 32` is the right size, that eight rooms are the right count, that an L-shaped corridor is
the right corridor — each is a constant of this canon, changeable only by minting a new one. And
nothing about canonical *game state*: this is one level, not a run; D24 §2's shape — seed, world
identity, generated dungeon state, entities, RNG state, action history — is what a later rung
constructs, and this module supplies exactly one of its fields.

## Falsifier

`gamegen-canon` (the corpus reproduces raw, the digests are distinct, the deepest level generates,
the domain refuses at both ends), with `gamegen:scenes`, `gamegen-invariance`, `gamegen-structure`
and `gamegen-layer` alongside; `tests/test_gamegen.py`.
