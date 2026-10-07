#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""design/test_design.py — the design tool's own checks. Content time: this is not a row of the gate.

    python design/test_design.py

It drives design.py the way a person, a script or a model would, in a scratch project, against a real shell (the
one the gate built, or one it builds here). Each check plants what it claims to catch.

Two of DESIGN-IR/DIFF-0a's named parts live here and nowhere on the gate, because nothing under verify/ reads this
folder and the tool is not certified: DESIGN-IR/CLIENT-FENCE-0 (the tool is a client of the shell's compiler: design.py
to the compiler to the batch, and never design.py to the batch), with four plants that are changed copies of the tool;
and the tool's side of DESIGN-IR/ROUNDTRIP-0 (what `inspect` shows after an admission is the designed grid).
"""
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import design  # noqa: E402

RESULTS = []
TEXT = "VERDANDI-DESIGN 0\n"
TOOL = os.path.join(HERE, "design.py")


def run(proj, *argv, text=None):
    """One run of the tool as a program. The design text goes to it as bytes, LF line ends, on every platform."""
    env = dict(os.environ, VERDANDI_DESIGN=proj)
    cp = subprocess.run([sys.executable, "-B", TOOL] + list(argv), capture_output=True, input=None if text is None else text.encode("utf-8"), env=env)
    return cp.returncode, (cp.stdout + cp.stderr).decode("utf-8", "replace").replace("\r\n", "\n")


def check(name, fn):
    try:
        said = fn()
        RESULTS.append(("PASS", name, said or ""))
    except AssertionError as e:
        RESULTS.append(("FAIL", name, str(e)))
    print("[%s] %s %s" % RESULTS[-1])


def status(proj):
    return json.loads(run(proj, "status", "--json")[1])


def sessions(proj):
    d = os.path.join(proj, "sessions")
    return sorted(os.listdir(d)) if os.path.isdir(d) else []


def compiler(shell, proj, session, data: bytes):
    """The shell's compiler asked directly, beside the tool: (exit, the bytes it wrote, its first coded line)."""
    path = os.path.join(proj, "beside.design")
    with open(path, "wb") as fh:
        fh.write(data)
    env = dict(os.environ, VERDANDI_SESSIONS=os.path.join(proj, "sessions"), VERDANDI_REFUSAL_LOG=os.path.join(proj, "beside-refusals.log"),
               VERDANDI_RUN_LEDGER=os.path.join(proj, "beside-runs.log"))
    cp = subprocess.run([shell, "design-compile", "--session", session, "--design", path], capture_output=True, cwd=ROOT, env=env)
    return cp.returncode, cp.stdout, (cp.stderr.decode("utf-8", "replace").strip().splitlines() or [""])[0]


# ------------------------------------------------------------------ DESIGN-IR/CLIENT-FENCE-0: the tool held as a client
class Spy:
    """Stands where the tool's `subprocess` stands, in a copy of the tool loaded in this process. Every run goes to the
    real shell and is written down. With `stand_in`, the compiler's answer is replaced by another batch: the same header
    with the last operation left out. A tool that proposes what it is handed proposes that one."""

    PIPE, DEVNULL, STDOUT = subprocess.PIPE, subprocess.DEVNULL, subprocess.STDOUT

    def __init__(self, stand_in=False):
        self.calls, self.stand_in, self.handed, self.wrote = [], stand_in, [], []

    def run(self, argv, **kw):
        self.calls.append(list(argv))
        cp = subprocess.run(argv, **kw)
        if len(argv) > 1 and argv[1] == "design-compile":
            self.handed.append(open(argv[argv.index("--design") + 1], "rb").read())
            if self.stand_in and cp.returncode == 0:
                lines = cp.stdout.split(b"\n")
                n = int(lines[5].split(b"=")[1])
                lines[5] = b"operations=%d" % (n - 1)
                cp = subprocess.CompletedProcess(argv, 0, b"\n".join(lines[:-2] + [b""]), cp.stderr)
            self.wrote.append(cp.stdout)
        return cp


def load_tool(source: str, spy: Spy):
    """A copy of the tool, from its source text, with the spy where its subprocess is."""
    mod = types.ModuleType("design_under_test")
    mod.__file__ = TOOL
    exec(compile(source, TOOL, "exec"), mod.__dict__)
    mod.subprocess = spy
    return mod


def call(mod, proj, *argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.main(["design.py"] + list(argv) + ["--project", proj])
    return rc, buf.getvalue()


# two single cells: a tool that nets single cells for itself writes, for this design, the very bytes the compiler writes
FENCE_DESIGN = (TEXT + "# the fence's design\nclose 27,28\nopen 20,27\n").encode("ascii")


def client_fence(source: str, shell: str, tmp: str, tag: str) -> list:
    """What does not hold of a tool given by its source. An empty list: the tool is a client of the shell's compiler."""
    wrong = []
    # (a) the batch the tool hands on is byte for byte what the compiler wrote for that design and that session
    proj = os.path.join(tmp, "fence-%s-a" % tag)
    spy = Spy()
    mod = load_tool(source, spy)
    rc, out = call(mod, proj, "new", "--shell", shell)
    assert rc == 0, out
    session = json.load(open(os.path.join(proj, "project.json")))["history"][-1]["session"]
    text = os.path.join(tmp, "fence-%s.design" % tag)
    with open(text, "wb") as fh:
        fh.write(FENCE_DESIGN)
    rc, out = call(mod, proj, "propose", text)
    _c, beside, _e = compiler(shell, proj, session, FENCE_DESIGN)
    pending = os.path.join(proj, "pending.vrdnp2")
    got = open(pending, "rb").read() if os.path.exists(pending) else b""
    if rc != 0 or not beside or got != beside:
        wrong.append("the pending batch is not the bytes the shell's compiler writes for the design")
    compiles = [c for c in spy.calls if len(c) > 1 and c[1] == "design-compile"]
    if len(compiles) != 1 or spy.handed != [FENCE_DESIGN]:
        wrong.append("the tool did not hand the design's bytes, exactly, to the compiler once")
    kept = os.path.join(proj, "designs", design.sha256(FENCE_DESIGN) + ".design")
    if not os.path.exists(kept) or open(kept, "rb").read() != FENCE_DESIGN:
        wrong.append("the design's bytes are not kept under their id")
    # (b) with a stand-in compiler that writes something else, the tool proposes what the stand-in wrote
    proj = os.path.join(tmp, "fence-%s-b" % tag)
    spy = Spy(stand_in=True)
    mod = load_tool(source, spy)
    rc, out = call(mod, proj, "new", "--shell", shell)
    assert rc == 0, out
    rc, out = call(mod, proj, "propose", text)
    pending = os.path.join(proj, "pending.vrdnp2")
    got = open(pending, "rb").read() if os.path.exists(pending) else b""
    if rc != 0 or len(spy.wrote) != 1 or got != spy.wrote[0] or got == beside:
        wrong.append("with a stand-in compiler, the tool does not propose what the stand-in wrote")
    # (c) an admit is bound to its preview: bytes changed after the preview are not admitted
    proj = os.path.join(tmp, "fence-%s-c" % tag)
    spy = Spy()
    mod = load_tool(source, spy)
    rc, out = call(mod, proj, "new", "--shell", shell)
    assert rc == 0, out
    call(mod, proj, "grant", "--cells", "0,0,47,31")
    head0 = json.load(open(os.path.join(proj, "project.json")))["history"][-1]["head"]
    rc, out = call(mod, proj, "propose", text)
    rc, out = call(mod, proj, "preview")
    pending = os.path.join(proj, "pending.vrdnp2")
    if rc == 0 and os.path.exists(pending):
        raw = open(pending, "rb").read()
        with open(pending, "wb") as fh:   # the same count and the same form, another cell
            fh.write(raw.replace(b"close 27,28\n", b"close 26,28\n"))
        rc, out = call(mod, proj, "admit")
        if rc != 2 or "SHELL-ADMIT-PREVIEW" not in out or json.load(open(os.path.join(proj, "project.json")))["history"][-1]["head"] != head0:
            wrong.append("bytes changed after the preview were not refused by the shell's binding")
    else:
        wrong.append("the design could not be previewed")
    # (d) by source: no writer of the batch language and no netting
    import ast
    tree = ast.parse(source)
    writer = re.compile(r"(^|\n)(VRDNP2\n|renderer=|bearing=|proposal=|operations=)")
    written = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, (str, bytes)):
            v = n.value if isinstance(n.value, str) else n.value.decode("latin-1")
            if v == "VRDNP2" or writer.search(v):
                written.add(n.lineno)
        if isinstance(n, ast.FunctionDef) and n.name in ("compile_design", "parse_design", "canonical", "batch_bytes"):
            wrong.append("the source holds %s" % n.name)
    if written:
        wrong.append("the source holds a line of the batch language to write (%d place%s)" % (len(written), "" if len(written) == 1 else "s"))
    if source.count('"design-compile"') != 1 or "def compile_with_shell(" not in source:
        wrong.append("the source does not reach the compiler in exactly one place")
    return wrong


def plant(source: str, old: str, new: str) -> str:
    assert source.count(old) == 1, "the plant's place is not in the tool once: %r" % old[:60]
    return source.replace(old, new)


def planted_tools(source: str) -> list:
    """Four changed copies of the tool, each one way of not being a client."""
    head = "def compile_with_shell(prj: dict, session: str, data: bytes) -> tuple:\n"
    own = head + '''    # PLANT: the tool calls the compiler, sets its answer aside, computes its own difference for single cells and
    # writes its own batch. For the fence's design those are the compiler's bytes: only a stand-in compiler tells them apart.
    compile_with_shell_set_aside(prj, session, data)
    w, a, ops = World(session), anchor(prj, session), []
    for ln in data.decode("ascii").splitlines()[1:]:
        t = ln.split("#")[0].split()
        if len(t) == 2 and t[0] in ("open", "close") and "," in t[1]:
            x, z = (int(v) for v in t[1].split(","))
            if chr(w.at(x, z)) != ("." if t[0] == "open" else "#"):
                ops.append((z, x, t[0]))
    lines = ["VRDNP2", "renderer=" + a["renderer"], "bearing=" + a["bearing"], "parent=" + a["parent"], "proposal=" + sha256(data), "operations=%d" % len(ops)]
    return ("\\n".join(lines + ["%s %d,%d" % (v, x, z) for z, x, v in sorted(ops)]) + "\\n").encode("ascii"), None


def compile_with_shell_set_aside(prj: dict, session: str, data: bytes) -> tuple:
'''
    never = head + '''    # PLANT: the tool never calls the compiler: it answers with a batch of its own keeping
    a = anchor(prj, session)
    said = [b"VRDNP2", b"renderer=" + a["renderer"].encode(), b"bearing=" + a["bearing"].encode(), b"parent=" + a["parent"].encode()]
    return b"\\n".join(said + [b"proposal=" + sha256(data).encode(), b"operations=1", b"close 27,28", b""]), None


def compile_with_shell_unused(prj: dict, session: str, data: bytes) -> tuple:
'''
    return [
        ("computes its own difference", plant(source, head, own)),
        ("rewrites the compiler's result", plant(source, "    return cp.stdout, None\n",
                                                 "    lines = cp.stdout.split(b\"\\n\")   # PLANT: the tool reorders what the compiler wrote\n"
                                                 "    return b\"\\n\".join(lines[:6] + lines[6:-1][::-1] + [b\"\"]), None\n")),
        ("never calls the compiler", plant(source, head, never)),
        ("admits without the preview's binding", plant(source, 'batch_file(prj), "--previewed", bound] + grant_args(prj))', 'batch_file(prj)] + grant_args(prj))')),
    ]


def main():
    tmp = tempfile.mkdtemp(prefix="verdandi-design-")
    proj = os.path.join(tmp, "p")
    try:
        shell = design.find_shell(None, tmp)
    except design.Refused as r:
        print("[SKIP] no shell: %s" % r)
        return 0
    rc, out = run(proj, "new", "--shell", shell)
    assert rc == 0, out
    head0 = status(proj)["head"]
    session0 = status(proj)["session"]

    def t_inspect():
        rc, out = run(proj, "inspect", "--json")
        d = json.loads(out)
        assert rc == 0 and d["session"]["head"] == head0 and d["world"]["width"] == 48 and d["world"]["rows"] == 32, out[:200]
        assert d["readings"]["floor_not_reachable"] == 0 and d["world"]["camera"].startswith("28,28"), d["readings"]
        assert d["project"]["compiler"] == "shell design-compile" and d["capabilities"]["limits"] == {"bytes": 16384, "statements": 64, "operations": 4096}, d["project"]
        return "the project's identities, head, world and readings are reported; the world is 48 x 32; the compiler named is the shell's"
    check("inspect", t_inspect)

    def t_language():
        bad = {"no version line": ("open 3,3\n", "SHELL-COMPILE-PARSE: line 1: "), "an unknown statement": (TEXT + "dig 3,3\n", "SHELL-COMPILE-PARSE: line 2: "),
               "a cell that is not x,z": (TEXT + "open 3;3\n", "SHELL-COMPILE-PARSE: line 2: "), "a leading zero": (TEXT + "open 03,3\n", "SHELL-COMPILE-PARSE: line 2: "),
               "a cell outside the level": (TEXT + "open 48,3\n", "SHELL-COMPILE-RANGE: line 2: "), "a room with no inside": (TEXT + "room 3,3 4,9\n", "SHELL-COMPILE-RANGE: line 2: "),
               "a colour above 255": (TEXT + "paint floor 256,0,0\n", "SHELL-COMPILE-PARSE: line 2: "), "an unknown class": (TEXT + "paint roof 1,2,3\n", "SHELL-COMPILE-PARSE: line 2: "),
               "nothing at all": (TEXT + "# only a comment\n", "SHELL-COMPILE-PARSE: line 2: "),
               "opening the border": (TEXT + "open 0,5\n", "SHELL-COMPILE-BORDER: line 2: "), "writing over a stair": (TEXT + "close 7,26\n", "SHELL-COMPILE-STAIR: line 2: "),
               "closing the camera's cell": (TEXT + "close 28,28\n", "SHELL-COMPILE-CAMERA: "), "a design that changes nothing": (TEXT + "open 27,27\nclose 27,27\n", "SHELL-COMPILE-EMPTY: ")}
        for what, (text, code) in bad.items():
            rc, out = run(proj, "propose", "-", text=text)
            assert rc == 2 and ("COMPILER  the shell refuses the design: " + code) in out, "%s was not refused by the shell's compiler with %s: %s" % (what, code, out[:160])
            assert status(proj)["pending"] is None and not os.path.exists(os.path.join(proj, "pending.vrdnp2")), "%s left a proposal behind" % what
        return "%d design texts the language does not take are each refused by the shell's compiler, with its code and the line, and leave no proposal" % len(bad)
    check("what the language refuses, the shell's compiler refuses", t_language)

    def t_grant():
        run(proj, "grant", "--cells", "20,20,30,29", "--classes", "floor")
        rc, out = run(proj, "propose", "-", text=TEXT + "open 3,10\n")
        assert rc == 0, out
        rc, out = run(proj, "preview")
        assert rc == 2 and "SHELL-ADMIT-CAPABILITY" in out, out[-300:]
        rc, out = run(proj, "propose", "-", text=TEXT + "paint wall0 1,2,3\n")
        rc, out = run(proj, "preview")
        assert rc == 2 and "SHELL-ADMIT-CAPABILITY" in out, out[-300:]
        rc, out = run(proj, "admit")
        assert rc == 2 and out.startswith("DESIGN-NOT-ADMISSIBLE") and status(proj)["head"] == head0, out
        run(proj, "reject")
        return "a cell outside the granted rectangle and a class outside the granted set compile, and are refused by the admission (ADMIT-CAPABILITY)"
    check("a proposer does less than its grant", t_grant)

    design_a = TEXT + "room 22,21 26,25\nentrance 24,25\npaint floor 60,70,90\n"

    def t_preview_is_not_authority():
        rc, out = run(proj, "propose", "-", text=design_a)
        assert rc == 0 and "11 operation(s): 6 cell(s) open, 4 close, 1 class(es) painted" in out, out
        before = sessions(proj)
        rc, out = run(proj, "preview", "--json")
        d = json.loads(out)
        assert rc == 0 and d["ok"] and d["operations"] == 11 and d["proposed_head"] != head0 and len(d["digest"]) == 64, out[:300]
        assert d["design"] == design.sha256(design_a.encode("ascii")), "the proposal's id is not the SHA-256 of the design's bytes"
        assert sessions(proj) == before and status(proj)["head"] == head0, "a preview changed the project's sessions or its head"
        assert not os.path.exists(os.path.join(proj, "preview")), "a preview left a scratch root behind"
        assert d["readings"]["proposed"]["floor_cells"] == d["readings"]["current"]["floor_cells"] + 6 - 4, d["readings"]
        rc2, out2 = run(proj, "preview", "--json")
        assert json.loads(out2)["proposed_head"] == d["proposed_head"] and sessions(proj) == before, "a second preview differs, or wrote a session"
        return "a preview is the shell's dry run of the %d operations: it names the head they would give and writes no session" % d["operations"]
    check("a preview is state, not authority", t_preview_is_not_authority)

    def t_admit():
        previewed = status(proj)["pending"]["preview"]["head"]
        rc, out = run(proj, "admit")
        st = status(proj)
        assert rc == 0 and st["head"] == previewed != head0 and st["pending"] is None and st["steps_back_available"] == 1, out
        doc = design.savedform.read_file(st["session"])
        edits = [e for e in doc["data"]["log"] if e["kind"] == "edit"]
        assert len(edits) == 11 and all("admit" in e and e["admit"]["language"] == "VRDNP2" for e in edits), "an admitted edit carries no envelope"
        assert [e["admit"]["place"] for e in edits] == [str(k) for k in range(1, 12)] and {e["admit"]["count"] for e in edits} == {"11"}, "the places are not 1 to 11 of 11"
        assert len({e["admit"]["proposal"] for e in edits}) == 1 and len({e["admit"]["digest"] for e in edits}) == 1, "the eleven edits are not one batch"
        assert edits[-1]["admit"]["head"] == previewed and "cells=20,20,30,29" in edits[0]["admit"]["grant"], edits[-1]["admit"]
        assert len(sessions(proj)) == 2, "one design made more than one session"
        kept = os.path.join(proj, "batches", previewed + ".vrdnp2")
        assert design.sha256(open(kept, "rb").read()) == edits[0]["admit"]["digest"], "the kept batch is not the bytes the envelope names"
        # the chain: exact design bytes, their digest, the proposal id, the envelope
        did = edits[0]["admit"]["proposal"]
        text = open(os.path.join(proj, "designs", did + ".design"), "rb").read()
        assert text == design_a.encode("ascii") and design.sha256(text) == did, "the design kept under the envelope's id is not the bytes that were proposed"
        rc_, beside, _e = compiler(shell, proj, session0, text)
        assert rc_ == 0 and beside == open(kept, "rb").read(), "the admitted batch is not what the shell's compiler writes for the kept design"
        return "one admission, one new session: 11 ordinary edits at places 1 to 11 of one batch; the admitted head is the previewed head; the envelope's id is the digest of the design kept"
    check("admit is the previewed proposal, byte for byte", t_admit)

    def t_roundtrip():
        # DESIGN-IR/ROUNDTRIP-0, the tool's side: what inspect shows after the admission is the designed grid, typed here by hand
        rc, out = run(proj, "inspect", "--region", "22,21,26,25", "--json")
        d = json.loads(out)
        want = ["#####", "#...#", "#...#", "#...#", "##.##"]
        got = [row[5:] for row in d["top_view"][2:]]
        assert rc == 0 and got == want, "inspect shows %r for the room, and %r was designed" % (got, want)
        assert d["world"]["tile_classes"]["floor"] == [60, 70, 90] and d["session"]["admitted_edits"] == 11, d["world"]["tile_classes"]
        return "after the admission, inspect shows the room's rim, its inside, its entrance and the floor's colour as the design said them"
    check("design, compile, batch, admit, world, inspect", t_roundtrip)

    def t_stale_and_changed():
        head1 = status(proj)["head"]
        rc, out = run(proj, "propose", "-", text=TEXT + "open 27,27\n")
        rc, out = run(proj, "preview")
        assert rc == 0, out
        # the previewed bytes are changed on disk before the admit: the shell, not this tool, refuses them
        prj = json.load(open(os.path.join(proj, "project.json")))
        p = os.path.join(proj, "pending.vrdnp2")
        raw = open(p, "rb").read()
        assert b"open 27,27\n" in raw
        open(p, "wb").write(raw.replace(b"open 27,27\n", b"open 26,27\n"))
        rc, out = run(proj, "admit")
        assert rc == 2 and "SHELL-ADMIT-PREVIEW" in out and status(proj)["head"] == head1, out
        rc, out = run(proj, "preview")
        assert rc == 2 and out.startswith("DESIGN-STALE"), "a pending batch that is not the compiler's bytes was previewed: " + out[:160]
        open(p, "wb").write(raw)
        # the project moves on (an undo) while the proposal waits: it is stale
        run(proj, "undo")
        prj2 = json.load(open(os.path.join(proj, "project.json")))
        assert prj2["pending"] is None and status(proj)["head"] == head0, "an undo left a proposal against another head"
        prj["history"] = prj2["history"]
        json.dump(prj, open(os.path.join(proj, "project.json"), "w"))
        rc, out = run(proj, "admit")
        assert rc == 2 and out.startswith("DESIGN-STALE"), out
        run(proj, "reject")
        return "bytes that are not the previewed ones are refused by the shell (ADMIT-PREVIEW); a proposal against a head the project has left is refused"
    check("what is admitted is what was previewed, against the head it was made for", t_stale_and_changed)

    def t_undo():
        st = status(proj)
        assert st["head"] == head0 and st["steps_back_available"] == 0
        kept = [s for s in sessions(proj)]
        assert len(kept) == 2, "the session the project stepped back from is gone (%d)" % len(kept)
        rc, out = run(proj, "undo")
        assert rc == 2 and out.startswith("DESIGN-NOTHING"), out
        rc, out = run(proj, "propose", "-", text=design_a)
        rc, out = run(proj, "preview", "--json")
        assert rc == 0 and json.loads(out)["ok"], out[:200]
        run(proj, "reject")
        return "after an undo the project stands at the earlier head, every session is still on disk, and the same design can be proposed again"
    check("undo steps back and deletes nothing", t_undo)

    def t_net_difference():
        rc, out = run(proj, "propose", "-", text=TEXT + "close 21,28 23,28\nopen 21,28 23,28\nclose 22,28\n")
        assert rc == 0 and "1 operation(s)" in out, out
        lines = open(os.path.join(proj, "pending.vrdnp2"), "rb").read().decode("ascii").split("\n")[6:-1]
        assert lines == ["close 22,28"], lines
        run(proj, "reject")
        return "three statements over one row compile to the single cell that differs"
    check("the smallest operation set", t_net_difference)

    def t_one_change_set():
        # overlapping rectangles, a repeat and a statement undone, in two different orders: one change set, two designs
        a = TEXT + "open 21,22 25,24\nclose 23,22 27,23\nopen 26,23\nclose 26,23\npaint floor 1,2,3\npaint wall0 9,9,9\n"
        b = TEXT + "paint wall0 9,9,9\nopen 21,22 22,24\nopen 23,24 25,24\nclose 23,22 27,23\npaint floor 1,2,3\npaint floor 1,2,3\n"
        run(proj, "grant", "--cells", "20,20,30,29", "--classes", "wall0,floor")
        raws = []
        for text in (a, b):
            rc, out = run(proj, "propose", "-", text=text)
            assert rc == 0, out
            raws.append(open(os.path.join(proj, "pending.vrdnp2"), "rb").read().decode("ascii").split("\n"))
        assert raws[0][6:] == raws[1][6:] and raws[0][:4] == raws[1][:4], "two texts with one net difference compiled to two change sets"
        assert [r[4] for r in raws] == ["proposal=" + design.sha256(t.encode("ascii")) for t in (a, b)] and raws[0][4] != raws[1][4], "each text does not carry its own digest as its id"
        assert raws[1][-3:-1] == ["paint wall0 592137", "paint floor 66051"], raws[1][-3:]
        rc, out = run(proj, "preview", "--json")
        assert rc == 0 and json.loads(out)["ok"], out[:300]
        run(proj, "reject")
        return "two texts with one net difference compile to the same operations in the same order, each under the digest of its own bytes"
    check("one change set, two designs", t_one_change_set)

    def t_many_statements():
        text = TEXT + "".join("open %d,%d\n" % (21 + k % 8, 21 + k // 8) for k in range(64))
        rc, out = run(proj, "propose", "-", text=text)
        assert rc == 0 and "operation(s)" in out, out
        rc, out = run(proj, "propose", "-", text=text + "open 21,21\n")
        assert rc == 2 and "SHELL-COMPILE-SIZE: line 66: " in out, out[:160]
        assert status(proj)["pending"] is None, "a refused design left the earlier proposal standing"
        return "64 statements are taken and compile to one batch; a 65th is refused by the compiler (COMPILE-SIZE, naming its line)"
    check("the bound on a design text", t_many_statements)

    def t_twice():
        # the session's own rule: the same design bytes are admitted at most once in a history
        run(proj, "grant", "--cells", "0,0,47,31", "--classes", "floor")
        shut, back = TEXT + "close 27,28\n", TEXT + "open 27,28\n"
        for text in (shut, back):
            assert run(proj, "propose", "-", text=text)[0] == 0 and run(proj, "preview")[0] == 0 and run(proj, "admit")[0] == 0, "the two designs were not admitted"
        rc, out = run(proj, "propose", "-", text=shut)
        assert rc == 0, out
        rc, out = run(proj, "preview")
        assert rc == 2 and "SHELL-ADMIT-DUPLICATE" in out, out[-240:]
        rc, out = run(proj, "propose", "-", text=shut + "# again\n")
        rc, out = run(proj, "preview")
        assert rc == 0, out[-240:]
        run(proj, "reject")
        return "the same design bytes offered again in one history are refused by the admission (ADMIT-DUPLICATE); with one more comment line they are another design"
    check("the same design bytes, twice in one history", t_twice)

    source = open(TOOL, encoding="utf-8").read()

    def t_client():
        wrong = client_fence(source, shell, tmp, "tool")
        assert not wrong, "; ".join(wrong)
        return ("the pending batch is byte for byte what shell design-compile writes for the design and the session; the design's bytes go to the compiler exactly, "
                "once, and are kept under their id; with a stand-in compiler the tool proposes what the stand-in wrote; bytes changed after a preview are refused "
                "by the shell's binding; the source holds no line of the batch language to write and reaches the compiler in one place")
    check("the tool is a client of the shell's compiler", t_client)

    for k, (what, changed) in enumerate(planted_tools(source)):
        def t_plant(what=what, changed=changed, k=k):
            wrong = client_fence(changed, shell, tmp, "plant%d" % k)
            assert wrong, "a tool that %s passed every check of the fence" % what
            return "caught: " + "; ".join(wrong)
        check("PLANT, a tool that %s" % what, t_plant)

    shutil.rmtree(tmp, ignore_errors=True)
    bad = [r for r in RESULTS if r[0] != "PASS"]
    print("DESIGN TOOL %s  %d checks / %d fail   (content time: not a row of the gate)" % ("FAILED" if bad else "PASSED", len(RESULTS), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
