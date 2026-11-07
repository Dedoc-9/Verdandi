# VERIFICATION-COST: what verification costs in Verðandi, and what its design saves (0267)

This note records two things. First, what one full verification of a landed change cost, as measured. Second, which
parts of the architecture are meant to lower the cost of verifying the next change. For each of those parts, the note
says whether code enforces it, whether code merely implements it, or whether it is an order a person follows.

It is documentation only. It changes no code, row, register, frozen file or count, and nothing in the program reads it.
It was written on 2026-11-07 at tree `63796a2614ca2d4e2e92b90fc124302a30c7e9f0` (main at `e43fa3d`). Every `file:line`
below is a line of that tree. Lines move, so read an anchor against that tree, not the working copy. "The owner" is
the repository's owner; his rulings are quoted in his words.

## How to read it

Every claim carries one of three grades, the owner's labels for this note:

- **MEASURED**: a count or a time taken from a run's own output. It says where and when it ran.
- **DESIGN**: what the code at the anchor does, read from the code. It is not a measurement, and it says nothing of
  speed.
- **HYPOTHESIS**: a saving the design is meant to give, which no off-against-on comparison has measured.

Every mechanism claim also carries one of three enforcement classes, his too:

- **ENFORCED**: the relevant check runs automatically on an ordinary work path taken by the work itself, and code
  refuses or fails when the property does not hold: every export, every evaluation, every admission, every studio
  request. No one has to start a check separately. The path is named.
- **IMPLEMENTED**: the check exists but requires someone to start it separately, or its result is not acted upon. The
  cell says which. Code that refuses inside a run a person starts is IMPLEMENTED here, the gate's 251 rows included:
  inside its run the gate's verdict is code's, but the run is a person's choice.
- **OPERATOR**: the relevant comparison or decision remains with a person, such as which checks run and in what order
  (a table in `AGENTS.md`, a sheet), or reading a printed value against the expected one. No code performs it.

A code anchor establishes an implementation, not its enforcement (the owner's words, 2026-11-07: "Code anchors
establish implementation, not necessarily enforcement."). No percentage appears below, and no speedup is claimed
without the baseline that measured it.

## 1. What one verification cost (MEASURED)

### 1.1 Where, when and how

- **Where:** the owner's Windows host, one machine, in his real checkout right after `git am` of 0265 and 0266 v4.
  Python 3.14.5, rustc 1.96.1. Nothing ran in the build container or on GitHub's side.
- **When:** 2026-11-07, from 01:23:24 to 02:32:02 local time.
- **How:** one shell script ran the steps one after another. It timed each step with `date +%s`, whose step is 1 s.
  The full suite's own figures come from `time.perf_counter` in `art/selftests.py`, printed to 0.1 s.
- **Load:** a read-only research workflow ran on the same machine from about 01:32 to 01:37. That is about minutes 5
  to 10 of the full suite's 11.6. No other overlap is recorded. That nothing else ran is not measured.

| # | command | verdict (verbatim, opening words) | rows or cases | wall s |
|---|---|---|---|---|
| 1 | `python -B art/director.py racetest` | `DIRECTOR RACETEST PASSED (36 cases)` | 36, of them 7 `plant:` rows | 91 |
| 2 | `python -B art/director.py crashtest` | `DIRECTOR CRASHTEST PASSED (15 cases)` | 15 | 71 |
| 3 | `python -B art/director.py vectors` | `VECTORS 97 / 97` | 97 vectors | 1 |
| 4 | `rustc -O art/director/conform.rs -o art/build/conform` | (no output, exit 0) | a compile | 6 |
| 5 | `art/build/conform art/director/vectors.json` | `CONFORMANCE 97 / 97` | the same 97, a second implementation | 0 |
| 6 | `python -B art/check.py` | `ART CHECKS PASSED` | 262 rows | 57 |
| 7 | `python -B art/selftests.py` | `ART SELFTESTS PASSED` | 28 of 28 suites (1.2) | 695 |
| 8 | `python -B verify/verify.py` | `GATE PASSED`; `RECONCILE  rowset 74db4c8d78625af5  251 rows / 0 fail / 0 skipped` | 251 rows | 827 |
| 9 | `python -B verify/verify.py`, again | the same two lines; the two outputs byte-identical, sha256 `7639fb48300e1bc3aaafd1c79a80de53b5b144d030be008b7dc74c4c9a9b9a29` | 251 rows | 845 |
| 10 | `python -B tools/rung.py selftest` | `RUNG SELFTEST 22/22` | 22 | 9 |
| 11 | the pushed tree's `rung.py classify origin/main HEAD` | `THE CHANGE: rung D`; `loosens nothing this classifier knows to look for` | 10 files: 5 D, 5 D? | 16 |
| 12 | the pushed tree's `rung.py plants origin/main HEAD` | `RUNG-0 PLANTS  347 planted defects refused by the old checker; 350 by the new (350 rows)`; `PLANTS HELD` | 350 plant rows | 1499 |

**Total:** the twelve steps ran back to back, 4117 s of wall time from 01:23:24 to 02:32:01 (68 min 37 s), each timed
to the clock's 1 s step. The script, with its closing check of the checkout, ended at 02:32:02. The checkout was clean
before and after, with the same tree.

Steps 3 and 5 read 1 s and 0 s, each the difference of two whole-second readings. Step 3 therefore took under 2 s and
step 5 under 1 s, so their times are not measurements of their cost.

### 1.2 The full suite, suite by suite

The suites run at once in a pool, the browser suites one at a time in a lane. A suite's seconds are its own wall time
inside the shared pool, not what it costs alone. Summed, they far exceed the wall time.

Three runs of tree `63796a26` and one of 0265's tree `fe9b5c4d` are side by side. All four ran on the same host on
2026-11-06 and 2026-11-07. "Alone" means only that no other step of the script ran beside it.

| suite | landing (loaded: research) | v4 scratch, alone | v4 scratch, a race court beside it | 0265's tree, alone |
|---|---|---|---|---|
| director | 693.9 | 625.0 | 638.8 | 801.6 |
| studio | 681.4 | 611.3 | 630.8 | 763.4 |
| schedule | 388.8 | 355.1 | 366.3 | 439.3 |
| racetest | 292.8 (36 cases) | 270.4 | 300.5 | 542.9 (34 cases) |
| flagship | 274.6 | 262.7 | 280.4 | 344.9 |
| page-cards | 259.3 | 240.8 | 252.4 | 303.8 |
| preview-studio | 252.2 | 241.7 | 252.8 | 308.6, **13/14** |
| crashtest | 250.0 | 244.3 | 261.9 | 564.1 |
| txn | 225.3 | 178.7 | 191.2 | 231.3 |
| held | 225.0 | 224.1 | 239.0 | 271.5 |
| glue | 206.5 | 188.2 | 200.6 | 218.7 |
| page | 202.6 | 172.9 | 173.6 | 225.2 |
| queue | 192.7 | 202.2 | 209.3 | 251.7 |
| check | 191.3 | 180.4 | 204.5 | 231.1 |
| impact-studio | 155.1 | 159.3 | 152.8 | 191.2 |
| path | 138.3 | 131.3 | 131.9 | 143.5 |
| app | 99.5 | 102.8 | 100.3 | 114.1 |
| strict | 99.2 | 104.2 | 108.6 | 131.9 |
| live | 67.6 | 64.4 | 73.4 | 75.5 |
| facade | 54.8 | 58.2 | 61.6 | 84.2 |
| boundary | 46.0 | 43.8 | 44.1 | 47.7 |
| preview | 42.7 | 37.3 | 41.1 | 43.6 |
| page-worlds | 40.5 | 29.2 | 31.2 | 38.1 |
| marks | 27.1 | 24.7 | 29.2 | 28.9 |
| cert | 9.9 | 7.1 | 10.1 | 10.2 |
| legible | 5.6 | 5.6 | 4.9 | 6.0 |
| quality | 5.3 | 4.9 | 4.9 | 4.9 |
| impact | 1.2 | 0.9 | 0.5 | 0.6 |
| **wall** | **694.5**, 28 of 28 | **625.5**, 28 of 28 | **639.3**, 28 of 28 | **802.1**, 27 of 28 |
| PREVIEW-STUDIO's B4-TIMING-BOUNDARY row, the whole preview over HTTP (bound 10 s) | 7.46 s | 8.02 s | 8.54 s | 14.78 s, red |

Two rows carry the name B4-TIMING-BOUNDARY. PREVIEW's ("one candidate's runs") passed in every kept log. The row in
the table is PREVIEW-STUDIO's ("one candidate's preview").

On 2026-11-06 and 2026-11-07, 0265's tree was run in full twice: the run above and one more (823.1 s). Both were 27 of
28, with PREVIEW-STUDIO at 13 of 14. In the run above, the red row was B4-TIMING-BOUNDARY, at 14.78 s. In the other,
only the suite's summary line was kept, so which row failed is not recorded. Earlier, 0265's own commit message
(`07f27c0`, whose `Gated-Tree` is `fe9b5c4d`) reports one `--repeat 2` run of the same tree on 2026-10-25, both runs 28
of 28 (602.4 s and 668.4 s wall). These figures are not MEASURED by this note: they are read from the commit message,
not from the run's own output, and the message does not name the machine. The timing row's reading in those runs is not
known here.

Run alone (`python -B art/play.py --preview-selftest`), PREVIEW-STUDIO passes 14 of 14 on both trees. Its timing row
reads 1.70 s and 1.79 s on 0265's tree (two runs) and 1.77 s on `63796a26` (one run). The 1.79 s and 1.77 s runs took
64 s each; the 1.70 s run was not timed.

The cause of the red row inside a full suite is not measured, and this note names none. The bound is unchanged. In
the owner's words: "Its timing variability remains an observed limitation, not proof that the bound is wrong."

### 1.3 How much was checked

| what | count | how counted |
|---|---|---|
| rows that passed, steps 1 to 10 | 2116 | each log's own PASS rows (race court 36, crash test 15, art checks 262, full suite 1085, the gate 2 × 251, rung self-test 22) and, for vectors and conformance, which print no rows, the count in their one summary line (97 each) |
| each check counted once | 1551 | 2116, less the second gate run (251), less what the full suite repeats: race court 36, crash test 15, art checks 262, and the director self-test's first row, which judges step 3's 97 vectors again as one row |
| rows failed | 0 | every step |
| planted defects held across the change | 350 at the new tree, 347 at the old | R5 runs four suites (quality, art checks, director, studio) in full at both trees and reads their plant rows. Those rows are not counted above |

These counts are MEASURED from the logs. Which steps repeat which is DESIGN, read from `art/selftests.py`,
`art/director.py:1554-1556` and `tools/rung.py:388`. Vectors and conformance are two implementations of one set of 97
vectors, so both are counted.

### 1.4 The limits of these measurements

- **One machine.** Nothing here measures another host, the build container (where `AGENTS.md` section 4 says the gate
  takes about 25 minutes), a browser or a GPU. It is a software timing, labelled so.
- **Few runs.** No timing in section 1 is an average or a median of repeated runs: each comes from a single run. On the
  same tree, the three runs in 1.2 took from 625.5 s to 694.5 s of wall time. The two full runs of 0265's tree on
  2026-11-06 and 2026-11-07 took 802.1 s and 823.1 s. Its commit message reports two more on 2026-10-25, at 602.4 s and
  668.4 s (read from the commit message, not MEASURED here; the machine not named). Nothing recorded explains the
  difference between the two runs of 2026-11-06 and 2026-11-07. The 2026-10-25 pair differs from them in date,
  invocation and recorded conditions, and is not compared with them.
- **Loaded runs are not benchmarks.** The landing's full suite shared the machine with research for about five of its
  minutes. The v4 "beside" run shared it with a race court on purpose. Neither is a clean measurement, and no saving
  is computed from any difference between them.
- **PREVIEW-STUDIO's timing row is unstable.** Twelve full suites were completed on 2026-11-06 and 2026-11-07, and a
  thirteenth was stopped. PREVIEW-STUDIO passed in 3 of the twelve, all on tree `63796a26`, at 7.46 s to 8.54 s. The
  other nine ended 27 of 28 with PREVIEW-STUDIO at 13 of 14. In eight of those nine, the suite's own kept log names
  B4-TIMING-BOUNDARY as the red row, at 11.01 s to 18.55 s. In the other one, the full run of 0265's tree at 823.1 s,
  only the suite's summary line was kept. Seven of the twelve ran on the trees of 0265, 0266 v3 and 0266 v4. The other
  five ran earlier on 2026-11-06: four on unlanded trees over the base `b441a1e` (one with earlier drafts of 0266's D6
  fix and of a change, not landed, to how Undo finds its target in `art/studio.py`, applied together, neither as later
  delivered; one with the D6 fix's first delivered version; two with its second), and one on `b441a1e` itself. The bound
  was not changed.
- **No time is compared with anything.** The tables say what one verification cost. They do not say what the same
  work would cost without the design (section 3).

## 2. The six mechanisms and their enforcement

Each mechanism is split into claims, and each claim has one class. Every claim in this section is DESIGN, read from
the code at its anchors, unless it is marked MEASURED. All six mechanisms are partly enforced: each has parts that are
ENFORCED on a path the work takes and parts that rest on a person.

### 2.1 Narrow change scope

A change declares its reach, and code holds an art edit to what it declared. Nothing selects or skips a check because
a change is small.

| claim | class | anchors | does not establish |
|---|---|---|---|
| ADMISSION-0 computes an art edit's rung from the addresses the scope protocol found changed or affected. An admission refuses any rung but A, whether it comes from the command line or from the studio's Admit and Undo (both through `cmd_admit`). Replay refuses it again. | ENFORCED at every admission of an art brief through `art/director.py` | `art/director/contract.py:79-105`, `:160-161`; `art/director.py:1033`, `:1086-1088`, `:1292-1294`; `art/studio.py:1743`, `:2411` | That the rung is right at the admission: both the admission and replay check the rung recorded at evaluation, not one computed again. Replay does not check pre-0222 evaluations without a record. World edits through `design/design.py` are outside ADMISSION-0. |
| DIRECTOR-0 requires every changed or affected address to be declared. It never admits a REFUSED verdict. It admits LEAKAGE only when a person accepts it on the command line (`--accept-leakage`, recorded). The studio admits only CLEAN. | ENFORCED at every admission | `art/director/scope.py:243-258`; `art/director.py:920`, `:1080-1083`, `:2926`; `art/studio.py:1898-1899` (Admit), `:2277-2282` (Undo's inverse, called at `:2332`) | That a declared change is the right one. The declaration is the intent's own, and a model writes it in the studio. CLEAN means "matches what was declared", not "matches the prompt". The admission reads the verdict recorded at evaluation. |
| STRICT-0 computes the region check again from the admission's own evaluation, and refuses a strict request that fails it. | ENFORCED at the studio's admission, but only for a request the designer made strict | `art/studio.py:1901-1911`; `art/director.py:1049-1052` (the director's check of the flags it is handed) | Any region bound on a request that is not strict. The command line passes no region (`art/director.py:2926-2927`). |
| RUNG-0 computes a patch's rung from the dependency closure of its named roots, read through git on both trees and never from the patch's words. It escalates to D? every changed file outside that closure by its kind: every Python file when the trusted base loads code by a computed name, and every other file when it reads files by a computed path. | IMPLEMENTED: a person runs it, and nothing heeds its result | `tools/rung.py:55-65`, `:343-362`, `:658-662` | That anything uses it. No code calls `tools/rung.py`, and it is no gate row and no suite. `classify` returns 0 whatever the rung. Its headline does not separate D from D?, because `max()` at `:361` keeps the first file of rank 3 in diff order. |
| What each rung needs (the owner's runs, R5's plants, an unchanged rowset, the pushed tree's copy of the classifier) is printed text. | OPERATOR | `tools/rung.py:16-18`, `:69-79`; `AGENTS.md:111` | That the needs were met for any patch. Only commit messages say so: the classifier never reads one (`tools/rung.py:40`), the delivering agent drafts them, and the owner applies them. |
| No code chooses checks from what changed. The gate calls all 251 rows. The choice of which checks to run for a change is the `AGENTS.md` section 4 table and `--only`, which a person types. | OPERATOR | `verify/verify.py:16752-17015`; `art/selftests.py:361-363`; `AGENTS.md:73-78` | That the table was followed, or that the checks it picks suffice. |

**Saving: HYPOTHESIS.** A narrow change should need less review, and less work out of the person who judges it. That
is a hypothesis about review and change complexity. It is not a reduction in gate work: the gate runs all 251 rows
whatever the change (his words: "Narrow scope is not selective verification."). Neither rung computation saves any
machine work. ADMISSION-0's rung is computed after a full export and every expected check.

### 2.2 Deterministic, executable rules

The program's claims are code that returns a verdict. Most of that code runs only when a person starts it: the gate and
its rows, plus the self-tests and check commands named below. Two checks below run on the work path itself, on every
export and evaluation and at the studio's Admit and Undo. Either way, no one redoes the reasoning.

| claim | class | anchors | does not establish |
|---|---|---|---|
| Every gate claim is a row function. An `Exception` in a row becomes a FAIL row, not a missing one. The gate prints `GATE FAILED` and exits 1 when any row fails. | IMPLEMENTED: refuses inside the gate's run, which a person starts | `verify/verify.py:475-490`, `:17016-17021` | That a row checks the right thing, or checks it strongly. That a skipped row was acceptable: SKIP changes neither the verdict nor the exit status. A `SystemExit` or `KeyboardInterrupt` in a row ends the run with no verdict line and no RECONCILE line. The exit status is then not the gate's: a `SystemExit` exits with its own code (0 for `sys.exit()` or `sys.exit(0)`), so an exit status of 0 alone does not show that the gate passed. |
| The names and order of all 251 rows in `main()` are held: rows 1 to 247 by digest, rows 248 to 251 by name, with no duplicates. The rows already executed are also held, up to the fence. | IMPLEMENTED: refuses inside the gate's run | `verify/verify.py:16716-16719` (hermeneutics-fence); `:13142-13148` (reasoncourt-fence) | A count. A row appended after the 251st passes every fence. So can a weakened row body, unless it touches what some rows hold: mintwatch-fence holds the source text of REASON-COURT-0's six rows by sha256 (`verify/verify.py:13751-13754`, against `MW_REASONCOURT_ROWS` at `:13193-13200`), though not the helpers they call, such as `_rsn_source_check` (`:12626`); other rows hold registered text or counted endings (section 4). That pin is in the same file, so one edit can move it too. |
| The 58 sources in `RSN_SOURCES` are pinned by sha256. A changed one turns reasoncourt-fence and mintwatch-fence red. Clearing that needs a moved pin, a registered amendment that names both hashes, and a new link of `RSN_CHAIN`, whose length is held at four, so the gate's checks change too. `verify/envelope.py` and `verify/savedform.py` are pinned through the `mints.json` register, by mintwatch-inventory; `savedform.py` also by its own constant. | IMPLEMENTED: refuses inside the gate's run | `verify/verify.py:12262-12321`; `:13138` (reasoncourt-fence); `:13763-13765` (mintwatch-fence); `:13181`, `:13419-13420` and `:13326-13332` (the `mints.json` register's own bytes and the files it pins, mintwatch-inventory); `:11460`; `:16506` | That a change was right: a pin detects change, not correctness. `verify/verify.py` is not pinned as a file (`:13326`); of its rows, only REASON-COURT-0's six are pinned whole, by the sha256 of their text, by mintwatch-fence (`:13751-13754`). One edit to it can move a pin together with its expected value, and only the classifier and a person's review stand against that. |
| All 55 registered entries have their chain hash recomputed. 27 of them are also phrase-locked, by substring. | IMPLEMENTED: refuses inside the gate's run | `verify/verify.py:1358-1374`, `:4322-4336` | That an entry cannot be edited. An editor who also recomputes the stored hash passes. The phrase locks test that words are present, not what they mean. |
| Urðr's frozen game suites run inside the gate, under seed 0. Ten of their test files start fresh interpreters under `PYTHONHASHSEED` 0, 1 and 2 and require one output. | IMPLEMENTED: refuses inside the gate's run | `verify/verify.py:690-693`, `:740-742`, row `game-suites` at `:16754`; the loop at `oracle/game/tests/test_actionlog.py:189-195`, and in the nine other `test_*.py` files beside it | Seed independence outside Urðr's frozen game layer. Elsewhere, two outputs are tested across seeds (`art/scene_diff_test.py:995-1003`, `graybox/bot_ref.py:686-691`), by commands a person runs. |
| The art file's numbers and every intent are refused, not coerced, before any export or evaluation. | ENFORCED on every export and every evaluation | `art/dress.py:95-114`; `art/director/intent.py:168-218`, `:274-275`; `art/director.py:941`; `art/studio.py:1571-1575` (each candidate of a studio request, refused before `:1585` evaluates it), `:1396` (a recorded request drawn again) | That a statement is meaningful: `intent.validate` checks its form. |
| BINDING-0 runs as the gate of the director's commit, under the content lock and before the commit's first write. | ENFORCED at the studio's Admit and Undo | `art/director.py:730-732`; `art/studio.py:1732-1744` (Admit), `:2401-2411` (Undo) | Anything about an admission from the command line, which passes no gate (`art/director.py:1028-1029`). The register check itself (`art/director/binding.py:76-143`) runs only in self-tests and in check commands a person runs (`binding.py check`, `binding_freeze.py check`, `inverse_freeze.py check`); at a press the host never reads the register: it writes its pinned version and sha256 (`BINDING_SHA256`, `art/studio.py:617`) into the decision record (`art/studio.py:777`) and compares them with nothing; the pin is compared with the register's version-0 line only by STUDIO's self-test row M20p (`art/binding_rows.py:1436-1447`), which a person starts: IMPLEMENTED. |
| Three comparisons are made by a person reading output: the printed rowset against `74db4c8d78625af5`, the skip count beside `GATE PASSED`, and the byte identity of two gate runs. | OPERATOR | `verify/verify.py:17018-17021`; `AGENTS.md:80`, `:116-119` | That any of them was made, or made correctly. The repository says so itself: `docs/CAPABILITY-MATRIX.md:250` and `docs/CAPABILITY-MATRIX-ROWS.md:2694`. |

**Saving: HYPOTHESIS.** After a change, one gate run re-establishes the properties its rows hold. Without it, a person
would re-read the code those rows cover. No baseline measures that reading. The gate's own cost is MEASURED in 1.1
(827 s and 845 s on the owner's host), and it is a cost, not a saving.

### 2.3 Independent, reusable checks

Expected outputs, second implementations and planted defects are stored once. Most run again only when a person starts a
command. Two parts run in every export the director computes, and a memo hit (2.5) hands back the result of an export of
the same text that ran them: the art checks' `verify` (`art/director.py:279-281`) and, for a scene with movers, the
twin's mover table (both below). "Independent" means separately written, not written by someone else: one author wrote
every twin (`art/director/conform.rs:13`; `docs/GHOSTS.md`, G23).

| claim | class | anchors | does not establish |
|---|---|---|---|
| Every export the director computes runs `art/check.py`'s `verify`, which is written apart from the exporter (a memo hit, 2.5, hands back the checks' result of an export of the same text). It recomputes the reach ceiling (REACH-1) and compares it cell for cell with the scene's. It also requires that the rules-3 version, phase unit and body that `graybox/web/sim.js` and `graybox/tick_ref.py` declare agree. At an evaluation, a failed check, except the lineage row the director drops, makes the verdict REFUSED (CHECK-FAILED), and a REFUSED evaluation is never admitted. | ENFORCED at every evaluation, from the command line and from the studio (the studio evaluates again before it admits); an admission acts on the verdict recorded at evaluation | `art/director.py:279-281`, `:288`, `:913`, `:920`, `:1080-1081`; `art/check.py:110-112`, `:294-297`, `:304-319`, `:329`, `:437`, `:439`; `art/director/scope.py:50`, `:252-254`, `:258`; `art/director/contract.py:44-56`; `art/studio.py:1883` | That either reach computation is right: one author wrote both, with the same arithmetic operation for operation (`art/check.py:110-112`). Any comparison of the two simulations' behaviour: only the constants each declares are compared, read from their sources by pattern. That the checks of other exports are acted on: the base's (`art/director.py:876`) and a command-line admission's re-export (`:1105`) are discarded, as is the row "the lineage binds every input" (`:288`). |
| The Python reference is judged against all 97 stored vectors, each on the exact output its kind defines. A mismatch makes `vectors` exit 1 and fails the director self-test's first row. | IMPLEMENTED: refuses inside `vectors` and the director self-test, which a person runs | `art/director.py:1508-1551`, `:1554-1556`, `:2897-2899` | That the expected outputs are right. `vectors.json` itself records no provenance (its note at `:618`), but its writer says they "were written by the Python reference and read through by hand" (`art/director/vectors_source.py:9-10`). So for every output the reference computed, `vectors` holds the reference to its own earlier output: a regression check, not an independent one, and the Rust implementation's agreement (next row) is agreement with that output. That it ran for any change: no gate row, admission or other path the work takes calls it. |
| A std-only Rust implementation reads `vectors.json` with its own reader and reproduces every expected output, byte for byte. | IMPLEMENTED: refuses inside `conform`, which a person compiles and runs | `art/director/conform.rs:4-14`, `:1053-1054` | That it runs: no tracked code compiles or runs it. `art/director/inverse/0254-spec.md:425` says so. |
| The 65 pre-0254 vectors are pinned byte for byte to their 7dee210 form. A copy whose expectations were regenerated to fit the code is refused. | IMPLEMENTED: refuses inside the director self-test (row GR0) and `inverse_freeze.py check`, each of which a person runs | `art/director/inverse_freeze.py:276-278`, `:482`, `:514`; `art/director/inverse_rows.py:229-246`; `art/director.py:1827-1828` | Protection of the 32 intents appended in 0254, beyond their frozen verdicts. That the pinned bytes are right, only that they did not move. |
| The graybox has references written from its rules documents: `tick_ref` (RULES-1), `bot_ref` (WALK-1) and `ort_ref` (ORT-1). Each holds the browser's trace to its own reading and names the first field that differs. `rules_ref` is a second implementation of `sim.js`'s own arithmetic. The twins share code: `tick_ref` takes its sine, cosine and atan2 from `rules_ref`, and `bot_ref` takes its atan2 and hypot from it. `bot_ref` advances and snapshots its states with `tick_ref`'s tick and snapshot writer. `ort_ref` plays, snapshots and hashes its rules-2 states with `tick_ref`'s. `tick_ref verify` makes its walk with `bot_ref`. A defect in `tick_ref`'s tick or snapshot is shared by `bot_ref`'s and `ort_ref`'s checks. | IMPLEMENTED: each refuses inside its own command, which a person runs | `graybox/tick_ref.py:19-27`, `:68`, `:1109-1113`; `graybox/rules_ref.py:4-5`; `graybox/bot_ref.py:17-18`, `:47`, `:57`, `:397`; `graybox/ort_ref.py:28`, `:157`, `:341-342` | That the browser's engine is right. Any cross-browser or cross-platform determinism. That the three references are independent of one another: `bot_ref` and `ort_ref` play `tick_ref`'s tick. |
| Holding a browser to the references takes two steps: `graybox/trace.py run` writes a trace, and a person runs the reference's check on it. For the tables (`--ort`, `--rules2`, `--rules3`, `--cases`) trace.py prints that check's command. For the tick trace it prints only a command that compares the trace with another trace; the reference's check (`tick_ref.py verify`) is named in AGENTS.md. | OPERATOR | `graybox/trace.py:514`, `:521`, `:530`, `:353`; `AGENTS.md:83-87` | That this was done for any change, or on which browser. |
| Here the tick twin's code is used, not compared with `sim.js`'s; the art checks' `verify` (the first row) compares only the twin's declared rules-3 version, phase unit and body with `sim.js`'s, read from both sources as text. `tick_ref.Mover`, the twin's table of what rules 2 allow a mover to be, runs inside every `dress.export` of a scene with movers, and a mover outside that table is refused: some cases by dress.py's own reading first (among them a box with no extent and a policy it does not know), the rest by the twin (`MoverRefused`, raised as the export's `ArtError`; dress.py's own reading checks none of a unique id, speed within len or the tunnelling bound). Through the director, a memo hit (2.5) does not run it again: it hands back the result of an export of the same text that ran it, and a refused export is never kept. `tick_ref.tick3` runs in ART CHECKS' reach witness, which runs only when `python art/check.py` is run with no brief named. `tick_ref.tick3` also plays both sides of every preview in motion the studio makes; no verdict, order or admission reads the preview's fingerprints, which are advisory. | ENFORCED on every computed export with movers; for the reach witness, IMPLEMENTED: it refuses inside that one command, which a person runs; for the preview in motion, IMPLEMENTED: it runs when a person asks for a preview, and nothing acts on its result | `art/dress.py:569`, `:587-588`, `:605-606`, `:612-615`; `graybox/tick_ref.py:479`, `:499-500`, `:505-509`; `art/director.py:199-200`; `art/check.py:304-319`, `:329-331`, `:439`, `:937-986`, `:1079`, `:1085-1086`; `art/motion.py:36`, `:115`; `art/studio.py:2057` | A check of the browser, or of the twin's behaviour against `sim.js`: the uses run the twin, and the art checks' `verify` compares only the two sources' declared rules version, phase unit and body, never their behaviour. That the reach witness ran for any change: no evaluation, admission or gate row calls it. |
| The only expected values that stand apart from both twins are those a person wrote down rather than took from either program: rules 2's and rules 3's cases, worked by hand with their working; most of ORT-1's, "fixed before either program ran"; the input contract's table of required outcomes (each step admitted, or refused with its category; no working is recorded, and the state an admitted step reaches is held only between the two programs, apart from three cases whose `same_as` requires each to end where another named case ends, a relation each program checks against the table); and 0254's 40 vectors marked by hand, frozen before the code they govern. | OPERATOR (a person's working, done once and recorded) | `graybox/web/rules2_cases.json:6`; `graybox/web/rules3_cases.json:6`; `graybox/ort_ref.py:13`; `graybox/web/input_cases.json:13`, `:76`, `:78`; `graybox/tick_ref.py:1553`; `graybox/web/sim.js:649`; `art/director/inverse/0254-spec.md:11`, `:403` | That the hand working, where recorded, is right, or that the input table's required outcomes are. Which came first for rules 2 and 3: each case file was committed with both its implementations. A hand-worked value may later be corrected, with its working (`AGENTS.md` section 4). |
| R5 runs four suites in full at the base and at the head, and reads only their planted-defect rows. It exits 1 when a plant the old checker refused now passes or is gone, or when a suite of the new checker stopped early. An early stop of the old checker is printed and does not fail the run. | IMPLEMENTED: refuses inside `rung.py plants`, which a person runs | `tools/rung.py:388`, `:403`, `:450`, `:457-461`, `:470-475`, `:488-495` | Plants outside those four suites (the tick reference's, GLUE's, CERT's, the page tests'). A failing row that is not a plant row, or a suite's own verdict: R5 reads a suite's exit status only to tell whether it crashed. That anything calls it: on 0266 a driver a person wrote called its functions directly. |

**Saving: HYPOTHESIS.** Replaying 97 stored outputs, or a trace against a reference, should cost less than working the
expected results out again after each change. No baseline measures it. The second implementations and R5 add work by
design. Their value is that a regression is caught; they are not meant to save time.

### 2.4 Layered verification

Code orders checks from structural to costly only inside one command or one admission. Across commands, the order
from cheap to costly is an order a person follows.

| claim | class | anchors | does not establish |
|---|---|---|---|
| `tick_ref.py verify` holds a trace at its door before playing any tick. A trace of the wrong form (its rules-1 section, or its `inputs_from`), and whose map converts here, gets a VERIFY-FORM FAIL and no row after it (`:1358-1363`); VERIFY-MAP is written before it (`:1468`) and may fail as well. If the map cannot be converted, VERIFY-MAP fails and VERIFY-FORM is not written (`:1043-1045`, `:1469`). A trace that is not JSON, is not VERDANDI-TRACE 1 with a rules-1 section, or names no map is refused before the door by `SystemExit`, with no row (`:1023-1029`, `:1037-1038`). A map that cannot be converted plays nothing. A run is played only if its start and inputs are exactly the ones the host made. | IMPLEMENTED: refuses inside that one command, which a person runs; nothing calls it but its own `main` (`:2796-2797`) | `graybox/tick_ref.py:1358-1363`, `:1415-1416`, `:1469-1472` | Cheapest-first: the map is converted (`:1040`) before the form is checked. A map whose manifest does not match is reported FAIL and still played (`:1047-1051`). |
| An evaluation refuses a wrong brief, an undo that is not the stored inverse, an intent that cannot be applied, and a refused layout, all before the candidate is exported and checked. | ENFORCED in every evaluation | `art/director.py:884-885` (brief), `:890-894` (inverse), `:896-899` (intent), `:903-909` (layout), `:913` (the candidate's export after them); `:876` (the base exported first) | Cheapest-first: the base is exported first, and an undo replays the ledger before its inverse is judged. |
| An admission refuses before its first durable write (the stills, `art/director.py:736-739`). `admit_checks` runs before the content lock. Under the lock come the moved head, the shared map, `held_head` and the binding gate. | ENFORCED at every admission | `art/director.py:681-684`, `:714-732`, `:1033`, `:1056-1113` | A cost order: the purpose is that nothing is written on a refusal. The studio makes its own checks first (`art/studio.py:1724`), then appends the evaluation event (`:1729`) before `cmd_admit` runs `admit_checks`. An admission refused after that append (for example by `admit_checks`, the fence, the shared map, `held_head` or the binding gate) leaves that event behind. One the studio's Admit refuses first (for example not drawn, no still, stale, not CLEAN, strict, flagged still) leaves no evaluation event. Undo appends the inverse's evaluation before it checks that the inverse is CLEAN (`art/studio.py:2331-2332`), so an inverse that is not CLEAN leaves its event behind. Recovery of an earlier dead writer may write first (`:715-717`). |
| The gate is exhaustive, not layered. All 251 rows are called whatever the earlier rows returned or raised as an `Exception`. The only skip is the environment's (no rustc). A `SystemExit` or `KeyboardInterrupt` in a row ends the run there with no verdict line, and with an exit status that is not the gate's (2.2). | IMPLEMENTED: the gate's run, which a person starts | `verify/verify.py:489-490`, `:529-531`, `:16752-17021` | That rows are independent. Some read the state of earlier rows (a built shell, the rows already run), so an early failure can turn later rows red. |
| The full art check does not stop at a failure. By his 0251 ruling it runs the browser suites one at a time; it runs them in BROWSER's order, and a free worker takes the next one first whenever none is running. It starts the other suites longest first, and it fails if any suite fails. | IMPLEMENTED: inside that one command, which a person runs; no code calls `art/selftests.py` | `art/selftests.py:283` (a stop on failure exists only as the plant at `:335-336`), `:86-90`, `:279-280`, `:306-308`, `:295`, `:392` | Any wall-clock gain from its parallel pool: no off-against-on baseline exists. |
| The order across commands is prose. The batch protocol runs each item's targeted checks at its own commit, then the full check, the plants comparison and the gate at the batch's last commit, recording `Gated-Tree:`. The landing check follows `git am`. One batch's sheet writes that order out as five steps. | OPERATOR | `docs/BATCH-0.md:51-54`, `:70-72`; `AGENTS.md:164-174`; for one batch, `art/fixtures/locality/SHEET.md:164-172` | That the order was followed for any change. That a defect caught early would also have been caught by the gate, or the reverse. |

**Saving: HYPOTHESIS.** Running a targeted check first should surface most defects in seconds or minutes, rather than
after a full gate run, which took 827 s and 845 s on the owner's host on 2026-11-07 (1.1; `AGENTS.md` gives about 25
minutes in the build container). No baseline compares the two orders, and the timings in 1.2 are not clean enough to
make one.

### 2.5 Persistent evidence

Keeping a result is one thing, and reusing it as computation is another. In this tree, the export memo is the one
demonstrated case of reused computation with an off-against-on baseline (his words: "The export memo remains the one
demonstrated case of reused computation with an off-against-on baseline."). None of the other comparisons listed in
section 3 is of reused computation; section 3 lists three that compare one way of verifying with another. Replay takes
each admission's recorded parts as written and does not export them again: that is provenance it trusts, not saved
computation. Everything else in the table below that is kept establishes provenance (his words: "Persistent evidence is
not automatically reused computation."). Outside the table, the studio server also keeps results in memory and uses them
again, none of them measured and no saving claimed; among them: the worlds list's read-back of each world
(`Hub.inspect`'s replay), handed back while a key of its files' stamps and its ledger's last line is unchanged
(`art/play.py:1509-1511`, `:1532-1549`); each scene's outline, by its sha256 (`:1648-1662`); and each served scene's
parsed form, by its sha256 (`:1915`, `:1920-1928`).

| claim | class | anchors | does not establish |
|---|---|---|---|
| Every `Workspace.export` calls `memo_call`. Unless the memo is switched off (`VERDANDI_EXPORT_MEMO=0`) or a durable plant is set, when every export is computed and nothing is kept, it goes through an exact in-memory memo. A kept result is handed back, as a copy, only while every file the export opened and every folder it listed hash the same, and every path it did not find is still absent. It keeps nothing from an export that wrote, raised, opened or listed by a descriptor, or saw a read file's stat change during the export. | ENFORCED in every export while the memo is on, in one process | `art/director.py:107-117`, `:120`, `:171-177`, `:180-193`, `:204-222`, `:261-267` | That a hit always equals a recomputation. The memo's own header names a blind spot: a test of whether a file exists that opens nothing (`:115-117`). A rewrite during the export that leaves mtime, size and inode unchanged is not seen. That the memo is used: some self-tests switch it off. The memo lives in one process, at most 24 entries: two command-line runs (`evaluate`, then `admit`) share nothing. |
| **MEASURED:** the memo off (`VERDANDI_EXPORT_MEMO=0`) against on. Ten requests each way of one prompt at one head, three candidates each, in the build container at 0237's tree, with a private harness that is not committed. The record gives no date for the run; the entry was first committed in `4d16dae` (2026-10-15), which bounds the run from above. p50 in ms: one candidate's evaluation 884 → 68; the whole request 3,187 → 350; the admission 1,873 → 76; the undo 2,454 → 83. The page's own build of the head does not go through the memo, and it did not move: 411 → 402. The memo counted 177 hits and 4 misses. | OPERATOR (a recorded run; nothing re-runs it) | `docs/ROADMAP.md:4626-4645`; the same harness on another region, `:4682-4686` | A general speedup, or one on the owner's host (`:4650`: "NOT_MEASURED: his machine."). The cost at this tree: `art/director.py` has changed since 0237. A mixed workload: after the first request every export hit, so this is the best case. The two tables come from one harness and corroborate each other; they are not independent. |
| The memo's correctness is held by rows that compare its result with the export made with the memo off, with four plants. | IMPLEMENTED: refuses inside the director self-test and `memotest`, which a person runs | `art/director.py:2052-2055`, `:2133-2135`; `art/play.py:4304-4305` | That the memo is on in a given host: FACADE's row passes when the memo is off. |
| A command-line admission decides from the evaluation's stored ADMISSION-0 record, bound to the current head. It exports the base and the candidate again and discards those checks. | ENFORCED at the command line's admission | `art/director.py:1068-1071`, `:1086-1088`, `:1105`; `art/director/contract.py:167-170` | Saved computation: the exports still run. The studio evaluates again in full before it admits (`art/studio.py:1883`). |
| Replay rebuilds the art text by applying each admitted revision again. It takes each event's recorded parts, head and certified checks as written, without exporting again. `held_head` runs it under the content lock before every evaluate, admit and approve append (`:641`, `:729`), and once when an evaluation command starts, before any input is read (`:936`), so it also precedes a `refuse_input` event, an input that could not be read as an intent (`:943`). A `refuse` event, a chooser's refusal of an evaluation (`:1139`), and a genesis are appended without it. | ENFORCED on those appends | `art/director.py:616-621`, `:641`, `:729`, `:936`, `:1286-1315`; `:1139`, `:1185` | That the recorded parts are true. A ledger line written consistently by someone else passes replay. Replay holds provenance; it does not verify the world again. |
| The ledger's hash chain (each `prev` the sha256 of the line before) is checked only by `led.chain`. Outside self-tests only `cmd_verify` calls it: in an import's stage and commit, and in seeding's stage alone (seeding puts its staging in place by a rename, never through the commit's check); in `Hub.inspect`, which the launcher's look, the worlds list and the history view run; and in the `verify` command and self-tests. Some self-test rows also call `led.chain` directly on their own fixture ledgers (`art/director.py:1888`, `:1891`, `:2383`, `:2460`; `art/director/inverse_rows.py:320`; `art/play.py:3247`). The 0254 freeze check's call (`art/director/inverse_freeze.py:322`) is reached only under 7dee210's `director.py`, not at this tree. | ENFORCED on an import's stage and commit, and on seeding's stage (seeding has no commit check: it puts its staging in place by rename); IMPLEMENTED, nothing heeds its result, in `Hub.inspect`, which the launcher's look, the worlds list and the history view run on studio requests and which only reports verified or not; IMPLEMENTED, run only when a person starts it, in the `verify` command and the self-tests; never on the admission or append path, which reads with `led.read` | `art/director/ledger.py:31-46`, `:106-116`; `art/director.py:1031`, `:1365`; `art/play.py:823`, `:844`, `:1037`, `:1297`, `:1479`, `:1482`, `:1544`, `:2122` | That a ledger is intact at the moment of an admission. |
| The gate checks the preregistered entries, `verify/reasons.json`'s bytes and the ledger excerpts that register cites again on every run, and keeps nothing between runs. | IMPLEMENTED: refuses inside the gate's run | `verify/verify.py:1368-1374`, `:12396-12398`, `:12663-12666` | Reuse: these are checked again every time, never trusted. |
| The 0253 and 0254 freezes are held to their sha256 by freeze checks a person runs. `art/references.jsonl` has no sha256 of its own: ART CHECKS compares each brief's exported scene with the scene sha256 its line records, and the file itself is checked only for its form and for keys that repeat. | IMPLEMENTED: refuses inside those checks, which a person runs | `art/director/binding_freeze.py:304-305`; `art/director/inverse_freeze.py:115-116`; `art/check.py:839`; `art/quality.py:503-537` | Immutability. No code holds a freeze's record line, so a frozen file rewritten with its record line passes. No evaluation compares a scene with `art/references.jsonl` (`art/director/contract.py:46-56`). |
| An admission's certificate is derived from the ledger, by the studio only: at its admissions and undos, and at its start for any admission without one. A kept certificate is reused only while it is bound to its event. The certificate decides nothing. | IMPLEMENTED: nothing heeds it | `art/studio.py:1745`, `:2412`, `:2443-2448`, `:2472-2483`, `:2506-2509`, `:2529-2530`; `art/play.py:2377` | Saved computation: the undo's verdict comes from two replays, and an admission stands when its certificate cannot be made. |
| The `Gated-Tree` trailer ties a landed commit to the tree the gate ran on twice. Only his hand-run landing check reads it, and its effect is to stop a landing. | OPERATOR | `AGENTS.md:165-174` | That any check is skipped because of it. He still runs his own checks after `TREE HELD`. |

**Saving:** MEASURED for the export memo, inside one long-lived process, in the build container, at 0237's tree, in its
best case. NONE claimed for everything else in this table, which is provenance. One smaller saving is HYPOTHESIS:
inside one command-line admission, two of its three exports of the base should be memo hits. It is not measured.

### 2.6 Separation of generation and admission

A model proposes and the host decides. The parts that hold this in code are on the request and admission paths of the
art studio, and on the design tool's admission, which `design/design.py` binds to its previewed digest. That a person,
rather than a program, takes the admitting step is an operator rule.

| claim | class | anchors | does not establish |
|---|---|---|---|
| A provider's answer is read whole or refused whole. Each candidate is rebuilt as an intent whose letter, base, brief and prompt are the gateway's. The director evaluates it at the current head, a refused candidate is not drawn, and candidates are ordered by host facts only. | ENFORCED on every studio request | `art/studio.py:393-396`, `:499-507`, `:858-863`, `:1546-1547`, `:1585-1586`; `art/director.py:920` | That the model's revision or declared scope is truthful (CLEAN holds a change to what was declared). The provider's raw rationale and its self-reported name and model reach the advisory impact report (`art/studio.py:1582-1583`). |
| A studio Admit press refuses a candidate that is stale, not CLEAN, without its still, or, if the request is strict, outside its region. It then appends the evaluation and runs the director's `admit_checks`, and under the lock the fence and the binding gate, all before the admission's first write. Undo needs no still; it requires the exact inverse. | ENFORCED on the studio's Admit and Undo | `art/play.py:1887-1890`; `art/studio.py:1729`, `:1743`, `:1874-1932`, `:2411`; `art/director.py:681-684`, `:714-732`, `:1080-1088` | Who pressed. That the candidate does what was asked. None of it runs in the gate's 251 rows. |
| The shipped Claude Code adapter runs `claude` with its tools off, in a fresh temporary folder holding only the system prompt file. It kills the process when the first init event lists a tool other than StructuredOutput, or omits the list. | ENFORCED on every request, only when that provider is configured | `art/providers/claude_code.py:84-88`, `:96-103`, `:133-141` | That the real CLI lists every tool it would honour: the self-test uses a fake. An empty tool list passes. With no init event the adapter never checks the tools and does not stop `claude` (`:148`); it runs until it exits, or until the gateway ends the provider on a timeout (240 s in the shipped `art/providers/claude_code.json`), a cancellation or too much output. Other providers. |
| A provider is bounded in time, output and cancellation, on every platform. When a bound is hit on Windows, every process in the provider's job is ended and waited for, up to 30 s, and the error raised counts any left. On POSIX the provider's process group is sent SIGKILL and only the provider itself is waited for; that path has not been measured since 0256. | ENFORCED in every provider run (the bounds); the job's end, wait and count on Windows only | `art/studio.py:262-290`, `:360-377`; `art/studio_app.py:136-139` | A sandbox: a provider gets no filesystem or network restriction, and its descendants are not contained after a normal exit. A write to the world's files is not prevented. It is detected when the next evaluation, admission, approval or refusal of an input is held to the ledger's head, which is refused LEDGER-UNLOGGED (`art/director.py:619-626`) until a person records the change with `rebase`, unless the ledger was brought to it too. |
| That a person authorizes an admission. The studio's only proof of a person is the page token, which the page embeds for any request naming the local server. The command line admits with no token, a free-text `--chooser`, and `--accept-leakage`. | OPERATOR | `art/play.py:2135-2137`, `:2296-2298`; `art/director.py:2925-2927` | That no local process takes the token or calls the command line. That risk is argued from the code, not measured. |
| Which provider runs, and so whether it is tool-less, is the operator's configuration. | OPERATOR | `art/studio.py:245-246`, `:301`, `:310` | That a configured provider has no side effects. |
| A still is required, and the host reads its detectors. When a studio Admit press passes every earlier check, BINDING-0's gate checks that the scene the page declared for the still equals the candidate scene from the admission's own evaluation (`art/studio.py:1883-1888`), and refuses BINDING-MISMATCH or BINDING-UNKNOWN. Nothing compares the still's pixels with the candidate. The command line's `--still` is bound to nothing, because its admission passes no gate. The detectors flag, and a person judges. | ENFORCED at every admission that is not an undo (the still's presence and its detectors, ADMISSION-0, `art/director.py:1086-1088`); OPERATOR (the picture and its judgment); the studio's scene binding is ENFORCED, see the Admit row | `art/studio.py:1659-1685`, `:1732-1742`, `:1765-1766`; `art/director.py:731-732`, `:2925-2927`; `art/director/contract.py:60-61` | That the pixels are the candidate's: the page declares the kept scene. That a command-line still is of the candidate. That the picture is right. |
| In the design tool, `admit` refuses without a pending, admissible preview at the same head, and passes the previewed digest to the shell, which refuses ADMIT-PREVIEW on a mismatch. A gate row holds that refusal. The acceptance itself, a person reading the preview, is no code's. | ENFORCED on every design admission (the binding); IMPLEMENTED for the gate row that holds the refusal (it refuses inside the gate's run, which a person starts); OPERATOR (the acceptance) | `design/design.py:499-514`; `shell/designevent.rs:305-310`; `verify/verify.py:14525-14528` | That the preview was judged. That a direct shell call without `--previewed` is bound to any preview. |

**Saving: HYPOTHESIS.** Because no model output is trusted, review can shrink to what the contract lists as never
checked (`art/director/contract.py`, `NEVER_CHECKED`). And binding admission to a previewed digest should spare a person
a second review of the bytes after accepting the preview, since the shell refuses any other bytes or reached head
(ADMIT-PREVIEW) and any other parent (ADMIT-ANCHOR). No machine check is saved: the preview is the admission's own run
ended early, and the admission runs every check again (`shell/designevent.rs:35-36`, `:282-372`;
`design/design.py:514`). No baseline exists for either. The separation adds checks; its first purpose is safety, not
speed.

## 3. Speed savings by design: demonstrated against intended

| mechanism | demonstrated reuse, with a baseline | intended, unmeasured (HYPOTHESIS) |
|---|---|---|
| narrow change scope | none | less to review and judge per change; not less gate work |
| executable rules | none | a gate run instead of re-reading the code its rows cover |
| reusable checks | none | stored outputs replayed instead of worked again |
| layered verification | none | most defects found before a full gate run (827 s and 845 s on the owner's host, 1.1; one machine, not a general figure) |
| persistent evidence | **the export memo only** (2.5): off against on, the build container, 0237's tree, its best case | inside one command-line admission, two of its three base exports should hit the memo |
| generation apart from admission | none | review limited to what is never checked; no second human review of the bytes after a previewed acceptance (the shell still re-runs every check at admission) |

The repository records other comparisons too. Three of them compare one way of verifying with another (an order, a check
or a content function). None is reuse:

- **Gate passes in parallel** (MEASURED after, approximate before, in the build container, `docs/DEVNOTES.md:298-303`):
  three gate passes run at once against one after another. The same work, scheduled differently.
- **STRICT-0's added cost** (MEASURED, in the build container, `docs/ROADMAP.md:4750-4754`): a request not strict
  against strict. A cost a check adds, not a saving.
- **DSC-0, a tree commitment, against the incumbent content hash** (MEASURED in the build container,
  `docs/ROADMAP.md:4482`, `:4500-4505`, and again on the owner's host in his run of 0234, `:4513-4516`): no measurable
  gain at the kernel's world size. A gain was measured only on larger copies of
  the present layout, sizes the kernel refuses. It was not adopted (`:4510-4511`; his ruling, `:4516-4518`).

## 4. Limitations

- **The gate runs all 251 rows on every run** (DESIGN). No change, however small, shortens it. Any saving from a
  narrow change is in review, and is a hypothesis.
- **The rowset comparison is manual** (DESIGN: `verify/verify.py:17018-17021` prints the rowset and compares it with
  nothing). The skip count and the byte identity of two runs are read the same way. The fences hold the existing rows'
  names and order, not a count. An appended row changes the printed rowset and row count, and only a person comparing
  them with `74db4c8d78625af5` and 251 catches it. A row body weakened under its own name changes neither, because the
  rowset hashes names only. Some gate rows hold parts of row bodies as text: reasoncourt-source requires each registered
  judging statement to stand, as text, in the function its register names (`verify/verify.py:12672-12686`), and
  hermeneutics-fence holds DESIGN-IR/DIFF-0's two widened rules as text, and that the comments marking the changed lines
  stand in those two rows (`verify/verify.py:16691-16699`). They show that the words are still there, not what the row
  does. Some rows are also held by what they did in the run: reasoncourt-watch and mintwatch-watch require each
  registered ending and mint to be heard its registered number of times (`verify/verify.py:12801`, `:13563`), so an
  early return that skips a required ending or mint turns the gate red. All of these act only when someone runs the
  gate. Against a weakening that leaves the held words and the counted endings and mints standing, and outside
  REASON-COURT-0's six rows, whose text mintwatch-fence pins by sha256 in the same file
  (`verify/verify.py:13751-13754`), only a person's review of the change stands, with the classifier's rung D when
  someone runs the classifier (`verify/verify.py` is one of its roots, `tools/rung.py:55-65`). The gate does not
  guarantee the expected rowset on its own. Putting that comparison in code is future work, by the owner's word.
- **Exclusion of two starts between processes is argued, not measured.** Two starts of one ledger are kept apart by
  the operating system's file lock (`durable.locked`; DESIGN). The race court tests two starts only as two threads of
  one process (`art/director.py:2482`). Its two-process trials cover appends, the chain whole in 3 of 3 trials with
  their no-lock plant caught in 3 of 3 (`art/director.py:2491-2506`), and recovery refused `LEDGER-BUSY` under a held
  lock, not starts (MEASURED in the landing's race court). A two-process race test of starts is future work, by the
  owner's word.
- **Concurrent work makes overlapping timings unsuitable as clean benchmarks** (the owner's limitation). The landing's
  full suite shared the machine with research for about five of its minutes, MEASURED approximately as in 1.1: the
  research's start was read when the workflow was launched and its end when it reported complete, 281 s later. That
  overlap's effect on any timing is not measured. A timing taken beside other work is not a benchmark, and none in this
  note is used as one (1.4, section 3).
- **One machine, few runs** (MEASURED, on the owner's host only). No figure measured on the owner's host is an average
  or a median of repeated runs (2.5's p50s are medians of ten requests each way, in the build container), and the suite
  times in 1.2 vary run to run on the same tree. PREVIEW-STUDIO, the suite that holds the timing row, passed in 3 of the
  12 full suites completed on 2026-11-06 and 2026-11-07, all 3 on tree `63796a26` (1.4).
- **Most checks run only when a person runs them** (DESIGN). The gate, every art suite, the classifier, R5, the tick
  reference and the Rust conformance all start by hand, and the repository has no automatic pipeline. That is why so
  much of section 2 is IMPLEMENTED: those checks refuse when they run, and a person decides that they run.
- **Counts in other documents lag** (MEASURED: the race court's output on this tree). The race court prints 36 cases.
  `AGENTS.md:91` and `art/STUDIO.md:1057` still say 34. This note changes neither.

## 5. What would change these findings

- A measured run of the gate or the full suite alone on a quiet machine would replace the timings in 1.1 and 1.2 for
  that machine.
- An off-against-on measurement of any HYPOTHESIS above would move that line to MEASURED or refute it. Examples are
  review time on narrow patches against broad ones, or a command-line admission with its memo hits against one without.
- A caller found on an ordinary work path, where the check runs automatically rather than through a separately started
  command, could move an IMPLEMENTED item to ENFORCED. An OPERATOR item moves only if code takes over the relevant
  human comparison or decision. A caller found missing for an ENFORCED item would move it down.
- Any anchor that does not hold its claim at tree `63796a26` falsifies that claim as written.
