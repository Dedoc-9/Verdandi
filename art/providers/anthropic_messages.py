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
# It reads a VERDANDI-STUDIO-REQUEST 1 on standard input and writes a VERDANDI-STUDIO-RESPONSE 0 on standard output
# (art/STUDIO.md). The model is given the request as director_prompt.py renders it for every provider (the prompt, the
# tagged objects with their statements, geometry and relations, the camera, the brief's statements, the language's
# reference and the revision syntax),
# and a single tool whose input schema is the response schema the request carries; it is made to call that tool, so
# that its answer has the schema's shape rather than being prose read for JSON. The response names the model the API
# says answered and the tokens it counted (no cost: prices are not this file's to know). What it proposes is then the gateway's to refuse and the director's to judge: nothing it
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

import director_prompt   # beside this file: the system text and the request as the model reads it, shared by the providers

ENDPOINT = "https://api.anthropic.com/v1/messages"
TOOL = "propose_candidates"


def fail(msg, code=2):
    sys.stderr.write("anthropic_messages: %s\n" % msg)
    return code


def ask(req):
    key, model = os.environ.get("ANTHROPIC_API_KEY", ""), os.environ.get("VERDANDI_DIRECTOR_MODEL", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set in the environment play.py was started from")
    if not model:
        raise RuntimeError("VERDANDI_DIRECTOR_MODEL is not set: name the model to ask")
    body = {"model": model, "max_tokens": 4096, "system": director_prompt.SYSTEM,
            "tools": [{"name": TOOL, "description": "Propose at most %d candidate revisions of the brief." % req["respond"]["max_candidates"],
                       "input_schema": req["respond"]["schema"]}],
            "tool_choice": {"type": "tool", "name": TOOL},
            "messages": [{"role": "user", "content": director_prompt.user_text(req)}]}
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
    u = ans.get("usage") or {}
    tin = sum(u.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens") if isinstance(u.get(k), int))
    usage = {"input_tokens": tin, "output_tokens": u.get("output_tokens") if isinstance(u.get("output_tokens"), int) else 0,
             "cost_usd": None, "cost_basis": "not computed here: token counts as the API reported them"}
    return ans.get("model") or model, calls[0]["input"].get("candidates", []), usage


def main():
    try:
        req = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        model, cands, usage = ask(req)
    except (RuntimeError, ValueError, KeyError, TypeError) as e:
        return fail(str(e))
    out = {"format": "VERDANDI-STUDIO-RESPONSE", "version": "0", "id": req["id"], "provider": {"name": "anthropic-messages", "model": model, "usage": usage}, "candidates": cands}
    sys.stdout.buffer.write(json.dumps(out, sort_keys=True).encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
