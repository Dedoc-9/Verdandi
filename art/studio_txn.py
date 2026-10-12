# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/studio_txn.py — the studio's change transaction, as a reference: the promotion journal's byte form and grammar,
# and Recover(J, P, F), the one decision the stub takes at every start and after every exit of a generation
# (docs/STUDIO-CONTRACT.md). Nothing here launches, moves or writes anything in a studio: `recover ROOT` reads one
# and prints what the stub must do; `check` holds the decision to its contract over every crash point of every
# enumerated promotion; `selftest` plants wrong decisions and requires `check` to catch each. Standard library only.
#
# By the owner's review of 2026-10-12 (the reviews he brought, which agree): the commit point is the durable `blessed`
# record; recovery reads the journal J, the pointer P and the surviving files F together, never the journal alone;
# "After any tested interruption, recovery must produce one well-defined state, preserve the last admitted generation
# as a recoverable fallback, and never bless a candidate without intact evidence that it was validated against its
# recorded basis." Crash-only (Candea and Fox, 2003): "stop=crash and start=recover"; here the stub has no other
# start, and its normal promotion steps are the same decision taken again.
#
# The fault model the check enumerates is the termination of a process at any point between two durable writes, and a
# torn final append. An operating-system crash is claimed only under the axioms of docs/STUDIO-APP.md §5.2; power loss
# is not claimed. A journal or pointer fault outside the model (a damaged middle line, a pointer naming what the
# journal never set) is not guessed at: the decision is SAFE, and a person chooses.

import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "director"))
import intent as canon  # noqa: E402

PROTOCOL, VERSION = "STUDIO-TXN", "0"
ZERO = "0" * 64
LIFECYCLE = ("proposed", "staged", "built", "checked", "launched", "healthy", "dead", "rejected")
STUB = ("activate", "boot", "blessed", "rollback", "aborted", "recovered")
KINDS = ("installed",) + LIFECYCLE + ("promote",) + STUB
FIELDS = {"installed": ("gen",), "checked": ("gen", "basis", "evidence"), "promote": ("gen", "from", "basis", "tries"),
          "activate": ("gen",), "boot": ("gen", "left"), "blessed": ("gen",), "rollback": ("from", "to", "reason"),
          "aborted": ("gen", "reason"), "recovered": ("reason",)}
TARGETS = ("installed", "activate", "blessed", "rollback")      # the records a pointer may name: each sets the target
COMMITTED = "committed"                                        # the basis of a promotion back to a committed generation
MAX_TRIES = 9

# ------------------------------------------------------------------------------------------------ the decision table
# Printed by `table`; docs/STUDIO-CONTRACT.md holds the same lines, and `selftest` requires the two to agree.
TABLE = """\
R0   J missing                                             SAFE journal-missing
R1   J's bytes do not end in LF                            set the bytes after the last LF aside; truncate; append recovered{torn-tail}; again
R2   a line of J is not the next record of the chain       SAFE journal-fault
R3   J's records break the grammar                         SAFE journal-grammar
R4   P names a seq beyond J's end                          SAFE pointer-ahead
R5   P's seq is not a target record naming P's gen         SAFE pointer-inconsistent
R6   P missing                                             append recovered{pointer-missing}; write P := target; again
R7   P not a pointer document                              append recovered{pointer-invalid}; write P := target; again
R8   P's gen is not the target's                           append recovered{pointer-stale}; write P := target; again
R9   promote open, not activated, and Integrity(C),        append activate{C}; write P := C; again
     Evidence(C), Integrity(committed)
R10  promote open, not activated, otherwise                append aborted{C, reason}; again
R11  activated, Integrity(C), Evidence(C), left > 0        append boot{C, left-1}; BOOT C (the stub appends blessed{C} once Healthy)
R12  activated, otherwise, Integrity(committed)            append rollback{C, committed, reason}; write P := committed; again
R13  activated, otherwise                                  SAFE fallback-corrupt
R14  no transaction open, Integrity(committed)             RUN committed
R15  no transaction open, otherwise                        SAFE committed-corrupt"""


class Fault(Exception):
    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code


def sha256(b):
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------------------------------------ bytes
def record(seq, prev, kind, fields):
    d = dict(fields, protocol=PROTOCOL, version=VERSION, seq=str(seq), prev=prev, kind=kind)
    return canon.dumps(d)


def append_bytes(raw, kind, fields):
    """J's bytes with one record appended (raw must be a whole journal: empty, or ending in LF)."""
    lines = raw.split(b"\n")[:-1] if raw else []
    prev = sha256(lines[-1]) if lines else ZERO
    return raw + record(len(lines), prev, kind, fields) + b"\n"


def pointer_bytes(gen, seq):
    return canon.dumps({"protocol": PROTOCOL, "version": VERSION, "kind": "pointer", "gen": gen, "seq": str(seq)})


def parse_pointer(b):
    """("missing",) | ("invalid",) | ("ok", gen, seq)."""
    if b is None:
        return ("missing",)
    try:
        d = canon.loads(b)
        if (set(d) != {"protocol", "version", "kind", "gen", "seq"} or d["protocol"] != PROTOCOL or d["version"] != VERSION
                or d["kind"] != "pointer" or not canon.HEX64.match(d["gen"])):
            return ("invalid",)
        return ("ok", d["gen"], canon.integer(d["seq"], "seq"))
    except (canon.IntentError, TypeError, AttributeError):
        return ("invalid",)


_CHAIN, _REPLAY = {}, {}


def chain(raw):
    """chain_(raw), remembered (the check asks for the same bytes many times; at most 20,000 kept)."""
    r = _CHAIN.get(raw)
    if r is None:
        try:
            r = ("ok", chain_(raw))
        except Fault as e:
            r = ("fault", e)
        if len(_CHAIN) > 20000:
            _CHAIN.clear()
        _CHAIN[raw] = r
    if r[0] == "fault":
        raise r[1]
    return r[1]


def chain_(raw):
    """J's records, each the next of the chain: (records, torn bytes). Fault R2 otherwise."""
    torn = b""
    if raw and not raw.endswith(b"\n"):
        cut = raw.rfind(b"\n") + 1
        raw, torn = raw[:cut], raw[cut:]
    lines = raw.split(b"\n")[:-1] if raw else []
    recs, prev = [], ZERO
    for i, ln in enumerate(lines):
        try:
            d = canon.loads(ln)
        except canon.IntentError as e:
            raise Fault("journal-fault", "line %d: %s" % (i + 1, e.code))
        if not isinstance(d, dict) or d.get("protocol") != PROTOCOL or d.get("version") != VERSION:
            raise Fault("journal-fault", "line %d: not a %s %s record" % (i + 1, PROTOCOL, VERSION))
        if d.get("seq") != str(i) or d.get("prev") != prev:
            raise Fault("journal-fault", "line %d: seq or prev is not the chain's" % (i + 1))
        k = d.get("kind")
        if k not in KINDS or any(not isinstance(d.get(f), str) for f in FIELDS.get(k, ())):
            raise Fault("journal-fault", "line %d: kind %r or its fields" % (i + 1, k))
        prev = sha256(ln)
        recs.append(d)
    return recs, torn


# ------------------------------------------------------------------------------------------------ the grammar
def parse(raw):
    """(records, state) of a whole journal's bytes, remembered; Fault (R2 or R3) otherwise."""
    r = _REPLAY.get(raw)
    if r is None:
        try:
            recs = chain(raw)[0]
            r = ("ok", recs, replay(recs))
        except Fault as e:
            r = ("fault", e)
        if len(_REPLAY) > 20000:
            _REPLAY.clear()
        _REPLAY[raw] = r
    if r[0] == "fault":
        raise r[1]
    return r[1], r[2]


def replay(recs):
    """The state a journal describes, or Fault R3. A journal is installed, then any number of lifecycle records and
    transactions; a transaction is promote, then aborted, or activate, boot..., and blessed or rollback; while one is
    open only the stub writes, and only its records."""
    if not recs or recs[0]["kind"] != "installed":
        raise Fault("journal-grammar", "the first record is not installed")
    st = {"committed": recs[0]["gen"], "history": [recs[0]["gen"]], "checked": {}, "txn": None,
          "target": recs[0]["gen"], "target_seq": 0, "targets": {0: recs[0]["gen"]}}

    def bad(i, why):
        raise Fault("journal-grammar", "record %d (%s): %s" % (i, recs[i]["kind"], why))
    for i, r in enumerate(recs[1:], 1):
        k, t = r["kind"], st["txn"]
        if k == "installed":
            bad(i, "installed is only the first record")
        if k == "recovered":
            continue
        if t is None:
            if k == "checked":
                st["checked"].setdefault(r["gen"], []).append((r["basis"], r["evidence"]))
            elif k == "promote":
                try:
                    tries = canon.integer(r["tries"], "tries")
                except canon.IntentError:
                    bad(i, "tries is not an integer")
                if not 1 <= tries <= MAX_TRIES:
                    bad(i, "tries outside 1..%d" % MAX_TRIES)
                if r["from"] != st["committed"] or r["gen"] == st["committed"]:
                    bad(i, "a promotion is from the committed generation to another")
                if r["basis"] == COMMITTED:
                    if r["gen"] not in st["history"]:
                        bad(i, "a promotion back names a generation never committed")
                elif r["basis"] not in [b for b, _e in st["checked"].get(r["gen"], [])]:
                    bad(i, "no checked record of this generation has this basis")
                st["txn"] = {"gen": r["gen"], "basis": r["basis"], "tries": tries, "activated": False, "boots": 0}
            elif k in LIFECYCLE:
                pass
            else:
                bad(i, "a stub record with no transaction open")
            continue
        if k in LIFECYCLE or k == "promote":
            bad(i, "a supervisor record while a transaction is open")
        gen = r.get("gen", r.get("from"))
        if gen != t["gen"]:
            bad(i, "names another generation than the open transaction's")
        if k == "aborted":
            if t["activated"]:
                bad(i, "aborted after activate (that is a rollback)")
            st["txn"] = None
        elif k == "activate":
            if t["activated"]:
                bad(i, "activated twice")
            t["activated"] = True
            st["target"], st["target_seq"] = gen, i
            st["targets"][i] = gen
        elif k == "boot":
            if not t["activated"] or r["left"] != str(t["tries"] - t["boots"] - 1):
                bad(i, "a boot before activate, or its left is not tries less the boots")
            t["boots"] += 1
        elif k == "blessed":
            if not t["activated"] or t["boots"] < 1:
                bad(i, "blessed before a boot")
            st["committed"] = gen
            st["history"].append(gen)
            st["target"], st["target_seq"] = gen, i
            st["targets"][i] = gen
            st["txn"] = None
        elif k == "rollback":
            if not t["activated"] or r["to"] != st["committed"]:
                bad(i, "a rollback before activate, or not to the committed generation")
            st["target"], st["target_seq"] = st["committed"], i
            st["targets"][i] = st["committed"]
            st["txn"] = None
    return st


def evidence(st, F):
    """Evidence(C): its promotion's basis is that of a checked record whose evidence file is intact; a promotion back
    to a committed generation needs only that generation's integrity."""
    t = st["txn"]
    if t["basis"] == COMMITTED:
        return True
    return any(b == t["basis"] and F["evidence"](e) for b, e in st["checked"].get(t["gen"], []))


# ------------------------------------------------------------------------------------------------ the decision
def recover(J, P, F, plant=None):
    """Recover(J, P, F): (effects, action, rules). J is the journal's bytes or None, P the pointer's bytes or None, F
    {"integrity": gen -> bool, "evidence": sha -> bool}. Effects are the durable writes, in order, the stub makes before
    the action: ("aside", bytes), ("truncate", n), ("append", kind, fields), ("pointer", gen, seq). The action is
    ("run", gen), ("boot", gen) or ("safe", code, detail)."""
    effects, rules = [], []
    ok = F["integrity"]

    def safe(rule, code, detail):
        rules.append(rule)
        return effects, ("safe", code, detail), rules
    if J is None:
        return safe("R0", "journal-missing", "no promotions.log")
    for _ in range(4 * MAX_TRIES + 16):
        if J and not J.endswith(b"\n"):
            if plant == "torn-is-fault":
                return safe("R1", "journal-fault", "torn")
            cut = J.rfind(b"\n") + 1
            if plant == "torn-keeps-line":
                J = J + b"\n"
            else:
                effects.extend([("aside", J[cut:]), ("truncate", cut)])
                J = J[:cut]
            rules.append("R1")
            if J:
                effects.append(("append", "recovered", {"reason": "torn-tail"}))
                J = append_bytes(J, "recovered", {"reason": "torn-tail"})
            continue
        try:
            recs, st = parse(J)
        except Fault as e:
            if e.code == "journal-grammar":
                return safe("R3", e.code, str(e))
            if plant == "fault-keeps-prefix":
                lines = J.split(b"\n")[:-1]
                for n in range(len(lines), -1, -1):
                    try:
                        J = b"".join(ln + b"\n" for ln in lines[:n])
                        chain(J)
                        break
                    except Fault:
                        continue
                effects.append(("truncate", len(J)))
                continue
            return safe("R2", e.code, str(e))
        p = parse_pointer(P)
        if plant == "pointer-wins" and p[0] == "ok" and ok(p[1]):
            rules.append("R14")
            return effects, ("run", p[1]), rules
        if p[0] == "ok":
            if p[2] >= len(recs):
                if plant != "pointer-ahead-ignored":
                    return safe("R4", "pointer-ahead", "P names seq %d; J ends at %d" % (p[2], len(recs) - 1))
            elif st["targets"].get(p[2]) != p[1]:
                if plant == "pointer-rebuilt":
                    p = ("stale",)
                else:
                    return safe("R5", "pointer-inconsistent", "seq %d does not set %s" % (p[2], p[1][:12]))
        why = {"missing": ("R6", "pointer-missing"), "invalid": ("R7", "pointer-invalid"), "stale": ("R8", "pointer-stale")}.get(p[0])
        if why is None and p[1] != st["target"] and plant != "stale-pointer-runs":
            why = ("R8", "pointer-stale")
        if why is not None:
            if why[0] == "R6" and plant == "missing-pointer-safe":
                return safe("R6", "pointer-missing", "refused")
            rules.append(why[0])
            effects.append(("append", "recovered", {"reason": why[1]}))
            effects.append(("pointer", st["target"], st["target_seq"]))
            J = append_bytes(J, "recovered", {"reason": why[1]})
            P = pointer_bytes(st["target"], st["target_seq"])
            continue
        if p[0] == "ok" and plant == "stale-pointer-runs" and p[1] != st["target"] and ok(p[1]):
            rules.append("R14")
            return effects, ("run", p[1]), rules
        t = st["txn"]
        if t is not None and not t["activated"]:
            checks = [("integrity", ok(t["gen"])), ("evidence", evidence(st, F) or plant == "no-evidence"),
                      ("fallback", ok(st["committed"]) or plant == "no-fallback-check")]
            failed = [n for n, v in checks if not v]
            if not failed:
                rules.append("R9")
                if plant == "pointer-before-activate":
                    effects.append(("pointer", t["gen"], len(recs)))
                    effects.append(("append", "activate", {"gen": t["gen"]}))
                else:
                    effects.append(("append", "activate", {"gen": t["gen"]}))
                    effects.append(("pointer", t["gen"], len(recs)))
                J = append_bytes(J, "activate", {"gen": t["gen"]})
                P = pointer_bytes(t["gen"], len(recs))
            else:
                rules.append("R10")
                f = {"gen": t["gen"], "reason": failed[0]}
                effects.append(("append", "aborted", f))
                J = append_bytes(J, "aborted", f)
            continue
        if t is not None:
            left = t["tries"] - t["boots"]
            go = (ok(t["gen"]) or plant == "no-integrity") and (evidence(st, F) or plant == "no-evidence")
            if go and (left > 0 or (plant == "extra-try" and left > -1)):
                rules.append("R11")
                if plant != "no-boot-record":
                    effects.append(("append", "boot", {"gen": t["gen"], "left": str(left - 1)}))
                return effects, ("boot", t["gen"]), rules
            back = st["history"][0] if plant == "rollback-to-first" else st["committed"]
            if ok(back):
                rules.append("R12")
                reason = "tries" if go else ("integrity" if not ok(t["gen"]) else "evidence")
                f = {"from": t["gen"], "to": back, "reason": reason}
                effects.append(("append", "rollback", f))
                effects.append(("pointer", back, len(recs)))
                J = append_bytes(J, "rollback", f)
                P = pointer_bytes(back, len(recs))
                continue
            return safe("R13", "fallback-corrupt", "neither %s nor %s is intact" % (t["gen"][:12], back[:12]))
        if ok(st["committed"]):
            rules.append("R14")
            return effects, ("run", st["committed"]), rules
        if plant == "undo-commit" and len(st["history"]) > 1 and ok(st["history"][-2]):
            rules.append("R14")
            return effects, ("run", st["history"][-2]), rules
        return safe("R15", "committed-corrupt", "%s does not verify" % st["committed"][:12])
    raise AssertionError("recover did not reach an action")


def apply(J, P, effects, upto=None):
    """The studio's J and P after the first `upto` effects (all of them by default)."""
    for e in effects[:len(effects) if upto is None else upto]:
        if e[0] == "truncate":
            J = J[:e[1]]
        elif e[0] == "append":
            J = append_bytes(J, e[1], e[2])
        elif e[0] == "pointer":
            P = pointer_bytes(e[1], e[2])
    return J, P


# ------------------------------------------------------------------------------------------------ the contract, apart
def allowed(J, F):
    """What the protocol permits after a crash, from the durable records alone, written apart from recover(): the
    action a crash-free run would take next, as ("run", gen), ("trial", gen) or ("safe",). Exactly one."""
    whole = J if J.endswith(b"\n") else J[:J.rfind(b"\n") + 1]
    if not whole:
        return ("safe",)
    try:
        st = parse(whole)[1]
    except Fault:
        return ("safe",)
    ok, B, t = F["integrity"], st["committed"], st["txn"]
    if t is None:
        return ("run", B) if ok(B) else ("safe",)
    fine = ok(t["gen"]) and evidence(st, F)
    if not t["activated"]:
        if fine and ok(B):
            return ("trial", t["gen"])
        return ("run", B) if ok(B) else ("safe",)
    if fine and t["boots"] < t["tries"]:
        return ("trial", t["gen"])
    return ("run", B) if ok(B) else ("safe",)


def allowed_fallback(J):
    """The committed generation of a journal (the fallback of its open transaction)."""
    whole = J if J.endswith(b"\n") else J[:J.rfind(b"\n") + 1]
    return parse(whole)[1]["committed"]


GEN = {n: sha256(n.encode()) for n in ("G0", "G1", "C")}
EVID = sha256(b"results of C")


def scripts():
    """The durable writes of promotions as a correct supervisor and stub make them, each a list of ("append", kind,
    fields) and ("pointer", gen, seq) in order; written as sequences, not by recover()."""
    G0, G1, C = GEN["G0"], GEN["G1"], GEN["C"]
    out = []
    for hist in ("fresh", "one"):
        base = [("append", "installed", {"gen": G0}), ("pointer", G0, 0)]
        B = G0
        if hist == "one":
            base += [("append", "checked", {"gen": G1, "basis": "b1", "evidence": EVID}),
                     ("append", "promote", {"gen": G1, "from": G0, "basis": "b1", "tries": "2"}),
                     ("append", "activate", {"gen": G1}), ("pointer", G1, 3),
                     ("append", "boot", {"gen": G1, "left": "1"}), ("append", "blessed", {"gen": G1})]
            B = G1
        targets = [(C, "bC", [("append", "launched", {}), ("append", "dead", {}),
                              ("append", "checked", {"gen": C, "basis": "bC", "evidence": EVID})])]
        if hist == "one":
            targets.append((G0, COMMITTED, []))
        for gen, basis, pre in targets:
            for tries in (1, 2, 3):
                head = base + pre + [("append", "promote", {"gen": gen, "from": B, "basis": basis, "tries": str(tries)})]
                n0 = sum(1 for w in head if w[0] == "append")
                act = [("append", "activate", {"gen": gen}), ("pointer", gen, n0)]

                def boots(k):
                    return [("append", "boot", {"gen": gen, "left": str(tries - j - 1)}) for j in range(k)]
                out.append(("%s/%s/%d/aborted" % (hist, basis, tries), head + [("append", "aborted", {"gen": gen, "reason": "integrity"})]))
                for k in range(1, tries + 1):
                    out.append(("%s/%s/%d/blessed-after-%d" % (hist, basis, tries, k), head + act + boots(k) + [("append", "blessed", {"gen": gen})]))
                for k, reason in [(tries, "tries")] + [(j, "integrity") for j in range(tries)]:
                    w = head + act + boots(k)
                    n = n0 + 1 + k
                    out.append(("%s/%s/%d/rollback-%s-%d" % (hist, basis, tries, reason, k),
                                w + [("append", "rollback", {"from": gen, "to": B, "reason": reason}), ("pointer", B, n)]))
    return out


def fs(intact):
    """F with the named generations intact, and C's evidence intact unless 'evidence' is absent from the set."""
    return {"integrity": lambda g: any(GEN[n] == g for n in intact if n in GEN),
            "evidence": lambda e: "evidence" in intact and e == EVID}


FS = [frozenset(s) for s in ([], ["G0"], ["G1"], ["C"], ["G0", "G1"], ["G0", "C"], ["G1", "C"], ["G0", "G1", "C"])]
FS = [s | {"evidence"} for s in FS] + FS
ALL = frozenset(["G0", "G1", "C", "evidence"])


def states(script):
    """Every crash point of a script: (label, J, P) after each prefix of its writes, and with the next append torn."""
    J, P = b"", None
    for i, w in enumerate(script):
        yield ("after %d" % i, J, P)
        if w[0] == "append":
            nxt = append_bytes(J, w[1], w[2])
            line = nxt[len(J):]
            for cut in sorted({1, len(line) // 2, len(line) - 1}):
                yield ("torn %d at %d" % (i, cut), J + line[:cut], P)
            J = nxt
        else:
            yield ("pointer-invalid %d" % i, J, b'{"half')
            P = pointer_bytes(w[1], w[2])
    yield ("whole", J, P)


RULES_SEEN = set()


def outcome(J, P, F, plant):
    """Recover, then the action it reaches as allowed() names actions."""
    effects, action, rules = recover(J, P, F, plant)
    RULES_SEEN.update(rules)
    J2, P2 = apply(J, P, effects)
    if action[0] == "safe":
        return ("safe",), effects, action, rules, J2, P2
    return ("run" if action[0] == "run" else "trial", action[1]), effects, action, rules, J2, P2


def wal(effects, J):
    """Every pointer write names a record that is durable before it."""
    n = len(J.split(b"\n")) - 1 if J else 0
    for e in effects:
        if e[0] == "truncate":
            n = J[:e[1]].count(b"\n")
        elif e[0] == "append":
            n += 1
        elif e[0] == "pointer" and e[2] >= n:
            return False
    return True


class Enough(Exception):
    pass


def check(plant=None, say=print, first=False):
    """Recover held to its contract over every crash point of every script and every F; returns the failures (with
    first, the first alone)."""
    fails, n = [], {"states": 0, "crashes-in-recovery": 0, "chains": 0, "mutations": 0, "rules": set()}
    RULES_SEEN.clear()
    try:
        check_(plant, say, first, fails, n)
        n["rules"] = set(RULES_SEEN)
    except Enough:
        return fails
    except Exception as e:  # noqa: BLE001 — a decision that throws has failed its contract
        say("  FAIL the check stopped: %s: %s" % (type(e).__name__, e))
        fails.append("the check stopped: %s: %s" % (type(e).__name__, e))
        return fails
    unreached = [r for r in ("R%d" % i for i in range(16)) if r not in n["rules"]]
    if unreached:
        fails.append("rules never reached: %s" % " ".join(unreached))
    say("STUDIO-TXN  scripts %d  crash states %d  crashes inside recovery %d  boot chains %d  damaged journals and pointers %d  "
        "rules reached %d of 16%s  failures %d" % (len(scripts()), n["states"], n["crashes-in-recovery"], n["chains"], n["mutations"],
                                                   16 - len(unreached), (" (not " + " ".join(unreached) + ")") if unreached else "", len(fails)))
    return fails


def check_(plant, say, first, fails, n):
    def fail(what):
        if len(fails) < 8:
            say("  FAIL %s" % what)
        fails.append(what)
        if first:
            raise Enough()
    for name, script in scripts():
        for label, J, P in states(script):
            for intact in FS:
                F = fs(intact)
                n["states"] += 1
                where = "%s %s F=%s" % (name, label, ",".join(sorted(intact)) or "-")
                try:
                    want = allowed(J, F) if J else ("safe",)
                    got, effects, action, rules, J2, P2 = outcome(J if J else None, P, F, plant)
                except Exception as e:  # noqa: BLE001 — a crash of the decision is a failure of the contract
                    fail("%s: %s" % (where, e))
                    continue
                if got != want:
                    fail("%s: %s, the contract %s (%s)" % (where, got, want, " ".join(rules)))
                    continue
                if not wal(effects, J or b""):
                    fail("%s: a pointer written before its record (%s)" % (where, " ".join(rules)))
                    continue
                # a crash inside the recovery itself: after each of its effects, and with each of its appends torn
                for k in range(len(effects) + 1):
                    Jk, Pk = apply(J or b"", P, effects, k)
                    variants = [(Jk, Pk)]
                    if k < len(effects) and effects[k][0] == "append":
                        line = append_bytes(Jk, effects[k][1], effects[k][2])[len(Jk):]
                        variants.append((Jk + line[:len(line) // 2], Pk))
                    for Jv, Pv in variants:
                        n["crashes-in-recovery"] += 1
                        try:
                            got2 = outcome(Jv if Jv else None, Pv, F, plant)[0]
                        except Exception as e:  # noqa: BLE001
                            fail("%s, crashed at recovery effect %d: %s" % (where, k, e))
                            continue
                        want2 = allowed(Jv, F) if Jv else ("safe",)
                        if got2 != want2 or (want2[0] != "safe" and want2 != want and not (
                                want[0] == "trial" and want2 == ("run", allowed_fallback(Jv)))):
                            fail("%s, crashed at recovery effect %d: %s, the contract %s (before the crash %s)" % (where, k, got2, want2, want))
                # idempotent, and every chain of failed boots ends; a healthy boot commits
                if got[0] == "run":
                    e3, a3, _r = recover(J2, P2, F, plant)[:3]
                    if e3 or a3 != action:
                        fail("%s: run twice, a second decision %s %s" % (where, a3, e3))
                elif got[0] == "trial":
                    Jc, Pc, steps = J2, P2, 0
                    while True:
                        n["chains"] += 1
                        steps += 1
                        ec, ac, _rc = recover(Jc, Pc, F, plant)
                        Jc, Pc = apply(Jc, Pc, ec)
                        if ac[0] != "boot" or steps > MAX_TRIES + 3:
                            break
                    if steps > MAX_TRIES + 3 or ac[0] == "boot":
                        fail("%s: failed boots do not end" % where)
                    elif ac[0] == "run" and not F["integrity"](ac[1]):
                        fail("%s: ran %s, which does not verify" % (where, ac[1][:12]))
                    Jh = append_bytes(J2, "blessed", {"gen": action[1]})
                    eh, ah, _rh = recover(Jh, P2, F, plant)
                    if ah != ("run", action[1]):
                        fail("%s: blessed, then %s" % (where, ah))
                # the commit is never undone
                whole = J if J.endswith(b"\n") else J[:J.rfind(b"\n") + 1]
                if whole and "blessed" in [r["kind"] for r in parse(whole)[0]]:
                    st = parse(whole)[1]
                    if st["txn"] is None and got not in (("run", st["committed"]), ("safe",)):
                        fail("%s: the committed %s undone (%s)" % (where, st["committed"][:12], got))
        # the whole journal, damaged: every line but the last is held by the chain; a cut is a torn tail or a prefix
        J, P = b"", None
        for w in script:
            J, P = apply(J, P, [w])
        lines = J.split(b"\n")[:-1]
        F = fs(ALL)
        for i in range(len(lines) - 1):
            for bad in (lines[:i] + [lines[i][:-3] + b'x"}'] + lines[i + 1:], lines[:i] + [lines[i], lines[i]] + lines[i + 1:],
                        lines[:i] + [lines[i + 1], lines[i]] + lines[i + 2:], lines[:i] + lines[i + 1:]):
                n["mutations"] += 1
                Jb = b"".join(ln + b"\n" for ln in bad)
                got = outcome(Jb, P, F, plant)[0]
                if got != ("safe",):
                    fail("%s: line %d damaged, decided %s" % (name, i, got))
        for cut in range(len(J)):
            n["mutations"] += 1
            Jc = J[:cut]
            whole = Jc[:Jc.rfind(b"\n") + 1] if b"\n" in Jc else b""
            p = parse_pointer(P)
            if not whole:
                want = ("safe",)
            elif p[0] == "ok" and p[2] >= whole.count(b"\n"):
                want = ("safe",)
            else:
                want = allowed(whole, F)
            got = outcome(Jc if Jc else None, P, F, plant)[0]
            if got != want:
                fail("%s: cut at byte %d, decided %s, the contract %s" % (name, cut, got, want))
    # a pointer that names what the journal never set is not guessed at
    J, P = b"", None
    for w in scripts()[0][1]:
        J, P = apply(J, P, [w])
    for pb in (pointer_bytes(GEN["C"], 0), pointer_bytes(GEN["G0"], 1), pointer_bytes(GEN["G0"], 999)):
        n["mutations"] += 1
        if outcome(J, pb, fs(ALL), plant)[0] != ("safe",):
            fail("a pointer %r not set by the journal was followed" % pb[:60])


PLANTS = ("torn-is-fault", "torn-keeps-line", "fault-keeps-prefix", "pointer-wins", "pointer-ahead-ignored", "pointer-rebuilt",
          "stale-pointer-runs", "missing-pointer-safe", "pointer-before-activate", "no-evidence",
          "no-fallback-check", "no-integrity", "extra-try", "no-boot-record", "rollback-to-first", "undo-commit")


def doc_table():
    p = os.path.join(os.path.dirname(HERE), "docs", "STUDIO-CONTRACT.md")
    text = open(p, encoding="utf-8").read()
    start = text.index("```text decision-table\n") + len("```text decision-table\n")
    return text[start:text.index("```", start)].rstrip("\n")


def disk_cases():
    """recover on a studio written to a temporary directory: a generation intact, then with a file the manifest does
    not name, then with a named file changed. Returns the failures."""
    import shutil
    import tempfile
    fails = []
    root = tempfile.mkdtemp(prefix="studio-txn-")
    try:
        files = {"art/studio_app.py": b"print('studio')\n", "art/web/play.js": b"// page\n"}
        mb = manifest_bytes(files)
        gen = sha256(mb)
        d = os.path.join(root, "versions", gen)
        for rel, b in files.items():
            os.makedirs(os.path.dirname(os.path.join(d, *rel.split("/"))), exist_ok=True)
            open(os.path.join(d, *rel.split("/")), "wb").write(b)
        open(os.path.join(d, "manifest.json"), "wb").write(mb)
        os.makedirs(os.path.join(root, "studio", "evidence"))
        J = append_bytes(b"", "installed", {"gen": gen})
        open(os.path.join(root, "studio", "promotions.log"), "wb").write(J)
        open(os.path.join(root, "studio", "active.json"), "wb").write(pointer_bytes(gen, 0))

        def decide():
            F = {"integrity": integrity_on_disk(root), "evidence": evidence_on_disk(root)}
            return recover(read_or_none(os.path.join(root, "studio", "promotions.log")),
                           read_or_none(os.path.join(root, "studio", "active.json")), F)[1]
        for label, act, want in (("intact", None, ("run", gen)),
                                 ("an unnamed file", lambda: open(os.path.join(d, "art", "json.py"), "wb").write(b"x"), "committed-corrupt"),
                                 ("a named file changed", lambda: (os.remove(os.path.join(d, "art", "json.py")),
                                                                   open(os.path.join(d, "art", "web", "play.js"), "ab").write(b" ")), "committed-corrupt")):
            if act:
                act()
            a = decide()
            if (a if isinstance(want, tuple) else a[1]) != want:
                fails.append("disk %s: %s" % (label, a))
            print("  disk %-22s %s" % (label, " ".join(a)[:90]))
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return fails


def selftest():
    bad = 0
    if disk_cases():
        bad += 1
    if doc_table() != TABLE:
        print("  FAIL docs/STUDIO-CONTRACT.md's decision table is not TABLE")
        bad += 1
    if check(say=lambda s: print("  honest   " + s)):
        bad += 1
    for p in PLANTS:
        caught = check(plant=p, say=lambda s: None, first=True)
        print("  plant %-24s %s" % (p, ("caught: " + caught[0][:110]) if caught else "NOT CAUGHT"))
        bad += 0 if caught else 1
    print("STUDIO-TXN SELFTEST %s" % ("PASSED" if not bad else "FAILED (%d)" % bad))
    return 0 if not bad else 1


# ------------------------------------------------------------------------------------------------ a real studio
def manifest_bytes(files):
    """A generation's manifest: {path: bytes} -> the canonical document naming every file with its sha256."""
    return canon.dumps({"protocol": "STUDIO-GEN", "version": VERSION,
                        "files": [{"path": k, "sha256": sha256(files[k])} for k in sorted(files)]})


def integrity_on_disk(root):
    """Integrity(G): versions/G/manifest.json hashes to G, names its files in ascending order once each, every file it
    names hashes as it says, and no other file is in G (a file the manifest does not name could still be imported)."""
    def ok(gen):
        d = os.path.join(root, "versions", gen)
        try:
            mb = open(os.path.join(d, "manifest.json"), "rb").read()
            if sha256(mb) != gen:
                return False
            m = canon.loads(mb)
            if m.get("protocol") != "STUDIO-GEN" or m.get("version") != VERSION:
                return False
            paths = [f["path"] for f in m["files"]]
            if paths != sorted(set(paths)):
                return False
            seen = set()
            for dp, _dn, fn in os.walk(d):
                for f in fn:
                    rel = os.path.relpath(os.path.join(dp, f), d).replace(os.sep, "/")
                    if rel != "manifest.json":
                        seen.add(rel)
            if seen != set(paths):
                return False
            return all(sha256(open(os.path.join(d, *f["path"].split("/")), "rb").read()) == f["sha256"] for f in m["files"])
        except (OSError, canon.IntentError, KeyError, TypeError, AttributeError):
            return False
    return ok


def evidence_on_disk(root):
    def ok(e):
        try:
            return sha256(open(os.path.join(root, "studio", "evidence", e + ".json"), "rb").read()) == e
        except OSError:
            return False
    return ok


def read_or_none(p):
    try:
        return open(p, "rb").read()
    except OSError:
        return None


def main(argv):
    if argv[:1] == ["table"]:
        print(TABLE)
        return 0
    if argv[:1] == ["check"]:
        f = check()
        print("STUDIO-TXN %s" % ("CHECKED" if not f else "FAILED"))
        return 0 if not f else 1
    if argv[:1] == ["selftest"]:
        return selftest()
    if argv[:1] == ["recover"] and len(argv) == 2:
        root = argv[1]
        F = {"integrity": integrity_on_disk(root), "evidence": evidence_on_disk(root)}
        effects, action, rules = recover(read_or_none(os.path.join(root, "studio", "promotions.log")),
                                         read_or_none(os.path.join(root, "studio", "active.json")), F)
        print("RULES   %s" % " ".join(rules))
        for e in effects:
            print("EFFECT  %s" % " ".join(str(x) if not isinstance(x, (bytes, dict)) else repr(x) for x in e))
        print("ACTION  %s" % " ".join(action))
        return 0
    print("usage: python art/studio_txn.py table | check | selftest | recover STUDIO-ROOT")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
