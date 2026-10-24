# LOCALITY-0 — the measurement, fixed before it runs

> **Frozen 2026-10-24, before any perturbed brief was exported.** Nothing here is a result. This file is to ship
> byte for byte as `art/fixtures/locality/SPEC.md`; `art/locality.py` holds its sha256 and prints it in every report.
> Every line number below is `art/dress.py` at `de91aaf` unless another file is named.

What the measurement can and cannot establish, in his words: *"LOCALITY-0 can establish whether the current exporter
exhibits identity churn and unexpected influence; it cannot, by itself, prove that a particular replacement identity
architecture is necessary or sufficient."*

## 1. The fixtures

Byte copies of the files at `de91aaf`, kept in `art/fixtures/locality/`. The exporter reads the map from this folder
(`dress.export(A, maps_dir)`), never from `graybox/maps/`, and the briefs never from `art/briefs/`, which change with
his admissions.

| fixture | sha256 | copied from |
|---|---|---|
| `briefs/foundry-yard.art` | `4735ea905d006269f0eaeb4c117ef58ebdefa588db8effb33c12948cb2f33f88` | `art/briefs/foundry-yard.art` |
| `briefs/harbor-day.art` | `d50985f0496ad3f548ddd615700e6624f52569b018de6e91841feff2ed02c9a3` | `art/briefs/harbor-day.art` |
| `briefs/harbor-lift.art` | `0e3b033530470310d89e96a138c4f4333f428e90bfc0e87f7a02d1e1c3502921` | `art/briefs/harbor-lift.art` |
| `briefs/plaza-night.art` | `0ece61b53654a0192d72ee642342bfa6dd92e94526a406c0d54eb9545155ad2a` | `art/briefs/plaza-night.art` |
| `maps/tactical.gbx` | `18143644a2bfde0fdad5022a91b0e851b5a029576c533e7131f824e6d9777af3` | `graybox/maps/tactical.gbx` |
| `maps/tactical.layout` | `9680c4c87d82c2ef919cda66cd3cfae9645653beda3809f24a3073a63b7c3525` | `graybox/maps/tactical.layout` |

`FIXTURES.sha256` (those six lines): `cf61fcd30e2013c87b0015e1d557cce63323bf0edeaea291ab95154115863214`.

## 2. The inventory

`INVENTORY.jsonl`: 2,418 entries, sha256 `455af6c829f85f76b491a8bd1774b7f22b24eb306d65621e19353e7c3aadd45d`. It is made
from the fixtures' text alone: the briefs are parsed with `dress.parse`, nothing is exported. `art/locality.py` makes it
again from the fixtures and refuses to run unless the bytes are equal (`LOCALITY-INVENTORY`).

**A statement** is a line that keeps a word once its comment (from `#`) is removed, the first line (the format line)
excepted. **Excluded:** `map`, which selects the world (W and C); LOCALITY-0 measures the dressing of one world.

**The edit classes.** Each entry makes one brief from a fixture by changing one line:

- **NOOP** — one per brief. Every statement line is rewritten with its words joined by two spaces and
  `  # locality-0 no-op` appended. The parser reads every statement's words as before, so the scene must be the same.
- **DEL** — the statement's line is replaced by an empty line, so every other line keeps its number.
- **NUM+ / NUM−** — one number is moved up or down by one unit of the last decimal place it is written to, and written
  to that place: `2.9` → `3.0` / `2.8`, `0.022` → `0.023` / `0.021`, `0` → `1` / `-1`. A number is a word of the number
  grammar (`dress.NUMBER`), or one part of a word of comma-joined numbers (a cell, a colour, a mover's corner); each
  part is moved alone. There are no NUM edits for `title`, `seed`, `asset` or `time`, whose values are words.
- **SHIFT+x, SHIFT−x, SHIFT+z, SHIFT−z** — in a statement with two or more cell words (a region's corners, a canopy's
  or a building's), every cell word is moved together by one cell. A mover's two corners are moved together by one
  metre along x or z. A statement with one cell (a view) is moved by its NUM entries, which would be these.
- **MAT** — a word in a material's position is replaced by the next declared material in sorted name order, wrapping
  round. The positions are the 1st word of `skyline`; the 2nd word of `tower`, `canopy`, `neon`, `puddle`, `building`,
  `mover` and `surface`; a building's `face` material; and the 3rd word of `bay`.
- **SEED** — the brief's `seed` line is replaced by `seed locality-k`, for k = 1 to 7 (the seed sweep, §8).

**A number's role** comes from its statement's grammar. The table is `ROLE` and `OPTIONS` in the generator.

| role | numbers it covers |
|---|---|
| POSITION | cells and corners |
| SIZE | heights, depth, storey, travel |
| LATTICE | spacing, `every`, percentage, `ribs`, `bay` |
| APPEARANCE | colours, candelas, lux, sun angles, fog, exposure, bloom, rain, material values |
| VIEW | a view's yaw and pitch |
| MOTION | a mover's speed |

A number the table does not cover stops the generator.

**What an entry can end in.** An entry the exporter refuses is **REFUSED**, and its message is recorded. Refused
entries are not retried or replaced, and none is filtered out beforehand.

**Counts per brief:**

| brief | NOOP | DEL | NUM+ | NUM− | SHIFT+x | SHIFT−x | SHIFT+z | SHIFT−z | MAT | SEED |
|---|---|---|---|---|---|---|---|---|---|---|
| foundry-yard | 1 | 70 | 249 | 249 | 17 | 17 | 17 | 17 | 33 | 7 |
| harbor-day | 1 | 64 | 208 | 208 | 12 | 12 | 12 | 12 | 23 | 7 |
| harbor-lift | 1 | 68 | 233 | 233 | 14 | 14 | 14 | 14 | 25 | 7 |
| plaza-night | 1 | 64 | 208 | 208 | 12 | 12 | 12 | 12 | 23 | 7 |

NUM entries by role: APPEARANCE 870, POSITION 548, SIZE 152, LATTICE 122, VIEW 100, MOTION 4. No two entries make the
same brief, and none makes a fixture itself.

## 3. What is compared

For each entry there are two scenes:

- **A** — exported from the fixture: the baseline.
- **B** — exported from the entry's brief.

Both are made by `dress.export(dress.parse(text, NAME + ".art") + {name: NAME, sha256}, maps_dir)`, from the exact bytes,
with no file written. The lineage is not compared: it names the brief's bytes and lines, which every edit changes.

**Outcomes:**

- **ACCEPTED** — B was exported.
- **REFUSED** — `dress.ArtError` was raised by `parse` or `export`.
- **CRASHED** — any other exception raised inside `dress.parse` or `dress.export`. This is a finding about the
  exporter, and it is listed. An exception anywhere else ends the run.

**The records** are the units `scene_diff.diff(A, B)` keys (`art/scene_diff.py`, read and not changed):

- each record of `visuals`, `lights`, `collision` and `movers`, by its `id`;
- each entry of `assets`, `environment`, `materials`, `regions`, `spawns`, `targets` and `views`, by its name;
- each cell of `reach` and `tops`, by its index;
- each other top-level field: `format`, `name`, `title`, `map`, `units`, `grid`, `player` and `rules`.

A record has **changed** when it is added, removed, or its canonical bytes (`scene_diff.enc`) differ. The diff's
`objects` section is a view of `visuals` and `lights`, and is not counted again.

## 4. Identity

A record is matched only to the record of the same section and the same id (or name, or index). It is never matched by
content or likeness — HELD-0's rule. An **object** is a root in `studio_refs`' sense: a visual's id, with each `:part`
tail removed while the shorter id exists in the scene. `scene_diff.object_records` gives the roots for each scene.

## 5. The classification

**Notation:**

- s is the edited statement.
- h0 and h1 are its hash before and after the edit, in the exporter's sense: the first 12 hex digits of the sha256 of
  its words joined by single spaces. After a DEL there is no h1.
- by(r) is a record r's `by` field, on whichever side of the edit it has one.

Each changed record gets exactly one class: the first of these rules that holds.

1. **OWN**
   - (a) r is in `visuals`, `lights` or `movers`, and by(r) ∈ {h0, h1}; or
   - (b) r is the entry s itself declares:

     | s | the entry it declares |
     |---|---|
     | `material N` | `materials/N` |
     | `region N` | `regions/N` |
     | `view N` | `views/N` |
     | `asset N` | `assets/N` |
     | `time`, `fog`, `exposure`, `bloom`, `rain` | `environment/` that word |
     | `sun` or `moon` | `environment/light` |
     | `title` | the top field `title` |
     | `surface K` | every `collision` record of kind K |

   A changed record whose only changed field is `by` is OWN, and it is flagged **BY-ONLY**.
2. **IN-SCOPE** — r has a footprint, s has a scope, and they share a cell.
   - **Footprint** (cells, both sides of the edit together):
     - `visuals` and `collision`: the cells a box covers with area in plan (`dress.footprint`);
     - `lights`: the cell that holds `pos` (⌊x / cell⌋, ⌊z / cell⌋);
     - `movers`: the swept box's cells;
     - a spawn, a target or a view: its cell;
     - `reach` and `tops`: the cell of the index.

     Other records have no footprint.
   - **Scope** (cells, before and after together):
     - a statement that names a region (`tower`, `canopy`, `neon`, `lamp`, `puddle`, `building`): the region's
       rectangle as the scene's `regions` section states it, plus a canopy's or a building's own corners;
     - `skyline`: every cell, since it dresses the whole city;
     - `mover`: its swept footprint;
     - `region`: its rectangle;
     - `view`: its cell;
     - `bay`: its building's corners.

     Every other statement has no scope.
3. **DECLARED-GLOBAL** — r is reached through one of the three channels below. Each was read from the exporter's
   code before the run, and is reported by name.
   - **G-REACH** — s is a `mover`, and r is either a `reach` cell or a `lamp:` visual or light whose cell's reach
     differs between A and B. The movers enter the reach ceiling (702–703), and a lamp hangs at
     `max(reach + 0.1, 3.4)` (894).
   - **G-SEED** — s is the `seed` statement, and r is a record of a `skyline`, a `tower` in its comb form, a `neon` or
     a `puddle`. These are the four verbs that call `pick` (742, 761, 861, 912); the seed is read nowhere else (704,
     727).
   - **G-NAME** — the statement that made r (its `by`, on either side) names what s declares. It names a material s
     declares by using it in a material's position. It names the region s declares by using it as its first word. It
     names the building s declares by giving that building's corners in a bay's place. A neon's light takes its
     material's colour and strength (851, 878), and every verb with a region reads it by name through `_region` (464).
4. **UNEXPLAINED** — every other changed record.

The classification is mechanical. The judgment in it is the channel list, which is fixed here. The report lists every
DECLARED-GLOBAL record with its channel, and every UNEXPLAINED record in full, so that a reader sees what the list
absorbed.

## 6. Measures that do not depend on the classification

These are counted for every accepted entry:

- **Changed records**, by section and kind: added, removed and changed.
- **BEYOND** — changed records whose footprint shares no cell with s's scope. They are counted under each class, so
  the channel list cannot move a record into or out of BEYOND.
- **NO-EFFECT** — an accepted entry, other than NOOP, that changes no record.

## 7. Churn

Fix an accepted entry e, a statement p and a kind k. A kind is an id's word before its first `:`, or `mover` for a
mover. p's hash is h0 in A and h1 in B when p = s, and its one hash otherwise.

- **GONE(p, k)** — the records in `visuals`, `lights` or `movers` of kind k, with `by` equal to p's hash in A, whose id
  is absent from B.
- **NEW(p, k)** — the records of kind k, with `by` equal to p's hash in B, whose id is absent from A.
- **REPLACED(e)** = Σ over p and k of min(GONE(p, k), NEW(p, k)).
- **REASSIGNED(e)** — the records in `visuals`, `lights` or `movers` whose id is in both A and B but whose `by` differs,
  other than h0 in A and h1 in B: an id kept across the edit that now names another statement's piece.

REPLACED is the number of pieces a statement lost while as many pieces of the same kind appeared: an object
**re-addressed**. It never says which piece became which, since nothing is matched by likeness. So where an edit also
changes how many pieces there are (a lattice, a percentage, a seed), it is an upper bound on re-identification.
REASSIGNED counts the other failure of an id, **reuse**: one id naming two things across an edit.

The same counts are kept for objects — **ROOT-GONE**, **ROOT-NEW**, **ROOT-REPLACED** and **ROOT-REASSIGNED** — over
`scene_diff.object_records`' roots and their `by`. **KEY-CHANGED(e)** means s's statement key (`dress.statement_key`)
differs before and after the edit.

Each count is reported per class, per role and per verb, as sums and as the entries with ROOT-REPLACED > 0, with
OWN (p = s) and OTHER (p ≠ s) kept apart.

## 8. The seed sweep

For each brief: the baseline and its seven SEED entries, eight scenes.

## 9. The predictions (frozen; the run decides them)

**P2.** In `harbor-lift`, at least one accepted perturbation of `mover deck …` or `mover lift …` changes at least one
record of `lights` whose cell lies outside the union of that mover's swept footprints before and after the
perturbation.

- **Verdict:**
  - HELD — such an entry exists.
  - FAILED — accepted mover entries exist, and none is such.
  - NOT-REACHED — no mover entry is accepted.

  Every such entry and light is listed.
- **The author's expectation, recorded before the run:** HELD, through G-REACH: each lamp hangs at its cell's reach
  (894), and a mover raises the reach of the cells near it.

**P3.** The debate's words: "across seeds the topology is identical and only heights differ". Operationally, for each
brief, every one of §8's eight scenes:

- has the baseline's ids in `visuals`, `lights`, `collision` and `movers`;
- holds each such record equal to the baseline's except at `box[1]`, `box[4]` and `pos[1]`;
- holds every other section equal.

**Verdict:** HELD for a brief when all three hold. P3 is HELD when it holds for all four briefs.

- **The author's expectation from reading, recorded before the run:** FAILED for all four briefs.
  - `pick` decides whether a neon is placed (861; `every` is 2, 3 or 5 in the briefs).
  - It decides whether a puddle lies and where in plan (913–916; the percentages are 15 to 35).
  - So the ids that differ are expected to be `neon:` and `puddle:` only, and skyline and comb-tower records to differ
    at `box[4]` only. Every other record is expected equal across seeds.
- P3 stays a prediction under his first condition. The expectation is recorded beside it, not in its place.

## 10. The confirmation row (from reading, not a prediction)

**P1.** A one-cell shift re-identifies an object. For every accepted SHIFT entry of a `building`, or of a `canopy` with
corners:

- the statement's root object id in A (`building:x0,z0-x1,z1` or `canopy:x0,z0-x1,z1`) is absent from B; and
- a root of the same kind made by s is new.

The id is written from the corners (791, 951): this is established by reading, and the run confirms it. A row with no
accepted case reads NOT-REACHED, never HELD.

## 11. Reading expectations, recorded before the run

These are not predictions. Each is DECLARED until the run, which reads it CONFIRMED or CONTRADICTED.

- **R1.** UNEXPLAINED = 0 over all accepted entries: every path found in reading from one statement to another
  statement's records is a channel of §5.
- **R2.** The eight scenes of §8 differ only in `skyline`, comb-`tower`, `neon` and `puddle` records.
- **R3.** ROOT-REPLACED > 0 on at least one MODIFY entry (§15), since P1's cases are MODIFY entries.
- **R4.** REASSIGNED = 0 over all accepted entries: an id is a place, and two pieces in one place are refused (the
  one-fixture-per-place rule), so no edit of one statement hands a kept id to another statement.

## 12. Grant survival

This is a proxy for his F-3 decision, not SCOPE-GRANT-0's evidence. A target or a pin names one object by its id
(`art/studio.py:894`).

Take an accepted MODIFY entry of a statement that makes objects. Its id-grant G is the set of root ids s makes in A. G
**survives** when every root s makes in B has an id in G. The report gives the share that survives, per class and role.

Grants derived from shapes are not measured. The fixtures have no shapes. A shape names its anchor object by id
(MARK-0), so its naming survives exactly when the id-grant does. Whether an edit stays inside a shape's prism is
STRICT-0's question.

## 13. The harness's checks (they set the run's exit status)

| check | holds when |
|---|---|
| H1 INVENTORY | the inventory made again equals `INVENTORY.jsonl` byte for byte; otherwise `LOCALITY-INVENTORY`, nothing run |
| H2 FIXTURES | every fixture's sha256 equals `FIXTURES.sha256`; otherwise `LOCALITY-FIXTURE`, nothing run |
| H3 NOOP | for each brief, the NOOP entry's bytes differ from the fixture's, and its scene equals the baseline's (no changed record, equal `scene_bytes`) |
| H4 DIFF | for every accepted entry, `scene_diff.apply(diff(A, B), A)` returns B (its own completeness check, `SCENE-DIFF-INCOMPLETE` otherwise) |
| H5 TOTAL | every changed record has exactly one class, and the classes sum to the changed records |
| H6 COVERAGE | every statement but `map` has an entry, and every dressing or mover statement has an accepted entry |
| H7 HASHSEED | `PYTHONHASHSEED` is `0`; otherwise `LOCALITY-HASHSEED`, nothing run |

The predictions, the P1 row and R1 to R4 do not set the exit status: a FAILED prediction is a result. Two byte-identical
runs of the report establish reproducibility on one machine, *"not completeness of the dependency audit"*, as he wrote.

## 14. The plants (`python art/locality.py selftest`)

PL-GLOBAL and PL-RENUMBER run over a fixed subset: every entry of `plaza-night` and `harbor-lift`, 1,182 entries; the
clean run of the same subset is made in the same self-test. NOOP-CLEAN and PL-NOOP run over the four NOOP entries. Each
plant is set only by its row and put back after.

| row | the defect planted | caught when |
|---|---|---|
| NOOP-CLEAN | none | H3 holds for all four briefs |
| PL-GLOBAL | a dependence on the whole brief: after `export`, every `lights` record's `candela` is raised by 1 + the first four hex digits of the sha256 of all statement texts, read as a number | the subset's UNEXPLAINED is greater than the clean subset's, and every record UNEXPLAINED under the plant but not clean is a `lights` record whose changed fields are among `candela` and `by` |
| PL-RENUMBER | ids that are not names: every visual's id becomes `v%05d` by its place in sorted id order, a light sharing a visual's id takes that visual's new id, and every other light becomes `l%05d` by its place among the rest | the subset's REASSIGNED records under the plant exceed the clean subset's (so at least one entry has more) |
| PL-NOOP | a harness defect: each entry's brief is exported under a name of its own (`NAME~n`) | H3 fails on all four briefs, with its one changed record the top field `name` |

Expected: `LOCALITY SELFTEST 4/4`.

## 15. The exit record (its form is fixed here)

**MODIFY** entries are the accepted entries of SHIFT, MAT, and NUM± with role POSITION, SIZE, APPEARANCE, VIEW or
MOTION. DEL, LATTICE, SEED and NOOP entries are not MODIFY.

The report ends with these lines:

```
EXIT  churn under MODIFY: OBSERVED (k of m entries re-addressed roots, r reused an id; by verb and class …; the key
                          changed in j of them) | NOT OBSERVED (0 of m re-addressed, 0 reused)
      unexpected influence: OBSERVED (n UNEXPLAINED records in q entries, listed) | NOT OBSERVED (0 in N changed records)
      declared channels: G-REACH n, G-SEED n, G-NAME n records; BEYOND n
      predictions: P2 …, P3 …; confirmation P1 …; reading R1 …, R2 …, R3 …, R4 …
      cited: the inventory numbers that decide each line
      limits: Observed influence under-approximates true dependence. Each entry is one step of one statement in one of
        four briefs over one map (tactical), with the exporter whose sha256 the report names: a dependence shows only
        where that step crosses it (a max(), a threshold, rounding to 0.1 mm, a modulus or a refusal can hide one), and
        only in these briefs. Two edits at once, other maps, other exporters and other values are not measured.
      not established: the necessity or sufficiency of any replacement identity architecture (statement key and role
        path, a sidecar, a new scene version or another); anything about the renderer, play, physics, generated worlds
        or perceptual diversity.
```

The recommendation that goes to him cites these lines, the inventory numbers and the limits. It proposes nothing the
lines do not show.
