# P-1 rev 20 → rev 21 — amendment (v3) — RATIFIED & APPLIED 2026-10-23

> **RATIFIED by the owner and APPLIED to `ENCODING-TABLE-P1.md` as rev 21 (2026-10-23); the SKULD-R2 scratch
> `MANIFEST.sha256` was refreshed.** The normative text below is now in the spec. **0263 (the P6 walk) is NOT
> implemented**, R8.2 stays **PARTIAL**, M-1 **reopened**, the P6 equivalence **unproved**, and no P6/production
> gap is closed. `ecs.py` (`3d568d22…`) and `ecs.digest` are untouched. This document is retained as the ratification
> record. (History: it)
> proposes the edits resolving the Level-1 findings S-1…S-8 (owner-adjudicated 2026-10-23), with S-4 resolved by
> **option (B): add a literal per-ancestor-slot walk as direct P6 enforcement.** For each finding: the **location** in
> `ENCODING-TABLE-P1.md`, the proposed **[N]ormative** / **(note)** text, and an **impact trace** that distinguishes a
> **new normative requirement** from behaviour the oracle already implements, and names the **code / test / matrix**
> changes. Editing the spec to rev 21, bumping the rev, refreshing the manifest, implementing the walk, and marking any
> gap closed each need the owner's **separate explicit approval** (of the text, and for the walk, of the evidence).
> P-1 remains `OPEN`; `ecs.digest` untouched.

Impact-trace legend per finding: **New-normative?** (does the spec gain a requirement, even one the oracle already
meets) · **Code?** (oracle source must change) · **Tests?** · **Matrix rows**.

---

## S-1 — pin `VERSION = 0` (confirmed defect)
**Location:** §0 *Versioning scope (P3)*, append.
- **[N]** `VERSION` is the unsigned 16-bit integer **0** in v0; every carrier the clause enumerates emits `u16(0)`,
  field order/widths unchanged.
- (note) A different integer is a different format version carried identically by the same set.
**Impact trace:** New-normative **YES** (the integer was unpinned; pinning it is a genuinely new requirement the oracle
*happens* to satisfy). Code **no** (`decoder.VERSION = 0` already). Tests **no** (`test_g6` P1V-constants already
asserts `== 0`). Matrix: R0.6 note — "VERSION value now normatively pinned (was implementation choice)".

## S-2 — version in domain suffix and `u16`: require agreement (confirmed defect)
**Location:** §0 *Versioning scope (P3)*, after S-1.
- **[N] Agreement.** Where a domain suffix (`…-0`) and a `u16(VERSION)` field **coexist**, they denote the **same**
  version; a decoder that reads both **rejects** any disagreement.
- **[N] Acceptance (independent of agreement).** The applicable decoder **rejects an unsupported version**. A matching
  pair of **unsupported** values — e.g. a future `…-1` suffix with `u16(1)` that agree with each other — is **still
  rejected**; checking agreement alone is **not** sufficient for acceptance.
- **[N] Boundaries.** Agreement and acceptance are checked at the validation boundaries that actually exist — **node**
  and **container (§4a)** decoding, where a decoder reads both. For the **record** and **checkpoint** preimages (no
  byte-decoder, per S-3), the prescribed version is emitted consistently **by construction**; that is a **construction**
  rule, **not** a decoding rule, and this clause introduces **no** record/checkpoint byte-decoder.
- (note) Both fields are kept deliberately (domain separation + explicit field); the specific error label (the oracle's
  `DOMAIN` vs `VERSION`) is **not** mandated.
**Impact trace:** New-normative **YES** (agreement requirement is new). Code **no** (both checked already). Tests **no**
(`test_tier1` drives both). Matrix: R0.6 note — add the agreement requirement; keep "error labels are impl policy".

## S-3 — record obligations as a preimage-construction invariant, not a wire decoder (confirmed defect, HIGH)
**Location:** §6, the "record decoder obligations" paragraph — **replace framing**.
- **[N]** A valid `Commit` record's `LINK` is one of the two specified semantic values; its **preimage encoding emits
  exactly `0x00` or `0x01`**. The commit **`seq`** is nonzero (`seq ≥ 1`) and in the contiguous **commit-chain** position
  its ledger position implies — both already stated in §6; this amendment introduces **no** new sequence rule.
- **[N]** The §5 **effects-index** invariant (`base_effect_index + count ≤ 2⁶⁴−1`, the exclusive-sum / index convention)
  is a **separate** check on **effects-log indices**, not on the commit `seq`; the two indices are distinct and must not
  be conflated.
- **[N]** These are **structured-record / preimage-construction** invariants. P-1 v0 defines **no standalone record
  wire format**, requires **no record byte-decoder**, and conformance does **not** require rejecting a raw `LINK`-tag
  byte ∉ {0,1}.
- (note) A future, separately-authorized byte-decoding requirement must first define the complete record wire format.
- Remove "record decoder obligations" and any wording implying an undefined normative byte decoder.
**Impact trace:** New-normative **re-scope** (narrows an over-broad obligation; no new runtime requirement). Code **no**.
Tests **no**. Matrix: **R6.5 + gap list** — the invalid-LINK-**byte** item moves from *"architectural OPEN"* to **N/A
by the preimage-construction contract** (it was mis-scoped, not a missing test).

## S-4 — P6: outcome mandatory; add the literal ancestor-slot walk (option B) (clarification + implementation)
**Location:** §8 Tier-2, the "Full key-path validation (P6)" sentence — **restructure** into outcome + method; the
oracle gains a direct walk.
- **[N] Normative requirement — branch path.** For **each** `LEAF_*` and **each** `BUCKET` member, at **every branch**
  on its root-to-element path the element's **own** key hash (`H = SHA256(KEY)`, §2) must agree with the slot it
  occupies: the slot equals `chunk(d)`, computed with the prescribed chunk index and root-depth convention, for each
  branch depth `d` on the path (`d = 0…51`).
- **[N] Normative requirement — bucket placement.** A `BUCKET` is valid **only at depth 52**, i.e. **after** the path's
  52 chunks (`chunk(0…51)`) have been consumed; depth 52 is the **terminal** position, **not** a branch slot. Every
  bucket member must match the **complete** path **to** that bucket (all 52 chunks shared); there is **no additional
  branch-slot check inside the bucket** — members are terminal, not re-routed at depth 52.
- Any off-path placement, or a `BUCKET` anywhere but depth 52, is **rejected**, never repaired or canonicalized first.
- **[N] Alternative-method conformance condition:** an implementation may enforce this requirement by a method other
  than the explicit walk **only if it proves** that its method establishes the same requirement for **all** admitted
  inputs. This is a conformance **condition to be discharged**, **not** an assertion that any current method (e.g.
  rebuild-and-compare) satisfies it — the present rebuild-and-compare equivalence is **unproved**.
- **Implementation requirement (the oracle):** the oracle performs the **explicit ancestor-slot walk** as its direct
  enforcement of the normative requirement (detailed below).
- **Current status (updated 2026-10-23, 0263):** the walk is **implemented and tested** (`canonicality._p6_walk`,
  `tests/test_walk.py`, both candidates; 193 PASS / 0 FAIL / 1 BLOCKED, 12/12 plants bite). Its **universal** correctness
  is still **not** demonstrated — the evidence is MEASURED on the enumerated vectors only. Implementing the walk does
  **not** by itself close R8.2 to universal VERIFIED; R8.2 is marked VERIFIED **on the tested vectors, pending the
  owner's review**, and the walk's "correctness" remains an obligation reviewed against the normative depth rules.
**Option-(B) implementation (0263, DONE — pending the owner's review of text + evidence):**
1. **Direct walk = P6 enforcement, exact depth semantics.** For **every** leaf key, recompute `H` via the **active**
   hasher (production, or the authorized **key-hash** seam). At **each** branch depth `d` on the root-to-leaf path, the
   leaf's `chunk(d)` **must equal the slot it occupies** in that ancestor; a mismatch at **any** depth is rejected —
   checking the immediate parent alone is **not** sufficient. For a `BUCKET`, **every member key** must satisfy the
   **complete** path: the shared `chunk(0…51)` down the branch chain **and** the final routing decision that places the
   bucket at **depth 52** (all members' `H` agree on all 52 chunks). Final-bit handling matches the spec's exact
   52-chunk definition (`chunk(51)` is the 1-bit chunk; `BUCKET` at `d = 52`). The validator **rejects** a misplaced
   node; it never repairs or canonicalizes before checking. **Implemented codes (0263):** `WALK_MISROUTE` (slot ≠
   `chunk(d)` at some ancestor level); the bucket-depth and bucket-collision cases keep their existing specific codes
   `BUCKET_MISPLACED` (not at terminal depth 52) and `BUCKET_NOT_COLLIDING` (members not fully colliding); `WALK_DEPTH`
   guards a branch nesting past level 51 and, for Candidate B, a stored `level` that disagrees with the structural depth;
   `WALK_EMPTY_PLACEMENT` guards an `EMPTY` outside a size-0 component-trie top (S-7).
2. **Rebuild-and-compare stays as an independent defence, not the proof.** Both enforce canonicality through distinct
   mechanisms. **Shared dependencies are documented, not hidden:** both use `read_one_node` parsing, `node_address`
   hashing, and the active key-hasher — independence is *partial* (distinct traversal/logic, shared parse+hash). No
   full-independence claim is made. **The walk's correctness rests on its own logic** (it literally checks the spec's
   `chunk(d)` rule at each depth), reviewed against the normative depth rules — not on any equivalence argument.
3. **No node-address seam.** Only the already-authorized key-hash seam is used; node addressing stays production SHA-256.

**Impact trace:** New-normative **YES** (outcome made explicit; proof-obligation clause new). Code **YES** (0263 added
the walk to `canonicality.py`, run before rebuild-and-compare). Tests **YES** (`test_walk.py`, done). Matrix: **R8.2 is
now VERIFIED on the tested vectors (0263), pending the owner's review** — never promoted to full/universal VERIFIED, and
attribution remains unproven.

### S-4 test plan (safeguard 4; implemented 0263 — `tests/test_walk.py`, both candidates)
- Retain the existing `CANONICALITY` misrouting/placement tests (they continue to assert rejection).
- Walk-specific vectors, **both candidates**, each asserted to reject with the specific `WALK_*` code (the walk runs
  **before** rebuild-and-compare, so the observed code attributes the verdict to the walk): a leaf off-path at
  **depth 0**; a leaf off-path at a **deeper** ancestor (`d > 0`, multi-level trie); a `BUCKET` whose members do **not**
  all fully collide (off the shared path); a `BUCKET` at the **wrong depth** (≠ 52) incl. the depth-52 boundary.
- Accepting controls: correctly-routed counterparts pass.
- **Attribution — reported UNPROVEN, by construction.** Rebuild-and-compare is a *complete* canonicality check, so it
  rejects every misrouted tree too; there is **no witness the walk catches that rebuild-and-compare accepts** (a
  canonical tree has no off-path node). So "disable the walk → the vector is accepted" is **impossible**, and the
  walk's **necessity cannot be demonstrated**. A disable-the-walk plant therefore shows only that the **code** changes
  (`WALK_*` → `CANONICALITY`) while the tree is **still rejected** — proving the walk *produced* the `WALK_*` verdict,
  **not** that it is necessary. The matrix records attribution as **unproven**; the walk's value is a **direct** P6
  check (independent of the unproved equivalence), a second mechanism, and a specific code — not a unique catch.
- Key-hash seam only; no node-address seam.

## S-5 — bitmap: one `raw32` per set bit (clarification only)
**Location:** §8 Tier-1, the "popcount == child-slot count, slots ascending" clause — **replace**.
- **[N]** A `ROOT`/`BRANCH` child payload contains exactly one `raw32` per set `bitmap` bit, in ascending slot order;
  insufficient/excess payload is rejected by framing. Separate child-hash checks (distinctness, §4a) unaffected.
- (note) Slot count/order are structural consequences of the `bitmap`; no independent slot field exists.
**Impact trace:** New-normative **no** (restates an existing structural truth). Code **no**. Tests **no** (framing +
`test_struct` `DUP_CHILD`). Matrix: R8.1 note.

## S-6 — `SCALARS` present iff ROOT, via framing (clarification only)
**Location:** §8 Tier-1, add a note to the "SCALARS iff ROOT" clause.
- **[N]** `SCALARS` is present exactly for `ROOT`.
- (note) This is a **consequence of the prescribed encodings** — the `ROOT` production includes `SCALARS` and the
  non-`ROOT` productions do not — so an encoding with `SCALARS` on a non-`ROOT`, or missing on a `ROOT`, is ill-formed.
  There is no separate presence flag. This does **not** mandate any particular parsing order to reach that consequence.
**Impact trace:** New-normative **no**. Code **no**. Tests **no** (`test_tier1`). Matrix: R8.1 note.

## S-7 — restrict `EMPTY` to the component-trie-top position (confirmed underspecification)
**Location:** §3 / §4 `EMPTY` definition — add a placement restriction.
- **[N]** `EMPTY` is permitted **only** as a `component_trie_top_hash` target (empty component map); any other position
  is **invalid**.
- (note) Verified against the construction rules: `construct`/`build_state` emit `EMPTY` only there; the restriction
  prohibits nothing canonical.
**Impact trace:** New-normative **YES** (an explicit placement rule; previously only implied). Code **no**. Enforcement
is currently **incidental, verified by probe** (not asserted): a stray `EMPTY` as a ROOT child → `UNEXPECTED_NODE`, as a
bucket member → `BUCKET_MEMBER_TYPE`, both candidates — via generic traversal / member-type checks, **not** a dedicated
`EMPTY`-placement check or vector. So enforcement is **not yet covered by a dedicated test**; a dedicated negative vector
(`EMPTY` as a ROOT child → reject) **should be added** to cover the new rule directly rather than relying on incidental
rejection. Matrix: R4.1/R8.2 note — mark the restriction normative and its coverage as incidental-pending-a-vector.

## S-8 — content-address collision: preserve behavior, qualify testability (clarification only)
**Location:** §4a block C(2) — add a qualification.
- **[N]** Two distinct encodings with one computed address → `CONTENT_ADDRESS_COLLISION`, never silent aliasing.
- (note) Defined for completeness; under A-h a real collision is outside the conformance-vector model, so no vector
  exercises it; no injected node-address seam is authorized.
**Impact trace:** New-normative **no**. Code **no**. Tests **no**. Matrix: R4a.2 already marks it OPEN/untestable.

---

## Consolidated impact

| Finding | New normative requirement? | Oracle code | Tests | Matrix |
|---|---|---|---|---|
| S-1 VERSION=0 | yes (oracle already meets) | no | no | R0.6 note |
| S-2 version agreement | yes (oracle already meets) | no | no | R0.6 note |
| S-3 preimage invariant | re-scope (narrows) | no | no | R6.5 + gap → **N/A** |
| S-4 P6 outcome + walk | yes | **yes (0263)** | **yes (0263)** | R8.2 **downgrade now**, upgrade after walk |
| S-5 bitmap framing | no | no | no | R8.1 note |
| S-6 SCALARS framing | no | no | no | R8.1 note |
| S-7 EMPTY placement | yes (enforced only incidentally today) | no | **add vector** (coverage incidental, verified by probe) | R4.1/R8.2 note |
| S-8 collision | no | no | no | R4a.2 (as is) |

## R8.2 downgrade (applied now, per safeguard 3)

Old: "VERIFIED (equivalent, documented)." New (honest current state): the tested misrouting/placement vectors are
rejected (**MEASURED on those vectors**); universal P6 compliance is **not** proved; the rebuild-and-compare
equivalence is **argued, not proved (provisional)**; the direct per-ancestor-slot walk is **planned (0263)** to enforce
P6 directly. The row is **not** promoted to full VERIFIED until the walk is implemented, tested across the stated scope,
and reviewed against the normative depth rules.

## Ratification order

1. Owner reviews this draft and the **exact normative wording** above.
2. On explicit approval of the text: edit `ENCODING-TABLE-P1.md` → rev 21 with exactly the ratified **[N]** text; bump
   the rev; refresh the SKULD-R2 `MANIFEST.sha256`.
3. Implement 0263 (the walk + tests + the S-3 matrix re-scope + optional S-7 vector); re-run the gate twice; refresh
   evidence without overwriting history.
4. Present the implementation evidence; only on the owner's approval of that evidence is the S-4 gap marked closed and
   R8.2 upgraded within its tested scope.
5. Then D4-2 (effects-range-root), then D8 (anchor trust); below-boundary anchor proofs stay blocked.

Nothing above is applied; the only change made alongside this draft is the R8.2 downgrade (an honesty correction that
lowers a claim). P-1 remains `OPEN`.
