"""0260 (G-5): link and sequence validation (reported under G4). Each negative is isolated — constructed on the record
whose own check fires, with every other field valid — so the specific link/sequence error is reached, not masked by a
downstream failure. Both candidates. Accepting neighbours confirm specificity.

Architectural note (honest): the oracle models records as structured dicts (prev/parent = None|hash) + preimage
hashing; it has NO record byte-decoder, so an invalid LINK-*tag byte* (a byte other than 0x00/0x01) is not reachable
here. That case is left OPEN in the matrix rather than faked; it would need a record byte-parser (larger than G-5)."""
from oracle import canonicality as C
from oracle import records as R
from oracle.frozen import ecs
from .harness import Cases, reject

EV2 = [[("create", "e1")], [("create", "e2")]]
EV3 = [[("create", "e1")], [("create", "e2")], [("create", "e3")]]


def _ledger(events, cand):
    state = ecs.genesis()
    prev = None
    recs = []
    log = 0
    for i, ev in enumerate(events):
        ns, eff = R.replay_event(state, ev)
        ec = R.ecs_state_commitment(ecs.digest(ns))
        rh, _ = C.build_state(ns, cand)
        sc = R.structural_state_commitment(rh)
        rec = {"seq": i + 1, "prev_hash": prev, "parent_hash": prev, "event": ev,
               "base_effect_index": log, "effects": eff, "ecs_commit": ec, "struct_commit": sc}
        rec["_commit"] = R.record_commitment(rec, cand, ec, sc)
        recs.append(rec)
        prev = rec["_commit"]
        log += len(eff)
        state = ns
    return recs


def run():
    c = Cases()
    for cand in ("A", "B"):
        # --- sequence ---
        def seq_zero(cand=cand):
            r = _ledger(EV2, cand)
            r[0]["seq"] = 0
            reject(lambda: R.verify_ledger(r, cand), code="SEQ_ZERO")
        c.ok("G4 genesis seq=0 -> SEQ_ZERO [%s]" % cand, seq_zero)

        def seq_order(cand=cand):
            r = _ledger(EV2, cand)
            r[1]["seq"] = 5
            reject(lambda: R.verify_ledger(r, cand), code="SEQ_ORDER")
        c.ok("G4 seq out of order -> SEQ_ORDER [%s]" % cand, seq_order)

        # --- prev link ---
        def prev_unknown(cand=cand):
            r = _ledger(EV2, cand)
            r[1]["prev_hash"] = bytes([0xAB]) * 32
            reject(lambda: R.verify_ledger(r, cand), code="PREV_LINK")
        c.ok("G4 unknown prev -> PREV_LINK [%s]" % cand, prev_unknown)

        def prev_forward(cand=cand):
            r = _ledger(EV3, cand)
            r[1]["prev_hash"] = r[2]["_commit"]          # a later record's commit
            reject(lambda: R.verify_ledger(r, cand), code="PREV_LINK")
        c.ok("G4 forward prev -> PREV_LINK [%s]" % cand, prev_forward)

        # --- parent link (forward / self / unknown all reject as PARENT_LINK = 'not an earlier record') ---
        def parent_unknown(cand=cand):
            r = _ledger(EV2, cand)
            r[1]["parent_hash"] = bytes([0xCD]) * 32
            reject(lambda: R.verify_ledger(r, cand), code="PARENT_LINK")
        c.ok("G4 unknown parent -> PARENT_LINK [%s]" % cand, parent_unknown)

        def parent_forward(cand=cand):
            r = _ledger(EV3, cand)
            r[1]["parent_hash"] = r[2]["_commit"]        # forward (higher-seq) reference
            reject(lambda: R.verify_ledger(r, cand), code="PARENT_LINK")
        c.ok("G4 forward parent -> PARENT_LINK [%s]" % cand, parent_forward)

        def parent_self(cand=cand):
            r = _ledger(EV2, cand)
            r[1]["parent_hash"] = r[1]["_commit"]        # self-reference (last record, no downstream break)
            reject(lambda: R.verify_ledger(r, cand), code="PARENT_LINK")
        c.ok("G4 self parent -> PARENT_LINK [%s]" % cand, parent_self)

        # --- accepting neighbours ---
        def valid_linear(cand=cand):
            if not R.verify_ledger(_ledger(EV2, cand), cand)["ok"]:
                raise AssertionError("valid linear ledger rejected")
        c.ok("G4 valid linear ledger accepts (neighbour) [%s]" % cand, valid_linear)

        def parentless_last(cand=cand):
            r = _ledger(EV2, cand)
            r[1]["parent_hash"] = None                   # parentless non-genesis, last record -> legal
            if not R.verify_ledger(r, cand)["ok"]:
                raise AssertionError("parentless non-genesis (last) rejected")
        c.ok("G4 parentless non-genesis accepts (neighbour) [%s]" % cand, parentless_last)

        def parent_earlier(cand=cand):
            r = _ledger(EV3, cand)
            r[2]["parent_hash"] = r[0]["_commit"]        # earlier record, last position -> legal
            if not R.verify_ledger(r, cand)["ok"]:
                raise AssertionError("parent=earlier record rejected")
        c.ok("G4 parent = earlier record accepts (neighbour) [%s]" % cand, parent_earlier)

    return c.done()
