# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/locality.py — LOCALITY-1 (admitted under the working name LOCALITY-0, which is the registered floor-tile court's;
# SHEET-v3.md): how far a one-step edit of one statement of an art brief reaches, and whether the
# exporter's ids keep naming the same things across it. A measurement, admitted as one: its definitions, predictions,
# plants and exit form were frozen before it ran (art/fixtures/locality/SPEC.md, held here by its sha256), and so were
# its fixtures and its inventory of 2,418 perturbations, whose rule and checks are art/locality_inventory.py's,
# committed before this file. It changes nothing it measures: the exporter (art/dress.py),
# the diff (art/scene_diff.py) and the graybox converter are imported and read, never written.
#
#   python art/locality.py inventory   the inventory made again from the fixtures, held to INVENTORY.jsonl (H1, H2)
#   python art/locality.py run         every entry exported and diffed: art/build/locality/REPORT.json and REPORT.txt
#   python art/locality.py selftest    the harness's plants (SPEC.md §14): LOCALITY SELFTEST 4/4
#
# What it does not show: anything about the renderer, play, physics, generated worlds or perceptual diversity; any
# dependence a one-step edit does not cross (observed influence under-approximates true dependence); the necessity or
# sufficiency of any replacement identity architecture. Standard library only; it starts no process, writes no
# temporary file (every brief is parsed from bytes) and writes nothing but the report.

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import dress              # noqa: E402  (the exporter, read: parse, export, statement_key, footprint, swept)
import scene_diff as SD   # noqa: E402  (the diff, read: records keyed by identity, objects by studio_refs' rule)
from locality_inventory import (FIX, SPEC_SHA256, INVENTORY_SHA256, FIXTURES_SHA256, BRIEFS, CLASSES, MATPOS,  # noqa: E402
                                Refusal, sha256, statements, fixture, check_fixtures, check_inventory, check_frozen,
                                brief_bytes)

REPO = os.path.dirname(HERE)
OUT = os.path.join(HERE, "build", "locality")
FORMAT = "VERDANDI-LOCALITY-1 0"
READ = ("art/locality.py", "art/locality_inventory.py", "art/dress.py", "art/scene_diff.py", "art/studio_refs.py",
        "art/studio_marks.py", "art/director/durable.py", "art/director/intent.py", "art/director/ledger.py",
        "graybox/level.py", "graybox/tick_ref.py", "graybox/rules_ref.py")   # the code a run executes, as measured


# ------------------------------------------------------------------------------------------------ export
PLANT = ""   # "global", "renumber" or "noop-name": set by the self-test's rows alone, put back after (SPEC.md §14)


def scene_bytes(scene):
    """The exporter's byte form of a scene (art/dress.py's export), for a scene a plant has changed."""
    return (json.dumps(scene, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def plant_scene(A, scene):
    if PLANT == "global":
        # a dependence on the whole brief: every light's candela, by a number of all the statements' texts
        off = 1 + int(sha256("\n".join(s["text"] for s in A["statements"]).encode("utf-8"))[:4], 16)
        for L in scene["lights"]:
            L["candela"] = dress.r4(L["candela"] + off)
    elif PLANT == "renumber":
        # ids that are not names: a piece's id is its place in the sorted list
        new = {v["id"]: "v%05d" % i for i, v in enumerate(sorted(scene["visuals"], key=lambda v: v["id"]))}
        rest = sorted(L["id"] for L in scene["lights"] if L["id"] not in new)
        lid = {k: "l%05d" % j for j, k in enumerate(rest)}
        for v in scene["visuals"]:
            v["id"] = new[v["id"]]
        for L in scene["lights"]:
            L["id"] = new.get(L["id"]) or lid[L["id"]]
        scene["visuals"].sort(key=lambda v: v["id"])
        scene["lights"].sort(key=lambda v: v["id"])


def export(name, raw, n=None):
    """(A, scene, scene bytes) of a brief's exact bytes. dress.ArtError is a refusal; anything else raised inside
    dress.parse or dress.export is the exporter's crash, and is wrapped as Crash; anything raised here is the harness's."""
    text = raw.decode("utf-8")
    try:
        A = dress.parse(text, name + ".art")
    except dress.ArtError:
        raise
    except Exception as e:  # noqa: BLE001  (a crash of the exporter is a finding, recorded, never a harness failure)
        raise Crash("%s: %s" % (type(e).__name__, e))
    A["name"], A["sha256"] = name, sha256(raw)
    if PLANT == "noop-name" and n is not None:
        A["name"] = "%s~%d" % (name, n)
    maps = os.path.join(FIX, "maps")
    try:
        out = dress.export(A, maps)
    except dress.ArtError:
        raise
    except Exception as e:  # noqa: BLE001
        raise Crash("%s: %s" % (type(e).__name__, e))
    scene = out["scene"]
    if not PLANT:
        return A, scene, out["scene_bytes"]
    plant_scene(A, scene)
    return A, scene, scene_bytes(scene)


class Crash(Exception):
    pass


# ------------------------------------------------------------------------------------------------ the classification
DRESSING = ("skyline", "tower", "canopy", "neon", "lamp", "puddle", "building", "bay")
REGIONAL = ("tower", "canopy", "neon", "lamp", "puddle", "building")
KEYED = ("visuals", "lights", "movers")
ENV = {"time": "time", "fog": "fog", "exposure": "exposure", "bloom": "bloom", "rain": "rain", "sun": "light", "moon": "light"}
RECORD_CLASSES = ("OWN", "IN-SCOPE", "DECLARED-GLOBAL", "UNEXPLAINED")
CHANNELS = ("G-REACH", "G-SEED", "G-NAME")
MODIFY_ROLES = ("POSITION", "SIZE", "APPEARANCE", "VIEW", "MOTION")
ALL = "ALL"   # skyline's scope: every cell
LIMITS = ("Observed influence under-approximates true dependence. Each entry is one step of one statement in one of "
          "four briefs over one map (tactical), with the exporter whose sha256 the report names: a dependence shows only "
          "where that step crosses it (a max(), a threshold, rounding to 0.1 mm, a modulus or a refusal can hide one), "
          "and only in these briefs. Two edits at once, other maps, other exporters and other values are not measured.")
NOT_ESTABLISHED = ("the necessity or sufficiency of any replacement identity architecture (statement key and role path, "
                   "a sidecar, a new scene version or another); anything about the renderer, play, physics, generated "
                   "worlds or perceptual diversity.")


def words(text):
    w = text.split(" ")
    return w[0], w[1:]


def corners(a, b):
    (ax, az), (bx, bz) = (tuple(int(v) for v in t.split(",")) for t in (a, b))
    return min(ax, bx), min(az, bz), max(ax, bx), max(az, bz)


def place(a, b):
    return "%d,%d-%d,%d" % corners(a, b)


def rect(r, g):
    x0, z0, x1, z1 = r
    return {(x, z) for z in range(max(0, z0), min(g["h"], z1 + 1)) for x in range(max(0, x0), min(g["w"], x1 + 1))}


def cell_of(x, z, g):
    """The cell that holds a point (SPEC.md §5: ⌊x / cell⌋, ⌊z / cell⌋), inside the grid or not."""
    return {(int(x // g["cell"]), int(z // g["cell"]))}


def footprint(sec, key, rec, g):
    """The cells a record stands on, in plan (SPEC.md §5): none for a record that has no place."""
    if rec is None:
        return set()
    if sec in ("reach", "tops"):
        i = int(key)
        return {(i % g["w"], i // g["w"])}
    if sec in ("visuals", "collision"):
        return set(dress.footprint(rec["box"], g["w"], g["h"], g["cell"]))
    if sec == "lights":
        return cell_of(rec["pos"][0], rec["pos"][2], g)
    if sec == "movers":
        return set(dress.footprint(dress.swept(rec), g["w"], g["h"], g["cell"]))
    if sec in ("spawns", "targets", "views"):
        return cell_of(rec["x"], rec["z"], g)
    return set()


def mover_cells(name, scene, g):
    return {c for m in scene.get("movers", []) if m["id"] == name for c in dress.footprint(dress.swept(m), g["w"], g["h"], g["cell"])}


def scope(st, scene, g):
    """The cells a statement declares, in one scene (SPEC.md §5): ALL for a skyline, an empty set for none."""
    if st is None:
        return set()
    verb, args = st
    if verb == "skyline":
        return ALL
    out = set()
    regions = scene.get("regions", {})
    if verb in REGIONAL and args and args[0] in regions:
        out |= rect(regions[args[0]], g)
        if verb in ("canopy", "building") and len(args) >= 5 and dress.is_cell(args[3]) and dress.is_cell(args[4]):
            out |= rect(corners(args[3], args[4]), g)
    elif verb == "mover" and args:
        out |= mover_cells(args[0], scene, g)
    elif verb == "region" and args and args[0] in regions:
        out |= rect(regions[args[0]], g)
    elif verb == "view" and len(args) > 1 and dress.is_cell(args[1]):
        x, z = (int(v) for v in args[1].split(","))
        out |= rect((x, z, x, z), g)
    elif verb == "bay" and args and dress.BAY.fullmatch(args[0]):
        m = dress.BAY.fullmatch(args[0])
        out |= rect(tuple(int(m.group(i)) for i in (1, 2, 3, 4)), g)
    return out


def meets(cells, sc):
    return bool(cells) and (sc == ALL or bool(cells & sc))


def declares(st):
    """The entries the statement itself declares (OWN's second rule), and the collision kind a surface declares."""
    verb, args = st
    if verb in ("material", "region", "view", "asset") and args:
        return {({"material": "materials", "region": "regions", "view": "views", "asset": "assets"}[verb], args[0])}, None
    if verb in ENV:
        return {("environment", ENV[verb])}, None
    if verb == "title":
        return {("top", "title")}, None
    if verb == "surface" and args:
        return set(), args[0]
    return set(), None


def matpos(verb, args):
    pos = list(MATPOS.get(verb, ()))
    if verb == "building" and "face" in args:
        pos.append(args.index("face") + 2)
    return [i for i in pos if i < len(args)]


def named(st):
    """What a statement declares by name (G-NAME): a material, a region, a building's corners."""
    verb, args = st
    if verb in ("material", "region") and args:
        return {(verb, args[0])}
    if verb == "building" and len(args) >= 5 and dress.is_cell(args[3]) and dress.is_cell(args[4]):
        return {("building", place(args[3], args[4]))}
    return set()


def uses(st):
    """What a statement uses by name: the materials in its materials' positions, its region, a bay's building."""
    verb, args = st
    out = {("material", args[i]) for i in matpos(verb, args)}
    if verb in REGIONAL and args:
        out.add(("region", args[0]))
    if verb == "bay" and args:
        out.add(("building", args[0].split(":", 1)[0]))
    return out


def comb_or_picked(st):
    verb, args = st
    return verb in ("skyline", "neon", "puddle") or (verb == "tower" and len(args) == 4)


def kind(sec, key):
    return "mover" if sec == "movers" else key.split(":", 1)[0]


def records(d, A, B):
    """Every changed record of the diff: (section, key, before, after, changed fields), in a fixed order."""
    out = []
    for sec in SD.SECTIONS:
        ra, rb, s = SD._records(A, sec), SD._records(B, sec), d[sec]
        for k in sorted(s["added"]):
            out.append((sec, k, None, rb[k], ["*"]))
        for k in sorted(s["removed"]):
            out.append((sec, k, ra[k], None, ["*"]))
        for k in sorted(s["changed"]):
            c = s["changed"][k]
            out.append((sec, k, ra[k], rb[k], sorted(c["fields"]) if "fields" in c else ["="]))
    for f in sorted(d["top"]):
        if not f.startswith("has:"):   # scene_diff's mark that a section exists, not a field of the scene (SPEC.md §3)
            out.append(("top", f, A.get(f), B.get(f), ["="]))
    return out


def diff_count(d):
    """The changed records as the diff states them, counted apart from records() (H5)."""
    return sum(len(d[sec][w]) for sec in SD.SECTIONS for w in ("added", "removed", "changed")) + \
        sum(1 for f in d["top"] if not f.startswith("has:"))


class Entry:
    """One accepted entry's context: the statement before and after, its hashes, its scope, the two scenes."""

    def __init__(self, e, A, B, stA, stB):
        self.e, self.A, self.B, self.g = e, A, B, A["grid"]
        self.s0 = words(e["before"]) if e["before"] else None
        self.s1 = words(e["after"]) if e["after"] else None
        self.h0 = e["hash"] or None
        self.h1 = dress.sha256(e["after"].encode("utf-8"))[:12] if e["after"] else None
        self.stA, self.stB = stA, stB
        self.verb = self.s0[0] if self.s0 else ""
        sa, sb = scope(self.s0, A, self.g), scope(self.s1, B, self.g)
        self.scope = ALL if ALL in (sa, sb) else (sa | sb)

    def producers(self, a, b):
        out = []
        if a is not None and a.get("by") in self.stA:
            out.append(self.stA[a["by"]])
        if b is not None and b.get("by") in self.stB:
            out.append(self.stB[b["by"]])
        return out

    def classify(self, sec, key, a, b, fields):
        """(record class, channel or None): the first of SPEC.md §5's rules that holds."""
        own = {h for h in (self.h0, self.h1) if h}
        if sec in KEYED and {r["by"] for r in (a, b) if r is not None} & own:
            return "OWN", None
        if fields == ["by"]:
            # §5 as written: a record whose only changed field is `by` is OWN (and flagged BY-ONLY), whoever made it; a
            # kept id that now names another statement's piece is also counted, apart, as REASSIGNED (§7)
            return "OWN", None
        for st in (self.s0, self.s1):
            if st is None:
                continue
            decl, surface = declares(st)
            if (sec, key) in decl:
                return "OWN", None
            if surface and sec == "collision" and any(r["kind"] == surface for r in (a, b) if r is not None):
                return "OWN", None
        cells = footprint(sec, key, a, self.g) | footprint(sec, key, b, self.g)
        if meets(cells, self.scope):
            return "IN-SCOPE", None
        if self.verb == "mover":
            if sec == "reach":
                return "DECLARED-GLOBAL", "G-REACH"
            if sec in ("visuals", "lights") and key.startswith("lamp:"):
                x, z = (int(v) for v in key.split(":", 1)[1].split(","))
                i = z * self.g["w"] + x
                if self.A["reach"][i] != self.B["reach"][i]:
                    return "DECLARED-GLOBAL", "G-REACH"
        if self.verb == "seed" and sec in ("visuals", "lights"):
            if any(comb_or_picked(p) for p in self.producers(a, b)):
                return "DECLARED-GLOBAL", "G-SEED"
        nm = (named(self.s0) if self.s0 else set()) | (named(self.s1) if self.s1 else set())
        if nm and sec in KEYED and any(uses(p) & nm for p in self.producers(a, b)):
            return "DECLARED-GLOBAL", "G-NAME"
        return "UNEXPLAINED", None


def churn(x, A, B, OA, OB):
    """SPEC.md §7: re-addressing (REPLACED, by statement and kind) and reuse (REASSIGNED), of records and of objects."""
    h0, h1 = x.h0, x.h1

    def who(by, side):
        if (side == "A" and by == h0 and h0) or (side == "B" and by == h1 and h1):
            return "s"
        return by

    def count(ra, rb, kindof, label):
        gone, new, reassigned = {}, {}, 0
        for k, r in ra.items():
            if k not in rb:
                key = (who(r["by"], "A"), kindof(k))
                gone[key] = gone.get(key, 0) + 1
        for k, r in rb.items():
            if k not in ra:
                key = (who(r["by"], "B"), kindof(k))
                new[key] = new.get(key, 0) + 1
        for k in sorted(set(ra) & set(rb)):
            p, q = ra[k]["by"], rb[k]["by"]
            if p != q and not (p == h0 and q == h1):
                reassigned += 1
        def part(m, mine):
            return sum(v for key, v in m.items() if (key[0] == "s") == mine)
        own = sum(min(v, new.get(key, 0)) for key, v in gone.items() if key[0] == "s")
        other = sum(min(v, new.get(key, 0)) for key, v in gone.items() if key[0] != "s")
        # which statement and kind: the edited statement as "s", any other by its key; never which piece became which
        detail = sorted([label(key[0]), key[1], v, new[key]] for key, v in gone.items() if min(v, new.get(key, 0)))
        return {"gone_own": part(gone, True), "gone_other": part(gone, False), "new_own": part(new, True),
                "new_other": part(new, False), "replaced_own": own, "replaced_other": other,
                "reassigned": reassigned, "replaced_detail": detail}

    def label(p):
        if p == "s" or p not in x.stA:
            return p
        verb, args = x.stA[p]
        return " ".join([verb] + args[:1])

    ra, rb = {}, {}
    for sec in KEYED:
        ra.update({(sec, k): r for k, r in SD._records(A, sec).items()})
        rb.update({(sec, k): r for k, r in SD._records(B, sec).items()})
    rec = count(ra, rb, lambda sk: kind(*sk), label)
    root = count(OA, OB, lambda k: k.split(":", 1)[0], label)
    out = dict(rec)
    out.update({"root_" + k: v for k, v in root.items()})
    return out


# ------------------------------------------------------------------------------------------------ the run
def measure(entries, texts, keep=None):
    """Every entry exported and diffed (SPEC.md §3-§12). `keep`, when given, limits the entries to those briefs."""
    base, results = {}, []
    for b in BRIEFS:
        if keep and b not in keep:
            continue
        raw = texts[b].encode("utf-8")
        A_, scene, sb = export(b, raw)
        st = {s["hash"]: words(s["text"]) for s in A_["statements"]}
        base[b] = {"scene": scene, "bytes": sb, "st": st, "objects": SD.object_records(scene), "sha": SD.canon_sha(scene)}
    for e in entries:
        if keep and e["brief"] not in keep:
            continue
        r = {"n": e["n"], "brief": e["brief"], "class": e["class"], "line": e["line"], "verb": e["verb"], "role": e["role"]}
        raw = brief_bytes(e, texts[e["brief"]])
        try:
            A_, B, bbytes = export(e["brief"], raw, e["n"])
        except dress.ArtError as err:
            r.update({"outcome": "REFUSED", "message": str(err)})
            results.append(r)
            continue
        except Crash as err:
            r.update({"outcome": "CRASHED", "message": str(err)})
            results.append(r)
            continue
        bs = base[e["brief"]]
        A = bs["scene"]
        stB = {s["hash"]: words(s["text"]) for s in A_["statements"]}
        x = Entry(e, A, B, bs["st"], stB)
        d = SD.diff(A, B)
        try:
            SD.apply(d, A)
            complete = True
        except SD.DiffError:
            complete = False
        recs = records(d, A, B)
        classes = {c: 0 for c in RECORD_CLASSES}
        channels = {c: 0 for c in CHANNELS}
        beyond = {c: 0 for c in RECORD_CLASSES}
        sections, kinds, declared, unexplained, by_only = {}, {}, [], [], 0
        for sec, key, a, b, fields in recs:
            c, ch = x.classify(sec, key, a, b, fields)
            classes[c] += 1
            if ch:
                channels[ch] += 1
                declared.append([sec, key, ch])
            if c == "UNEXPLAINED":
                unexplained.append([sec, key, fields])
            if c == "OWN" and fields == ["by"]:
                by_only += 1
            cells = footprint(sec, key, a, x.g) | footprint(sec, key, b, x.g)
            if cells and not meets(cells, x.scope):
                beyond[c] += 1
            how = "added" if a is None else "removed" if b is None else "changed"
            sections.setdefault(sec, {"added": 0, "removed": 0, "changed": 0})[how] += 1
            if sec in KEYED + ("collision",):
                kinds.setdefault("%s/%s" % (sec, kind(sec, key)), {"added": 0, "removed": 0, "changed": 0})[how] += 1
        OB = SD.object_records(B)
        ch_ = churn(x, A, B, bs["objects"], OB)
        key_changed = None
        if x.s0 and x.s1:
            key_changed = dress.statement_key([x.s0[0]] + x.s0[1]) != dress.statement_key([x.s1[0]] + x.s1[1])
        grant = None
        G = {i for i, o in bs["objects"].items() if x.h0 and o["by"] == x.h0}
        if G and x.h1:
            grant = {i for i, o in OB.items() if o["by"] == x.h1} <= G
        r.update({"outcome": "ACCEPTED", "changed": len(recs), "classes": classes, "channels": channels, "beyond": beyond,
                  "by_only": by_only, "sections": sections, "kinds": dict(sorted(kinds.items())), "churn": ch_, "key_changed": key_changed, "grant": grant,
                  "diff_complete": complete, "diff_count": diff_count(d), "declared": declared, "unexplained": unexplained,
                  "scene_sha": SD.canon_sha(B)})
        if e["class"] == "NOOP":
            r["noop"] = {"bytes_differ": raw != texts[e["brief"]].encode("utf-8"), "scene_bytes_equal": bbytes == bs["bytes"],
                         "changed_records": [[sec, key, fields] for sec, key, _a, _b, fields in recs]}
        if e["verb"] == "mover":
            union = mover_cells(x.s0[1][0], A, x.g) | (mover_cells(x.s1[1][0], B, x.g) if x.s1 else set())
            r["p2"] = sorted(key for sec, key, a, b, _f in recs if sec == "lights" and
                             (footprint(sec, key, a, x.g) | footprint(sec, key, b, x.g)) and
                             not ((footprint(sec, key, a, x.g) | footprint(sec, key, b, x.g)) & union))
        if e["class"].startswith("SHIFT") and x.verb in ("canopy", "building") and len(x.s0[1]) >= 5 \
                and dress.is_cell(x.s0[1][3]) and dress.is_cell(x.s0[1][4]):
            rid = "%s:%s" % (x.verb, place(x.s0[1][3], x.s0[1][4]))
            made = rid in bs["objects"] and bs["objects"][rid]["by"] == x.h0
            gone = rid not in OB
            new = sorted(i for i, o in OB.items() if o["by"] == x.h1 and i.split(":", 1)[0] == x.verb and i not in bs["objects"])
            r["p1"] = {"root": rid, "made_by_s": made, "gone": gone, "new": new}
        if e["class"] == "SEED":
            r["p3"] = seed_diff(d, A, B)
            r["r2_outside"] = [[sec, key] for sec, key, a, b, _f in recs
                               if not (sec in ("visuals", "lights") and any(comb_or_picked(p) for p in x.producers(a, b)))]
        results.append(r)
    return base, results


def masked(rec):
    m = json.loads(SD.enc(rec))
    if isinstance(m.get("box"), list) and len(m["box"]) == 6:
        m["box"][1] = m["box"][4] = None
    if isinstance(m.get("pos"), list) and len(m["pos"]) == 3:
        m["pos"][1] = None
    return m


def seed_diff(d, A, B):
    """P3's three conditions for one seed's scene against the baseline (SPEC.md §9)."""
    ids, heights, beyond = {}, [], []
    for sec in ("visuals", "lights", "collision", "movers"):
        s = d[sec]
        for k in list(s["added"]) + list(s["removed"]):
            ids.setdefault(kind(sec, k), 0)
            ids[kind(sec, k)] += 1
        ra, rb = SD._records(A, sec), SD._records(B, sec)
        for k in sorted(s["changed"]):
            if not SD.same(masked(ra[k]), masked(rb[k])):
                beyond.append("%s/%s" % (sec, k))
            else:
                heights.append("%s/%s" % (sec, k))
    others = [sec for sec in SD.SECTIONS if sec not in ("visuals", "lights", "collision", "movers")
              and any(d[sec][w] for w in ("added", "removed", "changed"))] + (["top"] if d["top"] else [])
    return {"ids_differ": dict(sorted(ids.items())), "heights_only": len(heights), "beyond_heights": beyond, "other_sections": others}


# ------------------------------------------------------------------------------------------------ the verdicts
def tally(results, key):
    out = {}
    for r in results:
        k = r[key] or "-"
        t = out.setdefault(k, {"entries": 0, "accepted": 0, "refused": 0, "crashed": 0, "changed": 0, "beyond": 0,
                               "no_effect": 0, "root_readdressed_entries": 0, "root_readdressed_own_entries": 0,
                               "root_readdressed_other_entries": 0, "reassigned": 0, "key_changed": 0,
                               "grant_survived": 0, "grant_of": 0, "by_only": 0, **{c: 0 for c in RECORD_CLASSES},
                               **{"beyond_" + c: 0 for c in RECORD_CLASSES}, **{c: 0 for c in CHURN_SUMS}})
        t["entries"] += 1
        t[r["outcome"].lower()] += 1
        if r["outcome"] != "ACCEPTED":
            continue
        t["changed"] += r["changed"]
        t["beyond"] += sum(r["beyond"].values())
        t["no_effect"] += 1 if (r["changed"] == 0 and r["class"] != "NOOP") else 0
        for c in RECORD_CLASSES:
            t[c] += r["classes"][c]
            t["beyond_" + c] += r["beyond"][c]
        t["root_readdressed_entries"] += 1 if (r["churn"]["root_replaced_own"] + r["churn"]["root_replaced_other"]) else 0
        t["root_readdressed_own_entries"] += 1 if r["churn"]["root_replaced_own"] else 0
        t["root_readdressed_other_entries"] += 1 if r["churn"]["root_replaced_other"] else 0
        t["reassigned"] += r["churn"]["reassigned"]
        t["key_changed"] += 1 if r["key_changed"] else 0
        t["by_only"] += r["by_only"]
        for c in CHURN_SUMS:
            t[c] += r["churn"][c]
        if r["grant"] is not None and is_modify(r):
            t["grant_of"] += 1
            t["grant_survived"] += 1 if r["grant"] else 0
    return dict(sorted(out.items()))


CHURN_SUMS = ("gone_own", "gone_other", "new_own", "new_other", "replaced_own", "replaced_other", "root_gone_own",
              "root_gone_other", "root_new_own", "root_new_other", "root_replaced_own", "root_replaced_other", "root_reassigned")


def is_modify(r):
    c = r["class"]
    return r["outcome"] == "ACCEPTED" and (c.startswith("SHIFT") or c == "MAT" or (c in ("NUM+", "NUM-") and r["role"] in MODIFY_ROLES))


def verdicts(head, entries, base, results):
    acc = [r for r in results if r["outcome"] == "ACCEPTED"]
    byn = {r["n"]: r for r in results}
    H = {}
    H["H1 INVENTORY"] = (True, "made again from the fixtures, equal to INVENTORY.jsonl (%d entries, %s)" % (len(entries), INVENTORY_SHA256[:12]))
    H["H2 FIXTURES"] = (True, "6 fixtures, SPEC.md and FROZEN.sha256 with what it names are the frozen bytes, before the run "
                              "and after it; the code the run executed is the same bytes after it as before")
    noop = [r for r in results if r["class"] == "NOOP"]
    ok3 = len(noop) == 4 and all(r["outcome"] == "ACCEPTED" and r["changed"] == 0 and r["noop"]["bytes_differ"]
                                 and r["noop"]["scene_bytes_equal"] for r in noop)
    H["H3 NOOP"] = (ok3, "; ".join("%s %s" % (r["brief"], ("no changed record, equal scene bytes, the brief's bytes differ"
                                                          if r["outcome"] == "ACCEPTED" and r["changed"] == 0 and r["noop"]["bytes_differ"]
                                                          and r["noop"]["scene_bytes_equal"] else "FAILED: %s" % noop_fault(r))) for r in noop))
    bad4 = [r["n"] for r in acc if not r["diff_complete"]]
    H["H4 DIFF"] = (not bad4, "scene_diff.apply(diff(A, B), A) is B for %d of %d accepted entries%s" % (
        len(acc) - len(bad4), len(acc), (": not for %s" % bad4) if bad4 else ""))
    # the classes' sum against the diff's own count of what changed, taken apart from the list the classes were given to
    bad5 = [r["n"] for r in acc if not (sum(r["classes"].values()) == r["changed"] == r["diff_count"]
                                        and len(r["unexplained"]) == r["classes"]["UNEXPLAINED"]
                                        and len(r["declared"]) == r["classes"]["DECLARED-GLOBAL"] == sum(r["channels"].values()))]
    H["H5 TOTAL"] = (not bad5, "%d changed records, each given one class; the classes' sums equal the diff's own count, and the "
                     "UNEXPLAINED and DECLARED-GLOBAL listings their counts, in %d of %d accepted entries%s" % (sum(r["changed"] for r in acc), len(acc) - len(bad5), len(acc), (": not in %s" % bad5) if bad5 else ""))
    by_stmt, ok6, miss = {}, True, []
    for e in entries:
        if e["class"] != "NOOP":
            by_stmt.setdefault((e["brief"], e["line"], e["verb"]), []).append(byn[e["n"]]["outcome"])
    for b in BRIEFS:
        for line, verb, _a in statements(base[b]["text"]):
            outs = by_stmt.get((b, line, verb))
            if verb != "map" and not outs:
                ok6 = False
                miss.append("%s line %d (no entry)" % (b, line))
            elif verb in DRESSING + ("mover",) and "ACCEPTED" not in outs:
                ok6 = False
                miss.append("%s line %d %s (none accepted)" % (b, line, verb))
    H["H6 COVERAGE"] = (ok6, "every statement but map has an entry and every dressing or mover statement an accepted one%s" % (
        (": not %s" % "; ".join(miss)) if miss else ""))
    H["H7 HASHSEED"] = (True, "PYTHONHASHSEED=0 and the interpreter's hash randomization off")

    # P2
    mov = [r for r in results if r["brief"] == "harbor-lift" and r["verb"] == "mover" and r["class"] != "NOOP"]
    macc = [r for r in mov if r["outcome"] == "ACCEPTED"]
    wit = [[r["n"], r["p2"]] for r in macc if r["p2"]]
    p2 = "NOT-REACHED" if not macc else "HELD" if wit else "FAILED"
    P2 = {"verdict": p2, "mover_entries": len(mov), "accepted": len(macc), "witnesses": wit,
          "expected_before_the_run": "HELD, through G-REACH"}
    # P3
    P3 = {"briefs": {}, "expected_before_the_run": "FAILED for all four briefs (neon and puddle ids differ; skyline and comb-tower records at box[4] only)"}
    for b in BRIEFS:
        sd = [r for r in results if r["brief"] == b and r["class"] == "SEED"]
        if len(sd) != 7 or any(r["outcome"] != "ACCEPTED" for r in sd):
            # §9: HELD only when every one of the eight scenes holds the conditions; a scene not made holds none
            P3["briefs"][b] = {"verdict": "FAILED", "seeds_not_made": [[r["n"], r["outcome"]] for r in sd if r["outcome"] != "ACCEPTED"],
                               "entries": [r["n"] for r in sd]}
            continue
        held = all(not r["p3"]["ids_differ"] and not r["p3"]["beyond_heights"] and not r["p3"]["other_sections"] for r in sd)
        ids, beyond, other = {}, set(), set()
        for r in sd:
            for k, v in r["p3"]["ids_differ"].items():
                ids[k] = ids.get(k, 0) + v
            beyond |= {x.split(":", 1)[0] for x in r["p3"]["beyond_heights"]}
            other |= set(r["p3"]["other_sections"])
        P3["briefs"][b] = {"verdict": "HELD" if held else "FAILED", "ids_added_or_removed_by_kind": dict(sorted(ids.items())),
                           "kinds_differing_beyond_heights": sorted(beyond), "other_sections": sorted(other),
                           "heights_only_records": sum(r["p3"]["heights_only"] for r in sd), "entries": [r["n"] for r in sd]}
    vs = [v["verdict"] for v in P3["briefs"].values()]
    P3["verdict"] = "HELD" if len(vs) == 4 and all(v == "HELD" for v in vs) else "FAILED"
    # P1
    cases = [r for r in acc if "p1" in r]
    fails = [r["n"] for r in cases if not (r["p1"]["made_by_s"] and r["p1"]["gone"] and r["p1"]["new"])]
    refused = [r["n"] for r in results if r["outcome"] != "ACCEPTED" and r["class"].startswith("SHIFT") and r["verb"] in ("canopy", "building")]
    P1 = {"verdict": "NOT-REACHED" if not cases else "HELD" if not fails else "FAILED", "cases": [[r["n"], r["p1"]["root"], r["p1"]["new"]] for r in cases],
          "failed": fails, "shift_entries_not_accepted": refused}
    # R1-R4
    unex = [[r["n"]] + u for r in acc for u in r["unexplained"]]
    seeds = [r for r in results if r["class"] == "SEED"]
    # R2 is read from what made each changed record (its producers' verbs), not from the channel list, so that a channel
    # too broad cannot confirm it
    seed_not = [[r["n"]] + x for r in acc if r["class"] == "SEED" for x in r["r2_outside"]]
    seed_ch = [[r["n"], r["outcome"]] for r in seeds if r["outcome"] != "ACCEPTED"]   # a scene not made confirms nothing
    mod = [r for r in acc if is_modify(r)]
    readd = [r for r in mod if r["churn"]["root_replaced_own"] + r["churn"]["root_replaced_other"]]
    reas = [[r["n"], r["churn"]["reassigned"]] for r in acc if r["churn"]["reassigned"]]
    R = {"R1": ("CONFIRMED" if not unex else "CONTRADICTED", "%d UNEXPLAINED records in %d accepted entries" % (len(unex), len(acc))),
         "R2": ("CONFIRMED" if not (seed_not or seed_ch) else "CONTRADICTED",
                "every changed record of the %d seed scenes (of %d seed entries) is a visual or a light made by a "
                "skyline, a comb tower, a neon or a puddle" % (
                    sum(1 for r in seeds if r["outcome"] == "ACCEPTED"), len(seeds))
                if not (seed_not or seed_ch) else "made otherwise, or not made: %s" % (seed_not + seed_ch)),
         "R3": ("CONFIRMED" if readd else "CONTRADICTED", "%d of %d MODIFY entries re-addressed objects" % (len(readd), len(mod))),
         "R4": ("CONFIRMED" if not reas else "CONTRADICTED", "%d records reassigned over %d accepted entries%s" % (
             sum(v for _n, v in reas), len(acc), (" (entries %s)" % [n for n, _v in reas]) if reas else ""))}
    # the exit
    reused = [r for r in mod if r["churn"]["reassigned"]]
    keyc = [r for r in readd if r["key_changed"]]
    split = {}
    for r in readd:
        k = "%s %s" % (r["verb"], r["class"] if r["class"] in ("MAT",) or r["class"].startswith("SHIFT") else "%s/%s" % (r["class"], r["role"]))
        split[k] = split.get(k, 0) + 1
    tot = {c: sum(r["channels"][c] for r in acc) for c in CHANNELS}
    beyond = sum(sum(r["beyond"].values()) for r in acc)
    changed = sum(r["changed"] for r in acc)
    unex_entries = sorted({u[0] for u in unex})
    churn_line = ("OBSERVED (%d of %d entries re-addressed roots, %d reused an id; by verb and class: %s; the key changed in %d of them)"
                  % (len(readd), len(mod), len(reused), ", ".join("%s %d" % kv for kv in sorted(split.items())), len(keyc))
                  if (readd or reused) else "NOT OBSERVED (0 of %d re-addressed, 0 reused)" % len(mod))
    infl_line = ("OBSERVED (%d UNEXPLAINED records in %d entries, listed)" % (len(unex), len(unex_entries)) if unex
                 else "NOT OBSERVED (0 in %d changed records)" % changed)
    exit_ = [
        "EXIT  churn under MODIFY: " + churn_line,
        "      unexpected influence: " + infl_line,
        "      declared channels: G-REACH %d, G-SEED %d, G-NAME %d records; BEYOND %d" % (tot["G-REACH"], tot["G-SEED"], tot["G-NAME"], beyond),
        "      predictions: P2 %s, P3 %s; confirmation P1 %s; reading R1 %s, R2 %s, R3 %s, R4 %s" % (
            p2, P3["verdict"], P1["verdict"], R["R1"][0], R["R2"][0], R["R3"][0], R["R4"][0]),
        "      cited: re-addressing %s; reuse %s; UNEXPLAINED %s; G-REACH %s; G-SEED %s; G-NAME %s; BEYOND %s; P2 %s; P3 %s; P1 %s; "
        "R1 %s; R2 %s; R3 the re-addressing entries; R4 %s" % (
            [r["n"] for r in readd], [r["n"] for r in reused], unex_entries,
            *[[r["n"] for r in acc if r["channels"][c]] for c in CHANNELS], [r["n"] for r in acc if sum(r["beyond"].values())],
            [w[0] for w in wit], json.dumps({b: v.get("entries", []) for b, v in P3["briefs"].items()}, sort_keys=True),
            [c[0] for c in P1["cases"]], unex_entries, [r["n"] for r in seeds], [n for n, _v in reas]),
        "      limits: " + LIMITS,
        "      not established: " + NOT_ESTABLISHED,
    ]
    return H, {"P2": P2, "P3": P3}, P1, R, exit_, {"modify": len(mod), "readdressed": [r["n"] for r in readd],
                                                  "reused": [r["n"] for r in reused], "key_changed": [r["n"] for r in keyc],
                                                  "unexplained": unex, "channels": tot, "beyond": beyond, "changed": changed}


def noop_fault(r):
    if r["outcome"] != "ACCEPTED":
        return r["outcome"]
    return "%d changed record(s) %s; bytes differ %s; scene bytes equal %s" % (
        r["changed"], r["noop"]["changed_records"], r["noop"]["bytes_differ"], r["noop"]["scene_bytes_equal"])


# ------------------------------------------------------------------------------------------------ the report
def file_sha(rel):
    return sha256(open(os.path.join(REPO, rel), "rb").read().replace(b"\r\n", b"\n"))


def table(title, t, keys):
    cols = ["entries", "accepted", "refused", "crashed", "changed", "OWN", "by_only", "IN-SCOPE", "DECLARED-GLOBAL",
            "UNEXPLAINED", "beyond", "beyond_OWN", "beyond_IN-SCOPE", "beyond_DECLARED-GLOBAL", "beyond_UNEXPLAINED",
            "no_effect", "gone_own", "gone_other", "new_own", "new_other", "replaced_own", "replaced_other", "reassigned",
            "root_gone_own", "root_gone_other", "root_new_own", "root_new_other", "root_replaced_own", "root_replaced_other",
            "root_reassigned", "root_readdressed_entries", "root_readdressed_own_entries", "root_readdressed_other_entries",
            "key_changed", "grant_survived", "grant_of"]
    out = ["%s (%s)" % (title, " ".join(cols))]
    for k in keys:
        if k in t:
            out.append("  %-16s %s" % (k, " ".join(str(t[k][c]) for c in cols)))
    return out


def report(head, entries, base, results, code):
    H, P, P1, R, exit_, summ = verdicts(head, entries, base, results)
    acc = [r for r in results if r["outcome"] == "ACCEPTED"]
    by_class, by_role, by_verb = tally(results, "class"), tally(results, "role"), tally(results, "verb")
    refusals = {}
    for r in results:
        if r["outcome"] == "REFUSED":
            k = "%s %s" % (r["verb"], r["class"])
            refusals[k] = refusals.get(k, 0) + 1
    crashes = [[r["n"], r["brief"], r["class"], r["message"]] for r in results if r["outcome"] == "CRASHED"]
    reads = dict(sorted(code.items()))
    doc = {"format": FORMAT, "spec_sha256": SPEC_SHA256, "inventory_sha256": INVENTORY_SHA256, "fixtures_sha256": FIXTURES_SHA256,
           "read": reads, "python": "%d.%d.%d" % sys.version_info[:3],
           "baselines": {b: base[b]["sha"] for b in BRIEFS},
           "harness": {k: {"held": v[0], "detail": v[1]} for k, v in H.items()},
           "measured": {"entries": len(results), "accepted": len(acc), "refused": sum(1 for r in results if r["outcome"] == "REFUSED"),
                        "crashed": len(crashes), "by_class": by_class, "by_role": by_role, "by_verb": by_verb,
                        "refusals": dict(sorted(refusals.items())), "crashes": crashes, "summary": summ},
           "predictions": P, "confirmation": {"P1": P1}, "reading": {k: {"verdict": v[0], "detail": v[1]} for k, v in R.items()},
           "limits": LIMITS, "not_established": NOT_ESTABLISHED, "exit": exit_, "entries": results}
    js = (json.dumps(doc, sort_keys=True, indent=0, ensure_ascii=True) + "\n").encode("ascii")
    T = ["LOCALITY-1 REPORT (%s)" % FORMAT,
         "spec SPEC.md %s  inventory %s  fixtures %s" % (SPEC_SHA256, INVENTORY_SHA256, FIXTURES_SHA256),
         "read and executed, unchanged through the run: " + "; ".join("%s %s" % kv for kv in reads.items()),
         "python %d.%d.%d" % sys.version_info[:3], "",
         "== HARNESS (these set the exit status; a FAILED prediction does not)"]
    T += ["  %s %s: %s" % (k, "held" if v[0] else "FAILED", v[1]) for k, v in H.items()]
    T += ["", "== MEASURED (what this exporter did with these fixtures; observations, not proofs)",
          "  entries %d: accepted %d, refused %d, crashed %d (every entry of the inventory, none dropped)" % (
              len(results), len(acc), doc["measured"]["refused"], len(crashes))]
    T += ["  " + x for x in table("by edit class", by_class, CLASSES)]
    T += ["  " + x for x in table("by role (NUM and SHIFT entries carry one; '-' none)", by_role, sorted(by_role))]
    T += ["  " + x for x in table("by verb", by_verb, sorted(by_verb))]
    T += ["  channels: " + ", ".join("%s %d" % kv for kv in summ["channels"].items()) + "; BEYOND %d of %d changed records" % (summ["beyond"], summ["changed"]),
          "  refused, by verb and class: " + (", ".join("%s %d" % kv for kv in sorted(refusals.items())) or "none") + " (every message in REPORT.json)",
          "  crashed: " + (json.dumps(crashes) if crashes else "none"),
          "  MODIFY entries %d; re-addressed objects in %d; reused an id in %d; the key changed in %d of the re-addressed" % (
              summ["modify"], len(summ["readdressed"]), len(summ["reused"]), len(summ["key_changed"])),
          "  grant survival (a proxy for the F-3 decision, SPEC.md §12; shape grants not measured): " +
          ", ".join("%s %d/%d" % (k, v["grant_survived"], v["grant_of"]) for k, v in by_class.items() if v["grant_of"]),
          "", "== PREDICTIONS (frozen before the run; decided by it)",
          "  P2 %s: %d mover entries, %d accepted; witnesses (entry, lights outside the mover's swept cells): %s" % (
              P["P2"]["verdict"], P["P2"]["mover_entries"], P["P2"]["accepted"], json.dumps(P["P2"]["witnesses"])),
          "     expected by the author before the run: %s" % P["P2"]["expected_before_the_run"],
          "  P3 %s:" % P["P3"]["verdict"]]
    for b, v in P["P3"]["briefs"].items():
        T.append("     %s %s: %s" % (b, v["verdict"], json.dumps({k: v[k] for k in sorted(v) if k != "verdict"}, sort_keys=True)))
    T += ["     expected by the author's reading before the run: %s" % P["P3"]["expected_before_the_run"],
          "", "== CONFIRMATION (from reading; the run confirms or refutes it)",
          "  P1 %s: %d accepted SHIFT entries of a building or a canopy with corners; failed %s; not accepted %s" % (
              P1["verdict"], len(P1["cases"]), P1["failed"], P1["shift_entries_not_accepted"]),
          "", "== READING EXPECTATIONS (declared before the run; each now read against it)"]
    T += ["  %s %s: %s" % (k, v[0], v[1]) for k, v in R.items()]
    T += ["", "== LIMITS", "  " + LIMITS, "  Not established: " + NOT_ESTABLISHED, ""] + exit_
    txt = ("\n".join(T) + "\n").encode("utf-8")
    return doc, js, txt, all(v[0] for v in H.values())


# ------------------------------------------------------------------------------------------------ commands
def code_sha():
    return {rel: file_sha(rel) for rel in READ}


def prepare():
    if os.environ.get("PYTHONHASHSEED") != "0" or sys.flags.hash_randomization:
        raise Refusal("LOCALITY-HASHSEED", "PYTHONHASHSEED is %r and the interpreter's hash randomization is %s, not '0' and off"
                      % (os.environ.get("PYTHONHASHSEED"), "on" if sys.flags.hash_randomization else "off"))
    check_fixtures()
    head, entries = check_inventory()
    check_frozen()
    texts = {b: fixture("briefs/%s.art" % b).decode("utf-8") for b in BRIEFS}
    for e in entries:
        brief_bytes(e, texts[e["brief"]])
    return head, entries, texts


def cmd_inventory():
    head, entries, _t = prepare()
    print("LOCALITY INVENTORY HELD: %d entries, sha256 %s" % (len(entries), INVENTORY_SHA256))
    return 0


def after(code):
    """H2 after the run: the fixtures, the map among them, read again; the executed code the same bytes as before."""
    check_fixtures()
    check_frozen()
    now = code_sha()
    moved = [rel for rel in READ if now[rel] != code[rel]]
    if moved:
        raise Refusal("LOCALITY-FIXTURE", "the code changed during the run: %s" % ", ".join(moved))


def cmd_run():
    head, entries, texts = prepare()
    code = code_sha()
    base, results = measure(entries, texts)
    after(code)
    for b in BRIEFS:
        base[b]["text"] = texts[b]
    _doc, js, txt, held = report(head, entries, base, results, code)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "REPORT.json"), "wb") as fh:
        fh.write(js)
    with open(os.path.join(OUT, "REPORT.txt"), "wb") as fh:
        fh.write(txt)
    lines = txt.decode("utf-8").splitlines()
    for ln in lines[lines.index("== HARNESS (these set the exit status; a FAILED prediction does not)"):]:
        if ln.startswith("  H") or ln.startswith("EXIT") or ln.startswith("      "):
            print(ln)
    print("LOCALITY HARNESS %s" % ("HELD (H1-H7)" if held else "FAILED"))
    print("LOCALITY-1 REPORT %s" % sha256(js))
    return 0 if held else 1


def cmd_selftest():
    """SPEC.md §14: each plant caught by its own row, for its stated reason; plant success is evidence about the harness,
    not about the exporter."""
    head, entries, texts = prepare()
    code = code_sha()
    subset = ("plaza-night", "harbor-lift")
    noops = [e for e in entries if e["class"] == "NOOP"]
    rows = []

    def run(plant, es, keep):
        global PLANT
        PLANT = plant
        try:
            return measure(es, texts, keep)[1]
        finally:
            PLANT = ""

    def row(name, ok, detail):
        rows.append(ok)
        print("%s  %s: %s" % ("PASS" if ok else "FAIL", name, detail))

    clean_noop = run("", noops, None)
    ok = len(clean_noop) == 4 and all(r["outcome"] == "ACCEPTED" and r["changed"] == 0 and r["noop"]["bytes_differ"]
                                      and r["noop"]["scene_bytes_equal"] for r in clean_noop)
    row("NOOP-CLEAN", ok, "the no-op control on the clean harness: %s" % "; ".join(
        "%s %s" % (r["brief"], "0 changed, bytes differ, scene bytes equal" if r["outcome"] == "ACCEPTED" and r["changed"] == 0
                   else noop_fault(r)) for r in clean_noop))

    es = [e for e in entries if e["brief"] in subset]
    clean = run("", es, subset)
    cu = {(r["n"], u[0], u[1]): u[2] for r in clean if r["outcome"] == "ACCEPTED" for u in r["unexplained"]}
    cre = sum(r["churn"]["reassigned"] for r in clean if r["outcome"] == "ACCEPTED")
    print("      clean subset: %d entries, %d accepted, UNEXPLAINED %d, REASSIGNED %d" % (
        len(clean), sum(1 for r in clean if r["outcome"] == "ACCEPTED"), len(cu), cre))

    g = run("global", es, subset)
    gu = {(r["n"], u[0], u[1]): u[2] for r in g if r["outcome"] == "ACCEPTED" for u in r["unexplained"]}
    extra = {k: v for k, v in gu.items() if k not in cu}
    fields = sorted({f for v in extra.values() for f in v})
    ok = len(gu) > len(cu) and all(k[1] == "lights" and set(v) <= {"candela", "by"} for k, v in extra.items())
    gre = sum(r["churn"]["reassigned"] for r in g if r["outcome"] == "ACCEPTED")
    row("PL-GLOBAL caught", ok, "UNEXPLAINED %d under the plant, %d clean; the %d records it added are all lights, their "
        "changed fields %s" % (len(gu), len(cu), len(extra), fields))
    print("      attribution: under the global plant REASSIGNED is %d (clean %d); outcomes differ from the clean subset's in %d entries"
          % (gre, cre, sum(1 for a, b in zip(clean, g) if a["outcome"] != b["outcome"])))

    rn = run("renumber", es, subset)
    rre = sum(r["churn"]["reassigned"] for r in rn if r["outcome"] == "ACCEPTED")
    ok = rre > cre
    row("PL-RENUMBER caught", ok, "REASSIGNED %d under the plant, %d clean" % (rre, cre))
    # the reason: under the plant an id is a place in a sorted list, so it moves onto another piece exactly where an
    # entry adds or removes a piece; an entry that adds or removes none keeps every id on its piece
    moved = {r["n"] for r in rn if r["outcome"] == "ACCEPTED" and r["churn"]["reassigned"]}
    addrem = {r["n"] for r in clean if r["outcome"] == "ACCEPTED" and
              any(r["sections"].get(s, {}).get(w, 0) for s in ("visuals", "lights") for w in ("added", "removed"))}
    ru = sum(len(r["unexplained"]) for r in rn if r["outcome"] == "ACCEPTED")
    print("      attribution: %d entries reassign an id under the plant; every one of them adds or removes a visual or a light "
          "in the clean run: %s (%d such entries clean); UNEXPLAINED under the plant %d (clean %d)" % (
              len(moved), moved <= addrem, len(addrem), ru, len(cu)))

    pn = run("noop-name", noops, None)
    ok = len(pn) == 4 and all(r["outcome"] == "ACCEPTED" and r["changed"] == 1 and r["noop"]["changed_records"] == [["top", "name", ["="]]]
                              for r in pn)
    row("PL-NOOP caught", ok, "the no-op control fails on %d of 4 briefs, each with one changed record: %s" % (
        sum(1 for r in pn if r["outcome"] == "ACCEPTED" and r["changed"]), sorted({json.dumps(r["noop"]["changed_records"]) for r in pn
                                                                                   if r["outcome"] == "ACCEPTED"})))
    after(code)
    print("      plant success is evidence about the harness, not about the exporter")
    print("LOCALITY SELFTEST %d/%d" % (sum(rows), len(rows)))
    return 0 if all(rows) else 1


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    try:
        if cmd == "inventory":
            return cmd_inventory()
        if cmd == "run":
            return cmd_run()
        if cmd == "selftest":
            return cmd_selftest()
    except Refusal as e:
        print("LOCALITY REFUSED %s" % e)
        return 2
    print(__doc__ or "usage: python art/locality.py inventory | run | selftest")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
