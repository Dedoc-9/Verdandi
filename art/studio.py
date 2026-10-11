# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/studio.py — STUDIO-0: the director gateway between the running plaza (art/play.py) and a model.
#
#   python art/studio.py selftest
#   python art/studio.py schema           the response schema a provider answers with (JSON Schema, for an adapter)
#
# By the owner's direction and ruling of 2026-10-11: "the LLM edits design intent; Verðandi compiles that intent into a
# live world; the designer remains in control"; "a pluggable model adapter", behind "a local director gateway that
# accepts requests from play.py, invokes a configurable model provider, validates its output, and returns up to three
# structured design candidates"; "Start with a CLI adapter so the first implementation remains standard-library-only";
# "the model proposes changes—it never directly mutates the live world. Verðandi owns validation, compilation,
# preview, and admission." The contract is in art/STUDIO.md.
#
# What it does, for one request (the page's prompt, its selection and its camera):
#   1. the context, from the head as the files stand: the brief's statements, the selected piece's statement and the
#      address patterns it falls under, the camera; written as one VERDANDI-STUDIO-REQUEST 0 document with an id and
#      the head it is based on, and kept under art/build/studio/BRIEF/ID/ with everything that follows;
#   2. the provider, a command from a configuration file (an argv list, never a shell line; the request on its
#      standard input, never in its arguments), with a time limit, a limit on what it may print, and cancellation:
#      a newer request cancels the one before it, and the page's cancel kills the command;
#   3. the response read whole or refused whole (STUDIO-RESPONSE-*): a VERDANDI-STUDIO-RESPONSE 0 document naming the
#      request's id, with at most three candidates of bounded fields; each made a VERDANDI-INTENT (the letter, the
#      base and the prompt are the gateway's, not the model's) and evaluated by the director at the current head
#      (art/director.py: the art checks, and the scope check, which holds everything outside the declared scope
#      unchanged); a candidate the director refuses is shown with its reason and never drawn;
#   4. the rest compiled and handed to play.py as sources the page can switch to, in place, the game untouched;
#   5. nothing admitted until the designer admits one: then the candidate is evaluated again at the head as it is,
#      and admitted through the director's ledger only if that head is the one it was previewed at. Rejecting records
#      a refusal; undo admits the last admission's exact inverse as an intent of its own.
# A timeout, a provider that cannot start or exits with an error, a response too long or malformed, a cancellation:
# each leaves the world as it was and says why. API keys are the provider's affair, in its environment; nothing here
# reads one, and nothing of a provider's reaches the browser but the candidates' text and verdicts.
#
# Standard library only. It writes the request records under art/build/studio/ (not committed) and, on the
# designer's admission or rejection, the brief and its ledger, as art/director.py does.

import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

REQUEST, RESPONSE, VERSION = "VERDANDI-STUDIO-REQUEST", "VERDANDI-STUDIO-RESPONSE", "0"
LETTERS = ("A", "B", "C")
UNDO_NOTE = "undo of ledger #"
LIMITS = {"prompt": 2000, "title": 80, "rationale": 1200, "revision": 16, "line": 400, "scope": 12, "pattern": 120,
          "preserve": 12, "item": 200, "candidates": 3}
PATTERN = re.compile(r"[A-Za-z0-9*_.,:-]+(/[A-Za-z0-9*_.,:-]+)*\Z")
CONFIG_KEYS = {"provider", "argv", "model", "timeout_s", "max_output_bytes"}

# The response a provider writes: what an adapter constrains a model's output to, where the provider supports it.
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["candidates"],
    "properties": {
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
def run_provider(cfg, request_bytes, cancel):
    """The provider's standard output for the request, or a StudioError: it cannot start, it is cancelled, it runs past
    its time, it prints more than its limit, it exits with an error. Its standard error is kept for the message."""
    try:
        p = subprocess.Popen(cfg["argv"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=REPO, shell=False)
    except OSError as e:
        raise StudioError("STUDIO-PROVIDER-START", "the provider cannot be started: %s" % e)
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
    while p.poll() is None:
        if cancel.is_set():
            why = StudioError("STUDIO-CANCELLED", "cancelled while the provider ran")
        elif too_long.is_set():
            why = StudioError("STUDIO-RESPONSE-SIZE", "the provider printed more than %d bytes" % limit)
        elif time.monotonic() - t0 > cfg["timeout_s"]:
            why = StudioError("STUDIO-TIMEOUT", "the provider ran past %d s" % cfg["timeout_s"])
        if why:
            p.kill()
            p.wait()
            raise why
        time.sleep(0.02)
    for t in threads[:2]:
        t.join(5)
    if cancel.is_set():
        raise StudioError("STUDIO-CANCELLED", "cancelled")
    if too_long.is_set():
        raise StudioError("STUDIO-RESPONSE-SIZE", "the provider printed more than %d bytes" % limit)
    if p.returncode != 0:
        tail = bytes(err).decode("utf-8", "replace").strip().splitlines()[-1:] or ["(nothing on standard error)"]
        raise StudioError("STUDIO-PROVIDER-EXIT", "the provider exited %d: %s" % (p.returncode, tail[0][:300]))
    return bytes(out), int((time.monotonic() - t0) * 1000)


# ------------------------------------------------------------------------------------------------ the response
def read_response(raw, rid):
    """The candidates of a response, each with exactly its five fields, or STUDIO-RESPONSE-*: the response refused
    whole. An empty list of candidates is an answer: the provider proposed nothing."""
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
        raise StudioError("STUDIO-RESPONSE-JSON", "not JSON in UTF-8 (%s)" % str(e)[:120])
    if not isinstance(doc, dict) or doc.get("format") != RESPONSE or doc.get("version") != VERSION:
        raise StudioError("STUDIO-RESPONSE-FORMAT", "not a %s %s document" % (RESPONSE, VERSION))
    if set(doc) - {"format", "version", "id", "provider", "candidates"}:
        raise StudioError("STUDIO-RESPONSE-FIELD", "unknown fields %s" % sorted(set(doc) - {"format", "version", "id", "provider", "candidates"}))
    if doc.get("id") != rid:
        raise StudioError("STUDIO-RESPONSE-ID", "the response answers %r, not this request (%s)" % (doc.get("id"), rid))
    prov = doc.get("provider")
    if not isinstance(prov, dict) or not all(isinstance(prov.get(k), str) and prov.get(k) for k in ("name", "model")) or set(prov) != {"name", "model"}:
        raise StudioError("STUDIO-RESPONSE-FIELD", "provider is {name, model}, each a non-empty string")
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
    return doc["provider"], out


def intent_doc(c, letter, brief, base, prompt):
    """A candidate as a VERDANDI-INTENT: the letter, the base and the prompt are the gateway's; the title, the
    rationale, the revision and the scope the provider's. The layout is empty: STUDIO-0 changes the look alone."""
    rationale = " ".join((c["title"].strip() + ". " + c["rationale"].strip()).split())
    if c["preserve"]:
        rationale += " Keeps: " + "; ".join(" ".join(p.split()) for p in c["preserve"]) + "."
    return {"base": dict(base), "brief": brief, "candidate": letter, "format": "VERDANDI-INTENT", "layout": [],
            "prompt": prompt, "rationale": rationale, "revision": [" ".join(ln.split()) if ln[0] != "-" else "- " + " ".join(ln[2:].split()) for ln in c["revision"]],
            "scope": list(c["scope"]), "version": "0"}


# ------------------------------------------------------------------------------------------------ the gateway
class Gateway:
    """One brief's director gateway. `play` gives what the gateway needs of art/play.py: director() (the director
    module), workspace() (the brief's Workspace), candidate_slot(ws, intent_dict, label) (a candidate evaluated at the
    current head: a play.py source, served or refused), and publish(slots) (the candidates the page can switch to)."""

    def __init__(self, play, brief, cfg=None, root=REPO, say=print):
        self.play, self.brief, self.cfg, self.root, self.say = play, brief, cfg, root, say
        self.lock = threading.Lock()
        self.req = None          # the latest request: dict, see state()
        self.cancel = None       # its cancellation event
        self.n = 0
        self.last = {}           # the last admission, rejection or undo, for the page
        self.records = os.path.join(root, "art", "build", "studio", brief)
        self.error = ""          # why there is no provider, when a configuration was refused

    # ------------------------------------------------------------------ what the page reads
    def state(self):
        with self.lock:
            r = self.req
            prov = {"configured": self.cfg is not None, "model": self.cfg["model"] if self.cfg else "", "error": self.error,
                    "config": os.path.basename(self.cfg["path"]) if self.cfg else ""}
            req = None
            if r:
                req = {k: r[k] for k in ("id", "state", "prompt", "message", "code", "selection", "head", "provider")}
                req["elapsed_ms"] = int(((r["ended"] or time.monotonic()) - r["started"]) * 1000)
                req["candidates"] = [{k: c[k] for k in ("letter", "title", "verdict", "codes", "message", "slot", "decided", "head")} for c in r["candidates"]]
            return {"provider": prov, "request": req, "last": dict(self.last)}

    # ------------------------------------------------------------------ the context
    def context(self, piece):
        """The head as the files stand, the brief's statements, and the selected piece's statement and patterns."""
        D = self.play.director()
        ws = self.play.workspace()
        out, parts, _checks = ws.export()
        head = D.canon.head(parts)
        stmts = [{"line": s["line"], "text": s["text"], "key": s["key"]} for s in out["lineage"]["statements"]]
        sel = None
        if piece is not None:
            S = out["scene"]
            hits = [p for p in S["visuals"] + S["lights"] if p["id"] == piece]
            if not hits:
                raise StudioError("STUDIO-SELECTION", "the piece %r is not in the brief's scene at the head" % piece)
            p = hits[0]
            st = [s for s in out["lineage"]["statements"] if s["hash"] == p["by"]]
            kind, place = piece.split(":", 1)
            region = "city" if p["region"] == "*" else p["region"]
            sel = {"piece": piece, "address": "%s/%s/%s" % (region, kind, place), "region": region, "kind": kind,
                   "statement": {"line": st[0]["line"], "text": st[0]["text"], "key": st[0]["key"]} if st else None,
                   "material": p.get("material", ""), "patterns": ["%s/%s/*" % (region, kind)] + (["material/%s" % p["material"]] if p.get("material") else [])}
        return ws, parts, head, stmts, sel

    # ------------------------------------------------------------------ a request
    def ask(self, prompt, piece=None, camera=None):
        """Start a request; it cancels the one before it. Returns the request's id, or raises StudioError at once
        (no provider, an empty prompt, an unknown piece)."""
        if self.cfg is None:
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
        ws, parts, head, stmts, sel = self.context(piece)
        with self.lock:
            if self.req and self.req["state"] == "running":
                self.cancel.set()
                self.req["state"], self.req["code"], self.req["message"] = "superseded", "STUDIO-SUPERSEDED", "a newer request was asked"
                self.req["ended"] = time.monotonic()
            self.n += 1
            rid = "%s-%d" % (datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S"), self.n)
            base = {k: parts[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}
            request = {"format": REQUEST, "version": VERSION, "id": rid, "brief": self.brief, "head": head, "base": base,
                       "prompt": prompt.strip(), "selection": sel, "camera": cam, "statements": stmts,
                       "revision_syntax": "'= <statement>' replaces the brief's statement with the same key; '+ <statement>' adds one "
                                          "whose key is new; '- <key>' removes one. A statement's key: its verb (or the verb and its "
                                          "first word; a canopy adds its two corner cells), as the statements' keys show.",
                       "language": language(),
                       "respond": {"format": RESPONSE, "version": VERSION, "id": rid, "max_candidates": LIMITS["candidates"], "schema": SCHEMA}}
            self.req = {"id": rid, "state": "running", "prompt": prompt.strip(), "message": "", "code": "", "selection": sel,
                        "head": head, "provider": {"model": self.cfg["model"]}, "candidates": [], "started": time.monotonic(),
                        "ended": None, "base": base}
            self.cancel = threading.Event()
            req, cancel = self.req, self.cancel
        self.play.publish([])
        threading.Thread(target=self._run, args=(req, request, cancel, ws), daemon=True).start()
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
        os.makedirs(self.records, exist_ok=True)
        with open(os.path.join(self.records, "requests.jsonl"), "ab") as fh:
            fh.write(json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii") + b"\n")

    def _finish(self, req, state, code="", message=""):
        with self.lock:
            if req["state"] != "running":      # cancelled or superseded meanwhile: its result is discarded
                return False
            req["state"], req["code"], req["message"], req["ended"] = state, code, message, time.monotonic()
            return True

    def _run(self, req, request, cancel, ws):
        rid = req["id"]
        rb = (json.dumps(request, sort_keys=True, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
        self._record(rid, "request.json", rb)
        entry = {"id": rid, "at": now(), "brief": self.brief, "head": req["head"], "prompt": req["prompt"],
                 "selection": (req["selection"] or {}).get("address"), "config": self.cfg["path"], "model": self.cfg["model"],
                 "request_sha256": sha256(rb)}
        try:
            raw, ms = run_provider(self.cfg, rb, cancel)
            self._record(rid, "response.raw", raw)
            entry.update({"response_sha256": sha256(raw), "provider_ms": ms})
            provider, cands = read_response(raw, rid)
            entry["provider"] = provider
        except StudioError as e:
            entry.update({"outcome": e.code, "detail": str(e)[:300]})
            if e.code != "STUDIO-CANCELLED":
                self._finish(req, "failed", e.code, e.detail)
            self._log(entry)
            return
        with self.lock:
            if req["state"] != "running":
                entry.update({"outcome": req["code"] or "STUDIO-DISCARDED", "detail": "the response came after the request was %s" % req["state"]})
                self._log(entry)
                return
            req["provider"] = provider
        D = self.play.director()
        made = []
        for letter, c in zip(LETTERS, cands):
            doc = intent_doc(c, letter, self.brief, req["base"], req["prompt"])
            item = {"letter": letter, "title": c["title"].strip(), "verdict": "", "codes": [], "message": "", "slot": None,
                    "decided": "", "head": "", "intent": None}
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
                         "head": slot.get("checked_against", "")})
            made.append((item, slot if slot["ok"] else None))
        entry["candidates"] = [{"letter": i["letter"], "title": i["title"], "verdict": i["verdict"], "codes": i["codes"],
                                "intent_sha256": sha256(i["intent"]) if i["intent"] else ""} for i, _s in made]
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
        self._finish(req, "done", "", "%d candidate%s, %d drawn" % (len(made), "" if len(made) == 1 else "s", n_ok) if made else "the director proposed nothing")
        entry["outcome"] = "DONE"
        self._log(entry)

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

    def admit(self, rid, letter):
        """Admit a drawn candidate: evaluated again at the head as the files stand, and admitted through the ledger only
        if that is the head it was drawn at and its verdict is CLEAN."""
        r, c = self._candidate(rid, letter)
        if c["slot"] is None or c["intent"] is None:
            raise StudioError("STUDIO-NOT-ADMISSIBLE", "candidate %s was not drawn (%s)" % (letter, c["verdict"]))
        D = self.play.director()
        ws = self.play.workspace()
        it = D.canon.load_intent(c["intent"])
        verdict, after, timings, _o1, _o0, _t = D.evaluate_doc(ws, it)
        if verdict["checked_against"] != c["head"]:
            raise StudioError("STUDIO-STALE", "the head moved since candidate %s was drawn (%s, now %s): ask again" % (letter, c["head"][:12], verdict["checked_against"][:12]))
        if verdict["verdict"] != "CLEAN":
            raise StudioError("STUDIO-NOT-ADMISSIBLE", "candidate %s is %s (%s); only a CLEAN candidate is admitted here" % (letter, verdict["verdict"], ",".join(verdict["codes"])))
        ev = D.led.append(ws.ledger, "evaluate", {"intent": c["intent"].decode("ascii"), "intent_sha256": sha256(c["intent"]), "re_evaluation_of": "",
                                                  "verdict": verdict, "after": after, "observed": {"at": now(), "ms": timings}})
        a = quiet(D.cmd_admit, ws, ev["seq"], chooser="the designer (studio)", note="request %s, candidate %s" % (rid, letter))
        with self.lock:
            c["decided"] = "admitted"
            self.last = {"what": "admitted", "request": rid, "candidate": letter, "ledger": [ev["seq"], a["seq"]], "head": a["head_after"]}
        self._log({"id": rid, "at": now(), "decision": "admit", "candidate": letter, "ledger": [ev["seq"], a["seq"]], "head_after": a["head_after"]})
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
        verdict, after, timings, _o1, _o0, _t = D.evaluate_doc(ws, it)
        ev = D.led.append(ws.ledger, "evaluate", {"intent": c["intent"].decode("ascii"), "intent_sha256": sha256(c["intent"]), "re_evaluation_of": "",
                                                  "verdict": verdict, "after": after, "observed": {"at": now(), "ms": timings}})
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
        verdict, after, timings, _o1, _o0, _t = D.evaluate_doc(ws, it)
        ev = D.led.append(ws.ledger, "evaluate", {"intent": raw.decode("ascii"), "intent_sha256": sha256(raw), "re_evaluation_of": "",
                                                  "verdict": verdict, "after": after, "observed": {"at": now(), "ms": timings}})
        if verdict["verdict"] != "CLEAN":
            raise StudioError("STUDIO-NOT-UNDOABLE", "the inverse of #%s is %s (%s), recorded as #%s and not admitted" % (a["seq"], verdict["verdict"], ",".join(verdict["codes"]), ev["seq"]))
        u = quiet(D.cmd_admit, ws, ev["seq"], chooser="the designer (studio)", note=UNDO_NOTE + a["seq"])
        with self.lock:
            self.last = {"what": "undone", "of": a["seq"], "ledger": [ev["seq"], u["seq"]], "head": u["head_after"]}
        self._log({"at": now(), "decision": "undo", "of": a["seq"], "ledger": [ev["seq"], u["seq"]], "head_after": u["head_after"]})
        return self.last


def quiet(fn, *a, **k):
    """A director command, its printing kept off the console; its refusals (it raises SystemExit) made the gateway's."""
    import io
    import contextlib
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            return fn(*a, **k)
    except SystemExit as e:
        raise StudioError("STUDIO-DIRECTOR-REFUSED", " ".join(str(e).split())[:300])


# ------------------------------------------------------------------------------------------------ commands
def main(argv):
    if argv == ["schema"]:
        print(json.dumps(SCHEMA, indent=1, sort_keys=True))
        return 0
    if argv == ["selftest"]:
        sys.path.insert(0, HERE)
        import play   # noqa: E402  (the gateway is tested through the launcher that hosts it)
        return play.studio_selftest()
    print("usage: python art/studio.py selftest | schema", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
