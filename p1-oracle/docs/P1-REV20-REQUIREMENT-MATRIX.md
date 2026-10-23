# P-1 rev 20 — Requirement-to-Evidence Matrix

> **DESIGN / TRACEABILITY ONLY. Off-gate, non-normative. P-1 remains `OPEN`.** This maps the normative requirements of
> `ENCODING-TABLE-P1.md` rev 20 to the evidence produced by the test-only `p1-oracle/` package at the published
> revision **`76e9d69`**. It is a control document for review and for scoping any future production-conformance test.
> It establishes **oracle-level** evidence (Level 2) only; it is **not** a conformance claim, selects no candidate,
> freezes no reference, and leaves `ecs.digest` untouched. Reported results are **MEASURED on the author's host**
> (Python 3.14.5, Windows; `evidence/latest.json`), **not independently reproduced** by the owner.

## Legend

**Status** — `VERIFIED` independent positive **and** negative vectors, apparatus shown to bite; `PARTIAL` tested but
with a named gap (missing negative, correlated provenance, or one-candidate only); `OPEN` no executable test yet, or
not testable as built; `BLOCKED` held on D4-2/D8; `FAILED` none.

**Expected-result provenance** — `HAND` byte literal written from the grammar and checkable by eye; `INDEP` derived by
an independent reference tool (`hashlib`) over hand-written bytes; `CORRELATED` fixture re-encodes the same grammar the
oracle does (agreement is cross-implementation, not an independent human derivation); `ORACLE` oracle-derived only;
`N/A`.

**A hard honesty rule for this matrix:** a requirement is not `VERIFIED` because a code path exists — only because an
executed vector in the gate exercises it and a plant shows the check bites. Where the code path exists but no gate
vector drives it, the status is `PARTIAL` or `OPEN`, and the gap is named.

Evidence references are `test_module::case` (gate rows) run under `run_gate.py`, with plant sensitivity from
`verify_plants.py`; both recorded in `evidence/latest.json` / `latest.txt` / `plants.txt`.

## Changelog — 0258 structural-rejection closure (2026-10-23)

Probed the current checkout first (no presuming), then: **fixed** ROOT (and uniformly BRANCH) duplicate-child so a
repeated child hash in one node rejects at **Tier-1 as `DUP_CHILD`** (`decoder._read_bitmap_children`) instead of
downstream as `DUP_KEY`; **added** adversarial vectors `tests/test_struct.py` (both candidates) for ROOT/BRANCH
`DUP_CHILD`, malformed inline bucket members (`DOMAIN`/`VERSION`/`BUCKET_MIXED`/`BUCKET_ORDER`/`BUCKET_DUP_KEY`/`VTYPE`),
and a misrouted-leaf `CANONICALITY` witness; **recorded** the P6 equivalence argument in
[`P6-REBUILD-EQUIVALENCE.md`](P6-REBUILD-EQUIVALENCE.md); **added** a `verify_plants` plant for the distinct-children
check. New run: **112 PASS / 0 FAIL / 1 BLOCKED**, two runs identical, **7/7 plants bite**. Prior **90 / 0 / 1** is
preserved immutably at `76e9d69` and `evidence/history/pre-0258/`. Rows R4.3, R4a.2, R8.2 and gap-list P0 items updated
below. Deferred by owner ruling: composite hand-traced vector (G-1), standalone Tier-1 negatives (G-2/G-3), link/SEQ
cases (G-5), `MAX_TOTAL` symmetry (G-7); BLOCKED items stay BLOCKED.

## Changelog — 0259 standalone Tier-1 negatives (2026-10-23)

Probed each case at its **local** decoder layer first; every malformed input already rejected there with a specific
code except **lone-surrogate-on-encode**, which raised an untyped `UnicodeEncodeError` — **hardened** to a typed
`STR_SURROGATE` (`encode_value`). **Added** `tests/test_tier1.py`: §1 int `INT_NONMINIMAL`/`INT_NEGZERO`/`INT_SIGN`,
bad `VTYPE`, `STR_UTF8` (decode), `STR_SURROGATE` (encode); §2 `KTYPE`/`KTYPE_POS`; node framing (both candidates)
wrong `DOMAIN`, wrong `VERSION`, `ROOT`-missing-scalars→`TRUNCATED`, scalars-on-non-ROOT→`TRAILING`,
popcount>children→`TRUNCATED`; container `STATE_DOM`/`VERSION`; accepting neighbours throughout. Added a `verify_plants`
plant that disables the minimal/sign/UTF-8 guards. New run **136 PASS / 0 FAIL / 1 BLOCKED**, two runs identical,
**8/8 plants bite**; 0258 evidence kept at `evidence/history/pre-0259/`. Rows R1.1–R1.3, R2.1, R0.6, R8.1 and gap item
G-2 updated. *Honest structural notes:* slot order is implied by the bitmap, so "non-ascending slots" is **not
representable** (no negative possible); a popcount/child mismatch surfaces as a framing `TRUNCATED`/`TRAILING`, not a
dedicated `POPCOUNT` code; record/checkpoint domain/VERSION are preimage-hashed (no byte-decoder), so those carriers
are covered by commitment recomputation, not a local `DOMAIN`/`VERSION` reject.

---

## §0 Primitives, resource limits, versioning

| ID | Normative requirement | Component | Pos / Neg vectors | Provenance | Evidence | Status | Gap / next action |
|---|---|---|---|---|---|---|---|
| R0.1 | big-endian fixed-width `u8/u16/u32/u64`; `lp = u64(len)‖bytes` | `decoder` primitives | pos: value/key/node encodings; neg: truncation→`TRUNCATED` | HAND | `test_g1` value/key vectors | PARTIAL | truncation reject is incidental (no dedicated vector); add explicit truncated-field negatives |
| R0.2 | legal integer ranges; indices in `[0,2⁶⁴−2]`, `2⁶⁴−1` reserved; exclusive sums `≤2⁶⁴−1` | `decoder`,`records` | pos/neg: `test_g4::index_bounds`; reduced-limit `test_g6` | HAND | G4 index bounds; G6 reduced-limit | VERIFIED | — |
| R0.3 | `MAX_HASH_CHUNKS=52`; 51×5-bit + 1-bit; two-level depth ≤ 53+53 | `decoder.chunk`,`_construct` | pos: injected final-bit reaches `BRANCH(51)` / depth-52 bucket | INDEP (injected) | `test_seams` final-bit/full-collision | PARTIAL | the 53-node max-chain bound is not asserted as its own vector |
| R0.4 | content-addressing is a DAG; `MAX_NODES` counts unique-by-hash; `MAX_TOTAL` sums unique bytes; shared node once | `canonicality`,`parse_collection` | pos: DAG share `test_g3`; neg: reduced `MAX_NODES` `test_g6` | HAND/ORACLE | G3 DAG; G6 reduced node-count | VERIFIED | `MAX_TOTAL` reduced-limit not separately driven (only `MAX_NODES`) — PARTIAL on the total bound |
| R0.5 | limits checked incrementally — reject **before** over-allocation | `Reader.lp`,`parse_collection` | neg: reduced `MAX_LEN` rejects on the length prefix before the body | — | `test_g6::reduced_limit_lp` | VERIFIED (lp) | node/total incrementality asserted only indirectly |
| R0.6 | `u16(VERSION)` carried by the six node types, `state_serialization`, record, `EFF_EMPTY_RANGE`, checkpoint; **not** `EFF_LEAF/EFF_NODE` | encoders, `_read_version` | pos: every encoding carries `u16(0)`; neg: wrong version→`VERSION` (node + container) | HAND | `test_tier1` wrong-VERSION node (both cands) + container | VERIFIED (decoded carriers) | record/checkpoint are preimage-hashed (no byte-decoder) → their VERSION is covered by commitment recomputation, not a local `VERSION` reject |

## §1 Values

| ID | Normative requirement | Component | Pos / Neg vectors | Provenance | Evidence | Status | Gap / next action |
|---|---|---|---|---|---|---|---|
| R1.1 | `VTYPE 0x01` int / `0x02` str; one accepted encoding per value | `decode_value` | pos: int & str vectors; neg: bad `VTYPE`→`VTYPE` | HAND | `test_g1` value vectors; `test_tier1` bad-VTYPE | VERIFIED | closed 0259 |
| R1.2 | int = sign byte + minimal magnitude; positive-zero only; neg-zero/non-minimal/bad-sign rejected | `decode_value` | pos: `0,10,255,256,-7`; neg: `INT_NONMINIMAL`/`INT_NEGZERO`/`INT_SIGN` | HAND | `test_g1` positives; `test_tier1` negatives + plant | VERIFIED | closed 0259 |
| R1.3 | str UTF-8, no normalization; invalid UTF-8 / lone surrogate rejected | `decode_value`,`encode_value` | pos: `"orc"`,`""`, composed `é`; neg: `STR_UTF8` (decode), `STR_SURROGATE` (encode) | HAND | `test_g1`; `test_tier1` UTF-8 + surrogate | VERIFIED | closed 0259 (encode-surrogate hardened to a typed reject) |

## §2 Keys and chunk extraction

| ID | Normative requirement | Component | Pos / Neg vectors | Provenance | Evidence | Status | Gap / next action |
|---|---|---|---|---|---|---|---|
| R2.1 | `KEY = KTYPE(0x10/0x11)‖lp(utf8)`; order by full KEY bytes | `encode_key`,`decode_key` | pos: key vectors; neg: `KTYPE`, `KTYPE_POS` | HAND | `test_g1` key vectors; `test_tier1` KTYPE/position | VERIFIED | closed 0259 |
| R2.2 | `chunk(d)` MSB-first, 51×5-bit then 1-bit (52 levels) | `decoder.chunk` | pos: real-SHA KAT; injected final-bit/full-collision | HAND (KAT) / INDEP | `test_seams::kat`, final-bit, full-collision | VERIFIED | — |

## §3 State → tree hierarchy

| ID | Normative requirement | Component | Pos / Neg vectors | Provenance | Evidence | Status | Gap / next action |
|---|---|---|---|---|---|---|---|
| R3.1 | entity-trie top always `ROOT` (binds `SCALARS`); component top = `construct(K,0)` (EMPTY/bare LEAF_COMP/BRANCH) | `build_state` | pos: genesis / singleton / one-comp / multi-comp | HAND (leaf) + CORRELATED (composite) | G1 serializations; `test_g2` ordinary | VERIFIED | composite-byte provenance is CORRELATED (see Gap G-1) |
| R3.2 | `SCALARS` = `DOM‖A·VALUE‖S·VALUE‖C·VALUE`; all three **int** (block D); string scalar rejected | `_decode_scalars` | pos: round-trips; neg: string scalar→`SCALAR_NOT_INT` | HAND | `test_g3::scalar_type`; plant `verify_plants` | VERIFIED | — |
| R3.3 | duplicate logical keys unrepresentable; rejected on descent | `reconstruct` | neg: duplicate entity key→`DUP_KEY` | ORACLE | `test_g3::dup_key` | PARTIAL | component-level duplicate not separately crafted |

## §4 Node grammar, construction, buckets

| ID | Normative requirement | Component | Pos / Neg vectors | Provenance | Evidence | Status | Gap / next action |
|---|---|---|---|---|---|---|---|
| R4.1 | per-type grammar (domain/version/type/fields); B carries `level` ROOT=0/BRANCH 0–51/BUCKET=52 | `enc_*`,`read_one_node` | pos: node encodings A & B; neg: level-range, bitmap-high-bits | HAND | G1 EMPTY/LEAF_COMP both cands; `test_g2::bitmap_high` | VERIFIED | — |
| R4.2 | `construct()` is the one deterministic shape; decoder rejects any non-`construct` shape | `_construct`,`reconstruct` | pos: all round-trips; neg: reorder→`NODE_ORDER`, orphan→`CANONICALITY` | HAND/ORACLE | G1/G2/G3 | VERIFIED (via rebuild-and-compare) | method note M-1: shape is enforced by rebuild-compare, not the literal P6 walk |
| R4.3 | bucket: inline leaves, by-hash children; leaf-type-per-trie; `count≥2`; canonical order; no dup key | `enc_bucket`,`read_one_node` | pos: injected full-collision bucket; neg: `count<2`, mixed, order, dup, wrong-domain/version, bad-value | HAND/INDEP | `test_g2::bucket_count`; `test_seams::full_collision`; `test_struct` inline members (both cands) | VERIFIED | closed 0258 — inline-member malformations rejected for their specific local reason |
| R4.4 | bucket placement: **depth 52 and members fully collide** (recompute under active hash) else misplaced | `_check_buckets` | pos: placed-ok; neg: `BUCKET_MISPLACED`, `BUCKET_NOT_COLLIDING` | INDEP (injected) | `test_buckets` (A & B); plant `verify_plants` | VERIFIED | — |
| R4.5 | node address = `SHA256(node encoding)`; Candidate A recomputes, stores no hash field | `node_address` | pos: all serializations; isolation (seam never reaches it) | — | `test_seams::isolation` | VERIFIED | — |

## §4a State serialization

| ID | Normative requirement | Component | Pos / Neg vectors | Provenance | Evidence | Status | Gap / next action |
|---|---|---|---|---|---|---|---|
| R4a.1 | container = `DOM‖u16‖root_hash‖u64(count)‖nodes`, ascending by node-hash | `serialize_state`,`parse_collection` | pos: serializations; neg: reorder→`NODE_ORDER` | HAND (leaf)/CORRELATED | G1; `test_g2::reorder` | VERIFIED | composite provenance CORRELATED (G-1) |
| R4a.2 | unique nodes; dup-entry reject; content-address-collision **reported not aliased**; dup child in one parent reject; shared-across-parents lawful | `parse_collection`,`_read_bitmap_children` | pos: DAG share; neg: `DUP_CHILD` (ROOT & BRANCH, Tier-1), `DUP_ENTRY`/`CONTENT_ADDRESS_COLLISION` (code paths) | ORACLE | G3 DAG share; `test_struct` ROOT/BRANCH `DUP_CHILD` + plant | PARTIAL | **`DUP_CHILD` closed 0258 (VERIFIED, both cands)**; `DUP_ENTRY` still lacks a vector; **content-address collision OPEN — untestable without breaking SHA-256** |
| R4a.3 | reconstruction recovers every ECS field; `MISSING_CHILD` vs malformed; orphan rejected | `reconstruct` | pos: full-field recovery; neg: `MISSING_CHILD`, orphan→`CANONICALITY` | ORACLE | `test_g3::fields`; `test_g2::missing`; `test_g3::orphan` | VERIFIED | — |
| R4a.4 | three distinct digest identities (`structural_state_root`=ROOT hash; `ecs_state_digest`=`ecs.digest`; container byte-hash used nowhere) | `records`,`checkpoints` | pos: commitments bind ROOT hash + ecs.digest | ORACLE | used in G4/G5 | PARTIAL | **gap: no dedicated `P1V-identity` vector asserting the three are distinct and the container hash is unused** — add it |

## §5 Effects

| ID | Normative requirement | Component | Pos / Neg vectors | Provenance | Evidence | Status | Gap / next action |
|---|---|---|---|---|---|---|---|
| R5.1 | `EFF_LEAF`/`EFF_NODE`/`EFF_EMPTY_RANGE` preimages | `records` | `EFF_LEAF` via index bounds; `EFF_EMPTY_RANGE` defined | HAND | `test_g4::index_bounds` | PARTIAL | `EFF_NODE`/`EFF_EMPTY_RANGE` not exercised; `EFF_NODE` range-tree is BLOCKED (R5.6) |
| R5.2 | `effect_index` assignment: global forward log, `base=L`,`count=c`, emission order, carries `commit_seq` | `verify_ledger` | pos: 0/1/multi-effect positions | ORACLE | `test_g4::ledger_accept` (both cands) | VERIFIED | — |
| R5.3 | index arithmetic convention (reserved `2⁶⁴−1`, exclusive sums) | `records` | pos/neg: `index_bounds` | HAND | `test_g4::index_bounds` | VERIFIED | — |
| R5.4 | `range_count` bounded only by the index convention, **not** `MAX_LEN` | `records` | (arithmetic validity of `range_count>MAX_LEN`) | — | — | OPEN | no vector asserts `range_count>MAX_LEN` is accepted on arithmetic grounds |
| R5.5 | coverage `(0, E_boundary)` recomputed from retained records; zero-effect boundary | `checkpoints`,`verify_ledger` | pos/neg: range identity; wrong range→FAIL | ORACLE | `test_g5::valid`,`range_bad` | VERIFIED | — |
| R5.6 | `effects_range_root` construction **and verification** | — | — | — | — | **BLOCKED (D4-2)** | range-tree algorithm + proof format undefined; never a pass |
| R5.7 | pruning: retain-full-prefix this milestone; prefix-pruning deferred | `checkpoints` | recompute-from-zero holds under retain-full-prefix | ORACLE | implicit in G5 | VERIFIED / BLOCKED | prefix-pruning path BLOCKED (D4-2/D8) |

## Changelog — 0260 link / sequence validation (2026-10-23)

Probed first: `SEQ_ZERO`, `SEQ_ORDER`, `PREV_LINK` (unknown/forward), `PARENT_LINK` (unknown/forward/self) all fire at
their local check; valid linear / parentless-non-genesis / parent=earlier accept. **Added** `tests/test_links.py` (both
candidates), each negative isolated on the record whose check fires, with accepting neighbours, + a plant that disables
the link/sequence checks. New run **156 PASS / 0 FAIL / 1 BLOCKED**, two runs identical, **9/9 plants bite**; 0259
evidence kept at `evidence/history/pre-0260/`. Rows R6.4, R6.5 and gap G-5 updated. *Honest findings:* (1) `SEQ_ZERO` is
**doubly guarded** (`verify_ledger` and `record_preimage`), so the link/seq plant flips 12 of 14 negatives — defence in
depth, not a miss. (2) The oracle has **no record byte-decoder** (records are structured dicts + preimage hashing), so
an invalid **LINK-tag byte** (≠ 0x00/0x01) is **not reachable** and stays **OPEN** — faking it would need a record
byte-parser, beyond G-5.

## §6 Records, commitments, links

| ID | Normative requirement | Component | Pos / Neg vectors | Provenance | Evidence | Status | Gap / next action |
|---|---|---|---|---|---|---|---|
| R6.1 | typed commitment wrappers recompute (`ecs_`/`structural_state_commitment`) | `records` | neg: wrong `ecs`/`struct` commitment→`SEMANTIC` | HAND | `test_g4::wrong_ecs`,`wrong_struct` (both cands) | VERIFIED | — |
| R6.2 | record preimage layout (`Q/V/W/N/F/S/T`, `EVENT/OP/EFFECTS/LINK`) | `record_preimage` | pos: hand-calculated preimage; A==B candidate-independence | HAND | `test_g4::preimage_bytes` | VERIFIED | — |
| R6.3 | Tier-3 replay via **frozen ECS**; effects one-for-one; unknown/wrong-arity/`fail` → whole-event `SEMANTIC`, no partial | `replay_event`,`verify_ledger` | neg: unknown / fail-after-valid / wrong-arity; atomicity | ORACLE | `test_g4::atomic` (both cands); plant | VERIFIED | — |
| R6.4 | link truth table (genesis `0x00`/`0x00`; `seq≥2` prev mandatory; parentless non-genesis legal; forward/self/unknown rejected) | `verify_ledger` | neg: `GENESIS_PREV`, `PREV_LINK` (unknown/forward), `PARENT_LINK` (unknown/forward/self); pos: linear, parentless non-genesis, parent=earlier | ORACLE | `test_g4::links`, `test_links` (both cands) + plant | VERIFIED | closed 0260 (forward/self/unknown share the `PARENT_LINK` = "not an earlier record" code) |
| R6.5 | record decoder obligations: `LINK` tag ∉{0,1} reject; `seq=0` reject; seq order; overflow | `records`,`verify_ledger` | neg: `SEQ_ZERO`, `SEQ_ORDER`, overflow (R5.3) | ORACLE | `test_links` SEQ_ZERO/SEQ_ORDER (both cands); `test_g4` overflow | PARTIAL | `SEQ_ZERO`/`SEQ_ORDER` closed 0260 (SEQ_ZERO doubly-guarded); **bad-LINK-tag byte OPEN — no record byte-decoder in the oracle** |

## §7 Checkpoint and anchor

| ID | Normative requirement | Component | Pos / Neg vectors | Provenance | Evidence | Status | Gap / next action |
|---|---|---|---|---|---|---|---|
| R7.1 | `checkpoint_digest` preimage (all fields) | `checkpoints` | pos: valid; neg: tampered field vs expected digest | ORACLE | `test_g5::valid`,`digest_bad` | VERIFIED | — |
| R7.2 | `checkpoint_head_seq == pruning_boundary_seq` invariant (D4-3) | `checkpoints` | neg: head≠boundary→FAIL | ORACLE | `test_g5::head_bad` | VERIFIED | — |
| R7.3 | range identity `(0,E_boundary)` bound in checkpoint | `checkpoints` | pos/neg: `range_identity` | ORACLE | `test_g5::valid`,`range_bad` | VERIFIED | — |
| R7.4 | `effects_range_root` commits to exactly the prefix | — | — | — | — | **BLOCKED (D4-2)** | reported BLOCKED, never a pass |
| R7.5 | anchor: identity / reachability / trust reported **apart**; retained `prev` walk; genesis inherently trusted (D5-1) | `checkpoints._walk_prev` | pos: genesis identity+reachability+trust; non-genesis trust BLOCKED | ORACLE | `test_g5::valid`,`nongenesis` | VERIFIED / BLOCKED | non-genesis **trust** BLOCKED (D8) |
| R7.6 | below-boundary / out-of-range anchor | `checkpoints` | neg: out-of-range→`BLOCKED` | ORACLE | `test_g5::out_of_range` | **BLOCKED (D4-2/D8)** | correctly held, not pass/fail |

## §8 Decoder tiers

| ID | Normative requirement | Component | Pos / Neg vectors | Provenance | Evidence | Status | Gap / next action |
|---|---|---|---|---|---|---|---|
| R8.1 | Tier-1 local: framing, minimal int, UTF-8, `KTYPE`, `node_type`, domain, single `VERSION`, popcount==slots ascending, `SCALARS` iff ROOT, bucket `count≥2`/order/no-dup, B `level` in range | `read_one_node` | neg: domain, VERSION, minimal-int, UTF-8, KTYPE, SCALARS-iff-ROOT (framing), popcount (framing), bucket count/order/dup/mixed, bitmap-high-bits, scalar-type | HAND | `test_tier1` (both cands), `test_g2`, `test_g3`, `test_struct` | VERIFIED | closed 0259. Structural: non-ascending slots not representable (bitmap-implied); popcount mismatch → framing `TRUNCATED`/`TRAILING`, not a dedicated code |
| R8.2 | Tier-2 whole-state: `construct` shape, top-node rules, **P6 full key-path** (every ancestor slot = `chunk(d)`), no dup key, shared-root lawful, distinct children, reachable/unique | `reconstruct`,`_check_buckets` | pos: round-trips; neg: misrouted leaf→`CANONICALITY`, `MISSING_CHILD`, `DUP_CHILD`, bucket placement | ORACLE | G2/G3/`test_buckets`/`test_struct` misrouting | VERIFIED (equivalent, documented) | **M-1 closed 0258: the rebuild-and-compare ⇒ P6 argument is recorded in `docs/P6-REBUILD-EQUIVALENCE.md` with a planted misrouting witness; a literal ancestor-walk remains optional defence-in-depth** |
| R8.3 | Tier-3 semantic: replay, recompute **both** commitments, reject re-wrapped-over-changed-field (DIG-08) | `verify_ledger` | neg: wrong `ecs`/`struct` commitment | ORACLE | `test_g4::wrong_ecs`,`wrong_struct` | VERIFIED | — |

---

## Prioritized gap list (for the next milestone, all off-gate, no production change)

**Correlated-provenance risk (highest — it is the limit of Level-2 evidence):**
- **G-1.** For composite serializations (ROOT, multi-node trees), the "expected bytes" in `fixtures/hand_calculated/vectors.py`
  are built by re-encoding the same grammar the oracle implements, then hashing with `hashlib`. The **leaf** literals
  (EMPTY, LEAF_COMP, VALUE sign-byte, KEY) are genuinely HAND and checkable by eye; the composite structure is
  `CORRELATED`. A shared misreading of the grammar would pass G1. *Next:* add a few fully hand-traced composite
  byte-strings (whole container bytes written out by hand for one tiny state), and/or a second independent encoder
  authored from the prose without reading the oracle.

**Missing negative vectors (Tier-1 rejections) — CLOSED across 0258/0259:**
- **G-2.** §1/§2 — **CLOSED 0259:** `INT_NONMINIMAL`, `INT_NEGZERO`, `INT_SIGN`, bad `VTYPE`, invalid UTF-8 (decode) +
  lone surrogate (encode, now typed `STR_SURROGATE`), bad `KTYPE`, KTYPE-position — all driven by `test_tier1` + plant.
  (R1.1–R1.3, R2.1)
- **G-3.** §8/§4 — **CLOSED (0258 + 0259):** bucket member malformations (`test_struct`, 0258); standalone-node wrong
  `DOMAIN`/`VERSION`, `SCALARS`-iff-ROOT and popcount via framing `TRUNCATED`/`TRAILING` (`test_tier1`, 0259).
  *Structural:* non-ascending slots are bitmap-implied (not representable); record/checkpoint carriers are
  preimage-hashed. (R8.1, R0.6)
- **G-4.** §4a — **`DUP_CHILD` CLOSED 0258** (ROOT & BRANCH, both candidates, Tier-1, + plant). **Still open:**
  `DUP_ENTRY` as a dedicated vector. (R4a.2)
- **G-5.** §6 — **CLOSED 0260** except one architectural OPEN: `SEQ_ZERO`, `SEQ_ORDER`, forward/self/unknown `parent`,
  forward/unknown `prev` all driven (`test_links`, both cands) + plant. **Still OPEN (architectural):** invalid
  **LINK-tag byte** — the oracle has no record byte-decoder, so a raw tag ≠ 0x00/0x01 is unreachable without adding one.
  (R6.4, R6.5)
- **G-6.** §4a: dedicated `P1V-identity` (three digests distinct; container hash unused). (R4a.4)

**Method equivalence — CLOSED 0258:**
- **M-1.** The rebuild-and-compare ⇒ P6 argument is recorded in [`P6-REBUILD-EQUIVALENCE.md`](P6-REBUILD-EQUIVALENCE.md),
  with its assumptions (complete parsing, unique-key recovery, consistent active hasher, seam-independent addressing,
  whole-byte comparison, explicit bucket placement) each tied to a test, and a planted misrouting witness
  (`test_struct`) that rejects with `CANONICALITY`. An explicit per-ancestor-slot walk remains optional defence-in-depth.

**Blocked (held on D4-2 / D8; must stay BLOCKED, never a pass):**
- **B-1.** `effects_range_root` construction + verification (R5.6, R7.4) — D4-2.
- **B-2.** Below-boundary / out-of-range anchor proof (R7.6) — D4-2/D8.
- **B-3.** Non-genesis anchor **trust** (R7.5) — D8.
- **B-4.** Content-address collision behavior (R4a.2) — OPEN by nature: defined, not testable without breaking SHA-256.

**Scope notes:**
- `range_count > MAX_LEN` arithmetic-validity vector is absent (R5.4) — OPEN, low priority.
- The `MAX_TOTAL` reduced-limit boundary is not separately driven (R0.4) — PARTIAL.

## What this matrix does and does not establish

It records **Level-2 (oracle) evidence** against P-1 rev 20 at `76e9d69`, with every requirement given a status and
every gap named. It does **not** establish Level-1 (that the specification is complete and unambiguous across all
clauses) or Level-3 (that a production P-1 implementation conforms — none exists; `ecs.digest` is untouched; candidate
selection and P-1 ratification are `OPEN` and unauthorized). The correlated-provenance limit (G-1) means even a fully
green gate is cross-implementation agreement plus eye-checkable leaves — not a proof the spec is correctly read.
