"""P1V-seam (G2): injected-routing fixtures (final-bit divergence, full collision, bucket+leaf under a two-slot
BRANCH(51)), seam CONSISTENCY (one injected H for build AND validate) and seam ISOLATION (swapping H changes no node
address or collection order), plus the key-hash KAT with the seam DISABLED. All injected results are labelled injected.
"""
import hashlib

from oracle import decoder as d
from oracle import canonicality as C
from .harness import Cases, reject

# A 256-bit base value for crafting controlled key-hashes (INJECTED; never a real SHA-256 outcome).
_HBASE = int.from_bytes(bytes(range(1, 33)), "big")
_H_EVEN = _HBASE & ~1          # bit0 = 0
_H_ODD = _H_EVEN | 1           # bit0 = 1 (agrees with _H_EVEN on bits 255..1; differs only at the final bit)


def _ek(eid):
    return d.encode_key("eid", eid)


def _types(coll, cand):
    return [d.decode_node(enc, cand)["type"] for enc in coll.values()]


def run():
    c = Cases()

    # --- injected FINAL-BIT divergence -> a two-slot BRANCH(51) [INJECTED] ---
    def final_bit():
        st = {"entities": {"e1": {}, "e2": {}}, "alloc": 3, "rng": {"seed": 0, "counter": 0}}
        kh = d.InjectedKeyHasher({_ek("e1"): _H_EVEN, _ek("e2"): _H_ODD})
        rh, coll = C.build_state(st, "B", keyhasher=kh)
        branch51 = [d.decode_node(e, "B") for e in coll.values()
                    if d.decode_node(e, "B")["type"] == "BRANCH" and d.decode_node(e, "B")["level"] == 51]
        if len(branch51) != 1 or len(branch51[0]["children"]) != 2:
            raise AssertionError("expected one two-slot BRANCH(51), got %r" % branch51)
        buf = C.serialize_state(st, "B", keyhasher=kh)
        if C.reconstruct(buf, "B", keyhasher=kh) != st:
            raise AssertionError("injected final-bit round-trip failed")
        return "INJECTED two-slot BRANCH(51)"
    c.ok("P1V-seam injected final-bit divergence -> two-slot BRANCH(51) [INJECTED]", final_bit)

    # --- injected FULL collision -> a terminal BUCKET [INJECTED] ---
    def full_collision():
        st = {"entities": {"e1": {}, "e2": {}}, "alloc": 3, "rng": {"seed": 0, "counter": 0}}
        kh = d.InjectedKeyHasher({_ek("e1"): _HBASE, _ek("e2"): _HBASE})   # identical 256-bit H
        rh, coll = C.build_state(st, "B", keyhasher=kh)
        buckets = [d.decode_node(e, "B") for e in coll.values() if d.decode_node(e, "B")["type"] == "BUCKET"]
        if len(buckets) != 1 or buckets[0]["count"] != 2:
            raise AssertionError("expected one BUCKET(count=2), got %r" % buckets)
        buf = C.serialize_state(st, "B", keyhasher=kh)
        if C.reconstruct(buf, "B", keyhasher=kh) != st:
            raise AssertionError("injected full-collision round-trip failed")
        return "INJECTED BUCKET count=2"
    c.ok("P1V-seam injected full collision -> terminal BUCKET [INJECTED]", full_collision)

    # --- bucket + leaf under a two-slot BRANCH(51) [INJECTED] ---
    def bucket_and_leaf():
        st = {"entities": {"e1": {}, "e2": {}, "e3": {}}, "alloc": 4, "rng": {"seed": 0, "counter": 0}}
        kh = d.InjectedKeyHasher({_ek("e1"): _H_EVEN, _ek("e2"): _H_EVEN, _ek("e3"): _H_ODD})
        rh, coll = C.build_state(st, "B", keyhasher=kh)
        nodes = [d.decode_node(e, "B") for e in coll.values()]
        b51 = [n for n in nodes if n["type"] == "BRANCH" and n["level"] == 51]
        buckets = [n for n in nodes if n["type"] == "BUCKET"]
        if not (len(b51) == 1 and len(b51[0]["children"]) == 2 and len(buckets) == 1 and buckets[0]["count"] == 2):
            raise AssertionError("expected two-slot BRANCH(51) with a BUCKET(2) and a LEAF_ENT sibling")
        if C.reconstruct(C.serialize_state(st, "B", keyhasher=kh), "B", keyhasher=kh) != st:
            raise AssertionError("bucket+leaf round-trip failed")
        return "INJECTED BRANCH(51){BUCKET(2), LEAF_ENT}"
    c.ok("P1V-seam bucket + leaf under two-slot BRANCH(51) [INJECTED]", bucket_and_leaf)

    # --- seam CONSISTENCY: build under H, validate under H -> OK; validate under a DIFFERENT hash -> reject ---
    def consistency():
        st = {"entities": {"e1": {}, "e2": {}}, "alloc": 3, "rng": {"seed": 0, "counter": 0}}
        kh = d.InjectedKeyHasher({_ek("e1"): _H_EVEN, _ek("e2"): _H_ODD})
        buf = C.serialize_state(st, "B", keyhasher=kh)
        if C.reconstruct(buf, "B", keyhasher=kh) != st:                 # same H -> canonical
            raise AssertionError("consistent-H validation failed")
        # validate the SAME bytes under production SHA-256 routing -> canonicality disagreement -> reject
        reject(lambda: C.reconstruct(buf, "B", keyhasher=d.prod_key_hasher), code="CANONICALITY")
    c.ok("P1V-seam consistency: build-H==validate-H passes; different H -> CANONICALITY reject", consistency)

    # --- seam ISOLATION: swapping H changes NO node address or collection order of a fixed encoded tree ---
    def isolation():
        st = {"entities": {"e1": {}, "e2": {}}, "alloc": 3, "rng": {"seed": 0, "counter": 0}}
        kh = d.InjectedKeyHasher({_ek("e1"): _H_EVEN, _ek("e2"): _H_ODD})
        buf = C.serialize_state(st, "B", keyhasher=kh)
        _rh, order1, amap1 = C.parse_collection(buf, "B")
        _rh2, order2, amap2 = C.parse_collection(buf, "B")
        if order1 != order2:
            raise AssertionError("parse order not deterministic")
        # node addresses are production SHA-256 over encodings, independent of any key-hash
        for a in order1:
            if a != hashlib.sha256(amap1[a]["_encoding"]).digest():
                raise AssertionError("node address not SHA256(encoding) -- seam leaked into addressing")
        # the test BITES: if addressing wrongly incorporated the key-hash, the order would change
        hb = _HBASE.to_bytes(32, "big")
        leak_order = sorted((amap1[a]["_encoding"] for a in order1),
                            key=lambda e: hashlib.sha256(e + hb).digest())
        real_order = [amap1[a]["_encoding"] for a in order1]
        if leak_order == real_order:
            raise AssertionError("plant inert: a seam leak would not change order for this fixture")
        return "addresses/order are H-independent; a leak WOULD reorder (plant bites)"
    c.ok("P1V-seam isolation: swapping H changes no node address/order; plant bites", isolation)

    # --- key-hash KAT with the seam DISABLED: H == int.from_bytes(sha256(KEY), 'big') ---
    def kat():
        for eid in ("e1", "entity-longer-name", "x"):
            kb = _ek(eid)
            want = int.from_bytes(hashlib.sha256(kb).digest(), "big")
            if d.prod_key_hasher(kb) != want:
                raise AssertionError("prod key-hash != sha256(KEY) for %s" % eid)
    c.ok("P1V-keyhash-kat: production key-hash == sha256(KEY), seam disabled", kat)

    return c.done()
