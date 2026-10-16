# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/legibility.py — LEGIBLE-0 (0241, with B5a): one test of Meaning-to-View, off the gate and advisory.
#
#   python art/legibility.py selftest    the projection, the contrast and the occlusion worked by hand; the flagship's
#                                        window measured along its path; three planted collapses of its cue (an
#                                        occluder, a panel in the wall's own material, a pose behind or grazing the
#                                        face) each found by the proxy that should find it; the plants
#
# THE QUESTION. A piece of the world is meant to be read as something (here, a role a person names: "the subject of
# this request"). Does the evidence for it survive the view? Along a camera path, at each pose, three proxies, each
# computed from the scene's numbers alone (no renderer, no image):
#
#   framed and seen   of a 5 x 5 grid of points on the piece's outward face, the share in the viewport, in front of the
#                     face's plane, and on a line from the camera that passes inside no box of the scene (art/camera.py's
#                     exact test): framing and occlusion at once (a box's own face seen from behind is occluded by it);
#   apparent size     the face's area in pixels at the preview's viewport (480 x 270, a vertical field of 66 degrees, as
#                     the page draws a still), its corners projected as scene_render.js projects them;
#   contrast          the WCAG 2.x contrast ratio of the base colours of the piece's material and of the surface it is set
#                     in (relative luminance of linearised sRGB): lighting, emission, reflection and hue are not in it.
#
# A pose reads the cue when at least SEEN_MIN of the face is framed and seen, its area is at least AREA_MIN pixels and the
# contrast at least CONTRAST_MIN. The thresholds are declared, not fitted: a majority of the face; 24 x 24 pixels (WCAG
# 2.2's minimum target size, borrowed); 3:1 (WCAG 2.1's non-text contrast, borrowed). Borrowed from screens, they are
# proxies for "distinguishable", never a claim about what a person in a lit scene perceives. Nothing that decides reads
# this: no verdict, order or admission.

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import camera  # noqa: E402

VIEWPORT = (480, 270)
FOV = 66.0
NEAR = 0.1
GRID = 5
SEEN_MIN = 0.5
AREA_MIN = 24 * 24
CONTRAST_MIN = 3.0
ADVISORY = "PROXY — not a perception claim, not admission evidence"

PLANT = ""
PLANTS = ("legibility-no-occlusion", "legibility-unframed-seen", "legibility-srgb-unlinearised")


def luminance(rgb):
    """WCAG relative luminance of an sRGB colour 0-255."""
    def lin(v):
        v /= 255.0
        if PLANT == "legibility-srgb-unlinearised":
            return v
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(float(c)) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def basis(pose):
    y, p = math.radians(pose["yaw_deg"]), math.radians(pose["pitch_deg"])
    f = [math.sin(y) * math.cos(p), math.sin(p), -math.cos(y) * math.cos(p)]
    r = [math.cos(y), 0.0, math.sin(y)]
    u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]]
    return f, r, u


def project(pose, pt, viewport=VIEWPORT, fov=FOV):
    """(px, py, depth) of a world point in the still, or None behind the near plane."""
    f, r, u = basis(pose)
    d = [pt[0] - pose["x"], pt[1] - pose["y"], pt[2] - pose["z"]]
    z = sum(d[i] * f[i] for i in range(3))
    if z <= NEAR:
        return None
    t = math.tan(math.radians(fov) / 2)
    w, h = viewport
    xn, yn = sum(d[i] * r[i] for i in range(3)) / (z * t * w / h), sum(d[i] * u[i] for i in range(3)) / (z * t)
    return ((xn + 1) / 2 * w, (1 - yn) / 2 * h, z)


def _clip(poly, w, h):
    """Sutherland-Hodgman: the polygon clipped to the viewport."""
    for axis, lim, keep_below in ((0, 0.0, False), (0, float(w), True), (1, 0.0, False), (1, float(h), True)):
        out = []
        for i in range(len(poly)):
            a, b = poly[i - 1], poly[i]
            ia = a[axis] <= lim if keep_below else a[axis] >= lim
            ib = b[axis] <= lim if keep_below else b[axis] >= lim
            if ib:
                if not ia:
                    t = (lim - a[axis]) / (b[axis] - a[axis])
                    out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
                out.append(b)
            elif ia:
                t = (lim - a[axis]) / (b[axis] - a[axis])
                out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
        poly = out
        if not poly:
            return []
    return poly


def face(box, normal):
    """The four corners of an axis-aligned box's face whose outward normal is `normal`, and that face's plane point."""
    x0, y0, z0, x1, y1, z1 = box
    if normal[2]:
        z = z1 if normal[2] > 0 else z0
        return [[x0, y0, z], [x1, y0, z], [x1, y1, z], [x0, y1, z]]
    x = x1 if normal[0] > 0 else x0
    return [[x, y0, z0], [x, y0, z1], [x, y1, z1], [x, y1, z0]]


def probe(scene, path, piece, against, normal):
    """At each pose of the path: the share of the piece's face framed and seen, its area in pixels, the contrast of its
    material against `against`'s, and whether the cue reads (and why not). A function of its arguments alone."""
    vis = {v["id"]: v for v in scene["visuals"]}
    P, A = vis[piece], vis[against]
    mats = scene["materials"]
    c = round(contrast(mats[P["material"]]["base"], mats[A["material"]]["base"]), 4)
    corners = face(P["box"], normal)
    pts = [[corners[0][i] + (corners[1][i] - corners[0][i]) * (a + 0.5) / GRID + (corners[3][i] - corners[0][i]) * (b + 0.5) / GRID for i in range(3)]
           for a in range(GRID) for b in range(GRID)]
    grown = [camera._grown(b, 0) for _i, b in camera.obstacles(scene)]
    w, h = VIEWPORT
    rows = []
    for k, pose in enumerate(path["poses"]):
        eye = [pose["x"], pose["y"], pose["z"]]
        seen = 0
        for pt in pts:
            front = sum((eye[i] - pt[i]) * normal[i] for i in range(3)) > 0
            pr = project(pose, pt)
            framed = pr is not None and 0 <= pr[0] <= w and 0 <= pr[1] <= h
            if not front or not (framed or PLANT == "legibility-unframed-seen"):
                continue
            if PLANT != "legibility-no-occlusion":
                e, q_ = [camera.q(v) for v in eye], [camera.q(round(v, 6)) for v in pt]
                if any(camera.crosses(e, q_, g) for g in grown):
                    continue
            seen += 1
        prj = [project(pose, p_) for p_ in corners]
        area = 0.0
        if all(prj):
            poly = _clip([(p_[0], p_[1]) for p_ in prj], w, h)
            area = abs(sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))) / 2 if len(poly) >= 3 else 0.0
        share = seen / float(len(pts))
        why = ([] if share >= SEEN_MIN else ["not seen (%.0f%% of the face)" % (100 * share)]) + \
              ([] if area >= AREA_MIN else ["small (%.0f px)" % area]) + ([] if c >= CONTRAST_MIN else ["low contrast (%.2f:1)" % c])
        rows.append({"pose": k, "seen": round(share, 4), "area_px": round(area, 1), "contrast": c, "reads": not why, "why": why})
    return {"piece": piece, "against": against, "normal": list(normal), "path_id": path.get("id"), "advisory": ADVISORY,
            "thresholds": {"seen": SEEN_MIN, "area_px": AREA_MIN, "contrast": CONTRAST_MIN}, "poses": rows,
            "reads": sum(r["reads"] for r in rows)}


# ------------------------------------------------------------------------------------------------ self-test
FLAGSHIP = "building:10,2-17,2"
SUBJECT = FLAGSHIP + ":s-b3-f2"


def selftest():
    import copy
    rows = []

    def row(n, ok, detail):
        rows.append((n, bool(ok)))
        if not PLANT:
            print("[%s] %s — %s" % ("PASS" if ok else "FAIL", n, detail))
    # worked by hand: a 2 x 2 m white face 10 m straight ahead of a camera looking north, in front of a black wall
    S0 = {"visuals": [{"id": "wall", "box": [-5, 0, -11, 5, 6, -10.05], "material": "black"}, {"id": "sign", "box": [-1, 2, -10.05, 1, 4, -10], "material": "white"}],
          "collision": [], "movers": [], "targets": {},
          "materials": {"black": {"base": [0, 0, 0]}, "white": {"base": [255, 255, 255]}, "grey": {"base": [128, 128, 128]}}}
    pose = {"x": 0, "y": 3, "z": 0, "yaw_deg": 0, "pitch_deg": 0}
    fpx = (VIEWPORT[1] / 2) / math.tan(math.radians(FOV) / 2)
    want_area = (2 * fpx / 10) ** 2
    r0 = probe(S0, {"poses": [pose]}, "sign", "wall", [0, 0, 1])["poses"][0]
    centre = project(pose, [0, 3, -10])
    grey = round(contrast([128] * 3, [0] * 3), 4)
    row("worked by hand: the face's area, its centre in the middle of the still, its contrast and every point seen",
        abs(r0["area_px"] - round(want_area, 1)) < 0.2 and abs(centre[0] - 240) < 1e-9 and abs(centre[1] - 135) < 1e-9 and r0["contrast"] == 21.0
        and r0["seen"] == 1.0 and r0["reads"] and abs(grey - 5.3174) < 1e-3,
        "area %.1f px (by hand %.1f), centre (%.1f, %.1f), white on black %.1f:1, mid grey on black %.4f:1 (sRGB linearised), seen %.0f%%"
        % (r0["area_px"], want_area, centre[0], centre[1], r0["contrast"], grey, 100 * r0["seen"]))
    S = camera._world("foundry-yard")
    mass = next(v for v in S["visuals"] if v["id"] == FLAGSHIP)
    bay = next(v for v in S["visuals"] if v["id"] == SUBJECT)
    focus = [(bay["box"][0] + bay["box"][3]) / 2, (bay["box"][1] + bay["box"][4]) / 2, bay["box"][5]]
    path = camera.plan(S, focus, "flagship", [0, 0, 1])
    m1, m2 = probe(S, path, SUBJECT, FLAGSHIP, [0, 0, 1]), probe(S, path, SUBJECT, FLAGSHIP, [0, 0, 1])
    row("the flagship's window along its path, measured (a function of its inputs)", camera.enc(m1) == camera.enc(m2) and len(m1["poses"]) == len(path["poses"]),
        "%d of %d poses read the cue; seen %s; area %s px; contrast %.2f:1 (%s %s against %s %s)" % (
            m1["reads"], len(m1["poses"]), [r["seen"] for r in m1["poses"]], [int(r["area_px"]) for r in m1["poses"]], m1["poses"][0]["contrast"],
            bay["material"], S["materials"][bay["material"]]["base"], mass["material"], S["materials"][mass["material"]]["base"]))
    # planted: a hoarding a metre in front of the bay, 24 m wide and rising 8 m above it
    S_occ = copy.deepcopy(S)
    b = bay["box"]
    S_occ["visuals"].append({"id": "planted:hoarding", "box": [b[0] - 12, 0.0, b[5] + 1, b[3] + 12, b[4] + 8, b[5] + 1.2], "material": "brick"})
    m_occ = probe(S_occ, path, SUBJECT, FLAGSHIP, [0, 0, 1])
    # planted: the bay panelled in the wall's own material
    S_same = copy.deepcopy(S)
    next(v for v in S_same["visuals"] if v["id"] == SUBJECT)["material"] = mass["material"]
    m_same = probe(S_same, path, SUBJECT, FLAGSHIP, [0, 0, 1])
    # planted: a pose behind the face's plane looking at it, and one grazing it from 60 m along the street
    behind = dict(path["poses"][0], z=b[2] - 3, pitch_deg=0)
    gx, gz = focus[0] - 60, focus[2] + 1.5
    graze = {"x": gx, "y": focus[1], "z": gz, "yaw_deg": math.degrees(math.atan2(focus[0] - gx, -(focus[2] - gz))) % 360, "pitch_deg": 0}
    away = dict(path["poses"][0], yaw_deg=(path["poses"][0]["yaw_deg"] + 90) % 360)
    m_pose = probe(S, {"poses": [behind, graze, away]}, SUBJECT, FLAGSHIP, [0, 0, 1])
    occ_ok = all(r["seen"] == 0 and any(w.startswith("not seen") for w in r["why"]) for r in m_occ["poses"])
    same_ok = all(r["contrast"] == 1.0 and any(w.startswith("low contrast") for w in r["why"]) for r in m_same["poses"])
    pose_ok = m_pose["poses"][0]["seen"] == 0 and m_pose["poses"][1]["area_px"] < AREA_MIN and any(w.startswith("small") for w in m_pose["poses"][1]["why"]) \
        and m_pose["poses"][2]["seen"] == 0 and m_pose["poses"][2]["area_px"] == 0
    row("planted collapses of the cue, each found by the proxy that should find it: a hoarding before it (seen), the wall's own material (contrast), "
        "a pose behind the face (seen), one grazing it from 60 m (size), one turned away (framed)", occ_ok and same_ok and pose_ok,
        "behind a hoarding: seen %s; same material: contrast %s; behind: seen %s; grazing: %.1f px; turned away: seen %s, %.0f px" % (
            sorted({r["seen"] for r in m_occ["poses"]}), sorted({r["contrast"] for r in m_same["poses"]}), m_pose["poses"][0]["seen"], m_pose["poses"][1]["area_px"],
            m_pose["poses"][2]["seen"], m_pose["poses"][2]["area_px"]))
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
        print("[%s] legibility plant %s caught — %s" % ("PASS" if failed else "FAIL", p, ("by: " + "; ".join(f[:60] for f in failed)) if failed else "NOT CAUGHT"))
    ok = all(o for _n, o in rows) and all(caught)
    print("LEGIBLE SELFTEST %d/%d" % (sum(o for _n, o in rows) + sum(caught), len(rows) + len(caught)))
    return 0 if ok else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["selftest"]:
        sys.exit(selftest())
    print("usage: python art/legibility.py selftest")
    sys.exit(2)
