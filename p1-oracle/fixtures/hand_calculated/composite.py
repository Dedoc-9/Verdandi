"""0262 (G-1): a fully hand-traced COMPOSITE serialization vector, independent of the oracle and of any
grammar-reimplementing helper. Only arithmetic primitives (u8/u16/u32/u64) and SHA-256 are used; every P-1 grammar
field is written as a literal here (domain ASCII, type byte, KEY/VALUE bytes, SCALARS), so a reviewer can audit the
bytes against the spec without trusting a helper. Child hashes, the ROOT slot, the collection order and the root hash
are computed by SHA-256 / bit arithmetic over those literals (allowed). Derivation: docs/0262-COMPOSITE-DERIVATION.md.

State: one entity "e1" with one string component name="orc"; scalars alloc=2, seed=0, counter=0.
This exercises the component-trie top (bare LEAF_COMP), the entity LEAF_ENT, the ROOT with SCALARS, content-addressed
node hashing, the ascending-by-hash collection order, and the final container — i.e. multiple composite layers.
"""
import hashlib

STATE = {"entities": {"e1": {"name": "orc"}}, "alloc": 2, "rng": {"seed": 0, "counter": 0}}


def _u8(n):
    return n.to_bytes(1, "big")


def _u16(n):
    return n.to_bytes(2, "big")


def _u32(n):
    return n.to_bytes(4, "big")


def _u64(n):
    return n.to_bytes(8, "big")


def _sha(b):
    return hashlib.sha256(b).digest()


def composite_vector(cand):
    """Return (STATE, expected_container_bytes) for candidate 'A' or 'B', hand-assembled from literal grammar fields."""
    infix = "hamtA" if cand == "A" else "merkleB"
    root_level = _u8(0) if cand == "B" else b""      # Candidate B carries u8(level)=0 on ROOT; A carries none

    # --- literal grammar fields (auditable against the spec) ---
    key_e1 = b"\x10" + _u64(2) + b"e1"               # KEY(eid "e1")   = KTYPE 0x10 ‖ lp("e1")
    key_name = b"\x11" + _u64(4) + b"name"           # KEY(comp "name")= KTYPE 0x11 ‖ lp("name")
    val_orc = b"\x02" + _u64(3) + b"orc"             # VALUE(str "orc")= VTYPE 0x02 ‖ lp("orc")
    val_2 = b"\x01\x00" + _u64(1) + b"\x02"          # VALUE(int 2)    = VTYPE 0x01, sign 0x00, lp(0x02)
    val_0 = b"\x01\x00" + _u64(0)                    # VALUE(int 0)    = VTYPE 0x01, sign 0x00, lp(b"")

    # component-trie top = bare LEAF_COMP (one component)
    leaf_comp = ("skuld-%s-leafcomp-0\x00" % infix).encode("ascii") + _u16(0) + _u8(0x04) + key_name + val_orc
    comp_top_hash = _sha(leaf_comp)

    # entity leaf references the component top by hash
    leaf_ent = ("skuld-%s-leafent-0\x00" % infix).encode("ascii") + _u16(0) + _u8(0x03) + key_e1 + comp_top_hash
    leaf_ent_hash = _sha(leaf_ent)

    # ROOT slot = chunk(0) of sha256(KEY(eid "e1")) = top 5 bits, MSB-first
    H = int.from_bytes(_sha(key_e1), "big")
    slot = (H >> (256 - 5)) & 0x1F
    bitmap = 1 << slot

    # SCALARS (candidate-independent): DOM ‖ "A" VALUE(alloc) ‖ "S" VALUE(seed) ‖ "C" VALUE(counter)
    scalars = b"skuld-scalars-0\x00" + b"A" + val_2 + b"S" + val_0 + b"C" + val_0

    root = (("skuld-%s-root-0\x00" % infix).encode("ascii") + _u16(0) + _u8(0x01) + root_level
            + _u32(bitmap) + leaf_ent_hash + scalars)
    root_hash = _sha(root)

    nodes = sorted([leaf_comp, leaf_ent, root], key=_sha)          # §4a: ascending by raw node hash
    container = b"skuld-state-0\x00" + _u16(0) + root_hash + _u64(len(nodes)) + b"".join(nodes)
    return STATE, container
