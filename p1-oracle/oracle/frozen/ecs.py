"""STATE-TRANSACTION-0 (scratch, design experiment): a transactional ECS with a double-buffered authoritative state, a
reversible change journal, exact rollback, deterministic replay, and a ledger-style baseline to compare against
(DESIGN.md). Pure standard library; run with PYTHONHASHSEED=0.

Authoritative state (canonical, digestible):
    {"entities": {eid: {component: value}}, "alloc": next_id_int, "rng": {"seed": int, "counter": int}}
Values are ints or strings only, so the canonical bytes are exact. External effects are kept in a separate log, never
in the digest and never reversed by reversing memory.

An op is one of:
    ("create", eid)                 allocate the next entity (eid is checked against the allocator)
    ("destroy", eid)                remove an entity (and all its components)
    ("set", eid, comp, value)       set a component
    ("remove", eid, comp)           remove a component
    ("rng", )                       advance the RNG counter (deterministic; its inverse restores it)
    ("effect", kind, payload)       an external effect: logged apart, no state change, not reversible by memory
    ("fail", )                      the self-test's injected failure: raises, to prove atomicity

A transaction is a list of ops. commit() computes the whole result and its inverse on a shadow buffer; if every op is
valid it swaps the shadow in and journals the inverse, else it aborts and the current buffer is byte-for-byte untouched.
"""
import copy
import hashlib
import json


class TxnAbort(Exception):
    pass


class Conflict(Exception):
    pass


def genesis():
    return {"entities": {}, "alloc": 1, "rng": {"seed": 0, "counter": 0}}


def canon(state):
    return json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def digest(state):
    return hashlib.sha256(canon(state)).hexdigest()


def footprint(ops):
    """The (eid, comp) cells, entities and resources a transaction touches — used to decide independence. 'alloc' and
    'rng' are shared cells; an effect touches no state cell."""
    f = set()
    for op in ops:
        k = op[0]
        if k == "create":
            f.add(("alloc",))
            f.add(("entity", op[1]))
        elif k == "destroy":
            f.add(("entity", op[1]))
        elif k == "set":
            f.add(("cell", op[1], op[2]))
        elif k == "remove":
            f.add(("cell", op[1], op[2]))
        elif k == "rng":
            f.add(("rng",))
    return f


def independent(a, b):
    return footprint(a).isdisjoint(footprint(b))


def _apply_ops(state, ops):
    """Apply ops to `state` (mutated in place) and return the inverse ops and the external effects. Raises TxnAbort
    before the first mutation that cannot be validated — but the caller always works on a shadow, so the authoritative
    buffer is never touched on abort. The inverse is built as we go, so it exactly undoes what was done."""
    inverse = []
    effects = []
    for op in ops:
        k = op[0]
        if k == "create":
            eid = op[1]
            want = "e%d" % state["alloc"]
            if eid != want:
                raise TxnAbort("create expected %s, got %s" % (want, eid))
            if eid in state["entities"]:
                raise TxnAbort("entity %s already exists" % eid)
            state["entities"][eid] = {}
            state["alloc"] += 1
            inverse.append(("_setalloc", state["alloc"] - 1))
            inverse.append(("_delentity", eid))
        elif k == "destroy":
            eid = op[1]
            if eid not in state["entities"]:
                raise TxnAbort("destroy missing entity %s" % eid)
            old = state["entities"].pop(eid)
            inverse.append(("_putentity", eid, old))
        elif k == "set":
            _, eid, comp, value = op
            if eid not in state["entities"]:
                raise TxnAbort("set on missing entity %s" % eid)
            if not isinstance(value, (int, str)) or isinstance(value, bool):
                raise TxnAbort("value for %s.%s is not an int or str" % (eid, comp))
            had = comp in state["entities"][eid]
            prev = state["entities"][eid].get(comp)
            state["entities"][eid][comp] = value
            inverse.append(("_setcell", eid, comp, prev) if had else ("_delcell", eid, comp))
        elif k == "remove":
            _, eid, comp = op
            if eid not in state["entities"] or comp not in state["entities"][eid]:
                raise TxnAbort("remove missing %s.%s" % (eid, comp))
            prev = state["entities"][eid].pop(comp)
            inverse.append(("_setcell", eid, comp, prev))
        elif k == "rng":
            state["rng"]["counter"] += 1
            inverse.append(("_setrng", state["rng"]["counter"] - 1))
        elif k == "effect":
            effects.append({"kind": op[1], "payload": op[2]})      # apart from the digest; not reversible by memory
        elif k == "fail":
            raise TxnAbort("injected failure")
        else:
            raise TxnAbort("unknown op %r" % (op,))
    return list(reversed(inverse)), effects


def _apply_inverse(state, inverse):
    for op in inverse:
        k = op[0]
        if k == "_setalloc":
            state["alloc"] = op[1]
        elif k == "_delentity":
            state["entities"].pop(op[1], None)
        elif k == "_putentity":
            state["entities"][op[1]] = op[2]
        elif k == "_setcell":
            state["entities"][op[1]][op[2]] = op[3]
        elif k == "_delcell":
            state["entities"][op[1]].pop(op[2], None)
        elif k == "_setrng":
            state["rng"]["counter"] = op[1]
        else:
            raise AssertionError("unknown inverse op %r" % (op,))


class Engine:
    """The authoritative state, double-buffered, with a reversible journal and a separate effect log."""

    def __init__(self):
        self.current = genesis()
        self.journal = []        # one {"id","inverse","footprint"} per committed transaction
        self.effects = []        # external effects, in commit order; apart from the digest
        self._next_txn = 1

    def commit(self, ops):
        """Apply a transaction atomically. Returns its id on commit; raises TxnAbort (the current buffer untouched) on
        any invalid op. The shadow is a deep copy, so a mid-transaction abort cannot leave partial state current."""
        shadow = copy.deepcopy(self.current)
        try:
            inverse, effects = _apply_ops(shadow, ops)
        except TxnAbort:
            raise                                    # self.current is untouched (we mutated only the shadow)
        self.current = shadow
        tid = self._next_txn
        self._next_txn += 1
        self.journal.append({"id": tid, "inverse": inverse, "footprint": sorted(map(list, footprint(ops)))})
        self.effects.extend({"txn": tid, **e} for e in effects)
        return tid

    def digest(self):
        return digest(self.current)

    def rollback(self, n=1):
        """Undo the last n committed transactions by applying their inverses in reverse; the journal shrinks by n. The
        work is O(sum of the deltas), not O(history). It does NOT compute a digest: producing a digest is a separate
        O(state) serialization (a real engine would keep it incrementally), so the caller asks for .digest() when it
        wants one and pays that cost explicitly. Returns the journal's new length."""
        if n > len(self.journal):
            raise ValueError("cannot roll back %d of %d transactions" % (n, len(self.journal)))
        for _ in range(n):
            entry = self.journal.pop()
            _apply_inverse(self.current, entry["inverse"])
        return len(self.journal)


def replay(commands):
    """Fold commit over a fresh engine; return the digest after each command (and the final engine)."""
    e = Engine()
    digs = []
    for ops in commands:
        e.commit(ops)
        digs.append(e.digest())
    return digs, e


def ledger_state(commands):
    """The ledger-style baseline: the authoritative state as the fold of every command from genesis, with no reverse
    journal. Rollback to k is ledger_state(commands[:k]) — replaying the history, which is what the benchmark compares
    against the journal's O(delta) rollback."""
    s = genesis()
    for ops in commands:
        inv, _eff = _apply_ops(s, ops)              # raises TxnAbort on an invalid command, as commit would
    return s


def ledger_digest_at(commands, k):
    s = genesis()
    for ops in commands[:k]:
        _apply_ops(s, ops)
    return digest(s)


# ------------------------------------------------------------------------------------------------ the self-test
def selftest():
    rows = []

    def row(name, ok, detail):
        rows.append(bool(ok))
        print("%s %s — %s" % ("PASS" if ok else "FAIL", name, detail))

    # 1. the digest is canonical: insertion order does not change it
    a = genesis(); a["entities"]["e1"] = {"hp": 3, "name": "x"}; a["alloc"] = 2
    b = genesis(); b["alloc"] = 2; b["entities"]["e1"] = {}; b["entities"]["e1"]["name"] = "x"; b["entities"]["e1"]["hp"] = 3
    row("canonical digest is insertion-order independent", digest(a) == digest(b), digest(a)[:16])

    # 2. a transaction modifying several components commits and changes the digest
    e = Engine()
    d0 = e.digest()
    e.commit([("create", "e1"), ("set", "e1", "hp", 10), ("set", "e1", "name", "orc"), ("rng",)])
    d1 = e.digest()
    row("a multi-component transaction commits and changes the digest", d0 != d1 and e.current["entities"]["e1"] ==
        {"hp": 10, "name": "orc"} and e.current["rng"]["counter"] == 1, "%s -> %s" % (d0[:12], d1[:12]))

    # 3. exact reversible delta: apply a transaction then its inverse restores the exact bytes
    before = canon(e.current)
    e.commit([("set", "e1", "hp", 7), ("remove", "e1", "name"), ("create", "e2"), ("rng",)])
    e.rollback(1)
    row("apply then inverse restores the exact bytes (incl. alloc and rng)", canon(e.current) == before,
        "restored digest %s" % e.digest()[:12])

    # 4. atomicity: a failure at any op boundary aborts, state byte-identical, no journal entry
    atomic = True
    for pos in range(4):
        e2 = Engine()
        e2.commit([("create", "e1"), ("set", "e1", "hp", 1)])
        snap, jlen = canon(e2.current), len(e2.journal)
        ops = [("set", "e1", "hp", 2), ("create", "e2"), ("set", "e2", "k", 9), ("rng",)]
        ops.insert(pos, ("fail",))
        try:
            e2.commit(ops)
            atomic = False                           # should have raised
        except TxnAbort:
            pass
        if canon(e2.current) != snap or len(e2.journal) != jlen:
            atomic = False
    row("a failure injected at every op boundary aborts atomically; no journal entry", atomic, "4 positions")

    # 5. rollback restores every intermediate digest exactly
    cmds = [[("create", "e1")], [("set", "e1", "hp", 5)], [("create", "e2")], [("set", "e2", "hp", 9)], [("rng",)]]
    digs, eng = replay(cmds)
    ok5 = True
    for k in range(len(cmds) - 1, -1, -1):
        eng.rollback(1)
        want = digs[k - 1] if k >= 1 else digest(genesis())
        if eng.digest() != want:
            ok5 = False
    row("rollback restores every intermediate digest exactly", ok5, "%d steps" % len(cmds))

    # 6. allocator + rng rollback
    e6 = Engine()
    g = e6.digest()
    e6.commit([("create", "e1"), ("rng",), ("rng",)])
    e6.rollback(1)
    row("allocator and rng counter are restored by rollback", e6.digest() == g and e6.current["alloc"] == 1
        and e6.current["rng"]["counter"] == 0, "alloc %d rng %d" % (e6.current["alloc"], e6.current["rng"]["counter"]))

    # 7. deterministic replay: same commands from genesis give the same final digest, twice
    d_a, _ = replay(cmds)
    d_b, _ = replay(cmds)
    row("replay is deterministic (same final digest across two runs)", d_a[-1] == d_b[-1], d_a[-1][:16])

    # 8. scheduling: independent transactions reorder to the same digest; a conflicting pair is detected, not reordered
    t_ind = [[("create", "e1"), ("set", "e1", "hp", 1)], [("set", "e2", "k", 2)]]   # disjoint cells
    # seed e2 first so both are valid regardless of order
    def run_order(order):
        e = Engine(); e.commit([("create", "e1"), ("create", "e2")])
        for ops in order:
            e.commit(ops)
        return e.digest()
    o1 = run_order([[("set", "e1", "hp", 1)], [("set", "e2", "k", 2)]])
    o2 = run_order([[("set", "e2", "k", 2)], [("set", "e1", "hp", 1)]])
    conflict_detected = not independent([("set", "e1", "hp", 1)], [("set", "e1", "hp", 2)])
    row("independent transactions reorder to the same digest; a conflicting pair is detected (not reordered)",
        o1 == o2 and conflict_detected, "independent equal %s; conflict flagged %s" % (o1 == o2, conflict_detected))

    # 9. external effects are apart from the digest and not reversed by memory
    e9 = Engine()
    e9.commit([("create", "e1"), ("effect", "file-write", "out.txt"), ("set", "e1", "hp", 1)])
    no_effect_op = Engine(); no_effect_op.commit([("create", "e1"), ("set", "e1", "hp", 1)])
    row("an external effect is logged apart and not in the digest", e9.digest() == no_effect_op.digest()
        and len(e9.effects) == 1 and e9.effects[0]["kind"] == "file-write", "effects %d" % len(e9.effects))

    # 10. ledger equivalence: the baseline reaches the same digest as the buffer+journal
    _, eng10 = replay(cmds)
    row("the ledger-style baseline reaches the same digest as the buffer", digest(ledger_state(cmds)) == eng10.digest(),
        digest(ledger_state(cmds))[:16])

    print("ECS SELFTEST %d/%d" % (sum(rows), len(rows)))
    return 0 if all(rows) else 1


if __name__ == "__main__":
    import sys
    sys.exit(selftest() if sys.argv[1:2] == ["selftest"] else (print(__doc__) or 2))
