# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""verify.py — the Verðandi gate. Every claim in the repository as a row that can redden.

    python verify/verify.py            # from the repository root (any cwd works)

Prints one line per row, `GATE PASSED` or `GATE FAILED`, and a reconcile line naming the rowset. Rows that
need `rustc` SKIP without it, count-stable. Nothing here prints a clock or a temporary path, so two
consecutive runs are byte-identical when the tree is; that identity is the landing condition.

Stages: oracle (pure Python, the frozen evidence is self-consistent), kernel (the placement reproduces the
oracle natively; the corpus; the mirrored sign table as the control that shows the rows can redden).
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


def witnesses(exe: str, level: str, tiles: str, camera: str) -> tuple[str, str]:
    code, out, err = run(exe, ["--level", os.path.join(ORACLE, "levels", level + ".lvl"),
                               "--tiles", os.path.join(ORACLE, "tiles", tiles + ".tiles"), "--camera", camera])
    if code != 0:
        raise Red(f"kernel exited {code}: {err.strip()}")
    lines = dict(ln.split(" ", 1) for ln in out.strip().splitlines() if " " in ln)
    if lines.get("selfcheck") != "OK":
        raise Red("kernel selfcheck DIVERGED")
    return lines["frame"], lines["pixels"]


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
    return "kernel/main.rs (+ mantle.rs, formats.rs) compiled live with " + " ".join(FLAGS)


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


# ------------------------------------------------------------------ main
def main() -> int:
    print("VERÐANDI GATE")
    row("oracle-frozen", oracle_frozen)
    row("kernel-build", kernel_build)
    row("kernel-oracle", kernel_oracle)
    row("kernel-corpus", kernel_corpus)
    row("kernel-selftest", kernel_selftest)
    fails = sum(1 for st, _, _ in ROWS if st == "FAIL")
    skips = sum(1 for st, _, _ in ROWS if st == "SKIP")
    rowset = sha256("\n".join(name for _, name, _ in ROWS).encode("utf-8"))[:16]
    print("GATE FAILED" if fails else "GATE PASSED")
    print(f"RECONCILE  rowset {rowset}  {len(ROWS)} rows / {fails} fail / {skips} skipped")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
