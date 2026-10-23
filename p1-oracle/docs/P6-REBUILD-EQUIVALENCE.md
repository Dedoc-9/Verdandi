# P6 enforcement: the direct ancestor-slot walk (0263) and rebuild-and-compare as a cross-check

> DESIGN / traceability only, off-gate, P-1 OPEN. P-1 rev 21 §8 Tier-2 "full key-path validation (P6)" — *every ancestor
> slot equals `chunk(d)` at its depth* — is enforced by TWO mechanisms in `canonicality.reconstruct`: (1) a **direct
> per-ancestor-slot walk** (`_p6_walk`, 0263), run first, and (2) **rebuild-and-compare**, kept as an independent
> cross-check. This records what each does, the dependencies they share (so no false independence is claimed), and why
> walk **attribution** (that the walk is *necessary* for the rejection) is **unproven by construction**.

## The requirement

P6: for every `LEAF_*` / `BUCKET` member in the presented tree, every ancestor slot on its root-to-node path equals
`chunk(d)` at the corresponding depth `d` (recomputed from the **active** key-hash of its KEY), so a node placed off its
canonical path is rejected — not merely that child hashes resolve. Buckets sit at terminal construction depth 52 with
all members on the complete shared path (one key-hash across all 52 chunks).

## Mechanism 1 — the direct walk (`_p6_walk`, 0263): the primary enforcement

For every leaf and bucket member the walk recomputes `H = keyhasher(KEY)` with the **active** hasher and, descending from
the ROOT, checks at each branching node of level `L` (ROOT is level 0; a BRANCH's level is its structural construction
depth; a terminal BUCKET is at depth 52) that the slot the element occupies equals `chunk(H, L)` — at **every** depth
0…51, not just the immediate parent. A mismatch is rejected (`WALK_MISROUTE`); a bucket off depth 52 is `BUCKET_MISPLACED`
and members that do not all fully collide are `BUCKET_NOT_COLLIDING`; a stray `EMPTY` is `WALK_EMPTY_PLACEMENT`; a branch
nesting past level 51, or (Candidate B) a stored `level` that disagrees with the structural depth, is `WALK_DEPTH`. The
walk **rejects, never repairs or canonicalises**. It literally checks the spec's `chunk(d)` rule at each depth, so its
correctness rests on its own logic (reviewable against the normative depth rules), not on any equivalence argument.

## Mechanism 2 — rebuild-and-compare: the independent cross-check

`reconstruct` also recovers the logical ECS state `S` and recomputes the canonical serialization `serialize_state(S)`,
requiring it to be **byte-identical** to the presented `buf`. Because `serialize_state` lays out exactly the
`construct()` shape (each key routed by `chunk(d)` at every depth, content-addressed, ordered by node hash), byte
equality to `construct(S)` admits only the unique canonical tree for `S`; any off-path node would be placed elsewhere in
the rebuild, so `rebuilt != buf` and the input is rejected (`CANONICALITY`). This is **at least as strong** as the
per-ancestor-slot check — it is a *complete* canonicality check.

## Shared dependencies (independence is PARTIAL, not claimed otherwise)

The two mechanisms use **distinct traversal and logic** (the walk checks `chunk` per slot top-down; rebuild-and-compare
reconstructs then re-serializes and compares bytes), but they are **not fully independent** — they share:

1. **Parsing** — both consume `parse_collection` / `read_one_node` output, so a parsing gap (content a node carries but
   the parser ignores) would affect both.
2. **Node addressing** — both use `decoder.node_address` (production SHA-256 over the encoding; never the key-hash seam),
   so child resolution and collection order are common.
3. **The active key-hasher** — both route/recompute with the same injected-or-production hasher (G2 consistency).
4. **`chunk` semantics** — both depend on the 52-chunk MSB-first definition; a bug there affects both.

No full-independence claim is made. The walk's value is that it enforces P6 **directly** (not via the rebuild argument),
gives the **specific reason**, and is a **second mechanism** over shared parse+hash foundations.

## Attribution is UNPROVEN by construction

Because rebuild-and-compare is a *complete* canonicality check, it rejects **every** off-path tree the walk rejects:
there is **no witness the walk catches that rebuild-and-compare accepts** (a canonical tree has no off-path node, so
"disable the walk → the vector is accepted" is impossible). Therefore the walk's **necessity cannot be demonstrated**.
What the evidence shows instead:

- **Sufficiency on its own vectors** — `test_walk` runs the walk **alone** via `check_p6_walk` (no rebuild-and-compare)
  and shows it rejects misroutes at depth 0, at a deeper branch, and inside a component trie, plus bucket off-52 and
  non-colliding members, for both candidates; the routing-only plant (`_p6_check_slot` neutered) turns those rows RED.
- **The specific code** — with the walk on, `reconstruct` surfaces `WALK_MISROUTE` (not the generic `CANONICALITY`).
- **Not necessity** — with the walk disabled (`reconstruct(..., _p6=False)`) the **same** off-path tree is **still
  rejected**, as `CANONICALITY`, by rebuild-and-compare alone. So a disable-the-walk plant shows only that the **code**
  changes while the tree stays rejected — the walk *produced* the `WALK_*` verdict, it was not *required* for rejection.

This matches the owner's S-4 ruling: the matrix records R8.2 as VERIFIED **on the tested vectors** with attribution
**unproven**, not universal P6 and not a production-conformance claim.

## Residual

Both mechanisms are only as strong as the shared foundations above (parsing completeness, unique-key recovery,
`node_address`, `chunk`). The Tier-1 vectors (`test_tier1`, `test_struct` `DUP_CHILD` + plant) guard parsing; the
`test_walk` plants guard the walk's routing. This is Level-2 (oracle) evidence on enumerated vectors, **not** a proof of
specification correctness nor of P6 for all admitted inputs.
