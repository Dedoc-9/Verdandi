# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/scene_diff.py — HELD-0 (0235): what a candidate changed, said by the host, and where it changed it against a
# designer's shape. Prepared by MIXER-C beside 0230 and 0231 (its proofs, T1 to T8, are summarised at each function);
# taken here with the shapes as MARK-0 keeps them, their status and frames from art/studio_marks.py (one table, one
# status), and a region that reaches out from its face.
#
#   python art/scene_diff.py selftest           the falsifiers, art/scene_diff_test.py (properties and planted defects)
#   python art/scene_diff.py diff A.json B.json
#   python art/scene_diff.py account A.json B.json SHAPES.json NAME
#
#   diff(a, b)            the diff of two VERDANDI-ART-SCENE 0 scenes: raw sections keyed by identity, and the
#                         object-level view (art/studio_refs.py's objects: an object is its id, never matched by likeness)
#   invert(d)             the diff read backwards: invert(diff(a, b)) == diff(b, a), byte for byte
#   apply(d, a)           the scene the diff leads to from a (refused, SCENE-DIFF-STALE, if a is not its base)
#   badges(d)             M (the look), C (the play geometry), P (the placement of the dressing): each an OR over the
#                         diff's entries, and each raised exactly when its projection of the scene changes (T4)
#   region(rec, S)        a kept shape's prism over a scene: its polygon on its anchor's face, swept from the back of the
#                         anchor's box out to the shape's reach (reach_of); refused unless the shape is ok in that scene
#   classify(box, R)      inside | crossing | touching | outside, exactly (rationals, never floats)
#   account(d, a, b, R)   every box the diff changes or affects, grouped by object, each held to the region
#
# Pure functions over the scenes as data: no file, no clock, no randomness, no set iterated without sorting. Standard
# library only. Coordinates are the exact decimals the scene states (a float's shortest repr is the JSON text the
# exporter wrote): the briefs' boxes are 0.1 mm values (art/dress.py r4), not whole millimetres.

import hashlib
import json
import os
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import studio_refs as R      # noqa: E402  (the object identity the studio already uses)
import studio_marks as SM    # noqa: E402  (MARK-0: the face frames, a shape's status, its checks, its reach)

FORMAT, VERSION = "VERDANDI-SCENE-DIFF", "0"

KEYED_LISTS = ("collision", "lights", "movers", "visuals")          # lists of records, each with a unique "id"
KEYED_DICTS = ("assets", "environment", "materials", "regions", "spawns", "targets", "views")
INDEXED = ("reach", "tops")                                         # lists by position (one value a cell)
SECTIONS = KEYED_LISTS + KEYED_DICTS + INDEXED                      # every other top-level key is a field of "top"
QN = 256                                                            # a mover's phase units a metre (art/dress.py)
BACK_MARGIN = Fraction(1)                                           # an opening's region: this far behind its anchor too


class DiffError(Exception):
    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code, self.detail = code, detail


# ------------------------------------------------------------------------------------------------ bytes
def enc(v):
    """The canonical bytes of a JSON value (as text): sorted keys, no spaces, ASCII, no NaN. Two values are the same
    when these are equal, so 1 and 1.0, 0.0 and -0.0, true and 1 are different values, as they are different bytes."""
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def same(x, y):
    return enc(x) == enc(y)


def _records(scene, key):
    v = scene.get(key)
    if v is None:
        return {}
    if key in KEYED_LISTS:
        out = {}
        for r in v:
            if not isinstance(r, dict) or not isinstance(r.get("id"), str):
                raise DiffError("SCENE-DIFF-RECORD", "%s holds a record without a string id" % key)
            if r["id"] in out:
                raise DiffError("SCENE-DIFF-DUPLICATE", "%s holds two records of id %r: an id that names two things names neither" % (key, r["id"]))
            out[r["id"]] = r
        return out
    if key in INDEXED:
        return {"%d" % i: x for i, x in enumerate(v)}
    if not isinstance(v, dict):
        raise DiffError("SCENE-DIFF-RECORD", "%s is not an object" % key)
    return dict(v)


def _top(scene):
    t = {}
    for k, v in scene.items():
        if k.startswith("has:"):
            raise DiffError("SCENE-DIFF-RECORD", "a scene field named %r" % k)
        if k not in SECTIONS:
            t[k] = v
    for k in SECTIONS:
        if k in scene:
            t["has:" + k] = True
    return t


def canon(scene):
    """The scene with its keyed lists in id order: the form the diff is a function of."""
    out = {}
    for k, v in scene.items():
        out[k] = [r for _i, r in sorted(_records(scene, k).items())] if k in KEYED_LISTS else v
    return out


def canon_sha(scene):
    return hashlib.sha256(enc(canon(scene)).encode("ascii")).hexdigest()


# ------------------------------------------------------------------------------------------------ objects
def root(i, ids):
    """The object a visual id belongs to (art/studio_refs.py's rule), against the ids of BOTH scenes, so that the parts
    of an object a candidate adds root to it and are not counted as objects of their own (T7a)."""
    r = i
    while r.count(":") >= 2 and r.rsplit(":", 1)[0] in ids:
        r = r.rsplit(":", 1)[0]
    return r


def object_records(scene):
    """{object id: {region, material, by, boxes, parts, lights}}: studio_refs.objects over the scene in id order (so a
    root is met before its parts), its boxes and lights sorted, so the record is a function of the scene's content."""
    O = R.objects(canon(scene))
    return {i: {"region": o["region"], "material": o["material"], "by": o["by"],
                "boxes": sorted(o["boxes"], key=enc), "parts": dict(sorted(o["parts"].items())),
                "lights": sorted(o["lights"], key=enc)} for i, o in sorted(O.items())}


# ------------------------------------------------------------------------------------------------ the diff
def change(x, y):
    """None if x and y are the same value; {"fields": {f: {"a"?, "b"?}}} for two objects (a side is absent when the
    field is); {"value": {"a", "b"}} otherwise."""
    if same(x, y):
        return None
    if isinstance(x, dict) and isinstance(y, dict):
        f = {}
        for k in sorted(set(x) | set(y)):
            if k in x and k in y and same(x[k], y[k]):
                continue
            e = {}
            if k in x:
                e["a"] = x[k]
            if k in y:
                e["b"] = y[k]
            f[k] = e
        return {"fields": f}
    return {"value": {"a": x, "b": y}}


def keyed(A, B):
    out = {"added": {}, "removed": {}, "changed": {}}
    for k in sorted(set(A) | set(B)):
        if k not in A:
            out["added"][k] = B[k]
        elif k not in B:
            out["removed"][k] = A[k]
        else:
            c = change(A[k], B[k])
            if c is not None:
                out["changed"][k] = c
    return out


def diff(a, b):
    """T1: a function of the two scenes' content (every collection keyed or sorted; no clock, file or randomness)."""
    d = {"format": FORMAT, "version": VERSION, "from": canon_sha(a), "to": canon_sha(b)}
    for k in SECTIONS:
        d[k] = keyed(_records(a, k), _records(b, k))
    t = change(_top(a), _top(b))
    d["top"] = t["fields"] if t else {}
    d["objects"] = keyed(object_records(a), object_records(b))
    return d


def _ab(e):
    r = {}
    if "b" in e:
        r["a"] = e["b"]
    if "a" in e:
        r["b"] = e["a"]
    return r


def _swap(c):
    if "value" in c:
        return {"value": _ab(c["value"])}
    return {"fields": {f: _ab(e) for f, e in c["fields"].items()}}


def invert_keyed(s):
    return {"added": dict(s["removed"]), "removed": dict(s["added"]), "changed": {k: _swap(c) for k, c in s["changed"].items()}}


def invert(d):
    """T2: invert(diff(a, b)) == diff(b, a), byte for byte, and invert is an involution."""
    out = {"format": d["format"], "version": d["version"], "from": d["to"], "to": d["from"]}
    for k in SECTIONS + ("objects",):
        out[k] = invert_keyed(d[k])
    out["top"] = {f: _ab(e) for f, e in d["top"].items()}
    return out


def _stale(what):
    raise DiffError("SCENE-DIFF-STALE", "the scene is not the diff's base: %s" % what)


def apply_fields(fields, x):
    y = dict(x)
    for f, e in fields.items():
        if "a" in e:
            if f not in y or not same(y[f], e["a"]):
                _stale("field %r" % f)
        elif f in y:
            _stale("field %r is present" % f)
        if "b" in e:
            y[f] = e["b"]
        else:
            del y[f]
    return y


def apply_change(c, x):
    if "value" in c:
        if not same(x, c["value"]["a"]):
            _stale("a value")
        return c["value"]["b"]
    return apply_fields(c["fields"], x)


def apply_keyed(s, A):
    out = dict(A)
    for k, v in s["removed"].items():
        if k not in out or not same(out[k], v):
            _stale("removed %r" % k)
        del out[k]
    for k, v in s["added"].items():
        if k in out:
            _stale("added %r exists" % k)
        out[k] = v
    for k, c in s["changed"].items():
        if k not in out:
            _stale("changed %r is absent" % k)
        out[k] = apply_change(c, out[k])
    return out


def apply(d, a, verify=True):
    """T3: the scene diff d leads to from a, in canonical form. Refused if a is not d's base; with verify, refused too if
    the result is not d's target (SCENE-DIFF-INCOMPLETE: a diff that does not say everything)."""
    if canon_sha(a) != d["from"]:
        _stale("its sha256 is %s, the diff's base %s" % (canon_sha(a)[:12], d["from"][:12]))
    top = apply_fields(d["top"], _top(a))
    out = {k: v for k, v in top.items() if not k.startswith("has:")}
    for k in SECTIONS:
        recs = apply_keyed(d[k], _records(a, k))
        if not top.get("has:" + k):
            if recs:
                raise DiffError("SCENE-DIFF-SHAPE", "%s has records but the scene has no %s" % (k, k))
            continue
        if k in KEYED_LISTS:
            out[k] = [r for _i, r in sorted(recs.items())]
        elif k in INDEXED:
            n = len(recs)
            if set(recs) != {"%d" % i for i in range(n)}:
                raise DiffError("SCENE-DIFF-SHAPE", "%s is not a list after the diff" % k)
            out[k] = [recs["%d" % i] for i in range(n)]
        else:
            out[k] = recs
    if verify and canon_sha(out) != d["to"]:
        raise DiffError("SCENE-DIFF-INCOMPLETE", "the diff applied to its base is not its target")
    return out


def apply_objects(d, O):
    return apply_keyed(d["objects"], O)


# ------------------------------------------------------------------------------------------------ the badges
def _badge(sec, field):
    """The badges one entry of the diff raises: field "*" is a record added or removed, "=" a whole value replaced."""
    if sec == "visuals":
        return "PM" if field == "*" else "M" if field == "material" else "" if field in ("by", "region") else "P"
    if sec in ("collision", "movers"):
        if field == "*":
            return "CM"
        if field == "material":
            return "M"
        return "" if (sec == "movers" and field == "by") else "C"
    if sec in ("lights", "materials", "environment"):
        return "M"
    if sec in ("tops", "spawns", "targets"):
        return "C"
    if sec in ("reach", "views", "regions", "assets"):
        return ""          # derived (reach), camera presets, region bounds, mesh declarations: listed, not badged
    if sec == "top":
        if field in ("format", "name", "title", "units") or field.startswith("has:"):
            return ""
        return "C"         # grid, rules, player, map, and any field this table does not know: play, conservatively
    raise DiffError("SCENE-DIFF-SECTION", "no section %r" % sec)


def entries(d):
    """Every entry of the diff, in order: (section, key, field, badges)."""
    out = []
    for sec in SECTIONS:
        s = d.get(sec) or {"added": {}, "removed": {}, "changed": {}}
        for k in sorted(s["added"]):
            out.append((sec, k, "*", _badge(sec, "*")))
        for k in sorted(s["removed"]):
            out.append((sec, k, "*", _badge(sec, "*")))
        for k in sorted(s["changed"]):
            c = s["changed"][k]
            for f in (["="] if "value" in c else sorted(c["fields"])):
                out.append((sec, k, f, _badge(sec, f)))
    for f in sorted(d.get("top") or {}):
        out.append(("top", "", f, _badge("top", f)))
    return out


def badges(d):
    """T4: M iff the look's projection changed, C iff the play's, P iff the placement's (scene_diff_test.py writes the
    projections apart from this table); each an OR over entries, so a sub-diff never raises more."""
    b = {"M": False, "C": False, "P": False}
    for _s, _k, _f, bs in entries(d):
        for x in bs:
            b[x] = True
    return b


def summary(d):
    E = entries(d)
    return {"badges": badges(d), "entries": len(E),
            "objects": {k: len(d["objects"][k]) for k in ("added", "removed", "changed")},
            "unbadged": ["%s/%s/%s" % (s, k, f) for s, k, f, bs in E if not bs][:24]}


# ------------------------------------------------------------------------------------------------ exact geometry
def q(x):
    """A coordinate as the exact decimal the scene states."""
    if isinstance(x, bool):
        raise DiffError("SCENE-DIFF-NUMBER", "a boolean is not a coordinate")
    if isinstance(x, Fraction):
        return x
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, float):
        if x != x or x in (float("inf"), float("-inf")):
            raise DiffError("SCENE-DIFF-NUMBER", "not a finite number")
        return Fraction(repr(x))
    if isinstance(x, str):
        return Fraction(x)
    raise DiffError("SCENE-DIFF-NUMBER", "not a number: %r" % (x,))


def cross(u, v):
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def frame(box, face):
    """MARK-0's frame of a box's face (art/studio_marks.py FRAMES, the one table), with n = u x v: the outward normal
    when the table is right-handed, as T5's frames property checks against the normals worked by hand."""
    if face not in SM.FRAMES:
        raise DiffError("SCENE-DIFF-FACE", "no face %r" % (face,))
    o, u, v, W, H = SM.frame([q(x) for x in box], face)
    return {"face": face, "origin": tuple(o), "u": u, "v": v, "n": cross(u, v), "W": W, "H": H}


def _axis(vec):
    nz = [(i, s) for i, s in enumerate(vec) if s]
    if len(nz) != 1 or nz[0][1] not in (1, -1):
        raise DiffError("SCENE-DIFF-FACE", "a frame axis that is not a signed unit axis")
    return nz[0]


def world(fr, p):
    """A surface-local point [u, v] (metres) in world coordinates: origin + u*p.u + v*p.v."""
    a, b = q(p[0]), q(p[1])
    return tuple(fr["origin"][i] + fr["u"][i] * a + fr["v"][i] * b for i in range(3))


def local_box(fr, box):
    """A world box in the frame's coordinates: (a0, a1, b0, b1, t0, t1), exact. u, v and n are signed axes, so an
    axis-aligned box stays an axis-aligned box: the reduction the containment test rests on (T5, step 1)."""
    B = [q(x) for x in box]
    out = []
    for vec in (fr["u"], fr["v"], fr["n"]):
        i, s = _axis(vec)
        lo, hi = s * (B[i] - fr["origin"][i]), s * (B[i + 3] - fr["origin"][i])
        out += [min(lo, hi), max(lo, hi)]
    return tuple(out)


def local_point(fr, p):
    P = [q(x) for x in p]
    return tuple(sum(vec[i] * (P[i] - fr["origin"][i]) for i in range(3)) for vec in (fr["u"], fr["v"], fr["n"]))


def orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def on_seg(p, a, b):
    return orient(a, b, p) == 0 and min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])


def pip(p, poly):
    """'boundary', 'inside' or 'outside' of a closed polygon (even-odd; exact)."""
    n = len(poly)
    for i in range(n):
        if on_seg(p, poly[i], poly[(i + 1) % n]):
            return "boundary"
    inside = False
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[1] > p[1]) != (b[1] > p[1]):
            x = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if p[0] < x:
                inside = not inside
    return "inside" if inside else "outside"


def clip_seg(a, b, rect):
    """The part of segment ab in the closed rectangle (x0, x1, y0, y1), or None (Liang-Barsky, exact)."""
    x0, x1, y0, y1 = rect
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = Fraction(0), Fraction(1)
    for p, r in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if p == 0:
            if r < 0:
                return None
        else:
            t = Fraction(r) / p
            if p < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
    if t0 > t1:
        return None
    return (a[0] + t0 * dx, a[1] + t0 * dy), (a[0] + t1 * dx, a[1] + t1 * dy)


def seg_meets_open(a, b, rect):
    """Whether segment ab has a point in the rectangle's interior: its clipped part's midpoint is interior iff any of
    it is (a segment between an interior point and a point of a convex set lies in its interior)."""
    c = clip_seg(a, b, rect)
    if c is None:
        return False
    m = ((c[0][0] + c[1][0]) / 2, (c[0][1] + c[1][1]) / 2)
    x0, x1, y0, y1 = rect
    return x0 < m[0] < x1 and y0 < m[1] < y1


def edges(poly, closed):
    n = len(poly)
    return [(poly[i], poly[(i + 1) % n]) for i in range(n if closed else n - 1)]


def rel2(poly, closed, rect):
    """(inside, overlap, meet) of a closed simple polygon (or a path) and a closed rectangle with an interior (T5, step
    3): inside, the rectangle lies in the polygon; overlap, their interiors meet; meet, they share a point. If no edge of
    P has a point in int(R), int(R) lies wholly in int(P) or wholly outside P, and R's centre says which; if an edge
    does, the interiors meet and R is not inside P. A path has no interior: it only meets or misses."""
    E = edges(poly, closed)
    hits_closed = any(clip_seg(a, b, rect) is not None for a, b in E)
    if not closed:
        return False, False, hits_closed
    hits_open = any(seg_meets_open(a, b, rect) for a, b in E)
    x0, x1, y0, y1 = rect
    cin = pip(((x0 + x1) / 2, (y0 + y1) / 2), poly) != "outside"
    return (not hits_open) and cin, hits_open or cin, hits_closed or cin


# ------------------------------------------------------------------------------------------------ shapes and regions
def status(rec, scene):
    """MARK-0's status of a kept shape in a scene, and its anchor box there (art/studio_marks.py status_of: one place)."""
    return SM.status_of(rec, scene)


def shape_status(rec, scene):
    return status(rec, scene)[0]


reach_of = SM.reach_of       # how far a shape's region reaches from its face (art/studio_marks.py reach_of)


def polygon_problems(verts, closed):
    """The host's checks of a shape's vertices (integer millimetres): a closed shape simple (art/studio_marks.py simple),
    a path without a zero-length edge."""
    if closed:
        ok, why = SM.simple(verts)
        return [] if ok else [why]
    return ["a path with a zero-length edge"] if any(verts[i] == verts[i + 1] for i in range(len(verts) - 1)) else []


def region(rec, scene, t=None):
    """The prism of a kept shape (VERDANDI-SHAPES 0) over the scene it is used against: its polygon on its anchor's face,
    swept along the face's outward normal n from the back of the anchor's box (t = minus its depth along n; an opening
    BACK_MARGIN further, through it) out to the shape's reach (studio_marks.reach_of: its own, or to the sky on a top
    face and 1 m elsewhere; None is no end). Refused (STUDIO-SHAPE) unless the shape is ok in that scene (T6: a stale
    shape is never re-read silently) and passes the host's checks; the anchor box is the scene's, never the page's.
    t, if given, is the interval [t0, t1] in metres in place of the shape's own (the self-test's)."""
    st, box = status(rec, scene)
    if st != "ok":
        raise DiffError("STUDIO-SHAPE", "#%s is %s in this scene: mark it again" % (rec.get("name"), st))
    face = rec["anchor"]["face"]
    fr = frame(box, face)
    verts = [(int(u), int(v)) for u, v in rec["vertices"]]
    poly = [(Fraction(u, 1000), Fraction(v, 1000)) for u, v in verts]
    closed = rec["operation"] != "path"
    bad = polygon_problems(verts, closed)
    if rec["constraints"].get("within", True) and any(not (0 <= u <= fr["W"] and 0 <= v <= fr["H"]) for u, v in poly):
        bad.append("a vertex off the face")
    if bad:
        raise DiffError("STUDIO-SHAPE", "#%s: %s" % (rec.get("name"), "; ".join(bad)))
    reach = reach_of(rec)
    depth = -local_box(fr, box)[4]          # the anchor behind its face: t from -depth to 0
    t0 = -depth - (min(reach, BACK_MARGIN) if reach is not None else BACK_MARGIN) if rec["operation"] == "subtract" else -depth
    if t is not None:
        t0, reach = q(t[0]), (None if t[1] is None else q(t[1]))
        if reach is not None and t0 > reach:
            raise DiffError("SCENE-DIFF-REGION", "an empty interval")
    return {"name": rec.get("name"), "operation": rec["operation"], "frame": fr, "poly": poly, "closed": closed,
            "t": (t0, reach), "reach": reach, "anchor": rec["anchor"]["piece"]}


def classify(box, reg):
    """T5: inside, the box lies in the prism (closed sets); crossing, their interiors meet and it does not; touching,
    they share only boundary; outside, they share nothing. A point (a light without a fixture) is inside or outside.
    Exact for axis-aligned boxes and simple polygons, convex or not; a path's prism has no volume (touching or outside).
    The prism's far end may be None (no end)."""
    a0, a1, b0, b1, s0, s1 = local_box(reg["frame"], box)
    T0, T1 = reg["t"]
    below = (lambda x: True) if T1 is None else (lambda x: x <= T1)
    if a0 == a1 and b0 == b1 and s0 == s1:
        if not (T0 <= s0 and below(s0)):
            return "outside"
        if reg["closed"]:
            return "inside" if pip((a0, b0), reg["poly"]) != "outside" else "outside"
        return "touching" if any(on_seg((a0, b0), a, b) for a, b in edges(reg["poly"], False)) else "outside"
    if a0 == a1 or b0 == b1 or s0 == s1:
        raise DiffError("SCENE-DIFF-DEGENERATE", "a flat box is neither a box nor a point")
    inside2, overlap2, meet2 = rel2(reg["poly"], reg["closed"], (a0, a1, b0, b1))
    hi = s1 if T1 is None else min(s1, T1)
    if inside2 and T0 <= s0 and below(s1):
        return "inside"
    if overlap2 and max(s0, T0) < hi:
        return "crossing"
    if meet2 and max(s0, T0) <= hi:
        return "touching"
    return "outside"


# ------------------------------------------------------------------------------------------------ the region account
def swept(m):
    """A mover's box over its whole travel (art/dress.py swept), exact."""
    b = [q(x) for x in m["box"]]
    dlen = Fraction(m["len"], QN)
    for i, a in enumerate(m["axis"]):
        if a > 0:
            b[i + 3] += dlen
        elif a < 0:
            b[i] -= dlen
    return b


def footprint(d, a, b):
    """Every box the diff changes, adds, removes or affects: [(object, reason, side, piece, box)], sorted. A visual's
    material, box, address or other field changed, a light changed (its fixture's box, or its position as a point), a
    visual made of a material whose record changed, a play box or mover changed. Provenance alone (a statement's hash)
    touches nothing (T7b). Objects are rooted against both scenes' ids (T7a)."""
    Va, Vb = _records(a, "visuals"), _records(b, "visuals")
    ids = set(Va) | set(Vb)
    rows = {}

    def add(obj, why, side, piece, box):      # one row a box: the same box on both sides is one row, sides "ab"
        rows.setdefault((obj, why, piece, enc([str(q(x)) for x in box])), set()).add(side)
    s = d["visuals"]
    for i in s["added"]:
        add(root(i, ids), "added", "b", i, Vb[i]["box"])
    for i in s["removed"]:
        add(root(i, ids), "removed", "a", i, Va[i]["box"])
    for i, c in s["changed"].items():
        fs = set(c["fields"]) if "fields" in c else {"="}
        if fs <= {"by"}:
            continue
        why = "box" if "box" in fs else "material" if "material" in fs else "address" if fs <= {"by", "region"} else "fields"
        add(root(i, ids), why, "a", i, Va[i]["box"])
        add(root(i, ids), why, "b", i, Vb[i]["box"])
    La, Lb = _records(a, "lights"), _records(b, "lights")
    s = d["lights"]
    for side, keys, V, L in (("a", s["removed"], Va, La), ("b", s["added"], Vb, Lb), ("a", s["changed"], Va, La), ("b", s["changed"], Vb, Lb)):
        for i in keys:
            if i in V:
                add(root(i, ids), "light", side, i, V[i]["box"])
            else:
                p = L[i]["pos"]
                add("light:" + i, "light", side, i, [p[0], p[1], p[2], p[0], p[1], p[2]])
    mats = set(d["materials"]["added"]) | set(d["materials"]["removed"]) | set(d["materials"]["changed"])
    Mb = _records(b, "materials")
    grew = True
    while grew:               # a material whose parent changed changed too (DIRECTOR-0's reference graph; no brief has one)
        grew = False
        for n in sorted(Mb):
            if n not in mats and isinstance(Mb[n], dict) and Mb[n].get("parent") in mats:
                mats.add(n)
                grew = True
    for i, v in sorted(Vb.items()):
        if v.get("material") in mats:
            add(root(i, ids), "material:" + v["material"], "b", i, v["box"])
    Ca, Cb = _records(a, "collision"), _records(b, "collision")
    s = d["collision"]
    for side, keys, C in (("a", s["removed"], Ca), ("b", s["added"], Cb), ("a", s["changed"], Ca), ("b", s["changed"], Cb)):
        for i in keys:
            add("play:" + i, "play", side, "play:" + i, C[i]["box"])
    for i, c in sorted(Cb.items()):
        if c.get("material") in mats:
            add("play:" + i, "surface:" + c["material"], "b", "play:" + i, c["box"])
    Ma, Mb2 = _records(a, "movers"), _records(b, "movers")
    s = d["movers"]
    for side, keys, M in (("a", s["removed"], Ma), ("b", s["added"], Mb2), ("a", s["changed"], Ma), ("b", s["changed"], Mb2)):
        for i in keys:
            add("mover:" + i, "mover (its travel)", side, "mover:" + i, swept(M[i]))
    return [(o, w, "".join(sorted(rows[(o, w, p, bx)])), p, [Fraction(x) for x in json.loads(bx)]) for o, w, p, bx in sorted(rows)]


def global_changes(d):
    """What changes the whole world, so is never held: the air, the tops, spawns and targets, a play field of top."""
    glob = ["environment/" + k for k in sorted(set(d["environment"]["added"]) | set(d["environment"]["removed"]) | set(d["environment"]["changed"]))]
    glob += ["%s/%s" % (s, k) for s in ("tops", "spawns", "targets") for k in sorted(set(d[s]["added"]) | set(d[s]["removed"]) | set(d[s]["changed"]))]
    glob += ["top/" + f for f in sorted(d["top"]) if _badge("top", f)]
    return glob


def account(d, a, b, reg, rows=None):
    """The region account of a candidate: each object the diff touches, its boxes' relations to the shape's prism, and
    whether it is held (every box inside). The verdict: empty (nothing physical changed), held (every object held),
    adjacent (nothing beyond the region's boundary, something on it: a tower on the cell beside a marked floor), missed
    (changed things, none of them in the region), outside (the rest; and any change of the whole world)."""
    objs = {}
    for o, why, side, piece, box in (footprint(d, a, b) if rows is None else rows):
        r = classify(box, reg)
        e = objs.setdefault(o, {"reasons": [], "relations": {"inside": 0, "crossing": 0, "touching": 0, "outside": 0}})
        if why not in e["reasons"]:
            e["reasons"].append(why)
        e["relations"][r] += 1
    for e in objs.values():
        e["reasons"].sort()
        r = e["relations"]
        n = sum(r.values())
        e["held"] = r["inside"] == n
        e["class"] = "held" if e["held"] else "adjacent" if r["crossing"] == 0 and r["outside"] == 0 else \
            "elsewhere" if r["outside"] == n else "straddles"
    glob = global_changes(d)
    outside = sorted(o for o, e in objs.items() if not e["held"])
    classes = {e["class"] for e in objs.values()}
    if not objs and not glob:
        verdict = "empty"
    elif glob:
        verdict = "outside"
    elif classes == {"held"}:
        verdict = "held"
    elif classes <= {"held", "adjacent"}:
        verdict = "adjacent"
    elif classes == {"elsewhere"}:
        verdict = "missed"
    else:
        verdict = "outside"
    return {"region": reg["name"], "verdict": verdict, "objects": objs, "outside": outside, "global": glob}


VERDICTS = ("held", "adjacent", "empty", "outside", "missed", "stale")


# STRICT-0 (0238): region-strict admission. A request may be strict: then a candidate is admitted only when its footprint
# lies within the union of the named shapes' regions. Its receipt is that footprint, box by box, each with the shapes
# whose regions hold it; its inverse receipt is the footprint of the change back, held against the same regions (the
# regions are the request's, computed in the candidate's base, and do not move with the change).
STRICT_CODES = ("ADMIT-OUTSIDE", "ADMIT-EMPTY", "ADMIT-STALE")


def dec(f):
    """A coordinate as exact decimal text (a scene's numbers are decimals, so the expansion ends)."""
    f = Fraction(f)
    n, d = abs(f.numerator), f.denominator
    k = next((k for k in range(65) if (n * 10 ** k) % d == 0), None)
    if k is None:
        raise DiffError("SCENE-DIFF-NUMBER", "%s is not a decimal" % f)
    t = str(n * 10 ** k // d).rjust(k + 1, "0")
    t = t[:-k] + "." + t[-k:] if k else t
    return ("-" if f < 0 else "") + t


def receipt_of(rows, regs):
    """[{piece, object, why, sides, box, inside}] for footprint rows, `inside` naming the regions that hold each box."""
    return [{"piece": piece, "object": o, "why": why, "sides": side, "box": [dec(x) for x in box],
             "inside": sorted(n for n, reg in regs if classify(box, reg) == "inside")} for o, why, side, piece, box in rows]


def strict(a, b, shapes):
    """The strict check of a candidate `b` against its base `a` and the request's shape records: ok when something in the
    world's boxes changed, nothing changed the whole world (the air, the tops, spawns or targets), and every box of the
    footprint lies inside at least one shape's region; else ADMIT-OUTSIDE (a box outside every region, or a change of
    the whole world), ADMIT-EMPTY (nothing to hold), ADMIT-STALE (no shape, or one not as marked in the base). With its
    receipt and inverse receipt and their sha256. A function of the two scenes and the records alone."""
    regs, stale = [], []
    for rec in shapes:
        try:
            regs.append((rec.get("name"), region(rec, a)))
        except DiffError:
            stale.append(rec.get("name"))
    d = diff(a, b)
    rows = footprint(d, a, b)
    rec_ = receipt_of(rows, regs)
    inv = receipt_of(footprint(diff(b, a), b, a), regs)
    outside = [r["piece"] for r in rec_ if not r["inside"]]
    glob = global_changes(d)
    code = "ADMIT-STALE" if stale or not regs else "ADMIT-OUTSIDE" if outside or glob else "ADMIT-EMPTY" if not rows else ""
    sha = lambda v: hashlib.sha256(enc(v).encode("ascii")).hexdigest()
    return {"format": "VERDANDI-STRICT", "version": "0", "ok": not code, "code": code, "shapes": [n for n, _r in regs], "stale": stale,
            "outside": outside[:16], "outside_count": len(outside), "global": glob[:12], "count": len(rec_),
            "receipt": rec_, "receipt_sha256": sha(rec_), "inverse_receipt": inv, "inverse_receipt_sha256": sha(inv)}


def report(a, b, shapes=()):
    """What the studio keeps of a candidate (play.candidate_slot): the diff's summary and M, C and P; for each shape the
    request names, its account against the candidate's own base `a` (or "stale", if the shape is not ok in it); and the
    boxes the page outlines in Diff mode, each with its relation to the first shape's region. Floats only for drawing."""
    d = diff(a, b)
    rows = footprint(d, a, b)
    out = {"format": "VERDANDI-HELD", "version": "0", "base": d["from"], "target": d["to"], **summary(d), "accounts": []}
    first = None
    for rec in shapes:
        try:
            reg = region(rec, a)
        except DiffError as e:
            out["accounts"].append({"shape": rec.get("name"), "verdict": "stale", "detail": e.detail})
            continue
        acc = account(d, a, b, reg, rows)
        first = first or reg
        cls = {}
        for e in acc["objects"].values():
            cls[e["class"]] = cls.get(e["class"], 0) + 1
        out["accounts"].append({"shape": rec.get("name"), "verdict": acc["verdict"], "classes": dict(sorted(cls.items())),
                                "objects": len(acc["objects"]), "outside": acc["outside"][:16], "outside_count": len(acc["outside"]),
                                "global": acc["global"][:12],
                                "reach_m": None if reg["reach"] is None else float(reg["reach"]),
                                "held": sorted(o for o, e in acc["objects"].items() if e["held"])[:16]})
    out["boxes"] = [{"object": o, "why": w, "side": s, "piece": p, "box": [float(x) for x in bx],
                     "relation": classify(bx, first) if first else None} for o, w, s, p, bx in rows[:400]]
    out["boxes_count"] = len(rows)
    return out


# ------------------------------------------------------------------------------------------------ command line
def _load(p):
    with open(p, "rb") as fh:
        doc = json.loads(fh.read().decode("utf-8"))
    return doc.get("scene", doc) if isinstance(doc, dict) else doc


def main(argv):
    if argv[:1] == ["selftest"]:
        import scene_diff_test
        return scene_diff_test.main(argv[1:])
    if len(argv) == 3 and argv[0] == "diff":
        a, b = _load(argv[1]), _load(argv[2])
        print(json.dumps(summary(diff(a, b)), indent=1, sort_keys=True))
        return 0
    if len(argv) == 5 and argv[0] == "account":
        a, b = _load(argv[1]), _load(argv[2])
        shapes = json.loads(open(argv[3], "rb").read().decode("utf-8"))["shapes"]
        rec = [s for s in shapes if s["name"] == argv[4]]
        if not rec:
            print("no shape %r in %s" % (argv[4], argv[3]))
            return 2
        print(json.dumps(account(diff(a, b), a, b, region(rec[0], a)), indent=1, sort_keys=True, default=str))
        return 0
    print("usage: scene_diff.py selftest | diff A.json B.json | account A.json B.json SHAPES.json NAME")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
