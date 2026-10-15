# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/providers/director_prompt.py — what every model provider of the director gateway (art/studio.py) tells its model:
# one system text and one rendering of a VERDANDI-STUDIO-REQUEST 1 as plain text (the tagged objects, their geometry
# and their relations among it, STUDIO-1; and, in a request of version 2, MARK-0's shapes), so that two providers given the same
# request ask their models the same thing, and differ only in how the model is reached (the owner's ruling of
# 2026-10-11: "shared schema and gateway throughout"). Standard library only; imported by the providers beside it.

SYSTEM = """You are the art director's assistant inside Verðandi, a studio where a designer changes a running game world
by describing what they want. You do not edit the world. You propose at most three candidate revisions of the world's
art file (its brief), each a short list of revision lines, and the studio checks, compiles and previews them; the
designer admits one or none.

Rules for every candidate:
- Change the look only: the statements of the art file. Walls, floors, cover, spawns and the player's route belong to
  the map and cannot be changed here.
- Write each revision line exactly as the request's revision syntax says: '= <statement>' replaces the statement with
  the same key, '+ <statement>' adds one whose key is new, '- <key>' removes one. Keep every word of a statement you
  do not mean to change.
- Use only the statements and options the art language below defines.
- Declare in scope every address the candidate changes (region/kind/* for the pieces a statement makes, material/NAME
  for a material); anything outside the scope must stay exactly as it is, or the candidate is refused.
- Anything overhead must clear the reach ceiling; a change that puts dressing where a player can be is refused.
- Make the candidates genuinely different answers to the prompt, and say in each rationale what it does and why.

Every answer has an outcome. When you propose candidates, its kind is "none". When you propose none, say why, in one
of three ways, and never leave it empty:
- "unsupported": the prompt needs something the studio cannot make yet. List in unmet the names it needs, chosen
  only from the request's list of what the studio cannot make (for example entity.person for a figure, motion.path
  for something that moves along a route). If part of the prompt can be made, propose candidates for that part
  instead and say in their rationale what was left out.
- "ambiguous": the prompt can be read in more than one way and the choice matters; ask one to three short questions.
- "declined": you will not do it; give the reason (content, rights, safety or other) and one sentence.
The note is one plain sentence for the designer. It is shown as text and never carried out.

The designer names objects with tags (@1, @2, ...). The request lists each tagged object: what it is, the statement
that made it, what that statement can change, where it is in metres, and how the tagged objects stand to one another
and to the nearest wall, measured from the scene. A tag means that object and no other. Change the target; change a
pinned object only if the prompt asks for it, and otherwise keep it exactly as it is (it is a reference). Change no
object that is not tagged unless the prompt asks for it; if the only statement that can make the change also makes
other objects, say so in the rationale. Name, in each rationale, the tagged objects the candidate changes.

The designer may also name shapes (#name): an outline drawn on one face of one box of the world, exact to the
millimetre, with what the designer means by it (an opening to cut, an addition, a region to change, a path). A shape is
the designer's mark, not the world, and it is where the designer means: keep the candidate's change to that region, and
say in each rationale how the candidate answers the shape, or why it cannot (the art language changes whole statements;
an opening in the play geometry is a layout change, which the studio cannot make: unsupported, layout.change). The
shape's checks are the studio's own; its words are the designer's, and nothing has checked them. The studio holds every
candidate to the shapes named: it decides exactly whether every box the candidate changes lies in the shape's region
(the outline swept from the back of the marked box out to the region's reach) and shows the candidates in that order,
held first. Each shape lists the statements whose objects lie wholly in its region now, and those that reach it with
objects outside it: changing one of the latter changes something outside the region."""


def _ref_lines(r):
    g, st = r["geometry"], r.get("statement") or {}
    b = g["bounds_m"]
    lines = ["%s, %s: %s %s, material %s%s" % (r["tag"], "the target" if r["role"] == "target" else "pinned as a reference", r["kind"], r["address"],
                                                r["material"] or "-", "  (mentioned in the prompt)" if r.get("mentioned") else ""),
             "    made by line %s of the brief: %s" % (st.get("line"), st.get("text")),
             "    that statement makes %d object%s; a revision of it can change: %s" % (r["statement_makes"], "" if r["statement_makes"] == 1 else "s", r["changeable"] or "-"),
             "    its address patterns, for a scope: " + ", ".join(r["patterns"]) + " (an exact address such as " + r["address"] + " does not cover the "
             "parts its statement makes, its ribs and lights, which have addresses of their own)",
             "    bounds [x0, y0, z0, x1, y1, z1] = [%s] m; size %s x %s x %s m (x, y, z); underside %s m, top %s m; long axis %s; %s; %d box%s%s" % (
                 ", ".join("%g" % v for v in b), g["size_m"][0], g["size_m"][1], g["size_m"][2], g["underside_m"], g["top_m"], g["long_axis"],
                 g["orientation"], g["boxes"], "" if g["boxes"] == 1 else "es",
                 (" (" + ", ".join("%s %d" % kv for kv in g["parts"].items()) + ")") if g["parts"] else "")]
    if g.get("faces"):
        lines.append("    faces %s (%s)" % (", ".join(g["faces"]["directions"]), g["faces"]["basis"]))
    w = r.get("nearest_wall")
    if w:
        lines.append("    nearest wall: %s, on its %s side, %s m away in plan and %s m in space; the wall's top at %s m (%s)" % (
            w["address"], w["side"], w["plan_gap_m"], w["gap_m"], w["wall_top_m"], w["basis"]))
    if r["bound"]["changed_since"]:
        lines.append("    it has changed since the designer tagged it (the same object, another shape or look)")
    elif r["bound"]["changed_since"] is None:
        lines.append("    whether it has changed since the designer tagged it is not known (the tag was kept from before the studio restarted)")
    return lines


def _rel_lines(x):
    m = x["measured"]
    d = m["direction_of_to"]
    lines = ["%s to %s: gap %s m%s; overlap in plan %s m along x and %s m along z (negative: apart); %s lies %s of %s (bearing %s deg), centres %s m apart; "
             "%s's underside is %+g m and its top %+g m relative to %s's; %s kind, %s material, %s statement" % (
                 x["from"], x["to"], m["gap_m"], " (the boxes touch or overlap)" if m["touching"] else "", m["plan_overlap_m"]["x"], m["plan_overlap_m"]["z"],
                 x["to"], d["compass"], x["from"], d["bearing_deg"], d["centres_apart_m"], x["to"], m["to_underside_minus_from_underside_m"],
                 m["to_top_minus_from_top_m"], x["from"], "the same" if m["same_kind"] else "another", "the same" if m["same_material"] else "another",
                 "the same" if m["same_statement"] else "another"),
             "    (" + x["basis"] + ")"]
    if x.get("inferred"):
        lines.append("    %s %s toward %s (%s)" % (x["from"], "faces" if x["inferred"]["from_faces_toward_to"] else "does not face", x["to"], x["inferred"]["basis"]))
    return lines


def user_text(req):
    """The request as the model reads it: the prompt, the tagged objects (the target and the pins) with their geometry
    and relations, where the designer stands, the brief's statements, the revision syntax and the language's
    reference."""
    lines = ["The designer's prompt: " + req["prompt"], ""]
    refs = req.get("references") or []
    if not req.get("target"):
        lines += ["No target is selected: the prompt is for the whole world%s." % (", with the pinned objects below as references" if refs else ""), ""]
    if refs:
        lines += ["The tagged objects (a tag names that object and no other):"]
        for r in refs:
            lines += _ref_lines(r)
        rels = req.get("relations") or []
        if rels:
            lines += ["", "How the tagged objects stand to one another:"]
            for x in rels:
                lines += _rel_lines(x)
        lines += [""]
    shapes = req.get("shapes") or []
    if shapes:
        lines += ["The shapes the designer drew and named (a shape is that outline on that face and nowhere else):"]
        for s in shapes:
            on, f = s["on"], s["face"]
            st = on.get("statement") or {}
            lines += ["#%s: %s, %s of %d vertices, on the %s face of %s (%s)%s" % (
                          s["name"], s["meaning"], "a closed outline" if s["closed"] else "an open path", len(s["vertices_m"]), on["face"], on["address"],
                          on["kind"], (", made by line %s of the brief: %s" % (st.get("line"), st.get("text"))) if st else ", the map's play geometry"),
                      "    the face: %s x %s m, its origin at [%s] m, u along %s and v along %s (metres on the face from its origin)" % (
                          f["width_m"], f["height_m"], ", ".join("%g" % v for v in f["origin_m"]), f["u"], f["v"]),
                      "    vertices (u, v) m: " + "; ".join("(%g, %g)" % tuple(v) for v in s["vertices_m"]),
                      "    in the world (x, y, z) m: " + "; ".join("(%g, %g, %g)" % tuple(v) for v in s["world_m"])]
            if s.get("area_m2") is not None:
                lines.append("    area %s m2" % s["area_m2"])
            lines.append("    the studio's checks: " + "; ".join("%s %s (%s)" % (k, "yes" if c["ok"] else "no" if c["ok"] is False else "not checked", c["detail"])
                                                          for k, c in sorted(s["checks"].items())))
            if on.get("changeable"):
                lines.append("    what a revision of its statement can change: " + on["changeable"])
            if s["words"]:
                lines.append("    the designer's words, not checked: " + "; ".join(s["words"]))
            if s.get("note"):
                lines.append("    the designer's note: " + s["note"])
            g = s.get("region") or {}
            if g and "error" not in g:
                lines.append("    its region: the outline swept from the back of the box out to %s" % (
                    "the sky" if g["reach_m"] is None else "%g m from the face" % g["reach_m"]))
                lines.append("    statements whose every object lies in the region now: " + (", ".join(g["statements_inside"]) or "none"))
                lines.append("    statements that reach the region with objects outside it: " + (", ".join(g["statements_partly"]) or "none"))
        lines += [""]
    lines += ["Coordinates: " + req.get("coordinates", ""), ""]
    if req.get("camera"):
        c = req["camera"]
        lines += ["The designer stands at x %.1f, z %.1f (metres), eye height %.1f m, facing %.0f degrees (0 north, 90 east), looking %.0f degrees up." % (
            c["x"], c["z"], c["y"], c["yaw_deg"], c["pitch_deg"]), ""]
    lines += ["The brief's statements (line: text; key):"] + ["%d: %s ; key %s" % (s["line"], s["text"], s["key"]) for s in req["statements"]]
    lines += ["", "The revision syntax: " + req["revision_syntax"], "", req.get("language", "")]
    cap = req.get("capabilities")
    if cap:
        lines += ["", "What the studio can make now: " + ", ".join(cap.get("supported", [])) + ".",
                  "What it cannot make yet (the only names an unsupported outcome may list): " + ", ".join(cap.get("unsupported", [])) + "."]
    return "\n".join(lines)
