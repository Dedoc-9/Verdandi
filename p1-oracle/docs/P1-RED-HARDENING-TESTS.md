# P1 red-hardening tests — RH-T1…RH-T5 executed (0263)

> **DESIGN / probe record, off-gate, P-1 remains `OPEN`.** This records the RH-T1…RH-T5 falsification proposals from
> [`P1-RED-HARDENING-AUDIT.md`](P1-RED-HARDENING-AUDIT.md) **run as probes** against the 0263 implementation
> (`p1-oracle/probes/redharden.py`). It is the EXECUTED companion to the audit's proposals, kept separate from them per
> the owner's instruction ("Keep research-derived claims separate from executed tests"). The probes are **off the gate**
> (not imported by `run_gate.py`); they look for additional failures and do not themselves certify anything.
>
> **Headline:** **21 PASS · 2 BLOCKED · 2 N.A. · 3 OBSERVED · 0 FAIL.** No confirmed new normative defect; **no S-9
> proposed.** A FAIL would be escalated separately as a proposed S-9+ for the owner's adjudication, never a silent change
> to rev 21. Run `PYTHONHASHSEED=0 PYTHONUTF8=1 python p1-oracle/probes/redharden.py`; two runs identical; transcript at
> [`../probes/redharden.out.txt`](../probes/redharden.out.txt).

## Baseline / provenance (forward-only pin, added after 663211f)

So a future reader can reconstruct exactly which implementation and frozen dependency these off-gate results refer to:

- **Baseline commit:** `663211f` (`feat(p1-oracle): 0263 direct P6 ancestor-slot walk + RH-T red-hardening probes`).
  The probes reproduce this record's results **byte-for-byte** when re-run against that committed tree
  (`PYTHONHASHSEED=0 PYTHONUTF8=1 python p1-oracle/probes/redharden.py`, two runs identical) — this pin was verified by
  re-running against `663211f`, not inferred.
- **Frozen dependency:** `oracle/frozen/ecs.py` SHA-256 `3d568d22d812ae2321b03b7450d09109c8ff20e3308b5f9cd2a5e2fde9eb1c0b` (unchanged).
- **Scope:** off-gate RH-T1–RH-T5 probes (`probes/redharden.py`); **not** part of `run_gate.py`; **not**
  production-conformance evidence; P-1 remains `OPEN`.
- **Associated gate evidence:** `evidence/latest.json`, reported `193 PASS / 0 FAIL / 1 BLOCKED` — the gate over the same
  committed tree, which does not import the probes (so its count is independent of RH-T).
- **Environment:** CPython 3.14.5, `Windows-11-10.0.26200-SP0`, `PYTHONHASHSEED=0 PYTHONUTF8=1` — the values recorded in
  the accompanying `evidence/latest.json` from this session's run (the probe transcript itself does not record the
  environment; these are read from the gate evidence, not reconstructed from memory). MEASURED on that host, not
  independently reproduced by the owner.

Grades per row: **PASS** (apparatus behaved as the test demanded — the bad input was rejected, or the good input
accepted), **FAIL** (a real defect), **BLOCKED** (a D4-2/D8 item, never a pass), **N.A.** (the external case's mechanism
does not arise / is unconstructable under A-h), **OBSERVED** (a measurement, not a pass/fail).

## RH-T1 — resource bounds reject before work/allocation (OpenSSL CVE-2026-34180 lesson)

| probe (concrete input) | observed outcome | grade |
|---|---|---|
| `lp` length `u64(2**40)` (> `MAX_LEN`) | `LP_TOO_LONG` on the prefix, before buffering | PASS |
| `lp` length 1000 with 3 payload bytes | `TRUNCATED` (bounds check; no over-read) | PASS |
| `node_count` `u64(2**40)` (> `MAX_NODES`) | `MAX_NODES` on the prefix, before the node loop | PASS |
| `node_count` `2**32-2`, no node bytes | fast reject (`DOMAIN` on the first read; `range()` is lazy — no hang/alloc) | PASS |
| `BUCKET` count `2**32-1`, no member bytes | fast reject (`DOMAIN` on the first member) | PASS |
| two legal nodes, `max_total` = total−1 | `MAX_TOTAL` (collectively-over, legal singles) | PASS |

**Finding:** every length/count/total is checked at the point it is interpreted, before conversion, allocation, or
iteration; `u64` lengths cannot truncate to a machine int (the OpenSSL pattern), and a non-`OracleError` crash
(`MemoryError`/`OverflowError`/`RecursionError`) would have been a FAIL — none occurred. No defect.

## RH-T2 — independent canonicality: near-neighbour accept/reject (G-1)

| probe | observed outcome | grade |
|---|---|---|
| composite (2 entities; int/str/neg), both candidates | round-trips (accepting control) | PASS |
| reversed node order, both candidates | `NODE_ORDER` | PASS |
| a referenced node dropped, both candidates | `MISSING_CHILD` | PASS |
| misplaced leaf (0263 fixture), both candidates | `WALK_MISROUTE` | PASS |
| non-minimal int value (alternate form) | `INT_NONMINIMAL` | PASS |
| a **second** independent encoder written from the prose | not run — recorded **residual**, not a defect | N.A. |

**Finding:** valid-vs-malformed near-neighbours are separated with specific codes. The full RH-T2 close (a second encoder
authored from the prose, so expected and actual do not share one constructor) remains future work; G-1 stays **reduced,
not eliminated** (0262 + these probes), which is a known residual, not a defect.

## RH-T3 — structural uniqueness, cases (a)–(e)

| case | probe | observed outcome | grade |
|---|---|---|---|
| (a) | two identical child refs in one parent | `DUP_CHILD` | PASS |
| (b) | a component subtree shared across two entities | lawful DAG — one shared `LEAF_COMP`, round-trips | PASS |
| (c) | a duplicate entity key | `WALK_MISROUTE` (walk) / `DUP_KEY` (backstop, walk off) | PASS |
| (d) | two encodings, one address → `CONTENT_ADDRESS_COLLISION` | code path present; unconstructable under A-h (S-8) | N.A. |
| (e) | a reordered valid tree | `NODE_ORDER` — exactly one canonical serialization per state | PASS |

**Finding:** within-parent duplication and non-canonical structure are rejected; lawful cross-parent DAG sharing is
accepted; the content-address collision is defined-for-completeness only (unreachable without breaking SHA-256). No
demonstrated P-1 analogue of the Bitcoin CVE-2012-2459 duplicate-structure ambiguity. No defect.

## RH-T4 — worst-case work (measurement, OBSERVED — not pass/fail)

| structure | bytes | nodes | key-hash calls |
|---|---|---|---|
| wide ROOT (20 entities, distinct `chunk(0)`) | 2175 | 22 | 40 |
| deep single-path full-collision bucket (2 entities) | 3411 | 54 | 4 |
| shared component DAG (8 entities, one `hp=1`) | 980 | 10 | 1 shared `LEAF_COMP` |

**Finding (OBSERVED):** key-hash work scales with the **element count**, not the trie depth — the 52-level single-path
bucket costs only 4 key-hash calls (2 members + 2 build), and a shared subgraph is stored and validated **once**, not
per parent. This is a measurement on these shapes, **not** a proven asymptotic bound, and injected key-hash collisions
are a mechanism test only (SHA-256 routing makes cheap collisions infeasible under A-h; RH-4 premise-limited). No defect
observed. The depth-decoupling of the **key-hash** cost (vs. total node-level work, which is **not** O(N)) is recorded,
graded and bounded, in [`P1-SCALING-NOTE.md`](P1-SCALING-NOTE.md).

## RH-T5 — checkpoint trust as separate predicates (§7, D4-2/D8)

| probe | observed outcome | grade |
|---|---|---|
| digest / range / head / anchor reported apart | all reported as distinct verdicts, none collapsed | PASS |
| `effects_range_root` | stays **BLOCKED** (D4-2) | BLOCKED |
| non-genesis anchor | identity/reachability PASS, **trust BLOCKED** (D8) | BLOCKED |
| two local-valid checkpoints at one boundary, different anchors | each valid locally; **no** global-agreement function exists in `checkpoints.py` | PASS |

**Finding:** local checkpoint validity is never promoted to a claim of globally-consistent history (the RFC 6962/9162
split-view lesson); the oracle exposes no cross-checkpoint consistency inference, and D4-2 (effects-range-root) and D8
(non-genesis trust / below-boundary anchor) remain **BLOCKED**, never a pass. No defect; the blocks are reinforced.

## Adjudication

No probe produced a FAIL, so **no S-9 (or later) finding is proposed** and rev 21 is **unchanged**. The residuals are
pre-existing and already recorded: the full RH-T2 independent-encoder close (G-1 reduced, not eliminated) and the
RH-T4 formal work bound (measurement only); the D4-2/D8 items stay BLOCKED. If a future probe produces a FAIL it becomes
a **proposed** S-9+ for the owner's adjudication — these probes never silently alter the ratified spec. This is an
oracle-level (Level-2) probe record, not a conformance claim; P-1 remains `OPEN`.
