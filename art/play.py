# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/play.py — the native plaza: a brief's dressed scene, played in the browser, without Unreal.
#
#   python art/play.py BRIEF [--port N] [--no-browser] [--art PATH] [--check]
#
# By the owner's ruling (2026-10-11): an art-owned launcher, with WebGL 2, and graybox/serve.py and the graybox's
# boundary left as they are.
#
# At launch it compiles the brief through art/dress.py into the scene, the runtime's artifact, and holds the scene to
# the art checks (art/check.py: the scene's collision is C, nothing dressed where a player can be, the art carries no
# collision): a scene that fails one is not served. Then it serves, on 127.0.0.1 only, exactly these and nothing else:
#
#   /play.html, /play.js, /scene_render.js    art/web/, the page and the renderer
#   /sim.js                                   graybox/web/sim.js, the graybox's simulation, read and served unchanged
#   /scene/BRIEF.json                         the compiled scene, from memory
#   /map/MAP.json                             the brief's map, converted by graybox/level.py, as graybox/serve.py serves it
#
# The browser gets no other path into art/ or graybox/. The simulation moves the player against the map's C; the
# renderer draws the scene and writes no state. --art PATH compiles another art file for the same brief (a candidate's
# text, read once at launch). --check compiles and checks and stops before serving. Nothing is written to disk.
# Standard library only.

import http.server
import importlib.util
import json
import os
import re
import sys
import threading
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
    res = check.verify(out, None, D=check.gcheck.source_rows(out["W"]))
    bad = [(c, d) for c, ok, d in res if not ok and c != "the lineage binds every input"]
    if bad:
        raise SystemExit("PLAY: the scene is not served; it fails the art checks:\n" + "\n".join("  FAIL %s — %s" % b for b in bad))
    scene = out["scene"]
    m = level.convert(scene["map"])
    return out, level.canon(m), m["manifest"]


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    vals = {opt("--port"), opt("--art")}
    pos = [a for a in args if a not in vals]
    if not pos:
        print("usage: python art/play.py BRIEF [--port N] [--no-browser] [--art PATH] [--check]", file=sys.stderr)
        return 2
    brief = pos[0]
    try:
        out, map_bytes, manifest = compile_scene(brief, opt("--art"))
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 1
    scene, scene_bytes, sha = out["scene"], out["scene_bytes"], out["lineage"]["scene_sha256"]
    c = out["lineage"]["counts"]
    head = "PLAY  %s  scene %s  (%d play boxes, %d dressing pieces, %d lights)  map %s  canonical %s  collision %s" % (
        brief, sha[:12], c["collision"], c["visuals"], c["lights"], scene["map"], manifest["canonical_sha256"][:12], manifest["collision_sha256"][:12])
    if "--check" in argv:
        print(head)
        print("the art checks passed; not served (--check)")
        return 0
    page = open(os.path.join(WEB, "play.html"), encoding="utf-8").read().replace("%BRIEF%", brief).replace("%SHA%", sha)

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
            path = self.path.split("?", 1)[0]
            if path == "/":
                self.send_response(302)
                self.send_header("Location", "/play.html")
                self.end_headers()
                return
            if path == "/play.html":
                return self.send(200, page.encode("utf-8"), "text/html; charset=utf-8")
            if path in FILES:
                f, ctype = FILES[path]
                with open(f, "rb") as fh:
                    return self.send(200, fh.read(), ctype)
            if path == "/scene/%s.json" % brief:
                return self.send(200, scene_bytes, "application/json")
            if path == "/map/%s.json" % scene["map"]:
                return self.send(200, map_bytes, "application/json")
            return self.send(404, b"not found", "text/plain")

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", int(opt("--port", "0"))), Handler)
    url = "http://127.0.0.1:%d/" % srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(head)
    print("the art checks passed; movement and collision are the graybox simulation's, against C")
    print("open %s  — Ctrl+C here to stop" % url)
    if "--no-browser" not in argv:
        webbrowser.open(url)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    srv.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
