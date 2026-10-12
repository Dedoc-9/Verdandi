# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/play.py — the native plaza: a brief's dressed scene, played in the browser, without Unreal, and changed while it
# runs.
#
#   python art/play.py BRIEF [--intent FILE]... [--art PATH] [--director CONFIG.json] [--root DIR] [--port N]
#                            [--no-browser] [--no-watch] [--check]
#   python art/play.py --selftest
#
# By the owner's ruling (2026-10-11): an art-owned launcher, with WebGL 2, and graybox/serve.py and the graybox's
# boundary left as they are.
#
# What it serves are sources, each compiled through art/dress.py into a scene and held to the art checks (art/check.py:
# the scene's collision is C, nothing dressed where a player can be, the art carries no collision):
#
#   0  the brief as it stands (art/briefs/BRIEF.art), or the art file --art PATH names
#   k  each --intent FILE: the brief with that intent applied, as art/director.py evaluates it — its scope verdict at
#      the current head, its layout lines (if any) made through the design tool in a scratch folder. Nothing is written
#      to the ledger: playing a candidate is not admitting it.
#
# A source that fails a check, or whose intent the director refuses, is not served. If the first fails at launch, nothing
# is. Then it serves, on 127.0.0.1 only, exactly these and nothing else:
#
#   /play.html, /play.js, /scene_render.js    art/web/, the page and the renderer
#   /sim.js                                   graybox/web/sim.js, the graybox's simulation, read and served unchanged
#   /scene/BRIEF.json?slot=K                  source K's compiled scene, from memory (K is 0 if not given)
#   /map/MAP.json?slot=K                      source K's map, converted by graybox/level.py, as graybox/serve.py serves it
#   /live                                     what is served now: each source's scene and map digests, its verdict, the
#                                             last refusal, and the digests of the three scripts
#
# Live edits (unless --no-watch). A thread watches every file the sources are made from: the art file, the intents, the
# graybox's maps folder, and the code that compiles them (art/*.py, art/director/*.py, graybox/level.py,
# graybox/check.py). When their content changes it compiles every source again, in a fresh Python process, so that an
# edit to the exporter is used as well as an edit to the text. A source that compiles and passes is served in place of
# the old one; one that does not leaves the old one served and says why. The page asks /live twice a second: a new
# scene of the same map is drawn in place and the game goes on untouched, since the renderer writes no state; a new
# map is a new collision world, and so a new game: the simulation's own new state at the spawn, nothing of the old
# game carried into it (the edit is new authority). The renderer's own file is swapped in place too; a change to
# play.js or sim.js is announced and loaded by reloading the page. Nothing is written to disk but the self-test's
# scratch folder, unless the studio is used (below). Standard library only.
#
# The studio (STUDIO-0, the owner's direction of 2026-10-11; art/studio.py, art/STUDIO.md). With --director CONFIG.json
# the page can summon a director: Enter opens a prompt; E makes the object under the crosshair the target and R pins
# one as a reference (STUDIO-1: each given a tag, @1, @2, ..., by the gateway); the prompt, the tags and the camera go
# to art/studio.py's gateway, which asks the configured provider for at most three
# candidates, has the director evaluate each at the current head, and serves those it does not refuse as further
# sources: the page switches to one in place, the game untouched. Admit, reject and undo go through the director's
# ledger and write the brief, as art/director.py does; the requests are recorded under art/build/studio/. The page's
# POSTs carry the token play.html is served with and must name this server as their host. --root DIR plays the brief
# of another tree (DIR/art/briefs, DIR/art/ledger), as the self-test does in a scratch copy.

import hashlib
import http.server
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import dress  # noqa: E402

level = dress.level
_spec = importlib.util.spec_from_file_location("art_check", os.path.join(HERE, "check.py"))
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)

WEB = os.path.join(HERE, "web")
FILES = {
    "/play.js": (os.path.join(WEB, "play.js"), "text/javascript; charset=utf-8"),
    "/scene_render.js": (os.path.join(WEB, "scene_render.js"), "text/javascript; charset=utf-8"),
    "/sim.js": (os.path.join(REPO, "graybox", "web", "sim.js"), "text/javascript; charset=utf-8"),
}
CODE = [os.path.join(HERE, "dress.py"), os.path.join(HERE, "check.py"), os.path.join(HERE, "director.py"),
        os.path.join(REPO, "graybox", "level.py"), os.path.join(REPO, "graybox", "check.py")]
SERVED = "the art checks passed; movement and collision are the graybox simulation's, against C"
_director = None
ROOT = REPO     # the tree whose brief and ledger the director and the studio use (--root)


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def director():
    """art/director.py, loaded when an intent is first played (it is not needed to play a brief)."""
    global _director
    if _director is None:
        spec = importlib.util.spec_from_file_location("art_director", os.path.join(HERE, "director.py"))
        _director = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_director)
    return _director


def compile_scene(brief, art_path=None):
    """The brief's scene, held to the art checks, and the map it is played on. Raises SystemExit with the reason if
    the brief is refused or a check fails."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", brief):
        raise SystemExit("PLAY: a brief's name is lower-case letters, digits and -")
    if art_path is None and not os.path.isfile(os.path.join(dress.BRIEFS, brief + ".art")):
        raise SystemExit("PLAY: no brief art/briefs/%s.art" % brief)
    try:
        out = dress.export(dress.load(brief, art_path))
    except (dress.ArtError, level.MapError) as e:
        raise SystemExit("PLAY: the exporter refused the brief: %s" % e)
    except OSError as e:
        raise SystemExit("PLAY: the art file cannot be read: %s" % e)
    res = check.verify(out, None, D=check.gcheck.source_rows(out["W"]))
    bad = [(c, d) for c, ok, d in res if not ok and c != "the lineage binds every input"]
    if bad:
        raise SystemExit("PLAY: the scene is not served; it fails the art checks:\n" + "\n".join("  FAIL %s — %s" % b for b in bad))
    scene = out["scene"]
    m = level.convert(scene["map"])
    return out, level.canon(m), m["manifest"]


def _slot(label, source, out=None, map_bytes=None, message="", **extra):
    s = {"label": label, "source": source, "ok": out is not None, "message": message, "verdict": "", "codes": []}
    if out is not None:
        c = out["lineage"]["counts"]
        s.update({"scene_bytes": out["scene_bytes"], "sha": out["lineage"]["scene_sha256"], "map": out["scene"]["map"],
                  "map_bytes": map_bytes, "map_sha": sha256(map_bytes), "counts": c})
    s.update(extra)
    return s


def brief_slot(brief, art_path=None):
    label = "art " + os.path.basename(art_path) if art_path else "the brief"
    try:
        out, map_bytes, _m = compile_scene(brief, art_path)
    except SystemExit as e:
        return _slot(label, art_path or "art/briefs/%s.art" % brief, message=str(e))
    return _slot(label, art_path or "art/briefs/%s.art" % brief, out, map_bytes)


def workspace(brief):
    return director().Workspace(brief, ROOT)


def intent_slot(brief, path):
    """The brief with the intent at `path` applied, as the director evaluates it at the current head."""
    D = director()
    label = "intent " + os.path.basename(path)
    try:
        raw = open(path, "rb").read()
        it = D.canon.load_intent(raw)
    except OSError as e:
        return _slot(label, path, message="PLAY: the intent cannot be read: %s" % e)
    except D.canon.IntentError as e:
        return _slot(label, path, message="PLAY: the intent is malformed: %s %s" % (e.code, e))
    label = "intent %s (%s): %s" % (os.path.basename(path), it["candidate"], it["prompt"])
    return candidate_slot(workspace(brief), it, label, path)


def candidate_slot(ws, it, label, source="studio"):
    """An intent evaluated by the director at the current head: a source, served unless the director refuses it."""
    D = director()
    got = {}

    def keep(out1, maps):
        got["map"] = level.canon(dress.world(out1["scene"]["map"], maps))

    path = source
    try:
        verdict, _after, _t, out1, _out0, _text1 = D.evaluate_doc(ws, it, on_candidate=keep)
    except (dress.ArtError, level.MapError, OSError) as e:
        return _slot(label, path, message="PLAY: the head cannot be compiled: %s" % e)
    extra = {"verdict": verdict["verdict"], "codes": verdict["codes"], "written_against": verdict["written_against"],
             "checked_against": verdict["checked_against"]}
    # what the director found the candidate changed: the studio's account of which objects a candidate touched (STUDIO-1)
    for k in ("realized", "affected", "materials_changed"):
        if k in verdict:
            extra[k] = list(verdict[k])
    if verdict["verdict"] == "REFUSED" or out1 is None:
        why = verdict.get("detail") or ""
        why = why if why.startswith(tuple(verdict["codes"])) and why else "; ".join(verdict["codes"]) + (": " + why if why else "")
        if verdict.get("failed_checks"):
            why += " (fails: %s)" % ", ".join(verdict["failed_checks"])
        return _slot(label, path, message="PLAY: the director refuses the candidate: %s" % why, **extra)
    return _slot(label, path, out1, got["map"], **extra)


def compile_slots(brief, art_path=None, intents=(), only=None):
    """Every source (or those whose index is in `only`; the others are None)."""
    want = lambda k: only is None or k in only
    return [brief_slot(brief, art_path) if want(0) else None] + [intent_slot(brief, f) if want(k + 1) else None for k, f in enumerate(intents)]


def emit(brief, art_path, intents, only=None):
    """--emit: the sources compiled, as one JSON document on stdout (what the watcher reads from a fresh process)."""
    slots = compile_slots(brief, art_path, intents, only)
    for s in slots:
        if s and s["ok"]:
            s["scene_bytes"] = s["scene_bytes"].decode("utf-8")
            s["map_bytes"] = s["map_bytes"].decode("utf-8")
    sys.stdout.buffer.write(json.dumps({"slots": slots}, ensure_ascii=True).encode("ascii"))
    return 0


def line(i, s):
    if not s["ok"]:
        return "PLAY  [%d] %s  NOT SERVED\n%s" % (i, s["label"], s["message"])
    c = s["counts"]
    v = ("  %s %s" % (s["verdict"], ",".join(s["codes"]) or "-")) if s["verdict"] else ""
    return "PLAY  [%d] %s  scene %s  (%d play boxes, %d dressing pieces, %d lights)  map %s %s%s" % (
        i, s["label"], s["sha"][:12], c["collision"], c["visuals"], c["lights"], s["map"], s["map_sha"][:12], v)


class Live:
    """What is served, and the thread that changes it when the files it is made from change."""

    def __init__(self, brief, art_path=None, intents=(), slots=None, poll=0.3):
        self.brief, self.art_path, self.intents, self.poll = brief, art_path, list(intents), poll
        self.cmd = [sys.executable, "-B", os.path.abspath(__file__), brief, "--emit"] + \
            (["--art", os.path.abspath(art_path)] if art_path else []) + sum((["--intent", os.path.abspath(f)] for f in self.intents), [])
        self.lock = threading.Lock()
        self.version, self.compiled_ms, self.stopping = 0, 0, False
        slots = slots if slots is not None else compile_slots(brief, art_path, self.intents)
        self.served = [s if s["ok"] else None for s in slots]
        self.latest = slots
        self.inputs = [self.digest(self.inputs_of(k)) for k in range(len(slots))]
        self.compiles = [1] * len(slots)
        self.log = []
        self.extra = []          # the studio's candidates: sources after the given ones, replaced by each request
        self.studio = None       # art/studio.py's gateway, with --director
        self.studio_error = ""

    def publish(self, slots):
        """The studio's candidates, served after the given sources; returns their indices."""
        with self.lock:
            self.extra = list(slots)
            self.version += 1
            n = len(self.served)
            return list(range(n, n + len(self.extra)))

    # ------------------------------------------------------------------ what is watched
    def inputs_of(self, k):
        """The files source k is made from: its own (the art file; an intent and the brief it is applied to), the maps,
        and the code that compiles them."""
        brief_file = os.path.join(ROOT, "art", "briefs", self.brief + ".art")
        own = [self.art_path or brief_file] if k == 0 else [self.intents[k - 1], brief_file]
        return sorted(set(os.path.abspath(f) for f in own + self.shared()))

    def watched(self):
        return sorted(set(f for k in range(len(self.served)) for f in self.inputs_of(k)))

    def shared(self):
        maps = os.path.join(REPO, "graybox", "maps")
        fs = list(CODE)
        fs += sorted(os.path.join(HERE, f) for f in os.listdir(HERE) if f.endswith(".py"))
        fs += sorted(os.path.join(HERE, "director", f) for f in os.listdir(os.path.join(HERE, "director")) if f.endswith(".py"))
        if os.path.isdir(maps):
            fs += sorted(os.path.join(maps, f) for f in os.listdir(maps) if os.path.isfile(os.path.join(maps, f)))
        for s in self.served:
            lv = s and json.loads(s["map_bytes"])["manifest"]["source"].get("level")
            if lv:
                fs.append(os.path.join(REPO, lv))
        return fs

    @staticmethod
    def stamp(files):
        out = {}
        for f in files:
            try:
                st = os.stat(f)
                out[f] = (st.st_mtime_ns, st.st_size)
            except OSError:
                out[f] = None
        return out

    @staticmethod
    def digest(files):
        h = hashlib.sha256()
        for f in files:
            try:
                b = open(f, "rb").read()
            except OSError:
                b = None
            h.update(f.encode("utf-8") + b"\0" + (sha256(b).encode("ascii") if b is not None else b"-") + b"\n")
        return h.hexdigest()

    def code(self):
        out = {}
        for path, (f, _ctype) in FILES.items():
            try:
                out[path[1:]] = sha256(open(f, "rb").read())[:16]
            except OSError:
                out[path[1:]] = ""
        return out

    # ------------------------------------------------------------------ compiling again
    def recompile(self, only=None):
        """The sources in `only` (all if None) compiled again in a fresh process; what passes replaces what was served.
        Returns the lines to print."""
        t0 = time.perf_counter()
        only = list(range(len(self.served))) if only is None else sorted(only)
        try:
            cp = subprocess.run(self.cmd + ["--only", ",".join(str(k) for k in only)], capture_output=True, cwd=REPO, timeout=300,
                                env=dict(os.environ, PYTHONHASHSEED="0"))
            if cp.returncode != 0:
                tail = (cp.stderr.decode("utf-8", "replace").strip().splitlines() or ["(nothing on stderr)"])[-1]
                raise RuntimeError("the compiler stopped (exit %d): %s" % (cp.returncode, tail[:300]))
            slots = json.loads(cp.stdout.decode("ascii"))["slots"]
            if len(slots) != len(self.served):
                raise RuntimeError("the compiler returned %d sources, not %d" % (len(slots), len(self.served)))
        except (RuntimeError, subprocess.TimeoutExpired, ValueError, KeyError) as e:
            slots = [dict(s, ok=False, message="PLAY: %s" % e) if k in only else None for k, s in enumerate(self.latest)]
        for k, s in enumerate(slots):
            if s is None or k not in only:
                slots[k] = self.latest[k]
                continue
            self.compiles[k] += 1
            if s["ok"]:
                s["scene_bytes"] = s["scene_bytes"].encode("utf-8")
                s["map_bytes"] = s["map_bytes"].encode("utf-8")
        lines = []
        with self.lock:
            served = list(self.served)
            for i, s in enumerate(slots):
                old = served[i]
                if i not in only:
                    continue
                if s["ok"]:
                    if old is None or old["sha"] != s["sha"] or old["map_sha"] != s["map_sha"]:
                        lines.append("LIVE  [%d] scene %s -> %s%s" % (i, old["sha"][:12] if old else "(none)", s["sha"][:12],
                                                                     "  (a new map: a new game)" if old and old["map_sha"] != s["map_sha"] else ""))
                    served[i] = s
                elif s["message"] != self.latest[i].get("message") or self.latest[i]["ok"]:
                    lines.append("LIVE  [%d] refused; %s stands\n%s" % (i, ("scene " + old["sha"][:12]) if old else "nothing", s["message"]))
            changed = [(a and a["sha"], a and a["map_sha"]) for a in served] != [(a and a["sha"], a and a["map_sha"]) for a in self.served] or \
                [(s["ok"], s["message"], s.get("verdict"), s.get("codes")) for s in slots] != \
                [(s["ok"], s["message"], s.get("verdict"), s.get("codes")) for s in self.latest]
            self.served, self.latest = served, slots
            self.compiled_ms = int((time.perf_counter() - t0) * 1000)
            if changed:
                self.version += 1
        return ["%s  (v%d, %d ms)" % (ln, self.version, self.compiled_ms) for ln in lines]

    def watch(self, say=print):
        files = self.watched()
        seen = self.stamp(files)
        while not self.stopping:
            time.sleep(self.poll)
            files = self.watched()
            now = self.stamp(files)
            if now == seen:
                continue
            # let a writer finish: the stamps must hold still for one more poll
            while not self.stopping:
                time.sleep(self.poll)
                again = self.stamp(files)
                if again == now:
                    break
                now = again
            seen = now
            d = [self.digest(self.inputs_of(k)) for k in range(len(self.served))]
            changed = [k for k in range(len(d)) if d[k] != self.inputs[k]]
            if not changed:
                continue
            self.inputs = d
            for ln in self.recompile(changed):
                self.log.append(ln)
                say(ln)

    # ------------------------------------------------------------------ what the page reads
    def state(self):
        with self.lock:
            slots = []
            for s, last in zip(self.served, self.latest):
                slots.append({"label": last["label"], "ok": last["ok"], "message": last["message"],
                              "verdict": last.get("verdict", ""), "codes": last.get("codes", []),
                              "served": {"sha": s["sha"], "map": s["map"], "map_sha": s["map_sha"], "counts": s["counts"],
                                         "verdict": s.get("verdict", ""), "codes": s.get("codes", [])} if s else None})
            for s in self.extra:
                slots.append({"label": s["label"], "ok": True, "message": "", "verdict": s.get("verdict", ""), "codes": s.get("codes", []),
                              "studio": True, "served": {"sha": s["sha"], "map": s["map"], "map_sha": s["map_sha"], "counts": s["counts"],
                                                         "verdict": s.get("verdict", ""), "codes": s.get("codes", [])}})
            out = {"format": "VERDANDI-PLAY-LIVE 0", "brief": self.brief, "version": self.version, "compiled_ms": self.compiled_ms,
                   "slots": slots, "code": self.code()}
        out["studio"] = self.studio.state() if self.studio else {"provider": {"configured": False, "model": "", "config": "", "error": self.studio_error},
                                                                   "request": None, "last": {}}
        return out

    def slot(self, k):
        with self.lock:
            if 0 <= k < len(self.served):
                return self.served[k]
            k -= len(self.served)
            return self.extra[k] if 0 <= k < len(self.extra) else None


class Host:
    """What the studio's gateway needs of this launcher."""

    def __init__(self, live):
        self.live = live
        self._scene = (None, None)

    def scene0(self):
        """(sha, scene) of the brief as the page is served it now: what the references' status is read against."""
        s = self.live.slot(0)
        if s is None:
            return None, None
        if self._scene[0] != s["sha"]:
            self._scene = (s["sha"], json.loads(s["scene_bytes"]))
        return self._scene

    def director(self):
        return director()

    def workspace(self):
        return workspace(self.live.brief)

    def candidate_slot(self, ws, it, label):
        return candidate_slot(ws, it, label)

    def publish(self, slots):
        return self.live.publish(slots)


STUDIO_POSTS = ("/studio/ask", "/studio/cancel", "/studio/admit", "/studio/reject", "/studio/undo", "/studio/select", "/studio/pin", "/studio/unpin")


def studio_post(live, path, body):
    """One of the page's studio requests: (HTTP status, JSON reply)."""
    import studio
    g = live.studio
    if g is None:
        return 409, {"ok": False, "code": "STUDIO-NO-PROVIDER", "message": "the studio is not running"}
    try:
        if path == "/studio/ask":
            return 200, {"ok": True, "id": g.ask(body.get("prompt"), body.get("piece"), body.get("camera"))}
        if path == "/studio/select":
            return 200, {"ok": True, "refs": g.select(body.get("piece"))}
        if path == "/studio/pin":
            return 200, {"ok": True, "refs": g.pin(body.get("piece"))}
        if path == "/studio/unpin":
            return 200, {"ok": True, "refs": g.unpin(body.get("tag"))}
        if path == "/studio/cancel":
            return 200, {"ok": g.cancel_request(body.get("id"))}
        if path == "/studio/admit":
            return 200, dict(g.admit(body.get("id"), body.get("candidate")), ok=True)
        if path == "/studio/reject":
            return 200, dict(g.reject(body.get("id"), body.get("candidate")), ok=True)
        return 200, dict(g.undo(), ok=True)
    except studio.StudioError as e:
        return 409, {"ok": False, "code": e.code, "message": e.detail}
    except (dress.ArtError, level.MapError, OSError, ValueError, KeyError, TypeError) as e:
        return 409, {"ok": False, "code": "STUDIO-FAILED", "message": "%s: %s" % (type(e).__name__, str(e)[:300])}


def server(live, port=0):
    import secrets
    page_t = open(os.path.join(WEB, "play.html"), encoding="utf-8").read()
    brief = live.brief
    live.token = secrets.token_hex(16)

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, code, body, ctype):
            self.send_response(code)
            for k, v in (("Content-Type", ctype), ("Content-Length", str(len(body))), ("Cache-Control", "no-store"),
                         ("Cross-Origin-Opener-Policy", "same-origin"), ("Cross-Origin-Embedder-Policy", "require-corp")):
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path, _, query = self.path.partition("?")
            q = dict(kv.split("=", 1) for kv in query.split("&") if "=" in kv)
            k = 0
            if "slot" in q:
                if not re.fullmatch(r"[0-9]{1,3}", q["slot"]):
                    return self.send(404, b"not found", "text/plain")
                k = int(q["slot"])
            if path == "/":
                self.send_response(302)
                self.send_header("Location", "/play.html")
                self.end_headers()
                return
            if path == "/play.html":
                s0 = live.slot(0)
                page = page_t.replace("%BRIEF%", brief).replace("%SHA%", s0["sha"] if s0 else "").replace("%STUDIO%", live.token)
                return self.send(200, page.encode("utf-8"), "text/html; charset=utf-8")
            if path == "/live":
                return self.send(200, json.dumps(live.state(), sort_keys=True).encode("utf-8"), "application/json")
            if path in FILES:
                f, ctype = FILES[path]
                with open(f, "rb") as fh:
                    return self.send(200, fh.read(), ctype)
            s = live.slot(k)
            if s is not None and path == "/scene/%s.json" % brief:
                return self.send(200, s["scene_bytes"], "application/json")
            if s is not None and path == "/map/%s.json" % s["map"]:
                return self.send(200, s["map_bytes"], "application/json")
            return self.send(404, b"not found", "text/plain")

        def do_POST(self):
            # the studio's requests: only from the page this server served (its token, in a header a page of another
            # origin cannot send without a preflight this server never answers), and only to this host by name
            path = self.path.partition("?")[0]
            if path not in STUDIO_POSTS:
                return self.send(404, b"not found", "text/plain")
            host = self.headers.get("Host", "")
            port_ = self.server.server_address[1]
            if host not in ("127.0.0.1:%d" % port_, "localhost:%d" % port_) or self.headers.get("X-Studio-Token") != live.token:
                return self.send(403, b"forbidden", "text/plain")
            n = int(self.headers.get("Content-Length", "0") or 0)
            if n > 65536 or not (self.headers.get("Content-Type", "").startswith("application/json")):
                return self.send(400, b"a studio request is JSON of at most 64 KiB", "text/plain")
            try:
                body = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
                if not isinstance(body, dict):
                    raise ValueError("not an object")
            except (UnicodeDecodeError, ValueError):
                return self.send(400, b"not a JSON object", "text/plain")
            code, reply = studio_post(live, path, body)
            return self.send(code, json.dumps(reply, sort_keys=True).encode("utf-8"), "application/json")

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def start_studio(live, config, say=print):
    """The studio's gateway on this launcher's brief. Without --director it runs with no provider: the page says so, and
    the world is played as ever. A configuration that cannot be read is said, and the same holds."""
    import studio
    cfg, err = None, ""
    if config:
        try:
            cfg = studio.load_config(config)
        except studio.StudioError as e:
            err = str(e)
    own = os.path.abspath(os.path.join(ROOT, "art", "briefs", live.brief + ".art"))
    if live.art_path and os.path.abspath(live.art_path) != own:
        cfg, err = None, "the studio edits %s; --art plays another file" % os.path.relpath(own, REPO)
    live.studio = studio.Gateway(Host(live), live.brief, cfg, ROOT, say=say)
    live.studio.error = err
    if config or err:
        say("studio: %s" % (err or "the director %s (%s); Enter in the page summons it, E selects" % (cfg["model"], os.path.relpath(cfg["path"], REPO))))
    return live.studio


def opts(argv, k):
    return [argv[i + 1] for i, a in enumerate(argv) if a == k and i + 1 < len(argv)]


def main(argv):
    if "--selftest" in argv:
        return selftest()
    global ROOT
    one = lambda k, d=None: (opts(argv, k) or [d])[0]
    vals = set(opts(argv, "--port") + opts(argv, "--art") + opts(argv, "--intent") + opts(argv, "--only") + opts(argv, "--director") + opts(argv, "--root"))
    pos = [a for a in argv if not a.startswith("--") and a not in vals]
    if not pos:
        print("usage: python art/play.py BRIEF [--intent FILE]... [--art PATH] [--port N] [--no-browser] [--no-watch] [--check]\n"
              "       python art/play.py --selftest", file=sys.stderr)
        return 2
    brief, art_path, intents = pos[0], one("--art"), opts(argv, "--intent")
    if one("--root"):
        ROOT = os.path.abspath(one("--root"))
        if art_path is None:
            art_path = os.path.join(ROOT, "art", "briefs", brief + ".art")
    if "--emit" in argv:
        only = one("--only")
        return emit(brief, art_path, intents, None if only is None else {int(k) for k in only.split(",")})
    first = brief_slot(brief, art_path)
    if not first["ok"]:
        print(first["message"], file=sys.stderr)
        return 1
    slots = [first] + [intent_slot(brief, f) for f in intents]
    for i, s in enumerate(slots):
        print(line(i, s))
    if "--check" in argv:
        print("the art checks passed; not served (--check)" if all(s["ok"] for s in slots) else "a source is not served (--check)")
        return 0 if all(s["ok"] for s in slots) else 1
    live = Live(brief, art_path, intents, slots=slots)
    start_studio(live, one("--director"))
    srv = server(live, int(one("--port", "0")))
    url = "http://127.0.0.1:%d/" % srv.server_address[1]
    print(SERVED)
    if "--no-watch" not in argv:
        threading.Thread(target=live.watch, daemon=True).start()
        print("live: watching %d files; an edit that passes the checks is drawn without a restart" % len(live.watched()))
    print("open %s  — Ctrl+C here to stop" % url)
    if "--no-browser" not in argv:
        webbrowser.open(url)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    live.stopping = True
    if live.studio:
        live.studio.shutdown()
    srv.shutdown()
    return 0


# ---------------------------------------------------------------------------------------------- the self-test
def selftest():
    """The live loop without a browser, in a scratch folder: the served scene follows an edit to the art and to an intent,
    a touch that changes nothing compiles nothing, and each planted defect is refused with the old scene left served.
    Compiles with the repository's own code; writes only in the scratch folder."""
    brief = "plaza-night"
    tmp = tempfile.mkdtemp(prefix="play-selftest-")
    rows = []

    def row(name, ok, detail):
        rows.append(ok)
        print("[%s] %s — %s" % ("PASS" if ok else "FAIL", name, detail))

    def get(srv, path):
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d%s" % (srv.server_address[1], path), timeout=30) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, b""

    def until(live, v0, secs=60):
        t = time.time()
        while time.time() - t < secs:
            if live.version != v0:
                return True
            time.sleep(0.1)
        return False

    srv = None
    live = None
    sha = lambda k: (live.slot(k) or {}).get("sha")
    try:
        art = os.path.join(tmp, brief + ".art")
        base = open(os.path.join(dress.BRIEFS, brief + ".art"), "rb").read()
        open(art, "wb").write(base)
        rounds = os.path.join(HERE, "rounds", "plaza-cantilevers")
        intent = os.path.join(tmp, "candidate.intent")
        shutil.copy(os.path.join(rounds, "C.intent"), intent)
        live = Live(brief, art, [intent], poll=0.15)
        srv = server(live)
        threading.Thread(target=live.watch, kwargs={"say": lambda s: None}, daemon=True).start()
        head = brief_slot(brief)
        s0 = live.slot(0)
        code, body = get(srv, "/scene/%s.json" % brief)
        _c, mbody = get(srv, "/map/%s.json?slot=0" % s0["map"])
        row("serves-the-brief", s0["ok"] and s0["sha"] == head["sha"] and code == 200 and sha256(body) == head["sha"] and mbody == head["map_bytes"],
            "the copy's scene %s is the brief's, and the bytes served hash to it" % s0["sha"][:12])
        bad = ["/art/play.py", "/../art/dress.py", "/scene/other.json", "/scene/%s.json?slot=7" % brief, "/scene/%s.json?slot=x" % brief,
               "/map/%s.json" % brief, "/graybox/web/sim.js", "/web/play.js"]
        codes = [get(srv, p)[0] for p in bad]
        row("named-paths-only", all(c == 404 for c in codes), "%d paths outside the named ones, every one 404" % len(bad))
        st = json.loads(get(srv, "/live")[1])
        c1 = live.slot(1)
        row("intent-served", c1 is not None and st["slots"][1]["served"]["verdict"] == "CLEAN" and st["slots"][1]["served"]["map_sha"] == s0["map_sha"],
            "candidate C served as the director evaluates it: %s, the same map" % st["slots"][1]["served"]["verdict"])

        # an edit to the art is served, and is what compiling that text gives
        v = live.version
        text = base.replace(b"rain 0.8", b"rain 0.4")
        open(art, "wb").write(text)
        ok = until(live, v)
        s1 = live.slot(0)
        _o, _m, _x = compile_scene(brief, art)
        row("edit-swaps", ok and s1["sha"] != head["sha"] and s1["sha"] == _o["lineage"]["scene_sha256"] and s1["map_sha"] == head["map_sha"]
            and sha256(get(srv, "/scene/%s.json" % brief)[1]) == s1["sha"],
            "rain 0.8 -> 0.4: scene %s -> %s, compiled in a fresh process as in this one, the map the same" % (head["sha"][:12], s1["sha"][:12]))

        # a touch that changes no byte compiles nothing
        v = live.version
        n = list(live.compiles)
        os.utime(art, None)
        time.sleep(1.0)
        row("touch-ignored", live.version == v and live.compiles == n, "the file's time moved, its bytes did not: no compile, still v%d" % v)

        # plants: each refused, the scene before it still served
        plants = [
            ("a canopy where a player can be", text + b"canopy plaza concrete 3.0\n", "no dressing where a player can be"),
            ("a statement the exporter cannot read", text + b"canopy plaza\n", "the exporter refused"),
        ]
        for name, body_, want in plants:
            v = live.version
            open(art, "wb").write(body_)
            ok = until(live, v)
            st = live.state()["slots"][0]
            row("refused-keeps: " + name, ok and not st["ok"] and want in st["message"] and sha(0) == s1["sha"]
                and sha256(get(srv, "/scene/%s.json" % brief)[1]) == s1["sha"],
                "refused (%s); scene %s still served" % (want, s1["sha"][:12]))
        v = live.version
        open(art, "wb").write(base)
        ok = until(live, v)
        row("restore", ok and live.state()["slots"][0]["ok"] and sha(0) == head["sha"],
            "the brief's own text again: scene %s, as at the start" % head["sha"][:12])

        # the intent: rewritten, served; a revision naming nothing, refused
        a_sha = intent_slot(brief, os.path.join(rounds, "A.intent"))["sha"]
        n0 = live.compiles[0]
        v = live.version
        shutil.copy(os.path.join(rounds, "A.intent"), intent)
        ok = until(live, v)
        row("intent-swaps", ok and sha(1) == a_sha and sha(1) != c1["sha"],
            "the candidate file rewritten from C to A: scene %s -> %s" % (c1["sha"][:12], a_sha[:12]))
        row("only-what-changed", live.compiles[0] == n0, "the brief's source not compiled for an edit to the intent (%d compiles of it, as before)" % n0)
        doc = json.loads(open(os.path.join(rounds, "A.intent"), "rb").read())
        doc["revision"] = ["= canopy plaza concrete_slab 7.0 0,0 1,1 deep 1.2"]
        v = live.version
        open(intent, "wb").write(director().canon.dumps(doc))
        ok = until(live, v)
        st = live.state()["slots"][1]
        row("refused-keeps: an intent naming no statement", ok and not st["ok"] and "INTENT-APPLY" in st["message"] and sha(1) == a_sha,
            "refused (INTENT-APPLY); candidate A still served")

        doc["revision"] = ["= canopy plaza concrete_slab 3.0 19,10 28,11"]
        v = live.version
        open(intent, "wb").write(director().canon.dumps(doc))
        ok = until(live, v)
        st = live.state()["slots"][1]
        row("refused-keeps: an intent whose candidate fails a check", ok and not st["ok"] and "CHECK-FAILED" in st["message"] and sha(1) == a_sha,
            "a slab lowered to 3.0 m: the director's verdict REFUSED (CHECK-FAILED), not served; candidate A still served")

        # the compiler itself failing (an exporter half-written, say) leaves everything served as it was
        cmd, live.cmd = live.cmd, [sys.executable, "-c", "import sys; sys.stderr.write('SyntaxError: planted\\n'); sys.exit(3)"]
        v = live.version
        open(art, "wb").write(text)
        ok = until(live, v)
        st = live.state()["slots"]
        row("refused-keeps: the compiler stops", ok and not st[0]["ok"] and "exit 3" in st[0]["message"] and sha(0) == head["sha"]
            and sha(1) == a_sha, "the art's source refused (exit 3), its scene %s still served; the intent's not compiled" % head["sha"][:12])
        live.cmd = cmd
    finally:
        if live:
            live.stopping = True
        if srv:
            srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    print("LIVE SELFTEST %d/%d" % (sum(rows), len(rows)))
    return 0 if all(rows) else 1


# ---------------------------------------------------------------------------------------------- the studio's self-test
TEST_PROVIDERS = {
    # each a provider a director could be: what it does, and what the gateway must make of it
    "malformed.py": "import sys; sys.stdin.read(); sys.stdout.write('this is not JSON')",
    "wrong_id.py": "import sys, json; r = json.load(sys.stdin); print(json.dumps({'format': 'VERDANDI-STUDIO-RESPONSE', 'version': '0', 'id': 'another', 'provider': {'name': 't', 'model': 't'}, 'candidates': []}))",
    "one_bad.py": ("import sys, json; r = json.load(sys.stdin); st = r['target']['statement']['text']\n"
                   "good = {'title': 'Deeper', 'rationale': 'deeper', 'revision': ['= ' + st + ' deep 2.6'], 'scope': [r['target']['patterns'][0]], 'preserve': []}\n"
                   "bad = {'title': 'Nowhere', 'rationale': 'a slab the brief does not have', 'revision': ['= canopy plaza concrete_slab 7.0 0,0 1,1'], 'scope': ['plaza/canopy/*'], 'preserve': []}\n"
                   "leak = {'title': 'Leaks', 'rationale': 'the slab and the lamps', 'revision': ['= ' + st + ' deep 2.0', '= lamp plaza 255,120,60 500 3'], 'scope': [r['target']['patterns'][0]], 'preserve': []}\n"
                   "print(json.dumps({'format': 'VERDANDI-STUDIO-RESPONSE', 'version': '0', 'id': r['id'], 'provider': {'name': 't', 'model': 't'}, 'candidates': [bad, good, leak]}))"),
    "slow.py": "import sys, time, os; sys.stdin.read(); time.sleep(20); open(os.environ.get('STUDIO_TEST_MARK', os.devnull), 'w').write('ran to the end')",
    "crash.py": "import sys; sys.stdin.read(); sys.stderr.write('the model is unavailable: 503\\n'); sys.exit(3)",
    "huge.py": "import sys; sys.stdin.read(); sys.stdout.write('x' * 200000)",
    "bad_usage.py": "import sys, json; r = json.load(sys.stdin); print(json.dumps({'format': 'VERDANDI-STUDIO-RESPONSE', 'version': '0', 'id': r['id'], 'provider': {'name': 't', 'model': 't', 'usage': {'input_tokens': -5, 'output_tokens': 1, 'cost_usd': None, 'cost_basis': ''}}, 'candidates': []}))",
    "spawner.py": ("import sys, subprocess, time, os; sys.stdin.read()\n"
                   "subprocess.Popen([sys.executable, '-c', 'import time, os, sys; time.sleep(2); open(sys.argv[1], \"w\").write(\"outlived\")', os.environ['STUDIO_TEST_CHILD']])\n"
                   "time.sleep(30)"),
    # a stand-in for Claude Code's CLI (art/providers/claude_code.py runs it through VERDANDI_CLAUDE): it records what it was
    # given, and answers as `claude -p --output-format stream-json` does, in the way FAKE_CLAUDE names
    "fake_claude.py": ("import sys, json, os, time\n"
                       "a = sys.argv[1:]; text = sys.stdin.read(); mode = os.environ.get('FAKE_CLAUDE', 'ok')\n"
                       "opt = lambda k: a[a.index(k) + 1] if k in a else None\n"
                       "sp = opt('--system-prompt-file'); system = open(sp, encoding='utf-8').read() if sp else None\n"
                       "json.dump({'argv': a, 'stdin': text, 'system': system, 'cwd': os.getcwd(), 'cwd_files': sorted(os.listdir('.'))}, open(os.environ['FAKE_CLAUDE_SEEN'], 'w'))\n"
                       "emit = lambda e: (sys.stdout.write(json.dumps(e) + '\\n'), sys.stdout.flush())\n"
                       "tools = ['StructuredOutput', 'Bash', 'mcp__browser__navigate'] if mode == 'tools' else ['StructuredOutput']\n"
                       "emit({'type': 'system', 'subtype': 'init', 'model': 'fake-sonnet', 'tools': tools, 'mcp_servers': []})\n"
                       "if mode == 'tools':\n"
                       "    time.sleep(3); open(os.environ['STUDIO_TEST_CHILD'], 'w').write('answered'); sys.exit(0)\n"
                       "stmt = [ln.split(': ', 1)[1].split(' ; key')[0] for ln in text.splitlines() if ln.startswith('61: ')][0]\n"
                       "cand = {'title': 'Heavier section', 'rationale': 'deeper', 'revision': ['= ' + stmt + ' deep 2.4'], 'scope': ['plaza/canopy/*'], 'preserve': ['the route']}\n"
                       "if mode == 'extra': cand['note'] = 'a field the schema does not have'\n"
                       "usage = {'input_tokens': 3, 'cache_creation_input_tokens': 4000, 'cache_read_input_tokens': 100, 'output_tokens': 250}\n"
                       "if mode == 'retries': emit({'type': 'result', 'subtype': 'error_max_structured_output_retries', 'is_error': True, 'result': ''}); sys.exit(1)\n"
                       "if mode == 'auth': emit({'type': 'result', 'subtype': 'error_during_execution', 'is_error': True, 'result': 'Not logged in. Please run /login'}); sys.exit(1)\n"
                       "emit({'type': 'result', 'subtype': 'success', 'is_error': False, 'result': '', 'structured_output': {'candidates': [cand]}, 'usage': usage, 'total_cost_usd': 0.0123})\n"),
    # STUDIO-1: every canopy of the brief made 1 m deep, the target's and the others' alike
    "all_canopies.py": ("import sys, json, re; r = json.load(sys.stdin)\n"
                        "rev = ['= ' + re.sub(r' deep [0-9.]+', '', s['text']) + ' deep 1.0' for s in r['statements'] if s['text'].startswith('canopy ')]\n"
                        "print(json.dumps({'format': 'VERDANDI-STUDIO-RESPONSE', 'version': '0', 'id': r['id'], 'provider': {'name': 't', 'model': 't'}, "
                        "'candidates': [{'title': 'All deep', 'rationale': 'every canopy 1 m deep', 'revision': rev, 'scope': ['plaza/canopy/*'], 'preserve': []}]}))"),
    # STUDIO-1: the target's corners moved one cell: its id is its cells, so a new object, and the old one changed
    "corners.py": ("import sys, json; r = json.load(sys.stdin); st = r['target']['statement']\n"
                   "rev = ['- ' + st['key'], '+ ' + st['text'].replace(' 28,11', ' 27,11')]\n"
                   "print(json.dumps({'format': 'VERDANDI-STUDIO-RESPONSE', 'version': '0', 'id': r['id'], 'provider': {'name': 't', 'model': 't'}, "
                   "'candidates': [{'title': 'Narrower', 'rationale': 'one cell narrower', 'revision': rev, 'scope': ['plaza/canopy/*'], 'preserve': []}]}))"),
    # STUDIO-1: the canopies' material lightened, their statements untouched: every object of that material is touched
    "material.py": ("import sys, json; r = json.load(sys.stdin)\n"
                    "m = [s['text'] for s in r['statements'] if s['text'].startswith('material concrete_slab ')][0].split()\n"
                    "m[2] = '120,118,112'\n"
                    "print(json.dumps({'format': 'VERDANDI-STUDIO-RESPONSE', 'version': '0', 'id': r['id'], 'provider': {'name': 't', 'model': 't'}, "
                    "'candidates': [{'title': 'Lighter slab', 'rationale': 'a lighter concrete', 'revision': ['= ' + ' '.join(m)], 'scope': ['material/concrete_slab', 'plaza/canopy/*'], 'preserve': []}]}))"),
    "four.py": ("import sys, json; r = json.load(sys.stdin); st = r['target']['statement']['text']\n"
                "c = lambda d: {'title': 'Deep ' + d, 'rationale': 'deeper', 'revision': ['= ' + st + ' deep ' + d], 'scope': ['plaza/canopy/*'], 'preserve': []}\n"
                "print(json.dumps({'format': 'VERDANDI-STUDIO-RESPONSE', 'version': '0', 'id': r['id'], 'provider': {'name': 't', 'model': 't'}, 'candidates': [c(d) for d in ('1.0', '1.5', '2.0', '2.5')]}))"),
}


def studio_selftest():
    """The gateway end to end in a scratch copy of the brief, its ledger and the maps, served by this launcher: the
    scripted provider's candidates drawn, replayed from their records, admitted, rejected and undone through the
    ledger; and each way a provider can fail (no provider, a refused configuration, not JSON, another request's id, a
    candidate the director refuses, one that leaks, a cancellation, a newer request, a timeout, an exit with an error,
    too much output, a command that cannot start), each leaving the world served as it was."""
    global ROOT
    import studio
    brief, tmp, rows = "plaza-night", tempfile.mkdtemp(prefix="studio-selftest-"), []
    saved_root = ROOT

    def row(name, ok, detail):
        rows.append(ok)
        print("[%s] %s — %s" % ("PASS" if ok else "FAIL", name, detail))

    def cfg(name, argv, timeout=30, size=65536):
        path = os.path.join(tmp, name + ".json")
        open(path, "w").write(json.dumps({"provider": "cli", "argv": argv, "model": name, "timeout_s": timeout, "max_output_bytes": size}))
        return path

    def wait(g, rid, secs=60):
        t = time.time()
        while time.time() - t < secs:
            r = g.state()["request"]
            if r and r["id"] == rid and r["state"] != "running":
                return r
            time.sleep(0.05)
        return g.state()["request"]

    def post(srv, path, body, token, host=None):
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (srv.server_address[1], path), data=json.dumps(body).encode("utf-8"), method="POST",
                                     headers={"Content-Type": "application/json", "X-Studio-Token": token, "Host": host or "127.0.0.1:%d" % srv.server_address[1]})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read())
            except ValueError:
                return e.code, {}

    live = srv = None
    try:
        for sub in ("art/briefs", "art/ledger", "graybox/maps"):
            shutil.copytree(os.path.join(REPO, sub), os.path.join(tmp, sub))
        for name, code in TEST_PROVIDERS.items():
            open(os.path.join(tmp, name), "w").write(code + "\n")
        ROOT = tmp
        art = os.path.join(tmp, "art", "briefs", brief + ".art")
        original = open(art, "rb").read()
        live = Live(brief, art, [], poll=0.15)
        srv = server(live)
        threading.Thread(target=live.watch, kwargs={"say": lambda s: None}, daemon=True).start()
        s0 = live.slot(0)["sha"]
        piece, cam = "canopy:19,10-28,11", {"x": 40.0, "y": 1.62, "z": 30.0, "yaw_deg": 0.0, "pitch_deg": 12.0}

        # no provider; a configuration refused whole
        g = start_studio(live, None, say=lambda s: None)
        try:
            g.ask("heavier", piece, cam)
            row("no provider: the ask refused, the world served", False, "it was asked")
        except studio.StudioError as e:
            row("no provider: the ask refused, the world served", e.code == "STUDIO-NO-PROVIDER" and live.slot(0)["sha"] == s0, e.code)
        bad_cfg = os.path.join(tmp, "shell.json")
        open(bad_cfg, "w").write(json.dumps({"provider": "cli", "argv": "python provider.py --prompt \"$PROMPT\"", "model": "m", "timeout_s": 30, "max_output_bytes": 65536}))
        g = start_studio(live, bad_cfg, say=lambda s: None)
        row("a configuration with a shell line refused whole", g.cfg is None and "STUDIO-CONFIG" in g.error and live.state()["studio"]["provider"]["error"] == g.error, g.error[:90])

        # the scripted provider: three candidates drawn, the same map, the request recorded
        g = start_studio(live, os.path.join(REPO, "art", "providers", "scripted.json"), say=lambda s: None)
        rid = g.ask("make this overhang heavier and more imposing, a restrained magenta glow underneath", piece, cam)
        r = wait(g, rid)
        drawn = [c for c in r["candidates"] if c["slot"] is not None]
        same_map = all(live.slot(c["slot"])["map_sha"] == live.slot(0)["map_sha"] for c in drawn)
        row("three candidates drawn for a selected slab", r["state"] == "done" and len(drawn) == 3 and all(c["verdict"] == "CLEAN" for c in drawn) and same_map
            and len({live.slot(c["slot"])["sha"] for c in drawn} | {s0}) == 4,
            "%s; %s; each a scene of its own on the same map (so the page swaps the scene and keeps the game)" % (r["message"], ", ".join("%s %s %s" % (c["letter"], c["title"], c["verdict"]) for c in drawn)))
        st = live.state()
        row("the page sees them as sources", [x.get("studio") for x in st["slots"]] == [None, True, True, True] and st["studio"]["request"]["id"] == rid,
            "%d sources: the brief and the three candidates" % len(st["slots"]))
        rec = os.path.join(tmp, "art", "build", "studio", brief, rid)
        req = json.loads(open(os.path.join(rec, "request.json"), "rb").read())
        log = [json.loads(ln) for ln in open(os.path.join(tmp, "art", "build", "studio", brief, "requests.jsonl"), "rb").read().splitlines()]
        row("the request recorded: context, response, intents", req["target"]["statement"]["text"].startswith("canopy plaza concrete_slab 7.0 19,10 28,11")
            and req["head"] == r["head"] and sorted(os.listdir(rec)) == ["A.intent", "B.intent", "C.intent", "request.json", "response.raw"]
            and log[-1]["id"] == rid and log[-1]["outcome"] == "DONE" and log[-1]["model"] == "scripted-1",
            "the target's statement (line %d), the head, the response's sha256, each candidate's intent" % req["target"]["statement"]["line"])
        replay = intent_slot(brief, os.path.join(rec, "A.intent"))
        row("a recorded candidate replayed without the provider", replay["ok"] and replay["sha"] == live.slot(drawn[0]["slot"])["sha"],
            "play.py --intent %s gives scene %s, the one drawn" % (os.path.relpath(os.path.join(rec, "A.intent"), tmp), replay["sha"][:12]))

        # the HTTP boundary: the token and the host
        tok = live.token
        a, _ = post(srv, "/studio/cancel", {"id": rid}, "not-the-token")
        b, _ = post(srv, "/studio/cancel", {"id": rid}, tok, host="evil.example:80")
        c, body = post(srv, "/studio/cancel", {"id": rid}, tok)
        row("a POST without the page's token, or to another host, refused", a == 403 and b == 403 and c == 200, "no token %d, another host %d, the page's %d" % (a, b, c))

        # admit A through HTTP: the brief written, the ledger two events longer, the head the candidate's, verified
        n0 = len(workspace(brief) and director().led.read(os.path.join(tmp, "art", "ledger", brief + ".ledger"))[0])
        a_sha = live.slot(drawn[0]["slot"])["sha"]
        code, body = post(srv, "/studio/admit", {"id": rid, "candidate": "A"}, tok)
        v = live.version
        t = time.time()
        while live.slot(0)["sha"] != a_sha and time.time() - t < 30:
            time.sleep(0.1)
        events = director().led.read(os.path.join(tmp, "art", "ledger", brief + ".ledger"))[0]
        try:
            quiet_verify = studio.quiet(director().cmd_verify, workspace(brief), quiet=True)
            verified = True
        except director().led.LedgerError as e:
            verified = str(e)
        row("A admitted: the brief written, the ledger's evaluate and admit, the page's source 0 the candidate", code == 200 and body.get("ok") and len(events) == n0 + 2
            and [e["kind"] for e in events[-2:]] == ["evaluate", "admit"] and events[-1]["observed"]["chooser"] == "the designer (studio)"
            and live.slot(0)["sha"] == a_sha and verified is True,
            "ledger #%s, #%s; source 0 now scene %s; the ledger verifies" % (events[-2]["seq"], events[-1]["seq"], live.slot(0)["sha"][:12]))
        code, body = post(srv, "/studio/admit", {"id": rid, "candidate": "B"}, tok)
        row("B, drawn at the head before A, refused as stale", code == 409 and body.get("code") == "STUDIO-STALE", body.get("message", "")[:100])
        code, body = post(srv, "/studio/reject", {"id": rid, "candidate": "C"}, tok)
        events = director().led.read(os.path.join(tmp, "art", "ledger", brief + ".ledger"))[0]
        row("C rejected: an evaluation and a refusal in the ledger", code == 200 and [e["kind"] for e in events[-2:]] == ["evaluate", "refuse"], "ledger #%s" % ", #".join(body.get("ledger", [])))
        # a second request on the slab as A left it; its third candidate admitted; then undo twice, back to the start
        after_a = open(art, "rb").read()
        rid2 = g.ask("deeper still", piece, cam)
        r2 = wait(g, rid2)
        c3 = [c for c in r2["candidates"] if c["letter"] == "C"][0]
        code, body = post(srv, "/studio/admit", {"id": rid2, "candidate": "C"}, tok)
        row("a second request, on the head A made: its C admitted", r2["state"] == "done" and r2["head"] != r["head"] and c3["verdict"] == "CLEAN" and code == 200,
            "request %s at head %s; ledger #%s" % (rid2, r2["head"][:12], ", #".join(body.get("ledger", []))))
        code, body = post(srv, "/studio/undo", {}, tok)
        undo1 = body
        row("undo: the last admission's exact inverse admitted, the brief as A left it", code == 200 and body.get("ok") and open(art, "rb").read() == after_a,
            "ledger #%s, the inverse of #%s" % (", #".join(body.get("ledger", [])), body.get("of")))
        code, body = post(srv, "/studio/undo", {}, tok)
        t = time.time()
        while live.slot(0)["sha"] != s0 and time.time() - t < 30:
            time.sleep(0.1)
        row("undo again: an undo is never undone; it walks back to A, and the brief's bytes and scene are as at the start",
            code == 200 and body.get("ok") and body.get("of") != undo1.get("of") and open(art, "rb").read() == original and live.slot(0)["sha"] == s0,
            "ledger #%s, the inverse of #%s; the brief as it was, byte for byte; scene %s" % (", #".join(body.get("ledger", [])), body.get("of"), s0[:12]))
        try:
            studio.quiet(director().cmd_verify, workspace(brief), quiet=True)
            row("the ledger verifies after the admissions, the refusal and the undos", True, "%d events" % len(director().led.read(os.path.join(tmp, "art", "ledger", brief + ".ledger"))[0]))
        except director().led.LedgerError as e:
            row("the ledger verifies after the admissions, the refusal and the undos", False, str(e)[:120])

        # the ways a provider fails: each refused, the world as it was
        def failing(label, name, argv, want, timeout=30, size=65536, cancel_after=None, then=None):
            g = start_studio(live, cfg(name, argv, timeout, size), say=lambda s: None)
            before = (live.slot(0)["sha"], live.state()["slots"][0]["ok"])
            rid = g.ask("heavier", piece, cam)
            if cancel_after is not None:
                time.sleep(cancel_after)
                g.cancel_request(rid)
            if then:
                then(g)
            r = wait(g, rid, 90)
            ok = r["code"] == want and (live.slot(0)["sha"], live.state()["slots"][0]["ok"]) == before
            return ok, r

        py = sys.executable
        ok, r = failing("not JSON", "malformed", [py, os.path.join(tmp, "malformed.py")], "STUDIO-RESPONSE-JSON")
        row("a provider that writes no JSON: refused whole, the world as it was", ok and len(live.state()["slots"]) == 1, r["code"] + ": " + r["message"][:70])
        ok, r = failing("wrong id", "wrong_id", [py, os.path.join(tmp, "wrong_id.py")], "STUDIO-RESPONSE-ID")
        row("a response to another request: refused", ok, r["message"][:90])
        ok, r = failing("bad usage", "bad_usage", [py, os.path.join(tmp, "bad_usage.py")], "STUDIO-RESPONSE-FIELD")
        row("a provider's usage that is not counts: refused whole", ok, r["message"][:90])
        ok, r = failing("four", "four", [py, os.path.join(tmp, "four.py")], "STUDIO-RESPONSE-CANDIDATES")
        row("a response of four candidates: refused whole, not cut to three", ok and not r["candidates"], r["message"][:90])
        g = start_studio(live, cfg("one_bad", [py, os.path.join(tmp, "one_bad.py")]), say=lambda s: None)
        rid = g.ask("heavier", piece, cam)
        r = wait(g, rid)
        by = {c["letter"]: c for c in r["candidates"]}
        row("a candidate the director refuses is shown, never drawn; the others are", r["state"] == "done" and by["A"]["verdict"] == "REFUSED" and "INTENT-APPLY" in by["A"]["codes"]
            and by["A"]["slot"] is None and by["B"]["verdict"] == "CLEAN" and by["B"]["slot"] is not None and by["C"]["verdict"] == "LEAKAGE",
            "A %s %s (not drawn); B %s; C %s (it changes a lamp outside its scope)%s" % (by["A"]["verdict"], ",".join(by["A"]["codes"]), by["B"]["verdict"], by["C"]["verdict"],
                                                                                         "" if by["B"]["verdict"] == "CLEAN" else "; " + by["B"]["message"][:200]))
        code, body = post(srv, "/studio/admit", {"id": rid, "candidate": "C"}, tok)
        row("a LEAKAGE candidate drawn but not admitted here", code == 409 and body.get("code") == "STUDIO-NOT-ADMISSIBLE", body.get("message", "")[:90])
        mark = os.path.join(tmp, "slow.ran")
        os.environ["STUDIO_TEST_MARK"] = mark
        ok, r = failing("cancelled", "slow", [py, os.path.join(tmp, "slow.py")], "STUDIO-CANCELLED", cancel_after=0.5)
        time.sleep(0.5)
        row("a request cancelled: the provider killed, nothing drawn", ok and r["state"] == "cancelled" and not os.path.exists(mark), r["state"] + ", " + r["message"])
        g = start_studio(live, cfg("slow2", [py, os.path.join(tmp, "slow.py")]), say=lambda s: None)
        first = g.ask("heavier", piece, cam)
        time.sleep(0.3)
        g.cfg = studio.load_config(os.path.join(REPO, "art", "providers", "scripted.json"))
        second = g.ask("lighter", piece, cam)
        r2 = wait(g, second)
        log = [json.loads(ln) for ln in open(os.path.join(tmp, "art", "build", "studio", brief, "requests.jsonl"), "rb").read().splitlines()]
        first_out = [e for e in log if e.get("id") == first]
        row("a newer request supersedes the one running: its result discarded", r2["state"] == "done" and r2["id"] == second and first_out and first_out[-1]["outcome"] == "STUDIO-CANCELLED",
            "the first %s, the second %s with %d candidates" % (first_out[-1]["outcome"] if first_out else "?", r2["state"], len(r2["candidates"])))
        ok, r = failing("timeout", "slow3", [py, os.path.join(tmp, "slow.py")], "STUDIO-TIMEOUT", timeout=1)
        row("a provider past its time: killed, refused", ok, r["message"][:90])
        ok, r = failing("exit", "crash", [py, os.path.join(tmp, "crash.py")], "STUDIO-PROVIDER-EXIT")
        row("a provider that exits with an error (the model unavailable): said, the world as it was", ok and "503" in r["message"], r["message"][:90])
        ok, r = failing("size", "huge", [py, os.path.join(tmp, "huge.py")], "STUDIO-RESPONSE-SIZE")
        row("a provider that prints past its limit: killed, refused", ok, r["message"][:90])
        ok, r = failing("start", "missing", [os.path.join(tmp, "no-such-provider")], "STUDIO-PROVIDER-START")
        row("a provider that cannot start: said, the world as it was", ok, r["message"][:90])
        st0 = live.state()["slots"][0]
        # the Anthropic Messages adapter, against a local server that answers as the API's documentation describes
        seen = {}

        class Mock(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))).decode("utf-8"))
                seen.update(headers={k.lower(): v for k, v in self.headers.items()}, body=body, path=self.path)
                if body.get("model") == "overloaded":
                    out, code = {"type": "error", "error": {"type": "overloaded_error", "message": "Overloaded"}}, 529
                else:
                    text = body["messages"][0]["content"]
                    stmt = [ln.split(": ", 1)[1].split(" ; key")[0] for ln in text.splitlines() if ln.startswith("61: ")][0]
                    out = {"id": "msg_test", "type": "message", "role": "assistant", "model": "mock-" + body["model"], "stop_reason": "tool_use",
                           "usage": {"input_tokens": 1234, "output_tokens": 56},
                           "content": [{"type": "tool_use", "id": "toolu_test", "name": "propose_candidates",
                                        "input": {"candidates": [{"title": "Heavier section", "rationale": "deeper", "revision": ["= " + stmt + " deep 2.4"],
                                                                  "scope": ["plaza/canopy/*"], "preserve": ["the route"]}]}}]}
                    code = 200
                b = json.dumps(out).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

        mock = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Mock)
        threading.Thread(target=mock.serve_forever, daemon=True).start()
        saved_env = {k: os.environ.get(k) for k in ("ANTHROPIC_API_KEY", "VERDANDI_DIRECTOR_MODEL", "VERDANDI_DIRECTOR_API")}
        try:
            os.environ.update(ANTHROPIC_API_KEY="test-key-not-a-real-one", VERDANDI_DIRECTOR_MODEL="test-model",
                              VERDANDI_DIRECTOR_API="http://127.0.0.1:%d/v1/messages" % mock.server_address[1])
            g = start_studio(live, os.path.join(REPO, "art", "providers", "anthropic.json"), say=lambda s: None)
            rid = g.ask("heavier, a deeper section", piece, cam)
            r = wait(g, rid)
            b, h = seen.get("body", {}), seen.get("headers", {})
            shaped = (h.get("x-api-key") == "test-key-not-a-real-one" and h.get("anthropic-version") == "2023-06-01" and b.get("model") == "test-model"
                      and b.get("tool_choice") == {"type": "tool", "name": "propose_candidates"} and b["tools"][0]["input_schema"] == studio.SCHEMA
                      and "heavier, a deeper section" in b["messages"][0]["content"] and "## The art file" in b["messages"][0]["content"])
            row("the Anthropic adapter: the request shaped as the API's documentation describes, the tool's input read back as the candidates",
                shaped and r["state"] == "done" and len(r["candidates"]) == 1 and r["candidates"][0]["verdict"] == "CLEAN" and r["provider"]["model"] == "mock-test-model",
                "the key in x-api-key, anthropic-version 2023-06-01, one tool whose input schema is the gateway's, the call forced; %s" % r["message"])
            os.environ["VERDANDI_DIRECTOR_MODEL"] = "overloaded"
            rid = g.ask("heavier", piece, cam)
            r = wait(g, rid)
            row("the API overloaded (529): said, the world as it was", r["code"] == "STUDIO-PROVIDER-EXIT" and "529" in r["message"] and live.slot(0)["sha"] == s0, r["message"][:100])
            del os.environ["ANTHROPIC_API_KEY"]
            seen.clear()
            rid = g.ask("heavier", piece, cam)
            r = wait(g, rid)
            row("no key in the environment: said, nothing sent", r["code"] == "STUDIO-PROVIDER-EXIT" and "ANTHROPIC_API_KEY" in r["message"] and not seen, r["message"][:100])
        finally:
            mock.shutdown()
            for k, v in saved_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        # a provider's own children die with it: the process group (POSIX) or taskkill /T (Windows)
        child_mark = os.path.join(tmp, "child.ran")
        os.environ["STUDIO_TEST_CHILD"] = child_mark
        ok, r = failing("child", "spawner", [py, os.path.join(tmp, "spawner.py")], "STUDIO-CANCELLED", cancel_after=0.6)
        time.sleep(3.0)
        row("a cancelled provider's own children killed with it", ok and not os.path.exists(child_mark),
            "the provider started a command that would write a mark after 2 s; cancelled at 0.6 s, no mark at 3.6 s" if not os.path.exists(child_mark) else "the child outlived the cancellation")

        # what is recorded of every call: the exit status, whether the response was valid, the time, the usage
        log = [json.loads(ln) for ln in open(os.path.join(tmp, "art", "build", "studio", brief, "requests.jsonl"), "rb").read().splitlines()]
        done = [e for e in log if e.get("outcome") == "DONE" and e.get("model") == "scripted-1"]
        bad = [e for e in log if e.get("outcome") == "STUDIO-RESPONSE-JSON"]
        crashed = [e for e in log if e.get("outcome") == "STUDIO-PROVIDER-EXIT" and "503" in e.get("detail", "")]
        api = [e for e in log if e.get("outcome") == "DONE" and (e.get("provider") or {}).get("name") == "anthropic-messages"]
        row("each call recorded with its exit status, validity, time and usage", done and all(e.get("exit") == 0 and e.get("valid") is True and e.get("provider_ms", -1) >= 0 for e in done)
            and bad and bad[-1].get("exit") == 0 and bad[-1].get("valid") is False and crashed and crashed[-1].get("exit") == 3 and "valid" not in crashed[-1]
            and api and api[-1].get("usage") == {"input_tokens": 1234 + 0, "output_tokens": 56, "cost_usd": None, "cost_basis": "not computed here: token counts as the API reported them"}
            and not any("test-key-not-a-real-one" in ln for ln in open(os.path.join(tmp, "art", "build", "studio", brief, "requests.jsonl"), encoding="utf-8")),
            "scripted: exit 0, valid; not JSON: exit 0, not valid; 503: exit 3; the API's tokens as it counted them; no key in the log")

        # Claude Code's CLI, through art/providers/claude_code.py, with a stand-in for claude
        seen_path = os.path.join(tmp, "fake_claude.seen")
        saved_env = {k: os.environ.get(k) for k in ("VERDANDI_CLAUDE", "FAKE_CLAUDE", "FAKE_CLAUDE_SEEN", "VERDANDI_DIRECTOR_MODEL")}
        said = []
        try:
            os.environ.update(VERDANDI_CLAUDE=os.path.join(tmp, "fake_claude.py"), FAKE_CLAUDE="ok", FAKE_CLAUDE_SEEN=seen_path, VERDANDI_DIRECTOR_MODEL="sonnet")
            os.environ.pop("STUDIO_TEST_CHILD", None)
            os.environ["STUDIO_TEST_CHILD"] = os.path.join(tmp, "claude.answered")
            g = start_studio(live, os.path.join(REPO, "art", "providers", "claude_code.json"), say=said.append)
            rid = g.ask("heavier, a deeper section", piece, cam)
            r = wait(g, rid)
            seen = json.loads(open(seen_path, encoding="utf-8").read())
            a = seen["argv"]
            opt_ = lambda k: a[a.index(k) + 1] if k in a else None
            sys.path.insert(0, os.path.join(REPO, "art", "providers"))
            import director_prompt
            flags = (opt_("--tools") == "" and opt_("--disallowedTools") == "mcp__*" and "--strict-mcp-config" in a and "--safe-mode" in a
                     and "--no-session-persistence" in a and opt_("--permission-mode") == "dontAsk" and opt_("--output-format") == "stream-json"
                     and json.loads(opt_("--json-schema")) == studio.SCHEMA and opt_("--model") == "sonnet" and seen["system"] == director_prompt.SYSTEM
                     and "heavier, a deeper section" in seen["stdin"] and "heavier" not in " ".join(a) and seen["cwd_files"] == ["system.txt"]
                     and os.path.realpath(seen["cwd"]) != os.path.realpath(REPO))
            e = [x for x in (json.loads(ln) for ln in open(os.path.join(tmp, "art", "build", "studio", brief, "requests.jsonl"), "rb").read().splitlines()) if x.get("id") == rid][-1]
            row("Claude Code's CLI: tools off, no session, the schema and the request given; its structured output read back",
                flags and r["state"] == "done" and len(r["candidates"]) == 1 and r["candidates"][0]["verdict"] == "CLEAN" and r["provider"]["model"] == "fake-sonnet"
                and e.get("usage") == {"input_tokens": 4103, "output_tokens": 250, "cost_usd": 0.0123, "cost_basis": "Claude Code's own client-side estimate"}
                and any(ln.startswith("STUDIO  " + rid + "  claude-code (fake-sonnet)") and "A CLEAN" in ln for ln in said),
                "--tools \"\" --disallowedTools mcp__* --strict-mcp-config --safe-mode --no-session-persistence --permission-mode dontAsk, the gateway's schema, "
                "director_prompt's system text, the prompt on stdin only, an empty folder; the model and usage it reported recorded")
            os.environ["FAKE_CLAUDE"] = "tools"
            rid = g.ask("heavier", piece, cam)
            r = wait(g, rid, 90)
            time.sleep(3.5)
            row("Claude Code offering a tool beyond its structured output: stopped, its answer never used",
                r["code"] == "STUDIO-PROVIDER-EXIT" and "Bash" in r["message"] and not os.path.exists(os.environ["STUDIO_TEST_CHILD"]) and live.slot(0)["sha"] == s0,
                r["message"][:120])
            os.environ["FAKE_CLAUDE"] = "extra"
            rid = g.ask("heavier", piece, cam)
            r = wait(g, rid)
            row("its schema enforcement not relied on: a fifth field refused by the gateway itself", r["code"] == "STUDIO-RESPONSE-FIELD", r["message"][:100])
            os.environ["FAKE_CLAUDE"] = "retries"
            rid = g.ask("heavier", piece, cam)
            r = wait(g, rid)
            row("Claude Code out of structured-output retries: said, the world as it was", r["code"] == "STUDIO-PROVIDER-EXIT" and "error_max_structured_output_retries" in r["message"], r["message"][:100])
            os.environ["FAKE_CLAUDE"] = "auth"
            rid = g.ask("heavier", piece, cam)
            r = wait(g, rid)
            row("Claude Code not logged in: said", r["code"] == "STUDIO-PROVIDER-EXIT" and "Not logged in" in r["message"], r["message"][:100])
            shim = os.path.join(tmp, "claude.cmd")
            open(shim, "w").write("@echo off\n")
            os.environ["VERDANDI_CLAUDE"] = shim
            os.remove(seen_path)
            rid = g.ask("heavier", piece, cam)
            r = wait(g, rid)
            row("a claude that only a shell can run (.cmd): refused, nothing run", r["code"] == "STUDIO-PROVIDER-EXIT" and "claude.exe" in r["message"] and not os.path.exists(seen_path), r["message"][:110])
        finally:
            for k, v in saved_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            os.environ.pop("STUDIO_TEST_CHILD", None)
        st0 = live.state()["slots"][0]
        row("the brief served throughout", st0["ok"] and live.slot(0)["sha"] == s0, "scene %s%s" % (s0[:12], "" if st0["ok"] else "; " + st0["message"][:200]))
    finally:
        ROOT = saved_root
        os.environ.pop("STUDIO_TEST_MARK", None)
        if live:
            live.stopping = True
        if srv:
            srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    references_selftest(row, cfg_dir=None)
    print("STUDIO SELFTEST %d/%d" % (sum(rows), len(rows)))
    return 0 if all(rows) else 1


def references_selftest(row, cfg_dir=None):
    """STUDIO-1's references, in a scratch copy of their own (the brief edited by hand there, so no admission is made):
    tags made, kept and never moved; the request's geometry and relations against the scene's own boxes; a candidate's
    account of the objects it changed; a prompt naming a tag it may not; an object changed, and one gone."""
    global ROOT
    import studio
    import studio_refs
    brief, tmp = "plaza-night", tempfile.mkdtemp(prefix="studio-refs-")
    saved_root = ROOT
    live = srv = None

    def wait(g, rid, secs=60):
        t = time.time()
        while time.time() - t < secs:
            r = g.state()["request"]
            if r and r["id"] == rid and r["state"] != "running":
                return r
            time.sleep(0.05)
        return g.state()["request"]

    def until(pred, secs=30):
        t = time.time()
        while time.time() - t < secs:
            if pred():
                return True
            time.sleep(0.1)
        return False

    def refused(fn, *a):
        try:
            fn(*a)
            return "", ""
        except studio.StudioError as e:
            return e.code, e.detail
    try:
        for sub in ("art/briefs", "art/ledger", "graybox/maps"):
            shutil.copytree(os.path.join(REPO, sub), os.path.join(tmp, sub))
        for name in ("all_canopies.py", "corners.py", "material.py"):
            open(os.path.join(tmp, name), "w").write(TEST_PROVIDERS[name] + "\n")
        ROOT = tmp
        art = os.path.join(tmp, "art", "briefs", brief + ".art")
        text = open(art, encoding="utf-8").read()
        # the west canopy given ribs, edge fixtures and a depth, so that it has parts and is unlike the north one
        west0 = "canopy plaza concrete_slab 7.6 19,12 20,19"
        assert west0 + "\n" in text
        text = text.replace(west0 + "\n", west0 + " deep 1.2 ribs 2 edgelit 255,178,112 60\n")
        open(art, "w", encoding="utf-8").write(text)
        live = Live(brief, art, [], poll=0.15)
        srv = server(live)
        threading.Thread(target=live.watch, kwargs={"say": lambda s: None}, daemon=True).start()
        g = start_studio(live, os.path.join(REPO, "art", "providers", "scripted.json"), say=lambda s: None)
        north, west, south = "canopy:19,10-28,11", "canopy:19,12-20,19", "canopy:19,20-28,21"

        # tags: made on first touch, kept by the object, never given to another
        r1 = g.select(north)
        r2 = g.pin(west + ":rib20")                     # a part of the west canopy: the object is the canopy
        r3 = g.pin(south)
        un = g.pin(west)                               # pinned again: unpinned
        again = g.pin(west)
        code_t, _d = refused(g.pin, north)
        extra = ["tower:19,9-23,9", "lamp:20,11", "neon:26,9:s"]
        S0 = json.loads(live.slot(0)["scene_bytes"])
        have = {v["id"] for v in S0["visuals"]}
        extra = [x for x in extra if x in have] or sorted(i for i in have if i.startswith("lamp:"))[:3]
        g.pin(extra[0])
        g.pin(extra[1])
        code_p, _d = refused(g.pin, extra[2])
        g.pin(extra[1])                                # unpinned again, back to three pins
        ok = (r1["target"] == "@1" and r2["pins"] == ["@2"] and r2["items"][1]["piece"] == west and r3["pins"] == ["@2", "@3"]
              and un["pins"] == ["@3"] and again["pins"] == ["@3", "@2"] and code_t == "STUDIO-REFERENCE" and code_p == "STUDIO-PINS"
              and g.tag_of[west] == "@2" and g.refs()["pins"] == ["@3", "@2", "@4"])
        sw = g.select(west)
        back = g.select(north)
        g.pin(west)
        row("tags: E selects, R pins and unpins, a part names its object, the same object keeps its tag", ok and sw["target"] == "@2" and "@2" not in sw["pins"]
            and back["target"] == "@1" and [i["status"] for i in g.refs()["items"]] == ["ok"] * len(g.refs()["items"]),
            "@1 the north canopy; @2 the west one, pinned through its rib; unpinned and pinned again, still @2; the target refused as a pin; "
            "a fifth pin refused; @2 selected as the target and back")
        for t in ("@4",):
            if t in g.pins:
                g.unpin(t)

        # the request: geometry and relations against the scene's own boxes
        rid = g.ask("match @2", None, {"x": 44.0, "y": 1.62, "z": 30.0, "yaw_deg": 0.0, "pitch_deg": 20.0})
        r = wait(g, rid)
        rec = os.path.join(tmp, "art", "build", "studio", brief, rid)
        req = json.loads(open(os.path.join(rec, "request.json"), "rb").read())
        S = json.loads(live.slot(0)["scene_bytes"])

        def boxes(i):
            return [v["box"] for v in S["visuals"] if v["id"] == i or v["id"].startswith(i + ":")]
        bn, bw = boxes(north), boxes(west)
        union = lambda B: [min(b[0] for b in B), min(b[1] for b in B), min(b[2] for b in B), max(b[3] for b in B), max(b[4] for b in B), max(b[5] for b in B)]
        least = min(sum(max(0.0, q[k] - p[k + 3], p[k] - q[k + 3]) ** 2 for k in range(3)) ** 0.5 for p in bn for q in bw)
        by = {x["tag"]: x for x in req["references"]}
        rel = [x for x in req["relations"] if x["from"] == "@1" and x["to"] == "@2"][0]
        walls = [w for w in S["collision"] if w["kind"] == "wall"]
        nw = by["@1"]["nearest_wall"]
        wb = [w["box"] for w in walls if w["id"] == nw["wall"]][0]
        plan = min(((max(0.0, wb[0] - p[3], p[0] - wb[3])) ** 2 + (max(0.0, wb[2] - p[5], p[2] - wb[5])) ** 2) ** 0.5 for p in bn)
        geo = (req["version"] == "1" and req["target"]["tag"] == "@1" and by["@1"]["geometry"]["bounds_m"] == [round(x, 3) for x in union(bn)]
               and by["@2"]["geometry"]["bounds_m"] == [round(x, 3) for x in union(bw)] and by["@2"]["geometry"]["parts"].get("rib", 0) >= 2
               and by["@2"]["geometry"]["parts"].get("light-edge", 0) >= 1 and req["coordinates"].startswith(S["units"])
               and abs(rel["measured"]["gap_m"] - round(least, 3)) < 1e-9 and rel["measured"]["touching"] is (least == 0.0)
               and abs(nw["plan_gap_m"] - round(plan, 3)) < 1e-9 and nw["basis"].startswith("measured") and rel["basis"].startswith("measured")
               and req["mentions"] == ["@2"] and by["@2"]["mentioned"] and not by["@3"]["mentioned"] and by["@1"]["statement_makes"] == 1)
        row("the request's geometry and relations are the scene's own boxes", geo,
            "@1 bounds %s, @2 bounds %s (%d boxes, its ribs and fixtures); their gap %.3f m, recomputed here; @1's nearest wall %s, %.3f m in plan, recomputed here"
            % (by["@1"]["geometry"]["bounds_m"], by["@2"]["geometry"]["bounds_m"], by["@2"]["geometry"]["boxes"], least, nw["wall"], plan))
        neon = [i for i in sorted(have) if i.startswith("neon:")][0]
        g.pin(neon)
        n_tag = g.tag_of[neon]
        out_ = studio_refs.objects(S)
        rel_n = studio_refs.relation(out_[neon], out_[north], n_tag, "@1")
        row("facing is inferred, and said to be", "inferred" in rel_n and rel_n["inferred"]["basis"].startswith("inferred") and "facing" not in json.dumps(rel_n["measured"])
            and "faces" in studio_refs.geometry(out_[neon]) and studio_refs.geometry(out_[neon])["faces"]["basis"].startswith("measured"),
            "%s's lights point %s (measured, as the scene records them); whether it faces @1 is a half-space test, marked inferred" % (n_tag, studio_refs.geometry(out_[neon])["faces"]["directions"]))
        g.pin(neon)

        # what a model is told: the tags, their geometry and their relations, as director_prompt.py renders the request
        sys.path.insert(0, os.path.join(REPO, "art", "providers"))
        import director_prompt
        txt = director_prompt.user_text(req)
        b1 = ", ".join("%g" % v for v in by["@1"]["geometry"]["bounds_m"])
        row("what a model is told: each tag, what made it, its bounds, and how the tags stand", "@1, the target: canopy plaza/canopy/19,10-28,11" in txt
            and "@2, pinned as a reference: canopy plaza/canopy/19,12-20,19" in txt and "(mentioned in the prompt)" in txt and "[%s] m" % b1 in txt
            and "line 61 of the brief" in txt and "How the tagged objects stand to one another:" in txt and "@1 to @2: gap %s m" % rel["measured"]["gap_m"] in txt
            and "nearest wall: play/wall/" in txt and "A tag means that object and no other" in director_prompt.SYSTEM,
            "the target and the pins with their lines, bounds [%s] m, the relations and the nearest walls; the system text's rule for tags" % b1)

        # a candidate's account of what it changed
        c = r["candidates"][0] if r["candidates"] else {}
        t = c.get("touches") or {}
        intent = json.loads(open(os.path.join(rec, "A.intent"), "rb").read())
        row("match @2: @1 takes @2's height and options, @2 and everything else untouched, and the candidate says so",
            r["state"] == "done" and c.get("verdict") == "CLEAN" and intent["revision"] == ["= canopy plaza concrete_slab 7.6 19,10 28,11 deep 1.2 ribs 2 edgelit 255,178,112 60"]
            and t.get("tags") == {"@1": "changed", "@2": "unchanged", "@3": "unchanged"} and t.get("others_count") == 0,
            "%s; touches %s, %d other objects" % (intent["revision"][0], t.get("tags"), t.get("others_count", -1)))
        g.cfg = studio.load_config(_cfg_file(tmp, "all", [sys.executable, os.path.join(tmp, "all_canopies.py")]))
        g.unpin("@3")
        rid = g.ask("make @1 a metre deep", None, None)
        r = wait(g, rid)
        t = (r["candidates"][0].get("touches") if r["candidates"] else None) or {}
        row("a candidate that changes objects nobody tagged is shown so", r["state"] == "done" and t.get("tags") == {"@1": "changed", "@2": "changed"}
            and t.get("others") == [south] and t.get("others_count") == 1 and t.get("added") == [],
            "every canopy 1 m deep: @1 changed, @2 changed, and 1 other object (%s)" % ", ".join(t.get("others", [])))
        g.cfg = studio.load_config(_cfg_file(tmp, "corners", [sys.executable, os.path.join(tmp, "corners.py")]))
        rid = g.ask("make @1 one cell narrower", None, None)
        r = wait(g, rid)
        t = (r["candidates"][0].get("touches") if r["candidates"] else None) or {}
        row("a candidate that moves the target's corners: the target changed, a new object made, no other touched", r["state"] == "done"
            and t.get("tags", {}).get("@1") == "changed" and t.get("others_count") == 0 and t.get("added") == ["canopy:19,10-27,11"],
            "touches %s; others %d; new %s" % (t.get("tags"), t.get("others_count", -1), t.get("added")))
        g.cfg = studio.load_config(_cfg_file(tmp, "material", [sys.executable, os.path.join(tmp, "material.py")]))
        rid = g.ask("a lighter concrete for @1", None, None)
        r = wait(g, rid)
        t = (r["candidates"][0].get("touches") if r["candidates"] else None) or {}
        row("a material changed: every object of it touched, tagged or not", r["state"] == "done" and t.get("tags") == {"@1": "changed", "@2": "changed"}
            and t.get("others") == [south] and t.get("materials") == ["concrete_slab"],
            "concrete_slab lightened: touches %s, others %s, materials %s" % (t.get("tags"), t.get("others"), t.get("materials")))
        # the gap is the boxes', not their bounds': an L of two boxes, 4 m from a box its bounds enclose
        Ls = {"visuals": [{"id": "x:0", "by": "a", "region": "r", "material": "m", "box": [0, 0, 0, 1, 1, 1]},
                          {"id": "y:0", "by": "b", "region": "r", "material": "m", "box": [5, 0, 0, 6, 1, 1]},
                          {"id": "y:0:part1", "by": "b", "region": "r", "material": "m", "box": [0, 5, 0, 1, 6, 1]}], "lights": []}
        OL = studio_refs.objects(Ls)
        gL = studio_refs.relation(OL["x:0"], OL["y:0"], "@a", "@b")["measured"]["gap_m"]
        row("a gap is measured between the boxes, not their bounds", gL == 4.0 and studio_refs.geometry(OL["y:0"])["bounds_m"] == [0, 0, 0, 6, 6, 1],
            "an L of two boxes whose bounds enclose a third box, 4 m from it: gap %s m" % gL)
        g.cfg = studio.load_config(os.path.join(REPO, "art", "providers", "scripted.json"))

        # a prompt naming a tag that is not the target or a pin
        n_log = len(open(os.path.join(tmp, "art", "build", "studio", brief, "requests.jsonl"), "rb").read().splitlines())
        code, detail = refused(g.ask, "make @1 like @9", None, None)
        code3, detail3 = refused(g.ask, "make @1 like @3", None, None)
        row("a prompt naming a tag that is not the target or a pin: refused, nothing asked", code == "STUDIO-REFERENCE" and code3 == "STUDIO-REFERENCE"
            and "@9" in detail and "@3" in detail3 and len(open(os.path.join(tmp, "art", "build", "studio", brief, "requests.jsonl"), "rb").read().splitlines()) == n_log,
            detail[:110])

        # an object changed since it was pinned: said, and bound again by pinning it again
        sha0 = live.slot(0)["sha"]
        open(art, "w", encoding="utf-8").write(text.replace(west0 + " deep 1.2 ", west0 + " deep 1.6 "))
        until(lambda: live.slot(0)["sha"] != sha0)
        st = {i["tag"]: i["status"] for i in g.refs()["items"]}
        g.cfg = studio.load_config(os.path.join(REPO, "art", "providers", "scripted.json"))
        rid = g.ask("match @2", None, None)
        wait(g, rid)
        req = json.loads(open(os.path.join(tmp, "art", "build", "studio", brief, rid, "request.json"), "rb").read())
        ch = {x["tag"]: x["bound"]["changed_since"] for x in req["references"]}
        g.pin(west)
        g.pin(west)
        st2 = {i["tag"]: i["status"] for i in g.refs()["items"]}
        row("an object changed since it was pinned: said, in the page and in the request; pinned again, bound again", st.get("@2") == "changed" and st.get("@1") == "ok"
            and ch == {"@1": False, "@2": True} and st2.get("@2") == "ok" and g.tag_of[west] == "@2",
            "the west canopy 1.2 -> 1.6 m deep: @2 %s, the request's @2 changed_since %s; pinned again: %s, still @2" % (st.get("@2"), ch.get("@2"), st2.get("@2")))

        # an object gone: its tag stays its own, and the request is refused until it is unpinned
        g.pin(south)
        t_s = g.tag_of[south]
        sha1 = live.slot(0)["sha"]
        cur = open(art, encoding="utf-8").read()
        open(art, "w", encoding="utf-8").write(cur.replace("canopy plaza concrete_slab 7.0 19,20 28,21", "canopy plaza concrete_slab 7.0 19,20 27,21"))
        until(lambda: live.slot(0)["sha"] != sha1)
        st = {i["tag"]: i["status"] for i in g.refs()["items"]}
        code, detail = refused(g.ask, "match @2", None, None)
        newer = "canopy:19,20-27,21"
        g.pin(newer)
        t_new = g.tag_of[newer]
        g.unpin(t_s)
        g.unpin(t_new)
        rid = g.ask("match @2", None, None)
        r = wait(g, rid)
        row("an object gone: its tag never moves to another; the request refused until it is unpinned", st.get(t_s) == "gone" and code == "STUDIO-REFERENCE"
            and t_s in detail and t_new not in (t_s, "@1", "@2") and g.tags[t_s]["piece"] == south and r["state"] == "done",
            "the south canopy's corners moved: %s gone (%s); the new canopy pinned as %s; %s unpinned, asked again: %s" % (t_s, detail[:60], t_new, t_s, r["state"]))

        # the page's own requests
        def post(path, body, token):
            q = urllib.request.Request("http://127.0.0.1:%d%s" % (srv.server_address[1], path), data=json.dumps(body).encode("utf-8"), method="POST",
                                       headers={"Content-Type": "application/json", "X-Studio-Token": token})
            try:
                with urllib.request.urlopen(q, timeout=60) as h:
                    return h.status, json.loads(h.read())
            except urllib.error.HTTPError as e:
                return e.code, {}
        a, _ = post("/studio/pin", {"piece": south.replace("28", "27")}, "not-the-token")
        b, body = post("/studio/select", {"piece": north}, live.token)
        c_, body2 = post("/studio/pin", {"piece": "nothing:1,1"}, live.token)
        with urllib.request.urlopen("http://127.0.0.1:%d/live" % srv.server_address[1], timeout=30) as h:
            st = json.loads(h.read())["studio"]["refs"]
        row("select and pin from the page: its token, the refs in /live", a == 403 and b == 200 and body["refs"]["target"] == "@1" and c_ == 409
            and st["target"] == "@1" and all(set(i) >= {"tag", "role", "piece", "address", "status"} for i in st["items"]),
            "no token %d; select %d; an unknown piece %d; /live lists %s" % (a, b, c_, ", ".join("%s %s %s" % (i["tag"], i["role"], i["status"]) for i in st["items"])))
    except (studio.StudioError, KeyError, IndexError, TypeError, ValueError, OSError) as e:
        row("the references' test ran to its end", False, "%s: %s" % (type(e).__name__, str(e)[:160]))
    finally:
        ROOT = saved_root
        if live:
            live.stopping = True
        if srv:
            srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)


def _cfg_file(tmp, name, argv, timeout=30, size=65536):
    path = os.path.join(tmp, name + ".json")
    open(path, "w").write(json.dumps({"provider": "cli", "argv": argv, "model": name, "timeout_s": timeout, "max_output_bytes": size}))
    return path


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
