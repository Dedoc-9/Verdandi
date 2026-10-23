"""G4 record semantics, run for BOTH candidates (A and B) against independent expectations.

The record/effects/commitment/link byte grammar is candidate-independent (checked: preimage A == B for equal inputs);
the candidate-dependent part is structural_state_commitment, which wraps the candidate's structural_state_root. Running
the ledger under A and under B exercises each candidate's actual structural path, not an inference from shared literals.
"""
import hashlib

from oracle import decoder as d
from oracle import canonicality as C
from oracle import records as R
from oracle.frozen import ecs
from .harness import Cases, reject


def _make_ledger(events, cand):
    state = ecs.genesis()
    prev = None
    recs = []
    log_len = 0
    for i, ev in enumerate(events):
        new_state, effects = R.replay_event(state, ev)
        ec = R.ecs_state_commitment(ecs.digest(new_state))
        rh, _ = C.build_state(new_state, cand)
        sc = R.structural_state_commitment(rh)
        rec = {"seq": i + 1, "prev_hash": prev, "parent_hash": prev,
               "event": ev, "base_effect_index": log_len, "effects": effects,
               "ecs_commit": ec, "struct_commit": sc}
        rec["_commit"] = R.record_commitment(rec, cand, ec, sc)
        recs.append(rec)
        prev = rec["_commit"]
        log_len += len(effects)
        state = new_state
    return recs


def run():
    c = Cases()

    # candidate-independent: record preimage bytes == hand-calculated, and A == B for the same inputs
    def preimage_bytes():
        ec = bytes([0x11]) * 32
        sc = bytes([0x22]) * 32
        rec = {"seq": 1, "prev_hash": None, "parent_hash": None,
               "event": [("create", "e1")], "base_effect_index": 0, "effects": []}

        def u16(n): return n.to_bytes(2, "big")
        def u64(n): return n.to_bytes(8, "big")
        def lp(b): return u64(len(b)) + b
        def dom(s): return s.encode("ascii") + b"\x00"
        event = u64(1) + lp(b"create") + u64(1) + (bytes([0x02]) + lp(b"e1"))
        hand = (dom("skuld-record-0") + u16(0) + b"Q" + u64(1) + b"V" + b"\x00" + b"W" + b"\x00"
                + b"N" + event + b"F" + (u64(0) + u64(0)) + b"S" + ec + b"T" + sc)
        pa = R.record_preimage(rec, "A", ec, sc)
        pb = R.record_preimage(rec, "B", ec, sc)
        if pa != hand:
            raise AssertionError("record preimage != hand-calculated")
        if pa != pb:
            raise AssertionError("record preimage differs between candidates (should be candidate-independent)")
        if R.record_commitment(rec, "A", ec, sc) != hashlib.sha256(hand).digest():
            raise AssertionError("record_commitment != sha256(hand)")
    c.ok("G4 record preimage bytes == hand-calculated; candidate-independent (A==B)", preimage_bytes)

    # candidate-independent index convention
    def index_bounds():
        reject(lambda: R.eff_leaf(d.U64_MAX, 1, "k", "p"), code="INDEX_RESERVED")
        R.encode_effects(d.U64_MAX - 1, [("k", "p")])
        reject(lambda: R.encode_effects(d.U64_MAX, []), code="INDEX_RESERVED")
        reject(lambda: R.encode_effects(d.U64_MAX - 1, [("a", "b"), ("c", "e")]), code="INDEX_OVERFLOW")
    c.ok("G4 index convention: 2^64-1 reserved; exclusive sum <= 2^64-1", index_bounds)

    # the candidate-dependent path is actually exercised, not inferred: B's struct commit differs from A's
    def b_path_distinct():
        events = [[("create", "e1"), ("set", "e1", "hp", 10)]]
        ra = _make_ledger(events, "A")
        rb = _make_ledger(events, "B")
        if ra[0]["struct_commit"] == rb[0]["struct_commit"]:
            raise AssertionError("A and B structural_state_commitment coincide (B path not actually exercised)")
        if ra[0]["ecs_commit"] != rb[0]["ecs_commit"]:
            raise AssertionError("ecs_state_commitment should match across candidates (same ECS state)")
    c.ok("G4 Candidate B structural commit differs from A (B path executed, not inferred)", b_path_distinct)

    for cand in ("A", "B"):
        def ledger_accept(cand=cand):
            events = [[("create", "e1"), ("set", "e1", "hp", 10)], [("effect", "log", "a")],
                      [("effect", "x", "1"), ("effect", "y", "2"), ("set", "e1", "hp", 11)], [("rng",)]]
            res = R.verify_ledger(_make_ledger(events, cand), cand)
            want = [(0, 2, "log", "a"), (1, 3, "x", "1"), (2, 3, "y", "2")]
            if res["eff_log"] != want or res["E_boundary"] != 3:
                raise AssertionError("effect indexing wrong: %r / E=%d" % (res["eff_log"], res["E_boundary"]))
        c.ok("G4 valid ledger accepts; effect_index 0/1/multi [%s]" % cand, ledger_accept)

        def wrong_ecs(cand=cand):
            recs = _make_ledger([[("create", "e1")]], cand)
            recs[0]["ecs_commit"] = bytes(32)
            reject(lambda: R.verify_ledger(recs, cand), code="ECS_COMMIT", category=d.SEMANTIC)
        c.ok("G4 wrong ecs_state_commitment -> SEMANTIC [%s]" % cand, wrong_ecs)

        def wrong_struct(cand=cand):
            recs = _make_ledger([[("create", "e1")]], cand)
            recs[0]["struct_commit"] = bytes(32)
            reject(lambda: R.verify_ledger(recs, cand), code="STRUCT_COMMIT", category=d.SEMANTIC)
        c.ok("G4 wrong structural_state_commitment -> SEMANTIC [%s]" % cand, wrong_struct)

        def atomic(cand=cand):
            st = ecs.genesis()
            reject(lambda: R.replay_event(st, [("frobnicate", "x")]), category=d.SEMANTIC)
            if st != ecs.genesis():
                raise AssertionError("unknown op mutated scratch")
            before = ecs.canon(st)
            reject(lambda: R.replay_event(st, [("create", "e1"), ("set", "e1", "hp", 1), ("fail",)]), category=d.SEMANTIC)
            if ecs.canon(st) != before:
                raise AssertionError("partial apply leaked")
            reject(lambda: R.replay_event(st, [("set", "e1")]), category=d.SEMANTIC)
        c.ok("G4 unknown/fail-after-valid/wrong-arity -> SEMANTIC, atomic [%s]" % cand, atomic)

        def links(cand=cand):
            g = _make_ledger([[("create", "e1")]], cand)
            g[0]["prev_hash"] = bytes([0x01]) * 32
            reject(lambda: R.verify_ledger(g, cand), code="GENESIS_PREV")
            two = _make_ledger([[("create", "e1")], [("set", "e1", "hp", 1)]], cand)
            two[1]["prev_hash"] = bytes([0x09]) * 32
            reject(lambda: R.verify_ledger(two, cand), code="PREV_LINK")
            pl = _make_ledger([[("create", "e1")], [("create", "e2")]], cand)
            pl[1]["parent_hash"] = None                 # parentless non-genesis is legal
            if not R.verify_ledger(pl, cand)["ok"]:
                raise AssertionError("parentless non-genesis rejected")
        c.ok("G4 link truth table (genesis/prev/parentless) [%s]" % cand, links)

    return c.done()
