# Repository truth — the documentation audit of 2026-10-09

What the documents said, set against what the code does. This is a documentation-only pass: no source, test, build
script, format, registered entry or gate row was changed. Where a finding needs a code change, it is recorded here
and left. The audit is graded as the program grades everything else, and its own errors are part of the record.

## 1. Method

- **The checkout.** Branch `fast0`, HEAD `4247a61` (the pushed `main`), tree `6d0147ee`. There are 240 tracked files,
  and the working tree was clean before the pass.
- **What was read.** Five readers worked in parallel, read-only:
  - the formats, from their writers and readers;
  - the top-level and folder READMEs;
  - the roadmap, dev notes, ghosts, boundaries and the graybox;
  - the recorded rationale for each design decision;
  - the architecture.

  Their reports were then checked against the code before anything was written. One reported number was wrong:
  `kernel-corpus` holds 12 witnesses (6 scenes × 2 tile sets), not 20. It was corrected before use, which is the rule
  this file applies to its own inputs.
- **What was run:**
  - the gate's row count, statically: 251 `row(...)` calls in `main()`, rowset `74db4c8d78625af5`;
  - the three examples in [`BINARY-SDK.md`](BINARY-SDK.md);
  - the registration ledger's 55 hashes, recomputed, all equal;
  - the kernel built twice, byte-identical ([`RESEARCH-FINDINGS.md`](RESEARCH-FINDINGS.md), R-5);
  - one canonical-JSON comparison (R-4).

  Earlier, one auditor ran the documented commands of the README and the design tool in a scratch copy, and another
  ran `graybox/check.py` and `sim.js`'s self-test under node.
- **What was not run.** The gate. It is a release instrument, and nothing it holds changed. Its last runs on a tree
  differing from this one only in `graybox/`, `docs/` and the README: 251 / 0 in the build container (the 0175 tree)
  and FULL×2 on the host (`51ebd25d`).
- **The rule for history.** Dated records, lessons, the ledger and registered texts are not rewritten. A current-state
  sentence that is stale is corrected. A dated record that was wrong when it was written (the GPU, T-11) is corrected
  in place with a note that says so.

## 2. Findings

Dispositions: **C** corrected in this pass · **D** deferred, because it needs a code or pinned-source change · **O** the
owner's decision · **H** historical, left as written.

### Current-state text that had gone stale or was overstated

| id | where | the claim | the evidence | disposition |
|---|---|---|---|---|
| T-1 | `README.md:4` | "for the repository and the crate names" | no `Cargo.toml` or crate exists; each program is one `rustc` file | C |
| T-2 | `README.md:10-11`, its ghosts list; `workshop/README.md` G17 | a saved session is "verified by the workshop" / "the workshop verifying every saved file" | the shell starts no process; `sessionwalk verify` runs in the gate's rows and in `verify/livesession.py` before sealing | C |
| T-3 | `README.md:60-62` | "the tool compiles them" | `design.py` calls `shell design-compile` (DESIGN-IR/DIFF-0) | C |
| T-4 | `README.md` goal 4 | a proposal becomes one event | a batch becomes N events under one admission (`shell/designevent.rs`) | C |
| T-5 | `README.md` invariants; `docs/PROGRAM.md` §2 | the borrow checker keeps a read from editing the authority | the typestate exists only in `workshop/membrane.rs`; the live session uses private fields | C |
| T-6 | `README.md`, folder table | — | no rows for `design/`, `graybox/`, `docs/` | C |
| T-7 | `README.md`, Running | the gate "needs rustc for the kernel rows" | most rows build with rustc; no design or graybox commands; a gate run rebuilds `verify/build/shell` without the window | C |
| T-8 | `README.md`, `verify/README.md`, `docs/DEVNOTES.md` (rhythm) | landing = two byte-identical gate runs, said of everything | the owner's ruling of 2026-10-09: the full gate at release checkpoints, other work its own checks | C (scoped) |
| T-9 | `README.md`, Reading further | the roadmap holds "the declared design-event stream" | built since; new documents unlinked | C |
| T-10 | `docs/PROGRAM.md` §2, §8, §10, §12 | the charter "has not moved since"; "242 rows"; the design tool admits into a scratch root and calls `shell admit` | the charter moved once (`ac22fd3`, 2026-10-01, the second oracle tag); 251 rows; `design.py` calls `design-compile`, then `design --dry-run`, then `design --previewed` | C |
| T-11 | `docs/ROADMAP.md` (0179 and 0180 host records), `README.md`, `docs/DEVNOTES.md` | the host GPU named a "Radeon R9 200-series" | Firefox maps many AMD GPUs to "Radeon R9 200 Series, or similar" (R-8). The string establishes an AMD GPU through ANGLE on Direct3D 11, not the model | C, with a correction note; the pushed commit messages `222f856` and `4247a61` cannot be corrected |
| T-13 | `verify/README.md:4-6` | without rustc "only the verdict" depends on the toolchain | the verdict prints PASSED whenever no row fails, whatever the number skipped (`verify.py:17016-17020`) | C (doc); the gate's behaviour: O |
| T-14 | `docs/BOUNDARIES.md`, diagram | `design/` inside "the certified tree (held by the gate)" | no row reads `design/`; `designir-fence` and `hermeneutics-fence` check that nothing under `verify/` does (this audit's own earlier text, 0175) | C |
| T-15 | `docs/BOUNDARIES.md`, table | a statement on rock is refused; serve.py writes nothing; "every response" isolated; the simulation the only writer; every solid a column; seven plants refused; the bench sample one draw | a probe may name rock; Python's bytecode cache; the redirect and the server's own error responses carry neither header; `main.js` ages `s.fx`; the targets are solids drawn in their hit boxes; the plants ran once, off the tree; a sample is the mean of K draws | C |
| T-16 | `docs/ROADMAP.md`: lines 7, 57, 161 and the headers of HOST-STATE-1, the design language and hermeneutics | "named but not yet built"; "not yet done: that compiler"; "timed in SwiftShader only"; "no court records it yet"; "not registered, nothing built"; "nothing built" | most route rungs built; the compiler built; host timings in 0179; DRIFT-0's records cite HOST-STATE-1; the design text and compiler built; hermeneutics built | C |
| T-17 | `docs/ROADMAP.md`, the invariants that carry forward | "Everything above obeys the same discipline" | the graybox stands beside the tree with floats and WebGL by the 2026-10-09 rulings | C (scoped) |
| T-18 | `docs/DEVNOTES.md`, Part I's watch list | presentation geometry "still a separate court"; the shell "has no per-frame render loop" | PRESENTATION-CHOICE-0 decided it; LIVE-LOOP-0 built one | C |
| T-19 | `docs/GHOSTS.md` | "Nothing here is a defect the gate missed"; the index and disposition stop at G28 | G30, G31, G34, G35 are owner-ruled defects; G29–G33 missing | C; also G27's count, G28's tense, G13's sitting, G36's first direct check |
| T-20 | `graybox/README.md` | the flags, the controls, the self-test, the format, the timings "stop at the browser's hand-off to the compositor" | `--timeout` undocumented; the map name must come first; G has no effect under the flat renderer; on the witness level the cover check reports "not applicable" and counts; five converter rules unstated; the timings end in the page's callbacks | C |
| T-21 | `shell/README.md` | file table and command list | `designcompile.rs` and the `design` / `design-compile` commands missing | C |
| T-22 | `kernel/README.md` | the attest table | the two BEARING-FAST-0 records missing; no `gauntlet2-confirm` record is committed | C |
| T-23 | `design/README.md` | "Thirteen drive it as a program"; the comment rule; the project default | twelve (`design/test_design.py`: 12 + 1 client + 4 plants = 17); line 1 takes no comment; `$VERDANDI_DESIGN` | C |
| T-24 | `verify/README.md` dev notes | the build "will move" line numbers; "the build's row is to hold" the split | REASON-COURT-0 is built; `reasoncourt-register` holds the 1,103 split | C |
| T-25 | `docs/ROADMAP.md:33`, `kernel/README.md` | "everything the tree saves and reads back" is the saved form | the refusal log, the run ledger, `project.json` and the graybox JSON are plain JSON | C (scoped); the same sentence in pinned sources: D |

### What the audit observed of the gate itself (nothing changed)

**T-12 · The registration ledger's lock is self-consistency.** `records-preregistered` recomputes each entry's
`chain_hash` from its own fields (`verify.py:1358-1390`). Its refusal says *the entry was edited after registration*.
An entry edited together with a recomputed hash also passes: the hash is unkeyed, and anyone can recompute it
(BINARY-SDK.md, example 3). What does hold an entry is one of these:

- a full hash constant in a rung's rows;
- a committed record that cites the hash;
- the Git history.

By string search, **nine of the 55 entries** have their hash in neither the gate's source nor any committed record:
RECORD-0, REFUSAL-WHY-0, REFUSAL-LOG-0, RUN-LEDGER-0, REFUSAL-WHY-1, LIVE-AUTHOR-0, HOLD-WALK-0, BEARING-0 and
MOUSE-LOOK-0a. GHOSTS G29 already notes that the ledger has no head. Disposition: `verify/README.md` corrected; the
row and its text are code (**O**).

**T-26 · Other observations, each the owner's to weigh (O):**

- **No release checkpoint is defined** anywhere, though the rule for when the full gate runs depends on one.
- **The toolchain is unpinned.** No rustc version and no edition (the default is 2015). FULL×2 establishes repeatable
  gate output, not reproducible binaries (R-5).
- **The charter block** (README lines 16–43) was edited once after ratification: `ac22fd3` added the second oracle tag.
  It was reported and not edited.
- **Three charter lines stand in tension with the code.**
  - "contains no authority mirror" against the shell's own copy of the fold. That tension is recorded as G17.
  - "never: shell ──► canonical authority", while the shell writes saved and admitted sessions. Whether this conflicts
    depends on what "canonical authority" means.
  - "editor / inspector / tool panes = shell chrome", which is not built: the design tool is a command line.
- **The README's not-goals** include "a general game engine" and "a second platform's window". The graybox is a
  cross-platform browser runtime, allowed because it stands beside the tree. How it sits against those not-goals is
  unstated.
- **No Python version is stated.** The host runs 3.14 and the container 3.11.

### Stale comments in pinned sources, and small code findings (deferred, D)

A comment in a pinned file is part of its hash. Fixing one moves a pin, which is an amendment.

| where | what it says | what is so |
|---|---|---|
| `workshop/text.rs:69` | comments are `#…` | they are `;`; `#` is rock |
| `workshop/input.rs:32` | `commands LFFRF` | only the first word after `commands` is kept |
| `workshop/session.rs:33-37` | `--level/--tiles` on every verb | used by `new` only; later verbs read the stored base |
| `shell/refusallog.rs:12-15`, `shell/runledger.rs:12-15` | the logs are the present path's | admission, the batch, the compiler and the live loop write them too |
| `kernel/savedform.rs:6`, `verify/savedform.py:5` | everything the tree saves is the saved form | as T-25 |
| `shell/admit.rs:51`, `shell/designevent.rs:48` | `MIN_BYTES`, `MIN_BATCH_BYTES` | declared and never tested; the grammar holds them |
| `kernel/formats.rs:121-168` | the camera token | trimmed and narrowed with `as i32`; not canonical |
| `shell/playback.rs:141-187` | — | applies edit specs without the bounds and border checks other readers make (read, not run) |

Code outside the pins, left because this pass changes no code:

- `graybox/serve.py`'s argument order;
- `graybox/level.py` accepting `NaN` yaw and padded or non-ASCII digits;
- `graybox/web/main.js:7-8`, which says the timings stop at the compositor;
- `design/design.py:592`, which prints its pipeline diagram as usage.

### Historical text, verified and left (H)

- **The README's sequence.** Its numbers each match their source: 411 tests; 3,716 µs and 622,440; 13,931 reports and
  1,761 looks; 163,072 mutants; the 145 / 103 / 42 split; 164 mint sites; 17 checks; 11 compiler plants; 10 designs,
  4 laws and 5 plants.
- **EPISTEMIC-INVARIANCE.md** is accurate in its own terms.
- **The dated host records** in the roadmap and the ledger stand, except T-11, which carries its correction note.

## 3. Design rationale: what is written down

| decision | recorded reason | enforced where | still applies | gap |
|---|---|---|---|---|
| std-only Rust, stdlib Python | the charter's rule, cited as authority. The cost is recorded (G1's raw pointer instead of a crate) | bare `rustc`; the pins; `GAME_STDLIB` for `oracle/game` only | yes, for the certified tree; the graybox is outside by design | **the reason is undocumented** (auditability, offline builds and supply chain are inferences, not records). The only motive on record is the egress policy, and that is the graybox's |
| integers, no float in a rule | exactness inherited from Urðr (`kernel/mantle.rs:22-28`); the saved form rejects JSON floats because the rules are integers (ROADMAP) | `simtick-fence` (one file); elsewhere byte identity and the pins | yes | why the tick rules specifically must be float-free is not written. Cross-machine head equality is the evident reason, but it is an inference |
| one byte form for proposals | "at a trust boundary, prefer a language with one reading" (DEVNOTES) | `admit-reader`, `admit-single`, `designevent-language` | yes | — |
| the saved form, not canonical bytes | the writers share a data language, not a serialisation (ROADMAP) | `readercourt-*` | yes | — |
| pins and amendment chains | "make weakening a method a visible diff" (PROGRAM); history, identity and behaviour kept apart (verify/README) | `reasoncourt-fence`, `mintwatch-fence`, the chain rows | yes; frozen since `3dc15ec` | the ledger has no head (T-12) |
| unsafe only at the edges | "unbounded authority across the boundary" is the violation, not unsafe itself (the owner, BOUNDARIES) | token fences on eleven files | yes | no inventory of `unsafe` was written down; it is now in `CORE.md` §5 |
| timing never claims input to photon | software and hardware boundaries; a slow display cannot launder a software number (LATENCY-0) | the method locks; no row reads a clock | yes | — |
| the gate as a release instrument | the owner's sprint ruling, 2026-10-09 | process only | yes | no release checkpoint defined |

## 4. The "recommended docs folder structure", reviewed

A text proposed ten documents under `docs/`, and a minimal four. Much of its content is not this repository. A large
part of it describes, as if built, the competitive-arena proposal that `docs/ROADMAP.md` records as *declared, not
registered, nothing built*, followed there by a correction that disputes it. Pasted into a model's context as true,
it would make the model write to a contract that does not exist. `integrity ≠ truth`: a tidy structure is not
evidence of its content.

| proposed file | what it asserts | what is so | done instead |
|---|---|---|---|
| ARCHITECTURE.md | a three-layer model; a verified core with "no FFI, no float" | layers are oracle, kernel, workshop and shell, with the gate apart. FFI exists (`win32.rs`, `MoveFileExW`) and floats appear in off-gate timing | `docs/CORE.md` |
| DESIGN-RULES.md | integer **voxel** coordinates; tile classes floor, wall, void, spawn, objective; primitives block, cut, plane | the language has cells (2D), rock and floor, five tile *colour* classes (`wall0`–`wall3`, `floor`), and the statements open, close, room, entrance, paint. `block`/`cut`/`void`/`plane` are the arena proposal's `VERDANDI-GEO 0`, not built | none: `design/README.md` and `shell/designcompile.rs` are the rules |
| PORTING-GUIDE.md | an amendment for every core change; "FULL×2 across host/container"; "a fairness court re-run" | amendments are for pinned files and registered entries; FULL×2 is two runs on one tree; there are no fairness courts | `CORE.md` §10, and `AGENTS.md` |
| VERIFICATION-CONTRACT.md | "Linux + Windows produce identical state"; fairness courts at 100% | cross-platform identity is shown for registered literals and a few sessions, not in general (`CORE.md` §6); there are no fairness courts | `CORE.md` §6 and §8 |
| CONVERSION-SPEC.md | a wall is a block at y = 0..1; void tiles; a 3D → 2D round trip; "any geometry that cannot be traced to a 2D source is INVALID" | graybox walls are columns at the overlay's `wall` height (4 m); there is no void or round trip. Decoration is allowed when it decides nothing (the owner's three-worlds rule) | `graybox/README.md`, `BOUNDARIES.md`, `BINARY-SDK.md` §3 |
| FAIRNESS-COURTS.md | SPAWN_SAFE, SIGHTLINE_BALANCED, RAYCAST_CONSISTENT, APPROACH_DIVERSITY, with thresholds | the arena proposal's courts, declared and disputed; the 15% and 40% thresholds appear in no court, row or registration | none |
| MUTATION-CATALOG.md | classes M_C, M_F, M_E, M_H | invented labels. The mutation record lives in the ledger, the ghosts and `verify/README.md` | none; a generated index could be a later choice |
| BOUNDARIES.md | heap allocation and floats forbidden in the core; a fixed-point state interface | allocation is everywhere (`Vec`); floats are fenced in one file; the graybox state is JS doubles | the existing file, corrected (T-14, T-15) |
| WITNESS-PROTOCOL.md | manifests per file, reject on unnamed changes | the witness exists and lives outside the repository; its protocol is in the ledger (RUNGS, INPUT-0b) | none |
| CHANGELOG.md | `0a \| fbac854 \| shell/main.rs`; `0b \| 8db2d8ee \| designir-*`; "HERMENEUTICS-0a TBD, awaiting ruling" | `fbac854` is BEARING-FAST-0's commit, not an amendment. `8db2d8ee` is a file hash (`shell/main.rs` in REASON-COURT-0b), not a commit. HERMENEUTICS-0a was registered (`7e012752`) and built | none: `verify/preregister.json`, the ledger and `git log` are the record |

What was worth keeping:

- **A brief for a model.** That is `AGENTS.md`, the format coding agents read ([agents.md](https://agents.md/)).
- **A change-impact map.** That is `CORE.md` §10.
- **The minimum four's intent.** The intent was to keep a model from inventing rules. The way to serve it is to point
  at the files that hold the rules, not to restate them where they can drift.

## 5. Validation of this pass

- Every repository path named in the new documents was checked to exist.
- Every command in `README.md`'s additions was checked against its parser.
- The examples were run.
- `git diff --stat` shows Markdown only: no source, test, script, map, format, entry or row changed.
- `verify/RUNGS.md` and `oracle/` are untouched. The README's charter block is untouched.
- The patch was applied to a fresh clone of the pushed `main`, and its tree was compared there.
