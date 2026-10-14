<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# ORT-1: the origin moved between two ticks, as a transition bound to its basis

A rules-2 world ([`RULES-2.md`](RULES-2.md)) may have an **origin**, and ORT-1 moves it between two ticks. A rebase is
not a change of view: it is a transition from one complete world and state to another, prepared from one exact basis,
committed only if that basis is still the owner's, and recorded by a receipt. This document is the specification that
two implementations are written from, [`web/ort.js`](web/ort.js) and [`ort_ref.py`](ort_ref.py); where they disagree,
one of them is wrong. Both are held first to values worked by hand ([`web/ort_cases.json`](web/ort_cases.json)).

**Where it comes from.** The owner's documents of 2026-10-14 — the origin-rebase protocol, its ORT-0 draft and the
draft's corrected version, two reviews of them, and *ORT-0 → ORT-1* — and his word, *"batch/scrap and proceed"*. Kept:
a rebase is a state transition at a tick boundary, not a camera move; conservation of every global position, proved
by exact arithmetic, not assumed; a closed event and a canonical, self-delimiting, versioned byte form; the candidate
built without writing to the live world, every check made before anything changes, and a refusal changing nothing;
the commit bound to the exact basis it was prepared from (a stale or replayed transition refused); a receipt naming
the pre-state, the event and the post-state; every coordinate-dependent field declared, an undeclared one refusing;
three answers (values by hand, Python, JavaScript), compared as bytes; plants that must be refused with their own
code. Scrapped, and why: the int32 region and local coordinates (Verðandi's state is binary64 metres under rules 1 and
2; a second state model would be a second simulation); the region size of 2^20 units (here the shift is the map's own
cell, so that every cell, spawn and target keeps its place on the grid); the 90% trigger (when to rebase is the
caller's choice; what ORT-1 enforces is representability and exactness); a rebase of some objects and not others (the
whole frame moves, or relative positions would change); the phase variable standing for atomicity (here the owner is
single-threaded and the commit is one assignment of world and state between two ticks); a rebase as a rung-D
admission (introducing ORT-1 is a change to the program, which RUNG-0 classifies; a rebase at run time is a step of
the run); and every claim of being unbreakable.

## The coordinate model

- A rules-2 world has an origin `(oi, oj)`: whole numbers of cells, each at most 2^20 either way; `(0, 0)` unless the
  map says otherwise. Local cell `(i, j)` is the map's cell `(i + oi, j + oj)`.
- A local position `p` (metres, a double) is the global position `oi·cell + p` along x, and `oj·cell + p` along z.
  Heights are not rebased: `y` is absolute.
- The cell must be a whole number of metres from 1 to 64 (`ORT-CELL`): then `Δ·cell` is a whole number, exact.
- **Conservation.** A rebase by `(di, dj)` sets `oi' = oi + di`, and every moved number `p' = p − di·cell` (x) or
  `p − dj·cell` (z). Over the reals `oi'·cell + p' = oi·cell + p`. In binary64 this holds exactly when the subtraction is
  exact; ORT-1 computes each one's rounding error by TwoSum (`r = p − d`; `b = r − p`; `err = (p − (r − b)) + (−d − b)`,
  exact in IEEE 754 round to nearest) and refuses the rebase unless every error is 0 (`ORT-INEXACT`). A committed rebase
  therefore conserves every global position exactly. A shift toward 0 is exact as a rule; a shift that makes a number
  larger may not be (the hand-worked case O4).
- **What it does not conserve: the bits of the ticks after it.** The tick's arithmetic in another frame rounds
  differently (`translate_probe.py`, 0225: the same run moved by 128 m parts at tick 1). So a rebase is a step of the
  run, recorded, done the same way by both implementations; a run with a rebase is held to a run with the same rebase.

## The world with an origin

Rules 2's world, amended: `top(i, j)` reads the map's cell `(i + oi, j + oj)`; a spawn stands at local
`((sx − oi + 0.5)·cell, (sz − oj + 0.5)·cell)`, a target likewise; the objective (map cells) is met when
`floor(x / cell) + oi` and `floor(z / cell) + oj` are inside it. The identity document gains `"origin": [oi, oj]` (its
numbers written as every number is) when the origin is not `(0, 0)`; at `(0, 0)` every byte of rules 2 is what it was,
and every identity and hash published for rules 2 stands. Rules 0 and 1 have no origin: a world with one is refused
(`ORT-RULES`). A mover's box is local: a rebase moves it with everything else.

## The frame table

Every leaf of the state's snapshot is declared, moved along x, moved along z, or independent of the origin:

| leaf | |
|---|---|
| `x`, `targets[k].x` | moved by `−di·cell` |
| `z`, `targets[k].z` | moved by `−dj·cell` |
| `tick`, `side`, `feet`, `vy`, `yaw`, `pitch`, `onGround`, `cooldown`, `score`, `shots`, `onObjective`, `targets[k].id`, `.y`, `.up`, `.downFor`, `movers[k].phase`, `.stopped` | independent (a phase is a place along a mover's own path, which moves with it) |

The world: the origin moves by `(di, dj)`; each mover's box `x0`, `x1` by `−di·cell`, `z0`, `z1` by `−dj·cell`; the map
(cells, tops, spawns, targets' cells, the objective, probes, routes) is global and read through the origin; a mover's
axis, travel, speed and policy are independent. The view's feedback (`fx`) is not authoritative and is cleared.

The world's own fields are declared too: read through the origin (the cell, the grid, the tops, the map, the
spawns, the targets' cells, the objective, the probes and routes), the origin, the movers (local, moved), or made from
the rest (the identity and its hash's starting state); `ort.js` holds `Object.keys(world)` to its table, `ort_ref.py`
the world's `vars`.

**Closure.** A leaf of the snapshot or a field of the world that the tables do not name refuses the rebase
(`ORT-UNDECLARED`), so a field added to the state or the world cannot be left behind by a rebase without the rebase
refusing. What the table does not reach: state
outside the simulation. The graybox's and the plaza's renderers read the state every frame and keep nothing in world
space between frames; that is said, not checked. No run is persisted.

## The event

A record of exactly `tick`, `di` and `dj`: `tick` a whole number from 0, `di` and `dj` whole numbers of cells, each at
most 2^20 either way (a boolean is not a number) — `ORT-EVENT` otherwise. Its canonical bytes:
`VERDANDI-ORT-EVENT 1\ntick T\ndi DI\ndj DJ\n`, each number in decimal, `-` in front when negative, no leading zero.

## The canonical bytes of a basis

`VERDANDI-ORT 1\n`, `identity N\n`, the world's identity (RULES-2.md) as UTF-8, `\nstate M\n`, the state's snapshot,
`\n`; `N` and `M` the byte counts in decimal. Self-delimiting and versioned. The basis digest is the SHA-256 of these
bytes in lower-case hex. Implementations are compared on the bytes; the digest names a basis in a receipt.

## prepare(owner, event)

Reads the owner's world and state and writes nothing. In order, the first that fails refuses: the world is rules 2
(`ORT-RULES`); its cell is whole metres from 1 to 64 (`ORT-CELL`); the event's form (`ORT-EVENT`); its tick is the
state's (`ORT-STALE-TICK`); the new origin within 2^20 (`ORT-ORIGIN`); every leaf of the snapshot in the frame table
(`ORT-UNDECLARED`); every moved number of the state, in the snapshot's order of leaves, then every mover's box, moved
exactly (`ORT-INEXACT`); the world rules 2 build from the map with the new origin and the moved movers (`ORT-MOVER` when
a mover leaves rules 2's table). Then the candidate: a copy of the state with exactly the moved leaves changed, held to
that before anything is returned — every leaf of its snapshot the old one's but the moved ones, each the number
computed (`ORT-SELF`) — and the receipt:

    VERDANDI-ORT-RECEIPT 1
    seq K
    prev PREV
    tick T
    pre PRE
    event EV
    post POST

each line ending in a line feed: `K` the owner's committed transitions so far plus one, `PREV` the id (the SHA-256 of
the receipt's bytes) of the owner's last committed receipt, or 64 zeros, so that the receipts are a chain; `PRE` and
`POST` the basis digests before and of the candidate, `EV` the SHA-256 of the event's canonical bytes, all lower-case
hex.

## commit(owner, prepared)

In order: a transition whose receipt the owner has committed is a replay (`ORT-REPLAY`), recognised before anything
else and never applied twice; the owner's tick must be the prepared tick (`ORT-STALE-TICK`); the owner's basis digest
must be the prepared `pre`, and its last receipt the prepared `prev` (`ORT-STALE-BASIS`): the bytes and the history
are two checks, each catching what the other cannot — a world moved there and back has its old bytes and a longer
history (the ABA problem of a compare-and-swap; O11), and a live state written outside a tick and a commit has its old
history and other bytes (O13); the candidate and its receipt must be what was prepared, its digest the receipt's
`post` and the receipt's id and lines its own (`ORT-TAMPERED`; O12). Then the owner's published record — its world and
its state, one value — is replaced whole by the candidate's, in one assignment between two ticks, and the receipt is
appended. A refused commit changes nothing: not the world, the state, the receipts, the count or the last id. The owner
is single-threaded: no tick runs while it prepares or commits.

The transitions: *Ready* (the owner at a basis) → prepare → *Prepared* (a value the caller holds) → commit →
*Committed* (Ready again, at the new basis); a prepared transition never committed is dropped (*Aborted*), and a
refused one leaves the owner as it was. At most one rebase commits for a given basis, since committing changes it.
**Not built:** concurrency (the graybox's tick owner is one thread) and durability (no run is persisted: a crash loses
the run, rebased or not); both deferred until a runtime that has them asks.

## Three answers

1. **By hand** (`web/ort_cases.json`): for each rebase, the numbers it moves and where to (`set`, or `moved`: the shift
   every moved number must show, held exactly), the origin, each mover's box, or the code it is refused with; values at
   chosen ticks. The expected state after a rebase is built by the checker from the state before it and these numbers
   alone, never from either program's rebase.
2. **`ort_ref.py`** (Python, its own transform), whose every committed rebase is also held to conservation in exact
   fractions (`Fraction`).
3. **`web/ort.js`** in a browser (its own transform), whose every committed rebase is held to conservation with BigInt,
   counting each double in units of 2^-1074, exactly.

The two programs are then held to each other: the start's bytes, every tick's snapshot and hash, every rebase's
outcome, code, bytes and receipt, the end's bytes and the receipts. Plants, each refused by the case written for it:
in Python a rebase that rounds, a commit without the bytes' check, without the history's, without the replay check,
without the candidate's, a rebase that writes into the live state before it is checked, a transform that also moves
the feet (with and without the self-check), the frame table without a leaf and with a leaf wrongly independent, the
objective read without the origin, and the world given a field no table names; in the comparison, an engine's results
changed in one place (a snapshot, a refusal's code, a rebase's framing, a receipt, one bit of a moved number).

## Hardening: what an adversary was given, and what answers it (0227)

Reviewed against the build itself, by his word of 2026-10-14 (*"do an adversarial review for hardening and
implement"*); each finding is a case or a plant that fails without its answer.

| attack | answer | held by |
|---|---|---|
| a transition prepared at a basis, committed after the world went there and back (the same bytes, a longer history) | the receipt names the last receipt it follows (`prev`); commit compares the history as well as the bytes | O11; plant *bytes alone* |
| the live state written outside a tick and a commit, then a prepared transition committed | the bytes' check | O13; plant *no bytes' check* |
| a candidate changed after it was prepared | its digest and its receipt checked at commit (`ORT-TAMPERED`) | O12; plant *no candidate check* |
| a transform that moves a leaf it should not | the candidate's self-check (`ORT-SELF`), and the state built by hand | plants *moves the feet* |
| a field added to the world, in metres, that the rebase would leave behind | the world's fields declared; an undeclared one refuses | O14; plant *world field* |
| a refusal that writes something before refusing | every refusal held to the owner's bytes, objects, receipts, count and last id | every refused case; plant *writes first* |
| the TwoSum guard meeting overflow | TwoSum's error is exact for finite operands under round to nearest when nothing overflows; an overflow in its intermediate steps can make the error NaN (the 2Sum literature, below), which is not 0, so the guard refuses: a false refusal at worst, never a false admission; conservation is checked again without floating point (Fraction, BigInt) | O4, O5; the two exact checks |
| two programs that agree because they share a mistake | the values worked by hand, and the state after a rebase built from them alone | every case |
| a replayed transition | its receipt id recorded; replay refused before anything else | O9; plant *no replay check* |

Not answered, and said: concurrency and durability (above); state outside the simulation (above); and an adversary
who can write the owner's fields directly can do anything (the owner is a value in one thread, not a boundary of
trust). The 2Sum literature consulted: S. Boldo, S. Graillat and J.-M. Muller, *On the robustness of the 2Sum and
Fast2Sum algorithms* (HAL ensl-01310023, not opened: access refused to the fetch), and the UW PLSE note *2Sum
Algorithms* (2025), read, which states the exact error for finite inputs provided that no overflow occurs, and that an
intermediate subtraction can overflow and make the error NaN.
