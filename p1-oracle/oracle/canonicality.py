"""Canonical construction and whole-state (Tier-2) validation (ENCODING-TABLE-P1.md §3, §4, §4a, §8).

construct() is the one deterministic shape function (§4). build_state()/serialize_state() encode a state. Tier-2
validation reconstructs the logical state from a presented serialization and then REBUILDS-AND-COMPARES against the
canonical serialization of that state (byte-identical or reject) — which enforces shape, bucket placement, ordering,
no orphans, and DAG sharing in one check. Routing uses the ACTIVE key-hasher (G2 consistency); node addressing is
decoder.node_address (production SHA-256), never the key-hash seam (G2 isolation).
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


def _check_buckets(addr_map, root_hash, cand, keyhasher):
    """Dedicated BUCKET placement check (§4), run BEFORE the generic rebuild-and-compare so a misplaced bucket is
    rejected for its SPECIFIC reason: BUCKET_MISPLACED (not at construction depth 52) or BUCKET_NOT_COLLIDING (its
    members do not all share every one of the 52 chunks under the ACTIVE key-hash). Depth is tracked structurally:
    entity-trie children start at depth 1, component-trie tops at depth 0; a BRANCH's children are one deeper."""
    root = _resolve(addr_map, root_hash)
    for _slot, child in root["children"]:
        _bwalk(addr_map, child, 1, "eid", cand, keyhasher)


def _bwalk(addr_map, addr, depth, kind, cand, keyhasher):
    node = _resolve(addr_map, addr)
    t = node["type"]
    if t == "BRANCH":
        for _s, ch in node["children"]:
            _bwalk(addr_map, ch, depth + 1, kind, cand, keyhasher)
    elif t == "BUCKET":
        if depth != 52:
            raise d.malformed("BUCKET_MISPLACED", "bucket at construction depth %d (must be 52), %s trie" % (depth, kind))
        hashes = set()
        for _kb, leaf_enc in node["members"]:
            m = d.decode_node(leaf_enc, cand)
            hashes.add(keyhasher(m["key_bytes"]))
            if kind == "eid":
                _descend_comp(addr_map, m, cand, keyhasher)
        if len(hashes) != 1:
            raise d.malformed("BUCKET_NOT_COLLIDING", "members do not all fully collide under the active key-hash")
    elif t == "LEAF_ENT":
        _descend_comp(addr_map, node, cand, keyhasher)
    # LEAF_COMP / EMPTY: nothing to descend (a bucket cannot hang beneath them)


def _descend_comp(addr_map, leaf_ent, cand, keyhasher):
    top = _resolve(addr_map, leaf_ent["comp_top"])
    if top["type"] != "EMPTY":
        _bwalk(addr_map, leaf_ent["comp_top"], 0, "comp", cand, keyhasher)


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


def reconstruct(buf, cand, keyhasher=d.prod_key_hasher, limits=d.PROD_LIMITS):
    """Tier-2: parse, reconstruct the logical ECS state, then rebuild-and-compare for canonicality (§8)."""
    root_hash, order, addr_map = parse_collection(buf, cand, limits)
    root = _resolve(addr_map, root_hash)
    if root["type"] != "ROOT":
        raise d.malformed("ROOT_TYPE", root["type"])
    # dedicated bucket-placement check (specific reason, before the generic rebuild-and-compare)
    _check_buckets(addr_map, root_hash, cand, keyhasher)
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
