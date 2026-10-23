"""Validity-not-outcome check (the falsifier that CAN fail): plant a real defect in the oracle and confirm the
relevant gate turns RED. A green gate run proves nothing unless the gate would catch a real bug; this demonstrates it.

Run:  PYTHONHASHSEED=0 PYTHONUTF8=1 python p1-oracle/verify_plants.py
Exit 0 iff EVERY plant bites (makes >=1 FAIL in its gate). Patches are in-memory only; the package is never written.
"""
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from oracle import decoder as d          # noqa: E402
from oracle import canonicality as C     # noqa: E402
from oracle import records as R          # noqa: E402
from oracle import checkpoints as K      # noqa: E402
from tests import test_g1, test_g3, test_g4, test_g5, test_seams, test_buckets, test_struct, test_tier1  # noqa: E402


def _fails(rows):
    return sum(1 for _n, v, _d in rows if v == "FAIL")


def _plant(label, patch, unpatch, module):
    patch()
    try:
        f = _fails(module.run())
    finally:
        unpatch()
    print("%-46s planted -> FAIL=%d  %s" % (label, f, "BITES" if f > 0 else "INERT (BAD)"))
    return f > 0


def main():
    ok = True

    _orig_empty = d.enc_empty
    ok &= _plant("G1 corrupt EMPTY encoder",
                 lambda: setattr(d, "enc_empty", lambda cand: _orig_empty(cand) + b"\x99"),
                 lambda: setattr(d, "enc_empty", _orig_empty), test_g1)

    _orig_scalars = d._decode_scalars

    def _lax_scalars(r):
        out = {}
        for tag, key in ((b"A", "alloc"), (b"S", "seed"), (b"C", "counter")):
            r.expect(tag, "SCALARS_TAG")
            out[key] = d.decode_value(r)            # defect: no int-type gate (block D)
        return out
    ok &= _plant("G3 scalars accept string (block D off)",
                 lambda: setattr(d, "_decode_scalars", _lax_scalars),
                 lambda: setattr(d, "_decode_scalars", _orig_scalars), test_g3)

    _orig_replay = R.replay_event
    ok &= _plant("G4 replay swallows TxnAbort",
                 lambda: setattr(R, "replay_event", lambda s, ops: (copy.deepcopy(s), [])),
                 lambda: setattr(R, "replay_event", _orig_replay), test_g4)

    _orig_vc = K.verify_checkpoint

    def _lax_vc(cp, ledger, trusted_ref, expected_digest=None):
        v = _orig_vc(cp, ledger, trusted_ref, expected_digest)
        v["range_identity"] = ("PASS", "forced")    # defect: ignore range mismatch
        return v
    ok &= _plant("G5 range identity forced PASS",
                 lambda: setattr(K, "verify_checkpoint", _lax_vc),
                 lambda: setattr(K, "verify_checkpoint", _orig_vc), test_g5)

    _orig_recon = C.reconstruct

    def _lax_recon(buf, cand, keyhasher=d.prod_key_hasher, limits=d.PROD_LIMITS):
        return _orig_recon(buf, cand, keyhasher=d.prod_key_hasher, limits=limits)   # defect: ignore active hasher
    ok &= _plant("G2 reconstruct ignores active key-hasher",
                 lambda: setattr(C, "reconstruct", _lax_recon),
                 lambda: setattr(C, "reconstruct", _orig_recon), test_seams)

    _orig_cb = C._check_buckets
    ok &= _plant("G2 bucket-placement check disabled",
                 lambda: setattr(C, "_check_buckets", lambda *a, **k: None),
                 lambda: setattr(C, "_check_buckets", _orig_cb), test_buckets)

    # 0258: disable the Tier-1 distinct-children check -> the ROOT/BRANCH DUP_CHILD vectors must FAIL
    _orig_bmc = d._read_bitmap_children

    def _lax_bmc(r, level):
        bitmap = r.u32()
        children = []
        for slot in range(32):
            if bitmap & (1 << slot):
                children.append((slot, r.take(32)))
        return bitmap, children                        # defect: no distinct-children check
    ok &= _plant("G2 distinct-children check disabled",
                 lambda: setattr(d, "_read_bitmap_children", _lax_bmc),
                 lambda: setattr(d, "_read_bitmap_children", _orig_bmc), test_struct)

    # 0259: disable the minimal-int / surrogate guards -> the Tier-1 value negatives must FAIL
    _orig_dv = d.decode_value

    def _lax_dv(r):
        vt = r.u8()
        if vt == d.VTYPE_INT:
            sign = r.u8()
            mag = r.lp()
            return (int.from_bytes(mag, "big") if sign == 0x00 else -int.from_bytes(mag, "big"))  # no minimal/sign guard
        if vt == d.VTYPE_STR:
            return r.lp().decode("utf-8", "replace")        # no strict UTF-8 guard
        raise d.malformed("VTYPE", hex(vt))
    ok &= _plant("T1 value guards (minimal/sign/utf-8) disabled",
                 lambda: setattr(d, "decode_value", _lax_dv),
                 lambda: setattr(d, "decode_value", _orig_dv), test_tier1)

    print("ALL PLANTS BITE" if ok else "SOME PLANT INERT -- APPARATUS DOES NOT FULLY BITE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
