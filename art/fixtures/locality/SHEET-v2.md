# LOCALITY-0 — batch sheet, version 2: one amendment to version 1's read-set rule

> **Version 1** is `SHEET.md` (sha256 `fa717ede5c0f1bc5d8d2ab17b6f35a372028124755e7350f1e89858d3e3bbe0b`). It stays
> byte for byte as frozen, and in force in everything but the rule below.
>
> **This version** is registered 2026-10-24, after the build and before the read-set measurement it governs is run
> again. Its sha256 is recorded before any code that applies it is written.

## 1. Why a version 2

Version 1's rule (I-2, read set): *A read outside the declared set stops the build and revises this sheet.*

The read-set recorder (a Python audit hook installed before the program, in a fresh clone) found two kinds of event
outside version 1's declared set, in all three programs measured (`art/locality_inventory.py`, `art/locality.py run`,
`art/locality.py selftest`):

1. **`art/locality_inventory.py`**, a source file read.
   - It did not exist when version 1 was written.
   - It holds the inventory rule moved out of `art/locality.py`, under his commit-structure instruction for commit 1:
     *"Inventory-generation and verification tooling."*
   - The earlier read-set analyses used a declared set that already included it, without a revision of this sheet.
     That was a departure, and it is recorded as one.
2. **Bytecode probes**: `open` events on `__pycache__/*.cpython-314.pyc` paths (2 in the tool, 11 in each of the run
   and the self-test).

His ruling on the second (2026-10-24), verbatim:
- *"Accept documenting the bytecode probes as an explicit, bounded exception in the declared read-set policy, provided
  the recorder's retained output establishes that these were only probes for nonexistent cache files."*
- *"Do not rewrite the recorder's verdict to PASS."*
- *"The exception must not become a general exemption for undeclared file reads."*

Version 1's rule says an outside read revises the sheet, so the exception cannot be taken without changing it. His
ruling for that case: *"Register a new sheet/spec version and rerun the affected measurement."* This is that version.

## 2. The rule, as amended

**Declared read set:** version 1's, plus `art/locality_inventory.py`:
- `art/locality.py`, `art/locality_inventory.py`, `art/fixtures/locality/**`;
- `art/dress.py`, `art/scene_diff.py`, `art/studio_refs.py`, `art/studio_marks.py`;
- `art/director/durable.py`, `art/director/intent.py`, `art/director/ledger.py`;
- `graybox/level.py`, `graybox/tick_ref.py`, `graybox/rules_ref.py`.

No read of `art/briefs/` or `graybox/maps/` is allowed (unchanged).

**Declared writes** (unchanged in substance, made explicit): the folders `art/build` and `art/build/locality` when
absent, then `art/build/locality/REPORT.json` and `REPORT.txt`, by `run` only.

**The bounded exception: a bytecode probe.** An `open` event on a path `D/__pycache__/S.cpython-NNN.pyc` is a bytecode
probe, and is excepted from "outside the declared set", only when **all** of these hold:

1. `D/S.py` is a declared source file, read in the same run;
2. no `__pycache__` folder exists anywhere in the clone before the run, nor after it;
3. the run records no write, folder creation, rename or removal at any path containing `__pycache__`.

**What still counts as outside:**
- An `open` that fails any one of those conditions.
- Every other path outside the declared read set.
- An open of a `.pyc` whose folder existed, an open of a probe whose source is not declared or not read in the run,
  and any undeclared file of any kind.

The consequence is unchanged: such a read stops the build and revises this sheet again. A process start still makes
the read set INCOMPLETE.

## 3. How the verdicts are written

The recorder's own verdict under version 1's declared set is printed first, unchanged. It stays
`READSET OUTSIDE THE DECLARED SETS` for these runs, and it is never rewritten.

The version 2 analysis prints a second line, naming this version and every excepted probe:
- `READSET UNDER SHEET v2: WITHIN THE DECLARED SETS (N bytecode probes excepted)`; or
- `READSET UNDER SHEET v2: OUTSIDE THE DECLARED SETS`, with each path that broke the rule.

## 4. What the analysis must refuse (its plants)

The version 2 analysis is held to these cases before it is used, each on a recorded log made for it:

| case | must read |
|---|---|
| a probe whose source was read, no `__pycache__` before or after, no write under one (the control) | WITHIN, the probe excepted |
| a `__pycache__` present before the run | OUTSIDE |
| a `__pycache__` present after the run | OUTSIDE |
| a write under a `__pycache__` | OUTSIDE |
| a probe whose source is not read in the run | OUTSIDE |
| a probe whose source is not declared | OUTSIDE |
| an undeclared `.py` file read | OUTSIDE |
| a read under `art/briefs/` | OUTSIDE |
| a process start | INCOMPLETE |

## 5. What is run again under it

- **The read-set measurement:** the tool, `run` and `selftest`, in a fresh clone holding the commit's exact files,
  analysed under version 1 (verdict kept) and under version 2.
- **Commit 2's tree** gains this file and the record's update, so the final sequence runs again on the new tree:
  - the LOCALITY-0 runs;
  - the art checks;
  - the full check twice;
  - the gate twice, with the `Gated-Tree` trailer;
  - the classifier and `rung.py plants`;
  - the landing check.
- **Commit 1** is unchanged.
