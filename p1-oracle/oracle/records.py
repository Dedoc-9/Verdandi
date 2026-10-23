"""Records, effects, commitments and Tier-3 semantic replay (ENCODING-TABLE-P1.md §5, §6).

Tier-3 is the SEMANTIC oracle: it re-derives effects and state by replaying each event through the FROZEN ECS
(ecs._apply_ops on a deep-copied scratch state), never a reimplementation, and checks the record's declared effects
and both state commitments against that. A well-formed record is not a correct one.
"""
import copy
import hashlib

from . import decoder as d
from . import canonicality as C
from .frozen import ecs


# --- commitments (§6) -------------------------------------------------------------------------------------------------
def ecs_state_commitment(ecs_digest_hex):
    return hashlib.sha256(d.DOM("skuld-state-commit-0") + d.raw32(bytes.fromhex(ecs_digest_hex))).digest()


def structural_state_commitment(root_hash):
    return hashlib.sha256(d.DOM("skuld-struct-commit-0") + d.raw32(root_hash)).digest()


# --- effect leaves/nodes (§5); the range-tree construction/proof is D4-2-deferred (BLOCKED) ---------------------------
def eff_leaf(effect_index, commit_seq, kind, payload):
    _check_index(effect_index, "effect_index")
    _check_index(commit_seq, "commit_seq")
    return (d.DOM("skuld-eff-leaf-0") + d.u64(effect_index) + d.u64(commit_seq)
            + d.encode_value(kind) + d.encode_value(payload))


def eff_node(left, right):
    return d.DOM("skuld-eff-node-0") + d.raw32(left) + d.raw32(right)


def eff_empty_range():
    return d.DOM("skuld-eff-emptyrange-0") + d.u16(d.VERSION)


# --- index convention (§5): indices in [0, 2^64-2]; exclusive sums <= 2^64-1 ------------------------------------------
def _check_index(n, what):
    if not (0 <= n <= d.U64_MAX - 1):
        raise d.OracleError(d.MALFORMED, "INDEX_RESERVED", "%s=%d (2^64-1 is reserved)" % (what, n))


def _check_exclusive_sum(a, b, what):
    if a + b > d.U64_MAX:
        raise d.OracleError(d.MALFORMED, "INDEX_OVERFLOW", "%s sum %d > 2^64-1" % (what, a + b))
    return a + b


# --- record preimage (§6) ---------------------------------------------------------------------------------------------
def _link(h):
    if h is None:
        return b"\x00"
    return b"\x01" + d.raw32(h)


def encode_event(ops):
    out = d.u64(len(ops))
    for op in ops:
        name = op[0]
        args = op[1:]
        out += d.lp(name.encode("utf-8")) + d.u64(len(args))
        for a in args:
            out += d.encode_value(a)
    return out


def encode_effects(base_effect_index, effects):
    _check_index(base_effect_index, "base_effect_index")
    _check_exclusive_sum(base_effect_index, len(effects), "base_effect_index+count")
    out = d.u64(base_effect_index) + d.u64(len(effects))
    for (kind, payload) in effects:
        out += d.encode_value(kind) + d.encode_value(payload)
    return out


def record_preimage(rec, cand, ecs_commit, struct_commit):
    """rec: dict{seq, prev_hash, parent_hash, event(ops), base_effect_index, effects[(kind,payload)]}."""
    if rec["seq"] < 1:
        raise d.OracleError(d.MALFORMED, "SEQ_ZERO", "seq must be >= 1")
    return (d.DOM("skuld-record-0") + d.u16(d.VERSION)
            + b"Q" + d.u64(rec["seq"])
            + b"V" + _link(rec["prev_hash"])
            + b"W" + _link(rec["parent_hash"])
            + b"N" + encode_event(rec["event"])
            + b"F" + encode_effects(rec["base_effect_index"], rec["effects"])
            + b"S" + d.raw32(ecs_commit)
            + b"T" + d.raw32(struct_commit))


def record_commitment(rec, cand, ecs_commit, struct_commit):
    return hashlib.sha256(record_preimage(rec, cand, ecs_commit, struct_commit)).digest()


# --- Tier-3 replay ----------------------------------------------------------------------------------------------------
def replay_event(state, ops):
    """Apply ops to a DEEP COPY of state via the frozen ecs._apply_ops. Returns (new_state, effects[(kind,payload)]).
    An unknown op, wrong arity, or a raising op (TxnAbort) -> SEMANTIC rejection, whole event, scratch absorbs partial."""
    scratch = copy.deepcopy(state)
    try:
        op_tuples = [tuple(op) for op in ops]
        _inverse, effects = ecs._apply_ops(scratch, op_tuples)
    except ecs.TxnAbort as e:
        raise d.OracleError(d.SEMANTIC, "REPLAY_ABORT", str(e))
    except (TypeError, ValueError, IndexError, KeyError) as e:
        raise d.OracleError(d.SEMANTIC, "REPLAY_ERROR", "%s: %s" % (type(e).__name__, e))
    return scratch, [(e["kind"], e["payload"]) for e in effects]


def verify_ledger(records, cand):
    """Independent full-audit oracle for a LINEAR ledger (parent == prev unless parentless-at-genesis).
    Folds from genesis via the frozen ECS, validates links + the effect_index assignment + both commitments per record.
    Returns {"ok": bool, "per_record": [...], "eff_log": [...], "E_boundary": int, "final_state": ...}."""
    state = ecs.genesis()
    prev_commit = None
    eff_log = []            # global forward-only log: list of (effect_index, commit_seq, kind, payload)
    per = []
    for i, rec in enumerate(records):
        seq = rec["seq"]
        # --- link validity (§6 truth table), independent of replay ---
        if seq < 1:
            raise d.OracleError(d.MALFORMED, "SEQ_ZERO", "seq %d" % seq)
        if seq != i + 1:
            raise d.OracleError(d.MALFORMED, "SEQ_ORDER", "seq %d at position %d" % (seq, i))
        if i == 0:
            if rec["prev_hash"] is not None:
                raise d.OracleError(d.MALFORMED, "GENESIS_PREV", "genesis must have 0x00 prev")
            if rec["parent_hash"] is not None:
                raise d.OracleError(d.MALFORMED, "GENESIS_PARENT", "genesis must have 0x00 parent")
        else:
            if rec["prev_hash"] != prev_commit:
                raise d.OracleError(d.MALFORMED, "PREV_LINK", "prev != preceding ledger head")
            # parent: 0x00 (world-parent genesis, legal) OR an earlier record's commitment
            if rec["parent_hash"] is not None and rec["parent_hash"] not in [p["commit"] for p in per]:
                raise d.OracleError(d.MALFORMED, "PARENT_LINK", "parent not an earlier record")

        # --- Tier-3 replay: effects + resulting state via frozen ECS ---
        base = len(eff_log)
        if rec["base_effect_index"] != base:
            raise d.OracleError(d.SEMANTIC, "BASE_INDEX", "declared %d != log length %d"
                                % (rec["base_effect_index"], base))
        new_state, effects = replay_event(state, rec["event"])
        if [(k, p) for (k, p) in effects] != list(rec["effects"]):
            raise d.OracleError(d.SEMANTIC, "EFFECTS_MISMATCH", "replayed effects != declared")
        for j, (k, p) in enumerate(effects):
            eff_log.append((base + j, seq, k, p))

        # --- commitments of the world this record produced (D4-1 both) ---
        ecs_dig = ecs.digest(new_state)
        root_hash, _coll = C.build_state(new_state, cand)
        ecs_commit = ecs_state_commitment(ecs_dig)
        struct_commit = structural_state_commitment(root_hash)
        if "ecs_commit" in rec and rec["ecs_commit"] != ecs_commit:
            raise d.OracleError(d.SEMANTIC, "ECS_COMMIT", "declared ecs_state_commitment != recomputed")
        if "struct_commit" in rec and rec["struct_commit"] != struct_commit:
            raise d.OracleError(d.SEMANTIC, "STRUCT_COMMIT", "declared structural_state_commitment != recomputed")

        commit = record_commitment(rec, cand, ecs_commit, struct_commit)
        per.append({"seq": seq, "commit": commit, "ecs_commit": ecs_commit, "struct_commit": struct_commit,
                    "base_effect_index": base, "count": len(effects), "ecs_digest": ecs_dig, "root_hash": root_hash})
        prev_commit = commit
        state = new_state

    E_boundary = len(eff_log)
    return {"ok": True, "per_record": per, "eff_log": eff_log, "E_boundary": E_boundary, "final_state": state}
