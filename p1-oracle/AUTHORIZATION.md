# AUTHORIZATION — test-only P-1 G1–G6 decoder/oracle build

> **This file records a grant to *build and run* a test harness. It is NOT evidence that any gate passes, and NOT a
> change in P-1's status. P-1 remains `OPEN`.** (Owner, 2026-10-23: *"Do not represent the authorization itself as a
> test result or a change in P-1 status."*)

## The grant (verbatim, 2026-10-23)

> *"I grant the narrowly scoped authorization for the test-only G1–G6 decoder/oracle build under the exact scope stated
> in your request."* … *"The authorization is subject to all five conditions, verbatim, and all stated exclusions."*

It authorizes **only** this scratch/off-gate package: a standalone decoder/oracle implemented from the written P-1
grammar, its independently hand-calculated fixtures, and execution of the G1–G6 gate. It is **not** part of the Verðandi
gate (no row, no rung, no pinned source), and nothing here is applied, committed, or pushed by the assistant — the
owner applies it.

## The five conditions (verbatim) — preserved by this build

1. *"No production candidate or frozen reference changes."*
2. *"No production-reference freeze, candidate selection, promotion, or conformance claim."*
3. *"Independent hand-calculated vectors, with injected-routing results explicitly labeled."*
4. *"Separate verdicts for malformed input, semantic mismatch, and `BLOCKED`."*
5. *"Reproducible logs, inputs, outputs, source hashes, and exit status."*

## Exclusions (verbatim restatement, 2026-10-23)

- *"Production artifacts remain untouched. `ecs.py` must remain byte-identical to the frozen version identified by hash
  prefix `3d568d22…`."*
- *"P-1 remains `OPEN`. No candidate selection, production-reference freeze, promotion, or conformance claim is
  authorized."*
- *"G2 must earn its verdict through execution. The injected-routing results must be explicitly labeled, P1V seam
  consistency and isolation must be tested, and the real key-hash KATs must run with the seam disabled."*
- *"D4-2, below-boundary anchor proof, and D8 trust remain `BLOCKED` and out of scope."*
- *"Reproducibility is mandatory. Preserve the source hashes, independent fixtures, inputs, outputs, logs, run commands,
  and exit status. Keep malformed-input, semantic-mismatch, and `BLOCKED` verdicts distinct."*

## What a grant does not do (owner, 2026-10-23)

> *"This grant authorizes only the specified scratch-tree implementation and validation work. It does not certify the
> written specification, establish that any gate passes, or authorize additional production changes."*

## Specification under test

`ENCODING-TABLE-P1.md` rev 20 and `ADVERSARIAL-AUDIT-PLAN.md` §6b, in the SKULD-R2 scratch tree. This package derives
its rules from that written grammar; it does **not** import any production candidate implementation (there is none to
import — the candidates are hypothetical specifications).
