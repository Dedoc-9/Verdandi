<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# `verify/` — the gate

`python verify/verify.py` runs every row and prints `GATE PASSED` or `GATE FAILED`, then a reconcile line
naming the rowset. A change is landed only when two consecutive runs are byte-identical (`sha256` of the two
logs equal) and the gate reads PASSED. Rows that need `rustc` are SKIPPED without it, count-stable, so the
rowset digest does not depend on the toolchain being present — only the verdict does.

Off-gate instruments (wall-clock on a named host) never print inside the gate; they write records beside the
oracle with the witnesses checked first.

`pins/` holds the goldens Verðandi mints itself (today: the HUD's overlay identities and composites), each held
under laws by rows; the oracle folder holds only what Urðr certified.

`RUNGS.md` is the ledger: one graded entry per rung, with what it measured, what it does not show, and the
row that would redden if the claim were false.
