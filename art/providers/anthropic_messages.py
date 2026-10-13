# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/providers/anthropic_messages.py — a provider for the director gateway (art/studio.py) that asks a Claude model,
# through the Anthropic Messages API, for the candidates. Standard library only.
#
#   art/providers/anthropic.json     {"provider": "cli", "argv": ["{python}", "art/providers/anthropic_messages.py",
#                                     "--model", "claude-opus-5-5"], ...}
#
# Its settings are in its configuration's arguments and its environment, never in the browser:
#   --model ID                the model's id, from the configuration (B1: claude-opus-5-5, the model his Claude Code
#                             CLI runs, so the two providers differ in the adapter alone; a field, not a constant here)
#   VERDANDI_DIRECTOR_MODEL   overrides --model when set
#   ANTHROPIC_API_KEY         the key (never in a file of the repository)
#   VERDANDI_DIRECTOR_API     the endpoint, https://api.anthropic.com/v1/messages if not set
#
# It reads a VERDANDI-STUDIO-REQUEST 1 on standard input and writes a VERDANDI-STUDIO-RESPONSE 0 on standard output
# (art/STUDIO.md). The model is given the request as director_prompt.py renders it for every provider, and its answer
# is constrained by structured outputs: output_config.format {"type": "json_schema", "schema": ...}, the answer being
# JSON in the response's text block (VERIFIED 2026-10-12, platform.claude.com/docs/en/build-with-claude/
# structured-outputs). B1 replaced a forced tool choice, which every current model refuses with 400 ("any and tool
# return a 400 error"). The schema sent is the gateway's with what structured outputs do not support (minLength,
# maxLength, maxItems) moved into the descriptions; the gateway still enforces every limit when it reads the answer.
# A refusal (stop_reason "refusal") is passed on as an answer with no candidates and its stop reason, for the gateway
# to record as DECLINED (0220); a cut answer ("max_tokens") is said, not read, since its output "may not match
# your schema". The system text carries a cache breakpoint. The response names the model the API says answered and
# the tokens it counted (no cost: prices are not this file's to know). What it proposes is then the gateway's to
# refuse and the director's to judge. An error is written to standard error and the exit status is not 0.
#
# Not measured against the live API in the build container (no key there); its request and its reading of an answer
# are held to a local server that answers as the API's documentation describes, and refuses a forced tool choice.

import copy
import json
import os
import sys
import urllib.error
import urllib.request

import director_prompt   # beside this file: the system text and the request as the model reads it, shared by the providers

ENDPOINT = "https://api.anthropic.com/v1/messages"
UNSUPPORTED = {"minLength": "at least %s characters", "maxLength": "at most %s characters", "maxItems": "at most %s items",
               "minimum": "at least %s", "maximum": "at most %s"}


def fail(msg, code=2):
    sys.stderr.write("anthropic_messages: %s\n" % msg)
    return code


def api_schema(schema):
    """The gateway's schema as structured outputs accept it: each unsupported constraint moved into the description
    ("at most 80 characters"), minItems kept only at 0 or 1, every object closed (additionalProperties false)."""
    s = copy.deepcopy(schema)

    def walk(x):
        if isinstance(x, dict):
            notes = [UNSUPPORTED[k] % x.pop(k) for k in list(UNSUPPORTED) if k in x]
            if "minItems" in x and x["minItems"] not in (0, 1):
                notes.append("at least %d items" % x.pop("minItems"))
            if notes:
                x["description"] = ((x["description"] + " ") if x.get("description") else "") + "(" + "; ".join(notes) + ")"
            if x.get("type") == "object":
                x["additionalProperties"] = False
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(s)
    return s


def model_of(argv):
    m = os.environ.get("VERDANDI_DIRECTOR_MODEL", "")
    if not m and "--model" in argv and argv.index("--model") + 1 < len(argv):
        m = argv[argv.index("--model") + 1]
    return m


def ask(req, model):
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set in the environment the studio was started from")
    if not model:
        raise RuntimeError("no model: the configuration names none (--model) and VERDANDI_DIRECTOR_MODEL is not set")
    body = {"model": model, "max_tokens": 8192,
            "system": [{"type": "text", "text": director_prompt.SYSTEM, "cache_control": {"type": "ephemeral"}}],
            "output_config": {"format": {"type": "json_schema", "schema": api_schema(req["respond"]["schema"])}},
            "messages": [{"role": "user", "content": director_prompt.user_text(req)}]}
    http = urllib.request.Request(os.environ.get("VERDANDI_DIRECTOR_API", ENDPOINT), data=json.dumps(body).encode("utf-8"), method="POST",
                                  headers={"content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(http, timeout=170) as r:
            ans = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        raise RuntimeError("the API answered %d: %s" % (e.code, " ".join(detail.split())))
    except (urllib.error.URLError, OSError) as e:
        raise RuntimeError("the API could not be reached: %s" % e)
    stop = ans.get("stop_reason")
    u = ans.get("usage") or {}
    num = lambda k: u.get(k) if isinstance(u.get(k), int) else 0
    usage = {"input_tokens": num("input_tokens") + num("cache_creation_input_tokens") + num("cache_read_input_tokens"),
             "output_tokens": num("output_tokens"), "cost_usd": None,
             "cost_basis": "not computed here: token counts as the API reported them (of the input, %d read from the cache)" % num("cache_read_input_tokens")}
    if stop == "refusal":
        # 0220: a refusal is an answer, observed here, not an error: no candidates, and the stop reason passed on for the
        # gateway to decide (DECLINED); nothing of the model's text is read
        return ans.get("model") or model, [], usage, "refusal", None
    if stop == "max_tokens":
        raise RuntimeError("the answer was cut at max_tokens (%d); it is not read" % body["max_tokens"])
    text = "".join(b.get("text", "") for b in ans.get("content", []) if b.get("type") == "text")
    try:
        doc = json.loads(text)
    except ValueError:
        raise RuntimeError("the answer's text is not JSON (stop reason %s): %r" % (stop, text[:120]))
    if not isinstance(doc, dict) or not isinstance(doc.get("candidates"), list):
        raise RuntimeError("the answer has no candidates list (stop reason %s)" % stop)
    return ans.get("model") or model, doc["candidates"], usage, stop if isinstance(stop, str) else None, doc.get("outcome")


def main(argv):
    try:
        req = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        model, cands, usage, stop, outcome = ask(req, model_of(argv))
    except (RuntimeError, ValueError, KeyError, TypeError) as e:
        return fail(str(e))
    out = {"format": "VERDANDI-STUDIO-RESPONSE", "version": "0", "id": req["id"], "provider": {"name": "anthropic-messages", "model": model, "usage": usage}, "candidates": cands}
    if stop:
        out["provider"]["stop_reason"] = stop         # what the API reported, observed here; the model's own account is the outcome
    if outcome is not None:
        out["outcome"] = outcome
    sys.stdout.buffer.write(json.dumps(out, sort_keys=True).encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
