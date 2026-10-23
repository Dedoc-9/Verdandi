"""Deterministic G1-G6 gate runner for the P-1 oracle (test-only; OFF-GATE).

Run:  PYTHONHASHSEED=0 PYTHONUTF8=1 python p1-oracle/run_gate.py

Reports each gate SEPARATELY (panel, not a scalar). Verdicts: PASS / FAIL / BLOCKED. BLOCKED is never counted as a
pass and never relabelled. Exit status is 0 iff there are zero FAILs; BLOCKED rows do not fail the run. Writes real
run evidence under evidence/ (logs, source hashes, run command, exit status). Nothing here certifies P-1, which is OPEN.
"""
import hashlib
import json
import os
import sys
import platform

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from tests import test_g1, test_g2, test_g3, test_g4, test_g5, test_g6, test_seams, test_buckets, test_struct, test_tier1, test_links, test_total  # noqa: E402

GATES = [
    ("G1 canonical bytes (+ Tier-1 local negatives)", [test_g1, test_tier1]),
    ("G2 trie shape (+ injected routing / seam / bucket placement / structural rejection)", [test_g2, test_seams, test_buckets, test_struct]),
    ("G3 reconstruction", [test_g3]),
    ("G4 record semantics (+ link/sequence validation)", [test_g4, test_links]),
    ("G5 checkpoint + anchor", [test_g5]),
    ("G6 reproducibility + bounds + constants (+ MAX_TOTAL)", [test_g6, test_total]),
]


def _source_hashes():
    out = {}
    for root, _dirs, files in os.walk(HERE):
        if os.sep + "evidence" in root or "__pycache__" in root:
            continue
        for fn in sorted(files):
            if fn.endswith((".py", ".md", ".json")):
                p = os.path.join(root, fn)
                rel = os.path.relpath(p, HERE).replace(os.sep, "/")
                out[rel] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    return out


def main():
    log = []

    def emit(s=""):
        print(s)
        log.append(s)

    emit("P-1 ORACLE GATE (test-only, OFF-GATE; P-1 remains OPEN)")
    emit("python %s on %s; PYTHONHASHSEED=%s PYTHONUTF8=%s"
         % (platform.python_version(), platform.platform(),
            os.environ.get("PYTHONHASHSEED"), os.environ.get("PYTHONUTF8")))
    emit("=" * 100)

    results = {}
    totals = {"PASS": 0, "FAIL": 0, "BLOCKED": 0}
    for gate_name, modules in GATES:
        rows = []
        for m in modules:
            rows += m.run()
        results[gate_name] = rows
        gp = sum(1 for _n, v, _d in rows if v == "PASS")
        gf = sum(1 for _n, v, _d in rows if v == "FAIL")
        gb = sum(1 for _n, v, _d in rows if v == "BLOCKED")
        totals["PASS"] += gp
        totals["FAIL"] += gf
        totals["BLOCKED"] += gb
        emit("")
        emit("%s   [PASS %d / FAIL %d / BLOCKED %d]" % (gate_name, gp, gf, gb))
        for name, verdict, detail in rows:
            emit("  %-8s %s%s" % (verdict, name, ("  -- " + detail) if detail else ""))

    emit("")
    emit("=" * 100)
    emit("TOTAL  PASS %d  FAIL %d  BLOCKED %d" % (totals["PASS"], totals["FAIL"], totals["BLOCKED"]))
    status = "PASS" if totals["FAIL"] == 0 else "FAIL"
    emit("GATE %s  (BLOCKED rows are not passes and do not fail the run; they mark D4-2/D8 scope)" % status)

    # ---- write real evidence (actual outputs only; no predeclared results) ----
    evdir = os.path.join(HERE, "evidence")
    os.makedirs(evdir, exist_ok=True)
    frozen = hashlib.sha256(open(os.path.join(HERE, "oracle", "frozen", "ecs.py"), "rb").read()).hexdigest()
    evidence = {
        "run_command": "PYTHONHASHSEED=0 PYTHONUTF8=1 python p1-oracle/run_gate.py",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "env": {"PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED"), "PYTHONUTF8": os.environ.get("PYTHONUTF8")},
        "frozen_ecs_sha256": frozen,
        "totals": totals,
        "gate_status": status,
        "exit_status": 0 if status == "PASS" else 1,
        "gates": {g: [{"name": n, "verdict": v, "detail": d} for (n, v, d) in rows] for g, rows in results.items()},
        "source_sha256": _source_hashes(),
    }
    with open(os.path.join(evdir, "latest.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)
        f.write("\n")
    with open(os.path.join(evdir, "latest.log"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(log) + "\n")
    emit("")
    emit("evidence written: evidence/latest.json, evidence/latest.log")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
