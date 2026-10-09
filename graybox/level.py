# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# graybox/level.py — FPS-GRAYBOX-0's converter: a graybox map to the canonical world and the collision world.
#
#   D  the source: a map file (`GRAYBOX 0`, maps/*.gbx) and the walls and floor it names — a layout file the design
#      compiler produced (maps/*.layout), or a level file of the oracle pinned by its sha256
#   W  the canonical world: every cell's base ('#' rock, '.' floor, '<' '>' stairs), kind, solid top in metres and the
#      source lines that made it; the spawns, the objective, the targets, the probes and the routes
#   C  the collision world: the solid top of every cell and nothing else. The runtime moves the player against C
#      alone; the renderer draws from W and is never asked whether a wall is there
#
# The map's walls and floor are the layout's and nothing here changes them: the overlay adds height, cover and
# gameplay marks to floor cells only. Standard library only. Deterministic: the same files give the same bytes.

import hashlib
import json
import os
import struct

FORMAT = "GRAYBOX 0"
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
MAPS = os.path.join(HERE, "maps")


class MapError(Exception):
    """A map the converter refuses, with the file and line it names."""


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon(obj) -> bytes:
    """The one byte form of a JSON value this converter hashes: sorted keys, no blanks, UTF-8."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _cell(tok: str, w: int, h: int, where: str):
    try:
        x, z = (int(v) for v in tok.split(","))
    except ValueError:
        raise MapError("%s: %r is not a cell x,z" % (where, tok))
    if not (0 <= x < w and 0 <= z < h):
        raise MapError("%s: the cell %d,%d is outside the %d x %d grid" % (where, x, z, w, h))
    return x, z


def _rect(toks, w, h, where):
    a = _cell(toks[0], w, h, where)
    b = _cell(toks[1], w, h, where) if len(toks) > 1 else a
    return min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])


def _metres(tok: str, where: str) -> float:
    try:
        v = float(tok)
    except ValueError:
        raise MapError("%s: %r is not a number of metres" % (where, tok))
    if not (0 <= v <= 100):
        raise MapError("%s: %r metres is out of range" % (where, tok))
    return v


def read_layout(path: str):
    """A layout file: header lines starting ';', then the grid's rows. Returns (rows, header, raw bytes)."""
    raw = open(path, "rb").read()
    header, rows = {}, []
    for n, ln in enumerate(raw.decode("utf-8").splitlines(), start=1):
        if ln.startswith(";"):
            parts = ln[1:].split()
            if len(parts) >= 2 and parts[0] in ("design", "parent", "head", "content"):
                header[parts[0]] = parts[-1]
            continue
        if ln.strip() == "":
            continue
        if any(c not in "#.<>" for c in ln):
            raise MapError("%s line %d: a layout row holds only '#', '.', '<' and '>'" % (os.path.basename(path), n))
        rows.append(ln)
    if not rows or len({len(r) for r in rows}) != 1:
        raise MapError("%s: the layout's rows are missing or of unequal length" % os.path.basename(path))
    return rows, header, raw


def read_level(path: str):
    """A level file of the oracle (VRDNLVL1): its cells as rows."""
    raw = open(path, "rb").read()
    if raw[:8] != b"VRDNLVL1":
        raise MapError("%s is not a VRDNLVL1 level" % path)
    w, h = struct.unpack("<II", raw[8:16])
    cells = raw[16:16 + w * h].decode("ascii")
    rows = [cells[z * w:(z + 1) * w] for z in range(h)]
    if any(c not in "#.<>" for c in cells):
        raise MapError("%s holds a cell that is not '#', '.', '<' or '>'" % path)
    return rows, raw


def convert(name: str) -> dict:
    """The map `name` (maps/<name>.gbx) converted: {"canonical": W, "collision": C, "manifest": M}."""
    gpath = os.path.join(MAPS, name + ".gbx")
    graw = open(gpath, "rb").read()
    lines = graw.decode("utf-8").splitlines()
    fname = os.path.basename(gpath)
    stmts = []
    for n, ln in enumerate(lines, start=1):
        code = ln.split("#", 1)[0].split()
        if code:
            stmts.append((n, code))
    if not stmts or " ".join(stmts[0][1]) != FORMAT:
        raise MapError("%s: the first line is not %r" % (fname, FORMAT))
    source = {"map": fname, "map_sha256": sha256(graw)}
    rows = None
    W = {"format": "VERDANDI-GRAYBOX-WORLD 0", "name": name, "cell": 2.0, "wall": 4.0, "spawns": {}, "objective": None,
         "targets": [], "probes": [], "routes": {}}
    # the walls and floor come first, from the layout or the level
    for n, code in stmts[1:]:
        where = "%s line %d" % (fname, n)
        if code[0] == "name":
            W["name"] = code[1]
        elif code[0] == "layout":
            lpath = os.path.normpath(os.path.join(MAPS, code[1]))
            rows, header, lraw = read_layout(lpath)
            source.update({"layout": code[1], "layout_sha256": sha256(lraw), "layout_design_sha256": header.get("design"),
                           "layout_parent": header.get("parent"), "layout_head": header.get("head"), "layout_content": header.get("content")})
        elif code[0] == "level":
            lpath = os.path.normpath(os.path.join(REPO, code[1]))
            rows, lraw = read_level(lpath)
            if len(code) < 3 or sha256(lraw) != code[2]:
                raise MapError("%s: %s is not the level pinned here (its sha256 is %s)" % (where, code[1], sha256(lraw)))
            source.update({"level": code[1], "level_sha256": code[2]})
        elif code[0] in ("cell", "wall"):
            W[code[0]] = _metres(code[1], where)
    if rows is None:
        raise MapError("%s: no layout and no level names the walls and floor" % fname)
    w, h = len(rows[0]), len(rows)
    W.update({"w": w, "h": h})
    lay = source.get("layout") or source.get("level")
    cells = []
    for z in range(h):
        for x in range(w):
            b = rows[z][x]
            kind = {"#": "wall", ".": "floor", "<": "stair", ">": "stair"}[b]
            cells.append({"base": b, "kind": kind, "top": W["wall"] if b == "#" else 0.0, "src": ["%s:%d,%d" % (lay, x, z)]})
    floor = lambda x, z: cells[z * w + x]["base"] != "#"

    def need_floor(x0, z0, x1, z1, where, what):
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                if not floor(x, z):
                    raise MapError("%s: %s at %d,%d, a rock cell of the layout: the overlay adds to floor and never moves a wall" % (where, what, x, z))

    # then the overlay, statement by statement, each on floor cells only
    for n, code in stmts[1:]:
        where = "%s line %d" % (fname, n)
        tag = "%s:%d" % (fname, n)
        verb, args = code[0], code[1:]
        if verb in ("name", "layout", "level", "cell", "wall"):
            continue
        if verb in ("height", "cover"):
            r = _rect(args[:-1], w, h, where)
            top = _metres(args[-1], where)
            need_floor(*r, where, verb)
            if not 0 < top < W["wall"]:
                raise MapError("%s: %s of %s m is not between the floor and the wall's top" % (where, verb, args[-1]))
            for z in range(r[1], r[3] + 1):
                for x in range(r[0], r[2] + 1):
                    c = cells[z * w + x]
                    if verb == "cover" and top <= c["top"]:
                        raise MapError("%s: cover at %d,%d is not above the floor it stands on" % (where, x, z))
                    c["top"] = top
                    c["kind"] = "cover" if verb == "cover" else "raised"
                    c["src"].append(tag)
        elif verb == "spawn":
            if len(args) != 3 or args[0] not in ("A", "B"):
                raise MapError("%s: spawn takes a side A or B, a cell and a yaw in degrees" % where)
            x, z = _cell(args[1], w, h, where)
            need_floor(x, z, x, z, where, "spawn")
            W["spawns"][args[0]] = {"x": x, "z": z, "yaw": float(args[2]) % 360.0, "src": tag}
        elif verb == "objective":
            r = _rect(args, w, h, where)
            need_floor(*r, where, "objective")
            W["objective"] = {"rect": list(r), "src": tag}
        elif verb == "target":
            x, z = _cell(args[0], w, h, where)
            need_floor(x, z, x, z, where, "target")
            W["targets"].append({"id": "T%d" % (len(W["targets"]) + 1), "x": x, "z": z, "src": tag})
        elif verb == "probe":
            if len(args) != 2 or args[0] not in ("wall", "open"):
                raise MapError("%s: probe takes wall or open, and a cell" % where)
            x, z = _cell(args[1], w, h, where)
            W["probes"].append({"expect": args[0], "x": x, "z": z, "src": tag})
        elif verb == "route":
            if len(args) < 3:
                raise MapError("%s: route takes a name and at least two cells" % where)
            pts = [_cell(t, w, h, where) for t in args[1:]]
            for x, z in pts:
                need_floor(x, z, x, z, where, "a route's waypoint")
            W["routes"][args[0]] = {"cells": [list(p) for p in pts], "src": tag}
        else:
            raise MapError("%s: %r is not a statement of %s" % (where, verb, FORMAT))
    for side in ("A", "B"):
        if side not in W["spawns"]:
            raise MapError("%s: no spawn %s" % (fname, side))
    # spawns, targets and the objective's cells stand on open floor, not on cover
    for what, x, z in [("spawn " + k, v["x"], v["z"]) for k, v in W["spawns"].items()] + [("target " + t["id"], t["x"], t["z"]) for t in W["targets"]]:
        if cells[z * w + x]["kind"] == "cover":
            raise MapError("%s: %s stands on cover" % (fname, what))
    W["cells"] = [[c["base"], c["kind"], c["top"], c["src"]] for c in cells]
    W["source"] = source
    C = {"format": "VERDANDI-GRAYBOX-COLLISION 0", "w": w, "h": h, "cell": W["cell"], "tops": [c["top"] for c in cells]}
    M = {"format": "VERDANDI-GRAYBOX-MANIFEST 0", "map": name, "source": source,
         "converter_sha256": sha256(open(os.path.abspath(__file__), "rb").read().replace(b"\r\n", b"\n")),
         "canonical_sha256": sha256(canon(W)), "collision_sha256": sha256(canon(C))}
    return {"canonical": W, "collision": C, "manifest": M}


def names() -> list:
    return sorted(f[:-4] for f in os.listdir(MAPS) if f.endswith(".gbx"))


if __name__ == "__main__":
    import sys
    for nm in sys.argv[1:] or names():
        out = convert(nm)
        print(json.dumps(out["manifest"], indent=1, sort_keys=True))
