# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/impact.py — IMPACT-0 (0239, Phase I's B3): what a candidate costs the native renderer, beside what it changes.
#
#   python art/impact.py selftest            the counts against hand-worked scenes, the fit reproduced, the plants
#   python art/impact.py fit ROWS.json       least squares over calibration rows: the coefficients, exactly
#   python art/impact.py scene SCENE.json    one scene's counts and its estimate
#
# For a candidate and the base of its own evaluation (the two scenes the director compiled), the host counts what the
# native renderer (art/web/scene_render.js) makes of each, as it makes it: the triangles (every play box and every piece
# of dressing is one box of six faces, two triangles a face, in one call a pass; a target five faces, a mover six), the
# draw calls of one frame (the sky and the geometry in the mirror and in the scene, the targets and movers when there
# are any, the rain when it rains, and the bloom and tone passes), the lights it draws (the first 160) and the sum of
# their candelas, and the bytes of the textures it builds from the scene (the lights, their visibility per cell, the
# height and roof fields; the scenes carry no image texture). Then an ESTIMATE of one frame's milliseconds from a linear
# model whose coefficients and calibration rows are art/impact_model.json, with the host and the date they were measured
# on: an estimate from counts, never a measured frame, and never evidence for an admission. Budgets are advisory: a
# candidate over one is flagged, and nothing is refused for it. The preview's camera path is named and seeded: every
# candidate of a request is shown along the same path. Standard library only; deterministic.

import hashlib
import json
import math
import os
import re
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
RENDERER = os.path.join(HERE, "web", "scene_render.js")
MODEL = os.path.join(HERE, "impact_model.json")
FORMAT, VERSION = "VERDANDI-IMPACT", "0"
ADVISORY = "ADVISORY ESTIMATE — not admission evidence"
POST_PASSES = 13        # bright 1, blur of the quarter 2 x 2, down to the eighth 1, its blur 3 x 2, tone 1 (scene_render.js draw)
PATH_POSES = 8          # the preview's camera path: poses around the focus

# IMPACT-0's plants, each set by its self-test and each caught by one of its rows
PLANT = ""
PLANTS = ("impact-budget-skipped", "impact-provenance-fixed", "impact-path-unseeded")


class ImpactError(Exception):
    pass


def enc(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256(b):
    return hashlib.sha256(b).hexdigest()


_LIMITS = []


def renderer_cap():
    """The lights the native renderer draws, read from its source once (as art/quality.py reads it)."""
    if not _LIMITS:
        js = open(RENDERER, "rb").read().decode("utf-8")
        cap = re.findall(r"S\.lights\.slice\(0,\s*([0-9]+)\)", js)
        posts = len(re.findall(r"self\.fullscreen\(pr,|this\.fullscreen\(pr,", js))
        if len(cap) != 1:
            raise ImpactError("the renderer's source no longer says its light cap once (%d found)" % len(cap))
        _LIMITS.append({"lights": int(cap[0]), "fullscreen_calls_in_source": posts})
    return _LIMITS[0]


def counts(S):
    """What the native renderer makes of a scene: triangles, draw calls a frame, lights drawn and their candelas, the
    bytes of the textures it builds from the scene. Each as scene_render.js makes it (load, geometry, setTargets, draw)."""
    cap = renderer_cap()["lights"]
    g = S["grid"]
    wh = int(g["w"]) * int(g["h"])
    targets, movers = len(S.get("targets") or {}), len(S.get("movers") or [])
    static = 12 * (len(S.get("collision", [])) + len(S.get("visuals", [])))
    lights = S.get("lights", [])
    drawn = lights[:cap]
    nl = max(len(drawn), 1)
    tex = {"lights": nl * 2 * 16, "visibility": wh * nl, "height": wh * 4, "roof": wh * 4}
    rain = (S.get("environment") or {}).get("rain") or 0
    dyn = targets or movers
    return {"boxes": len(S.get("collision", [])) + len(S.get("visuals", [])),
            "triangles": static + 10 * targets + 12 * movers,
            "draw_calls": 4 + (2 if dyn else 0) + (1 if rain > 0 else 0) + POST_PASSES,
            "lights": len(lights), "lights_drawn": len(drawn),
            "candela": round(sum(float(L.get("candela", 0)) for L in drawn), 4),
            "texture_bytes": sum(tex.values()), "textures": tex}


# ------------------------------------------------------------------------------------------------ the model
def load_model(path=MODEL):
    return json.load(open(path, encoding="utf-8"))


def features(c, terms):
    return [Fraction(c["triangles"]) if t == "triangles" else Fraction(c["draw_calls"]) if t == "draw_calls" else
            Fraction(c["lights_drawn"]) if t == "lights" else Fraction(c["texture_bytes"], 1 << 20) for t in terms]


def fit(rows, terms):
    """Ordinary least squares, exactly (Fractions): ms = e + sum(k_t x_t) over the identified terms. Returns the
    coefficients as decimal text (9 places) and the residuals' root mean square."""
    X = [[Fraction(1)] + [Fraction(str(r[t])) for t in terms] for r in rows]
    y = [Fraction(str(r["ms"])) for r in rows]
    n = len(terms) + 1
    A = [[sum(x[i] * x[j] for x in X) for j in range(n)] for i in range(n)]
    b = [sum(x[i] * yy for x, yy in zip(X, y)) for i in range(n)]
    for col in range(n):                     # Gauss-Jordan, exact
        piv = next((r for r in range(col, n) if A[r][col] != 0), None)
        if piv is None:
            raise ImpactError("the calibration rows do not identify %s: it does not vary independently" % (["the intercept"] + terms)[col])
        A[col], A[piv], b[col], b[piv] = A[piv], A[col], b[piv], b[col]
        for r in range(n):
            if r != col and A[r][col] != 0:
                f = A[r][col] / A[col][col]
                A[r] = [a - f * c for a, c in zip(A[r], A[col])]
                b[r] -= f * b[col]
    k = [b[i] / A[i][i] for i in range(n)]
    pred = [sum(ki * xi for ki, xi in zip(k, x)) for x in X]
    rms = math.sqrt(float(sum((p - yy) ** 2 for p, yy in zip(pred, y)) / len(y)))
    q = lambda f: "%.9f" % float(f)
    return {"intercept": q(k[0]), **{t: q(kk) for t, kk in zip(terms, k[1:])}}, round(rms, 3)


def estimate(c, model):
    """One frame's milliseconds, estimated from the counts: the intercept plus each identified term's coefficient times
    its count; a term the calibration did not identify adds nothing, and says so."""
    co = model["coefficients"]
    v = Fraction(co["intercept"])
    for t, x in zip(model["terms"], features(c, model["terms"])):
        v += Fraction(co[t]) * x
    return round(float(v), 3)


def budgets_over(c, budgets):
    if PLANT == "impact-budget-skipped":
        return []
    return [{"budget": k, "limit": lim, "value": c[k]} for k, lim in sorted(budgets.items()) if k in c and c[k] > lim]


# ------------------------------------------------------------------------------------------------ the preview path
def camera_path(scene, focus, seed, name="orbit"):
    """A named, seeded path of PATH_POSES poses around `focus` ([x, y, z] in metres): at 14 m, 6 m above it, looking at
    it, starting at an angle the seed decides. The same focus and seed give the same path, byte for byte; its id is the
    sha256 of its canonical form. The page shows every candidate of a request along it."""
    if PLANT == "impact-path-unseeded":
        import time
        seed = str(time.time())
    a0 = int(sha256(str(seed).encode("utf-8"))[:8], 16) % 360
    fx, fy, fz = (float(v) for v in focus)
    poses = []
    for k in range(PATH_POSES):
        a = math.radians(a0 + 360.0 * k / PATH_POSES)
        x, z, y = fx + 14.0 * math.sin(a), fz - 14.0 * math.cos(a), fy + 6.0
        yaw = math.degrees(math.atan2(fx - x, -(fz - z))) % 360
        pitch = -math.degrees(math.atan2(6.0, 14.0))
        poses.append({"x": round(x, 3), "y": round(y, 3), "z": round(z, 3), "yaw_deg": round(yaw, 3), "pitch_deg": round(pitch, 3)})
    doc = {"name": name, "seed": str(seed), "focus": [round(fx, 3), round(fy, 3), round(fz, 3)], "poses": poses}
    return dict(doc, id="%s-%s" % (name, sha256(enc(doc).encode("ascii"))[:12]))


def focus_of(scene, shapes=(), target=None):
    """Where the preview looks: the first shape's world vertices' middle, else the target's box's middle, else the
    scene's first view."""
    for s in shapes or ():
        w = s.get("world_m") or []
        if w:
            return [sum(p[i] for p in w) / len(w) for i in range(3)]
    if target and target.get("box"):
        b = target["box"]
        return [(b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2]
    v = sorted((scene.get("views") or {}).items())
    if v:
        return [v[0][1]["x"], v[0][1]["y"], v[0][1]["z"]]
    g = scene["grid"]
    return [g["w"] * g["cell"] / 2, 0.0, g["h"] * g["cell"] / 2]


# ------------------------------------------------------------------------------------------------ the report
def report(base, cand, provenance, path, rationale="", model=None):
    """The impact of a candidate: the counts of its base and of itself, their differences, the estimate of each frame
    and its difference (labelled), the advisory budgets it is over, the provenance and the preview's path. A function of
    its arguments alone (no clock): the same inputs give the same bytes."""
    model = model or load_model()
    c0, c1 = counts(base), counts(cand)
    keys = ("boxes", "triangles", "draw_calls", "lights", "lights_drawn", "candela", "texture_bytes")
    delta = {k: round(c1[k] - c0[k], 4) for k in keys}
    e0, e1 = estimate(c0, model), estimate(c1, model)
    cal = model["calibration"]
    prov = dict(provenance)
    if PLANT == "impact-provenance-fixed":
        prov["prompt_sha256"] = sha256(b"")
    over = budgets_over(c1, model["budgets"])
    return {"format": FORMAT, "version": VERSION, "advisory": ADVISORY,
            "base": {k: c0[k] for k in keys}, "candidate": {k: c1[k] for k in keys}, "delta": delta,
            "textures": c1["textures"],
            "estimate": {"label": "ESTIMATE", "base_ms": e0, "candidate_ms": e1, "delta_ms": round(e1 - e0, 3),
                         "how": "frame_ms = %s + %s; calibrated on %s, %s, at %s x %s; %s" % (
                             model["coefficients"]["intercept"], " + ".join("%s x %s" % (model["coefficients"][t], t) for t in model["terms"]),
                             cal["host"], cal["date"], cal["resolution"][0], cal["resolution"][1],
                             "not a measured frame; " + "; ".join("%s: %s" % kv for kv in sorted(model["not_identified"].items())))},
            "budgets": model["budgets"], "over_budget": over, "flag": "over budget (advisory)" if over else "",
            "provenance": prov, "preview": {"path_id": path["id"], "name": path["name"], "seed": path["seed"], "poses": path["poses"]},
            "rationale": {"text": (rationale or "")[:600], "basis": "the director's words, not checked"}}


# ------------------------------------------------------------------------------------------------ self-test
def selftest():
    rows = []

    def row(name, ok, detail):
        rows.append((name, bool(ok)))
        if not PLANT:
            print("[%s] %s — %s" % ("PASS" if ok else "FAIL", name, detail))
    box = lambda i, b: {"id": "tower:%d" % i, "box": b, "material": "m", "by": "x", "region": "r", "asset": "cube"}
    S = {"grid": {"w": 4, "h": 2, "cell": 2.0, "wall": 4.0}, "collision": [box(0, [0, 0, 0, 2, 4, 2])], "visuals": [box(1, [0, 4, 0, 2, 8, 2]), box(2, [2, 0, 2, 4, 1, 4])],
         "lights": [{"id": "lamp:1", "candela": 500.0}, {"id": "lamp:2", "candela": 250.5}], "targets": {"T": {}}, "environment": {"rain": 0.5}, "views": {}}
    c = counts(S)
    want = {"boxes": 3, "triangles": 3 * 12 + 10, "draw_calls": 4 + 2 + 1 + 13, "lights": 2, "lights_drawn": 2, "candela": 750.5,
            "texture_bytes": 2 * 2 * 16 + 8 * 2 + 8 * 4 * 2}
    row("counts as the renderer makes them, worked by hand", all(c[k] == v for k, v in want.items()), json.dumps({k: c[k] for k in want}, sort_keys=True))
    many = dict(S, lights=[{"id": "l%d" % i, "candela": 1.0} for i in range(200)], targets={}, environment={})
    c2 = counts(many)
    row("the lights past the renderer's cap are not drawn, nor counted in its textures", c2["lights"] == 200 and c2["lights_drawn"] == renderer_cap()["lights"]
        and c2["texture_bytes"] == 160 * 32 + 8 * 160 + 64 and c2["draw_calls"] == 17, "%d lights, %d drawn; %d texture bytes" % (c2["lights"], c2["lights_drawn"], c2["texture_bytes"]))
    m = load_model()
    co, rms = fit(m["calibration"]["rows"], m["terms"])
    row("the model's coefficients are its calibration rows' least squares, exactly", co == m["coefficients"] and rms == m["calibration"]["rms_ms"],
        "%s; rms %s ms over %d rows (%s, %s)" % (co, rms, len(m["calibration"]["rows"]), m["calibration"]["host"], m["calibration"]["date"]))
    p1, p2 = camera_path(S, [1, 2, 3], "seed-a"), camera_path(S, [1, 2, 3], "seed-a")
    p3 = camera_path(S, [1, 2, 3], "seed-b")
    row("the preview's path: named, seeded, the same for the same seed", p1 == p2 and p1["id"] != p3["id"] and len(p1["poses"]) == PATH_POSES,
        "%s, %s" % (p1["id"], p3["id"]))
    prov = {"producer": "t", "model": "t-1", "prompt_sha256": sha256(b"close #bay"), "request": "r1", "seed": "r1"}
    r1, r2 = report(S, many, prov, p1, "why", m), report(S, many, prov, p1, "why", m)
    over = [o["budget"] for o in r1["over_budget"]]
    row("a candidate over a budget is flagged, advisory", "lights_drawn" in over and r1["flag"] and r1["advisory"] == ADVISORY,
        "over: %s; %s" % (over, r1["flag"]))
    r3 = report(S, many, dict(prov, prompt_sha256=sha256(b"close #bay now")), p1, "why", m)
    row("the report is a function of its inputs; another prompt, another provenance", enc(r1) == enc(r2) and r3["provenance"]["prompt_sha256"] != r1["provenance"]["prompt_sha256"],
        "%d bytes, twice the same; prompt sha %s and %s" % (len(enc(r1)), r1["provenance"]["prompt_sha256"][:12], r3["provenance"]["prompt_sha256"][:12]))
    if PLANT:
        return rows
    global PLANT_
    caught = []
    for p in PLANTS:
        globals()["PLANT"] = p
        try:
            failed = [n for n, ok in selftest() if not ok]
        finally:
            globals()["PLANT"] = ""
        caught.append(bool(failed))
        print("[%s] impact plant %s caught — %s" % ("PASS" if failed else "FAIL", p, ("by: " + "; ".join(failed)) if failed else "NOT CAUGHT"))
    ok = all(o for _n, o in rows) and all(caught)
    print("IMPACT SELFTEST %d/%d" % (sum(o for _n, o in rows) + sum(caught), len(rows) + len(caught)))
    return 0 if ok else 1


def main(argv):
    if argv[:1] == ["selftest"]:
        return selftest()
    if argv[:1] == ["fit"] and len(argv) == 2:
        d = json.load(open(argv[1], encoding="utf-8"))
        co, rms = fit(d["rows"], d["terms"])
        print(json.dumps({"coefficients": co, "rms_ms": rms}, indent=1, sort_keys=True))
        return 0
    if argv[:1] == ["scene"] and len(argv) == 2:
        S = json.load(open(argv[1], encoding="utf-8"))
        c = counts(S)
        print(json.dumps(dict(c, estimate_ms=estimate(c, load_model())), indent=1, sort_keys=True))
        return 0
    print("usage: python art/impact.py selftest | fit ROWS.json | scene SCENE.json")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
