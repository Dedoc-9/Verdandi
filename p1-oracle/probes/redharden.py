"""RH-T1..RH-T5 red-hardening falsification PROBES (test-only, OFF-GATE; NOT imported by run_gate.py).

These EXECUTE the falsification-test proposals from docs/P1-RED-HARDENING-AUDIT.md against the 0263 implementation and
record, per probe, one of: PASS (the apparatus behaved as the test demanded), FAIL (a real defect — would be escalated
as a proposed S-9+), BLOCKED (a D4-2/D8 item, never a pass), N.A. (the external case's mechanism does not arise), or
OBSERVED (a measurement, not a pass/fail). Concrete inputs and observed outcomes are printed. A FAIL (non-OracleError
crash, a hang-shaped iteration, or a wrong accept/reject) exits non-zero.

Run:  PYTHONHASHSEED=0 PYTHONUTF8=1 python p1-oracle/probes/redharden.py
This is a probe record, not a gate and not a conformance claim; P-1 remains OPEN.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from oracle import decoder as d          # noqa: E402
from oracle import canonicality as C     # noqa: E402
from oracle import records as R          # noqa: E402
from oracle import checkpoints as K      # noqa: E402
from oracle.frozen import ecs            # noqa: E402
from fixtures.malformed import walk as W  # noqa: E402
from fixtures.malformed import buckets as B  # noqa: E402

ROWS = []


def row(rid, verdict, label, detail=""):
    ROWS.append((rid, verdict, label, detail))
    print("%-7s %-9s %s%s" % (rid, verdict, label, ("  -- " + detail) if detail else ""))


def _ek(eid):
    return d.encode_key("eid", eid)


def _container(root_enc, extra):
    nodes = sorted(set([root_enc] + extra), key=d.node_address)
    return (d.DOM("skuld-state-0") + d.u16(d.VERSION) + d.raw32(d.node_address(root_enc))
            + d.u64(len(nodes)) + b"".join(nodes))


def _raised(fn):
    """Return (kind, code): kind in {'malformed','blocked','semantic','ok','CRASH'}; code is the OracleError code or the
    crashing exception type name. A non-OracleError (MemoryError, RecursionError, OverflowError, ...) is a CRASH = FAIL."""
    try:
        fn()
        return ("ok", None)
    except d.OracleError as e:
        return ({d.MALFORMED: "malformed", d.BLOCKED: "blocked", d.SEMANTIC: "semantic"}.get(e.category, e.category), e.code)
    except Exception as e:  # noqa: BLE001 - a non-OracleError here is exactly the defect class the probe hunts
        return ("CRASH", type(e).__name__)


# =====================================================================================================================
# RH-T1 — resource bounds reject BEFORE work/allocation (OpenSSL CVE-2026-34180 lesson; matrix R0.2/R0.4/R0.5, G6)
# =====================================================================================================================
def rh_t1():
    # (a) an lp length past MAX_LEN is rejected on the u64 prefix, before any body is buffered
    kind, code = _raised(lambda: d.Reader(d.u64(2 ** 40)).lp())
    row("RH-T1", "PASS" if (kind, code) == ("malformed", "LP_TOO_LONG") else "FAIL",
        "lp length 2**40 (>MAX_LEN) rejected on the prefix", "input=u64(2**40); outcome=%s/%s" % (kind, code))

    # (b) an lp length within MAX_LEN but past the buffer -> TRUNCATED (bounds check, no over-read)
    kind, code = _raised(lambda: d.Reader(d.u64(1000) + b"abc").lp())
    row("RH-T1", "PASS" if (kind, code) == ("malformed", "TRUNCATED") else "FAIL",
        "lp length 1000 with 3 payload bytes -> TRUNCATED", "input=u64(1000)+3B; outcome=%s/%s" % (kind, code))

    # (c) a node_count past MAX_NODES is rejected on the u64, before the node loop
    big = d.DOM("skuld-state-0") + d.u16(d.VERSION) + d.raw32(bytes(32)) + d.u64(2 ** 40)
    kind, code = _raised(lambda: C.parse_collection(big, "A"))
    row("RH-T1", "PASS" if (kind, code) == ("malformed", "MAX_NODES") else "FAIL",
        "node_count 2**40 (>MAX_NODES) rejected on the prefix", "outcome=%s/%s" % (kind, code))

    # (d) a node_count just under MAX_NODES with no node bytes does not hang: the first read fails fast (lazy range())
    near = d.DOM("skuld-state-0") + d.u16(d.VERSION) + d.raw32(bytes(32)) + d.u64(2 ** 32 - 2)
    kind, code = _raised(lambda: C.parse_collection(near, "A"))
    row("RH-T1", "PASS" if kind == "malformed" else "FAIL",
        "node_count 2**32-2 with no nodes -> fast reject (no hang/alloc)", "outcome=%s/%s" % (kind, code))

    # (e) a bucket with a huge count and no member bytes fails on the first member read, not after allocating count
    bk = d.dom("A", "bucket") + d.u16(d.VERSION) + d.u8(0x05) + d.u32(2 ** 32 - 1)
    kind, code = _raised(lambda: d.decode_node(bk, "A"))
    row("RH-T1", "PASS" if kind == "malformed" else "FAIL",
        "bucket count 2**32-1 with no members -> fast reject", "outcome=%s/%s" % (kind, code))

    # (f) individually-legal nodes that together exceed MAX_TOTAL are rejected (parser), under a reduced limit
    st = {"entities": {"e1": {"hp": 1}, "e2": {"k": 2}}, "alloc": 3, "rng": {"seed": 0, "counter": 0}}
    buf = C.serialize_state(st, "A")
    _rh, order, amap = C.parse_collection(buf, "A")
    total = sum(len(amap[a]["_encoding"]) for a in order)
    lim = d.Limits(max_total=total - 1)
    kind, code = _raised(lambda: C.parse_collection(buf, "A", limits=lim))
    row("RH-T1", "PASS" if (kind, code) == ("malformed", "MAX_TOTAL") else "FAIL",
        "collectively-over-MAX_TOTAL (legal singles) -> MAX_TOTAL", "max_total=%d<%d; outcome=%s/%s" % (total - 1, total, kind, code))


# =====================================================================================================================
# RH-T2 — independent canonicality: near-neighbour accept/reject on a composite state (matrix R3.1/R4a.1, G-1)
# =====================================================================================================================
def rh_t2():
    st = {"entities": {"e1": {"hp": 3, "name": "x"}, "e2": {"k": -7}}, "alloc": 4, "rng": {"seed": 5, "counter": 2}}
    for cand in ("A", "B"):
        buf = C.serialize_state(st, cand)
        ok = (C.reconstruct(buf, cand) == st)
        row("RH-T2", "PASS" if ok else "FAIL", "composite round-trips (accepting control) [%s]" % cand,
            "entities=2, mixed int/str/neg; len=%d" % len(buf))

        _rh, order, amap = C.parse_collection(buf, cand)
        encs = [amap[a]["_encoding"] for a in order]
        # reversed node order
        rev = d.DOM("skuld-state-0") + d.u16(d.VERSION) + d.raw32(_rh) + d.u64(len(encs)) + b"".join(reversed(encs))
        kind, code = _raised(lambda: C.reconstruct(rev, cand))
        row("RH-T2", "PASS" if code == "NODE_ORDER" else "FAIL", "reversed node order -> NODE_ORDER [%s]" % cand, "outcome=%s/%s" % (kind, code))
        # drop one referenced node (keep root) -> missing child
        drop = [e for e in encs if d.node_address(e) != order[0]] if order[0] != _rh else encs[:-1]
        miss = d.DOM("skuld-state-0") + d.u16(d.VERSION) + d.raw32(_rh) + d.u64(len(drop)) + b"".join(drop)
        kind, code = _raised(lambda: C.reconstruct(miss, cand))
        row("RH-T2", "PASS" if code in ("MISSING_CHILD", "MAX_NODES", "NODE_ORDER") else "FAIL",
            "a referenced node dropped -> rejected [%s]" % cand, "outcome=%s/%s" % (kind, code))

    # misplaced leaf (reuse the 0263 walk fixture): off-path -> WALK_MISROUTE
    for cand in ("A", "B"):
        mbuf, kh = W.misroute_root(cand)
        kind, code = _raised(lambda: C.reconstruct(mbuf, cand, keyhasher=kh))
        row("RH-T2", "PASS" if code == "WALK_MISROUTE" else "FAIL", "misplaced leaf -> WALK_MISROUTE [%s]" % cand, "outcome=%s/%s" % (kind, code))

    # non-minimal int value in a LEAF_COMP (alternate int form) -> INT_NONMINIMAL
    bad = d.dom("A", "leafcomp") + d.u16(d.VERSION) + d.u8(0x04) + d.encode_key("comp", "hp") + bytes([0x01, 0x00]) + d.lp(bytes([0x00, 0x05]))
    kind, code = _raised(lambda: d.decode_node(bad, "A"))
    row("RH-T2", "PASS" if code == "INT_NONMINIMAL" else "FAIL", "non-minimal int (alt form) -> INT_NONMINIMAL", "outcome=%s/%s" % (kind, code))
    row("RH-T2", "N.A.", "a SECOND independent encoder from the prose (full G-1 close)", "not run; recorded residual, not a defect")


# =====================================================================================================================
# RH-T3 — structural uniqueness, cases (a)-(e) (matrix R4a.2, G2/G3; S-8)
# =====================================================================================================================
def rh_t3():
    cand = "A"
    empty = d.enc_empty(cand); eh = d.node_address(empty)
    # (a) two identical child refs in one parent -> DUP_CHILD
    le = d.enc_leaf_ent(cand, "e1", eh); lh = d.node_address(le)
    root = d.enc_root(cand, {0: lh, 1: lh}, d.enc_scalars(2, 0, 0))
    kind, code = _raised(lambda: C.reconstruct(_container(root, [empty, le]), cand))
    row("RH-T3", "PASS" if code == "DUP_CHILD" else "FAIL", "(a) identical child refs in one parent -> DUP_CHILD", "outcome=%s/%s" % (kind, code))

    # (b) one component subtree shared across two entities -> lawful DAG (one shared node, round-trips)
    st = {"entities": {"e1": {"hp": 1}, "e2": {"hp": 1}}, "alloc": 3, "rng": {"seed": 0, "counter": 0}}
    _rh, coll = C.build_state(st, cand)
    comps = [e for e in coll.values() if d.decode_node(e, cand)["type"] == "LEAF_COMP"]
    ok = (len(comps) == 1 and C.reconstruct(C.serialize_state(st, cand), cand) == st)
    row("RH-T3", "PASS" if ok else "FAIL", "(b) component subtree shared across entities -> lawful DAG", "shared LEAF_COMP nodes=%d" % len(comps))

    # (c) duplicate logical key -> rejected (walk first: WALK_MISROUTE; DUP_KEY backstop with walk off)
    lc = d.enc_leaf_comp(cand, "hp", 1)
    le1 = d.enc_leaf_ent(cand, "e1", eh); le2 = d.enc_leaf_ent(cand, "e1", d.node_address(lc))
    rootd = d.enc_root(cand, {0: d.node_address(le1), 1: d.node_address(le2)}, d.enc_scalars(3, 0, 0))
    dbuf = _container(rootd, [empty, lc, le1, le2])
    _k1, c1 = _raised(lambda: C.reconstruct(dbuf, cand))
    _k2, c2 = _raised(lambda: C.reconstruct(dbuf, cand, _p6=False))
    row("RH-T3", "PASS" if (c1 == "WALK_MISROUTE" and c2 == "DUP_KEY") else "FAIL",
        "(c) duplicate entity key -> WALK_MISROUTE (walk) / DUP_KEY (backstop)", "walk=%s backstop=%s" % (c1, c2))

    # (d) two distinct encodings sharing one address -> CONTENT_ADDRESS_COLLISION: unconstructable under A-h
    row("RH-T3", "N.A.", "(d) one address, two encodings -> CONTENT_ADDRESS_COLLISION", "code path present; unconstructable without breaking SHA-256 (S-8)")

    # (e) uniqueness: exactly one canonical serialization per state (any reorder of a valid tree is rejected)
    buf = C.serialize_state(st, cand)
    _rh2, order, amap = C.parse_collection(buf, cand)
    if len(order) >= 2:
        swapped = list(order); swapped[0], swapped[1] = swapped[1], swapped[0]
        alt = d.DOM("skuld-state-0") + d.u16(d.VERSION) + d.raw32(_rh2) + d.u64(len(order)) + b"".join(amap[a]["_encoding"] for a in swapped)
        _k, code = _raised(lambda: C.reconstruct(alt, cand))
        row("RH-T3", "PASS" if code == "NODE_ORDER" else "FAIL", "(e) a reordered valid tree -> NODE_ORDER (one canonical form)", "outcome=%s" % code)
    else:
        row("RH-T3", "N.A.", "(e) too few nodes to reorder", "node_count=%d" % len(order))


# =====================================================================================================================
# RH-T4 — worst-case work: a MEASUREMENT (OBSERVED), not a pass/fail (matrix G2/G3/G6)
# =====================================================================================================================
def rh_t4():
    class CountingHasher:
        def __init__(self, base):
            self.base = base
            self.calls = 0

        def __call__(self, kb):
            self.calls += 1
            return self.base(kb)

    # wide ROOT: 20 entities on distinct ROOT slots (injected chunk(0) = i)
    def mkH(i):
        return (i & 0x1F) << 251
    ents = {"e%02d" % i: {} for i in range(20)}
    kh = d.InjectedKeyHasher({_ek("e%02d" % i): mkH(i) for i in range(20)})
    st = {"entities": ents, "alloc": 21, "rng": {"seed": 0, "counter": 0}}
    buf = C.serialize_state(st, "A", keyhasher=kh)
    _rh, order, _am = C.parse_collection(buf, "A")
    ch = CountingHasher(kh)
    C.reconstruct(buf, "A", keyhasher=ch)
    row("RH-T4", "OBSERVED", "wide ROOT (20 entities)", "len=%dB nodes=%d keyhash_calls=%d" % (len(buf), len(order), ch.calls))

    # deep single-path bucket: 2 fully-colliding entities -> ~52-level chain + terminal bucket
    _stc, bufc, kh_coll, _bad = B.colliding_tree("A")
    _rh, orderc, _am = C.parse_collection(bufc, "A")
    chc = CountingHasher(kh_coll)
    C.reconstruct(bufc, "A", keyhasher=chc)
    row("RH-T4", "OBSERVED", "deep single-path full-collision bucket", "len=%dB nodes=%d keyhash_calls=%d (branches 1..51 + bucket)" % (len(bufc), len(orderc), chc.calls))

    # shared DAG: 8 entities with identical component map -> one shared LEAF_COMP
    shared = {"s%d" % i: {"hp": 1} for i in range(8)}
    sts = {"entities": shared, "alloc": 9, "rng": {"seed": 0, "counter": 0}}
    bufs = C.serialize_state(sts, "A")
    _rh, orders, ams = C.parse_collection(bufs, "A")
    ncomp = sum(1 for a in orders if d.decode_node(ams[a]["_encoding"], "A")["type"] == "LEAF_COMP")
    row("RH-T4", "OBSERVED", "shared component DAG (8 entities, one hp=1)", "len=%dB nodes=%d shared_LEAF_COMP=%d (not re-stored per parent)" % (len(bufs), len(orders), ncomp))


# =====================================================================================================================
# RH-T5 — checkpoint trust as SEPARATE predicates; no global-agreement inference (matrix §7, G5, D4-2/D8)
# =====================================================================================================================
def _ledger(cand):
    events = [[("create", "e1"), ("set", "e1", "hp", 10)], [("effect", "log", "a")], [("create", "e2"), ("effect", "x", "1")]]
    state = ecs.genesis(); prev = None; recs = []; log_len = 0
    for i, ev in enumerate(events):
        ns, effects = R.replay_event(state, ev)
        ec = R.ecs_state_commitment(ecs.digest(ns)); rh, _ = C.build_state(ns, cand); sc = R.structural_state_commitment(rh)
        rec = {"seq": i + 1, "prev_hash": prev, "parent_hash": prev, "event": ev,
               "base_effect_index": log_len, "effects": effects, "ecs_commit": ec, "struct_commit": sc}
        rec["_commit"] = R.record_commitment(rec, cand, ec, sc); recs.append(rec); prev = rec["_commit"]; log_len += len(effects); state = ns
    return recs, R.verify_ledger(recs, cand)


def _checkpoint(res):
    head = res["per_record"][-1]
    return {"version": 0, "head_seq": head["seq"], "head_hash": head["commit"], "ecs_commit": head["ecs_commit"],
            "struct_commit": head["struct_commit"], "effects_range_root": bytes(32), "range_start": 0,
            "range_count": res["E_boundary"], "history_anchor": res["per_record"][0]["commit"],
            "boundary_seq": head["seq"], "boundary_hash": head["commit"]}


def rh_t5():
    _recs, res = _ledger("A")
    gen = res["per_record"][0]["commit"]
    v = K.verify_checkpoint(_checkpoint(res), res, trusted_ref=(1, gen))
    # each predicate is reported apart; none collapsed
    sep = all(k in v for k in ("digest", "range_identity", "head_eq_boundary", "anchor_identity", "anchor_reachability", "anchor_trust", "effects_range_root"))
    row("RH-T5", "PASS" if sep and v["digest"][0] == "PASS" and v["range_identity"][0] == "PASS" else "FAIL",
        "digest / range / head / anchor reported as SEPARATE predicates", "verdicts=%s" % {k: x[0] for k, x in v.items()})
    row("RH-T5", "BLOCKED" if v["effects_range_root"][0] == "BLOCKED" else "FAIL", "effects_range_root stays BLOCKED (D4-2)", v["effects_range_root"][1][:48])
    # non-genesis trust stays BLOCKED (D8) even though identity/reachability PASS
    anchor = next(p for p in res["per_record"] if p["seq"] == 2)
    cp2 = _checkpoint(res); cp2["history_anchor"] = anchor["commit"]
    v2 = K.verify_checkpoint(cp2, res, trusted_ref=(2, anchor["commit"]))
    ok = v2["anchor_identity"][0] == "PASS" and v2["anchor_reachability"][0] == "PASS" and v2["anchor_trust"][0] == "BLOCKED"
    row("RH-T5", "BLOCKED" if ok else "FAIL", "non-genesis anchor: identity/reachability PASS, trust BLOCKED (D8)", "trust=%s" % v2["anchor_trust"][0])
    # two valid checkpoints at the SAME boundary with DIFFERENT anchors: each validates locally; NO global-agreement
    # function exists (the oracle exposes no cross-checkpoint consistency inference). This is a structural absence.
    cp_g = _checkpoint(res)
    dig_g = K.checkpoint_digest(cp_g); dig_ng = K.checkpoint_digest(cp2)
    both_local = (v["digest"][0] == "PASS" and v2["digest"][0] == "PASS" and dig_g != dig_ng)
    has_global = any("agree" in n.lower() or "consisten" in n.lower() or "global" in n.lower() for n in dir(K))
    row("RH-T5", "PASS" if (both_local and not has_global) else "FAIL",
        "two local-valid checkpoints at one boundary -> no global-agreement inference", "distinct digests; no cross-checkpoint function in checkpoints.py")


def main():
    for fn in (rh_t1, rh_t2, rh_t3, rh_t4, rh_t5):
        print("-" * 100)
        fn()
    print("=" * 100)
    fails = [r for r in ROWS if r[1] == "FAIL"]
    counts = {}
    for _id, v, _l, _d in ROWS:
        counts[v] = counts.get(v, 0) + 1
    print("RH-T PROBE TOTALS: " + "  ".join("%s=%d" % (k, counts[k]) for k in sorted(counts)))
    print("RED-HARDENING PROBES: NO CONFIRMED NEW DEFECT (no FAIL); no S-9 proposed" if not fails
          else "RED-HARDENING PROBES: %d FAIL -> escalate as proposed S-9+ for owner review" % len(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
