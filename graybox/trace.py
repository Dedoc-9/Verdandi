# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# graybox/trace.py — the trace experiment: where two JavaScript engines part, and why. A diagnostic, outside the
# self-test and outside the gate; nothing passes or fails on what it finds.
#
#   python graybox/trace.py run [MAP] [--inputs TRACE.json] [--browser NAME] [--expect FAMILY] [--name LABEL] [--port N]
#                               [--no-browser] [--timeout SECONDS]
#   python graybox/trace.py compare A.json B.json
#   python graybox/trace.py selftest A.json
#
# `run` serves a page (web/trace.html) that, in a worker, plays the self-test's three runs (the first route's walk, the
# fight and the stress run) twice: under rules 0, the rules as first built, which call the engine's Math, and under
# rules 1, which call none of it (graybox/README.md, the simulation's contract). Every call of Math.sin, Math.cos,
# Math.hypot, Math.atan2 and Math.sqrt is logged in call order (the bits of each argument and of the result), and every
# tick's input and every tick's snapshot of the authoritative state, with the browser's own description of itself.
# Without --inputs the worker records the runs itself (the walk is a bot's, which under rules 0 calls the engine's
# functions); with --inputs TRACE.json it plays that trace's runs, the same start and the same inputs, so that two
# browsers play exactly the same sequence. --browser NAME opens the page in that browser (msedge, chrome, firefox, …)
# rather than the default one, and expects a trace from its engine; --expect FAMILY (firefox, chromium, safari) says
# the same without opening anything. A trace from another engine than the one expected is refused and not written:
# a file's name never says less than the truth about which engine made it. The trace is written to
# graybox/build/trace/MAP/ as ENGINE.json (named by the engine the page reported, -given added with --inputs), as
# FAMILY.json (firefox, chromium or safari, -given likewise), as LABEL.json with --name (a label that names a family
# must be the trace's), and again as latest.json. It reads nothing outside graybox/ (and the trace --inputs names) and serves only the
# files it names.
#
# `compare` sets two traces side by side, rules by rules. For each function: its results on the arguments both runs
# passed (so that two runs which call a function with different arguments are not mistaken for a function that
# differs). Then the calls in order, and the first that differs, said to differ in an argument (the runs had parted
# before it) or in a result (the engines' functions differ). Then each run: the first tick whose input differs, and the
# first tick whose state differs, with the fields (the state's leaves) that differ there. A state that matches is only
# as complete as the snapshot, which the self-test holds to the whole of it.
#
# `selftest` plants differences in a copy of a trace (a function's result, a call's argument, one state leaf, one
# input) and requires `compare` to name each where it was planted, and to find nothing between a trace and itself.

import hashlib
import http.server
import subprocess
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
RULES = ("0", "1")
FNS = ("sin", "cos", "hypot", "atan2", "sqrt")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


BROWSERS = {"firefox": "firefox", "msedge": "chromium", "edge": "chromium", "chrome": "chromium", "chromium": "chromium",
            "brave": "chromium", "safari": "safari"}
FAMILIES = ("firefox", "chromium", "safari")


def engine_family(rt):
    """The engine family the page's own description names: firefox (SpiderMonkey), chromium (V8: Chrome, Edge,
    Chromium) or safari (JavaScriptCore); other for anything else (node, say)."""
    ua = (rt or {}).get("userAgent", "")
    if re.search(r"Firefox/\d", ua):
        return "firefox"
    if re.search(r"(HeadlessChrome|Chrome|Chromium|Edg)/\d", ua):
        return "chromium"
    if re.search(r"Version/\d[^ ]* .*Safari/", ua):
        return "safari"
    return "other"


def engines(A, B):
    """What a comparison of A and B can show about engines: (kind, line)."""
    ta, tb = engine_tag(A.get("runtime")), engine_tag(B.get("runtime"))
    ua, ub = (A.get("runtime") or {}).get("userAgent"), (B.get("runtime") or {}).get("userAgent")
    fa, fb = engine_family(A.get("runtime")), engine_family(B.get("runtime"))
    if ua == ub:
        return "same", "NOT A CROSS-ENGINE COMPARISON: both traces come from %s (the same description of itself)" % ta
    if fa == fb:
        return "builds", "two builds of one engine family (%s): %s and %s" % (fa, ta, tb)
    return "cross", "cross-engine: %s (%s) against %s (%s)" % (fa, ta, fb, tb)


def open_in(browser, url):
    """Open url in the named browser, not the default one."""
    if sys.platform.startswith("win"):
        subprocess.Popen(["cmd", "/c", "start", "", browser, url])   # start finds msedge, chrome, firefox by their App Paths
    elif sys.platform == "darwin":
        app = {"msedge": "Microsoft Edge", "edge": "Microsoft Edge", "chrome": "Google Chrome", "chromium": "Chromium",
               "firefox": "Firefox", "safari": "Safari", "brave": "Brave Browser"}.get(browser, browser)
        subprocess.Popen(["open", "-a", app, url])
    else:
        try:
            webbrowser.get(browser).open(url)
        except webbrowser.Error:
            subprocess.Popen([browser, url])


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
    """Two traces, rules by rules (the rules both hold)."""
    return {k: compare_rules(A["rules"][k], B["rules"][k]) for k in RULES if k in A["rules"] and k in B["rules"]}


def compare_rules(A, B):
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


def print_compare(A, B, rr):
    print("TRACE COMPARE  map %s" % A.get("map"))
    for side, T in (("A", A), ("B", B)):
        print("%s  %s  %s%s" % (side, engine_tag(T.get("runtime")), (T.get("runtime") or {}).get("userAgent", "?"),
                                "  (the runs of %s)" % T["inputs_from"]["engine"] if T.get("inputs_from") else ""))
    if A.get("inputs_from") and B.get("inputs_from") and A["inputs_from"] == B["inputs_from"]:
        print("both played the same given runs (%s, inputs %s)" % (A["inputs_from"]["engine"], A["inputs_from"]["inputs"][:16]))
    kind, line = engines(A, B)
    print(line)
    for k, r in rr.items():
        print("---- rules %s%s" % (k, " (the engine's Math)" if k == "0" else " (no engine Math: the contract)"))
        print_rules(A["rules"][k], B["rules"][k], r, k)
    print("ENGINES  " + line)


def print_rules(A, B, r, k):
    for side, fn, args, rs in r["impure"]:
        print("NOTE  in %s, Math.%s gave %d results for one argument (%s)" % (side, fn, len(rs), args))
    for fn in FNS:
        f = r["functions"][fn]
        if f["calls"] == (0, 0):
            print("Math.%-6s not called in either" % fn)
            continue
        head = "Math.%-6s %d and %d calls; %d and %d distinct arguments, %d in common: " % (fn, f["calls"][0], f["calls"][1], f["A"], f["B"], f["common"])
        if not f["diff"]:
            print(head + "the same result on every one")
        else:
            print(head + "DIFFERENT results on %d" % len(f["diff"]))
            for args, ra, rb in f["diff"][:3]:
                print("    Math.%s(%s): A %s, B %s, %d ulp apart" % (fn, ", ".join(show(a) for a in args.split(",")), show(ra), show(rb), ulps(ra, rb)))
    o = r["order"]
    if o is None:
        print("calls in order: the same %d calls, argument for argument and result for result" % len(A["calls"]) if A["calls"] else "calls in order: no call of the engine's Math in either")
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
    calls = len(A["calls"]) + len(B["calls"])
    print("SUMMARY rules %s  engine Math calls: %d; functions with different results on common arguments: %s; states parted: %s" % (
        k, calls, ", ".join("Math." + f for f in fns) or "none", "; ".join(parted) or "none"))


# ------------------------------------------------------------------------------------------------ the file
def load(path):
    with open(path, encoding="utf-8") as fh:
        T = json.load(fh)
    if T.get("format") != "VERDANDI-TRACE" or T.get("version") not in ("0", "1"):
        raise SystemExit("TRACE: %s is not a VERDANDI-TRACE file of version 0 or 1" % path)
    if T.get("error"):
        raise SystemExit("TRACE: %s records a failed trace: %s" % (path, T["error"]))
    if T["version"] == "0":   # before the rules were versioned: one section, played under what are now rules 0
        T["rules"] = {"0": {"calls": T.pop("calls"), "runs": T.pop("runs")}}
    return T


def summary(T, path):
    print("TRACE  map %s  engine %s" % (T["map"], engine_tag(T["runtime"])))
    print("runtime  %s" % T["runtime"].get("userAgent"))
    if T["runtime"].get("brands"):
        print("brands   %s  (%s)" % (", ".join(T["runtime"]["brands"]), T["runtime"].get("platform")))
    if T.get("inputs_from"):
        print("the runs given: those of %s (inputs %s)" % (T["inputs_from"]["engine"], T["inputs_from"]["inputs"][:16]))
    for k in RULES:
        if k not in T["rules"]:
            continue
        R = T["rules"][k]
        print("rules %s: %d calls of the engine's Math" % (k, len(R["calls"])))
        for fn in FNS:
            m = results_by_argument(R["calls"], fn)
            if not m:
                continue
            pairs = "\n".join("%s>%s" % (a, ",".join(sorted(rs))) for a, rs in sorted(m.items()))
            print("  Math.%-6s %6d calls, %6d distinct arguments, digest of its (argument, result) pairs %s" % (
                fn, sum(1 for c in R["calls"] if c[2] == fn), len(m), sha(pairs)[:16]))
        for run in R["runs"]:
            print("  run %-10s %5d ticks; inputs %s; every tick's state %s; the last state %s" % (
                run["name"], len(run["snaps"]), sha("\n".join(run["inputs"]))[:16], sha("\n".join(run["snaps"]))[:16], sha(run["snaps"][-1])[:16]))
    print("written %s" % os.path.relpath(path))
    print("compare it with another trace: python graybox/trace.py compare %s OTHER.json" % os.path.relpath(path))


# ------------------------------------------------------------------------------------------------ run
def cmd_run(argv):
    args = [a for a in argv if not a.startswith("--")]
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    name = args[0] if args and args[0] not in (opt("--port"), opt("--timeout"), opt("--inputs"), opt("--name"), opt("--browser"), opt("--expect")) else "tactical"
    label, browser = opt("--name"), opt("--browser")
    if browser is not None and not re.fullmatch(r"[A-Za-z0-9._-]+", browser):
        print("TRACE: a browser is named by letters, digits, ., _ and - (msedge, chrome, firefox)", file=sys.stderr)
        return 2
    expect = opt("--expect") or (BROWSERS.get(browser.lower()) if browser else None)
    if expect is not None and expect not in FAMILIES:
        print("TRACE: --expect is one of %s" % ", ".join(FAMILIES), file=sys.stderr)
        return 2
    if label and label.split("-")[0] in FAMILIES and expect and label.split("-")[0] != expect:
        print("TRACE: the name %s says %s, and the trace is expected from %s" % (label, label.split("-")[0], expect), file=sys.stderr)
        return 2
    if label is not None and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", label):
        print("TRACE: a trace's name is lower-case letters, digits and -", file=sys.stderr)
        return 2
    if not re.fullmatch(r"[a-z0-9_-]+", name):
        print("TRACE: a map's name is lower-case letters, digits, - and _", file=sys.stderr)
        return 2
    try:
        m = level.convert(name)
    except level.MapError as e:
        print("GRAYBOX-MAP: %s" % e, file=sys.stderr)
        return 2
    given = None
    if opt("--inputs"):
        G = load(opt("--inputs"))
        if G.get("map") != name:
            print("TRACE: %s is a trace of the map %s, not %s" % (opt("--inputs"), G.get("map"), name), file=sys.stderr)
            return 2
        src = G["rules"].get("1") or G["rules"]["0"]
        runs = [{"name": r["name"], "start": r["start"], "inputs": r["inputs"]} for r in src["runs"]]
        given = {"from": {"engine": engine_tag(G.get("runtime")), "inputs": sha(json.dumps(runs, sort_keys=True, separators=(",", ":")))},
                 "runs": runs}
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
                self.send_header("Location", "/trace.html?map=%s%s" % (name, "&inputs=1" if given else ""))
                self.end_headers()
                return
            if path == "/map/%s.json" % name:
                return self.send(200, level.canon(m), "application/json")
            if given and path == "/inputs.json":
                return self.send(200, json.dumps(given).encode("utf-8"), "application/json")
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
    print("TRACE  map %s  open %s%s" % (name, url, "  (playing the runs of %s)" % given["from"]["engine"] if given else ""))
    if browser:
        print("TRACE  opening it in %s; a trace from %s is expected" % (browser, expect or "any engine"))
        try:
            open_in(browser, url)
        except OSError as e:
            print("TRACE: %s could not be opened (%s); open the address in it by hand" % (browser, e), file=sys.stderr)
    elif "--no-browser" not in argv:
        webbrowser.open(url)
    elif expect:
        print("TRACE  open it in a %s browser; a trace from another engine will be refused" % expect)
    ok = done.wait(float(opt("--timeout", "180")))
    srv.shutdown()
    if not ok:
        print("TRACE: no trace came back from the page in time", file=sys.stderr)
        return 2
    T = got["trace"]
    if T.get("error"):
        print("TRACE: the page failed: %s" % T["error"], file=sys.stderr)
        return 1
    fam = engine_family(T.get("runtime"))
    if expect and fam != expect:
        print("TRACE: REFUSED, not written: the trace came from %s (%s), not from a %s engine" % (
            engine_tag(T.get("runtime")), (T.get("runtime") or {}).get("userAgent"), expect), file=sys.stderr)
        return 1
    if label and label.split("-")[0] in FAMILIES and label.split("-")[0] != fam:
        print("TRACE: REFUSED, not written: the name %s says %s, and the trace came from %s" % (label, label.split("-")[0], engine_tag(T.get("runtime"))), file=sys.stderr)
        return 1
    outdir = os.path.join(HERE, "build", "trace", name)
    os.makedirs(outdir, exist_ok=True)
    suffix = "-given" if given else ""
    path = os.path.join(outdir, engine_tag(T["runtime"]) + suffix + ".json")
    names = [path] + ([os.path.join(outdir, fam + suffix + ".json")] if fam in FAMILIES else []) + \
        ([os.path.join(outdir, label + ".json")] if label else []) + [os.path.join(outdir, "latest.json")]
    for p in names:   # latest.json: the last trace of this map, whatever the engine
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(T, fh, separators=(",", ":"), sort_keys=True)
            fh.write("\n")
    summary(T, path)
    for p in names[1:]:
        print("written %s" % os.path.relpath(p))
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

    full = A
    r = compare(full, copy.deepcopy(full))
    clean = all(x["order"] is None and not any(f["diff"] for f in x["functions"].values())
                and all(not y["input"] and not y["state"] for y in x["runs"].values()) for x in r.values())
    found("a trace against itself: nothing found", clean, "rules " + ", ".join(sorted(r)))
    found("a trace against itself: named not a cross-engine comparison", engines(full, full)[0] == "same", engines(full, full)[1])
    uas = {"firefox": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:157.0) Gecko/20100101 Firefox/157.0",
           "chromium": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0",
           "safari": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
           "other": "node v22.22.2 (V8 12.4.254.21-node.39)"}
    got = {k: engine_family({"userAgent": v}) for k, v in uas.items()}
    found("the engine families named from the browsers' descriptions", all(k == v for k, v in got.items()), ", ".join("%s -> %s" % kv for kv in got.items()))
    X = copy.deepcopy(full)
    X["runtime"] = {"userAgent": uas["chromium" if engine_family(full.get("runtime")) == "firefox" else "firefox"]}
    found("a trace against one from another engine: named cross-engine", engines(full, X)[0] == "cross", engines(full, X)[1])
    A = full["rules"]["0"]   # the plants: in the rules-0 section, which calls the engine's Math
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
        r = compare_rules(A, B)
        d = r["functions"][fn]["diff"]
        first = min(i for i, c in enumerate(A["calls"]) if c[2] == fn and c[3] == args)
        found("plant: Math.cos's result changed in its last bit at one argument", len(d) == 1 and d[0][0] == args and r["order"]["kind"] == "result" and r["order"]["index"] == first,
              "named Math.cos(%s), first at call %d, as a result" % (args, first))
        B = copy.deepcopy(A)
        B["calls"][k][3] = ",".join(flip(a) for a in args.split(","))
        r = compare_rules(A, B)
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
        r = compare_rules(A, B)
        st = r["runs"][walk["name"]]["state"]
        found("plant: one state leaf changed at tick 500", st is not None and st["tick"] == 500 and [x[0] for x in st["leaves"]] == ["x"], "tick 500, leaf x")
        B = copy.deepcopy(A)
        B["runs"][0]["inputs"][299] = B["runs"][0]["inputs"][299] + " "
        r = compare_rules(A, B)
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
