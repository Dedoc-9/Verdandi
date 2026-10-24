# LOCALITY-1 — the record of its run

> **The name.** LOCALITY-1 was admitted on 2026-10-24 under the working name LOCALITY-0. That name is already the
> registered, LOCKED floor-tile execution-format court's (`verify/preregister.json`; seats 18 and 19 of
> `verify/RUNGS.md`). By his ruling (*"Name: LOCALITY-1"*), `SHEET-v3.md` records the alias: where this
> measurement's frozen and registered records, and his rulings, say LOCALITY-0, they mean LOCALITY-1. Their bytes
> stay as they are.

> A measurement, admitted as one (2026-10-24): *"I admit LOCALITY-0 as the next foundational measurement commit, not as
> proof that an identity layer is necessary."*
>
> Every result below was run in a scratch clone on this machine, not from his checkout: Windows, Python 3.14.5,
> `PYTHONHASHSEED=0`, `PYTHONUTF8=1`. None of it is his host's record. The gate's, the full check's and the classifier's
> results **for the tree that holds this file** are in its commit's message, never in a file of that tree (AGENTS.md
> §7). The results for earlier trees, named by tree id, are history and are kept here.

## 0. How each claim is graded

| grade | meaning |
|---|---|
| **MEASURED** | run here, with the output kept (its sha256 in §11) |
| **STATIC AUDIT** | read from the code's path construction; nothing run |
| **READING** | what the code says it does, cited by line; nothing run |
| **EXPECTATION** | written down before the run; the run then confirms or contradicts it |
| **NOT_MEASURED** | said so, and nothing more |

## 1. To reproduce

| command | expected |
|---|---|
| `python art/locality_inventory.py` | `LOCALITY INVENTORY HELD: 2418 entries, sha256 455af6c8…`, after the fixtures, the inventory and `FROZEN.sha256` (`7f701155…`) have been held to their bytes and the spec's text; exit 0 |
| `python art/locality.py run` | `LOCALITY HARNESS HELD (H1-H7)`, then `LOCALITY-1 REPORT a16faccda679e5c3c4f6c741bd6d804d671ecbe7d886c2f63a5d4c7402af02aa`; exit 0 whatever the predictions' verdicts. It writes `art/build/locality/REPORT.json` (that sha256) and `REPORT.txt` (`7d220dbe0df533563124567d57f295a3e6464c2107825ac532541fd1381e1ed3`). |
| `python art/locality.py selftest` | `LOCALITY SELFTEST 4/4`; exit 0 |

**Reproducibility (MEASURED).** The report was byte-identical in three runs: two in the scratch clone, and one in a
fresh clone under the read-set recorder.

**The report's history.** The rename (`SHEET-v3.md`) changed three things: the report's format name
(`VERDANDI-LOCALITY-1 0`), its title line, and the hashes of the two renamed source files. Before it, the bytes were
`51695596…` / `776e7456…`, identical in eight runs. Before hardening fix 5 they were `5793105e…` / `8195d54f…`,
identical in eight runs:
- two after the conformance review, one in a fresh clone, two after the inventory split, one in a second fresh clone;
- two more on the tree before the hardening fixes.

Hardening fix 5 changed them, as it was meant to: the report now hashes all twelve files the run executes. A field
comparison of the two reports finds exactly these differences:
- `read` gains the 8 newly hashed files;
- the H2, H5, H7 and R2 detail texts change;
- each of the 28 seed entries gains its `r2_outside` list, which is empty.

No measured value differs.

Three earlier runs, made before the conformance review, are superseded and not counted: `eec61d73…` (one run) and
`ae3df68c…` (two equal runs).

Two equal runs establish reproducibility on one machine, in his words *"not completeness of the dependency audit"*.
Nothing is claimed for another machine or interpreter.

**Times (MEASURED, software timings):** the counted runs took 209, 210 and 209 s (the last under the recorder); the
self-test 317 and 321 s.

## 2. What the run observed

These are observations of this exporter on these fixtures; §9's limits apply.

**Accounting (MEASURED):**
- 2,418 entries = 2,042 accepted + 376 refused + 0 crashed. None is dropped.
- 35,962 changed records. H5 holds: each record has one class, the classes sum to the diff's own count, and each listing
  equals its count.

**Refusals by reason (MEASURED; all 376, each in exactly one row):**

| reason | entries |
|---|---|
| a canopy's corners leave its region | 86 |
| a material's `metallic` stepped below 0 | 44 |
| not a colour | 38 |
| no region (a region deleted while a statement names it) | 36 |
| no material (a material deleted while a statement names it) | 31 |
| no surface for a class (a surface deleted) | 24 |
| a building not on rock | 18 |
| a surface names a material that is not declared | 16 |
| a neon material that does not emit | 11 |
| a view where no player can stand | 11 |
| a building bordering no cell of its region | 10 |
| a mover's number not a whole unit (its corners, travel or speed) | 10 |
| a value outside its bounds (spacing, rain, storey height, yaw) | 10 |
| two puddles in one place | 8 |
| two lamps in one place | 7 |
| a mover's travel meets a cell above its bottom | 6 |
| the asset `cube` not declared | 4 |
| a lamp's housing material not declared | 4 |
| a mover's travel leaves the world | 2 |

Every refusal message is in `REPORT.json`.

**Classes (MEASURED):** OWN 17,838 (2,894 of them BY-ONLY), IN-SCOPE 1,262, DECLARED-GLOBAL 16,862, **UNEXPLAINED 0**.

| channel | records |
|---|---|
| G-REACH | 334 |
| G-SEED | 14,590 |
| G-NAME | 1,938 |

**BEYOND (MEASURED): 19,676**, whatever the class.
- It includes 2,466 records of comb towers.
  - *READING:* they stand on the rock cells round their region, outside its rectangle (`art/dress.py` tower branch).
- It also includes every seed-reached record. A seed has no scope.

**Churn under MODIFY (MEASURED): 1,741 entries.**
- **Re-addressing of the edited statement's own objects: 126 entries.**
  - Buildings: 48, from corner NUM and SHIFT edits.
  - Canopies: 78, from corner NUM and SHIFT edits.
  - All 126 also changed the statement's key.
  - *READING:* both verbs write id and key from their corners (`art/dress.py:791, 951`).
  - The 44 accepted SIZE edits of buildings and canopies kept their ids.
- **Re-addressing of other statements' objects: 41 region edits.**
  - These are tower, neon, puddle and lamp pieces: pieces of a kind were lost while others of that kind appeared.
  - REPLACED = min(gone, new) per statement and kind. It bounds re-identification from above; it is not shown to be
    one object renamed. Where the pieces stand is not recorded.
- **Re-addressing outside MODIFY:**
  - lattice edits: 55 (neon 31, lamp 24);
  - seed entries: 28;
  - seed deletions: 4.

  These are per-cell pieces, as above.
- **Reuse of an id (REASSIGNED): 0** over all accepted entries.

**Predictions (frozen before the run; MEASURED verdicts):**
- **P2 HELD.** Two witnesses changed lamp records outside the lift's swept cells:
  - entry 1828 deleted `mover lift …`, and changed the lamp records at 8,28 and 12,28;
  - entry 1830 raised the lift's lower corner from y 0 to 1, and changed the lamp record at 8,28.

  This matches the EXPECTATION written before the run.
- **P3 FAILED on all four briefs.**
  - Neon and puddle ids differ across the eight seeds.
  - 580 kept-id puddle records differ in plan.
  - No other kind differs beyond the masked fields.
  - The verdict, and the kinds of id that differ, match the EXPECTATION, whose "where in plan" covers the kept-id
    puddle changes.
  - The harness masks `box[1]`, `box[4]` and `pos[1]` together. So whether skyline and comb towers differ at `box[4]`
    only is **NOT_MEASURED**.

**Confirmation:** P1 HELD on all 29 accepted SHIFT entries of a building, or of a canopy with corners (MEASURED). The
39 such entries that were refused stay outside the confirmation.

**Reading expectations, all CONFIRMED (MEASURED):**
- R1: UNEXPLAINED is 0.
- R2: every changed record of the 28 seed scenes is a visual or a light made by a skyline, a comb tower, a neon or a
  puddle. This is read from the producing statements' verbs, apart from the channel list.
- R3: 167 of 1,741 MODIFY entries re-addressed objects.
- R4: 0 records reassigned.

**Grant proxy (MEASURED; SPEC.md §12; shape grants not measured):** id-grants survived MAT 67/67, NUM 286/383 and
SHIFT 0/29.

## 3. The plants, and the hardening tests

**`LOCALITY SELFTEST 4/4` (MEASURED).**

**Clean subset** (plaza-night and harbor-lift): 1,182 entries, 997 accepted, UNEXPLAINED 0, REASSIGNED 0.

| row | result |
|---|---|
| NOOP-CLEAN | four briefs: 0 changed, bytes differ, scene bytes equal |
| PL-GLOBAL | UNEXPLAINED 69,386 under the plant, 0 clean. Every added record is a light whose only changed field is `candela`. REASSIGNED unchanged; no outcome changed. |
| PL-RENUMBER | REASSIGNED 26,520 under the plant, 0 clean. Each of the 244 entries that reassign an id adds or removes a visual or a light in the clean run (283 entries do so); the inclusion is one-way. |
| PL-NOOP | the no-op control fails on all four briefs, each with one changed record: the top field `name` |

Plant success is evidence about the harness, not about the exporter. These plants are not R5 keys.

**`HARDENING TESTS 20/20` (MEASURED).** These are planted tests of the hardening fixes (§8), run from outside the
repository; each requires its refusal, or its failing check, and a control that holds.
- A one-byte change to `SHEET.md` or `FROZEN.sha256`, and a reordered `FROZEN.sha256`, are each refused by the harness.
- An altered inventory is refused `LOCALITY-INVENTORY`.
- The rule, the constants, the inventory and `FROZEN.sha256` edited together are refused: the spec states otherwise.
- A map fixture, or executed code, changed during a run is refused after it.
- The `.py` files a run with movers opens are exactly the twelve in `READ`, hashed before `measure()`.
- `python -E` with `PYTHONHASHSEED=0` is refused.
- H5 fails, in turn, on:
  - a listing that disagrees with its count (with the sums kept equal);
  - a dropped DECLARED-GLOBAL record;
  - a diff count that is off;
  - `records()` dropping the reach section (11 of 12 accepted mover entries in the sample).
- R2's producer reading finds 70 lights not made by a picked verb, under a classifier that forces every seed
  record into G-SEED.

Two earlier runs of that test file failed on defects of the test itself, not of the harness. Both outputs are kept:
- **run 1:** it looked for loaded modules in `sys.modules`, which `graybox/rules_ref.py` never enters (it is loaded by
  `spec_from_file_location`), and it called `verdicts()` with every entry for a subset's results;
- **run 2:** its sample held no accepted entry with a declared record.

## 4. The read and write sets, under version 1 and version 2 of the sheet

The measurement ran in a fresh clone holding commit 2's exact code and fixtures, with no bytecode, under a Python audit
hook installed before the program. The hook records `open`, listing and process-start events; it sees nothing a C
library reads without one. The recorder's own check caught a planted read, a planted forbidden read and a planted
process.

| program | code files read | fixture files read | bytecode probes | folders listed | writes | processes |
|---|---|---|---|---|---|---|
| `art/locality_inventory.py` | 3 | 11 | 2 | `art`, `graybox` | none | none |
| `art/locality.py run` | 12 | 11 | 11 | `art`, `art/director`, `graybox` | `art/build/locality/` with `REPORT.json` and `REPORT.txt` | none |
| `art/locality.py selftest` | 12 | 11 | 11 | as `run` | none | none |

`art/briefs/` and `graybox/maps/` were never touched. No `__pycache__` folder existed in the clone before or after any
run (MEASURED: counted 0 and 0 around each run).

**Under version 1** (`SHEET.md`, frozen), all three verdicts are **`READSET OUTSIDE THE DECLARED SETS`**. They stand
as the recorder gave them, and are not relabelled. Two kinds of event are outside version 1's declared set:

1. **`art/locality_inventory.py`**, a source file.
   - It came into being when the inventory rule moved into commit 1's tooling, at his instruction, after version 1 was
     written.
   - The read-set analyses before this one used a declared set that already included it, without revising the sheet.
     That was a departure, and it is now recorded (§10).
2. **The bytecode probes.** These are `open` events on `__pycache__/*.cpython-314.pyc` paths.
   - Each is for the cached copy of a `.py` file read in the same run.
   - No `__pycache__` folder existed at any point, and the run wrote nothing under one. So each was an open of a file
     that did not exist.

Version 1 says *a read outside the declared set stops the build and revises this sheet*. So the exception he allowed
cannot be taken under version 1.

**Version 2** (`SHEET-v2.md`, sha256 `2706f28b…`) was registered before any code applying it was written, and before
this measurement was run again. It does two things:
- adds `art/locality_inventory.py` to the declared read set;
- defines one bounded exception, the bytecode probe. An open of `D/__pycache__/S.cpython-NNN.pyc` is excepted only
  when all three hold:
  - `D/S.py` is a declared source read in the same run;
  - no `__pycache__` exists before or after the run;
  - nothing is written under one.

Every other undeclared read is still outside.

Its analysis (`readset_v2.py`) passed `READSET V2 SELFTEST 9/9` before use. These are its cases, each on a log made for
it; version 1's verdict stays OUTSIDE on each one:

| case | reads |
|---|---|
| the control | WITHIN |
| a `__pycache__` present before | OUTSIDE |
| a `__pycache__` present after | OUTSIDE |
| a write under one | OUTSIDE |
| a probe whose source was not read | OUTSIDE |
| a probe whose source is undeclared | OUTSIDE |
| an undeclared `.py` | OUTSIDE |
| a read under `art/briefs/` | OUTSIDE |
| a process | INCOMPLETE |

**Under version 2** (MEASURED, the measurement run again): all three read
**`READSET UNDER SHEET v2: WITHIN THE DECLARED SETS`**, with 2, 11 and 11 bytecode probes excepted, each named in the
kept analysis. That run's report was `51695596…` again, and its self-test 4/4. After the rename (`SHEET-v3.md`), the
measurement was run once more in a third fresh clone of the renamed code: the same verdicts under both versions, the
analysis byte-identical (`1875ea3d…`), and the report `a16faccd…`.

## 5. Which existing checks reach these files (STATIC AUDIT)

This is a read of the gate (`verify/`) and the full check's suites, by path construction; nothing was run.
- **The 12 files under `art/fixtures/locality/`:** no listing, copy or import reaches them. The briefs' and maps'
  basename matches (for example `art/certificate.py`, `art/director.py`) open `art/briefs/` and `graybox/maps/`, never
  these copies.
- **The two new `.py` files:** `art/play.py:380`, the live loop, lists `art/*.py`.
  - `digest()` opens and sha256s each file (`art/play.py:401-409`).
  - `stamp()` stats each one (`art/play.py:473-484`).
  - This happens in LIVE, PAGE, PAGE-CARDS, PAGE-WORLDS, FLAGSHIP and STUDIO.
  - The loop never imports or runs them.
  - Whether hashing them changes any row's outcome is **NOT_MEASURED**.
- **The gate:** `verify/` builds no path into `art/`.
- **Not settled:** the audit did not walk every computed path one by one.

## 6. The classifier, tree by tree

The sheet expected "below D" and "C". The pushed tree's `tools/rung.py` computes **D?** for every tree measured so far
(MEASURED):

| tree | range | rung |
|---|---|---|
| `dd35fe15…` | the change as first staged | D? |
| `a38e7d4a…` | the first commit 1 | D? |
| `e5053c02…` | origin/main to the first commit 2 | D? |
| `e5053c02…` | the first commit 1 to the first commit 2 | D? |

The final commits' results are in their messages. The expectation is now D?.

**Why D?** The fixture briefs and maps read D because files of the trusted base name their basenames. Every other new
file reads D? because the base reads files by computed paths (717 places) and loads code by computed names, so the
classifier cannot show a file is outside its closure.

**Why it stays uncertain:**
- Name matching cannot follow a computed path.
- §5's audit is static.
- The suites' own read sets have not been measured.

So the closure question stays open, and no claim is made that these files are outside the trusted closure. The
classifier was not changed. It reports that the change loosens nothing it knows to look for.

## 7. The full check, run by run

| tree | run 1 | run 2 |
|---|---|---|
| `dd35fe15…` (the change as first staged) | 28/28 | **24/28** (see below) |
| `de91aaf` (the base, without the change), run just after | **24/28** (see below) | **27/28**: PREVIEW-STUDIO 13/14, 14.84 s |
| `e5053c02…` (the change before the hardening fixes) | 28/28 (600.9 s wall) | 28/28 (640.5 s wall) |

**`dd35fe15…` run 2's failures:**
- STUDIO-2 46/47: "the provider ran past 30 s";
- PREVIEW-STUDIO 13/14: B4-TIMING-BOUNDARY, 15.89 s against a 10 s bound;
- PAGE-CARDS 26/27: "the request drew no Panelled bay";
- FLAGSHIP 5/6: a StopIteration where a candidate stage was missing.

**The base's run 1 failures:**
- STUDIO-2 4/6: "the provider ran past 30 s", then "HTTP Error 409: Conflict", and the suite did not run to its end;
- STRICT 10/11 and IMPACT-STUDIO 7/8: no candidate returned;
- FLAGSHIP 4/5: the same StopIteration.

**Isolated reruns.** The four suites that failed on `dd35fe15…`'s run 2 were then run alone on that tree, `--repeat 2`.
They passed twice: STUDIO-2 47/47, PREVIEW-STUDIO 14/14, FLAGSHIP 9/9, PAGE-CARDS 31/31. These reruns are diagnostic,
not a pass. Neither full-check run was repeated or tuned.

**Disposition: BASE-AND-PATCH-FAIL; the cause is NOT_MEASURED.** The base red too, and the isolated passes, do not show
that the change is unrelated to the failures. The `e5053c02…` passes do not undo the earlier failures. The final tree's
two runs are in its commit's message.

**The gate (MEASURED, history).** On `dd35fe15…` and on `e5053c02…`, `GATE PASSED`, rowset `74db4c8d78625af5`,
251/0/0, the outputs byte-identical (`7639fb48…`).
- On `e5053c02…` the first comparison failed. The cause was a timing line that the build's own step wrapper appended
  to each output file.
- With that line removed, the gate's bytes are identical.
- The final runs keep timings in a separate file.

## 8. The reviews, and what they changed

**A conformance review of the harness against `SPEC.md`** made eight fixes, none to a definition: H5 able to fail, P3's
extra label removed, R2 counting every seed, BY-ONLY as written, the reporting splits, unclipped cells, the decode
outside the crash catch, and the plant rows' names.

**Four hardening reviews**, read-only, each from a different angle:
- **R-A** planted harness defects;
- **R-B** re-derived the inventory from the spec alone and matched all 2,418 entries;
- **R-C** audited what reads the new files (§5);
- **R-D** audited this record against the raw outputs.

**Eight fixes, within the frozen spec, came from them:**
1. the harness holds `SHEET.md` and `FROZEN.sha256`;
2. the tool refuses an altered inventory as `LOCALITY-INVENTORY`;
3. the hash constants are held to the spec's text;
4. the fixtures and the executed code are checked again after each run;
5. all twelve executed files are hashed before and after a run;
6. H7 also holds the interpreter's hash-randomization flag;
7. H5 holds each listing to its count;
8. R2 is read from the producers' verbs.

R-D's nineteen corrections to this record are applied here.

## 9. Limits, what is deferred, and what is not established

**Limits:** Observed influence under-approximates true dependence. Each entry is one step of one statement, in one of
four briefs over one map (tactical), with the exporter at `e926f9f1…`:
- a dependence shows only where that step crosses it (a `max()`, a threshold, rounding to 0.1 mm, a modulus or a
  refusal can hide one);
- and only in these briefs.

Two edits at once, other maps, other exporters and other values are not measured. A skyline's scope is every cell, so
its 24 entries can never show UNEXPLAINED or BEYOND for a record with a footprint.

**What the plants cannot falsify.** These are deferred from LOCALITY-1, as he recommended, with the spec and the
inventory unchanged:
- **A1:** PL-GLOBAL plants a dependence in lights only. A channel too broad for visuals or collision would pass every
  plant, and R1 would still read CONFIRMED.
- **A2:** a churn-blind harness (REPLACED forced to 0) passes every check and plant. P1 and R3 would then disagree, and
  no row checks that.
- **A3:** an accepted entry mislabelled REFUSED would be lost silently; H6 needs only one accepted entry per statement.
- **A4:** BY-ONLY as written makes a reused id whose only change is `by` read OWN. It is still counted apart as
  REASSIGNED, and in this corpus both readings give identical results.

Any of these would be a new spec version, registered before its code. None is needed for the measurement as admitted.

**Where `SPEC.md` is silent, and the frozen inventory chose (R-B):**
1. the edited line is rewritten with single spaces;
2. NOOP rewrites the `map` line too;
3. SHIFT carries role POSITION, while MAT, DEL and SEED carry none;
4. a mover corner's y part is POSITION.

Also, `SPEC.md` line 4 says `art/locality.py` holds its sha256; since the split, it imports it from
`art/locality_inventory.py`.

**Latent, not met by the fixtures (R-B):**
- `step()` would write a number of more than four decimals in exponent form;
- a region, material or mover named `bay`, `deep`, `speed` or `face` would get the wrong role;
- MAT skips a material word that is not declared.

**Not established:**
- the necessity or sufficiency of any replacement identity architecture: statement key and role path, a sidecar, a
  new scene version or another;
- the correctness of the exporter;
- the completeness of the dependency audit;
- anything about the renderer, play, physics, generated worlds or perceptual diversity.

**What the observations give the next decision.** In today's exporter, a corner edit of a building or a canopy changes
both its id and its statement key; its SIZE edits keep them. Region, lattice and seed edits change which per-cell pieces
exist. No id was reused, and no influence went outside the three named channels. This supports investigating identity
preservation for corner-named objects. It does not authorize an identity layer, and it does not show which design would
be sufficient.

## 10. Departures from the sheet

| departure | detail |
|---|---|
| size | `art/locality.py` 901 lines and `art/locality_inventory.py` 317, against an ESTIMATE of 500–700 |
| added at his instruction (2026-10-24) | commit 1 holds `SHEET.md` (its recorded bytes), `FROZEN.sha256` and `art/locality_inventory.py`; commit 2 holds this record |
| the inventory rule's place | it moved into `art/locality_inventory.py`. The inventory, the report and the self-test were byte-identical across the move |
| the report's bytes | they changed with hardening fix 5, and again with the rename (§1) |
| the name | admitted as LOCALITY-0, which is the registered floor-tile court's. `SHEET-v3.md` (`d5ba09a9…`), registered before any file was renamed, makes it LOCALITY-1; the frozen and registered records keep the working name in their bytes |
| the read-set rule | the recorder's verdict under version 1 is outside the declared set (§4). Version 1's rule is revised by `SHEET-v2.md` (`2706f28b…`), registered before the rerun; the earlier analyses' use of an extended declared set is a departure, recorded here. Pending his acceptance of version 2 |
| the rung | D?, not C (§6) |
| the full check | red on one earlier tree, BASE-AND-PATCH-FAIL (§7) |
| the scratch tools | not committed, because they hold the build machine's paths. They are recorded by sha256 instead: `make_inventory.py` (`04447763…`) made the inventory before any result; `verify_sheet.py` (`8325eaba…`) verified the sheet |

## 11. Outputs kept outside the repository, by sha256

**This tree's runs:**

| output | sha256 |
|---|---|
| `REPORT.json` | `a16faccd…` |
| `REPORT.txt` | `7d220dbe…` |
| the field comparison across the rename | `c7feeee2…` |
| `SHEET-v3.md`'s registration log | `46acf4fe…` |
| the self-test's output | `cbd7783d…` |
| the hardening tests' output | `6cfdc246…` (run 1 `c3daa372…`, run 2 `104051cf…`) |
| the hardening test file | `562d31e4…` |
| the read-set analysis under version 1's recorder output (first run) | `dae49bdb…` |
| `SHEET-v2.md`'s registration log | `ad55a159…` |
| the version 2 analysis, `readset_v2.py` | `a8acaf73…` |
| its plants, `READSET V2 SELFTEST 9/9` | `8c4c7604…` |
| the rerun's analysis under versions 1 and 2 | `1875ea3d…` |
| the read-set recorder | `3b05b7e3…` |
| the report field comparison across hardening fix 5 | `3bddaa77…` |
| `REPORT.json` and `REPORT.txt` before the rename | `51695596…`, `776e7456…` |

**Earlier trees:**

| output | sha256 |
|---|---|
| `dd35fe15…` full check summary | `8ac75168…` |
| `dd35fe15…` full check log | `a3400363…` |
| the base full check summary | `81665eae…` |
| the base full check log | `073e986f…` |
| the isolated reruns | `4963a360…` |
| `e5053c02…` full check summary | `afbd8070…` |
| `e5053c02…` full check log | `a21ee67c…` |
| the gate output | `7639fb48…` |

Each report can be made again with §1's commands.
