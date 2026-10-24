# LOCALITY-1 — batch sheet, version 3: the measurement's name

> **The earlier versions** stay byte for byte and in force:
> - version 1, `SHEET.md` (sha256 `fa717ede5c0f1bc5d8d2ab17b6f35a372028124755e7350f1e89858d3e3bbe0b`);
> - version 2, `SHEET-v2.md` (sha256 `2706f28b99c5e5d567e1f10bddd4872fefdb581217c248f3fb1c9cb126b91be1`).
>
> **This version** changes only the measurement's name. It is registered 2026-10-24, before any file is renamed.

## 1. Why

**"LOCALITY-0" is already a registered, LOCKED rung of this repository**: the floor-tile execution-format court
(blocked vs Morton).
- It was introduced in `e838288` and locked in `c95a136`.
- It is an entry in `verify/preregister.json`, and seats 18 and 19 in `verify/RUNGS.md`.
- The gate's rows read it (`verify/verify.py:3396`).
- It is the first court of `EPISTEMIC-INVARIANCE.md`.

The debate of 2026-10-24 gave this measurement the same name, and it was admitted and recorded under it. Two different
things under one registered name name neither.

His ruling: *"Name: LOCALITY-1"*. No file at `de91aaf` contains `LOCALITY-1`, `locality1` or `LOCALITY_1` in any
case; this was checked.

## 2. The alias

Several records of this measurement, written before this version, say "LOCALITY-0":
- his admission and rulings of 2026-10-24;
- `SPEC.md`, `SHEET.md` and `SHEET-v2.md`;
- `INVENTORY.jsonl`'s header ("LOCALITY-0 measures the dressing of one world");
- the comment `# locality-0 no-op` inside the inventory's hashed no-op briefs.

Wherever they name this measurement that way, the name means **LOCALITY-1**. It never means the registered floor-tile
LOCALITY-0. Their bytes stay as they are: they are frozen, registered or quoted.

## 3. What takes the new name

- the two commits' subjects and messages;
- `EVIDENCE.md`;
- the header comments of `art/locality.py` and `art/locality_inventory.py`;
- the harness's report: its format becomes `VERDANDI-LOCALITY-1 0`, and its name lines `LOCALITY-1 REPORT …`.

## 4. What keeps its form

- **The paths** (`art/locality.py`, `art/locality_inventory.py`, `art/fixtures/locality/`), as `SPEC.md` states them.
- **The refusal codes** `LOCALITY-INVENTORY`, `LOCALITY-FIXTURE` and `LOCALITY-HASHSEED`.
- **The summary lines** `LOCALITY INVENTORY HELD`, `LOCALITY HARNESS HELD` and `LOCALITY SELFTEST`.
- **Two strings in `art/locality_inventory.py`** (the excluded-verb text, and the no-op comment) that must equal the
  frozen inventory's bytes.

The frozen spec and sheet name the codes and the summary lines, and none of them carries a version number.

## 5. What runs again

The rename changes commit 1's tree (a comment) and the report's bytes, so these run again:
- commit 1's checks;
- the report twice: new hashes, recorded beside the old ones;
- the self-test and the hardening tests;
- the read-set measurement, under versions 1 and 2;
- the art checks, the full check twice, the gate twice;
- the classifier and `rung.py plants`;
- the landing check.
