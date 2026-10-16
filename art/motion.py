# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/motion.py — PREVIEW-0 (0240, Phase I's B4): the preview in motion, as a replayable experiment.
#
#   python art/motion.py selftest          determinism, the seed, a planted mismatch, a capture cut short, a still
#                                          re-drawn otherwise, the reset between runs, the cost, the archives' bytes,
#                                          the SSIM against hand-worked images, the retention, the plants
#   python art/motion.py gc FOLDER [DAYS]  remove the previews under FOLDER older than DAYS (30)
#
# The base and a candidate are each played along the request's camera path (art/impact.py camera_path: named, seeded,
# the same for every candidate of the request) with the same seeded simulation: the graybox's own tick, its Python
# twin graybox/tick_ref.py under rules 3 (the specification's, written apart from the browser's sim.js), from spawn A,
# driven by a seeded stream of inputs (an actor that walks, turns and jumps, its next input drawn every 30 ticks). Each
# tick's state is written canonically (the twin's own snapshot, every mover's box where it stands, the world's
# identity, the stream's counter) and its fingerprint is that text's sha256. Where the base's and the candidate's
# fingerprints agree at every tick, the candidate's motion is the base's: the state is the evidence. The page draws a
# still of each side at each pose (the renderer it plays with) and gives them to the host; their SSIM (Wang et al.
# 2004) and PSNR are advisory, a look, never a verdict. A capture missing a still or a state reads PREVIEW-INCOMPLETE and
# is never called replayed. The archives are byte for byte the same from the same inputs (no time in them). Standard
# library only; nothing here writes outside the folder it is given.

import gzip
import hashlib
import io
import json
import math
import os
import sys
import tarfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "graybox"))
import tick_ref  # noqa: E402  (the graybox's tick, rules 3, in Python)

FORMAT, VERSION, SEMANTICS = "VERDANDI-PREVIEW", "0", "preview-0: rules 3 (graybox/RULES-3.md) by graybox/tick_ref.py, 120 ticks a second"
TICKS_PER_POSE = 120          # a pose a second
INPUT_EVERY = 30              # the actor's next input, drawn from the stream every quarter of a second
VIEWPORT = (480, 270)         # the stills' size, as the page draws them
SSIM_SIZE = (96, 54)          # the stills compared as luma, box-averaged to this size
RETENTION_DAYS = 30           # a preview's files kept this long; the request's record keeps their sha256 for good
CODES = ("PREVIEW-INCOMPLETE", "PREVIEW-STALE", "PREVIEW-NO-PLAN", "PREVIEW-STILL", "PREVIEW-NO-PATH")
INPUTS = ({"f": True}, {"f": True, "l": True}, {"f": True, "r": True}, {"f": True, "jump": True}, {}, {"b": True},
          {"f": True, "dyaw": 0.05}, {"f": True, "dyaw": -0.05})

# PREVIEW-0's plants, each set by its self-test and each caught by one of its rows
PLANT = ""
PLANTS = ("preview-unseeded", "preview-shared-state", "preview-incomplete-passes")


class PreviewError(Exception):
    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code, self.detail = code, detail


def enc(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256(b):
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------------------------------------ the simulation
class Stream:
    """The seeded stream of the actor's inputs: draw k is the sha256 of the seed and k; its counter is in every state."""

    def __init__(self, seed):
        self.seed, self.counter = str(seed), 0

    def draw(self):
        h = sha256(("%s:%d" % ("" if PLANT == "preview-unseeded" else self.seed, self.counter)).encode("utf-8"))
        self.counter += 1
        return int(h[:8], 16)


_SHARED = {}


def world_of(out):
    """The twin's rules-3 world of an export (its W and C, the scene's movers): a new one for every run."""
    movers = [{k: m[k] for k in ("id", "box", "axis", "len", "speed", "policy")} for m in out["scene"].get("movers", [])]
    if PLANT == "preview-shared-state" and "w" in _SHARED:
        return _SHARED["w"]
    w = tick_ref.World3({"canonical": out["W"], "collision": out["C"]}, movers)
    _SHARED["w"] = w
    return w


def state_text(world, s, counter):
    """One tick's state, canonical: the twin's snapshot (the actor, the movers' phases, the targets), every mover's box
    where it stands, the world's identity and the stream's counter."""
    boxes = [[m.id] + [round(v, 6) for v in m.pose(st.phase)] for m, st in zip(world.movers, s.movers)]
    return enc({"identity": "%016x" % world.identity_state, "snapshot": tick_ref.write_snapshot2(s), "movers": boxes, "rng": counter})


def simulate(out, seed, ticks, side="A"):
    """The states of `ticks` ticks from spawn `side`, the actor driven by the seed's stream: [state text], the start
    first (tick 0), and the boxes of the movers and targets at every tick (for the page's stills)."""
    world = world_of(out)
    if PLANT == "preview-shared-state" and "s" in _SHARED:
        s = _SHARED["s"]
    else:
        s = tick_ref.State2.new(world, side)
        _SHARED["s"] = s
    stream = Stream(seed)
    inp = {}
    states, frames = [state_text(world, s, stream.counter)], [frame_of(world, s)]
    for t in range(ticks):
        if t % INPUT_EVERY == 0:
            inp = dict(INPUTS[stream.draw() % len(INPUTS)])
        tick_ref.tick3(world, s, inp)
        states.append(state_text(world, s, stream.counter))
        frames.append(frame_of(world, s))
    return states, frames


def frame_of(world, s):
    """What the page draws of the simulation at a tick: the movers' boxes and the targets (as play.js's targets())."""
    movers = [[round(v, 6) for v in m.pose(st.phase)] for m, st in zip(world.movers, s.movers)]
    targets = [{"up": bool(t.up), "box": [round(v, 6) for v in (t.x - 0.4, t.y + (0 if t.up else -1.9 + 0.1), t.z - 0.4, t.x + 0.4, t.y + (1.9 if t.up else 0.1), t.z + 0.4)]}
               for t in s.targets]
    return {"movers": movers, "targets": targets}


def fingerprints(states):
    return [sha256(t.encode("ascii")) for t in states]


def first_difference(a, b):
    """(tick, the fields that differ) of the first tick whose states differ, or None."""
    for k, (x, y) in enumerate(zip(a, b)):
        if x != y:
            X, Y = json.loads(x), json.loads(y)
            why = sorted(f for f in X if X[f] != Y.get(f))
            if "snapshot" in why:
                sx, sy = json.loads(X["snapshot"]), json.loads(Y["snapshot"])
                why = [w for w in why if w != "snapshot"] + ["snapshot." + f for f in sorted(sx) if sx[f] != sy.get(f)]
            return k, why
    if len(a) != len(b):
        return min(len(a), len(b)), ["length"]
    return None


# ------------------------------------------------------------------------------------------------ the plan
def plan(base_out, cand_out, path, seed):
    """Both sides played: the poses, the ticks the stills are drawn at, the boxes the page draws at each, every tick's
    fingerprint on each side and where they first differ. The same inputs give the same plan."""
    poses = path["poses"]
    ticks = TICKS_PER_POSE * len(poses)
    t0 = time.perf_counter()
    sb, fb = simulate(base_out, seed, ticks)
    sc, fc = simulate(cand_out, seed, ticks)
    ms = int((time.perf_counter() - t0) * 1000)
    at = [k * TICKS_PER_POSE for k in range(len(poses))]
    diff = first_difference(sb, sc)
    return {"poses": poses, "path_id": path["id"], "seed": str(seed), "spawn": "A", "ticks": ticks, "still_ticks": at,
            "viewport": list(VIEWPORT), "framerate": 1.0 / tick_ref.TICK, "semantics": SEMANTICS,
            "frames": {"base": [fb[t] for t in at], "candidate": [fc[t] for t in at]},
            "fingerprints": {"base": fingerprints(sb), "candidate": fingerprints(sc)},
            "states": {"base": sb, "candidate": sc},
            "first_difference": None if diff is None else {"tick": diff[0], "fields": diff[1]}, "sim_ms": ms}


# ------------------------------------------------------------------------------------------------ the stills
def luma(png, size=SSIM_SIZE):
    """The still's luma (BT.601), box-averaged to `size`: a list of rows of floats 0..255."""
    import quality
    w, h, rgb = quality.decode_png(png)
    W, H = size
    out = []
    for j in range(H):
        y0, y1 = j * h // H, max(j * h // H + 1, (j + 1) * h // H)
        row = []
        for i in range(W):
            x0, x1 = i * w // W, max(i * w // W + 1, (i + 1) * w // W)
            s = n = 0
            for y in range(y0, y1):
                base = (y * w) * 3
                for x in range(x0, x1):
                    p = base + x * 3
                    s += 0.299 * rgb[p] + 0.587 * rgb[p + 1] + 0.114 * rgb[p + 2]
                    n += 1
            row.append(s / n)
        out.append(row)
    return out


def _gauss(n=11, sigma=1.5):
    g = [math.exp(-((i - n // 2) ** 2) / (2 * sigma * sigma)) for i in range(n)]
    s = sum(g)
    return [v / s for v in g]


def _blur(img, g):
    """The 'valid' separable Gaussian filter (no padding), as Wang et al.'s ssim_index uses filter2(window, ., 'valid')."""
    n, H, W = len(g), len(img), len(img[0])
    rows = [[sum(g[k] * r[x + k] for k in range(n)) for x in range(W - n + 1)] for r in img]
    return [[sum(g[k] * rows[y + k][x] for k in range(n)) for x in range(W - n + 1)] for y in range(H - n + 1)]


def ssim(a, b, L=255.0, K1=0.01, K2=0.03):
    """Mean SSIM of two luma images of one size (Wang, Bovik, Sheikh and Simoncelli 2004): an 11 x 11 Gaussian window of
    sigma 1.5, C1 = (K1 L)^2, C2 = (K2 L)^2, the mean of the valid map."""
    g = _gauss()
    C1, C2 = (K1 * L) ** 2, (K2 * L) ** 2
    mul = lambda p, q: [[x * y for x, y in zip(r, s)] for r, s in zip(p, q)]
    m1, m2 = _blur(a, g), _blur(b, g)
    s11, s22, s12 = _blur(mul(a, a), g), _blur(mul(b, b), g), _blur(mul(a, b), g)
    tot = n = 0
    for y in range(len(m1)):
        for x in range(len(m1[0])):
            u1, u2 = m1[y][x], m2[y][x]
            v1, v2, v12 = s11[y][x] - u1 * u1, s22[y][x] - u2 * u2, s12[y][x] - u1 * u2
            tot += ((2 * u1 * u2 + C1) * (2 * v12 + C2)) / ((u1 * u1 + u2 * u2 + C1) * (v1 + v2 + C2))
            n += 1
    return tot / n


def psnr(a, b):
    mse = sum((x - y) ** 2 for r, s in zip(a, b) for x, y in zip(r, s)) / (len(a) * len(a[0]))
    return None if mse == 0 else round(10 * math.log10(255.0 * 255.0 / mse), 3)


# ------------------------------------------------------------------------------------------------ the report
def report(p, stills, previous=None):
    """The preview's report: at each still's tick the two state fingerprints, the two stills' digests, their SSIM and
    PSNR (advisory) and the tick's comparison_result: PASS (the same state, both stills), DIFFER (the states differ),
    INCOMPLETE (a still or a state missing), or UNTRUSTED (UNTRUSTED_IMAGE: `previous`, a report of the same plan, had
    this state with other still bytes: the renderer moved, not the world). `stills` maps ("base"|"candidate", k) to PNG
    bytes. Replayed only when every tick is complete; state verified only when, besides, every state agrees."""
    rows, incomplete, untrusted = [], [], []
    fb, fc = p["fingerprints"]["base"], p["fingerprints"]["candidate"]
    for k, t in enumerate(p["still_ticks"]):
        a, b = stills.get(("base", k)), stills.get(("candidate", k))
        sa = fb[t] if t < len(fb) else None
        sb = fc[t] if t < len(fc) else None
        row = {"pose": k, "tick": t, "state_fingerprint": {"base": sa, "candidate": sb},
               "image_digest": {"base": sha256(a) if a else None, "candidate": sha256(b) if b else None}}
        if not (a and b and sa and sb) and PLANT != "preview-incomplete-passes":
            row["comparison_result"] = "INCOMPLETE"
            incomplete.append(t)
        else:
            row["comparison_result"] = "PASS" if sa == sb else "DIFFER"
            if a and b:
                la, lb = luma(a), luma(b)
                row["ssim"], row["psnr"] = round(ssim(la, lb), 4), psnr(la, lb)
        pr = next((x for x in (previous or {}).get("ticks", []) if x["pose"] == k), None)
        if pr and row["comparison_result"] == "PASS" and any(
                pr["state_fingerprint"][s] == row["state_fingerprint"][s] and pr["image_digest"][s] and pr["image_digest"][s] != row["image_digest"][s]
                for s in ("base", "candidate")):
            row["comparison_result"], row["reason"] = "UNTRUSTED", "UNTRUSTED_IMAGE: the state as in the previous capture, the still's bytes not"
            untrusted.append(t)
        rows.append(row)
    agree = all(r["comparison_result"] in ("PASS", "UNTRUSTED") for r in rows)
    return {"format": FORMAT, "version": VERSION, "semantics": p["semantics"], "path_id": p["path_id"], "seed": p["seed"], "ticks": rows,
            "replayed": not incomplete, "code": "PREVIEW-INCOMPLETE" if incomplete else "", "incomplete_ticks": incomplete,
            "untrusted_ticks": untrusted, "state_verified": bool(agree and not incomplete), "first_difference": p["first_difference"],
            "path_check": p.get("path_check"), "framing": p.get("framing"),
            "fingerprints_sha256": {s: sha256(enc(p["fingerprints"][s]).encode("ascii")) for s in ("base", "candidate")},
            "advisory": "the stills' SSIM and PSNR are a look, never a verdict: the states are the evidence"}


# ------------------------------------------------------------------------------------------------ the sheet to inspect
def compare_sheet(p, stills):
    """FRAME-0 (0243): a picture for a person to inspect, not evidence: at each pose a row of the base's and the
    candidate's stills at half size, and, when the path frames a subject, both crops of the subject (its box on the still
    and a fifth round it, square) enlarged side by side, then their difference eight times over (where the candidate
    changed the picture, however faintly). PNG bytes, or None when a still is missing."""
    import quality
    n = len(p["still_ticks"])
    if any((s_, k) not in stills for s_ in ("base", "candidate") for k in range(n)):
        return None
    fr = (p.get("framing") or {}).get("base")
    C, G = 135, 4
    W = 240 * 2 + G + ((C * 3 + G * 3) if fr else 0)
    H = n * 135 + (n - 1) * G
    out = bytearray([18, 18, 20] * (W * H))

    def put(x0, y0, w, h, px):
        for y in range(h):
            out[((y0 + y) * W + x0) * 3:((y0 + y) * W + x0 + w) * 3] = px[y * w * 3:(y + 1) * w * 3]

    for k in range(n):
        y0 = k * (135 + G)
        imgs = [quality.decode_png(stills[(s_, k)]) for s_ in ("base", "candidate")]
        for j, (w, h, rgb) in enumerate(imgs):
            half = bytearray(240 * 135 * 3)
            for y in range(135):
                sy = min(h - 1, y * h // 135)
                for x in range(240):
                    sx = min(w - 1, x * w // 240)
                    half[(y * 240 + x) * 3:(y * 240 + x) * 3 + 3] = rgb[(sy * w + sx) * 3:(sy * w + sx) * 3 + 3]
            put(j * (240 + G), y0, 240, 135, bytes(half))
        bb = fr["poses"][k]["bbox"] if fr and k < len(fr["poses"]) else None
        if bb:
            crops = []
            for j, (w, h, rgb) in enumerate(imgs):
                sx_, sy_ = w / 480.0, h / 270.0
                cx, cy = (bb[0] + bb[2]) / 2 * sx_, (bb[1] + bb[3]) / 2 * sy_
                half_side = max(bb[2] - bb[0], bb[3] - bb[1]) * 0.6 * max(sx_, sy_) + 2
                crop = bytearray(C * C * 3)
                for y in range(C):
                    sy = int(min(h - 1, max(0, cy - half_side + (y + 0.5) * 2 * half_side / C)))
                    for x in range(C):
                        sx = int(min(w - 1, max(0, cx - half_side + (x + 0.5) * 2 * half_side / C)))
                        crop[(y * C + x) * 3:(y * C + x) * 3 + 3] = rgb[(sy * w + sx) * 3:(sy * w + sx) * 3 + 3]
                put(480 + G * 2 + j * (C + G), y0, C, C, bytes(crop))
                crops.append(crop)
            put(480 + G * 2 + 2 * (C + G), y0, C, C, bytes(min(255, 8 * abs(a_ - b_)) for a_, b_ in zip(crops[0], crops[1])))
    return quality.png_bytes(W, H, bytes(out))


# ------------------------------------------------------------------------------------------------ the archives
def tar_gz(members):
    """A gzip'd tar of {name: bytes}, byte for byte the same from the same members: sorted, mode 644, uid and gid 0, no
    owner names, every time 0, and no name or time in the gzip header."""
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.USTAR_FORMAT) as tf:
        for name in sorted(members):
            data = members[name]
            ti = tarfile.TarInfo(name)
            ti.size, ti.mtime, ti.mode, ti.uid, ti.gid, ti.uname, ti.gname = len(data), 0, 0o644, 0, 0, "", ""
            tf.addfile(ti, io.BytesIO(data))
    out = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0, compresslevel=9) as gz:
        gz.write(raw.getvalue())
    return out.getvalue()


def artifacts(p, stills, rep, meta):
    """The candidate's preview, as files: its meta, its states, its stills and its report (name -> bytes)."""
    states = {"%s.states.jsonl" % s: ("\n".join(p["states"][s]) + "\n").encode("ascii") for s in ("base", "candidate")}
    states.update({"%s.fingerprints.txt" % s: ("\n".join(p["fingerprints"][s]) + "\n").encode("ascii") for s in ("base", "candidate")})
    pics = {"%s-%d-tick%d.png" % (side, k, p["still_ticks"][k]): b for (side, k), b in stills.items()}
    return {"preview.meta.json": (json.dumps(meta, sort_keys=True, indent=1) + "\n").encode("ascii"),
            "preview.states.tar.gz": tar_gz(states), "preview.stills.tar.gz": tar_gz(pics),
            "preview.report.json": (json.dumps(rep, sort_keys=True, indent=1) + "\n").encode("ascii")}


def gc(folder, days, now=None):
    """Remove preview artifacts older than `days` (by their meta's `made_at`, seconds since the epoch) under `folder`;
    the request's record keeps their sha256. Returns the files removed."""
    now = time.time() if now is None else now
    gone = []
    for root, _dirs, files in os.walk(folder):
        for f in sorted(files):
            if not f.endswith(".preview.meta.json"):
                continue
            try:
                made = float(json.load(open(os.path.join(root, f), encoding="utf-8"))["made_at"])
            except (OSError, ValueError, KeyError, TypeError):
                continue
            if now - made > days * 86400:
                stem = f[:-len("preview.meta.json")]
                for g in sorted(os.listdir(root)):
                    if g.startswith(stem + "preview."):
                        os.remove(os.path.join(root, g))
                        gone.append(os.path.join(root, g))
                stills = os.path.join(root, stem + "stills")
                if os.path.isdir(stills):
                    for g in sorted(os.listdir(stills)):
                        os.remove(os.path.join(stills, g))
                        gone.append(os.path.join(stills, g))
                    os.rmdir(stills)
    return gone


# ------------------------------------------------------------------------------------------------ self-test
def _scene_out(text):
    import dress
    A = dress.parse(text, "x.art")
    A["name"], A["sha256"] = "x", "x"
    return dress.export(A)


def selftest():
    import copy
    import quality
    import impact
    rows = []

    def row(name, ok, detail):
        rows.append((name, bool(ok)))
        if not PLANT:
            print("[%s] %s — %s" % ("PASS" if ok else "FAIL", name, detail))
    lift = _scene_out(open(os.path.join(HERE, "briefs", "harbor-lift.art"), encoding="utf-8").read())
    path = impact.camera_path(lift["scene"], [24, 0, 16], "req-1")
    _SHARED.clear()
    p1 = plan(lift, lift, path, "req-1")
    p2 = plan(lift, lift, path, "req-1")
    row("the same inputs, the same states, tick for tick, and the same archives (B4-DETERMINISM)", p1["fingerprints"] == p2["fingerprints"]
        and p1["fingerprints"]["base"] == p1["fingerprints"]["candidate"] and p1["first_difference"] is None
        and artifacts(p1, {}, {}, {}) == artifacts(p2, {}, {}, {}),
        "%d ticks a side, %d movers, the plan %d ms; the archives the same bytes" % (p1["ticks"], len(lift["scene"].get("movers", [])), p1["sim_ms"]))
    p3 = plan(lift, lift, path, "req-2")
    moved = sum(1 for x, y in zip(p1["fingerprints"]["base"], p3["fingerprints"]["base"]) if x != y)
    row("another seed, another run (B4-SEED-SENSITIVITY)", moved > 0, "%d of %d ticks differ under seed req-2" % (moved, len(p3["fingerprints"]["base"])))
    planted = copy.deepcopy(lift)
    m0 = planted["scene"]["movers"][0]
    m0["box"] = [v + (0.5 if i in (0, 3) else 0) for i, v in enumerate(m0["box"])]
    p4 = plan(lift, planted, path, "req-1")
    fd = p4["first_difference"] or {}
    row("a mover started elsewhere: the first tick that differs and why (B4-PLANTED-MISMATCH)", fd.get("tick") == 0 and "identity" in fd.get("fields", [])
        and "movers" in fd.get("fields", []), "tick %s, fields %s" % (fd.get("tick"), fd.get("fields")))
    png = quality.png_bytes(48, 27, bytes((x * 5 + y * 3 + c * 40) % 256 for y in range(27) for x in range(48) for c in range(3)))
    full = {(s, k): png for s in ("base", "candidate") for k in range(len(path["poses"]))}
    cut = dict(full)
    del cut[("candidate", 3)]
    r_full, r_cut = report(p1, full), report(p1, cut)
    row("a still missing: INCOMPLETE at its tick, never replayed (B4-INCOMPLETE-CAPTURE)", r_full["replayed"] and r_full["state_verified"]
        and not r_cut["replayed"] and r_cut["code"] == "PREVIEW-INCOMPLETE" and r_cut["incomplete_ticks"] == [3 * TICKS_PER_POSE]
        and not r_cut["state_verified"], "complete: replayed %s, verified %s; one still missing: %s at tick %s" % (
            r_full["replayed"], r_full["state_verified"], r_cut["code"], r_cut["incomplete_ticks"]))
    other = quality.png_bytes(48, 27, bytes((x * 5 + y * 3 + c * 40 + 1) % 256 for y in range(27) for x in range(48) for c in range(3)))
    redrawn = dict(full)
    redrawn[("candidate", 0)] = other
    r_again = report(p1, redrawn, previous=r_full)
    r_diff = report(p4, full)
    row("the state as before, the still not: UNTRUSTED_IMAGE, the state still verified; states that differ: DIFFER, not verified",
        r_again["ticks"][0]["comparison_result"] == "UNTRUSTED" and r_again["untrusted_ticks"] == [0] and r_again["state_verified"]
        and all(t["comparison_result"] == "PASS" for t in r_again["ticks"][1:]) and r_diff["replayed"] and not r_diff["state_verified"]
        and r_diff["ticks"][0]["comparison_result"] == "DIFFER", "re-captured: tick 0 %s (%s); the planted mover: %s, replayed %s, verified %s" % (
            r_again["ticks"][0]["comparison_result"], r_again["ticks"][0].get("ssim"), r_diff["ticks"][0]["comparison_result"], r_diff["replayed"], r_diff["state_verified"]))
    a = plan(lift, lift, path, "req-1")["fingerprints"]["base"]
    plan(planted, planted, path, "req-1")
    b = plan(lift, lift, path, "req-1")["fingerprints"]["base"]
    row("every run from a new world and state: the base the same after another run (B4-RESET-ON-CHANGE)", a == b, "%d ticks the same before and after a run of the planted world" % len(a))
    t0 = time.perf_counter()
    plan(lift, lift, path, "req-1")
    sec = time.perf_counter() - t0
    row("one candidate's runs well inside 10 s (B4-TIMING-BOUNDARY)", sec < 10, "%.2f s for both sides, %d ticks each" % (sec, p1["ticks"]))
    flat = [[128.0] * 30 for _ in range(30)]
    ramp = [[float(x * 8) for x in range(30)] for _y in range(30)]
    row("SSIM: 1 for an image against itself, less for a change, as Wang et al. define it", abs(ssim(ramp, ramp) - 1) < 1e-12 and ssim(flat, ramp) < 0.5
        and psnr(ramp, ramp) is None, "itself %.6f, flat against ramp %.4f" % (ssim(ramp, ramp), ssim(flat, ramp)))
    import tempfile
    tmp = tempfile.mkdtemp(prefix="motion-gc-")
    try:
        for name, made in (("A", 0.0), ("B", 10 ** 10)):
            open(os.path.join(tmp, name + ".preview.meta.json"), "w").write(json.dumps({"made_at": made}))
            open(os.path.join(tmp, name + ".preview.report.json"), "w").write("{}")
        gone = gc(tmp, 30, now=10 ** 10)
        row("the archives' retention: older than 30 days removed, the newer kept", sorted(os.path.basename(g) for g in gone) == ["A.preview.meta.json", "A.preview.report.json"]
            and os.path.exists(os.path.join(tmp, "B.preview.report.json")), ", ".join(sorted(os.path.basename(g) for g in gone)))
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    if PLANT:
        return rows
    caught = []
    for p in PLANTS:
        globals()["PLANT"] = p
        _SHARED.clear()
        try:
            failed = [n for n, ok in selftest() if not ok]
        except Exception as e:  # noqa: BLE001 — a plant that breaks the run is caught by it
            failed = ["the run: %s" % type(e).__name__]
        finally:
            globals()["PLANT"] = ""
            _SHARED.clear()
        caught.append(bool(failed))
        print("[%s] preview plant %s caught — %s" % ("PASS" if failed else "FAIL", p, ("by: " + "; ".join(failed)) if failed else "NOT CAUGHT"))
    ok = all(o for _n, o in rows) and all(caught)
    print("PREVIEW SELFTEST %d/%d" % (sum(o for _n, o in rows) + sum(caught), len(rows) + len(caught)))
    return 0 if ok else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["selftest"]:
        sys.path.insert(0, HERE)
        sys.exit(selftest())
    if sys.argv[1:2] == ["gc"] and len(sys.argv) in (3, 4):
        for f in gc(sys.argv[2], float(sys.argv[3]) if len(sys.argv) == 4 else RETENTION_DAYS):
            print("removed %s" % f)
        sys.exit(0)
    print("usage: python art/motion.py selftest\n       python art/motion.py gc FOLDER [DAYS]   (the previews older than DAYS, %d by default)" % RETENTION_DAYS)
    sys.exit(2)
