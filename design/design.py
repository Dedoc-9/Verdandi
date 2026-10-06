#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""design/design.py — the design surface: inspect, propose, preview, admit, undo.

CONTENT TIME. This tool is not part of the gate and no gate runs when it is used. It holds no authority: every change
it makes to a world is made by the certified admission seam, `shell admit` (ADMIT-0), one proposal at a time, and what
the seam refuses stays refused. A person, a script and a language model all use it the same way, by writing a few
lines of design text.

    language proposes  ->  this tool compiles  ->  the shell admits  ->  the session records  ->  the kernel renders

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

The design text (version 0; this tool's own, not a registered language of the tree):

    VERDANDI-DESIGN 0
    # a comment
    open   x0,z0 x1,z1        every cell of the rectangle becomes floor       (one corner alone means one cell)
    close  x0,z0 x1,z1        every cell of the rectangle becomes rock
    room   x0,z0 x1,z1        the rectangle's rim becomes rock and its inside floor
    entrance x,z              one cell becomes floor
    paint  CLASS R,G,B        a tile class (wall0 wall1 wall2 wall3 floor) takes one colour

Statements apply in order to a working copy; what is proposed is the net difference from the current world, one cell
operation per changed cell. A preview admits those operations into a scratch root and shows the result; it changes
nothing that counts. `admit` gives the same proposal bytes to the seam again, for the project's own sessions.

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
MAX_STATEMENTS = 64          # a design text is small on purpose
MAX_OPERATIONS = 4096        # and so is what it compiles to
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


# ------------------------------------------------------------------ the design text, and what it compiles to
def parse_design(text: str, w: World) -> list:
    """The statements of a design text, typed. Anything else is refused with its line."""
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != TEXT_VERSION:
        raise Refused("DESIGN-PARSE", "line 1: a design text begins with the line `%s`" % TEXT_VERSION)
    out = []

    def point(tok: str, n: int) -> tuple:
        m = re.fullmatch(r"(0|[1-9][0-9]{0,4}),(0|[1-9][0-9]{0,4})", tok)
        if not m:
            raise Refused("DESIGN-PARSE", "line %d: `%s` is not a cell x,z" % (n, tok))
        x, z = int(m.group(1)), int(m.group(2))
        if x >= w.w or z >= w.rows:
            raise Refused("DESIGN-RANGE", "line %d: the cell %d,%d is outside the %dx%d level" % (n, x, z, w.w, w.rows))
        return x, z
    for n, raw in enumerate(lines[1:], start=2):
        ln = raw.split("#", 1)[0].strip()
        if not ln:
            continue
        t = ln.split()
        verb = t[0]
        if verb in ("open", "close", "room"):
            if len(t) not in (2, 3) or (verb == "room" and len(t) != 3):
                raise Refused("DESIGN-PARSE", "line %d: `%s` takes %s" % (n, verb, "two corners" if verb == "room" else "a cell, or two corners"))
            a = point(t[1], n)
            b = point(t[2], n) if len(t) == 3 else a
            x0, x1, z0, z1 = min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])
            if verb == "room" and (x1 - x0 < 2 or z1 - z0 < 2):
                raise Refused("DESIGN-RANGE", "line %d: a room needs a rim and an inside: at least 3 cells each way" % n)
            out.append((verb, (x0, z0, x1, z1), n))
        elif verb == "entrance":
            if len(t) != 2:
                raise Refused("DESIGN-PARSE", "line %d: `entrance` takes one cell" % n)
            x, z = point(t[1], n)
            out.append(("open", (x, z, x, z), n))
        elif verb == "paint":
            m = re.fullmatch(r"(0|[1-9][0-9]{0,2}),(0|[1-9][0-9]{0,2}),(0|[1-9][0-9]{0,2})", t[2]) if len(t) == 3 else None
            if len(t) != 3 or t[1] not in CLASSES or not m or any(int(v) > 255 for v in m.groups()):
                raise Refused("DESIGN-PARSE", "line %d: `paint` takes a class (%s) and R,G,B, each 0 to 255" % (n, " ".join(CLASSES)))
            out.append(("paint", (t[1], tuple(int(v) for v in m.groups())), n))
        else:
            raise Refused("DESIGN-PARSE", "line %d: `%s` is not a statement (open, close, room, entrance, paint)" % (n, verb))
        if len(out) > MAX_STATEMENTS:
            raise Refused("DESIGN-SIZE", "a design text holds at most %d statements" % MAX_STATEMENTS)
    if not out:
        raise Refused("DESIGN-PARSE", "the design text holds no statement")
    return out


def compile_design(stmts: list, w: World, predict: bool = True) -> tuple:
    """The net difference the statements make to the current world, as the seam's operations, one per changed cell or
    class. Returns (operations, the proposed cells, notes). With `predict`, what the seam is known to refuse is refused
    here first, with the line; without it, the seam is left to say so."""
    cells, tiles, notes = bytearray(w.cells), dict(w.tiles), []
    for verb, arg, n in stmts:
        if verb == "paint":
            tiles[arg[0]] = arg[1]
            continue
        x0, z0, x1, z1 = arg
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                rim = verb == "room" and (x in (x0, x1) or z in (z0, z1))
                to = ord("#") if verb == "close" or rim else ord(".")
                border = x in (0, w.w - 1) or z in (0, w.rows - 1)
                if predict and border and to != ord("#"):
                    raise Refused("DESIGN-BORDER", "line %d: the cell %d,%d is on the level's border, which stays rock" % (n, x, z))
                if predict and cells[z * w.w + x] in b"<>" and to != cells[z * w.w + x]:
                    raise Refused("DESIGN-STAIR", "line %d: the cell %d,%d is a stair, which this language does not change" % (n, x, z))
                cells[z * w.w + x] = to
    ops = []
    for z in range(w.rows):
        for x in range(w.w):
            a, b = w.cells[z * w.w + x], cells[z * w.w + x]
            if a != b:
                ops.append({"op": "close" if b == ord("#") else "open", "target": "%d,%d" % (x, z), "value": "0",
                            "spec": "cell:%d,%d,%s" % (x, z, chr(b))})
    for c in CLASSES:
        if tiles[c] != w.tiles[c]:
            r, g, b = tiles[c]
            ops.append({"op": "paint", "target": c, "value": str(r * 65536 + g * 256 + b), "spec": "tile:%s,%d,%d,%d" % (c, r, g, b)})
    if predict and cells[w.cam[1] * w.w + w.cam[0]] not in OPEN_CELLS:
        raise Refused("DESIGN-CAMERA", "the design closes the cell the camera stands on (%d,%d)" % w.cam)
    if len(ops) > MAX_OPERATIONS:
        raise Refused("DESIGN-SIZE", "the design changes %d cells or classes; at most %d go in one proposal" % (len(ops), MAX_OPERATIONS))
    if not ops:
        notes.append("the design changes nothing: the world is already so")
    return ops, cells, notes


def readings(w: World, cells) -> dict:
    """What this tool reads off a grid. A view for a reader: nothing here is a registered constraint."""
    reach = w.reachable(cells)
    floor = sum(1 for c in cells if c in OPEN_CELLS)
    return {"floor_cells": floor, "reachable_from_camera": len(reach), "floor_not_reachable": floor - len(reach),
            "camera_on_floor": cells[w.cam[1] * w.w + w.cam[0]] in OPEN_CELLS}


def proposal_bytes(a: dict, pid: str, op: dict) -> bytes:
    """A VRDNP1 proposal: the one byte sequence of this operation against this anchor (shell/admit.rs)."""
    return ("VRDNP1\nrenderer=%s\nbearing=%s\nparent=%s\nproposal=%s\nop=%s\ntarget=%s\nvalue=%s\n"
            % (a["renderer"], a["bearing"], a["parent"], pid, op["op"], op["target"], op["value"])).encode("ascii")


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
                        "design_text": TEXT_VERSION, "proposal_language": "VRDNP1"},
            "session": {"path": cur["session"], "head": w.head, "events": w.events, "edits": w.edits, "admitted_edits": w.admitted,
                        "steps_back_available": len(prj["history"]) - 1},
            "world": {"width": w.w, "rows": w.rows, "camera": w.camera, "border": "the outermost cells stay rock",
                      "tile_classes": {c: (list(w.tiles[c]) if w.tiles[c] else "textured") for c in CLASSES}},
            "readings": readings(w, w.cells),
            "capabilities": {"grant": prj["grant"], "statements": ["open", "close", "room", "entrance", "paint"],
                             "limits": {"statements": MAX_STATEMENTS, "operations": MAX_OPERATIONS}},
            "pending": None if not prj.get("pending") else {"operations": len(prj["pending"]["ops"]), "previewed": bool(prj["pending"].get("preview"))}}


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
    text = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()
    cur = current(prj)
    w = World(cur["session"])
    stmts = parse_design(text, w)
    ops, cells, notes = compile_design(stmts, w, predict="--no-predict" not in args)
    nonce = os.environ.get("VERDANDI_DESIGN_NONCE") or os.urandom(16).hex()
    for i, op in enumerate(ops):
        op["id"] = sha256(("%s:%d:%s:%s" % (w.head, i, op["spec"], nonce)).encode("ascii"))
    prj["pending"] = {"base_session": cur["session"], "base_head": w.head, "text": text, "text_sha256": sha256(text.encode("utf-8")),
                      "ops": ops, "preview": None}
    save_project(prj)
    kinds = {k: sum(1 for o in ops if o["op"] == k) for k in ("open", "close", "paint")}
    print("PROPOSED  against head %s: %d operation(s): %d cell(s) open, %d close, %d class(es) painted"
          % (w.head[:12], len(ops), kinds["open"], kinds["close"], kinds["paint"]))
    for nt in notes:
        print("          " + nt)
    print("          nothing is changed. `preview` admits it into a scratch root and shows the result; `reject` drops it")
    return 0


def cmd_preview(args: dict) -> int:
    prj = load_project(args)
    pend = prj.get("pending")
    if not pend:
        raise Refused("DESIGN-NOTHING", "there is no proposal: `propose` one first")
    cur = current(prj)
    if pend["base_head"] != cur["head"]:
        raise Refused("DESIGN-STALE", "the proposal was made against head %s and the project stands at %s: propose again" % (pend["base_head"][:12], cur["head"][:12]))
    scratch = os.path.join(prj["dir"], "preview")
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch)
    w = World(cur["session"])
    session, a = cur["session"], anchor(prj, cur["session"])
    done, refusal = [], None
    for i, op in enumerate(pend["ops"]):
        pb = proposal_bytes(a, op["id"], op)
        pfile = os.path.join(scratch, "%04d.vrdnp" % i)
        with open(pfile, "wb") as fh:
            fh.write(pb)
        cp = shell(prj, "admit", ["--session", session, "--proposal", pfile] + grant_args(prj), os.path.join(scratch, "sessions"))
        if not saved(cp):
            refusal = {"operation": i, "spec": op["spec"], "shell": refusal_line(cp)}
            break
        session, head = saved(cp)
        a = dict(a, parent=head)
        done.append({"proposal": pfile, "digest": sha256(pb), "head": head})
    ok = refusal is None
    pend["preview"] = {"ok": ok, "head": a["parent"] if ok else None, "session": session if ok else None, "steps": done, "refusal": refusal}
    save_project(prj)
    cells = bytearray(w.cells)
    marks = {}
    for op in pend["ops"]:
        if op["op"] != "paint":
            x, z = (int(v) for v in op["target"].split(","))
            cells[z * w.w + x] = ord("#") if op["op"] == "close" else ord(".")
            marks[(x, z)] = "X" if op["op"] == "close" else "o"
    before, after = readings(w, w.cells), readings(w, cells)
    xs = [x for x, _ in marks] or [w.cam[0]]
    zs = [z for _, z in marks] or [w.cam[1]]
    region = (max(0, min(xs) - 3), max(0, min(zs) - 2), min(w.w - 1, max(xs) + 3), min(w.rows - 1, max(zs) + 2))
    if "--region" in args:
        region = parse_region(args["--region"], w)
    if "--json" in args:
        print(json.dumps({"ok": ok, "base_head": cur["head"], "proposed_head": pend["preview"]["head"], "operations": len(pend["ops"]),
                          "admitted_in_scratch": len(done), "refusal": refusal, "readings": {"current": before, "proposed": after},
                          "current": top_view(w, w.cells, region), "proposed": top_view(w, cells, region, marks)}, indent=1))
        return 0 if ok else 2
    print("CURRENT   head %s" % cur["head"][:12])
    print("\n".join(top_view(w, w.cells, region)))
    print("PROPOSED  %s   (o a cell that opens, X a cell that closes)" % (("head " + pend["preview"]["head"][:12]) if ok else "NOT ADMISSIBLE"))
    print("\n".join(top_view(w, cells, region, marks)))
    kinds = {k: sum(1 for o in pend["ops"] if o["op"] == k) for k in ("open", "close", "paint")}
    print("CHANGES   %d cell(s) open, %d close, %d class(es) painted" % (kinds["open"], kinds["close"], kinds["paint"]))
    for op in pend["ops"]:
        if op["op"] == "paint":
            print("          " + op["spec"])
    print("READINGS  floor %d -> %d cells; reachable from the camera %d -> %d; floor not reachable %d -> %d   (a view, not a constraint)"
          % (before["floor_cells"], after["floor_cells"], before["reachable_from_camera"], after["reachable_from_camera"],
             before["floor_not_reachable"], after["floor_not_reachable"]))
    if ok:
        print("SEAM      the shell admitted all %d operation(s) in the scratch root, each within the grant; nothing of the project changed"
              % len(done))
        print("          `admit` gives the same proposal bytes to the shell for the project; `reject` drops them")
        return 0
    print("SEAM      the shell refused operation %d of %d (%s): %s" % (refusal["operation"] + 1, len(pend["ops"]), refusal["spec"], refusal["shell"]))
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
    if not pend["ops"]:
        raise Refused("DESIGN-NOTHING", "the proposal changes nothing")
    session = cur["session"]
    for i, step in enumerate(pend["preview"]["steps"]):
        pb = open(step["proposal"], "rb").read()
        if sha256(pb) != step["digest"]:
            raise Refused("DESIGN-CHANGED", "the previewed proposal %d is not the bytes that were previewed" % (i + 1))
        cp = shell(prj, "admit", ["--session", session, "--proposal", step["proposal"]] + grant_args(prj), os.path.join(prj["dir"], "sessions"))
        if not saved(cp):
            print("SEAM      the shell refused operation %d of %d: %s" % (i + 1, len(pend["ops"]), refusal_line(cp)))
            print("          the project still stands at head %s; nothing was accepted" % cur["head"][:12])
            return 2
        session = saved(cp)[0]
    head = anchor(prj, session)["parent"]
    if head != pend["preview"]["head"]:
        raise Refused("DESIGN-DIVERGED", "the admitted head %s is not the previewed head %s; the project is left where it was" % (head[:12], pend["preview"]["head"][:12]))
    prj["history"].append({"session": session, "head": head, "note": "%d operation(s), design text %s" % (len(pend["ops"]), pend["text_sha256"][:12])})
    n = len(pend["ops"])
    prj["pending"] = None
    save_project(prj)
    shutil.rmtree(os.path.join(prj["dir"], "preview"), ignore_errors=True)
    print("ADMITTED  %d operation(s), each one ordinary edit of the session with its envelope" % n)
    print("          head %s -> %s" % (cur["head"][:12], head[:12]))
    print("          session %s" % session)
    return 0


def cmd_reject(args: dict) -> int:
    prj = load_project(args)
    had = bool(prj.get("pending"))
    prj["pending"] = None
    save_project(prj)
    shutil.rmtree(os.path.join(prj["dir"], "preview"), ignore_errors=True)
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
         "pending": None if not pend else {"operations": len(pend["ops"]), "against": pend["base_head"], "stale": pend["base_head"] != cur["head"],
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
        print("PENDING   %d operation(s) against %s%s: %s" % (len(pend["ops"]), pend["base_head"][:12], " (STALE)" if d["pending"]["stale"] else "",
                                                               "not previewed" if not pv else ("previewed, admissible, head " + pv["head"][:12]) if pv["ok"] else "previewed, REFUSED by the shell"))
    return 0


COMMANDS = {"new": cmd_new, "open": cmd_new, "grant": cmd_grant, "inspect": cmd_inspect, "propose": cmd_propose, "preview": cmd_preview,
            "admit": cmd_admit, "reject": cmd_reject, "undo": cmd_undo, "status": cmd_status}
FLAGS = {"new": ("--project", "--level", "--tiles", "--camera", "--shell"), "open": ("--project", "--session", "--shell"),
         "grant": ("--project", "--allow", "--cells", "--classes"), "inspect": ("--project", "--region", "--json"),
         "propose": ("--project", "--no-predict"), "preview": ("--project", "--region", "--json"), "admit": ("--project",),
         "reject": ("--project",), "undo": ("--project",), "status": ("--project", "--json")}
BARE = ("--json", "--no-predict")


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
