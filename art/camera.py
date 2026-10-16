# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/camera.py — PATH-0 (0241, Phase I's B5a): the preview's camera path, and the rule it holds.
#
#   python art/camera.py selftest      the rule against boxes worked by hand, a planted interior pose and a planted
#                                      wall-crossing segment refused, every path of every world held to it, the same
#                                      seed and world to the same path, a facade's arc seeing its focus, the plants
#
# THE RULE (exact). Every box of the scene is an obstacle: its play geometry (collision), its dressing (visuals: the
# buildings, their bays, towers, skyline, canopies, lamps' housings, neon, puddles), every mover over its whole travel
# and every target's column as it stands up. A pose is clear when it is at least MARGIN (0.5 m) from every obstacle in
# the max norm (outside every box grown by MARGIN on each side; on its face counts as clear) and at least MARGIN above
# the ground plane. A segment between two consecutive poses is clear when no point of it lies inside a grown box. Both
# are decided in exact rational arithmetic from the numbers as the scene and the path write them (Python's Fraction of
# their decimal form); floats only choose which candidate poses to try. The path is open: the camera goes from the first
# pose to the last and does not return. Sight (recorded, not required): the line from a pose to its focus, its last
# SIGHT_TRIM metres left out (the surface the focus lies on), passes inside no box as it is.
#
# What the rule does not say: that a pose frames its subject well. Clearance is a geometric condition; the framing is
# a person's to judge (the owner reviews a world's reference path by eye before freezing it).
#
# THE PATH. With a face (a shape's normal), POSES poses on an arc of ARC degrees in front of it, its start turned a few
# degrees by the seed; without one, an orbit, its start angle the seed's. Each pose looks at the focus. For each pose in
# turn the candidates are tried in a fixed order (the radius, the rise, a small turn) and the first that is clear, whose
# segment from the pose before is clear and that sees the focus is taken; failing sight, the first clear one; failing
# that the pose is skipped and named. Fewer than MIN_POSES poses: no path (CameraError). The same scene, focus, normal
# and seed give the same path, byte for byte; its id is the sha256 of its canonical form. Standard library only.

import hashlib
import json
import math
import os
import sys
import time
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))

MARGIN = Fraction(1, 2)           # metres, max norm
SIGHT_TRIM = 0.75                 # metres of the sight line left out at the focus
POSES = 8
MIN_POSES = 4
ARC = 120.0                       # degrees in front of a face
RADII = (14.0, 11.0, 17.0, 8.0, 20.0, 5.0)
RISES = (6.0, 4.0, 9.0, 2.5)
TURNS = (0.0, 7.0, -7.0, 14.0, -14.0)
RULE = "clear: >= 0.5 m from every box (max norm) and >= 0.5 m above the ground plane; consecutive poses' segments inside no grown box; exact"

# FRAME-0 (0243, B5b): with a subject (the marked region of a face), the arc is framed for it
FRAME_RADII = (5.0, 6.0, 8.0, 10.0, 12.0, 14.0, 17.0, 20.0)
FRAME_AREA = 24 * 24              # px at the preview's 480 x 270: LEGIBLE-0's size, borrowed again
FRAME_SEEN = 0.5                  # a majority of the subject seen
FRAME_INSET = 0.05                # its four corners inside the still less 5% at each edge
SUBJECT_OFFSET = 0.1              # m: the subject's points sampled in front of the face (a bay stands out 4-5 cm)
FRAME_RULE = ("framed: at every pose the subject's four corners inside the still less 5% at each edge, at least half of it seen "
              "(exact occlusion, 0.1 m in front of the face) and at least 24 x 24 px; among the rings that hold PATH-0 and this, the one "
              "whose smallest subject is largest")

PLANT = ""
PLANTS = ("camera-endpoints-only", "camera-no-margin", "camera-visuals-ignored", "frame-any-ring")


class CameraError(Exception):
    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code, self.detail = code, detail


def enc(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def q(v):
    """A number as the scene or the path writes it, exactly."""
    return Fraction(repr(float(v))) if not isinstance(v, (int, Fraction)) else Fraction(v)


# ------------------------------------------------------------------------------------------------ the obstacles
def obstacles(scene):
    """[(id, box)] of every box of the scene, box = [x0, y0, z0, x1, y1, z1] in metres as the scene writes them."""
    out = [(c.get("id", "collision"), list(c["box"])) for c in scene.get("collision", [])]
    if PLANT != "camera-visuals-ignored":
        out += [(v["id"], list(v["box"])) for v in scene.get("visuals", [])]
    for m in scene.get("movers", []):
        d = m["len"] / 256.0
        b = list(m["box"])
        for i, a in enumerate(m["axis"]):
            if a > 0:
                b[i + 3] += d
            elif a < 0:
                b[i] -= d
        out.append(("mover:" + m["id"], b))
    for k, t in sorted((scene.get("targets") or {}).items()):
        if "x" not in t or "z" not in t:
            continue
        x, y, z = t["x"], t.get("y", 0.0), t["z"]
        out.append(("target:" + k, [x - 0.4, y, z - 0.4, x + 0.4, y + 1.9, z + 0.4]))
    return out


def _grown(box, m):
    return [q(box[i]) - m for i in range(3)] + [q(box[i]) + m for i in range(3, 6)]


def _margin():
    return Fraction(0) if PLANT == "camera-no-margin" else MARGIN


def inside(p, g):
    """p strictly inside the box g (exact)."""
    return all(g[i] < p[i] < g[i + 3] for i in range(3))


def crosses(p, r, g):
    """Some point of the segment p-r strictly inside the box g (exact slab test)."""
    lo, hi = Fraction(0), Fraction(1)
    for i in range(3):
        d = r[i] - p[i]
        if d == 0:
            if not (g[i] < p[i] < g[i + 3]):
                return False
            continue
        t1, t2 = (g[i] - p[i]) / d, (g[i + 3] - p[i]) / d
        if t1 > t2:
            t1, t2 = t2, t1
        lo, hi = max(lo, t1), min(hi, t2)
        if lo >= hi:
            return False
    return lo < hi


def point(pose):
    return [q(pose["x"]), q(pose["y"]), q(pose["z"])]


def _violations(grown, pts):
    m = _margin()
    bad = []
    for k, p in enumerate(pts):
        if p[1] < m:
            bad.append({"code": "CAMERA-LOW", "pose": k, "box": "ground plane"})
        for i, g in grown:
            if inside(p, g):
                bad.append({"code": "CAMERA-INSIDE", "pose": k, "box": i})
    if PLANT != "camera-endpoints-only":
        for k in range(len(pts) - 1):
            for i, g in grown:
                if crosses(pts[k], pts[k + 1], g):
                    bad.append({"code": "CAMERA-CROSSES", "segment": [k, k + 1], "box": i})
    return bad


def _grown_all(scene):
    m = _margin()
    return [(i, _grown(b, m)) for i, b in obstacles(scene)]


def check(scene, path):
    """Every way the path breaks the rule, exactly: [{code, pose | segment, box}] (empty when it holds).
    CAMERA-INSIDE: a pose nearer than MARGIN to a box (or inside it); CAMERA-LOW: a pose nearer than MARGIN to the
    ground plane; CAMERA-CROSSES: a segment between consecutive poses through a grown box."""
    return _violations(_grown_all(scene), [point(p) for p in path["poses"]])


def sight(scene, path):
    """For each pose, whether its line to the focus (less the last SIGHT_TRIM m) passes inside no box (exact)."""
    f = [q(v) for v in path["focus"]]
    boxes = [_grown(b, 0) for _i, b in obstacles(scene)]
    out = []
    for pose in path["poses"]:
        p = point(pose)
        d = [p[i] - f[i] for i in range(3)]
        n = math.sqrt(sum(float(v) * float(v) for v in d))
        if n <= SIGHT_TRIM:
            out.append(True)
            continue
        t = q(round(SIGHT_TRIM / n, 6))
        e = [f[i] + d[i] * t for i in range(3)]
        out.append(not any(crosses(p, e, g) for g in boxes))
    return out


# ------------------------------------------------------------------------------------------------ the path
def _f_inside(p, b, m):
    return all(b[i] - m < p[i] < b[i + 3] + m for i in range(3))


def _f_crosses(p, r, b, m):
    lo, hi = 0.0, 1.0
    for i in range(3):
        d = r[i] - p[i]
        a0, a1 = b[i] - m, b[i + 3] + m
        if abs(d) < 1e-12:
            if not (a0 < p[i] < a1):
                return False
            continue
        t1, t2 = (a0 - p[i]) / d, (a1 - p[i]) / d
        if t1 > t2:
            t1, t2 = t2, t1
        lo, hi = max(lo, t1), min(hi, t2)
        if lo >= hi:
            return False
    return lo < hi


def _pose(f, a, radius, rise):
    x, z, y = f[0] + radius * math.sin(a), f[2] - radius * math.cos(a), f[1] + rise
    yaw = math.degrees(math.atan2(f[0] - x, -(f[2] - z))) % 360
    pitch = -math.degrees(math.atan2(y - f[1], math.hypot(f[0] - x, f[2] - z)))
    return {"x": round(x, 3), "y": round(y, 3), "z": round(z, 3), "yaw_deg": round(yaw, 3), "pitch_deg": round(pitch, 3)}


def _f_sight(p, f, obs):
    d = [p[i] - f[i] for i in range(3)]
    n = math.sqrt(sum(v * v for v in d))
    if n <= SIGHT_TRIM:
        return True
    e = [f[i] + d[i] * SIGHT_TRIM / n for i in range(3)]
    return not any(_f_crosses(p, e, b, 0.0) for _i, b in obs)


def _ring(f, angles, radius, rise, obs, grown, fm, need_sight, skip):
    """One radius and one rise for every pose (the same distance from the focus all round), each pose turned at most a
    little to clear; or, with `skip`, any radius and rise for each pose and a pose that cannot clear left out."""
    poses, prev, prevx, skipped = [], None, None, []
    tries = [(radius, rise, t) for t in TURNS] if not skip else [(r_, h_, t) for r_ in RADII for h_ in RISES for t in TURNS]
    for k, a in enumerate(angles):
        took = None
        for r_, h_, t in tries:
            c = _pose(f, math.radians(a + t), r_, h_)
            p = (c["x"], c["y"], c["z"])
            if p[1] < fm or any(_f_inside(p, b, fm) for _i, b in obs):
                continue
            if prev is not None and any(_f_crosses(prev, p, b, fm) for _i, b in obs):
                continue
            if need_sight and not _f_sight(p, f, obs):
                continue
            px = point(c)
            if _violations(grown, ([prevx] if prevx else []) + [px]):
                continue
            took = c
            break
        if took is None:
            if not skip:
                return None
            skipped.append(k)
            continue
        poses.append(took)
        prev, prevx = (took["x"], took["y"], took["z"]), point(took)
    return poses, skipped


def subject_of(shapes):
    """FRAME-0: the first shape on an upright face, as {shape, corners, normal}: the rectangle round its vertices in the
    face's plane (its corners in order round it), or None."""
    for s_ in shapes or ():
        w, n = s_.get("world_m") or [], (s_.get("face") or {}).get("normal")
        if len(w) < 3 or not n or abs(float(n[1])) > 1e-9:
            continue
        xs, ys, zs = [p[0] for p in w], [p[1] for p in w], [p[2] for p in w]
        y0, y1 = min(ys), max(ys)
        if float(n[2]):
            z = zs[0]
            c = [[min(xs), y0, z], [max(xs), y0, z], [max(xs), y1, z], [min(xs), y1, z]]
        else:
            x = xs[0]
            c = [[x, y0, min(zs)], [x, y0, max(zs)], [x, y1, max(zs)], [x, y1, min(zs)]]
        return {"shape": s_.get("name"), "corners": [[round(float(v), 4) for v in p] for p in c], "normal": [float(v) for v in n]}
    return None


def framing(scene, path, subject, exact=True):
    """FRAME-0: at each pose, what it shows of the subject (legibility.view), and whether the path frames it."""
    import legibility
    boxes = [b for _i, b in obstacles(scene)]
    rows = []
    for k, pose in enumerate(path["poses"]):
        v = legibility.view(pose, subject["corners"], subject["normal"], boxes, exact=exact, offset=SUBJECT_OFFSET, inset=FRAME_INSET)
        why = ([] if v["inside"] else ["not framed"]) + ([] if v["seen"] >= FRAME_SEEN else ["not seen (%.0f%%)" % (100 * v["seen"])]) + \
              ([] if v["area_px"] >= FRAME_AREA else ["small (%.0f px)" % v["area_px"]])
        rows.append(dict(v, pose=k, framed=not why, why=why))
    return {"rule": FRAME_RULE, "met": bool(rows) and all(r["framed"] for r in rows), "poses": rows,
            "smallest_px": min((r["area_px"] for r in rows), default=0.0)}


def plan(scene, focus, seed, normal=None, name=None, subject=None):
    """The path: {name, seed, focus, normal, margin, rule, radius, rise, poses, sight, skipped, id}. See the head of
    this file. Tried in order: one radius and rise all round with every pose seeing the focus; the same without sight;
    then each pose on its own, a pose that cannot clear left out."""
    f = [float(v) for v in focus]
    h = int(sha256(str(seed).encode("utf-8"))[:8], 16)
    flat = normal is not None and abs(float(normal[1])) < 1e-9 and bool(float(normal[0]) or float(normal[2]))
    if flat:
        a_n = math.degrees(math.atan2(float(normal[0]), -float(normal[2])))
        angles = [a_n - ARC / 2 + (h % 15) + ARC * k / (POSES - 1) for k in range(POSES)]
        name = name or "arc"
    else:
        angles = [(h % 360) + 360.0 * k / POSES for k in range(POSES)]
        name = name or "orbit"
    obs = obstacles(scene)
    grown = _grown_all(scene)
    fm = float(MARGIN) + 1e-6
    got, ring = None, [None, None]
    frame = None
    if subject is not None and flat:
        # FRAME-0: every ring that holds PATH-0 with every pose seeing the focus, framed for the subject in floats; the one
        # whose smallest subject is largest is taken and its framing decided exactly. None framed: the plain arc below,
        # its framing said not met (FRAME-NONE), the path never loosened to meet it
        best = None
        for radius in FRAME_RADII:
            for rise in RISES:
                g = _ring(f, angles, radius, rise, obs, grown, fm, True, False)
                if not g:
                    continue
                fr = framing(scene, {"poses": g[0]}, subject, exact=False)
                if (fr["met"] or PLANT == "frame-any-ring") and (best is None or fr["smallest_px"] > best[0]):
                    best = (fr["smallest_px"], g, [radius, rise])
        if best is not None:
            got, ring = best[1], best[2]
    for need_sight in ((True, False) if got is None else ()):
        for radius in RADII:
            for rise in RISES:
                got = _ring(f, angles, radius, rise, obs, grown, fm, need_sight, False)
                if got:
                    ring = [radius, rise]
                    break
            if got:
                break
        if got:
            break
    if not got:
        got = _ring(f, angles, None, None, obs, grown, fm, False, True)
    poses, skipped = got
    if len(poses) < MIN_POSES:
        raise CameraError("CAMERA-PATH-NONE", "only %d of %d poses about %s are clear" % (len(poses), POSES, [round(v, 3) for v in f]))
    doc = {"name": name, "seed": str(seed), "focus": [round(v, 3) for v in f], "normal": [float(v) for v in normal] if flat else None,
           "margin": str(MARGIN), "rule": RULE, "radius": ring[0], "rise": ring[1], "poses": poses, "skipped": skipped}
    doc["sight"] = sight(scene, doc)
    if subject is not None:
        frame = framing(scene, doc, subject)
        doc["subject"] = subject
        doc["framing"] = dict(frame, code="" if frame["met"] else "FRAME-NONE")
    return dict(doc, id="%s-%s" % (name, sha256(enc(doc).encode("ascii"))[:12]))


# ------------------------------------------------------------------------------------------------ self-test
def faces(S):
    """[(focus, normal)] of every building's side that has bays: the middle of the side, its outward normal."""
    out = []
    for v in S.get("visuals", []):
        if not (v["id"].startswith("building:") and v["id"].count(":") == 1):
            continue
        b = v["box"]
        sides = sorted({x["id"].split(":")[2][0] for x in S["visuals"] if x["id"].startswith(v["id"] + ":")})
        mx, my, mz = (b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2
        at = {"s": ([mx, my, b[5]], [0, 0, 1]), "n": ([mx, my, b[2]], [0, 0, -1]), "e": ([b[3], my, mz], [1, 0, 0]), "w": ([b[0], my, mz], [-1, 0, 0])}
        out += [at[sd] for sd in sides if sd in at]
    return out


def _world(name):
    sys.path.insert(0, HERE)
    import dress
    return dress.export(dress.load(name))["scene"]


def selftest():
    rows = []

    def row(n, ok, detail):
        rows.append((n, bool(ok)))
        if not PLANT:
            print("[%s] %s — %s" % ("PASS" if ok else "FAIL", n, detail))
    wall = {"collision": [{"id": "wall", "box": [0, 0, 0, 10, 4, 1]}], "visuals": [{"id": "sign", "box": [2, 5, 0, 3, 6, 0.04]}], "movers": [], "targets": {}}
    P = lambda x, y, z: {"x": x, "y": y, "z": z, "yaw_deg": 0, "pitch_deg": 0}
    path = lambda *ps: {"focus": [5, 2, 0.5], "poses": list(ps)}
    cases = [("a pose 0.5 m in front of the wall, on the grown face", path(P(5, 2, 1.5)), []),
             ("a pose 0.499 m in front of it", path(P(5, 2, 1.499)), ["CAMERA-INSIDE"]),
             ("a pose inside the wall", path(P(5, 2, 0.5)), ["CAMERA-INSIDE"]),
             ("a pose 0.4 m above the ground plane", path(P(20, 0.4, 20)), ["CAMERA-LOW"]),
             ("a pose 0.3 m in front of a 4 cm sign (the dressing counts)", path(P(2.5, 5.5, 0.34)), ["CAMERA-INSIDE"]),
             ("two clear poses either side of the wall: the segment crosses it", path(P(5, 2, -2), P(5, 2, 3)), ["CAMERA-CROSSES"]),
             ("two clear poses whose segment passes over the wall and the sign", path(P(-2, 7, 0.5), P(12, 7, 0.5)), []),
             ("two clear poses whose segment runs along the wall's grown top exactly", path(P(-1, 4.5, 0.5), P(11, 4.5, 0.5)), [])]
    got = [(n, sorted({b["code"] for b in check(wall, p)}), w) for n, p, w in cases]
    row("the rule against boxes worked by hand, exactly (a planted interior pose and a wall-crossing segment refused)",
        all(g == w for _n, g, w in got), "; ".join("%s: %s" % (n, ",".join(g) or "clear") for n, g, _w in got))
    worlds = ("harbor-day", "harbor-lift", "plaza-night", "foundry-yard")
    scenes = {w: _world(w) for w in worlds if os.path.exists(os.path.join(HERE, "briefs", w + ".art"))}
    S = scenes.get("foundry-yard") or next(iter(scenes.values()))
    fc, nrm = next(((f_, n_) for f_, n_ in faces(S) if n_ == [0, 0, 1]), ([24.0, 6.0, 6.0], [0, 0, 1]))
    a1 = plan(S, fc, "req-1", nrm)
    mass = next(v["box"] for v in S["visuals"] if v["id"].startswith("building:") and v["id"].count(":") == 1 and v["box"][5] == fc[2])
    inner = dict(a1, poses=[dict(p_) for p_ in a1["poses"]])
    inner["poses"][3].update(x=(mass[0] + mass[3]) / 2, y=(mass[1] + mass[4]) / 2, z=(mass[2] + mass[5]) / 2)
    # behind it: over the lowest of the yard's roofs behind the warehouse, a metre above that roof and below the
    # warehouse's top, clear itself; the segments to it from the poses either side go through the warehouse
    sky = sorted((v["box"] for v in S["visuals"] if v["id"].startswith("skyline:") and v["box"][5] <= mass[2] + 0.01
                  and v["box"][0] >= mass[0] - 0.01 and v["box"][3] <= mass[3] + 0.01), key=lambda b_: (b_[4], b_[0]))
    lo = sky[0] if sky else [mass[0], 0.0, mass[2] - 4, mass[3], 0.0, mass[2]]
    behind = dict(a1, poses=[dict(p_) for p_ in a1["poses"]])
    behind["poses"][3].update(x=(lo[0] + lo[3]) / 2, y=lo[4] + 1.0, z=(lo[2] + lo[5]) / 2)
    vi, vb = check(S, inner), check(S, behind)
    row("planted in the district: a pose inside the flagship's warehouse, and a pose behind it whose segments cross it, refused",
        not check(S, a1) and any(v["code"] == "CAMERA-INSIDE" and v["pose"] == 3 and v["box"].startswith("building:") for v in vi)
        and {tuple(v["segment"]) for v in vb if v["code"] == "CAMERA-CROSSES" and v["box"].startswith("building:")} == {(2, 3), (3, 4)}
        and not any(v["code"] == "CAMERA-INSIDE" for v in vb),
        "the path as made: clear; pose 3 inside: %s; pose 3 behind: %s" % (
            sorted({"%s %s" % (v["code"], v["box"]) for v in vi if v.get("pose") == 3})[:2], sorted({"%s %s" % (v["code"], v.get("segment")) for v in vb})[:3]))
    if not PLANT:
        held, n_paths, none, full_faces, n_faces, t0 = True, 0, [], 0, 0, time.perf_counter()
        for w, Sw in sorted(scenes.items()):
            foci = [([Sw["views"][v]["x"], Sw["views"][v]["y"], Sw["views"][v]["z"]], None) for v in sorted(Sw["views"])] + faces(Sw)
            for fc_, nrm_ in foci:
                for seed in ("s1", "s2", "s3"):
                    try:
                        pth = plan(Sw, fc_, "%s-%s" % (w, seed), nrm_)
                    except CameraError:
                        none.append(w)
                        continue
                    n_paths += 1
                    held = held and not check(Sw, pth)
                    if nrm_ is not None:
                        n_faces += 1
                        full_faces += len(pth["poses"]) == POSES and all(pth["sight"])
        row("every path made in every world holds the rule, checked again exactly; every face's arc whole and seeing its focus",
            held and n_paths > 0 and n_faces > 0 and full_faces == n_faces,
            "%d paths (every view and every building's face of %d worlds, three seeds each) in %.1f s, all clear; %d of %d faces' arcs eight poses, "
            "every pose seeing its focus; %d views' orbits refused (CAMERA-PATH-NONE: a narrow place, fewer than %d clear poses)"
            % (n_paths, len(scenes), time.perf_counter() - t0, full_faces, n_faces, len(none), MIN_POSES))
    a2, a3 = plan(S, fc, "req-1", nrm), plan(S, fc, "req-2", nrm)
    row("the same scene, focus, face and seed give the same path, byte for byte; another seed another", enc(a1) == enc(a2) and a1["id"] != a3["id"],
        "%s twice; %s" % (a1["id"], a3["id"]))
    front = all((p_["z"] - fc[2]) > 0 for p_ in a1["poses"])
    row("a facade's arc stands in front of its face, one radius and rise all round, and sees its focus", a1["name"] == "arc" and front
        and len(a1["poses"]) == POSES and all(a1["sight"]) and a1["radius"] is not None,
        "%d poses at %s m and %s m up, all in front, all seeing %s" % (len(a1["poses"]), a1["radius"], a1["rise"], a1["focus"]))
    # FRAME-0 (0243): the flagship's marked bay (bay 3 of floor 2, as #bay marks it: 2 x 3.5 m of the face) framed
    sub = {"shape": "bay", "corners": [[26.0, 7.0, 6.0], [28.0, 7.0, 6.0], [28.0, 10.5, 6.0], [26.0, 10.5, 6.0]], "normal": [0.0, 0.0, 1.0]}
    fc2 = [27.0, 8.75, 6.0]
    plain = plan(S, fc2, "req-1", [0, 0, 1])
    framed = plan(S, fc2, "req-1", [0, 0, 1], subject=sub)
    fr = framed.get("framing") or {}
    before = framing(S, plain, sub)
    row("FRAME-0: the marked bay framed at every pose, the path still clear, the framing decided exactly again",
        fr.get("met") and fr.get("smallest_px", 0) >= FRAME_AREA and not check(S, framed) and framing(S, framed, sub) == {k: v for k, v in fr.items() if k != "code"}
        and len(framed["poses"]) == POSES,
        "framed at %s m, %s m up: the bay %s to %s px at its poses, all seen; the arc unframed for it (B5a's way): %s to %s px, framed %s" % (
            framed["radius"], framed["rise"], int(fr.get("smallest_px", 0)), int(max((r["area_px"] for r in fr.get("poses", [])), default=0)),
            int(before["smallest_px"]), int(max(r["area_px"] for r in before["poses"])), before["met"]))
    tiny = dict(sub, corners=[[26.9, 8.7, 6.0], [27.0, 8.7, 6.0], [27.0, 8.8, 6.0], [26.9, 8.8, 6.0]])
    small = plan(S, fc2, "req-1", [0, 0, 1], subject=tiny)
    row("FRAME-0: a subject no ring can frame (10 cm square): FRAME-NONE, said, and the path the plain arc, never loosened to meet it",
        small["framing"]["code"] == "FRAME-NONE" and not small["framing"]["met"] and small["poses"] == plain["poses"] and not check(S, small),
        "framing %s; its largest %.0f px; the poses those of the plain arc: %s" % (small["framing"]["code"], max(r["area_px"] for r in small["framing"]["poses"]),
                                                                                small["poses"] == plain["poses"]))
    if PLANT:
        return rows
    caught = []
    for p in PLANTS:
        globals()["PLANT"] = p
        try:
            failed = [n for n, ok in selftest() if not ok]
        except Exception as e:  # noqa: BLE001 — a plant that breaks the run is caught by it
            failed = ["the run: %s" % type(e).__name__]
        finally:
            globals()["PLANT"] = ""
        caught.append(bool(failed))
        print("[%s] camera plant %s caught — %s" % ("PASS" if failed else "FAIL", p, ("by: " + "; ".join(f[:70] for f in failed)) if failed else "NOT CAUGHT"))
    ok = all(o for _n, o in rows) and all(caught)
    print("PATH SELFTEST %d/%d" % (sum(o for _n, o in rows) + sum(caught), len(rows) + len(caught)))
    return 0 if ok else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["selftest"]:
        sys.exit(selftest())
    print("usage: python art/camera.py selftest")
    sys.exit(2)
