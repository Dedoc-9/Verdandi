<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Capability matrix — Phase 0 of the engine and studio specification (2026-10-16)

On 2026-10-16 the owner pasted two documents. The first is an engine and studio specification built on a canonical
relational world (here **SPEC1**). The second, which he introduced with "in other words", is a corrected brief (here
**SPEC2**, the operative one). SPEC2 asks first for an inventory: a capability matrix graded `EXISTS-TESTED`,
`EXISTS-UNVERIFIED`, `PARTIAL`, `MISSING` or `CONFLICTS-WITH-SPEC`, a baseline gate report, and a patch plan *"before
broad changes"*. This file is that inventory, read at HEAD `6af1d9f`.

It also does what the roadmap records as agreed for the next product rung. *"The dashboard a consolidation of the
shell the studio already has, audited against his five areas before anything is built"* (docs/ROADMAP.md:5050-5051).
The five areas are not written in the repository. Here they are read as SPEC2 §11's layout (INFERRED): the
viewport; the world browser and outliner; the inspector; the drawer (candidates, queue, validation, evidence); and the
summoned Director. The global strip is added as a sixth.

**Status: an audit. Nothing was built by it.** No source, test, row, registered entry, pinned file, reference or
ledger changed in making it. Two files were written: this one, and its generated rows,
[`CAPABILITY-MATRIX-ROWS.md`](CAPABILITY-MATRIX-ROWS.md) (704 rows, with their evidence). He agreed the order of §7 the
same day (*"Agreed on the order. Build 0245 (LEDGER-SAFE-0) here, as a patch I apply"*), and 0245 builds its first
patch and brings these two files with it (docs/ROADMAP.md).

## 1. How it was made

- **The checkout.** `main` at `6af1d9f`, which is `origin/main` after his push `e1fb9f4..6af1d9f`. Two files were
  untracked and left alone: `art/ledger/harbor-lift.tags.json` and `art/ledger/plaza-night.tags.json`.
- **Readers.** Eleven agents read the tree, one per subsystem:
  - the Rust core;
  - the gate and RUNG-0;
  - the graybox;
  - the art layer's admission algebra;
  - the studio's back end;
  - the dashboard;
  - rendering and evidence;
  - procedural geometry and marks;
  - the Director;
  - the design tool, principles and decisions;
  - SPEC1 against the rules.

  Each wrote one row per capability its sections of SPEC2 name, with the `file:line` it opened.
- **Skeptics.** Each reader had two:
  - one opened the test behind every `EXISTS-TESTED` or `PARTIAL` row and asked whether it would fail if the
    capability broke, and whether the gate, `art/selftests.py` or an AGENTS.md §4 check runs it;
  - the other searched the whole tree for what every `MISSING`, `EXISTS-UNVERIFIED` and `CONFLICTS` row said was
    absent, and checked each cited rule.

  A third skeptic checked the dashboard's areas and steps.
- **The critic.** It named 8 gaps and 8 contradictions, and 16 more agents answered them. That makes 51 agents.
  - Their resolutions are applied to the rows: 54 rows took a resolved grade.
  - The skeptics corrected 87 reader grades.
- **`EXISTS-TESTED` means two things together:**
  - a test would fail on a defect;
  - something that ran at HEAD runs it: the gate, or a suite of `art/selftests.py` (his log
    `art/build/selftests/20261016T162615Z.log`).

  A check of its own with no run on record at HEAD is said so in its row.
- **What was run, and where.** All of it was on his machine, by the agent writing this:
  - the gate, once (§2);
  - `art/director.py verify plaza-night`, then `evaluate` and `rebase`, in a `git archive HEAD` export in a scratch
    folder, never in the checkout (§5, F-1);
  - a count of RUNG-0's plant keys from his self-test log (§5, F-6).

  Two agents ran snippets outside the repository:
  - `apply_revision` extracted and round-tripped (F-8);
  - `int('1'*5000)` on Python 3.14.5 (rows F7.*).

  Everything else is **VERIFIED BY READING**, and a row says when it is.
- **How far a grade can be trusted (MEASURED).** The first run stopped with nine agents unfinished (a usage limit).
  The second ran every skeptic again over the same reader rows. In the seven sections whose skeptics finished both
  times, 26 of 284 shared rows came out with another grade:
  - 14 moved between `EXISTS-TESTED` and `PARTIAL`;
  - the rest moved one step elsewhere.

  Read a single row's grade as ± one step. The findings in §5 are those checked here by hand, or by two agents that
  agree.

## 2. The baseline (SPEC2 §3)

| what | where | command | result |
|---|---|---|---|
| the gate | his machine, run here, started 2026-10-16T17:12:09Z | `PYTHONHASHSEED=0 PYTHONUTF8=1 python -B verify/verify.py` | `GATE PASSED`, `RECONCILE rowset 74db4c8d78625af5 251 rows / 0 fail / 0 skipped`, exit 0. 1,074 s wall, with the inventory's agents running beside it, so this is not a timing of the gate. Python 3.14.5, rustc 1.96.1 (31fca3adb 2026-06-26). Output sha256 `eb2bea34ef89…` |
| the gate | his run before the push | `python verify\verify.py` | the same rows and the same reconcile line (his output) |
| art self-tests | his run, log `art/build/selftests/20261016T162615Z.log` | `python art\selftests.py --repeat 2` | `ART SELFTESTS PASSED`: 24 suites, 156.5 s and 196.6 s wall |
| RUNG-0 | his run, with the classifier he held before this push | `classify HEAD~1 HEAD`, `plants HEAD~1 HEAD`, `tools\rung.py selftest` | rung D; `PLANTS HELD`, 116 and 116; `RUNG SELFTEST 19/19` |
| graybox checks, `design/test_design.py`, `conform.rs` | — | — | no run at HEAD found on record. The graybox's last host results are from 2026-10-14; `graybox/` has not changed since `f17a4b9` |

## 3. The matrix by SPEC2 §17's fourteen areas

The grades below are this file's synthesis of the rows. Each area's rows are in the row file, under the readers
named.

| § 17 area | grade | what holds it | what is missing |
|---|---|---|---|
| persistence, migration, crash recovery | PARTIAL | Crash-safe commits with planted death points on both layers: the gate's `admit-crash` (8 points), `designevent-crash` (12) and `livesession-recover`; DIRECTOR CRASHTEST (15 cases) and RACETEST (32). The art layer recovers at every start. | **Migration is MISSING on every path**: an unknown version is refused, never translated, and a saved shell session carries no version member. The shell's recovery needs a person to name the journal. Plain writes remain: `workshop/session.rs:383` and `sessionwalk.rs:631` overwrite their only copy; certificates and request lines are written outside the content lock (`art/studio.py:1135-1139`, `1153-1154`); the visual-baseline file has no fsync. |
| stable identity across edits and reload | PARTIAL | Ids are places and statement keys, never renumbered, as SPEC2 §2.6 asks. A gone object's tag never rebinds (studio suite). Shapes go `changed` or `gone`, never moved (marks suite). | A moved or resized object is a new id. Graybox targets are dense ordinals `T%d` by statement order (`graybox/level.py:187`): this is the one place §2.6's rule is broken. |
| atomicity, stale refusal, undo | atomicity and stale refusal EXISTS-TESTED; undo PARTIAL | `designevent-admit`, `admit-anchor`; the director's fence under the content lock; STUDIO-STALE, PREVIEW-STALE | Undo is a compensating intent. It is byte-exact for a narrower subset than 0244 states (F-8), it is bound to no expected child revision, and there is no redo. The page never shows `head_restored`. |
| geo-stability and rebase | PARTIAL, and it covers no world anyone plays | ORT-1 conserves global positions exactly, refuses inexact rebases, and binds a receipt (an own check, not run at HEAD). | ORT-1 refuses rules 3, which every art scene names. Its own O10 measured that a tick does not commute with a rebase. No runtime calls it. The art scene is flat (world-space boxes, no parent or transform), so charts, composition and hierarchy are MISSING. MARK-0's face frames are the one tested local frame. |
| procedural reproducibility and local regeneration | reproducibility EXISTS-TESTED; locality PARTIAL | Export twice; frozen bytes references (check, quality) | Locality is held on one layout revision only. The whole scene is re-exported on every edit, and lamp heights read the whole world's reach ceiling. The hierarchy is world, region, building, side, then bay by floor. A building statement's own refusals are planted nowhere. |
| physics and movement subset, determinism scope | PARTIAL | A kinematic FPS tick in binary64 with every rounding fixed, an independent Python twin, rules 1-3 worked by hand with plants, and the input contract. Cross-engine byte equality was MEASURED once on one map: rules 1 on four engines, rules 2 and 3 on V8 only. | No rigid bodies, solver, capsule, slopes, acceleration, events or blocked-move trace. The gate holds no graybox row; the art suites touch it only through `preview` and `check`. The graybox's own launcher still plays rules 1 (`graybox/web/main.js:13`). |
| navigation and stale cache | PARTIAL | A BFS over cells. The bot's walk file is refused when the map changes (an own check). | There are three reachability models that differ by construction: `check.py`'s BFS, walk-1 and REACH-1. REACH-1 was held against the simulation once, by a container search. There is no navmesh, link or regional rebuild. |
| renderer quality corpus, GPU profiling | MISSING in substance | QUALITY-0 bounds the scene's bytes; detectors on stills; IMPACT-0's counts | **No test ever runs `art/web/scene_render.js`**, and every still in every suite is a synthetic PNG. There is no GPU timer, p99 or pacing measure. The impact model was fitted on SwiftShader at 480×270 and gives negative estimates for small scenes. The renderer has never been timed on his machine. No visual baseline is approved (`art/visual_baselines.jsonl` is absent). |
| studio end-to-end | PARTIAL | FLAGSHIP-0 runs mark, request, candidate, preview, admit and undo over HTTP, with four plants | Never through the page (§4). The flagship world `foundry-yard` never reaches an existing worlds folder, because `seed_worlds` seeds only an empty one (`art/play.py:802-803`). |
| Director permissions, provenance, bounded repair | permissions and provenance largely EXISTS-TESTED; repair MISSING | No tools; the prompt on stdin only; a record chained line to line; dispositions | **The provider writes the scope its own candidate is judged CLEAN against** (F-3). A candidate written at another head is evaluated at the new one (F-4). There is no repair loop, and no token or cost budget. |
| evidence completeness | PARTIAL | Admission level: ADMISSION-0, where a skip is not a pass, and FLAGSHIP-0's stages | Suite level: no harness keeps an expected row set apart from its output (F-6). The gate's expected rowset lives in documents only, and a skipped row still reads `GATE PASSED` (`verify/verify.py:17019`). |
| target-hardware performance | MISSING | The sealed host distributions are of the Rust kernel and the GDI presenter. | No file declares a target profile (nothing names Xbox Ally X or a hardware class). There is no gamepad. The studio's renderer has no frame-time record. |
| recovery with no unadmitted promotion | EXISTS-TESTED for content | crashtest: a pending admission recovers to the parent or the child, never a candidate | The studio's own code promotion (B2) exists only as `studio_txn.py`'s reference model, which no program executes. |
| extension without duplicated authority | PARTIAL | One shell seam for walls; closed schemas refuse the unknown (quality's `doors` plant) | The client glue for walls is written three times. A new statement kind is restated by hand across `dress.py`, `director/`, `quality.py` and `check.py`. |

Counts over all 704 rows: 191 `EXISTS-TESTED`, 54 `EXISTS-UNVERIFIED`, 341 `PARTIAL`, 61 `MISSING`, 57
`CONFLICTS-WITH-SPEC`. The count is not a score (AGENTS.md §6): the rows differ in size and weight.

## 4. The dashboard against the five areas

The roadmap's next product rung is a consolidation. These are the areas as they stand, after the skeptic.

| area | verdict | what exists | what is missing |
|---|---|---|---|
| 1 · viewport and camera | present | The WebGL2 viewport with fly, look, dolly, frame, the brief's views, top and side (telephoto), picking by ray, Measure, overlays, a stats box, and play mode with P and Esc | Any committed test. No orthographic projection. Saved views are lost on reload. No gamepad. |
| 2 · world browser and outliner | partial | A world select in four places (the launcher reads each world back, verified or not); a two-level asset browser by kind in the dock; Mark mode's world and layer lists | A collapsible left panel. An outliner by region, object and parts, with search. Projects. Seven left-navigator items only toast "Not built". The in-page world lists do not say whether a world verifies. |
| 3 · inspector | partial | GET `/object.json`: transform (read-only), materials, collision and why, custom properties (the making line and what it can change); the shape inspector | No edit of transform, geometry, material or dimension, by design so far ("Nothing in the editor moves the world", `art/web/play.js:681`). |
| 4 · drawer: candidates, queue, validation, evidence | partial | Cards (rank, M/C/P, held per shape, strict PASS or FAIL, impact ESTIMATE, verdict, Show, Admit, Reject, Preview), the Ledger tab, the Validate modal and the preview modal | The queue lives in the Director overlay, and validation and evidence are modals. There is no evidence panel: the launcher's Evidence view is "not built" (`art/web/views/evidence.json`). Missing evidence is only partly accounted for, and a disabled Admit gives no reason. Review ▸ Compare outside Mark mode is a dead end. |
| 5 · the Director | present | A drawer (Enter): world, target and pins with their status, tags and shapes, the prompt, Strict, the request's state and disposition, each candidate's verdict, touches and record; a queue for any world | The selection reaches it only once it is the target. Its script is executed by no test. |
| 6 · global strip | partial | The menu bar; context chips (world, revision and verification, source, rules); Build now; play controls; viewport modes | No save status. Undo is in the Director drawer only and there is no redo. No preview state. No project. |

SPEC2 §15's thirteen steps through the UI today:

- **yes:** 3, 4, 5, 6, 7 and 9: select and show the world; submit; an isolated candidate bound to its head; validation
  and preview; both sides at identical poses; admit only by a person's act.
- **partial:** 1, 2, 8 and 10: inspect the workflow; choose a world and a safe edit; show missing evidence; undo and
  verify.
- **no:** 11, 12 and 13: planted failures through the UI; tests from the UI; a report of the diff.

**The finding that decides the plan: no test executes the page.**

- LIVE SELFTEST is "the live loop without a browser" (`art/play.py:1523-1526`).
- The preview and flagship suites post synthetic PNG stills (`art/play.py:3380`, `art/flagship.py:267-268`).
- STUDIO APP's stand-in browser only reads the HTML.
- The page's own hooks (`window.PLAY`, `art/web/play.js:2165`) are called by no file.

So the page side of every area is `EXISTS-UNVERIFIED`. SPEC2 Phase 1's acceptance, *"one existing world completes
the existing candidate flow through UI"*, is unmet, even though the HTTP flow behind it is complete and tested.
Lesson 75 applies: a consolidation of a page no test runs could not be checked.

Smaller findings in the page (by reading):

- An undo's `head_restored` and its certificate are never shown: neither word occurs in `play.js`. A person cannot
  see whether an undo restored the head.
- Compare, and Mark mode's split, draw "Current" from source 0, not the candidate's evaluation base
  (`play.js:2023`; the host's plan names `base: 0`, `art/studio.py:1455`).
- The stats box shows an averaged FPS with no software-timing label.
- The face-frame table is written twice, in `art/studio_marks.py:131-138` and `art/web/studio_ui.js:186-193`, and
  no test compares them.

## 5. Findings that need a repair or a ruling

Ranked by consequence. The grade of each claim is given.

**F-1 · The checkout's plaza-night ledger cannot be evaluated against without breaking it (MEASURED here, in a
clean export of HEAD).**

1. `python art/director.py verify plaza-night` refuses: `UNLOGGED-CHANGE: the head is df8b640defd8, the ledger's
   9e7811343bcf`.
2. One `evaluate plaza-night art/fixtures/round/A.intent` (it came out `REFUSED INTENT-APPLY`) appended event #26,
   checked against the files' head.
3. After that, `verify` refuses `LEDGER-HEAD: #26 was checked against df8b640defd8, but the head was 9e7811343bcf`.
4. `rebase`, the remedy that `verify`'s own message names, refuses with the same line. The tools can no longer
   repair this ledger; only restoring the file by hand (git) could.

The likely cause is INFERRED: 0237's exporter change (`art/dress.py`, `0a6ce8b`) was recorded by no rebase, as #21,
#24 and #25 recorded theirs.

By reading, the same breakage follows any evaluation or admission over a hand edit in any world:

- evaluation takes the head from the files (`art/director.py:632`, `782-786`);
- `rebase` replays the ledger first (`art/director.py:849-857`).

By reading too, a new worlds folder seeded from this checkout would leave plaza-night out, because seeding verifies
each copied ledger (`art/play.py:835`).

MEASURED after the audit, the same day, on copies of his desktop studio's worlds folder: `verify` refuses
`UNLOGGED-CHANGE` for both of its worlds too (harbor-day: the files `bd321617d339`, the ledger `36686b4e6080`;
plaza-night: `7221f144ba1f` against `7017cc385db7`). So every ledgered world was unlogged at HEAD, and the first
evaluation in any of them would have broken its ledger.

**Remedy:**

- *His act now:* rebase the checkout's plaza-night after reading what moved, before any evaluation there:
  `python art/director.py rebase plaza-night --note TEXT`. The same for each desktop world, adding
  `--root "%LOCALAPPDATA%\VerdandiStudio\worlds\NAME"`.
- *A repair (patch 0245):* evaluate, admit, refuse, approve and rebase refuse while the files' head is not the
  ledger's replayed head, before anything is appended. *As built:* evaluate, re-evaluate, admit and approve, the
  events that name a head; a refuse names none and replay checks none for it, so it is appended as before; a rebase
  refuses on the checks, not on the head (it is the remedy).

**F-2 · `rebase` records any brief and discards its checks (VERIFIED BY READING, two agents).**

- `cmd_rebase` takes `out, parts, _c = ws.export()` and drops the check results (`art/director.py:852`).
- Replay accepts a rebase of any content.
- `rebase` reads `head_before` outside the content lock.
- Movers, the rules and the overlay have entered every world this way, or by a commit with no ledger at all. Three of
  the four briefs have no ledger in the checkout. This is a second mutation path beside admission. It is documented,
  not hidden, but nothing checks it.

**F-3 · The provider writes the scope its candidate is judged against (VERIFIED BY READING; F0's rows).**

- `intent_doc` copies the provider's `scope` into the intent (`art/studio.py:443-451`), and CLEAN means "changed
  nothing outside the declared scope".
- A response that declares `**`, `material/*` and `env/*` makes any art change inside them CLEAN, and admissible with
  a still.
- No test plants an over-wide scope, and the card does not show the declared scope.

The roadmap records the ADMIT-0 ruling: *"A scope the proposal writes for itself bounds nothing. It bounds something
when whoever admits grants it, and a proposal can only ask for less"* (docs/ROADMAP.md:1196-1197). The art studio
does otherwise. In a strict request the shapes do bound the change (STRICT-0, tested). **His ruling.**

**F-4 · A candidate is evaluated at the head its answer arrives at, not the head the model was shown (VERIFIED BY
READING, checked here).**

- `candidate_slot` evaluates at the current head (`art/studio.py:1266-1267`).
- `HEAD-MOVED` is informational (`art/director/scope.py:255-258`).
- A `=` replaces its statement by key, so after another window's admission a candidate written against the old head
  can come out CLEAN and overwrite that admission's change, with no conflict named (F8's row).

A stale admission is refused (STUDIO-STALE, tested). This finding concerns the drawing. **His ruling:** refuse, or
mark on the card.

**F-5 · The page is never executed by a test** (§4). It decides the plan's order.

**F-6 · RUNG-0's plants reconcile less than they appear to (MEASURED from his log).**

R5 reads four suites. Read from `20261016T162615Z.log` with R5's own expression, they give:

| suite | plant rows | distinct keys |
|---|---|---|
| quality | 54 | 54 |
| check | 202 | 56 |
| director | 6 | 6 |
| studio | 0 | 0 |

That totals 116, his "116 and 116".

- **studio:** its rows do not begin `plant: `, so it contributes nothing.
- **check:** it prints each plant once per brief without the brief's name, so four worlds collapse into one key, and
  the last brief's verdict wins.
- **The old checker:** a stop in it is printed but still reads HELD (`tools/rung.py:467-473`).

This is the identity refinement agreed at docs/ROADMAP.md:5049-5050, not yet built.

**F-7 · The gate's expected set is in documents (VERIFIED BY READING).**

- The rowset `74db4c8d78625af5` is computed (`verify/verify.py:17018`) and compared with nothing. The fences hold
  rows 1-247 by digest and 248-251 by name.
- A skipped row still reads `GATE PASSED`. ADMISSION-0 in the art layer does the opposite: a skip is not a pass.
- docs/REPOSITORY-TRUTH.md T-13 left this to him. **His ruling** (the gate is his).

**F-8 · The stored inverse is exact on a narrower subset than 0244's FOUND (MEASURED by an agent, by a scratch
round-trip of `apply_revision`).**

- `+` is byte-exact only when the parent ends in exactly one LF.
- `-` of the *last* statement is exact; `-` of a middle one is not.
- `=` also fails on a line whose comment is not preceded by exactly two spaces.

Today's four briefs fall inside the subset art/STUDIO.md describes. *Corrected, MEASURED on his machine the same day:*
they do not quite. A `-` of the last statement is exact when it is single-spaced with no comment, the brief ends in
exactly one LF and the line before it is not blank. harbor-day, harbor-lift and plaza-night meet that, so a `-` of
their last statement and its undo give back the head, which 0244's "every `-`" denies; only foundry-yard's last line
is aligned. CERT SELFTEST pins the inexact cases as expected
(`art/certificate.py:126-149`), so the repair (his (a) or (b) from 0244) must rewrite those rows with it.

**F-9 · Smaller defects in the art layer (VERIFIED BY READING).**

- Certificates are written with a plain `open()` after the commit, outside the lock, and their exceptions are
  swallowed (`art/studio.py:1135-1139`, `1632-1633`); nothing regenerates a missing one.
- Director refusals lose their code at the studio boundary: every one becomes `STUDIO-DIRECTOR-REFUSED`
  (`art/studio.py:1643-1651`). *Said more exactly (0245's review):* the code survives only inside the message's
  text, never as a field; a LedgerError is not caught there at all.
- `CERT-ART-ONLY` can never fire on a certificate `make()` builds (`art/certificate.py:69-71`).
- The undo's bookkeeping parses a note's text (`art/studio.py:1589-1591`).
- `studio_post` falls through to undo for any studio path not matched above it (`art/play.py:983`). It is safe only
  because the route whitelist refuses others first: fragile, not live.
- `graybox/level.py` reads numbers with `float()` and `int()` alone (`:42`, `:58`, `:179`), beneath the art's number
  grammar.

**F-10 · Defects in pinned Rust (VERIFIED BY READING; each needs an amendment, his).**

- An admitted VRDNP1 or VRDNP2 `close` of the camera's own cell is not refused (`shell/playback.rs:601-611`), though
  the workshop and the compiler refuse it.
- `shell/playback.rs`'s `apply_spec` writes a cell with no bound (`:141-157`). This is recorded already in
  docs/BINARY-SDK.md:334-335.
- The workshop's writers overwrite their only copy (`workshop/session.rs:383`, `sessionwalk.rs:631`).
- A saved session has no version member (`shell/livesession.rs:496-500`).

None of these blocks the studio, which does not use these paths. Under the sprint ruling they wait.

## 6. SPEC1 against the rules

About a third of SPEC1 already exists under other names, off the gate, in the art layer: stored inverses and
certificates (CERT-0), glue with obstruction objects and a census (GLUE-0), region containment (STRICT-0 and the
shell's grant), place-named ids, scripted acceptance (FLAGSHIP-0) and evidence sheets (PREVIEW-0). Its central moves
conflict with a rule or a ruling, and SPEC2 §2.6, §5 and §16 already reject or defer nearly all of them.

| SPEC1 | verdict | the rule, or what the code shows |
|---|---|---|
| the anchor graph as the authority; the log demoted to a view | CONFLICTS | SPEC2 §5 and §16 defer it. DESIGN-EVENT-0's registered ruling keeps replay as the authority, and canonicalising belongs to the compiler, "never to the shell" (verify/preregister.json:674). See also the DSC-0 ruling |
| dense ids renumbered in canonical order | CONFLICTS | SPEC2 §2.6 and §16 reject it. Admission refuses a proposal id already in the whole history (`shell/admit.rs:390-393`) |
| "certified-path floats 0", "charter-bound" | true only on the gate's Rust path | The charter has no float clause. The graybox is binary64 by design (RULES-1). The exporter computes in Python floats, and the checkers read the written decimals |
| admission O(k log n) | never measured | The registered ruling: full verification locked, delta verification deferred (preregister.json:674, 688) |
| rebase commutation as "the theorem of geo-stability" | already disproved here | graybox/ORT-1.md:40-42; the translation probe (docs/ROADMAP.md:4131-4136) |
| Q32.32 physics everywhere | CONFLICTS | ORT-1 scrapped an int32 state model (ORT-1.md:18-19). The conflict is with "everywhere": `oracle/game` carries Q32.32 kinematics |
| a `sha2` dependency, DEP-0 | the vendored branch exists | `kernel/mantle.rs:74-89` is the hand-written SHA-256. DEP-0 would be a new row, and the gate stops growing |
| fourteen new gate rows, rungs E1-E11 | CONFLICTS | The sprint ruling of 2026-10-09. The names CERT-0, E2, E3 and E4 are already taken with other meanings |
| kernel modules and a C ABI | CONFLICTS | Pinned single-file sources, no Cargo (AGENTS.md §3). The kernel stays untouched through Phase I |
| materials as palette indices | CONFLICTS | Art materials are sRGB plus PBR scalars by design, and SPEC2 §12 says not to force them into a palette |
| a bit-exact reference renderer and a downsample | PARTIAL / CONFLICTS | The bit-exact reference renders the kernel's tile world only. By rule, nothing hashes the art's picture |

## 7. The patch plan

Each patch is one rung, off the gate, with its plants. None touches a row, a registered entry, a pinned source or a
reference. The order:

- **0245** comes first because F-1 is live in the checkout, and the dashboard drives the routes it repairs.
- **0246** comes before **0247** because a consolidation of a page that no test runs could not be held (F-5).
- **0248** and **0249** wait on his rulings.

### 0245 · LEDGER-SAFE-0: no event over a head the ledger does not hold, and R5's reading

**What it changes.**
- `evaluate`, `reevaluate`, `admit`, `refuse` and `approve`, whether from the command line or through the studio,
  refuse with a typed code while the files' head is not the ledger's replayed head. The code names both heads and
  "rebase first", and nothing is appended. The live loop still serves a hand edit; only the ledger's writers wait.
  *As built:* `refuse` is not among them (it names no head); the studio's reject is held by its evaluation.
- `rebase` runs the art checks and refuses a brief that fails them, with their names. It records the results, reads
  under the content lock, and replay checks a rebase's `art_text` against its parts.
- Certificates are written through `durable.write`, and the studio's start writes a missing one from the ledger (a
  certificate is derived).
- `quiet()` keeps a director refusal's own code.
- `studio_post`'s undo becomes an explicit branch, and an unknown studio path is refused.
- `tools/rung.py`'s R5 keys `art/check.py`'s rows by the `== NAME` world header, and reads the studio suite's plant
  rows by a stated rule. It takes effect from the next patch, once he takes the classifier from `origin/main`.

**Plants.**
- An evaluation over a hand edit is refused and the ledger still verifies. Without the check, `LEDGER-HEAD`, as
  measured in F-1.
- A rebase of a brief that fails a check is refused.
- A crash after the admit event: the next start writes the certificate.
- A RUNG SELFTEST row each for the two R5 readings.

**Acceptance.** DIRECTOR SELFTEST, CRASHTEST and RACETEST; STUDIO SELFTEST with its new rows and plants; RUNG
SELFTEST; `ART SELFTESTS PASSED` twice; `PLANTS HELD`; the gate as before (`251 rows / 0 fail / 0 skipped`, rowset
`74db4c8d78625af5`).

**His act with it:** the checkout's plaza-night rebase (F-1).

### 0246 · PAGE-0: the page executed by a test (SPEC2 §15 steps 3-11, through the UI)

**What it changes.** `art/play.py` serves the page with a self-test that drives its own controls through the DOM: the
real buttons and keys, not the routes. It posts each step's result back, in the manner of the graybox's self-test (a
browser opens: Edge on his machine, Chromium in the container).

**The flow.** On foundry-yard, with the scripted director: the saved bay shape; Ask with Strict; the card's Preview;
Admit, with the still taken from the canvas by `scene_render.js`; then Undo. Every stage's evidence is the host's, as
in FLAGSHIP-0.

**Plants through the page.** Each must show its code in the page and leave the world as it was:
- a stale head;
- a missing still;
- a failing preview;
- a region refused.

Two plants of the harness itself:
- a control whose handler is gone;
- a page that skips the still.

**What it adds.** The first stills drawn by the native renderer in any suite, read by QUALITY-0's detectors.

**Acceptance.** `PAGE SELFTEST n/n` with its plants caught. The browser's name and version, and the GPU string as
the browser reports it, are recorded as OBSERVED context, never as a claim.

### 0247 · DASHBOARD-0: the consolidation, held by 0246's harness

*Note (2026-10-17): the numbers moved. 0247 and 0248 were PAGE-0's repairs; the dashboard is built as 0249 (the
revision, the cards and their accounts, the drawer's tabs, Evidence, Undo's proof, the wrong-world guard) and 0250 (the
worlds, the outliner, import), after a settled design and his word (`docs/ROADMAP.md`, the 0249 entry). Two things below
read otherwise now: the account that disables Admit is the admission's own checks run dry, never FLAGSHIP-0's stage
logic (FLAGSHIP-0's predicates give an advisory checklist, EVIDENCE-0, which gates nothing); and the page is held by a
suite of its own, PAGE-CARDS, beside PAGE, not by rows grown in PAGE alone.*

*Note (2026-10-17): the left panel below is built as 0250 (the worlds read back, the outline by the host's object rule,
import staged, checked and committed by one rename), held by STUDIO-2 and PAGE-WORLDS (`docs/ROADMAP.md`, the 0250 entry).*

**Left.** A collapsible panel holding:
- the worlds, each verified or not, from the launcher's tested read-back;
- an outliner by region, kind and object, with search, built from the scene the page already holds;
- *Import from the checkout* for a brief not in the worlds folder (`seed_worlds`' per-brief copy, kept only if its
  ledger verifies in the copy), so that foundry-yard reaches his desktop studio.

**Drawer.** Four tabs: Candidates, Queue, Validation and Evidence.
- **Evidence** gathers one candidate's evidence: the verdict and its record, held and strict, the impact ESTIMATE with
  its calibration, the preview's report and sheet, and the certificate after an admission.
- **The missing-evidence account** is computed by the host: a GET route that runs FLAGSHIP-0's stage logic read-only
  and says what the next stage needs and what is missing. A disabled Admit says why.

**Strip and cards.**
- Undo in the Edit menu and on the strip, with its answer shown: `head_restored`, and whether the certificate is
  exact or "the statements came back, the bytes did not".
- Each card names the head it was drawn at, and HEAD-MOVED.
- The stats box is labelled a software timing.
- Compare is repaired outside Mark mode.
- A row holds `studio_ui.js`'s face frames equal to the host's.

**Not in it:** direct edits, redo, projects, docking and gamepad. Each needs his word (§8).

**Acceptance.** PAGE SELFTEST grows a row for each area it drives. `ART SELFTESTS PASSED`. §4's table is audited
again, with the harness.

### 0248 · candidate binding (after his rulings on F-3 and F-4)

*Note (2026-10-17): now 0251, after the dashboard's two halves; the still's and the preview's scene, recorded since 0249,
are refused on there, if he so rules.*

*Note (2026-10-18): now 0252, BROWSER-SERIALIZATION-0 having taken 0251.*

*Note (2026-10-18, later): his ruling of that day settled the binding otherwise than this plan: BINDING-0, registered in
0252 (`art/director/bindings/BINDING-0.v0.json`) and enforced in 0253 (the still, a preview the admission names, and the
undo's operation and the world's scene it was shown over, each refused on a mismatch or an unknown, after every existing
check). Of the items below, the provider's scope bounded by the request and a provider's answer at another head are not
BINDING-0's and wait on his word; the undo's binding is BINDING-0's, as he chose it.*

*Note (2026-10-19): built in 0253, in two commits: the test matrix and the conformance vectors frozen first
(`art/director/bindings/0253-matrix.json`, `0253-vectors.json`, `frozen-0253.jsonl`), then the guard (art/studio.py,
the `gate` of the director's commit): the still's kept scene, a preview the admission names by its id and the undo's `of`
and `scene` refused BINDING-MISMATCH or BINDING-UNKNOWN after every existing check and before the first write, every
press answered and logged with its decision record. The page names no preview, and FLAGSHIP-0 none (his rulings of
2026-10-19, docs/ROADMAP.md). The inverse's repair is 0254's.*

- The provider's scope is bounded by the request. Either the host intersects it with the target's, the pins' and the
  shapes' patterns, or a namespace-wide pattern needs the designer's grant. The card shows the declared scope and the
  phantom patterns.
- A provider's answer evaluated at a head other than the one it was shown is refused, or marked on the card, as he
  rules.
- The undo request names the head the page saw, and the inverse applies only while the head is the undone admission's
  `head_after`.

### 0249 · the inverse's repair (his (a) or (b) from 0244), with F-8's narrower subset and CERT SELFTEST's rows rewritten with it.

*Note (2026-10-17): now 0252.*

*Note (2026-10-18): now 0253.*

*Note (2026-10-18, later): now 0254.*

### Later, measured before decided

- **PLANTS-COMPLETE-0, his "rung of its own":**
  - expected row sets per suite, apart from the output;
  - rows by identity (suite, world, kind);
  - exact reconciliation, failing closed;
  - planted omissions;
  - both consoles.

  The gate's skipped-row verdict and its rowset comparison are his (F-7).
- **D1-M:** a frame-time instrument for `scene_render.js` on his machine: p50, p95 and p99 with the clock's step, the
  scene's digest, resolution, browser and settings. A declared target profile comes before any comparison of
  renderers.
- **SPEC2 Phases 3-8**, in its order, each by its own measurement.

## 8. The decisions that are his

1. The order above: 0245, then 0246, then 0247.
2. The checkout's plaza-night rebase (F-1). It is his world.
3. F-3: whether a provider's scope is bounded by the request, as the ADMIT-0 ruling would have it.
4. F-4: whether a provider's answer that arrives at a moved head is refused or marked.
5. The inverse's repair, (a) or (b), pending since 0244.
6. F-7: whether a skipped gate row fails, and whether the gate compares its rowset with a constant.
7. Whether direct edits, redo, projects, docking and gamepad enter the dashboard. Direct edits would be intents the
   page writes, admitted through `cmd_admit`, the one path.
8. The target profile: whether SPEC2's (Windows desktop and Xbox Ally X-class hardware, 1920×1080) becomes the
   studio's, and D1-M is measured against it.
9. F-10's Rust defects: amend now or leave.
10. The two untracked `art/ledger/*.tags.json` in the checkout, written by checkout-mode sessions: keep, commit or
    remove.

## 9. Documents found stale (to correct with the patch that touches them)

Reported by the readers. Each line is to be read again before its fix.

| document | says | the code or log shows |
|---|---|---|
| AGENTS.md:96 | PREVIEW-STUDIO SELFTEST 13/13 | 14/14 in his log |
| art/STUDIO.md:639 | the studio app's self-test has 11 cases, 12 on Windows | 13/13 |
| art/STUDIO.md:686 | the queue's has 13 | 19/19 |
| art/STUDIO.md:655 | two briefs | four |
| docs/STUDIO-APP.md:47 | the content files' crash-safe writes are "missing" | they go through `art/director/durable.py` |
| docs/STUDIO-APP.md:676-677 | outliner, details and strip are "still to be built" | details and cards were built at 0230 |
| docs/STUDIO-CONTRACT.md:72-73 | the validators' and configuration's digests are "a gap" | they are recorded and tested |
| art/director/README.md:188, 208 | 62 vectors | 65 |
| docs/BOUNDARIES.md:35 | the art writes "never W, C or a layout" | `art/director.py` writes `graybox/maps/*.layout` |
| docs/BOUNDARIES.md:50 | replay determinism is shown on one build | — |
| graybox/README.md:364-365 | "not yet measured in another engine" | Firefox 157 and Edge 155, MEASURED on his machine |
| docs/CORE.md:4 | its header says HEAD 4247a61 | its tables run to 0244 |
| art/web/play.js:1817-1820 | M, C and P are computed by the page | they are the host's |
| README.md:46-50 | "nothing of this is built" of LLM proposals | true of the session world only |
| art/README.md:75 | a dressing choice is a hash of its statement's text | it is keyed by the statement's key |

0245 corrects AGENTS.md:96, the three art/STUDIO.md lines and the director README's current-state table (line 208;
line 188 is dated and stays). The rest wait for the patch that touches them.

Commit `6af1d9f`'s message says the flagship's undo stage requires the certificate "exact". It requires `ok` and
`head_restored` (`art/flagship.py:176`), which has the same effect. History is not rewritten; this is said here.

## 10. What this does not show

- Whether any of it is right beyond what the cited tests hold. A row graded `EXISTS-TESTED` means a test would fail on
  a defect and has passed at HEAD. It does not mean the capability is complete.
- Anything of the page as it runs, of visual quality, or of performance. Nothing was rendered or timed, except the
  gate's wall time (§2).
- The graybox's own checks, `design/test_design.py` and `conform.rs` at HEAD: none was run.
- Every cited line. The agents' `file:line` references were checked where §5 says so. Elsewhere they may be off by a
  few lines.
- That the five areas are his five. That is INFERRED from SPEC2 §11.
- The falsifier of this file: a row whose cited test does not fail on a planted defect, or a `MISSING` capability
  found in the tree. Either is corrected in the rows file with a note, as the program corrects any record.
