# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# tools/rung.py — RUNG-0: the candidate rung of a change to the program, computed by the host (0223).
#
#   python tools/rung.py classify BASE HEAD [--repo DIR]   each changed file's rung and why; the change's rung; what it needs
#   python tools/rung.py plants BASE HEAD [--repo DIR]     the old checker's planted defects, run by the old and the new trees
#   python tools/rung.py selftest                          the classifier against the cases planted for it, in a scratch repo
#
# By the owner's ruling of 2026-10-13: "Four candidate rungs, classified by the host … The model must not choose its own
# rung, and filenames alone must not determine it."; "Classify the effective change, not only its direct diff …
# calculate the rung from the candidate's dependency closure and changed semantics, conservatively escalating when that
# analysis is incomplete."; and of rung D, "a trusted admission path outside the candidate's authority, plus
# independent evidence". An intent's rung is ADMISSION-0's (art/director/contract.py); this is the rung of a patch.
#
# WHO RUNS IT. The classifier that judges a change must not be the change's: run the copy the pushed tree holds, against
# the commits to be pushed (docs/ROADMAP.md, 0223, gives the two commands). A change to this file is rung D, so it is
# judged by the copy before it. The first copy (this one) came with its own patch and was judged by nobody: said.
#
# HOW. The trusted base is anchored by the ROOTS below (the gate, the art's checks, the director, the admission path,
# the twins and references, this file, the agents' rules) — the one place names decide, and a change to it is rung D.
# Everything else is computed, on the HEAD tree and the BASE tree both (a file that was the checker's stays so when it
# is removed or renamed):
#   closure  each Python root is read as source (ast): its imports, resolved against its own folder and the folders
#            it puts on sys.path; and every path it names (so also a file it loads by spec_from_file_location) — a literal that is
#            a tracked file's path or name (a docstring is not a use; a message naming a file is counted, which errs
#            toward the checker), an os.path.join of known parts naming a file or a folder (a folder brings every
#            tracked file under it). A Python file reached is read the same way. Non-Python files are data, and
#            are not read further (a Rust or JS file is in the closure if a Python one names it).
#   escalate a root that loads code by a computed name (importlib.import_module, __import__, exec, eval of something not
#            a literal) may load any Python file; one that opens files by computed paths may read any file. Both are
#            said with their lines, and every changed file outside the closure is then D? — D for its evidence, marked
#            as escalated, not shown.
#   semantics changes that loosen a checker are named, whatever the rung: a name dropped from ADMISSION-0's expected
#            checks, a detector's threshold or a budget made looser, a frozen reference rewritten or removed (only
#            appends are allowed), the conformance vectors changed, planted defects fewer.
# Rungs: D a file of the closure (the checker, its data, what it reads by name) or escalated (D?); C code outside the
# closure (new behaviour); A a file of words, Markdown, outside the closure and every escalation. B, vocabulary made
# only of admitted kinds, has no form in this repository yet. A change's rung is the highest of its files'.
# Never read: a commit message, a patch's prose, a file's own claim about itself.
#
# Standard library and git only.

import ast
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# the trusted base's anchors: what decides, admits or holds the evidence. Changing this list is rung D (it is in it).
ROOTS = (
    "verify/verify.py",                                                       # the gate
    "art/check.py", "art/quality.py",                                         # the art's checks, QUALITY-0
    "art/director.py", "art/director/contract.py", "art/director/scope.py",   # the director, ADMISSION-0, the scope protocol
    "art/director/intent.py", "art/director/ledger.py", "art/director/durable.py",
    "art/director/conform.rs",                                                # the second implementation of the protocol
    "art/studio.py", "art/play.py", "art/studio_queue.py", "art/studio_txn.py",  # the admission path and its tokens
    "graybox/check.py", "graybox/tick_ref.py", "graybox/rules_ref.py", "graybox/bot_ref.py",  # the twins and references
    "tools/rung.py",                                                          # this classifier
    "AGENTS.md",                                                              # the rules every agent is given
)
WORDS = (".md",)
RUNG_ORDER = {"A": 0, "B": 1, "C": 2, "D?": 3, "D": 3}
DYNAMIC_CODE = ("import_module", "__import__", "exec", "eval", "run_path", "run_module")
NEEDS = {
    "A": ["a person reads the change (words: nothing runs them)"],
    "C": ["the program's own self-tests and the gate, run by the owner on his machine from the patch applied to the pushed tree",
          "a new behaviour of the language or the rules comes with its version bump and its twin (RULES, the art language), "
          "and with the frozen references of every brief frozen again by a person when the exporter's bytes move"],
    "D": ["admitted outside the candidate's authority: the owner applies it and runs the gate and the self-tests on his "
          "machine, and this classifier is run from the pushed tree, not from the patch",
          "independent evidence: every planted defect the old checker refused is refused by the new one "
          "(python tools/rung.py plants BASE HEAD), and every loosening named below is read and accepted by the owner",
          "the gate's row count and rowset as before, unless a registered property needs revision (his ruling)"],
}


# ------------------------------------------------------------------------------------------------ the trees
def git(repo, *a):
    r = subprocess.run(["git", "-C", repo] + list(a), capture_output=True)
    if r.returncode:
        raise SystemExit("git %s: %s" % (" ".join(a), r.stderr.decode("utf-8", "replace").strip()[:300]))
    return r.stdout


class Tree:
    """A tree's files, read through git (never the working folder): {path: bytes} on demand."""

    def __init__(self, repo, rev):
        self.repo, self.rev = repo, rev
        self.paths = set(p for p in git(repo, "ls-tree", "-r", "--name-only", rev).decode("utf-8").split("\n") if p)
        self._cache = {}
        self.names = {}
        for p in self.paths:
            self.names.setdefault(p.rsplit("/", 1)[-1], set()).add(p)

    def read(self, path):
        if path not in self._cache:
            self._cache[path] = git(self.repo, "show", "%s:%s" % (self.rev, path)) if path in self.paths else None
        return self._cache[path]


class MemTree:
    """A tree given as {path: bytes} (the self-test's)."""

    def __init__(self, files):
        self.files, self.paths = files, set(files)
        self.names = {}
        for p in self.paths:
            self.names.setdefault(p.rsplit("/", 1)[-1], set()).add(p)

    def read(self, path):
        return self.files.get(path)


# ------------------------------------------------------------------------------------------------ the closure
def _norm(p):
    parts = []
    for s in p.replace("\\", "/").split("/"):
        if s in ("", "."):
            continue
        if s == "..":
            if parts:
                parts.pop()
            continue
        parts.append(s)
    return "/".join(parts)


class Reader(ast.NodeVisitor):
    """One Python file read as source: what it imports, loads and names, and where it reads or loads by computed name."""

    def __init__(self, tree, path):
        self.tree, self.path = tree, path
        self.binds = {}                      # name -> set of resolved path strings
        self.dirs = {os.path.dirname(path)}  # where its imports are looked for
        self.code, self.data, self.mods = set(), set(), []
        self.dynamic, self.computed_reads = [], []

    def value(self, n):
        """The set of repository paths an expression may be ('' is the repository's root), or None if unknown."""
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            return {n.value}
        if isinstance(n, ast.Name):
            if n.id == "__file__":
                return {self.path}
            return self.binds.get(n.id)
        if isinstance(n, ast.Call):
            f = ast.unparse(n.func)
            if f in ("os.path.abspath", "os.path.normpath", "os.path.realpath") and n.args:
                return self.value(n.args[0])
            if f == "os.path.dirname" and n.args:
                v = self.value(n.args[0])
                return {os.path.dirname(_norm(x)) for x in v} if v else None
            if f == "os.path.join" and n.args:
                acc = {""}
                for a in n.args:
                    v = self.value(a)
                    if not v:
                        return None
                    acc = {_norm(x + "/" + y) if x else _norm(y) for x in acc for y in v}
                return acc
        return None

    def mention(self, p):
        """A resolved path: a tracked file, or a folder whose tracked files are all named by it."""
        p = _norm(p)
        if p in self.tree.paths:
            (self.code if p.endswith(".py") else self.data).add(p)
            return True
        pre = p + "/" if p else ""
        under = [q for q in self.tree.paths if pre and q.startswith(pre)]
        for q in under:
            self.data.add(q)
        return bool(under)

    def visit_Assign(self, n):
        v = self.value(n.value)
        for t in n.targets:
            if isinstance(t, ast.Name) and v:
                self.binds.setdefault(t.id, set()).update(v)
        self.generic_visit(n)

    def visit_Import(self, n):
        for a in n.names:
            self.mods.append(a.name)

    def visit_ImportFrom(self, n):
        if n.module and not n.level:
            self.mods.append(n.module)

    def visit_Expr(self, n):
        # a string standing alone as a statement is a docstring or a comment, not a use: not a mention
        if not (isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)):
            self.generic_visit(n)

    def visit_Constant(self, n):
        if isinstance(n.value, str) and 2 < len(n.value) < 300 and "\n" not in n.value:
            s = n.value.replace("\\", "/")
            if s in self.tree.paths:
                (self.code if s.endswith(".py") else self.data).add(s)
            elif "." in s and "/" not in s and s in self.tree.names:
                for q in self.tree.names[s]:
                    (self.code if q.endswith(".py") else self.data).add(q)

    def visit_Call(self, n):
        f = ast.unparse(n.func)
        if f in ("sys.path.insert", "sys.path.append") and n.args:
            v = self.value(n.args[-1])
            if v:
                self.dirs.update(_norm(x) for x in v)
        if f == "os.path.join":
            v = self.value(n)
            if v:
                for x in v:
                    self.mention(x)
        name = f.rsplit(".", 1)[-1]
        if name in DYNAMIC_CODE and n.args and not (isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)):
            self.dynamic.append("%s:%d %s(...)" % (self.path, n.lineno, f))
        if name in DYNAMIC_CODE and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str) and name in ("import_module", "__import__"):
            self.mods.append(n.args[0].value)
        if f in ("open", "io.open", "os.listdir", "os.walk", "os.scandir") and n.args and self.value(n.args[0]) is None:
            self.computed_reads.append("%s:%d %s(...)" % (self.path, n.lineno, f))
        self.generic_visit(n)

    def run(self, src):
        try:
            t = ast.parse(src)
        except SyntaxError as e:
            self.dynamic.append("%s: not Python this classifier can read (%s), so what it loads is unknown" % (self.path, e.msg))
            return self
        # bindings first, everywhere in the file (a name bound in a function counts too: the union of what it may be)
        for _ in range(3):
            for node in ast.walk(t):
                if isinstance(node, ast.Assign):
                    v = self.value(node.value)
                    for tg in node.targets:
                        if isinstance(tg, ast.Name) and v:
                            self.binds.setdefault(tg.id, set()).update(v)
        self.visit(t)
        for m in self.mods:
            rel = m.replace(".", "/")
            for d in sorted(self.dirs) + [""]:
                for cand in (_norm(d + "/" + rel + ".py"), _norm(d + "/" + rel + "/__init__.py")):
                    if cand in self.tree.paths:
                        self.code.add(cand)
        return self


def closure(tree, roots=ROOTS):
    """(files, why, dynamic, computed): the trusted base's files in this tree, each with the chain that brought it in."""
    why, todo = {}, []
    for r in roots:
        if r in tree.paths:
            why[r] = "a root (" + r + ")"
            todo.append(r)
    dynamic, computed = [], []
    seen = set()
    while todo:
        p = todo.pop()
        if p in seen or not p.endswith(".py"):
            continue
        seen.add(p)
        src = tree.read(p)
        if src is None:
            continue
        R = Reader(tree, p).run(src.decode("utf-8", "replace"))
        dynamic += R.dynamic
        computed += R.computed_reads
        for q in sorted(R.code | R.data):
            if q not in why:
                why[q] = "%s, by %s" % ("imported or run" if q in R.code else "named", p)
                if q.endswith(".py"):
                    todo.append(q)
    return set(why), why, dynamic, computed


# ------------------------------------------------------------------------------------------------ the semantics
def _const(src, name):
    try:
        t = ast.parse(src)
    except SyntaxError:
        return None
    for n in ast.walk(t):
        if isinstance(n, ast.Assign) and any(isinstance(x, ast.Name) and x.id == name for x in n.targets):
            try:
                return ast.literal_eval(n.value)
            except ValueError:
                return None
    return None


def loosenings(base, head):
    """Changes that make a checker accept more, named whatever the rung."""
    out = []

    def both(p):
        a, b = base.read(p), head.read(p)
        return (a.decode("utf-8", "replace") if a is not None else None, b.decode("utf-8", "replace") if b is not None else None)
    a, b = both("art/director/contract.py")
    if a and b:
        x, y = _const(a, "EXPECTED_CHECKS") or (), _const(b, "EXPECTED_CHECKS")
        if y is None:
            out.append("art/director/contract.py: EXPECTED_CHECKS is no longer a literal this classifier can read")
        elif set(x) - set(y):
            out.append("art/director/contract.py: checks dropped from EXPECTED_CHECKS: " + ", ".join(sorted(set(x) - set(y))))
    elif a and not b:
        out.append("art/director/contract.py removed")
    a, b = both("art/quality.py")
    if a and b:
        da, db = _const(a, "DETECT") or {}, _const(b, "DETECT") or {}
        for k, looser in (("white", lambda u, v: v > u), ("black", lambda u, v: v > u), ("clipped", lambda u, v: v > u),
                          ("flat", lambda u, v: v < u), ("near", lambda u, v: v > u)):
            if k in da and (k not in db or looser(da[k], db[k])):
                out.append("art/quality.py: the detector threshold %s made looser (%r -> %r)" % (k, da.get(k), db.get(k)))
        for k in ("BUDGET_BOXES", "BUDGET_BYTES", "F32_LIMIT", "WEBGL2_MIN_TEXTURE", "JS_SAFE"):
            u, v = _const(a, k), _const(b, k)
            if u is not None and (v is None or v > u):
                out.append("art/quality.py: %s raised or no longer a literal (%r -> %r)" % (k, u, v))
    a, b = base.read("art/references.jsonl"), head.read("art/references.jsonl")
    if a is not None and (b is None or not b.startswith(a)):
        out.append("art/references.jsonl: a frozen reference rewritten or removed (only appends are allowed)")
    a, b = base.read("art/director/vectors.json"), head.read("art/director/vectors.json")
    if a is not None and a != b:
        out.append("art/director/vectors.json changed: an expected output changed is a new protocol version, never a fix")
    pa = sum(len(re.findall(rb"plant", base.read(p) or b"")) for p in base.paths if p.endswith(".py"))
    pb = sum(len(re.findall(rb"plant", head.read(p) or b"")) for p in head.paths if p.endswith(".py"))
    if pb < pa:
        out.append("the word 'plant' appears %d times in the Python sources, %d before: planted defects may be fewer" % (pb, pa))
    return out


# ------------------------------------------------------------------------------------------------ the classification
def changed(repo, base, head):
    out = git(repo, "diff", "--no-renames", "--name-status", base, head).decode("utf-8").split("\n")
    return [(ln.split("\t")[0][0], ln.split("\t")[1]) for ln in out if ln.strip()]


def classify(base, head, files):
    """{file: (rung, why)}, the change's rung, the escalations, the loosenings. files: [(status, path)]."""
    cb, wb, db, rb = closure(base)
    ch, wh, dh, rh = closure(head)
    escal = sorted(set(db + dh)), sorted(set(rb + rh))
    res = {}
    for st, p in files:
        if p in ch or p in cb:
            res[p] = ("D", "in the trusted base: " + (wh.get(p) or wb.get(p)) + ("" if p in ch else " (as it was before this change)"))
        elif escal[0] and p.endswith(".py"):
            res[p] = ("D?", "escalated: the trusted base loads code by a computed name (%s), so this file may be part of it" % "; ".join(escal[0][:3]))
        elif escal[1] and not p.endswith(".py"):
            res[p] = ("D?", "escalated: the trusted base reads files by computed paths (%d place(s), e.g. %s), so this file may be one" % (
                len(escal[1]), "; ".join(escal[1][:2])))
        elif p.endswith(WORDS):
            res[p] = ("A", "words, outside the trusted base: nothing runs them")
        else:
            res[p] = ("C", "outside the trusted base, and not words: new behaviour")
    rung = max((r for r, _w in res.values()), key=lambda r: RUNG_ORDER[r]) if res else "A"
    return res, rung, escal, loosenings(base, head)


def report(res, rung, escal, loose, base_rev="BASE", head_rev="HEAD"):
    lines = ["RUNG-0  %s..%s: %d file(s) changed" % (base_rev, head_rev, len(res))]
    for p in sorted(res, key=lambda q: (-RUNG_ORDER[res[q][0]], q)):
        lines.append("  %-3s %s — %s" % (res[p][0], p, res[p][1]))
    if escal[0]:
        lines.append("  the trusted base loads code by a computed name at: " + "; ".join(escal[0]))
    if escal[1]:
        lines.append("  the trusted base reads files by computed paths at %d places (the first: %s)" % (len(escal[1]), "; ".join(escal[1][:4])))
    lines.append("THE CHANGE: rung %s (the highest of its files'; computed here, never taken from the patch's own words)" % rung)
    for n in NEEDS["D" if rung.startswith("D") else rung]:
        lines.append("  needs: " + n)
    if loose:
        for x in loose:
            lines.append("  LOOSENS: " + x)
    else:
        lines.append("  loosens nothing this classifier knows to look for (a dropped expected check, a looser detector or budget, "
                     "a rewritten reference, changed vectors, fewer plants)")
    lines.append("  not checked: whether the change is right; what a computed path or a computed import reaches; a loosening of a "
                 "kind not listed above")
    return "\n".join(lines)


# ------------------------------------------------------------------------------------------------ the plants (R5)
SUITES = (("art/quality.py", "selftest"), ("art/check.py",), ("art/director.py", "selftest"), ("art/studio.py", "selftest"))
PLANT_ROW = re.compile(r"^\[?(PASS|FAIL)\]? ?(plant: .*?)(?: — .*)?$")
# 0245: a bracketed row whose name names a plant ("[PASS] name — detail", as art/studio.py's self-test prints its rows:
# none of them opens "plant: ", so R5 read none of that suite's until 0245), and the world a row is printed under
# ("== NAME ...", art/check.py's header for each brief: its plants print the same words once per brief, and keyed
# without the brief's name the four briefs' rows were one, the last brief's verdict standing for all four)
NAMED_PLANT = re.compile(r"^\[(PASS|FAIL)\] (.*?\bplant\b.*?)(?: — .*)?$")
WORLD_HEAD = re.compile(r"^== (\S+)(?:\s|$)")


def suite_output(root, suite):
    """A suite's output, as UTF-8 whatever the console: the child is told to write UTF-8 (PYTHONUTF8, PYTHONIOENCODING)
    and is read as UTF-8. A Windows pipe is cp1252 by default, and a suite that prints what cp1252 cannot write stops
    there: art/check.py did, at its number-grammar plant (Arabic-Indic digits), so on the owner's machine R5 compared 22
    of its plant rows, its first brief's, not all of them, until 0242 (MEASURED by simulation in the container)."""
    r = subprocess.run([sys.executable, "-B"] + list(suite), cwd=root, capture_output=True,
                       env=dict(os.environ, PYTHONHASHSEED="0", PYTHONUTF8="1", PYTHONIOENCODING="utf-8"), timeout=1800)
    return r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace"), r.returncode


def crashed(err, rc=1):
    """The exception that ended a suite, or None: it ended with a non-zero status and its error output ends with a
    traceback (the frames, then the exception's own line). A traceback a suite logs and goes on from is not a stop
    (0244: STUDIO SELFTEST logs one when a request's thread fails, by design, and 0242's reading took it for a stop)."""
    lines = [ln for ln in err.rstrip().splitlines() if ln.strip()]
    at = [i for i, ln in enumerate(lines) if ln.startswith("Traceback (most recent call last)")]
    if rc == 0 or not at:
        return None
    tail = lines[at[-1] + 1:]
    frames = [ln for ln in tail if ln.startswith(" ")]
    last = tail[-1] if tail else ""
    if not frames or last.startswith(" ") or not re.match(r"[A-Za-z_][\w.]*(: |$)", last):
        return None
    return last[:200]


def plant_rows(root, broken=None):
    """Every planted-defect row of the suites in a checkout: {suite + row: passed}. A suite that raised is added to
    `broken` (suite, the error's last line)."""
    out = {}
    for suite in SUITES:
        if not os.path.exists(os.path.join(root, suite[0])):
            continue
        txt, err, rc = suite_output(root, suite)
        why = crashed(err, rc)
        if why and broken is not None:
            broken.append((" ".join(suite), why))
        out.update(parse_rows(" ".join(suite), txt))
    return out


def parse_rows(name, txt):
    """A suite's planted-defect rows, {name | [world |] words: passed}: a row opening "plant: ", or a bracketed row whose
    name names a plant; keyed by the world it is printed under, when the suite prints one (WORLD_HEAD). Two rows under
    one key are one row that passes only if both do: a later PASS never hides an earlier FAIL (0245)."""
    out, world = {}, ""
    for ln in txt.splitlines():
        s = ln.strip()
        w = WORLD_HEAD.match(s)
        if w:
            world = w.group(1)
            continue
        m = PLANT_ROW.match(s) or NAMED_PLANT.match(s)
        if m:
            k = name + " | " + (world + " | " if world else "") + m.group(2).strip()
            out[k] = out.get(k, True) and m.group(1) == "PASS"
    return out


def compare_plants(old, new):
    """(no longer refused, gone): of the planted defects the old checker refused."""
    lost = [k for k, ok in sorted(old.items()) if ok and k not in new]
    worse = [k for k, ok in sorted(old.items()) if ok and k in new and not new[k]]
    return worse, lost


def cmd_plants(repo, base, head):
    """R5: every planted defect the old checker refused, refused by the new one (by the row's words; a reworded row is
    listed as gone, for a person to read)."""
    rows, broken = {}, {base: [], head: []}
    tmp = tempfile.mkdtemp(prefix="rung-plants-")
    try:
        for rev in (base, head):
            wt = os.path.join(tmp, rev.replace("/", "_"))
            git(repo, "worktree", "add", "--detach", wt, rev)
            try:
                rows[rev] = plant_rows(wt, broken[rev])
            finally:
                git(repo, "worktree", "remove", "--force", wt)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    old, new = rows[base], rows[head]
    worse, lost = compare_plants(old, new)
    print("RUNG-0 PLANTS  %d planted defects refused by the old checker; %d by the new (%d rows)" % (
        sum(old.values()), sum(new.values()), len(new)))
    for k in worse:
        print("  NOW PASSES THROUGH: " + k)
    for k in lost:
        print("  GONE (or reworded; read it): " + k)
    for su, why in broken[base]:
        print("  THE OLD CHECKER STOPPED EARLY (its rows after were not compared): %s: %s" % (su, why))
    for su, why in broken[head]:
        print("  THE NEW CHECKER STOPPED EARLY (its rows after were never run): %s: %s" % (su, why))
    ok = not worse and not lost and not broken[head]
    print("PLANTS HELD" if ok else "PLANTS NOT HELD (%d no longer refused, %d gone%s)" % (
        len(worse), len(lost), ", %d suite(s) of the new checker stopped early" % len(broken[head]) if broken[head] else ""))
    return 0 if ok else 1


# ------------------------------------------------------------------------------------------------ the self-test
def cmd_selftest():
    rows = []

    def row(name, ok, detail=""):
        rows.append(bool(ok))
        print("%s %s%s" % ("PASS" if ok else "FAIL", name, (" — " + detail) if detail else ""))

    py = lambda s: s.encode("utf-8")
    base = {
        "art/check.py": py("import os, sys\nHERE = os.path.dirname(os.path.abspath(__file__))\nsys.path.insert(0, os.path.join(HERE, 'lib'))\n"
                           "import helper\nREFS = os.path.join(HERE, 'refs.jsonl')\nBRIEFS = os.path.join(HERE, 'briefs')\n"
                           "import importlib.util\n_s = importlib.util.spec_from_file_location('g', os.path.join(HERE, '..', 'graybox', 'gcheck.py'))\n"),
        "art/lib/helper.py": py("LIMIT = 3\n"),
        "art/refs.jsonl": b"{}\n",
        "art/briefs/a.art": b"VERDANDI-ART 0\n",
        "graybox/gcheck.py": py("import json\nNAME = 'sim.js'\n"),
        "graybox/web/sim.js": b"// rules\n",
        "art/feature.py": py("def f():\n    return 1\n"),
        "art/web/page.js": b"// a page\n",
        "docs/NOTES.md": b"# notes\n",
        "art/director/contract.py": py("EXPECTED_CHECKS = ('a', 'b', 'c')\n"),
        "art/quality.py": py("DETECT = {'white': 0.05, 'black': 0.95, 'clipped': 0.25, 'flat': 4, 'near': 250}\nBUDGET_BOXES = 4096\n"),
        "tools/rung.py": py("ROOTS = ()\n"),
        "AGENTS.md": b"# rules\n",
    }
    roots = ("art/check.py", "art/director/contract.py", "art/quality.py", "tools/rung.py", "AGENTS.md")

    def cls(head_files, files):
        b, h = MemTree(base), MemTree(head_files)
        global ROOTS
        saved = ROOTS
        ROOTS = roots
        try:
            return classify(b, h, files)
        finally:
            ROOTS = saved
    H = dict(base)
    res, rung, esc, loose = cls(H, [("M", "art/lib/helper.py")])
    row("a helper the checker imports through a folder it puts on sys.path is the checker's, as code (the file's name says nothing of it)",
        res["art/lib/helper.py"][0] == "D" and "imported or run" in res["art/lib/helper.py"][1], res["art/lib/helper.py"][1])
    res, rung, esc, loose = cls(H, [("M", "graybox/gcheck.py"), ("M", "graybox/web/sim.js")])
    row("a module loaded by spec_from_file_location, and the file it names by a literal, are the checker's",
        res["graybox/gcheck.py"][0] == "D" and res["graybox/web/sim.js"][0] == "D", res["graybox/web/sim.js"][1])
    res, rung, esc, loose = cls(H, [("M", "art/refs.jsonl"), ("M", "art/briefs/a.art")])
    row("data the checker names by os.path.join, a file or a whole folder, is the checker's", res["art/refs.jsonl"][0] == "D" and res["art/briefs/a.art"][0] == "D",
        res["art/briefs/a.art"][1])
    res, rung, esc, loose = cls(H, [("M", "art/feature.py"), ("M", "art/web/page.js"), ("M", "docs/NOTES.md")])
    row("code outside the trusted base is C, words are A, and the change is the highest of them (C)",
        (res["art/feature.py"][0], res["art/web/page.js"][0], res["docs/NOTES.md"][0], rung) == ("C", "C", "A", "C"))
    H2 = dict(H, **{"art/feature.py": py("import helper\n"), "art/check.py": base["art/check.py"] + py("import feature\n")})
    res, rung, esc, loose = cls(H2, [("M", "art/feature.py"), ("M", "art/check.py")])
    row("a file the change brings into the checker (now imported by it) is D, whatever it was", res["art/feature.py"][0] == "D", res["art/feature.py"][1])
    H3 = dict(H, **{"art/check.py": base["art/check.py"] + py("import importlib\nm = importlib.import_module(NAME)\n")})
    res, rung, esc, loose = cls(H3, [("M", "art/feature.py"), ("M", "docs/NOTES.md")])
    row("a checker that loads code by a computed name: every changed Python file escalates to D?, with the line that made it so",
        res["art/feature.py"][0] == "D?" and "art/check.py:" in res["art/feature.py"][1] and res["docs/NOTES.md"][0] == "A", res["art/feature.py"][1][:100])
    H4 = dict(H, **{"art/check.py": base["art/check.py"] + py("def r(p):\n    return open(p).read()\n")})
    res, rung, esc, loose = cls(H4, [("M", "docs/NOTES.md")])
    row("a checker that opens files by computed paths: a changed file of words escalates to D?", res["docs/NOTES.md"][0] == "D?", res["docs/NOTES.md"][1][:100])
    res, rung, esc, loose = cls({k: v for k, v in H.items() if k != "art/lib/helper.py"}, [("D", "art/lib/helper.py")])
    row("a checker's file removed is still the checker's (read in the tree before)", res["art/lib/helper.py"][0] == "D", res["art/lib/helper.py"][1])
    res, rung, esc, loose = cls(dict(H, **{"tools/rung.py": py("ROOTS = ('nothing',)\n")}), [("M", "tools/rung.py")])
    row("this classifier changed, its roots emptied: D (judged by the copy before it)", res["tools/rung.py"][0] == "D")
    res, rung, esc, loose = cls(dict(H, **{"AGENTS.md": b"# rules, loosened\n"}), [("M", "AGENTS.md")])
    row("the agents' rules changed: D, words though they are", res["AGENTS.md"][0] == "D")
    L = dict(H, **{"art/director/contract.py": py("EXPECTED_CHECKS = ('a', 'c')\n"),
                   "art/quality.py": py("DETECT = {'white': 0.5, 'black': 0.95, 'clipped': 0.25, 'flat': 4, 'near': 250}\nBUDGET_BOXES = 9000\n")})
    res, rung, esc, loose = cls(L, [("M", "art/director/contract.py"), ("M", "art/quality.py")])
    row("loosenings named: a check dropped from the expected list, a detector's threshold raised, a budget raised",
        any("dropped" in x and "b" in x for x in loose) and any("threshold white" in x for x in loose) and any("BUDGET_BOXES" in x for x in loose), "; ".join(loose)[:150])
    res, rung, esc, loose = cls(dict(H, **{"art/director/contract.py": py("EXPECTED_CHECKS = ('a', 'b', 'c', 'd')\n")}), [("M", "art/director/contract.py")])
    row("a check added to the expected list loosens nothing", not loose, "; ".join(loose))
    worse, lost = compare_plants({"s | plant: a": True, "s | plant: b": True, "s | plant: c": False}, {"s | plant: a": False, "s | plant: c": True, "s | plant: d": True})
    row("the plants compared: one the old checker refused and the new does not, one gone, are both said; new ones and one fixed are not held against it",
        worse == ["s | plant: a"] and lost == ["s | plant: b"], "no longer refused %s; gone %s" % (worse, lost))
    # 0242: a suite that prints what the console cannot write is read whole, and one that raises is said
    import tempfile as _t
    d = _t.mkdtemp(prefix="rung-enc-")
    try:
        open(os.path.join(d, "suite.py"), "w", encoding="utf-8").write(
            "print('PASS plant: one — refused')\nprint('PASS plant: two \\u0661\\u0660\\u0660 — refused')\nprint('PASS plant: three — refused')\n")
        saved = os.environ.get("PYTHONIOENCODING")
        os.environ["PYTHONIOENCODING"] = "cp1252"       # the owner's console, as a Windows pipe has it
        try:
            txt, err, rc = suite_output(d, ("suite.py",))
            r = subprocess.run([sys.executable, "-B", "suite.py"], cwd=d, capture_output=True, env=dict(os.environ, PYTHONUTF8="0"))
        finally:
            if saved is None:
                os.environ.pop("PYTHONIOENCODING", None)
            else:
                os.environ["PYTHONIOENCODING"] = saved
        got = [PLANT_ROW.match(ln).group(2) for ln in txt.splitlines() if PLANT_ROW.match(ln)]
        bare = crashed(r.stderr.decode("cp1252", "replace"), r.returncode)
        row("a suite printing what a cp1252 console cannot write is read whole; left to cp1252 it stops, and the stop is said",
            got == ["plant: one", "plant: two \u0661\u0660\u0660", "plant: three"] and not crashed(err, rc) and bare is not None and "UnicodeEncodeError" in bare,
            "read as UTF-8: %d of 3 rows; under cp1252: %s" % (len(got), bare))
        # 0244: a traceback a suite logs and goes on from is not a stop; one that ends it is
        open(os.path.join(d, "logs.py"), "w", encoding="utf-8").write(
            "import sys, traceback\ntry:\n    1 / 0\nexcept ZeroDivisionError:\n    sys.stderr.write(traceback.format_exc() + '-' * 40 + '\\n')\nprint('PASS plant: after — refused')\n")
        open(os.path.join(d, "dies.py"), "w", encoding="utf-8").write("print('PASS plant: before — refused')\n1 / 0\n")
        t1, e1, r1 = suite_output(d, ("logs.py",))
        t2, e2, r2 = suite_output(d, ("dies.py",))
        row("a traceback a suite logs and goes on from is not a stop; an exception that ends it is", crashed(e1, r1) is None and "plant: after" in t1
            and (crashed(e2, r2) or "").startswith("ZeroDivisionError"), "logged: %s; ended: %s" % (crashed(e1, r1), crashed(e2, r2)))
    finally:
        import shutil as _sh
        _sh.rmtree(d, ignore_errors=True)
    # 0245: art/check.py's rows keyed by the world they are printed under, and art/studio.py's bracketed rows that name a plant
    two = "== harbor-day   scene x\nPASS plant: a canopy — refused\n== plaza-night   scene y\nPASS plant: a canopy — refused\n"
    two_new = two.replace("PASS plant: a canopy — refused\n== plaza-night", "FAIL plant: a canopy — passed\n== plaza-night", 1)
    old_r, new_r = parse_rows("art/check.py", two), parse_rows("art/check.py", two_new)
    worse, lost = compare_plants(old_r, new_r)
    flat = lambda txt: {"c | " + PLANT_ROW.match(ln).group(2): PLANT_ROW.match(ln).group(1) == "PASS" for ln in txt.splitlines() if PLANT_ROW.match(ln)}
    w0, l0 = compare_plants(flat(two), flat(two_new))
    row("a plant no longer refused in one world of several is said: rows are keyed by the world they are printed under (0245); keyed "
        "without it, the last world's verdict stands for all and it is missed", len(old_r) == 2 and worse == ["art/check.py | harbor-day | plant: a canopy"]
        and not lost and not w0 and not l0, "keyed by world: %s; without: %d row, nothing said" % (worse, len(flat(two))))
    st = parse_rows("art/studio.py selftest", "[PASS] two at once: the console kept (plant: no lock leaves it redirected) — ok\n"
                    "[PASS] a refusal after the body (a still); plant, no draining: the answer comes first — ok\n"
                    "[PASS] three candidates drawn — ok\n[FAIL] planted bays refused — 7 of 8\n")
    row("a bracketed row that names a plant is read (art/studio.py's form, 0245); one that names none, or says 'planted', is not", sorted(st) == [
        "art/studio.py selftest | a refusal after the body (a still); plant, no draining: the answer comes first",
        "art/studio.py selftest | two at once: the console kept (plant: no lock leaves it redirected)"], "; ".join(sorted(st))[:150])
    twice = parse_rows("s", "FAIL plant: one — not refused\nPASS plant: one — refused\n")
    row("a plant printed twice under one key keeps its FAIL: the rows are combined, never one overwritten by the other (0245)",
        twice == {"s | plant: one": False}, repr(twice))
    m = PLANT_ROW.match("[PASS] plant: a still taken away — refused — LEDGER-STILL: #19")
    row("a plant row is read from a suite's line, its words without the detail", bool(m) and m.group(1) == "PASS" and m.group(2) == "plant: a still taken away", m.group(2) if m else "")
    msgless = report(*cls(H, [("M", "art/feature.py")]))
    row("the report reads no commit message: the same files give the same rung whatever the patch says of itself",
        "THE CHANGE: rung C" in msgless and "needs:" in msgless)
    # against this repository's own tree, through git: the checker's files are D, the roadmap escalated or A
    try:
        t = Tree(REPO, "HEAD")
        c, why, dyn, comp = closure(t)
        row("this repository at HEAD: the director, QUALITY-0, the exporter, the renderer and the frozen references are in the closure",
            all(p in c for p in ("art/director.py", "art/quality.py", "art/dress.py", "art/web/scene_render.js", "art/references.jsonl")),
            "%d files; art/dress.py: %s; scene_render.js: %s" % (len(c), why.get("art/dress.py"), why.get("art/web/scene_render.js")))
        row("  and the computed imports and reads that escalate the rest are listed (%d and %d)" % (len(dyn), len(comp)), len(dyn) > 0 and len(comp) > 0,
            "; ".join(dyn[:2]))
    except SystemExit as e:
        row("this repository at HEAD read through git", False, str(e)[:120])
    n, k = len(rows), sum(rows)
    print("RUNG SELFTEST %d/%d" % (k, n))
    return 0 if k == n else 1


def main(argv):
    if not argv:
        print(open(__file__, encoding="utf-8").read().split("\n\n")[0])
        return 2
    repo = REPO
    if "--repo" in argv:
        i = argv.index("--repo")
        repo = os.path.abspath(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    cmd = argv[0]
    if cmd == "selftest":
        return cmd_selftest()
    if cmd == "classify" and len(argv) == 3:
        base, head = argv[1], argv[2]
        res, rung, esc, loose = classify(Tree(repo, base), Tree(repo, head), changed(repo, base, head))
        print(report(res, rung, esc, loose, base, head))
        return 0
    if cmd == "plants" and len(argv) == 3:
        return cmd_plants(repo, argv[1], argv[2])
    print("python tools/rung.py classify BASE HEAD | plants BASE HEAD | selftest   [--repo DIR]")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
