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
        if not isinstance(tid, str):
            raise studio.StudioError("STUDIO-QUEUE", "a task is named by its id, a string")       # HARDEN-0 (0232): a list was a 500
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
IMPORT_POINTS_STAGE = ("import:staged", "import:file-1", "import:copied", "import:verified", "import:checked", "import:genesis", "import:record")
IMPORT_POINTS_COMMIT = ("import:renamed", "import:logged")


def import_once(worlds_dir, source, name):
    """One import staged and committed in this process (the crash loop's child: VERDANDI_CRASH_AT ends it at a point)."""
    import play
    hub = play.Hub(worlds_dir=worlds_dir, watch=False, source=source, source_label="the scratch checkout", say=lambda s: None)
    st = hub.import_stage(name)
    hub.import_commit(st["staging"], st["record_sha256"])
    print("COMMITTED %s" % name)
    return 0


def seed_once(worlds_dir, source):
    """One first seeding in this process (the seeding's resume row: VERDANDI_CRASH_AT ends it between two briefs)."""
    import play
    print("SEEDED %s" % play.seed_worlds(worlds_dir, source=source, say=lambda s: None, source_label="the scratch checkout"))
    return 0


def import_rows(tmp, row, tree_bytes):
    """DASHBOARD-0 (0250): STUDIO-2's rows of the import (play.Hub.import_stage, import_commit, import_discard,
    recover_worlds, seed_worlds), in a worlds folder of their own seeded from a scratch checkout, and a source tree of
    their own whose briefs are made for each refusal. Every row's world and source are compared where the row says so:
    a source's comparison holds its files byte for byte and its content lock, which a recovery takes, by its absence."""
    import play
    import shutil
    import studio as S_
    S_quiet = lambda fn, *a, **k: S_.quiet(fn, *a, **k)
    import subprocess
    import threading
    D = play.director()
    LABEL = "the scratch checkout"
    src = os.path.join(tmp, "import-source")
    D.selftest_tree(src)                                    # plaza-night, its ledger started
    base = open(os.path.join(src, "art", "briefs", "plaza-night.art"), "rb").read().replace(b"\r\n", b"\n")
    slab = b"canopy plaza concrete_slab 7.0 19,10 28,11"

    def brief(name, text=base, ledger=False):
        p = os.path.join(src, "art", "briefs", name + ".art")
        with open(p, "wb") as fh:
            fh.write(text)
        if ledger:
            D.cmd_genesis_quiet(D.Workspace(name, src))
        return p

    def half_written(root, name):
        # an admission half written: its pending folder with a file in it (a recovery that ran removes it, and is seen)
        p = os.path.join(root, "art", "ledger", name + ".ledger.pending")
        os.makedirs(p)
        with open(os.path.join(p, "old.0"), "wb") as fh:
            fh.write(b"prepared, never committed")
    for n in ("plaza-east", "plaza-west", "plaza-meet", "plaza-crash", "plaza-q", "plaza-moved", "plaza-fail", "plaza-change", "plaza-extra", "plaza-ledg",
              "plaza-logless", "plaza-gone", "plaza-busy", "plaza-build"):
        brief(n)
    brief("plaza-busyled", ledger=True)
    brief("plaza-empty")
    open(os.path.join(src, "art", "ledger", "plaza-empty.ledger"), "wb").close()        # a ledger of no line
    brief("plaza-led", ledger=True)
    brief("plaza-pend", ledger=True)
    half_written(src, "plaza-pend")
    brief("plaza-unl", ledger=True)
    with open(os.path.join(src, "art", "briefs", "plaza-unl.art"), "ab") as fh:
        fh.write(b"# a hand edit, not recorded\n")
    # 0254 (the frozen matrix's IM1): a source whose ledger holds a forged positioned inverse (OU7's): an admission by the
    # command line, its stored '@=' inverse's restored row altered and the chain rehashed from it on
    brief("plaza-forged", ledger=True)
    wf = D.Workspace("plaza-forged", src)
    _pf = D.current_parts(wf)
    with open(os.path.join(src, "forged.intent"), "wb") as fh:
        fh.write(D.canon.dumps({"base": {k: _pf[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}, "brief": "plaza-forged",
                                "candidate": "F", "format": "VERDANDI-INTENT", "layout": [], "prompt": "0254's IM1", "rationale": "an admission",
                                "revision": ["= lamp north-lane 255,170,90 500 4"], "scope": ["**", "env/**"], "version": "0"}))
    _r = S_quiet(D.cmd_evaluate, wf, [os.path.join(src, "forged.intent")], quiet=True)[0]
    _af = S_quiet(D.cmd_admit_still, wf, _r[4])
    os.remove(os.path.join(src, "forged.intent"))
    _evs = D.led.read(wf.ledger)[0]
    _f, _v = D.canon.inverse_form(_evs[int(_af["seq"])]["inverse"][0])
    _evs[int(_af["seq"])] = dict(_evs[int(_af["seq"])], inverse=[D.canon.inverse_line(_f, [_v[0], _v[1], _v[2].replace(" 600 ", " 650 ")])])
    _prev, _lines = D.led.ZERO, []
    for _e in _evs:
        _b = D.canon.dumps(dict(_e, prev=_prev))
        _lines.append(_b)
        _prev = D.canon.sha256(_b)
    with open(wf.ledger, "wb") as fh:
        fh.write(b"".join(x + b"\n" for x in _lines))
    assert base.count(slab) == 1
    brief("plaza-low", base.replace(slab, b"canopy plaza concrete_slab 3.0 19,10 28,11"))      # a slab the art checks refuse
    brief("plaza-bad", base + b"bogus_statement x\n")                                       # a statement the exporter refuses
    src_lock = os.path.join(src, "art", "build", "content.lock")
    if os.path.exists(src_lock):
        os.remove(src_lock)                                 # the fixture's geneses took it; a lock taken again leaves it
    worlds = os.path.join(tmp, "worlds-import")
    os.makedirs(worlds)
    D.selftest_tree(os.path.join(tmp, "import-seed"))
    play.seed_worlds(worlds, source=os.path.join(tmp, "import-seed"), say=lambda s: None, source_label=LABEL)
    hub = play.Hub(worlds_dir=worlds, watch=False, source=src, source_label=LABEL, say=lambda s: None)
    aside = lambda: sorted(n for n in os.listdir(worlds) if play.ASIDE.match(n))

    def post(op, body, h=None):
        return play.studio_post(h or hub, "/studio/worlds/import/" + op, body)

    def refused(op, body, h=None):
        c, a = post(op, body, h)
        return a.get("code", "") if c != 200 else "accepted"

    def log_names():
        p = os.path.join(worlds, "IMPORTS.jsonl")
        return [json.loads(ln)["name"] for ln in open(p, "rb").read().splitlines() if ln.strip()] if os.path.isfile(p) else []
    night = tree_bytes(os.path.join(worlds, "plaza-night"))
    src_before = tree_bytes(src)

    # the routes the page reads: the worlds read back and the briefs to import, the source by its label alone
    c1, wj = play.worlds_get(hub, "/worlds.json", {})
    c2, ij = play.worlds_get(hub, "/importable.json", {})
    insp = hub.inspect("plaza-night")
    c4, oj = play.worlds_get(hub, "/outline.json", {"world": "plaza-night", "slot": "0"})
    c5, on = play.worlds_get(hub, "/outline.json", {"slot": "0"})
    wrow = {w["world"]: w for w in wj.get("worlds", [])}
    names_i = [b["name"] for b in ij.get("briefs", [])]
    pn = next((b for b in ij.get("briefs", []) if b["name"] == "plaza-led"), {})
    real_listdir = os.listdir
    briefs_dir = os.path.join(src, "art", "briefs")

    def unlistable(p="."):
        if os.path.abspath(p) == os.path.abspath(briefs_dir):
            raise PermissionError(13, "Permission denied", p)
        return real_listdir(p)
    os.listdir = unlistable
    try:
        c8, iu = play.worlds_get(hub, "/importable.json", {})
    finally:
        os.listdir = real_listdir
    row("import: a source whose briefs cannot be listed is refused by /importable.json (ok false, IMPORT-SOURCE-UNREAD), named by its label, "
        "its path in no part of the answer", iu.get("ok") is False and iu.get("code") == "IMPORT-SOURCE-UNREAD" and LABEL in iu.get("message", "")
        and not iu.get("briefs") and not any(v in json.dumps(iu) for v in (src, json.dumps(src)[1:-1], src.replace(os.sep, "/"))),
        "%s ok %s %s: %s" % (c8, iu.get("ok"), iu.get("code"), iu.get("message", "")[:80]))
    row("import: /worlds.json is each world as Hub.inspect reads it back, and /importable.json each brief of the source that is no world here, "
        "with its files' sha256 and its ledger, the source named by its label alone (its absolute path in no answer); /outline.json opens no world",
        c1 == 200 and c2 == 200 and wrow.get("plaza-night", {}).get("head") == insp["head"] and wrow["plaza-night"]["state"] == "verified"
        and wrow["plaza-night"]["events"] == insp["events"] and "plaza-night" not in names_i and "plaza-east" in names_i
        and pn.get("ledger", {}).get("events") == 1 and all(f["sha256"] == play.sha256(open(os.path.join(src, f["path"]), "rb").read()) for f in pn.get("files", []))
        and ij.get("source_label") == LABEL and not any(v in json.dumps([wj, ij]) for v in (src, json.dumps(src)[1:-1], src.replace(os.sep, "/")))
        and c4 == 404 and oj.get("code") == "STUDIO-WORLD" and c5 == 404 and on.get("code") == "STUDIO-WORLD" and not hub.worlds,
        "plaza-night %s, %s events; importable %s; /outline.json of a world not open %s %s, with no world %s %s (no world opened)" % (
            wrow.get("plaza-night", {}).get("state"), wrow.get("plaza-night", {}).get("events"), ", ".join(names_i), c4, oj.get("code"), c5, on.get("code")))

    # stage, then commit: an isolated candidate, never listed until one rename puts it in place
    c, st = post("stage", {"name": "plaza-east"})
    staged = st.get("staging", "")
    listed_while = "plaza-east" in hub.names()
    rec_sha = play.sha256(open(os.path.join(worlds, staged, "IMPORTED.json"), "rb").read()) if staged and os.path.isdir(os.path.join(worlds, staged)) else ""
    c3, cm = post("commit", {"staging": staged, "record_sha256": st.get("record_sha256")})
    info = hub.inspect("plaza-east") if "plaza-east" in hub.names() else {}
    row("import: staged as an isolated candidate (a folder of its own, not listed), then committed by one rename: the world listed, verified, "
        "its ledger started at import (one event, its bytes in the record), its line in IMPORTS.jsonl; the other worlds and the source as before",
        c == 200 and staged.startswith(".import-plaza-east-") and not listed_while and rec_sha == st.get("record_sha256") and c3 == 200
        and cm.get("world") == "plaza-east" and cm.get("logged") is True and info.get("verified") and info.get("events") == 1 and not aside()
        and st.get("record", {}).get("ledger", {}).get("started_at_import") == info.get("head") and len(st.get("record", {}).get("ledger", {}).get("sha256", "")) == 64
        and log_names() == ["plaza-east"] and "source" not in st.get("record", {}) and tree_bytes(os.path.join(worlds, "plaza-night")) == night
        and tree_bytes(src) == src_before and not os.path.exists(src_lock),
        "staged %s (listed %s); committed %s; %s events, verified %s; log %s" % (staged, listed_while, cm.get("world", cm.get("code")), info.get("events"),
                                                                                info.get("verified"), log_names()))

    # refused before anything is copied: a world of the name, or an empty folder of the name
    os.makedirs(os.path.join(worlds, "plaza-west"))
    e1, e2 = refused("stage", {"name": "plaza-night"}), refused("stage", {"name": "plaza-west"})
    row("import: IMPORT-EXISTS for the name of a world, and for an empty folder of that name; nothing staged",
        e1 == e2 == "IMPORT-EXISTS" and not aside(), "plaza-night %s; an empty plaza-west %s; aside %s" % (e1, e2, aside()))
    os.rmdir(os.path.join(worlds, "plaza-west"))

    def pending_case():
        before = tree_bytes(src)
        got = refused("stage", {"name": "plaza-pend"})
        locked = os.path.exists(src_lock)
        if locked:
            os.remove(src_lock)
        return got, tree_bytes(src) == before and not locked
    got, same = pending_case()
    row("import: a source holding an admission half written is refused (IMPORT-SOURCE-PENDING), nothing of the source recovered, locked or "
        "written: its files byte for byte as before, its content lock not taken", got == "IMPORT-SOURCE-PENDING" and same and not aside(),
        "%s; the source the same and not locked %s" % (got, same))
    c, a = post("stage", {"name": "plaza-unl"})
    row("import: a ledger that does not verify in the copy is refused (IMPORT-LEDGER, the director's UNLOGGED-CHANGE); nothing staged",
        a.get("code") == "IMPORT-LEDGER" and a.get("director_code") == "UNLOGGED-CHANGE" and a.get("source_label") == LABEL and a.get("name") == "plaza-unl"
        and not aside(), "%s (%s): %s" % (a.get("code"), a.get("director_code"), a.get("message", "")[:80]))
    c, a = post("stage", {"name": "plaza-forged"})
    row("import: a source whose ledger holds a forged positioned inverse is refused IMPORT-LEDGER carrying LEDGER-INVERSE, the staging removed",
        a.get("code") == "IMPORT-LEDGER" and a.get("director_code") == "LEDGER-INVERSE" and a.get("name") == "plaza-forged" and not aside()
        and "plaza-forged" not in hub.names(), "%s (%s): %s; aside %s" % (a.get("code"), a.get("director_code"), a.get("message", "")[:100], aside()))
    c, a = post("stage", {"name": "plaza-low"})
    row("import: a brief the art checks refuse is refused (IMPORT-CHECKS, the checks named); nothing staged",
        a.get("code") == "IMPORT-CHECKS" and "no dressing where a player can be" in a.get("message", "") and not aside(),
        "%s: %s" % (a.get("code"), a.get("message", "")[:120]))
    c, a = post("stage", {"name": "plaza-led"})
    ok_led = c == 200 and a.get("record", {}).get("ledger", {}).get("copied") is True and a.get("record", {}).get("ledger", {}).get("events") == 1
    post("discard", {"staging": a.get("staging", "")})
    row("import: a brief with a ledger is staged with its ledger copied and verified in the copy; discarded, nothing left",
        ok_led and not aside() and "plaza-led" not in hub.names(), "ledger %s; aside %s" % (a.get("record", {}).get("ledger"), aside()))

    # the codes no other row reaches: not in worlds mode, no such brief, the exporter's refusal, a staging gone, the lock held
    one = play.Hub(watch=False, say=lambda s: None)
    m_mode = refused("stage", {"name": "plaza-east"}, one)
    m_name = refused("stage", {"name": "no-such-brief"})
    m_art = refused("stage", {"name": "plaza-bad"})
    _c, g_ = post("stage", {"name": "plaza-gone"})
    post("discard", {"staging": g_.get("staging", "")})
    m_gone = refused("commit", {"staging": g_.get("staging", ""), "record_sha256": g_.get("record_sha256")})
    held, free = threading.Event(), threading.Event()

    def holder():
        with play.worlds_locked(worlds):
            held.set()
            free.wait(30)
    th = threading.Thread(target=holder)
    th.start()
    held.wait(10)
    try:
        m_busy = refused("stage", {"name": "plaza-busy"})
    finally:
        free.set()
        th.join(30)
    row("import: the other refusals — not a worlds folder (IMPORT-MODE), no such brief (IMPORT-NAME), the exporter refusing it (IMPORT-ART), "
        "a staging discarded before its commit (IMPORT-STAGE-GONE), the worlds folder's lock held (IMPORT-BUSY); nothing staged",
        (m_mode, m_name, m_art, m_gone, m_busy) == ("IMPORT-MODE", "IMPORT-NAME", "IMPORT-ART", "IMPORT-STAGE-GONE", "IMPORT-BUSY") and not aside()
        and "plaza-busy" not in hub.names(), "%s, %s, %s, %s, %s" % (m_mode, m_name, m_art, m_gone, m_busy))

    def failing_case():
        def boom(name):
            if name == "import:file-2":
                raise RuntimeError("planted: the import stopped at its second file")
        names0 = hub.names()
        D.durable.HOOK = boom
        try:
            c_, a_ = post("stage", {"name": "plaza-fail"})
        finally:
            D.durable.HOOK = None
        return a_, hub.names() == names0
    a, same_list = failing_case()
    row("import: case 6, an import that fails partway (at its second file) — IMPORT-FAILED with the source and the name; no staging by a listing "
        "of the folder; the listing as before", a.get("code") == "IMPORT-FAILED" and a.get("name") == "plaza-fail" and a.get("source_label") == LABEL
        and not aside() and same_list, "%s: %s; aside %s" % (a.get("code"), a.get("message", "")[:80], aside()))

    def moved_case(name="plaza-moved", what="art/briefs/plaza-moved.art", at="import:file-1"):
        # the file written once it has been copied (the brief is the first file copied, the ledger the second)
        p = os.path.join(src, *what.split("/"))
        keep = open(p, "rb").read()

        def touch(point):
            if point == at:
                with open(p, "ab") as fh:
                    fh.write(b"# written while it was copied\n")
        D.durable.HOOK = touch
        try:
            return refused("stage", {"name": name})
        finally:
            D.durable.HOOK = None
            open(p, "wb").write(keep)
    got = moved_case()
    got_led = moved_case("plaza-busyled", "art/ledger/plaza-busyled.ledger", "import:file-2")
    row("import: a source changed while it was copied is refused — its brief (IMPORT-SOURCE-MOVED), its ledger written (the source busy: "
        "IMPORT-SOURCE-BUSY); nothing staged", got == "IMPORT-SOURCE-MOVED" and got_led == "IMPORT-SOURCE-BUSY" and not aside(), "%s; %s" % (got, got_led))

    def changed_case(name="plaza-change", how="brief"):
        c_, s_ = post("stage", {"name": name})
        stg = os.path.join(worlds, s_.get("staging", "") or "-")
        if how == "brief":                                  # a staged file of the record changed
            with open(os.path.join(stg, "art", "briefs", name + ".art"), "ab") as fh:
                fh.write(b"# changed after the stage\n")
        elif how == "build":                                # a file of the build folder that is not its content lock
            os.makedirs(os.path.join(stg, "art", "build", "studio", name))
            with open(os.path.join(stg, "art", "build", "studio", name, "requests.jsonl"), "wb") as fh:
                fh.write(b"{}\n")
        elif how == "ledger":                               # the ledger started at the stage given another valid line
            D.led.append(os.path.join(stg, "art", "ledger", name + ".ledger"), "refuse_input",
                         {"code": "PLANTED", "detail": "a line added after the stage", "observed": {"at": "2026-10-18T00:00:00Z"}})
        else:                                               # a file the record does not name
            with open(os.path.join(stg, "art", "ledger", name + ".tags.json"), "wb") as fh:
                fh.write(b"{}\n")
        got_ = refused("commit", {"staging": s_.get("staging", ""), "record_sha256": s_.get("record_sha256")})
        kept = os.path.isdir(stg)
        listed = name in hub.names()
        if listed:                                           # the plant put it in place: taken away again for the next rows
            D.durable.remove_tree(os.path.join(worlds, name))
        dis = refused("discard", {"staging": s_.get("staging", "")}) if kept else "nothing to discard"
        return got_, kept, listed, dis
    outs = [changed_case(n, h) for n, h in (("plaza-change", "brief"), ("plaza-ledg", "ledger"), ("plaza-extra", "extra"), ("plaza-build", "build"))]
    row("import: a staging changed before its commit is refused (IMPORT-STAGE-CHANGED), nothing put in place, the staging kept, then discarded "
        "to nothing — a file of its record changed, the ledger started at the stage given another valid line, a file its record does not name, "
        "a file of its build folder that is not its content lock",
        all(o_[0] == "IMPORT-STAGE-CHANGED" and o_[1] and not o_[2] and o_[3] == "accepted" for o_ in outs) and not aside(),
        "; ".join("%s: %s, kept %s, listed %s, discard %s" % (h, *o_) for h, o_ in zip(("a file of the record", "the started ledger", "a file not named",
                                                                                         "a build file"), outs)))

    def meeting_case():
        a1 = post("stage", {"name": "plaza-meet"})[1]
        a2 = post("stage", {"name": "plaza-meet"})[1]
        bar, out = threading.Barrier(2), {}

        def commit(k, s_):
            bar.wait()
            out[k] = refused("commit", {"staging": s_.get("staging", ""), "record_sha256": s_.get("record_sha256")})
        th_ = [threading.Thread(target=commit, args=(k, s_)) for k, s_ in (("a", a1), ("b", a2))]
        for t_ in th_:
            t_.start()
        for t_ in th_:
            t_.join(60)
        worlds_of = [n for n in os.listdir(worlds) if n == "plaza-meet"]
        left = {k: os.path.isdir(os.path.join(worlds, s_.get("staging", "") or "-")) for k, s_ in (("a", a1), ("b", a2))}
        loser = [k for k in ("a", "b") if out.get(k) != "accepted"]
        kept_ok = len(loser) == 1 and left[loser[0]] and not left["b" if loser[0] == "a" else "a"]
        dis = refused("discard", {"staging": (a1 if loser and loser[0] == "a" else a2).get("staging", "")}) if loser and left.get(loser[0]) else "nothing to discard"
        for s_ in (a1, a2):
            if os.path.isdir(os.path.join(worlds, s_.get("staging", "") or "-")):
                post("discard", {"staging": s_["staging"]})
        return sorted(out.values(), key=lambda v: v != "accepted"), worlds_of, kept_ok, dis
    outs, wl, kept_ok, dis = meeting_case()
    row("import: two staged imports of one name committed at once — one world, the other IMPORT-EXISTS (or IMPORT-BUSY), its staging kept "
        "and then discarded, the winner's gone",
        len(wl) == 1 and outs[0] == "accepted" and outs[1] in ("IMPORT-EXISTS", "IMPORT-BUSY") and kept_ok and dis == "accepted" and not aside()
        and hub.inspect("plaza-meet").get("verified"), "the commits: %s; worlds of the name %d; the loser's staging kept %s, discard %s" % (outs, len(wl), kept_ok, dis))

    # the commit point: a log that cannot be written is said, the commit answered as made, and the next start writes the line
    log = os.path.join(worlds, "IMPORTS.jsonl")
    log_keep = open(log, "rb").read()
    os.remove(log)
    os.makedirs(log)                                        # a log that cannot be written (a folder of its name)
    try:
        c, s_ = post("stage", {"name": "plaza-logless"})
        c6, cm6 = post("commit", {"staging": s_.get("staging", ""), "record_sha256": s_.get("record_sha256")})
    finally:
        os.rmdir(log)
        D.durable.write(log, log_keep)
    lines6 = play.recover_worlds(worlds, say=lambda s: None)
    row("import: a commit whose imports log cannot be written is answered committed (logged false, why said), the world in place; the next "
        "start's recovery writes its line from the world's own record", c6 == 200 and cm6.get("world") == "plaza-logless" and cm6.get("logged") is False
        and "next start" in cm6.get("note", "") and "plaza-logless" in hub.names() and log_names().count("plaza-logless") == 1
        and any("plaza-logless" in ln for ln in lines6), "%s logged %s (%s); recovery: %s" % (c6, cm6.get("logged"), cm6.get("note", "")[:60], lines6))

    # a duplicate under the worlds folder's lock: refused while another writer holds it, made once it is free
    held, free = threading.Event(), threading.Event()
    t = threading.Thread(target=holder)
    t.start()
    held.wait(10)
    try:
        hub.duplicate("plaza-night", "plaza-dup")
        busy = "made"
    except S_.StudioError as e:
        busy = e.code + ": " + e.detail[:60]
    free.set()
    t.join(30)
    hub.duplicate("plaza-night", "plaza-dup")
    for w in list(hub.worlds.values()):
        w.stopping = True
        if w.studio:
            w.studio.shutdown()
    row("import: a duplicate takes the worlds folder's lock: refused while another writer holds it, made once it is free, nothing left aside",
        "being written" in busy and "plaza-dup" in hub.names() and not aside(), "while held: %s; then %s" % (busy, "made" if "plaza-dup" in hub.names() else "not made"))

    # a ledger of no line (a first line that did not finish, set aside): said, and started again when its world is opened;
    # in a source, refused by its name
    east_led = os.path.join(worlds, "plaza-east", "art", "ledger", "plaza-east.ledger")
    keep_led = open(east_led, "rb").read()
    open(east_led, "wb").close()
    _c, wj2 = play.worlds_get(hub, "/worlds.json", {})
    erow = {w["world"]: w for w in wj2.get("worlds", [])}.get("plaza-east", {})
    try:
        hub.world("plaza-east")
        reopened = hub.inspect("plaza-east")
    finally:
        for w in list(hub.worlds.values()):
            w.stopping = True
            if w.studio:
                w.studio.shutdown()
        hub.worlds.clear()
    c7, a7 = post("stage", {"name": "plaza-empty"})
    row("import: a ledger of no line is said (LEDGER-EMPTY, not verified) and started again when its world is opened (one event, verified); a "
        "source's is refused (IMPORT-LEDGER, LEDGER-EMPTY), nothing staged", erow.get("code") == "LEDGER-EMPTY" and erow.get("state") == "not-verified"
        and reopened.get("verified") and reopened.get("events") == 1 and a7.get("code") == "IMPORT-LEDGER" and a7.get("director_code") == "LEDGER-EMPTY"
        and not aside(), "the row %s %s; opened: verified %s, %s events; the source's %s (%s)" % (erow.get("state"), erow.get("code"), reopened.get("verified"),
                                                                                                     reopened.get("events"), a7.get("code"), a7.get("director_code")))
    del keep_led

    # an import's genesis and a command inside quiet() meeting, the genesis paused inside its own console swap when it can
    # enter it: with QUIET_LOCK it cannot until the command's quiet() has ended, and the console is the console after; the
    # plant (the genesis's swap without the lock) puts the command's buffer back as the console
    def quiet_case():
        saved_out = sys.stdout
        at, go_on, in_gen, returned = threading.Event(), threading.Event(), threading.Event(), threading.Event()

        def pause(name):
            if name == "import:checked":
                at.set()
                go_on.wait(30)
            elif name == "ledger:genesis":
                in_gen.set()
                returned.wait(30)
        D.durable.HOOK = pause
        res = {}
        th_ = threading.Thread(target=lambda: res.setdefault("r", post("stage", {"name": "plaza-q"})))
        th_.start()
        try:
            at.wait(30)

            def inside():
                go_on.set()
                in_gen.wait(2)                               # the genesis inside its swap now, unless the lock holds it out
                print("inside quiet()")
                return "done"
            q = S_.quiet(inside)
            returned.set()
            th_.join(60)
        finally:
            D.durable.HOOK = None
        restored = sys.stdout is saved_out
        sys.stdout = saved_out
        r = res.get("r") or (0, {})
        if r[0] == 200:
            post("discard", {"staging": r[1].get("staging", "")})
        return q, r, restored
    q, r, restored = quiet_case()
    row("import: an import's genesis and a command inside quiet() meeting, the genesis paused inside its own console swap: both end, and the "
        "console is the console after (QUIET_LOCK holds the genesis out until the command's quiet() ends)",
        q == "done" and r[0] == 200 and r[1].get("record", {}).get("ledger", {}).get("started_at_import") and restored and not aside(),
        "quiet() %s; the stage %s; the console restored %s" % (q, r[0], restored))

    # the crash loop: a process ended at each point of the stage and the commit, then the start's recovery
    crash = []
    for point in IMPORT_POINTS_STAGE + IMPORT_POINTS_COMMIT:
        others = {n: tree_bytes(os.path.join(worlds, n)) for n in hub.names()}
        env = dict(os.environ, VERDANDI_CRASH_AT=point, PYTHONHASHSEED="0")
        cp = subprocess.run([sys.executable, "-B", os.path.join(HERE, "studio_queue.py"), "import-once", worlds, src, "plaza-crash"],
                            capture_output=True, env=env, timeout=300)
        lines = play.recover_worlds(worlds, say=lambda s: None)
        listed = "plaza-crash" in hub.names()
        mine = [json.loads(ln) for ln in open(log, "rb").read().splitlines() if ln.strip() and json.loads(ln)["name"] == "plaza-crash"]
        if point in IMPORT_POINTS_STAGE:
            ok = cp.returncode == 77 and not listed and not aside() and not mine
        else:
            ok = (cp.returncode == 77 and listed and hub.inspect("plaza-crash").get("verified") and len(mine) == 1 and not aside()
                  and mine[0]["recovered"] is (point == "import:renamed"))
        ok = ok and all(tree_bytes(os.path.join(worlds, n)) == b for n, b in others.items() if n != "plaza-crash")
        crash.append((point, ok, cp.returncode, listed, len(mine), len(lines)))
        if listed:
            D.durable.remove_tree(os.path.join(worlds, "plaza-crash"))
            keep = [ln for ln in open(log, "rb").read().splitlines() if ln.strip() and json.loads(ln)["name"] != "plaza-crash"]
            D.durable.write(log, b"".join(ln + b"\n" for ln in keep))
    row("import: the crash loop — a process ended at each of %d points of the stage and the commit, then the start's recovery: before the rename "
        "nothing listed and nothing left aside; after it the world listed and verified with its one line in the log (restored from its record "
        "when the process ended before the log); every other world byte for byte as before" % len(crash), all(c_[1] for c_ in crash),
        "; ".join("%s %s (exit %s, listed %s, lines %s)" % (p_, "ok" if o_ else "WRONG", rc_, l_, m_) for p_, o_, rc_, l_, m_, _n in crash))

    # recovery: a duplicate's and a seeding's folders made aside removed, named by their literal paths (not by the rule they
    # test); an imports log that cannot be read and a record that is not one said, the start not ended
    others = {n: tree_bytes(os.path.join(worlds, n)) for n in hub.names()}
    dup_aside, seed_aside = os.path.join(worlds, ".dup-plaza-x-0000abcd"), os.path.join(worlds, "plaza-x.making")
    os.makedirs(os.path.join(dup_aside, "art"))
    os.makedirs(os.path.join(seed_aside, "art"))
    lines8 = play.recover_worlds(worlds, say=lambda s: None)
    rec_east = os.path.join(worlds, "plaza-east", "IMPORTED.json")
    keep_rec, keep_log = open(rec_east, "rb").read(), open(log, "rb").read()
    open(rec_east, "wb").write(b"[]\n")
    try:
        lines9 = play.recover_worlds(worlds, say=lambda s: None)                         # a record that is not one
        os.remove(log)
        os.makedirs(log)
        lines10 = play.recover_worlds(worlds, say=lambda s: None)                        # a log that cannot be read
        raised = ""
    except Exception as e:  # noqa: BLE001 — the row's own failure: recovery raised
        raised = "%s: %s" % (type(e).__name__, str(e)[:80])
        lines9 = lines10 = []
    finally:
        if os.path.isdir(log):
            os.rmdir(log)
        D.durable.write(log, keep_log)
        D.durable.write(rec_east, keep_rec)
    row("recovery: a duplicate's and a seeding's folders made aside removed (by their names, each said); an imports log that cannot be read and a "
        "record that is not one said, the start not ended; every world byte for byte as before",
        not os.path.exists(dup_aside) and not os.path.exists(seed_aside) and sum(1 for ln in lines8 if "removed" in ln) == 2 and not raised
        and any("COULD NOT READ the imports log" in ln for ln in lines10) and any("import record of plaza-east" in ln for ln in lines9)
        and all(tree_bytes(os.path.join(worlds, n)) == b for n, b in others.items()),
        "removed: %s; a record []: %s; a log not read: %s%s" % (lines8, lines9, lines10[:1], "; raised " + raised if raised else ""))

    # the first seeding: a checkout brief holding an admission half written is refused, and nothing of the checkout written
    def seeding_pending_case():
        w3 = os.path.join(tmp, "worlds-pending-%d" % len(os.listdir(tmp)))
        seed_src = os.path.join(tmp, "seed-pending-%d" % len(os.listdir(tmp)))
        D.selftest_tree(seed_src)
        half_written(seed_src, "plaza-night")
        lock = os.path.join(seed_src, "art", "build", "content.lock")
        if os.path.exists(lock):
            os.remove(lock)
        sb = tree_bytes(seed_src)
        made3 = play.seed_worlds(w3, source=seed_src, say=lambda s: None, source_label=LABEL)
        refusal = json.load(open(os.path.join(w3, "SEEDED.json")))["worlds"].get("plaza-night", {}).get("refused", "")
        return made3, refusal, tree_bytes(seed_src) == sb and not os.path.exists(lock), [n for n in os.listdir(w3) if play.ASIDE.match(n)]
    made3, refusal, same3, left3 = seeding_pending_case()
    row("seeding: a checkout brief holding an admission half written is not made a world (IMPORT-SOURCE-PENDING) and the checkout is not recovered: "
        "its files byte for byte as before, its content lock not taken (before 0250 seeding recovered it, and so wrote it)",
        made3 == [] and refusal.startswith("IMPORT-SOURCE-PENDING") and same3 and not left3, refusal[:120])

    # the first seeding cut off between two briefs is finished at the next start, never left part-made in silence
    def seeding_resume_case():
        w4 = os.path.join(tmp, "worlds-resume-%d" % len(os.listdir(tmp)))
        s4 = os.path.join(tmp, "seed-two-%d" % len(os.listdir(tmp)))
        D.selftest_tree(s4)
        shutil.copy(os.path.join(REPO, "art", "briefs", "harbor-day.art"), os.path.join(s4, "art", "briefs", "harbor-day.art"))
        env = dict(os.environ, VERDANDI_CRASH_AT="seed:placed-1", PYTHONHASHSEED="0")
        cp = subprocess.run([sys.executable, "-B", os.path.join(HERE, "studio_queue.py"), "seed-once", w4, s4], capture_output=True, env=env, timeout=300)
        part = play.Hub(worlds_dir=w4).names()
        lines4 = play.recover_worlds(w4, say=lambda s: None)
        made4 = play.seed_worlds(w4, source=s4, say=lambda s: None, source_label=LABEL)
        seeded = json.load(open(os.path.join(w4, "SEEDED.json")))["worlds"] if os.path.exists(os.path.join(w4, "SEEDED.json")) else {}
        return cp.returncode, part, lines4, made4, seeded, play.Hub(worlds_dir=w4).names()
    rc4, part, lines4, made4, seeded4, names4 = seeding_resume_case()
    row("seeding: a first seeding ended between two briefs (one world made, no SEEDED.json) is said at the next start and finished there: every "
        "brief a world, SEEDED.json listing both", rc4 == 77 and part == ["harbor-day"] and any("ended part-way" in ln for ln in lines4)
        and made4 == ["plaza-night"] and names4 == ["harbor-day", "plaza-night"] and sorted(seeded4) == ["harbor-day", "plaza-night"]
        and "resumed" in seeded4.get("harbor-day", {}), "cut off: exit %s, made %s; recovery %s; then made %s; worlds %s" % (rc4, part, lines4, made4, names4))

    # the plants: each a defect of the import, caught by the row it breaks (its scenario run again, from where it began)
    D.durable.remove_tree(os.path.join(worlds, "plaza-meet"))
    caught = {}
    for plant in play.IMPORT_PLANTS:
        play.IMPORT_PLANT = plant
        try:
            if plant == "import-recover-source":
                got, same = pending_case()
                caught[plant] = (got != "IMPORT-SOURCE-PENDING" or not same, "%s; the source the same and not locked %s" % (got, same))
                # the row's byte and lock half catches it too, not its code alone
                caught[plant] = (caught[plant][0] and not same, caught[plant][1])
            elif plant == "import-keep-staging":
                a, _same = failing_case()
                caught[plant] = (bool(aside()) or a.get("code") != "IMPORT-FAILED", "%s; aside %s" % (a.get("code"), aside()))
            elif plant == "import-rename-first":
                got, kept, listed, dis = changed_case()
                caught[plant] = (listed or not kept, "%s; kept %s; listed %s" % (got, kept, listed))
            elif plant == "import-no-exists-check":
                outs, wl, kept_ok, dis = meeting_case()
                caught[plant] = (not (outs[1] in ("IMPORT-EXISTS", "IMPORT-BUSY")), "the commits: %s" % outs)
                D.durable.remove_tree(os.path.join(worlds, "plaza-meet"))
            elif plant == "import-quiet-unlocked":
                q, r, restored = quiet_case()
                caught[plant] = (r[0] == 200 and not restored, "the stage %s; the console restored %s" % (r[0], restored))
            elif plant == "seed-names-guard":
                rc4, part, lines4, made4, seeded4, names4 = seeding_resume_case()
                caught[plant] = (names4 != ["harbor-day", "plaza-night"], "after the cut: made %s; worlds %s" % (made4, names4))
        except Exception as e:  # noqa: BLE001 — a plant whose scenario raises is said, and not counted caught
            caught[plant] = (False, "raised %s: %s" % (type(e).__name__, str(e)[:80]))
        finally:
            play.IMPORT_PLANT = ""
            for n in aside():
                D.durable.remove_tree(os.path.join(worlds, n))
    for plant in play.IMPORT_PLANTS:
        ok, detail = caught.get(plant, (False, "not run"))
        row("import plant %s caught" % plant, ok is True, detail)


def selftest():
    """STUDIO-2 end to end, off the gate, in a scratch folder: the worlds folder seeded from a checkout of its own (the
    fixture's plaza with a ledger and tags, and harbor-day), a checkout whose ledger does not verify refused; the worlds
    served, each read by name, each from its own tree; a request queued for one world while the page plays the other,
    run, reviewed and admitted there, the other world's bytes untouched; a world duplicated with maps of its own; at
    most two requests at once and one per world; the studio busy while work waits; two worlds compiled at once over
    different maps; and fixes 3 and 4 of 2026-10-13 with their plants (a torn tail cut durably; a task the studio
    stopped under, whose answer was recorded, ready without asking again); and the import, transactional (DASHBOARD-0,
    0250: import_rows), with its crash loop and its six plants."""
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
            and seeded["worlds"]["plaza-night"]["ledger_events"] == "2" and not os.path.exists(os.path.join(worlds, "harbor-day", "art", "ledger"))
            and not [n for n in os.listdir(worlds) if play.ASIDE.match(n)],
            "; ".join(said)[:200])
        again = play.seed_worlds(worlds, source=src, say=said.append)
        row("seeded once: a folder that holds worlds is not seeded again", again == [] and json.load(open(os.path.join(worlds, "SEEDED.json"))) == seeded, "made %s" % again)
        bad = checkout("checkout-unlogged", edit_recorded=False)
        w2, said2 = os.path.join(tmp, "worlds-2"), []
        made2 = play.seed_worlds(w2, source=bad, say=said2.append)
        row("a checkout brief whose ledger does not verify is not made a world, and why is said; nothing of it left", made2 == ["harbor-day"]
            and not os.path.exists(os.path.join(w2, "plaza-night")) and not [n for n in os.listdir(w2) if play.ASIDE.match(n)]
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
        # ADMISSION-0 (0222): the still the page takes of the candidate as drawn, given with the studio's token; BINDING-0
        # (0253): it declares the scene it is of, as the page's does (the candidate's, as harbor-day's host names it)
        qs = urllib.request.Request(base + "/studio/still?world=harbor-day&id=%s&candidate=A&scene=%s" % (
            t["rid"], play.declared_scene(hub.worlds["harbor-day"].studio, t["rid"], "A")), data=D.selftest_still(), method="POST",
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
        # the scheduler stopped and gone before the task is added, so that it is still queued when cancelled (added first, it
        # was started before the stop 1 run in 2 under load: OBSERVED at 0236, "running" where "cancelled" was meant)
        hub.queue.stop()
        if hub.queue.thread is not None:
            hub.queue.thread.join(30)
        c, r = post("/studio/queue/add", {"world": "plaza-copy", "prompt": "one to cancel", "provider": "slow.json"})
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
            wrong, count_lock = [0], threading.Lock()
            durable.PLANT = plant

            def one(m):
                for _i in range(12):
                    try:
                        bad = play.compile_scene("plaza-night", art, m)[1] != want[m]
                    except (SystemExit, ValueError, OSError):           # the converter read the other world's maps
                        bad = True
                    with count_lock:            # 0246: two threads add to one count; without a lock an addition can be lost
                        wrong[0] += bad
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
        # 5. DASHBOARD-0 (0250): import, transactional, in a worlds folder of its own
        import_rows(tmp, row, tree_bytes)
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
    if sys.argv[1:2] == ["import-once"] and len(sys.argv) == 5:
        sys.exit(import_once(*sys.argv[2:5]))
    if sys.argv[1:2] == ["seed-once"] and len(sys.argv) == 4:
        sys.exit(seed_once(*sys.argv[2:4]))
    print("usage: python art/studio_queue.py selftest", file=sys.stderr)
    sys.exit(2)
