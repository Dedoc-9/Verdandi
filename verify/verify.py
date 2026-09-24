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
hud (the overlay is a frame: pinned, index-free, inside its region, reading state and not materials),
records (RECORD-0: every record Verðandi mints passes the envelope's firewall, the two writers agree, and a
rung that produces a number on a host was preregistered with a failure condition),
shell (SHELL-0a: the blit-hash law headless — the shell shows the kernel's composite, the blit is an invertible
carrier of it, and a byte corrupted between kernel and blit is detectable; the window is the host's, cfg-gated).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envelope  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORACLE = os.path.join(ROOT, "oracle")
KERNEL = os.path.join(ROOT, "kernel")
WORKSHOP = os.path.join(ROOT, "workshop")
SHELL = os.path.join(ROOT, "shell")
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
    exe = os.path.join(BUILD, out + EXE)
    src = src_dir
    scratch = None
    if source_override:
        # A crate may reference a sibling directory (`#[path = "../kernel/mantle.rs"]`), so the scratch copy
        # must sit at the SAME place under the repo root as the real source dir — a sibling of `kernel/` — for
        # those relative paths to resolve. It is removed after the compile so the working tree stays clean.
        scratch = os.path.join(ROOT, ".gate-" + out)
        if os.path.isdir(scratch):
            shutil.rmtree(scratch)
        os.makedirs(scratch)
        for name in os.listdir(src_dir):
            if name.endswith(".rs"):
                shutil.copy(os.path.join(src_dir, name), os.path.join(scratch, name))
        for name, text in source_override.items():
            with open(os.path.join(scratch, name), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
        src = scratch
    try:
        cp = subprocess.run([RUSTC] + FLAGS + [os.path.join(src, main), "-o", exe], capture_output=True, text=True)
    finally:
        if scratch and os.path.isdir(scratch):
            shutil.rmtree(scratch)
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
    return envelope.read(os.path.join(WS, name + ".record.json"))["data"]


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


def tampered(name: str, suffix: str, mutate, reseal: bool = True) -> str:
    """Write a tampered copy of a record beside the original (same files) and return its path. The plants
    against `check`'s laws are RESEALED (a fresh chain hash) so that they reach the law they target; the
    envelope plants are not."""
    with open(os.path.join(WS, name + ".record.json"), encoding="utf-8") as fh:
        r = json.load(fh)
    mutate(r["data"])
    if reseal:
        r["chain_hash"] = envelope.chain_hash(r)
    path = os.path.join(WS, f"{name}.{suffix}.record.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(r, fh, indent=1, ensure_ascii=False)
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
    why = c.get("explanation")
    if why != "inside the view cone, occluded":
        raise Red(f"explanation {why!r}")
    return ("cell (1, 1) rock -> floor, out of the camera's view — signature outside-view: W moved; strips, frame and pixels UNMOVED; "
            "0 columns; CHECK OK; explanation computed and re-derived: inside the view cone, occluded. An edit the world accepts and the "
            "screen does not see is a consequence, not a fault: the proposed biconditional authority-moved <=> projection-moved would refuse it")


def workshop_census():
    """The off-gate census record re-derives its provenance, states the number, and holds the cone theorem."""
    path = os.path.join(ROOT, "workshop", "attest", "census-witness.json")
    r = envelope.read(path)
    c = corpus()
    if r["name"] != "verdandi-edit-census" or r["version"] != 2:
        raise Red("not a census record v2")
    pv, d = r["provenance"], r["data"]
    if pv["W"] != c["levels"]["witness"]["W"] or pv["M"] != c["tiles"]["identity"]["M"]:
        raise Red("the census was not taken on the frozen witness authority")
    w = c["scenes"]["witness"]["witnesses"]["identity"]
    if pv["base"]["frame"] != w["frame"] or pv["base"]["pixels"] != w["pixels"] or pv["camera"] != c["scenes"]["witness"]["camera"]:
        raise Red("the census's base witnesses are not the corpus's")
    if d["impossible"] != 0 or d["unexplained_columns_total"] != 0:
        raise Red(f"impossible {d['impossible']}, unexplained {d['unexplained_columns_total']}")
    sig = d["signatures"]
    if sum(sig.values()) != d["tested"]:
        raise Red("the signature counts do not sum to the edits tested")
    ov = sig.get("outside-view", 0)
    if ov == 0:
        raise Red("no outside-view edit in the census — the biconditional's refutation has no witness")
    cone = d["cone"]
    if cone["geometry_outside_cone"] != 0:
        raise Red(f"{cone['geometry_outside_cone']} geometry edits lie OUTSIDE the view cone — the cone theorem is false")
    if sum(cone["inside"].values()) + sum(cone["outside"].values()) != d["tested"]:
        raise Red("the cone split does not sum to the edits tested")
    ov_in, ov_out = cone["inside"].get("outside-view", 0), cone["outside"].get("outside-view", 0)
    return (f"workshop/attest/census-witness.json (off-gate, {d['tested']} single-cell edits of the witness level under (34, 28, W)): "
            f"{', '.join(f'{v} {k}' for k, v in sorted(sig.items(), key=lambda kv: -kv[1]))}; impossible 0; unexplained columns 0 — "
            f"{ov * 1000 // d['tested']} permille of legitimate edits move the authority and nothing on screen. THE CONE: every geometry edit "
            f"lies inside the view cone (0 outside); of the outside-view edits {ov_out} are outside the cone (a coordinate test could name them) "
            f"and {ov_in} inside it, occluded (only the traversal can); the record's provenance equals the frozen corpus and its chain hash seals it")


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
        other = json.load(fh)["data"]["after"]["pixels"]

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
    return envelope.read(PINS)


def hud_pins():
    need_rustc()
    p, c = pins(), corpus()
    n = 0
    for name, e in c["scenes"].items():
        for tname in e["witnesses"]:
            h = hud_lines(KERNEL_EXE, e["level"], tname, camera_of(e))
            HUD[(name, tname)] = h
            want = p["data"]["scenes"][name][tname]
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
        same = hb["hud_overlay"] == p["data"]["scenes"][name]["identity"]["hud_overlay"]
        faces_w = e["camera"][2] == "W"
        if faces_w and not same:
            raise Red(f"{name} faces W and its overlay moved under the frozen-W plant")
        if not faces_w and same:
            raise Red(f"{name} does not face W and its overlay did not move under the frozen-W plant — the pins do not bite")
        (kept if faces_w else moved).append(name)
    return (f"PLANTS: one pixel outside the region is counted (outside=1); the facing frozen to W moves the pinned overlay of "
            f"{', '.join(moved)} and of none of {', '.join(kept)} (which face W) — the pins bite and the HUD reads the camera")


# ------------------------------------------------------------------ records (RECORD-0)
def committed_records() -> list[str]:
    """Every record Verðandi mints and commits: the pins, the attest folders. The oracle folder is Urðr's evidence
    and is not enveloped (it is read-only here and verified by oracle-frozen)."""
    out = []
    for sub in ("verify/pins", "workshop/attest", "kernel/attest", "shell/attest"):
        d = os.path.join(ROOT, sub)
        if os.path.isdir(d):
            out += sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".json"))
    return out


def records_firewall():
    paths = committed_records()
    if not paths:
        raise Red("no committed records found")
    for p in paths:
        try:
            envelope.read(p)
        except envelope.EnvelopeViolation as e:
            raise Red(f"{os.path.relpath(p, ROOT)}: {e}")
    # the plants: a verdict-shaped key inside data, and a tampered hash — both must be refused by the Python reader
    base = envelope.read(paths[0])
    bad = json.loads(json.dumps(base))
    bad["data"]["verdict"] = "within"
    bad["chain_hash"] = envelope.chain_hash(bad)
    try:
        envelope.validate(bad)
        raise Red("a verdict-shaped key inside data passed the firewall")
    except envelope.EnvelopeViolation as e:
        if "verdict_field" not in str(e):
            raise Red(f"wrong refusal for the verdict plant: {e}")
    tam = json.loads(json.dumps(base))
    tam["data"] = {"tampered": 1, **tam["data"]}
    try:
        envelope.validate(tam)
        raise Red("a record whose data changed after sealing passed the firewall")
    except envelope.EnvelopeViolation as e:
        if "chain_hash" not in str(e):
            raise Red(f"wrong refusal for the tamper plant: {e}")
    names = ", ".join(os.path.relpath(p, ROOT) for p in paths)
    return (f"{len(paths)} committed records carry name, version, claim_class, provenance, a scope that says what it certifies, "
            f"forbidden interpretations and a chain hash over the required fields, with no verdict-shaped key inside data ({names}); "
            f"PLANTS: a `verdict` key inside data and a change after sealing are both refused")


def records_twins():
    """The Rust writer (workshop/edit.rs) and the Python reader agree on the canonical form: Python recomputes the chain
    hash of every record Rust sealed during this gate, and Rust refuses the Python-made plants."""
    need_rustc()
    rust_written = sorted(os.path.join(WS, f) for f in os.listdir(WS) if f.endswith(".record.json") and f.count(".") == 2)
    if len(rust_written) < 4:
        raise Red("expected the workshop's records to be present")
    for p in rust_written:
        envelope.read(p)   # validate() recomputes the chain hash in Python over Rust's bytes
    # Rust must refuse the Python-made plants at the envelope
    verdict_plant = tampered("cell", "verdict", lambda d: d.__setitem__("verdict", "within"))
    must_refuse(verdict_plant, "ENVELOPE")
    tamper_plant = tampered("cell", "tamper", lambda d: d.__setitem__("tampered", 1), reseal=False)
    must_refuse(tamper_plant, "ENVELOPE")
    # the two verdict-key sets are the same list
    src = read(os.path.join(WORKSHOP, "edit.rs")).decode("utf-8")
    start = src.index("const VERDICT_KEYS")
    body = src[src.index("= [", start) + 3:src.index("];", start)]
    rust_keys = set(re.findall(r'"([^"]+)"', body))
    if rust_keys != set(envelope.VERDICT_KEYS):
        raise Red(f"the two firewalls disagree on the verdict keys: {sorted(rust_keys ^ set(envelope.VERDICT_KEYS))}")
    census = envelope.read(os.path.join(ROOT, "workshop", "attest", "census-witness.json"))
    return (f"Python recomputes the chain hash of {len(rust_written)} records Rust sealed in this run and of the committed census "
            f"({census['chain_hash'][:12]}…); Rust refuses a verdict key and a post-seal change made in Python (ENVELOPE); "
            f"the two firewalls carry the same {len(rust_keys)} verdict-shaped keys")


def records_preregistered():
    path = os.path.join(ROOT, "verify", "preregister.json")
    with open(path, encoding="utf-8") as fh:
        reg = json.load(fh)
    if reg["name"] != "verdandi-preregistration":
        raise Red("not the registry")
    for rung, e in reg["entries"].items():
        for k in ("hypothesis", "success_condition", "failure_condition", "interpretation_limits", "instrument"):
            if not e.get(k):
                raise Red(f"{rung}: {k} missing — a rung without a failure condition is refused a seat")
        want = envelope.chain_hash({"name": "verdandi-preregistration-entry", "version": 1, "claim_class": "declared",
                                    "provenance": {"registered_in": "verify/preregister.json"},
                                    "validity_scope": {"certifies": f"the conditions {rung} was seated under"},
                                    "forbidden_interpretations": ["that registering a condition earns it"],
                                    "data": {k: v for k, v in e.items() if k != "chain_hash"}})
        if e["chain_hash"] != want:
            raise Red(f"{rung}: the entry was edited after registration (chain hash)")
    # every attest record of a preregistered rung must cite its entry's hash
    cited = []
    for p in committed_records():
        r = envelope.read(p)
        pr = r["provenance"].get("preregistered")
        if pr:
            rung, h = pr.get("rung"), pr.get("chain_hash")
            if rung not in reg["entries"] or reg["entries"][rung]["chain_hash"] != h:
                raise Red(f"{os.path.relpath(p, ROOT)} cites a registration that does not exist or was changed")
            cited.append(rung)
    locked = ", ".join("{} {}".format(k, v["chain_hash"][:8]) for k, v in reg["entries"].items())
    cite_note = " ({})".format(", ".join(cited)) if cited else " (none yet: SHELL-0's will be the first)"
    return (f"{len(reg['entries'])} rungs registered with hypothesis, success AND failure conditions and interpretation limits, each entry "
            f"hash-locked ({locked}); {len(cited)} committed records cite a registration" + cite_note)


# ------------------------------------------------------------------ shell (SHELL-0a)
SHELL_EXE: str | None = None


def shell_lines(exe: str, cmd: str, level: str, tiles: str, camera: str) -> dict:
    code, out, err = run(exe, [cmd, "--level", os.path.join(ORACLE, "levels", level + ".lvl"),
                               "--tiles", os.path.join(ORACLE, "tiles", tiles + ".tiles"), "--camera", camera])
    if code != 0:
        raise Red(f"shell {cmd} exited {code}: {err.strip()}")
    return dict(ln.split(" ", 1) for ln in out.strip().splitlines() if " " in ln)


def shell_build():
    global SHELL_EXE
    SHELL_EXE = compile_rs(SHELL, "main.rs", "shell")
    # the window is behind `--cfg shell_window`, which the gate never passes, so win32.rs is out of this build on
    # EVERY host (not only non-Windows) and the gate stays host-independent
    r1, o1, e1 = run(SHELL_EXE, ["run", "--level", os.path.join(ORACLE, "levels", "witness.lvl"),
                                 "--tiles", os.path.join(ORACLE, "tiles", "identity.tiles"), "--camera", "34,28,W"])
    _ = (r1, o1, e1)
    return ("shell/main.rs (+ the kernel's mantle.rs, formats.rs, hud.rs, present.rs) compiled live; the Win32 window "
            "(shell/win32.rs) is behind `--cfg shell_window`, which the gate never passes, so it is out of this build on "
            "every host — the blit-hash law below is what the gate exercises")


def shell_blit_pins():
    need_rustc()
    p, c, hud = envelope.read(os.path.join(ROOT, "verify", "pins", "shell-1.json")), corpus(), pins()
    n = 0
    for name, e in c["scenes"].items():
        for tname in e["witnesses"]:
            d = shell_lines(SHELL_EXE, "witness", e["level"], tname, camera_of(e))
            want = p["data"]["scenes"][name][tname]
            if d["composite"] != want["composite"] or d["blit"] != want["blit"]:
                raise Red(f"{name}/{tname}: shell witness ({d['composite'][:12]}, {d['blit'][:12]}) != pins")
            if d["composite"] != hud["data"]["scenes"][name][tname]["hud"]:
                raise Red(f"{name}/{tname}: the shell's composite is not the kernel's HUD composite")
            n += 1
    return (f"{n} composites and {n} blit witnesses equal verify/pins/shell-1.json, and every composite equals the HUD composite the "
            f"kernel minted — the shell shows the kernel's picture and hands the OS exactly its BGR top-down bytes")


def shell_blit_law():
    need_rustc()
    c = corpus()
    n = 0
    for name, e in c["scenes"].items():
        for tname in e["witnesses"]:
            d = shell_lines(SHELL_EXE, "selfcheck", e["level"], tname, camera_of(e))
            if d.get("blit_roundtrip") != "OK":
                raise Red(f"{name}/{tname}: from_blit(to_blit(composite)) != composite")
            n += 1
    # the Linux build has no window and says so rather than pretending to present
    code, out, _err = run(SHELL_EXE, ["run", "--level", os.path.join(ORACLE, "levels", "witness.lvl"),
                                      "--tiles", os.path.join(ORACLE, "tiles", "identity.tiles"), "--camera", "34,28,W"])
    line = (out.strip().splitlines() or [""])[0]
    # the refusal is on stderr; re-run capturing it
    cp = subprocess.run([SHELL_EXE, "run", "--level", os.path.join(ORACLE, "levels", "witness.lvl"),
                         "--tiles", os.path.join(ORACLE, "tiles", "identity.tiles"), "--camera", "34,28,W"], capture_output=True, text=True)
    if cp.returncode != 2 or "SHELL-NO-WINDOW" not in cp.stderr:
        raise Red(f"a windowless build did not refuse `run`: exit {cp.returncode} {cp.stderr.strip()[:60]}")
    _ = line
    return (f"the blit round-trip holds on all {n} corpus composites (the transform carries the kernel's bytes intact), and a build "
            f"with no window refuses `run` (SHELL-NO-WINDOW) rather than pretending to present")


def shell_blit_plant():
    """The plant: a to_blit that drops the red channel (writes 0). The blit witness must move on the witness scene and
    the round-trip must break — a corrupted present path is detectable."""
    need_rustc()
    src = read(os.path.join(SHELL, "present.rs")).decode("utf-8")
    anchor = "        out[i * 3 + 2] = rgb[i * 3]; // R"
    if src.count(anchor) != 1:
        raise Red("the blit-plant anchor is not where expected")
    corrupted = src.replace(anchor, "        out[i * 3 + 2] = 0; // PLANT: the present path drops red")
    exe = compile_rs(SHELL, "main.rs", "shell-plant", {"present.rs": corrupted})
    p = envelope.read(os.path.join(ROOT, "verify", "pins", "shell-1.json"))
    d = shell_lines(exe, "witness", "witness", "identity", "34,28,W")
    if d["blit"] == p["data"]["scenes"]["witness"]["identity"]["blit"]:
        raise Red("the corrupted present path produced the pinned blit witness — the law is not load-bearing")
    sc = shell_lines(exe, "selfcheck", "witness", "identity", "34,28,W")
    if sc.get("blit_roundtrip") != "BROKEN":
        raise Red("a corrupted to_blit still round-trips — the law does not bite")
    return ("PLANT: a present path that drops the red channel moves the blit witness off the pin AND breaks the round-trip "
            "(blit_roundtrip BROKEN) — the shell hashing what it blits catches a picture the kernel did not make")


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
    row("records-firewall", records_firewall)
    row("records-twins", records_twins)
    row("records-preregistered", records_preregistered)
    row("shell-build", shell_build)
    row("shell-blit-pins", shell_blit_pins)
    row("shell-blit-law", shell_blit_law)
    row("shell-blit-plant", shell_blit_plant)
    fails = sum(1 for st, _, _ in ROWS if st == "FAIL")
    skips = sum(1 for st, _, _ in ROWS if st == "SKIP")
    rowset = sha256("\n".join(name for _, name, _ in ROWS).encode("utf-8"))[:16]
    print("GATE FAILED" if fails else "GATE PASSED")
    print(f"RECONCILE  rowset {rowset}  {len(ROWS)} rows / {fails} fail / {skips} skipped")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
