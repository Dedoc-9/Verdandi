# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/providers/anthropic_messages.py — a provider for the director gateway (art/studio.py) that asks a Claude model,
# through the Anthropic Messages API, for the candidates. Standard library only.
#
#   art/providers/anthropic.json     {"provider": "cli", "argv": ["{python}", "art/providers/anthropic_messages.py"], ...}
#
# Its settings are in its environment, never in a file of the repository and never in the browser:
#   ANTHROPIC_API_KEY         the key
#   VERDANDI_DIRECTOR_MODEL   the model's id (required: nothing here guesses one)
#   VERDANDI_DIRECTOR_API     the endpoint, https://api.anthropic.com/v1/messages if not set
#
# It reads a VERDANDI-STUDIO-REQUEST 0 on standard input and writes a VERDANDI-STUDIO-RESPONSE 0 on standard output
# (art/STUDIO.md). The model is given the request (the prompt, the selection and its statement, the camera, the brief's
# statements, the language's reference and the revision syntax) and a single tool whose input schema is the response
# schema the request carries; it is made to call that tool, so that its answer has the schema's shape rather than
# being prose read for JSON. What it proposes is then the gateway's to refuse and the director's to judge: nothing it
# says reaches the world but through them. An error (no key, an HTTP failure, an answer without the tool's call) is
# written to standard error and the exit status is not 0, which the gateway shows; the world is untouched.
#
# Not measured against the live API in the build container (no key there); its request and its reading of an answer
# are held to a local server that answers as the API's documentation describes.

import json
import os
import sys
import urllib.error
import urllib.request

ENDPOINT = "https://api.anthropic.com/v1/messages"
TOOL = "propose_candidates"
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
- Declare in scope every address the candidate changes (region/kind/* for the pieces a statement makes, material/NAME
  for a material); anything outside the scope must stay exactly as it is, or the candidate is refused.
- Anything overhead must clear the reach ceiling; a change that puts dressing where a player can be is refused.
- Make the candidates genuinely different answers to the prompt, and say in each rationale what it does and why.
- If the prompt cannot be answered within these rules, propose no candidates."""


def fail(msg, code=2):
    sys.stderr.write("anthropic_messages: %s\n" % msg)
    return code


def ask(req):
    key, model = os.environ.get("ANTHROPIC_API_KEY", ""), os.environ.get("VERDANDI_DIRECTOR_MODEL", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set in the environment play.py was started from")
    if not model:
        raise RuntimeError("VERDANDI_DIRECTOR_MODEL is not set: name the model to ask")
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
    body = {"model": model, "max_tokens": 4096, "system": SYSTEM,
            "tools": [{"name": TOOL, "description": "Propose at most %d candidate revisions of the brief." % req["respond"]["max_candidates"],
                       "input_schema": req["respond"]["schema"]}],
            "tool_choice": {"type": "tool", "name": TOOL},
            "messages": [{"role": "user", "content": "\n".join(lines)}]}
    http = urllib.request.Request(os.environ.get("VERDANDI_DIRECTOR_API", ENDPOINT), data=json.dumps(body).encode("utf-8"), method="POST",
                                  headers={"content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(http, timeout=120) as r:
            ans = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        raise RuntimeError("the API answered %d: %s" % (e.code, " ".join(detail.split())))
    except (urllib.error.URLError, OSError) as e:
        raise RuntimeError("the API could not be reached: %s" % e)
    calls = [b for b in ans.get("content", []) if b.get("type") == "tool_use" and b.get("name") == TOOL]
    if not calls or not isinstance(calls[0].get("input"), dict):
        raise RuntimeError("the answer holds no call of %s (stop reason %s)" % (TOOL, ans.get("stop_reason")))
    return ans.get("model") or model, calls[0]["input"].get("candidates", [])


def main():
    try:
        req = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        model, cands = ask(req)
    except (RuntimeError, ValueError, KeyError, TypeError) as e:
        return fail(str(e))
    out = {"format": "VERDANDI-STUDIO-RESPONSE", "version": "0", "id": req["id"], "provider": {"name": "anthropic-messages", "model": model}, "candidates": cands}
    sys.stdout.buffer.write(json.dumps(out, sort_keys=True).encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
