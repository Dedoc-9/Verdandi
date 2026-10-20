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
import scene_diff         # noqa: E402  (HELD-0: a shape's region, and what lies in it)
import impact             # noqa: E402  (IMPACT-0: what a candidate costs the native renderer, advisory)
import motion             # noqa: E402  (PREVIEW-0: the preview in motion, a replayable experiment)
import camera             # noqa: E402  (PATH-0: the preview's camera path and its clearance rule)
import certificate        # noqa: E402  (CERT-0: every admission's certificate and the exact check of its inverse)

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
    """A refusal, with its code: STUDIO-<WHAT>; and, when the director refused (STUDIO-DIRECTOR-REFUSED), the director's
    own code (LEDGER-SAFE-0, 0245: LEDGER-UNLOGGED, HEAD-MOVED, ADMISSION-0, ...), kept as a field of the answer."""

    def __init__(self, code, detail, director=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code, self.detail, self.director = code, detail, director

    def answer(self):
        """The HTTP answer's body (art/play.py). BINDING-0 (0253): a press of Admit or Undo carries its binding (checked,
        or not reached and why) and its decision record."""
        return dict({"ok": False, "code": self.code, "message": self.detail}, **({"director_code": self.director} if self.director else {}),
                    **binding_fields(self))


def binding_fields(e):
    """What a refused press's answer carries of BINDING-0 (0253): the binding and the decision record, when the press
    made one (an exception of another kind than the press's, or the binding check removed, carries neither)."""
    out = {}
    if getattr(e, "binding", None) is not None:
        out["binding"] = e.binding
    if getattr(e, "binding_record", None) is not None:
        out["record"] = e.binding_record
    return out


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
REGION_RANK = {"held": 0, "adjacent": 1, "outside": 2, "missed": 3, "empty": 4, "stale": 5}
VERDICT_RANK = {"CLEAN": 0, "LEAKAGE": 1}


def held_line(item):
    """What a request's record line keeps of a candidate's report (HELD-0): M, C and P, how much changed, and each named
    shape's verdict; the whole report is the request's <letter>.held.json, named by its sha256."""
    h = item.get("held")
    if not h:
        return None
    if "error" in h:
        return {"error": h["error"][:200]}
    return {"badges": h["badges"], "entries": h["entries"], "objects": h["objects"], "sha256": item.get("held_sha256", ""),
            "accounts": [{k: a.get(k) for k in ("shape", "verdict", "objects", "outside_count")} for a in h["accounts"]]}


# STRICT-0's plants, each set by its self-test alone (play.strict_selftest) and each caught by one of its rows: the check
# skipped at admission, a footprint passed when any box (not every box) is held, the receipts left out of the ledger
STRICT_PLANT = ""
STRICT_PLANTS = ("strict-not-checked", "strict-any-region", "strict-no-receipt")

# DASHBOARD-0's plants of the host (0249), each set by the studio self-test alone and caught by one of its rows: the
# account's dry run taking the candidate as drawn at the files' head (its stale check gone), the account skipping the
# director's checks, the restoration's verdict read from the undo's own certificate, the gateway's state not saying it is
# publishing while a request's candidates are given new slots, and Undo's dry run (_undoing) skipping the director's
# checks, so that Undo's account says it would undo a hand edit the press refuses
ACCOUNT_PLANT = ""
ACCOUNT_PLANTS = ("account-drops-stale", "account-director-skipped", "restoration-from-own-certificate", "publishing-unflagged", "undo-dry-skipped")


# ------------------------------------------------------------------------------------------------ BINDING-0, enforced
# BINDING-0 version 0 (art/director/bindings/BINDING-0.v0.json, registered in 0252 before this code), enforced from 0253:
# an admission (or an undo) through the host that relies on a piece of evidence is written only if that evidence's
# declared identity is known and equals, exactly, the identity the contract names for it, and the host's existing checks
# pass. The registered contract is the authority for what counts as a match; the functions below are its prose made
# executable and are held to the conformance vectors frozen before them (art/director/bindings/0253-vectors.json, cited
# by its sha256 in frozen-0253.jsonl) by STUDIO's rows: keep (the still's rule), compare (one field), piece, press,
# record (the decision record's bytes) and preview_id. The host pins the contract it implements: the version and sha256
# below, which every decision record carries. It never reads the register at a press (his ruling of 2026-10-19: "Do not
# add a runtime register-file read or a new refusal outcome at the press. Pin BINDING-0 v0 in the host, verify that the
# host pin matches the registered v0 line, and require the planted mismatched-pin case to refuse."): STUDIO's rows hold
# the pin against the register's version-0 line.
BINDING_CONTRACT = "BINDING-0"
BINDING_VERSION = 0
BINDING_SHA256 = "cb08e8ed3566f7d4aa19b38ad33fdaf79d1bfd2c21afe73a38576466815cdd85"
BINDING_CODES = ("BINDING-MISMATCH", "BINDING-UNKNOWN")
# BINDING-0's plants of the host (0253), each set by the studio self-test alone (as ACCOUNT_PLANT and STRICT_PLANT are)
# and caught by its own rows (art/director/bindings/0253-matrix.json names them): a name, or a set of names
#   binding-removed        the binding check skipped, and with it the decision record (the host as 0252 was)
#   binding-sufficient     the binding compared right after the admission's evaluation and, once every binding matches,
#                          the studio's checks after the evaluation skipped (STUDIO-STALE, STUDIO-NOT-ADMISSIBLE on the
#                          verdict, the strict check, STUDIO-STILL-FLAGGED), the region passed as None
#   binding-first          the binding check made before every existing check of the press
#   stale-skipped          STUDIO-STALE's comparison skipped at the press, the evaluation left as computed
#   not-reached-as-match   an entry not reached recorded as a MATCH
#   account-claims-binding the account before the press says a binding was checked and matched
#   mismatch-as-match      a MISMATCH compared as a MATCH
#   unknown-as-match       an UNKNOWN compared as a MATCH
#   binding-refreshed      the evidence's declared values replaced at the press by the values expected
#   keeping-case-folded    the still's scene case-folded before it is kept
#   pin-differs            the host's pinned sha256 not the register's
BINDING_PLANT = ""
BINDING_PLANTS = ("binding-removed", "binding-sufficient", "binding-first", "stale-skipped", "not-reached-as-match", "account-claims-binding",
                  "mismatch-as-match", "unknown-as-match", "binding-refreshed", "keeping-case-folded", "pin-differs")


def binding_planted(name):
    """Whether BINDING_PLANT sets the plant `name` (BINDING_PLANT a name, or a set of names)."""
    p = BINDING_PLANT
    if not p:
        return False
    return p == name if isinstance(p, str) else name in p


class _Absent:
    """A request's key that is not there: a JSON body with no `preview` names no preview; an undo with no `of` or no
    `scene` declares none (BINDING-UNKNOWN). Never a JSON value: null is a value, and is not this."""
    __slots__ = ()

    def __repr__(self):
        return "ABSENT"


ABSENT = _Absent()


def binding_pin():
    """The contract this host implements, as every decision record names it: BINDING-0, version 0, its sha256."""
    sha = BINDING_SHA256
    if binding_planted("pin-differs"):
        sha = sha[:-1] + ("0" if sha[-1] != "0" else "1")
    return {"contract": BINDING_CONTRACT, "version": BINDING_VERSION, "sha256": sha}


def _form_decode(s):
    """One name or value of a query as application/x-www-form-urlencoded reads it: '+' a space, each '%' and two hex
    digits the byte they name (any other '%' as it is), the bytes read as UTF-8."""
    b = s.replace("+", " ").encode("utf-8", "surrogatepass")
    out, i, hexd = bytearray(), 0, b"0123456789abcdefABCDEF"
    while i < len(b):
        if b[i] == 0x25 and i + 2 < len(b) and b[i + 1] in hexd and b[i + 2] in hexd:
            out.append(int(b[i + 1:i + 3], 16))
            i += 3
        else:
            out.append(b[i])
            i += 1
    return out.decode("utf-8", "replace")


def first_scene(query):
    """The first value of a query's `scene` parameter, None when it has none (BINDING-0 v0, evidence.still.declared: "the
    first value of POST /studio/still's scene query parameter", a query parameter read as application/x-www-form-urlencoded
    defines one: the query split on '&', each part a name and a value split at its first '=', a name with no '=' having
    the empty value, both decoded; frozen as the keeping vectors K1 to K16). A blank first value is the first value."""
    for part in (query or "").split("&"):
        if not part:
            continue
        name, _eq, value = part.partition("=")
        if _form_decode(name) == "scene":
            return _form_decode(value)
    return None


def keep(value):
    """The still's rule (BINDING-0 v0, evidence.still.declared): a declared scene is kept as it is when it is exactly 64
    characters, each 0-9 or a-f, and as "" otherwise; absent, blank and malformed are one case. Nothing kept is refreshed
    afterwards. A preview's still is kept by the same rule."""
    if binding_planted("keeping-case-folded") and isinstance(value, str):
        value = value.lower()
    return value if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) else ""


def keep_query(query):
    """What the host keeps of a still's query: keep(first_scene(query))."""
    return keep(first_scene(query))


def well_formed(field, value):
    """BINDING-0 v0, comparison.well formed: a scene (and a preview's id) a JSON string of exactly 64 characters, each 0-9
    or a-f; an operation (the undo's `of`) a JSON string in the ledger's form of a sequence number, \\A(0|[1-9][0-9]*)\\Z.
    Any other type, any other string, or none, is not."""
    if not isinstance(value, str):
        return False
    return bool(re.fullmatch(r"0|[1-9][0-9]*" if field == "of" else r"[0-9a-f]{64}", value))


def compare(kind, field, declared, expected="", finished=None):
    """One field of one piece of evidence compared (BINDING-0 v0, comparison.rule): exact equality of the declared value
    and the expected one, as strings, no case folding, no trimming, no prefix, no conversion. `declared` is
    {"present": bool, "value": ...}: the request's value, or the value the host kept. UNKNOWN when either side is not well
    formed (fail-closed: an identity absent or not well formed is unknown), else MATCH or MISMATCH. The entry's declared is
    the value when it is a JSON string, else "". For a preview's name (`finished` the ids of the candidate's finished
    previews) the expected value is the name itself when it names one of them, else "" (UNKNOWN); a body with no key
    `preview` names none, and there is no entry (None)."""
    present = isinstance(declared, dict) and declared.get("present") is True
    value = declared.get("value") if present else None
    if kind == "preview" and field == "preview":
        if not present:
            return None
        expected = value if isinstance(value, str) and value in (finished or ()) else ""
    d = value if isinstance(value, str) else ""
    x = expected if isinstance(expected, str) else ""
    if not well_formed(field, d) or not well_formed(field, x):
        outcome = "UNKNOWN"
    elif d == x:
        outcome = "MATCH"
    else:
        outcome = "MISMATCH"
    if outcome == "MISMATCH" and binding_planted("mismatch-as-match"):
        outcome = "MATCH"
    if outcome == "UNKNOWN" and binding_planted("unknown-as-match"):
        outcome = "MATCH"
    return {"kind": kind, "field": field, "declared": d, "expected": x, "outcome": outcome}


def piece(fields):
    """A piece of evidence's outcome (BINDING-0 v0, comparison.precedence): UNKNOWN if any of its fields is, else MISMATCH
    if any is, else MATCH."""
    outs = [f["outcome"] for f in fields]
    return "UNKNOWN" if "UNKNOWN" in outs else "MISMATCH" if "MISMATCH" in outs else "MATCH"


def preview_order(drawn):
    """A named preview's fields in BINDING-0 v0's precedence: its name, its recorded candidate scene, then each still drawn
    on its candidate's side by pose number as an integer (keyed candidate-K as the host keys it); no base-side still."""
    ks = sorted(int(k.split("-", 1)[1]) for k in (drawn or {}) if re.fullmatch(r"candidate-(0|[1-9][0-9]*)", k))
    return ["preview", "candidate_sha"] + ["candidate-%d" % k for k in ks]


def press(entries):
    """The press's binding answer (BINDING-0 v0, comparison.precedence), the entries in precedence order: BINDING-UNKNOWN
    if any piece is UNKNOWN, else BINDING-MISMATCH if any is MISMATCH, naming the first such field ("kind.field"); ("", "")
    when the binding adds no refusal."""
    for want, code in (("UNKNOWN", "BINDING-UNKNOWN"), ("MISMATCH", "BINDING-MISMATCH")):
        for e in entries:
            if e["outcome"] == want:
                return code, "%s.%s" % (e["kind"], e["field"])
    return "", ""


def record(operation, candidate, intent_sha256, of, evidence, decision, director_code=""):
    """The decision record (BINDING-0 v0, decision record.content): the contract, its version and sha256 (the host's
    pin), the operation, the candidate, its intent's sha256, the undo's target, every piece of evidence relied on in
    precedence order, the decision and the director's own code. No clock and no request id."""
    pin = binding_pin()
    return {"contract": pin["contract"], "version": pin["version"], "sha256": pin["sha256"], "operation": operation,
            "candidate": candidate, "intent_sha256": intent_sha256, "of": of,
            "evidence": [{k: e[k] for k in ("kind", "field", "declared", "expected", "outcome")} for e in evidence],
            "decision": decision, "director_code": director_code}


def record_bytes(rec):
    """The decision record's one form: json.dumps(record, sort_keys=True, separators=(',', ':'), ensure_ascii=True) as
    bytes, with no trailing newline (BINDING-0 v0, decision record.form)."""
    return json.dumps(rec, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def preview_id(binding, drawn, report_sha256):
    """A finished preview's id (BINDING-0 v0, evidence.preview.relied on): the sha256 of the canonical form (sorted keys,
    separators ',' and ':', ASCII, nothing added) of its binding as recorded at its plan ({head, base_sha, candidate_sha}),
    the scene kept for each still drawn for it (keyed side-k, "" where none was kept) and the sha256 of its
    preview.report.json."""
    obj = {"binding": {k: binding[k] for k in ("head", "base_sha", "candidate_sha")}, "drawn": dict(drawn), "report_sha256": report_sha256}
    return sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii"))


def not_reached(entries):
    """Where an earlier check refused (BINDING-0 v0, decision record.content): each piece relied on listed with what it
    declared, "expected" "" and "outcome" "not reached", never a comparison made after the first refusal (his safeguard:
    "`not_checked` must be explicit")."""
    if binding_planted("not-reached-as-match"):
        return [{"kind": e["kind"], "field": e["field"], "declared": e["declared"], "expected": e["declared"], "outcome": "MATCH"} for e in entries]
    return [{"kind": e["kind"], "field": e["field"], "declared": e["declared"], "expected": "", "outcome": "not reached"} for e in entries]


def binding_message(code, names, entries):
    """A binding refusal's words: the evidence and the field it names; for a mismatch the value declared and the value
    expected, as the record's entry gives them; for an unknown that its value is absent or not well formed."""
    e = [x for x in entries if "%s.%s" % (x["kind"], x["field"]) == names][0]
    what = {"still": "the admission's still", "preview": "the named preview", "undo": "the undo"}[e["kind"]]
    if code == "BINDING-MISMATCH":
        return ("BINDING-0: %s binds another identity than the one this %s relies on: %s declared %s, expected %s; nothing of it was "
                "written (the evidence is never refreshed: take it again)" % (what, "undo" if e["kind"] == "undo" else "admission", names, e["declared"], e["expected"]))
    return ("BINDING-0: %s's %s is absent or not well formed (declared %r): an identity that is not known is refused, never taken as a match; "
            "nothing of it was written" % (what, names, e["declared"]))


def bounds_of(O, piece):
    """IMPACT-0: the box around an object's boxes ({"box": [...]}), the object found by a piece of it; None if none."""
    if not piece:
        return None
    root = piece
    while root not in O and root.count(":") >= 2:
        root = root.rsplit(":", 1)[0]
    if root not in O or not O[root]["boxes"]:
        return None
    bs = O[root]["boxes"]
    return {"box": [min(b[i] for b in bs) for i in range(3)] + [max(b[i] for b in bs) for i in range(3, 6)]}


def impact_line(rep, sha):
    """IMPACT-0 (0239): what the request's record line keeps of a candidate's impact; the whole is <letter>.impact.json."""
    if "error" in rep:
        return {"error": rep["error"][:200], "sha256": sha}
    return {"delta": rep["delta"], "estimate_delta_ms": rep["estimate"]["delta_ms"], "flag": rep["flag"],
            "over_budget": [o["budget"] for o in rep["over_budget"]], "path_id": rep["preview"]["path_id"], "sha256": sha}


def strict_check(scene0, scene1, shapes):
    """art/scene_diff.py's strict check, said and never raised: a check that cannot be made refuses (ADMIT-STALE)."""
    try:
        return scene_diff.strict(scene0, scene1, shapes)
    except (scene_diff.DiffError, studio_marks.ShapeError, KeyError, TypeError, ValueError) as e:
        return {"format": "VERDANDI-STRICT", "version": "0", "ok": False, "code": "ADMIT-STALE", "error": "%s: %s" % (type(e).__name__, str(e)[:300])}


def strict_line(rep, sha):
    """STRICT-0 (0238): what the request's record line and the page keep of a candidate's strict check; the whole check,
    with its receipt and inverse receipt, is the request's <letter>.strict.json, named by its sha256."""
    if "error" in rep:
        return {"ok": False, "code": rep["code"], "error": rep["error"][:200], "sha256": sha}
    return {"ok": rep["ok"], "code": rep["code"], "count": rep["count"], "outside": rep["outside"], "outside_count": rep["outside_count"],
            "global": rep["global"], "stale": rep["stale"], "receipt_sha256": rep["receipt_sha256"], "sha256": sha}


def host_order(items):
    """COMPARE-0 (0235): the candidates in the host's order, by host facts alone and lexicographically, never a weighted
    sum: the director's verdict (CLEAN, then LEAKAGE, then the rest); the region (the worst of its shapes' verdicts:
    held, adjacent, outside, missed, empty, stale; a candidate with no report last); for an art request, the play
    geometry changed (C) after it unchanged; the objects outside the regions; the diff's entries; the letter. The
    model's title, rationale and words are never read."""
    def key(i):
        h = i.get("held") or {}
        ok = bool(h) and "error" not in h
        accs = h.get("accounts", []) if ok else []
        region = max([REGION_RANK.get(a["verdict"], 6) for a in accs] or [0]) if ok else 6
        c_art = 1 if ok and h["badges"]["C"] and not i.get("layout") else 0
        return [VERDICT_RANK.get(i["verdict"], 2), region, c_art, sum(a.get("outside_count", 0) for a in accs), h.get("entries", 0) if ok else 1 << 30, i["letter"]]
    keyed = sorted((key(i), i["letter"]) for i in items)
    return [{"letter": letter, "key": k[:5]} for k, letter in keyed]


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
        # DASHBOARD-0 (0249): set while a request's candidates are published and their slots not yet given them (the
        # slots serve the new scenes, the request the old indices): a reader of the state is told, never shown a card
        # that points at a slot serving another scene
        self.publishing = False
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
            # HARDEN-0 (0232): the object's fingerprint as it was tagged is kept (a file before 0232 has none: its tags read
            # "unknown" until they are bound again, never "changed")
            fp = t.get("fingerprint", "")
            if not isinstance(fp, str) or (fp and not re.fullmatch(r"[0-9a-f]{64}", fp)):
                raise ValueError("a tag's fingerprint that is not a sha256: %r" % (fp,))
            tags[t["tag"]] = {"tag": t["tag"], "piece": t["piece"], "address": t["address"], "kind": t["kind"], "scene": t["scene"], "head": "",
                              "fingerprint": fp, "statement": None, "size_m": []}
            tag_of[t["piece"]] = t["tag"]
        self.tags, self.tag_of, self.next_tag = tags, tag_of, nxt

    def _save_tags(self):
        """Write the tags file whole (a temporary file, flushed, renamed over it). Holds the lock."""
        if not self.tags_path:
            return
        doc = {"format": TAGS_FORMAT, "version": "0", "brief": self.brief, "next": str(self.next_tag),
               "tags": [dict({"tag": t["tag"], "piece": t["piece"], "address": t["address"], "kind": t["kind"], "scene": t["scene"]},
                             **({"fingerprint": t["fingerprint"]} if t["fingerprint"] else {}))
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
                req["candidates"] = [dict({k: c[k] for k in ("letter", "title", "verdict", "codes", "message", "slot", "decided", "head", "touches")}, compared=c.get("compared", ""),
                                          record=c.get("record"), still={k: c["still"].get(k, "") for k in ("sha256", "detectors", "flags", "scene")} if c.get("still") else None,
                                          held={k: v for k, v in c["held"].items() if k != "boxes"} if c.get("held") else None,
                                          strict=c.get("strict"), impact=c.get("impact"),
                                          preview=dict({k: c["preview_report"][k] for k in ("replayed", "state_verified", "code", "path_id")},
                                                       binding=c.get("preview_binding"), drawn_ok=drawn_ok(c.get("preview_binding"), c.get("preview_drawn"))) if c.get("preview_report") else None,
                                          # DASHBOARD-0 (0249): what the card names: the head its intent was written against, the
                                          # base scene of its own evaluation, and the scene its slot served when it was published
                                          written_against=c.get("written_against", ""), base_sha=c.get("base_sha", ""), scene=c.get("scene", ""))
                                     for c in r["candidates"]]
                if self.publishing and ACCOUNT_PLANT != "publishing-unflagged":
                    for x in req["candidates"]:
                        x["slot"] = None
                req["strict"] = bool(r.get("strict"))
                req["path"] = {k: r["path"][k] for k in ("id", "name", "seed")} if r.get("path") else None
                req["order"] = r.get("order", [])
            last = dict(self.last)
            publishing = self.publishing and ACCOUNT_PLANT != "publishing-unflagged"
        return {"provider": prov, "request": req, "last": last, "refs": self.refs(), "publishing": publishing}

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
            status = "unknown" if O is None or (o is not None and not t["fingerprint"]) else "gone" if o is None else "changed" if R.fingerprint(o) != t["fingerprint"] else "ok"
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
                         "bound": {"scene": rec["scene"], "head": rec["head"],
                                   # HARDEN-0: not known (None) when the tag was read from a file without its fingerprint
                                   "changed_since": (R.fingerprint(o) != rec["fingerprint"]) if rec["fingerprint"] else None}})
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
        recs = {r_["name"]: r_ for r_ in store.records(names)}
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
            res[-1]["region"] = self._held_region(recs.get(ev["name"]), out, O)
        return res

    def _held_region(self, rec, out, O):
        """HELD-0 (0235): the region a candidate is held to (the outline swept from the back of the marked box out to its
        reach) and, at the head, which statements make objects that lie wholly in it and which make some in it and some
        outside: the director's real choice before it answers. Host facts, exact."""
        if rec is None:
            return None
        try:
            reg = scene_diff.region(rec, out["scene"])
        except scene_diff.DiffError as e:
            return {"error": e.detail[:200]}
        by = {}
        for o in O.values():
            rels = {scene_diff.classify(b, reg) for b in o["boxes"]}
            e = by.setdefault(o["by"], {"inside": 0, "meets": 0, "outside": 0})
            e["inside" if rels == {"inside"} else "meets" if rels - {"outside"} else "outside"] += 1
        keys = {x["hash"]: x["key"] for x in out["lineage"]["statements"]}
        inside = sorted(keys[h] for h, e in by.items() if h in keys and e["inside"] and not e["meets"] and not e["outside"])
        partly = sorted(keys[h] for h, e in by.items() if h in keys and (e["meets"] or e["inside"]) and (e["meets"] or e["outside"]))
        return {"reach_m": None if reg["reach"] is None else float(reg["reach"]),
                "statements_inside": inside[:24], "statements_partly": partly[:24],
                "rule": "held: every box the candidate changes lies in this region; the studio decides it exactly and orders the candidates by it"}

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
        # HARDEN-0 (0232): an object the candidate adds is counted once, with its parts (a new canopy and its ribs and
        # lights were each counted as a new object; the sprint-3 review MEASURED it)
        new = {i for i in ids if i not in O}

        def root_new(i):
            r = i
            while r.count(":") >= 2 and r.rsplit(":", 1)[0] in new:
                r = r.rsplit(":", 1)[0]
            return r
        added = sorted({root_new(i) for i in new})
        return {"tags": tagged, "others": others[:12], "others_count": len(others), "added": added[:12], "added_count": len(added),
                "materials": list(slot.get("materials_changed") or [])}

    # ------------------------------------------------------------------ a request
    def ask(self, prompt, piece=None, camera=None, refs=None, cfg=None, strict=False):
        """Start a request; it cancels the one before it. Returns the request's id, or raises StudioError at once
        (no provider, an empty prompt, an unknown piece, a reference that names nothing). `piece`, if given, is selected
        first as the target (E does it in the page). STUDIO-2, for the queue: `refs` (target tag, [pin tags]) are the
        references the task was queued with, in place of the page's present ones; `cfg` the provider it was queued with.
        STRICT-0 (0238): `strict` (True only) admits a candidate only when every box it changes lies within the named
        shapes' regions; a strict request names at least one shape."""
        cfg = cfg or self.cfg
        if cfg is None:
            raise StudioError("STUDIO-NO-PROVIDER", "no director is configured: start play.py with --director CONFIG.json (art/STUDIO.md)")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > LIMITS["prompt"]:
            raise StudioError("STUDIO-PROMPT", "a prompt is 1 to %d characters" % LIMITS["prompt"])
        try:
            # HARDEN-0 (0232): a prompt is text: half of a character (a lone surrogate, as half an emoji pasted) is refused
            # here, not found by the request's thread after it reads as running (ADVERSARY-A: it stayed running for ever)
            prompt.encode("utf-8")
        except UnicodeEncodeError:
            raise StudioError("STUDIO-PROMPT", "the prompt holds half of a character (a lone surrogate): type it again")
        cam = {}
        if camera is not None and not isinstance(camera, dict):
            camera = None                # a camera that is not an object is no camera (it was a 500 before 0232)
        for k in ("x", "y", "z", "yaw_deg", "pitch_deg"):
            v = (camera or {}).get(k)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or v != v or v in (float("inf"), float("-inf")) or not (-1e9 < v < 1e9):
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
        strict = strict is True
        if strict and not shapes:
            raise StudioError("STUDIO-STRICT", "a strict request is held to the regions of the shapes it names (#name), and this one names none")
        store = getattr(self.play, "shapes", lambda: None)()
        shape_recs = store.records([x["name"] for x in shapes]) if (shapes and store is not None) else []
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
            if strict:
                request["strict"] = True
            # IMPACT-0 (0239): the preview's camera path, named and seeded by the request, the same for all its candidates
            # PATH-0/FRAME-0: the path is made in the request's own thread (it may take a second or more), named in the
            # state once made; the page's preview waits for the request anyway
            path_args = (S, shapes, bounds_of(O, (target or {}).get("piece")))
            path = None
            self.req = {"id": rid, "state": "running", "prompt": prompt.strip(), "message": "", "code": "", "shapes": [s["name"] for s in shapes], "path": path, "path_args": path_args,
                        "references": {r["tag"]: {"role": r["role"], "piece": r["piece"], "address": r["address"]} for r in refs},
                        "selection": target["address"] if target else None,
                        "head": head, "provider": {"model": cfg["model"]}, "candidates": [], "started": time.monotonic(),
                        "ended": None, "base": base, "objects": O, "cfg": cfg, "shape_recs": shape_recs, "strict": strict}
            self.cancel = threading.Event()
            req, cancel = self.req, self.cancel
        self.play.publish([])
        threading.Thread(target=self._run, args=(req, request, cancel, ws), daemon=True).start()
        return rid

    def _path(self, S, shapes, target_box, rid):
        """PATH-0 (0241): the request's camera path (art/camera.py), or, when too few poses about its focus are clear, a
        path of none that says why (the preview then refuses: PREVIEW-NO-PATH). FRAME-0 (0243): with a shape on an upright
        face, the arc framed for the shape's region (its framing said in the path, met or FRAME-NONE)."""
        focus, normal = impact.aim_of(S, shapes, target_box)
        try:
            return impact.camera_path(S, focus, rid, normal, camera.subject_of(shapes))
        except camera.CameraError as e:
            return {"id": "none", "name": "none", "seed": rid, "focus": focus, "poses": [], "refused": "%s: %s" % (e.code, e.detail)}

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
        titles, previews = {}, {}
        try:
            for ln in open(os.path.join(self.records, "requests.jsonl"), "rb").read().splitlines():
                e = json.loads(ln)
                if e.get("id") == rid and e.get("candidates"):
                    titles = {c["letter"]: c["title"] for c in e["candidates"]}
                if e.get("id") == rid and e.get("decision") == "preview" and isinstance(e.get("preview_id"), str):
                    previews.setdefault(e.get("candidate"), []).append(e)
        except (OSError, ValueError):
            pass
        D = self.play.director()
        ws, out, parts, head = self._head()
        O = R.objects(out["scene"])
        refs = {r["tag"]: r["piece"] for r in request.get("references", [])}
        # HELD-0: the request's shapes as they are kept now (a shape marked again since is held as it stands now; one that
        # is not ok at this head is accounted "stale", and said below)
        store = getattr(self.play, "shapes", lambda: None)()
        shape_recs = store.records([s_.get("name") for s_ in request.get("shapes", [])]) if store is not None else []
        made = []
        # PATH-0 (0241): the request's path again, at the head as it is now, seeded by its id; each candidate's impact
        # computed again from its evaluation now (kept in the state; the first, recorded one is left as it was)
        path = self._path(out["scene"], request.get("shapes", []), bounds_of(O, (request.get("target") or {}).get("piece")), rid)
        for letter in LETTERS:
            f = os.path.join(d, letter + ".intent")
            if not os.path.exists(f):
                continue
            raw_intent = open(f, "rb").read()
            try:
                was = json.loads(open(os.path.join(d, letter + ".impact.json"), "rb").read())
            except (OSError, ValueError):
                was = {}
            wp = was.get("provenance") or {}
            ctx = {"path": path, "rationale": (was.get("rationale") or {}).get("text", ""),
                   "provenance": {"producer": wp.get("producer", "recorded"), "model": wp.get("model", ""), "configured_model": wp.get("configured_model", ""),
                                  "prompt_sha256": sha256(request.get("prompt", "").encode("utf-8")), "request": rid, "seed": path["seed"]}}
            item = {"letter": letter, "title": titles.get(letter, letter), "verdict": "", "codes": [], "message": "", "slot": None,
                    "decided": "", "head": "", "intent": raw_intent, "touches": None, "record": None, "still": None, "held": None}
            # BINDING-0 (0253): the candidate's finished previews as the host kept them under their ids, read back from the
            # request's own preview lines (each line's id held again to its binding, drawn scenes and report's sha256; a
            # line that does not hold is not kept), never overwritten
            for e in previews.get(letter, []):
                try:
                    b_, d_ = {k: e["binding"][k] for k in ("head", "base_sha", "candidate_sha")}, dict(e["drawn"])
                    if preview_id(b_, d_, e["files"]["preview.report.json"]) == e["preview_id"]:
                        item.setdefault("previews", {}).setdefault(e["preview_id"], {"binding": b_, "drawn": d_})
                except (KeyError, TypeError, ValueError, AttributeError):
                    continue
            it = D.canon.load_intent(raw_intent)
            item["layout"] = bool(it["layout"])
            slot = self.play.candidate_slot(ws, it, "studio %s %s: %s (drawn again)" % (rid, letter, item["title"]), shapes=shape_recs, impact_ctx=ctx)
            item.update({"verdict": slot.get("verdict", "") or "REFUSED", "codes": slot.get("codes", []), "message": slot["message"],
                         "head": slot.get("checked_against", ""), "touches": self.touches(slot, refs, O) if "realized" in slot else None,
                         "record": slot.get("record"), "held": slot.get("held"), "written_against": slot.get("written_against", ""),
                         "base_sha": slot.get("base_sha", ""), "scene": slot.get("sha", "") if slot["ok"] else ""})
            if slot.get("impact") is not None:
                item["impact"] = dict(slot["impact"], sha256=sha256((json.dumps(slot["impact"], sort_keys=True, indent=1, ensure_ascii=True) + "\n").encode("ascii")))
            made.append((item, slot if slot["ok"] else None))
        drawn = [(i, s) for i, s in made if s is not None]
        with self.lock:
            self.publishing = True
        try:
            return self._restored(rid, request, head, parts, O, made, drawn, path, shape_recs, out)
        finally:
            with self.lock:
                self.publishing = False

    def _restored(self, rid, request, head, parts, O, made, drawn, path, shape_recs, out):
        """restore()'s second half: the candidates published, then the request replaced (publishing meanwhile)."""
        slots = self.play.publish([s for _i, s in drawn])
        durable.point("studio:published")
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
                        "base": {k: parts[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}, "objects": O, "cfg": self.cfg,
                        "shape_recs": shape_recs, "order": host_order([i for i, _s in made]), "path": path}
            self.publishing = False
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
        os.makedirs(os.path.dirname(os.path.join(d, name)), exist_ok=True)
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
        """The request's thread. HARDEN-0 (0232): whatever it raises, the request ends (failed, STUDIO-FAILED, recorded),
        never left running with no thread behind it."""
        try:
            self._run1(req, request, cancel, ws)
        except Exception as e:  # noqa: BLE001 — a request always ends
            import traceback
            detail = "%s: %s" % (type(e).__name__, str(e)[:300])
            disp = {"kind": "FAILED", "decided_by": "host", "code": "STUDIO-FAILED", "detail": detail}
            try:
                self._log({"id": req["id"], "at": now(), "brief": self.brief, "head": req["head"], "outcome": "STUDIO-FAILED", "detail": detail, "disposition": disp})
            except Exception:  # noqa: BLE001 — the record could not be written either; the state still ends
                pass
            self._finish(req, "failed", "STUDIO-FAILED", detail, disp)
            self.say("STUDIO  %s  STUDIO-FAILED: %s\n%s" % (req["id"], detail, traceback.format_exc()[-800:]))

    def _run1(self, req, request, cancel, ws):
        rid = req["id"]
        if req.get("path") is None and req.get("path_args"):
            made = self._path(*req["path_args"], rid)
            with self.lock:
                req["path"] = made
                req.pop("path_args", None)
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
                    "decided": "", "head": "", "intent": None, "touches": None, "record": None, "still": None, "held": None,
                    "layout": bool(doc.get("layout"))}
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
            ctx = {"path": req["path"], "rationale": c.get("rationale", ""),
                   "provenance": {"producer": provider.get("name", ""), "model": provider.get("model", ""), "configured_model": req["cfg"].get("model", ""),
                                  "prompt_sha256": sha256(req["prompt"].encode("utf-8")), "request": rid, "seed": req["path"]["seed"]}}
            slot = self.play.candidate_slot(ws, D.canon.load_intent(raw_intent), "studio %s %s: %s" % (rid, letter, item["title"]),
                                            shapes=req.get("shape_recs", ()), strict=req.get("strict", False), impact_ctx=ctx)
            item.update({"verdict": slot.get("verdict", "") or "REFUSED", "codes": slot.get("codes", []), "message": slot["message"],
                         "head": slot.get("checked_against", ""), "record": slot.get("record"), "held": slot.get("held"),
                         "written_against": slot.get("written_against", ""), "base_sha": slot.get("base_sha", ""),
                         "scene": slot.get("sha", "") if slot["ok"] else "",
                         "touches": self.touches(slot, {t: r["piece"] for t, r in req["references"].items()}, req["objects"]) if "realized" in slot else None})
            if item["held"] is not None:
                # HELD-0: the whole report kept beside the intent; the record's line names it by its sha256
                hb = (json.dumps(item["held"], sort_keys=True, indent=1, ensure_ascii=True) + "\n").encode("ascii")
                self._record(rid, letter + ".held.json", hb)
                item["held_sha256"] = sha256(hb)
            if slot.get("strict") is not None:
                # STRICT-0: the whole check (its receipt and inverse receipt) kept beside the intent; the line names it
                sb = (json.dumps(slot["strict"], sort_keys=True, indent=1, ensure_ascii=True) + "\n").encode("ascii")
                self._record(rid, letter + ".strict.json", sb)
                item["strict"] = strict_line(slot["strict"], sha256(sb))
            elif req.get("strict"):
                item["strict"] = {"ok": False, "code": "ADMIT-STALE", "detail": "the candidate was not drawn, so nothing of it can be held"}
            if slot.get("impact") is not None:
                # IMPACT-0: the whole impact beside the intent, the line naming it; advisory, it decides nothing
                ib = (json.dumps(slot["impact"], sort_keys=True, indent=1, ensure_ascii=True) + "\n").encode("ascii")
                self._record(rid, letter + ".impact.json", ib)
                item["impact"] = dict(slot["impact"], sha256=sha256(ib))
            made.append((item, slot if slot["ok"] else None))
        order = host_order([i for i, _s in made])
        entry["order"] = order
        entry["candidates"] = [{"letter": i["letter"], "title": i["title"], "verdict": i["verdict"], "codes": i["codes"],
                                "intent_sha256": sha256(i["intent"]) if i["intent"] else "", "touches": i["touches"],
                                "held": held_line(i), **({"strict": i["strict"]} if "strict" in i else {}),
                                **({"impact": impact_line(i["impact"], i["impact"]["sha256"])} if i.get("impact") else {})} for i, _s in made]
        with self.lock:
            if req["state"] != "running":
                entry.update({"outcome": req["code"] or "STUDIO-DISCARDED", "detail": "the request was %s while its candidates compiled" % req["state"]})
                self._log(entry)
                return
        drawn = [(i, s) for i, s in made if s is not None]
        with self.lock:
            self.publishing = True
        try:
            slots = self.play.publish([s for _i, s in drawn])
            durable.point("studio:published")
            with self.lock:
                for (item, _s), k in zip(drawn, slots):
                    item["slot"] = k
                req["candidates"] = [i for i, _s in made]
                req["order"] = order
                self.publishing = False
        finally:
            with self.lock:
                self.publishing = False
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

    def still(self, rid, letter, png, scene=""):
        """A drawn candidate's still, as the page drew it (ADMISSION-0, 0222): kept in the world's build folder by its
        sha256, its detectors read here from the bytes. It flags; it decides nothing. Admit names it. DASHBOARD-0 (0249):
        `scene`, the scene the page says it drew, is recorded; scene_is_candidate is an observation against the card's
        kept scene, never BINDING-0's outcome. BINDING-0 (0253): the scene is kept by the still's rule (keep: the first
        value of the route's scene parameter, as it is when it is 64 lower hex, else ""), each send replacing the one
        before; an admission relying on this still is held to it at the press, never here."""
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
        scene = keep(scene)
        with self.lock:
            c["still"] = {"sha256": h, "path": path, "detectors": det, "flags": said, "scene": scene}
        return {"still": h, "detectors": det, "flags": said, "scene": scene, "scene_is_candidate": bool(scene) and scene == c.get("scene")}

    def admit(self, rid, letter, still="", despite=False, preview=ABSENT):
        """Admit a drawn candidate: evaluated again at the head as the files stand, and admitted through the ledger only
        if that is the head it was drawn at, its verdict is CLEAN, and (ADMISSION-0) it brings the still the page took of
        it as drawn — a still the detectors flag only when the designer admits despite them. BINDING-0 (0253): and only if
        the evidence it relies on is bound to the candidate scene at admission (the scene its own evaluation exports): the
        still's kept scene, and a preview when the request names one by its id (`preview`; ABSENT, the key not in the body,
        names none), compared after every existing check, the commit's own under the content lock included, and before
        the admission's first write. Every press is decided with its decision record, on the answer and the request's
        log line (one line a press), whatever it answers."""
        D = self.play.director()
        c0, st0 = self._find(rid, letter)
        ctx = {"op": "admit", "rid": rid, "letter": letter, "still": still, "preview": preview, "entries": None, "c": c0, "st0": st0}
        try:
            return self._admit(rid, letter, still, despite, preview, ctx)
        except StudioError as e:
            self._decided(ctx, e, e.code, e.director)
            raise
        except failures(D) as e:
            self._decided(ctx, e, "STUDIO-FAILED", "")
            raise

    def _find(self, rid, letter):
        """The candidate a press names, as the gateway holds it, and its still as it stood at the start of the press, in
        one snapshot: (candidate or None, still or None). For the decision record only (its intent's sha256, and the still
        a record not reached declares), never a check (the press's own checks find it, or refuse)."""
        with self.lock:
            r = self.req
            if not r or r.get("id") != rid or not isinstance(letter, str):
                return None, None
            got = [x for x in r.get("candidates") or [] if x.get("letter") == letter]
            return (got[0], got[0].get("still")) if got else (None, None)

    def _admit(self, rid, letter, still, despite, preview, ctx):
        D = self.play.director()
        ws = self.play.workspace()
        if binding_planted("binding-first"):
            self._binding_first_admit(rid, letter, still, preview, ctx)
        r, c, st, png, it, verdict, after, timings, rec, region = self._admission(rid, letter, still, despite, ctx=ctx)
        scene = ctx["scene"]
        # LEDGER-SAFE-0 (0245): the evaluation was made outside the content lock; it is appended under it, and only at the
        # head the ledger holds (another admission may have landed meanwhile, or the files changed outside the loop)
        durable.point("studio:admit-evaluated")
        ev = quiet(D.append_evaluation, ws, c["intent"], verdict, after, timings, rec)
        parent_text = ws.text()

        def gate():
            # BINDING-0 (0253): the binding check, called by the director's commit under the content lock after every
            # check it makes and before its first write (v0 order.rule); the values compared fixed before the press
            # began: the still's kept scene, the named preview's kept scenes, this admission's own evaluation's scene
            if binding_planted("binding-removed"):
                return
            entries = self._admission_entries(c, st, preview, scene, refreshed=binding_planted("binding-refreshed"))
            ctx["entries"] = entries
            code, names = press(entries)
            if code:
                raise StudioError(code, binding_message(code, names, entries))
        a = quiet(D.cmd_admit, ws, ev["seq"], chooser="the designer (studio)", note="request %s, candidate %s" % (rid, letter),
                  still=png, despite=bool(despite), region=region, gate=gate)
        cert = self._certify(ws, a, it["revision"], parent_text, (c.get("impact") or {}).get("provenance") or {"request": rid}, rid, letter)
        decided = self._binding_decided(ctx, "ADMIT", "")
        with self.lock:
            c["decided"] = "admitted"
            c["certificate"] = cert
            comparison = self._compared(r, letter)
            self.last = dict({"what": "admitted", "request": rid, "candidate": letter, "ledger": [ev["seq"], a["seq"]], "head": a["head_after"], "certificate": cert},
                             **decided)
        self._log(dict({"id": rid, "at": now(), "decision": "admit", "candidate": letter, "ledger": [ev["seq"], a["seq"]], "head_after": a["head_after"],
                        "still_sha256": still, "despite_detectors": bool(st["flags"]), "comparison": comparison, "certificate": cert},
                       **({"strict": {k: region[k] for k in ("count", "receipt_sha256", "inverse_receipt_sha256", "support_sha256")}} if region else {}),
                       **decided))
        return self.last

    # BINDING-0 (0253): the evidence a press relies on, its comparison, its decision record and its line
    def _admission_entries(self, c, st, preview, scene, refreshed=False):
        """An admission's evidence compared, in precedence order (v0 comparison.precedence): the still (its kept scene,
        "" when no still the admission names is kept), then the named preview, when the request names one: its name; when
        the name is a finished preview of the candidate, its recorded candidate scene and its candidate-side stills by
        pose. Each expected to be the candidate scene at admission, `scene`. `refreshed` is the plant binding-refreshed."""
        kept = (st or {}).get("scene", "")
        entries = [compare("still", "scene", {"present": True, "value": scene if refreshed else kept}, scene)]
        if preview is not ABSENT:
            with self.lock:
                store = dict(c.get("previews") or {})
            entries.append(compare("preview", "preview", {"present": True, "value": preview}, finished=store))
            kept_pv = store.get(preview) if isinstance(preview, str) else None
            if kept_pv is not None:
                entries.append(compare("preview", "candidate_sha", {"present": True, "value": scene if refreshed else kept_pv["binding"].get("candidate_sha")}, scene))
                for f in preview_order(kept_pv["drawn"])[2:]:
                    entries.append(compare("preview", f, {"present": True, "value": scene if refreshed else kept_pv["drawn"][f]}, scene))
        return entries

    def _declared_admission(self, ctx):
        """What an admission declared, for a record whose binding was not reached: the still the admission names, by the
        scene kept with it ("" when no still it names is kept), and a named preview by its name alone, whatever it names
        (the name's own comparison would be made after the first refusal)."""
        # the still _admission decided (None included: checked, none the admission names held) whenever the press got that
        # far, and otherwise the still as it stood at the start of the press; never read again after the refusal, so that
        # a still posted meanwhile, or a request restored, does not change what the record declares
        st = ctx["st"] if "st" in ctx else ctx.get("st0")
        still = ctx.get("still")
        kept = st.get("scene", "") if st and isinstance(still, str) and still and st.get("sha256") == still else ""
        out = [{"kind": "still", "field": "scene", "declared": kept}]
        if ctx.get("preview") is not ABSENT:
            out.append({"kind": "preview", "field": "preview", "declared": ctx["preview"] if isinstance(ctx["preview"], str) else ""})
        return out

    def _binding_decided(self, ctx, decision, director):
        """The press's binding and its decision record ({"binding": ..., "record": ...}); {} when the plant removes the
        check (the host as 0252 was). Where the binding check was not reached, the record lists each piece relied on as
        declared, "not reached", and the binding says so (checked false, why the earlier code)."""
        if binding_planted("binding-removed"):
            return {}
        if ctx["op"] == "admit":
            c = ctx.get("c")
            cand = ctx["letter"] if isinstance(ctx["letter"], str) else ""
            intent = sha256(c["intent"]) if c is not None and c.get("intent") is not None else ""
            of = ""
            declared = self._declared_admission
        else:
            cand, intent, of = "", "", ctx.get("target") or ""
            declared = lambda x: [{"kind": "undo", "field": f, "declared": x[f] if isinstance(x[f], str) else ""} for f in ("of", "scene")]
        if ctx["entries"] is None:
            entries = not_reached(declared(ctx))
            binding = {"checked": False, "why": decision}
        else:
            entries = ctx["entries"]
            code, names = press(entries)
            binding = {"checked": True, "refused": code, "names": names}
        return {"binding": binding, "record": record(ctx["op"], cand, intent, of, entries, decision, director)}

    def _decided(self, ctx, e, decision, director):
        """A refused press (or one answered STUDIO-FAILED): its binding and record put on the exception, which the
        answer carries (StudioError.answer, failed_answer), and its one line written to the request's log."""
        decided = self._binding_decided(ctx, decision, director)
        if decided:
            e.binding, e.binding_record = decided["binding"], decided["record"]
        extra = getattr(e, "line", None) or {}
        if not decided and not extra:
            return
        if ctx["op"] == "admit":
            line = {"id": ctx["rid"] if isinstance(ctx["rid"], str) else "", "at": now(), "decision": "admit-refused",
                    "candidate": ctx["letter"] if isinstance(ctx["letter"], str) else "", "code": decision}
        else:
            line = {"at": now(), "decision": "undo-refused", "of": ctx.get("target") or "", "code": decision}
        if director:
            line["director_code"] = director
        try:
            self._log(dict(line, **extra, **decided))
        except OSError:
            pass            # the record could not be written; the press is answered as it was decided

    def _binding_first_admit(self, rid, letter, still, preview, ctx):
        """The plant binding-first: the binding check made before every existing check of the press, against the
        candidate's evaluation at the head as the files stand (so that an order state is answered BINDING-*)."""
        D = self.play.director()
        ws = self.play.workspace()
        c = ctx.get("c")
        scene = ""
        if c is not None and c.get("intent") is not None:
            try:
                o1 = D.evaluate_doc(ws, D.canon.load_intent(c["intent"]))[3]
                scene = o1["lineage"]["scene_sha256"] if o1 is not None else ""
            except Exception:  # noqa: BLE001 — a plant's evaluation that fails leaves the scene unknown
                scene = ""
        with self.lock:
            st = (c or {}).get("still")
        st = st if st and isinstance(still, str) and still and st.get("sha256") == still else None
        entries = self._admission_entries(c or {}, st, preview, scene)
        code, names = press(entries)
        if code:
            ctx["entries"] = entries
            raise StudioError(code, binding_message(code, names, entries))

    def _admission(self, rid, letter, still="", despite=False, dry=False, ctx=None):
        """DASHBOARD-0 (0249): the checks of an admission, in admit()'s order, raising admit()'s refusal at the first that
        fails. One predicate: admit() runs it before it writes, and account() runs it dry, writing nothing, with the still
        pending (the page takes it as Admit is pressed: its presence and its detectors are checked then) and the
        director's own checks made as they would be made at the press (D.admit_dry: append_evaluation's guard, cmd_admit's
        checks and the commit's shared map), with a stand-in still the detectors flag nothing in. Returns what admit()
        goes on with."""
        r, c = self._candidate(rid, letter)
        if c["slot"] is None or c["intent"] is None:
            raise StudioError("STUDIO-NOT-ADMISSIBLE", "candidate %s was not drawn (%s)" % (letter, c["verdict"]))
        st, png = c.get("still"), None
        if ctx is not None:
            ctx["st"] = st if st and isinstance(still, str) and still and st.get("sha256") == still else None
        if not dry:
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
        # BINDING-0 (0253): the candidate scene at admission, the scene this admission's own evaluation exports (its
        # lineage.scene_sha256): never the card's kept value, never the scene a slot serves, never the page's
        scene = _o1["lineage"]["scene_sha256"] if _o1 is not None else ""
        if ctx is not None:
            ctx["scene"] = scene
        press_ = ctx is not None and not dry
        skip = False
        if press_ and binding_planted("binding-sufficient"):
            # the plant: a matched binding taken as sufficient, the studio's checks after the evaluation skipped
            skip = all(e["outcome"] == "MATCH" for e in self._admission_entries(c, ctx["st"], ctx["preview"], scene))
        if ACCOUNT_PLANT == "account-drops-stale" and dry:
            verdict = dict(verdict, checked_against=c["head"])
        if verdict["checked_against"] != c["head"] and not skip and not (press_ and binding_planted("stale-skipped")):
            raise StudioError("STUDIO-STALE", "the head moved since candidate %s was drawn (%s, now %s): ask again" % (letter, c["head"][:12], verdict["checked_against"][:12]))
        if verdict["verdict"] != "CLEAN" and not skip:
            raise StudioError("STUDIO-NOT-ADMISSIBLE", "candidate %s is %s (%s); only a CLEAN candidate is admitted here" % (letter, verdict["verdict"], ",".join(verdict["codes"])))
        region = None
        if r.get("strict") and not skip:
            # STRICT-0 (0238): checked again here, from this admission's own evaluation (never the card's), against the
            # shapes as the request kept them; refused, and the refusal recorded with its reason, unless every box the
            # candidate changes lies within their regions
            rep = strict_check(_o0["scene"], _o1["scene"], r.get("shape_recs", ())) if _o0 is not None and _o1 is not None else \
                {"ok": False, "code": "ADMIT-STALE", "error": "the candidate did not export"}
            if STRICT_PLANT == "strict-any-region" and rep.get("count"):
                rep = dict(rep, ok=any(x["inside"] for x in rep["receipt"]), code="")
            if STRICT_PLANT == "strict-not-checked":
                rep = dict(rep, ok=True, code="")
            if not rep["ok"]:
                e = StudioError(rep["code"], "candidate %s is not held by the request's regions (strict): %s" % (letter, (
                    "%d of its %d boxes outside every region: %s" % (rep["outside_count"], rep["count"], ", ".join(rep["outside"][:6])) if rep.get("outside_count")
                    else "it changes the whole world: " + ", ".join(rep["global"][:6]) if rep.get("global")
                    else rep.get("error") or ("its shapes are not as marked: " + ", ".join("#" + n for n in rep.get("stale", []))) if rep["code"] == "ADMIT-STALE"
                    else "it changes nothing a region could hold")))
                if not dry:
                    # the refusal recorded with its reason: on the press's one line (admit() writes it, with the decision
                    # record, BINDING-0 0253), as before 0253 on a line of its own
                    e.line = {"strict": strict_line(rep, "")}
                    if ctx is None:
                        self._log({"id": rid, "at": now(), "decision": "admit-refused", "candidate": letter, "code": rep["code"], "strict": e.line["strict"]})
                raise e
            region = {"strict": True, "ok": rep["ok"], "shapes": rep["shapes"],
                      "support_sha256": sha256(json.dumps(r.get("shape_recs", []), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")),
                      "count": str(rep["count"]), "receipt": rep["receipt"], "receipt_sha256": rep["receipt_sha256"],
                      "inverse_receipt": rep["inverse_receipt"], "inverse_receipt_sha256": rep["inverse_receipt_sha256"]}
            if STRICT_PLANT == "strict-no-receipt":
                region = {k: v for k, v in region.items() if k not in ("receipt", "inverse_receipt")}
        if not dry and st["flags"] and not despite and not skip:
            raise StudioError("STUDIO-STILL-FLAGGED", "candidate %s's still: %s. A detector proves nothing: admit despite it, which the ledger "
                                                      "records, or reject the candidate" % (letter, "; ".join(st["flags"])))
        if dry:
            # the director's checks at the press, made now and nothing appended: what quiet() makes of their refusals
            try:
                events = D.led.read(ws.ledger)[0]
                if ACCOUNT_PLANT != "account-director-skipped":
                    D.admit_dry(ws, events, D.evaluation_fields(c["intent"], verdict, after, timings, rec),
                                still=D.selftest_still(), despite=bool(despite), region=region)
            except (SystemExit, led.LedgerError) as e:
                raise director_refusal(e)
        return r, c, st, png, it, verdict, after, timings, rec, region

    def account(self, rid, letter, despite=False):
        """DASHBOARD-0 (0249): the host's account of admitting candidate `letter` of request `rid` now. It is admit()'s
        own predicate run dry (_admission): its first refusal, with admit()'s code and the director's, or none; the
        still is pending (taken by the page as Admit is pressed, its detectors read then), and the checks after the first
        refusal are not reached, as at the press. It writes nothing, and decides nothing: the press checks again.
        BINDING-0 (0253, v0 order.account): it checks no binding whose evidence is declared only with the press (the
        still's scene, whether a preview is named) and never reports one as checked or matched."""
        got = self._account(rid, letter, despite)
        if binding_planted("account-claims-binding"):
            got = dict(got, binding={"checked": True, "outcome": "MATCH"})
        return got

    def _account(self, rid, letter, despite=False):
        D = self.play.director()
        ws = self.play.workspace()
        if os.path.isdir(ws.pending):
            # a dead writer's half-done admission: the press recovers it under the content lock before its checks, so its
            # refusal is not foreseen here; nothing is said that the press might not say
            return {"ok": False, "first": None, "not_foreseen": "an admission half written by a writer that ended: the press recovers it first, so its answer is not foreseen"}
        try:
            self._admission(rid, letter, despite=despite, dry=True)
        except StudioError as e:
            return {"ok": False, "first": {"code": e.code, "director_code": e.director, "why": e.detail[:600]}}
        except failures(self.play.director()) as e:
            a = failed_answer(e)
            return {"ok": False, "first": {"code": a["code"], "director_code": "", "why": a["message"]}}
        except Exception as e:  # noqa: BLE001 — what the press is answered for anything else (art/play.py, internal)
            return {"ok": False, "first": {"code": "STUDIO-INTERNAL", "director_code": "", "why": "%s: %s" % (type(e).__name__, str(e)[:200])}}
        return {"ok": True, "first": None}

    def accounts(self):
        """DASHBOARD-0 (0249): every candidate's account (account()) of the request shown now, and its EVIDENCE-0
        checklist's missing items; what /live carries for the cards. Computed by the host's worker (art/play.py,
        Live.accounts_loop), never by the page."""
        with self.lock:
            r = self.req
            if not r or r["state"] != "done":
                return {"request": r["id"] if r else "", "by_letter": {}}
            rid, cands = r["id"], [(c["letter"], c) for c in r["candidates"]]
            shapes, strict = list(r.get("shapes", [])), bool(r.get("strict"))
            paths = drawn_paths(r)
        out = {}
        for letter, c in cands:
            acc = self.account(rid, letter)
            chk = evidence_checklist({"shapes": shapes, "strict": strict, "paths": paths}, c)
            despite = self.account(rid, letter, despite=True) if acc["ok"] and (c.get("still") or {}).get("flags") else None
            out[letter] = dict(acc, evidence={"missing": chk["missing"], "of": chk["of"], "next": chk["next"]},
                               despite={"ok": bool(despite and despite["ok"]), "flags": list((c.get("still") or {}).get("flags") or [])} if despite else None)
        return {"request": rid, "by_letter": out}

    def evidence(self, rid, letter):
        """DASHBOARD-0 (0249): what the host holds of a candidate's admission and its evidence, read and never written:
        the admission's account (account(): admit()'s own checks, run dry), EVIDENCE-0's checklist (advisory: the
        studio's admission reads none of it), and the evidence itself (the record, the held and strict reports, the
        impact as an ESTIMATE, the preview's report with its binding, the still with the scene the page named, the
        certificate)."""
        with self.lock:
            r = self.req
            if not r or r["id"] != rid:
                raise StudioError("STUDIO-NO-CANDIDATE", "no request %s is shown" % (rid if isinstance(rid, str) else "")[:40])
            got = [x for x in r["candidates"] if x["letter"] == letter]
            if not got:
                raise StudioError("STUDIO-NO-CANDIDATE", "request %s has no candidate %s" % (rid, letter if isinstance(letter, str) else ""))
            c = dict(got[0])
            shapes, strict, state = list(r.get("shapes", [])), bool(r.get("strict")), r["state"]
            paths = drawn_paths(r)
        acc = self.account(rid, letter) if state == "done" else {"ok": False, "first": {"code": "STUDIO-NO-CANDIDATE", "director_code": "",
                                                                                         "why": "the request is %s" % state}}
        imp = c.get("impact") or {}
        rep = c.get("preview_report") or {}
        st = c.get("still") or {}
        return {"request": rid, "candidate": letter,
                "admission": dict(acc, pending=[{"what": "still", "why": "taken from the canvas as Admit is pressed; its presence and its "
                                                                        "detectors are checked then (ADMISSION-0)"}],
                                  rule="the admission's own checks, run dry (Gateway._admission; the director's admit_dry): its first refusal"),
                "checklist": evidence_checklist({"shapes": shapes, "strict": strict, "paths": paths}, c),
                "items": {"verdict": c.get("verdict", ""), "codes": c.get("codes", []), "record": c.get("record"), "head": c.get("head", ""),
                          "written_against": c.get("written_against", ""), "base_sha": c.get("base_sha", ""), "scene": c.get("scene", ""),
                          "held": {k: v for k, v in c["held"].items() if k != "boxes"} if c.get("held") else None, "strict": c.get("strict"),
                          "impact": {"label": "ESTIMATE", "advisory": imp.get("advisory", ""), "delta": imp.get("delta"), "estimate": imp.get("estimate"),
                                     "flag": imp.get("flag", ""), "error": imp.get("error", "")} if imp else None,
                          "preview": {"replayed": rep.get("replayed"), "state_verified": rep.get("state_verified"), "code": rep.get("code", ""),
                                      "path_id": rep.get("path_id", ""), "binding": c.get("preview_binding"), "drawn": c.get("preview_drawn"),
                                      "drawn_ok": drawn_ok(c.get("preview_binding"), c.get("preview_drawn"))} if rep else None,
                          "still": {"sha256": st.get("sha256", ""), "flags": st.get("flags", []), "scene": st.get("scene", ""),
                                    "scene_is_candidate": bool(st.get("scene")) and st.get("scene") == c.get("scene")} if st else None,
                          "certificate": c.get("certificate"), "decided": c.get("decided", "")}}

    # ------------------------------------------------------------------ PREVIEW-0 (0240): the preview in motion
    def _drawn(self, rid, letter):
        with self.lock:
            r = self.req
            if not r or r["id"] != rid or r["state"] != "done":
                raise StudioError("STUDIO-NO-CANDIDATE", "no finished request %s" % (rid if isinstance(rid, str) else "")[:40])
            c = [x for x in r["candidates"] if x["letter"] == letter]
            if not c or c[0]["slot"] is None or c[0]["intent"] is None:
                raise StudioError("STUDIO-NO-CANDIDATE", "request %s has no drawn candidate %s" % (rid, letter if isinstance(letter, str) else ""))
            return r, c[0]

    def preview_plan(self, rid, letter):
        """Both sides played along the request's path with its seed (art/motion.py plan), from the candidate's own
        evaluation at the head as the files stand; the page then draws a still of each side at each pose."""
        r, c = self._drawn(rid, letter)
        D = self.play.director()
        ws = self.play.workspace()
        verdict, _a, _t, o1, o0, _x, _r = D.evaluate_doc(ws, D.canon.load_intent(c["intent"]))
        if verdict["checked_against"] != c["head"]:
            raise StudioError("PREVIEW-STALE", "the head moved since candidate %s was drawn: ask again" % letter)
        if o1 is None or o0 is None:
            raise StudioError("PREVIEW-NO-PLAN", "candidate %s did not export, so it has no motion to show" % letter)
        path = r.get("path") or self._path(o0["scene"], (), None, rid)
        if not path.get("poses"):
            raise StudioError("PREVIEW-NO-PATH", "the request has no camera path: %s" % path.get("refused", "none was made"))
        p = motion.plan(o0, o1, path, path["seed"])
        # PATH-0: the path made at the head, held again to the rule against the candidate's own scene (a candidate may
        # put a box where a pose stands): said in the plan and the report, never moved
        p["path_check"] = {"id": path["id"], "rule": camera.RULE, "base": camera.check(o0["scene"], path), "candidate": camera.check(o1["scene"], path)}
        if path.get("subject"):
            # FRAME-0: the subject framed in each scene along the one path (a candidate may hide or move what it frames)
            p["framing"] = {"subject": path["subject"], "rule": camera.FRAME_RULE,
                            "base": camera.framing(o0["scene"], path, path["subject"]), "candidate": camera.framing(o1["scene"], path, path["subject"])}
        # DASHBOARD-0 (0249): the scenes the plan is of (the base and the candidate of this evaluation), so that the page
        # draws its stills from them and says when it did not; recorded, never refused on (R8)
        binding = {"head": verdict["checked_against"], "base_sha": o0["lineage"]["scene_sha256"], "candidate_sha": o1["lineage"]["scene_sha256"]}
        with self.lock:
            c["preview"] = {"plan": p, "stills": {}, "drawn": {}}
            c["preview_binding"] = binding
        return {"path_id": p["path_id"], "path_check": p["path_check"], "framing": p.get("framing"), "seed": p["seed"], "spawn": p["spawn"], "poses": p["poses"], "still_ticks": p["still_ticks"], "ticks": p["ticks"],
                "viewport": p["viewport"], "frames": p["frames"], "first_difference": p["first_difference"], "sim_ms": p["sim_ms"],
                "slots": {"base": 0, "candidate": c["slot"]}, "binding": binding}

    def preview_still(self, rid, letter, side, k, png, scene=""):
        r, c = self._drawn(rid, letter)
        pv = c.get("preview")
        if not pv:
            raise StudioError("PREVIEW-NO-PLAN", "no preview of candidate %s is under way: ask for its plan first" % letter)
        if side not in ("base", "candidate") or not isinstance(k, int) or not 0 <= k < len(pv["plan"]["still_ticks"]):
            raise StudioError("PREVIEW-STILL", "a still is of the base or the candidate, at one of the plan's poses")
        try:
            import quality
            quality.decode_png(png)
        except Exception as e:  # noqa: BLE001 — a still the host cannot read is refused, never kept
            raise StudioError("PREVIEW-STILL", "the still is not an 8-bit RGB or RGBA PNG: %s" % str(e)[:120])
        scene = keep(scene)          # BINDING-0 (0253): by the still's rule
        with self.lock:
            pv["stills"][(side, k)] = png
            pv.setdefault("drawn", {})["%s-%d" % (side, k)] = scene
        return {"side": side, "pose": k, "sha256": sha256(png), "scene": scene}

    def preview_finish(self, rid, letter):
        """The preview's report (art/motion.py report), its four files kept beside the intent and its stills in a folder
        of their own, and one line of the request's record naming them by their sha256 (which outlives their retention)."""
        r, c = self._drawn(rid, letter)
        pv = c.get("preview")
        if not pv:
            raise StudioError("PREVIEW-NO-PLAN", "no preview of candidate %s is under way" % letter)
        p, stills = pv["plan"], dict(pv["stills"])
        rep = motion.report(p, stills, c.get("preview_report"))
        prov = (c.get("impact") or {}).get("provenance") or {}
        meta = {"format": motion.FORMAT, "version": motion.VERSION, "request": rid, "candidate": letter, "provider": prov.get("producer", ""),
                "model": prov.get("model", ""), "prompt_sha256": prov.get("prompt_sha256") or sha256(r.get("prompt", "").encode("utf-8")),
                "camera_path_id": p["path_id"], "viewport": p["viewport"], "framerate": p["framerate"], "tick_count": p["ticks"], "seed": p["seed"],
                "spawn": p["spawn"], "still_ticks": p["still_ticks"], "semantics": p["semantics"], "made_at": time.time()}
        rep["provenance"] = {k: meta[k] for k in ("request", "candidate", "provider", "model", "prompt_sha256")}
        files = motion.artifacts(p, stills, rep, meta)
        shas = {}
        for name, data in sorted(files.items()):
            self._record(rid, "%s.%s" % (letter, name), data)
            shas[name] = sha256(data)
        for (side, k), data in sorted(stills.items()):
            self._record(rid, "%s.stills/%s-%d.png" % (letter, side, k), data)
        sheet = motion.compare_sheet(p, stills)
        if sheet is not None:
            # FRAME-0: the sheet a person inspects (both stills at each pose and the subject's crops), named by its sha256
            self._record(rid, "%s.preview.compare.png" % letter, sheet)
            shas["preview.compare.png"] = sha256(sheet)
        drawn = dict(pv.get("drawn") or {})
        # BINDING-0 (0253): the finished preview's id, which an admission names it by (`preview`), over what it declared:
        # its binding as recorded at its plan, the scene kept for each still drawn for it, its report's sha256; kept under
        # that id with its binding and its drawn scenes, never overwritten by a later plan or finish
        binding = dict(c.get("preview_binding") or {})
        pid = preview_id(binding, drawn, shas["preview.report.json"])
        with self.lock:
            c["preview_report"] = rep
            c["preview_drawn"] = drawn
            c.pop("preview", None)
            c.setdefault("previews", {}).setdefault(pid, {"binding": binding, "drawn": drawn})
        self._log({"id": rid, "at": now(), "decision": "preview", "candidate": letter, "replayed": rep["replayed"], "state_verified": rep["state_verified"],
                   "code": rep["code"], "path_id": p["path_id"], "seed": p["seed"], "files": shas,
                   "binding": c.get("preview_binding"), "drawn": drawn, "drawn_ok": drawn_ok(c.get("preview_binding"), drawn), "preview_id": pid})
        motion.gc(self.records, motion.RETENTION_DAYS)          # the previews past their retention; their sha256 stay on their lines
        # DASHBOARD-0: the answer (never the report's file) names the plan's scenes and whether the stills were drawn from them
        return dict(rep, files=shas, binding=c.get("preview_binding"), drawn_ok=drawn_ok(c.get("preview_binding"), drawn), preview_id=pid)

    def preview_report(self, rid, letter):
        r, c = self._drawn(rid, letter)
        if not c.get("preview_report"):
            raise StudioError("PREVIEW-NO-PLAN", "candidate %s has no preview yet" % letter)
        return c["preview_report"]

    def preview_png(self, rid, letter, side, k):
        self._drawn(rid, letter)
        if side not in ("base", "candidate", "compare") or not re.match(r"[0-9]{1,3}\Z", str(k)):
            raise StudioError("PREVIEW-STILL", "a still is of the base or the candidate, at one of the plan's poses")
        f = os.path.join(self.records, rid, "%s.stills" % letter, "%s-%s.png" % (side, k)) if side != "compare" \
            else os.path.join(self.records, rid, "%s.preview.compare.png" % letter)
        if not os.path.exists(f):
            raise StudioError("PREVIEW-STILL", "no still %s %s of candidate %s" % (side, k, letter))
        return open(f, "rb").read()

    def _compared(self, r, chosen):
        """COMPARE-0 (0235): one admission (or none) is chosen from a set, and the record says so: what was shown, in the
        host's order, with each one's region verdicts, what was chosen, and which were not. A candidate not chosen is
        marked so for the page and stays undecided: rejecting it still writes its refusal to the ledger, and admitting it
        is refused as it was (the head moved: STUDIO-STALE). Holds the lock."""
        not_chosen = []
        for x in r["candidates"]:
            if x["letter"] != chosen and not x["decided"]:
                x["compared"] = "not chosen" if chosen else "none chosen"
                not_chosen.append(x["letter"])
        return {"shown": [x["letter"] for x in r["candidates"] if x["slot"] is not None], "order": [o["letter"] for o in r.get("order", [])],
                "chosen": chosen or None, "not_chosen": not_chosen,
                "held": {x["letter"]: held_line(x) for x in r["candidates"] if x.get("held")}}

    def none(self, rid):
        """COMPARE-0: none of a request's candidates is chosen: every one not decided is marked so, and one line records
        the set rejected. The ledger is not written (it holds what is admitted and what is rejected one by one); the world
        is as it was."""
        with self.lock:
            r = self.req
            if not r or r["id"] != rid or r["state"] != "done":
                raise StudioError("STUDIO-NO-CANDIDATE", "no finished request %s" % rid)
            if not any(not x["decided"] and not x.get("compared") for x in r["candidates"]):
                raise StudioError("STUDIO-DECIDED", "every candidate of request %s is already decided, or none was chosen" % rid)
            comparison = self._compared(r, "")
            self.last = {"what": "none", "request": rid, "candidates": comparison["not_chosen"]}
        self._log({"id": rid, "at": now(), "decision": "none", "comparison": comparison})
        return self.last

    def held(self, rid, letter):
        """HELD-0: a candidate's whole report (with the boxes Diff mode outlines), as its evaluation computed it."""
        with self.lock:
            r = self.req
            if not r or r["id"] != rid or r["state"] != "done":
                raise StudioError("STUDIO-NO-CANDIDATE", "no finished request %s" % (rid if isinstance(rid, str) else "")[:40])
            c = [x for x in r["candidates"] if x["letter"] == letter]
            if not c or not c[0].get("held"):
                raise StudioError("STUDIO-NO-CANDIDATE", "request %s has no candidate %s with a report" % (rid, letter if isinstance(letter, str) else ""))
            return dict(c[0]["held"], letter=letter, request=rid)

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
        ev = quiet(D.append_evaluation, ws, c["intent"], verdict, after, timings, rec)
        x = quiet(D.cmd_refuse, ws, ev["seq"], chooser="the designer (studio)", note="request %s, candidate %s" % (rid, letter))
        with self.lock:
            c["decided"] = "rejected"
            self.last = {"what": "rejected", "request": rid, "candidate": letter, "ledger": [ev["seq"], x["seq"]]}
        self._log({"id": rid, "at": now(), "decision": "reject", "candidate": letter, "ledger": [ev["seq"], x["seq"]]})
        return self.last

    @staticmethod
    def _latest_admission(events):
        """The latest admission not yet undone (an undo is never itself undone), or None: the admission Undo is about,
        undoable or not (BINDING-0's record names it as the undo's `of`, a layout admission's among them)."""
        admits = [e for e in events if e["kind"] == "admit"]
        undo_of = lambda e: e.get("observed", {}).get("note", "")[len(UNDO_NOTE):] if e.get("observed", {}).get("note", "").startswith(UNDO_NOTE) else None
        undone = {undo_of(e) for e in admits if undo_of(e) is not None}
        left = [e for e in admits if undo_of(e) is None and e["seq"] not in undone]
        return left[-1] if left else None

    @staticmethod
    def _undo_target(events):
        """The admission Undo undoes: the latest not yet undone (an undo is never itself undone); refused as undo()'s choice
        of a target is (STUDIO-NOTHING-TO-UNDO; STUDIO-NOT-UNDOABLE for a layout admission)."""
        a = Gateway._latest_admission(events)
        if a is None:
            raise StudioError("STUDIO-NOTHING-TO-UNDO", "every admission in the ledger is undone, or an undo")
        if a.get("design_lines"):
            raise StudioError("STUDIO-NOT-UNDOABLE", "the last admission (#%s) changed the layout; undo it through the design tool" % a["seq"])
        return a

    def undo_target(self):
        """DASHBOARD-0 (0249): what Undo would undo now, read and never written: the admission (its sequence number, the
        request and candidate its note names), the head it moved the world from (the head an exact restoration gives
        back) and to, and that admission's certificate (the kept one, checked; else one made from the ledger now and not
        kept). Whether Undo would be refused is undo()'s own checks run dry (_undoing), never a second rule: `can` false
        with its first refusal's code (and the director's) when the press would be refused, as of the ledger and the files
        read now; the press reads them again. BINDING-0 (0253, v0 order.account): `scene`, the world's scene its dry run
        laid the inverse over, the value the undo will declare beside `of`; "" where it answers before its dry run (no
        target, a layout target, a pending folder); never a binding checked or matched."""
        got = self._undo_account()
        if binding_planted("account-claims-binding"):
            got = dict(got, binding={"checked": True, "outcome": "MATCH"})
        return got

    def _undo_account(self):
        D = self.play.director()
        ws = self.play.workspace()
        try:
            events = D.led.read(ws.ledger)[0]
        except (SystemExit, led.LedgerError) as e:
            raise director_refusal(e)
        try:
            a = self._undo_target(events)
        except StudioError as e:
            return {"can": False, "code": e.code, "director_code": e.director, "message": e.detail, "scene": ""}
        note = a.get("observed", {}).get("note", "")
        m = re.match(r"request (\S+), candidate ([A-Z])\Z", note)
        out = {"can": True, "code": "", "director_code": "", "message": "", "of": a["seq"], "request": m.group(1) if m else "",
               "candidate": m.group(2) if m else "", "note": note[:160], "from_head": a["head_after"], "would_restore": a["head_before"],
               "undone_certificate": self._certificate_of(D, ws, events, int(a["seq"]), keep=False), "scene": ""}
        if os.path.isdir(ws.pending):
            out.update(can=None, message="an admission half written by a writer that ended: the press recovers it first, so its answer is not foreseen")
            return out
        seen = {}
        try:
            self._undoing(dry=True, seen=seen)
        except StudioError as e:
            out.update(can=False, code=e.code, director_code=e.director, message=e.detail[:600])
        except failures(D) as e:
            out.update(can=False, code="STUDIO-FAILED", message=failed_answer(e)["message"])
        out["scene"] = seen.get("scene", "")
        return out

    @staticmethod
    def _inverse_clean(a, verdict, recorded=""):
        """undo()'s rule for its inverse: admitted only when its verdict is CLEAN (the press says where it recorded it)."""
        if verdict["verdict"] != "CLEAN":
            raise StudioError("STUDIO-NOT-UNDOABLE", "the inverse of #%s is %s (%s), %s" % (
                a["seq"], verdict["verdict"], ",".join(verdict["codes"]),
                ("recorded as #%s and not admitted" % recorded) if recorded else "which the press records and does not admit"))

    def _undoing(self, dry=False, record=None, seen=None):
        """DASHBOARD-0 (0249): an undo's checks, in undo()'s order and in this one place, raising its refusal at the first
        that fails: the target (_undo_target); the inverse evaluated at the files' head; append_evaluation's guard (the
        press: `record`, which appends the evaluation under it; dry: held_head at that head, nothing appended); the
        inverse's verdict (_inverse_clean); cmd_admit's checks with the inverse it names (dry: D.admit_dry; the press runs
        cmd_admit itself). undo() runs it and goes on to write; undo_target() runs it dry. Returns (the admission undone,
        the inverse's bytes, its intent, the evaluation appended or None). A ledger that does not read is the director's
        refusal on both paths. BINDING-0 (0253): `seen`, when given, is told the admission Undo is about ("target", its
        sequence number, "" when there is none) and the scene at the undo ("scene": the scene the inverse's evaluation
        lays it over, the files' as they stand, its base's lineage.scene_sha256), as soon as each is known."""
        D = self.play.director()
        ws = self.play.workspace()
        seen = {} if seen is None else seen
        try:
            events, _l, _h = D.led.read(ws.ledger)
        except (SystemExit, led.LedgerError) as e:
            raise director_refusal(e)
        seen["target"] = (self._latest_admission(events) or {}).get("seq", "")
        a = self._undo_target(events)
        src = D.canon.load_intent(events[int(a["evaluation"])]["intent"].encode("ascii"))
        _o, parts, _c = ws.export()
        doc = {"base": {k: parts[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}, "brief": self.brief, "candidate": "U",
               "format": "VERDANDI-INTENT", "layout": [], "prompt": "undo: " + src["prompt"],
               "rationale": "The exact inverse of admission #%s (candidate %s), restoring the statements it changed." % (a["seq"], src["candidate"]),
               "revision": list(a["inverse"]), "scope": list(src["scope"]), "version": "0"}
        raw = D.canon.dumps(doc)
        it = D.canon.load_intent(raw)
        verdict, after, timings, _o1, _o0, _t, rec = D.evaluate_doc(ws, it)
        seen["scene"] = _o0["lineage"]["scene_sha256"] if _o0 is not None else ""
        if dry and ACCOUNT_PLANT == "undo-dry-skipped":
            return a, raw, it, None
        ev = None
        if dry:
            try:
                D.held_head(ws, events, verdict["checked_against"])
            except (SystemExit, led.LedgerError) as e:
                raise director_refusal(e)
        else:
            ev = record(raw, verdict, after, timings, rec)
        self._inverse_clean(a, verdict, ev["seq"] if ev else "")
        if dry:
            try:
                D.admit_dry(ws, events, D.evaluation_fields(raw, verdict, after, timings, rec), inverse_of=a["seq"])
            except (SystemExit, led.LedgerError) as e:
                raise director_refusal(e)
        return a, raw, it, ev

    def undo(self, of=ABSENT, scene=ABSENT):
        """Undo at the level of intent: the latest admission not yet undone (an undo is never itself undone; undo again
        walks further back), its exact inverse admitted as an intent of its own. DASHBOARD-0 (0249): the answer proves
        what came back (`restoration`), from the ledger: the head before the admission against the head after the undo,
        the art's bytes and its statements, the parts that differ, and the undone admission's certificate. BINDING-0
        (0253): every undo through the host names the admission it reverses (`of`) and the scene it was shown as reversing
        (`scene`), as GET /undo.json gave them (ABSENT, the key not in the body, declares none: BINDING-UNKNOWN); `of` is
        held to the undo target's sequence number and `scene` to the scene at the undo, after every existing check (the
        commit's own under the content lock included) and before the undo's first write. Every press is decided with its
        decision record, on the answer and the log line, whatever it answers."""
        D = self.play.director()
        ctx = {"op": "undo", "of": of, "scene": scene, "entries": None, "target": ""}
        try:
            return self._undo(of, scene, ctx)
        except StudioError as e:
            self._decided(ctx, e, e.code, e.director)
            raise
        except failures(D) as e:
            self._decided(ctx, e, "STUDIO-FAILED", "")
            raise

    def _undo_entries(self, of, scene, target, at_scene, refreshed=False):
        """An undo's evidence compared, in precedence order: `of` against the undo target's sequence number, then `scene`
        against the scene at the undo. `refreshed` is the plant binding-refreshed."""
        def decl(v, now_):
            if refreshed:
                return {"present": True, "value": now_}
            return {"present": False} if v is ABSENT else {"present": True, "value": v}
        return [compare("undo", "of", decl(of, target), target), compare("undo", "scene", decl(scene, at_scene), at_scene)]

    def _binding_first_undo(self, of, scene, ctx):
        """The plant binding-first: the undo's binding checked before every existing check of the press, against the
        admission the ledger names as Undo's (any, a layout one too) and the scene the files export as they stand."""
        D = self.play.director()
        ws = self.play.workspace()
        try:
            target = (self._latest_admission(D.led.read(ws.ledger)[0]) or {}).get("seq", "")
        except Exception:  # noqa: BLE001 — a plant's reading that fails leaves the target unknown
            target = ""
        try:
            at_scene = ws.export()[0]["lineage"]["scene_sha256"]
        except Exception:  # noqa: BLE001 — likewise the scene
            at_scene = ""
        entries = self._undo_entries(of, scene, target, at_scene)
        code, names = press(entries)
        if code:
            ctx["entries"], ctx["target"] = entries, target
            raise StudioError(code, binding_message(code, names, entries))

    def _undo(self, of, scene, ctx):
        D = self.play.director()
        ws = self.play.workspace()
        if binding_planted("binding-first"):
            self._binding_first_undo(of, scene, ctx)
        seen = {}
        try:
            a, raw, it, ev = self._undoing(record=lambda raw_, v_, af_, t_, r_: quiet(D.append_evaluation, ws, raw_, v_, af_, t_, r_), seen=seen)
        finally:
            ctx["target"] = seen.get("target", "")
        parent_text = ws.text()

        def gate():
            # BINDING-0 (0253): the undo's binding check, called by the director's commit under the content lock after
            # every check it makes and before its first write; `of` and `scene` as the request gave them
            if binding_planted("binding-removed"):
                return
            entries = self._undo_entries(of, scene, a["seq"], seen.get("scene", ""), refreshed=binding_planted("binding-refreshed"))
            ctx["entries"] = entries
            code, names = press(entries)
            if code:
                raise StudioError(code, binding_message(code, names, entries))
        u = quiet(D.cmd_admit, ws, ev["seq"], chooser="the designer (studio)", note=UNDO_NOTE + a["seq"], inverse_of=a["seq"], gate=gate)
        cert = self._certify(ws, u, list(a["inverse"]), parent_text, {"producer": "undo", "of": a["seq"]})
        # CERT-0: whether the undo gave back the head before the admission it undoes (exactly when that admission's
        # certificate is exact; otherwise its statements and its scene, under another head: said, never hidden)
        restored = {"head": u["head_after"] == a["head_before"]}
        try:
            restoration = self._restoration(D, ws, a, u, cert)
        except Exception as e:  # noqa: BLE001 — the undo is in the ledger; a proof that cannot be read is said, never an undo answered as failed
            restoration = {"of": a["seq"], "verdict": "unknown", "head": None, "art_bytes": None, "statements": None, "parts_differ": [],
                           "expected_head": a["head_before"], "from_head": a["head_after"], "undone_at": u["head_before"], "head_after": u["head_after"], "undone_certificate": {},
                           "ledger": {"seq": u["seq"], "held_after": "unknown"},
                           "said": "the restoration could not be read: %s: %s" % (type(e).__name__, str(e)[:200])}
        of_ = None if of is ABSENT else of
        page_saw = {"of": str(of_) if of_ not in (None, "") else "", "matched": None if of_ in (None, "") else str(of_) == str(a["seq"])}
        decided = self._binding_decided(ctx, "UNDONE", "")
        with self.lock:
            self.last = dict({"what": "undone", "of": a["seq"], "ledger": [ev["seq"], u["seq"]], "head": u["head_after"], "certificate": cert,
                              "head_restored": u["head_after"] == a["head_before"], "restoration": restoration, "page_saw": page_saw}, **decided)
        self._log(dict({"at": now(), "decision": "undo", "of": a["seq"], "ledger": [ev["seq"], u["seq"]], "head_after": u["head_after"], "certificate": cert,
                        "head_restored": restored["head"], "page_saw": page_saw,
                        "restoration": {k: restoration[k] for k in ("verdict", "head", "art_bytes", "statements", "parts_differ")}}, **decided))
        return self.last

    def _restoration(self, D, ws, a, u, own_cert):
        """DASHBOARD-0 (0249): what the undo `u` of the admission `a` gave back, from the ledger alone (two replays; the
        files are read only for held_after, under the content lock): the head before `a` against the head after `u`, the art's bytes, its statements
        (certificate.statements: what the exporter reads), the parts that differ, and `a`'s own certificate (the kept one
        checked, or one made from the ledger and kept now). Its verdict: exact (the head came back, and so every part and
        byte), statements-not-bytes (the art's statements came back and nothing but its bytes differs), or not-restored
        (naming what differs). The undo's own certificate (`own_cert`, a redo's inverse) is another thing, and never this."""
        events = D.led.read(ws.ledger)[0]
        i_a, i_u = int(a["seq"]), int(u["seq"])
        parent, after = D.replay(ws, events[:i_a]), D.replay(ws, events[:i_u + 1])
        differ = [p[:-len("_sha256")] for p in ("art_sha256", "world_sha256", "exporter_sha256") if after["parts"].get(p) != parent["parts"].get(p)]
        head = after["head"] == parent["head"]
        art_bytes = after["art"].encode("utf-8") == parent["art"].encode("utf-8")
        same_statements = certificate.statements(after["art"]) == certificate.statements(parent["art"])
        verdict = "exact" if head else "statements-not-bytes" if same_statements and differ == ["art"] else "not-restored"
        if ACCOUNT_PLANT == "restoration-from-own-certificate":
            verdict = "exact" if own_cert.get("exact") else "not-restored"
        # held_after: the ledger and the files read again under the content lock (a reader of both, as the launcher's
        # inspect), so that no admission stands between its append and its files when they are compared
        try:
            with durable.locked(led.lock_path(ws.ledger), wait=5):
                D.held_head(ws, D.led.read(ws.ledger)[0])
            held_after = "held"
        except durable.Busy:
            held_after = "BUSY"
        except Exception as e:  # noqa: BLE001 — a reading after the undo is in the ledger: named, never raised (SystemExit is caught below)
            held_after = director_code(e) or type(e).__name__
        except SystemExit as e:
            held_after = director_code(e) or type(e).__name__
        said = {"exact": "restored exactly: the head before the admission came back",
                "statements-not-bytes": "the statements came back, the bytes did not: the head before the admission did not come back",
                "not-restored": "NOT restored: %s differ%s; the statements %s back" % (
                    " and ".join(differ) or "nothing", "s" if len(differ) == 1 else "", "came" if same_statements else "did not come")}[verdict]
        return {"of": a["seq"], "expected_head": parent["head"], "from_head": a["head_after"], "undone_at": u["head_before"], "head_after": after["head"], "head": head,
                "art_bytes": art_bytes, "statements": same_statements, "parts_differ": differ,
                "undone_certificate": self._certificate_of(D, ws, events, i_a, keep=True),
                "ledger": {"seq": u["seq"], "held_after": held_after}, "verdict": verdict, "said": said}

    def _kept_is_own(self, D, ev):
        """Whether the kept certificates/<seq>.json is this admit event's own (it names this event's sequence number and the
        sha256 of its bytes): a ledger started again keeps old numbers, and an old file is never taken for a new event's.
        DASHBOARD-0 (0249)."""
        path = os.path.join(self.records, "certificates", "%s.json" % ev["seq"])
        try:
            cert = json.loads(open(path, "rb").read().decode("utf-8"))
        except (OSError, ValueError):
            return False
        return (cert.get("ledger") or {}).get("seq") == ev["seq"] and (cert.get("ledger") or {}).get("event_sha256") == sha256(D.canon.dumps(ev))

    def _ledger_certificate(self, D, ws, events, i, producer):
        """The certificate of the art admission events[i], made from the ledger alone (recover_certificates'): the
        parent's and the child's texts replayed, the operation the admitted evaluation's revision. (cert, child text)."""
        ev = events[i]
        parent = D.replay(ws, events[:i])["art"]
        src = D.canon.load_intent(events[int(ev["evaluation"])]["intent"].encode("ascii"))
        child = D.replay(ws, events[:i + 1])["art"]
        return certificate.make(self.brief, ev, src["revision"], parent, child, {"producer": producer, "note": ev.get("observed", {}).get("note", "")},
                                "", src["candidate"]), child

    def _certificate_of(self, D, ws, events, i, keep):
        """DASHBOARD-0 (0249): the certificate of the admission events[i], as the host holds it: the kept file checked
        against the child's text replayed; else one made from the ledger now, kept only when `keep` (a POST; a GET writes
        nothing). What a page is shown of it, with `made` saying which."""
        ev = events[i]
        path = os.path.join(self.records, "certificates", "%s.json" % ev["seq"])
        try:
            other = ""
            if os.path.exists(path):
                cert = json.loads(open(path, "rb").read().decode("utf-8"))
                # the kept file is this event's only if it names this event's bytes (a ledger started again keeps old numbers)
                if self._kept_is_own(D, ev):
                    child = D.replay(ws, events[:i + 1])["art"]
                    res = certificate.check(cert, child)
                    return {"seq": ev["seq"], "ok": res["ok"], "exact": res["exact"], "statements": res["statements"], "codes": res["codes"], "made": "kept"}
                other = " (the kept file was another event's)"
            cert, child = self._ledger_certificate(D, ws, events, i, "made from the ledger for the undo's proof (0249)")
            if keep:
                kept = self._keep_certificate(cert, child)
                return dict({k: kept[k] for k in ("seq", "ok", "exact", "statements", "codes")}, made="from the ledger, kept now" + other)
            res = certificate.check(cert, child)
            return {"seq": ev["seq"], "ok": res["ok"], "exact": res["exact"], "statements": res["statements"], "codes": res["codes"],
                    "made": "from the ledger now; not kept" + other}
        except Exception as e:  # noqa: BLE001 — a certificate that cannot be read or made is said, the answer stands
            return {"seq": ev.get("seq"), "ok": False, "exact": False, "statements": False, "codes": [], "made": "none",
                    "error": "%s: %s" % (type(e).__name__, str(e)[:200])}

    def _certify(self, ws, event, revision, parent_text, provenance, rid="", letter=""):
        """CERT-0 (0244): the admission's certificate (art/certificate.py), kept by its ledger sequence number in the
        world's certificates folder and checked at once against the brief as admitted; what the request's line keeps of it."""
        try:
            child = ws.text()
            cert = certificate.make(self.brief, event, revision, parent_text, child, provenance, rid, letter)
            return self._keep_certificate(cert, child)
        except Exception as e:  # noqa: BLE001 — a certificate that cannot be made is said, the admission stands (the ledger is the authority)
            return {"seq": event.get("seq"), "ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:200])}

    def _keep_certificate(self, cert, child):
        """A certificate checked against the child's text and kept by its ledger sequence number, written whole and
        flushed (durable.write: LEDGER-SAFE-0, 0245; a plain write before). What the request's line keeps of it."""
        res = certificate.check(cert, child)
        b = (json.dumps(cert, sort_keys=True, indent=1, ensure_ascii=True) + "\n").encode("ascii")
        durable.write(os.path.join(self.records, "certificates", "%s.json" % cert["ledger"]["seq"]), b)
        return {"seq": cert["ledger"]["seq"], "sha256": sha256(b), "ok": res["ok"], "exact": res["exact"], "statements": res["statements"], "codes": res["codes"]}

    def recover_certificates(self):
        """LEDGER-SAFE-0 (0245): a certificate is derived from the ledger, so every art admission the ledger holds without
        one is given one at the start, from the ledger alone: the parent's and the child's texts replayed, the operation
        the admitted evaluation's revision. Among them the one a crash left without (the studio writes it after the admit
        event), and those the studio never certified (the command line's, those from before CERT-0). The request's
        provenance is not in the ledger: such a certificate says it was made from the ledger, and names the admission's
        note. Art admissions only, as the studio certifies (a layout's is the design tool's). Returns the sequence numbers
        made. It never stops a start: an admission whose part of the ledger does not replay gets none (verify says why)."""
        D = self.play.director()
        try:
            ws = self.play.workspace()
            events = D.led.read(ws.ledger)[0] if os.path.exists(ws.ledger) else []
        except Exception:  # noqa: BLE001 — the start goes on; the ledger's own reading says what is wrong with it
            return []
        made = []
        for i, ev in enumerate(events):
            try:
                if ev.get("kind") != "admit" or ev.get("design_lines") or self._kept_is_own(D, ev):
                    continue
                cert, child = self._ledger_certificate(D, ws, events, i, "made from the ledger at the start (0245)")
                self._keep_certificate(cert, child)
                made.append(ev["seq"])
            except Exception:  # noqa: BLE001 — a certificate that cannot be made is not made; the start goes on
                continue
        return made


# contextlib.redirect_stdout swaps the process's one sys.stdout: two quiet() calls at once (an admission and an undo,
# two worlds' requests) left it pointing at a dead buffer in 20 of 20 trials (MEASURED in the container, 2026-10-13),
# and play.py's console said nothing after. One at a time; the studio self-test keeps the case and its plant.
QUIET_LOCK = threading.RLock()
LOG_LOCK = threading.Lock()          # the requests' records (Gateway._log): one line at a time in this process


DIRECTOR_CODE = re.compile(r"(?:REFUSED \(([A-Z0-9-]+)\)|([A-Z]+(?:-[A-Z0-9]+)+):)")


def director_code(e):
    """The director's own code of a refusal: a Refusal's field, or the code its message opens with ('REFUSED (CODE): ...',
    'LEDGER-CODE: ...'); '' when it names none."""
    if getattr(e, "refusal", ""):
        return e.refusal
    m = DIRECTOR_CODE.match(" ".join(str(e).split()))
    return (m.group(1) or m.group(2)) if m else ""


def quiet(fn, *a, **k):
    """A director command, its printing kept off the console; its refusals (SystemExit, or the ledger's LedgerError) made
    the gateway's, STUDIO-DIRECTOR-REFUSED with the director's own code kept (LEDGER-SAFE-0, 0245; it was lost before)."""
    import io
    import contextlib
    try:
        with QUIET_LOCK, contextlib.redirect_stdout(io.StringIO()):
            return fn(*a, **k)
    except (SystemExit, led.LedgerError) as e:
        raise director_refusal(e)


def director_refusal(e):
    """What the gateway makes of a director command's refusal (SystemExit, or the ledger's LedgerError): its own
    STUDIO-DIRECTOR-REFUSED, with the director's code kept (quiet(), and an account's dry run: one mapping)."""
    # 600, not 300 (0245): a refusal's remedy (LEDGER-UNLOGGED's rebase command, a world's --root) is not cut away
    return StudioError("STUDIO-DIRECTOR-REFUSED", " ".join(str(e).split())[:600], director_code(e))


def failures(D):
    """DASHBOARD-0 (0249): what a studio request is answered STUDIO-FAILED for when it raises it (art/play.py,
    studio_post), and an account likewise (Gateway.account): one list."""
    return (D.dress.ArtError, D.dress.level.MapError, OSError, ValueError, KeyError, TypeError)


def failed_answer(e):
    """The answer to one of failures(): STUDIO-FAILED and the exception's kind and words; for a press of Admit or Undo
    (BINDING-0, 0253) its binding and its decision record, a STUDIO-FAILED press being a decision too."""
    return dict({"ok": False, "code": "STUDIO-FAILED", "message": "%s: %s" % (type(e).__name__, str(e)[:300])}, **binding_fields(e))


def drawn_paths(r):
    """The preview paths of a request's drawn candidates (their impacts'), as FLAGSHIP-0's run() collects them. Holds the
    lock (it reads the request)."""
    return {((x.get("impact") or {}).get("preview") or {}).get("path_id") for x in r["candidates"] if x.get("slot") is not None}


def drawn_ok(binding, drawn):
    """DASHBOARD-0 (0249): whether the preview's stills were drawn from the plan's scenes, as the page named them: every
    base still from the plan's base, every candidate still from its candidate (None when there is nothing to say)."""
    if not binding or not drawn:
        return None
    want = {"base": binding.get("base_sha"), "candidate": binding.get("candidate_sha")}
    return all(v == want.get(k.split("-", 1)[0]) for k, v in drawn.items())


EVIDENCE_NOTE = ("advisory: the studio's admission reads none of this (AGENTS.md: IMPACT-0, PREVIEW-0, FLAGSHIP-0); it applies "
                 "FLAGSHIP-0's predicates item by item and is not FLAGSHIP-0's acceptance")


def evidence_checklist(r, c):
    """EVIDENCE-0 version 0 (0249): a candidate's evidence, item by item, held to FLAGSHIP-0's own predicates
    (art/flagship.py: held_ok, strict_ok, impact_ok, preview_ok, clear_ok, framed_ok) and its run's conditions on a
    preview (framed when there is a subject; one path, the candidate's own), over what the host keeps of the candidate;
    what is not applicable to a request (no shape, not strict) is said so. Advisory: it gates nothing, it never says
    "accepted", and its `next` is the first item missing."""
    import flagship as F
    items = []

    def add(item, status, predicate, needs, evidence):
        items.append({"item": item, "status": status, "predicate": predicate, "needs": needs, "evidence": evidence})

    acc = ((c.get("held") or {}).get("accounts") or [{}])[0]
    if not r.get("shapes"):
        add("held", "not-applicable", "FLAGSHIP-HELD", "a request that names a shape (#name)", {})
    else:
        add("held", "met" if F.held_ok(c) else "missing", "FLAGSHIP-HELD", "the candidate held in the request's first shape",
            {"shape": acc.get("shape", ""), "verdict": acc.get("verdict", "")})
    if not r.get("strict"):
        add("strict", "not-applicable", "FLAGSHIP-HELD", "a strict request", {})
    else:
        add("strict", "met" if F.strict_ok(c) else "missing", "FLAGSHIP-HELD", "its strict check passed",
            {"ok": (c.get("strict") or {}).get("ok"), "code": (c.get("strict") or {}).get("code", "")})
    imp = c.get("impact") or {}
    add("impact", "met" if F.impact_ok(c) else "missing", "FLAGSHIP-NO-IMPACT", "its impact computed (an ESTIMATE)",
        {"error": imp.get("error", "")} if imp.get("error") else {"present": bool(imp)})
    rep = c.get("preview_report")
    if not rep:
        add("preview", "missing", "FLAGSHIP-PREVIEW", "a preview, replayed and verified (Preview on the card)", {})
    else:
        # as FLAGSHIP-0's run holds it: framed in both scenes (required when the request names a shape, the path's subject;
        # a request that names none has no subject to frame), the path clear in both, the candidate's own path the plan's,
        # replayed and every state verified
        framed = F.framed_ok(rep.get("framing")) if r.get("shapes") else None
        # run()'s own condition: every drawn candidate's preview path is the plan's (paths == {path_id})
        one_path = set(r.get("paths") if r.get("paths") is not None else [(imp.get("preview") or {}).get("path_id")]) == {rep.get("path_id")}
        ok = F.preview_ok(rep) and F.clear_ok(rep.get("path_check")) and framed is not False and one_path
        add("preview", "met" if ok else "missing", "FLAGSHIP-PREVIEW", "replayed, every state verified, its path clear in both scenes and the "
            "candidate's own, and, when the request names a shape, its subject framed in both",
            {"replayed": rep.get("replayed"), "state_verified": rep.get("state_verified"), "clear": F.clear_ok(rep.get("path_check")),
             "one_path": one_path, "paths_of_candidates": sorted(p_ or "" for p_ in (r.get("paths") or [])),
             "framed": "no subject (the request names no shape)" if framed is None else framed})
    cert = c.get("certificate")
    if c.get("decided") != "admitted":
        add("certificate", "not-reached", "FLAGSHIP-ADMIT", "an admission (its certificate exact)", {})
    else:
        add("certificate", "met" if (cert or {}).get("ok") is True and (cert or {}).get("exact") is True else "missing", "FLAGSHIP-ADMIT",
            "its certificate checked and exact", {k: (cert or {}).get(k) for k in ("seq", "ok", "exact", "statements")})
    missing = [x["item"] for x in items if x["status"] == "missing"]
    return {"name": "EVIDENCE-0", "version": "0", "advisory": True, "note": EVIDENCE_NOTE, "items": items, "missing": missing,
            "next": missing[0] if missing else "", "of": len([x for x in items if x["status"] in ("met", "missing")])}


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
