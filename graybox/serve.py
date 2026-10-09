# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# graybox/serve.py — launch FPS-GRAYBOX-0 on this machine.
#
#   python graybox/serve.py [MAP] [--port N] [--no-browser] [--renderer flat]
#                           [--selftest | --bench [--samples N] [--batch K]] [--timeout SECONDS]
#
# Converts the map (maps/MAP.gbx, default `tactical`) with level.py, serves the runtime in graybox/web/ and the
# converted map on 127.0.0.1, and opens it in the default browser. --renderer flat plays with the graybox's first
# renderer instead of FPS-VISUAL-0's. With --selftest the page runs the runtime's conformance checks instead of the
# game and sends the results back here; this prints them and ends 0 if every one passed, 1 if one failed, 2 if none
# came back in time. With --bench the page draws the same poses with both renderers, times them in that browser and
# sends back the timings and a screenshot of each; this writes them to graybox/build/bench/MAP/ and prints the
# timings. Every response asks the browser to isolate the page from other origins (it loads nothing from any), which
# also lets a browser give the page its finer clock. Standard library only; nothing is written to disk but by --bench,
# and only there.

import base64
import http.server
import json
import math
import os
import statistics
import sys
import threading
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import level  # noqa: E402

WEB = os.path.join(HERE, "web")
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8"}


def main(argv) -> int:
    args = [a for a in argv if not a.startswith("--")]
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    name = args[0] if args and args[0] not in (opt("--port"), opt("--timeout"), opt("--renderer"), opt("--samples"), opt("--batch")) else "tactical"
    port = int(opt("--port", "0"))
    selftest = "--selftest" in argv
    bench = "--bench" in argv and not selftest
    flat = opt("--renderer") == "flat"
    try:
        maps = {n: level.convert(n) for n in level.names()}
    except level.MapError as e:
        print("GRAYBOX-MAP: %s" % e, file=sys.stderr)
        return 2
    if name not in maps:
        print("GRAYBOX-MAP: no map %r; the maps are %s" % (name, ", ".join(sorted(maps))), file=sys.stderr)
        return 2
    done = threading.Event()
    got = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, code, body: bytes, ctype):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Cross-Origin-Opener-Policy", "same-origin")
            self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/":
                self.send_response(302)
                mode = "&selftest=1" if selftest else "&bench=1&samples=%d&batch=%d" % (int(opt("--samples", "20")), int(opt("--batch", "10"))) if bench else "&renderer=flat" if flat else ""
                self.send_header("Location", "/index.html?map=%s%s" % (name, mode))
                self.end_headers()
                return
            if path.startswith("/map/") and path.endswith(".json"):
                m = maps.get(path[5:-5])
                if m is None:
                    return self.send(404, b"no such map", "text/plain")
                return self.send(200, level.canon(m), "application/json")
            f = os.path.normpath(os.path.join(WEB, path.lstrip("/")))
            if os.path.dirname(f) != WEB or not os.path.isfile(f):
                return self.send(404, b"not found", "text/plain")
            with open(f, "rb") as fh:
                return self.send(200, fh.read(), TYPES.get(os.path.splitext(f)[1], "application/octet-stream"))

        def do_POST(self):
            if self.path != ("/bench" if bench else "/selftest"):
                return self.send(404, b"not found", "text/plain")
            n = int(self.headers.get("Content-Length", "0"))
            got["result"] = json.loads(self.rfile.read(n).decode("utf-8"))
            self.send(200, b"ok", "text/plain")
            done.set()

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = "http://127.0.0.1:%d/" % srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    m = maps[name]["manifest"]
    print("FPS-GRAYBOX-0  map %s  canonical %s  collision %s" % (name, m["canonical_sha256"][:12], m["collision_sha256"][:12]))
    print("open %s%s" % (url, "  (the self-test)" if selftest else "  (the bench)" if bench else "  — Ctrl+C here to stop"))
    if "--no-browser" not in argv:
        webbrowser.open(url)
    if not selftest and not bench:
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
        srv.shutdown()
        return 0
    if not done.wait(float(opt("--timeout", "900" if bench else "120"))):
        print("GRAYBOX %s: no result came back from the page in time" % ("BENCH" if bench else "SELFTEST"), file=sys.stderr)
        srv.shutdown()
        return 2
    srv.shutdown()
    r = got["result"]
    if bench:
        return report_bench(r)
    for x in r.get("results", []):
        print("%s %s — %s" % ("PASS" if x["ok"] else "FAIL", x["name"], x["detail"]))
    print("GRAYBOX SELFTEST %s  %d / %d  (map %s)" % ("PASSED" if r.get("ok") else "FAILED", sum(1 for x in r.get("results", []) if x["ok"]),
                                                       len(r.get("results", [])), r.get("map")))
    return 0 if r.get("ok") else 1


def report_bench(r) -> int:
    if r.get("error"):
        print("GRAYBOX BENCH: the page failed: %s" % r["error"], file=sys.stderr)
        return 1
    out = os.path.join(HERE, "build", "bench", r["map"])
    os.makedirs(out, exist_ok=True)
    for key, url in sorted(r.pop("shots").items()):
        kind, pose = key.split("/", 1)
        with open(os.path.join(out, "%s-%s.png" % (pose, kind)), "wb") as fh:
            fh.write(base64.b64decode(url.split(",", 1)[1]))
    q = lambda xs, p: sorted(xs)[max(0, math.ceil(p * len(xs)) - 1)]   # the nearest rank
    lines = ["FPS-VISUAL-0 bench  map %s  %d x %d px  %d samples a pose and renderer" % (r["map"], r["size"][0], r["size"][1], r["samples"]),
             "browser %s" % r["ua"], "WebGL renderer %s" % r["gpu"],
             "each sample: %s" % r["note"],
             "the page's clock steps by %.4f ms; cross-origin isolated: %s" % (r["clock"], "yes" if r["isolated"] else "no"), "",
             "%-14s %26s %26s" % ("pose", "flat p50 / p95 / max ms", "lit p50 / p95 / max ms")]
    for row in r["poses"]:
        cell = lambda xs: "%7.3f /%7.3f /%7.3f" % (statistics.median(xs), q(xs, 0.95), max(xs))
        lines.append("%-14s %26s %26s" % (row["label"], cell(row["ms"]["flat"]), cell(row["ms"]["lit"])))
    lines.append("")
    lines.append("screenshots and timings: %s" % out)
    text = "\n".join(lines)
    with open(os.path.join(out, "bench.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text + "\n")
    with open(os.path.join(out, "bench.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(r, fh, indent=1, sort_keys=True)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
