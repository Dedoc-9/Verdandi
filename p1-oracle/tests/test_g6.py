"""G6 reproducibility + isolation + resource bounds (3B) + P1V-constants.

- determinism: identical inputs -> identical bytes/commitments across repeated runs
- the frozen ecs.py is byte-identical (sha256 == 3d568d22...)
- write isolation: the oracle package opens no file for writing and never touches ecs.py
- reduced-limit seam (3B): boundary behaviour at a test-only limit, rejection on the length prefix before buffering
- P1V-constants: the normative v0 bounds hold by value, with no reduced limit active
"""
import hashlib
import os

from oracle import decoder as d
from oracle import canonicality as C
from oracle import records as R
from oracle.frozen import ecs
from .harness import Cases, reject

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # p1-oracle/
_ORACLE_DIR = os.path.join(_HERE, "oracle")
FROZEN_ECS_SHA = "3d568d22d812ae2321b03b7450d09109c8ff20e3308b5f9cd2a5e2fde9eb1c0b"


def run():
    c = Cases()

    # determinism: same serialization and commitments across repeated runs
    def determinism():
        st = {"entities": {"e1": {"hp": 3, "name": "x"}, "e2": {"k": -7}}, "alloc": 4, "rng": {"seed": 5, "counter": 2}}
        a = C.serialize_state(st, "A")
        b = C.serialize_state(st, "A")
        if a != b:
            raise AssertionError("serialization not reproducible")
        ev = [[("create", "e1"), ("effect", "k", "p")]]
        r1 = _ledger_commits(ev, "A")
        r2 = _ledger_commits(ev, "A")
        if r1 != r2:
            raise AssertionError("ledger commitments not reproducible")
    c.ok("G6 determinism: identical bytes/commitments across runs", determinism)

    # frozen ecs.py byte-identical
    def frozen_hash():
        p = os.path.join(_ORACLE_DIR, "frozen", "ecs.py")
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if h != FROZEN_ECS_SHA:
            raise AssertionError("frozen ecs.py sha256 %s != %s" % (h, FROZEN_ECS_SHA))
    c.ok("G6 frozen ecs.py sha256 == 3d568d22... (byte-identical)", frozen_hash)

    # write isolation: no oracle source opens a file for writing / deletes
    def write_isolation():
        bad = []
        for fn in os.listdir(_ORACLE_DIR):
            if not fn.endswith(".py"):
                continue
            src = open(os.path.join(_ORACLE_DIR, fn), "r", encoding="utf-8").read()
            for needle in ('open(', 'os.remove', 'os.unlink', 'shutil.', 'Path(', '.write_text', '.write_bytes'):
                if needle == 'open(':
                    # allow read-only opens? the oracle should not open files at all
                    if 'open(' in src:
                        bad.append("%s: open(" % fn)
                elif needle in src:
                    bad.append("%s: %s" % (fn, needle))
        if bad:
            raise AssertionError("oracle sources perform I/O: %r" % bad)
    c.ok("G6 write isolation: oracle package performs no file I/O", write_isolation)

    # reduced-limit seam (3B): accept at the limit, reject one past, on the length prefix (before buffering)
    def reduced_limit_lp():
        lim8 = d.Limits(max_len=8)
        ok8 = bytes([d.VTYPE_STR]) + d.u64(8) + b"12345678"           # body length 8 == limit -> accept
        if d.decode_value(d.Reader(ok8, lim8)) != "12345678":
            raise AssertionError("length-at-limit not accepted")
        past = bytes([d.VTYPE_STR]) + d.u64(9) + b"abc"               # declared 9 > 8; only 3 bytes present
        e = reject(lambda: d.decode_value(d.Reader(past, lim8)), code="LP_TOO_LONG")
        # rejection fired on the length prefix, NOT on truncation of the body
        if "TRUNCATED" in str(e):
            raise AssertionError("rejected on truncation, not the length prefix")
        return "reduced-limit MAX_LEN_TEST=8; accept at 8, reject at 9 on the prefix"
    c.ok("P1V-bounds reduced-limit lp (3B): at-limit accept, one-past reject on prefix", reduced_limit_lp)

    def reduced_limit_nodes():
        st = {"entities": {"e1": {"hp": 1, "name": "x"}}, "alloc": 2, "rng": {"seed": 0, "counter": 0}}
        buf = C.serialize_state(st, "A")
        reject(lambda: C.parse_collection(buf, "A", d.Limits(max_nodes=1)), code="MAX_NODES")
        return "reduced MAX_NODES_TEST=1 rejects a >1-node collection"
    c.ok("P1V-bounds reduced-limit node_count (3B): over-limit collection rejected", reduced_limit_nodes)

    # P1V-constants: normative v0 bounds by value, no reduced limit active
    def constants():
        checks = {"MAX_LEN": (d.MAX_LEN, 2**32 - 1), "MAX_NODES": (d.MAX_NODES, 2**32 - 1),
                  "MAX_TOTAL": (d.MAX_TOTAL, 2**40), "MAX_HASH_CHUNKS": (d.MAX_HASH_CHUNKS, 52),
                  "VERSION": (d.VERSION, 0)}
        for name, (got, want) in checks.items():
            if got != want:
                raise AssertionError("%s == %d, expected %d" % (name, got, want))
    c.ok("P1V-constants: MAX_LEN/MAX_NODES/MAX_TOTAL/MAX_HASH_CHUNKS by value", constants)

    return c.done()


def _ledger_commits(events, cand):
    import copy
    state = ecs.genesis()
    prev = None
    out = []
    log_len = 0
    for i, ev in enumerate(events):
        new_state, effects = R.replay_event(state, ev)
        ec = R.ecs_state_commitment(ecs.digest(new_state))
        rh, _ = C.build_state(new_state, cand)
        sc = R.structural_state_commitment(rh)
        rec = {"seq": i + 1, "prev_hash": prev, "parent_hash": prev, "event": ev,
               "base_effect_index": log_len, "effects": effects, "ecs_commit": ec, "struct_commit": sc}
        commit = R.record_commitment(rec, cand, ec, sc)
        out.append(commit.hex())
        prev = commit
        log_len += len(effects)
        state = new_state
    return out
