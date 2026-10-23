# p1-oracle — test-only G1–G6 decoder/oracle for the P-1 encoding contract

> **OFF-GATE / SCRATCH. Not part of the Verðandi gate. P-1 remains `OPEN`.** This package is authorized to *build and
> run* a validation harness (see [AUTHORIZATION.md](AUTHORIZATION.md)); its results are **not** a conformance claim, a
> candidate selection, a reference freeze, or a change in P-1's status. Nothing here is committed or pushed by the
> assistant — the owner applies it.

Validates the byte-level P-1 contract in `ENCODING-TABLE-P1.md` rev 20 (the SKULD-R2 scratch tree) by **execution**: a
standalone decoder/oracle implemented from the written grammar, independently hand-calculated byte vectors, planted
negative fixtures, and a deterministic gate that reports each dimension separately.

## Layout

```
p1-oracle/
├── AUTHORIZATION.md     the dated grant + five conditions + exclusions (verbatim)
├── MANIFEST.json        authorized scope, baseline/isolation facts, pinned v0 constants, commit boundaries
├── README.md            this file
├── run_gate.py          deterministic G1–G6 runner -> evidence/
├── verify_plants.py     validity check: plants a real defect, confirms each gate turns RED
├── oracle/
│   ├── decoder.py       primitives, VALUE/KEY, chunk, the two TYPED hash seams, node encode + Tier-1 decode, limits
│   ├── canonicality.py  construct(), build/serialize, Tier-2 parse + reconstruct + rebuild-and-compare
│   ├── records.py       record preimage, link table, Tier-3 replay via the frozen ECS, effect indexing
│   ├── checkpoints.py   checkpoint digest, range identity, anchor (identity/reachability/trust), BLOCKED markers
│   └── frozen/ecs.py    byte-identical frozen ECS (sha256 3d568d22…); the ONLY semantic dependency
├── fixtures/
│   ├── hand_calculated/vectors.py   expected bytes from LOCAL primitives + hashlib (never the oracle)
│   └── malformed/buckets.py         crafted misplaced-bucket vectors (+ their defect-removed counterparts)
├── tests/               test_g1..g6 + test_seams + test_buckets (+ harness)
└── evidence/            ACTUAL run outputs only (latest.json, latest.log, plants.log)
```

## Run

```bash
PYTHONHASHSEED=0 PYTHONUTF8=1 python p1-oracle/run_gate.py       # the G1–G6 gate
PYTHONHASHSEED=0 PYTHONUTF8=1 python p1-oracle/verify_plants.py  # confirm the gate bites
```

Determinism: `PYTHONHASHSEED=0`; on Windows set `PYTHONUTF8=1` for redirected output. No third-party dependencies.

## What each gate establishes (reported as a panel, never one score)

| gate | establishes | grade |
|---|---|---|
| **G1** | canonical bytes: oracle encode == independently hand-calculated literals; decode round-trips (both candidates) | MEASURED |
| **G2** | trie shape: ordinary (real SHA-256) routing; **injected** final-bit `BRANCH(51)`, full-collision `BUCKET`, bucket+leaf; seam **consistency** and **isolation**; key-hash KAT; **dedicated bucket-placement** check (`BUCKET_MISPLACED` / `BUCKET_NOT_COLLIDING`, before rebuild-compare), both candidates | MEASURED |
| **G3** | reconstruction: DAG sharing, empty maps, duplicate-key / orphan / missing-child rejection, full ECS field recovery, block-D scalar gate | MEASURED |
| **G4** | records (**both candidates A & B**): preimage bytes (hand-checked, candidate-independent), Tier-3 replay via the frozen ECS, effect indexing, wrong-commitment / atomic-rejection, link table, index bounds | MEASURED |
| **G5** | checkpoint + anchor (**both candidates A & B**): digest, range identity `(0,E_boundary)`, head==boundary (D4-3), three anchor verdicts | MEASURED, with **BLOCKED** parts kept apart |
| **G6** | reproducibility, frozen-hash, write isolation, reduced-limit bounds (3B), P1V-constants | MEASURED |

## What stays BLOCKED (never reported as a pass)

- **`effects_range_root` verification** — the range-tree algorithm + proof format are **D4-2**-deferred.
- **Below-boundary / out-of-range `history_anchor`** — needs the authenticated-prefix mechanism (**D4-2/D8**).
- **Non-genesis anchor trust** — external provenance is **D8**; only genesis is inherently trusted (D5-1).

## Seam contract (G2) — enforced by execution

The injected key-hash drives the **entire key-path** (chunk extraction, routing, canonicality validation, bucket
membership) for **both** the candidate and the oracle (consistency). Node content addresses and the §4a collection
order are **production SHA-256**, never the seam (isolation) — `decoder.node_address` is a module function that does
not take a key-hasher. `verify_plants.py` shows a reconstruct that ignores the active hasher turns G2 RED.

## Honest grading

Every PASS here is **MEASURED on this run** (Python 3.14.5, Windows; see `evidence/latest.json`). This is **artifact
and apparatus evidence**, not a proof that the written specification is correct, and it is **not independently
reproduced by the owner**. `built != adopted`, `declared != verified`. The oracle and the hand-calculated fixtures can
still share a blind spot the vectors do not probe; the gate's scope is exactly the listed vectors and plants.
