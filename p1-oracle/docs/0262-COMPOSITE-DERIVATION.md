# 0262 — hand-traced composite serialization vector (G-1)

> DESIGN / traceability only, off-gate, P-1 OPEN. A fully hand-traced composite serialization, derived from P-1 rev 20
> **without** calling the oracle or any grammar-reimplementing helper. Only `u8/u16/u32/u64` (big-endian) and SHA-256
> are used as tools; every grammar field below is a literal you can audit against the spec. The fixture
> (`fixtures/hand_calculated/composite.py`) assembles exactly these literals; `tests/test_composite.py` asserts the
> oracle reproduces the result byte-for-byte. Agreement is independent (two derivations from the spec, not one copied
> from the other). It reduces — it does not eliminate — correlated-interpretation risk; the eliminating step is a human
> reading this derivation against the spec.

## State

`{"entities": {"e1": {"name": "orc"}}, "alloc": 2, "rng": {"seed": 0, "counter": 0}}`

Layers exercised: component-trie top (bare `LEAF_COMP`), entity `LEAF_ENT`, `ROOT` + `SCALARS`, content-addressed node
hashing, ascending-by-hash collection order, and the `§4a` container.

## Primitive fields (literals)

| field | bytes (hex) | note |
|---|---|---|
| `u16(0)` VERSION | `0000` | |
| `KEY(eid "e1")` | `10` `0000000000000002` `6531` | KTYPE 0x10 ‖ lp("e1") |
| `KEY(comp "name")` | `11` `0000000000000004` `6e616d65` | KTYPE 0x11 ‖ lp("name") |
| `VALUE(str "orc")` | `02` `0000000000000003` `6f7263` | VTYPE 0x02 ‖ lp("orc") |
| `VALUE(int 2)` | `01` `00` `0000000000000001` `02` | sign 0x00, minimal mag `02` |
| `VALUE(int 0)` | `01` `00` `0000000000000000` | empty mag |
| `SCALARS` | `skuld-scalars-0\x00` ‖ `41`·VALUE(2) ‖ `53`·VALUE(0) ‖ `43`·VALUE(0) | "A"/"S"/"C" = 0x41/0x53/0x43 |

## Candidate A (`hamtA`, no `level` byte)

- **LEAF_COMP** = `skuld-hamtA-leafcomp-0\x00` ‖ `0000` ‖ `04` ‖ KEY(comp "name") ‖ VALUE("orc")  → **51 bytes**
  `sha256 = 54e2e9ab28070332b24f5c38cf653f1e4900c24e34b4ad7728f64223090745ba`
- **LEAF_ENT** = `skuld-hamtA-leafent-0\x00` ‖ `0000` ‖ `03` ‖ KEY(eid "e1") ‖ raw32(LEAF_COMP hash)  → **68 bytes**
  `sha256 = b8dcf673bdb029521469e885fd4cf94030f75c8f0891021c9830550a4d9a5b90`
- **ROOT slot** = `chunk(0)` of `sha256(KEY(eid "e1"))` = top 5 bits = **11** → `bitmap = 0x00000800`
- **ROOT** = `skuld-hamtA-root-0\x00` ‖ `0000` ‖ `01` ‖ `00000800` ‖ raw32(LEAF_ENT hash) ‖ SCALARS  → **108 bytes**
  `sha256 = 6a06be04cf07e3d0327d934b04b7362a3cf6b57a0bec76ac379375fa48f286bb`
- **collection order** (ascending by node hash): LEAF_COMP (`54e2…`), ROOT (`6a06…`), LEAF_ENT (`b8dc…`)
- **container** = `skuld-state-0\x00` ‖ `0000` ‖ raw32(root_hash `6a06…`) ‖ `u64(3)` ‖ (the three nodes in that order)
  → **283 bytes total**

## Candidate B (`merkleB`, `ROOT` carries `u8(level)=0`)

Same fields, `merkleB` domains, and `ROOT` inserts `00` (level) after the type byte:
- **LEAF_COMP** 53 B, `sha256 = f6c71dd77ababab51c1a5ca163ffc2b0c7720c02df45d38d189415473f9c5835`
- **LEAF_ENT** 70 B, `sha256 = d67a2f2ace80441ede2ef8de66400afc2b5e84496473834241a89fefaa9907e6`
- **ROOT** 111 B, slot 11, `sha256 = 947c8fff3bfa1d5006a0cae2b2df5215223ff8c014f11b6b272a1a9d1f3d3f65`
- **order**: ROOT (`947c…`), LEAF_ENT (`d67a…`), LEAF_COMP (`f6c7…`) → **container 290 bytes**

## How to verify by hand

Read each literal field above against P-1 rev 20 §1–§4a. Compute the node hashes with any SHA-256 tool over the exact
node bytes (e.g. `python -c "import hashlib;print(hashlib.sha256(bytes.fromhex('…')).hexdigest())"`), confirm the slot
is the top 5 bits of `sha256(KEY(eid "e1"))`, sort the three nodes by raw hash, and concatenate. The result must equal
`serialize_state(STATE, cand)`. The SHA-256 tool is trusted only for hashing; the grammar is entirely in the literals.

## What this establishes (and does not)

It is **one** independently derived composite vector per candidate, auditable field-by-field — it materially lowers the
G-1 correlated-provenance risk for the composite path. It does **not** prove every composite encoding is independently
correct, and it does not change P-1's `OPEN` status or any production artifact.
