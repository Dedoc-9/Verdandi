# LOCALITY-0 — admission record and batch sheet (for his adjudication; nothing built)

> Scratchpad only. Nothing in the repository has changed: HEAD is `de91aaf`, and no file is tracked as changed. No
> perturbed brief has been exported, and no LOCALITY-0 result exists. The one thing run against the exporter was a
> timing for the cost estimate: three exports each of the unperturbed `plaza-night` and `harbor-lift` fixtures, with
> the output discarded unread (0.057–0.090 s each, OBSERVED here, a software timing). `verify_sheet.py` re-checks
> every hash, count, quotation and code citation below; its output is `verify-out.txt`.

## 1. The admission record

| | |
|---|---|
| **Name** | LOCALITY-0 |
| **Admitted** | 2026-10-24, by his words below. The ruling text is kept verbatim in `ruling-admit-locality-0.txt`. |
| **What is admitted** | *"I admit LOCALITY-0 as the next foundational measurement commit, not as proof that an identity layer is necessary. The admission is limited to the proposed scope in §5."* · *"Admitted: the proposed LOCALITY-0 measurement and report, subject to the conditions above."* |
| **What it can establish** | *"LOCALITY-0 can establish whether the current exporter exhibits identity churn and unexpected influence; it cannot, by itself, prove that a particular replacement identity architecture is necessary or sufficient."* |
| **Not admitted** | *"Not admitted: SCOPE-GRANT-0, DESIGN-IR-0a, LIVE-AI-EDIT-0, or any change to their order. Those remain separate decisions."* |
| **Not authorized** | *"Not authorized: implementation beyond the admitted measurement, changes to protected artifacts, commit or push before the resulting batch is reviewed."* |
| **Unchanged** | *"Unchanged: Q9 remains open; its pending V4 ruling is separate."* |
| **The question** | Does a one-step edit of one statement of an art brief change only the records it should, and do the exporter's ids keep naming the same things across such edits? |
| **Discriminator** | `SPEC.md` §2–§8: 2,418 single-statement perturbations of four briefs, each exported and diffed by id, every changed record classified, and churn counted two ways (re-addressing and reuse). |
| **Exit** | `SPEC.md` §15: observations with their limits, and a recommendation that cites them and proposes nothing they do not show. After the exit the harness retires to its self-test (a later item, not in this batch). |

### His four conditions, and where each is met

| condition (his words) | met by |
|---|---|
| *"Freeze the predictions before running the experiment. Keep P2 and P3 as predictions; label P1 as a reading-derived confirmation, not a prediction. Record the fixture set and perturbation inventory before collecting results."* | P2 and P3 frozen with their verdict rules (`SPEC.md` §9). P1 is a confirmation row (§10). The fixtures (§1) and the inventory (§2) are recorded with their sha256, made from text alone. The author's expectations are recorded beside the predictions, not in their place (§9, §11). |
| *"Make the measurements operationally precise. Define the records being compared, identity matching, edit classes, and the OWN / IN-SCOPE / DECLARED-GLOBAL / UNEXPLAINED classification rules. Otherwise, the report risks encoding the author's judgment rather than measuring behavior."* | §3 the records; §4 identity, by id only; §2 the edit classes; §5 the rules, first match wins. The judgment in it is the channel list, three channels each tied to its code line. Measures that no list can move are reported beside it (§6, BEYOND), and every absorbed record is listed. |
| *"Keep the plants capable of falsifying the harness. The global-dependency, ID-renumbering, and no-op plants should demonstrably trigger their expected results. Two byte-identical runs establish reproducibility, not completeness of the dependency audit."* | §14: each plant has a "caught when" that fails if the harness is blind to it. The no-op control has a harness plant of its own, so that it is not vacuous, and its brief must differ in bytes. §13 quotes his sentence on reproducibility, and completeness is claimed nowhere. |
| *"Preserve the scope boundary. No exporter changes, scene-byte changes, reference or ledger changes, gate rows, Q9 changes, or freeze changes. The report must state that observed influence under-approximates true dependence."* | The write sets below hold only new files under `art/fixtures/locality/` and `art/locality.py`. The exporter, `scene_diff.py`, `studio_refs.py` and `level.py` are only read. The limits line (§15) opens with that sentence. |

### Departures from the debate's §5 (for his acceptance)

1. **The exit.**
   - §5 said: "A report that decides one question: an identity layer is needed … or it is not."
   - By his qualification, the exit now reports observed churn and influence with their limits, and names what it
     cannot establish (§15).
2. **Grant survival is narrowed.**
   - Measured: target- and pin-derived grants, which name objects by id (a proxy, §12).
   - Not measured: shape-derived grants, since the fixtures have no shapes.
3. **The read set is wider than §5's four files.**
   - `scene_diff.py` imports `studio_marks.py`, and with it `art/director/durable.py`, `intent.py` and `ledger.py`.
   - A brief with movers makes the exporter import `graybox/tick_ref.py` and `graybox/rules_ref.py`.
   - All of them are read; none is written.
4. **The fixtures are byte copies.** The four briefs and the map are copied from `de91aaf`, so his later admissions
   cannot move the measurement. The spec itself is a fixture file, held by its sha256.
5. **Id reuse is counted beside re-addressing** (REASSIGNED, §7).
   - Worked by hand: a by-id count of gone and new ids is blind to the renumbering plant. A renumbered id shifts onto
     another piece, so it reads as a changed record, not as one added and one removed.
   - REASSIGNED — a kept id whose `by` changed — is what the plant is caught by.

### A reading he should see before the run

**P3**, as the debate worded it — "across seeds the topology is identical and only heights differ" — is expected
**FAILED** on all four briefs by reading the exporter:

- `pick` decides whether a neon is placed (`art/dress.py:861`).
- `pick` decides whether a puddle lies, and where in plan (`art/dress.py:913-916`).

P3 stays a prediction, as he ruled, and the expectation is recorded beside it. If he wants a prediction whose outcome
reading does not already suggest, that is his to word. Nothing in this sheet changes P3.

## 2. The frozen inputs (recorded before any result)

All in this folder. Each is to ship byte for byte under `art/fixtures/locality/`; `make_inventory.py` stays in scratch.

| file | sha256 | what |
|---|---|---|
| `SPEC.md` | `a4424d7e2d503c49837437ebdea4fc67dee275e126ee94123763039556da7a31` | definitions, predictions, plants, exit form |
| `INVENTORY.jsonl` | `455af6c829f85f76b491a8bd1774b7f22b24eb306d65621e19353e7c3aadd45d` | 2,418 entries |
| `FIXTURES.sha256` | `cf61fcd30e2013c87b0015e1d557cce63323bf0edeaea291ab95154115863214` | the six fixture files' sha256 |
| `fixtures/briefs/*.art`, `fixtures/maps/tactical.*` | `SPEC.md` §1 | byte copies of `de91aaf` |
| `make_inventory.py` | `04447763ff24c5915707f29d811d6548408aa8c3a6d6e6cbfd9b00a37016c01f` | the generator. It parses and never exports. `art/locality.py` must reproduce its output byte for byte. |

## 3. The batch: one patch, two commits

The patch number is his to assign; 0264 follows the pushed 0263. The file is `NNNN-locality-0.patch`, one mbox of two
commits built in a scratch clone of the pushed tree. The last commit carries `Gated-Tree:`.

### I-1 · The measurement, frozen in the tree — BUILD

- **Writes (all new):**
  - `art/fixtures/locality/SPEC.md`, `FIXTURES.sha256`, `INVENTORY.jsonl`;
  - `art/fixtures/locality/briefs/{foundry-yard,harbor-day,harbor-lift,plaza-night}.art`;
  - `art/fixtures/locality/maps/tactical.gbx`, `tactical.layout`.

  Each is byte-identical to its scratch file.
- **Obligation:** the definitions, predictions and inventory enter the history before any code that decides them. No
  program reads them yet.
- **Checks at I-1's commit:**

  | command | expected |
  |---|---|
  | sha256 of each written file | the values in §2 and `SPEC.md` §1 |
  | `python art/check.py` | `ART CHECKS PASSED`. It lists `art/briefs/` only (`art/check.py:1057`), so the fixture briefs are not its worlds. |
  | `python art/quality.py selftest` | `QUALITY SELFTEST 76/76` (it lists `art/briefs/` only, `art/quality.py:701`) |

- **Plants:** none (data). **Non-claims:** no result of any kind.
- **Rung:** computed by the classifier taken from the pushed tree. The expectation, not asserted: below D, since no file
  is in the closure.
- **Rollback:** revert the commit.
- **Touches registered evidence, baselines, admission or the gate:** no.

### I-2 · The harness — BUILD

- **Writes:** `art/locality.py` (new). It is standard library only, with the SPDX header and copyright line of its
  neighbours; about 500–700 lines, an ESTIMATE.
- **Obligation:** `SPEC.md` §3–§15, as written. The harness:
  - holds `SPEC.md`'s sha256 as a constant and prints it in every report;
  - refuses with `LOCALITY-INVENTORY`, `LOCALITY-FIXTURE` or `LOCALITY-HASHSEED` before exporting anything;
  - writes only `art/build/locality/REPORT.json` and `REPORT.txt`;
  - starts no process, and writes no temporary file (each brief is parsed from bytes in memory).
- **Commands and expected outputs:**

  | command | expected |
  |---|---|
  | `python art/locality.py inventory` | `LOCALITY INVENTORY HELD: 2418 entries, sha256 455af6c8…`; exit 0 |
  | `python art/locality.py run` | the EXIT lines of `SPEC.md` §15, then `LOCALITY HARNESS HELD (H1-H7)` and `LOCALITY-0 REPORT <sha256 of REPORT.json>`; exit 0 whatever the predictions' verdicts |
  | the same, a second time | `REPORT.json` and `REPORT.txt` byte-identical to the first run's |
  | `python art/locality.py selftest` | `LOCALITY SELFTEST 4/4`: NOOP-CLEAN, PL-GLOBAL, PL-RENUMBER and PL-NOOP, each plant caught by its own row as `SPEC.md` §14 defines |
  | `python art/check.py`; `python art/quality.py selftest` | as at I-1. The exporter is untouched, so the lineage's `exporter_sha256` is unchanged. |
  | `git diff --stat` against the base | nothing outside the two write sets; `art/dress.py`, `art/scene_diff.py`, `art/studio_refs.py`, `graybox/level.py` byte-identical |

- **Read set:**
  - *Declared:*
    - `art/locality.py` and `art/fixtures/locality/**`;
    - `art/dress.py`, `art/scene_diff.py`, `art/studio_refs.py`, `art/studio_marks.py`;
    - `art/director/durable.py`, `intent.py`, `ledger.py`;
    - `graybox/level.py`, `graybox/tick_ref.py`, `graybox/rules_ref.py`.

    No read of `art/briefs/` or `graybox/maps/` is allowed: either would mean the fixture override failed.
  - *Measured* at build in a fresh clone, with no bytecode, by a Python audit hook installed before the harness is
    imported. A read outside the declared set stops the build and revises this sheet. Any process start makes the read
    set INCOMPLETE, and the build stops. The import closure measured here today (imports only, nothing run) matches the
    declared set.
- **Plants:** `SPEC.md` §14. They are not R5 keys: `art/locality.py` is outside `tools/rung.py`'s `SUITES`, so
  `PLANTS HELD` says nothing of them.
- **Non-claims:** `SPEC.md` §15's limits and "not established" lines. No claim across machines or Python versions:
  reproducibility is shown on the machine that ran it.
- **Cost:**
  - A run is 2,422 exports plus diffs; a self-test about 3,560 (the 1,182-entry subset three times, and the NOOP rows).
  - A few minutes each is an ESTIMATE from the timing above; NOT_MEASURED until built.
- **Rung:** the classifier's. The expectation, not asserted: C, code outside the closure.
- **Rollback:** revert the commit (I-1's files stay, read by nothing).
- **Touches registered evidence, baselines, admission or the gate:** no.

### Order, interactions and boundaries

- **Order:** I-1, then I-2. I-2 reads I-1's files, and the predictions precede the code that decides them.
- **Each commit's own evidence** goes in its message: the commit, its tree, a clean status, each command's exit status
  and output digest, and the classifier over that commit alone. I-2's message carries the run's report digest and its
  EXIT lines as **run here**. His own run is his record.
- **The results** reach him as a scratch record: the report, the predictions' verdicts and the exit recommendation. A
  record of results in `docs/` is outside §5's write set and would be an admission of its own.
- **Boundaries stated before the build:**
  - The harness imports the exporter. If `dress.py` changes later, the report changes with it; its sha256 is printed.
  - If `dress.parse`, `dress.statement_key` or `dress.NUMBER` change, H1 refuses rather than measure another
    inventory.
  - `scene_diff` imports `studio_marks` and three director modules at import time; they are read, never called to
    write.
  - Python 3.14 on this host; nothing is claimed for another interpreter.

## 4. Expected at the tip, in order (fail fast)

1. `python art/locality.py run` twice, identical reports; `python art/locality.py selftest`, 4/4.
2. The full check, `python art/selftests.py`: `ART SELFTESTS PASSED`, its suites as at the base (LOCALITY-0 is not one
   of them).
3. The classifier taken from the pushed tree, nothing loosened; `rung.py plants`, PLANTS HELD, count unchanged.
4. The gate twice: `GATE PASSED`, `RECONCILE  rowset 74db4c8d78625af5  251 rows / 0 fail / 0 skipped`, the two compact
   outputs byte-identical.
5. Landing: `Gated-Tree:` in the last commit's trailers, then his `TREE HELD` check after `git am`.

## 5. Before any push (AGENTS.md §7)

Two kinds of untracked file in his checkout must be gone before he pushes:

- `.claude/worktrees/agent-ac17b21a8cea256c1/`, left from the debate;
- `art/ledger/harbor-lift.tags.json` and `art/ledger/plaza-night.tags.json`, which are older.

## 6. His decision

Build I-1 and I-2 as this sheet and `SPEC.md` state them, departures included — or name what changes first.
