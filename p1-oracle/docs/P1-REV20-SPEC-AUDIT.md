# P-1 rev 20 — Level-1 specification audit

> DESIGN / findings only, off-gate, **P-1 remains OPEN**. This audits the **specification itself** — `ENCODING-TABLE-P1.md`
> rev 20 (SKULD-R2 scratch tree) — for **completeness, ambiguity, and internal consistency**. It is **Level 1**
> (is the spec well-defined enough that two independent implementers would produce the same bytes and the same
> accept/reject decisions?), distinct from **Level 2** (does the `p1-oracle` implementation obey it). It **edits no
> specification text**, changes no production artifact, selects no candidate, and makes no conformance claim; every
> finding is a **question for the owner's ruling**, not a change. Findings are informed by having implemented the spec
> in `p1-oracle` (the places implementation forced an interpretation choice are, by definition, Level-1 findings).

Severity: **HIGH** two conforming implementers could diverge (interop or accept/reject); **MED** an ambiguity with a
safe default that should be ratified; **LOW** cosmetic / holds-by-construction / untestable.

## Findings

### S-1 — `VERSION` integer value is never pinned (MED, incompleteness; interop)
§0 *Versioning scope* mandates `u16(VERSION)` on every node, the `state_serialization` container, the record preimage,
`EFF_EMPTY_RANGE`, and the checkpoint — but **nowhere states the integer value of `VERSION`**. Only the domain-string
suffix `-0` is normative. Two implementers could emit `u16(0)` vs `u16(1)` and both claim conformance, producing
incompatible, mutually-rejected byte streams. *p1-oracle pinned `VERSION = 0`.* **Q:** ratify the v0 integer
(presumably `0`) as a normative constant in §0.

### S-2 — version is encoded twice; their relationship is unstated (MED, consistency)
Version appears in **two** places per node: the domain literal suffix (`…-0`) **and** `u16(VERSION)`. The spec never
says the two must agree, which is authoritative, or how a future bump changes each. A stream with domain `…-0` but
`u16(1)` (or vice-versa) has undefined status by the letter of the spec. *p1-oracle ties both to 0 (domain mismatch →
`DOMAIN`, u16 mismatch → `VERSION`).* **Q:** state that the suffix and `u16` both denote the same version, both change
together on a bump, and both are checked.

### S-3 — "record decoder obligations" presuppose a record wire form the spec never defines (HIGH, incompleteness)
§6 defines `record_commitment` as a **hash preimage** and the ledger as structured records; it does **not** define a
standalone serialized-record object parsed from a byte stream. Yet §6 lists *"record decoder obligations: a `LINK` tag
other than `0x00`/`0x01` reject; `seq = 0` reject; …"* — obligations that only arise when **decoding a record from
bytes**. An implementer that validates structured records (as `p1-oracle` does) **cannot reach** the "LINK-tag byte ∉
{0,1}" case at all; an implementer that parses records from bytes needs a wire format §6 does not supply. This is the
one gap that left a stated obligation **architecturally unreachable** in a faithful implementation. **Q:** either (a)
define a normative record wire format (making the LINK-tag-byte reject reachable and testable), or (b) restate the
obligation as a **preimage-construction invariant** (LINK is only ever *constructed* as `0x00`/`0x01`; a bad tag is
unconstructable) and drop the word "decoder."

### S-4 — §8 Tier-2 P6 prescribes a *method*, but the *goal* is method-independent (MED, ambiguity)
P6 says *"recompute `SHA256(KEY)` and verify **every ancestor slot** equals `chunk(d)`"* — read literally, a mandated
per-ancestor-slot walk. The **outcome** it secures (a node off its canonical path is rejected) is equally secured by
**rebuild-and-compare** (byte-equality to `construct(reconstructed state)`), which `p1-oracle` uses and documents
(`P6-REBUILD-EQUIVALENCE.md`). It is unclear whether the literal walk is normative or whether any method achieving the
rejection conforms. **Q:** clarify that P6 states a **required outcome** (off-path placement → reject) for which the
walk is one sufficient method, OR make the walk mandatory (then rebuild-and-compare alone is non-conforming).

### S-5 — bitmap "popcount == child-slot count, slots ascending" is not falsifiable in the byte form (LOW, over-specification)
§8 Tier-1 lists this as a check, but the grammar stores one `raw32` per set bitmap bit **in bitmap order**: the slot
count is *derived* from the bitmap and order is *inherently* ascending. There is no independent slot-count or
slot-index field to contradict; a malformed node surfaces only as a **framing** `TRUNCATED`/`TRAILING`. The check as
worded cannot fail on a well-framed node. **Q:** reword to a framing-length invariant
(`len == DOM+u16+type[+level]+u32+popcount·32[+SCALARS]`) and drop the implication of an independent slot count.

### S-6 — "`SCALARS` present iff ROOT" is a framing consequence, not a positive check (LOW, consistency)
There is no SCALARS-presence flag: a ROOT reads SCALARS after its children (absent → `TRUNCATED`); a non-ROOT reads
none (extra → `TRAILING`). The "iff" holds **by framing**, which is fine, but the wording implies a dedicated check.
**Q:** note it is enforced by node framing, not a flag.

### S-7 — `EMPTY`'s permitted positions are implied, not stated exhaustively (LOW, incompleteness)
§3 introduces `EMPTY` as the size-0 **component-trie top**. The spec does not explicitly forbid `EMPTY` elsewhere (an
entity-trie child, a bucket member); `construct` implies it, and `p1-oracle` rejects a stray `EMPTY` via traversal /
rebuild-compare. **Q:** state "`EMPTY` occurs only as a `component_trie_top_hash` target; anywhere else → reject."

### S-8 — content-address collision behavior is defined for an A-h-impossible event (LOW, untestable)
§4a block C(2) mandates `CONTENT_ADDRESS_COLLISION` (never silent aliasing) for two distinct encodings sharing one
digest — which §0/P8 (A-h) assumes cannot happen. Defining behavior for completeness is defensible, but no conformance
vector can construct it without breaking SHA-256. **Q:** annotate as "defined for completeness; unreachable under A-h;
not a conformance vector" (so no implementer is expected to exhibit it).

## Checked and found internally consistent / unambiguous (no action)

To show the audit is not only a defect list, these were read closely and hold together: the `chunk` function (MSB-first,
51×5-bit + 1-bit, 52 levels; the LSB-first form is withdrawn); the three distinct digest identities
(`structural_state_root` = ROOT hash, `ecs_state_digest` = `ecs.digest`, container byte-hash used nowhere); `construct`
and the bucket-placement rule (depth 52, full collision, one-slot BRANCH only over a BRANCH/terminal BUCKET); the index
convention (`2⁶⁴−1` reserved, exclusive sums `≤ 2⁶⁴−1`); `range_count` bounded by the index convention not `MAX_LEN`;
the §5 range coverage `(0, E_boundary)` with the zero-effect boundary; the §6 link truth table (genesis, mandatory
`prev` for `seq ≥ 2`, legal parentless non-genesis); block D (scalars must be int); and the explicitly **deferred /
BLOCKED** items (`effects_range_root` and `EFF_LEAF/EFF_NODE` versioning on D4-2; below-boundary anchor and non-genesis
trust on D8) — openly marked, not silent gaps.

## Disposition

Level-1 status of P-1 rev 20: **mostly well-defined, with one HIGH and three MED items worth a ruling before any Level-3
production-conformance claim.** The HIGH item (S-3) and S-1/S-2 bear on interoperability (two implementers agreeing on
bytes and on the record contract); S-4 bears on whether an implementation's validation *method* conforms. None is a
blocker for the Level-2 oracle (which pinned safe interpretations, recorded in the requirement matrix), but each is a
place the written spec — not the implementation — should be tightened. **No spec text is changed here; these are
questions for the owner.** P-1 remains `OPEN`.
