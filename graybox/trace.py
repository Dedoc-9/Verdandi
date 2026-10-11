# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# graybox/trace.py — the trace experiment: where two JavaScript engines part, and why. A diagnostic, outside the
# self-test and outside the gate; nothing passes or fails on what it finds.
#
#   python graybox/trace.py run [MAP] [--port N] [--no-browser] [--timeout SECONDS]
#   python graybox/trace.py compare A.json B.json
#   python graybox/trace.py selftest A.json
#
# `run` serves a page (web/trace.html) that, in a worker, records and plays the self-test's two runs (the first route's
# recorded walk and the fight) with every call of Math.sin, Math.cos, Math.hypot and Math.atan2 logged in call order:
# the bits of each argument and of the result. Every tick's input and every tick's snapshot of the authoritative state
# go with it, and the browser's own description of itself. The trace is written to graybox/build/trace/MAP/, named by
# the engine, and again as latest.json there. It reads nothing outside graybox/ and serves only the four files it names.
#
# `compare` sets two traces side by side. For each function: its results on the arguments both runs passed (so that
# two runs which call a function with different arguments are not mistaken for a function that differs). Then the
# calls in order, and the first that differs, said to differ in an argument (the runs had parted before it) or in a
# result (the engines' functions differ). Then each run: the first tick whose input differs, and the first tick whose
# state differs, with the leaves that differ there. A state digest that matches says only what the snapshot holds.
#
# `selftest` plants differences in a copy of a trace (a function's result, a call's argument, one state leaf, one
# input) and requires `compare` to name each where it was planted, and to find nothing between a trace and itself.

import hashlib
import http.server
import json
import os
import re
import struct
import sys
import threading
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import level  # noqa: E402

WEB = os.path.join(HERE, "web")
SERVED = {"/trace.html": "text/html; charset=utf-8", "/trace.js": "text/javascript; charset=utf-8",
          "/sim.js": "text/javascript; charset=utf-8", "/sim_worker.js": "text/javascript; charset=utf-8"}
FNS = ("sin", "cos", "hypot", "atan2")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def engine_tag(rt):
    ua = (rt or {}).get("userAgent", "")
    tag = "browser"
    for pat, name in ((r"Edg/(\d+)", "edge"), (r"Firefox/(\d+)", "firefox"), (r"HeadlessChrome/(\d+)", "chrome-headless"),
                      (r"Chrome/(\d+)", "chrome"), (r"Version/(\d+)[^ ]* .*Safari", "safari")):
        m = re.search(pat, ua)
        if m:
            tag = "%s-%s" % (name, m.group(1))
            break
    osname = "windows" if "Windows" in ua else "mac" if "Mac OS X" in ua else "linux" if "Linux" in ua else "other"
    return "%s-%s" % (tag, osname)


# ------------------------------------------------------------------------------------------------ numbers
def f64(h):
    return struct.unpack(">d", bytes.fromhex(h))[0]


def ordinal(h):
    u = int(h, 16)
    return u if u < 1 << 63 else -(u - (1 << 63))


def ulps(a, b):
    return abs(ordinal(a) - ordinal(b))


def show(h):
    return "0x%s (%r)" % (h, f64(h))


def leaves(v, path=""):
    if isinstance(v, dict):
        for k in sorted(v):
            yield from leaves(v[k], path + ("." if path else "") + k)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from leaves(x, "%s[%d]" % (path, i))
    else:
        yield path, v


def leaf_text(v):
    if isinstance(v, str) and v.startswith("f") and len(v) == 17:
        return repr(f64(v[1:]))
    return json.dumps(v[1:] if isinstance(v, str) else v)


# ------------------------------------------------------------------------------------------------ comparison
def results_by_argument(calls, fn):
    m = {}
    for _phase, _tick, f, args, res in calls:
        if f == fn:
            m.setdefault(args, set()).add(res)
    return m


def compare(A, B):
    out = {"functions": {}, "order": None, "runs": {}, "impure": []}
    for fn in FNS:
        ma, mb = results_by_argument(A["calls"], fn), results_by_argument(B["calls"], fn)
        for side, m in (("A", ma), ("B", mb)):
            for args, rs in m.items():
                if len(rs) > 1:
                    out["impure"].append((side, fn, args, sorted(rs)))
        common = sorted(set(ma) & set(mb))
        diff = [(args, sorted(ma[args])[0], sorted(mb[args])[0]) for args in common if ma[args] != mb[args]]
        out["functions"][fn] = {"A": len(ma), "B": len(mb), "common": len(common), "diff": diff,
                                "calls": (sum(1 for c in A["calls"] if c[2] == fn), sum(1 for c in B["calls"] if c[2] == fn))}
    ca, cb = A["calls"], B["calls"]
    for i in range(min(len(ca), len(cb))):
        if ca[i] != cb[i]:
            a, b = ca[i], cb[i]
            if a[:4] == b[:4]:
                kind = "result"
            elif a[0] == b[0] and a[2] == b[2]:
                kind = "argument"
            else:
                kind = "sequence"
            out["order"] = {"index": i, "kind": kind, "A": a, "B": b}
            break
    else:
        if len(ca) != len(cb):
            out["order"] = {"index": min(len(ca), len(cb)), "kind": "length", "A": len(ca), "B": len(cb)}
    rb = {r["name"]: r for r in B["runs"]}
    for ra in A["runs"]:
        r2 = rb.get(ra["name"])
        if r2 is None:
            out["runs"][ra["name"]] = {"missing": True}
            continue
        res = {"ticks": (len(ra["snaps"]), len(r2["snaps"])), "start": ra["start"] == r2["start"], "input": None, "state": None}
        for n, (x, y) in enumerate(zip(ra["inputs"], r2["inputs"])):
            if x != y:
                res["input"] = {"tick": n + 1, "A": x, "B": y}
                break
        for n, (x, y) in enumerate(zip(ra["snaps"], r2["snaps"])):
            if x != y:
                la, lb = dict(leaves(json.loads(x))), dict(leaves(json.loads(y)))
                keys = sorted(set(la) | set(lb))
                diffs = [(k, la.get(k), lb.get(k)) for k in keys if la.get(k) != lb.get(k)]
                res["state"] = {"tick": n + 1, "leaves": diffs}
                break
        out["runs"][ra["name"]] = res
    return out


def print_compare(A, B, r):
    print("TRACE COMPARE  map %s" % A.get("map"))
    for side, T in (("A", A), ("B", B)):
        print("%s  %s  %s" % (side, engine_tag(T.get("runtime")), (T.get("runtime") or {}).get("userAgent", "?")))
    for side, fn, args, rs in r["impure"]:
        print("NOTE  in %s, Math.%s gave %d results for one argument (%s)" % (side, fn, len(rs), args))
    for fn in FNS:
        f = r["functions"][fn]
        head = "Math.%-6s %d and %d calls; %d and %d distinct arguments, %d in common: " % (fn, f["calls"][0], f["calls"][1], f["A"], f["B"], f["common"])
        if not f["diff"]:
            print(head + "the same result on every one")
        else:
            print(head + "DIFFERENT results on %d" % len(f["diff"]))
            for args, ra, rb in f["diff"][:3]:
                print("    Math.%s(%s): A %s, B %s, %d ulp apart" % (fn, ", ".join(show(a) for a in args.split(",")), show(ra), show(rb), ulps(ra, rb)))
    o = r["order"]
    if o is None:
        print("calls in order: the same %d calls, argument for argument and result for result" % len(A["calls"]))
    elif o["kind"] == "length":
        print("calls in order: the same up to call %d; then one trace ends (%d and %d calls)" % (o["index"], o["A"], o["B"]))
    else:
        a, b = o["A"], o["B"]
        where = "call %d (%s, tick %s)" % (o["index"], a[0], a[1])
        if o["kind"] == "result":
            print("calls in order: the first difference is at %s, in a RESULT: Math.%s(%s) returned %s in A and %s in B" % (
                where, a[2], ", ".join(show(x) for x in a[3].split(",")), show(a[4]), show(b[4])))
        elif o["kind"] == "argument":
            print("calls in order: the first difference is at %s, in an ARGUMENT: Math.%s(%s) in A, Math.%s(%s) in B; the runs had parted before this call" % (
                where, a[2], a[3], b[2], b[3]))
        else:
            print("calls in order: the first difference is at %s: %s in A, %s in B" % (where, a[:3], b[:3]))
    for name, res in r["runs"].items():
        if res.get("missing"):
            print("run %s: not in B" % name)
            continue
        print("run %s: %d and %d ticks; the start %s" % (name, res["ticks"][0], res["ticks"][1], "the same" if res["start"] else "DIFFERENT"))
        print("    inputs: " + ("the same at every tick" if not res["input"] else "first different at tick %d: %s in A, %s in B" % (res["input"]["tick"], res["input"]["A"], res["input"]["B"])))
        if not res["state"]:
            print("    states: the same at every tick (as far as the snapshot holds the state)")
        else:
            ls = res["state"]["leaves"]
            print("    states: first different at tick %d, in %d leaf(s): %s" % (res["state"]["tick"], len(ls), "; ".join(
                "%s A %s B %s%s" % (k, leaf_text(a), leaf_text(b), (", %d ulp" % ulps(a[1:], b[1:])) if isinstance(a, str) and isinstance(b, str) and a[:1] == "f" == b[:1] else "")
                for k, a, b in ls[:6])))
    fns = [fn for fn in FNS if r["functions"][fn]["diff"]]
    parted = ["%s at tick %d" % (n, x["state"]["tick"]) for n, x in r["runs"].items() if not x.get("missing") and x["state"]]
    print("SUMMARY  functions with different results on common arguments: %s; states parted: %s" % (
        ", ".join("Math." + f for f in fns) or "none", "; ".join(parted) or "none"))


# ------------------------------------------------------------------------------------------------ the file
def load(path):
    with open(path, encoding="utf-8") as fh:
        T = json.load(fh)
    if T.get("format") != "VERDANDI-TRACE" or T.get("version") != "0":
        raise SystemExit("TRACE: %s is not a VERDANDI-TRACE 0 file" % path)
    if T.get("error"):
        raise SystemExit("TRACE: %s records a failed trace: %s" % (path, T["error"]))
    return T


def summary(T, path):
    print("TRACE  map %s  engine %s" % (T["map"], engine_tag(T["runtime"])))
    print("runtime  %s" % T["runtime"].get("userAgent"))
    if T["runtime"].get("brands"):
        print("brands   %s  (%s)" % (", ".join(T["runtime"]["brands"]), T["runtime"].get("platform")))
    for fn in FNS:
        m = results_by_argument(T["calls"], fn)
        pairs = "\n".join("%s>%s" % (a, ",".join(sorted(rs))) for a, rs in sorted(m.items()))
        print("Math.%-6s %6d calls, %6d distinct arguments, digest of its (argument, result) pairs %s" % (
            fn, sum(1 for c in T["calls"] if c[2] == fn), len(m), sha(pairs)[:16]))
    for run in T["runs"]:
        print("run %-10s %5d ticks; inputs %s; every tick's state %s; the last state %s" % (
            run["name"], len(run["snaps"]), sha("\n".join(run["inputs"]))[:16], sha("\n".join(run["snaps"]))[:16], sha(run["snaps"][-1])[:16]))
    print("written %s" % os.path.relpath(path))
    print("compare it with another trace: python graybox/trace.py compare %s OTHER.json" % os.path.relpath(path))


# ------------------------------------------------------------------------------------------------ run
def cmd_run(argv):
    args = [a for a in argv if not a.startswith("--")]
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    name = args[0] if args and args[0] not in (opt("--port"), opt("--timeout")) else "tactical"
    if not re.fullmatch(r"[a-z0-9_-]+", name):
        print("TRACE: a map's name is lower-case letters, digits, - and _", file=sys.stderr)
        return 2
    try:
        m = level.convert(name)
    except level.MapError as e:
        print("GRAYBOX-MAP: %s" % e, file=sys.stderr)
        return 2
    done, got = threading.Event(), {}

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
                self.send_header("Location", "/trace.html?map=%s" % name)
                self.end_headers()
                return
            if path == "/map/%s.json" % name:
                return self.send(200, level.canon(m), "application/json")
            if path in SERVED:
                with open(os.path.join(WEB, path[1:]), "rb") as fh:
                    return self.send(200, fh.read(), SERVED[path])
            return self.send(404, b"not found", "text/plain")

        def do_POST(self):
            if self.path != "/trace":
                return self.send(404, b"not found", "text/plain")
            n = int(self.headers.get("Content-Length", "0"))
            got["trace"] = json.loads(self.rfile.read(n).decode("utf-8"))
            self.send(200, b"ok", "text/plain")
            done.set()

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", int(opt("--port", "0"))), Handler)
    url = "http://127.0.0.1:%d/" % srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print("TRACE  map %s  open %s" % (name, url))
    if "--no-browser" not in argv:
        webbrowser.open(url)
    ok = done.wait(float(opt("--timeout", "180")))
    srv.shutdown()
    if not ok:
        print("TRACE: no trace came back from the page in time", file=sys.stderr)
        return 2
    T = got["trace"]
    if T.get("error"):
        print("TRACE: the page failed: %s" % T["error"], file=sys.stderr)
        return 1
    outdir = os.path.join(HERE, "build", "trace", name)
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, engine_tag(T["runtime"]) + ".json")
    for p in (path, os.path.join(outdir, "latest.json")):   # latest.json: the last trace of this map, whatever the engine
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(T, fh, separators=(",", ":"), sort_keys=True)
            fh.write("\n")
    summary(T, path)
    return 0


# ------------------------------------------------------------------------------------------------ selftest
def flip(h):
    return h[:-1] + "%x" % (int(h[-1], 16) ^ 1)


def cmd_selftest(path):
    import copy
    A = load(path)
    checks = []

    def found(label, ok, detail):
        checks.append((label, ok, detail))

    r = compare(A, copy.deepcopy(A))
    clean = (r["order"] is None and not any(f["diff"] for f in r["functions"].values())
             and all(not x["input"] and not x["state"] for x in r["runs"].values()))
    found("a trace against itself: nothing found", clean, "")
    play = [i for i, c in enumerate(A["calls"]) if c[0].startswith("play") and c[2] == "cos"]
    if not play:
        found("the trace has calls of Math.cos in play", False, "")
    else:
        k = play[len(play) // 2]
        fn, args, res = A["calls"][k][2], A["calls"][k][3], A["calls"][k][4]
        B = copy.deepcopy(A)
        for c in B["calls"]:
            if c[2] == fn and c[3] == args:
                c[4] = flip(c[4])
        r = compare(A, B)
        d = r["functions"][fn]["diff"]
        first = min(i for i, c in enumerate(A["calls"]) if c[2] == fn and c[3] == args)
        found("plant: Math.cos's result changed in its last bit at one argument", len(d) == 1 and d[0][0] == args and r["order"]["kind"] == "result" and r["order"]["index"] == first,
              "named Math.cos(%s), first at call %d, as a result" % (args, first))
        B = copy.deepcopy(A)
        B["calls"][k][3] = ",".join(flip(a) for a in args.split(","))
        r = compare(A, B)
        found("plant: one call's argument changed", r["order"]["kind"] == "argument" and r["order"]["index"] == k and not r["functions"][fn]["diff"],
              "call %d named as an argument, no function blamed" % k)
    walk = A["runs"][0]
    if len(walk["snaps"]) < 600:
        found("the first run is long enough to plant in", False, "")
    else:
        B = copy.deepcopy(A)
        s = json.loads(B["runs"][0]["snaps"][499])
        s["x"] = "f" + flip(s["x"][1:])
        B["runs"][0]["snaps"][499] = json.dumps(s, separators=(",", ":"), sort_keys=True)
        r = compare(A, B)
        st = r["runs"][walk["name"]]["state"]
        found("plant: one state leaf changed at tick 500", st is not None and st["tick"] == 500 and [x[0] for x in st["leaves"]] == ["x"], "tick 500, leaf x")
        B = copy.deepcopy(A)
        B["runs"][0]["inputs"][299] = B["runs"][0]["inputs"][299] + " "
        r = compare(A, B)
        inp = r["runs"][walk["name"]]["input"]
        found("plant: one input changed at tick 300", inp is not None and inp["tick"] == 300, "tick 300")
    failed = 0
    for label, ok, detail in checks:
        print("%s %s%s" % ("PASS" if ok else "FAIL", label, (" — " + detail) if detail else ""))
        failed += 0 if ok else 1
    print("TRACE SELFTEST %s" % ("PASSED" if not failed else "FAILED (%d)" % failed))
    return 0 if not failed else 1


def main(argv):
    if not argv or argv[0] not in ("run", "compare", "selftest"):
        print("usage: python graybox/trace.py run [MAP] | compare A.json B.json | selftest A.json", file=sys.stderr)
        return 2
    if argv[0] == "run":
        return cmd_run(argv[1:])
    if argv[0] == "compare":
        if len(argv) != 3:
            print("usage: python graybox/trace.py compare A.json B.json", file=sys.stderr)
            return 2
        A, B = load(argv[1]), load(argv[2])
        print_compare(A, B, compare(A, B))
        return 0
    if len(argv) != 2:
        print("usage: python graybox/trace.py selftest A.json", file=sys.stderr)
        return 2
    return cmd_selftest(argv[1])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
