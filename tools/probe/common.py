# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# tools/probe/common.py — what the five probes of docs/STUDIO-CONTRACT.md §11 share: their one output form, the
# repository's paths, a free port, and waiting for play.py's /healthz. Off the gate; standard library only. A probe
# prints only what its verdict needs: never the machine's edition or its hardware.
#
#   PROBE <n>-<name> <case> HELD|BROKEN|SKIPPED [key=value ...]
#   PROBE <n>-<name> VERDICT HELD | KILLED <criterion> | INCOMPLETE <why>

import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "art"))
sys.path.insert(0, os.path.join(REPO, "art", "director"))


class Probe:
    def __init__(self, n, name):
        self.tag = "PROBE %d-%s" % (n, name)
        self.cases = []

    def case(self, case, status, **kv):
        assert status in ("HELD", "BROKEN", "SKIPPED")
        self.cases.append((case, status))
        extra = " ".join("%s=%s" % (k, str(v).replace(" ", "_")) for k, v in kv.items())
        print("%s %s %s%s" % (self.tag, case, status, (" " + extra) if extra else ""), flush=True)
        return status == "HELD"

    def verdict(self, killed=None, incomplete=None):
        if killed:
            print("%s VERDICT KILLED %s" % (self.tag, killed), flush=True)
            return 1
        if incomplete or not self.cases or any(s == "SKIPPED" for _c, s in self.cases):
            print("%s VERDICT INCOMPLETE %s" % (self.tag, incomplete or "a case was skipped"), flush=True)
            return 2
        if any(s == "BROKEN" for _c, s in self.cases):
            print("%s VERDICT HELD with-broken-cases-that-are-not-kill-criteria" % self.tag, flush=True)
            return 0
        print("%s VERDICT HELD" % self.tag, flush=True)
        return 0


def windows_only(p):
    if os.name != "nt":
        p.case("windows", "SKIPPED", why="this probe measures Windows")
        sys.exit(p.verdict(incomplete="not Windows"))


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def health(port):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/healthz" % port, timeout=3) as r:
            return json.loads(r.read())
    except (urllib.error.URLError, OSError, ValueError):
        return None


def wait_health(port, secs=120, pred=lambda h: h.get("ready")):
    t = time.time()
    while time.time() - t < secs:
        h = health(port)
        if h and pred(h):
            return h
        time.sleep(0.3)
    return None


def post(port, path, token, body=None):
    q = urllib.request.Request("http://127.0.0.1:%d%s" % (port, path), data=json.dumps(body or {}).encode("utf-8"), method="POST",
                               headers={"Content-Type": "application/json", "X-Studio-Token": token})
    try:
        with urllib.request.urlopen(q, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, OSError):
        return 0


def page_token(port):
    import re
    with urllib.request.urlopen("http://127.0.0.1:%d/play.html" % port, timeout=10) as r:
        return re.search(r'data-studio="([0-9a-f]+)"', r.read().decode("utf-8")).group(1)
