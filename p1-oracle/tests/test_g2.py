"""G2 trie shape (ordinary, real SHA-256 routing) + structural rejections. Injected final-bit/full-collision and the
seam consistency/isolation assertions are in test_seams (reported under G2 by the gate runner)."""
from oracle import decoder as d
from oracle import canonicality as C
from .harness import Cases, reject


def _multi_comp_state():
    # several components almost surely route to >= 2 slots at depth 0 under real SHA-256 -> a BRANCH top
    return {"entities": {"e1": {"hp": 10, "name": "orc", "pos": 5, "tag": "alpha", "lvl": 2}},
            "alloc": 2, "rng": {"seed": 0, "counter": 0}}


def run():
    c = Cases()

    # ordinary routing: multi-component top is a BRANCH; shared-prefix handled by construct; round-trips (real SHA-256)
    def ordinary_branch():
        st = _multi_comp_state()
        rh, coll = C.build_state(st, "A")
        # the component trie top for e1 must be a BRANCH (>=2 components)
        root = d.decode_node(coll[rh], "A")
        le_addr = root["children"][0][1]
        le = d.decode_node(coll[le_addr], "A")
        top = d.decode_node(coll[le["comp_top"]], "A")
        if top["type"] != "BRANCH":
            raise AssertionError("component top is %s, expected BRANCH" % top["type"])
        if C.reconstruct(C.serialize_state(st, "A"), "A") != st:
            raise AssertionError("round-trip failed")
    c.ok("G2 ordinary routing -> BRANCH top + round-trip (real SHA-256)", ordinary_branch)

    # node-order rejection: reorder two nodes in a valid serialization
    def reorder():
        st = _multi_comp_state()
        buf = C.serialize_state(st, "A")
        rh, order, amap = C.parse_collection(buf, "A")
        encs = [amap[a]["_encoding"] for a in order]
        if len(encs) < 2:
            raise AssertionError("need >=2 nodes to reorder")
        swapped = encs[:]
        swapped[0], swapped[1] = swapped[1], swapped[0]
        bad = d.DOM("skuld-state-0") + d.u16(d.VERSION) + d.raw32(rh) + d.u64(len(swapped)) + b"".join(swapped)
        reject(lambda: C.reconstruct(bad, "A"), code="NODE_ORDER")
    c.ok("G2 reorder nodes -> NODE_ORDER reject", reorder)

    # missing child: drop a referenced node
    def missing():
        st = _multi_comp_state()
        buf = C.serialize_state(st, "A")
        rh, order, amap = C.parse_collection(buf, "A")
        # drop a non-root node
        keep = [a for a in order if a != rh]
        drop = keep[0]
        remaining = [amap[a]["_encoding"] for a in order if a != drop]
        bad = d.DOM("skuld-state-0") + d.u16(d.VERSION) + d.raw32(rh) + d.u64(len(remaining)) + b"".join(remaining)
        reject(lambda: C.reconstruct(bad, "A"), code="MISSING_CHILD")
    c.ok("G2 drop referenced node -> MISSING_CHILD reject", missing)

    # Tier-1 bucket count < 2 (hand-crafted single-member bucket)
    def bucket_count():
        lc = d.enc_leaf_comp("A", "hp", 10)
        bad_bucket = d.dom("A", "bucket") + d.u16(d.VERSION) + d.u8(0x05) + d.u32(1) + lc  # count=1
        reject(lambda: d.decode_node(bad_bucket, "A"), code="BUCKET_COUNT")
    c.ok("G2 bucket count<2 -> reject", bucket_count)

    # Tier-1 bitmap high bits at level 51 (Candidate B BRANCH level 51, bit >=2 set)
    def bitmap_high():
        # BRANCH(51) with bitmap 0b100 (bit 2) and one child -> reject BITMAP_HIGH_BITS
        child = d.node_address(d.enc_empty("B"))
        bad = d.dom("B", "branch") + d.u16(d.VERSION) + d.u8(0x02) + d.u8(51) + d.u32(0b100) + child
        reject(lambda: d.decode_node(bad, "B"), code="BITMAP_HIGH_BITS")
    c.ok("G2 BRANCH level51 high bitmap bit -> reject", bitmap_high)

    return c.done()
