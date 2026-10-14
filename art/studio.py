# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/studio.py — STUDIO-0: the director gateway between the running plaza (art/play.py) and a model.
#
#   python art/studio.py selftest
#   python art/studio.py schema           the response schema a provider answers with (JSON Schema, for an adapter)
#   python art/studio.py probe CONFIG.json [--brief B] [--piece ID]
#                                         the smoke test: that the provider's model is asked and its answers follow the prompt
#   python art/studio.py probe CONFIG.json --references [--runs N]
#                                         STUDIO-1's measure: whether a model changes the tagged objects a prompt names, and only those
#   python art/studio.py report [--brief B]
#                                         every recorded request, by provider: failures, latency, tokens, cost per admitted edit
#   python art/studio.py records [--brief B] [--root DIR]
#                                         the request record read back: its chain, each disposition, what was asked for and is not made
#
# By the owner's direction and ruling of 2026-10-11: "the LLM edits design intent; Verðandi compiles that intent into a
# live world; the designer remains in control"; "a pluggable model adapter", behind "a local director gateway that
# accepts requests from play.py, invokes a configurable model provider, validates its output, and returns up to three
# structured design candidates"; "Start with a CLI adapter so the first implementation remains standard-library-only";
# "the model proposes changes—it never directly mutates the live world. Verðandi owns validation, compilation,
# preview, and admission." The contract is in art/STUDIO.md.
#
# The references (STUDIO-1, the owner's ruling of 2026-10-11): E makes an object the target and R pins one as a
# reference; each is given a tag (@1, @2, ...) that names that object, by its id, for as long as the gateway runs, and is
# bound to the scene and head it was selected or pinned at. It is never moved to another object: a tag whose object is
# gone refuses the request until it is unpinned, and a prompt may name only the target and the pins.
#
# What it does, for one request (the page's prompt, its tags and its camera):
#   1. the context, from the head as the files stand: the brief's statements; the target and the pins, each with its
#      statement, its geometry and its nearest wall, and the relations between them (art/studio_refs.py, measured
#      from the scene's boxes, an approximate facing marked inferred); the camera; written as one
#      VERDANDI-STUDIO-REQUEST 1 document with an id and the head it is based on, and kept under
#      art/build/studio/BRIEF/ID/ with everything that follows;
#   2. the provider, a command from a configuration file (an argv list, never a shell line; the request on its
#      standard input, never in its arguments), with a time limit, a limit on what it may print, and cancellation:
#      a newer request cancels the one before it, and the page's cancel kills the command;
#   3. the response read whole or refused whole (STUDIO-RESPONSE-*): a VERDANDI-STUDIO-RESPONSE 0 document naming the
#      request's id, with at most three candidates of bounded fields; each made a VERDANDI-INTENT (the letter, the
#      base and the prompt are the gateway's, not the model's) and evaluated by the director at the current head
#      (art/director.py: the art checks, and the scope check, which holds everything outside the declared scope
#      unchanged); a candidate the director refuses is shown with its reason and never drawn;
#   4. the rest compiled and handed to play.py as sources the page can switch to, in place, the game untouched, each
#      with what it touches: the tags it changed, the untagged objects it changed, the objects it made;
#   5. nothing admitted until the designer admits one: then the candidate is evaluated again at the head as it is,
#      and admitted through the director's ledger only if that head is the one it was previewed at. Rejecting records
#      a refusal; undo admits the last admission's exact inverse as an intent of its own.
# A timeout, a provider that cannot start or exits with an error, a response too long or malformed, a cancellation:
# each leaves the world as it was and says why.
#
# Every request that ends on its own ends in one disposition (0220, after a prompt to add a figure was answered with
# nothing and no reason): REALIZED (candidates came back), UNSUPPORTED (the studio cannot make what was asked: the
# model names it from the closed list of capabilities the request publishes, and a name outside that list is not
# read), AMBIGUOUS (the model asks one to three questions, shown as text and never sent back as instructions),
# DECLINED (the provider's API reported a refusal, decided by the host; or the model declined, with a reason from a
# closed list, its claim), or FAILED (the provider could not be run or read, or answered nothing and gave no reason).
# What the host observes decides first; what the model says of itself is recorded as its claim. INFEASIBLE and
# PROJECTED are reserved for a repair stage that does not exist yet. Every line of requests.jsonl names the sha256 of
# the line before it, so a line taken out is found (`records`); a line cut from the end is not, without an anchor. API keys are the provider's affair, in its environment; nothing here
# reads one, and nothing of a provider's reaches the browser but the candidates' text and verdicts, and the name, model
# and usage its response gives.
#
# Standard library only. It writes the request records under art/build/studio/ (not committed) and, on the
# designer's admission or rejection, the brief and its ledger, as art/director.py does.

import datetime
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import studio_refs as R   # noqa: E402  (beside this file: the references' geometry and relations, STUDIO-1)
sys.path.insert(0, os.path.join(HERE, "director"))
import durable            # noqa: E402  (the content path's crash-safe writes: the tags file)
import intent as canon    # noqa: E402  (DIRECTOR-0's canonical bytes: the tags file's form)
import ledger as led      # noqa: E402  (the content lock's place: ledger.lock_path)
import studio_marks       # noqa: E402  (MARK-0: the shapes a request names)

REQUEST, RESPONSE, VERSION = "VERDANDI-STUDIO-REQUEST", "VERDANDI-STUDIO-RESPONSE", "0"
REQUEST_VERSION = "1"    # STUDIO-1: the target and the pins, their geometry and relations, in place of one selection
REQUEST_VERSION_SHAPES = "2"   # MARK-0 (0231): version 1 and the shapes the prompt names (#name), each where it is
MAX_PINS = 4
PIECE = re.compile(r"[a-z]+:[0-9a-z,:-]{1,60}\Z")
MENTION = re.compile(r"@([0-9]{1,4})")
NAMESPACES = ("play", "surface", "material", "env", "asset", "view", "layout", "region")
LETTERS = ("A", "B", "C")
TAGS_FORMAT = "VERDANDI-STUDIO-TAGS"
TAG = re.compile(r"@[1-9][0-9]{0,3}\Z")
UNDO_NOTE = "undo of ledger #"
LIMITS = {"prompt": 2000, "title": 80, "rationale": 1200, "revision": 16, "line": 400, "scope": 12, "pattern": 120,
          "preserve": 12, "item": 200, "candidates": 3, "unmet": 6, "questions": 3, "question": 200, "note": 300}
# The capabilities the request publishes (0220): what the art language can make today, and, by name, the closed list of
# what it cannot make yet. A model that proposes nothing because the prompt needs one of the latter names it; the
# names the studio is asked for most become its backlog (`records`), never a gate.
CAPABILITIES = {
    "supported": ["look.material", "look.surface", "look.sky", "look.air", "dressing.canopy", "dressing.tower",
                  "dressing.skyline", "dressing.neon", "dressing.lamp", "dressing.puddle", "view"],
    "unsupported": ["entity.person", "entity.animal", "entity.vehicle", "entity.prop", "entity.vegetation", "motion.path",
                    "motion.surface", "mechanism.door", "mechanism.trigger", "physics.dynamic", "layout.change", "audio",
                    "text.sign", "mesh.import", "effect.particles"],
}
DISPOSITIONS = ("REALIZED", "UNSUPPORTED", "AMBIGUOUS", "DECLINED", "FAILED", "INFEASIBLE", "PROJECTED")
OUTCOME_KINDS = ("none", "unsupported", "ambiguous", "declined")
DECLINE_REASONS = ("content", "rights", "safety", "other")
PATTERN = re.compile(r"[A-Za-z0-9*_.,:-]+(/[A-Za-z0-9*_.,:-]+)*\Z")
CONFIG_KEYS = {"provider", "argv", "model", "timeout_s", "max_output_bytes"}
USAGE_KEYS = {"input_tokens", "output_tokens", "cost_usd", "cost_basis"}
# The validators' sources, whose hashes each request records with its configuration's (B1: the content envelope's
# basis, docs/STUDIO-CONTRACT.md §3). The exporter's hash is already in every intent's base.
VALIDATORS = ("art/director.py", "art/director/scope.py", "art/director/intent.py", "art/check.py")


def basis(cfg):
    """What a verdict on this request depended on, besides its base: the validators' sources and the configuration."""
    def h(p):
        try:
            return sha256(open(p, "rb").read())
        except OSError:
            return ""
    return {"validators": {v: h(os.path.join(REPO, *v.split("/"))) for v in VALIDATORS}, "config_sha256": h(cfg["path"])}

# The response a provider writes: what an adapter constrains a model's output to, where the provider supports it.
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["candidates", "outcome"],
    "properties": {
        "outcome": {
            "type": "object",
            "additionalProperties": False,
            "required": ["kind", "unmet", "questions", "reason", "note"],
            "description": "why there are no candidates, when there are none; kind none when you propose candidates",
            "properties": {
                "kind": {"type": "string", "enum": list(OUTCOME_KINDS),
                         "description": "none: candidates are proposed; unsupported: the prompt needs something the studio cannot make; "
                                        "ambiguous: the prompt can be read several ways and you need the designer's answer; declined: you will not do it"},
                "unmet": {"type": "array", "maxItems": LIMITS["unmet"], "items": {"type": "string", "enum": list(CAPABILITIES["unsupported"])},
                          "description": "for unsupported: what the prompt needs, from the request's list of what the studio cannot make yet"},
                "questions": {"type": "array", "maxItems": LIMITS["questions"], "items": {"type": "string", "maxLength": LIMITS["question"]},
                              "description": "for ambiguous: one to three short questions for the designer"},
                "reason": {"type": "string", "enum": [""] + list(DECLINE_REASONS), "description": "for declined: why"},
                "note": {"type": "string", "maxLength": LIMITS["note"], "description": "one sentence for the designer, or empty"},
            },
        },
        "candidates": {
            "type": "array", "minItems": 0, "maxItems": LIMITS["candidates"],
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title", "rationale", "revision", "scope", "preserve"],
                "properties": {
                    "title": {"type": "string", "minLength": 1, "maxLength": LIMITS["title"],
                              "description": "a few words naming the candidate"},
                    "rationale": {"type": "string", "minLength": 1, "maxLength": LIMITS["rationale"],
                                  "description": "what the change means, in one paragraph"},
                    "revision": {"type": "array", "minItems": 1, "maxItems": LIMITS["revision"],
                                 "items": {"type": "string", "maxLength": LIMITS["line"]},
                                 "description": "art revision lines: '= <statement>' replaces the statement with the same key, "
                                                "'+ <statement>' adds one with a new key, '- <key>' removes one"},
                    "scope": {"type": "array", "minItems": 1, "maxItems": LIMITS["scope"],
                              "items": {"type": "string", "maxLength": LIMITS["pattern"]},
                              "description": "the address patterns the change touches (region/kind/*, material/NAME, ...); "
                                             "everything outside them must stay as it is"},
                    "preserve": {"type": "array", "maxItems": LIMITS["preserve"],
                                 "items": {"type": "string", "maxLength": LIMITS["item"]},
                                 "description": "what the candidate means to keep (the player's route, the supports, ...), in words"},
                },
            },
        },
    },
}


class StudioError(Exception):
    """A refusal, with its code: STUDIO-<WHAT>."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code, self.detail = code, detail


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def language():
    """The art file's statements, as art/README.md describes them (its section "The art file"), for the provider."""
    try:
        text = open(os.path.join(HERE, "README.md"), encoding="utf-8").read()
    except OSError:
        return ""
    a = text.find("## The art file")
    b = text.find("\n## ", a + 1)
    return text[a:b].strip() if a >= 0 else ""


# ------------------------------------------------------------------------------------------------ configuration
def load_config(path):
    """A provider's configuration: {"provider": "cli", "argv": [...], "model": "...", "timeout_s": N, "max_output_bytes": N}.
    "{python}" as an argument is this Python. Refused whole (STUDIO-CONFIG) if any of it is not so."""
    try:
        with open(path, "rb") as fh:
            c = json.loads(fh.read().decode("utf-8"))
    except (OSError, ValueError) as e:
        raise StudioError("STUDIO-CONFIG", "%s cannot be read as JSON (%s)" % (path, e))
    if not isinstance(c, dict) or set(c) != CONFIG_KEYS:
        raise StudioError("STUDIO-CONFIG", "a configuration holds exactly %s" % sorted(CONFIG_KEYS))
    if c["provider"] != "cli":
        raise StudioError("STUDIO-CONFIG", "the provider %r is not one this gateway knows (cli)" % c["provider"])
    if not isinstance(c["argv"], list) or not c["argv"] or not all(isinstance(a, str) and a for a in c["argv"]):
        raise StudioError("STUDIO-CONFIG", "argv is a non-empty list of arguments (no shell line)")
    if not isinstance(c["model"], str) or not c["model"]:
        raise StudioError("STUDIO-CONFIG", "model names what answers, for the record")
    for k, lo, hi in (("timeout_s", 1, 600), ("max_output_bytes", 1024, 4 * 1024 * 1024)):
        if type(c[k]) is not int or not lo <= c[k] <= hi:
            raise StudioError("STUDIO-CONFIG", "%s is a whole number from %d to %d" % (k, lo, hi))
    c = dict(c, argv=[sys.executable if a == "{python}" else a for a in c["argv"]], path=os.path.abspath(path))
    return c


# ------------------------------------------------------------------------------------------------ the provider
def kill_tree(p):
    """The provider and every process it started (a provider may run a model's own command line, which must not outlive
    a cancellation): its process group on POSIX, `taskkill /T` on Windows."""
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True, timeout=15)
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            pass
    try:
        p.kill()
    except OSError:
        pass
    p.wait()


def run_provider(cfg, request_bytes, cancel, holder=None):
    """(standard output, milliseconds, exit status) of the provider for the request, or a StudioError: it cannot start,
    it is cancelled, it runs past its time, it prints more than its limit, it exits with an error (the error's `exit`
    is the status). Its standard error is kept for the message. It runs in a process group of its own, so that what it
    starts is killed with it; `holder["proc"]` is the process while it runs."""
    # its own process group; on Windows without a console window (CREATE_NO_WINDOW), which a studio started from its icon
    # would otherwise open for every console program it runs (claude.exe among them)
    kw = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | 0x08000000} if os.name == "nt" else {"start_new_session": True}
    env = dict(os.environ, **cfg["env"]) if cfg.get("env") else None     # a request's own settings (STUDIO-2: the model it was queued with)
    try:
        p = subprocess.Popen(cfg["argv"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=REPO, shell=False, env=env, **kw)
    except OSError as e:
        raise StudioError("STUDIO-PROVIDER-START", "the provider cannot be started: %s" % e)
    if holder is not None:
        holder["proc"] = p
    out, err, too_long = bytearray(), bytearray(), threading.Event()
    limit = cfg["max_output_bytes"]

    def read_out():
        while True:
            b = p.stdout.read(65536)
            if not b:
                return
            if len(out) + len(b) > limit:
                too_long.set()
                return
            out.extend(b)

    def read_err():
        while True:
            b = p.stderr.read(4096)
            if not b:
                return
            err.extend(b)
            del err[:-4096]

    def write_in():
        try:
            p.stdin.write(request_bytes)
            p.stdin.close()
        except OSError:
            pass

    threads = [threading.Thread(target=f, daemon=True) for f in (read_out, read_err, write_in)]
    for t in threads:
        t.start()
    t0 = time.monotonic()
    why = None
    try:
        while p.poll() is None:
            if cancel.is_set():
                why = StudioError("STUDIO-CANCELLED", "cancelled while the provider ran")
            elif too_long.is_set():
                why = StudioError("STUDIO-RESPONSE-SIZE", "the provider printed more than %d bytes" % limit)
            elif time.monotonic() - t0 > cfg["timeout_s"]:
                why = StudioError("STUDIO-TIMEOUT", "the provider ran past %d s" % cfg["timeout_s"])
            if why:
                kill_tree(p)
                raise why
            time.sleep(0.02)
    finally:
        if holder is not None:
            holder.pop("proc", None)
    for t in threads[:2]:
        t.join(5)
    if cancel.is_set():
        raise StudioError("STUDIO-CANCELLED", "cancelled")
    if too_long.is_set():
        raise StudioError("STUDIO-RESPONSE-SIZE", "the provider printed more than %d bytes" % limit)
    if p.returncode != 0:
        tail = bytes(err).decode("utf-8", "replace").strip().splitlines()[-1:] or ["(nothing on standard error)"]
        e = StudioError("STUDIO-PROVIDER-EXIT", "the provider exited %d: %s" % (p.returncode, tail[0][:300]))
        e.exit = p.returncode
        raise e
    return bytes(out), int((time.monotonic() - t0) * 1000), p.returncode


# ------------------------------------------------------------------------------------------------ the response
def read_response(raw, rid):
    """(provider, candidates, outcome) of a response: the candidates each with exactly its five fields, the outcome the
    model's account of an empty answer (None if the response has none), or STUDIO-RESPONSE-*: the response refused
    whole. provider.stop_reason, when an adapter gives it, is what the adapter observed of its API, not the model's."""
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
        raise StudioError("STUDIO-RESPONSE-JSON", "not JSON in UTF-8 (%s)" % str(e)[:120])
    if not isinstance(doc, dict) or doc.get("format") != RESPONSE or doc.get("version") != VERSION:
        raise StudioError("STUDIO-RESPONSE-FORMAT", "not a %s %s document" % (RESPONSE, VERSION))
    if set(doc) - {"format", "version", "id", "provider", "candidates", "outcome"}:
        raise StudioError("STUDIO-RESPONSE-FIELD", "unknown fields %s" % sorted(set(doc) - {"format", "version", "id", "provider", "candidates", "outcome"}))
    if doc.get("id") != rid:
        raise StudioError("STUDIO-RESPONSE-ID", "the response answers %r, not this request (%s)" % (doc.get("id"), rid))
    prov = doc.get("provider")
    if not isinstance(prov, dict) or not all(isinstance(prov.get(k), str) and prov.get(k) for k in ("name", "model")) or \
            set(prov) - {"usage", "stop_reason"} != {"name", "model"}:
        raise StudioError("STUDIO-RESPONSE-FIELD", "provider is {name, model}, each a non-empty string, and optionally usage and stop_reason")
    if "stop_reason" in prov and not (isinstance(prov["stop_reason"], str) and re.fullmatch(r"[a-z_]{1,40}", prov["stop_reason"])):
        raise StudioError("STUDIO-RESPONSE-FIELD", "provider.stop_reason is a short lower-case word, as the API names it")
    if "usage" in prov:
        u = prov["usage"]
        nat = lambda v: type(v) is int and 0 <= v < 10 ** 9
        if not isinstance(u, dict) or set(u) != USAGE_KEYS or not nat(u["input_tokens"]) or not nat(u["output_tokens"]) or \
                not (u["cost_usd"] is None or type(u["cost_usd"]) in (int, float) and 0 <= u["cost_usd"] < 10 ** 4) or \
                not isinstance(u["cost_basis"], str) or len(u["cost_basis"]) > 120:
            raise StudioError("STUDIO-RESPONSE-FIELD", "provider.usage is {input_tokens, output_tokens, cost_usd (or null), cost_basis}")
    cands = doc.get("candidates")
    if not isinstance(cands, list) or len(cands) > LIMITS["candidates"]:
        raise StudioError("STUDIO-RESPONSE-CANDIDATES", "candidates is a list of at most %d" % LIMITS["candidates"])
    keys = set(SCHEMA["properties"]["candidates"]["items"]["properties"])
    out = []
    for n, c in enumerate(cands):
        where = "candidate %d" % (n + 1)
        if not isinstance(c, dict) or set(c) != keys:
            raise StudioError("STUDIO-RESPONSE-FIELD", "%s holds exactly %s" % (where, sorted(keys)))
        for k in ("title", "rationale"):
            if not isinstance(c[k], str) or not c[k].strip() or len(c[k]) > LIMITS[k] or "\n" in c[k] and k == "title":
                raise StudioError("STUDIO-RESPONSE-FIELD", "%s: %s is a non-empty string of at most %d characters" % (where, k, LIMITS[k]))
        if not isinstance(c["revision"], list) or not 1 <= len(c["revision"]) <= LIMITS["revision"]:
            raise StudioError("STUDIO-RESPONSE-REVISION", "%s: revision is 1 to %d lines" % (where, LIMITS["revision"]))
        for ln in c["revision"]:
            if not isinstance(ln, str) or len(ln) > LIMITS["line"] or ln[:2] not in ("= ", "+ ", "- ") or "\n" in ln or "#" in ln or not ln[2:].strip():
                raise StudioError("STUDIO-RESPONSE-REVISION", "%s: %r is not '= <statement>', '+ <statement>' or '- <key>' on one line" % (where, ln if isinstance(ln, str) else type(ln).__name__))
        if not isinstance(c["scope"], list) or not 1 <= len(c["scope"]) <= LIMITS["scope"] or \
                not all(isinstance(p, str) and len(p) <= LIMITS["pattern"] and PATTERN.match(p) for p in c["scope"]):
            raise StudioError("STUDIO-RESPONSE-SCOPE", "%s: scope is 1 to %d address patterns (region/kind/*, material/NAME, ...)" % (where, LIMITS["scope"]))
        if not isinstance(c["preserve"], list) or len(c["preserve"]) > LIMITS["preserve"] or \
                not all(isinstance(p, str) and p.strip() and len(p) <= LIMITS["item"] for p in c["preserve"]):
            raise StudioError("STUDIO-RESPONSE-FIELD", "%s: preserve is at most %d short strings" % (where, LIMITS["preserve"]))
        out.append(c)
    return doc["provider"], out, read_outcome(doc.get("outcome"))


def read_outcome(o):
    """The model's account of an empty answer, checked whole (STUDIO-RESPONSE-OUTCOME), or None. A capability it names
    must be one the request listed as not yet made; one the studio has, or one it never listed, refuses the response."""
    if o is None:
        return None
    keys = {"kind", "unmet", "questions", "reason", "note"}
    if not isinstance(o, dict) or set(o) != keys or o["kind"] not in OUTCOME_KINDS:
        raise StudioError("STUDIO-RESPONSE-OUTCOME", "outcome holds exactly %s, its kind one of %s" % (sorted(keys), ", ".join(OUTCOME_KINDS)))
    if not isinstance(o["unmet"], list) or len(o["unmet"]) > LIMITS["unmet"] or not all(isinstance(u, str) for u in o["unmet"]):
        raise StudioError("STUDIO-RESPONSE-OUTCOME", "outcome.unmet is at most %d capability names" % LIMITS["unmet"])
    for u in o["unmet"]:
        if u in CAPABILITIES["supported"]:
            raise StudioError("STUDIO-RESPONSE-OUTCOME", "outcome.unmet names %s, which the studio can make: the answer contradicts the request's own list" % u)
        if u not in CAPABILITIES["unsupported"]:
            raise StudioError("STUDIO-RESPONSE-OUTCOME", "outcome.unmet names %r, which the request never listed" % u[:40])
    if not isinstance(o["questions"], list) or len(o["questions"]) > LIMITS["questions"] or \
            not all(isinstance(q, str) and q.strip() and len(q) <= LIMITS["question"] for q in o["questions"]):
        raise StudioError("STUDIO-RESPONSE-OUTCOME", "outcome.questions is at most %d short questions" % LIMITS["questions"])
    if o["reason"] not in ("",) + DECLINE_REASONS or not isinstance(o["note"], str) or len(o["note"]) > LIMITS["note"]:
        raise StudioError("STUDIO-RESPONSE-OUTCOME", "outcome.reason is one of %s or empty; outcome.note at most %d characters" % (", ".join(DECLINE_REASONS), LIMITS["note"]))
    return {"kind": o["kind"], "unmet": sorted(set(o["unmet"])), "questions": [" ".join(q.split()) for q in o["questions"]],
            "reason": o["reason"], "note": " ".join(o["note"].split())}


def disposition(provider, cands, outcome):
    """What a request that came back came to (0220). The host decides first: an API's reported refusal is DECLINED
    whatever else came; candidates are REALIZED. With none, the model's account is read, as its claim: UNSUPPORTED with
    the capabilities it needs, AMBIGUOUS with its questions, DECLINED with its reason; anything else is FAILED, an
    empty answer with no reason."""
    if provider.get("stop_reason") == "refusal":
        return {"kind": "DECLINED", "decided_by": "host", "code": "API-REFUSAL",
                "detail": "the provider's API reported a refusal (stop_reason refusal); nothing of its answer is read"}
    claim = outcome if outcome and outcome["kind"] != "none" else None
    if cands:
        d = {"kind": "REALIZED", "decided_by": "host", "code": "", "detail": "%d candidate%s" % (len(cands), "" if len(cands) == 1 else "s")}
        if claim:
            d["claim"] = claim                        # candidates came with an account of none: recorded, not acted on
        return d
    k = claim["kind"] if claim else "none"
    if k == "unsupported" and claim["unmet"]:
        return {"kind": "UNSUPPORTED", "decided_by": "provider", "code": "", "unmet": claim["unmet"], "note": claim["note"],
                "detail": "the studio cannot make %s yet (the provider's account; each is on the studio's own list of what it cannot make)" % ", ".join(claim["unmet"])}
    if k == "ambiguous" and claim["questions"]:
        return {"kind": "AMBIGUOUS", "decided_by": "provider", "code": "", "questions": claim["questions"], "note": claim["note"],
                "detail": "the director asks: " + " / ".join(claim["questions"])}
    if k == "declined" and claim["reason"]:
        return {"kind": "DECLINED", "decided_by": "provider", "code": "MODEL-DECLINED", "reason": claim["reason"], "note": claim["note"],
                "detail": "the model declined (%s)%s" % (claim["reason"], ": " + claim["note"] if claim["note"] else "")}
    return {"kind": "FAILED", "decided_by": "host", "code": "STUDIO-EMPTY-WITHOUT-REASON",
            "detail": "the provider answered with no candidates and no reason%s" % (" (its account: %s, with nothing to show for it)" % k if claim else "")}


def intent_doc(c, letter, brief, base, prompt):
    """A candidate as a VERDANDI-INTENT: the letter, the base and the prompt are the gateway's; the title, the
    rationale, the revision and the scope the provider's. The layout is empty: STUDIO-0 changes the look alone."""
    rationale = " ".join((c["title"].strip() + ". " + c["rationale"].strip()).split())
    if c["preserve"]:
        rationale += " Keeps: " + "; ".join(" ".join(p.split()) for p in c["preserve"]) + "."
    return {"base": dict(base), "brief": brief, "candidate": letter, "format": "VERDANDI-INTENT", "layout": [],
            "prompt": prompt, "rationale": rationale, "revision": [" ".join(ln.split()) if ln[0] != "-" else "- " + " ".join(ln[2:].split()) for ln in c["revision"]],
            "scope": list(c["scope"]), "version": "0"}


def last_line(path):
    """(the last line's bytes, whether the file ends without a newline), or (None, False) for an empty or absent file."""
    try:
        with open(path, "rb") as fh:
            fh.seek(0, 2)
            n = fh.tell()
            if n == 0:
                return None, False
            back = min(n, 1 << 20)
            fh.seek(n - back)
            data = fh.read()
    except OSError:
        return None, False
    torn = not data.endswith(b"\n")
    lines = data.split(b"\n")
    if not torn:
        lines = lines[:-1]
    return lines[-1], torn


def verify_records(path):
    """The request record read back (0220): every chained line must name the sha256 of the line before it. Returns
    {lines, legacy (lines before the chain began), unreadable, breaks [line numbers], dispositions {kind: n}, unmet {name: n}}.
    A line removed from the middle is a break; lines cut from the end are not found without an anchor kept elsewhere."""
    out = {"lines": 0, "legacy": 0, "unreadable": [], "breaks": [], "dispositions": {}, "unmet": {}}
    try:
        raw = open(path, "rb").read()
    except OSError:
        return out
    lines = raw.split(b"\n")
    if lines and lines[-1] == b"":
        lines = lines[:-1]
    chained = False
    for i, ln in enumerate(lines):
        out["lines"] += 1
        try:
            e = json.loads(ln)
        except ValueError:
            out["unreadable"].append(i + 1)
            continue
        if not isinstance(e, dict):
            out["unreadable"].append(i + 1)
            continue
        if "prev" not in e:
            if chained:
                out["breaks"].append(i + 1)          # a line without its link, after the chain began
            else:
                out["legacy"] += 1
        else:
            chained = True
            want = sha256(lines[i - 1]) if i > 0 else ""
            if e["prev"] != want:
                out["breaks"].append(i + 1)
        d = e.get("disposition")
        if isinstance(d, dict) and d.get("kind") in DISPOSITIONS:
            out["dispositions"][d["kind"]] = out["dispositions"].get(d["kind"], 0) + 1
            for u in d.get("unmet") or []:
                out["unmet"][u] = out["unmet"].get(u, 0) + 1
    return out


# ------------------------------------------------------------------------------------------------ the gateway
class Gateway:
    """One brief's director gateway. `play` gives what the gateway needs of art/play.py: director() (the director
    module), workspace() (the brief's Workspace), candidate_slot(ws, intent_dict, label) (a candidate evaluated at the
    current head: a play.py source, served or refused), and publish(slots) (the candidates the page can switch to)."""

    def __init__(self, play, brief, cfg=None, root=REPO, say=print, origin="page"):
        self.play, self.brief, self.cfg, self.root, self.say, self.origin = play, brief, cfg, root, say, origin
        self.lock = threading.Lock()
        self.req = None          # the latest request: dict, see state()
        self.cancel = None       # its cancellation event
        self.n = 0
        self.last = {}           # the last admission, rejection or undo, for the page
        self.records = os.path.join(root, "art", "build", "studio", brief)
        self.error = ""          # why there is no provider, when a configuration was refused
        self.running = {}        # the provider's process while it runs (run_provider's holder)
        # the references (STUDIO-1): a tag names one object, by its id; it is bound to the scene and head it was last
        # selected or pinned at, and never moved to another object. B1 (docs/STUDIO-CONTRACT.md §9): the studio's tags
        # are kept in <root>/art/ledger/<brief>.tags.json, so a restart keeps them; the counter only grows, a tag is
        # never reused, and a tag whose object is gone stays, listed apart. A probe's gateway keeps none.
        self.tags = {}           # "@n" -> {tag, piece, address, kind, scene, head, fingerprint, statement, size_m}
        self.tag_of = {}         # object id -> "@n"
        self.next_tag = 1
        self.target = None       # the tag E selected
        self.pins = []           # the tags R pinned, at most MAX_PINS
        self.tags_path = os.path.join(root, "art", "ledger", brief + ".tags.json") if origin == "page" else None
        self.tags_error = ""
        if self.tags_path and os.path.exists(self.tags_path):
            try:
                self._load_tags()
            except (OSError, ValueError, KeyError, TypeError, canon.IntentError) as e:
                self.tags_error = "the tags file %s was not read (%s); tags start again from @%d and the file is kept as it is" % (
                    os.path.relpath(self.tags_path, root), str(e)[:120], self.next_tag)
                self.tags_path = None    # never overwrite a file this gateway could not read

    def _load_tags(self):
        raw = open(self.tags_path, "rb").read()
        d = canon.loads(raw[:-1] if raw.endswith(b"\n") else raw)     # one canonical document and its LF
        if d.get("format") != TAGS_FORMAT or d.get("version") != "0" or d.get("brief") != self.brief:
            raise ValueError("not a %s 0 file of brief %s" % (TAGS_FORMAT, self.brief))
        nxt = canon.integer(d["next"], "next")
        tags, tag_of = {}, {}
        for t in d["tags"]:
            if not TAG.match(t["tag"]) or not PIECE.match(t["piece"]) or int(t["tag"][1:]) >= nxt or t["tag"] in tags or t["piece"] in tag_of:
                raise ValueError("a tag entry that is not one object's tag below next: %r" % (t,))
            tags[t["tag"]] = {"tag": t["tag"], "piece": t["piece"], "address": t["address"], "kind": t["kind"], "scene": t["scene"], "head": "",
                              "fingerprint": "", "statement": None, "size_m": []}
            tag_of[t["piece"]] = t["tag"]
        self.tags, self.tag_of, self.next_tag = tags, tag_of, nxt

    def _save_tags(self):
        """Write the tags file whole (a temporary file, flushed, renamed over it). Holds the lock."""
        if not self.tags_path:
            return
        doc = {"format": TAGS_FORMAT, "version": "0", "brief": self.brief, "next": str(self.next_tag),
               "tags": [{"tag": t["tag"], "piece": t["piece"], "address": t["address"], "kind": t["kind"], "scene": t["scene"]}
                        for t in sorted(self.tags.values(), key=lambda x: int(x["tag"][1:]))]}
        try:                 # the content lock, as every writer of art/ledger/ holds it: a recovery sweeping that folder
            with durable.locked(led.lock_path(self.tags_path)):           # never removes this write's temporary
                durable.write(self.tags_path, canon.dumps(doc) + b"\n")
        except durable.Busy:
            raise StudioError("STUDIO-BUSY", "the tags were not saved: another writer held the content lock for the whole wait; try again")

    def shutdown(self):
        """Cancel the request running, and kill its provider and what it started (play.py, stopping)."""
        with self.lock:
            if self.cancel is not None:
                self.cancel.set()
        p = self.running.get("proc")
        if p is not None and p.poll() is None:
            kill_tree(p)

    # ------------------------------------------------------------------ what the page reads
    def state(self):
        with self.lock:
            r = self.req
            prov = {"configured": self.cfg is not None, "model": self.cfg["model"] if self.cfg else "", "error": self.error,
                    "config": os.path.basename(self.cfg["path"]) if self.cfg else ""}
            req = None
            if r:
                req = {k: r[k] for k in ("id", "state", "prompt", "message", "code", "references", "head", "provider")}
                req["shapes"] = r.get("shapes", [])
                req["disposition"] = r.get("disposition")
                req["elapsed_ms"] = int(((r["ended"] or time.monotonic()) - r["started"]) * 1000)
                req["candidates"] = [dict({k: c[k] for k in ("letter", "title", "verdict", "codes", "message", "slot", "decided", "head", "touches")},
                                          record=c.get("record"), still={k: c["still"][k] for k in ("sha256", "detectors", "flags")} if c.get("still") else None)
                                     for c in r["candidates"]]
            last = dict(self.last)
        return {"provider": prov, "request": req, "last": last, "refs": self.refs()}

    # ------------------------------------------------------------------ the references (STUDIO-1)
    def _head(self):
        D = self.play.director()
        ws = self.play.workspace()
        out, parts, _checks = ws.export()
        return ws, out, parts, D.canon.head(parts)

    @staticmethod
    def _root(piece, O):
        """The object a picked box belongs to: itself, or the object whose id it extends (a canopy's rib, a light)."""
        r = piece
        while r not in O and r.count(":") >= 2:
            r = r.rsplit(":", 1)[0]
        return r if r in O else None

    @staticmethod
    def _statement(out, o):
        st = [x for x in out["lineage"]["statements"] if x["hash"] == o["by"]]
        return {"line": st[0]["line"], "text": st[0]["text"], "key": st[0]["key"]} if st else None

    def _resolve(self, piece):
        if not isinstance(piece, str) or not PIECE.match(piece):
            raise StudioError("STUDIO-SELECTION", "a piece is named by its id (kind:place)")
        ws, out, parts, head = self._head()
        O = R.objects(out["scene"])
        root = self._root(piece, O)
        if root is None:
            raise StudioError("STUDIO-SELECTION", "the piece %r is not in the brief's scene at the head" % piece)
        return out, head, O, root

    def _bind(self, out, head, o):
        """The object's tag, made if it has none; bound (again) to this scene and head. Holds the lock."""
        tag = self.tag_of.get(o["id"])
        new = tag is None
        if new:                  # tag ??= next(): made at the first touch, never reassigned, never reused
            tag = "@%d" % self.next_tag
            self.next_tag += 1
            self.tag_of[o["id"]] = tag
        self.tags[tag] = {"tag": tag, "piece": o["id"], "address": R.address(o), "kind": o["kind"], "scene": out["lineage"]["scene_sha256"],
                          "head": head, "fingerprint": R.fingerprint(o), "statement": self._statement(out, o), "size_m": R.geometry(o)["size_m"]}
        if new:
            self._save_tags()
        return tag

    def select(self, piece):
        """E: the object of the picked box becomes the target (and is no longer a pin); None clears the target."""
        if piece is None:
            with self.lock:
                self.target = None
            return self.refs()
        out, head, O, root = self._resolve(piece)
        with self.lock:
            tag = self._bind(out, head, O[root])
            if tag in self.pins:
                self.pins.remove(tag)
            self.target = tag
        return self.refs()

    def pin(self, piece):
        """R: the object of the picked box pinned as a reference, or unpinned if it was; at most MAX_PINS."""
        out, head, O, root = self._resolve(piece)
        with self.lock:
            tag = self.tag_of.get(root)
            if tag is not None and tag in self.pins:
                self.pins.remove(tag)
                return self.refs(locked=True)
            if tag is not None and tag == self.target:
                raise StudioError("STUDIO-REFERENCE", "%s is the target: E selects another target, R pins a reference" % tag)
            if len(self.pins) >= MAX_PINS:
                raise StudioError("STUDIO-PINS", "%d pins at most: unpin one first" % MAX_PINS)
            tag = self._bind(out, head, O[root])
            self.pins.append(tag)
            return self.refs(locked=True)

    def unpin(self, tag):
        with self.lock:
            if tag not in self.pins:
                raise StudioError("STUDIO-REFERENCE", "%r is not pinned" % (tag,))
            self.pins.remove(tag)
            return self.refs(locked=True)

    def refs(self, locked=False):
        """The target and the pins, each with what it names and how it stands in the scene the page is served now:
        "ok", "changed" since it was bound (the same object, another shape or look), or "gone" (no object of its id)."""
        scene = getattr(self.play, "scene0", lambda: (None, None))()[1]
        O = R.objects(scene) if scene is not None else None

        def item(tag, role):
            t = self.tags[tag]
            o = O.get(t["piece"]) if O is not None else None
            status = "unknown" if O is None else "gone" if o is None else "changed" if R.fingerprint(o) != t["fingerprint"] else "ok"
            return {"tag": tag, "role": role, "piece": t["piece"], "address": t["address"], "kind": t["kind"], "size_m": t["size_m"],
                    "statement": t["statement"], "bound_scene": t["scene"], "status": status}

        def build():
            known = [{"tag": t["tag"], "piece": t["piece"], "kind": t["kind"], "address": t["address"],
                      "present": None if O is None else t["piece"] in O} for t in sorted(self.tags.values(), key=lambda x: int(x["tag"][1:]))]
            return {"target": self.target, "pins": list(self.pins), "max_pins": MAX_PINS,
                    "items": ([item(self.target, "target")] if self.target else []) + [item(t, "pin") for t in self.pins],
                    "known": known, "kept": bool(self.tags_path), "tags_error": self.tags_error}
        if locked:
            return build()
        with self.lock:
            return build()

    def references(self, out, head, prompt, given=None):
        """The request's references at the head as the files stand: the target and the pins, each with its identity,
        its statement, what that statement can change, its geometry and its nearest wall; the relations between every
        two of them; the tags the prompt mentions. A tag the prompt mentions that is neither the target nor a pin, or
        a tag whose object is not in the scene at the head, refuses the request (STUDIO-REFERENCE): a tag is never
        moved to another object."""
        S = out["scene"]
        O = R.objects(S)
        with self.lock:
            if given is not None:            # the references a queued task was made with
                target, pins = given[0], list(given[1])
                gone = [t for t in ([target] if target else []) + pins if t not in self.tags]
                if gone:
                    raise StudioError("STUDIO-REFERENCE", "the task names %s, which no object of this world has now" % ", ".join(gone))
            else:
                target, pins = self.target, list(self.pins)
            active = ([target] if target else []) + pins
            recs = {t: dict(self.tags[t]) for t in active}
        mentions = []
        for m in MENTION.findall(prompt):
            t = "@" + str(int(m))
            if t not in mentions:
                mentions.append(t)
        for t in mentions:
            if t not in active:
                with self.lock:
                    k = dict(self.tags[t]) if t in self.tags else None
                now = ", ".join("%s %s" % (a, "target" if a == target else "pin") for a in active) or "none"
                if k is None:
                    raise StudioError("STUDIO-REFERENCE", "the prompt names %s, but no object has that tag (this request's: %s)" % (t, now))
                gone = "" if k["piece"] in O else "; it is not in the scene at the head"
                raise StudioError("STUDIO-REFERENCE", "the prompt names %s, the %s %s, which is not the target or a pin of this request "
                                  "(%s)%s. Pin it (R on it) or make it the target (E), then ask again" % (t, k["kind"], k["address"], now, gone))
        refs = []
        for t in active:
            rec = recs[t]
            o = O.get(rec["piece"])
            if o is None:
                raise StudioError("STUDIO-REFERENCE", "%s (%s) is not in the scene at the head; it was bound at scene %s. Unpin it, or "
                                  "select or pin what stands there now" % (t, rec["piece"], rec["scene"][:12]))
            region, kind = o["region"], o["kind"]
            refs.append({"tag": t, "role": "target" if t == target else "pin", "mentioned": t in mentions, "piece": o["id"],
                         "address": R.address(o), "kind": kind, "region": region, "material": o["material"],
                         "statement": self._statement(out, o), "statement_makes": sum(1 for x in O.values() if x["by"] == o["by"]),
                         "changeable": R.CHANGEABLE.get(kind, ""),
                         "patterns": ["%s/%s/*" % (region, kind)] + (["material/%s" % o["material"]] if o["material"] else []),
                         "geometry": R.geometry(o), "nearest_wall": R.nearest_wall(o, S),
                         "bound": {"scene": rec["scene"], "head": rec["head"], "changed_since": R.fingerprint(o) != rec["fingerprint"]}})
        rels = [R.relation(O[a["piece"]], O[b["piece"]], a["tag"], b["tag"]) for i, a in enumerate(refs) for b in refs[i + 1:]]
        return refs, rels, mentions, O

    def shapes_of(self, prompt, out, O):
        """MARK-0 (0231): the shapes the prompt names (#name), each as the director reads it: where it is on the world as
        the files stand (its face, its vertices in the face's frame and in the world, its area), the object it is drawn on
        and the statement that made that object, the host's checks, and the designer's words. A name no shape has, or a
        shape that is not as it was marked (changed, gone), refuses the request (STUDIO-SHAPE): a shape is never moved to
        another surface."""
        names = studio_marks.mentions(prompt)
        if not names:
            return []
        store = getattr(self.play, "shapes", lambda: None)()
        if store is None:
            raise StudioError("STUDIO-SHAPE", "the prompt names %s, but this studio keeps no shapes" % ", ".join("#" + n for n in names))
        try:
            got = store.resolve(names, out["scene"])
        except studio_marks.ShapeError as e:
            raise StudioError(e.code, e.detail)
        res = []
        for ev in got:
            piece = ev["piece"]
            if piece.startswith("play:"):
                c = next(c for c in out["scene"]["collision"] if c["id"] == piece[5:])
                on = {"layer": "play", "kind": c["kind"], "address": "play/%s/%s" % (c["kind"], c["id"]), "material": c["material"],
                      "statement": None, "changeable": "nothing: the play geometry is the map's; an opening or an addition in it is a layout "
                                                        "change, which the art cannot make (layout.change)", "patterns": []}
            else:
                root = piece
                while root not in O and root.count(":") >= 2:
                    root = root.rsplit(":", 1)[0]
                o = O[root]
                on = {"layer": "dressing", "kind": o["kind"], "address": R.address(o), "object": o["id"], "material": o["material"],
                      "statement": self._statement(out, o), "statement_makes": sum(1 for x in O.values() if x["by"] == o["by"]),
                      "changeable": R.CHANGEABLE.get(o["kind"], ""),
                      "patterns": ["%s/%s/*" % (o["region"], o["kind"])] + (["material/%s" % o["material"]] if o["material"] else [])}
            r3 = lambda v: round(float(v) + 0.0, 3)
            res.append({"name": ev["name"], "operation": ev["operation"], "meaning": studio_marks.OPERATIONS[ev["operation"]],
                        "closed": ev["closed"], "on": dict(on, piece=piece, face=ev["face"]), "status": ev["status"],
                        "face": {"width_m": r3(ev["face_m"]["width"]), "height_m": r3(ev["face_m"]["height"]), "normal": ev["face_m"]["normal"],
                                 "origin_m": [r3(x) for x in ev["face_m"]["origin"]], "u": ev["face_m"]["u"], "v": ev["face_m"]["v"]},
                        "vertices_m": ev["vertices_m"], "world_m": [[r3(x) for x in p_] for p_ in ev["world_m"]],
                        "area_m2": r3(ev["area_m2"]) if "area_m2" in ev else None,
                        "checks": {k: {"ok": c["ok"], "detail": c["detail"]} for k, c in sorted(ev["checks"].items())},
                        "words": ev["words"], "note": ev["note"],
                        "basis": "the shape is the designer's mark, not the world: its vertices are exact (millimetres on the face); the checks "
                                 "are the studio's; the words are the designer's and nothing checks them"})
        return res

    @staticmethod
    def touches(slot, refs, O):
        """Which of the request's objects a candidate changed, and how many others, from the director's own account of
        what it realized and affected: the measure of whether a model changed the objects it was asked about."""
        ids = set()
        for a in list(slot.get("realized") or []) + list(slot.get("affected") or []):
            segs = a.split("/")
            if len(segs) != 3 or segs[0] in NAMESPACES:
                continue
            i = segs[1] + ":" + segs[2]
            r = i
            while r not in O and r.count(":") >= 2:
                r = r.rsplit(":", 1)[0]
            ids.add(r if r in O else i)
        tagged = {t: ("changed" if p in ids else "unchanged") for t, p in refs.items()}
        # an object of the head that is not tagged, changed or removed; and an object the candidate makes that the head
        # has not (an object's id is its cells, so a slab given new corners is a new object, and its old self is changed)
        others = sorted(i for i in ids - set(refs.values()) if i in O)
        added = sorted(i for i in ids if i not in O)
        return {"tags": tagged, "others": others[:12], "others_count": len(others), "added": added[:12], "added_count": len(added),
                "materials": list(slot.get("materials_changed") or [])}

    # ------------------------------------------------------------------ a request
    def ask(self, prompt, piece=None, camera=None, refs=None, cfg=None):
        """Start a request; it cancels the one before it. Returns the request's id, or raises StudioError at once
        (no provider, an empty prompt, an unknown piece, a reference that names nothing). `piece`, if given, is selected
        first as the target (E does it in the page). STUDIO-2, for the queue: `refs` (target tag, [pin tags]) are the
        references the task was queued with, in place of the page's present ones; `cfg` the provider it was queued with."""
        cfg = cfg or self.cfg
        if cfg is None:
            raise StudioError("STUDIO-NO-PROVIDER", "no director is configured: start play.py with --director CONFIG.json (art/STUDIO.md)")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > LIMITS["prompt"]:
            raise StudioError("STUDIO-PROMPT", "a prompt is 1 to %d characters" % LIMITS["prompt"])
        cam = {}
        for k in ("x", "y", "z", "yaw_deg", "pitch_deg"):
            v = (camera or {}).get(k)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or v != v or v in (float("inf"), float("-inf")):
                cam = None
                break
            cam[k] = round(float(v), 3)
        if piece is not None:
            self.select(piece)
        ws, out, parts, head = self._head()
        stmts = [{"line": x["line"], "text": x["text"], "key": x["key"]} for x in out["lineage"]["statements"]]
        refs, rels, mentions, O = self.references(out, head, prompt, refs)
        S = out["scene"]
        shapes = self.shapes_of(prompt, out, O)
        target = refs[0] if refs and refs[0]["role"] == "target" else None
        with self.lock:
            if self.req and self.req["state"] == "running":
                self.cancel.set()
                self.req["state"], self.req["code"], self.req["message"] = "superseded", "STUDIO-SUPERSEDED", "a newer request was asked"
                self.req["ended"] = time.monotonic()
            self.n += 1
            rid = "%s-%s%d" % (datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S"), "" if self.origin == "page" else self.origin + "-", self.n)
            base = {k: parts[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}
            request = {"format": REQUEST, "version": REQUEST_VERSION_SHAPES if shapes else REQUEST_VERSION, "id": rid, "brief": self.brief, "head": head, "base": base,
                       "prompt": prompt.strip(), "target": target, "references": refs, "relations": rels, "mentions": mentions,
                       "coordinates": "%s; a cell is %g m; the walls of the play geometry are %g m high; a box is [x0, y0, z0, x1, y1, z1]" % (
                           S["units"], S["grid"]["cell"], S["grid"]["wall"]),
                       "camera": cam, "statements": stmts,
                       "revision_syntax": "'= <statement>' replaces the brief's statement with the same key; '+ <statement>' adds one "
                                          "whose key is new; '- <key>' removes one. A statement's key: its verb (or the verb and its "
                                          "first word; a canopy adds its two corner cells), as the statements' keys show.",
                       "language": language(),
                       "capabilities": CAPABILITIES,
                       "respond": {"format": RESPONSE, "version": VERSION, "id": rid, "max_candidates": LIMITS["candidates"], "schema": SCHEMA}}
            if shapes:
                request["shapes"] = shapes
            self.req = {"id": rid, "state": "running", "prompt": prompt.strip(), "message": "", "code": "", "shapes": [s["name"] for s in shapes],
                        "references": {r["tag"]: {"role": r["role"], "piece": r["piece"], "address": r["address"]} for r in refs},
                        "selection": target["address"] if target else None,
                        "head": head, "provider": {"model": cfg["model"]}, "candidates": [], "started": time.monotonic(),
                        "ended": None, "base": base, "objects": O, "cfg": cfg}
            self.cancel = threading.Event()
            req, cancel = self.req, self.cancel
        self.play.publish([])
        threading.Thread(target=self._run, args=(req, request, cancel, ws), daemon=True).start()
        return rid

    def restore(self, rid):
        """STUDIO-2: draw again the candidates a finished request recorded (its A, B, C intents), each evaluated at the head
        as the files stand now — after a restart, or when the person reviews a queued task after others ran for this
        world. A candidate written against an older head is re-evaluated, never trusted (HEAD-MOVED in its codes), and is
        admitted, as any other, only at the head it is drawn at. Returns the request's id; refuses while one runs."""
        d = os.path.join(self.records, rid)
        if not re.match(r"[0-9TZ:-]{8,40}\Z", rid or "") or not os.path.exists(os.path.join(d, "request.json")):
            raise StudioError("STUDIO-NO-CANDIDATE", "no recorded request %r" % rid)
        with self.lock:
            if self.req and self.req["state"] == "running":
                raise StudioError("STUDIO-BUSY", "a request for this world is running (%s): review when it ends" % self.req["id"])
        request = json.loads(open(os.path.join(d, "request.json"), "rb").read().decode("utf-8"))
        titles = {}
        try:
            for ln in open(os.path.join(self.records, "requests.jsonl"), "rb").read().splitlines():
                e = json.loads(ln)
                if e.get("id") == rid and e.get("candidates"):
                    titles = {c["letter"]: c["title"] for c in e["candidates"]}
        except (OSError, ValueError):
            pass
        D = self.play.director()
        ws, out, parts, head = self._head()
        O = R.objects(out["scene"])
        refs = {r["tag"]: r["piece"] for r in request.get("references", [])}
        made = []
        for letter in LETTERS:
            f = os.path.join(d, letter + ".intent")
            if not os.path.exists(f):
                continue
            raw_intent = open(f, "rb").read()
            item = {"letter": letter, "title": titles.get(letter, letter), "verdict": "", "codes": [], "message": "", "slot": None,
                    "decided": "", "head": "", "intent": raw_intent, "touches": None, "record": None, "still": None}
            slot = self.play.candidate_slot(ws, D.canon.load_intent(raw_intent), "studio %s %s: %s (drawn again)" % (rid, letter, item["title"]))
            item.update({"verdict": slot.get("verdict", "") or "REFUSED", "codes": slot.get("codes", []), "message": slot["message"],
                         "head": slot.get("checked_against", ""), "touches": self.touches(slot, refs, O) if "realized" in slot else None,
                         "record": slot.get("record")})
            made.append((item, slot if slot["ok"] else None))
        drawn = [(i, s) for i, s in made if s is not None]
        slots = self.play.publish([s for _i, s in drawn])
        for (item, _s), k in zip(drawn, slots):
            item["slot"] = k
        # MARK-0: a recorded request's shapes are read again against the head: one that is not as it was marked is said
        stale = []
        store = getattr(self.play, "shapes", lambda: None)()
        for s in request.get("shapes", []):
            st = "gone"
            if store is not None:
                got = [x for x in store.state(out["scene"])["shapes"] if x["name"] == s.get("name")]
                st = got[0]["status"] if got else "gone"
            if st != "ok":
                stale.append("#%s is %s now" % (s.get("name"), st))
        with self.lock:
            self.req = {"id": rid, "state": "done", "prompt": request.get("prompt", ""), "code": "", "restored": True,
                        "shapes": [s.get("name") for s in request.get("shapes", [])],
                        "message": "%d candidate%s drawn again at the head as it is now%s%s" % (
                            len(drawn), "" if len(drawn) == 1 else "s", "" if request.get("head") == head else " (the world moved since it was asked)",
                            "; " + ", ".join(stale) if stale else ""),
                        "references": {r["tag"]: {"role": r["role"], "piece": r["piece"], "address": r["address"]} for r in request.get("references", [])},
                        "selection": (request.get("target") or {}).get("address"), "head": head, "provider": {"model": "recorded"},
                        "candidates": [i for i, _s in made], "started": time.monotonic(), "ended": time.monotonic(),
                        "base": {k: parts[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}, "objects": O, "cfg": self.cfg}
        return rid

    def cancel_request(self, rid):
        with self.lock:
            if self.req and self.req["id"] == rid and self.req["state"] == "running":
                self.cancel.set()
                self.req["state"], self.req["code"], self.req["message"] = "cancelled", "STUDIO-CANCELLED", "cancelled by the designer"
                self.req["ended"] = time.monotonic()
                return True
        return False

    def _record(self, rid, name, data):
        d = os.path.join(self.records, rid)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, name), "wb") as fh:
            fh.write(data)

    def _log(self, entry):
        # one line at a time: the request's thread, a superseded request's and the page's admissions all record here, and
        # on Windows an append is the C runtime's seek to the end, then a write — two at once can land on one offset, the
        # later line over the earlier (git for Windows: "Windows does support atomic O_APPEND semantics using the file
        # access mode FILE_APPEND_DATA", which open() does not use)
        # 0220: each line names the sha256 of the line before it, so a line taken out of the record is found (`records`)
        with LOG_LOCK:
            os.makedirs(self.records, exist_ok=True)
            path = os.path.join(self.records, "requests.jsonl")
            prev, torn = last_line(path)
            line = json.dumps(dict(entry, prev=sha256(prev) if prev is not None else ""), sort_keys=True, separators=(",", ":"),
                              ensure_ascii=True).encode("ascii") + b"\n"
            with open(path, "ab") as fh:
                fh.write((b"\n" if torn else b"") + line)    # a torn last line stays a line of its own, which `records` reports

    def _finish(self, req, state, code="", message="", disp=None):
        with self.lock:
            if req["state"] != "running":      # cancelled or superseded meanwhile: its result is discarded
                return False
            req["state"], req["code"], req["message"], req["ended"] = state, code, message, time.monotonic()
            req["disposition"] = disp
            return True

    def _run(self, req, request, cancel, ws):
        rid = req["id"]
        rb = (json.dumps(request, sort_keys=True, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
        self._record(rid, "request.json", rb)
        entry = {"id": rid, "at": now(), "brief": self.brief, "head": req["head"], "prompt": req["prompt"],
                 "selection": req["selection"], "references": {t: r["piece"] for t, r in req["references"].items()},
                 "config": req["cfg"]["path"], "model": req["cfg"]["model"], "request_sha256": sha256(rb), "basis": basis(req["cfg"])}
        if req["cfg"].get("env"):
            entry["settings"] = dict(req["cfg"]["env"])
        if req.get("shapes"):
            entry["shapes"] = list(req["shapes"])
        if self.origin != "page":
            entry["origin"] = self.origin
        # what the owner asked to be recorded of every call (2026-10-11): the provider, the model, the exit status, whether
        # the response was valid, the latency; and the tokens and cost the provider reports. No credential is in any of it.
        try:
            raw, ms, rc = run_provider(req["cfg"], rb, cancel, self.running)
            self._record(rid, "response.raw", raw)
            entry.update({"response_sha256": sha256(raw), "provider_ms": ms, "exit": rc})
            provider, cands, outcome = read_response(raw, rid)
            entry.update({"provider": provider, "valid": True})
            if "usage" in provider:
                entry["usage"] = provider["usage"]
        except StudioError as e:
            entry.update({"outcome": e.code, "detail": str(e)[:300]})
            if hasattr(e, "exit"):
                entry["exit"] = e.exit
            if e.code.startswith("STUDIO-RESPONSE-"):
                entry["valid"] = False
            # the record first, then the state: a request reads as ended only once its line is in the record (his run of
            # 0223's self-test: a reader of the record after the request ended found no line, 1 run in 4 here)
            if e.code != "STUDIO-CANCELLED":
                disp = {"kind": "FAILED", "decided_by": "host", "code": e.code, "detail": e.detail[:300]}
                entry["disposition"] = disp
                self._log(entry)
                self._finish(req, "failed", e.code, e.detail, disp)
            else:
                self._log(entry)
            self.say("STUDIO  %s  %s: %s" % (rid, e.code, e.detail[:200]))
            return
        disp = disposition(provider, cands, outcome)
        entry["disposition"] = disp
        if disp["kind"] != "REALIZED":
            cands = []                                   # a reported refusal: nothing of the answer is read
        with self.lock:
            if req["state"] != "running":
                entry.update({"outcome": req["code"] or "STUDIO-DISCARDED", "detail": "the response came after the request was %s" % req["state"]})
                self._log(entry)
                return
            req["provider"] = provider
        if disp["kind"] != "REALIZED":
            # an answer without candidates: nothing to evaluate, nothing drawn, the world as it was; said and recorded
            entry["outcome"] = disp["kind"]
            self._log(entry)
            if disp["kind"] == "FAILED":
                self._finish(req, "failed", disp["code"], disp["detail"], disp)
            else:
                self._finish(req, "done", "", "%s: %s" % (disp["kind"], disp["detail"]), disp)
            self.say("STUDIO  %s  %s (%s)  %s: %s" % (rid, provider["name"], provider["model"], disp["kind"], disp["detail"][:200]))
            return
        D = self.play.director()
        made = []
        for letter, c in zip(LETTERS, cands):
            doc = intent_doc(c, letter, self.brief, req["base"], req["prompt"])
            item = {"letter": letter, "title": c["title"].strip(), "verdict": "", "codes": [], "message": "", "slot": None,
                    "decided": "", "head": "", "intent": None, "touches": None, "record": None, "still": None}
            try:
                raw_intent = D.canon.dumps(doc)
                D.canon.load_intent(raw_intent)
            except D.canon.IntentError as e:
                item.update({"verdict": "REFUSED", "codes": [e.code], "message": "the candidate is not an intent: %s" % e})
                made.append((item, None))
                continue
            self._record(rid, letter + ".intent", raw_intent)
            item["intent"] = raw_intent
            if cancel.is_set():
                break
            slot = self.play.candidate_slot(ws, D.canon.load_intent(raw_intent), "studio %s %s: %s" % (rid, letter, item["title"]))
            item.update({"verdict": slot.get("verdict", "") or "REFUSED", "codes": slot.get("codes", []), "message": slot["message"],
                         "head": slot.get("checked_against", ""), "record": slot.get("record"),
                         "touches": self.touches(slot, {t: r["piece"] for t, r in req["references"].items()}, req["objects"]) if "realized" in slot else None})
            made.append((item, slot if slot["ok"] else None))
        entry["candidates"] = [{"letter": i["letter"], "title": i["title"], "verdict": i["verdict"], "codes": i["codes"],
                                "intent_sha256": sha256(i["intent"]) if i["intent"] else "", "touches": i["touches"]} for i, _s in made]
        with self.lock:
            if req["state"] != "running":
                entry.update({"outcome": req["code"] or "STUDIO-DISCARDED", "detail": "the request was %s while its candidates compiled" % req["state"]})
                self._log(entry)
                return
        drawn = [(i, s) for i, s in made if s is not None]
        slots = self.play.publish([s for _i, s in drawn])
        with self.lock:
            for (item, _s), k in zip(drawn, slots):
                item["slot"] = k
            req["candidates"] = [i for i, _s in made]
        n_ok = sum(1 for i, s in made if s is not None)
        entry["outcome"] = "DONE"
        self._log(entry)
        self._finish(req, "done", "", "%d candidate%s, %d drawn" % (len(made), "" if len(made) == 1 else "s", n_ok), disp)
        u = entry.get("usage")
        self.say("STUDIO  %s  %s (%s)  %.1f s%s  %s" % (
            rid, provider["name"], provider["model"], entry["provider_ms"] / 1000.0,
            "  %d tokens in, %d out%s" % (u["input_tokens"], u["output_tokens"], ", ~$%.3f (%s)" % (u["cost_usd"], u["cost_basis"]) if u["cost_usd"] is not None else "") if u else "",
            "; ".join("%s %s" % (i["letter"], i["verdict"] + ("" if i["verdict"] == "CLEAN" else " " + ",".join(i["codes"]))) for i, _s in made) or "no candidates"))

    # ------------------------------------------------------------------ the designer's decisions
    def _candidate(self, rid, letter):
        with self.lock:
            r = self.req
            if not r or r["id"] != rid or r["state"] != "done":
                raise StudioError("STUDIO-NO-CANDIDATE", "no finished request %s" % rid)
            c = [c for c in r["candidates"] if c["letter"] == letter]
            if not c:
                raise StudioError("STUDIO-NO-CANDIDATE", "request %s has no candidate %s" % (rid, letter))
            if c[0]["decided"]:
                raise StudioError("STUDIO-DECIDED", "candidate %s is already %s" % (letter, c[0]["decided"]))
            return r, c[0]

    def still(self, rid, letter, png):
        """A drawn candidate's still, as the page drew it (ADMISSION-0, 0222): kept in the world's build folder by its
        sha256, its detectors read here from the bytes. It flags; it decides nothing. Admit names it."""
        r, c = self._candidate(rid, letter)
        if c["slot"] is None or c["intent"] is None:
            raise StudioError("STUDIO-NOT-ADMISSIBLE", "candidate %s was not drawn (%s)" % (letter, c["verdict"]))
        D = self.play.director()
        ws = self.play.workspace()
        h = sha256(png)
        try:
            m, flags = D.quality.detect_png(png)
            det, said = D.quality.detector_fields(m, flags), flags
        except D.quality.QualityError as e:
            det, said = {"not_checked": str(e)[:200]}, ["NOT READ: " + str(e)[:200]]
        d = os.path.join(ws.build, "stills")
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, h + ".png")
        with open(path, "wb") as fh:
            fh.write(png)
        with self.lock:
            c["still"] = {"sha256": h, "path": path, "detectors": det, "flags": said}
        return {"still": h, "detectors": det, "flags": said}

    def admit(self, rid, letter, still="", despite=False):
        """Admit a drawn candidate: evaluated again at the head as the files stand, and admitted through the ledger only
        if that is the head it was drawn at, its verdict is CLEAN, and (ADMISSION-0) it brings the still the page took of
        it as drawn — a still the detectors flag only when the designer admits despite them."""
        r, c = self._candidate(rid, letter)
        if c["slot"] is None or c["intent"] is None:
            raise StudioError("STUDIO-NOT-ADMISSIBLE", "candidate %s was not drawn (%s)" % (letter, c["verdict"]))
        st = c.get("still")
        if not st or not still or st["sha256"] != still:
            raise StudioError("STUDIO-NO-STILL", "candidate %s has no still taken as it was drawn: the page takes one as you admit, and an "
                                                 "admission needs it (ADMISSION-0)" % letter)
        png = open(st["path"], "rb").read()
        if sha256(png) != still:
            raise StudioError("STUDIO-NO-STILL", "candidate %s's still is no longer the bytes the page sent: take it again" % letter)
        D = self.play.director()
        ws = self.play.workspace()
        it = D.canon.load_intent(c["intent"])
        verdict, after, timings, _o1, _o0, _t, rec = D.evaluate_doc(ws, it)
        if verdict["checked_against"] != c["head"]:
            raise StudioError("STUDIO-STALE", "the head moved since candidate %s was drawn (%s, now %s): ask again" % (letter, c["head"][:12], verdict["checked_against"][:12]))
        if verdict["verdict"] != "CLEAN":
            raise StudioError("STUDIO-NOT-ADMISSIBLE", "candidate %s is %s (%s); only a CLEAN candidate is admitted here" % (letter, verdict["verdict"], ",".join(verdict["codes"])))
        if st["flags"] and not despite:
            raise StudioError("STUDIO-STILL-FLAGGED", "candidate %s's still: %s. A detector proves nothing: admit despite it, which the ledger "
                                                      "records, or reject the candidate" % (letter, "; ".join(st["flags"])))
        ev = D.led.append(ws.ledger, "evaluate", D.evaluation_fields(c["intent"], verdict, after, timings, rec))
        a = quiet(D.cmd_admit, ws, ev["seq"], chooser="the designer (studio)", note="request %s, candidate %s" % (rid, letter),
                  still=png, despite=bool(despite))
        with self.lock:
            c["decided"] = "admitted"
            self.last = {"what": "admitted", "request": rid, "candidate": letter, "ledger": [ev["seq"], a["seq"]], "head": a["head_after"]}
        self._log({"id": rid, "at": now(), "decision": "admit", "candidate": letter, "ledger": [ev["seq"], a["seq"]], "head_after": a["head_after"],
                   "still_sha256": still, "despite_detectors": bool(st["flags"])})
        return self.last

    def reject(self, rid, letter):
        r, c = self._candidate(rid, letter)
        D = self.play.director()
        ws = self.play.workspace()
        if c["intent"] is None:
            with self.lock:
                c["decided"] = "rejected"
            return {"what": "rejected", "request": rid, "candidate": letter, "ledger": []}
        it = D.canon.load_intent(c["intent"])
        verdict, after, timings, _o1, _o0, _t, rec = D.evaluate_doc(ws, it)
        ev = D.led.append(ws.ledger, "evaluate", D.evaluation_fields(c["intent"], verdict, after, timings, rec))
        x = quiet(D.cmd_refuse, ws, ev["seq"], chooser="the designer (studio)", note="request %s, candidate %s" % (rid, letter))
        with self.lock:
            c["decided"] = "rejected"
            self.last = {"what": "rejected", "request": rid, "candidate": letter, "ledger": [ev["seq"], x["seq"]]}
        self._log({"id": rid, "at": now(), "decision": "reject", "candidate": letter, "ledger": [ev["seq"], x["seq"]]})
        return self.last

    def undo(self):
        """Undo at the level of intent: the latest admission not yet undone (an undo is never itself undone; undo again
        walks further back), its exact inverse admitted as an intent of its own."""
        D = self.play.director()
        ws = self.play.workspace()
        events, _l, _h = D.led.read(ws.ledger)
        admits = [e for e in events if e["kind"] == "admit"]
        undo_of = lambda e: e.get("observed", {}).get("note", "")[len(UNDO_NOTE):] if e.get("observed", {}).get("note", "").startswith(UNDO_NOTE) else None
        undone = {undo_of(e) for e in admits if undo_of(e) is not None}
        left = [e for e in admits if undo_of(e) is None and e["seq"] not in undone]
        if not left:
            raise StudioError("STUDIO-NOTHING-TO-UNDO", "every admission in the ledger is undone, or an undo")
        a = left[-1]
        if a.get("design_lines"):
            raise StudioError("STUDIO-NOT-UNDOABLE", "the last admission (#%s) changed the layout; undo it through the design tool" % a["seq"])
        src = D.canon.load_intent(events[int(a["evaluation"])]["intent"].encode("ascii"))
        _o, parts, _c = ws.export()
        doc = {"base": {k: parts[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}, "brief": self.brief, "candidate": "U",
               "format": "VERDANDI-INTENT", "layout": [], "prompt": "undo: " + src["prompt"],
               "rationale": "The exact inverse of admission #%s (candidate %s), restoring the statements it changed." % (a["seq"], src["candidate"]),
               "revision": list(a["inverse"]), "scope": list(src["scope"]), "version": "0"}
        raw = D.canon.dumps(doc)
        it = D.canon.load_intent(raw)
        verdict, after, timings, _o1, _o0, _t, rec = D.evaluate_doc(ws, it)
        ev = D.led.append(ws.ledger, "evaluate", D.evaluation_fields(raw, verdict, after, timings, rec))
        if verdict["verdict"] != "CLEAN":
            raise StudioError("STUDIO-NOT-UNDOABLE", "the inverse of #%s is %s (%s), recorded as #%s and not admitted" % (a["seq"], verdict["verdict"], ",".join(verdict["codes"]), ev["seq"]))
        u = quiet(D.cmd_admit, ws, ev["seq"], chooser="the designer (studio)", note=UNDO_NOTE + a["seq"], inverse_of=a["seq"])
        with self.lock:
            self.last = {"what": "undone", "of": a["seq"], "ledger": [ev["seq"], u["seq"]], "head": u["head_after"]}
        self._log({"at": now(), "decision": "undo", "of": a["seq"], "ledger": [ev["seq"], u["seq"]], "head_after": u["head_after"]})
        return self.last


# contextlib.redirect_stdout swaps the process's one sys.stdout: two quiet() calls at once (an admission and an undo,
# two worlds' requests) left it pointing at a dead buffer in 20 of 20 trials (MEASURED in the container, 2026-10-13),
# and play.py's console said nothing after. One at a time; the studio self-test keeps the case and its plant.
QUIET_LOCK = threading.RLock()
LOG_LOCK = threading.Lock()          # the requests' records (Gateway._log): one line at a time in this process


def quiet(fn, *a, **k):
    """A director command, its printing kept off the console; its refusals (it raises SystemExit) made the gateway's."""
    import io
    import contextlib
    try:
        with QUIET_LOCK, contextlib.redirect_stdout(io.StringIO()):
            return fn(*a, **k)
    except SystemExit as e:
        raise StudioError("STUDIO-DIRECTOR-REFUSED", " ".join(str(e).split())[:300])


# ------------------------------------------------------------------------------------------------ the probe and the report
PROBE_PIECE = "canopy:19,10-28,11"
PROBE_PROMPTS = ("make it read as one heavy, monolithic slab that fills more of the sky",
                 "make it lighter and thinner, with a warm glow along its edge")


def probe(config, brief="plaza-night", piece=PROBE_PIECE, prompts=PROBE_PROMPTS, root=None, say=print):
    """The owner's smoke test (2026-10-11): that the configured provider's model "was actually invoked—not just that a
    provider configuration was loaded". The same piece is asked about with two different prompts, through the gateway
    as the page asks, at the head as the files stand; nothing is admitted and the brief is not written (the requests
    are recorded, marked as the probe's). Shown when the provider reports a model and tokens for every request, and the
    two answers differ. Returns (shown, the results)."""
    sys.path.insert(0, HERE)
    import play
    if root:
        play.ROOT = os.path.abspath(root)
    cfg = load_config(config)
    live = play.Live(brief, os.path.join(play.ROOT, "art", "briefs", brief + ".art") if root else None, [])
    g = Gateway(play.Host(live), brief, cfg, play.ROOT, say=lambda s: None, origin="probe")
    say("PROBE  %s  (%s)  brief %s, piece %s" % (os.path.relpath(cfg["path"], REPO), cfg["model"], brief, piece))
    out = []
    for n, prompt in enumerate(prompts, 1):
        rid = g.ask(prompt, piece, None)
        t = time.monotonic()
        while time.monotonic() - t < cfg["timeout_s"] + 60:
            r = g.state()["request"]
            if r["id"] == rid and r["state"] != "running":
                break
            time.sleep(0.1)
        log = [json.loads(ln) for ln in open(os.path.join(g.records, "requests.jsonl"), "rb").read().splitlines()]
        e = [x for x in log if x.get("id") == rid and "outcome" in x]
        e = e[-1] if e else {}
        cands = []
        if r["state"] == "done":
            for c in r["candidates"]:
                f = os.path.join(g.records, rid, c["letter"] + ".intent")
                rev = json.loads(open(f, "rb").read())["revision"] if os.path.isfile(f) else []
                cands.append({"letter": c["letter"], "title": c["title"], "verdict": c["verdict"], "codes": c["codes"], "revision": rev})
        u = e.get("usage")
        say("[%d] %r" % (n, prompt))
        say("    %s  exit %s  %s  %.2f s  %s%s" % (
            e.get("outcome", r["state"]), e.get("exit", "-"), {True: "valid", False: "INVALID"}.get(e.get("valid"), "not read"),
            e.get("provider_ms", 0) / 1000.0, ("%s (%s)" % (e["provider"]["name"], e["provider"]["model"])) if e.get("provider") else "-",
            ("  %d tokens in, %d out%s" % (u["input_tokens"], u["output_tokens"], ", ~$%.3f (%s)" % (u["cost_usd"], u["cost_basis"]) if u["cost_usd"] is not None else "")) if u else "  (no usage reported)"))
        if e.get("detail"):
            say("    " + e["detail"][:300])
        for c in cands:
            say("    %s %s  %s%s" % (c["letter"], c["title"], c["verdict"], "" if c["verdict"] == "CLEAN" else " " + ",".join(c["codes"])))
            for ln in c["revision"]:
                say("        " + ln)
        out.append({"prompt": prompt, "id": rid, "entry": e, "candidates": cands})
    invoked = all(x["entry"].get("provider") and x["entry"].get("usage") and x["entry"]["usage"]["input_tokens"] > 0
                  and x["entry"]["usage"]["output_tokens"] > 0 for x in out)
    lines = [set(ln for c in x["candidates"] for ln in c["revision"]) for x in out]
    answered = all(x["entry"].get("outcome") == "DONE" and x["candidates"] for x in out)
    differ = answered and len(out) > 1 and all(a != b for i, a in enumerate(lines) for b in lines[i + 1:])
    say("invoked: %s" % ("yes: the provider reported its model and its tokens for every request (%d in, %d out in all)" % (
        sum(x["entry"]["usage"]["input_tokens"] for x in out), sum(x["entry"]["usage"]["output_tokens"] for x in out)) if invoked
        else "NOT SHOWN: a request failed, or the provider reported no tokens"))
    say("the answers depend on the prompt: %s" % ("yes: no two prompts were answered with the same revision lines" if differ else
        "NOT SHOWN: a prompt was not answered" if not answered else "NO: two prompts were answered with the same revision lines"))
    shown = invoked and differ
    say("PROBE %s" % ("SHOWN" if shown else "NOT SHOWN"))
    live.stopping = True
    return shown, out


REF_PROBE = (("canopy:19,10-28,11", ("canopy:19,12-20,19", "canopy:19,20-28,21")),
             (("make @1 match @2", {"@1"}),
              ("make @1 twice as deep; keep @2 and @3 exactly as they are", {"@1"}),
              ("give @2 a warm glow along its edge, and leave @1 and @3 alone", {"@2"}),
              ("make @1 look like it connects to @2, without changing @2", {"@1"})))


def probe_refs(config, brief="plaza-night", runs=2, say=print):
    """STUDIO-1's measure, against a real model: with a target and two pins tagged, each prompt names the objects to
    change; for every candidate, which tagged objects it changed and how many untagged ones, by the director's own
    account (Gateway.touches), against the objects the prompt meant. Nothing is admitted. Returns the results."""
    sys.path.insert(0, HERE)
    import play
    cfg = load_config(config)
    live = play.Live(brief, None, [])
    g = Gateway(play.Host(live), brief, cfg, play.ROOT, say=lambda s: None, origin="probe")
    (target, pins), prompts = REF_PROBE
    g.select(target)
    for p in pins:
        g.pin(p)
    say("PROBE REFERENCES  %s  (%s)  brief %s; %s" % (os.path.relpath(cfg["path"], REPO), cfg["model"], brief,
                                                      ", ".join("%s %s %s" % (i["tag"], i["role"], i["piece"]) for i in g.refs()["items"])))
    out = []
    for prompt, meant in prompts:
        for n in range(runs):
            rid = g.ask(prompt, None, None)
            t = time.monotonic()
            while time.monotonic() - t < cfg["timeout_s"] + 60:
                r = g.state()["request"]
                if r["id"] == rid and r["state"] != "running":
                    break
                time.sleep(0.1)
            say("%r (run %d): %s%s" % (prompt, n + 1, r["state"], "" if r["state"] == "done" else " " + r["code"] + " " + r["message"][:120]))
            for c in r["candidates"]:
                tt = c.get("touches") or {}
                changed = {k for k, v in (tt.get("tags") or {}).items() if v == "changed"}
                ok = changed == meant and tt.get("others_count", 0) == 0
                say("    %s %-34s %-8s changed %-12s others %d  added %d%s" % (c["letter"], c["title"][:34], c["verdict"], ",".join(sorted(changed)) or "-",
                                                                             tt.get("others_count", 0), tt.get("added_count", 0), "  as meant" if ok else ""))
                out.append({"prompt": prompt, "run": n + 1, "letter": c["letter"], "verdict": c["verdict"], "changed": sorted(changed),
                            "others": tt.get("others_count", 0), "added": tt.get("added_count", 0), "as_meant": ok, "meant": sorted(meant)})
            if r["state"] != "done":
                out.append({"prompt": prompt, "run": n + 1, "letter": "", "verdict": r["code"], "changed": [], "others": 0, "as_meant": False, "meant": sorted(meant)})
    cands = [x for x in out if x["letter"]]
    say("candidates %d; as meant (the tagged objects the prompt named changed, no other tagged or untagged object of the head) %d; an untagged "
        "object changed %d; a tagged object changed that the prompt did not name %d; a new object made %d; CLEAN %d" % (
            len(cands), sum(x["as_meant"] for x in cands), sum(1 for x in cands if x["others"]), sum(1 for x in cands if set(x["changed"]) - set(x["meant"])),
            sum(1 for x in cands if x["added"]), sum(1 for x in cands if x["verdict"] == "CLEAN")))
    live.stopping = True
    return out


def report(brief="plaza-night", root=None, say=print):
    """Every recorded request of a brief, by provider configuration: the owner's comparison (2026-10-11), "invalid-output
    and timeout rates; latency and cost per accepted edit", from art/build/studio/BRIEF/requests.jsonl."""
    path = os.path.join(os.path.abspath(root) if root else REPO, "art", "build", "studio", brief, "requests.jsonl")
    try:
        log = [json.loads(ln) for ln in open(path, "rb").read().splitlines() if ln.strip()]
    except OSError:
        say("REPORT  no requests recorded for %s (%s)" % (brief, path))
        return 0
    by, of = {}, {}
    for e in log:
        if "outcome" not in e:
            continue
        k = os.path.basename(e.get("config", "?"))
        of[e["id"]] = k
        b = by.setdefault(k, {"requests": 0, "probe": 0, "done": 0, "codes": {}, "ms": [], "models": set(), "verdicts": {}, "admitted": 0,
                              "tin": 0, "tout": 0, "cost": 0.0, "costed": 0})
        b["requests"] += 1
        b["probe"] += 1 if e.get("origin") == "probe" else 0
        if e["outcome"] == "DONE":
            b["done"] += 1
        else:
            b["codes"][e["outcome"]] = b["codes"].get(e["outcome"], 0) + 1
        if "provider_ms" in e:
            b["ms"].append(e["provider_ms"])
        if e.get("provider"):
            b["models"].add(e["provider"]["model"])
        for c in e.get("candidates", []):
            b["verdicts"][c["verdict"]] = b["verdicts"].get(c["verdict"], 0) + 1
        u = e.get("usage")
        if u:
            b["tin"] += u["input_tokens"]
            b["tout"] += u["output_tokens"]
            if u["cost_usd"] is not None:
                b["cost"] += u["cost_usd"]
                b["costed"] += 1
    for e in log:
        if e.get("decision") == "admit" and e.get("id") in of:
            by[of[e["id"]]]["admitted"] += 1
    say("REPORT  %s  (%s)" % (brief, path))
    for k in sorted(by):
        b = by[k]
        ms = sorted(b["ms"])
        med = (ms[(len(ms) - 1) // 2] + ms[len(ms) // 2]) / 2000.0 if ms else 0.0
        invalid = sum(v for c, v in b["codes"].items() if c.startswith("STUDIO-RESPONSE-"))
        say("%s  models %s" % (k, ", ".join(sorted(b["models"])) or "-"))
        say("    %d requests (%d by the probe), %d answered; invalid output %d, timeouts %d, provider errors %d, cancelled or superseded %d" % (
            b["requests"], b["probe"], b["done"], invalid, b["codes"].get("STUDIO-TIMEOUT", 0), b["codes"].get("STUDIO-PROVIDER-EXIT", 0) + b["codes"].get("STUDIO-PROVIDER-START", 0),
            b["codes"].get("STUDIO-CANCELLED", 0) + b["codes"].get("STUDIO-SUPERSEDED", 0)))
        say("    the provider's time: median %.2f s, longest %.2f s" % (med, ms[-1] / 1000.0 if ms else 0.0))
        say("    candidates: %s; admitted from the page: %d" % (", ".join("%s %d" % kv for kv in sorted(b["verdicts"].items())) or "none", b["admitted"]))
        say("    tokens: %d in, %d out%s" % (b["tin"], b["tout"], "; reported cost ~$%.3f over %d requests%s" % (
            b["cost"], b["costed"], ", ~$%.3f an admitted edit" % (b["cost"] / b["admitted"]) if b["admitted"] else ", no admitted edit") if b["costed"] else ""))
    return 0


# ------------------------------------------------------------------------------------------------ commands
def main(argv):
    if argv == ["schema"]:
        print(json.dumps(SCHEMA, indent=1, sort_keys=True))
        return 0
    if argv == ["selftest"]:
        sys.path.insert(0, HERE)
        import play   # noqa: E402  (the gateway is tested through the launcher that hosts it)
        return play.studio_selftest()
    opt = lambda k: argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else None
    if argv[:1] == ["probe"] and len(argv) >= 2 and "--references" in argv:
        try:
            probe_refs(argv[1], opt("--brief") or "plaza-night", int(opt("--runs") or "2"))
        except StudioError as e:
            print("PROBE  %s" % e, file=sys.stderr)
            return 2
        return 0
    if argv[:1] == ["probe"] and len(argv) >= 2:
        try:
            shown, _out = probe(argv[1], opt("--brief") or "plaza-night", opt("--piece") or PROBE_PIECE, root=opt("--root"))
        except StudioError as e:
            print("PROBE  %s" % e, file=sys.stderr)
            return 2
        return 0 if shown else 1
    if argv[:1] == ["report"]:
        return report(opt("--brief") or "plaza-night", opt("--root"))
    if argv[:1] == ["records"]:
        brief = opt("--brief") or "plaza-night"
        path = os.path.join(os.path.abspath(opt("--root")) if opt("--root") else REPO, "art", "build", "studio", brief, "requests.jsonl")
        v = verify_records(path)
        print("RECORDS  %s: %d lines (%d before the chain began), %d unreadable%s, %s" % (
            brief, v["lines"], v["legacy"], len(v["unreadable"]), (" (lines %s)" % ", ".join(map(str, v["unreadable"][:8]))) if v["unreadable"] else "",
            "the chain whole" if not v["breaks"] else "the chain broken at line%s %s" % ("" if len(v["breaks"]) == 1 else "s", ", ".join(map(str, v["breaks"][:8])))))
        print("RECORDS  dispositions: %s" % (", ".join("%s %d" % kv for kv in sorted(v["dispositions"].items())) or "none recorded yet"))
        if v["unmet"]:
            print("RECORDS  asked for and not made yet (telemetry, never a gate): %s" % ", ".join("%s %d" % kv for kv in sorted(v["unmet"].items(), key=lambda kv: (-kv[1], kv[0]))))
        print("RECORDS  a line cut from the end is not found here: that needs the last line's hash kept outside the world folder")
        return 1 if v["breaks"] else 0
    print("usage: python art/studio.py selftest | schema | probe CONFIG.json [--brief B] [--piece ID] | probe CONFIG.json --references [--runs N] | report [--brief B] | records [--brief B] [--root DIR]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
