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
rung that produces a number on a host was preregistered with a failure condition; LATENCY-0's method — the
SOFTWARE-144-BUDGET / HARDWARE-144 split, their conjunction, and the honest scope — and GAUNTLET-0's method —
the render breakdown and its 500-permille optimization decision rule, with GAUNTLET-1 owing byte-identity before
any speed claim — are hash-locked before any host number, so weakening either is a visible diff),
gauntlet1 (GAUNTLET-1a: the emit differential court — a sibling fast.rs emit, seeded as an exact transcription, is
byte-identical to the frozen mantle.rs emit over the corpus plus adversarial cameras (candidate -> frozen, never
the reverse); a deterministic region measure names the floor's per-row divides as GAUNTLET-1b's target; and the
acceptance/promotion rule (byte-identity mandatory, speed a separate court) is hash-locked before any candidate),
shell (SHELL-0a: the blit-hash law headless — the shell shows the kernel's composite, the blit is an invertible
carrier of it, and a byte corrupted between kernel and blit is detectable; the window is the host's, cfg-gated),
membrane (MEMBRANE-0: the one-way law as a compile-time wall — editing the authority through a live read-borrow
does not compile, while read-then-edit does and renders the kernel's witnesses),
text (TEXT-0: the level as text — round-trips to the same W, and tells a reformat from an edit: a comment or
blank line moves the authoring digest and not W, a cell edit moves both),
workshop1 (WORKSHOP-1: the log is the history — a session is a base authority + a hash-chained cell/tile edit
log; undo is replay, propose is a scratchpad, tampering breaks the chain; a Python twin re-derives the head),
input (INPUT-0: moving around is the projection's job — a typed command log (L/R/F/B/Q/E) moves the camera
against a FIXED level, blocked by rock, and replays headless to a head that chains each step's kernel frame
digest; a walk never touches W or M, a tampered command breaks the chain, and a Python twin re-derives the head),
sessionwalk (SESSION-WALK: move while authoring — ONE interleaved append-only log of edits AND moves, each
evaluated in log order against the authority the preceding events produced, folded into a single head; a move
sees a prior edit (order is meaning), the head is checkpoint/replay-equivalent (batching cannot change it),
dropping moves leaves W,M and dropping edits changes navigation, and a Python twin re-derives the head),
shell-playback (SHELL-PLAYBACK: the window shows exactly the sealed becoming — playback consumes a sealed
SESSION-WALK, replays it through the SHELL-0 present path, and its composited frame-digest sequence EQUALS the
session's per-move witnesses; every frame passes the blit law, playback writes no authority, a tampered/reordered
input diverges rather than minting a new authority, and replay from any certified checkpoint reproduces the head).
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


def latency_preregistered():
    """LATENCY-0's METHOD is locked before any host number: the two independent conditions, the 144Hz budget, the
    conjunction, and the honest scope limits are asserted here, so weakening the method is a visible code diff (this
    row reddens) rather than a silent data edit that re-hashes the entry."""
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))
    e = reg["entries"].get("LATENCY-0")
    if not e:
        raise Red("LATENCY-0 is not registered")
    succ, fail = e["success_condition"], e["failure_condition"]
    lims = " ".join(e["interpretation_limits"]).lower()
    checks = {
        "SOFTWARE-144-BUDGET named in both conditions": "SOFTWARE-144-BUDGET" in succ and "SOFTWARE-144-BUDGET" in fail,
        "HARDWARE-144 named in both conditions": "HARDWARE-144" in succ and "HARDWARE-144" in fail,
        "the 144Hz budget is 6944 us": "6944" in succ and "6944" in fail,
        "the claim is conjunctive (A AND B)": "SUSTAINED-144Hz = SOFTWARE-144-BUDGET AND HARDWARE-144" in succ,
        "the budget is named a budget, not a refresh claim": "budget condition" in lims and "not a refresh-rate claim" in lims,
        "refresh is measured, not inferred": "measured from the dwmflush" in lims,
        "input-to-photon is out of scope": "not input-to-photon" in lims,
    }
    missing = [k for k, ok in checks.items() if not ok]
    if missing:
        raise Red("the LATENCY-0 method is not fully locked: " + "; ".join(missing))
    want = envelope.chain_hash({"name": "verdandi-preregistration-entry", "version": 1, "claim_class": "declared",
                                "provenance": {"registered_in": "verify/preregister.json"},
                                "validity_scope": {"certifies": "the conditions LATENCY-0 was seated under"},
                                "forbidden_interpretations": ["that registering a condition earns it"],
                                "data": {k: v for k, v in e.items() if k != "chain_hash"}})
    if e["chain_hash"] != want:
        raise Red("the LATENCY-0 entry was edited after registration (chain hash)")
    return ("LATENCY-0's method is locked before any host number: two independent MEASURED conditions (SOFTWARE-144-BUDGET, p99 "
            "frame-ready->composited <= 6944 us; HARDWARE-144, measured refresh >= 144 Hz), the sustained-144Hz claim is their "
            "conjunction, the budget is named a budget (not a refresh-rate claim), refresh is measured not inferred, and "
            "input-to-photon is out of scope; hash-locked %s so weakening it is a visible diff, not a silent edit" % e["chain_hash"][:8])


def gauntlet_preregistered():
    """GAUNTLET-0's method and DECISION RULE are locked before the host number: the render is decomposed at pub-phase
    boundaries, a phase must clear 500 permille of the render p99 to earn GAUNTLET-1, GAUNTLET-1 must prove byte-identity
    before any speed claim, the witness hashes are verification-only, and mantle.rs is not touched. Weakening any of these
    is a visible code diff, not a silent re-hash."""
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))
    e = reg["entries"].get("GAUNTLET-0")
    if not e:
        raise Red("GAUNTLET-0 is not registered")
    hyp, succ, fail = e["hypothesis"], e["success_condition"], e["failure_condition"]
    lims = " ".join(e["interpretation_limits"]).lower()
    checks = {
        "the render phases are named": all(p in hyp for p in ("strips", "frame", "emit")),
        "the 500-permille decision rule is in success AND failure": "500 permille" in succ and "500 permille" in fail,
        "GAUNTLET-1 must prove byte-identity before a speed claim": "byte-identical" in succ and "differential oracle" in succ,
        "the floor-cast hypothesis can die here": "incremental floor cast" in fail and "dies" in fail,
        "the witness hashes are verification-only, not render cost": "verification cost" in lims and "not interactive-render cost" in lims,
        "mantle.rs is not modified": "mantle.rs is not modified" in lims,
        "a breakdown is a target-finder, not a speed improvement": "target-finder" in lims and "not a speed improvement" in lims,
    }
    missing = [k for k, ok in checks.items() if not ok]
    if missing:
        raise Red("the GAUNTLET-0 method is not fully locked: " + "; ".join(missing))
    want = envelope.chain_hash({"name": "verdandi-preregistration-entry", "version": 1, "claim_class": "declared",
                                "provenance": {"registered_in": "verify/preregister.json"},
                                "validity_scope": {"certifies": "the conditions GAUNTLET-0 was seated under"},
                                "forbidden_interpretations": ["that registering a condition earns it"],
                                "data": {k: v for k, v in e.items() if k != "chain_hash"}})
    if e["chain_hash"] != want:
        raise Red("the GAUNTLET-0 entry was edited after registration (chain hash)")
    return ("GAUNTLET-0's method and decision rule are locked before the host number: the render is decomposed at pub-phase "
            "boundaries (strips/frame/emit) with the two witness hashes reported separately as verification-only cost; a render "
            "phase must clear 500 permille of the render p99 to earn a GAUNTLET-1 seat (the incremental-floor-cast hypothesis "
            "dies here unless frame() qualifies), GAUNTLET-1 must prove byte-identity (a differential oracle) before any speed "
            "claim, and mantle.rs is not touched; hash-locked %s" % e["chain_hash"][:8])


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


# ------------------------------------------------------------------ membrane (MEMBRANE-0)
MEMBRANE_EXE: str | None = None


def compile_expect_fail(src_dir: str, main: str, out: str, extra_flags: list[str], want_error: str) -> str:
    """Compile with extra flags and REQUIRE rustc to fail with `want_error` in its output. Returns the first
    matching error line. The row that calls this passes iff the compile is refused for the named reason."""
    need_rustc()
    os.makedirs(BUILD, exist_ok=True)
    cp = subprocess.run([RUSTC] + FLAGS + extra_flags + [os.path.join(src_dir, main), "-o", os.path.join(BUILD, out)],
                        capture_output=True, text=True)
    if cp.returncode == 0:
        raise Red(f"the compile SUCCEEDED but the wall required it to fail ({want_error})")
    line = next((ln for ln in cp.stderr.splitlines() if want_error in ln), None)
    if line is None:
        raise Red(f"the compile failed but not with {want_error}: {cp.stderr.strip().splitlines()[:1]}")
    return line.strip()


def membrane_build():
    global MEMBRANE_EXE
    MEMBRANE_EXE = compile_rs(WORKSHOP, "membrane.rs", "membrane")
    return "workshop/membrane.rs compiled live (the legal build): Authority owns the world, Reading borrows it immutably, edit_cell needs &mut"


def membrane_witness():
    need_rustc()
    c = corpus()
    n = 0
    for name, e in c["scenes"].items():
        w = e["witnesses"]["identity"]
        code, out, err = run(MEMBRANE_EXE, ["witness", "--level", os.path.join(ORACLE, "levels", e["level"] + ".lvl"),
                                            "--tiles", os.path.join(ORACLE, "tiles", "identity.tiles"), "--camera", camera_of(e)])
        if code != 0:
            raise Red(f"{name}: membrane witness exited {code}: {err.strip()}")
        d = dict(ln.split(" ", 1) for ln in out.strip().splitlines() if " " in ln)
        if d["frame"] != w["frame"] or d["pixels"] != w["pixels"]:
            raise Red(f"{name}: the Reading path rendered ({d['frame'][:12]}, {d['pixels'][:12]}) != the kernel's witnesses")
        n += 1
    return (f"the render path through the typestate (Authority::read -> Reading::witnesses) reproduces the kernel's frame digest and "
            f"pixel sha on all {n} corpus scenes — the immutable-borrow wall carries identical semantics, it costs nothing")


def membrane_legal():
    need_rustc()
    code, out, err = run(MEMBRANE_EXE, ["legal", "--level", os.path.join(ORACLE, "levels", "witness.lvl"),
                                        "--tiles", os.path.join(ORACLE, "tiles", "identity.tiles"), "--camera", "34,28,W", "--edit", "31,27,."])
    line = out.strip().splitlines()[0] if out.strip() else ""
    if code != 0 or not line.startswith("legal OK"):
        raise Red(f"the legal read-then-edit sequence did not run: exit {code} {err.strip()[:60]}")
    return "the legal sequence — read the authority FULLY, drop the Reading, THEN edit, then read again — compiles and runs: " + line


def membrane_wall():
    """The row whose PASS is rustc's REFUSAL: compiled with --cfg membrane_probe_illegal, an edit through a live
    Reading must not borrow-check. The legal build (membrane-build) is the control that shows the file is otherwise
    sound, so the failure is the borrow and nothing else."""
    line = compile_expect_fail(WORKSHOP, "membrane.rs", "membrane-illegal", ["--cfg", "membrane_probe_illegal"], "E0502")
    return ("PLANT (a compile-fail row): editing the authority through a LIVE read-borrow does not compile — rustc refuses with "
            + line.split(": ", 1)[-1] + " — so the one-way law (render reads, never writes) is a compile-time wall, not only a runtime test")


# ------------------------------------------------------------------ text (TEXT-0)
TEXT_EXE = None
TXT = os.path.join(BUILD, "txt")


def text_build():
    global TEXT_EXE
    TEXT_EXE = compile_rs(WORKSHOP, "text.rs", "text")
    if os.path.isdir(TXT):
        shutil.rmtree(TXT)
    os.makedirs(TXT)
    return "workshop/text.rs compiled live: to-text (depth + #.<> grid), from-text (borrows a same-depth oracle level's palette), digests"


def _to_text(name):
    lvl = os.path.join(ORACLE, "levels", name + ".lvl")
    code, out, err = run(TEXT_EXE, ["to-text", "--level", lvl])
    if code != 0:
        raise Red("to-text %s: %s" % (name, err.strip()))
    path = os.path.join(TXT, name + ".wtxt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(out)
    return path


def _digests(text_path, palette):
    code, out, err = run(TEXT_EXE, ["digests", "--text", text_path, "--palette-from", os.path.join(ORACLE, "levels", palette + ".lvl")])
    if code != 0:
        raise Red("digests: " + err.strip())
    d = dict(ln.split(" ", 1) for ln in out.strip().splitlines() if " " in ln)
    return d["content"], d["authoring"]


def text_roundtrip():
    need_rustc()
    c = corpus()
    n = 0
    for name, lv in c["levels"].items():
        tp = _to_text(name)
        out_lvl = os.path.join(TXT, name + ".rt.lvl")
        code, _o, err = run(TEXT_EXE, ["from-text", "--text", tp, "--palette-from", os.path.join(ORACLE, "levels", name + ".lvl"), "--out", out_lvl])
        if code != 0:
            raise Red("from-text %s: %s" % (name, err.strip()))
        if sha256(read(out_lvl)) != lv["W"]:
            raise Red("%s: the round-trip level's W != the frozen W" % name)
        _c2, out2, _e = run(TEXT_EXE, ["to-text", "--level", out_lvl])
        with open(tp, encoding="utf-8") as fh:
            if out2 != fh.read():
                raise Red("%s: to_text(from_text(to_text(L))) is not byte-identical to to_text(L)" % name)
        n += 1
    return ("all %d corpus levels round-trip: from_text(to_text(L)) rebuilds the frozen VRDNLVL1 bytes (W unchanged), and the "
            "text form is canonical (re-emitting reproduces it byte for byte); the palette is borrowed from the same-depth level" % n)


def text_reformat():
    need_rustc()
    tp = _to_text("witness")
    c0, a0 = _digests(tp, "witness")
    with open(tp, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    reflowed = ["; a note added by a human", ""] + lines[:6] + ["", "; midway comment"] + lines[6:]
    rp = os.path.join(TXT, "witness.reformat.wtxt")
    with open(rp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(reflowed))
    c1, a1 = _digests(rp, "witness")
    if c1 != c0:
        raise Red("a reformat moved the CONTENT digest (%s -> %s)" % (c0[:12], c1[:12]))
    if a1 == a0:
        raise Red("a reformat did not move the authoring digest")
    return ("a reformat (a `;` comment, blank lines, a comment amid the grid) leaves W (content) UNMOVED at %s and moves the "
            "authoring digest %s -> %s: the record can tell a reformat from an edit" % (c0[:12], a0[:12], a1[:12]))


def text_edit():
    need_rustc()
    import struct as _s
    tp = _to_text("witness")
    c0, _a0 = _digests(tp, "witness")
    with open(tp, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    gi = lines.index("grid") + 1
    row = list(lines[gi + 27])
    if row[31] != "#":
        raise Red("the witness grid cell (31, 27) is %r, expected rock" % row[31])
    row[31] = "."
    lines[gi + 27] = "".join(row)
    ep = os.path.join(TXT, "witness.edit.wtxt")
    with open(ep, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    c1, _a1 = _digests(ep, "witness")
    if c1 == c0:
        raise Red("editing a grid cell did not move W")
    b = bytearray(read(os.path.join(ORACLE, "levels", "witness.lvl")))
    w = _s.unpack_from("<I", b, 8)[0]
    b[16 + 27 * w + 31] = ord(".")
    if sha256(bytes(b)) != c1:
        raise Red("the text edit's W does not equal the same cell flip applied to the VRDNLVL1 bytes")
    return ("flipping one grid cell (31, 27) rock -> floor moves W %s -> %s, and that W equals the same byte flip "
            "applied to the level file: the text's content IS the cells, exactly" % (c0[:12], c1[:12]))


def text_refuse():
    need_rustc()
    tp = _to_text("witness")
    got = []
    code, _o, err = run(TEXT_EXE, ["from-text", "--text", tp, "--palette-from", os.path.join(ORACLE, "levels", "room.lvl"), "--out", os.path.join(TXT, "x.lvl")])
    if code != 2 or "TEXT-INVALID-TEXT" not in err or "depth" not in err:
        raise Red("a wrong-depth palette was not refused: exit %d %s" % (code, err.strip()[:60]))
    got.append("wrong-depth palette")
    with open(tp, encoding="utf-8") as fh:
        t = fh.read().split("\n")
    gi = t.index("grid") + 1
    bad = t[:]
    bad[gi] = bad[gi][:5] + "X" + bad[gi][6:]
    bp = os.path.join(TXT, "bad.wtxt")
    with open(bp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(bad))
    code, _o, err = run(TEXT_EXE, ["digests", "--text", bp, "--palette-from", os.path.join(ORACLE, "levels", "witness.lvl")])
    if code != 2 or "alphabet" not in err:
        raise Red("a non-alphabet grid byte was not refused: exit %d %s" % (code, err.strip()[:60]))
    got.append("non-alphabet cell")
    rag = t[:]
    rag[gi] = rag[gi] + "."
    rp = os.path.join(TXT, "ragged.wtxt")
    with open(rp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(rag))
    code, _o, err = run(TEXT_EXE, ["digests", "--text", rp, "--palette-from", os.path.join(ORACLE, "levels", "witness.lvl")])
    if code != 2 or "width" not in err:
        raise Red("a ragged grid was not refused: exit %d %s" % (code, err.strip()[:60]))
    got.append("ragged grid row")
    return "%d malformed texts refused typed before any content digest — %s" % (len(got), ", ".join(got))


# ------------------------------------------------------------------ workshop1 (WORKSHOP-1)
SESSION_EXE = None
SES = os.path.join(BUILD, "ses")
TILE_BYTES = 256 * 256 * 3


def workshop1_build():
    global SESSION_EXE
    SESSION_EXE = compile_rs(WORKSHOP, "session.rs", "session")
    if os.path.isdir(SES):
        shutil.rmtree(SES)
    os.makedirs(SES)
    return "workshop/session.rs compiled live: new / propose / commit / undo / replay / verify over a base authority and a cell+tile edit log"


# --- the Python chain twin: recompute content/full independently, mirroring session.rs ---
def _apply_cell(level_bytes, x, z, to):
    import struct as _s
    b = bytearray(level_bytes)
    w = _s.unpack_from("<I", b, 8)[0]
    b[16 + z * w + x] = ord(to)
    return bytes(b)


def _apply_tile(tiles_bytes, cls, rgb):
    b = bytearray(tiles_bytes)
    off = 8 + {"wall0": 0, "wall1": 1, "wall2": 2, "wall3": 3, "floor": 4}[cls] * TILE_BYTES
    px = bytes(rgb)
    for i in range(off, off + TILE_BYTES, 3):
        b[i:i + 3] = px
    return bytes(b)


def _content(level_bytes, tiles_bytes):
    return hashlib.sha256(hashlib.sha256(level_bytes).digest() + hashlib.sha256(tiles_bytes).digest()).digest()


def _chain_head(level_bytes, tiles_bytes, log):
    full = hashlib.sha256(b"VRDNSES1" + _content(level_bytes, tiles_bytes)).digest()
    lvl, til = level_bytes, tiles_bytes
    for e in log:
        if e["op"] == "cell":
            lvl = _apply_cell(lvl, e["x"], e["z"], e["to"])
        else:
            lvl2, til = lvl, _apply_tile(til, e["class"], tuple(e["rgb"]))
            lvl = lvl2
        full = hashlib.sha256(full + _content(lvl, til)).digest()
    return full.hex()


def _new_session(name, edits):
    """Build a scratch session with the witness base and the given edits; return its path."""
    sp = os.path.join(SES, name + ".json")
    lv = os.path.join(ORACLE, "levels", "witness.lvl")
    tl = os.path.join(ORACLE, "tiles", "identity.tiles")
    code, _o, err = run(SESSION_EXE, ["new", "--level", lv, "--tiles", tl, "--out", sp])
    if code != 0:
        raise Red("session new: " + err.strip())
    for e in edits:
        code, _o, err = run(SESSION_EXE, ["commit", "--session", sp, "--edit", e])
        if code != 0:
            raise Red("session commit %s: %s" % (e, err.strip()))
    return sp


def _session_head(sp):
    with open(sp, encoding="utf-8") as fh:
        return json.load(fh)["data"]["head"]


def _verify(sp):
    code, out, err = run(SESSION_EXE, ["verify", "--session", sp])
    return code, (out.strip() or err.strip())


def workshop1_replay():
    need_rustc()
    edits = ["cell:30,25,#", "cell:30,26,#", "cell:30,27,#", "tile:floor,96,80,64"]
    sp = _new_session("replay", edits)
    code, out, err = run(SESSION_EXE, ["replay", "--session", sp])
    if code != 0:
        raise Red("replay: " + err.strip())
    head = _session_head(sp)
    if ("head " + head[:12]) not in out:
        raise Red("replay did not report the stored head")
    # the Python chain twin recomputes the head independently
    log = json.load(open(sp, encoding="utf-8"))["data"]["log"]
    twin = _chain_head(read(os.path.join(ORACLE, "levels", "witness.lvl")), read(os.path.join(ORACLE, "tiles", "identity.tiles")), [e["edit"] for e in log])
    if twin != head:
        raise Red("the Python chain twin head %s != the session head %s" % (twin[:12], head[:12]))
    return ("a %d-edit session (3 walls + 1 texture) replays from the base to its head %s, and a Python recomputation of the "
            "hash chain (content=sha256(W‖M), full=sha256(parent‖content)) reproduces that head — the chain is a cross-checked single-writer log" % (len(edits), head[:12]))


def workshop1_undo():
    need_rustc()
    sp = _new_session("undo", ["cell:30,25,#", "cell:30,26,#", "cell:30,27,#", "tile:floor,96,80,64"])
    code, _o, err = run(SESSION_EXE, ["undo", "--session", sp, "--to", "2"])
    if code != 0:
        raise Red("undo: " + err.strip())
    undone = _session_head(sp)
    # undo to 2 must equal a fresh session of the first 2 edits (undo is replay, not mutation)
    sp2 = _new_session("undo_ref", ["cell:30,25,#", "cell:30,26,#"])
    if undone != _session_head(sp2):
        raise Red("undo to 2 did not equal replaying the first 2 edits — undo is not replay")
    code, out = _verify(sp)
    if code != 0 or "committed 2 irreversible 1" not in out:
        raise Red("the undone session did not verify with committed 2 irreversible 1: " + out)
    return ("undo to 2 rewinds the head to %s, which equals a fresh session of the first 2 edits — undo is a deterministic replay, "
            "never a localised mutation; the rewound session verifies (committed 2, irreversible 1, durable)" % undone[:12])


def workshop1_propose():
    need_rustc()
    sp = _new_session("propose", ["cell:30,25,#"])
    before = read(sp)
    # a valid propose writes nothing
    code, out, _e = run(SESSION_EXE, ["propose", "--session", sp, "--edit", "cell:31,25,#"])
    if code != 0 or "nothing written" not in out:
        raise Red("a valid propose did not report OK/nothing-written: " + out.strip())
    if read(sp) != before:
        raise Red("propose wrote to the session file — it must be a speculative scratchpad")
    # an invalid propose (opens the border) refuses, and still writes nothing
    code, _o, err = run(SESSION_EXE, ["propose", "--session", sp, "--edit", "cell:0,5,."])
    if code != 2 or "border" not in err:
        raise Red("an edit opening the border was not refused: %d %s" % (code, err.strip()[:50]))
    if read(sp) != before:
        raise Red("a refused propose changed the session")
    return ("propose validates against the head and writes NOTHING (a valid one reports the would-commit head; one that opens the "
            "border is refused) — the speculative scratchpad, with the committed log left oblivious")


def workshop1_tamper():
    need_rustc()
    sp = _new_session("tamper", ["cell:30,25,#", "cell:30,26,#", "tile:floor,96,80,64"])
    code, out = _verify(sp)
    if code != 0:
        raise Red("the untampered session did not verify: " + out)
    doc = json.load(open(sp, encoding="utf-8"))
    original = read(sp)
    # tamper: change the second entry's op param (30,26 -> 31,26) WITHOUT touching its stored digests
    doc["data"]["log"][1]["edit"]["x"] = 31
    with open(sp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1)
    code, out = _verify(sp)
    if code != 2 or "CHAIN-BROKEN" not in out:
        raise Red("a tampered log entry was not caught: %d %s" % (code, out[:60]))
    with open(sp, "wb") as fh:
        fh.write(original)
    code, out = _verify(sp)
    if code != 0:
        raise Red("the restored session did not re-verify")
    return ("changing one log entry (its edit param) without its digests makes `verify` replay and catch CHAIN-BROKEN — the head "
            "moves and every link after the change breaks; restored, the session re-verifies")


def workshop1_demo():
    need_rustc()
    sp = os.path.join(ROOT, "workshop", "attest", "session-demo.json")
    rec = envelope.read(sp)  # sealed under RECORD-0; records-firewall covers it too
    if rec["name"] != "verdandi-session":
        raise Red("the demo is not a verdandi-session")
    d = rec["data"]
    c = corpus()
    if d["base"]["W"] != c["levels"]["witness"]["W"] or d["base"]["M"] != c["tiles"]["identity"]["M"]:
        raise Red("the demo's base is not the frozen witness authority")
    code, out = _verify(sp)
    if code != 0 or ("head " + d["head"][:12]) not in out:
        raise Red("the committed demo did not replay to its sealed head: " + out)
    ts = d["three_state"]
    if ts["irreversible"] != ts["committed"] - 1 or not ts["durable"]:
        raise Red("the three-state invariant is inconsistent")
    return ("the committed demo (workshop/attest/session-demo.json, sealed under RECORD-0) replays to its head %s over %d edits on the "
            "frozen witness base; committed %d, irreversible %d, durable — a session is a hash-chained file" % (d["head"][:12], len(d["log"]), ts["committed"], ts["irreversible"]))


# ------------------------------------------------------------------ input (INPUT-0)
INPUT_EXE = None
WLK = os.path.join(BUILD, "wlk")
_FWD = {0: (0, -1), 1: (1, 0), 2: (0, 1), 3: (-1, 0)}   # N E S W — matches the kernel's `direction`
_LETTER = {0: "N", 1: "E", 2: "S", 3: "W"}


def input_build():
    global INPUT_EXE
    INPUT_EXE = compile_rs(WORKSHOP, "input.rs", "input")
    if os.path.isdir(WLK):
        shutil.rmtree(WLK)
    os.makedirs(WLK)
    return "workshop/input.rs compiled live: replay / write / verify — a typed command log (L R F B Q E) moves the camera against a fixed level and chains each step's kernel URDRFB1 frame digest into a head"


# --- the Python movement + chain twin: reproduce the trajectory and the head independently ---
def _grid(level_bytes):
    import struct as _s
    w = _s.unpack_from("<I", level_bytes, 8)[0]
    rows = _s.unpack_from("<I", level_bytes, 12)[0]
    return w, rows, level_bytes[16:16 + w * rows]


def _walk_trav(level_bytes, x, z):
    w, rows, cells = _grid(level_bytes)
    return 0 <= x < w and 0 <= z < rows and cells[z * w + x] != ord("#")


def _walk_step(level_bytes, cam, cmd):
    x, z, f = cam
    if cmd == "L":
        return (x, z, (f + 3) % 4)
    if cmd == "R":
        return (x, z, (f + 1) % 4)
    d = {"F": _FWD[f], "B": (-_FWD[f][0], -_FWD[f][1]), "Q": _FWD[(f + 3) % 4], "E": _FWD[(f + 1) % 4]}[cmd]
    nx, nz = x + d[0], z + d[1]
    return (nx, nz, f) if _walk_trav(level_bytes, nx, nz) else (x, z, f)   # blocked = a no-op


def _walk_cams(level_bytes, cam0, commands):
    cams, cam, blocked = [cam0], cam0, 0
    for cmd in commands:
        if cmd.isspace():
            continue
        before = (cam[0], cam[1])
        cam = _walk_step(level_bytes, cam, cmd)
        if cmd in "FBQE" and (cam[0], cam[1]) == before:
            blocked += 1
        cams.append(cam)
    return cams, blocked


def _walk_frame(cam):
    """the kernel executable's URDRFB1 frame digest for a camera over the witness/identity authority."""
    x, z, f = cam
    return witnesses(KERNEL_EXE, "witness", "identity", "%d,%d,%s" % (x, z, _LETTER[f]))[0]


def _walk_head(cams):
    """chain the per-step frame digests exactly as input.rs: genesis sha256(MAGIC‖frame0), then sha256(acc‖frame)."""
    frames = [_walk_frame(c) for c in cams]
    acc = hashlib.sha256(b"VWLK1" + frames[0].encode()).digest()
    for fr in frames[1:]:
        acc = hashlib.sha256(acc + fr.encode()).digest()
    return acc.hex(), frames


def _replay(camera, commands):
    lvl = os.path.join(ORACLE, "levels", "witness.lvl")
    tls = os.path.join(ORACLE, "tiles", "identity.tiles")
    code, out, err = run(INPUT_EXE, ["replay", "--level", lvl, "--tiles", tls, "--camera", camera, "--commands", commands])
    if code != 0:
        raise Red("replay %s: %s" % (commands, err.strip()))
    d = {}
    for ln in out.strip().splitlines():
        if ln.startswith("final camera "):
            p = ln.split()
            d["final"] = "%s,%s,%s" % (p[2], p[3], p[4])
        elif ln.startswith("steps "):
            p = ln.split()
            d["steps"], d["blocked"] = int(p[1]), int(p[3])
        elif ln.startswith("head "):
            d["head"] = ln.split()[1]
    return d


def input_replay():
    need_rustc()
    cam0, commands = (34, 28, 3), "LFFRF"   # from the witness spawn, facing W
    rep = _replay("34,28,W", commands)
    level_bytes = read(os.path.join(ORACLE, "levels", "witness.lvl"))
    cams, blocked = _walk_cams(level_bytes, cam0, commands)
    twin_head, _frames = _walk_head(cams)
    if twin_head != rep["head"]:
        raise Red("the Python movement+chain twin head %s != input replay's head %s" % (twin_head[:12], rep["head"][:12]))
    if (len(cams) - 1, blocked) != (rep["steps"], rep["blocked"]):
        raise Red("the twin's step/blocked (%d/%d) disagree with replay (%d/%d)" % (len(cams) - 1, blocked, rep["steps"], rep["blocked"]))
    fc = cams[-1]
    if "%d,%d,%s" % (fc[0], fc[1], _LETTER[fc[2]]) != rep["final"]:
        raise Red("the twin's final camera %s != replay's %s" % ((fc[0], fc[1], _LETTER[fc[2]]), rep["final"]))
    return ("a %d-command walk (LFFRF) replays to camera %s and head %s; a Python twin reimplements the movement rules "
            "(L/R turn, F/B/Q/E step, blocked=no-op) and chains the kernel executable's frame digests (genesis "
            "sha256(MAGIC‖frame0), then sha256(acc‖frame)) to the SAME head — trajectory AND chain are cross-checked, "
            "and the frame digests come from a separate kernel process than input.rs's library copy" % (rep["steps"], rep["final"], rep["head"][:12]))


def input_blocked():
    need_rustc()
    level_bytes = read(os.path.join(ORACLE, "levels", "witness.lvl"))
    # (34,29) faces S onto (34,30); that target is rock, so F must be a no-op, still logged
    if _walk_trav(level_bytes, 34, 30):
        raise Red("the blocked-step precondition failed: (34,30) is not rock")
    rep = _replay("34,29,S", "F")
    if rep["final"] != "34,29,S":
        raise Red("a blocked forward moved the camera to %s" % rep["final"])
    if (rep["steps"], rep["blocked"]) != (1, 1):
        raise Red("the blocked step was not counted (steps %d blocked %d)" % (rep["steps"], rep["blocked"]))
    # the no-op is witnessed: its frame equals the unchanged camera's frame, and the head is the two-frame chain of it
    twin_head, frames = _walk_head([(34, 29, 2), (34, 29, 2)])
    if frames[0] != frames[1]:
        raise Red("a blocked step's frame is not the unchanged camera's frame")
    if twin_head != rep["head"]:
        raise Red("the blocked walk's head %s != the twin's %s" % (rep["head"][:12], twin_head[:12]))
    return ("walking into rock (camera 34,29,S, F onto rock at 34,30) does not move the camera — final stays 34,29,S — yet the "
            "step is still logged: its frame digest equals the unchanged camera's, and the head is the two-frame chain of that "
            "one repeated frame; a wall stops you deterministically and the no-op is witnessed, never dropped")


def input_tamper():
    need_rustc()
    wp = os.path.join(WLK, "tamper.walk")
    with open(wp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("; a walk to tamper\nlevel %s\ntiles %s\ncamera 34 28 W\ncommands LFFRF\n"
                 % (os.path.join(ORACLE, "levels", "witness.lvl"), os.path.join(ORACLE, "tiles", "identity.tiles")))
    code, out, err = run(INPUT_EXE, ["write", "--walk", wp])
    if code != 0:
        raise Red("write: " + err.strip())
    code, out, err = run(INPUT_EXE, ["verify", "--walk", wp])
    if code != 0 or "verify OK" not in out:
        raise Red("the written walk did not verify: " + (out + err).strip())
    original = read(wp)
    # tamper: change one command (L -> R) without recomputing the stored head
    with open(wp, "wb") as fh:
        fh.write(original.replace(b"commands LFFRF", b"commands RFFRF"))
    code, out, err = run(INPUT_EXE, ["verify", "--walk", wp])
    if code != 2 or "CHAIN-BROKEN" not in err:
        raise Red("a tampered command was not caught: %d %s" % (code, (out + err).strip()[:60]))
    with open(wp, "wb") as fh:
        fh.write(original)
    code, out, err = run(INPUT_EXE, ["verify", "--walk", wp])
    if code != 0:
        raise Red("the restored walk did not re-verify")
    return ("`input write` seals a walk's head; changing one command (L→R) without recomputing it makes `input verify` replay and "
            "catch CHAIN-BROKEN (exit 2) — a different first turn takes a different trajectory, hence different frames, hence a "
            "different head; restored to the original bytes, the walk re-verifies")


def input_not_authority():
    need_rustc()
    c = corpus()
    lvl = os.path.join(ORACLE, "levels", "witness.lvl")
    tls = os.path.join(ORACLE, "tiles", "identity.tiles")
    W0, M0 = sha256(read(lvl)), sha256(read(tls))
    if W0 != c["levels"]["witness"]["W"] or M0 != c["tiles"]["identity"]["M"]:
        raise Red("the base authority is not the frozen witness/identity")
    wp = os.path.join(WLK, "na.walk")
    with open(wp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("level %s\ntiles %s\ncamera 34 28 W\ncommands LFFRF\n" % (lvl, tls))
    for verb in ("write", "verify"):
        code, _o, err = run(INPUT_EXE, [verb, "--walk", wp])
        if code != 0:
            raise Red("%s: %s" % (verb, err.strip()))
    rep = _replay("34,28,W", "LFFRF")
    if rep["final"].rsplit(",", 1)[0] == "34,28":
        raise Red("the walk did not move the camera, so this proves nothing")
    if sha256(read(lvl)) != W0 or sha256(read(tls)) != M0:
        raise Red("replaying/verifying a walk changed the level or tiles file — the camera is NOT projection-owned")
    return ("a walk moves the camera (34,28 → %s) but leaves the authority untouched: after write+verify+replay the level's W (%s…) "
            "and the tiles' M (%s…) are byte-identical to the frozen witness/identity — moving around is a VIEW mutation, never an "
            "edit (WORKSHOP-0b), so the shell cannot smuggle a world change in through the camera" % (rep["final"], W0[:8], M0[:8]))


def input_demo():
    need_rustc()
    rec = envelope.read(os.path.join(ROOT, "workshop", "attest", "walk-demo.json"))  # sealed under RECORD-0
    if rec["name"] != "verdandi-walk" or rec["claim_class"] != "established":
        raise Red("the demo is not an established verdandi-walk")
    d = rec["data"]
    c = corpus()
    lvl = os.path.join(ORACLE, "levels", "witness.lvl")
    tls = os.path.join(ORACLE, "tiles", "identity.tiles")
    if d["W"] != c["levels"]["witness"]["W"] or d["M"] != c["tiles"]["identity"]["M"]:
        raise Red("the demo's base is not the frozen witness/identity authority")
    if sha256(read(lvl)) != d["W"] or sha256(read(tls)) != d["M"]:
        raise Red("the demo's W/M do not equal the oracle files")
    # the binary re-derives the sealed head, and the Python twin re-derives it independently
    wp = os.path.join(WLK, "demo.walk")
    with open(wp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("level %s\ntiles %s\ncamera %s\ncommands %s\nhead %s\n"
                 % (lvl, tls, d["camera"].replace(",", " "), d["commands"], d["head"]))
    code, out, err = run(INPUT_EXE, ["verify", "--walk", wp])
    if code != 0 or ("head " + d["head"][:12]) not in out:
        raise Red("the sealed walk did not verify to its head: " + (out + err).strip())
    cam0 = tuple(int(v) for v in d["camera"].split(",")[:2]) + ({"N": 0, "E": 1, "S": 2, "W": 3}[d["camera"].split(",")[2]],)
    cams, blocked = _walk_cams(read(lvl), cam0, d["commands"])
    twin_head, _f = _walk_head(cams)
    fc = cams[-1]
    if twin_head != d["head"]:
        raise Red("the Python twin head %s != the sealed head %s" % (twin_head[:12], d["head"][:12]))
    if (len(cams) - 1, blocked, "%d,%d,%s" % (fc[0], fc[1], _LETTER[fc[2]])) != (d["steps"], d["blocked"], d["final"]):
        raise Red("the twin's trajectory disagrees with the sealed final/steps/blocked")
    return ("the committed demo (workshop/attest/walk-demo.json, sealed under RECORD-0) is a reference walk (commands %s, all six "
            "letters) that `input verify` replays to its sealed head %s over %d steps (%d blocked), and a Python twin re-derives "
            "that head on the frozen witness base — a walk is a hash-chained file, established (host-independent), not measured"
            % (d["commands"], d["head"][:12], d["steps"], d["blocked"]))


# ------------------------------------------------------------------ sessionwalk (SESSION-WALK)
SESSIONWALK_EXE = None
SW = os.path.join(BUILD, "sw")
SW_MAGIC = b"VRDNSW1"
_SWTILE = {"wall0": 0, "wall1": 1, "wall2": 2, "wall3": 3, "floor": 4}


def sessionwalk_build():
    global SESSIONWALK_EXE
    SESSIONWALK_EXE = compile_rs(WORKSHOP, "sessionwalk.rs", "sessionwalk")
    if os.path.isdir(SW):
        shutil.rmtree(SW)
    os.makedirs(SW)
    return ("workshop/sessionwalk.rs compiled live: new / move / edit / replay / verify — one interleaved append-only log "
            "of edits AND moves, each evaluated in log order against the authority the preceding events produced")


# --- the Python twin: reproduce the single interleaved head independently ---
def _sw_content(level_bytes, tiles_bytes):
    return hashlib.sha256(hashlib.sha256(level_bytes).digest() + hashlib.sha256(tiles_bytes).digest()).hexdigest()


def _sw_apply(level_bytes, tiles_bytes, spec):
    kind, rest = spec.split(":", 1)
    if kind == "cell":
        x, z, c = rest.split(",")
        x, z = int(x), int(z)
        import struct as _s
        b = bytearray(level_bytes)
        w = _s.unpack_from("<I", b, 8)[0]
        b[16 + z * w + x] = ord(c)
        return bytes(b), tiles_bytes
    if kind == "tile":
        cls, r, g, bl = rest.split(",")
        off = 8 + _SWTILE[cls] * (256 * 256 * 3)
        px = bytes((int(r), int(g), int(bl)))
        b = bytearray(tiles_bytes)
        for i in range(off, off + 256 * 256 * 3, 3):
            b[i:i + 3] = px
        return level_bytes, bytes(b)
    raise Red("twin: unknown edit kind " + kind)


def _sw_trav(level_bytes, x, z):
    return _walk_trav(level_bytes, x, z)  # shares INPUT-0's grid reader


def _sw_step(level_bytes, cam, cmd):
    return _walk_step(level_bytes, cam, cmd)  # shares INPUT-0's movement rules


def _sw_frame(level_bytes, tiles_bytes, cam, cache):
    """the kernel executable's frame digest at cam over the CURRENT (possibly edited) authority; cache the temp files."""
    if cache.get("lvl") != level_bytes or cache.get("til") != tiles_bytes:
        lp = os.path.join(SW, "cur.lvl")
        tp = os.path.join(SW, "cur.tiles")
        with open(lp, "wb") as fh:
            fh.write(level_bytes)
        with open(tp, "wb") as fh:
            fh.write(tiles_bytes)
        cache["lvl"], cache["til"], cache["lp"], cache["tp"] = level_bytes, tiles_bytes, lp, tp
    x, z, f = cam
    code, out, err = run(KERNEL_EXE, ["--level", cache["lp"], "--tiles", cache["tp"], "--camera", "%d,%d,%s" % (x, z, _LETTER[f])])
    if code != 0:
        raise Red("twin frame render: " + err.strip())
    d = dict(ln.split(" ", 1) for ln in out.strip().splitlines() if " " in ln)
    return d["frame"]


def _sw_genesis(base_content, cam0):
    x, z, f = cam0
    return hashlib.sha256(SW_MAGIC + base_content.encode() + b"@" + ("%d,%d,%s" % (x, z, _LETTER[f])).encode()).hexdigest()


def _sw_fold(head, tag, witness):
    return hashlib.sha256(head.encode() + b":" + tag + b":" + witness.encode()).hexdigest()


def _sw_advance(state, event, cache):
    """the pure step function of the fold: (level,tiles,cam,head,moves,edits) + event -> new state, and its witness."""
    lvl, til, cam, head, mv, ed = state
    kind, param = event
    if kind == "move":
        cam2 = _sw_step(lvl, cam, param)
        wit = _sw_frame(lvl, til, cam2, cache)
        return (lvl, til, cam2, _sw_fold(head, b"M", wit), mv + 1, ed), ("M", wit)
    lvl2, til2 = _sw_apply(lvl, til, param)
    wit = _sw_content(lvl2, til2)
    return (lvl2, til2, cam, _sw_fold(head, b"E", wit), mv, ed + 1), ("E", wit)


def _sw_fold_all(level_bytes, tiles_bytes, cam0, events, cache, start=None):
    if start is None:
        base_content = _sw_content(level_bytes, tiles_bytes)
        state = (level_bytes, tiles_bytes, cam0, _sw_genesis(base_content, cam0), 0, 0)
    else:
        state = start
    wits = []
    for ev in events:
        state, w = _sw_advance(state, ev, cache)
        wits.append(w)
    return state, wits


def _cam_tuple(tok):
    x, z, f = tok.split(",")
    return (int(x), int(z), {"N": 0, "E": 1, "S": 2, "W": 3}[f])


def _sw_build(name, cam0_tok, events):
    """drive the binary: new, then one move/edit per event; return the session path."""
    sp = os.path.join(SW, name + ".json")
    lv = os.path.join(ORACLE, "levels", "witness.lvl")
    tl = os.path.join(ORACLE, "tiles", "identity.tiles")
    code, _o, err = run(SESSIONWALK_EXE, ["new", "--level", lv, "--tiles", tl, "--camera", cam0_tok, "--out", sp])
    if code != 0:
        raise Red("sessionwalk new: " + err.strip())
    for kind, param in events:
        flag = "--command" if kind == "move" else "--edit"
        verb = "move" if kind == "move" else "edit"
        code, _o, err = run(SESSIONWALK_EXE, [verb, "--session", sp, flag, param])
        if code != 0:
            raise Red("sessionwalk %s %s: %s" % (verb, param, err.strip()))
    return sp


def _sw_stored(sp):
    return json.load(open(sp, encoding="utf-8"))["data"]


# a canonical interleaved demo: open a doorway, walk through it into the upper corridor, place a wall, turn and step
DEMO_CAM = "28,28,N"
DEMO_EVENTS = [("edit", "cell:28,27,."), ("move", "F"), ("move", "F"), ("edit", "tile:floor,96,80,64"), ("move", "L"), ("move", "F")]


def _sw_twin_head(cam0_tok, events):
    lv = read(os.path.join(ORACLE, "levels", "witness.lvl"))
    tl = read(os.path.join(ORACLE, "tiles", "identity.tiles"))
    cache = {}
    (lvl, til, cam, head, mv, ed), wits = _sw_fold_all(lv, tl, _cam_tuple(cam0_tok), events, cache)
    return head, cam, _sw_content(lvl, til), mv, ed, wits


def sessionwalk_replay():
    need_rustc()
    sp = _sw_build("replay", DEMO_CAM, DEMO_EVENTS)
    code, out, err = run(SESSIONWALK_EXE, ["replay", "--session", sp])
    if code != 0:
        raise Red("replay: " + err.strip())
    rep = {}
    for ln in out.strip().splitlines():
        if ln.startswith("head "):
            rep["head"] = ln.split()[1]
        elif ln.startswith("final camera "):
            p = ln.split()
            rep["cam"] = (int(p[2]), int(p[3]), {"N": 0, "E": 1, "S": 2, "W": 3}[p[4]])
        elif ln.startswith("final content "):
            rep["content"] = ln.split()[2]
    twin_head, twin_cam, twin_content, mv, ed, _w = _sw_twin_head(DEMO_CAM, DEMO_EVENTS)
    if twin_head != rep["head"]:
        raise Red("the Python twin head %s != the binary replay head %s" % (twin_head[:12], rep["head"][:12]))
    if twin_cam != rep["cam"] or twin_content != rep["content"]:
        raise Red("the twin's final camera/content disagrees with the binary")
    return ("a %d-event interleaved session (%d edits + %d moves) replays to head %s; a Python twin reimplements the fold — edits "
            "mutate (W,M), moves render the kernel's frame against the CURRENT authority, one interleaved chain — and re-derives the "
            "SAME head, final camera and content (frames from a separate kernel process)" % (mv + ed, ed, mv, rep["head"][:12]))


def sessionwalk_interleave():
    need_rustc()
    # the same two events in both orders; the move depends on the edit, so order is meaning, not a scheduler artifact
    a = _sw_build("inter_a", "28,28,N", [("edit", "cell:28,27,."), ("move", "F")])   # open, then step through
    b = _sw_build("inter_b", "28,28,N", [("move", "F"), ("edit", "cell:28,27,.")])   # step (blocked), then open
    da, db = _sw_stored(a), _sw_stored(b)
    if da["head"] == db["head"]:
        raise Red("reordering an edit past a dependent move did not change the head — the log order carries no meaning")
    if da["final_camera"] != "28,27,N":
        raise Red("with the edit first, the move did not step through the opened cell (got %s)" % da["final_camera"])
    if db["final_camera"] != "28,28,N":
        raise Red("with the move first, it was not blocked by rock (got %s)" % db["final_camera"])
    if da["final_content"] != db["final_content"]:
        raise Red("the two orders should leave the SAME (W,M) — the cell edit commutes; only navigation differs")
    # the twin agrees on both heads
    ha, _ca, _cc, _m, _e, _w = _sw_twin_head("28,28,N", [("edit", "cell:28,27,."), ("move", "F")])
    hb, _cb, _cc2, _m2, _e2, _w2 = _sw_twin_head("28,28,N", [("move", "F"), ("edit", "cell:28,27,.")])
    if ha != da["head"] or hb != db["head"]:
        raise Red("the twin disagrees with the binary on an interleaved head")
    return ("EDIT(open 28,27)→MOVE(F) steps THROUGH the opened cell (final 28,27,N) while MOVE(F)→EDIT is blocked by rock "
            "(final 28,28,N): same two events, same final (W,M), but different head and different camera — the move genuinely "
            "sees the edit, so log order is meaning, not a batching artifact; the twin re-derives both heads")


def sessionwalk_batch_invariance():
    need_rustc()
    # the binary built the session incrementally (one append per event); replay recomputes the head monolithically from base
    sp = _sw_build("batch", DEMO_CAM, DEMO_EVENTS)
    inc_head = _sw_stored(sp)["head"]
    code, out, _e = run(SESSIONWALK_EXE, ["replay", "--session", sp])
    mono_head = [l for l in out.strip().splitlines() if l.startswith("head ")][0].split()[1]
    if inc_head != mono_head:
        raise Red("incremental-append head %s != monolithic-replay head %s" % (inc_head[:12], mono_head[:12]))
    # the twin proves checkpoint equivalence: cut the fold at every split point, resume, and get the identical head
    lv = read(os.path.join(ORACLE, "levels", "witness.lvl"))
    tl = read(os.path.join(ORACLE, "tiles", "identity.tiles"))
    cache = {}
    full_state, _w = _sw_fold_all(lv, tl, _cam_tuple(DEMO_CAM), DEMO_EVENTS, cache)
    full_head = full_state[3]
    if full_head != mono_head:
        raise Red("the twin full-fold head %s != the binary head %s" % (full_head[:12], mono_head[:12]))
    splits = 0
    for k in range(len(DEMO_EVENTS) + 1):
        ck_state, _w1 = _sw_fold_all(lv, tl, _cam_tuple(DEMO_CAM), DEMO_EVENTS[:k], cache)
        resumed, _w2 = _sw_fold_all(None, None, None, DEMO_EVENTS[k:], cache, start=ck_state)
        if resumed[3] != full_head:
            raise Red("checkpoint at %d then resume gave head %s != the full head %s" % (k, resumed[3][:12], full_head[:12]))
        splits += 1
    return ("the head is one left fold, so it is checkpoint/replay-equivalent: incremental-append (%s) equals monolithic-replay, and "
            "cutting the fold at all %d split points then resuming from the checkpoint reproduces the identical head — a scheduler may "
            "batch verification any way it likes without changing what the sealed log means" % (inc_head[:12], splits))


def sessionwalk_tamper():
    need_rustc()
    sp = _sw_build("tamper", DEMO_CAM, DEMO_EVENTS)
    code, out, _e = run(SESSIONWALK_EXE, ["verify", "--session", sp])
    if code != 0 or "verify OK" not in out:
        raise Red("the untampered session did not verify: " + out.strip())
    original = read(sp)
    doc = json.load(open(sp, encoding="utf-8"))
    # tamper: change the first move's command without recomputing its witness or the head
    for e in doc["data"]["log"]:
        if e["kind"] == "move":
            e["command"] = "B" if e["command"] != "B" else "L"
            break
    with open(sp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1)
    code, _o, err = run(SESSIONWALK_EXE, ["verify", "--session", sp])
    if code != 2 or "CHAIN-BROKEN" not in err:
        raise Red("a tampered move was not caught: %d %s" % (code, err.strip()[:60]))
    with open(sp, "wb") as fh:
        fh.write(original)
    code, out, _e = run(SESSIONWALK_EXE, ["verify", "--session", sp])
    if code != 0:
        raise Red("the restored session did not re-verify")
    return ("changing one event (a move's command) without recomputing its witness makes `verify` replay and catch CHAIN-BROKEN "
            "(exit 2) at that event — every link after it breaks too; restored to the original bytes, the session re-verifies")


def sessionwalk_projection():
    need_rustc()
    # the full interleaved session
    full_head, full_cam, full_content, _m, _e, _w = _sw_twin_head(DEMO_CAM, DEMO_EVENTS)
    edits_only = [ev for ev in DEMO_EVENTS if ev[0] == "edit"]
    moves_only = [ev for ev in DEMO_EVENTS if ev[0] == "move"]
    # drop the moves: the (W,M) evolution is unchanged (moves are not edits)
    _eh, _ec, edits_content, _m2, _e2, _w2 = _sw_twin_head(DEMO_CAM, edits_only)
    if edits_content != full_content:
        raise Red("dropping the moves changed the final (W,M) — a move must not author")
    # drop the edits: a move that depended on an edit now behaves differently (edits are not views)
    _mh, moves_cam, _mc, _m3, _e3, _w3 = _sw_twin_head(DEMO_CAM, moves_only)
    if moves_cam == full_cam:
        raise Red("dropping the edits left the trajectory unchanged — then the edits never affected navigation, no bridge")
    return ("the two event kinds have distinct, non-independent roles: dropping every MOVE leaves the final (W,M) identical "
            "(content %s — moves never author), while dropping every EDIT changes where a move ends up (%s with edits vs %s without — "
            "the opened doorway is gone) — authoring and navigation interact through one ordered log, not two authorities"
            % (full_content[:12], "%d,%d,%s" % (full_cam[0], full_cam[1], _LETTER[full_cam[2]]),
               "%d,%d,%s" % (moves_cam[0], moves_cam[1], _LETTER[moves_cam[2]])))


def sessionwalk_demo():
    need_rustc()
    rec = envelope.read(os.path.join(ROOT, "workshop", "attest", "sessionwalk-demo.json"))  # sealed under RECORD-0
    if rec["name"] != "verdandi-session-walk" or rec["claim_class"] != "established":
        raise Red("the demo is not an established verdandi-session-walk")
    d = rec["data"]
    c = corpus()
    if d["base"]["W"] != c["levels"]["witness"]["W"] or d["base"]["M"] != c["tiles"]["identity"]["M"]:
        raise Red("the demo's base is not the frozen witness/identity authority")
    # rebuild the session from the sealed events, verify it replays to the sealed head, and the twin re-derives it
    events = [(e["kind"], e["command"] if e["kind"] == "move" else e["spec"]) for e in d["log"]]
    sp = _sw_build("demo", d["base"]["camera"], events)
    code, out, err = run(SESSIONWALK_EXE, ["verify", "--session", sp])
    if code != 0 or ("head " + d["head"][:12]) not in out:
        raise Red("the sealed session did not verify to its head: " + (out + err).strip())
    twin_head, twin_cam, twin_content, mv, ed, _w = _sw_twin_head(d["base"]["camera"], events)
    if twin_head != d["head"] or "%d,%d,%s" % (twin_cam[0], twin_cam[1], _LETTER[twin_cam[2]]) != d["final_camera"]:
        raise Red("the twin disagrees with the sealed demo head/camera")
    return ("the committed demo (workshop/attest/sessionwalk-demo.json, sealed under RECORD-0) is an interleaved session (%d edits + "
            "%d moves: open a doorway, walk through it, retexture the floor, turn and step) that `verify` replays to its sealed head "
            "%s and a Python twin re-derives — established, host-independent" % (ed, mv, d["head"][:12]))


# ------------------------------------------------------------------ shell playback (SHELL-PLAYBACK)
PB = os.path.join(BUILD, "pb")
SESSIONWALK_DEMO = os.path.join(ROOT, "workshop", "attest", "sessionwalk-demo.json")


def _pb_dir():
    if not os.path.isdir(PB):
        os.makedirs(PB)


def _pb_run(exe, args):
    return run(exe, args)


def _pb_playback(exe, session, root="", batch=None):
    a = ["playback", "--session", session]
    if root:
        a += ["--root", root]
    if batch is not None:
        a += ["--batch", str(batch)]
    code, out, err = _pb_run(exe, a)
    return code, out, err


def _pb_parse(out):
    frames, head, final = [], None, None
    for ln in out.strip().splitlines():
        if ln.startswith("frame "):
            p = ln.split()
            frames.append({"i": int(p[1]), "camera": p[3], "digest": p[5], "blit": p[7], "roundtrip": p[9]})
        elif ln.startswith("playback head "):
            p = ln.split()
            head = p[2]
            final = p[8]
    return frames, head, final


def _pb_demo_events(session_path):
    d = json.load(open(session_path, encoding="utf-8"))["data"]
    events = [(e["kind"], e["command"] if e["kind"] == "move" else e["spec"]) for e in d["log"]]
    move_wit = [e["witness"] for e in d["log"] if e["kind"] == "move"]
    return d, events, move_wit


def shell_playback_sealed_input():
    need_rustc()
    _pb_dir()
    # playback consumes the COMMITTED sealed session-walk (relative base paths resolved via --root)
    code, out, err = _pb_playback(SHELL_EXE, SESSIONWALK_DEMO, root=ROOT + os.sep)
    if code != 0:
        raise Red("playback of the committed demo failed: " + err.strip())
    d, _events, _mw = _pb_demo_events(SESSIONWALK_DEMO)
    _frames, head, _final = _pb_parse(out)
    if head != d["head"]:
        raise Red("playback head %s != the sealed demo head %s" % (head[:12], d["head"][:12]))
    # it refuses a NON-session artifact (an ad-hoc/reconstructed stream is not accepted)
    bad = os.path.join(PB, "not-a-session.json")
    with open(bad, "w", encoding="utf-8") as fh:
        fh.write('{"name":"verdandi-walk","data":{}}')
    code, _o, err = _pb_playback(SHELL_EXE, bad)
    if code != 2 or "INVALID-SESSION" not in err:
        raise Red("playback accepted a non-session artifact: %d %s" % (code, err.strip()[:60]))
    return ("`shell playback` consumes the committed sealed session-walk (workshop/attest/sessionwalk-demo.json) and re-derives its "
            "head %s; it refuses a non-session artifact (INVALID-SESSION) — playback reads the sealed authority, never an ad-hoc "
            "action stream" % head[:12])


def shell_playback_frame_sequence():
    need_rustc()
    _pb_dir()
    # THE CROWN WITNESS: the composited frame-digest sequence == the session's per-move frame-witness sequence
    code, out, err = _pb_playback(SHELL_EXE, SESSIONWALK_DEMO, root=ROOT + os.sep)
    if code != 0:
        raise Red("playback failed: " + err.strip())
    frames, _head, _final = _pb_parse(out)
    d, events, move_wit = _pb_demo_events(SESSIONWALK_DEMO)
    seq = [f["digest"] for f in frames]
    if seq != move_wit:
        raise Red("the playback frame-digest sequence != the sealed move-witness sequence")
    # cross-check with a Python twin: reconstruct the authority per move and render via a SEPARATE kernel process
    lv = read(os.path.join(ORACLE, "levels", "witness.lvl"))
    tl = read(os.path.join(ORACLE, "tiles", "identity.tiles"))
    cam = _cam_tuple(d["base"]["camera"])
    cache = {}
    twin = []
    for kind, param in events:
        if kind == "edit":
            lv, tl = _sw_apply(lv, tl, param)
        else:
            cam = _sw_step(lv, cam, param)
            twin.append(_sw_frame(lv, tl, cam, cache))
    if twin != seq:
        raise Red("a Python twin (separate kernel process) disagrees with the playback frame sequence")
    return ("the crown witness: playback's composited frame-digest sequence (%d frames) EQUALS the session's sealed per-move "
            "frame-witness sequence AND a Python twin rendering each move through a separate kernel process — the window's frames "
            "are exactly the becoming SESSION-WALK sealed, tied through the SHELL-0 present path" % len(seq))


def shell_playback_blit_law():
    need_rustc()
    _pb_dir()
    # every displayed frame passes SHELL-0's blit round-trip
    code, out, _e = _pb_playback(SHELL_EXE, SESSIONWALK_DEMO, root=ROOT + os.sep)
    frames, _h, _f = _pb_parse(out)
    if not frames or any(f["roundtrip"] != "OK" for f in frames):
        raise Red("a displayed frame did not pass the blit round-trip")
    # the law bites: a present path that drops the red channel makes playback report BROKEN
    src = read(os.path.join(SHELL, "present.rs")).decode("utf-8")
    anchor = "        out[i * 3 + 2] = rgb[i * 3]; // R"
    if src.count(anchor) != 1:
        raise Red("the blit-plant anchor moved")
    corrupted = src.replace(anchor, "        out[i * 3 + 2] = 0; // PLANT: playback's present path drops red")
    plant = compile_rs(SHELL, "main.rs", "shell-pb-plant", {"present.rs": corrupted})
    code, out, _e = _pb_playback(plant, SESSIONWALK_DEMO, root=ROOT + os.sep)
    fr, _h2, _f2 = _pb_parse(out)
    if not fr or all(f["roundtrip"] == "OK" for f in fr):
        raise Red("a corrupted present path still round-tripped — the blit law does not bite in playback")
    return ("every displayed frame passes SHELL-0's blit round-trip (from_blit(to_blit(c))==c), and a planted present path that "
            "drops the red channel makes playback report BROKEN — the window shows only bytes that carried the kernel's composite "
            "intact (%d frames)" % len(frames))


def shell_playback_no_authority():
    need_rustc()
    _pb_dir()
    lvl = os.path.join(ORACLE, "levels", "witness.lvl")
    tls = os.path.join(ORACLE, "tiles", "identity.tiles")
    sp = _sw_build("pb_na", "28,28,N", [("edit", "cell:28,27,."), ("move", "F"), ("move", "F"), ("edit", "tile:floor,96,80,64"), ("move", "L"), ("move", "F")])
    before = {p: sha256(read(p)) for p in (lvl, tls, sp)}
    _pb_playback(SHELL_EXE, sp)
    ck = os.path.join(PB, "na.ck")
    _pb_run(SHELL_EXE, ["checkpoint", "--session", sp, "--at", "3", "--out", ck])
    _pb_run(SHELL_EXE, ["resume", "--session", sp, "--checkpoint", ck])
    after = {p: sha256(read(p)) for p in (lvl, tls, sp)}
    if before != after:
        raise Red("playback/checkpoint/resume changed the level, tiles, or session file — the shell became a second authority")
    return ("after playback + checkpoint + resume the level's W, the tiles' M and the session file are byte-identical — the shell "
            "playback reads the sealed authority and writes none of it; it cannot become a second authority")


def shell_playback_order():
    need_rustc()
    _pb_dir()
    sp = _sw_build("pb_order", "28,28,N", [("edit", "cell:28,27,."), ("move", "F"), ("move", "F")])
    # in order, playback succeeds and its frames are in log order
    code, out, _e = _pb_playback(SHELL_EXE, sp)
    if code != 0:
        raise Red("in-order playback failed")
    frames, _h, _f = _pb_parse(out)
    if [f["i"] for f in frames] != list(range(len(frames))):
        raise Red("playback did not emit frames in log order")
    # reorder the sealed log (swap the opening edit with the first move) WITHOUT recomputing witnesses/head
    doc = json.load(open(sp, encoding="utf-8"))
    log = doc["data"]["log"]
    log[0], log[1] = log[1], log[0]
    with open(sp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1)
    code, _o, err = _pb_playback(SHELL_EXE, sp)
    if code != 2 or "DIVERGED" not in err:
        raise Red("a reordered sealed log was not caught: %d %s" % (code, err.strip()[:60]))
    return ("playback presents the sealed events strictly in log order (frames 0..n) and never reorders for presentation: swapping "
            "the opening edit with the first move makes a re-derived witness diverge and playback REFUSES (DIVERGED) rather than "
            "showing a different becoming")


def shell_playback_tamper():
    need_rustc()
    _pb_dir()
    sp = _sw_build("pb_tamper", "28,28,N", [("edit", "cell:28,27,."), ("move", "F"), ("move", "F")])
    code, _o, _e = _pb_playback(SHELL_EXE, sp)
    if code != 0:
        raise Red("the untampered session did not play back")
    # change one move command without recomputing its witness/head
    doc = json.load(open(sp, encoding="utf-8"))
    for e in doc["data"]["log"]:
        if e["kind"] == "move":
            e["command"] = "B"
            break
    with open(sp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1)
    code, _o, err = _pb_playback(SHELL_EXE, sp)
    if code != 2 or "DIVERGED" not in err:
        raise Red("a tampered move was not caught by playback: %d %s" % (code, err.strip()[:60]))
    # truncating the log (dropping the last event) is also caught (the stored head no longer matches)
    sp2 = _sw_build("pb_trunc", "28,28,N", [("edit", "cell:28,27,."), ("move", "F"), ("move", "F")])
    doc2 = json.load(open(sp2, encoding="utf-8"))
    doc2["data"]["log"] = doc2["data"]["log"][:-1]
    with open(sp2, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc2, fh, indent=1)
    code, _o, err = _pb_playback(SHELL_EXE, sp2)
    if code != 2 or "DIVERGED" not in err:
        raise Red("a truncated log was not caught by playback: %d %s" % (code, err.strip()[:60]))
    return ("a tampered move command and a truncated log both make playback REFUSE (DIVERGED, exit 2) — the re-derived witness or "
            "head no longer matches the seal, so playback never silently produces frames for an authority the seal does not name")


def shell_playback_checkpoint():
    need_rustc()
    _pb_dir()
    events = [("edit", "cell:28,27,."), ("move", "F"), ("move", "F"), ("edit", "tile:floor,96,80,64"), ("move", "L"), ("move", "F")]
    sp = _sw_build("pb_ck", "28,28,N", events)
    # the full playback's move digest sequence and head
    code, out, _e = _pb_playback(SHELL_EXE, sp)
    full_frames, full_head, _f = _pb_parse(out)
    full_seq = [f["digest"] for f in full_frames]
    cuts = []
    for k in range(len(events) + 1):
        ck = os.path.join(PB, "ck_%d" % k)
        code, cout, cerr = _pb_run(SHELL_EXE, ["checkpoint", "--session", sp, "--at", str(k), "--out", ck])
        if code != 0:
            raise Red("checkpoint at %d failed: %s" % (k, cerr.strip()))
        prefix = [ln.split()[5] for ln in cout.strip().splitlines() if ln.startswith("prefix frame ")]
        code, rout, rerr = _pb_run(SHELL_EXE, ["resume", "--session", sp, "--checkpoint", ck])
        if code != 0:
            raise Red("resume from checkpoint at %d failed: %s" % (k, rerr.strip()))
        suffix = [ln.split()[5] for ln in rout.strip().splitlines() if ln.startswith("suffix frame ")]
        rhead = [ln.split()[2] for ln in rout.strip().splitlines() if ln.startswith("resume head ")][0]
        if prefix + suffix != full_seq:
            raise Red("checkpoint at %d: prefix++suffix frames != the full sequence" % k)
        if not full_head.startswith(rhead):
            raise Red("checkpoint at %d: resumed head %s != full head %s" % (k, rhead, full_head[:12]))
        cuts.append(k)
    # the checkpoint carries the WHOLE authority: corrupt its tiles and resume must DIVERGE (not silently OK)
    ck = os.path.join(PB, "ck_lossy")
    _pb_run(SHELL_EXE, ["checkpoint", "--session", sp, "--at", "1", "--out", ck])   # suffix includes the tile edit
    tb = bytearray(read(ck + ".tiles"))
    tb[8] ^= 0xFF  # flip a byte of the checkpoint's tiles
    with open(ck + ".tiles", "wb") as fh:
        fh.write(tb)
    code, _o, err = _pb_run(SHELL_EXE, ["resume", "--session", sp, "--checkpoint", ck])
    if code != 2 or "DIVERGED" not in err:
        raise Red("a checkpoint with corrupted tiles did not diverge on resume: %d %s" % (code, err.strip()[:60]))
    return ("replay from a certified checkpoint reproduces the identical frame-witness suffix and head at all %d cut positions "
            "(prefix++suffix == the full sequence, resumed head == the full head), and a checkpoint whose tiles were corrupted "
            "DIVERGES on resume — the checkpoint carries the whole interleaved authority, not a partial projection" % len(cuts))


# ------------------------------------------------------------------ gauntlet1 (GAUNTLET-1a: the emit differential)
def _fast_lines(level, tiles, camera):
    code, out, err = run(KERNEL_EXE, ["--level", os.path.join(ORACLE, "levels", level + ".lvl"),
                                      "--tiles", os.path.join(ORACLE, "tiles", tiles + ".tiles"),
                                      "--camera", camera, "--fast"])
    if code != 0:
        raise Red("kernel --fast exited %d on %s@%s: %s" % (code, level, camera, err.strip()))
    return dict(ln.split(" ", 1) for ln in out.strip().splitlines() if " " in ln)


def _g1_cases():
    c = corpus()
    cases = []
    for _name, sc in c["scenes"].items():
        x, z, f = sc["camera"]
        for tiles in sc["witnesses"].keys():
            cases.append((sc["level"], tiles, "%d,%d,%s" % (x, z, f)))
    # adversarial witness cameras: all four facings at the spawn (both u-axes, both signs) and the frozen-traversable
    # positions of the SHELL-PLAYBACK reference path (28,27 is rock on the UNEDITED level — the demo opens it by an
    # edit — so it is excluded; the differential renders the frozen corpus)
    for cam in ["34,28,N", "34,28,E", "34,28,S", "34,28,W", "28,28,N", "28,26,N", "28,26,W", "27,26,W"]:
        cases.append(("witness", "identity", cam))
    seen, uniq = set(), []
    for cs in cases:
        if cs not in seen:
            seen.add(cs)
            uniq.append(cs)
    return uniq


def gauntlet1_equiv():
    need_rustc()
    cases = _g1_cases()
    for (lvl, tiles, cam) in cases:
        d = _fast_lines(lvl, tiles, cam)
        if d.get("selfcheck") != "OK":
            raise Red("kernel did not selfcheck on %s@%s" % (lvl, cam))
        if d.get("fast_equal") != "OK":
            raise Red("fast emit DIFFERS from the frozen emit on %s %s@%s" % (lvl, tiles, cam))
        if d.get("fast_pixels") != d.get("pixels") or d.get("fast_frame") != d.get("frame"):
            raise Red("fast pixels/frame != frozen on %s %s@%s" % (lvl, tiles, cam))
    return ("the sibling fast.rs emit is byte-identical to the frozen mantle.rs emit over %d cases (every corpus scene x its tile "
            "sets, plus adversarial witness cameras: the four spawn facings and the frozen-traversable sessionwalk positions) — "
            "fast_pixels == pixels AND fast_frame == frame everywhere; the GAUNTLET-1a seed is an exact transcription, so the "
            "differential harness (candidate -> frozen, never the reverse) is proven before any optimization technique" % len(cases))


def gauntlet1_region():
    need_rustc()
    d = _fast_lines("witness", "identity", "34,28,W")
    reg = dict(kv.split("=") for kv in d["fast_region"].split())
    work = dict(kv.split("=") for kv in d["fast_divwork"].split() if "=" in kv)
    wall_tex, floor_tex = int(reg["wall_tex"]), int(reg["floor_tex"])
    wall_work, floor_work = int(work["wall"]), int(work["floor"])
    if wall_work != wall_tex or floor_work != 4 * floor_tex:
        raise Red("the divide-work is not per-source (wall 1/px, floor 4/px): %s" % d["fast_divwork"])
    dominant = "floor" if floor_work >= wall_work else "wall"
    if work.get("dominant") != dominant:
        raise Red("the reported dominant region disagrees with the divide-work")
    return ("the DETERMINISTIC region measure on the witness frame (34,28,W): %d wall-textured px (1 divide each) vs %d "
            "floor-textured px (4 divides each) -> divide-work wall %d, floor %d; the FLOOR dominates (%s) by ~%dx, so "
            "GAUNTLET-1b's exact optimization targets the floor's per-row perspective divides — not the wall, and not the "
            "frame-pass floor cast the original hypothesis named" % (wall_tex, floor_tex, wall_work, floor_work, dominant, floor_work // max(wall_work, 1)))


def gauntlet1b_reduction():
    """GAUNTLET-1b: the floor divide-collapse. The candidate emit is byte-identical to the frozen emit (the same
    gauntlet1-equiv court judges it) AND its floor loop does exactly HALF the floor divides — 2 per textured floor
    pixel (one div_euclid per coordinate) where the frozen did 4 (two texel, each rem_euclid + div_euclid) — with the
    wall and ceiling untouched. This gates the DETERMINISTIC divide reduction (a source-cost proxy, not a wall-clock);
    the speed itself is GAUNTLET-1b's separate host court (verify/gauntlet1b.py, sealed off-gate citing GAUNTLET-1)."""
    need_rustc()
    d = _fast_lines("witness", "identity", "34,28,W")
    if d.get("fast_equal") != "OK" or d.get("fast_pixels") != d.get("pixels"):
        raise Red("the GAUNTLET-1b candidate is not byte-identical to the frozen emit on the witness frame")
    reg = dict(kv.split("=") for kv in d["fast_region"].split())
    base = dict(kv.split("=") for kv in d["fast_divwork"].split() if "=" in kv)
    opt = dict(kv.split("=") for kv in d["fast_optwork"].split() if "=" in kv)
    wall_tex, floor_tex = int(reg["wall_tex"]), int(reg["floor_tex"])
    base_floor = int(base["floor"])
    opt_wall, opt_floor, saved = int(opt["wall"]), int(opt["floor"]), int(opt["floor_saved"])
    if base_floor != 4 * floor_tex:
        raise Red("the frozen floor divide-work is not 4/px: %s" % d["fast_divwork"])
    if opt_wall != wall_tex:
        raise Red("the candidate changed the wall divide-work (the collapse must touch only the floor): %s" % d["fast_optwork"])
    if opt_floor != 2 * floor_tex:
        raise Red("the candidate floor divide-work is not 2/px (the 4->2 collapse): %s" % d["fast_optwork"])
    if saved != base_floor - opt_floor or saved != 2 * floor_tex:
        raise Red("floor_saved is not exactly the removed half of the floor divides: %s" % d["fast_optwork"])
    if opt.get("dominant") != ("floor" if opt_floor >= opt_wall else "wall"):
        raise Red("the candidate's reported dominant region disagrees with its divide-work")
    return ("GAUNTLET-1b's floor divide-collapse is byte-identical to the frozen emit (fast_equal OK, fast_pixels == "
            "pixels on 34,28,W) AND does exactly HALF the floor divides: %d floor-textured px at 2/px = %d (candidate) "
            "vs 4/px = %d (frozen), the wall unchanged at %d — %d divides removed on this frame, the floor still the "
            "dominant divide region left for GAUNTLET-1c. The reduction is deterministic (a source-cost proxy); the "
            "speed is a separate host court (gauntlet1b.py, off-gate, citing GAUNTLET-1)" % (floor_tex, opt_floor, base_floor, opt_wall, saved))


def gauntlet1_preregistered():
    """GAUNTLET-1's acceptance and promotion rule is locked: byte-identity is mandatory and gate-enforced, speed is a
    separate court, mantle.rs stays the frozen oracle, and a speed number is never cross-compared to GAUNTLET-0's
    instrumented render. Weakening any of it is a visible diff, not a silent re-hash."""
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))
    e = reg["entries"].get("GAUNTLET-1")
    if not e:
        raise Red("GAUNTLET-1 is not registered")
    hyp, succ, fail = e["hypothesis"], e["success_condition"], e["failure_condition"]
    lims = " ".join(e["interpretation_limits"]).lower()
    checks = {
        "emit is the accepted-renderer target": "emit" in hyp and "ACCEPTED as a renderer" in hyp,
        "byte-identity is mandatory and independent of speed": "byte-identical" in hyp and "independent of speed" in hyp,
        "a differing pixel is not a renderer at any speed": "different pixels is not a renderer at any speed" in hyp,
        "equivalence is gate-enforced (fast_pixels == pixels)": "fast_pixels == pixels" in succ,
        "any diff refuses the candidate regardless of speed": "regardless of speed" in fail,
        "two separate courts": "two separate courts" in lims,
        "mantle.rs stays the frozen oracle": "mantle.rs is the frozen correctness oracle" in lims and "mantle.rs is modified" in fail,
        "no cross-compare to GAUNTLET-0's absolute": "never compared to gauntlet-0" in lims,
        "the region measure is divide-work, not a wall-clock": "divide-work" in lims and "not a wall-clock" in lims,
    }
    missing = [k for k, ok in checks.items() if not ok]
    if missing:
        raise Red("the GAUNTLET-1 method is not fully locked: " + "; ".join(missing))
    want = envelope.chain_hash({"name": "verdandi-preregistration-entry", "version": 1, "claim_class": "declared",
                                "provenance": {"registered_in": "verify/preregister.json"},
                                "validity_scope": {"certifies": "the conditions GAUNTLET-1 was seated under"},
                                "forbidden_interpretations": ["that registering a condition earns it"],
                                "data": {k: v for k, v in e.items() if k != "chain_hash"}})
    if e["chain_hash"] != want:
        raise Red("the GAUNTLET-1 entry was edited after registration (chain hash)")
    return ("GAUNTLET-1's acceptance + promotion rule is locked before any candidate: byte-identity to the frozen emit "
            "(fast_pixels == pixels, fast_frame == frame over corpus + adversarial cameras) is MANDATORY and gate-enforced "
            "(gauntlet1-equiv); speed is a SEPARATE court (identical-but-slower is a correctness pass / performance fail, a "
            "differing pixel is not a renderer at any speed); mantle.rs stays the frozen oracle and a speed number is never "
            "cross-compared to GAUNTLET-0's instrumented absolute; hash-locked %s" % e["chain_hash"][:8])


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
    row("latency-preregistered", latency_preregistered)
    row("gauntlet-preregistered", gauntlet_preregistered)
    row("gauntlet1-preregistered", gauntlet1_preregistered)
    row("gauntlet1-equiv", gauntlet1_equiv)
    row("gauntlet1-region", gauntlet1_region)
    row("gauntlet1b-reduction", gauntlet1b_reduction)
    row("shell-build", shell_build)
    row("shell-blit-pins", shell_blit_pins)
    row("shell-blit-law", shell_blit_law)
    row("shell-blit-plant", shell_blit_plant)
    row("membrane-build", membrane_build)
    row("membrane-witness", membrane_witness)
    row("membrane-legal", membrane_legal)
    row("membrane-wall", membrane_wall)
    row("text-build", text_build)
    row("text-roundtrip", text_roundtrip)
    row("text-reformat", text_reformat)
    row("text-edit", text_edit)
    row("text-refuse", text_refuse)
    row("workshop1-build", workshop1_build)
    row("workshop1-replay", workshop1_replay)
    row("workshop1-undo", workshop1_undo)
    row("workshop1-propose", workshop1_propose)
    row("workshop1-tamper", workshop1_tamper)
    row("workshop1-demo", workshop1_demo)
    row("input-build", input_build)
    row("input-replay", input_replay)
    row("input-blocked", input_blocked)
    row("input-tamper", input_tamper)
    row("input-not-authority", input_not_authority)
    row("input-demo", input_demo)
    row("sessionwalk-build", sessionwalk_build)
    row("sessionwalk-replay", sessionwalk_replay)
    row("sessionwalk-interleave", sessionwalk_interleave)
    row("sessionwalk-batch-invariance", sessionwalk_batch_invariance)
    row("sessionwalk-tamper", sessionwalk_tamper)
    row("sessionwalk-projection", sessionwalk_projection)
    row("sessionwalk-demo", sessionwalk_demo)
    row("shell-playback-sealed-input", shell_playback_sealed_input)
    row("shell-playback-frame-sequence", shell_playback_frame_sequence)
    row("shell-playback-blit-law", shell_playback_blit_law)
    row("shell-playback-no-authority", shell_playback_no_authority)
    row("shell-playback-order", shell_playback_order)
    row("shell-playback-tamper", shell_playback_tamper)
    row("shell-playback-checkpoint", shell_playback_checkpoint)
    fails = sum(1 for st, _, _ in ROWS if st == "FAIL")
    skips = sum(1 for st, _, _ in ROWS if st == "SKIP")
    rowset = sha256("\n".join(name for _, name, _ in ROWS).encode("utf-8"))[:16]
    print("GATE FAILED" if fails else "GATE PASSED")
    print(f"RECONCILE  rowset {rowset}  {len(ROWS)} rows / {fails} fail / {skips} skipped")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
