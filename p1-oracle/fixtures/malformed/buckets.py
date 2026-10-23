"""Crafted misplaced-bucket vectors. Each is well-FRAMED (consistent hashes, ordered collection, resolvable root) so
it reaches the Tier-2 bucket-placement check and is rejected for the SPECIFIC placement reason, not a framing/digest
fault or a generic rebuild-compare. Each comes with its defect-removed counterpart, which must validate cleanly.
"""
from oracle import decoder as d
from oracle import canonicality as C

_HBASE = int.from_bytes(bytes(range(1, 33)), "big")


def _ek(eid):
    return d.encode_key("eid", eid)


def _container(root_enc, extra_nodes):
    nodes = sorted(set([root_enc] + extra_nodes), key=d.node_address)
    return (d.DOM("skuld-state-0") + d.u16(d.VERSION) + d.raw32(d.node_address(root_enc))
            + d.u64(len(nodes)) + b"".join(nodes))


def misplaced_depth(cand):
    """A well-framed tree with a BUCKET placed directly beneath the ROOT (construction depth 1, must be 52).
    Rejection: BUCKET_MISPLACED. Defect-removed counterpart: the canonical full-collision tree (bucket at depth 52)."""
    empty = d.enc_empty(cand)
    eh = d.node_address(empty)
    le1 = d.enc_leaf_ent(cand, "e1", eh)
    le2 = d.enc_leaf_ent(cand, "e2", eh)
    members = sorted([(_ek("e1"), le1), (_ek("e2"), le2)], key=lambda kv: kv[0])
    bucket = d.enc_bucket(cand, members)
    root = d.enc_root(cand, {0: d.node_address(bucket)}, d.enc_scalars(3, 0, 0))
    buf = _container(root, [empty, bucket])
    return buf  # validate under any key-hasher: depth 1 != 52 fails first


def colliding_tree(cand):
    """Canonical full-collision tree: e1,e2 forced (INJECTED) to the identical key-hash -> a legit BUCKET at depth 52.
    Returns (state, buf, keyhasher_collide, keyhasher_noncollide)."""
    st = {"entities": {"e1": {}, "e2": {}}, "alloc": 3, "rng": {"seed": 0, "counter": 0}}
    kh_coll = d.InjectedKeyHasher({_ek("e1"): _HBASE, _ek("e2"): _HBASE})
    kh_noncoll = d.InjectedKeyHasher({_ek("e1"): _HBASE, _ek("e2"): _HBASE ^ 1})
    buf = C.serialize_state(st, cand, keyhasher=kh_coll)
    return st, buf, kh_coll, kh_noncoll
