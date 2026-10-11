# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/play.py — the native plaza: a brief's dressed scene, played in the browser, without Unreal, and changed while it
# runs.
#
#   python art/play.py BRIEF [--intent FILE]... [--art PATH] [--port N] [--no-browser] [--no-watch] [--check]
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
# scratch folder. Standard library only.

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
    got = {}

    def keep(out1, maps):
        got["map"] = level.canon(dress.world(out1["scene"]["map"], maps))

    try:
        verdict, _after, _t, out1, _out0, _text1 = D.evaluate_doc(D.Workspace(brief), it, on_candidate=keep)
    except (dress.ArtError, level.MapError, OSError) as e:
        return _slot(label, path, message="PLAY: the head cannot be compiled: %s" % e)
    extra = {"verdict": verdict["verdict"], "codes": verdict["codes"], "written_against": verdict["written_against"],
             "checked_against": verdict["checked_against"]}
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

    # ------------------------------------------------------------------ what is watched
    def inputs_of(self, k):
        """The files source k is made from: its own (the art file; an intent and the brief it is applied to), the maps,
        and the code that compiles them."""
        brief_file = os.path.join(dress.BRIEFS, self.brief + ".art")
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
            return {"format": "VERDANDI-PLAY-LIVE 0", "brief": self.brief, "version": self.version, "compiled_ms": self.compiled_ms,
                    "slots": slots, "code": self.code()}

    def slot(self, k):
        with self.lock:
            return self.served[k] if 0 <= k < len(self.served) else None


def server(live, port=0):
    page_t = open(os.path.join(WEB, "play.html"), encoding="utf-8").read()
    brief = live.brief

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
                return self.send(200, page_t.replace("%BRIEF%", brief).replace("%SHA%", s0["sha"] if s0 else "").encode("utf-8"), "text/html; charset=utf-8")
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

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def opts(argv, k):
    return [argv[i + 1] for i, a in enumerate(argv) if a == k and i + 1 < len(argv)]


def main(argv):
    if "--selftest" in argv:
        return selftest()
    one = lambda k, d=None: (opts(argv, k) or [d])[0]
    vals = set(opts(argv, "--port") + opts(argv, "--art") + opts(argv, "--intent") + opts(argv, "--only"))
    pos = [a for a in argv if not a.startswith("--") and a not in vals]
    if not pos:
        print("usage: python art/play.py BRIEF [--intent FILE]... [--art PATH] [--port N] [--no-browser] [--no-watch] [--check]\n"
              "       python art/play.py --selftest", file=sys.stderr)
        return 2
    brief, art_path, intents = pos[0], one("--art"), opts(argv, "--intent")
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


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
