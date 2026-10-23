# P6 equivalence: why rebuild-and-compare enforces full key-path validation

> DESIGN / traceability only, off-gate, P-1 OPEN. Explains why `canonicality.reconstruct`'s rebuild-and-compare
> enforces P-1 rev 20 §8 Tier-2 "full key-path validation (P6)" — *every ancestor slot equals `chunk(d)` at its depth* —
> without a separate literal ancestor-by-ancestor walk, and states the assumptions that make the argument hold.

## The claim

P6 requires: for every `LEAF_*`/`BUCKET` in the presented tree, every ancestor slot on its root-to-node path equals
`chunk(d)` at the corresponding depth `d` (recomputed from `SHA256(KEY)`), so a node placed off its canonical path is
rejected — not merely that child hashes resolve.

`reconstruct(buf, cand, keyhasher)` instead: (1) parses and Tier-1-validates every node; (2) recovers the logical ECS
state `S` by resolving child hashes and reading leaves; (3) recomputes the canonical serialization
`serialize_state(S, cand, keyhasher)` and requires it to be **byte-identical** to `buf`.

**Equivalence.** `serialize_state` lays out, for `S`, exactly the `construct()` shape: each key is routed by `chunk(d)`
at every depth, nodes are content-addressed, and the collection is ordered by node hash. If the presented `buf` equals
that canonical serialization, then every node in `buf` sits at precisely the slot/depth `construct()` puts it — i.e.
every ancestor slot equals `chunk(d)`. If any node were off its canonical path (a misrouted leaf, a bucket at the wrong
depth, a wrong slot), the canonical rebuild of `S` would place it elsewhere, so `rebuilt != buf` and the input is
rejected (`CANONICALITY`). Thus byte-equality to `construct(S)` is **at least as strong** as the per-ancestor-slot
check: it admits only the unique canonical tree for `S`.

## Assumptions the argument depends on (each is tested or noted)

1. **Parsing is complete and faithful.** Every node and every inline bucket member is Tier-1-validated
   (`read_one_node`), so a presented node cannot carry content that reconstruction silently ignores. *Evidence:*
   `test_struct` inline-member vectors (domain/version/type/key/value/order/dup); `test_g2`/`test_g3` Tier-1 rejections.
2. **Each logical key is recovered exactly once.** Duplicate entity/component keys are rejected (`DUP_KEY`), and within
   one parent occupied slots reference distinct child hashes (`DUP_CHILD`, Tier-1, ROOT and BRANCH alike since 0258).
   *Evidence:* `test_g3::dup_key`, `test_struct` ROOT/BRANCH `DUP_CHILD`.
3. **Construction and validation use the same active key-hasher.** Routing in the rebuild uses the hasher passed to
   `reconstruct`; a mismatch is a detectable canonicality disagreement. *Evidence:* `test_seams` consistency.
4. **Node addressing and collection ordering are independent of the key-hash seam.** `node_address` = production
   SHA-256 over the encoding, never the seam, so swapping the hasher changes no address or order of a fixed tree.
   *Evidence:* `test_seams` isolation.
5. **The comparison covers the entire serialization** — root hash, node count, and every node encoding in order — not a
   prefix or a digest. *Evidence:* `serialize_state`/`reconstruct` compare the full `buf` bytes; `test_g2::reorder`,
   `test_g3::orphan`.
6. **Bucket placement is checked explicitly before the rebuild** (`_check_buckets`: depth 52 + full collision under the
   active hasher), giving `BUCKET_MISPLACED`/`BUCKET_NOT_COLLIDING` their own reason rather than a generic mismatch.
   *Evidence:* `test_buckets`.

## The planted witness

`test_struct` misroutes a singleton leaf into a deliberately wrong ROOT slot (`chunk(0)+1`); the canonical rebuild of
the reconstructed state places it in `chunk(0)`, so `rebuilt != buf` and the input is rejected with `CANONICALITY`.
This demonstrates the equivalence bites on exactly the failure P6 names. A defence-in-depth literal per-ancestor-slot
walk is **not required** by this argument, but may be added later; if added, it must agree with rebuild-and-compare on
every case, not replace the byte comparison.

## Residual

Rebuild-and-compare is only as strong as assumptions 1–2: a parsing gap that let a node carry ignored content, or a
missed duplicate, could in principle let a non-canonical tree reconstruct to a state whose canonical form happens to
equal the input. The Tier-1 vectors (above) are the guard; the `verify_plants` "distinct-children check disabled" plant
shows the DUP_CHILD guard bites. This is Level-2 (oracle) evidence, not a proof of specification correctness.
