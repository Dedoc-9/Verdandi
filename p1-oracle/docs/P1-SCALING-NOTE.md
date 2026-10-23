# P1 scaling note — depth-decoupled key-path work (graded, bounded)

> **DESIGN / observation only, off-gate, P-1 remains `OPEN`.** A graded record of a scaling property of the P-1
> structure as exercised by the `p1-oracle` validator. Every claim here carries a grade, a `does_not_show` boundary, and
> a falsifier (AGENTS.md §6). It is **not** a latency or throughput claim (counts are operation counts, not timings — a
> clock has a step), **not** a conformance claim, and **not** a scalar scorecard; it is a side-by-side of what the
> measurement supports and what it does not. Seeded by RH-T4 (`probes/redharden.py`,
> [`P1-RED-HARDENING-TESTS.md`](P1-RED-HARDENING-TESTS.md)).

## The precise claim (not "work scales strictly with N, decoupled from depth")

The strong phrasing — *all validation and traversal work scales strictly with the element count N and is completely
decoupled from tree depth D* — is **not** what the apparatus shows, and is recorded here only to be bounded. Total
validation work is **O(number of encoded nodes)**, which is **not** strictly O(N). What **is** supported splits into
three graded statements:

### C1 — key-path recomputation is per-element, not per-level (MEASURED)
The validator recomputes a key-hash **once per logical element** (each `LEAF_ENT`, each `LEAF_COMP`, each `BUCKET`
member) during the P6 walk, and once per element again when it rebuilds — never once per level on the root-to-leaf
path. So key-hash work is **O(N)** in the element count and **independent of the depth** of the element's path.
- **Evidence (MEASURED, author's host, these shapes; RH-T4):** a full-collision bucket whose two members sit at the end
  of a 52-level single-path branch chain cost **4** key-hash calls (2 members + 2 rebuild), **not** ~104; a 20-entity
  wide ROOT cost 40; an 8-entity shared-component DAG hashed the shared `hp=1` component **once**.
- **does_not_show:** this is the *key-hash* operation count only; see C3 for the costs that are **not** O(N).
- **Falsifier:** a structure (or a change to `_p6_walk` / `build_state`) where key-hash calls grow with depth — e.g.
  re-hashing per ancestor level — would exceed O(N) and break C1. `probes/redharden.py` RH-T4 would show it.

### C2 — trie depth is bounded by a constant, for any N (ESTABLISHED by construction)
The key-hash is 256 bits consumed as 52 chunks (51×5-bit + 1×1-bit, §2), so **no** root-to-leaf path exceeds **52**
branch levels, whatever N is. A `BUCKET` sits at the terminal depth 52 (full collision). Depth has a **fixed ceiling**,
it does not grow with N.
- **does_not_show:** a fixed depth ceiling is not "depth-independent work" (C3); and a HAMT **is** a tree — this is the
  fixed-width-hash property, not an escape from tree structure. "Out-scaling traditional trees" is not claimed; the
  defensible point is the constant ceiling (vs. an `O(log N)` depth that grows without a fixed bound).
- **Falsifier:** any admitted path longer than 52 levels; `chunk(d)` rejects `d > 51` and the walk raises `WALK_DEPTH`.

### C3 — total node-level work scales with node count, which is depth-dependent for collision chains (OBSERVED boundary)
Parsing (`read_one_node`), node addressing (`node_address` = SHA-256 over each encoding), the ascending-order sort, and
the node-visiting traversal are each **O(number of encoded nodes)** — **not** O(N). For an adversarial full-collision
group the node count includes an **O(52)** single-path branch chain per group: the deep bucket above encoded **54 nodes
for 2 elements**. So in that regime node-level work **is** depth-dependent and **can exceed N**.
- **Mitigation (POTENTIAL, premise-limited):** routing is by **SHA-256(KEY)**, so forcing a long shared prefix / a full
  collision is infeasible without breaking A-h (RH-4). In the **honest-input** regime, depth is `O(log₃₂ N) ≤ 52` and
  node count is `O(N)`, so node-level work is `O(N)` there — but this rests on A-h, not on the structure alone, and is
  **not** a worst-case bound.
- **does_not_show:** no proven asymptotic bound; MEASURED/OBSERVED on specific shapes on one host; no timing.

## Summary (side by side, no scorecard)

| statement | grade | holds | boundary |
|---|---|---|---|
| key-hash recomputation is O(N), depth-independent | MEASURED | yes, on the measured shapes | key-hash ops only (C1) |
| trie depth ≤ 52 for any N | ESTABLISHED | yes, by the 52-chunk key-hash | a ceiling, not depth-free work (C2) |
| total validation/traversal work is O(N), depth-decoupled | — | **no** | it is O(node count); depth-dependent for collision chains (C3) |
| forced collision chains are infeasible (so node count is O(N) in practice) | POTENTIAL | premise-limited (A-h) | not a worst-case bound (C3) |

**Bottom line:** the genuine, checkable property is C1 + C2 — *per-element key-path work is bounded by a constant
(≤ 52 levels) and recomputed once per element, not once per level* — which decouples the **key-hash** cost from depth.
It is **not** that all validation work is O(N) or free of structure. P-1 remains `OPEN`; this is Level-2 oracle
observation, graded, not a conformance or performance guarantee.
