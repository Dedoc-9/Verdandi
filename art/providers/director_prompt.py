# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/providers/director_prompt.py — what every model provider of the director gateway (art/studio.py) tells its model:
# one system text and one rendering of a VERDANDI-STUDIO-REQUEST as plain text, so that two providers given the same
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
- Use only the statements and options the art language below defines. If the designer asks for something the language
  cannot say, say so in the rationale of the nearest candidate it can say, or propose no candidates.
- Declare in scope every address the candidate changes (region/kind/* for the pieces a statement makes, material/NAME
  for a material); anything outside the scope must stay exactly as it is, or the candidate is refused.
- Anything overhead must clear the reach ceiling; a change that puts dressing where a player can be is refused.
- Make the candidates genuinely different answers to the prompt, and say in each rationale what it does and why.
- If the prompt cannot be answered within these rules, propose no candidates."""


def user_text(req):
    """The request as the model reads it: the prompt, what is selected, where the designer stands, the brief's
    statements, the revision syntax and the language's reference."""
    sel = req.get("selection")
    lines = ["The designer's prompt: " + req["prompt"], ""]
    if sel:
        st = sel.get("statement") or {}
        lines += ["The designer selected %s (material %s), made by line %s of the brief: %s" % (sel["address"], sel.get("material") or "-", st.get("line"), st.get("text")),
                  "Its address patterns: " + ", ".join(sel["patterns"]), ""]
    else:
        lines += ["Nothing is selected: the prompt is for the whole world.", ""]
    if req.get("camera"):
        c = req["camera"]
        lines += ["The designer stands at x %.1f, z %.1f (metres; a cell is 2 m), eye height %.1f m, facing %.0f degrees (0 north, 90 east), looking %.0f degrees up." % (
            c["x"], c["z"], c["y"], c["yaw_deg"], c["pitch_deg"]), ""]
    lines += ["The brief's statements (line: text; key):"] + ["%d: %s ; key %s" % (s["line"], s["text"], s["key"]) for s in req["statements"]]
    lines += ["", "The revision syntax: " + req["revision_syntax"], "", req.get("language", "")]
    return "\n".join(lines)
