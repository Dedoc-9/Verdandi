#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""design/design.py — the design surface: inspect, propose, preview, admit, undo.

CONTENT TIME. This tool is not part of the gate and no gate runs when it is used. It holds no authority and it
computes no change set. It is a client of two certified commands of the shell: `shell design-compile` (DESIGN-IR/DIFF-0),
which turns a design text into the one batch for it against a session, and `shell design` (DESIGN-EVENT-0), which admits
a batch or refuses it. What either refuses stays refused. A person, a script and a language model all use it the same
way, by writing a few lines of design text.

    language proposes  ->  the shell compiles  ->  the shell admits  ->  the session records  ->  the kernel renders

    python design/design.py new      [--project DIR] [--level L] [--tiles T] [--camera x,z,F] [--shell EXE]
    python design/design.py open     --session S.json [--project DIR] [--shell EXE]
    python design/design.py grant    [--allow open,close,paint] [--cells x0,z0,x1,z1] [--classes wall0,floor,...]
    python design/design.py inspect  [--region x0,z0,x1,z1] [--json]
    python design/design.py propose  FILE | -            (design text; `-` reads it from standard input)
    python design/design.py preview  [--json]
    python design/design.py admit
    python design/design.py reject
    python design/design.py undo
    python design/design.py status   [--json]

The design text (VERDANDI-DESIGN 0, the source language DESIGN-IR/DIFF-0 registered; the shell's compiler reads it):

    VERDANDI-DESIGN 0
    # a comment
    open   x0,z0 x1,z1        every cell of the rectangle becomes floor       (one corner alone means one cell)
    close  x0,z0 x1,z1        every cell of the rectangle becomes rock
    room   x0,z0 x1,z1        the rectangle's rim becomes rock and its inside floor
    entrance x,z              one cell becomes floor
    paint  CLASS R,G,B        a tile class (wall0 wall1 wall2 wall3 floor) takes one colour

Statements apply in order; what is proposed is the net difference from the current world, one operation per cell or
class that ends up different, written by the shell's compiler as ONE batch. `propose` hands the compiler the text's
bytes exactly as they were given and keeps what it wrote; the batch's id is the SHA-256 of those bytes, and the text
is kept under that id in the project. A preview is the shell's dry run of that batch: the same checks and the same
replay as the admission, and nothing written. `admit` gives the same bytes to the shell, bound to the preview: the
shell refuses unless they are the bytes that were previewed and reach the head the preview reached.

What this tool computes itself (the top view, the counts, what is reachable) is a view for a reader. It is never
authority, and where it disagrees with the shell the shell is right.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "verify"))
import savedform  # noqa: E402  the tree's one reader of what it saves

TEXT_VERSION = "VERDANDI-DESIGN 0"
# the source language's bounds, as DESIGN-IR/DIFF-0 registered them. Stated here for a reader; the shell's compiler holds them
LIMITS = {"bytes": 16384, "statements": 64, "operations": 4096}
CLASSES = ("wall0", "wall1", "wall2", "wall3", "floor")
OPEN_CELLS = b".<>"
EXE = ".exe" if os.name == "nt" else ""


class Refused(Exception):
    """This tool's own refusal: a code and a sentence. It ends the command with exit 2 and changes nothing."""

    def __init__(self, code: str, text: str):
        super().__init__("%s: %s" % (code, text))
        self.code = code


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------ the project: a pointer and a scratch, never authority
def project_dir(args: dict) -> str:
    return os.path.abspath(args.get("--project") or os.environ.get("VERDANDI_DESIGN") or os.path.join(HERE, "work"))


def load_project(args: dict) -> dict:
    p = os.path.join(project_dir(args), "project.json")
    if not os.path.exists(p):
        raise Refused("DESIGN-NO-PROJECT", "there is no project at %s: start one with `new` or `open`" % project_dir(args))
    with open(p, encoding="utf-8") as fh:
        prj = json.load(fh)
    prj["dir"] = project_dir(args)
    return prj


def save_project(prj: dict) -> None:
    d = {k: v for k, v in prj.items() if k != "dir"}
    tmp = os.path.join(prj["dir"], "project.json.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(d, fh, indent=1)
        fh.write("\n")
    os.replace(tmp, os.path.join(prj["dir"], "project.json"))


def find_shell(given: str | None, pdir: str) -> str:
    """The certified admitter: the shell the gate builds, or one built here from the same sources."""
    cands = [given] if given else [os.path.join(ROOT, "verify", "build", "shell" + EXE), os.path.join(ROOT, "build", "shell" + EXE),
                                   os.path.join(pdir, "shell" + EXE)]
    for c in cands:
        if c and os.path.isfile(c):
            return os.path.abspath(c)
    if given:
        raise Refused("DESIGN-NO-SHELL", "%s is not a file" % given)
    rustc = shutil.which("rustc")
    if rustc is None:
        raise Refused("DESIGN-NO-SHELL", "no built shell was found (verify/build/shell%s) and rustc is not here to build one" % EXE)
    out = os.path.join(pdir, "shell" + EXE)
    cp = subprocess.run([rustc, "-O", os.path.join(ROOT, "shell", "main.rs"), "-o", out], capture_output=True, text=True, cwd=ROOT)
    if cp.returncode != 0:
        raise Refused("DESIGN-NO-SHELL", "the shell did not build: " + cp.stderr.strip()[-300:])
    return out


def shell(prj: dict, cmd: str, argv: list, root: str):
    """One run of the shell, with its sessions, its refusal log and its run ledger kept inside the project."""
    env = dict(os.environ, VERDANDI_SESSIONS=root, VERDANDI_REFUSAL_LOG=os.path.join(prj["dir"], "refusals.log"),
               VERDANDI_RUN_LEDGER=os.path.join(prj["dir"], "runs.log"))
    return subprocess.run([prj["shell"], cmd] + argv, capture_output=True, text=True, cwd=ROOT, env=env, errors="replace")


def seam(prj: dict, argv: list):
    """One run of the admission, `shell design`. A shell built before DESIGN-EVENT-0 has no such command: said plainly."""
    cp = shell(prj, "design", argv, os.path.join(prj["dir"], "sessions"))
    if cp.returncode != 0 and "unknown command design" in (cp.stderr or "") + (cp.stdout or ""):
        raise Refused("DESIGN-NO-SHELL", "the shell at %s was built before the batch seam (it has no `design` command): build it again "
                                         "(a gate run does, or `rustc -O shell/main.rs`), or start the project with --shell" % prj["shell"])
    return cp


def refusal_line(cp) -> str:
    """The shell's own coded line for a run that did not end 0."""
    for ln in (cp.stderr or "").splitlines() + (cp.stdout or "").splitlines():
        if re.match(r"[A-Z][A-Z0-9-]*: ", ln):
            return ln.strip()
    return ((cp.stderr or cp.stdout or "").strip().splitlines() or ["(no output)"])[-1]


def saved(cp):
    """(the path, the head) of the session a run of the shell saved and verified, or None."""
    m = re.search(r"saved and verified: (.+?session\.json).*?head ([0-9a-f]{64})", cp.stdout or "")
    return (m.group(1), m.group(2)) if cp.returncode == 0 and m else None


def anchor(prj: dict, session: str) -> dict:
    """What a proposal against this session is anchored to, as the shell states it. The shell loads and checks the session."""
    cp = shell(prj, "admit-anchor", ["--session", session], os.path.join(prj["dir"], "sessions"))
    if cp.returncode != 0:
        raise Refused("DESIGN-SESSION", "the shell does not accept %s: %s" % (session, refusal_line(cp)))
    lines = cp.stdout.splitlines()
    if len(lines) != 4 or lines[0] != "VRDNP1":
        raise Refused("DESIGN-SESSION", "the shell's anchor is not the four lines expected")
    return {"renderer": lines[1].split("=", 1)[1], "bearing": lines[2].split("=", 1)[1], "parent": lines[3].split("=", 1)[1]}


def grant_args(prj: dict) -> list:
    g, out = prj["grant"], []
    for flag, key in (("--allow", "allow"), ("--cells", "cells"), ("--classes", "classes")):
        if g.get(key):
            out += [flag, g[key]]
    return out


# ------------------------------------------------------------------ the world, as a view
class World:
    """The session's world as this tool reads it: the base level and tiles, and the session's edits applied in order.
    A view. The authority is the session, and the shell is what replays it."""

    def __init__(self, session_path: str):
        doc = savedform.read_file(session_path)
        d = doc["data"]
        self.head, self.camera, self.events, self.edits = d["head"], d["final_camera"], len(d["log"]), d["edits"]
        lvl = open(os.path.join(ROOT, *d["base"]["level"].split("/")), "rb").read()
        til = open(os.path.join(ROOT, *d["base"]["tiles"].split("/")), "rb").read()
        if sha256(lvl) != d["base"]["W"] or sha256(til) != d["base"]["M"]:
            raise Refused("DESIGN-BASE", "the level or the tiles the session names are not the bytes it was made over")
        if lvl[:8] != b"VRDNLVL1" or til[:8] != b"VRDNTIL1":
            raise Refused("DESIGN-BASE", "the base level or tiles are not in the tree's formats")
        self.w, self.rows = int.from_bytes(lvl[8:12], "little"), int.from_bytes(lvl[12:16], "little")
        self.cells = bytearray(lvl[16:16 + self.w * self.rows])
        n = (len(til) - 8) // 5
        self.tiles = {c: None for c in CLASSES}      # a class's one colour, when a paint has made it one colour
        for i, c in enumerate(CLASSES):
            t = til[8 + i * n:8 + (i + 1) * n]
            if len(set(t[k:k + 3] for k in range(0, len(t), 3))) == 1:
                self.tiles[c] = tuple(t[:3])
        self.admitted = 0
        for e in d["log"]:
            if e["kind"] == "edit":
                self.apply(e["spec"])
                self.admitted += 1 if "admit" in e else 0
        x, z, f = self.camera.split(",")[:3]
        self.cam = (int(x), int(z))

    def apply(self, spec: str) -> None:
        kind, rest = spec.split(":", 1)
        p = rest.split(",")
        if kind == "cell":
            self.cells[int(p[1]) * self.w + int(p[0])] = ord(p[2])
        else:
            self.tiles[p[0]] = (int(p[1]), int(p[2]), int(p[3]))

    def at(self, x: int, z: int) -> int:
        return self.cells[z * self.w + x]

    def reachable(self, cells=None) -> set:
        """The cells a walk from the camera can stand on: floor and stairs, joined edge to edge."""
        cells = self.cells if cells is None else cells
        if cells[self.cam[1] * self.w + self.cam[0]] not in OPEN_CELLS:
            return set()
        seen, todo = {self.cam}, [self.cam]
        while todo:
            x, z = todo.pop()
            for nx, nz in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
                if 0 <= nx < self.w and 0 <= nz < self.rows and (nx, nz) not in seen and cells[nz * self.w + nx] in OPEN_CELLS:
                    seen.add((nx, nz))
                    todo.append((nx, nz))
        return seen


def top_view(w: World, cells, region, marks=None) -> list:
    """The grid from above: # rock, . floor, < > stairs, @ the camera; `marks` overrides a cell's letter."""
    x0, z0, x1, z1 = region
    out = ["     " + "".join(str((x // 10) % 10) if x % 10 == 0 else " " for x in range(x0, x1 + 1)),
           "     " + "".join(str(x % 10) for x in range(x0, x1 + 1))]
    for z in range(z0, z1 + 1):
        row = []
        for x in range(x0, x1 + 1):
            ch = chr(cells[z * w.w + x])
            if marks and (x, z) in marks:
                ch = marks[(x, z)]
            elif (x, z) == w.cam:
                ch = "@"
            row.append(ch)
        out.append("%4d %s" % (z, "".join(row)))
    return out


def parse_region(text: str | None, w: World) -> tuple:
    if not text:
        return (0, 0, w.w - 1, w.rows - 1)
    try:
        x0, z0, x1, z1 = (int(v) for v in text.split(","))
    except ValueError:
        raise Refused("DESIGN-USAGE", "--region takes x0,z0,x1,z1")
    if not (0 <= x0 <= x1 < w.w and 0 <= z0 <= z1 < w.rows):
        raise Refused("DESIGN-USAGE", "the region is not inside the %dx%d level" % (w.w, w.rows))
    return (x0, z0, x1, z1)


# ------------------------------------------------------------------ the compiler is the shell's
def design_file(prj: dict) -> str:
    return os.path.join(prj["dir"], "pending.design")


def compile_with_shell(prj: dict, session: str, data: bytes) -> tuple:
    """Hand a design's bytes to the certified compiler, `shell design-compile`, against a session. Returns (the batch
    it wrote, None) or (None, the shell's own refusal line). The bytes go to it exactly as they were given."""
    with open(design_file(prj), "wb") as fh:
        fh.write(data)
    env = dict(os.environ, VERDANDI_SESSIONS=os.path.join(prj["dir"], "sessions"), VERDANDI_REFUSAL_LOG=os.path.join(prj["dir"], "refusals.log"),
               VERDANDI_RUN_LEDGER=os.path.join(prj["dir"], "runs.log"))
    cp = subprocess.run([prj["shell"], "design-compile", "--session", session, "--design", design_file(prj)], capture_output=True, cwd=ROOT, env=env)
    err = cp.stderr.decode("utf-8", "replace")
    if cp.returncode != 0 and "unknown command design-compile" in err:
        raise Refused("DESIGN-NO-SHELL", "the shell at %s was built before the design compiler (it has no `design-compile` command): build it "
                                         "again (a gate run does, or `rustc -O shell/main.rs`), or start the project with --shell" % prj["shell"])
    if cp.returncode != 0 or not cp.stdout:
        lines = [ln.strip() for ln in err.splitlines() if re.match(r"[A-Z][A-Z0-9-]*: ", ln)]
        return None, (lines[0] if lines else (err.strip().splitlines() or ["(no output)"])[-1])
    return cp.stdout, None


def batch_said(raw: bytes) -> tuple:
    """What a batch says, read to show it: (the values of its header lines by name, its operation lines). Reading only:
    the batch is the compiler's, and this tool writes none."""
    lines = raw.decode("ascii", "replace").split("\n")
    said = dict(ln.split("=", 1) for ln in lines[1:6] if "=" in ln)
    return said, [ln for ln in lines[6:] if ln]


def readings(w: World, cells) -> dict:
    """What this tool reads off a grid. A view for a reader: nothing here is a registered constraint."""
    reach = w.reachable(cells)
    floor = sum(1 for c in cells if c in OPEN_CELLS)
    return {"floor_cells": floor, "reachable_from_camera": len(reach), "floor_not_reachable": floor - len(reach),
            "camera_on_floor": cells[w.cam[1] * w.w + w.cam[0]] in OPEN_CELLS}


BINDING = re.compile(r"\[design\] preview VRDNP2 parent=([0-9a-f]{64}) digest=([0-9a-f]{64}) head=([0-9a-f]{64}) operations=(\d+)")


def batch_file(prj: dict) -> str:
    return os.path.join(prj["dir"], "pending.vrdnp2")


def kinds_of(lines: list) -> dict:
    return {k: sum(1 for ln in lines if ln.startswith(k + " ")) for k in ("open", "close", "paint")}


# ------------------------------------------------------------------ the commands
def current(prj: dict) -> dict:
    return prj["history"][-1]


def cmd_new(args: dict) -> int:
    pdir = project_dir(args)
    if os.path.exists(os.path.join(pdir, "project.json")):
        raise Refused("DESIGN-EXISTS", "there is already a project at %s" % pdir)
    os.makedirs(os.path.join(pdir, "sessions"), exist_ok=True)
    prj = {"dir": pdir, "shell": find_shell(args.get("--shell"), pdir), "grant": {"allow": "open,close,paint", "cells": "", "classes": ""},
           "history": [], "pending": None}
    if "--session" in args:
        session = os.path.abspath(args["--session"])
    else:
        argv = ["--camera", args.get("--camera", "28,28,N"), "--keys", "ESC"]
        for flag in ("--level", "--tiles"):
            if flag in args:
                argv += [flag, args[flag]]
        cp = shell(prj, "live-selftest", argv, os.path.join(pdir, "sessions"))
        if not saved(cp):
            raise Refused("DESIGN-SESSION", "the shell did not save a starting session: " + refusal_line(cp))
        session = saved(cp)[0]
    a = anchor(prj, session)
    prj["history"].append({"session": session, "head": a["parent"], "note": "opened" if "--session" in args else "new"})
    prj["identity"] = {"renderer": a["renderer"], "bearing": a["bearing"]}
    save_project(prj)
    print("project   %s" % pdir)
    print("session   %s" % session)
    print("head      %s" % a["parent"])
    print("shell     %s" % prj["shell"])
    return 0


def cmd_grant(args: dict) -> int:
    prj = load_project(args)
    for flag, key in (("--allow", "allow"), ("--cells", "cells"), ("--classes", "classes")):
        if flag in args:
            prj["grant"][key] = args[flag]
    prj["pending"] = None
    save_project(prj)
    print("grant     allow=%s cells=%s classes=%s" % tuple(prj["grant"].get(k) or "(the shell's default)" for k in ("allow", "cells", "classes")))
    print("          the shell enforces it at every admission; a proposal cannot carry or widen it")
    return 0


def describe(prj: dict, w: World) -> dict:
    cur = current(prj)
    return {"project": {"dir": prj["dir"], "renderer_identity": prj["identity"]["renderer"], "bearing_identity": prj["identity"]["bearing"],
                        "design_text": TEXT_VERSION, "compiler": "shell design-compile", "admission": "shell design"},
            "session": {"path": cur["session"], "head": w.head, "events": w.events, "edits": w.edits, "admitted_edits": w.admitted,
                        "steps_back_available": len(prj["history"]) - 1},
            "world": {"width": w.w, "rows": w.rows, "camera": w.camera, "border": "the outermost cells stay rock",
                      "tile_classes": {c: (list(w.tiles[c]) if w.tiles[c] else "textured") for c in CLASSES}},
            "readings": readings(w, w.cells),
            "capabilities": {"grant": prj["grant"], "statements": ["open", "close", "room", "entrance", "paint"],
                             "limits": LIMITS},
            "pending": None if not prj.get("pending") else {"operations": prj["pending"].get("operations"), "previewed": bool(prj["pending"].get("preview"))}}


def cmd_inspect(args: dict) -> int:
    prj = load_project(args)
    w = World(current(prj)["session"])
    d = describe(prj, w)
    region = parse_region(args.get("--region"), w)
    if "--json" in args:
        d["top_view"] = top_view(w, w.cells, region)
        print(json.dumps(d, indent=1))
        return 0
    print("PROJECT   renderer %s...  bearing %s...  design text `%s`" % (d["project"]["renderer_identity"][:12], d["project"]["bearing_identity"][:12], TEXT_VERSION))
    print("SESSION   head %s  %d events, %d edits (%d admitted)  %d step(s) back available"
          % (w.head[:12], w.events, w.edits, w.admitted, len(prj["history"]) - 1))
    print("WORLD     %d x %d cells, camera %s, border stays rock" % (w.w, w.rows, w.camera))
    print("          classes: " + "  ".join("%s=%s" % (c, ("%d,%d,%d" % w.tiles[c]) if w.tiles[c] else "textured") for c in CLASSES))
    r = d["readings"]
    print("READINGS  floor %d cells, %d reachable from the camera, %d not  (this tool's view, not a constraint)"
          % (r["floor_cells"], r["reachable_from_camera"], r["floor_not_reachable"]))
    g = prj["grant"]
    print("GRANT     allow=%s cells=%s classes=%s" % tuple(g.get(k) or "(default)" for k in ("allow", "cells", "classes")))
    print("TOP VIEW  # rock  . floor  < > stairs  @ camera   (x across, z down)")
    print("\n".join(top_view(w, w.cells, region)))
    return 0


def cmd_propose(args: dict) -> int:
    prj = load_project(args)
    src = args.get("_", [None])[0]
    if src is None:
        raise Refused("DESIGN-USAGE", "propose takes a file of design text, or - for standard input")
    data = sys.stdin.buffer.read() if src == "-" else open(src, "rb").read()
    cur = current(prj)
    prj["pending"] = None
    if os.path.exists(batch_file(prj)):
        os.remove(batch_file(prj))
    raw, refusal = compile_with_shell(prj, cur["session"], data)
    if raw is None:
        save_project(prj)
        print("COMPILER  the shell refuses the design: %s" % refusal)
        print("          nothing is proposed and nothing of the project changed. Revise the design and propose again")
        return 2
    said, lines = batch_said(raw)
    did = sha256(data)
    # this tool's own check on what it was handed: the batch names this design's digest and this session's head
    if said.get("proposal") != did or said.get("parent") != cur["head"] or said.get("operations") != str(len(lines)):
        raise Refused("DESIGN-COMPILER", "the compiler's batch does not name this design's digest, this session's head and its own count")
    with open(batch_file(prj), "wb") as fh:
        fh.write(raw)
    # the design's bytes are kept under their id: the id is a commitment, and only the bytes say what was designed
    os.makedirs(os.path.join(prj["dir"], "designs"), exist_ok=True)
    with open(os.path.join(prj["dir"], "designs", did + ".design"), "wb") as fh:
        fh.write(data)
    prj["pending"] = {"base_session": cur["session"], "base_head": cur["head"], "design": did, "operations": len(lines), "digest": sha256(raw), "preview": None}
    save_project(prj)
    kinds = kinds_of(lines)
    print("PROPOSED  against head %s: %d operation(s): %d cell(s) open, %d close, %d class(es) painted"
          % (cur["head"][:12], len(lines), kinds["open"], kinds["close"], kinds["paint"]))
    print("          design %s, compiled by the shell (shell design-compile); its text is kept under that id" % did[:12])
    print("          nothing is changed. `preview` is the shell's dry run of this batch and shows the result; `reject` drops it")
    return 0


def cmd_preview(args: dict) -> int:
    prj = load_project(args)
    pend = prj.get("pending")
    if not pend:
        raise Refused("DESIGN-NOTHING", "there is no proposal: `propose` one first")
    cur = current(prj)
    if pend["base_head"] != cur["head"]:
        raise Refused("DESIGN-STALE", "the proposal was made against head %s and the project stands at %s: propose again" % (pend["base_head"][:12], cur["head"][:12]))
    if "design" not in pend or not os.path.exists(batch_file(prj)):
        raise Refused("DESIGN-STALE", "the pending proposal was made by an earlier version of this tool, which compiled it itself: propose it again")
    w = World(cur["session"])
    refusal, bound = None, None
    raw = open(batch_file(prj), "rb").read()
    if sha256(raw) != pend["digest"]:
        raise Refused("DESIGN-STALE", "the pending batch is not the bytes the compiler wrote: propose again")
    _said, lines = batch_said(raw)
    # the preview IS the admission, stopped before anything is written: the same bytes, the same checks, the same replay
    cp = seam(prj, ["--session", cur["session"], "--proposal", batch_file(prj), "--dry-run"] + grant_args(prj))
    m = BINDING.search(cp.stdout or "")
    if cp.returncode == 0 and m and m.group(1) == cur["head"] and m.group(2) == pend["digest"] and int(m.group(4)) == pend["operations"]:
        bound = {"parent": m.group(1), "digest": m.group(2), "head": m.group(3)}
    else:
        refusal = {"shell": refusal_line(cp)}
    ok = bound is not None
    pend["preview"] = {"ok": ok, "head": bound["head"] if ok else None, "digest": bound["digest"] if ok else None, "refusal": refusal}
    save_project(prj)
    # the proposed grid, for a reader: the batch's own operations laid over the current one
    cells = bytearray(w.cells)
    marks = {}
    for ln in lines:
        verb, _sp, target = ln.partition(" ")
        if verb in ("open", "close"):
            x, z = (int(v) for v in target.split(","))
            cells[z * w.w + x] = ord("#") if verb == "close" else ord(".")
            marks[(x, z)] = "X" if verb == "close" else "o"
    before, after = readings(w, w.cells), readings(w, cells)
    xs = [x for x, _ in marks] or [w.cam[0]]
    zs = [z for _, z in marks] or [w.cam[1]]
    region = (max(0, min(xs) - 3), max(0, min(zs) - 2), min(w.w - 1, max(xs) + 3), min(w.rows - 1, max(zs) + 2))
    if "--region" in args:
        region = parse_region(args["--region"], w)
    if "--json" in args:
        print(json.dumps({"ok": ok, "base_head": cur["head"], "proposed_head": pend["preview"]["head"], "operations": pend["operations"], "design": pend["design"],
                          "digest": pend["preview"]["digest"], "refusal": refusal, "readings": {"current": before, "proposed": after},
                          "current": top_view(w, w.cells, region), "proposed": top_view(w, cells, region, marks)}, indent=1))
        return 0 if ok else 2
    print("CURRENT   head %s" % cur["head"][:12])
    print("\n".join(top_view(w, w.cells, region)))
    print("PROPOSED  %s   (o a cell that opens, X a cell that closes)" % (("head " + pend["preview"]["head"][:12]) if ok else "NOT ADMISSIBLE"))
    print("\n".join(top_view(w, cells, region, marks)))
    kinds = kinds_of(lines)
    print("CHANGES   %d cell(s) open, %d close, %d class(es) painted" % (kinds["open"], kinds["close"], kinds["paint"]))
    for ln in lines:
        if ln.startswith("paint "):
            _v, cls, colour = ln.split(" ")
            print("          %s takes the colour %d,%d,%d" % (cls, int(colour) >> 16, (int(colour) >> 8) & 255, int(colour) & 255))
    print("READINGS  floor %d -> %d cells; reachable from the camera %d -> %d; floor not reachable %d -> %d   (a view, not a constraint)"
          % (before["floor_cells"], after["floor_cells"], before["reachable_from_camera"], after["reachable_from_camera"],
             before["floor_not_reachable"], after["floor_not_reachable"]))
    if ok:
        print("SEAM      the shell's dry run passed every check for all %d operation(s) and wrote nothing (batch %s...)"
              % (pend["operations"], bound["digest"][:12]))
        print("          `admit` gives the same bytes to the shell, bound to this preview; `reject` drops them")
        return 0
    print("SEAM      the shell refuses the batch: %s" % refusal["shell"])
    print("          nothing is admitted and nothing of the project changed. Revise the design and propose again")
    return 2


def cmd_admit(args: dict) -> int:
    prj = load_project(args)
    pend = prj.get("pending")
    if not pend or not pend.get("preview"):
        raise Refused("DESIGN-NOTHING", "there is no previewed proposal: `propose`, then `preview`, then `admit`")
    cur = current(prj)
    if pend["base_head"] != cur["head"]:
        raise Refused("DESIGN-STALE", "the proposal was made against head %s and the project stands at %s" % (pend["base_head"][:12], cur["head"][:12]))
    if not pend["preview"]["ok"]:
        raise Refused("DESIGN-NOT-ADMISSIBLE", "the preview was refused by the shell: revise the design")
    if "design" not in pend or not pend["preview"].get("digest"):
        raise Refused("DESIGN-STALE", "the pending proposal was made by an earlier version of this tool: propose and preview it again")
    # one admission: the previewed bytes, bound to the preview. The shell refuses (ADMIT-PREVIEW) unless they have the
    # previewed digest and reach the previewed head, and (ADMIT-ANCHOR) unless the session still stands at their parent
    bound = "%s,%s" % (pend["preview"]["digest"], pend["preview"]["head"])
    cp = seam(prj, ["--session", cur["session"], "--proposal", batch_file(prj), "--previewed", bound] + grant_args(prj))
    if not saved(cp):
        print("SEAM      the shell refuses the batch: %s" % refusal_line(cp))
        print("          the project still stands at head %s; nothing was accepted" % cur["head"][:12])
        return 2
    session, head = saved(cp)
    prj["history"].append({"session": session, "head": head, "design": pend["design"], "note": "%d operation(s) in one batch, design %s" % (pend["operations"], pend["design"][:12])})
    n = pend["operations"]
    prj["pending"] = None
    save_project(prj)
    if os.path.exists(batch_file(prj)):
        # the admitted bytes are kept, named by the head they gave: the envelope records their digest, not the bytes
        os.makedirs(os.path.join(prj["dir"], "batches"), exist_ok=True)
        os.replace(batch_file(prj), os.path.join(prj["dir"], "batches", head + ".vrdnp2"))
    print("ADMITTED  %d operation(s) as one batch: %d ordinary edits of the session, one admission" % (n, n))
    print("          head %s -> %s" % (cur["head"][:12], head[:12]))
    print("          session %s" % session)
    print("          design  %s (designs/%s.design)" % (prj["history"][-1]["design"][:12], prj["history"][-1]["design"]))
    return 0


def cmd_reject(args: dict) -> int:
    prj = load_project(args)
    had = bool(prj.get("pending"))
    prj["pending"] = None
    save_project(prj)
    for f in (batch_file(prj), design_file(prj)):
        if os.path.exists(f):
            os.remove(f)
    print("REJECTED  the proposal is dropped; the project stands at head %s" % current(prj)["head"][:12] if had else "there was no proposal")
    return 0


def cmd_undo(args: dict) -> int:
    prj = load_project(args)
    if len(prj["history"]) < 2:
        raise Refused("DESIGN-NOTHING", "the project stands at its first session: there is nothing to step back from")
    gone = prj["history"].pop()
    prj["pending"] = None
    save_project(prj)
    cur = current(prj)
    print("UNDONE    the project stands at head %s again (%s)" % (cur["head"][:12], cur["session"]))
    print("          the session it stepped back from is still on disk, unchanged: %s" % gone["session"])
    return 0


def cmd_status(args: dict) -> int:
    prj = load_project(args)
    cur = current(prj)
    pend = prj.get("pending")
    d = {"head": cur["head"], "session": cur["session"], "steps_back_available": len(prj["history"]) - 1, "grant": prj["grant"],
         "pending": None if not pend else {"operations": pend.get("operations"), "design": pend.get("design"), "against": pend["base_head"], "stale": pend["base_head"] != cur["head"],
                                           "preview": None if not pend.get("preview") else {"ok": pend["preview"]["ok"], "head": pend["preview"]["head"]}}}
    if "--json" in args:
        print(json.dumps(d, indent=1))
        return 0
    print("HEAD      %s   (%d step(s) back available)" % (cur["head"][:12], len(prj["history"]) - 1))
    print("SESSION   %s" % cur["session"])
    if not pend:
        print("PENDING   nothing proposed")
    else:
        pv = pend.get("preview")
        print("PENDING   %d operation(s) against %s%s: %s" % (pend.get("operations") or 0, pend["base_head"][:12], " (STALE)" if d["pending"]["stale"] else "",
                                                               "not previewed" if not pv else ("previewed, admissible, head " + pv["head"][:12]) if pv["ok"] else "previewed, REFUSED by the shell"))
    return 0


COMMANDS = {"new": cmd_new, "open": cmd_new, "grant": cmd_grant, "inspect": cmd_inspect, "propose": cmd_propose, "preview": cmd_preview,
            "admit": cmd_admit, "reject": cmd_reject, "undo": cmd_undo, "status": cmd_status}
FLAGS = {"new": ("--project", "--level", "--tiles", "--camera", "--shell"), "open": ("--project", "--session", "--shell"),
         "grant": ("--project", "--allow", "--cells", "--classes"), "inspect": ("--project", "--region", "--json"),
         "propose": ("--project",), "preview": ("--project", "--region", "--json"), "admit": ("--project",),
         "reject": ("--project",), "undo": ("--project",), "status": ("--project", "--json")}
BARE = ("--json",)


def main(argv: list) -> int:
    if len(argv) < 2 or argv[1] not in COMMANDS:
        print(__doc__.strip().split("\n\n")[2] if len(argv) < 2 else "DESIGN-USAGE: `%s` is not a command (%s)" % (argv[1], ", ".join(COMMANDS)))
        return 2
    cmd, args, i = argv[1], {"_": []}, 2
    try:
        while i < len(argv):
            a = argv[i]
            if a.startswith("--") and a != "-":
                if a not in FLAGS[cmd]:
                    raise Refused("DESIGN-USAGE", "`%s` does not take %s" % (cmd, a))
                if a in BARE:
                    args[a] = True
                    i += 1
                else:
                    if i + 1 >= len(argv):
                        raise Refused("DESIGN-USAGE", "%s needs a value" % a)
                    args[a] = argv[i + 1]
                    i += 2
            else:
                args["_"].append(a)
                i += 1
        if cmd == "open" and "--session" not in args:
            raise Refused("DESIGN-USAGE", "open takes --session S.json")
        return COMMANDS[cmd](args)
    except Refused as r:
        print(str(r))
        return 2
    except savedform.Refused as r:
        print("DESIGN-SESSION: the tree's reader refuses the session file: %s" % r)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
