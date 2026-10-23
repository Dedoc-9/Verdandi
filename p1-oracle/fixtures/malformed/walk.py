"""Crafted off-path trees for the explicit P6 ancestor-slot walk (0263). Each is well-FRAMED (consistent node hashes,
ascending collection, resolvable root) so it reaches the Tier-2 walk and is rejected for its SPECIFIC reason
(WALK_MISROUTE), not a framing fault. Each off-path tree is built from a canonical accepting counterpart by moving
exactly ONE element into a wrong slot at a chosen depth. Routing uses an InjectedKeyHasher so the chunk layout is
controlled and the fixtures are deterministic; injected key-hashes are explicitly NOT real SHA-256 outcomes. The
bucket-depth / bucket-collision vectors are reused from fixtures.malformed.buckets.
"""
from oracle import decoder as d
from oracle import canonicality as C


def _ek(eid):
    return d.encode_key("eid", eid)


def _ck(comp):
    return d.encode_key("comp", comp)


def _mkH(chunks):
    """Build a 256-bit key-hash with chosen chunk values. `chunks`: {depth: value}, depth 0..50 => 5-bit, 51 => 1-bit;
    unspecified depths are 0. Inverse of decoder.chunk: chunk(_mkH(c), d) == c.get(d, 0)."""
    H = 0
    for depth in range(51):
        H |= (chunks.get(depth, 0) & 0x1F) << (256 - 5 * (depth + 1))
    H |= chunks.get(51, 0) & 0x01
    return H


def _container(root_enc, extra):
    nodes = sorted(set([root_enc] + extra), key=d.node_address)
    return (d.DOM("skuld-state-0") + d.u16(d.VERSION) + d.raw32(d.node_address(root_enc))
            + d.u64(len(nodes)) + b"".join(nodes))


# --- accepting control: a canonical two-entity tree (distinct chunk(0)), built via the oracle -------------------------
def accept_entities(cand):
    """Canonical tree: e1,e2 at distinct ROOT slots chunk(0)=1 / 2. Returns (state, buf, keyhasher)."""
    st = {"entities": {"e1": {}, "e2": {}}, "alloc": 3, "rng": {"seed": 0, "counter": 0}}
    kh = d.InjectedKeyHasher({_ek("e1"): _mkH({0: 1}), _ek("e2"): _mkH({0: 2})})
    buf = C.serialize_state(st, cand, keyhasher=kh)
    return st, buf, kh


# --- misroute at depth 0 (the ROOT): a leaf in the wrong ROOT slot ----------------------------------------------------
def misroute_root(cand):
    """e1 at its correct slot 1; e2 moved from its canonical slot 2 into slot 5. WALK_MISROUTE at level 0."""
    kh = d.InjectedKeyHasher({_ek("e1"): _mkH({0: 1}), _ek("e2"): _mkH({0: 2})})
    empty = d.enc_empty(cand); eh = d.node_address(empty)
    le1 = d.enc_leaf_ent(cand, "e1", eh)
    le2 = d.enc_leaf_ent(cand, "e2", eh)
    root = d.enc_root(cand, {1: d.node_address(le1), 5: d.node_address(le2)}, d.enc_scalars(3, 0, 0))
    return _container(root, [empty, le1, le2]), kh


# --- misroute at a deeper branch (depth 1): e1,e2 share chunk(0), differ at chunk(1) ----------------------------------
def misroute_branch(cand):
    """ROOT slot 1 -> BRANCH(level 1) with e1 at its correct slot 3 and e2 moved from slot 7 into slot 9.
    WALK_MISROUTE at level 1 (a depth below the root, so the walk is shown to check more than the immediate parent)."""
    kh = d.InjectedKeyHasher({_ek("e1"): _mkH({0: 1, 1: 3}), _ek("e2"): _mkH({0: 1, 1: 7})})
    empty = d.enc_empty(cand); eh = d.node_address(empty)
    le1 = d.enc_leaf_ent(cand, "e1", eh)
    le2 = d.enc_leaf_ent(cand, "e2", eh)
    br = d.enc_branch(cand, 1, {3: d.node_address(le1), 9: d.node_address(le2)})
    root = d.enc_root(cand, {1: d.node_address(br)}, d.enc_scalars(3, 0, 0))
    return _container(root, [empty, le1, le2, br]), kh


# --- misroute inside a component trie (depth 0 of that trie) ----------------------------------------------------------
def misroute_comp(cand):
    """One entity e1 with two components whose comp-key-hashes differ at chunk(0); 'pos' moved from slot 8 into slot 10
    in the component-trie top BRANCH. WALK_MISROUTE at level 0 of the COMPONENT trie (shows comp-trie routing checked)."""
    kh = d.InjectedKeyHasher({_ek("e1"): _mkH({0: 1}), _ck("hp"): _mkH({0: 4}), _ck("pos"): _mkH({0: 8})})
    lc_hp = d.enc_leaf_comp(cand, "hp", 1)
    lc_pos = d.enc_leaf_comp(cand, "pos", 2)
    ctop = d.enc_branch(cand, 0, {4: d.node_address(lc_hp), 10: d.node_address(lc_pos)})
    le1 = d.enc_leaf_ent(cand, "e1", d.node_address(ctop))
    root = d.enc_root(cand, {1: d.node_address(le1)}, d.enc_scalars(3, 0, 0))
    return _container(root, [lc_hp, lc_pos, ctop, le1]), kh
