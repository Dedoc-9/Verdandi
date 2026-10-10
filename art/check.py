# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/check.py — ART-GENERATION-0's checks: the art may be bold because it cannot touch play.
#
#   python art/check.py [NAME ...]          every brief in art/briefs/ when no name is given
#
# For each brief: exports the scene twice (the same bytes), then an independent verifier holds the scene to the
# graybox world it dresses, with its own reader and its own arithmetic:
#
#   play      the graybox map's own checks pass on W and C (walls, probes, routes, spawns)
#   collision the scene's collision boxes, laid back onto the grid, are C exactly; the ground is there; no box overlaps
#   envelope  no dressing stands where a player can be: each piece is inside rock, inside a solid top, flat on the
#             floor, flush on a rock face, or above the reach ceiling, which is recomputed here from C and the player
#   no lies   no dressing carries collision, and the scene's own reach ceiling is the one recomputed here
#   sources   every mesh names its source and licence; every material a piece uses is declared
#   lineage   the lineage's hashes are the files' and the scene's own
#
# Then it plants defects and requires the check that should catch each one to refuse it, and it makes two
# revisions in the owner's words: a look revision ("make the wet surfaces less reflective"), which may change the
# materials it names and nothing else; and a layout revision ("make this alley narrower"), compiled and admitted
# through the design tool, after which play must still hold and every piece of the scene that changed must stand
# next to a cell that changed. The layout revision needs the shell; without it the line says SKIPPED, never PASS.
#
# Visual quality is not checked here and cannot be: these checks keep the art from lying about play. Whether the
# art is good is judged from rendered viewpoints, by a person. Standard library only. Ends 0 when nothing failed.

import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import dress  # noqa: E402
level = dress.level

_spec = importlib.util.spec_from_file_location("graybox_check", os.path.join(REPO, "graybox", "check.py"))
gcheck = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gcheck)


# ------------------------------------------------------------------------------------------------ the verifier
def reach_here(S):
    """The reach ceiling, computed again from the scene's C and player, apart from the exporter's code."""
    g, P = S["grid"], S["player"]
    w, h, wall, tops = g["w"], g["h"], g["wall"], S["tops"]
    apex = P["jump"] * P["jump"] / (2.0 * P["gravity"])
    cells = lambda sp: (int(sp["x"] // g["cell"]), int(sp["z"] // g["cell"]))
    start = sorted({cells(sp) for sp in S["spawns"].values()})
    ok, todo = set(start), list(start)
    while todo:
        x, z = todo.pop()
        for a, b in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
            if 0 <= a < w and 0 <= b < h and (a, b) not in ok and tops[b * w + a] < wall and tops[b * w + a] - tops[z * w + x] <= apex:
                ok.add((a, b))
                todo.append((a, b))
    out = []
    for z in range(h):
        for x in range(w):
            near = [tops[b * w + a] for a in (x - 1, x, x + 1) for b in (z - 1, z, z + 1) if (a, b) in ok]
            if near:
                out.append(round(max(near) + P["body"] + apex + P["margin"], 4))
            else:
                out.append(round(tops[z * w + x] + P["body"] + apex + P["margin"], 4) if tops[z * w + x] < wall else None)
    return out


def check_collision(S, C):
    g = S["grid"]
    w, h, cell = g["w"], g["h"], g["cell"]
    if S["tops"] != C["tops"]:
        return False, "the scene's tops are not C's"
    ground = [b for b in S["collision"] if b["kind"] == "ground"]
    if len(ground) != 1 or ground[0]["box"][4] != 0 or ground[0]["box"][0] > 0 or ground[0]["box"][2] > 0 \
            or ground[0]["box"][3] < w * cell or ground[0]["box"][5] < h * cell:
        return False, "the ground is not one slab under the whole grid with its top at 0"
    top = [0.0] * (w * h)
    hits = [0] * (w * h)
    for b in S["collision"]:
        if b["kind"] == "ground":
            continue
        x0, y0, z0, x1, y1, z1 = b["box"]
        gx0, gz0, gx1, gz1 = x0 / cell, z0 / cell, x1 / cell, z1 / cell
        if y0 != 0 or any(abs(v - round(v)) > 1e-9 for v in (gx0, gz0, gx1, gz1)) or gx1 <= gx0 or gz1 <= gz0:
            return False, "the box %s is not a column of whole cells standing on the ground" % b["id"]
        for z in range(int(round(gz0)), int(round(gz1))):
            for x in range(int(round(gx0)), int(round(gx1))):
                if not (0 <= x < w and 0 <= z < h):
                    return False, "the box %s leaves the grid" % b["id"]
                hits[z * w + x] += 1
                top[z * w + x] = y1
    if any(n > 1 for n in hits):
        k = next(i for i, n in enumerate(hits) if n > 1)
        return False, "two boxes overlap at %d,%d" % (k % w, k // w)
    diff = [k for k in range(w * h) if abs(top[k] - C["tops"][k]) > 1e-9]
    if diff:
        return False, "%d cells' collision is not C's (first %d,%d: %s m, C says %s m)" % (len(diff), diff[0] % w, diff[0] // w, top[diff[0]], C["tops"][diff[0]])
    return True, "%d boxes and the ground lay back onto C, cell for cell" % (len(S["collision"]) - 1)


def check_envelope(S, reach):
    g, P = S["grid"], S["player"]
    w, h, cell, wall, tops = g["w"], g["h"], g["cell"], g["wall"], S["tops"]
    rock = lambda x, z: not (0 <= x < w and 0 <= z < h) or tops[z * w + x] >= wall
    for v in S["visuals"]:
        x0, y0, z0, x1, y1, z1 = v["box"]
        if not (x1 > x0 and y1 > y0 and z1 > z0):
            return False, "%s is not a box" % v["id"]
        for z in range(max(0, int(z0 // cell)), min(h, int(-(-z1 // cell)))):
            for x in range(max(0, int(x0 // cell)), min(w, int(-(-x1 // cell)))):
                cx0, cz0, cx1, cz1 = x * cell, z * cell, (x + 1) * cell, (z + 1) * cell
                ox0, ox1, oz0, oz1 = max(x0, cx0), min(x1, cx1), max(z0, cz0), min(z1, cz1)
                if ox1 - ox0 <= 1e-9 or oz1 - oz0 <= 1e-9 or rock(x, z):
                    continue   # no area over this cell, or the cell is rock
                t = tops[z * w + x]
                if y1 <= t + P["flat"] + 1e-9:
                    continue   # inside the solid, or flat on it
                if reach[z * w + x] is not None and y0 >= reach[z * w + x] - 1e-9:
                    continue   # above every head
                flush = ((ox1 - ox0 <= P["flush"] + 1e-9) and ((abs(ox0 - cx0) < 1e-9 and rock(x - 1, z)) or (abs(ox1 - cx1) < 1e-9 and rock(x + 1, z)))) \
                    or ((oz1 - oz0 <= P["flush"] + 1e-9) and ((abs(oz0 - cz0) < 1e-9 and rock(x, z - 1)) or (abs(oz1 - cz1) < 1e-9 and rock(x, z + 1))))
                if flush:
                    continue   # thin, against a rock face
                return False, "%s stands where a player can be, over %d,%d (%.2f to %.2f m; the floor's top %.2f, the reach ceiling %s)" % (
                    v["id"], x, z, y0, y1, t, reach[z * w + x])
    return True, "%d pieces: each inside rock, inside a solid, flat, flush on a rock face, or above every head" % len(S["visuals"])


def sim_player():
    """The player's constants as the graybox runtime declares them, read from graybox/web/sim.js itself."""
    import re
    src = open(os.path.join(REPO, "graybox", "web", "sim.js"), encoding="utf-8").read()
    m = re.search(r"const P = \{([^}]*)\}", src)
    if not m:
        raise ValueError("graybox/web/sim.js declares no player P")
    vals = dict((k, float(v)) for k, v in re.findall(r"(\w+):\s*([0-9.]+)", m.group(1)))
    return {k: vals[k] for k in ("radius", "eye", "step", "speed", "gravity", "jump")}


def check_no_lies(S, reach, W=None):
    sim = sim_player()
    off = [k for k, v in sim.items() if S["player"].get(k) != v]
    if off:
        return False, "the scene's player %s is %s; graybox/web/sim.js says %s" % (off[0], S["player"].get(off[0]), sim[off[0]])
    if W is not None:
        g = S["grid"]
        for k, sp in sorted(W["spawns"].items()):
            got = S["spawns"].get(k, {})
            if (got.get("x"), got.get("z"), got.get("yaw")) != (round((sp["x"] + 0.5) * g["cell"], 4), round((sp["z"] + 0.5) * g["cell"], 4), round(sp["yaw"], 4)):
                return False, "the scene's spawn %s is not W's" % k
    for name, vw in sorted(S.get("views", {}).items()):
        x, z = int(vw["x"] // S["grid"]["cell"]), int(vw["z"] // S["grid"]["cell"])
        if reach[z * S["grid"]["w"] + x] is None or S["tops"][z * S["grid"]["w"] + x] >= S["grid"]["wall"]:
            return False, "the view %s stands in rock" % name
    bad = [v["id"] for v in S["visuals"] if v.get("collision")]
    if bad:
        return False, "%s carries collision: only C decides where a player can go" % bad[0]
    diff = [k for k in range(len(reach)) if reach[k] != S["reach"][k]]
    if diff:
        w = S["grid"]["w"]
        return False, "the scene's reach ceiling at %d,%d is %s; recomputed here it is %s" % (diff[0] % w, diff[0] // w, S["reach"][diff[0]], reach[diff[0]])
    lit = [L["id"] for L in S["lights"] if any(k in L for k in ("box", "collision", "asset"))]
    if lit:
        return False, "the light %s carries geometry" % lit[0]
    return True, "no piece has collision; the player is sim.js's and the spawns W's; the reach ceiling is the one recomputed here; lights are only light"


def check_sources(S):
    for name, a in S["assets"].items():
        if a.get("source") not in dress.SOURCES or not a.get("licence", "").strip() or not a.get("path"):
            return False, "the asset %s does not name its path, its source and its licence" % name
    for v in S["visuals"]:
        if v["asset"] not in S["assets"]:
            return False, "%s uses the asset %s, which the scene does not declare" % (v["id"], v["asset"])
        if v["material"] not in S["materials"]:
            return False, "%s uses the material %s, which the scene does not declare" % (v["id"], v["material"])
    for b in S["collision"]:
        if b["material"] not in S["materials"]:
            return False, "%s uses the material %s, which the scene does not declare" % (b["id"], b["material"])
    return True, "%d asset(s), each with a source and a licence: %s" % (len(S["assets"]), ", ".join(
        "%s (%s, %s)" % (k, a["source"], a["licence"]) for k, a in sorted(S["assets"].items())))


def check_lineage(out, art_path, scene_bytes):
    L = out["lineage"]
    raw = open(art_path, "rb").read().replace(b"\r\n", b"\n") if art_path else None
    if art_path and dress.sha256(raw) != L["art_sha256"]:
        return False, "the art file's bytes are not the ones the lineage names"
    if dress.sha256(scene_bytes) != L["scene_sha256"]:
        return False, "the scene's bytes are not the ones the lineage names"
    if L["canonical_sha256"] != dress.sha256(level.canon(out["W"])) or L["collision_sha256"] != dress.sha256(level.canon(out["C"])):
        return False, "the lineage's world hashes are not W's and C's"
    exp = dress.sha256(open(os.path.join(HERE, "dress.py"), "rb").read().replace(b"\r\n", b"\n"))
    if L["exporter_sha256"] != exp:
        return False, "the lineage names another exporter"
    return True, "art %s, layout head %s, scene %s" % (L["art_sha256"][:12], (L["map_source"].get("layout_head") or "-")[:12], L["scene_sha256"][:12])


def verify(out, art_path, scene_bytes=None, D=None):
    S, W, C = out["scene"], out["W"], out["C"]
    scene_bytes = out["scene_bytes"] if scene_bytes is None else scene_bytes
    reach = reach_here(S)
    res = []
    D = D if D is not None else gcheck.source_rows(W)
    play = [(c, ok, d) for c, ok, d in gcheck.verify(D, W, C)]
    bad = [c for c, ok, _d in play if not ok]
    res.append(("play holds: the graybox map's own checks", not bad, "%d checks%s" % (len(play), (", failed: " + bad[0]) if bad else "")))
    res.append(("collision is C, exactly",) + check_collision(S, C))
    res.append(("no dressing where a player can be",) + check_envelope(S, reach))
    res.append(("the art carries no collision and no false ceiling",) + check_no_lies(S, reach, W))
    res.append(("every mesh names its source and licence",) + check_sources(S))
    res.append(("the lineage binds every input",) + check_lineage(out, art_path, scene_bytes))
    return res


# ------------------------------------------------------------------------------------------------ revisions
def revise(text: str, revision: str, fname: str) -> (str, list):
    """A look revision (VERDANDI-ART-REVISION 0): each statement replaces the art file's one statement with the
    same verb and first argument. Returns the new text and the replaced statements' (verb, name) keys."""
    lines = [ln for ln in revision.splitlines() if ln.split("#", 1)[0].strip()]
    if not lines or lines[0].split("#", 1)[0].strip() != "VERDANDI-ART-REVISION 0":
        raise dress.ArtError("%s: the first line is not 'VERDANDI-ART-REVISION 0'" % fname)
    out, keys = text.splitlines(), []
    for ln in lines[1:]:
        code = ln.split("#", 1)[0].split()
        key = (code[0], code[1] if len(code) > 1 else "")
        at = [i for i, o in enumerate(out) if o.split("#", 1)[0].split()[:2] == list(key)]
        if len(at) != 1:
            raise dress.ArtError("%s: %s %s names %d statements of the art file; a revision replaces exactly one" % (fname, key[0], key[1], len(at)))
        tail = (" #" + out[at[0]].split("#", 1)[1]) if "#" in out[at[0]] else ""
        out[at[0]] = " ".join(code) + tail
        keys.append(key)
    return "\n".join(out) + "\n", keys


def items(S):
    d = {}
    for fam in ("collision", "visuals", "lights"):
        for it in S[fam]:
            d[(fam, it["id"])] = it
    return d


def look_only(S0, S1, keys):
    """A look revision may change the materials it names and the environment statements it names, nothing else."""
    named_m = {k[1] for k in keys if k[0] == "material"}
    env = {k[0] for k in keys} & {"time", "moon", "sun", "fog", "exposure", "bloom", "rain"}
    for f in ("tops", "reach", "collision", "visuals", "lights", "spawns", "views", "grid", "player", "assets"):
        if S0[f] != S1[f]:
            return False, "the look revision changed the scene's %s" % f
    changed = sorted(m for m in set(S0["materials"]) | set(S1["materials"]) if S0["materials"].get(m) != S1["materials"].get(m))
    if not changed or set(changed) - named_m:
        return False, "materials changed: %s; the revision names %s" % (changed or "none", sorted(named_m))
    if S0["environment"] != S1["environment"] and not env:
        return False, "the environment changed and the revision names none of it"
    return True, "only %s changed; play, dressing and lights are byte for byte the same" % ", ".join(changed)


def layout_local(S0, S1, region):
    """After a layout revision: the cells that changed lie in the revision's region, and every piece of the scene that
    changed stands within one cell of a changed cell (a collision box: in a chunk holding one)."""
    g = S0["grid"]
    w, cell = g["w"], g["cell"]
    delta = {(k % w, k // w) for k in range(len(S0["tops"])) if S0["tops"][k] != S1["tops"][k]}
    if not delta:
        return False, "no cell changed"
    x0, z0, x1, z1 = region
    out = sorted(p for p in delta if not (x0 <= p[0] <= x1 and z0 <= p[1] <= z1))
    if out:
        return False, "the cell %d,%d changed, outside the revision's region" % out[0]
    zone = {(x + dx, z + dz) for x, z in delta for dx in (-1, 0, 1) for dz in (-1, 0, 1)}
    chunks = {(x // dress.CHUNK, z // dress.CHUNK) for x, z in delta}
    I0, I1 = items(S0), items(S1)
    moved = sorted(k for k in set(I0) | set(I1) if I0.get(k) != I1.get(k))
    for fam, iid in moved:
        it = I1.get((fam, iid)) or I0.get((fam, iid))
        if fam == "collision":
            cx0, cz0, cx1, cz1 = it["cells"]
            if it["kind"] == "ground" or not any((x // dress.CHUNK, z // dress.CHUNK) in chunks for x in (cx0, cx1) for z in (cz0, cz1)):
                return False, "the collision box %s changed, in a chunk where no cell changed" % iid
        else:
            if fam == "lights":
                px, pz = it["pos"][0], it["pos"][2]
                foot = {(int(px // cell), int(pz // cell))}
            else:
                b = it["box"]
                foot = {(x, z) for x in range(int(b[0] // cell), int(-(-b[3] // cell))) for z in range(int(b[2] // cell), int(-(-b[5] // cell)))}
            if not foot & zone:
                return False, "%s %s changed, away from every changed cell" % (fam, iid)
    fams = {}
    for fam, _i in moved:
        fams[fam] = fams.get(fam, 0) + 1
    return True, "%d cell(s) changed, all in the region; %d piece(s) changed, all beside them (%s); %d unchanged" % (
        len(delta), len(moved), ", ".join("%s %d" % kv for kv in sorted(fams.items())), len(set(I0) & set(I1)) - len([m for m in moved if m in I0 and m in I1]))


def compile_revision(base_design: bytes, revision: bytes):
    """The base layout's design and then the revision, admitted through the design tool in a project of its own.
    Returns (rows, head) of the revised world, or (None, reason)."""
    tool = os.path.join(REPO, "design", "design.py")
    tmp = tempfile.mkdtemp(prefix="art-revision-")

    def run(*a, inp=None):
        cp = subprocess.run([sys.executable, tool] + list(a) + ["--project", tmp], input=inp, capture_output=True, cwd=REPO)
        return cp.returncode, cp.stdout.decode("utf-8", "replace"), cp.stderr.decode("utf-8", "replace")
    try:
        for step in (("new",), ("grant", "--allow", "open,close", "--cells", "0,0,47,31")):
            rc, o, e = run(*step)
            if rc != 0:
                return None, "design.py %s: %s" % (step[0], (e or o).strip()[-160:])
        for text in (base_design, revision):
            for step in (("propose", "-"), ("preview",), ("admit",)):
                rc, o, e = run(*step, inp=text if step[0] == "propose" else None)
                if rc != 0:
                    return None, "design.py %s: %s" % (step[0], (e or o).strip()[-160:])
        rc, o, e = run("inspect", "--json")
        d = json.loads(o)
        grid = [ln[5:] for ln in d["top_view"][2:]]
        cx, cz = (int(v) for v in d["world"]["camera"].split(",")[:2])
        grid[cz] = grid[cz][:cx] + "." + grid[cz][cx + 1:]
        return grid, d["session"]["head"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def shell_available():
    if shutil.which("rustc"):
        return True
    return os.path.exists(os.path.join(REPO, "verify", "build", "shell")) or os.path.exists(os.path.join(REPO, "verify", "build", "shell.exe"))


# ------------------------------------------------------------------------------------------------ plants
def plants(out, art_path):
    """Defects the art could have, each planted in a copy; the named check must refuse it. [(plant, refused, by)]."""
    S, W, C = out["scene"], out["W"], out["C"]
    D = gcheck.source_rows(W)
    res = []

    def judged(label, S2, expect, scene_bytes=None):
        o2 = dict(out, scene=S2)
        failed = [c for c, ok, _d in verify(o2, art_path, scene_bytes=scene_bytes if scene_bytes is not None else out["scene_bytes"], D=D) if not ok]
        res.append((label, expect in failed, ("refused by: " + expect) if expect in failed else "NOT refused by %r (failed: %s)" % (expect, failed or "nothing")))

    w, cell = S["grid"]["w"], S["grid"]["cell"]
    S2 = copy.deepcopy(S)
    i = next(i for i, b in enumerate(S2["collision"]) if b["kind"] == "wall")
    dropped = S2["collision"].pop(i)
    judged("a wall's collision box dropped (%s): a wall you can walk through" % dropped["id"], S2, "collision is C, exactly")
    S2 = copy.deepcopy(S)
    b = next(b for b in S2["collision"] if b["kind"] == "cover")
    b["box"][4] = round(b["box"][4] + 1.0, 4)
    judged("a cover box made 1 m taller than C says (%s)" % b["id"], S2, "collision is C, exactly")
    sx, sz = S["spawns"]["A"]["x"], S["spawns"]["A"]["z"]
    gx, gz = int(sx // cell) + 2, int(sz // cell)
    S2 = copy.deepcopy(S)
    S2["visuals"].append({"id": "plant:wall", "by": "plant", "region": "*", "asset": "cube", "material": "concrete",
                          "box": [gx * cell, 0.0, gz * cell, (gx + 1) * cell, 2.5, (gz + 1) * cell]})
    judged("a decorative wall on open floor at %d,%d: the art deciding a wall" % (gx, gz), S2, "no dressing where a player can be")
    S2 = copy.deepcopy(S)
    can = next((v for v in S2["visuals"] if v["id"].startswith("canopy:")), None)
    if can:
        can["box"][1], can["box"][4] = 3.0, 3.4
        judged("a canopy lowered to 3.0 m, under the reach ceiling (%s)" % can["id"], S2, "no dressing where a player can be")
    S2 = copy.deepcopy(S)
    neon = next((v for v in S2["visuals"] if v["id"].startswith("neon:")), None)
    if neon:
        # a sign pulled 0.3 m off its wall: no longer flush
        if neon["box"][3] - neon["box"][0] < 0.1:
            if neon["id"].endswith(":w"):
                neon["box"][3] = round(neon["box"][0] + 0.3, 4)
            else:
                neon["box"][0] = round(neon["box"][3] - 0.3, 4)
        else:
            if neon["id"].endswith(":n"):
                neon["box"][5] = round(neon["box"][2] + 0.3, 4)
            else:
                neon["box"][2] = round(neon["box"][5] - 0.3, 4)
        judged("a neon sign standing 0.3 m off its wall (%s)" % neon["id"], S2, "no dressing where a player can be")
    S2 = copy.deepcopy(S)
    S2["visuals"][0] = dict(S2["visuals"][0], collision=True)
    judged("a piece of dressing given collision (%s)" % S2["visuals"][0]["id"], S2, "the art carries no collision and no false ceiling")
    S2 = copy.deepcopy(S)
    k = next(k for k, r in enumerate(S2["reach"]) if r is not None)
    S2["reach"][k] = round(S2["reach"][k] - 1.0, 4)
    judged("the scene's reach ceiling lowered 1 m at %d,%d, so a low canopy would pass" % (k % w, k // w), S2, "the art carries no collision and no false ceiling")
    S2 = copy.deepcopy(S)
    S2["player"] = dict(S2["player"], jump=6.0)
    S2["reach"] = reach_here(S2)
    judged("the scene's player jumps 6 m/s, not sim.js's 7, and its ceiling is lowered to match", S2, "the art carries no collision and no false ceiling")
    S2 = copy.deepcopy(S)
    S2["spawns"]["A"] = dict(S2["spawns"]["A"], x=round(S2["spawns"]["A"]["x"] + 2 * cell, 4))
    judged("the scene's spawn A moved a cell from W's", S2, "the art carries no collision and no false ceiling")
    S2 = copy.deepcopy(S)
    S2["assets"]["cube"] = dict(S2["assets"]["cube"], licence="")
    judged("a mesh with no licence", S2, "every mesh names its source and licence")
    S2 = copy.deepcopy(S)
    m0 = sorted(S2["materials"])[0]
    S2["materials"][m0] = dict(S2["materials"][m0], roughness=0.5 if S2["materials"][m0]["roughness"] != 0.5 else 0.6)
    tampered = (json.dumps(S2, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    judged("the scene changed after export, its lineage not (%s)" % m0, S2, "the lineage binds every input", scene_bytes=tampered)
    # through the exporter itself: statements it must refuse
    text = open(art_path, encoding="utf-8").read()
    for label, old, new in (
            ("neon of a material that does not emit", "neon plaza neon_magenta", "neon plaza concrete"),
            ("a canopy whose corners leave its region", "canopy plaza concrete 5.2 19,10 28,11", "canopy plaza concrete 5.2 17,10 28,11"),
            ("a tower in a region never declared", "tower plaza concrete", "tower harbour concrete"),
            ("a mesh from an unnamed source", "asset cube /Engine/BasicShapes/Cube.Cube engine", "asset cube /Engine/BasicShapes/Cube.Cube somewhere"),
            ("a view where no player can stand", "view north-flank   23,8", "view north-flank   23,2")):
        if old not in text:
            res.append(("the exporter refuses " + label, False, "the plant's statement is not in the brief"))
            continue
        try:
            A = dress.parse(text.replace(old, new, 1), os.path.basename(art_path))
            A["name"], A["sha256"] = "plant", "-"
            dress.export(A)
            res.append(("the exporter refuses " + label, False, "the exporter took it"))
        except dress.ArtError as e:
            res.append(("the exporter refuses " + label, True, "refused: " + str(e)[:90]))
    return res


# ------------------------------------------------------------------------------------------------ main
def check_brief(name):
    art_path = os.path.join(dress.BRIEFS, name + ".art")
    lines, failed, skipped = [], 0, 0
    try:
        out = dress.export(dress.load(name))
        again = dress.export(dress.load(name))
    except (dress.ArtError, level.MapError) as e:
        print("FAIL %s: the exporter refused the brief: %s" % (name, e))
        return 1, 0
    print("== %s   scene %s   (%d play boxes, %d dressing pieces, %d lights)" % (
        name, out["lineage"]["scene_sha256"][:12], out["lineage"]["counts"]["collision"], out["lineage"]["counts"]["visuals"], out["lineage"]["counts"]["lights"]))
    lines.append(("the export is deterministic: the same files, the same bytes", out["scene_bytes"] == again["scene_bytes"] and out["lineage"] == again["lineage"], ""))
    lines += verify(out, art_path)
    for c, ok, d in lines:
        print("%s %s%s" % ("PASS" if ok else "FAIL", c, (" — " + d) if d else ""))
        failed += 0 if ok else 1
    for p, refused, by in plants(out, art_path):
        print("%s plant: %s — %s" % ("PASS" if refused else "FAIL", p, by))
        failed += 0 if refused else 1
    # the look revision
    rpath = os.path.join(dress.BRIEFS, name + ".revise-look")
    if os.path.exists(rpath):
        text = open(art_path, encoding="utf-8").read()
        new, keys = revise(text, open(rpath, encoding="utf-8").read(), os.path.basename(rpath))
        A1 = dress.parse(new, name + ".art (revised)")
        A1["name"], A1["sha256"] = name, dress.sha256(new.encode("utf-8"))
        o1 = dress.export(A1)
        ok, d = look_only(out["scene"], o1["scene"], keys)
        print("%s the look revision (%s) changes only the look — %s" % ("PASS" if ok else "FAIL", os.path.basename(rpath), d))
        failed += 0 if ok else 1
        rest = [c for c, okk, _d in verify(o1, None, D=gcheck.source_rows(o1["W"])) if not okk and c != "the lineage binds every input"]
        print("%s the revised scene passes every check — %s" % ("PASS" if not rest else "FAIL", "none failed" if not rest else rest[0]))
        failed += 0 if not rest else 1
        S2 = copy.deepcopy(o1["scene"])
        L = next(L for L in S2["lights"] if L["type"] == "point")
        L["pos"][0] = round(L["pos"][0] + 1.0, 4)
        ok2, d2 = look_only(out["scene"], S2, keys)
        print("%s plant: the look revision also moves a lamp — %s" % ("PASS" if not ok2 else "FAIL", ("refused: " + d2) if not ok2 else "NOT refused"))
        failed += 0 if not ok2 else 1
    # the layout revision
    dpath = os.path.join(dress.BRIEFS, name + ".revise-layout.design")
    if os.path.exists(dpath):
        if not shell_available():
            print("SKIPPED the layout revision (%s): no rustc and no built shell to compile and admit it" % os.path.basename(dpath))
            skipped += 1
        else:
            W0 = out["W"]
            src = W0["source"]
            if "layout" not in src:
                print("FAIL the layout revision: the map's walls are not a design-tool layout")
                failed += 1
            else:
                rtext = open(dpath, "rb").read().replace(b"\r\n", b"\n")
                region = None
                for ln in rtext.decode("utf-8").splitlines():
                    if ln.startswith("# region "):
                        region = [int(v) for v in ln[len("# region "):].replace(",", " ").split()[:4]]
                base = open(os.path.join(level.MAPS, src["layout"].rsplit(".", 1)[0] + ".design"), "rb").read().replace(b"\r\n", b"\n")
                rows, head = compile_revision(base, rtext)
                if rows is None:
                    print("FAIL the layout revision could not be admitted: %s" % head)
                    failed += 1
                else:
                    tmp = tempfile.mkdtemp(prefix="art-maps-")
                    try:
                        for f in os.listdir(level.MAPS):
                            shutil.copy(os.path.join(level.MAPS, f), tmp)
                        with open(os.path.join(tmp, src["layout"]), "w", encoding="utf-8", newline="\n") as fh:
                            fh.write("; VERDANDI LAYOUT 0\n; a revision for art/check.py, admitted through the design tool\n; head     %s\n" % head)
                            fh.write("\n".join(rows) + "\n")
                        A = dress.load(name)
                        saved = level.MAPS
                        level.MAPS = tmp
                        try:
                            o2 = dress.export(A, maps_dir=tmp)
                            D2 = gcheck.source_rows(o2["W"])
                            res = verify(o2, art_path, D=D2)
                        finally:
                            level.MAPS = saved
                        bad = [c for c, okk, _d in res if not okk]
                        print("%s the layout revision (%s), admitted at head %s, keeps every check — %s" % (
                            "PASS" if not bad else "FAIL", os.path.basename(dpath), head[:12], "none failed" if not bad else bad[0]))
                        failed += 0 if not bad else 1
                        ok, d = layout_local(out["scene"], o2["scene"], region or [0, 0, 10 ** 6, 10 ** 6])
                        print("%s the layout revision stays local — %s" % ("PASS" if ok else "FAIL", d))
                        failed += 0 if ok else 1
                        S3 = copy.deepcopy(o2["scene"])
                        far = next(v for v in S3["visuals"] if v["id"].startswith("skyline:"))
                        far["box"][4] = round(far["box"][4] + 3.0, 4)
                        ok3, d3 = layout_local(out["scene"], S3, region or [0, 0, 10 ** 6, 10 ** 6])
                        print("%s plant: the layout revision also raises a skyline block far away (%s) — %s" % (
                            "PASS" if not ok3 else "FAIL", far["id"], ("refused: " + d3) if not ok3 else "NOT refused"))
                        failed += 0 if not ok3 else 1
                    finally:
                        shutil.rmtree(tmp, ignore_errors=True)
    return failed, skipped


def main(argv) -> int:
    names = [a for a in argv if not a.startswith("--")] or sorted(f[:-4] for f in os.listdir(dress.BRIEFS) if f.endswith(".art"))
    failed = skipped = 0
    for name in names:
        f, s = check_brief(name)
        failed += f
        skipped += s
    verdict = "PASSED" if not failed else "FAILED (%d)" % failed
    print("ART CHECKS %s%s" % (verdict, (", %d SKIPPED" % skipped) if skipped else ""))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
