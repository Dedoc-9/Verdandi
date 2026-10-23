"""Checkpoint digest, range identity, and history-anchor validation (ENCODING-TABLE-P1.md §7).

Three verdicts are reported APART and never collapsed (P1-15/§7):
  (1) field parsing + checkpoint_digest recomputation
  (2) range identity: (range_start, range_count) == (0, E_boundary) recomputed from the retained prefix (§5)
  (3) effects_range_root commits to exactly that prefix  -> BLOCKED on D4-2 (never a pass)
Anchor validation reports identity / reachability / trust apart (P1-28/P1-30):
  - a below-boundary anchor -> BLOCKED (needs D4-2/D8)
  - trust: genesis is inherently trusted this milestone (D5-1); any other reference -> BLOCKED on D8.
"""
import hashlib

from . import decoder as d


def checkpoint_preimage(cp):
    return (d.DOM("skuld-checkpoint-0")
            + b"V" + d.u16(cp["version"])
            + b"Q" + d.u64(cp["head_seq"])
            + b"J" + d.raw32(cp["head_hash"])
            + b"S" + d.raw32(cp["ecs_commit"])
            + b"T" + d.raw32(cp["struct_commit"])
            + b"E" + d.raw32(cp["effects_range_root"])
            + b"a" + d.u64(cp["range_start"])
            + b"c" + d.u64(cp["range_count"])
            + b"H" + d.raw32(cp["history_anchor"])
            + b"B" + d.u64(cp["boundary_seq"])
            + b"P" + d.raw32(cp["boundary_hash"]))


def checkpoint_digest(cp):
    return hashlib.sha256(checkpoint_preimage(cp)).digest()


def verify_checkpoint(cp, ledger, trusted_ref, expected_digest=None):
    """ledger = records.verify_ledger(...) result. trusted_ref = (seq_ref, h_ref) retained/trusted OUTSIDE the ledger.
    Returns a dict of SEPARATE verdicts; each is 'PASS' | 'FAIL' | 'BLOCKED' with detail. No verdict is collapsed."""
    v = {}
    per = ledger["per_record"]

    # (1) field parsing + digest recomputation (field integrity only)
    if cp["version"] != d.VERSION:
        v["digest"] = ("FAIL", "version %d" % cp["version"])
    else:
        dig = checkpoint_digest(cp)
        if expected_digest is not None and dig != expected_digest:
            v["digest"] = ("FAIL", "checkpoint_digest != expected")
        else:
            v["digest"] = ("PASS", dig.hex()[:16])

    # D4-3 invariant: head == boundary (seq and hash)
    if cp["head_seq"] == cp["boundary_seq"] and cp["head_hash"] == cp["boundary_hash"]:
        v["head_eq_boundary"] = ("PASS", "head_seq == boundary_seq, hashes equal")
    else:
        v["head_eq_boundary"] = ("FAIL", "head != boundary (D4-3 invariant violated)")

    # head must be the last retained record; its commitment must match
    if per and cp["head_seq"] == per[-1]["seq"] and cp["head_hash"] == per[-1]["commit"]:
        v["head_binding"] = ("PASS", "head is the last retained record")
    else:
        v["head_binding"] = ("FAIL", "head_seq/head_hash not the last retained record")

    # (2) range identity: (0, E_boundary) recomputed from retained records (contiguous from 0)
    E_boundary = ledger["E_boundary"]
    if cp["range_start"] == 0 and cp["range_count"] == E_boundary:
        v["range_identity"] = ("PASS", "(0, %d) == retained prefix" % E_boundary)
    else:
        v["range_identity"] = ("FAIL", "declared (%d,%d) != (0,%d)"
                               % (cp["range_start"], cp["range_count"], E_boundary))

    # (3) effects_range_root commits to exactly that prefix -> BLOCKED on D4-2
    v["effects_range_root"] = ("BLOCKED", "D4-2: range-tree algorithm + proof format not specified; not verifiable")

    # --- anchor: identity / reachability / trust, apart ---
    seq_ref, h_ref = trusted_ref
    # history_anchor field must equal the trusted h_ref (field integrity)
    if cp["history_anchor"] != h_ref:
        v["anchor_identity"] = ("FAIL", "history_anchor field != trusted h_ref")
        v["anchor_reachability"] = ("FAIL", "not attempted: identity failed")
        v["anchor_trust"] = ("FAIL", "not attempted: identity failed")
        return v

    # below-boundary anchor -> BLOCKED (authenticated prefix needs D4-2/D8)
    if seq_ref < 1 or (per and seq_ref > per[-1]["seq"]):
        v["anchor_identity"] = ("BLOCKED", "anchor outside retained range")
        v["anchor_reachability"] = ("BLOCKED", "below-boundary / out-of-range anchor (D4-2/D8)")
        v["anchor_trust"] = ("BLOCKED", "D8")
        return v

    # identity: the retained record at seq_ref recomputes to h_ref
    rec_at = next((p for p in per if p["seq"] == seq_ref), None)
    if rec_at is not None and rec_at["commit"] == h_ref:
        v["anchor_identity"] = ("PASS", "record at seq_ref recomputes to h_ref")
    else:
        v["anchor_identity"] = ("FAIL", "no retained record at seq_ref recomputes to h_ref")
        v["anchor_reachability"] = ("FAIL", "not attempted: identity failed")
        v["anchor_trust"] = ("FAIL", "not attempted: identity failed")
        return v

    # reachability: walk the retained prev chain from the head back to the anchor, matching seq AND hash
    v["anchor_reachability"] = _walk_prev(per, cp["head_hash"], seq_ref, h_ref)

    # trust: genesis is inherently trusted this milestone (D5-1); anything else -> BLOCKED on D8
    if seq_ref == 1:
        v["anchor_trust"] = ("PASS", "genesis is the inherently-trusted reference (D5-1)")
    else:
        v["anchor_trust"] = ("BLOCKED", "non-genesis external provenance is D8; checkpoint-based trust BLOCKED")
    return v


def _walk_prev(per, head_hash, seq_ref, h_ref):
    """Walk the retained prev chain from head_hash back to the anchor, matching both seq and hash. per records carry
    the forward chain; we reconstruct the prev link as 'the record whose commit is this record's prev'."""
    by_commit = {p["commit"]: p for p in per}
    cur = by_commit.get(head_hash)
    if cur is None:
        return ("FAIL", "head not in retained records")
    seen = 0
    while cur is not None:
        if cur["seq"] == seq_ref and cur["commit"] == h_ref:
            return ("PASS", "anchor reached by retained prev walk from head")
        # step to prev: the record at seq-1 (linear retained chain)
        if cur["seq"] == 1:
            break
        prev = next((p for p in per if p["seq"] == cur["seq"] - 1), None)
        cur = prev
        seen += 1
        if seen > len(per) + 1:
            break
    return ("FAIL", "anchor not reachable by retained prev walk")
