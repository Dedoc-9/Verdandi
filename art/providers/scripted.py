# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/providers/scripted.py — a provider for the director gateway (art/studio.py) that is not a model: a fixed set of
# variations of a selected canopy, so that the studio can be tried, and tested, without a model or a key.
#
#   art/providers/scripted.json      {"provider": "cli", "argv": ["{python}", "art/providers/scripted.py"], ...}
#
# It reads a VERDANDI-STUDIO-REQUEST 1 or 2 on standard input and writes a VERDANDI-STUDIO-RESPONSE 0 on standard output
# (art/STUDIO.md). For a canopy as the target it proposes three candidates, the three of the owner's sketch of the studio:
# "Monolithic" (lower by 1.0 m, to no less than 6.0 m, and 2.2 m deep; 0229: REACH-1 puts the ceiling over the
# fixture's slabs at 5.875 m, a head on the 2.6 m covers under them, so 4.6 m, or 5.8 m, would be refused for it), "Lit
# underside" (a narrow row of fixtures along its edge, magenta if the prompt says so, warm otherwise, at a restrained
# 60 cd) and "Deeper canopy" (2.6 m deep). For
# anything else it proposes nothing. It reads the prompt only for the word "magenta", and for "match @N" (STUDIO-1):
# when the target is a canopy and @N a pinned canopy, its one candidate gives the target @N's material, height and
# options and keeps the target's corners, leaving @N as it is. It understands nothing.
#
# MARK-0 (0231): a request of version 2 names shapes. When the first is drawn on the play geometry and is an opening or an
# addition, it answers UNSUPPORTED layout.change (the art cannot change the map); when it is drawn on a canopy and no target
# is selected, that canopy is its target, as if E had selected it. It reads the shape's surface, not its outline.
#
# FACADE-0 (0237): when the first shape is drawn on a side of a building (its mass, or one bay's window or panel), the bay
# under the shape's middle is its target, and it proposes three candidates: "Panelled bay" (that bay of that floor a
# panel in the building's own material), "Blank bay" (left blank) and "Panelled column" (the same bay panelled on every
# floor, which reaches beyond a shape drawn on one floor). It reads the building's statement and the shape's place.
#
# 0220: when it proposes nothing it gives an outcome only where a word of the prompt is in its small list of things the
# studio cannot make yet (a person, a vehicle, a door, an escalator, ...): UNSUPPORTED, with those names. That is word
# matching, not understanding; anything else it answers with nothing and no reason, which the gateway records as FAILED.

import json
import re
import sys
from fractions import Fraction


def options(tokens):
    out, i = {}, 0
    while i < len(tokens):
        k = tokens[i]
        n = {"deep": 1, "ribs": 1, "lit": 2, "edgelit": 2}.get(k)
        if n is None:
            return None
        out[k] = tokens[i + 1:i + 1 + n]
        i += 1 + n
    return out


def statement(head, opts):
    words = list(head)
    for k in ("deep", "ribs", "lit", "edgelit"):
        if k in opts:
            words += [k] + list(opts[k])
    return " ".join(words)


def canopy(text):
    """(head words: verb, region, material, height, corner, corner; options), or None."""
    words = text.split()
    if len(words) >= 6 and words[0] == "canopy" and "," in words[4] and "," in words[5]:
        opts = options(words[6:])
        if opts is not None:
            return words[:6], opts
    return None


# words of a prompt, and what the studio would need to make what they name (0220; not understanding: a list)
LEXICON = (
    (("person", "people", "man", "woman", "figure", "fisherman", "child", "crowd", "npc", "character"), "entity.person"),
    (("dog", "cat", "bird", "gull", "seagull", "animal", "horse"), "entity.animal"),
    (("car", "boat", "ship", "bus", "bike", "bicycle", "vehicle", "truck"), "entity.vehicle"),
    (("train", "tram", "elevator", "lift", "platform", "moving"), "motion.path"),
    (("escalator", "conveyor", "travelator"), "motion.surface"),
    (("door", "gate", "hatch"), "mechanism.door"),
    (("crate", "barrel", "box", "bench", "table", "chair", "prop"), "entity.prop"),
    (("tree", "trees", "plant", "plants", "grass", "flowers"), "entity.vegetation"),
    (("sound", "music", "noise", "audio"), "audio"),
)


def unmet(prompt):
    words = set(re.findall(r"[a-z]+", prompt.lower()))
    return sorted({name for keys, name in LEXICON if words & set(keys)})


BAY_PIECE = re.compile(r"building:([0-9]+,[0-9]+-[0-9]+,[0-9]+):([nsew])-b([0-9]+)-f([0-9]+)$")
SIDE = {(0, 0, 1): "s", (0, 0, -1): "n", (1, 0, 0): "e", (-1, 0, 0): "w"}


def building(text):
    """A building statement's words: {region, material, height, rect, storey, bay}, or None."""
    words = text.split()
    if len(words) < 6 or words[0] != "building":
        return None
    try:
        a, b = [int(v) for v in words[4].split(",")], [int(v) for v in words[5].split(",")]
        opts, i = {}, 6
        while i < len(words):
            n = {"face": 2, "storey": 1, "bay": 1}[words[i]]
            opts[words[i]] = words[i + 1:i + 1 + n]
            i += 1 + n
        return {"region": words[1], "material": words[2], "height": Fraction(words[3]), "rect": (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])),
                "storey": Fraction(opts.get("storey", ["4"])[0]), "bay": int(opts.get("bay", ["1"])[0])}
    except (ValueError, KeyError, IndexError):
        return None


def facade(shape, req):
    """The candidates for a shape on a building's side, or None."""
    on = shape["on"]
    B = building((on.get("statement") or {}).get("text", ""))
    if B is None:
        return None
    x0, z0, x1, z1 = B["rect"]
    corners = "%d,%d-%d,%d" % B["rect"]
    m = BAY_PIECE.match(on.get("piece", ""))
    if m:
        side, k, f = m.group(2), int(m.group(3)), int(m.group(4))
    else:
        side = SIDE.get(tuple(int(v) for v in shape["face"]["normal"]))
        if side is None or on.get("piece") != "building:" + corners:
            return None
        cells = (x1 - x0 + 1) if side in "ns" else (z1 - z0 + 1)
        cell = Fraction(str(shape["face"]["width_m"])) / cells
        pts = shape["world_m"]
        cx, cy, cz = (sum(Fraction(str(p[i])) for p in pts) / len(pts) for i in range(3))
        along = (cx - x0 * cell) if side in "ns" else (cz - z0 * cell)
        k, f = int(along // (B["bay"] * cell)), int(cy // B["storey"])
    floors = int(B["height"] // B["storey"])
    keys = {s_["key"] for s_ in req.get("statements", [])}
    place = lambda f_: "%s:%s-b%d-f%d" % (corners, side, k, f_)
    line = lambda f_, rest: "%s bay %s %s" % ("=" if "bay " + place(f_) in keys else "+", place(f_), rest)
    addr = lambda f_: "%s/building/%s" % (B["region"], place(f_))
    keep = ["the player's route and every wall", "every other bay of the building"]
    return [
        {"title": "Panelled bay", "rationale": "Bay %d of floor %d closed with a panel in the building's own %s: the facade reads more solid there." % (k, f, B["material"]),
         "revision": [line(f, "panel " + B["material"])], "scope": [addr(f)], "preserve": keep},
        {"title": "Blank bay", "rationale": "Bay %d of floor %d left blank, the mass's face showing: a pause in the grid." % (k, f),
         "revision": [line(f, "blank")], "scope": [addr(f)], "preserve": keep},
        {"title": "Panelled column", "rationale": "Bay %d panelled on every floor, %d of them: a solid stripe up the facade." % (k, floors),
         "revision": [line(g, "panel " + B["material"]) for g in range(floors)], "scope": [addr(g) for g in range(floors)], "preserve": keep[:1]},
    ]


def main():
    req = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    out = {"format": "VERDANDI-STUDIO-RESPONSE", "version": "0", "id": req["id"],
           "provider": {"name": "scripted", "model": "scripted-1 (fixed variations, not a model)"}, "candidates": []}
    sel = req.get("target") or {}
    shapes = req.get("shapes") or []
    if shapes:
        on = shapes[0]["on"]
        if on.get("layer") == "play" and shapes[0]["operation"] in ("subtract", "add"):
            out["outcome"] = {"kind": "unsupported", "unmet": ["layout.change"], "questions": [], "reason": "",
                              "note": "#%s is %s in the play geometry (%s): that is a layout change, which the studio cannot make yet; "
                                      "this script read the shape's surface, not the prompt." % (shapes[0]["name"], shapes[0]["meaning"], on["address"])}
            sys.stdout.buffer.write(json.dumps(out, sort_keys=True).encode("utf-8"))
            return 0
        if not sel and on.get("kind") == "building" and on.get("layer") == "dressing":
            out["candidates"] = facade(shapes[0], req) or []
            if out["candidates"]:
                out["outcome"] = {"kind": "none", "unmet": [], "questions": [], "reason": "", "note": ""}
            sys.stdout.buffer.write(json.dumps(out, sort_keys=True).encode("utf-8"))
            return 0
        if not sel and on.get("kind") == "canopy" and on.get("statement"):
            sel = {"tag": "#" + shapes[0]["name"], "statement": on["statement"], "patterns": on["patterns"]}
    st = (sel.get("statement") or {}).get("text", "")
    words = st.split()
    m = re.search(r"\bmatch\s+(@[0-9]+)", req.get("prompt", ""))
    pins = {r["tag"]: r for r in req.get("references", []) if r.get("role") == "pin"}
    if m and canopy(st) and m.group(1) in pins and canopy((pins[m.group(1)].get("statement") or {}).get("text", "")):
        (head, _o), (phead, popts) = canopy(st), canopy(pins[m.group(1)]["statement"]["text"])
        tag, ptag = sel["tag"], m.group(1)
        out["candidates"] = [
            {"title": "Matched to %s" % ptag,
             "rationale": "%s takes %s's material, height and options (%s); its own corners stay, and %s is unchanged." % (
                 tag, ptag, " ".join(phead[2:4] + [w for k in ("deep", "ribs", "lit", "edgelit") if k in popts for w in [k] + popts[k]]), ptag),
             "revision": ["= " + statement(head[:2] + phead[2:4] + head[4:6], popts)], "scope": [sel["patterns"][0]],
             "preserve": ["%s as it is" % ptag, "the player's route and every wall"]}]
        sys.stdout.buffer.write(json.dumps(out, sort_keys=True).encode("utf-8"))
        return 0
    if len(words) >= 6 and words[0] == "canopy" and "," in words[4] and "," in words[5]:
        head, opts = words[:6], options(words[6:])
        if opts is not None:
            height = float(head[3])
            scope = [sel["patterns"][0]]
            keep = ["the player's route and every wall", "the other slabs, the lamps and the neon"]
            low = dict(opts, deep=["2.2"])
            low_head = head[:3] + ["%.1f" % max(6.0, height - 1.0)] + head[4:]
            colour = "255,40,190" if "magenta" in req.get("prompt", "").lower() else "255,178,112"
            lit = dict(opts, edgelit=[colour, "60"])
            deep = dict(opts, deep=["2.6"])
            out["candidates"] = [
                {"title": "Monolithic", "rationale": "The slab brought down to %.1f m and made 2.2 m deep, so that it fills more of the frame and reads as one heavy mass." % max(6.0, height - 1.0),
                 "revision": ["= " + statement(low_head, low)], "scope": scope, "preserve": keep},
                {"title": "Lit underside", "rationale": "The slab where it is, with a narrow row of small fixtures along its edge at a restrained 60 cd, so that its underside reads against the dark.",
                 "revision": ["= " + statement(head, lit)], "scope": scope, "preserve": keep},
                {"title": "Deeper canopy", "rationale": "The slab where it is, made 2.6 m deep: the same plan, a heavier section.",
                 "revision": ["= " + statement(head, deep)], "scope": scope, "preserve": keep},
            ]
    if out["candidates"]:
        out["outcome"] = {"kind": "none", "unmet": [], "questions": [], "reason": "", "note": ""}
    elif unmet(req.get("prompt", "")):
        names = unmet(req.get("prompt", ""))
        out["outcome"] = {"kind": "unsupported", "unmet": names, "questions": [], "reason": "",
                          "note": "The prompt names what the studio cannot make yet (%s); this script matched words, it did not read the prompt." % ", ".join(names)}
    sys.stdout.buffer.write(json.dumps(out, sort_keys=True).encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
