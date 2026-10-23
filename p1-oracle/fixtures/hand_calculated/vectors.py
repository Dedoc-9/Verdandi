"""Independently HAND-CALCULATED P-1 byte vectors (ENCODING-TABLE-P1.md rev 20, §1-§4a).

These helpers use ONLY local primitives (re-derived from the written grammar) and hashlib. They never import the
oracle. A reviewer can check each literal against the grammar by hand; the tests assert the oracle reproduces them.

Pinned v0 constants (checked separately by P1V-constants): VERSION=0, candidate infix A='hamtA', B='merkleB'.
"""
import hashlib

VERSION = 0


def _u16(n): return n.to_bytes(2, "big")
def _u32(n): return n.to_bytes(4, "big")
def _u64(n): return n.to_bytes(8, "big")
def _lp(b): return _u64(len(b)) + b
def _dom(s): return s.encode("ascii") + b"\x00"
def _sha(b): return hashlib.sha256(b).digest()


def _val_int(n):
    if n >= 0:
        sign = 0
        mag = b"" if n == 0 else n.to_bytes((n.bit_length() + 7) // 8, "big")
    else:
        sign = 1
        a = -n
        mag = a.to_bytes((a.bit_length() + 7) // 8, "big")
    return bytes([0x01, sign]) + _lp(mag)


def _val_str(s):
    return bytes([0x02]) + _lp(s.encode("utf-8"))


def _key(kind, s):
    return bytes([0x10 if kind == "eid" else 0x11]) + _lp(s.encode("utf-8"))


def _infix(cand):
    return "hamtA" if cand == "A" else "merkleB"


def _ndom(cand, name):
    return _dom("skuld-%s-%s-0" % (_infix(cand), name))


# ---------------------------------------------------------------------------------------------------------------------
# Leaf-level literals (fully hand-derivable; no hashing of children)

def value_vectors():
    """(python_value, expected VALUE bytes). Derivations in comments."""
    return [
        # int 0: VTYPE 0x01, sign 0x00, lp(b"") = 8 zero len bytes
        (0, bytes([0x01, 0x00]) + _u64(0)),
        # int 10: 0x01 0x00 lp(0x0a)
        (10, bytes([0x01, 0x00]) + _lp(b"\x0a")),
        # int 255: 0x01 0x00 lp(0xff)
        (255, bytes([0x01, 0x00]) + _lp(b"\xff")),
        # int 256: 0x01 0x00 lp(0x01 0x00)  (minimal big-endian, two bytes)
        (256, bytes([0x01, 0x00]) + _lp(b"\x01\x00")),
        # int -7: 0x01 0x01 lp(0x07)
        (-7, bytes([0x01, 0x01]) + _lp(b"\x07")),
        # str "orc"
        ("orc", _val_str("orc")),
        # str "" (empty)
        ("", _val_str("")),
        # str "é" composed U+00E9 -> utf-8 C3 A9
        ("é", bytes([0x02]) + _lp(b"\xc3\xa9")),
    ]


def key_vectors():
    return [
        (("eid", "e1"), _key("eid", "e1")),
        (("comp", "hp"), _key("comp", "hp")),
        (("eid", "entity-longer-name"), _key("eid", "entity-longer-name")),
    ]


def empty_node(cand):
    # EMPTY = DOM("skuld-<cand>-empty-0") ‖ u16(0) ‖ u8(0x00)
    return _ndom(cand, "empty") + _u16(VERSION) + bytes([0x00])


def leaf_comp(cand, comp, value):
    # LEAF_COMP = DOM(leafcomp) ‖ u16 ‖ 0x04 ‖ KEY(comp) ‖ VALUE
    return _ndom(cand, "leafcomp") + _u16(VERSION) + bytes([0x04]) + _key("comp", comp) + (
        _val_int(value) if isinstance(value, int) and not isinstance(value, bool) else _val_str(value))


def leaf_ent(cand, eid, comp_top_hash):
    return _ndom(cand, "leafent") + _u16(VERSION) + bytes([0x03]) + _key("eid", eid) + comp_top_hash


def scalars(alloc, seed, counter):
    return (_dom("skuld-scalars-0") + b"A" + _val_int(alloc) + b"S" + _val_int(seed) + b"C" + _val_int(counter))


def root(cand, slot_child, scalars_bytes):
    bitmap = 0
    body = b""
    for slot in sorted(slot_child):
        bitmap |= (1 << slot)
        body += slot_child[slot]
    out = _ndom(cand, "root") + _u16(VERSION) + bytes([0x01])
    if cand == "B":
        out += bytes([0])
    return out + _u32(bitmap) + body + scalars_bytes


def container(root_hash, node_encodings_sorted):
    out = _dom("skuld-state-0") + _u16(VERSION) + root_hash + _u64(len(node_encodings_sorted))
    for enc in node_encodings_sorted:
        out += enc
    return out


# ---------------------------------------------------------------------------------------------------------------------
# Whole-state serializations (composite; child hashes via hashlib reference, NOT the oracle)

def genesis_serialization(cand):
    """Empty entity map: ROOT with bitmap 0 + scalars(alloc=1, seed=0, counter=0)."""
    state = {"entities": {}, "alloc": 1, "rng": {"seed": 0, "counter": 0}}
    root_enc = root(cand, {}, scalars(1, 0, 0))
    root_h = _sha(root_enc)
    buf = container(root_h, [root_enc])          # one node
    return state, buf


def singleton_empty_entity_serialization(cand):
    """One entity 'e1' with NO components: ROOT -> LEAF_ENT(e1) -> EMPTY component top. alloc=2."""
    empty = empty_node(cand)
    empty_h = _sha(empty)
    le = leaf_ent(cand, "e1", empty_h)
    le_h = _sha(le)
    # entity key routes by chunk(0) of sha256(KEY(eid 'e1')); ROOT has one slot at that chunk
    H = int.from_bytes(_sha(_key("eid", "e1")), "big")
    slot0 = (H >> (256 - 5)) & 0x1F
    root_enc = root(cand, {slot0: le_h}, scalars(2, 0, 0))
    root_h = _sha(root_enc)
    nodes = sorted([empty, le, root_enc], key=lambda e: _sha(e))
    buf = container(root_h, nodes)
    state = {"entities": {"e1": {}}, "alloc": 2, "rng": {"seed": 0, "counter": 0}}
    return state, buf


def singleton_one_component_serialization(cand):
    """One entity 'e1' with one component hp=10: ROOT -> LEAF_ENT(e1) -> (bare LEAF_COMP top)."""
    lc = leaf_comp(cand, "hp", 10)
    lc_h = _sha(lc)                               # component top = the bare LEAF_COMP
    le = leaf_ent(cand, "e1", lc_h)
    le_h = _sha(le)
    H = int.from_bytes(_sha(_key("eid", "e1")), "big")
    slot0 = (H >> (256 - 5)) & 0x1F
    root_enc = root(cand, {slot0: le_h}, scalars(2, 0, 0))
    root_h = _sha(root_enc)
    nodes = sorted([lc, le, root_enc], key=lambda e: _sha(e))
    buf = container(root_h, nodes)
    state = {"entities": {"e1": {"hp": 10}}, "alloc": 2, "rng": {"seed": 0, "counter": 0}}
    return state, buf
