# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/studio_marks.py — MARK-0 (0231): marks and shapes on the scene's surfaces, the designer's way of pointing at
# part of a surface ("this part of that wall") so that the director can be asked about exactly that region.
#
#   python art/studio_marks.py selftest [--pure]      (--pure: the predicates and the file, without the launcher)
#
# A SHAPE is the designer's markup, never the world. It is anchored to one face of one box of the scene (a box of the
# dressing, or of the play geometry, C), and its vertices are surface-local: metres along the face's u and v from the
# face's origin, at most three decimals (a millimetre), held here as integer millimetres. Every predicate on a shape
# (is it simple, does it stay on the face, does it admit a body) is decided in exact arithmetic (integers and
# fractions.Fraction; no float is compared), so that it gives one answer on every machine.
#
# THE FACE FRAMES. For a box [x0, y0, z0, x1, y1, z1] and a face, an origin o and two unit vectors u and v with u x v the
# face's outward normal (seen from outside the box, u runs right and v up; on the top face u is east and v north):
#
#   +x  o (x1, y0, z1)  u (0, 0, -1)  v (0, 1, 0)   W z1-z0  H y1-y0        -x  o (x0, y0, z0)  u (0, 0, 1)   v (0, 1, 0)
#   +z  o (x0, y0, z1)  u (1, 0, 0)   v (0, 1, 0)   W x1-x0  H y1-y0        -z  o (x1, y0, z0)  u (-1, 0, 0)  v (0, 1, 0)
#   +y  o (x0, y1, z1)  u (1, 0, 0)   v (0, 0, -1)  W x1-x0  H z1-z0        -y  o (x0, y0, z0)  u (1, 0, 0)   v (0, 0, 1)
#
# and a point (a, b) of the face is o + a u + b v; (a, b) runs over [0, W] x [0, H] exactly when the point runs over the
# face's rectangle (u and v are two of the axes, signed, so the map is a translation and a signed permutation: a
# bijection, and its inverse is the dot product with u and v). art/web/studio_ui.js holds the same table (FRAMES).
#
# STATUS. A shape is bound to the box it was marked on: the box's id and its six coordinates as they were. Against the
# scene served now it is "ok" (a box of that id with exactly those coordinates: every vertex is where it was, in the
# world), "changed" (the id is there, its box is not: the vertices are read again in the new face's frame and its
# checks run again, and the change is said, never hidden), or "gone" (no box of that id). Only an ok shape is the
# director's input (STUDIO-SHAPE otherwise): a shape is never moved to another surface, as a tag is never moved to
# another object.
#
# CHECKS, by the host, never taken from the page: within (every vertex on the face), simple (a closed shape: no zero-
# length edge, no edge folding back on the one before it, no two edges that are not neighbours meeting, and an area),
# and clearance (an opening or an addition on an upright face admits an upright rectangle as wide as a body, 2 r, and
# as tall as the clearance asked; decided exactly, CLEARANCE below). The constraints "preserve structural supports",
# "update collision" and the material are WORDS: they are passed to the director as the designer's words, and the page
# says that nothing checks them.
#
# The shapes of a world are kept in <root>/art/ledger/<brief>.shapes.json (VERDANDI-SHAPES 0, the canonical bytes of
# DIRECTOR-0, integers as strings), written whole through durable.write under the tree's content lock, as the tags are.
# A file this module cannot read is never overwritten. Standard library only.

import os
import re
import sys
import threading
from decimal import Decimal, InvalidOperation
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "director"))
import durable            # noqa: E402  (crash-safe writes under the content lock)
import intent as canon    # noqa: E402  (DIRECTOR-0's canonical bytes)
import ledger as led      # noqa: E402  (the content lock's place)

FORMAT, VERSION = "VERDANDI-SHAPES", "0"
FACES = ("+x", "-x", "+y", "-y", "+z", "-z")
UPRIGHT = ("+x", "-x", "+z", "-z")
OPERATIONS = {"subtract": "an opening (subtract)", "add": "an addition (add)", "region": "a region", "path": "a path"}
NAME = re.compile(r"[a-z][a-z0-9_]{0,39}\Z")
MENTION = re.compile(r"(?<![A-Za-z0-9_&#])#([a-z][a-z0-9_]{0,39})(?![A-Za-z0-9_])")
PIECE = re.compile(r"(play:)?[A-Za-z0-9_.,:+-]{1,160}\Z")
MATERIAL = re.compile(r"[a-z][a-z0-9_]{0,39}\Z")
MAX_VERTICES, MAX_SHAPES, NOTE_MAX = 64, 64, 200
LIMIT_MM = 10 ** 9                    # a thousand kilometres: a coordinate beyond it is not a coordinate of this world
CLEARANCE_MAX_VERTICES = 16           # the exact clearance test's reach (CLEARANCE); beyond it the check says NOT CHECKED
DECIMAL = re.compile(r"-?(0|[1-9][0-9]{0,11})(\.[0-9]{1,12})?\Z")


class ShapeError(Exception):
    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code, self.detail = code, detail


# ------------------------------------------------------------------------------------------------ exact numbers
def exact(x, what):
    """A number of a JSON document, exactly: an int, a Decimal (play.py reads a shape's body with parse_float=Decimal,
    so that a number is the decimal written, not the nearest double), a float read as the decimal of its shortest repr,
    or a decimal string. A bool, NaN, an infinity or anything else is refused."""
    if isinstance(x, bool) or not isinstance(x, (int, float, str, Decimal)):
        raise ShapeError("SHAPE-NUMBER", "%s is not a number" % what)
    if isinstance(x, Decimal):
        if not x.is_finite():
            raise ShapeError("SHAPE-NUMBER", "%s is not finite" % what)
        d = x
    elif isinstance(x, float):
        if x != x or x in (float("inf"), float("-inf")):
            raise ShapeError("SHAPE-NUMBER", "%s is not finite" % what)
        d = Decimal(repr(x))
    elif isinstance(x, int):
        d = Decimal(x)
    else:
        if not DECIMAL.match(x):
            raise ShapeError("SHAPE-NUMBER", "%s %r is not a decimal" % (what, x[:40]))
        d = Decimal(x)
    try:
        return Fraction(d)
    except (InvalidOperation, ValueError, OverflowError):
        raise ShapeError("SHAPE-NUMBER", "%s is not a number" % what)


def mm(x, what):
    """Exact millimetres of a length in metres given with at most three decimals."""
    f = exact(x, what) * 1000
    if f.denominator != 1:
        raise ShapeError("SHAPE-NUMBER", "%s has more than three decimals: a shape is drawn to the millimetre" % what)
    if abs(f) > LIMIT_MM:
        raise ShapeError("SHAPE-NUMBER", "%s is out of range" % what)
    return int(f)


def dec(f):
    """A Fraction with a finite decimal as its shortest decimal string, exactly (refused if it has none)."""
    f = Fraction(f)
    if f.denominator == 1:
        return str(f.numerator)
    t = format((Decimal(f.numerator) / Decimal(f.denominator)).normalize(), "f")
    if Fraction(Decimal(t)) != f:
        raise ShapeError("SHAPE-NUMBER", "%s has no short decimal" % f)
    return t


def box_of(raw):
    return [exact(x, "a box coordinate") for x in raw]


# ------------------------------------------------------------------------------------------------ the face frames
FRAMES = {
    "+x": lambda b: ((b[3], b[1], b[5]), (0, 0, -1), (0, 1, 0), b[5] - b[2], b[4] - b[1]),
    "-x": lambda b: ((b[0], b[1], b[2]), (0, 0, 1), (0, 1, 0), b[5] - b[2], b[4] - b[1]),
    "+z": lambda b: ((b[0], b[1], b[5]), (1, 0, 0), (0, 1, 0), b[3] - b[0], b[4] - b[1]),
    "-z": lambda b: ((b[3], b[1], b[2]), (-1, 0, 0), (0, 1, 0), b[3] - b[0], b[4] - b[1]),
    "+y": lambda b: ((b[0], b[4], b[5]), (1, 0, 0), (0, 0, -1), b[3] - b[0], b[5] - b[2]),
    "-y": lambda b: ((b[0], b[1], b[2]), (1, 0, 0), (0, 0, 1), b[3] - b[0], b[5] - b[2]),
}
NORMALS = {"+x": (1, 0, 0), "-x": (-1, 0, 0), "+y": (0, 1, 0), "-y": (0, -1, 0), "+z": (0, 0, 1), "-z": (0, 0, -1)}


def frame(box, face):
    return FRAMES[face](box)


def world(F, a, b):
    """The world point of face-local (a, b), in the face frame F; a and b in the box's own unit (metres)."""
    o, u, v = F[0], F[1], F[2]
    return tuple(o[i] + u[i] * a + v[i] * b for i in range(3))


def local(F, p):
    o, u, v = F[0], F[1], F[2]
    d = [p[i] - o[i] for i in range(3)]
    return sum(d[i] * u[i] for i in range(3)), sum(d[i] * v[i] for i in range(3))


# ------------------------------------------------------------------------------------------------ exact predicates
def orient(a, b, c):
    """The sign of the turn a -> b -> c: 1 left, -1 right, 0 collinear."""
    d = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return (d > 0) - (d < 0)


def _on(a, b, p):
    """p on the closed segment ab, given that the three are collinear."""
    return min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])


def meet(a, b, c, d):
    """Do the closed segments ab and cd share a point?"""
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    if o1 != o2 and o3 != o4:
        return True
    return (o1 == 0 and _on(a, b, c)) or (o2 == 0 and _on(a, b, d)) or (o3 == 0 and _on(c, d, a)) or (o4 == 0 and _on(c, d, b))


def area2(poly):
    """Twice the signed area (positive counter-clockwise in the face's u, v)."""
    n = len(poly)
    return sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))


def simple(poly):
    """(True, "") if the closed polygon is simple, else (False, why). Exact; O(n^2), n <= 64.
    Decided: a zero-length edge is not simple; two neighbouring edges meet only at their shared vertex (an edge that
    folds back over the one before it, collinear and reversed, is not); two edges that are not neighbours do not meet
    at all (touching at a point is meeting); and the area is not zero."""
    n = len(poly)
    if n < 3:
        return False, "a closed shape has at least three vertices"
    for i in range(n):
        if poly[i] == poly[(i + 1) % n]:
            return False, "vertices %d and %d are the same point (a zero-length edge)" % (i, (i + 1) % n)
    for i in range(n):
        a, b, c = poly[i], poly[(i + 1) % n], poly[(i + 2) % n]
        if orient(a, b, c) == 0 and (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1]) < 0:
            return False, "the edge from vertex %d folds back over the one before it" % ((i + 1) % n)
    for i in range(n):
        for j in range(i + 1, n):
            if j == i + 1 or (i == 0 and j == n - 1):
                continue
            if meet(poly[i], poly[(i + 1) % n], poly[j], poly[(j + 1) % n]):
                return False, "edges %d and %d meet" % (i, j)
    if area2(poly) == 0:
        return False, "the shape has no area"
    return True, ""


def inside(poly, p):
    """p strictly inside the polygon, by the crossing number (p must not be on its boundary: the caller knows)."""
    c, n = False, len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[1] > p[1]) != (b[1] > p[1]):
            x = a[0] + Fraction(p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if p[0] < x:
                c = not c
    return c


def enters_open_box(a, b, lo, hi):
    """Does the closed segment ab meet the open box lo < p < hi (exact, Liang-Barsky)?"""
    L, U, Lx, Ux = Fraction(0), Fraction(1), False, False     # [0, 1], both ends included
    for k in range(2):
        d = b[k] - a[k]
        if d == 0:
            if not (lo[k] < a[k] < hi[k]):
                return False
            continue
        t1, t2 = Fraction(lo[k] - a[k]) / d, Fraction(hi[k] - a[k]) / d
        if t1 > t2:
            t1, t2 = t2, t1
        if t1 >= L:
            L, Lx = t1, True
        if t2 <= U:
            U, Ux = t2, True
    return L < U


def holds_rect(poly, lo, w, h):
    """The rectangle [lo, lo + (w, h)] inside the closed polygon: no edge meets its open interior, and its centre is
    inside (with no edge in the interior, the open interior is wholly inside or wholly outside)."""
    hi = (lo[0] + w, lo[1] + h)
    n = len(poly)
    for i in range(n):
        if enters_open_box(poly[i], poly[(i + 1) % n], lo, hi):
            return False
    return inside(poly, (lo[0] + Fraction(w, 2), lo[1] + Fraction(h, 2)))


def _lines(poly, w, h):
    """CLEARANCE's lines: each edge's line moved by each of the rectangle's corners, and the horizontal and vertical
    lines through each vertex moved by them. A line is (p, d): the points p + t d."""
    n, out = len(poly), set()
    corners = ((0, 0), (w, 0), (0, h), (w, h))
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        d = (b[0] - a[0], b[1] - a[1])
        for c in corners:
            out.add(((a[0] - c[0], a[1] - c[1]), d))
    for v in poly:
        for c in corners:
            out.add(((v[0] - c[0], v[1] - c[1]), (1, 0)))
            out.add(((v[0] - c[0], v[1] - c[1]), (0, 1)))
    return sorted(out)


def admits_rect(poly, w, h, max_y=None):
    """CLEARANCE: does the simple polygon contain an upright w x h rectangle (w, h > 0), with its bottom at most max_y if
    given? Exact.
    The rectangle's lower-left corners that fit form F = P eroded by the rectangle, a closed bounded set whose boundary
    lies on the lines of _lines (the boundary of the complement grown by the rectangle is made of the polygon's edges
    moved by the rectangle's corners and the rectangle's edges moved to the polygon's vertices). If F is not empty, its
    lowest leftmost point is a vertex of the arrangement of those lines: a point where two of them cross. So F is not
    empty exactly when the rectangle fits at one of those crossings, which are finitely many. With max_y: that lowest
    point has the least y of all F, so a fit with its bottom at most max_y exists exactly when one of the crossings
    with y at most max_y fits. Returns (bool, the corner found or None, the number of candidates tried)."""
    if w <= 0 or h <= 0:
        raise ShapeError("SHAPE-CLEARANCE", "a rectangle has a positive width and height")
    L = _lines(poly, w, h)
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    bx0, bx1, by0, by1 = min(xs), max(xs) - w, min(ys), max(ys) - h
    if max_y is not None:
        by1 = min(by1, max_y)
    if bx0 > bx1 or by0 > by1:
        return False, None, 0
    seen, tried = set(), 0
    for i in range(len(L)):
        (p1, d1) = L[i]
        for j in range(i + 1, len(L)):
            (p2, d2) = L[j]
            den = d1[0] * d2[1] - d1[1] * d2[0]
            if den == 0:
                continue
            t = Fraction((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0], den)
            q = (p1[0] + t * d1[0], p1[1] + t * d1[1])
            if not (bx0 <= q[0] <= bx1 and by0 <= q[1] <= by1) or q in seen:
                continue
            seen.add(q)
            tried += 1
            if holds_rect(poly, q, w, h):
                return True, q, tried
    return False, None, tried


# ------------------------------------------------------------------------------------------------ the scene's boxes
def box_in(scene, piece):
    """(box as Fractions, layer, the raw box) of a piece: a visual's box id, or play:ID for a box of C. None if there is
    none; "ambiguous" if the id names more than one box (QUALITY-0 refuses such a scene; a shape never guesses)."""
    if piece.startswith("play:"):
        hits = [c for c in scene.get("collision", []) if c["id"] == piece[5:]]
        layer = "play"
    else:
        hits = [v for v in scene.get("visuals", []) if v["id"] == piece]
        layer = piece.split(":", 1)[0]
    if len(hits) > 1:
        return "ambiguous"
    return (box_of(hits[0]["box"]), layer, hits[0]["box"]) if hits else None


# ------------------------------------------------------------------------------------------------ a shape
def parse(doc, scene, sha, player_radius=None):
    """A shape as the page sends it, checked against the scene served now (`sha` its digest). Returns the record kept
    (the canonical form: integers as strings) or raises ShapeError. The page's anchor must name a box of this scene with
    exactly the coordinates it gives: a shape is marked on the world as it is drawn now, never on an older scene."""
    if not isinstance(doc, dict):
        raise ShapeError("SHAPE-FORMAT", "a shape is an object")
    extra = set(doc) - {"name", "operation", "anchor", "vertices", "constraints", "note"}
    if extra:
        raise ShapeError("SHAPE-FORMAT", "unknown field(s): %s" % ", ".join(sorted(extra))[:120])
    name = doc.get("name")
    if not isinstance(name, str) or not NAME.match(name):
        raise ShapeError("SHAPE-NAME", "a shape's name is a lower-case letter, then letters, digits or _, at most 40")
    op = doc.get("operation")
    if op not in OPERATIONS:
        raise ShapeError("SHAPE-OPERATION", "the operation is one of %s" % ", ".join(sorted(OPERATIONS)))
    an = doc.get("anchor")
    if not isinstance(an, dict) or set(an) - {"piece", "face", "box", "scene", "view"}:
        raise ShapeError("SHAPE-ANCHOR", "an anchor is {piece, face, box, scene, view}")
    piece, face = an.get("piece"), an.get("face")
    if not isinstance(piece, str) or not PIECE.match(piece) or piece.startswith(("mover:", "target:")):
        raise ShapeError("SHAPE-PIECE", "a shape is marked on a box of the dressing or of the play geometry (a mover or a target moves)")
    if face not in FACES:
        raise ShapeError("SHAPE-FACE", "the face is one of %s" % " ".join(FACES))
    if an.get("scene") != sha:
        raise ShapeError("SHAPE-STALE", "the shape was marked on scene %s, not on the world as it is served now (%s): mark it again" % (
            str(an.get("scene"))[:12], sha[:12]))
    got = box_in(scene, piece)
    if got is None or got == "ambiguous":
        raise ShapeError("SHAPE-PIECE", ("no box %r in the scene" if got is None else "more than one box is %r") % piece[:80])
    box, layer, raw = got
    given = an.get("box")
    if not isinstance(given, list) or len(given) != 6 or [exact(x, "the anchor's box") for x in given] != box:
        raise ShapeError("SHAPE-STALE", "the anchor's box is not the box of %s in the scene served now: mark it again" % piece[:80])
    view = an.get("view") or {}
    if not isinstance(view, dict) or set(view) - {"x", "y", "z", "yaw_deg", "pitch_deg"}:
        raise ShapeError("SHAPE-ANCHOR", "a view is {x, y, z, yaw_deg, pitch_deg}")
    vw = {k: str(round(exact(view[k], "the view's " + k) * 1000)) for k in sorted(view)}     # provenance, kept to the millimetre
    vs = doc.get("vertices")
    closed = op != "path"
    if not isinstance(vs, list) or not (3 if closed else 2) <= len(vs) <= MAX_VERTICES:
        raise ShapeError("SHAPE-VERTICES", "a %s has %d to %d vertices" % ("closed shape" if closed else "path", 3 if closed else 2, MAX_VERTICES))
    verts = []
    for i, p in enumerate(vs):
        if not isinstance(p, list) or len(p) != 2:
            raise ShapeError("SHAPE-VERTICES", "vertex %d is [u, v]" % i)
        verts.append((mm(p[0], "vertex %d's u" % i), mm(p[1], "vertex %d's v" % i)))
    c = doc.get("constraints") or {}
    if not isinstance(c, dict) or set(c) - {"within", "clearance_m", "supports", "collision", "material"}:
        raise ShapeError("SHAPE-CONSTRAINTS", "constraints are {within, clearance_m, supports, collision, material}")
    for k in ("within", "supports", "collision"):
        if not isinstance(c.get(k, False), bool):
            raise ShapeError("SHAPE-CONSTRAINTS", "%s is true or false" % k)
    clear = c.get("clearance_m")
    clear_mm = None if clear is None else mm(clear, "the clearance")
    if clear_mm is not None and not (0 < clear_mm <= 20000):
        raise ShapeError("SHAPE-CONSTRAINTS", "a clearance is more than 0 and at most 20 m")
    mat = c.get("material", "keep")
    if not isinstance(mat, str) or not (mat == "keep" or (MATERIAL.match(mat) and mat in scene.get("materials", {}))):
        raise ShapeError("SHAPE-CONSTRAINTS", "the material is keep or one of the scene's materials")
    note = doc.get("note", "")
    if not isinstance(note, str) or len(note) > NOTE_MAX or any(ord(ch) < 0x20 or ord(ch) == 0x7F or 0xD800 <= ord(ch) <= 0xDFFF for ch in note):
        raise ShapeError("SHAPE-NOTE", "a note is at most %d characters of text on one line (no control character, no half of a character)" % NOTE_MAX)
    rec = {"name": name, "operation": op,
           "anchor": {"piece": piece, "face": face, "box": [dec(x) for x in box], "scene": sha, "view": vw},
           "vertices": [[str(u), str(v)] for u, v in verts],
           "constraints": {"within": bool(c.get("within", True)), "supports": bool(c.get("supports", False)),
                           "collision": bool(c.get("collision", False)), "material": mat,
                           "clearance_mm": "" if clear_mm is None else str(clear_mm)},
           "note": note}
    ev = evaluate(rec, scene, player_radius)
    if not ev["checks"]["simple"]["ok"]:
        raise ShapeError("SHAPE-SIMPLE", ev["checks"]["simple"]["detail"])
    if rec["constraints"]["within"] and not ev["checks"]["within"]["ok"]:
        raise ShapeError("SHAPE-WITHIN", ev["checks"]["within"]["detail"])
    return rec


def evaluate(rec, scene, player_radius=None):
    """A kept shape against a scene: its status, its world polygon, and the host's checks. Pure."""
    piece, face = rec["anchor"]["piece"], rec["anchor"]["face"]
    got = box_in(scene, piece)
    bound = [Fraction(Decimal(x)) for x in rec["anchor"]["box"]]
    out = {"name": rec["name"], "operation": rec["operation"], "closed": rec["operation"] != "path", "piece": piece, "face": face,
           "layer": "play" if piece.startswith("play:") else piece.split(":", 1)[0], "note": rec["note"],
           "vertices_m": [[int(u) / 1000, int(v) / 1000] for u, v in rec["vertices"]],
           "constraints": dict(rec["constraints"]), "bound_scene": rec["anchor"]["scene"]}
    if got is None or got == "ambiguous":
        out.update(status="gone" if got is None else "ambiguous", checks={}, world_m=None,
                   why="no box %s in the scene served now; the shape stays, listed apart" % piece if got is None else
                   "more than one box is %s; a shape never guesses which" % piece)
        return out
    box = got[0]
    out["status"] = "ok" if box == bound else "changed"
    F = frame(box, face)
    if out["status"] == "changed":
        F0 = frame(bound, face)
        out["face_same"] = F0[0] == F[0] and F0[3] == F[3] and F0[4] == F[4]
        out["why"] = ("the box of %s changed behind the marked face, which is where it was: every vertex is where it was" if out["face_same"] else
                      "the box of %s has moved or changed size since it was marked: the vertices are read again on the new face") % piece
    W, H = F[3], F[4]
    verts = [(int(u), int(v)) for u, v in rec["vertices"]]
    poly_m = [(Fraction(u, 1000), Fraction(v, 1000)) for u, v in verts]
    out["world_m"] = [[float(c) for c in world(F, a, b)] for a, b in poly_m]
    out["face_m"] = {"width": float(W), "height": float(H), "normal": list(NORMALS[face]), "origin": [float(c) for c in F[0]],
                     "u": list(F[1]), "v": list(F[2])}
    outside = [i for i, (a, b) in enumerate(poly_m) if not (0 <= a <= W and 0 <= b <= H)]
    checks = {"within": {"ok": not outside, "by": "host",
                         "detail": "every vertex on the face (%s x %s m)" % (dec(W), dec(H)) if not outside else
                         "vertices %s are off the face (%s x %s m)" % (", ".join(str(i) for i in outside[:8]), dec(W), dec(H))}}
    if out["closed"]:
        ok, why = simple(verts)
        a2 = area2(verts)
        checks["simple"] = {"ok": ok, "by": "host", "detail": why or "a simple polygon of %d vertices, %s m2" % (len(verts), dec(Fraction(abs(a2), 2 * 10 ** 6)))}
        out["area_m2"] = float(Fraction(abs(a2), 2 * 10 ** 6))
    else:
        zero = [i for i in range(len(verts) - 1) if verts[i] == verts[i + 1]]
        checks["simple"] = {"ok": not zero, "by": "host", "detail": "a path of %d vertices" % len(verts) if not zero else "vertices %d and %d are the same point" % (zero[0], zero[0] + 1)}
        out["length_m"] = sum(((poly_m[i + 1][0] - poly_m[i][0]) ** 2 + (poly_m[i + 1][1] - poly_m[i][1]) ** 2) ** 0.5 for i in range(len(poly_m) - 1))
    cl = rec["constraints"]["clearance_mm"]
    if cl and out["closed"] and rec["operation"] in ("subtract", "add"):
        r = Fraction(Decimal(repr(player_radius if player_radius is not None else scene.get("player", {}).get("radius", 0.35))))
        wmm = 2 * r * 1000
        if face not in UPRIGHT:
            checks["clearance"] = {"ok": None, "by": "host", "detail": "NOT CHECKED: a clearance is checked on an upright face; this is the %s face" % face}
        elif not checks["simple"]["ok"]:
            checks["clearance"] = {"ok": None, "by": "host", "detail": "NOT CHECKED: the shape is not simple"}
        elif len(verts) > CLEARANCE_MAX_VERTICES:
            checks["clearance"] = {"ok": None, "by": "host", "detail": "NOT CHECKED: more than %d vertices (the exact test's reach)" % CLEARANCE_MAX_VERTICES}
        else:
            # an opening must let a body walk through: the rectangle stands within a step of the face's foot (v = 0, the
            # box's underside); an addition need only hold one
            step = Fraction(Decimal(repr(scene.get("player", {}).get("step", 0.55)))) * 1000
            walk = rec["operation"] == "subtract"
            ok, at, n = admits_rect(verts, wmm, int(cl), step if walk else None)
            size = "%s x %s m" % (dec(wmm / 1000), dec(Fraction(int(cl), 1000)))
            checks["clearance"] = {"ok": ok, "by": "host",
                                   "detail": ("a body %s: an upright %s rectangle at u %s, v %s m" % ("walks through" if walk else "fits", size, dec(at[0] / 1000), dec(at[1] / 1000)) if ok else
                                              "no upright %s rectangle fits in the outline%s (%d positions tried, exactly)" % (
                                                  size, " standing within a step (%s m) of the face's foot" % dec(step / 1000) if walk else "", n))}
    out["checks"] = checks
    out["words"] = [w for w, on in (("preserve the structural supports", rec["constraints"]["supports"]),
                                    ("update the collision to match", rec["constraints"]["collision"])) if on] + \
        (["use the material %s" % rec["constraints"]["material"]] if rec["constraints"]["material"] != "keep" else [])
    return out


# ------------------------------------------------------------------------------------------------ a world's shapes
class Shapes:
    """The shapes of one world, kept in <root>/art/ledger/<brief>.shapes.json."""

    def __init__(self, root, brief):
        self.root, self.brief = root, brief
        self.path = os.path.join(root, "art", "ledger", brief + ".shapes.json")
        self.lock = threading.Lock()
        self.items, self.error, self.revision = {}, "", 0
        if os.path.exists(self.path):
            try:
                raw = open(self.path, "rb").read()
                d = canon.loads(raw[:-1] if raw.endswith(b"\n") else raw)
                if d.get("format") != FORMAT or d.get("version") != VERSION or d.get("brief") != brief or not isinstance(d.get("shapes"), list):
                    raise ValueError("not a %s %s file of %s" % (FORMAT, VERSION, brief))
                for s in d["shapes"]:
                    if not NAME.match(s["name"]) or s["name"] in self.items or s["operation"] not in OPERATIONS:
                        raise ValueError("a shape entry that is not one named shape: %r" % (s.get("name"),))
                    for u, v in s["vertices"]:
                        canon.integer(u, "u")
                        canon.integer(v, "v")
                    self.items[s["name"]] = s
                self.revision = canon.integer(d.get("revision", "0"), "revision")
            except (OSError, ValueError, KeyError, TypeError, canon.IntentError) as e:
                self.error = "the shapes file %s was not read (%s); shapes start empty and the file is kept as it is" % (
                    os.path.relpath(self.path, root), str(e)[:160])
                self.items, self.path = {}, None

    def _save(self):
        if not self.path:
            raise ShapeError("SHAPE-FILE", self.error or "the shapes are not kept")
        self.revision += 1
        doc = {"format": FORMAT, "version": VERSION, "brief": self.brief, "revision": str(self.revision),
               "shapes": [self.items[k] for k in sorted(self.items)]}
        try:
            with durable.locked(led.lock_path(self.path)):
                durable.write(self.path, canon.dumps(doc) + b"\n")
        except durable.Busy:
            self.revision -= 1
            raise ShapeError("SHAPE-BUSY", "the shapes were not saved: another writer held the content lock for the whole wait; try again")

    def save(self, doc, scene, sha):
        rec = parse(doc, scene, sha)
        with self.lock:
            if rec["name"] not in self.items and len(self.items) >= MAX_SHAPES:
                raise ShapeError("SHAPE-LIMIT", "%d shapes at most in a world: delete one first" % MAX_SHAPES)
            old = self.items.get(rec["name"])
            self.items[rec["name"]] = rec
            try:
                self._save()
            except ShapeError:
                if old is None:
                    del self.items[rec["name"]]
                else:
                    self.items[rec["name"]] = old
                raise
        return evaluate(rec, scene)

    def delete(self, name):
        with self.lock:
            if not isinstance(name, str) or name not in self.items:
                raise ShapeError("SHAPE-NAME", "no shape %r" % (name if isinstance(name, str) else type(name).__name__)[:60])
            old = self.items.pop(name)
            try:
                self._save()
            except ShapeError:
                self.items[name] = old
                raise

    def state(self, scene):
        with self.lock:
            items = [self.items[k] for k in sorted(self.items)]
            rev = self.revision
        return {"format": FORMAT, "revision": rev, "kept": bool(self.path), "error": self.error,
                "shapes": [evaluate(s, scene) if scene is not None else {"name": s["name"], "status": "unknown"} for s in items]}

    def resolve(self, names, scene, objects=None):
        """The shapes a request names, each as the director reads it; a name unknown, or a shape not ok, refuses."""
        out = []
        for n in names:
            with self.lock:
                rec = self.items.get(n)
            if rec is None:
                raise ShapeError("STUDIO-SHAPE", "the prompt names #%s, but no shape has that name (a colour is written R,G,B in the art language)" % n)
            ev = evaluate(rec, scene)
            if ev["status"] != "ok":
                raise ShapeError("STUDIO-SHAPE", "#%s is %s: %s. Mark it again on the world as it is now" % (n, ev["status"], ev.get("why", "")))
            failed = [k for k, c in ev["checks"].items() if c["ok"] is False and k in ("simple",)]
            if failed:
                raise ShapeError("STUDIO-SHAPE", "#%s fails the host's check %s" % (n, failed[0]))
            out.append(ev)
        return out


def mentions(prompt):
    out = []
    for m in MENTION.findall(prompt or ""):
        if m not in out:
            out.append(m)
    return out


# ------------------------------------------------------------------------------------------------ the self-test
def selftest():
    """The predicates against worked values and a slow witness; the frames' bijection; the status; the file; and planted
    defects, each of which a row must catch."""
    import json
    import random
    import shutil
    import tempfile
    rows = []

    def row(name, ok, detail):
        rows.append(bool(ok))
        print("[%s] %s — %s" % ("PASS" if ok else "FAIL", name, detail))

    # 1. the frames: u x v is the outward normal; world and local are inverse on the face's rectangle
    b = [Fraction(1), Fraction(2), Fraction(3), Fraction(7), Fraction(11, 2), Fraction(17, 2)]
    bad = []
    for f in FACES:
        F = frame(b, f)
        u, v = F[1], F[2]
        cross = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        if cross != NORMALS[f]:
            bad.append(f + " normal")
        for a, c in ((0, 0), (F[3], F[4]), (Fraction(1, 3), Fraction(2, 7))):
            p = world(F, a, c)
            if local(F, p) != (a, c):
                bad.append(f + " inverse")
            on = [p[k] == (b[k + 3] if NORMALS[f][k] > 0 else b[k]) for k in range(3) if NORMALS[f][k]]
            inb = all(b[k] <= p[k] <= b[k + 3] for k in range(3))
            if not (all(on) and inb):
                bad.append(f + " on the face")
    row("frames", not bad, "six faces: u x v the outward normal, world and local inverse, every corner on its face" + (": " + ", ".join(bad) if bad else ""))

    # 2. simple, by worked values
    sq = [(0, 0), (1000, 0), (1000, 1000), (0, 1000)]
    worked = [("a square", sq, True), ("a bow-tie", [(0, 0), (1000, 1000), (1000, 0), (0, 1000)], False),
              ("a zero-length edge", [(0, 0), (0, 0), (1000, 0), (0, 1000)], False),
              ("three collinear", [(0, 0), (500, 0), (1000, 0)], False),
              ("a spike folding back", [(0, 0), (1000, 0), (500, 0), (500, 800)], False),
              ("a vertex touching an edge", [(0, 0), (2000, 0), (2000, 2000), (1000, 0), (0, 2000)], False),
              ("an L", [(0, 0), (2000, 0), (2000, 1000), (1000, 1000), (1000, 2000), (0, 2000)], True),
              ("a straight angle kept", [(0, 0), (500, 0), (1000, 0), (1000, 1000), (0, 1000)], True)]
    got = [(n, simple(p)[0]) for n, p, _w in worked]
    row("simple: worked values", all(g == w for (_n, g), (_n2, _p, w) in zip(got, worked)), "; ".join("%s %s" % (n, "simple" if g else "not") for n, g in got))

    # 3. simple against a slow witness: every pair of edges sampled for a shared point on a fine lattice of t
    def slow(poly):
        n = len(poly)
        if n < 3 or any(poly[i] == poly[(i + 1) % n] for i in range(n)) or area2(poly) == 0:
            return False
        E = [(poly[i], poly[(i + 1) % n]) for i in range(n)]

        def pt(e, t):
            return (e[0][0] + (e[1][0] - e[0][0]) * t, e[0][1] + (e[1][1] - e[0][1]) * t)
        for i in range(n):
            for j in range(i + 1, n):
                adj = j == i + 1 or (i == 0 and j == n - 1)
                # the exact meeting set of two segments, by solving: parallel ones by overlap of projections
                a, b2 = E[i]
                c, d = E[j]
                den = (b2[0] - a[0]) * (d[1] - c[1]) - (b2[1] - a[1]) * (d[0] - c[0])
                if den != 0:
                    t = Fraction((c[0] - a[0]) * (d[1] - c[1]) - (c[1] - a[1]) * (d[0] - c[0]), den)
                    s = Fraction((c[0] - a[0]) * (b2[1] - a[1]) - (c[1] - a[1]) * (b2[0] - a[0]), den)
                    if 0 <= t <= 1 and 0 <= s <= 1:
                        p = pt(E[i], t)
                        shared = (b2 if j == i + 1 else a) if adj else None
                        if not adj or p != shared:
                            return False
                else:
                    cr = (c[0] - a[0]) * (b2[1] - a[1]) - (c[1] - a[1]) * (b2[0] - a[0])
                    if cr == 0:      # on one line: the overlap of their extents along it
                        k = 0 if b2[0] != a[0] else 1
                        lo1, hi1 = sorted((a[k], b2[k]))
                        lo2, hi2 = sorted((c[k], d[k]))
                        lo, hi = max(lo1, lo2), min(hi1, hi2)
                        if lo < hi or (lo == hi and not adj):
                            return False
        return True
    rnd = random.Random(20261014)
    disagree, n_simple, N = [], 0, 4000
    for _i in range(N):
        n = rnd.randint(3, 7)
        p = [(rnd.randint(0, 4) * 500, rnd.randint(0, 4) * 500) for _k in range(n)]
        a, w = simple(p)[0], slow(p)
        n_simple += a
        if a != w:
            disagree.append(p)
    row("simple: a slow witness", not disagree, "%d random polygons on a coarse lattice (collinear and touching cases common), %d simple, %d disagreements" % (N, n_simple, len(disagree)))

    # 4. clearance: worked values and a brute-force witness on a lattice
    door = [(0, 0), (900, 0), (900, 2100), (0, 2100)]
    tight = [(0, 0), (690, 0), (690, 2100), (0, 2100)]
    arch = [(0, 0), (1200, 0), (1200, 1800), (600, 2400), (0, 1800)]
    worked = [("a door 0.9 x 2.1", door, True), ("0.69 wide", tight, False), ("an arch, 1.8 at its sides and 2.4 at its crown", arch, True),
              ("an L whose arms are 0.6 wide", [(0, 0), (3000, 0), (3000, 600), (600, 600), (600, 3000), (0, 3000)], False)]
    got = [(n, admits_rect(p, 700, 2000)[0]) for n, p, _w in worked]
    row("clearance: worked values", all(g == w for (_n, g), (_n2, _p, w) in zip(got, worked)), "; ".join("%s %s" % (n, "fits" if g else "does not fit") for n, g in got))

    def brute(poly, w, h, step):
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        x = min(xs)
        while x + w <= max(xs):
            y = min(ys)
            while y + h <= max(ys):
                if holds_rect(poly, (x, y), w, h):
                    return True
                y += step
            x += step
        return False
    rnd = random.Random(7)
    wrong, fits, M = [], 0, 300
    for _i in range(M):
        while True:
            n = rnd.randint(3, 6)
            p = [(rnd.randint(0, 8) * 250, rnd.randint(0, 8) * 250) for _k in range(n)]
            if simple(p)[0]:
                break
        w, h = rnd.choice((250, 500, 750)), rnd.choice((250, 500, 1000))
        e = admits_rect(p, w, h)[0]
        fits += e
        # the lattice of 125 mm holds every candidate of these polygons? not always: the brute force can only say yes
        if brute(p, w, h, 125) and not e:
            wrong.append((p, w, h))
    row("clearance: never below a brute force", not wrong, "%d random simple polygons, %d admit their rectangle exactly; the lattice search found none the exact test missed" % (M, fits))

    # 4b. an opening is walked through: the rectangle stands within a step of the face's foot; a window does not
    window = [(1000, 1200), (1900, 1200), (1900, 3400), (1000, 3400)]
    low = [(1000, 500), (1900, 500), (1900, 2700), (1000, 2700)]
    door2 = [(1000, 0), (1900, 0), (1900, 2200), (1000, 2200)]
    got = [admits_rect(x, 700, 2000, 550)[0] for x in (door2, low, window)] + [admits_rect(window, 700, 2000)[0]]
    row("clearance: an opening is walked through", got == [True, True, False, True],
        "a door at the foot walks, one raised 0.5 m (within the step) walks, a window raised 1.2 m does not, though a body fits in it (%s)" % got)

    # 4c. numbers are the decimals written: a Decimal past the millimetre is refused where a double would round it
    try:
        mm(Decimal("1.0000000000000001"), "u")
        dd = "accepted"
    except ShapeError as e:
        dd = e.code
    row("exact numbers", dd == "SHAPE-NUMBER" and mm(Decimal("2.125"), "u") == 2125 and mm(2.125, "u") == 2125 and mm("2.125", "u") == 2125,
        "1.0000000000000001 written as a decimal: %s (a double reads it as 1.0); 2.125 as Decimal, float or string: 2125 mm" % dd)

    # 5. a shape against a scene: parse, status ok / changed / gone, the file, the director's resolve
    scene = {"visuals": [{"id": "tower:1,1", "region": "plaza", "box": [10.0, 0.0, 20.0, 14.0, 8.0, 24.0], "material": "concrete"}],
             "collision": [{"id": "c:0,0-1,1", "kind": "wall", "box": [0.0, 0.0, 0.0, 4.0, 4.0, 2.0], "material": "concrete"}],
             "materials": {"concrete": {}}, "player": {"radius": 0.35}}
    sha = "a" * 64
    doc = {"name": "wall_opening_01", "operation": "subtract",
           "anchor": {"piece": "play:c:0,0-1,1", "face": "+z", "box": [0.0, 0.0, 0.0, 4.0, 4.0, 2.0], "scene": sha, "view": {"x": 2, "y": 1.62, "z": 6, "yaw_deg": 0, "pitch_deg": 0}},
           "vertices": [[1.5, 0], [2.5, 0], [2.5, 2.2], [1.5, 2.2]], "constraints": {"within": True, "clearance_m": 2.0, "supports": True, "collision": True, "material": "keep"}}
    tmp = tempfile.mkdtemp(prefix="marks-selftest-")
    try:
        os.makedirs(os.path.join(tmp, "art", "ledger"))
        os.makedirs(os.path.join(tmp, "art", "build"))
        S = Shapes(tmp, "w")
        ev = S.save(doc, scene, sha)
        raw = open(S.path, "rb").read()
        again = Shapes(tmp, "w")
        row("save and reopen", ev["status"] == "ok" and ev["checks"]["clearance"]["ok"] is True and again.state(scene)["shapes"][0]["vertices_m"] == [[1.5, 0], [2.5, 0], [2.5, 2.2], [1.5, 2.2]]
            and canon.dumps(canon.loads(raw[:-1])) == raw[:-1] and ev["world_m"][2] == [2.5, 2.2, 2.0],
            "saved in canonical bytes, read back the same; ok; a body fits; vertex 2 at %s in the world" % (ev["world_m"][2],))
        moved = json.loads(json.dumps(scene))
        moved["collision"][0]["box"][4] = 4.5
        behind = json.loads(json.dumps(scene))
        behind["collision"][0]["box"][2] = -1.0           # thicker toward -z: the +z face where it was
        gone = json.loads(json.dumps(scene))
        gone["collision"] = []
        mm1 = json.loads(json.dumps(scene))
        mm1["collision"][0]["box"][3] = 4.001            # a millimetre longer
        edge = dict(doc, name="at_the_end", vertices=[[3, 0], [4, 0], [4, 2.2], [3, 2.2]])
        e_ok = S.save(edge, scene, sha)["checks"]["within"]["ok"]
        S.delete("at_the_end")
        twice = json.loads(json.dumps(scene))
        twice["collision"].append(dict(twice["collision"][0]))
        sts = [S.state(s)["shapes"][0] for s in (scene, moved, behind, gone, twice, mm1)]
        st = [x["status"] for x in sts]
        row("status", st == ["ok", "changed", "changed", "gone", "ambiguous", "changed"] and sts[1]["face_same"] is False and sts[2]["face_same"] is True and e_ok,
            "as marked %s; its wall raised 0.5 m %s; thicker behind the face %s (the face where it was); its wall gone %s; its id twice %s; "
            "a millimetre longer %s; a shape against the face's far end is on it" % tuple(st))
        raw = open(S.path, "rb").read()                  # the file as it stands before the refusals
        refused = []
        for what, mut in (("a bow-tie", lambda d: d.update(vertices=[[1.5, 0], [2.5, 2.2], [2.5, 0], [1.5, 2.2]])),
                          ("a vertex off the face", lambda d: d.update(vertices=[[1.5, 0], [4.5, 0], [4.5, 2.2], [1.5, 2.2]])),
                          ("four decimals", lambda d: d.update(vertices=[[1.5001, 0], [2.5, 0], [2.5, 2.2], [1.5, 2.2]])),
                          ("NaN", lambda d: d.update(vertices=[[float("nan"), 0], [2.5, 0], [2.5, 2.2], [1.5, 2.2]])),
                          ("a bool", lambda d: d.update(vertices=[[True, 0], [2.5, 0], [2.5, 2.2], [1.5, 2.2]])),
                          ("65 vertices", lambda d: d.update(vertices=[[i / 100, 0] for i in range(65)])),
                          ("an older scene", lambda d: d["anchor"].update(scene="b" * 64)),
                          ("a box that moved", lambda d: d["anchor"].update(box=[0, 0, 0, 4, 4.5, 2])),
                          ("a mover", lambda d: d["anchor"].update(piece="mover:deck")),
                          ("a name with ../", lambda d: d.update(name="../x")),
                          ("an unknown face", lambda d: d["anchor"].update(face="+w")),
                          ("an unknown field", lambda d: d.update(colour="red")),
                          ("a note of 201", lambda d: d.update(note="x" * 201)),
                          ("a note with half an emoji", lambda d: d.update(note="door \ud83d here")),
                          ("an unknown material", lambda d: d["constraints"].update(material="gold"))):
            d = json.loads(json.dumps(doc, allow_nan=True))
            d["vertices"] = list(doc["vertices"])
            mut(d)
            try:
                S.save(d, scene, sha)
                refused.append((what, "SAVED"))
            except ShapeError as e:
                refused.append((what, e.code))
        row("refusals", all(c != "SAVED" for _w, c in refused) and open(S.path, "rb").read() == raw,
            "; ".join("%s %s" % r for r in refused) + "; the file unchanged")
        try:
            S.resolve(["wall_opening_01"], moved)
            res = "resolved"
        except ShapeError as e:
            res = e.code
        row("the director's input", S.resolve(["wall_opening_01"], scene)[0]["status"] == "ok" and res == "STUDIO-SHAPE" and mentions("cut #wall_opening_01 here, not #x1 or a#b") == ["wall_opening_01", "x1"],
            "an ok shape resolves; a changed one refuses (%s); mentions read #names" % res)
        open(S.path, "ab").write(b"garbage")
        broken = Shapes(tmp, "w")
        try:
            broken.save(doc, scene, sha)
            kept = "saved"
        except ShapeError as e:
            kept = e.code
        row("an unreadable file is never overwritten", broken.error and kept == "SHAPE-FILE" and open(os.path.join(tmp, "art", "ledger", "w.shapes.json"), "rb").read().endswith(b"garbage"),
            "read refused (%s…), the save refused (%s), the file as it was" % (broken.error[:50], kept))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    # 6. over HTTP, through the launcher that serves the shapes and the gateway that sends them (art/play.py)
    if "--pure" not in sys.argv:
        sys.path.insert(0, HERE)
        import play   # noqa: E402
        play.marks_selftest(row)
    print("MARKS SELFTEST %d/%d" % (sum(rows), len(rows)))
    return 0 if all(rows) else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["selftest"] and set(sys.argv[2:]) <= {"--pure"}:
        sys.exit(selftest())
    print("usage: python art/studio_marks.py selftest [--pure]", file=sys.stderr)
    sys.exit(2)
