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
# each leaves the world as it was and says why. API keys are the provider's affair, in its environment; nothing here
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

REQUEST, RESPONSE, VERSION = "VERDANDI-STUDIO-REQUEST", "VERDANDI-STUDIO-RESPONSE", "0"
REQUEST_VERSION = "1"    # STUDIO-1: the target and the pins, their geometry and relations, in place of one selection
MAX_PINS = 4
PIECE = re.compile(r"[a-z]+:[0-9a-z,:-]{1,60}\Z")
MENTION = re.compile(r"@([0-9]{1,4})")
NAMESPACES = ("play", "surface", "material", "env", "asset", "view", "layout", "region")
LETTERS = ("A", "B", "C")
UNDO_NOTE = "undo of ledger #"
LIMITS = {"prompt": 2000, "title": 80, "rationale": 1200, "revision": 16, "line": 400, "scope": 12, "pattern": 120,
          "preserve": 12, "item": 200, "candidates": 3}
PATTERN = re.compile(r"[A-Za-z0-9*_.,:-]+(/[A-Za-z0-9*_.,:-]+)*\Z")
CONFIG_KEYS = {"provider", "argv", "model", "timeout_s", "max_output_bytes"}
USAGE_KEYS = {"input_tokens", "output_tokens", "cost_usd", "cost_basis"}

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
    kw = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    try:
        p = subprocess.Popen(cfg["argv"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=REPO, shell=False, **kw)
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
    if not isinstance(prov, dict) or not all(isinstance(prov.get(k), str) and prov.get(k) for k in ("name", "model")) or \
            set(prov) - {"usage"} != {"name", "model"}:
        raise StudioError("STUDIO-RESPONSE-FIELD", "provider is {name, model}, each a non-empty string, and optionally usage")
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
        # the references (STUDIO-1): a tag names one object, by its id, for as long as this gateway runs; it is bound to
        # the scene and head it was last selected or pinned at, and never moved to another object
        self.tags = {}           # "@n" -> {tag, piece, address, kind, scene, head, fingerprint, statement, size_m}
        self.tag_of = {}         # object id -> "@n"
        self.next_tag = 1
        self.target = None       # the tag E selected
        self.pins = []           # the tags R pinned, at most MAX_PINS

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
                req["elapsed_ms"] = int(((r["ended"] or time.monotonic()) - r["started"]) * 1000)
                req["candidates"] = [{k: c[k] for k in ("letter", "title", "verdict", "codes", "message", "slot", "decided", "head", "touches")} for c in r["candidates"]]
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
        if tag is None:
            tag = "@%d" % self.next_tag
            self.next_tag += 1
            self.tag_of[o["id"]] = tag
        self.tags[tag] = {"tag": tag, "piece": o["id"], "address": R.address(o), "kind": o["kind"], "scene": out["lineage"]["scene_sha256"],
                          "head": head, "fingerprint": R.fingerprint(o), "statement": self._statement(out, o), "size_m": R.geometry(o)["size_m"]}
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
            return {"target": self.target, "pins": list(self.pins), "max_pins": MAX_PINS,
                    "items": ([item(self.target, "target")] if self.target else []) + [item(t, "pin") for t in self.pins]}
        if locked:
            return build()
        with self.lock:
            return build()

    def references(self, out, head, prompt):
        """The request's references at the head as the files stand: the target and the pins, each with its identity,
        its statement, what that statement can change, its geometry and its nearest wall; the relations between every
        two of them; the tags the prompt mentions. A tag the prompt mentions that is neither the target nor a pin, or
        a tag whose object is not in the scene at the head, refuses the request (STUDIO-REFERENCE): a tag is never
        moved to another object."""
        S = out["scene"]
        O = R.objects(S)
        with self.lock:
            active = ([self.target] if self.target else []) + list(self.pins)
            recs = {t: dict(self.tags[t]) for t in active}
            target = self.target
        mentions = []
        for m in MENTION.findall(prompt):
            t = "@" + str(int(m))
            if t not in mentions:
                mentions.append(t)
        for t in mentions:
            if t not in active:
                raise StudioError("STUDIO-REFERENCE", "the prompt names %s, which is not the target or a pin of this request (%s)" % (
                    t, ", ".join("%s %s" % (a, "target" if a == target else "pin") for a in active) or "none"))
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
    def ask(self, prompt, piece=None, camera=None):
        """Start a request; it cancels the one before it. Returns the request's id, or raises StudioError at once
        (no provider, an empty prompt, an unknown piece, a reference that names nothing). `piece`, if given, is selected
        first as the target (E does it in the page)."""
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
        if piece is not None:
            self.select(piece)
        ws, out, parts, head = self._head()
        stmts = [{"line": x["line"], "text": x["text"], "key": x["key"]} for x in out["lineage"]["statements"]]
        refs, rels, mentions, O = self.references(out, head, prompt)
        S = out["scene"]
        target = refs[0] if refs and refs[0]["role"] == "target" else None
        with self.lock:
            if self.req and self.req["state"] == "running":
                self.cancel.set()
                self.req["state"], self.req["code"], self.req["message"] = "superseded", "STUDIO-SUPERSEDED", "a newer request was asked"
                self.req["ended"] = time.monotonic()
            self.n += 1
            rid = "%s-%s%d" % (datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S"), "" if self.origin == "page" else self.origin + "-", self.n)
            base = {k: parts[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}
            request = {"format": REQUEST, "version": REQUEST_VERSION, "id": rid, "brief": self.brief, "head": head, "base": base,
                       "prompt": prompt.strip(), "target": target, "references": refs, "relations": rels, "mentions": mentions,
                       "coordinates": "%s; a cell is %g m; the walls of the play geometry are %g m high; a box is [x0, y0, z0, x1, y1, z1]" % (
                           S["units"], S["grid"]["cell"], S["grid"]["wall"]),
                       "camera": cam, "statements": stmts,
                       "revision_syntax": "'= <statement>' replaces the brief's statement with the same key; '+ <statement>' adds one "
                                          "whose key is new; '- <key>' removes one. A statement's key: its verb (or the verb and its "
                                          "first word; a canopy adds its two corner cells), as the statements' keys show.",
                       "language": language(),
                       "respond": {"format": RESPONSE, "version": VERSION, "id": rid, "max_candidates": LIMITS["candidates"], "schema": SCHEMA}}
            self.req = {"id": rid, "state": "running", "prompt": prompt.strip(), "message": "", "code": "",
                        "references": {r["tag"]: {"role": r["role"], "piece": r["piece"], "address": r["address"]} for r in refs},
                        "selection": target["address"] if target else None,
                        "head": head, "provider": {"model": self.cfg["model"]}, "candidates": [], "started": time.monotonic(),
                        "ended": None, "base": base, "objects": O}
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
                 "selection": req["selection"], "references": {t: r["piece"] for t, r in req["references"].items()},
                 "config": self.cfg["path"], "model": self.cfg["model"], "request_sha256": sha256(rb)}
        if self.origin != "page":
            entry["origin"] = self.origin
        # what the owner asked to be recorded of every call (2026-10-11): the provider, the model, the exit status, whether
        # the response was valid, the latency; and the tokens and cost the provider reports. No credential is in any of it.
        try:
            raw, ms, rc = run_provider(self.cfg, rb, cancel, self.running)
            self._record(rid, "response.raw", raw)
            entry.update({"response_sha256": sha256(raw), "provider_ms": ms, "exit": rc})
            provider, cands = read_response(raw, rid)
            entry.update({"provider": provider, "valid": True})
            if "usage" in provider:
                entry["usage"] = provider["usage"]
        except StudioError as e:
            entry.update({"outcome": e.code, "detail": str(e)[:300]})
            if hasattr(e, "exit"):
                entry["exit"] = e.exit
            if e.code.startswith("STUDIO-RESPONSE-"):
                entry["valid"] = False
            if e.code != "STUDIO-CANCELLED":
                self._finish(req, "failed", e.code, e.detail)
            self._log(entry)
            self.say("STUDIO  %s  %s: %s" % (rid, e.code, e.detail[:200]))
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
                    "decided": "", "head": "", "intent": None, "touches": None}
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
                         "head": slot.get("checked_against", ""),
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
        self._finish(req, "done", "", "%d candidate%s, %d drawn" % (len(made), "" if len(made) == 1 else "s", n_ok) if made else "the director proposed nothing")
        entry["outcome"] = "DONE"
        self._log(entry)
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
    print("usage: python art/studio.py selftest | schema | probe CONFIG.json [--brief B] [--piece ID] | probe CONFIG.json --references [--runs N] | report [--brief B]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
