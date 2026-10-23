"""0258 structural-rejection closure (reported under G2): ROOT/BRANCH duplicate-child (DUP_CHILD at Tier-1), malformed
inline bucket members (rejected for the specific local reason), and a misrouted leaf (CANONICALITY via rebuild-compare,
the P6 equivalence witness). Both candidates; each negative paired with an accepting counterpart so the rejection is
shown specific, not a blanket failure."""
from oracle import decoder as d
from oracle import canonicality as C
from .harness import Cases, reject

_HBASE = int.from_bytes(bytes(range(1, 33)), "big")


def _ek(eid):
    return d.encode_key("eid", eid)


def _container(root_enc, extra):
    nodes = sorted(set([root_enc] + extra), key=d.node_address)
    return (d.DOM("skuld-state-0") + d.u16(d.VERSION) + d.raw32(d.node_address(root_enc))
            + d.u64(len(nodes)) + b"".join(nodes))


def _bucket(members, cand):
    out = d.dom(cand, "bucket") + d.u16(d.VERSION) + d.u8(0x05)
    if cand == "B":
        out += d.u8(52)
    out += d.u32(len(members))
    for m in members:
        out += m
    return out


def run():
    c = Cases()
    for cand in ("A", "B"):
        empty = d.enc_empty(cand)
        eh = d.node_address(empty)

        # --- ROOT duplicate child hash -> DUP_CHILD at Tier-1 (0258 fix) ---
        def root_dup(cand=cand, eh=eh):
            le = d.enc_leaf_ent(cand, "e1", eh)
            lh = d.node_address(le)
            root = d.enc_root(cand, {0: lh, 1: lh}, d.enc_scalars(2, 0, 0))
            reject(lambda: C.reconstruct(_container(root, [empty, le]), cand), code="DUP_CHILD")
        c.ok("G2 ROOT dup child hash -> DUP_CHILD (Tier-1) [%s]" % cand, root_dup)

        # --- BRANCH duplicate child hash -> DUP_CHILD ---
        def branch_dup(cand=cand, eh=eh):
            lc = d.enc_leaf_comp(cand, "hp", 1)
            ch = d.node_address(lc)
            br = d.enc_branch(cand, 0, {0: ch, 1: ch})
            le = d.enc_leaf_ent(cand, "e1", d.node_address(br))
            root = d.enc_root(cand, {0: d.node_address(le)}, d.enc_scalars(2, 0, 0))
            reject(lambda: C.reconstruct(_container(root, [lc, br, le]), cand), code="DUP_CHILD")
        c.ok("G2 BRANCH dup child hash -> DUP_CHILD [%s]" % cand, branch_dup)

        # --- positive counterpart: distinct children accept (injected distinct chunk(0) slots) ---
        def distinct_ok(cand=cand):
            st = {"entities": {"e1": {}, "e2": {}}, "alloc": 3, "rng": {"seed": 0, "counter": 0}}
            kh = d.InjectedKeyHasher({_ek("e1"): 0, _ek("e2"): 1 << 251})   # chunk(0) = 0 vs 1
            buf = C.serialize_state(st, cand, keyhasher=kh)
            if C.reconstruct(buf, cand, keyhasher=kh) != st:
                raise AssertionError("distinct-children ROOT did not round-trip")
        c.ok("G2 distinct ROOT children accept (counterpart) [%s]" % cand, distinct_ok)

        # --- malformed inline bucket members, each rejected for its specific local reason ---
        le_a = d.enc_leaf_ent(cand, "e1", eh)
        le_b = d.enc_leaf_ent(cand, "e2", eh)
        mem = sorted([le_a, le_b], key=lambda e: d.decode_node(e, cand)["key_bytes"])
        other = "B" if cand == "A" else "A"
        le_wrongdom = d.enc_leaf_ent(other, "e2", d.node_address(d.enc_empty(other)))
        le_wrongver = d.dom(cand, "leafent") + d.u16(1) + d.u8(0x03) + d.encode_key("eid", "e2") + eh
        lc = d.enc_leaf_comp(cand, "hp", 1)
        mix = sorted([le_a, lc], key=lambda e: d.decode_node(e, cand)["key_bytes"])
        bad_val = d.dom(cand, "leafcomp") + d.u16(d.VERSION) + d.u8(0x04) + d.encode_key("comp", "hp") + bytes([0x09, 0x00])

        def inline_valid(cand=cand, mem=mem):
            d.decode_node(_bucket(mem, cand), cand)        # parses (count 2, ordered, uniform) -> accepted
        c.ok("G2 inline bucket valid members parse (counterpart) [%s]" % cand, inline_valid)

        for label, members, code in (
            ("wrong candidate domain", [mem[0], le_wrongdom], "DOMAIN"),
            ("wrong VERSION", [le_a, le_wrongver], "VERSION"),
            ("duplicate member", [mem[0], mem[0]], "BUCKET_DUP_KEY"),
            ("out of order", [mem[1], mem[0]], "BUCKET_ORDER"),
            ("mixed leaf types", mix, "BUCKET_MIXED"),
            ("malformed value", [bad_val, le_a], "VTYPE"),
        ):
            c.ok("G2 inline member %s -> %s [%s]" % (label, code, cand),
                 lambda members=members, code=code, cand=cand: reject(lambda: d.decode_node(_bucket(members, cand), cand), code=code))

        # --- misrouting: a leaf under the wrong ROOT slot. Since 0263 the explicit P6 walk runs before rebuild-and-
        # compare, so this is now rejected with the specific WALK_MISROUTE (was the generic CANONICALITY). ---
        def misrouted(cand=cand, eh=eh):
            le = d.enc_leaf_ent(cand, "e1", eh)
            lh = d.node_address(le)
            H = d.prod_key_hasher(_ek("e1"))
            wrong = (d.chunk(H, 0) + 1) % 32
            root = d.enc_root(cand, {wrong: lh}, d.enc_scalars(2, 0, 0))
            reject(lambda: C.reconstruct(_container(root, [empty, le]), cand), code="WALK_MISROUTE")
        c.ok("G2 misrouted leaf (wrong ROOT slot) -> WALK_MISROUTE [%s]" % cand, misrouted)

    return c.done()
