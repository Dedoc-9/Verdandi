# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# graybox/check.py — FPS-GRAYBOX-0's map checks, for a change of map content.
#
#   python graybox/check.py [MAP ...] [--compile]
#
# For each map: converts it (level.py), then an independent verifier V(D, W, C) reads the source D again with its own
# reader and holds the canonical world W and the collision world C to it — walls and floor as the source says,
# collision as the canonical world says, provenance on every cell, spawns on open floor, probes that block or stay
# open, routes and the bases connected — by its own breadth-first search over C, not the runtime's. Then it plants
# defects the conversion could have (an opening collapsed, a spawn in a wall, an invisible blocker, a wall made
# passable, provenance stripped) and requires V to refuse each. It writes each map's manifest to graybox/build/.
# With --compile it also gives the tactical layout's design text to the design tool, in a project of its own, and
# requires the shell's compiler and admission to reach the layout and head the layout file records.
# Standard library only. Ends 0 when every check passes.

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import level  # noqa: E402

STEP = 0.55   # the runtime's step height (sim.js), the one constant the verifier shares with it


def source_rows(W):
    """D's walls and floor, read again here from the file the map names, apart from the converter's reader."""
    src = W["source"]
    if "layout" in src:
        raw = open(os.path.join(level.MAPS, src["layout"]), "rb").read()
        if level.sha256(raw) != src["layout_sha256"]:
            raise ValueError("the layout's bytes are not the ones the converter read")
        return [ln for ln in raw.decode("utf-8").splitlines() if ln and not ln.startswith(";")]
    raw = open(os.path.join(level.REPO, src["level"]), "rb").read()
    if level.sha256(raw) != src["level_sha256"]:
        raise ValueError("the level's bytes are not the pinned ones")
    w = int.from_bytes(raw[8:12], "little"); h = int.from_bytes(raw[12:16], "little")
    return [raw[16 + z * w:16 + (z + 1) * w].decode("ascii") for z in range(h)]


def bfs(C, wall, a, b):
    """A path over C from cell a to cell b, a step up of at most STEP at a time; None if there is none."""
    w, h, tops = C["w"], C["h"], C["tops"]
    seen, frontier = {tuple(a): None}, [tuple(a)]
    while frontier:
        nxt = []
        for p in frontier:
            if p == tuple(b):
                path = [p]
                while seen[path[-1]] is not None:
                    path.append(seen[path[-1]])
                return path[::-1]
            for d in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                n = (p[0] + d[0], p[1] + d[1])
                if not (0 <= n[0] < w and 0 <= n[1] < h) or n in seen:
                    continue
                tn, tp = tops[n[1] * w + n[0]], tops[p[1] * w + p[0]]
                if tn >= wall or tn - tp > STEP:
                    continue
                seen[n] = p
                nxt.append(n)
        frontier = nxt
    return None


def verify(D, W, C):
    """V(D, W, C): a list of (check, ok, detail)."""
    out = []
    w, h, wall = W["w"], W["h"], W["wall"]
    lay = W["source"].get("layout") or W["source"].get("level")
    rock = lambda x, z: D[z][x] == "#"
    # walls and floor: as the source says, in W and in C
    bad = [(x, z) for z in range(h) for x in range(w)
           if (W["cells"][z * w + x][0] != D[z][x]) or (rock(x, z) != (C["tops"][z * w + x] >= wall)) or (rock(x, z) != (W["cells"][z * w + x][1] == "wall"))]
    out.append(("walls and floor as the source says", not bad and len(D) == h and all(len(r) == w for r in D),
                "%d cells differ%s" % (len(bad), (" (first %d,%d)" % bad[0]) if bad else "")))
    # collision is the canonical world's
    diff = [k for k in range(w * h) if C["tops"][k] != W["cells"][k][2]]
    out.append(("collision as the canonical world says", not diff and C["w"] == w and C["h"] == h, "%d cells differ" % len(diff)))
    # provenance on every cell; every lifted cell names the map line that lifted it
    lost = [k for k in range(w * h) if not any(s.startswith(lay + ":") for s in W["cells"][k][3])
            or (W["cells"][k][1] in ("cover", "raised") and not any(s.startswith(W["source"]["map"] + ":") for s in W["cells"][k][3]))]
    out.append(("provenance on every cell", not lost, "%d cells without their source" % len(lost)))
    # spawns on open floor of the source, not on cover
    for side, sp in sorted(W["spawns"].items()):
        k = sp["z"] * w + sp["x"]
        ok = not rock(sp["x"], sp["z"]) and W["cells"][k][1] not in ("cover", "wall") and C["tops"][k] < wall
        out.append(("spawn %s on open floor" % side, ok, "cell %d,%d" % (sp["x"], sp["z"])))
    # probes, held against C
    a = (W["spawns"]["A"]["x"], W["spawns"]["A"]["z"])
    for p in W["probes"]:
        k = p["z"] * w + p["x"]
        if p["expect"] == "wall":
            ns = [(p["x"] + d[0], p["z"] + d[1]) for d in ((0, 1), (1, 0), (0, -1), (-1, 0))]
            ns = [n for n in ns if 0 <= n[0] < w and 0 <= n[1] < h and C["tops"][n[1] * w + n[0]] < wall]
            ok = all(C["tops"][k] - C["tops"][n[1] * w + n[0]] > STEP for n in ns) and C["tops"][k] >= wall
            out.append(("probe wall %d,%d blocks" % (p["x"], p["z"]), ok, "top %s m, %d open neighbour(s)" % (C["tops"][k], len(ns))))
        else:
            ok = C["tops"][k] < wall and bfs(C, wall, a, (p["x"], p["z"])) is not None
            out.append(("probe open %d,%d reachable from spawn A" % (p["x"], p["z"]), ok, "top %s m" % C["tops"][k]))
    # routes, the bases and the objective, connected over C
    paths = {}
    for name, r in sorted(W["routes"].items()):
        pts, path, broken = r["cells"], [tuple(r["cells"][0])], None
        for i in range(1, len(pts)):
            seg = bfs(C, wall, pts[i - 1], pts[i])
            if seg is None:
                broken = pts[i]
                break
            path += seg[1:]
        paths[name] = path
        out.append(("route %s connected" % name, broken is None, "%d cells" % len(path) if broken is None else "no path to %d,%d" % tuple(broken)))
    b = (W["spawns"]["B"]["x"], W["spawns"]["B"]["z"])
    out.append(("spawn A to spawn B", bfs(C, wall, a, b) is not None, ""))
    if W["objective"]:
        o = W["objective"]["rect"]
        out.append(("spawn A to the objective", bfs(C, wall, a, (o[0], o[1])) is not None, "cell %d,%d" % (o[0], o[1])))
    if len(paths) >= 3:
        names = sorted(paths)
        same = [(m, n) for i, m in enumerate(names) for n in names[i + 1:]
                if len(set(paths[m]) & set(paths[n])) / len(set(paths[m]) | set(paths[n])) >= 0.5]
        out.append(("the routes are distinct", not same, "%d routes; pairs sharing half their cells: %s" % (len(names), same or "none")))
    return out


def mutations(name, D, W, C):
    """Defects the conversion could have, each planted in a copy; V must refuse every one. [(mutation, refused, by)]."""
    w = W["w"]
    res = []

    def judged(label, D2, W2, C2):
        failed = [c for c, ok, _d in verify(D2, W2, C2) if not ok]
        res.append((label, bool(failed), failed[0] if failed else "nothing"))

    opens = [p for p in W["probes"] if p["expect"] == "open"]
    walls = [p for p in W["probes"] if p["expect"] == "wall"]
    route = next(iter(sorted(W["routes"].items())))[1]["cells"]
    if opens:
        p = opens[0]; k = p["z"] * w + p["x"]
        W2, C2 = copy.deepcopy(W), copy.deepcopy(C)
        W2["cells"][k][0], W2["cells"][k][1], W2["cells"][k][2] = "#", "wall", W["wall"]; C2["tops"][k] = W["wall"]
        judged("an opening collapsed by the conversion (%d,%d)" % (p["x"], p["z"]), D, W2, C2)
        D2 = list(D); D2[p["z"]] = D2[p["z"]][:p["x"]] + "#" + D2[p["z"]][p["x"] + 1:]
        W3, C3 = copy.deepcopy(W2), copy.deepcopy(C2)
        judged("an opening collapsed in the source (%d,%d)" % (p["x"], p["z"]), D2, W3, C3)
    rx, rz = next((x, z) for z, row in enumerate(D) for x, ch in enumerate(row) if ch == "#")
    W2 = copy.deepcopy(W); W2["spawns"]["A"] = dict(W2["spawns"]["A"], x=rx, z=rz)
    judged("spawn A moved into a wall (%d,%d)" % (rx, rz), D, W2, C)
    mid = route[len(route) // 2] if len(route) > 2 else route[-1]
    seg = bfs(C, W["wall"], route[0], route[1]) or [tuple(route[0])]
    blk = seg[len(seg) // 2]
    C2 = copy.deepcopy(C); C2["tops"][blk[1] * w + blk[0]] = W["wall"]
    judged("an invisible blocker on a route (%d,%d)" % blk, D, W, C2)
    if walls:
        p = walls[0]; C2 = copy.deepcopy(C); C2["tops"][p["z"] * w + p["x"]] = 0.0
        judged("a wall made passable in collision (%d,%d)" % (p["x"], p["z"]), D, W, C2)
    W2 = copy.deepcopy(W); W2["cells"][mid[1] * w + mid[0]][3] = []
    judged("provenance stripped from a cell (%d,%d)" % tuple(mid), D, W2, C)
    # through the converter itself: a spawn written into a wall in the map file is refused there
    tmp = tempfile.mkdtemp(prefix="graybox-mut-")
    try:
        for f in os.listdir(level.MAPS):
            shutil.copy(os.path.join(level.MAPS, f), tmp)
        gbx = os.path.join(tmp, name + ".gbx")
        t = open(gbx, encoding="utf-8").read()
        sp = W["spawns"]["A"]
        t = t.replace("spawn A %d,%d " % (sp["x"], sp["z"]), "spawn A %d,%d " % (rx, rz), 1)
        open(gbx, "w", encoding="utf-8", newline="\n").write(t)
        saved = level.MAPS
        level.MAPS = tmp
        try:
            level.convert(name)
            res.append(("spawn A written into a wall in the map file", False, "the converter took it"))
        except level.MapError as e:
            res.append(("spawn A written into a wall in the map file", True, "the converter refused it: " + str(e)[:80]))
        finally:
            level.MAPS = saved
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return res


def compile_layout():
    """The tactical layout's design given to the design tool in a project of its own: the shell's compiler and its
    admission must reach the head and the walls and floor that tactical.layout records."""
    design = os.path.join(level.MAPS, "tactical.design")
    rows, header, _raw = level.read_layout(os.path.join(level.MAPS, "tactical.layout"))
    tool = os.path.join(level.REPO, "design", "design.py")
    tmp = tempfile.mkdtemp(prefix="graybox-compile-")
    # bytes in and out: a text-mode pipe on Windows would turn the design's LF into CR LF, and the design's id with it
    def run(*a, inp=None):
        cp = subprocess.run([sys.executable, tool] + list(a) + ["--project", tmp], input=inp, capture_output=True, cwd=level.REPO)
        return subprocess.CompletedProcess(cp.args, cp.returncode, cp.stdout.decode("utf-8", "replace"), cp.stderr.decode("utf-8", "replace"))
    text = open(design, "rb").read().replace(b"\r\n", b"\n")
    try:
        for step in (("new",), ("grant", "--allow", "open,close", "--cells", "0,0,47,31")):
            cp = run(*step)
            if cp.returncode != 0:
                return False, "design.py %s: %s" % (step[0], (cp.stderr or cp.stdout).strip()[-200:])
        for step in (("propose", "-"), ("preview",), ("admit",)):
            cp = run(*step, inp=text if step[0] == "propose" else None)
            if cp.returncode != 0:
                return False, "design.py %s: %s" % (step[0], (cp.stderr or cp.stdout).strip()[-200:])
        d = json.loads(run("inspect", "--json").stdout)
        grid = [ln[5:] for ln in d["top_view"][2:]]
        cx, cz = (int(v) for v in d["world"]["camera"].split(",")[:2])
        grid[cz] = grid[cz][:cx] + "." + grid[cz][cx + 1:]
        same = grid == rows and d["session"]["head"] == header.get("head")
        return same, "head %s; %s" % (d["session"]["head"][:12], "the walls and floor are the layout's" if grid == rows else "the walls and floor differ from the layout")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv) -> int:
    names = [a for a in argv if not a.startswith("--")] or level.names()
    failed = 0
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    for name in names:
        try:
            out = level.convert(name)
        except level.MapError as e:
            print("FAIL %s: the converter refused the map: %s" % (name, e))
            failed += 1
            continue
        W, C, M = out["canonical"], out["collision"], out["manifest"]
        D = source_rows(W)
        print("== %s   canonical %s   collision %s" % (name, M["canonical_sha256"][:12], M["collision_sha256"][:12]))
        checks = verify(D, W, C)
        for c, ok, d in checks:
            print("%s %s%s" % ("PASS" if ok else "FAIL", c, (" — " + d) if d else ""))
        muts = mutations(name, D, W, C)
        for m, refused, by in muts:
            print("%s mutation: %s — %s" % ("PASS" if refused else "FAIL", m, ("refused: " + by) if refused else "NOT refused"))
        failed += sum(1 for _c, ok, _d in checks if not ok) + sum(1 for _m, r, _b in muts if not r)
        M = dict(M, conformance={"checks": [[c, ok] for c, ok, _d in checks], "mutations": [[m, r] for m, r, _b in muts]})
        with open(os.path.join(HERE, "build", name + ".manifest.json"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(M, indent=1, sort_keys=True) + "\n")
    if "--compile" in argv:
        ok, detail = compile_layout()
        print("%s the tactical layout compiled and admitted again through the design tool — %s" % ("PASS" if ok else "FAIL", detail))
        failed += 0 if ok else 1
    print("GRAYBOX MAP CHECKS %s" % ("PASSED" if not failed else "FAILED (%d)" % failed))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
