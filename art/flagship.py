# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/flagship.py — FLAGSHIP-0 (0243, Phase I's B5b): the flagship's acceptance, one command, scripted.
#
#   python art/flagship.py selftest       (python art/play.py --flagship-selftest runs the same)
#   python art/flagship.py approve WORLD REQUEST LETTER --note TEXT [--root DIR]
#                                         the owner's act: a visual baseline from a preview he has looked at
#
# THE PROCEDURE (`run`). In the foundry yard, through the studio's own HTTP surface and nothing else, the marked bay's
# edit from mark to undo, each stage's evidence required before the next; the first missing stops the procedure with its
# code and nothing further is asked of the studio:
#
#   mark       the region saved on the flagship's face, its status ok, on the warehouse     FLAGSHIP-MARK
#   request    strict, tied to the head it was asked at, its candidates drawn               FLAGSHIP-REQUEST
#   candidate  the chosen candidate held in the region and strict PASS                      FLAGSHIP-HELD
#              its impact present (advisory to the studio; required here as evidence)     FLAGSHIP-NO-IMPACT
#   preview    one path for every candidate, clear in both scenes and framed for the        FLAGSHIP-FRAMING
#              region in both; both sides' stills; replayed and every state verified       FLAGSHIP-PREVIEW
#   admit      admitted; the ledger's admit event from the request's head to the head the   FLAGSHIP-ADMIT
#              files now have, with its region receipt
#   undo       undone; the head, the brief's bytes and the scene's bytes as before          FLAGSHIP-UNDO
#
# The procedure decides nothing for the studio: the studio's admission reads none of the impact, the framing or the
# preview (IMPACT-0's and PREVIEW-0's rule); this is an acceptance, which asks for evidence the studio does not require.
# The scripted director makes the run the same every time; a real provider's run is a rehearsal recorded apart
# (OBSERVED, never this acceptance). Standard library only.

import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

FORMAT, VERSION = "VERDANDI-FLAGSHIP", "0"
WORLD = "foundry-yard"
FLAGSHIP = "building:10,2-17,2"
BAY = FLAGSHIP + ":s-b3-f2"
VERTICES = [[6, 3], [8, 3], [8, 6.5], [6, 6.5]]        # bay 3 of floor 2, in metres on the warehouse's south face
STAGES = ("mark", "request", "candidate", "preview", "admit", "undo")
BASELINES = os.path.join(HERE, "visual_baselines.jsonl")

PLANT = ""
PLANTS = ("flagship-held-unchecked", "flagship-impact-unchecked", "flagship-verify-unchecked")


def sha256(b):
    return hashlib.sha256(b).hexdigest()


class Http:
    """The studio's HTTP surface, with its token."""

    def __init__(self, base, token):
        self.base, self.token = base, token

    def post(self, path, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        rq = urllib.request.Request(self.base + path, data=data, method="POST", headers={"Content-Type": ctype, "X-Studio-Token": self.token})
        try:
            with urllib.request.urlopen(rq, timeout=180) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            raw = e.read() or b"{}"
            return e.code, json.loads(raw) if raw[:1] == b"{" else {"body": raw.decode("utf-8", "replace")}


def run(http, shape, prompt, choose, wait, snapshot, still_of, admission_still, before=None):
    """The flagship's procedure (see the head of this file). `wait(rid)` returns the studio's request when it has ended;
    `snapshot()` the world as its files stand ({head, brief_sha256, scene_sha256, admits}); `still_of(side, k)` PNG bytes;
    `admission_still` the still an admission brings; `before` {stage: callable} run before a stage (a planted change)."""
    stages, out = [], {"format": FORMAT, "version": VERSION, "world_before": snapshot()}

    def done(stage, ok, code, evidence):
        stages.append({"stage": stage, "ok": bool(ok), "code": "" if ok else code, "evidence": evidence})
        return ok

    def result():
        bad = [s_ for s_ in stages if not s_["ok"]]
        return dict(out, stages=stages, ok=not bad and len(stages) == len(STAGES), stopped_at=bad[0]["stage"] if bad else "",
                    code=bad[0]["code"] if bad else "", world_after=snapshot())

    def hook(stage):
        if before and stage in before:
            before[stage]()

    # mark
    hook("mark")
    c, r = http.post("/studio/shapes/save", {"shape": shape})
    got = r.get("shape") or {}
    on = {"piece": got.get("piece"), "face": got.get("face")}
    if not done("mark", c == 200 and got.get("status") == "ok" and on.get("piece") == FLAGSHIP and on.get("face") == "+z", "FLAGSHIP-MARK",
                {"status": got.get("status"), "piece": on.get("piece"), "face": on.get("face"), "code": r.get("code")}):
        return result()
    # request
    hook("request")
    head0 = snapshot()["head"]
    c, r = http.post("/studio/ask", {"prompt": prompt, "strict": True})
    st = wait(r.get("id")) if c == 200 else {}
    cands = [x for x in (st or {}).get("candidates", []) if x.get("slot") is not None]
    if not done("request", c == 200 and st.get("state") == "done" and st.get("strict") is True and st.get("head") == head0 and cands, "FLAGSHIP-REQUEST",
                {"id": r.get("id"), "state": (st or {}).get("state"), "strict": (st or {}).get("strict"), "head": (st or {}).get("head"),
                 "head_asked_at": head0, "drawn": [x["title"] for x in cands], "code": r.get("code")}):
        return result()
    rid = st["id"]
    # candidate
    hook("candidate")
    cand = next((x for x in cands if x["title"] == choose), None)
    if cand is None:
        done("candidate", False, "FLAGSHIP-HELD", {"chosen": choose, "drawn": [x["title"] for x in cands]})
        return result()
    acc = ((cand.get("held") or {}).get("accounts") or [{}])[0]
    strict = cand.get("strict") or {}
    held_ok = (acc.get("verdict") == "held" and strict.get("ok") is True) or PLANT == "flagship-held-unchecked"
    imp = cand.get("impact") or {}
    imp_ok = (bool(imp) and "error" not in imp and "delta" in imp) or PLANT == "flagship-impact-unchecked"
    ev = {"letter": cand["letter"], "title": cand["title"], "held": acc.get("verdict"), "strict": strict.get("ok"), "strict_code": strict.get("code"),
          "impact": {k: imp.get(k) for k in ("delta", "flag")} if imp and "error" not in imp else (imp.get("error") or "none")}
    if not done("candidate", held_ok and imp_ok, "FLAGSHIP-HELD" if not held_ok else "FLAGSHIP-NO-IMPACT", ev):
        return result()
    letter = cand["letter"]
    # preview
    hook("preview")
    c, pl = http.post("/studio/preview", {"id": rid, "candidate": letter})
    fr = (pl or {}).get("framing") or {}
    pc = (pl or {}).get("path_check") or {}
    paths = {((x.get("impact") or {}).get("preview") or {}).get("path_id") for x in cands}
    framed = c == 200 and fr.get("base", {}).get("met") and fr.get("candidate", {}).get("met")
    clear = c == 200 and pc.get("base") == [] and pc.get("candidate") == [] and paths == {pl.get("path_id")}
    if not framed or not clear:
        done("preview", False, "FLAGSHIP-FRAMING", {"code": pl.get("code"), "path": pl.get("path_id"), "paths_of_candidates": sorted(p_ or "" for p_ in paths),
                                                    "framed": [fr.get("base", {}).get("met"), fr.get("candidate", {}).get("met")],
                                                    "breaches": [len(pc.get("base") or []), len(pc.get("candidate") or [])]})
        return result()
    for k in range(len(pl["still_ticks"])):
        for side in ("base", "candidate"):
            http.post("/studio/preview/still?id=%s&candidate=%s&side=%s&k=%d" % (rid, letter, side, k), still_of(side, k), "image/png")
    c, rep = http.post("/studio/preview/finish", {"id": rid, "candidate": letter})
    verified = c == 200 and rep.get("replayed") and (rep.get("state_verified") or PLANT == "flagship-verify-unchecked")
    if not done("preview", verified, "FLAGSHIP-PREVIEW",
                {"path": pl.get("path_id"), "subject": (fr.get("subject") or {}).get("shape"),
                 "smallest_px": [fr["base"]["smallest_px"], fr["candidate"]["smallest_px"]], "replayed": rep.get("replayed"),
                 "state_verified": rep.get("state_verified"), "first_difference": rep.get("first_difference"), "files": rep.get("files")}):
        return result()
    # admit
    hook("admit")
    before_admit = snapshot()
    c, s_ = http.post("/studio/still?id=%s&candidate=%s" % (rid, letter), admission_still, "image/png")
    c, a = http.post("/studio/admit", {"id": rid, "candidate": letter, "still": s_.get("still", "")})
    after = snapshot()
    new = after["admits"][len(before_admit["admits"]):]
    ad = new[-1] if new else {}
    ok = c == 200 and len(new) == 1 and ad.get("head_before") == st["head"] and ad.get("head_after") == after["head"] != before_admit["head"] \
        and bool((ad.get("region") or {}).get("receipt"))
    if not done("admit", ok, "FLAGSHIP-ADMIT", {"status": c, "code": a.get("code"), "message": (a.get("message") or "")[:160], "seq": ad.get("seq"),
                                                "head_before": ad.get("head_before"), "head_after": ad.get("head_after"),
                                                "receipt_sha256": (ad.get("region") or {}).get("receipt_sha256")}):
        return result()
    # undo
    hook("undo")
    c, u = http.post("/studio/undo", {})
    back = snapshot()
    same = {k: back[k] for k in ("head", "brief_sha256", "scene_sha256")} == {k: before_admit[k] for k in ("head", "brief_sha256", "scene_sha256")}
    done("undo", c == 200 and same, "FLAGSHIP-UNDO", {"status": c, "head": back["head"], "as_before": same})
    return result()


# ------------------------------------------------------------------------------------------------ the owner's act
def approve(world, rid, letter, note, root=None, path=None):
    """A visual baseline: the owner's word that he has looked at a preview's stills and its sheet and takes them as the
    world's views. Written only from a preview that is complete, every state verified, its path clear and framed in both
    scenes; refused otherwise. Appends one line to art/visual_baselines.jsonl (or `path`); the scene's bytes reference
    (art/references.jsonl) is another thing and is not touched."""
    d = os.path.join(root or REPO, "art", "build", "studio", world, rid)
    try:
        rep = json.loads(open(os.path.join(d, letter + ".preview.report.json"), "rb").read())
        meta = json.loads(open(os.path.join(d, letter + ".preview.meta.json"), "rb").read())
    except (OSError, ValueError) as e:
        return False, "no preview of %s %s %s: %s" % (world, rid, letter, e)
    fr, pc = rep.get("framing") or {}, rep.get("path_check") or {}
    why = ([] if rep.get("replayed") else ["not replayed (%s)" % rep.get("code")]) + ([] if rep.get("state_verified") else ["a state not verified"]) + \
          ([] if pc.get("base") == [] and pc.get("candidate") == [] else ["the path not clear"]) + \
          ([] if fr.get("base", {}).get("met") and fr.get("candidate", {}).get("met") else ["the subject not framed"])
    names = [n for n in ("preview.meta.json", "preview.report.json", "preview.states.tar.gz", "preview.stills.tar.gz", "preview.compare.png")
             if os.path.exists(os.path.join(d, letter + "." + n))]
    if "preview.compare.png" not in names:
        why.append("no sheet to have looked at")
    if why:
        return False, "refused: " + "; ".join(why)
    if not (note or "").strip():
        return False, "refused: say what you looked at (--note)"
    import datetime
    line = {"format": "VERDANDI-VISUAL-BASELINE", "version": "0", "world": world, "request": rid, "candidate": letter,
            "path_id": rep.get("path_id"), "seed": rep.get("seed"), "subject": (fr.get("subject") or {}).get("shape"),
            "files": {n: sha256(open(os.path.join(d, letter + "." + n), "rb").read()) for n in names},
            "provenance": rep.get("provenance"), "semantics": meta.get("semantics"),
            "basis": "the owner's eyes on the stills and the sheet; the framing's 24 x 24 px and the legibility proxies are engineering proxies, not perceptual legibility",
            "note": note.strip(), "approved_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    with open(path or BASELINES, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(line, sort_keys=True, ensure_ascii=True) + "\n")
    return True, "APPROVED %s: request %s candidate %s, path %s, the sheet %s" % (world, rid, letter, line["path_id"], line["files"]["preview.compare.png"][:12])


# ------------------------------------------------------------------------------------------------ self-test
def selftest():
    import play
    import studio
    import impact
    import motion
    import quality
    rows = []

    def row(name, ok, detail):
        rows.append((name, bool(ok)))
        if not PLANT:
            print("[%s] %s — %s" % ("PASS" if ok else "FAIL", name, detail))
    tmp = tempfile.mkdtemp(prefix="flagship-selftest-")
    saved = (play.ROOT, impact.report, motion.PLANT)
    live = srv = None
    D = play.director()
    try:
        os.makedirs(os.path.join(tmp, "art", "briefs"))
        os.makedirs(os.path.join(tmp, "graybox", "maps"))
        for f in os.listdir(os.path.join(REPO, "graybox", "maps")):
            shutil.copy(os.path.join(REPO, "graybox", "maps", f), os.path.join(tmp, "graybox", "maps", f))
        art = os.path.join(tmp, "art", "briefs", WORLD + ".art")
        original = open(os.path.join(HERE, "briefs", WORLD + ".art"), "rb").read().replace(b"\r\n", b"\n")
        open(art, "wb").write(original)
        ws = D.Workspace(WORLD, tmp)
        D.cmd_genesis_quiet(ws)
        play.ROOT = tmp
        live = play.Live(WORLD, art, [], poll=0.15, root=tmp)
        threading.Thread(target=live.watch, kwargs={"say": lambda s_: None}, daemon=True).start()
        play.start_studio(live, os.path.join(HERE, "providers", "scripted.json"), say=lambda s_: None)
        srv = play.server(live)
        base = "http://127.0.0.1:%d" % srv.server_address[1]
        tok = re.search(r'data-studio="([0-9a-f]+)"', urllib.request.urlopen(base + "/play.html", timeout=30).read().decode("utf-8")).group(1)
        http = Http(base, tok)

        def wait(rid):
            for _i in range(1800):
                st = live.studio.state()["request"]
                if st and st["id"] == rid and st["state"] != "running":
                    return st
                time.sleep(0.1)
            return {}

        def snapshot():
            out, parts, _c = ws.export()
            return {"head": D.canon.head(parts), "brief_sha256": sha256(open(art, "rb").read()), "scene_sha256": sha256(out["scene_bytes"]),
                    "admits": [e for e in D.led.read(ws.ledger)[0] if e["kind"] == "admit"]}

        def still_of(side, k):
            return quality.png_bytes(48, 27, bytes((x * 5 + y * 3 + c * 40 + (0 if side == "base" else 9) + k) % 256 for y in range(27) for x in range(48) for c in range(3)))

        def shape():
            mass = next(v for v in ws.export()[0]["scene"]["visuals"] if v["id"] == FLAGSHIP)
            return {"name": "bay", "operation": "region", "anchor": {"piece": FLAGSHIP, "face": "+z", "box": mass["box"], "scene": live.slot(0)["sha"], "view": {}},
                    "vertices": VERTICES, "constraints": {"within": True, "supports": False, "collision": False, "material": "keep"}}
        world = lambda w: {k: w[k] for k in ("head", "brief_sha256", "scene_sha256")} if w else {}
        go = lambda choose, before=None: run(http, shape(), "panel #bay", choose, wait, snapshot, still_of, D.selftest_still(), before)

        r1 = go("Panelled bay")
        ev = {s_["stage"]: s_["evidence"] for s_ in r1["stages"]}
        pv = ev.get("preview", {})
        row("the flagship's edit from mark to undo, every stage's evidence (FLAGSHIP-0)", r1["ok"] and world(r1["world_after"]) == world(r1["world_before"])
            and len(r1["world_after"]["admits"]) == len(r1["world_before"]["admits"]) + 2,
            "stages %s; held %s, strict %s, impact %s; path %s framed for #bay in both scenes (smallest %s px); replayed %s, verified %s; admitted #%s %s -> %s, "
            "receipt %s; undone, the head, the brief and the scene as before" % (
                [s_["stage"] + ("" if s_["ok"] else " " + s_["code"]) for s_ in r1["stages"]], ev.get("candidate", {}).get("held"), ev.get("candidate", {}).get("strict"),
                ev.get("candidate", {}).get("impact"), pv.get("path"), [int(x) for x in pv.get("smallest_px", [0])], pv.get("replayed"), pv.get("state_verified"),
                ev.get("admit", {}).get("seq"), (ev.get("admit", {}).get("head_before") or "")[:12], (ev.get("admit", {}).get("head_after") or "")[:12],
                (ev.get("admit", {}).get("receipt_sha256") or "")[:12]))
        # planted failures: each stops its transition, and the active world is as it was
        r2 = go("Panelled column")
        rid2 = next(s_["evidence"]["id"] for s_ in r2["stages"] if s_["stage"] == "request")
        letter2 = next((c_["letter"] for c_ in live.studio.state()["request"]["candidates"] if c_["title"] == "Panelled column"), "C")
        c_d, r_d = http.post("/studio/still?id=%s&candidate=%s" % (rid2, letter2), D.selftest_still(), "image/png")
        c_d, r_d = http.post("/studio/admit", {"id": rid2, "candidate": letter2, "still": r_d.get("still", "")})
        w2 = snapshot()
        row("planted: an invalid region (the column reaches beyond #bay): stopped at the candidate, the studio refuses it too, the world as it was",
            r2["stopped_at"] == "candidate" and r2["code"] == "FLAGSHIP-HELD" and c_d == 409 and r_d.get("code") == "ADMIT-OUTSIDE"
            and world(w2) == world(r2["world_before"]) and len(w2["admits"]) == len(r2["world_before"]["admits"]),
            "%s at %s (strict %s); the studio's own admission %s %s" % (r2["code"], r2["stopped_at"],
                                                                      next(s_["evidence"].get("strict_code") for s_ in r2["stages"] if s_["stage"] == "candidate"), c_d, r_d.get("code")))

        def broken(*_a, **_k):
            raise impact.ImpactError("planted: no impact")
        impact.report = broken
        try:
            r3 = go("Panelled bay")
        finally:
            impact.report = saved[1]
        row("planted: the impact evidence missing: stopped at the candidate (FLAGSHIP-NO-IMPACT), nothing admitted, the world as it was",
            r3["stopped_at"] == "candidate" and r3["code"] == "FLAGSHIP-NO-IMPACT" and world(r3["world_after"]) == world(r3["world_before"])
            and len(r3["world_after"]["admits"]) == len(r3["world_before"]["admits"]),
            "%s at %s: %s" % (r3["code"], r3["stopped_at"], next(s_["evidence"].get("impact") for s_ in r3["stages"] if s_["stage"] == "candidate")))
        motion.PLANT = "preview-shared-state"
        motion._SHARED.clear()
        try:
            r4 = go("Panelled bay")
        finally:
            motion.PLANT = saved[2]
            motion._SHARED.clear()
        e4 = next(s_["evidence"] for s_ in r4["stages"] if s_["stage"] == "preview")
        row("planted: the preview's verification failing (one run's state carried into the next): stopped at the preview, nothing admitted, the world as it was",
            r4["stopped_at"] == "preview" and r4["code"] == "FLAGSHIP-PREVIEW" and world(r4["world_after"]) == world(r4["world_before"])
            and len(r4["world_after"]["admits"]) == len(r4["world_before"]["admits"]),
            "%s: replayed %s, state verified %s, first difference %s" % (r4["code"], e4.get("replayed"), e4.get("state_verified"), e4.get("first_difference")))
        # the owner's act: a visual baseline from r1's preview, and none from r4's
        rid1 = next(s_["evidence"]["id"] for s_ in r1["stages"] if s_["stage"] == "request")
        rid4 = next(s_["evidence"]["id"] for s_ in r4["stages"] if s_["stage"] == "request")
        bl = os.path.join(tmp, "baselines.jsonl")
        ok1, said1 = approve(WORLD, rid1, ev["candidate"]["letter"], "looked at the sheet", root=tmp, path=bl)
        ok4, said4 = approve(WORLD, rid4, "A", "looked at it", root=tmp, path=bl)
        ok0, said0 = approve(WORLD, rid1, ev["candidate"]["letter"], "", root=tmp, path=bl)
        lines = [json.loads(x) for x in open(bl, "rb").read().splitlines()] if os.path.exists(bl) else []
        row("the visual baseline: written only on a person's word, from a preview complete, verified and framed; refused otherwise",
            ok1 and not ok4 and not ok0 and len(lines) == 1 and lines[0]["path_id"] == pv.get("path") and lines[0]["files"].get("preview.compare.png")
            == pv.get("files", {}).get("preview.compare.png") and "not perceptual legibility" in lines[0]["basis"],
            "%s; %s; without a note: %s" % (said1, said4, said0))
        # stale: the brief changes after the preview, before the admission
        def outside_edit():
            v = live.version
            open(art, "ab").write(b"material plant_stale 10,20,30 0.5 0.0\n")
            t0 = time.time()
            while live.version == v and time.time() - t0 < 120:
                time.sleep(0.1)
        w5 = {}
        r5 = go("Panelled bay", before={"admit": lambda: (outside_edit(), w5.update(snapshot()))})
        e5 = next((s_["evidence"] for s_ in r5["stages"] if s_["stage"] == "admit"), {})
        row("planted: a stale revision (the brief edited after the preview): the admission refused, the world as the edit left it",
            r5["stopped_at"] == "admit" and r5["code"] == "FLAGSHIP-ADMIT" and e5.get("status") == 409 and world(r5["world_after"]) == world(w5)
            and len(r5["world_after"]["admits"]) == len(w5.get("admits", [])),
            "%s: %s %s" % (r5["code"], e5.get("status"), e5.get("code")))
    except Exception as e:  # noqa: BLE001 — the self-test says what stopped it
        import traceback
        if not PLANT:
            traceback.print_exc()
        row("flagship: the self-test ran to its end", False, "%s: %s" % (type(e).__name__, str(e)[:200]))
    finally:
        play.ROOT, impact.report, motion.PLANT = saved
        if live:
            live.stopping = True
            if live.studio:
                live.studio.shutdown()
        if srv:
            srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    if PLANT:
        return rows
    caught = []
    for p in PLANTS:
        globals()["PLANT"] = p
        try:
            failed = [n for n, ok in selftest() if not ok]
        finally:
            globals()["PLANT"] = ""
        caught.append(bool(failed))
        print("[%s] flagship plant %s caught — %s" % ("PASS" if failed else "FAIL", p, ("by: " + "; ".join(f[:70] for f in failed)) if failed else "NOT CAUGHT"))
    ok = all(o for _n, o in rows) and all(caught)
    print("FLAGSHIP SELFTEST %d/%d" % (sum(o for _n, o in rows) + sum(caught), len(rows) + len(caught)))
    return 0 if ok else 1


def main(argv):
    if argv[:1] == ["selftest"]:
        return selftest()
    if argv[:1] == ["approve"] and len(argv) >= 4 and "--note" in argv:
        i = argv.index("--note")
        root = argv[argv.index("--root") + 1] if "--root" in argv else None
        ok, said = approve(argv[1], argv[2], argv[3], argv[i + 1] if i + 1 < len(argv) else "", root=root)
        print(said)
        return 0 if ok else 1
    print("usage: python art/flagship.py selftest\n       python art/flagship.py approve WORLD REQUEST LETTER --note TEXT [--root DIR]")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
