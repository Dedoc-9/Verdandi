"""G5 checkpoint + anchor, run for BOTH candidates (A and B). Digest, range identity (0,E_boundary), head==boundary
(D4-3), the three anchor verdicts; BLOCKED verdicts (effects_range_root on D4-2, below-boundary anchor, non-genesis
trust on D8) are kept distinct from PASS. The checkpoint binds the candidate's structural_state_commitment, so A and B
checkpoints differ (checked)."""
from oracle import canonicality as C
from oracle import records as R
from oracle import checkpoints as K
from oracle.frozen import ecs
from .harness import Cases


def _ledger(cand):
    events = [[("create", "e1"), ("set", "e1", "hp", 10)], [("effect", "log", "a")],
              [("create", "e2"), ("effect", "x", "1")]]
    state = ecs.genesis()
    prev = None
    recs = []
    log_len = 0
    for i, ev in enumerate(events):
        new_state, effects = R.replay_event(state, ev)
        ec = R.ecs_state_commitment(ecs.digest(new_state))
        rh, _ = C.build_state(new_state, cand)
        sc = R.structural_state_commitment(rh)
        rec = {"seq": i + 1, "prev_hash": prev, "parent_hash": prev, "event": ev,
               "base_effect_index": log_len, "effects": effects, "ecs_commit": ec, "struct_commit": sc}
        rec["_commit"] = R.record_commitment(rec, cand, ec, sc)
        recs.append(rec)
        prev = rec["_commit"]
        log_len += len(effects)
        state = new_state
    return recs, R.verify_ledger(recs, cand)


def _checkpoint(res):
    head = res["per_record"][-1]
    return {"version": 0, "head_seq": head["seq"], "head_hash": head["commit"],
            "ecs_commit": head["ecs_commit"], "struct_commit": head["struct_commit"],
            "effects_range_root": bytes(32), "range_start": 0, "range_count": res["E_boundary"],
            "history_anchor": res["per_record"][0]["commit"],
            "boundary_seq": head["seq"], "boundary_hash": head["commit"]}


def run():
    c = Cases()

    # A and B checkpoints differ (candidate-dependent struct commit), ecs identity matches
    def ab_distinct():
        _ra, resa = _ledger("A")
        _rb, resb = _ledger("B")
        if K.checkpoint_digest(_checkpoint(resa)) == K.checkpoint_digest(_checkpoint(resb)):
            raise AssertionError("A and B checkpoint digests coincide (B path not exercised)")
    c.ok("G5 Candidate A/B checkpoints differ (B path executed, not inferred)", ab_distinct)

    for cand in ("A", "B"):
        recs, res = _ledger(cand)
        gen = res["per_record"][0]["commit"]

        def valid(cand=cand, res=res, gen=gen):
            v = K.verify_checkpoint(_checkpoint(res), res, trusted_ref=(1, gen))
            want = {"digest": "PASS", "head_eq_boundary": "PASS", "head_binding": "PASS",
                    "range_identity": "PASS", "effects_range_root": "BLOCKED",
                    "anchor_identity": "PASS", "anchor_reachability": "PASS", "anchor_trust": "PASS"}
            for k, exp in want.items():
                if v[k][0] != exp:
                    raise AssertionError("%s: expected %s got %s (%s)" % (k, exp, v[k][0], v[k][1]))
        c.ok("G5 valid checkpoint: digest/range/head/anchor PASS; effects-root BLOCKED [%s]" % cand, valid)

        def range_bad(cand=cand, res=res, gen=gen):
            cp = _checkpoint(res)
            cp["range_count"] += 1
            if K.verify_checkpoint(cp, res, trusted_ref=(1, gen))["range_identity"][0] != "FAIL":
                raise AssertionError("range mismatch not FAIL")
        c.ok("G5 wrong range_count -> range_identity FAIL [%s]" % cand, range_bad)

        def head_bad(cand=cand, res=res, gen=gen):
            cp = _checkpoint(res)
            cp["boundary_seq"] -= 1
            if K.verify_checkpoint(cp, res, trusted_ref=(1, gen))["head_eq_boundary"][0] != "FAIL":
                raise AssertionError("head!=boundary not FAIL")
        c.ok("G5 head != boundary -> FAIL (D4-3) [%s]" % cand, head_bad)

        def digest_bad(cand=cand, res=res, gen=gen):
            cp = _checkpoint(res)
            good = K.checkpoint_digest(cp)
            cp2 = dict(cp)
            cp2["range_count"] += 5
            if K.verify_checkpoint(cp2, res, trusted_ref=(1, gen), expected_digest=good)["digest"][0] != "FAIL":
                raise AssertionError("tampered digest not FAIL")
        c.ok("G5 tampered field vs expected digest -> digest FAIL [%s]" % cand, digest_bad)

        def nongenesis(cand=cand, res=res):
            anchor = next(p for p in res["per_record"] if p["seq"] == 2)
            cp = _checkpoint(res)
            cp["history_anchor"] = anchor["commit"]
            v = K.verify_checkpoint(cp, res, trusted_ref=(2, anchor["commit"]))
            if v["anchor_identity"][0] != "PASS" or v["anchor_reachability"][0] != "PASS":
                raise AssertionError("non-genesis identity/reachability should PASS")
            if v["anchor_trust"][0] != "BLOCKED":
                raise AssertionError("non-genesis trust must be BLOCKED (D8)")
        c.ok("G5 non-genesis anchor: identity/reachability PASS, trust BLOCKED (D8) [%s]" % cand, nongenesis)

        def out_of_range(cand=cand, res=res, gen=gen):
            cp = _checkpoint(res)
            v = K.verify_checkpoint(cp, res, trusted_ref=(res["per_record"][-1]["seq"] + 1, gen))
            if v["anchor_reachability"][0] != "BLOCKED":
                raise AssertionError("out-of-range anchor must be BLOCKED")
        c.ok("G5 out-of-range (below-boundary) anchor -> BLOCKED [%s]" % cand, out_of_range)

    c.blocked("G5 effects_range_root verification (both candidates)",
              "D4-2: range-tree algorithm + proof format not specified")
    return c.done()
