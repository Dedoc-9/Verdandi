# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/studio_queue.py — the studio's queue of creative work (STUDIO-2): prompts queued for any open or closed world, each
# with the provider and the model it is to be asked of, run in the background while the person plays, and kept across
# restarts. Standard library only.
#
# A task belongs to a world, never to the window: it records its world, the references (target and pins) and the
# camera it was queued with, the world's head when it was queued and when it ran, its provider's configuration file and
# its model. Tasks run in the order they were queued, at most `concurrency` at once, and at most one per world, so that
# a world's requests meet the head the one before it left (Creative World Closure, docs/CWCT.md: the epoch clause).
#
#   queued → running → ready | answered | failed | cancelled
#   ready → reviewed (a candidate admitted, all rejected, or set aside)    answered → reviewed (set aside)
#   running, when the studio stops → interrupted            answered, failed, cancelled, interrupted → queued again
# A task is answered (0220) when its request came back with no candidates and a disposition that says why:
# UNSUPPORTED (with what the studio cannot make yet), AMBIGUOUS (with the director's questions) or DECLINED.
#
# A ready task does not hold its world: the next task for it may run, and the ready one is reviewed later by drawing its
# recorded candidates again at the head as it is then (Gateway.restore), re-evaluated, never trusted — and admitted only
# at the head it is drawn at, as every candidate is. Nothing here admits: the person does, through the gateway.
#
# The queue is one file (`<worlds>/queue.jsonl` in worlds mode; `<root>/art/build/studio/queue.jsonl` in one tree), one
# event a line, each appended and flushed (art/director/durable.py), one at a time (every append holds the queue's lock:
# on Windows two unlocked appends at once lost and tore lines, MEASURED on the owner's machine, 2026-10-13); it is a work
# list, not a world's record (the ledger is): a line that cannot be read is skipped and said. Two rules from the ghost
# search (fixes 3 and 4 of 2026-10-13): a torn last line is set aside and cut from the file, durably, before anything is
# appended (as the ledger's and the promotion journal's are), so the next event never merges into it; and a task the
# studio stopped under is not taken for lost when its answer was recorded — its world's records hold the response and
# the candidates' intents, so it is ready to review, and nothing is asked (or paid for) again.

import datetime
import json
import os
import re
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "director"))
import durable        # noqa: E402
import studio         # noqa: E402

PROVIDERS_DIR = os.path.join(REPO, "art", "providers")
MODELS = ("", "claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5", "claude-fable-5-1")   # "" is the configuration's own
STATES = ("queued", "running", "ready", "answered", "failed", "cancelled", "interrupted", "reviewed")
CONFIG = re.compile(r"[a-z][a-z0-9_]{0,40}\.json\Z")


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def providers():
    """The provider configurations a task may name: art/providers/*.json that load."""
    out = []
    for f in sorted(os.listdir(PROVIDERS_DIR)):
        if CONFIG.match(f):
            try:
                cfg = studio.load_config(os.path.join(PROVIDERS_DIR, f))
                out.append({"file": f, "label": cfg["model"]})
            except studio.StudioError:
                pass
    return out


class Queue:
    def __init__(self, hub, path, concurrency=2, say=print, tick=0.2):
        self.hub, self.path, self.concurrency, self.say, self.tick = hub, path, max(1, int(concurrency)), say, tick
        self.lock = threading.Lock()
        self.tasks = {}          # id -> task
        self.order = []          # ids in the order they were queued
        self.n = 0
        self.notices = []        # (time, text) of tasks that became ready or failed: the page's toasts
        self.stopping = threading.Event()
        self.thread = None
        self._replay()

    # ------------------------------------------------------------------ the file
    def _event(self, e):
        e = dict(e, at=now())
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        durable.append(self.path, (json.dumps(e, sort_keys=True, ensure_ascii=True) + "\n").encode("ascii"))

    def _replay(self):
        if not os.path.exists(self.path):
            return
        raw = open(self.path, "rb").read()
        if raw and not raw.endswith(b"\n"):
            cut = raw.rfind(b"\n") + 1                       # a torn last line: never acted on; set aside, and cut from the file
            aside = "%s.torn.%d" % (self.path, cut)
            if durable.PLANT != "queue-torn-in-memory":
                durable.write(aside, raw[cut:])
                durable.write(self.path, raw[:cut])
            raw = raw[:cut]
            self.say("queue: a torn last line set aside in %s" % os.path.basename(aside))
        bad = 0
        for ln in raw.splitlines():
            try:
                e = json.loads(ln)
                self._apply(e)
            except (ValueError, KeyError, TypeError):
                bad += 1
        if bad:
            self.say("queue: %d line%s that could not be read, skipped" % (bad, "" if bad == 1 else "s"))
        for tid in self.order:                                # the studio stopped while these ran
            t = self.tasks[tid]
            if t["status"] != "running":
                continue
            n = self._recorded(t) if durable.PLANT != "queue-forgets" else 0
            d = self._recorded_answer(t) if not n and durable.PLANT != "queue-forgets" else None
            if n:                                             # its answer was recorded: ready to review, nothing asked again
                e = {"e": "ready", "id": tid, "candidates": n, "drawn": 0, "recovered": True,
                     "message": "recovered after a restart: %d candidate%s recorded; review to draw them" % (n, "" if n == 1 else "s")}
            elif d is not None:                               # an answer with no candidates was recorded: read again, not asked again
                e = {"e": "answered" if d["kind"] != "FAILED" else "failed", "id": tid, "code": d.get("code") or d["kind"], "recovered": True,
                     "disposition": d, "message": "recovered after a restart: %s: %s" % (d["kind"], d["detail"])}
            else:                                             # its provider died with the studio, before it answered
                e = {"e": "interrupted", "id": tid}
            self._event(e)
            self._apply(e)

    def _recorded(self, t):
        """How many candidates a task's request recorded (its response and its intents, in its world's records), or 0."""
        if not t.get("rid") or not re.match(r"[0-9TZ:-]{8,40}\Z", t["rid"]):
            return 0
        d = os.path.join(self.hub.root_of(t["world"]), "art", "build", "studio", t["world"], t["rid"])
        if not os.path.isfile(os.path.join(d, "response.raw")):
            return 0
        return sum(1 for letter in studio.LETTERS if os.path.isfile(os.path.join(d, letter + ".intent")))

    def _recorded_answer(self, t):
        """The disposition of a task's recorded response with no candidates, read again from its record (0220), or None."""
        if not t.get("rid") or not re.match(r"[0-9TZ:-]{8,40}\Z", t["rid"]):
            return None
        f = os.path.join(self.hub.root_of(t["world"]), "art", "build", "studio", t["world"], t["rid"], "response.raw")
        try:
            prov, cands, outcome = studio.read_response(open(f, "rb").read(), t["rid"])
        except (OSError, studio.StudioError):
            return None
        d = studio.disposition(prov, cands, outcome)
        return None if d["kind"] == "REALIZED" else d

    def _apply(self, e):
        k = e["e"]
        if k == "queued":
            t = dict(e["task"])
            self.tasks[t["id"]] = t
            self.order.append(t["id"])
            self.n = max(self.n, int(t["id"].split("-")[1]))
            return
        t = self.tasks[e["id"]]
        if k == "started":
            t.update(status="running", rid=e["rid"], head_at_run=e["head"], scene_at_run=e.get("scene", ""), started=e.get("at", ""), message="", code="")
        elif k == "ready":
            t.update(status="ready", message=e["message"], candidates=e["candidates"], drawn=e["drawn"], ended=e.get("at", ""),
                     recovered=bool(e.get("recovered")), usage=e.get("usage"))
        elif k == "answered":
            t.update(status="answered", code=e.get("code", ""), message=e.get("message", ""), disposition=e.get("disposition"),
                     ended=e.get("at", ""), usage=e.get("usage"), recovered=bool(e.get("recovered")))
        elif k in ("failed", "cancelled", "interrupted"):
            t.update(status=k, code=e.get("code", ""), message=e.get("message", {"cancelled": "cancelled", "interrupted": "the studio stopped while it ran"}.get(k, "")),
                     ended=e.get("at", ""))
            if e.get("disposition"):
                t["disposition"] = e["disposition"]
        elif k == "reviewed":
            t.update(status="reviewed", decision=e["decision"])
        elif k == "requeued":
            t.update(status="queued", rid="", message="queued again", code="")

    # ------------------------------------------------------------------ what the page asks
    def add(self, world, prompt, provider=None, model="", camera=None):
        """Queue a prompt for a world, with that world's present target and pins. Returns the task's id."""
        live = self.hub.world(world)
        g = live.studio
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > studio.LIMITS["prompt"]:
            raise studio.StudioError("STUDIO-PROMPT", "a prompt is 1 to %d characters" % studio.LIMITS["prompt"])
        provider = provider or (os.path.basename(g.cfg["path"]) if g.cfg else "")
        if provider not in [p["file"] for p in providers()]:
            raise studio.StudioError("STUDIO-NO-PROVIDER", "no provider configuration %r in art/providers/" % (provider,))
        if model not in MODELS:
            raise studio.StudioError("STUDIO-MODEL", "the model is one of %s, or the configuration's own" % ", ".join(m for m in MODELS if m))
        with g.lock:
            target, pins = g.target, list(g.pins)
        s0 = live.slot(0)
        with self.lock:
            self.n += 1
            tid = "t-%d-%s" % (self.n, datetime.datetime.now(datetime.timezone.utc).strftime("%H%M%S"))
            t = {"id": tid, "world": live.brief, "prompt": prompt.strip(), "provider": provider, "model": model, "target": target,
                 "pins": pins, "camera": camera if isinstance(camera, dict) else None, "status": "queued", "queued": now(),
                 "scene_at_queue": s0["sha"] if s0 else "", "rid": "", "message": "", "code": "", "candidates": 0, "drawn": 0}
            self._event({"e": "queued", "task": t})
            self.tasks[tid] = t
            self.order.append(tid)
        return tid

    def cancel(self, tid):
        t = self._task(tid)
        if t["status"] == "queued":
            with self.lock:
                self._event({"e": "cancelled", "id": tid})
                self._apply({"e": "cancelled", "id": tid})
        elif t["status"] == "running":
            self.hub.world(t["world"]).studio.cancel_request(t["rid"])     # the scheduler sees it end
        else:
            raise studio.StudioError("STUDIO-QUEUE", "task %s is %s: nothing to cancel" % (tid, t["status"]))
        return {"id": tid}

    def requeue(self, tid):
        t = self._task(tid)
        if t["status"] not in ("answered", "failed", "cancelled", "interrupted"):
            raise studio.StudioError("STUDIO-QUEUE", "task %s is %s: only an answered, failed, cancelled or interrupted task is queued again" % (tid, t["status"]))
        with self.lock:
            self._event({"e": "requeued", "id": tid})
            self._apply({"e": "requeued", "id": tid})
            self.order.remove(tid)
            self.order.append(tid)                            # to the end of the line
        return {"id": tid}

    def review(self, tid):
        """Draw a ready task's candidates in its world (again, at the head as it is now, unless they are the ones drawn)."""
        t = self._task(tid)
        if t["status"] != "ready":
            raise studio.StudioError("STUDIO-QUEUE", "task %s is %s, not ready for review" % (tid, t["status"]))
        g = self.hub.world(t["world"]).studio
        with g.lock:
            current = g.req is not None and g.req["id"] == t["rid"]
        if not current:
            g.restore(t["rid"])
        return {"id": tid, "world": t["world"], "drawn_again": not current}

    def dismiss(self, tid):
        t = self._task(tid)
        if t["status"] not in ("ready", "answered"):
            raise studio.StudioError("STUDIO-QUEUE", "task %s is %s: only a ready or answered task is set aside" % (tid, t["status"]))
        with self.lock:
            self._event({"e": "reviewed", "id": tid, "decision": "set aside"})
            self._apply({"e": "reviewed", "id": tid, "decision": "set aside"})
        return {"id": tid}

    def _task(self, tid):
        with self.lock:
            t = self.tasks.get(tid)
            if t is None:
                raise studio.StudioError("STUDIO-QUEUE", "no task %r" % (tid,))
            return dict(t)

    def state(self):
        with self.lock:
            ts = [dict(self.tasks[i]) for i in reversed(self.order)][:40]
            counts = {s: sum(1 for t in self.tasks.values() if t["status"] == s) for s in STATES}
            notices = list(self.notices[-8:])
        for t in ts:
            live = self.hub.worlds.get(t["world"])
            s0 = live.slot(0) if live is not None else None
            t["stale"] = bool(t["status"] == "ready" and s0 and t.get("scene_at_run") and s0["sha"] != t["scene_at_run"])
            t.pop("camera", None)
        return {"tasks": ts, "counts": counts, "concurrency": self.concurrency, "providers": providers(), "models": list(MODELS),
                "notices": notices}

    # ------------------------------------------------------------------ the scheduler
    def opened(self, world):
        """A world just opened: if its newest ready task is not drawn there, nothing is drawn now (the person reviews it)."""
        return None

    def start(self):
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.stopping.set()

    def _loop(self):
        while not self.stopping.wait(self.tick):
            try:
                self.step()
            except Exception as e:  # noqa: BLE001 — the scheduler says what failed and goes on
                self.say("queue: %s: %s" % (type(e).__name__, e))

    def step(self):
        """Follow the running tasks; start queued ones while there is room. Returns the ids started."""
        with self.lock:
            running = [self.tasks[i] for i in self.order if self.tasks[i]["status"] == "running"]
            ready = [self.tasks[i] for i in self.order if self.tasks[i]["status"] == "ready"]
        for t in running:
            live = self.hub.worlds.get(t["world"])
            r = live.studio.req if live is not None else None
            if r is None or r["id"] != t["rid"]:
                self._end(t, "failed", "STUDIO-LOST", "the request is no longer its world's (asked over it from elsewhere)")
            elif r["state"] == "done" and (r.get("disposition") or {}).get("kind", "REALIZED") != "REALIZED":
                d = r["disposition"]
                self._end(t, "answered", d["kind"], r["message"], usage=(r.get("provider") or {}).get("usage"), disp=d)
            elif r["state"] == "done":
                drawn = sum(1 for c in r["candidates"] if c["slot"] is not None)
                self._end(t, "ready", "", r["message"], candidates=len(r["candidates"]), drawn=drawn,
                          usage=(r.get("provider") or {}).get("usage"))
            elif r["state"] == "failed":
                self._end(t, "failed", r["code"], r["message"], disp=r.get("disposition"))
            elif r["state"] in ("cancelled", "superseded"):
                self._end(t, "cancelled", r["code"], r["message"])
        for t in ready:                                       # a ready task whose candidates the person decided on
            live = self.hub.worlds.get(t["world"])
            r = live.studio.req if live is not None else None
            if r is not None and r["id"] == t["rid"] and r["state"] == "done":
                decided = [c["decided"] for c in r["candidates"] if c["slot"] is not None]
                admitted = [c["letter"] for c in r["candidates"] if c["decided"] == "admitted"]
                if admitted or (decided and all(decided)):
                    with self.lock:
                        d = "admitted " + admitted[0] if admitted else "all rejected"
                        self._event({"e": "reviewed", "id": t["id"], "decision": d})
                        self._apply({"e": "reviewed", "id": t["id"], "decision": d})
        started = []
        with self.lock:
            busy = {self.tasks[i]["world"] for i in self.order if self.tasks[i]["status"] == "running"}
            room = self.concurrency - len(busy)
            todo = []
            for i in self.order:
                t = self.tasks[i]
                if room <= 0:
                    break
                if t["status"] == "queued" and t["world"] not in busy:
                    todo.append(dict(t))
                    busy.add(t["world"])
                    room -= 1
        for t in todo:
            self._run(t)
            started.append(t["id"])
        return started

    def _end(self, t, status, code, message, candidates=0, drawn=0, usage=None, disp=None):
        with self.lock:
            if status == "ready":
                e = {"e": "ready", "id": t["id"], "message": message, "candidates": candidates, "drawn": drawn}
            else:
                e = {"e": status, "id": t["id"], "code": code, "message": message}
            if isinstance(usage, dict) and status in ("ready", "answered"):   # what the provider said it used, as it said it
                e["usage"] = {k: usage[k] for k in ("input_tokens", "output_tokens", "cost_usd", "cost_basis") if k in usage}
            if isinstance(disp, dict):
                e["disposition"] = {k: disp[k] for k in ("kind", "decided_by", "code", "detail", "unmet", "questions", "reason", "note") if k in disp}
            self._event(e)
            self._apply(e)
            self.notices.append((time.time(), "%s · %s: %s" % (t["world"], t["prompt"][:40], message if status in ("ready", "answered") else status + " (" + (code or message)[:60] + ")"),
                                 t["id"], t["world"], status))
            self.notices = self.notices[-20:]

    def _run(self, t):
        try:
            live = self.hub.world(t["world"])
            g = live.studio
            cfg = studio.load_config(os.path.join(PROVIDERS_DIR, t["provider"]))
            if t["model"]:
                cfg = dict(cfg, env={"VERDANDI_DIRECTOR_MODEL": t["model"]}, model="%s (%s)" % (t["model"], cfg["model"]))
            s0 = live.slot(0)
            rid = g.ask(t["prompt"], None, t.get("camera"), refs=(t["target"], t["pins"]), cfg=cfg)
            with g.lock:
                head = g.req["head"] if g.req and g.req["id"] == rid else ""
            with self.lock:
                e = {"e": "started", "id": t["id"], "rid": rid, "head": head, "scene": s0["sha"] if s0 else ""}
                self._event(e)
                self._apply(e)
        except studio.StudioError as e:
            self._end(t, "failed", e.code, e.detail)
        except Exception as e:  # noqa: BLE001 — a task that cannot start fails, with why; the queue goes on
            self._end(t, "failed", "STUDIO-FAILED", "%s: %s" % (type(e).__name__, str(e)[:200]))


# ------------------------------------------------------------------------------------------------ the self-test
def selftest():
    """STUDIO-2 end to end, off the gate, in a scratch folder: the worlds folder seeded from a checkout of its own (the
    fixture's plaza with a ledger and tags, and harbor-day), a checkout whose ledger does not verify refused; the worlds
    served, each read by name, each from its own tree; a request queued for one world while the page plays the other,
    run, reviewed and admitted there, the other world's bytes untouched; a world duplicated with maps of its own; at
    most two requests at once and one per world; the studio busy while work waits; two worlds compiled at once over
    different maps; and fixes 3 and 4 of 2026-10-13 with their plants (a torn tail cut durably; a task the studio
    stopped under, whose answer was recorded, ready without asking again)."""
    import shutil
    import tempfile
    import urllib.error
    import urllib.request
    import play
    D = play.director()
    tmp = tempfile.mkdtemp(prefix="studio2-selftest-")
    rows = []
    saved_dir, saved_plant = globals()["PROVIDERS_DIR"], durable.PLANT
    srv = hub = None

    def row(name, ok, detail):
        rows.append(bool(ok))
        print("[%s] %s — %s" % ("PASS" if ok else "FAIL", name, detail), flush=True)

    def tree_bytes(root, skip=("art/build/",)):
        out = {}
        for dp, _dn, fn in os.walk(root):
            for f in fn:
                rel = os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/")
                if not rel.startswith(skip):
                    out[rel] = open(os.path.join(dp, f), "rb").read()
        return out

    def checkout(name, edit_recorded=True):
        src = os.path.join(tmp, name)
        ws = D.selftest_tree(src)
        shutil.copy(os.path.join(REPO, "art", "briefs", "harbor-day.art"), os.path.join(src, "art", "briefs", "harbor-day.art"))
        with open(ws.art, "ab") as fh:
            fh.write(b"# a hand edit\n")
        if edit_recorded:
            D._quiet(D.cmd_rebase, ws, "the self-test's hand edit")
            with open(os.path.join(src, "art", "ledger", "plaza-night.tags.json"), "wb") as fh:
                fh.write(studio.canon.dumps({"format": studio.TAGS_FORMAT, "version": "0", "brief": "plaza-night", "next": "1", "tags": []}) + b"\n")
        return src

    try:
        # 1. the worlds folder seeded from a checkout
        src = checkout("checkout")
        before = tree_bytes(src)
        worlds = os.path.join(tmp, "worlds")
        said = []
        made = play.seed_worlds(worlds, source=src, say=said.append)
        wp = os.path.join(worlds, "plaza-night")
        same = all(open(os.path.join(wp, rel), "rb").read() == before[rel] for rel in
                   ("art/briefs/plaza-night.art", "art/ledger/plaza-night.ledger", "art/ledger/plaza-night.tags.json", "graybox/maps/tactical.layout"))
        seeded = json.load(open(os.path.join(worlds, "SEEDED.json")))
        row("the worlds seeded from the checkout: each brief a world of its own tree, the plaza's ledger and tags copied byte for byte and "
            "verified in the copy; the checkout unchanged", made == ["harbor-day", "plaza-night"] and same and tree_bytes(src) == before
            and seeded["worlds"]["plaza-night"]["ledger_events"] == "2" and not os.path.exists(os.path.join(worlds, "harbor-day", "art", "ledger")),
            "; ".join(said)[:200])
        again = play.seed_worlds(worlds, source=src, say=said.append)
        row("seeded once: a folder that holds worlds is not seeded again", again == [] and json.load(open(os.path.join(worlds, "SEEDED.json"))) == seeded, "made %s" % again)
        bad = checkout("checkout-unlogged", edit_recorded=False)
        w2, said2 = os.path.join(tmp, "worlds-2"), []
        made2 = play.seed_worlds(w2, source=bad, say=said2.append)
        row("a checkout brief whose ledger does not verify is not made a world, and why is said; nothing of it left", made2 == ["harbor-day"]
            and not os.path.exists(os.path.join(w2, "plaza-night")) and not os.path.exists(os.path.join(w2, "plaza-night.making"))
            and "UNLOGGED-CHANGE" in json.load(open(os.path.join(w2, "SEEDED.json")))["worlds"]["plaza-night"]["refused"],
            [ln for ln in said2 if "NOT" in ln][0][:160] if any("NOT" in ln for ln in said2) else "nothing said")

        # 2. the worlds served
        pdir = os.path.join(tmp, "providers")
        os.makedirs(pdir)
        shutil.copy(os.path.join(REPO, "art", "providers", "scripted.json"), os.path.join(pdir, "scripted.json"))
        slow = os.path.join(tmp, "slow.py")
        open(slow, "w").write("import sys, time\nsys.stdin.read()\ntime.sleep(2.5)\n")
        json.dump({"provider": "cli", "argv": ["{python}", slow], "model": "slow", "timeout_s": 60, "max_output_bytes": 65536},
                  open(os.path.join(pdir, "slow.json"), "w"))
        globals()["PROVIDERS_DIR"] = pdir
        hub = play.Hub(config=os.path.join(pdir, "scripted.json"), say=lambda s: None, watch=False, worlds_dir=worlds, default="plaza-night")
        night = hub.world("plaza-night")
        hub.queue = Queue(hub, os.path.join(worlds, "queue.jsonl"), concurrency=2, say=lambda s: None, tick=0.1)
        srv = play.server(hub, 0)
        base = "http://127.0.0.1:%d" % srv.server_address[1]
        tok = hub.token

        def get(path):
            try:
                with urllib.request.urlopen(base + path, timeout=60) as r:
                    return r.status, r.read()
            except urllib.error.HTTPError as e:
                return e.code, e.read()

        def post(path, body):
            q = urllib.request.Request(base + path, data=json.dumps(body).encode(), method="POST",
                                       headers={"Content-Type": "application/json", "X-Studio-Token": tok})
            try:
                with urllib.request.urlopen(q, timeout=120) as r:
                    return r.status, json.loads(r.read())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read() or b"{}")
        c1, lv = get("/live?world=harbor-day")
        lv = json.loads(lv)
        harbor = hub.worlds["harbor-day"]
        hs = harbor.slot(0)
        c2, sb = get("/scene/harbor-day.json?slot=0")
        c3, mb = get("/map/%s.json?slot=0&world=harbor-day" % hs["map"])
        row("each world read by name, from its own tree: /live?world=, its scene, its map", c1 == 200 and lv["brief"] == "harbor-day"
            and [w["world"] for w in lv["worlds"]] == ["harbor-day", "plaza-night"] and c2 == 200 and play.sha256(sb) == hs["sha"]
            and c3 == 200 and mb == hs["map_bytes"] and harbor.root == os.path.join(worlds, "harbor-day") and night.root == wp
            and hs["sha"] != night.slot(0)["sha"], "harbor-day scene %s, plaza-night %s" % (hs["sha"][:12], night.slot(0)["sha"][:12]))

        # 3. a request queued for harbor-day while the page plays plaza-night: run, reviewed, admitted there
        night_before = tree_bytes(wp)
        c, r = post("/studio/select", {"world": "harbor-day", "piece": "canopy:19,10-28,11"})
        c, r = post("/studio/queue/add", {"world": "harbor-day", "prompt": "make the north slab heavier", "provider": "scripted.json"})
        tid = r.get("id")
        hub.queue.start()
        t0 = time.time()
        while time.time() - t0 < 120 and hub.queue._task(tid)["status"] in ("queued", "running"):
            time.sleep(0.2)
        t = hub.queue._task(tid)
        row("a request queued for the other world runs there in the background and is ready to review", c == 200 and t["status"] == "ready"
            and t["candidates"] == 3 and tree_bytes(wp) == night_before, "%s: %s; plaza-night's bytes %s" % (
                t["status"], t["message"], "unchanged" if tree_bytes(wp) == night_before else "CHANGED"))
        c, r = post("/studio/queue/review", {"id": tid})
        led_h = os.path.join(worlds, "harbor-day", "art", "ledger", "harbor-day.ledger")
        n0 = len(D.led.read(led_h)[0])
        # ADMISSION-0 (0222): the still the page takes of the candidate as drawn, given with the studio's token
        qs = urllib.request.Request(base + "/studio/still?world=harbor-day&id=%s&candidate=A" % t["rid"], data=D.selftest_still(), method="POST",
                                    headers={"Content-Type": "image/png", "X-Studio-Token": tok})
        with urllib.request.urlopen(qs, timeout=60) as r_:
            still = json.loads(r_.read()).get("still", "")
        c2, a = post("/studio/admit", {"world": "harbor-day", "id": t["rid"], "candidate": "A", "still": still})
        time.sleep(0.5)
        try:
            D._quiet(D.cmd_verify, D.Workspace("harbor-day", os.path.join(worlds, "harbor-day")), quiet=True)
            verified = True
        except D.led.LedgerError:
            verified = False
        t1 = time.time()
        while time.time() - t1 < 10 and hub.queue._task(tid)["status"] != "reviewed":
            time.sleep(0.1)
        row("reviewed and admitted in harbor-day: its ledger two events longer and verified; plaza-night's bytes untouched; the task reviewed",
            c == 200 and c2 == 200 and len(D.led.read(led_h)[0]) == n0 + 2 and verified and tree_bytes(wp) == night_before
            and hub.queue._task(tid)["status"] == "reviewed", "ledger #%s; the task %s" % (", #".join(a.get("ledger", [])), hub.queue._task(tid)["status"]))

        # 4. a world duplicated, with maps of its own
        c, r = post("/studio/worlds/duplicate", {"from": "plaza-night", "name": "plaza-copy"})
        wc = os.path.join(worlds, "plaza-copy")
        title = [ln for ln in open(os.path.join(wc, "art", "briefs", "plaza-copy.art"), encoding="utf-8") if ln.startswith("title ")]
        row("a world duplicated: a tree of its own, its maps copied, its title marked, a ledger of its genesis alone; the source untouched",
            c == 200 and r.get("world") == "plaza-copy" and open(os.path.join(wc, "graybox", "maps", "tactical.layout"), "rb").read()
            == open(os.path.join(wp, "graybox", "maps", "tactical.layout"), "rb").read() and "a copy of plaza-night" in (title or [""])[0]
            and len(D.led.read(os.path.join(wc, "art", "ledger", "plaza-copy.ledger"))[0]) == 1 and tree_bytes(wp) == night_before,
            (title or [""])[0].strip()[:90])

        # 0220: the first window, its views and its token; a task answered with no candidates
        c0 = urllib.request.urlopen(urllib.request.Request(base + "/", method="GET"), timeout=30)
        landed = c0.geturl().endswith("/start.html")
        _c, page = get("/start.html")
        presence = re.search(rb'data-presence="([0-9a-f]+)"', page).group(1).decode()
        _c, lj = get("/launcher.json")
        lj = json.loads(lj)
        vw = {v["id"]: v for v in lj["views"]}
        wl = {w["world"]: w for w in lj["worlds"]}
        row("the first window: / opens the launcher, which lists every world read back (its ledger replayed to its files) and every view, "
            "each from its manifest; a view not built says why",
            landed and wl["plaza-night"]["verified"] and wl["harbor-day"]["verified"] and wl["plaza-night"]["head"] == night.studio._head()[3]
            and vw["play"]["status"] == "ready" and vw["history"]["capability"] == "inspect" and vw["mechanisms"]["status"] == "not built"
            and vw["mechanisms"]["why"] and tok.encode() not in page,
            "worlds %s; views %s" % (", ".join("%s %s" % (w, "verified" if v["verified"] else v["error"][:30]) for w, v in sorted(wl.items())),
                                     ", ".join("%s %s" % (k, v["status"]) for k, v in sorted(vw.items()))))

        def post_as(path, body, token):
            q = urllib.request.Request(base + path, data=json.dumps(body).encode(), method="POST",
                                       headers={"Content-Type": "application/json", "X-Studio-Token": token})
            try:
                with urllib.request.urlopen(q, timeout=60) as r:
                    return r.status
            except urllib.error.HTTPError as e:
                return e.code
        codes = {p_: post_as(p_, b_, presence) for p_, b_ in (("/studio/alive", {}), ("/studio/ask", {"world": "plaza-night", "prompt": "x"}),
                                                                ("/studio/admit", {"world": "plaza-night", "id": "x", "candidate": "A"}),
                                                                ("/studio/queue/add", {"world": "plaza-night", "prompt": "x"}))}
        qs = urllib.request.Request(base + "/studio/still?world=plaza-night&id=x&candidate=A", data=D.selftest_still(), method="POST",
                                    headers={"Content-Type": "image/png", "X-Studio-Token": presence})
        try:
            with urllib.request.urlopen(qs, timeout=60) as r_:
                codes["/studio/still"] = r_.status
        except urllib.error.HTTPError as e:
            codes["/studio/still"] = e.code
        row("the launcher's token is good for the window's heartbeat and nothing else: it cannot ask, give a still, admit or queue",
            codes["/studio/alive"] == 200 and all(v == 403 for k, v in codes.items() if k != "/studio/alive"),
            ", ".join("%s %d" % (k.rsplit("/", 1)[-1], v) for k, v in codes.items()))
        saved_web = play.WEB
        try:
            fake_web = os.path.join(tmp, "web")
            shutil.copytree(os.path.join(saved_web, "views"), os.path.join(fake_web, "views"))
            open(os.path.join(fake_web, "views", "broken.json"), "w").write('{"id": "broken", "title": "x"}')
            open(os.path.join(fake_web, "views", "sneaky.json"), "w").write(json.dumps(dict(json.load(open(os.path.join(fake_web, "views", "play.json"))), id="sneaky", open="https://example.com/{world}")))
            play.WEB = fake_web
            vv = {v["id"]: v for v in play.views()}
        finally:
            play.WEB = saved_web
        row("a manifest that is not well formed, or that opens a page outside the studio, is listed as unavailable with why, never left out",
            vv["broken"]["status"] == "unavailable" and "fields" in vv["broken"]["why"] and vv["sneaky"]["status"] == "unavailable"
            and "opens none of the studio's pages" in vv["sneaky"]["why"] and vv["play"]["status"] == "ready",
            "%s; %s" % (vv["broken"]["why"][:60], vv["sneaky"]["why"][:60]))
        hd = os.path.join(worlds, "harbor-day", "art", "briefs", "harbor-day.art")
        keep = open(hd, "rb").read()
        try:
            open(hd, "ab").write(b"# changed outside the ledger\n")
            bad_i = hub.inspect("harbor-day")
        finally:
            open(hd, "wb").write(keep)
        good_i = hub.inspect("harbor-day")
        _c, hj = get("/history.json?world=harbor-day")
        hj = json.loads(hj)
        row("History: the world read back, its ledger newest first, its requests with what they came to; a file changed outside the ledger is "
            "not verified (plant), and verified again once restored",
            not bad_i["verified"] and "UNLOGGED-CHANGE" in bad_i["error"] and good_i["verified"] and hj["inspect"]["verified"]
            and [e["kind"] for e in hj["events"]][:2] == ["admit", "evaluate"] and hj["requests"] and not hj["records"]["breaks"],
            "planted: %s; restored: verified %s; %d events, %d requests" % (bad_i["error"][:50], good_i["verified"], len(hj["events"]), len(hj["requests"])))
        post("/studio/select", {"world": "harbor-day", "piece": None})        # no target: the prompt is for the whole world
        c, r = post("/studio/queue/add", {"world": "harbor-day", "prompt": "add a fisherman on the quay", "provider": "scripted.json"})
        tid_a = r.get("id")
        t0 = time.time()
        while time.time() - t0 < 60 and hub.queue._task(tid_a)["status"] in ("queued", "running"):
            time.sleep(0.1)
        ta = hub.queue._task(tid_a)
        c_set = post("/studio/queue/dismiss", {"id": tid_a})[0]
        row("a queued prompt the studio cannot make yet ends answered, not ready: UNSUPPORTED entity.person, with nothing to review; it can be set aside",
            ta["status"] == "answered" and (ta.get("disposition") or {}).get("unmet") == ["entity.person"] and c_set == 200
            and hub.queue._task(tid_a)["status"] == "reviewed",
            "%s: %s" % (ta["status"], ta["message"][:90]))

        # 5. at most two at once, one per world; the studio busy while work waits
        for w in ("plaza-night", "harbor-day"):
            post("/studio/select", {"world": w, "piece": "canopy:19,10-28,11"})
        ids = [post("/studio/queue/add", {"world": w, "prompt": "slow %d" % i, "provider": "slow.json"})[1].get("id")
               for i, w in enumerate(("harbor-day", "harbor-day", "plaza-night", "plaza-copy"))]
        most, per_world, busy_seen = 0, 0, False
        t0 = time.time()
        while time.time() - t0 < 60:
            st = hub.queue.state()
            run = [x for x in st["tasks"] if x["status"] == "running"]
            most = max(most, len(run))
            per_world = max([per_world] + [sum(1 for x in run if x["world"] == w) for w in ("harbor-day", "plaza-night", "plaza-copy")])
            busy_seen = busy_seen or json.loads(get("/healthz")[1])["busy"]
            if all(hub.queue._task(i)["status"] not in ("queued", "running") for i in ids):
                break
            time.sleep(0.1)
        busy_after = json.loads(get("/healthz")[1])["busy"]
        row("at most two requests at once and never two in one world; the studio busy while work waits, not after",
            most == 2 and per_world == 1 and busy_seen and not busy_after, "at most %d at once, %d in one world; busy while waiting %s, after %s" % (
                most, per_world, busy_seen, busy_after))
        c, r = post("/studio/queue/add", {"world": "plaza-copy", "prompt": "one to cancel", "provider": "slow.json"})
        hub.queue.stop()
        c2, _r = post("/studio/queue/cancel", {"id": r.get("id")})
        c3, _r = post("/studio/queue/requeue", {"id": ids[0]})
        row("a queued task cancelled; a failed one queued again", c2 == 200 and hub.queue._task(r["id"])["status"] == "cancelled" and c3 == 200
            and hub.queue._task(ids[0])["status"] == "queued", "%s; %s" % (hub.queue._task(r["id"])["status"], hub.queue._task(ids[0])["status"]))
        post("/studio/queue/cancel", {"id": ids[0]})

        # 6. two worlds compiled at once over different maps
        other = os.path.join(tmp, "older-maps")
        shutil.copytree(os.path.join(wp, "graybox", "maps"), other)
        rnd = os.path.join(REPO, "art", "rounds", "plaza-imposing", "base")
        for f in ("tactical.design", "tactical.layout"):
            shutil.copy(os.path.join(rnd, f), os.path.join(other, f))
        art = os.path.join(wp, "art", "briefs", "plaza-night.art")
        mine = play.maps_of(wp)
        want = {mine: play.compile_scene("plaza-night", art, mine)[1], other: play.compile_scene("plaza-night", art, other)[1]}

        def compile_trials(plant):
            wrong = [0]
            durable.PLANT = plant

            def one(m):
                for _i in range(12):
                    try:
                        wrong[0] += play.compile_scene("plaza-night", art, m)[1] != want[m]
                    except (SystemExit, ValueError, OSError):           # the converter read the other world's maps
                        wrong[0] += 1
            try:
                th = [threading.Thread(target=one, args=(m,)) for m in (mine, other)]
                for x in th:
                    x.start()
                for x in th:
                    x.join()
            finally:
                durable.PLANT = saved_plant
            return wrong[0]
        w0, w1 = compile_trials(""), compile_trials("no-export-lock")
        row("two worlds compiled at once over different maps: each its own map (plant: no lock, maps read across)", want[mine] != want[other]
            and w0 == 0 and w1 > 0, "%d of 24 wrong; with the plant %d" % (w0, w1))

        # 7. fix 3: a torn last line cut from the file before anything is appended (plant: cut in memory only)
        def torn_trial(plant):
            qp = os.path.join(tmp, "torn-%s.jsonl" % (plant or "fixed"))
            first = {"e": "queued", "task": dict(hub.queue._task(tid), id="t-1-000000", status="queued", rid="")}
            open(qp, "wb").write((json.dumps(first) + "\n").encode() + b'{"e": "started", "id": "t-1-0')
            durable.PLANT = plant
            try:
                q1 = Queue(hub, qp, say=lambda s: None)
                new = q1.add("plaza-copy", "after the tear", "scripted.json")
                q2 = Queue(hub, qp, say=lambda s: None)
                return new in q2.tasks, os.path.exists(qp + ".torn.%d" % (len(json.dumps(first)) + 1))
            finally:
                durable.PLANT = saved_plant
        kept, aside = torn_trial("")
        kept_p, _a = torn_trial("queue-torn-in-memory")
        row("fix 3: a torn last line set aside and cut from the file, so the next task survives the next start (plant: the task lost)",
            kept and aside and not kept_p, "kept %s, the tear set aside %s; with the plant kept %s" % (kept, aside, kept_p))

        # 8. fix 4: a task the studio stopped under, whose answer was recorded: ready, nothing asked again
        rec0 = os.path.join(worlds, "harbor-day", "art", "build", "studio", "harbor-day", t["rid"])
        rid2 = "20991231T235959-9"
        shutil.copytree(rec0, os.path.join(os.path.dirname(rec0), rid2))

        def stopped_trial(plant):
            qp = os.path.join(tmp, "stopped-%s.jsonl" % (plant or "fixed"))
            task = dict(hub.queue._task(tid), id="t-1-000001", status="queued", rid="")
            open(qp, "wb").write((json.dumps({"e": "queued", "task": task}) + "\n" + json.dumps({"e": "started", "id": task["id"], "rid": rid2, "head": ""})
                                  + "\n").encode())
            durable.PLANT = plant
            try:
                return Queue(hub, qp, say=lambda s: None)
            finally:
                durable.PLANT = saved_plant
        q4 = stopped_trial("")
        t4 = q4._task("t-1-000001")
        g = hub.worlds["harbor-day"].studio
        n_asked = len([ln for ln in open(os.path.join(os.path.dirname(rec0), "requests.jsonl"), "rb").read().splitlines()])
        r4 = q4.review("t-1-000001")
        drawn = [c for c in g.req["candidates"] if c["slot"] is not None]
        q4p = stopped_trial("queue-forgets")
        row("fix 4: a task the studio stopped under, its answer recorded, is ready after the restart and reviewed without asking again "
            "(plant: interrupted, to be paid for again)", t4["status"] == "ready" and t4.get("recovered") and r4["drawn_again"]
            and len(drawn) >= 1 and all("HEAD-MOVED" in c["codes"] for c in drawn)
            and len(open(os.path.join(os.path.dirname(rec0), "requests.jsonl"), "rb").read().splitlines()) == n_asked
            and q4p._task("t-1-000001")["status"] == "interrupted",
            "%s (%s); drawn again: %d, each re-evaluated at the head as it is now; with the plant %s" % (
                t4["status"], t4["message"], len(drawn), q4p._task("t-1-000001")["status"]))
        # 0220: the same for an answer with no candidates: read again from its record, its disposition kept, nothing asked again
        rid3 = "20991231T235959-8"
        d3 = os.path.join(os.path.dirname(rec0), rid3)
        os.makedirs(d3, exist_ok=True)
        open(os.path.join(d3, "response.raw"), "wb").write(json.dumps({"format": "VERDANDI-STUDIO-RESPONSE", "version": "0", "id": rid3,
            "provider": {"name": "t", "model": "t"}, "candidates": [], "outcome": {"kind": "unsupported", "unmet": ["motion.path"], "questions": [],
                                                                                  "reason": "", "note": ""}}).encode())
        qp3 = os.path.join(tmp, "stopped-answered.jsonl")
        task3 = dict(hub.queue._task(tid), id="t-1-000002", status="queued", rid="")
        open(qp3, "wb").write((json.dumps({"e": "queued", "task": task3}) + "\n" + json.dumps({"e": "started", "id": task3["id"], "rid": rid3, "head": ""}) + "\n").encode())
        t5 = Queue(hub, qp3, say=lambda s: None)._task("t-1-000002")
        row("fix 4 for an answer with no candidates: after the restart the task is answered from its record (UNSUPPORTED motion.path), not asked again",
            t5["status"] == "answered" and (t5.get("disposition") or {}).get("unmet") == ["motion.path"] and t5.get("recovered"),
            "%s: %s" % (t5["status"], t5["message"][:100]))

        # 9. the queue kept across a restart
        q9 = Queue(hub, os.path.join(worlds, "queue.jsonl"), say=lambda s: None)
        row("the queue read back after a restart: every task as it stood", q9._task(tid)["status"] == "reviewed"
            and q9._task(r["id"])["status"] == "cancelled" and len(q9.tasks) == len(hub.queue.tasks),
            "%d tasks; %s reviewed, %s cancelled" % (len(q9.tasks), tid, r["id"]))
    except Exception as e:  # noqa: BLE001 — the self-test says what stopped it
        import traceback
        traceback.print_exc()
        row("the self-test ran to its end", False, "%s: %s" % (type(e).__name__, str(e)[:160]))
    finally:
        globals()["PROVIDERS_DIR"] = saved_dir
        durable.PLANT = saved_plant
        if hub is not None and hub.queue is not None:
            hub.queue.stop()
        if hub is not None:
            for w in list(hub.worlds.values()):
                w.stopping = True
                if w.studio:
                    w.studio.shutdown()
        if srv is not None:
            srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    print("STUDIO-2 SELFTEST %d/%d" % (sum(rows), len(rows)))
    return 0 if all(rows) else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["selftest"]:
        sys.exit(selftest())
    print("usage: python art/studio_queue.py selftest", file=sys.stderr)
    sys.exit(2)
