"""Canonical construction and whole-state (Tier-2) validation (ENCODING-TABLE-P1.md §3, §4, §4a, §8).

construct() is the one deterministic shape function (§4). build_state()/serialize_state() encode a state. Tier-2
validation (reconstruct) enforces canonicality through TWO mechanisms run in order: (1) a DIRECT P6 ancestor-slot walk
(_p6_walk, 0263) that recomputes each leaf/bucket-member key-hash and checks every ancestor slot equals chunk(d) and
buckets sit at terminal depth 52 — the explicit enforcement, giving the specific reason; then (2) REBUILD-AND-COMPARE,
which recovers the logical state and requires the presented bytes to equal the canonical serialization of that state
(byte-identical or reject) — kept as an independent cross-check. Both use the ACTIVE key-hasher (G2 consistency) and
decoder.node_address (production SHA-256), never the key-hash seam for addressing (G2 isolation); their shared
dependencies and the unproven walk-attribution are documented in P6-REBUILD-EQUIVALENCE.md.
"""
from . import decoder as d


def _add(collection, enc):
    addr = d.node_address(enc)
    if addr in collection and collection[addr] != enc:        # a real SHA-256 collision; impossible under A-h
        raise d.OracleError(d.MALFORMED, "CONTENT_ADDRESS_COLLISION", "two encodings, one address (build)")
    collection[addr] = enc
    return addr


def _construct(items, depth, cand, keyhasher, collection):
    """items: list of {"kb": key_bytes, "H": int, "leaf": leaf_encoding}; all share chunk(0..depth-1)."""
    if len(items) == 1:
        return _add(collection, items[0]["leaf"])
    if depth == 52:                                           # all 52 chunks consumed => identical H => full collision
        members = sorted(items, key=lambda it: it["kb"])
        bucket = d.enc_bucket(cand, [(it["kb"], it["leaf"]) for it in members])
        return _add(collection, bucket)
    groups = {}
    for it in items:
        groups.setdefault(d.chunk(it["H"], depth), []).append(it)
    slot_child = {s: _construct(grp, depth + 1, cand, keyhasher, collection) for s, grp in groups.items()}
    return _add(collection, d.enc_branch(cand, depth, slot_child))


def _build_comp_top(comps, cand, keyhasher, collection):
    if not comps:
        return _add(collection, d.enc_empty(cand))            # distinguished EMPTY node (component map of size 0)
    items = []
    for comp, value in comps.items():
        leaf = d.enc_leaf_comp(cand, comp, value)
        kb = d.encode_key("comp", comp)
        items.append({"kb": kb, "H": keyhasher(kb), "leaf": leaf})
    return _construct(items, 0, cand, keyhasher, collection)   # top = construct(K_comp, 0): bare LEAF_COMP for 1, BRANCH for >=2


def build_state(state, cand, keyhasher=d.prod_key_hasher, limits=d.PROD_LIMITS):
    """Return (root_hash, {address: encoding}) for the canonical encoding of `state` under `cand`."""
    collection = {}
    ent_items = []
    for eid, comps in state["entities"].items():
        comp_top = _build_comp_top(comps, cand, keyhasher, collection)
        leaf = d.enc_leaf_ent(cand, eid, comp_top)
        kb = d.encode_key("eid", eid)
        ent_items.append({"kb": kb, "H": keyhasher(kb), "leaf": leaf})
    scalars = d.enc_scalars(state["alloc"], state["rng"]["seed"], state["rng"]["counter"])
    if not ent_items:
        return _add(collection, d.enc_root(cand, {}, scalars)), collection
    groups = {}
    for it in ent_items:
        groups.setdefault(d.chunk(it["H"], 0), []).append(it)  # ROOT groups entity keys by chunk(0); children begin at depth 1
    slot_child = {s: _construct(grp, 1, cand, keyhasher, collection) for s, grp in groups.items()}
    return _add(collection, d.enc_root(cand, slot_child, scalars)), collection


def serialize_state(state, cand, keyhasher=d.prod_key_hasher, limits=d.PROD_LIMITS):
    """The complete §4a state_serialization: container + unique nodes in ascending node-hash order."""
    root_hash, collection = build_state(state, cand, keyhasher, limits)
    if len(collection) > limits.max_nodes:
        raise d.malformed("MAX_NODES", "%d > %d" % (len(collection), limits.max_nodes))
    # builder/parser symmetry (0261): the builder honours MAX_TOTAL too (sum of unique node encodings, as the parser
    # counts it, excluding the container header), so it never emits output the parser would reject under the same limit.
    total = sum(len(enc) for enc in collection.values())
    if total > limits.max_total:
        raise d.malformed("MAX_TOTAL", "%d > %d" % (total, limits.max_total))
    out = d.DOM("skuld-state-0") + d.u16(d.VERSION) + d.raw32(root_hash) + d.u64(len(collection))
    for addr in sorted(collection):
        out += collection[addr]
    return out


# ---------------------------------------------------------------------------------------------------------------------
# Tier-2 parse + reconstruct


def parse_collection(buf, cand, limits=d.PROD_LIMITS):
    """Framing + node reads + ascending/unique-address + resource checks. Returns (root_hash, order, addr_map).
    Takes NO key-hasher: node addresses and ordering are a pure function of the bytes (G2 isolation is structural)."""
    r = d.Reader(buf, limits)
    r.expect(d.DOM("skuld-state-0"), "STATE_DOM")
    v = r.u16()
    if v != d.VERSION:
        raise d.malformed("VERSION", str(v))
    root_hash = r.take(32)
    node_count = r.u64()
    if node_count > limits.max_nodes:
        raise d.malformed("MAX_NODES", "%d > %d" % (node_count, limits.max_nodes))
    addr_map, order = {}, []
    total, prev = 0, None
    for _ in range(node_count):
        node = d.read_one_node(r, cand, limits)
        addr, enc = node["_address"], node["_encoding"]
        total += len(enc)
        if total > limits.max_total:
            raise d.malformed("MAX_TOTAL", "%d > %d" % (total, limits.max_total))
        if prev is not None and addr <= prev:
            if addr == prev:
                if enc == addr_map[addr]["_encoding"]:
                    raise d.malformed("DUP_ENTRY", "same node encoding twice")
                raise d.malformed("CONTENT_ADDRESS_COLLISION", "two encodings, one address")
            raise d.malformed("NODE_ORDER", "collection not strictly ascending by address")
        addr_map[addr] = node
        order.append(addr)
        prev = addr
    if not r.at_end():
        raise d.malformed("TRAILING", "%d bytes after collection" % (len(buf) - r.pos))
    return root_hash, order, addr_map


def _resolve(addr_map, addr):
    node = addr_map.get(addr)
    if node is None:
        raise d.malformed("MISSING_CHILD", addr.hex()[:16])
    return node


def _distinct_children(node):
    addrs = [h for _s, h in node["children"]]
    if len(set(addrs)) != len(addrs):
        raise d.malformed("DUP_CHILD", "same child hash in two slots of one parent")
    return addrs


# ---------------------------------------------------------------------------------------------------------------------
# P6 explicit ancestor-slot walk (ENCODING-TABLE-P1.md rev 21 §8 Tier-2; 0263)
#
# The DIRECT enforcement of P6 "full key-path validation": for EVERY leaf and EVERY bucket member, recompute
# H = keyhasher(its canonical KEY bytes) with the ACTIVE key-hasher and verify that at each ancestor branching node of
# level L the slot the element descends through equals chunk(H, L); a mismatch at ANY depth is rejected (checking the
# immediate parent alone is not enough). A BUCKET is required at terminal construction depth 52 with ALL members on the
# complete path: they share chunk(0..51) down the branch chain (so one key-hash) and the bucket sits where the 52nd
# chunk has been consumed. The walk REJECTS a misplaced node; it never repairs or canonicalises before checking.
#
# Depth is tracked STRUCTURALLY: the entity-trie ROOT is level 0 and positions its children at construction depth 1;
# each BRANCH is one deeper; a component trie is its own trie whose top sits at depth 0; a terminal BUCKET sits at
# depth 52. The structural depth, not Candidate B's stored `level` field, is the authority (for Candidate B the stored
# level is additionally cross-checked against it, WALK_DEPTH on disagreement).
#
# Node addressing stays production SHA-256 (decoder.node_address); the ONLY seam used is the already-authorized
# key-hash seam for routing. This walk runs BEFORE rebuild-and-compare and gives the SPECIFIC reason (WALK_MISROUTE /
# WALK_DEPTH / BUCKET_MISPLACED / BUCKET_NOT_COLLIDING). See P6-REBUILD-EQUIVALENCE.md for the dependencies it shares
# with rebuild-and-compare (parse, node_address, the active key-hasher, chunk) and for why walk ATTRIBUTION (necessity)
# is UNPROVEN: rebuild-and-compare is a complete canonicality check, so it independently rejects every tree this walk
# rejects; the walk's demonstrated value is sufficiency on its own vectors plus the specific code, not a unique catch.


def _p6_walk(addr_map, root_hash, cand, keyhasher):
    """Validate the whole tree's key-path placement from the ROOT down; raises the specific MALFORMED reason."""
    root = _resolve(addr_map, root_hash)
    if root["type"] != "ROOT":
        raise d.malformed("ROOT_TYPE", root["type"])
    _p6_node(addr_map, root, 0, "eid", cand, keyhasher)


def _p6_node(addr_map, node, pos, kind, cand, keyhasher):
    """Validate the subtree at `node` (positioned at construction depth `pos` = chunks already consumed to reach it) and
    RETURN the list of key-hashes (H) of every leaf beneath it, so the caller can verify each one routes to the slot it
    occupies. `kind` is 'eid' (entity trie) or 'comp' (a component trie)."""
    t = node["type"]
    if t in ("ROOT", "BRANCH"):
        if t == "ROOT" and (pos != 0 or kind != "eid"):
            raise d.malformed("UNEXPECTED_NODE", "ROOT nested at depth %d (%s trie)" % (pos, kind))
        level = pos                                     # a branching node at construction depth `pos` groups by chunk(H, pos)
        if level > 51:
            raise d.malformed("WALK_DEPTH", "%s branching at level %d > 51 (%s trie)" % (t, level, kind))
        if t == "BRANCH" and cand == "B" and node.get("level") is not None and node["level"] != level:
            raise d.malformed("WALK_DEPTH", "BRANCH stored level %d != structural depth %d" % (node["level"], level))
        hs = []
        for slot, child_hash in node["children"]:
            child_hs = _p6_node(addr_map, _resolve(addr_map, child_hash), pos + 1, kind, cand, keyhasher)
            for H in child_hs:
                _p6_check_slot(level, H, slot, kind)
            hs += child_hs
        return hs
    if t == "BUCKET":
        if pos != 52:
            raise d.malformed("BUCKET_MISPLACED", "bucket at construction depth %d (must be 52), %s trie" % (pos, kind))
        hs = []
        for _kb, leaf_enc in node["members"]:
            m = d.decode_node(leaf_enc, cand)
            hs.append(keyhasher(m["key_bytes"]))
            if kind == "eid":
                _p6_descend_comp(addr_map, m, cand, keyhasher)
        if len(set(hs)) != 1:                           # full collision: all 52 chunks (all 256 bits) identical
            raise d.malformed("BUCKET_NOT_COLLIDING", "members do not all fully collide under the active key-hash")
        return hs
    if t == "LEAF_ENT":
        if kind != "eid":
            raise d.malformed("WALK_LEAF_KIND", "LEAF_ENT inside a component trie")
        _p6_descend_comp(addr_map, node, cand, keyhasher)
        return [keyhasher(node["key_bytes"])]
    if t == "LEAF_COMP":
        if kind != "comp":
            raise d.malformed("WALK_LEAF_KIND", "LEAF_COMP inside the entity trie")
        return [keyhasher(node["key_bytes"])]
    if t == "EMPTY":
        raise d.malformed("WALK_EMPTY_PLACEMENT", "EMPTY outside a size-0 component-trie top (%s trie)" % kind)
    raise d.malformed("UNEXPECTED_NODE", "%s in %s trie" % (t, kind))


def _p6_check_slot(level, H, slot, kind):
    """The core routing predicate: an element with key-hash H must occupy the slot chunk(H, level) at an ancestor of
    level `level`. Factored out so a plant can neuter exactly this check (verify_plants, 0263)."""
    if d.chunk(H, level) != slot:
        raise d.malformed("WALK_MISROUTE", "element chunk(%d)=%d but sits in slot %d (%s trie)"
                          % (level, d.chunk(H, level), slot, kind))


def _p6_descend_comp(addr_map, leaf_ent, cand, keyhasher):
    """A LEAF_ENT's component trie is its own trie rooted at construction depth 0. A size-0 component map is the single
    distinguished EMPTY node (the one lawful EMPTY position, §3/S-7); anything else is walked."""
    top = _resolve(addr_map, leaf_ent["comp_top"])
    if top["type"] == "EMPTY":
        return
    _p6_node(addr_map, top, 0, "comp", cand, keyhasher)


def check_p6_walk(buf, cand, keyhasher=d.prod_key_hasher, limits=d.PROD_LIMITS):
    """Run the P6 ancestor-slot walk ALONE: parse + ROOT check + walk, with NO rebuild-and-compare. Used by tests to
    show the walk BY ITSELF rejects an off-path tree (sufficiency), independent of the rebuild. Returns the parsed
    (root_hash, order, addr_map) on success."""
    root_hash, order, addr_map = parse_collection(buf, cand, limits)
    _p6_walk(addr_map, root_hash, cand, keyhasher)
    return root_hash, order, addr_map


def _walk_leaves(addr_map, addr, want_type, cand):
    """Collect LEAF_* of want_type reachable through BRANCH/BUCKET from addr."""
    node = _resolve(addr_map, addr)
    t = node["type"]
    if t == want_type:
        return [node]
    if t == "BRANCH":
        out = []
        for child in _distinct_children(node):
            out += _walk_leaves(addr_map, child, want_type, cand)
        return out
    if t == "BUCKET":
        out = []
        for _kb, leaf_enc in node["members"]:
            m = d.decode_node(leaf_enc, cand)
            if m["type"] != want_type:
                raise d.malformed("BUCKET_MEMBER_TYPE", m["type"])
            out.append(m)
        return out
    raise d.malformed("UNEXPECTED_NODE", "%s where %s expected" % (t, want_type))


def reconstruct(buf, cand, keyhasher=d.prod_key_hasher, limits=d.PROD_LIMITS, _p6=True):
    """Tier-2: parse, run the direct P6 ancestor-slot walk, reconstruct the logical ECS state, then rebuild-and-compare
    for canonicality (§8). `_p6` (test-only, default True) disables the explicit walk so a plant / attribution test can
    show the tree is STILL rejected by rebuild-and-compare alone (necessity unproven); never pass it in production."""
    root_hash, order, addr_map = parse_collection(buf, cand, limits)
    root = _resolve(addr_map, root_hash)
    if root["type"] != "ROOT":
        raise d.malformed("ROOT_TYPE", root["type"])
    # direct P6 enforcement (explicit ancestor-slot walk, 0263) BEFORE the generic rebuild-and-compare, so a misrouted
    # or misplaced node is rejected for its SPECIFIC reason (WALK_MISROUTE / WALK_DEPTH / BUCKET_MISPLACED / ...).
    if _p6:
        _p6_walk(addr_map, root_hash, cand, keyhasher)
    alloc = root["scalars"]["alloc"]
    seed = root["scalars"]["seed"]
    counter = root["scalars"]["counter"]

    entities = {}
    for _slot, child in root["children"]:
        for leaf in _walk_leaves(addr_map, child, "LEAF_ENT", cand):
            eid = leaf["eid"]
            if eid in entities:
                raise d.malformed("DUP_KEY", "entity %s twice" % eid)
            comps = {}
            top = _resolve(addr_map, leaf["comp_top"])
            if top["type"] != "EMPTY":
                for cleaf in _walk_leaves(addr_map, leaf["comp_top"], "LEAF_COMP", cand):
                    comp = cleaf["comp"]
                    if comp in comps:
                        raise d.malformed("DUP_KEY", "component %s twice on %s" % (comp, eid))
                    comps[comp] = cleaf["value"]
            entities[eid] = comps

    state = {"entities": entities, "alloc": alloc, "rng": {"seed": seed, "counter": counter}}

    # rebuild-and-compare: the presented bytes must equal the canonical serialization of the reconstructed state
    # (uses the ACTIVE key-hasher for routing -> G2 consistency).
    rebuilt = serialize_state(state, cand, keyhasher, limits)
    if rebuilt != buf:
        raise d.malformed("CANONICALITY", "presented tree != construct(reconstructed state)")
    return state
