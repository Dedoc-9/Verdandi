# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""verify.py — the Verðandi gate. Every claim in the repository as a row that can redden.

    python verify/verify.py            # from the repository root (any cwd works)

Prints one line per row, `GATE PASSED` or `GATE FAILED`, and a reconcile line naming the rowset. Rows that
need `rustc` SKIP without it, count-stable. Nothing here prints a clock or a temporary path, so two
consecutive runs are byte-identical when the tree is; that identity is the landing condition.

Stages: oracle (pure Python, the frozen evidence is self-consistent), kernel (the placement reproduces the
oracle natively; the corpus; the mirrored sign table as the control that shows the rows can redden),
workshop (an edit is a new authority and the witnesses say what it moved; the planted falsifiers bite),
hud (the overlay is a frame: pinned, index-free, inside its region, reading state and not materials).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORACLE = os.path.join(ROOT, "oracle")
KERNEL = os.path.join(ROOT, "kernel")
WORKSHOP = os.path.join(ROOT, "workshop")
BUILD = os.path.join(ROOT, "verify", "build")
RUSTC = shutil.which("rustc")
FLAGS = ["-O"]
EXE = ".exe" if os.name == "nt" else ""

ROWS: list[tuple[str, str, str]] = []   # (status, name, text)


class Skip(Exception):
    pass


class Red(Exception):
    pass


def row(name, fn):
    try:
        text = fn()
        ROWS.append(("PASS", name, text))
    except Skip as e:
        ROWS.append(("SKIP", name, str(e)))
    except Red as e:
        ROWS.append(("FAIL", name, str(e)))
    except Exception as e:  # a crash is a red row, never a missing one
        ROWS.append(("FAIL", name, f"{type(e).__name__}: {e}"))
    st, _, text = ROWS[-1]
    print(f"[{st}] {name:<28} {text}")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def read(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def oracle() -> dict:
    with open(os.path.join(ORACLE, "urdr-oracle-1.json"), encoding="utf-8") as fh:
        return json.load(fh)


def corpus() -> dict:
    with open(os.path.join(ORACLE, "witnesses.json"), encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------ the toolchain
def need_rustc():
    if RUSTC is None:
        raise Skip("rustc not found — row skipped, count-stable")


def compile_rs(src_dir: str, main: str, out: str, source_override: dict | None = None) -> str:
    """rustc a single-file crate (with #[path] modules) from src_dir; optional {filename: text} overrides
    are written into a scratch copy of the directory first. Returns the executable path."""
    need_rustc()
    os.makedirs(BUILD, exist_ok=True)
    src = src_dir
    if source_override:
        src = os.path.join(BUILD, "src-" + os.path.basename(out))
        if os.path.isdir(src):
            shutil.rmtree(src)
        os.makedirs(src)
        for name in os.listdir(src_dir):
            if name.endswith(".rs"):
                shutil.copy(os.path.join(src_dir, name), os.path.join(src, name))
        for name, text in source_override.items():
            with open(os.path.join(src, name), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
    exe = os.path.join(BUILD, out + EXE)
    cp = subprocess.run([RUSTC] + FLAGS + [os.path.join(src, main), "-o", exe], capture_output=True, text=True)
    if cp.returncode != 0:
        raise Red("rustc failed: " + cp.stderr.strip().splitlines()[0])
    return exe


def run(exe: str, args: list[str]) -> tuple[int, str, str]:
    cp = subprocess.run([exe] + args, capture_output=True, text=True)
    return cp.returncode, cp.stdout, cp.stderr


def kernel_lines(exe: str, level: str, tiles: str, camera: str, extra: list[str] | None = None) -> dict:
    code, out, err = run(exe, ["--level", os.path.join(ORACLE, "levels", level + ".lvl"),
                               "--tiles", os.path.join(ORACLE, "tiles", tiles + ".tiles"), "--camera", camera] + (extra or []))
    if code != 0:
        raise Red(f"kernel exited {code}: {err.strip()}")
    lines = dict(ln.split(" ", 1) for ln in out.strip().splitlines() if " " in ln)
    if lines.get("selfcheck") != "OK":
        raise Red("kernel selfcheck DIVERGED")
    return lines


def witnesses(exe: str, level: str, tiles: str, camera: str) -> tuple[str, str]:
    lines = kernel_lines(exe, level, tiles, camera)
    return lines["frame"], lines["pixels"]


def hud_lines(exe: str, level: str, tiles: str, camera: str) -> dict:
    """frame, pixels, hud_overlay, hud, inside, outside — one --hud run."""
    lines = kernel_lines(exe, level, tiles, camera, ["--hud"])
    reg = dict(kv.split("=") for kv in lines["hud_region"].split())
    return {"frame": lines["frame"], "pixels": lines["pixels"], "hud_overlay": lines["hud_overlay"], "hud": lines["hud"],
            "inside": int(reg["inside"]), "outside": int(reg["outside"])}


def camera_of(entry: dict) -> str:
    x, z, f = entry["camera"]
    return f"{x},{z},{f}"


# ------------------------------------------------------------------ oracle
def oracle_frozen():
    o, c = oracle(), corpus()
    if c["origin"]["tag"] != "urdr-oracle-1" or c["origin"]["commit"] != "4c8c2451d942ff320a11501b59fbbf2737ec42ce":
        raise Red("the corpus names another origin than the oracle")
    for name, lv in c["levels"].items():
        b = read(os.path.join(ORACLE, "levels", name + ".lvl"))
        if len(b) != lv["bytes"] or sha256(b) != lv["W"]:
            raise Red(f"level {name}: W does not match its file")
        if b[:8] != b"VRDNLVL1":
            raise Red(f"level {name}: magic")
    for name, tl in c["tiles"].items():
        b = read(os.path.join(ORACLE, "tiles", name + ".tiles"))
        if len(b) != tl["bytes"] or sha256(b) != tl["M"]:
            raise Red(f"tiles {name}: M does not match its file")
    w = c["scenes"]["witness"]["witnesses"]
    if w["identity"]["frame"] != o["frame_digest_urdrfb1"] or w["identity"]["pixels"] != o["identity_pixels_sha256"]:
        raise Red("the corpus's witness scene disagrees with urdr-oracle-1.json")
    if w["oriented"]["pixels"] != o["oriented_pixels_sha256"] or c["tiles"]["oriented"]["urdr_tiles_digest"] != o["oriented_tiles_digest"]:
        raise Red("the corpus's oriented witnesses disagree with urdr-oracle-1.json")
    if c["scenes"]["corridor"]["level"] != c["scenes"]["pointblank"]["level"]:
        raise Red("corridor and pointblank must share a level (the camera-only pair)")
    n_sc, n_w = len(c["scenes"]), sum(len(e["witnesses"]) for e in c["scenes"].values())
    return (f"{len(c['levels'])} levels (W = sha256 of the file), {len(c['tiles'])} tile sets (M), {n_sc} scenes, "
            f"{n_w} witnesses, all frozen from Urðr @ {c['origin']['commit'][:7]}; the witness scene's frame, "
            f"identity pixels and oriented pixels equal urdr-oracle-1.json, and D_0 is carried as evidence only")


# ------------------------------------------------------------------ kernel
KERNEL_EXE: str | None = None


def kernel_build():
    global KERNEL_EXE
    KERNEL_EXE = compile_rs(KERNEL, "main.rs", "kernel")
    return "kernel/main.rs (+ mantle.rs, formats.rs, hud.rs) compiled live with " + " ".join(FLAGS)


def kernel_oracle():
    need_rustc()
    o = oracle()
    fd, ps = witnesses(KERNEL_EXE, "witness", "identity", "34,28,W")
    fd2, ps2 = witnesses(KERNEL_EXE, "witness", "identity", "34,28,W")
    if (fd, ps) != (fd2, ps2):
        raise Red("two runs disagree")
    if fd != o["frame_digest_urdrfb1"]:
        raise Red(f"frame digest {fd[:12]} != oracle {o['frame_digest_urdrfb1'][:12]}")
    if ps != o["identity_pixels_sha256"]:
        raise Red(f"pixel sha {ps[:12]} != oracle {o['identity_pixels_sha256'][:12]}")
    return (f"the placement reproduces the oracle natively, twice: frame {fd[:12]}… and identity pixels {ps[:12]}… "
            f"at ({o['view']['pos'][0]}, {o['view']['pos'][1]}) facing {o['view']['facing']}, seed {o['view']['seed']} depth "
            f"{o['view']['depth']} — the two of the oracle's three hashes a kernel can earn (D_0 is Urðr's CORE identity)")


def kernel_corpus():
    need_rustc()
    c = corpus()
    n = 0
    for name, e in c["scenes"].items():
        frames = set()
        for tname, w in e["witnesses"].items():
            fd, ps = witnesses(KERNEL_EXE, e["level"], tname, camera_of(e))
            if fd != w["frame"]:
                raise Red(f"{name}/{tname}: frame {fd[:12]} != frozen {w['frame'][:12]}")
            if ps != w["pixels"]:
                raise Red(f"{name}/{tname}: pixels {ps[:12]} != frozen {w['pixels'][:12]}")
            frames.add(fd)
            n += 1
        if len(frames) != 1:
            raise Red(f"{name}: the tile sets do not share one frame digest — a tile moved an index")
    return (f"{n} witnesses over {len(c['scenes'])} scenes x {len(c['tiles'])} tile sets equal the frozen values bit for bit, "
            f"and within each scene the tile sets share one frame digest (the lookup moves no index)")


def kernel_selftest():
    """The control: a mirrored sign table must move every oriented picture and no frame digest and no identity
    picture — the live comparison is load-bearing, and the two witnesses are distinct quantities."""
    need_rustc()
    src = read(os.path.join(KERNEL, "mantle.rs")).decode("utf-8")
    anchor = "const U_SIGN: [i64; 6] = [-1, 1, 0, 0, 1, -1];"
    if src.count(anchor) != 1:
        raise Red("the sign-table anchor is not where the selftest expects it")
    mutated = src.replace(anchor, "const U_SIGN: [i64; 6] = [1, -1, 0, 0, -1, 1];")
    exe = compile_rs(KERNEL, "main.rs", "kernel-mirrored", {"mantle.rs": mutated})
    c = corpus()
    moved, kept_frames, kept_identity = 0, 0, 0
    for name, e in c["scenes"].items():
        for tname, w in e["witnesses"].items():
            fd, ps = witnesses(exe, e["level"], tname, camera_of(e))
            if fd != w["frame"]:
                raise Red(f"{name}/{tname}: the mirrored sign table moved a FRAME digest")
            kept_frames += 1
            if tname == "identity":
                if ps != w["pixels"]:
                    raise Red(f"{name}: the mirrored sign table moved an IDENTITY picture")
                kept_identity += 1
            else:
                if ps == w["pixels"]:
                    raise Red(f"{name}/{tname}: the mirrored sign table did not move the oriented picture — the row is vacuous")
                moved += 1
    return (f"a mirrored sign table moves {moved} of {moved} oriented pictures and no frame digest ({kept_frames}) and no "
            f"identity picture ({kept_identity}): the rows above can redden, and geometry and appearance are distinct witnesses")


# ------------------------------------------------------------------ workshop
EDIT_EXE: str | None = None
WS = os.path.join(BUILD, "ws")
WITNESS_ARGS = ["--level", os.path.join(ORACLE, "levels", "witness.lvl"), "--tiles", os.path.join(ORACLE, "tiles", "identity.tiles"), "--camera", "34,28,W"]


def workshop_build():
    global EDIT_EXE
    EDIT_EXE = compile_rs(WORKSHOP, "edit.rs", "edit")
    if os.path.isdir(WS):
        shutil.rmtree(WS)
    os.makedirs(WS)
    return "workshop/edit.rs compiled live over the kernel's own mantle.rs and formats.rs (no mirror: one traversal, one emission)"


def record(name: str, spec: str, extra: list[str] | None = None) -> dict:
    """Run `edit record` for a spec on the witness authority; return the parsed record (or refuse typed)."""
    args = ["record"] + (extra if extra is not None else WITNESS_ARGS) + ["--edit", spec, "--out-dir", WS, "--name", name]
    code, out, _err = run(EDIT_EXE, args)
    if code != 0:
        raise Red(f"record refused: {out.strip().splitlines()[0] if out.strip() else code}")
    with open(os.path.join(WS, name + ".record.json"), encoding="utf-8") as fh:
        return json.load(fh)


def refusal(name: str, spec: str) -> str:
    """`edit record` must refuse typed; returns the refusal line."""
    code, out, _err = run(EDIT_EXE, ["record"] + WITNESS_ARGS + ["--edit", spec, "--out-dir", WS, "--name", name])
    line = out.strip().splitlines()[0] if out.strip() else ""
    if code != 2 or not line.startswith("WORKSHOP-REFUSE: INVALID-EDIT"):
        raise Red(f"{spec!r} was not refused as INVALID-EDIT: exit {code} {line}")
    return line


def check(path: str) -> tuple[int, str]:
    code, out, _err = run(EDIT_EXE, ["check", "--record", path])
    return code, (out.strip().splitlines()[0] if out.strip() else "")


def check_ok(name: str) -> str:
    code, line = check(os.path.join(WS, name + ".record.json"))
    if code != 0 or not line.startswith("CHECK OK"):
        raise Red(f"check of {name}: exit {code} {line}")
    return line


def tampered(name: str, suffix: str, mutate) -> str:
    """Write a tampered copy of a record beside the original (same files) and return its path."""
    with open(os.path.join(WS, name + ".record.json"), encoding="utf-8") as fh:
        r = json.load(fh)
    mutate(r)
    path = os.path.join(WS, f"{name}.{suffix}.record.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(r, fh, indent=1)
    return path


def must_refuse(path: str, code_word: str) -> str:
    code, line = check(path)
    if code != 2 or not line.startswith("WORKSHOP-REFUSE: " + code_word):
        raise Red(f"expected {code_word}, got exit {code}: {line}")
    return line


def signature(r: dict, name: str, w: bool, m: bool, strips: bool, frame: bool) -> dict:
    c = r["consequence"]
    if c["signature"] != name:
        raise Red(f"signature {c['signature']!r}, expected {name!r}")
    if (c["w_moved"], c["m_moved"], c["strips_moved"], c["frame_moved"], c["camera_carried"]) != (w, m, strips, frame, True):
        raise Red(f"signature fields {c}")
    if c["columns_unexplained"] != 0:
        raise Red(f"{c['columns_unexplained']} columns changed pixels with nothing behind them")
    if r["before"]["camera"] != r["after"]["camera"]:
        raise Red("the camera was not carried")
    return c


def workshop_seed():
    need_rustc()
    r = record("seed", "level:" + os.path.join(ORACLE, "levels", "neighbour.lvl"))
    c = signature(r, "geometry", True, False, True, True)
    if c["strips_changed"] == 0 or c["pixels_changed"] == 0:
        raise Red("a new level moved nothing")
    check_ok("seed")
    return (f"another frozen authority under the carried camera (34, 28, W) — signature geometry: W moved, M unmoved, "
            f"strips moved in {c['strips_changed']} of 1920 columns, the index in {c['index_changed']}, pixels in {c['columns_changed']} "
            f"({c['pixels_changed']} pixels, {c['pixels_permille']} permille), 0 unexplained; the record re-derives (CHECK OK); "
            f"the after level is a file whose sha256 is the new W")


def workshop_cell():
    need_rustc()
    r = record("cell", "cell:31,27,.")
    c = signature(r, "geometry", True, False, True, True)
    if not (0 < c["strips_changed"] < 1920) or c["pixels_changed"] == 0:
        raise Red(f"one cell moved {c['strips_changed']} strips")
    check_ok("cell")
    return (f"one cell (31, 27) rock -> floor — signature geometry: W moved, M unmoved; the exact strip moved in {c['strips_changed']} "
            f"of 1920 columns, the index column in {c['index_changed']} (the seam ink of a neighbour counts), the pixels in "
            f"{c['columns_changed']} ({c['pixels_changed']} pixels, {c['pixels_permille']} permille) and in 0 columns without a strip or "
            f"an index behind them — with M unmoved, appearance moves only where geometry moved, at one grain or the other; "
            f"{1920 - c['columns_changed']} columns untouched; the record re-derives")


def workshop_tile():
    need_rustc()
    r = record("tile", "tile:floor,96,80,64")
    c = signature(r, "material", False, True, False, False)
    if c["strips_changed"] != 0 or c["index_changed"] != 0 or c["pixels_changed"] == 0:
        raise Red(f"a material edit moved {c['strips_changed']} strips / {c['index_changed']} index columns")
    check_ok("tile")
    return (f"one material (the floor tile, recoloured flat) — signature material: M moved, W unmoved, the strips and the frame digest "
            f"UNMOVED, 0 strips and 0 index columns changed — the lookup moves no index, as a consequence row — while "
            f"{c['pixels_changed']} pixels ({c['pixels_permille']} permille) in {c['columns_changed']} columns changed; the authority moved "
            f"and the geometry did not, so no biconditional over geometry can be a law here")


def workshop_identity():
    need_rustc()
    r = record("none", "none")
    c = signature(r, "identity", False, False, False, False)
    if c["strips_changed"] or c["index_changed"] or c["pixels_changed"]:
        raise Red("the identity edit moved something")
    check_ok("none")
    return "the identity edit — signature identity: W, M, camera, strips, frame and pixels all unmoved, 0 columns — an honest no-op is accepted, so the refusals below are not vacuous"


def workshop_outside():
    """The arm a biconditional would refuse: the authority moved and nothing on screen did."""
    need_rustc()
    r = record("outside", "cell:1,1,.")
    c = signature(r, "outside-view", True, False, False, False)
    if c["columns_changed"] or c["pixels_changed"]:
        raise Red("the far corner moved a pixel")
    line = check_ok("outside")
    if not line.startswith("CHECK OK outside-view"):
        raise Red(line)
    return ("cell (1, 1) rock -> floor, out of the camera's view — signature outside-view: W moved; strips, frame and pixels UNMOVED; "
            "0 columns; CHECK OK. An edit the world accepts and the screen does not see is a consequence, not a fault: the proposed "
            "biconditional authority-moved <=> projection-moved would refuse it as VACUOUS-EDIT")


def workshop_census():
    """The off-gate census record re-derives its provenance and states the number."""
    path = os.path.join(ROOT, "workshop", "attest", "census-witness.json")
    with open(path, encoding="utf-8") as fh:
        r = json.load(fh)
    c = corpus()
    if r["name"] != "verdandi-edit-census" or r["version"] != 1:
        raise Red("not a census record")
    if r["W"] != c["levels"]["witness"]["W"] or r["M"] != c["tiles"]["identity"]["M"]:
        raise Red("the census was not taken on the frozen witness authority")
    w = c["scenes"]["witness"]["witnesses"]["identity"]
    if r["base"]["frame"] != w["frame"] or r["base"]["pixels"] != w["pixels"] or r["camera"] != c["scenes"]["witness"]["camera"]:
        raise Red("the census's base witnesses are not the corpus's")
    if r["impossible"] != 0 or r["unexplained_columns_total"] != 0:
        raise Red(f"impossible {r['impossible']}, unexplained {r['unexplained_columns_total']}")
    sig = r["signatures"]
    if sum(sig.values()) != r["tested"]:
        raise Red("the signature counts do not sum to the edits tested")
    ov = sig.get("outside-view", 0)
    if ov == 0:
        raise Red("no outside-view edit in the census — the biconditional's refutation has no witness")
    return (f"workshop/attest/census-witness.json (off-gate, {r['tested']} single-cell edits of the witness level under (34, 28, W)): "
            f"{', '.join(f'{v} {k}' for k, v in sorted(sig.items(), key=lambda kv: -kv[1]))}; impossible 0; unexplained columns 0 — "
            f"{ov * 1000 // r['tested']} permille of legitimate edits move the authority and nothing on screen, and the one-directional laws "
            f"held on every edit; the record's provenance (W, M, camera, base witnesses) equals the frozen corpus")


def workshop_stale():
    need_rustc()

    def stale(r):
        r["after"]["strips"] = r["before"]["strips"]
        r["after"]["frame"] = r["before"]["frame"]
        r["after"]["pixels"] = r["before"]["pixels"]
    line = must_refuse(tampered("cell", "stale", stale), "STALE-PROJECTION")
    return "PLANT: the authoritative cell changed while the recorded projection stayed the old one — " + line.split(" ", 2)[2]


def workshop_projection():
    need_rustc()
    with open(os.path.join(WS, "cell.record.json"), encoding="utf-8") as fh:
        other = json.load(fh)["after"]["pixels"]

    def moved(r):
        r["after"]["pixels"] = other
    line = must_refuse(tampered("none", "proj", moved), "PROJECTION-WITHOUT-AUTHORITY")
    return "PLANT: the picture changed while W, M and the camera did not — " + line.split(" ", 2)[2]


def workshop_camera():
    need_rustc()

    def turn(r):
        r["after"]["camera"] = [34, 28, "N"]
    line = must_refuse(tampered("cell", "cam", turn), "CAMERA-MOVED")

    def turn_only(r):
        r["after"]["camera"] = [34, 28, "N"]
    line2 = must_refuse(tampered("none", "cam", turn_only), "CAMERA-MOVED")
    return ("PLANTS: a record whose camera turned beside a real edit, and one whose camera turned with no edit at all, are both refused "
            "as edit records, each with its own reason — " + line.split(" ", 2)[2] + " / " + line2.split(" ", 2)[2])


def workshop_authority():
    need_rustc()
    path = os.path.join(WS, "cell.after.lvl")
    original = read(path)
    b = bytearray(original)
    b[16 + 27 * 48 + 30] = ord(".")          # a second, unrecorded edit hidden in the after file
    with open(path, "wb") as fh:
        fh.write(b)
    try:
        line = must_refuse(os.path.join(WS, "cell.record.json"), "AUTHORITY-MISMATCH")
    finally:
        with open(path, "wb") as fh:
            fh.write(original)
    check_ok("cell")
    return "PLANT: one more cell changed in the after FILE than the record says — " + line.split(" ", 2)[2] + "; restored, the record re-derives again"


def workshop_invalid():
    need_rustc()
    lines = [
        refusal("bad", "cell:0,5,."),
        refusal("bad", "cell:34,28,#"),
        refusal("bad", "cell:99,5,."),
        refusal("bad", "level:" + os.path.join(ORACLE, "levels", "corridor.lvl")),
        refusal("bad", "cell:3,3,x"),
        refusal("bad", "tile:roof,1,2,3"),
    ]
    return (f"{len(lines)} edits refused before any projection — an opened border, the camera left in rock (by a cell and by a level), "
            f"a cell outside the level, a byte outside the alphabet, an unknown material — each INVALID-EDIT with its reason, and the old authority stands")


# ------------------------------------------------------------------ hud
PINS = os.path.join(ROOT, "verify", "pins", "hud-1.json")
HUD: dict = {}   # (scene, tiles) -> hud_lines, filled by hud_pins


def pins() -> dict:
    with open(PINS, encoding="utf-8") as fh:
        return json.load(fh)


def hud_pins():
    need_rustc()
    p, c = pins(), corpus()
    n = 0
    for name, e in c["scenes"].items():
        for tname in e["witnesses"]:
            h = hud_lines(KERNEL_EXE, e["level"], tname, camera_of(e))
            HUD[(name, tname)] = h
            want = p["scenes"][name][tname]
            if h["hud_overlay"] != want["hud_overlay"]:
                raise Red(f"{name}/{tname}: overlay {h['hud_overlay'][:12]} != pinned {want['hud_overlay'][:12]}")
            if h["hud"] != want["hud"]:
                raise Red(f"{name}/{tname}: composite {h['hud'][:12]} != pinned {want['hud'][:12]}")
            n += 1
    return (f"{n} composites and {n} overlay identities equal verify/pins/hud-1.json over {len(c['scenes'])} scenes x {len(c['tiles'])} tile sets "
            f"— Verðandi's first appearance authority, minted here and held under the four rows below")


def hud_index():
    need_rustc()
    c = corpus()
    for name, e in c["scenes"].items():
        for tname, w in e["witnesses"].items():
            h = HUD[(name, tname)]
            if h["frame"] != w["frame"]:
                raise Red(f"{name}/{tname}: the overlay moved the FRAME digest")
            if h["pixels"] != w["pixels"]:
                raise Red(f"{name}/{tname}: the overlay moved the VIEWPORT picture")
    return "with the overlay drawn, every frame digest and every viewport pixel sha equal the frozen corpus: the HUD moves no index and the certified picture is untouched underneath"


def hud_region():
    need_rustc()
    inside = set()
    for (name, tname), h in HUD.items():
        if h["outside"] != 0:
            raise Red(f"{name}/{tname}: the overlay changed {h['outside']} pixels OUTSIDE its declared region")
        if h["inside"] == 0:
            raise Red(f"{name}/{tname}: the overlay changed nothing — vacuous")
        inside.add(h["inside"])
    return (f"0 pixels changed outside the declared region in every scene; {min(inside)}..{max(inside)} changed inside "
            f"(the bar, the facing plate, the minimap and the reticle's arms; declared, not argued)")


def hud_materials():
    need_rustc()
    c = corpus()
    overlays = {}
    for name in c["scenes"]:
        ids = {HUD[(name, t)]["hud_overlay"] for t in c["tiles"]}
        if len(ids) != 1:
            raise Red(f"{name}: the overlay identity differs between tile sets — the HUD read a material")
        overlays[name] = ids.pop()
    # corridor and pointblank share a level and differ in camera only: the overlay must differ (it reads the camera)
    if overlays["corridor"] == overlays["pointblank"]:
        raise Red("corridor and pointblank (same level, different camera) have the same overlay — the HUD did not read the camera")
    distinct = len(set(overlays.values()))
    return (f"the overlay identity is the same under both tile sets in every scene (it reads geometry and the camera, never a material) "
            f"and differs between the {distinct} scenes, including the camera-only pair corridor/pointblank")


def hud_selftest():
    """Two plants against hud.rs: one pixel written outside the region must be counted; the facing frozen to W
    must move the pinned overlay of every scene not facing W and of no scene facing W."""
    need_rustc()
    src = read(os.path.join(KERNEL, "hud.rs")).decode("utf-8")
    a1 = "    let _ = reticle;\n"
    a2 = "        fill(out, *r, if i as u8 == scene.facing { WHITE } else { DIM });"
    if src.count(a1) != 1 or src.count(a2) != 1:
        raise Red("the selftest anchors are not where expected")
    stray = src.replace(a1, a1 + "    put(out, W / 2, 100, WHITE); // PLANT: one pixel outside the region\n")
    frozen = src.replace(a2, "        fill(out, *r, if i as u8 == 3 { WHITE } else { DIM }); // PLANT: the facing frozen")
    exe_a = compile_rs(KERNEL, "main.rs", "kernel-hud-stray", {"hud.rs": stray})
    exe_b = compile_rs(KERNEL, "main.rs", "kernel-hud-frozen", {"hud.rs": frozen})
    c, p = corpus(), pins()
    e = c["scenes"]["witness"]
    ha = hud_lines(exe_a, e["level"], "identity", camera_of(e))
    if ha["outside"] != 1:
        raise Red(f"the stray pixel was counted as {ha['outside']} outside — the region audit is not load-bearing")
    moved, kept = [], []
    for name, e in c["scenes"].items():
        hb = hud_lines(exe_b, e["level"], "identity", camera_of(e))
        same = hb["hud_overlay"] == p["scenes"][name]["identity"]["hud_overlay"]
        faces_w = e["camera"][2] == "W"
        if faces_w and not same:
            raise Red(f"{name} faces W and its overlay moved under the frozen-W plant")
        if not faces_w and same:
            raise Red(f"{name} does not face W and its overlay did not move under the frozen-W plant — the pins do not bite")
        (kept if faces_w else moved).append(name)
    return (f"PLANTS: one pixel outside the region is counted (outside=1); the facing frozen to W moves the pinned overlay of "
            f"{', '.join(moved)} and of none of {', '.join(kept)} (which face W) — the pins bite and the HUD reads the camera")


# ------------------------------------------------------------------ main
def main() -> int:
    print("VERÐANDI GATE")
    row("oracle-frozen", oracle_frozen)
    row("kernel-build", kernel_build)
    row("kernel-oracle", kernel_oracle)
    row("kernel-corpus", kernel_corpus)
    row("kernel-selftest", kernel_selftest)
    row("workshop-build", workshop_build)
    row("workshop-seed", workshop_seed)
    row("workshop-cell", workshop_cell)
    row("workshop-tile", workshop_tile)
    row("workshop-identity", workshop_identity)
    row("workshop-outside", workshop_outside)
    row("workshop-census", workshop_census)
    row("workshop-stale", workshop_stale)
    row("workshop-projection", workshop_projection)
    row("workshop-camera", workshop_camera)
    row("workshop-authority", workshop_authority)
    row("workshop-invalid", workshop_invalid)
    row("hud-pins", hud_pins)
    row("hud-index", hud_index)
    row("hud-region", hud_region)
    row("hud-materials", hud_materials)
    row("hud-selftest", hud_selftest)
    fails = sum(1 for st, _, _ in ROWS if st == "FAIL")
    skips = sum(1 for st, _, _ in ROWS if st == "SKIP")
    rowset = sha256("\n".join(name for _, name, _ in ROWS).encode("utf-8"))[:16]
    print("GATE FAILED" if fails else "GATE PASSED")
    print(f"RECONCILE  rowset {rowset}  {len(ROWS)} rows / {fails} fail / {skips} skipped")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
