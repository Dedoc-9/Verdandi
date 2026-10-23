"""G3 reconstruction: DAG sharing, empty maps, duplicate keys, orphan/missing-child, node-order, full ECS field
recovery and mutate-one-field divergence, and the block-D scalar-type gate."""
import copy

from oracle import decoder as d
from oracle import canonicality as C
from .harness import Cases, reject


def run():
    c = Cases()

    # DAG: two entities with identical component maps share ONE component root (counted once)
    def dag_share():
        st = {"entities": {"e1": {"hp": 1}, "e2": {"hp": 1}}, "alloc": 3, "rng": {"seed": 0, "counter": 0}}
        rh, coll = C.build_state(st, "A")
        # exactly one LEAF_COMP node for hp=1, shared
        comps = [enc for enc in coll.values() if d.decode_node(enc, "A")["type"] == "LEAF_COMP"]
        if len(comps) != 1:
            raise AssertionError("expected 1 shared LEAF_COMP, got %d" % len(comps))
        if C.reconstruct(C.serialize_state(st, "A"), "A") != st:
            raise AssertionError("round-trip failed")
    c.ok("G3 shared component root is one DAG node + round-trips", dag_share)

    # empty component map and empty entity map
    def empties():
        g = {"entities": {}, "alloc": 1, "rng": {"seed": 0, "counter": 0}}
        e = {"entities": {"e1": {}}, "alloc": 2, "rng": {"seed": 0, "counter": 0}}
        for st in (g, e):
            if C.reconstruct(C.serialize_state(st, "A"), "A") != st:
                raise AssertionError("empty-map round-trip failed for %r" % st)
    c.ok("G3 empty component/entity maps round-trip", empties)

    # full ECS field recovery + mutate-one-field divergence
    def fields():
        st = {"entities": {"e1": {"hp": 3, "name": "x"}, "e2": {"k": -7}}, "alloc": 4,
              "rng": {"seed": 5, "counter": 2}}
        if C.reconstruct(C.serialize_state(st, "A"), "A") != st:
            raise AssertionError("field recovery failed")
        for mut in ("alloc", "seed", "counter", "value"):
            m = copy.deepcopy(st)
            if mut == "alloc":
                m["alloc"] = 5
            elif mut == "seed":
                m["rng"]["seed"] = 6
            elif mut == "counter":
                m["rng"]["counter"] = 3
            else:
                m["entities"]["e1"]["hp"] = 99
            if C.serialize_state(m, "A") == C.serialize_state(st, "A"):
                raise AssertionError("mutating %s did not change the serialization" % mut)
    c.ok("G3 every ECS field recovered; mutating any one changes the bytes", fields)

    # duplicate entity key -> reject (crafted: two LEAF_ENT for 'e1')
    def dup_key():
        empty = d.enc_empty("A")
        lc = d.enc_leaf_comp("A", "hp", 1)
        le1 = d.enc_leaf_ent("A", "e1", d.node_address(empty))
        le2 = d.enc_leaf_ent("A", "e1", d.node_address(lc))
        root = d.enc_root("A", {0: d.node_address(le1), 1: d.node_address(le2)}, d.enc_scalars(3, 0, 0))
        nodes = sorted([empty, lc, le1, le2, root], key=d.node_address)
        buf = d.DOM("skuld-state-0") + d.u16(d.VERSION) + d.raw32(d.node_address(root)) + d.u64(len(nodes)) + b"".join(nodes)
        reject(lambda: C.reconstruct(buf, "A"), code="DUP_KEY")
    c.ok("G3 duplicate entity key -> DUP_KEY reject", dup_key)

    # orphan node (unreferenced) -> rejected (rebuild-and-compare)
    def orphan():
        st = {"entities": {"e1": {"hp": 1}}, "alloc": 2, "rng": {"seed": 0, "counter": 0}}
        buf = C.serialize_state(st, "A")
        rh, order, amap = C.parse_collection(buf, "A")
        orphan_enc = d.enc_leaf_comp("A", "zzz", 123)   # not referenced by anything
        encs = [amap[a]["_encoding"] for a in order] + [orphan_enc]
        encs = sorted(set(encs), key=d.node_address)
        bad = d.DOM("skuld-state-0") + d.u16(d.VERSION) + d.raw32(rh) + d.u64(len(encs)) + b"".join(encs)
        reject(lambda: C.reconstruct(bad, "A"), code="CANONICALITY")
    c.ok("G3 orphan node -> CANONICALITY reject", orphan)

    # block D: a string-valued scalar -> reject
    def scalar_type():
        # SCALARS with alloc as a STR value
        bad_scalars = (d.DOM("skuld-scalars-0") + b"A" + d.encode_value("two")
                       + b"S" + d.encode_value(0) + b"C" + d.encode_value(0))
        root = d.dom("A", "root") + d.u16(d.VERSION) + d.u8(0x01) + d.u32(0) + bad_scalars
        reject(lambda: d.decode_node(root, "A"), code="SCALAR_NOT_INT")
    c.ok("G3 string-valued scalar -> SCALAR_NOT_INT reject (block D)", scalar_type)

    return c.done()
