# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""verify.py — the Verðandi gate. Every claim in the repository as a row that can redden.

    python verify/verify.py            # from the repository root (any cwd works)

Prints one line per row, `GATE PASSED` or `GATE FAILED`, and a reconcile line naming the rowset. Rows that
need `rustc` SKIP without it, count-stable. Nothing here prints a clock or a temporary path, so two
consecutive runs are byte-identical when the tree is; that identity is the landing condition.

Stages: oracle (pure Python, the frozen evidence is self-consistent), game (GAME-0: Urðr's game layer carried
verbatim from the same tag — bytes, sha256 and git blob equal a digest-pinned manifest, Urðr's own suites pass in
place, a flipped golden reddens both fences, and no runtime code reaches into it), kernel (the placement reproduces the
oracle natively; the corpus; the mirrored sign table as the control that shows the rows can redden),
workshop (an edit is a new authority and the witnesses say what it moved; the planted falsifiers bite),
hud (the overlay is a frame: pinned, index-free, inside its region, reading state and not materials),
records (RECORD-0: every record Verðandi mints passes the envelope's firewall, the two writers agree, and a
rung that produces a number on a host was preregistered with a failure condition; LATENCY-0's method — the
SOFTWARE-144-BUDGET / HARDWARE-144 split, their conjunction, and the honest scope — LATENCY-1's, its amendment
LATENCY-1a (the instrument fact, checked in source: LATENCY-0's window renders before it opens, so it cannot see the
renderer) and the render-inclusive LATENCY-1R, with both host sealers driven by synthetic numbers — and GAUNTLET-0's method —
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
input diverges rather than minting a new authority, and replay from any certified checkpoint reproduces the head),
latency1r (LATENCY-1R's court, headless: the render-inclusive court over a deterministic mock surface on the sealed
session — witnesses first, the declared phase regimes, plants that refuse with no record — and the fence that keeps
LATENCY-0's instrument a byte-exact prefix of shell/win32.rs), framesplit (FRAME-SPLIT-0: the split of render-start ->
frame-ready into seven contiguous phases beside its uninstrumented envelope — locked method, sealer rules, the court
over the mock, and the fence that keeps the marked mirror on fast::render's calls), presentscale (PRESENT-SCALE-0: the
same frame presented into a half-size and a full-size client area, the destination the only variable — locked method,
the diagnostic attribution rule, the court over the mock with a clamped-geometry plant, and the fence), presentstretch
(PRESENT-STRETCH-0: the half-size blit under three GDI stretch modes, the mode the only variable), allocreuse
(ALLOC-REUSE-0: the frame with its buffers allocated every frame vs once, the lifetime the only variable), allocreuse1
(ALLOC-REUSE-1: the persistent-buffer render-loop entry's adoption court — correctness first over the corpus, the
adversarial cameras and the sealed session from poisoned buffers in three orders; the same-run p99 rule; the fence that
pins the fresh reference; and allocreuse1-lock, the ADOPT carried out: LoopRenderer the production entry for in-loop
rendering, every fresh render entry's call site pinned), presentexact (PRESENTATION-CHOICE-0, declared: the certified
picture 1:1 in a borderless window; PRESENT-EXACT-0: StretchDIBits at 1:1 against SetDIBitsToDevice, the composed screen
read back as a hard gate, the same-run p99 rule, and the fence; presentexact-lock, the conforming presenter `shell show`
locked to SetDIBitsToDevice with the screen read back after every present), hoststate (HOST-STATE-0: the host's state
recorded beside a court, never controlled and never read by a rule), and — in the oracle stage — oracle-d0 (Urðr's own
statecanon recomputes the oracle's D_0 in place).
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
# Default output is COMPACT (one short line per row); --verbose (-v) prints each row's full reading. A FAIL always
# prints its reason regardless, so a red row is never silent. This changes only what is printed — the row set, the
# ordering, the pass/fail logic and the RECONCILE rowset are untouched, so the gate's identity is unchanged.
VERBOSE = ("-v" in sys.argv) or ("--verbose" in sys.argv)


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
    if VERBOSE or st == "FAIL":
        print(f"[{st}] {name:<28} {text}")
    else:
        print(f"[{st}] {name}")


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


# ------------------------------------------------------------------ game (GAME-0)
# GAME-0: Urðr's game layer carried as frozen evidence. The seventeen discrete vertical slices (gamegen … cue), their
# corpora, suites, briefs, the D24/D25 boundaries and the two exact-arithmetic physics modules kinema reads its radix
# from — verbatim from the SAME tag the oracle cites, so no new oracle is minted and no charter clause moves. The
# manifest is pinned here by digest, so re-indexing the evidence is a visible diff in the gate itself.
GAME = os.path.join(ORACLE, "game")
GAME_MANIFEST_SHA256 = "d506abe3341ca3762786a639422e28a47b33e3cb11aa8e03206e35ffc05ffce4"
GAME_PROSE = {"MANIFEST.json", "README.md"}   # Verðandi's index and prose beside the evidence, never evidence
GAME_STDLIB = {"ast", "collections", "hashlib", "inspect", "io", "os", "subprocess", "sys", "unittest"}


def game_imports(root: str) -> set:
    """Every top-level module name any .py under `root` imports (absolute imports; AST, not grep)."""
    import ast
    names = set()
    for rel in game_tree(root):
        if rel.endswith(".py"):
            for n in ast.walk(ast.parse(read(os.path.join(root, rel)).decode("utf-8"))):
                if isinstance(n, ast.Import):
                    names |= {a.name.split(".")[0] for a in n.names}
                elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
                    names.add(n.module.split(".")[0])
    return names


def git_blob(b: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def game_manifest() -> dict:
    with open(os.path.join(GAME, "MANIFEST.json"), encoding="utf-8") as fh:
        return json.load(fh)


def game_tree(root: str) -> list[str]:
    out = []
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x != "__pycache__")
        for f in files:
            rel = os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/")
            if rel not in GAME_PROSE and not f.endswith(".pyc"):
                out.append(rel)
    return sorted(out)


def game_bytes_fault(root: str, m: dict) -> str | None:
    """The first way the tree at `root` departs from the manifest, or None. Bytes, sha256 and the git blob are all
    recomputed from disk: the blob is what `git ls-tree -r urdr-oracle-1` names in Urðr, so a reviewer holding
    Urðr can check every file without trusting this repository."""
    listed = [f["path"] for f in m["files"]]
    on_disk = game_tree(root)
    if on_disk != sorted(listed):
        extra, missing = sorted(set(on_disk) - set(listed)), sorted(set(listed) - set(on_disk))
        return f"the tree is not the manifest: extra {extra[:3]}, missing {missing[:3]}"
    for f in m["files"]:
        b = read(os.path.join(root, f["path"]))
        if len(b) != f["bytes"] or sha256(b) != f["sha256"] or git_blob(b) != f["git_blob"]:
            return f"{f['path']}: bytes/sha256/git blob do not match the manifest"
    return None


def game_env() -> dict:
    env = dict(os.environ)
    env.update({"PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
    return env


def game_unittest(root: str, pattern: str) -> tuple[int, int, str]:
    """(returncode, tests ran, last line) of Urðr's own suites, run in place from `root`."""
    cp = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", pattern],
                        cwd=root, env=game_env(), capture_output=True, text=True, encoding="utf-8")
    ran = re.findall(r"^Ran (\d+) tests? in ", cp.stderr, re.M)
    tail = cp.stderr.strip().splitlines()[-1] if cp.stderr.strip() else ""
    return cp.returncode, int(ran[-1]) if ran else -1, tail


def game_frozen():
    m, c = game_manifest(), corpus()
    got = sha256(read(os.path.join(GAME, "MANIFEST.json")))
    if got != GAME_MANIFEST_SHA256:
        raise Red(f"oracle/game/MANIFEST.json is {got[:12]}, not the pinned {GAME_MANIFEST_SHA256[:12]} — the index moved")
    o = m["origin"]
    if (o["tag"], o["commit"]) != (c["origin"]["tag"], c["origin"]["commit"]) or o["tag"] != "urdr-oracle-1":
        raise Red("the game layer names another origin than the oracle — a different tag is a new oracle, never this one")
    fault = game_bytes_fault(GAME, m)
    if fault:
        raise Red(fault)
    cl = m["closure"]
    if len(cl["modules"]) != 17 or cl["physics"] != ["field", "rational"]:
        raise Red("the closure is not the seventeen slices plus field/rational")
    for mod in cl["modules"]:
        for p in (f"tools/terrain/{mod}.py", f"tools/terrain/conformance_{mod}.txt", f"tests/test_{mod}.py", f"docs/{mod}_brief.md"):
            if p not in {f["path"] for f in m["files"]}:
                raise Red(f"slice {mod} is missing {p}")
    roles: dict = {}
    for f in m["files"]:
        roles[f["role"]] = roles.get(f["role"], 0) + 1
    tally = ", ".join(f"{v} {k}" for k, v in sorted(roles.items()))
    closed = set(cl["modules"]) | set(cl["physics"])
    stray = sorted(game_imports(GAME) - closed - GAME_STDLIB)
    if stray:
        raise Red(f"the game layer imports outside its closure and the pinned stdlib set: {stray}")
    return (f"{len(m['files'])} files ({tally}) are Urðr's game layer verbatim @ {o['commit'][:7]} — the oracle's own tag; "
            f"each file's bytes, sha256 and git blob recomputed from disk equal the manifest, the tree holds nothing else, "
            f"the manifest is pinned here by digest ({GAME_MANIFEST_SHA256[:12]}…), and every import is one of the "
            f"{len(closed)} closure modules or the {len(GAME_STDLIB)} pinned stdlib names (closed, no third-party code)")


def game_suites():
    m = game_manifest()
    want = m["closure"]["tests"]
    code, ran, tail = game_unittest(GAME, "test_*.py")
    if code != 0 or tail != "OK":
        raise Red(f"Urðr's suites did not pass in place: exit {code}, {tail!r}")
    if ran != want:
        raise Red(f"ran {ran} tests, the manifest pins {want} — the closure is not the one that was imported")
    for mod in m["closure"]["modules"]:
        cp = subprocess.run([sys.executable, "-B", os.path.join("tools", "terrain", mod + ".py")], cwd=GAME,
                            env=game_env(), capture_output=True, text=True, encoding="utf-8")
        if cp.returncode != 0:
            raise Red(f"{mod}'s own witness exited {cp.returncode}")
        if "does_not_show" not in cp.stdout:
            raise Red(f"{mod}'s witness printed no does_not_show boundary")
    return (f"Urðr's own {ran} red-first tests pass in place under PYTHONHASHSEED=0 (conformance goldens included), and "
            f"all {len(m['closure']['modules'])} slices' witnesses exit 0 and print their does_not_show boundary — the "
            f"game layer is self-contained here, stdlib only, with no Urðr checkout beside it")


def game_plant():
    """Both fences bite on a scratch copy: one golden digit flipped in conformance_move.txt is refused by the byte
    fence AND reddens Urðr's own suite. The real tree is never touched; the copy is removed."""
    m = game_manifest()
    scratch = os.path.join(ROOT, ".gate-game-plant")
    if os.path.isdir(scratch):
        shutil.rmtree(scratch)
    try:
        shutil.copytree(GAME, scratch, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        if game_bytes_fault(scratch, m) is not None:
            raise Red("the unplanted copy already departs from the manifest")
        p = os.path.join(scratch, "tools", "terrain", "conformance_move.txt")
        text = read(p).decode("utf-8")
        i = text.index("\nmove-digest ") + len("\nmove-digest ")
        flipped = "0" if text[i] != "0" else "1"
        with open(p, "wb") as fh:
            fh.write((text[:i] + flipped + text[i + 1:]).encode("utf-8"))
        fault = game_bytes_fault(scratch, m)
        if fault is None or "conformance_move.txt" not in fault:
            raise Red("a flipped golden digit passed the byte fence")
        code, ran, tail = game_unittest(scratch, "test_move.py")
        if code == 0 or not tail.startswith("FAILED"):
            raise Red("a flipped golden digit did not redden Urðr's own suite")
    finally:
        if os.path.isdir(scratch):
            shutil.rmtree(scratch)
    return ("PLANT: one hex digit of move's frozen move-digest golden, flipped in a scratch copy, is refused by the byte "
            "fence (sha256/git blob) AND reddens test_move — the goldens are frozen, not rewritten, and both fences bite")


GAME_NAMES = ("oracle/game", "oracle\\\\game", "oracle\\game")


def game_refs(src: str) -> list[str]:
    """References to the imported game layer in CODE (comment lines dropped: a provenance comment naming where a
    port came from, as mantle.rs names Urðr's tools/terrain/mantle_rs, is history, not a dependency)."""
    code = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith(("//", "#")) or ln.lstrip().startswith("#["))
    return [n for n in GAME_NAMES if n in code]


def game_not_runtime():
    """The charter: Urðr is frozen evidence, not a runtime dependency. No kernel, workshop or shell source reaches
    into oracle/game (no #[path], include_*!, or file path); only the gate reads it. A plant proves the scan sees one."""
    hits = []
    for sub in ("kernel", "workshop", "shell"):
        d = os.path.join(ROOT, sub)
        for f in sorted(os.listdir(d)):
            if f.endswith((".rs", ".py")):
                refs = game_refs(read(os.path.join(d, f)).decode("utf-8"))
                if refs:
                    hits.append(f"{sub}/{f} -> {refs[0]}")
    if hits:
        raise Red("the game layer is referenced from runtime code: " + "; ".join(hits))
    if not game_refs('#[path = "../oracle/game/tools/terrain/move.py"]'):
        raise Red("PLANT: a runtime reference to oracle/game was not seen by the scan")
    if not game_refs('    let b = std::fs::read("oracle/game/tools/terrain/conformance_move.txt");'):
        raise Red("PLANT: a runtime file read of oracle/game was not seen by the scan")
    return ("no kernel/, workshop/ or shell/ code reaches into oracle/game — the game layer is evidence the gate reads, "
            "never a runtime dependency (the charter's ORACLE clause); PLANTS: a planted #[path] and a planted file read "
            "into oracle/game are both seen")


ORACLE_D0_SNIPPET = r"""
import json, sys
sys.path.insert(0, "tools/terrain")
import gamegen as G, entity as E, rngstream as R, actionlog as A, statecanon as S
seed, depth, pos = int(sys.argv[1], 16), int(sys.argv[2]), (int(sys.argv[3]), int(sys.argv[4]))
log = json.loads(sys.argv[5])
print(S.d_n(G.generate(seed, depth), E.at(pos), R.apply(R.root(seed), []), A.from_actions(log)))
"""


def oracle_d0_of(seed: str, depth: int, pos, log) -> str:
    cp = subprocess.run([sys.executable, "-B", "-c", ORACLE_D0_SNIPPET, seed.replace("0x", ""), str(depth), str(pos[0]),
                         str(pos[1]), json.dumps(log)], cwd=GAME, env=game_env(), capture_output=True, text=True,
                        encoding="utf-8")
    if cp.returncode != 0:
        tail = cp.stderr.strip().splitlines()[-1] if cp.stderr.strip() else "no output"
        raise Red("Urðr's statecanon did not run in place: " + tail)
    return cp.stdout.strip()


def oracle_d0():
    """ORACLE-D0: the oracle's third hash, until now carried as evidence only, is recomputed at gate time by Urðr's own
    code in place (oracle/game: gamegen, entity, rngstream, actionlog, statecanon) from the oracle's view — the level at
    (seed, depth), the entity at pos, the RNG stream at its root, an empty action log — and equals urdr-oracle-1.json's
    D_0. Verðandi still mints nothing: the composition is statecanon's. PLANT: the entity one cell over gives a different
    D_0."""
    o = oracle()
    v = o["view"]
    got = oracle_d0_of(v["seed"], v["depth"], v["pos"], [])
    if got != o["D_0"]:
        raise Red(f"Urðr's statecanon composes {got[:12]}… for the oracle's view, not the oracle's D_0 {o['D_0'][:12]}…")
    moved = oracle_d0_of(v["seed"], v["depth"], [v["pos"][0] + 1, v["pos"][1]], [])
    if moved == o["D_0"]:
        raise Red("PLANT: an entity one cell over composed the same D_0")
    return ("D_0 recomputed in place by Urðr's own statecanon (level %s depth %d, entity at %s, the RNG stream at its root, an "
            "empty action log) equals urdr-oracle-1.json's %s… — the oracle's third hash is now checked, not only carried, "
            "and Verðandi mints none of it; PLANT: the entity one cell over composes a different D_0"
            % (v["seed"], v["depth"], tuple(v["pos"]), o["D_0"][:12]))


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


def latency1_preregistered():
    """LATENCY-1's method is locked before any host number: it asks whether the promoted T=8 threaded render measurably
    changes frame-ready -> composited latency versus the LATENCY-0 sealed baseline — the SAME observable, inherited not
    re-derived, and NEVER compared to an emit p99 (a different observable; the GAUNTLET-2 7734 us baseline is one). The
    delta reading (improvement / none / degradation) is disciplined, and none of it proves input-to-photon. Hash-locked."""
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))
    e = reg["entries"].get("LATENCY-1")
    if not e:
        raise Red("LATENCY-1 is not registered")
    succ = e["success_condition"].lower()
    lims = " ".join(e["interpretation_limits"]).lower()
    checks = {
        "the comparator is LATENCY-0's frame-ready->composited, NEVER an emit p99": "not an emit p99" in lims and "different observables" in lims,
        "the baseline is inherited from LATENCY-0, never re-derived": "inherited" in lims and "latency-0" in lims and "never re-derived" in lims,
        "the disciplined delta reading (improvement / none / degradation)": "presentation" in lims and "dominant" in lims and "contention" in lims,
        "input-to-photon is out of scope": "not input-to-photon" in lims,
        "same apparatus + same sealed session as LATENCY-0": "same apparatus" in succ and "same sealed" in succ,
        "Windows-only, off-gate host": "windows-only" in lims,
    }
    missing = [k for k, ok in checks.items() if not ok]
    if missing:
        raise Red("the LATENCY-1 method is not fully locked: " + "; ".join(missing))
    want = envelope.chain_hash({"name": "verdandi-preregistration-entry", "version": 1, "claim_class": "declared",
                                "provenance": {"registered_in": "verify/preregister.json"},
                                "validity_scope": {"certifies": "the conditions LATENCY-1 was seated under"},
                                "forbidden_interpretations": ["that registering a condition earns it"],
                                "data": {k: v for k, v in e.items() if k != "chain_hash"}})
    if e["chain_hash"] != want:
        raise Red("the LATENCY-1 entry was edited after registration (chain hash)")
    return ("LATENCY-1's method is locked before any host number: it measures whether the promoted T=8 threaded render "
            "changes frame-ready -> composited latency for the fixed sealed session, on the SAME apparatus as LATENCY-0, "
            "compared ONLY against LATENCY-0's sealed frame-ready -> composited baseline (the same observable, inherited "
            "from shell/attest/latency-<host>.json, never re-derived) and NEVER against an emit p99 (a different "
            "observable — the GAUNTLET-2 7734 us baseline is one; mixing them is a category error). The delta reads as "
            "headroom-propagates / presentation-dominant / shell-contention, and none of it proves input-to-photon; "
            "Windows-only, off-gate; hash-locked %s" % e["chain_hash"][:8])


# ------------------------------------------------------------------ LATENCY-1a / LATENCY-1R
# LATENCY-0's instrument (shell/win32.rs as sealed at 0de8341, unchanged since): its bytes must stay a PREFIX of the
# file, so any court added later is appended after it and the instrument LATENCY-1 reuses is provably the same one.
LATENCY0_WIN32_LEN = 24869
LATENCY0_WIN32_SHA256 = "450900b054aed11615a26f91dcc347e905bdc1cd79ec2d46a738346d81523220"
# playback::frames — the pre-render LATENCY-0's (and LATENCY-1's) window plays — pinned by its text
PLAYBACK_FRAMES_SHA256 = "acb457940212c9b410e4cd02245f339a95ebe0232fd3a8fe0a057c3ca6a75569"
PLAYBACK_WINDOW_DISPATCH = ("                        let frames = playback::frames(&session, &root);\n"
                            "                        win32::playback_window(frames, measure, &host);\n")


def entry_hash_ok(rung: str, e: dict) -> bool:
    return e.get("chain_hash") == envelope.chain_hash({
        "name": "verdandi-preregistration-entry", "version": 1, "claim_class": "declared",
        "provenance": {"registered_in": "verify/preregister.json"},
        "validity_scope": {"certifies": f"the conditions {rung} was seated under"},
        "forbidden_interpretations": ["that registering a condition earns it"],
        "data": {k: v for k, v in e.items() if k != "chain_hash"}})


def src_span(src: str, start: str, end: str) -> str:
    i = src.index(start)
    return src[i:src.index(end, i + len(start))]


def latency1a_preregistered():
    """The LATENCY-1 amendment is locked before any LATENCY-1 host number, it cites LATENCY-1's CURRENT hash (so it
    amends that entry and no other), and the instrument fact it records is TRUE IN SOURCE: the playback-window
    dispatch renders every frame (`playback::frames`) before the window opens, and `latency_measure` times blit ->
    composited over pre-rendered bitmaps with no render call inside it."""
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    e = reg.get("LATENCY-1a")
    if not e:
        raise Red("the LATENCY-1 amendment (LATENCY-1a) is not registered")
    if e.get("amends") != {"rung": "LATENCY-1", "chain_hash": reg["LATENCY-1"]["chain_hash"]}:
        raise Red("LATENCY-1a does not amend LATENCY-1's current registration")
    hyp, succ, fail = e["hypothesis"].lower(), e["success_condition"].lower(), e["failure_condition"].lower()
    lims = " ".join(e["interpretation_limits"]).lower()
    checks = {
        "the instrument fact (pre-render, blit -> composited)": "playback::frames" in hyp and "before the window opens" in hyp and "cannot observe" in hyp,
        "the observable/comparator are NOT altered": "does not alter" in hyp and "does not alter" in lims,
        "the 50-permille materiality bound, declared": "50 permille" in succ and "declared convention" in lims,
        "a delta is never read as render headroom or contention": "never as render headroom propagating" in succ and "never as render contention" in succ,
        "the LATENCY-0 record is restored byte-exact": "restored byte-exact" in succ and "restored byte-exact" in fail,
        "the instrument stays a byte-exact prefix of win32.rs": "byte-exact prefix" in fail,
        "the render-inclusive question is LATENCY-1R's, never compared": "latency-1r" in lims and "never compared" in lims,
        "not input-to-photon, Windows-only": "not input-to-photon" in lims and "windows-only" in lims,
    }
    missing = [k for k, ok in checks.items() if not ok]
    if missing:
        raise Red("the LATENCY-1 amendment is not fully locked: " + "; ".join(missing))
    if not entry_hash_ok("LATENCY-1a", e):
        raise Red("the LATENCY-1a entry was edited after registration (chain hash)")
    # the fact, in source
    main_src = read(os.path.join(SHELL, "main.rs")).decode("utf-8")
    if PLAYBACK_WINDOW_DISPATCH not in main_src:
        raise Red("the playback-window dispatch no longer renders the frames (playback::frames) before opening the window")
    w32 = read(os.path.join(SHELL, "win32.rs")).decode("utf-8")
    measure = src_span(w32, "fn latency_measure(", "fn emit_latency(")
    for bad in ("compose_frame", "render(", "arm_composite", "emit("):
        if bad in measure:
            raise Red(f"latency_measure contains a render call ({bad}) — the amendment's instrument fact is false")
    if "StretchDIBits(" not in measure or "(dwm.flush)();" not in measure:
        raise Red("latency_measure no longer times StretchDIBits -> DwmFlush")
    pw = src_span(w32, "pub fn playback_window(", "fn latency_measure(")
    if "frames.iter().map(|c| to_blit(&c.composite)).collect()" not in pw:
        raise Red("playback_window no longer blits the pre-rendered composites")
    return ("LATENCY-1a is locked before any LATENCY-1 host number and amends LATENCY-1's current registration "
            f"({reg['LATENCY-1']['chain_hash'][:8]}) without altering its observable or comparator: the render runs "
            "BEFORE the window opens (playback::frames, then playback_window — checked in shell/main.rs) and "
            "latency_measure times StretchDIBits -> DwmFlush over pre-rendered bitmaps with no render call (checked in "
            "shell/win32.rs), so LATENCY-1 cannot see the T=8 renderer; its delta reads against a declared 50-permille "
            "materiality bound as a statement about the presentation interval only, never render headroom or "
            "contention; the LATENCY-0 record it overwrites is restored byte-exact; the render-inclusive question is "
            "LATENCY-1R's, never compared with it; hash-locked %s" % e["chain_hash"][:8])


def latency1r_preregistered():
    """LATENCY-1R's method is locked before any host number: the render-inclusive observable, the two arms, the two
    declared phase regimes and the fixed seed, witnesses first, ABBA interleaving, the p50 propagation rule and its
    four readings, and its scope. The code's constants must equal the registered ones."""
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    e = reg.get("LATENCY-1R")
    if not e:
        raise Red("LATENCY-1R is not registered")
    hyp, succ, fail = e["hypothesis"].lower(), e["success_condition"].lower(), e["failure_condition"].lower()
    lims = " ".join(e["interpretation_limits"]).lower()
    checks = {
        "the render-inclusive observable": "render-start -> composited" in hyp and "render-inclusive" in hyp,
        "the two arms (T=8 production, single-thread fast::emit)": "prod_threads = 8" in hyp and "fast::emit" in hyp,
        "the two declared phase regimes and the fixed seed": "locked" in hyp and "uniform" in hyp and "0x5eed1a7e00000001" in hyp,
        "witnesses first, byte-identical arms": "witnesses first" in succ and "byte-identical" in succ,
        "ABBA interleaving from a composition": "abba" in succ and "starting from a composition" in succ,
        "the p50 propagation rule and its four readings": "500 permille propagates" in succ and "partially absorbed" in succ and "void" in succ,
        "tail percentiles never folded in": "tail percentiles do not subtract" in lims and "one scalar" in fail,
        "never compared to LATENCY-0/1 or an emit p99": "different observables" in fail,
        "reproducibility (--confirm)": "--confirm" in fail,
        "the LATENCY-0 instrument untouched": "byte-exact prefix" in fail,
        "scope: not input-to-photon, Windows-only, PRESENT-1 owns the coupling": "not input-to-photon" in lims and "windows-only" in lims and "present-1" in lims,
    }
    missing = [k for k, ok in checks.items() if not ok]
    if missing:
        raise Red("the LATENCY-1R method is not fully locked: " + "; ".join(missing))
    if not entry_hash_ok("LATENCY-1R", e):
        raise Red("the LATENCY-1R entry was edited after registration (chain hash)")
    rs = read(os.path.join(SHELL, "latency1r.rs")).decode("utf-8")
    m = re.search(r"pub const PHASE_SEED: u64 = (0x[0-9A-Fa-f_]+);", rs)
    import latency1r as L1R
    if not m or int(m.group(1).replace("_", ""), 16) != 0x5EED1A7E00000001 or L1R.PHASE_SEED != "0x5EED1A7E00000001":
        raise Red("the court's phase seed is not the registered one")
    if L1R.PROPAGATES_PERMILLE != 500 or L1R.PROD_THREADS != 8:
        raise Red("the sealer's decision constants are not the registered ones")
    return ("LATENCY-1R's method is locked before any host number: render-start -> composited (render-inclusive) for the "
            "production render (T=8) and the single-thread reference (fast::emit) on the same sealed session and GDI "
            "present, in two declared phase regimes (locked / uniform, seed 0x5EED1A7E00000001), witnesses first with "
            "byte-identical arms, ABBA-interleaved from a composition; per regime the p50 propagation 1000*dG/dR reads "
            "PROPAGATES (>=500) / PARTIALLY ABSORBED / ABSORBED / VOID, p99s beside and never folded in; never compared "
            "to LATENCY-0/1 or an emit p99; not input-to-photon; the code's seed and thresholds equal the registered "
            "ones; hash-locked %s" % e["chain_hash"][:8])


def latency1_sealers():
    """Both host sealers are pure functions the gate can drive with synthetic numbers: court A's three branches are
    read through the amendment (never about the renderer), refuse a different session or a partial run, and the
    LATENCY-0 record the instrument overwrites is restored byte-exact; court B's four readings fire at the registered
    thresholds and a malformed raw record is refused. Every sealed record passes the firewall."""
    import latency1 as L1
    import latency1r as L1R
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    base_data = {"present_us": {"p50": 5921, "p95": 7078, "p99": 7318, "max": 7396}, "refresh_period_us": 13298,
                 "samples": 200, "sequence_frames": 4, "software_144_budget_us": 6944, "hardware_144_target_hz": 144}
    base = envelope.seal("verdandi-latency", 1, "measured",
                         {"preregistered": {"rung": "LATENCY-0", "chain_hash": reg["LATENCY-0"]["chain_hash"]}},
                         {"certifies": "a synthetic LATENCY-0-shaped baseline (gate)"}, ["synthetic"], base_data, "synthetic")
    L1.inherit_baseline(base, reg)

    def raw(p99, frames=4, samples=200):
        return {"name": "verdandi-latency", "provenance": {"unix_seconds": 0},
                "data": {"present_us": {"p50": 5900, "p95": 7000, "p99": p99, "max": p99 + 50}, "refresh_period_us": 13298,
                         "samples": samples, "sequence_frames": frames}}

    session, build = {"path": "synthetic", "chain_hash": "0" * 64}, {"rustc": "gate", "flags": ["-O"]}
    labels = {}
    for p99 in (7418, 6500, 8000):
        rec, label = L1.seal_latency1(raw(p99), base, "synthetic", reg, "gate", session, build)
        envelope.validate(rec)
        if "says NOTHING about the renderer" not in rec["reading"]:
            raise Red(f"court A's {label} reading is not bound by the amendment")
        pv = rec["provenance"]
        if (pv["preregistered"]["chain_hash"], pv["amended_by"]["chain_hash"], pv["inherited_baseline"]["chain_hash"]) != \
                (reg["LATENCY-1"]["chain_hash"], reg["LATENCY-1a"]["chain_hash"], base["chain_hash"]):
            raise Red("court A's record does not cite LATENCY-1, LATENCY-1a and the inherited baseline")
        labels[p99] = label
    if labels != {7418: "NO MATERIAL CHANGE", 6500: "IMPROVEMENT", 8000: "DEGRADATION"}:
        raise Red(f"court A's categories do not fire at the 50-permille bound: {labels}")
    for bad, why in ((raw(7318, frames=5), "a different session"), (raw(7318, samples=150), "a partial run")):
        try:
            L1.seal_latency1(bad, base, "synthetic", reg, "gate", session, build)
            raise Red(f"court A sealed {why}")
        except L1.Refuse:
            pass
    wrong = json.loads(json.dumps(base))
    wrong["provenance"]["preregistered"]["chain_hash"] = "0" * 64
    wrong["chain_hash"] = envelope.chain_hash(wrong)
    try:
        L1.inherit_baseline(wrong, reg)
        raise Red("court A inherited a baseline that does not cite LATENCY-0")
    except L1.Refuse:
        pass
    os.makedirs(BUILD, exist_ok=True)
    tmp = os.path.join(BUILD, "latency1-restore-plant.json")
    with open(tmp, "wb") as fh:
        fh.write(b"SEALED-LATENCY-0")

    def overwrite():
        with open(tmp, "wb") as fh:
            fh.write(b"RAW")

    def overwrite_then_fail():
        overwrite()
        raise L1.Refuse("instrument failed")

    got = L1.run_preserving(tmp, overwrite)
    if got != b"RAW" or read(tmp) != b"SEALED-LATENCY-0":
        raise Red("court A did not capture the instrument's bytes and restore the baseline byte-exact")
    try:
        L1.run_preserving(tmp, overwrite_then_fail)
    except L1.Refuse:
        pass
    restored = read(tmp) == b"SEALED-LATENCY-0"
    os.remove(tmp)
    if not restored:
        raise Red("a failing instrument left the baseline overwritten")

    def cell(render, total):
        return {"render_us": {"p50": render, "p95": render, "p99": render, "max": render},
                "present_us": {"p50": total - render, "p95": total - render, "p99": total - render, "max": total - render},
                "total_us": {"p50": total, "p95": total, "p99": total, "max": total}, "samples": 3}

    def raw_r(locked, uniform, seed="0x5EED1A7E00000001", threads=8):
        return {"name": "verdandi-latency1r", "provenance": {"tool": "synthetic", "unix_seconds": 0},
                "data": {"cells": {"locked": {"production": cell(*locked[0]), "single_thread": cell(*locked[1])},
                                   "uniform": {"production": cell(*uniform[0]), "single_thread": cell(*uniform[1])}},
                         "refresh_period_us": 13298, "sequence_frames": 4, "samples_per_cell": 3,
                         "production_threads": threads, "phase_seed": seed}}

    cases = {  # (production (render, total), single-thread (render, total)) -> the registered reading
        "ABSORBED": ((3000, 13300), (8000, 13300)),
        "PROPAGATES": ((3000, 9700), (8000, 14000)),
        "PARTIALLY ABSORBED": ((3000, 12000), (8000, 13000)),
        "VOID": ((5000, 13000), (5000, 13000)),
    }
    for want, arms in cases.items():
        rec, got = L1R.seal_latency1r(raw_r(arms, arms), reg, "gate", session, build)
        envelope.validate(rec)
        if got != {"locked": want, "uniform": want}:
            raise Red(f"court B read {got}, the registered rule says {want}")
        if rec["provenance"]["preregistered"]["chain_hash"] != reg["LATENCY-1R"]["chain_hash"]:
            raise Red("court B's record does not cite LATENCY-1R")
    for bad in (raw_r(cases["VOID"], cases["VOID"], seed="0x1"), raw_r(cases["VOID"], cases["VOID"], threads=4)):
        try:
            L1R.seal_latency1r(bad, reg, "gate", session, build)
            raise Red("court B sealed a record with another seed or another production T")
        except L1R.Refuse:
            pass
    return ("court A (verify/latency1.py): NO MATERIAL CHANGE / IMPROVEMENT / DEGRADATION fire at the 50-permille bound, "
            "every reading is bound by LATENCY-1a (nothing about the renderer), the record cites LATENCY-1 + LATENCY-1a + "
            "the inherited baseline, a different session / partial run / baseline not citing LATENCY-0 are refused, and "
            "the LATENCY-0 record the instrument overwrites is restored byte-exact even when the instrument fails; "
            "court B (verify/latency1r.py): PROPAGATES / PARTIALLY ABSORBED / ABSORBED / VOID fire at the registered "
            "thresholds on p50s, the record cites LATENCY-1R, and another seed or production T is refused — all sealed "
            "records pass the firewall")


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
            raise Red("the LOCKED blocked emit DIFFERS from the frozen emit on %s %s@%s" % (lvl, tiles, cam))
        if d.get("fast_pixels") != d.get("pixels") or d.get("fast_frame") != d.get("frame"):
            raise Red("blocked emit pixels/frame != frozen on %s %s@%s" % (lvl, tiles, cam))
        if d.get("linear_equal") != "OK" or d.get("linear_pixels") != d.get("pixels"):
            raise Red("the archived linear-fetch DDA reference (emit_linear) is not byte-identical to frozen on %s %s@%s" % (lvl, tiles, cam))
    return ("the sibling fast.rs emit (now the LOCALITY-0 LOCKED blocked-layout row-major floor DDA) is byte-identical to the "
            "frozen mantle.rs emit over %d cases (every corpus scene x its tile sets, plus adversarial witness cameras: the four "
            "spawn facings and the frozen-traversable sessionwalk positions) — fast_pixels == pixels AND fast_frame == frame "
            "everywhere; the archived linear-fetch DDA reference (emit_linear) stays byte-identical too (linear_pixels == pixels). "
            "The standing differential court (candidate -> frozen, never the reverse; proven on the 1a exact-transcription seed) "
            "judges each tread, and a single differing pixel refuses it regardless of speed" % len(cases))


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
    """GAUNTLET-1b: the floor divide-collapse, now RETAINED as fast::emit_collapse (the same-apparatus baseline the
    GAUNTLET-1c DDA is measured against). The collapse is byte-identical to the frozen emit (collapse_equal) AND its
    floor does exactly HALF the floor divides — 2 per textured floor pixel (one div_euclid per coordinate) where the
    frozen did 4 (two texel, each rem_euclid + div_euclid) — with the wall and ceiling untouched. This gates the
    DETERMINISTIC divide reduction (a source-cost proxy, not a wall-clock); the collapse's own speed win was measured
    in GAUNTLET-1b's host court (verify/gauntlet1b.py, sealed off-gate citing GAUNTLET-1)."""
    need_rustc()
    d = _fast_lines("witness", "identity", "34,28,W")
    if d.get("collapse_equal") != "OK" or d.get("collapse_pixels") != d.get("pixels"):
        raise Red("the retained GAUNTLET-1b collapse baseline is not byte-identical to the frozen emit on the witness frame")
    reg = dict(kv.split("=") for kv in d["fast_region"].split())
    base = dict(kv.split("=") for kv in d["fast_divwork"].split() if "=" in kv)
    opt = dict(kv.split("=") for kv in d["fast_optwork"].split() if "=" in kv)
    wall_tex, floor_tex = int(reg["wall_tex"]), int(reg["floor_tex"])
    base_floor = int(base["floor"])
    opt_wall, opt_floor, saved = int(opt["wall"]), int(opt["floor"]), int(opt["floor_saved"])
    if base_floor != 4 * floor_tex:
        raise Red("the frozen floor divide-work is not 4/px: %s" % d["fast_divwork"])
    if opt_wall != wall_tex:
        raise Red("the collapse changed the wall divide-work (it must touch only the floor): %s" % d["fast_optwork"])
    if opt_floor != 2 * floor_tex:
        raise Red("the collapse floor divide-work is not 2/px (the 4->2 collapse): %s" % d["fast_optwork"])
    if saved != base_floor - opt_floor or saved != 2 * floor_tex:
        raise Red("floor_saved is not exactly the removed half of the floor divides: %s" % d["fast_optwork"])
    if opt.get("dominant") != ("floor" if opt_floor >= opt_wall else "wall"):
        raise Red("the collapse's reported dominant region disagrees with its divide-work")
    return ("GAUNTLET-1b's floor divide-collapse, retained as the DDA's baseline, is byte-identical to the frozen emit "
            "(collapse_equal OK, collapse_pixels == pixels on 34,28,W) AND does exactly HALF the floor divides: %d "
            "floor-textured px at 2/px = %d (collapse) vs 4/px = %d (frozen), the wall unchanged at %d — %d divides "
            "removed. The reduction is deterministic (a source-cost proxy); the collapse's speed win was GAUNTLET-1b's "
            "host court (gauntlet1b.py, off-gate, citing GAUNTLET-1)" % (floor_tex, opt_floor, base_floor, opt_wall, saved))


def gauntlet1c_dda():
    """GAUNTLET-1c: the row-major floor DDA (fast::emit). It is byte-identical to the frozen emit (the same
    gauntlet1-equiv court judges it), the GAUNTLET-1b collapse is retained byte-identical as the same-apparatus
    baseline, and the DDA moves the floor's perspective divide from per-PIXEL to per-ROW: a bounded ~5 div/rem ops
    per floor row (the two step constants, the constant-axis texel, the row's starting q/rem), not 2 per floor pixel.
    A DETERMINISTIC structural reduction (a source-cost proxy, not a wall-clock); the DDA-vs-collapse speed is the
    separate host court (verify/gauntlet1c.py, sealed off-gate citing GAUNTLET-1)."""
    need_rustc()
    d = _fast_lines("witness", "identity", "34,28,W")
    if d.get("fast_equal") != "OK" or d.get("fast_pixels") != d.get("pixels"):
        raise Red("the GAUNTLET-1c DDA (LOCKED blocked emit) is not byte-identical to the frozen emit on the witness frame")
    if d.get("linear_equal") != "OK" or d.get("linear_pixels") != d.get("pixels"):
        raise Red("the archived linear-fetch DDA reference (emit_linear) is not byte-identical to the frozen emit")
    if d.get("collapse_equal") != "OK" or d.get("collapse_pixels") != d.get("pixels"):
        raise Red("the retained GAUNTLET-1b collapse baseline is not byte-identical to the frozen emit")
    w = dict(kv.split("=") for kv in d["fast_ddawork"].split() if "=" in kv)
    floor_px, rows = int(w["floor_px"]), int(w["floor_rows"])
    dda_div, collapse_div = int(w["dda_div"]), int(w["collapse_div"])
    if collapse_div != 2 * floor_px:
        raise Red("the collapse divide-work is not 2/floor px: %s" % d["fast_ddawork"])
    if dda_div != 5 * rows:
        raise Red("the DDA divide-work is not 5/floor row: %s" % d["fast_ddawork"])
    if rows > 540:  # H - CY: no more floor rows than the image has below the horizon
        raise Red("more floor rows than the image can hold below the horizon: %s" % d["fast_ddawork"])
    if dda_div >= collapse_div:
        raise Red("the DDA did not reduce the floor divide-work below the collapse: %s" % d["fast_ddawork"])
    ratio = collapse_div // max(dda_div, 1)
    return ("GAUNTLET-1c's row-major floor DDA is byte-identical to the frozen emit (fast_equal OK, fast_pixels == "
            "pixels on 34,28,W) in BOTH its LOCKED blocked-fetch production form (emit) and its archived linear-fetch "
            "reference (emit_linear, linear_equal OK) — the two share the recurrence, only the floor layout differs — "
            "AND the retained GAUNTLET-1b collapse baseline stays byte-identical (collapse_equal OK); the floor's "
            "perspective divide is per-ROW: %d floor px over %d rows -> %d DDA div/rem ops (5/row) vs the collapse's %d "
            "(2/floor px), a ~%dx reduction on this frame. Deterministic (a source-cost proxy); the DDA-vs-collapse "
            "speed is the separate host court (gauntlet1c.py, off-gate, citing GAUNTLET-1)"
            % (floor_px, rows, dda_div, collapse_div, ratio))


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


# ------------------------------------------------------------------ rebreakdown1 (RE-BREAKDOWN-1: probe emit's cost structure)
def _emit_struct_lines(level, tiles, camera):
    code, out, err = run(KERNEL_EXE, ["--level", os.path.join(ORACLE, "levels", level + ".lvl"),
                                      "--tiles", os.path.join(ORACLE, "tiles", tiles + ".tiles"),
                                      "--camera", camera, "--emit-structure"])
    if code != 0:
        raise Red("kernel --emit-structure exited %d on %s@%s: %s" % (code, level, camera, err.strip()))
    return dict(ln.split(" ", 1) for ln in out.strip().splitlines() if " " in ln)


def rebreakdown1_preregistered():
    """RE-BREAKDOWN-1's method is locked before the number: it measures (no optimization); two separate courts; the
    probes are apparatus not renderers with probe VERIFY == emit as the subset proof; the ablation deltas are
    incremental attribution (non-additive, no architectural counters), never vs GAUNTLET-0's absolute; the promotion
    table is fixed. Weakening any of it is a visible diff, not a silent re-hash."""
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))
    e = reg["entries"].get("RE-BREAKDOWN-1")
    if not e:
        raise Red("RE-BREAKDOWN-1 is not registered")
    hyp, succ, fail = e["hypothesis"].lower(), e["success_condition"].lower(), e["failure_condition"].lower()
    lims = " ".join(e["interpretation_limits"]).lower()
    checks = {
        "measures, does not optimize": "measure, not optimize" in hyp and "does not optimize" in lims,
        "two separate courts": "two separate courts" in lims,
        "probes are apparatus, not renderers": "measurement apparatus, not candidate renderers" in hyp and "not renderers" in lims,
        "probe VERIFY == emit is the subset proof": "verify == emit" in hyp and "emitbd_verify ok" in succ,
        "incremental attribution, non-additive": "incremental wall-clock attribution under controlled ablation" in lims and "non-additive" in lims,
        "no architectural counters": "no architectural counters" in lims,
        "never vs GAUNTLET-0's absolute": "never compared to gauntlet-0" in lims,
        "the fence (production emit calls no probe)": "calls a probe" in fail,
        "the promotion table with DEFER": "defer" in lims and "lock a data-layout/locality court" in lims,
    }
    missing = [k for k, ok in checks.items() if not ok]
    if missing:
        raise Red("the RE-BREAKDOWN-1 method is not fully locked: " + "; ".join(missing))
    want = envelope.chain_hash({"name": "verdandi-preregistration-entry", "version": 1, "claim_class": "declared",
                                "provenance": {"registered_in": "verify/preregister.json"},
                                "validity_scope": {"certifies": "the conditions RE-BREAKDOWN-1 was seated under"},
                                "forbidden_interpretations": ["that registering a condition earns it"],
                                "data": {k: v for k, v in e.items() if k != "chain_hash"}})
    if e["chain_hash"] != want:
        raise Red("the RE-BREAKDOWN-1 entry was edited after registration (chain hash)")
    return ("RE-BREAKDOWN-1's method is locked before the number: it MEASURES (no optimization committed); two separate "
            "courts (deterministic structure + host ablation); the probes are apparatus not renderers with probe "
            "VERIFY == emit as the subset proof; the ablation deltas are incremental wall-clock attribution under "
            "controlled ablation (non-additive, no architectural counters), never vs GAUNTLET-0's absolute; the "
            "promotion table (LOCK locality / arithmetic / write, else DEFER) is fixed; hash-locked %s" % e["chain_hash"][:8])


def rebreakdown1_structure():
    """Court A, deterministic and gate-enforced: the probe VERIFY path is byte-identical to emit (the apparatus is a
    proven subset of the certified path), emit writes every framebuffer pixel exactly once, the textured memory reads
    are 3 per pixel, and the divide-work is wall(1/px) + 5/floor-row. The tile working set and the floor texel-stride
    locality are reported as data (the memory axis), never as a wall-clock."""
    need_rustc()
    d = _emit_struct_lines("witness", "identity", "34,28,W")
    if d.get("selfcheck") != "OK":
        raise Red("kernel did not selfcheck under --emit-structure")
    if d.get("emitbd_verify") != "OK":
        raise Red("the probe VERIFY path is NOT byte-identical to emit — the apparatus is not a subset of the certified path")
    st = dict(kv.split("=") for kv in d["emitbd_struct"].split() if "=" in kv)
    wr = dict(kv.split("=") for kv in d["emitbd_writes"].split() if "=" in kv)
    lo = dict(kv.split("=") for kv in d["emitbd_locality"].split() if "=" in kv)
    wall_tex, floor_tex = int(st["wall_tex"]), int(st["floor_tex"])
    tex = wall_tex + floor_tex
    if int(st["tile_reads"]) != 3 * tex or int(st["map_reads"]) != 3 * tex:
        raise Red("the memory reads are not 3 per textured pixel: %s" % d["emitbd_struct"])
    if wr.get("writes_once") != "OK" or int(wr["writes"]) != 1920 * 1080:
        raise Red("emit does not write every framebuffer pixel exactly once (double-write or temp buffer?): %s" % d["emitbd_writes"])
    if (int(st["divides"]) - wall_tex) % 5 != 0 or int(st["divides"]) < wall_tex:
        raise Red("the divide-work is not wall(1/px) + 5/floor-row: %s" % d["emitbd_struct"])
    local = int(lo["local_permille"])
    if not (0 <= local <= 1000) or int(lo["floor_local"]) > int(lo["floor_adj"]):
        raise Red("the locality statistic is malformed: %s" % d["emitbd_locality"])
    return ("RE-BREAKDOWN-1 Court A (deterministic, wall-clock-free) on the witness (34,28,W): the probe VERIFY path is "
            "byte-identical to emit (emitbd_verify OK), so the ablation probes are a proven subset of the certified path; "
            "emit writes all %d framebuffer pixels exactly once (no double-write, no temp buffer); the textured work is "
            "%d px x 3 = %d tile reads and %d map reads; the tile working set is %s floor / %s wall distinct texels (of "
            "65536), and %d permille of adjacent-column floor texels fall within a 64-byte cache line — the memory / "
            "locality axis, reported as data, not a wall-clock" % (int(wr["writes"]), tex, int(st["tile_reads"]),
            int(st["map_reads"]), st["ws_floor"], st["ws_wall"], local))


def rebreakdown1_fence():
    """The fence: the production emit() (LOCKED blocked), the archived emit_linear() reference and the GAUNTLET-1b
    emit_collapse() baseline reference no probe, so the measurement apparatus (fast.rs::probe) is structurally
    isolated from fast.rs's promotion chain. The probes are scaffold, never renderers; a differing probe pixel is
    expected, not a fault."""
    src = open(os.path.join(ROOT, "kernel", "fast.rs"), encoding="utf-8").read()

    def between(a, b):
        i = src.index(a)
        j = src.index(b, i + len(a))
        return src[i:j]

    def code_only(body):  # strip // and /// lines so a doc comment may NAME the probe court without breaching the fence
        return "\n".join(ln for ln in body.splitlines() if not ln.lstrip().startswith("//"))

    emit_body = code_only(between("pub fn emit(", "pub fn emit_linear("))
    linear_body = code_only(between("pub fn emit_linear(", "pub fn emit_collapse("))
    collapse_body = code_only(between("pub fn emit_collapse(", "pub fn region_divides("))
    for name, body in (("emit()", emit_body), ("emit_linear()", linear_body), ("emit_collapse()", collapse_body)):
        if "probe" in body:
            raise Red("%s references a probe — the measurement apparatus is not fenced from the renderer" % name)
    if "pub mod probe" not in src or "emit_probe" not in src:
        raise Red("the fenced probe apparatus (pub mod probe / emit_probe) is missing")
    if "black_box" not in src:
        raise Red("the probes are not anchored against dead-code elision (no black_box) — the timing would be meaningless")
    return ("RE-BREAKDOWN-1 fence: the production emit() (LOCKED blocked), the archived emit_linear() reference and the "
            "GAUNTLET-1b emit_collapse() baseline reference no probe — the ablation apparatus (fast.rs::probe, "
            "black_box-anchored so the optimizer cannot elide the timed work) is isolated from fast.rs's promotion "
            "chain; the probes are measurement scaffold, never renderers, and a differing probe pixel is expected, not a fault")


# ------------------------------------------------------------------ locality0 (LOCALITY-0: the floor-tile execution-format court)
def _loc_lines(level, tiles, camera):
    code, out, err = run(KERNEL_EXE, ["--level", os.path.join(ORACLE, "levels", level + ".lvl"),
                                      "--tiles", os.path.join(ORACLE, "tiles", tiles + ".tiles"),
                                      "--camera", camera, "--locality"])
    if code != 0:
        raise Red("kernel --locality exited %d on %s@%s: %s" % (code, level, camera, err.strip()))
    return dict(ln.split(" ", 1) for ln in out.strip().splitlines() if " " in ln)


def locality0_preregistered():
    """LOCALITY-0's method is locked before any layout wins: two courts (byte-identity mandatory + host speed vs the
    DDA baseline), the Epistemic-Invariance process-isolation boundary (instruction-invariance a goal, not gate-proven),
    content-provenance isolated from execution-format, the three exits, and the GAUNTLET-2 baseline. Hash-locked."""
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))
    e = reg["entries"].get("LOCALITY-0")
    if not e:
        raise Red("LOCALITY-0 is not registered")
    hyp, succ, fail = e["hypothesis"].lower(), e["success_condition"].lower(), e["failure_condition"].lower()
    lims = " ".join(e["interpretation_limits"]).lower()
    checks = {
        "byte-identity is mandatory and gate-enforced": "mandatory, gate-enforced" in succ,
        "speed is a separate host court vs the DDA baseline": "separate host court" in lims and "dda baseline" in succ,
        "the Epistemic-Invariance process-isolation boundary": "epistemic-invariance boundary" in lims and "process-isolated" in lims,
        "instruction invariance is not gate-provable": "not gate-provable" in lims,
        "never vs GAUNTLET-0's absolute": "never gauntlet-0" in lims,
        "content provenance isolated from execution format": "content provenance is isolated from execution format" in lims,
        "the three exits incl. capacity->GAUNTLET-2": "three exits" in lims and "capacity" in lims,
        "the GAUNTLET-2 hard baseline": "baseline for gauntlet-2" in lims,
    }
    missing = [k for k, ok in checks.items() if not ok]
    if missing:
        raise Red("the LOCALITY-0 method is not fully locked: " + "; ".join(missing))
    want = envelope.chain_hash({"name": "verdandi-preregistration-entry", "version": 1, "claim_class": "declared",
                                "provenance": {"registered_in": "verify/preregister.json"},
                                "validity_scope": {"certifies": "the conditions LOCALITY-0 was seated under"},
                                "forbidden_interpretations": ["that registering a condition earns it"],
                                "data": {k: v for k, v in e.items() if k != "chain_hash"}})
    if e["chain_hash"] != want:
        raise Red("the LOCALITY-0 entry was edited after registration (chain hash)")
    return ("LOCALITY-0's method is locked before any layout wins: byte-identity is MANDATORY and gate-enforced, speed "
            "is a SEPARATE process-isolated host court vs the DDA baseline (never GAUNTLET-0's absolute); the Epistemic-"
            "Invariance boundary monomorphizes + process-isolates + interleaves (instruction-invariance a goal, not "
            "gate-proven); content provenance is isolated from execution format; three exits (blocked / morton / neither "
            "-> capacity stall -> GAUNTLET-2), and the accepted single-thread emit is the GAUNTLET-2 baseline; hash-locked %s"
            % e["chain_hash"][:8])


def locality0_equiv():
    """The regression court: both floor-tile layouts byte-identical to the frozen emit over corpus + adversarial
    cameras, and — non-vacuously — on a synthetic distinct-per-texel floor where a mis-index would actually diverge."""
    need_rustc()
    cases = _g1_cases()
    for (lvl, tiles, cam) in cases:
        d = _loc_lines(lvl, tiles, cam)
        if d.get("selfcheck") != "OK":
            raise Red("kernel did not selfcheck under --locality on %s@%s" % (lvl, cam))
        eq = dict(kv.split("=") for kv in d["locality_equal"].split() if "=" in kv)
        se = dict(kv.split("=") for kv in d["locality_synthemit"].split() if "=" in kv)
        if eq.get("blocked") != "OK" or eq.get("morton") != "OK" or eq.get("linear_anchor") != "OK":
            raise Red("a swizzled floor emit differs from the frozen emit on %s %s@%s" % (lvl, tiles, cam))
        if se.get("blocked") != "OK" or se.get("morton") != "OK":
            raise Red("the swizzled fetch is wrong on distinct floor data on %s@%s (the non-vacuous guard)" % (lvl, cam))
    return ("both floor-tile layouts (8x8 blocked, Morton Z-order) are byte-identical to the frozen emit over %d cases "
            "(every corpus scene x its tile sets + adversarial cameras), emit_swizzled<LINEAR> reproduces the DDA emit "
            "exactly, AND the non-vacuous synthetic distinct-per-texel render agrees across all three layouts — a "
            "mis-index would diverge on real data. Regression security is gate-enforced before any speed claim" % len(cases))


def locality0_bijection():
    """Each swizzle is a lossless bijection — proven on a synthetic distinct-per-texel tile (round-trip holds AND the
    format genuinely moves), not merely on the flat corpus tile where any permutation round-trips trivially."""
    need_rustc()
    d = _loc_lines("witness", "identity", "34,28,W")
    bj = dict(kv.split("=") for kv in d["locality_bijection"].split() if "=" in kv)
    sy = dict(kv.split("=") for kv in d["locality_synth"].split() if "=" in kv)
    if bj.get("blocked") != "OK" or bj.get("morton") != "OK":
        raise Red("a swizzle is not a lossless round-trip on the corpus tile")
    if sy.get("blocked_roundtrip") != "OK" or sy.get("morton_roundtrip") != "OK":
        raise Red("a swizzle is not a bijection on distinct data (round-trip failed) — a collision bug")
    if sy.get("blocked_fmt_moved") != "true" or sy.get("morton_fmt_moved") != "true":
        raise Red("the swizzle is a byte-level no-op on distinct data (the format did not move)")
    return ("both swizzles are lossless bijections: unswizzle(swizzle(tile)) == tile, and on a synthetic distinct-per-"
            "texel tile the round-trip holds AND the swizzled bytes differ from canonical — the permutation is proven "
            "on data where a collision bug would show, not just on the flat corpus tile")


def locality0_provenance():
    """Content-provenance isolated from execution-format (the text-reformat law for the tile): the canonical-order
    content hash is unmoved by the swizzle, while the storage layout moves. Certified content vs performance layout."""
    need_rustc()
    d = _loc_lines("witness", "identity", "34,28,W")
    pr = dict(kv.split("=") for kv in d["locality_provenance"].split() if "=" in kv)
    sy = dict(kv.split("=") for kv in d["locality_synth"].split() if "=" in kv)
    if pr.get("blocked_content_same") != "true" or pr.get("morton_content_same") != "true":
        raise Red("the swizzle changed the tile CONTENT (unswizzled hash moved) — not a pure re-format")
    if sy.get("blocked_fmt_moved") != "true" or sy.get("morton_fmt_moved") != "true":
        raise Red("the swizzle did not move the storage format on distinct data")
    return ("content-provenance is isolated from execution-format (the text-reformat law applied to the tile): the "
            "canonical-order content hash is UNMOVED by both swizzles while the storage layout MOVES (on distinct data "
            "the swizzled bytes differ from canonical) — the certified content's identity is independent of the "
            "performance layout, exactly as text-reformat separates content from authoring format")


def locality0_indextax():
    """The deterministic per-band within-cache-line locality (the shear story): both layouts raise locality over the
    linear order in every band, most in the near-field where the linear layout scatters. Names each layout as a real
    locality lever whose wall-clock worth, net of its index-arithmetic tax X, is the host court."""
    need_rustc()
    d = _loc_lines("witness", "identity", "34,28,W")
    lin = dict(kv.split("=") for kv in d["locality_bands_linear"].split() if "=" in kv)
    blk = dict(kv.split("=") for kv in d["locality_bands_blocked"].split() if "=" in kv)
    mor = dict(kv.split("=") for kv in d["locality_bands_morton"].split() if "=" in kv)
    for nm, band in (("linear", lin), ("blocked", blk), ("morton", mor)):
        for b in ("near", "mid", "far"):
            if not (0 <= int(band[b]) <= 1000):
                raise Red("malformed per-band locality for %s" % nm)
    for b in ("near", "mid", "far"):
        if int(blk[b]) < int(lin[b]) or int(mor[b]) < int(lin[b]):
            raise Red("a layout did not raise within-cache-line locality over linear in the %s band" % b)
    return ("the deterministic per-band within-cache-line locality (the shear story) on the witness: linear near/mid/far "
            "%s/%s/%s permille -> blocked %s/%s/%s, morton %s/%s/%s; both layouts raise locality in every band (most in "
            "the near-field where the linear order scatters), so each is a real locality lever — its WALL-CLOCK worth, "
            "net of the index-arithmetic tax X, is LOCALITY-0's process-isolated host court, not this deterministic proxy"
            % (lin["near"], lin["mid"], lin["far"], blk["near"], blk["mid"], blk["far"], mor["near"], mor["mid"], mor["far"]))


def locality0_lock():
    """LOCALITY-0 LOCK: the blocked floor-tile layout is PROMOTED to the accepted single-thread emit — the production
    fast::emit is monomorphized to the blocked-fetch DDA, its floor swizzled once at scene load — while the linear-fetch
    DDA is retained VERBATIM as emit_linear, an immutable reference witness. Both are byte-identical to the frozen emit;
    the accepted (blocked) emit's process-isolated host p99 (sealed in the LOCALITY-0 record) is GAUNTLET-2's hard
    baseline. This is LOCALITY-0's Exit 1 (blocked wins) made the production path, gate-enforced for correctness."""
    need_rustc()
    d = _fast_lines("witness", "identity", "34,28,W")
    if d.get("fast_equal") != "OK" or d.get("fast_pixels") != d.get("pixels"):
        raise Red("the LOCKED blocked emit is not byte-identical to the frozen emit")
    if d.get("linear_equal") != "OK" or d.get("linear_pixels") != d.get("pixels"):
        raise Red("the archived linear-fetch DDA reference (emit_linear) is not byte-identical to the frozen emit")
    if d.get("fast_pixels") != d.get("linear_pixels"):
        raise Red("the blocked production emit and the archived linear reference disagree — the LOCK moved the picture")
    return ("LOCALITY-0 LOCK (Exit 1, blocked wins): the blocked floor-tile layout is the accepted single-thread emit — the "
            "production fast::emit is the blocked-fetch DDA (floor swizzled once at scene load) and is byte-identical to the "
            "frozen emit (fast_pixels == pixels), while the linear-fetch DDA is retained verbatim as emit_linear, an immutable "
            "reference witness, byte-identical too (linear_pixels == pixels == fast_pixels). The accepted blocked emit's "
            "process-isolated host p99 (sealed in the LOCALITY-0 record) is the hard baseline GAUNTLET-2 must beat; correctness "
            "is gate-enforced here, the speed win is LOCALITY-0's off-gate host court")


def locality0_lockfence():
    """The LOCK is structural, not merely behavioural: the production emit() fetches the floor from the blocked scene-load
    buffer via floor_blocked and NEVER reads scene.floor in the hot path, with no runtime or generic layout toggle
    (monomorphized to blocked); the archived emit_linear() is the pre-LOCK linear-fetch path (reads scene.floor, no
    blocked index); and the scene-load swizzle blocked_floor() exists. A source-level fence, mirroring rebreakdown1-fence."""
    src = open(os.path.join(ROOT, "kernel", "fast.rs"), encoding="utf-8").read()

    def between(a, b):
        i = src.index(a)
        j = src.index(b, i + len(a))
        return src[i:j]

    def code_only(body):
        return "\n".join(ln for ln in body.splitlines() if not ln.lstrip().startswith("//"))

    def reads_raw_floor(body):  # `scene.floor` the raw tile, NOT `scene.floor_map` the band map (a substring of it)
        return "scene.floor" in body.replace("scene.floor_map", "")

    emit_body = code_only(between("pub fn emit(", "pub fn emit_linear("))
    linear_body = code_only(between("pub fn emit_linear(", "pub fn emit_collapse("))
    if "pub fn emit(scene: &Scene, strips: &[Strip], buf: &[u8], out: &mut [u8], floor: &[u8])" not in src:
        raise Red("the production emit() does not take the pre-swizzled blocked floor buffer — the LOCK is not wired")
    if "pub fn blocked_floor(" not in src:
        raise Red("the scene-load swizzle blocked_floor() is missing — nothing builds the blocked execution format")
    if "floor_blocked(" not in emit_body:
        raise Red("the production emit() hot path does not use the blocked index floor_blocked — it is not the LOCKED layout")
    if reads_raw_floor(emit_body):
        raise Red("the production emit() reads scene.floor in the hot path — the raw canonical tile, not the swizzled buffer")
    if "const LAYOUT" in emit_body or "if LAYOUT" in emit_body:
        raise Red("the production emit() carries a generic/runtime layout toggle — it is not monomorphized to blocked")
    if not reads_raw_floor(linear_body):
        raise Red("the archived emit_linear() does not fetch scene.floor — it is not the linear-fetch reference")
    if "floor_blocked(" in linear_body:
        raise Red("the archived emit_linear() uses the blocked index — it is not the pre-LOCK linear path")
    return ("LOCALITY-0 LOCK fence (source): the production emit() takes the pre-swizzled blocked floor buffer, uses the "
            "blocked index floor_blocked in the hot path, never reads scene.floor there, and carries no generic or runtime "
            "layout toggle — it is monomorphized to the LOCKED blocked layout; the scene-load swizzle blocked_floor() builds "
            "that format once; and the archived emit_linear() is the verbatim pre-LOCK linear-fetch reference (reads "
            "scene.floor, no blocked index). The promotion is a clean binary boundary, not a runtime branch")


def gauntlet2_preregistered():
    """GAUNTLET-2's full method is SEALED before the parallel rung is built. It is not 'make emit multithreaded': it
    establishes PARTITION INVARIANCE — the certified picture is byte-invariant under every admitted column partition and
    order (adversarial, not merely contiguous), so thread count and partition are execution parameters, not rendering
    authority. Two courts (deterministic partition-invariance + host threaded p99 vs the inherited LOCALITY-0 baseline);
    the thread count T is explicit and recorded in the attestation; the decision rule — including the memory-hierarchy
    redirect on a scaling stall — is preregistered before the number. Hash-locked, so weakening it is a visible diff."""
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))
    e = reg["entries"].get("GAUNTLET-2")
    if not e:
        raise Red("GAUNTLET-2 is not registered")
    lims = " ".join(e["interpretation_limits"]).lower()
    checks = {
        "the single-thread baseline is inherited from LOCALITY-0, never re-derived": "inherited from locality-0" in lims and "never re-measured" in lims,
        "PARTITION invariance (not merely thread count); partition/order are execution parameters, not authority": "partition invariance" in lims and "execution parameters, not rendering authority" in lims and "adversarial partitions" in lims,
        "byte-identity holds for every thread count (thread-count invariance)": "thread-count invariance" in lims,
        "the thread count T is explicit and recorded in the attestation": "explicit thread count" in lims and "recorded in the attestation" in lims,
        "the decision rule is preregistered before the number, incl. the memory-hierarchy redirect": "decision rule" in lims and "before the number" in lims and "memory-bandwidth" in lims,
        "correctness and speed are two separate courts": "two separate courts" in lims,
        "never vs GAUNTLET-0's absolute": "never compared to gauntlet-0" in lims,
        "mantle.rs stays the frozen oracle": "mantle.rs stays the frozen correctness oracle" in lims,
        "embarrassingly parallel; hides, does not remove, the stall": "embarrassingly parallel" in lims and "does not remove the capacity/lru stall" in lims,
    }
    missing = [k for k, ok in checks.items() if not ok]
    if missing:
        raise Red("the GAUNTLET-2 method is not fully locked: " + "; ".join(missing))
    want = envelope.chain_hash({"name": "verdandi-preregistration-entry", "version": 1, "claim_class": "declared",
                                "provenance": {"registered_in": "verify/preregister.json"},
                                "validity_scope": {"certifies": "the conditions GAUNTLET-2 was seated under"},
                                "forbidden_interpretations": ["that registering a condition earns it"],
                                "data": {k: v for k, v in e.items() if k != "chain_hash"}})
    if e["chain_hash"] != want:
        raise Red("the GAUNTLET-2 entry was edited after registration (chain hash)")
    return ("GAUNTLET-2's full method is sealed before the parallel rung is built: it establishes PARTITION INVARIANCE — the "
            "certified picture is byte-invariant under every admitted column partition and order (adversarial partitions, not "
            "merely contiguous chunks; thread-count invariance is its contiguous special case), so thread count and partition "
            "are execution parameters, not rendering authority. Two separate courts (deterministic partition-invariance on the "
            "gate + host threaded p99); the thread count T is explicit and recorded in the attestation (the T | correctness | "
            "p99 matrix); the single-thread floor is the LOCKED blocked emit's p99 inherited from LOCALITY-0, never re-measured; "
            "the decision rule is preregistered before the number — promote iff byte-invariant AND some admitted T>1 beats the "
            "baseline, and a scaling stall reads as memory-bandwidth/cache contention (turn to the memory hierarchy), not as too "
            "few threads. Never vs GAUNTLET-0's absolute; mantle.rs stays frozen; hash-locked %s" % e["chain_hash"][:8])


# ------------------------------------------------------------------ gauntlet2 correctness court (partition invariance)
def _g2_lines(level, tiles, camera):
    code, out, err = run(KERNEL_EXE, ["--level", os.path.join(ORACLE, "levels", level + ".lvl"),
                                      "--tiles", os.path.join(ORACLE, "tiles", tiles + ".tiles"),
                                      "--camera", camera, "--gauntlet2"])
    if code != 0:
        raise Red("kernel --gauntlet2 exited %d on %s@%s: %s" % (code, level, camera, err.strip()))
    meta, specs = {}, {}
    for ln in out.strip().splitlines():
        if ln.startswith("g2_spec "):
            parts = ln.split()
            specs[parts[1]] = dict(p.split("=") for p in parts[2:] if "=" in p)
        elif " " in ln:
            k, v = ln.split(" ", 1)
            meta[k] = v
    return specs, meta


def gauntlet2_partition_invariance():
    """The GAUNTLET-2 correctness court, deterministic and gate-enforced: emit_partitioned renders every column
    partition — contiguous chunks at T in {1,2,4,8,16} AND adversarial partitions (strided, reversed group+column
    order, single-column, seeded permutation) — byte-identical to the frozen picture over corpus + adversarial
    cameras, each a true partition of 0..W, and the core at T=1 equals the LOCKED blocked emit. Partition and order
    are execution parameters, not rendering authority; a shared-state or reduction-order dependency reddens here,
    deterministically, without a thread. Threading is GAUNTLET-2's separate off-gate performance court."""
    need_rustc()
    required = {"contig1", "contig2", "contig4", "contig8", "contig16", "strided2", "strided8", "reversed8", "single", "permuted8"}
    cases = _g1_cases()
    for (lvl, tiles, cam) in cases:
        specs, meta = _g2_lines(lvl, tiles, cam)
        if meta.get("selfcheck") != "OK":
            raise Red("kernel did not selfcheck under --gauntlet2 on %s@%s" % (lvl, cam))
        if meta.get("g2_vs_emit") != "OK":
            raise Red("emit_partitioned over the whole frame differs from the LOCKED blocked emit on %s@%s" % (lvl, cam))
        if meta.get("g2_pixels") != meta.get("pixels"):
            raise Red("the GAUNTLET-2 witness pixels disagree with the frozen witness on %s@%s" % (lvl, cam))
        miss = required - set(specs.keys())
        if miss:
            raise Red("GAUNTLET-2 is missing partition specs %s on %s@%s" % (sorted(miss), lvl, cam))
        for name, kv in specs.items():
            if kv.get("cover") != "OK":
                raise Red("partition spec %s is not a true partition of 0..W (coverage) on %s@%s" % (name, lvl, cam))
            if kv.get("equal") != "OK":
                raise Red("partition spec %s is NOT byte-identical to the frozen picture on %s@%s — a partition/order dependency" % (name, lvl, cam))
    return ("GAUNTLET-2 partition invariance (deterministic) over %d cases (every corpus scene x its tile sets + adversarial "
            "cameras): emit_partitioned renders every column partition — contiguous chunks at T in {1,2,4,8,16} AND adversarial "
            "partitions (strided/interleaved, reversed group+column order, single-column, a seeded permutation) — byte-identical "
            "to the frozen picture, each a true partition of 0..W (coverage exactly once), and the partition core at T=1 equals "
            "the LOCKED blocked emit (g2_vs_emit OK). Partition and order are execution parameters, not rendering authority; a "
            "shared-state or reduction-order dependency would redden here, deterministically, without spawning a thread — "
            "threading is GAUNTLET-2's separate off-gate performance court" % len(cases))


def _g2threads_lines(level, tiles, camera):
    code, out, err = run(KERNEL_EXE, ["--level", os.path.join(ORACLE, "levels", level + ".lvl"),
                                      "--tiles", os.path.join(ORACLE, "tiles", tiles + ".tiles"),
                                      "--camera", camera, "--gauntlet2-threads"])
    if code != 0:
        raise Red("kernel --gauntlet2-threads exited %d on %s@%s: %s" % (code, level, camera, err.strip()))
    meta, th = {}, {}
    for ln in out.strip().splitlines():
        if ln.startswith("g2t_thread "):
            parts = ln.split()
            th[parts[1]] = dict(p.split("=") for p in parts[2:] if "=" in p)
        elif " " in ln:
            k, v = ln.split(" ", 1)
            meta[k] = v
    return th, meta


def gauntlet2_threaded_equiv():
    """The threaded emit is byte-identical to the frozen picture at every thread count. emit_threaded partitions the
    columns into T contiguous groups and renders them across std::thread::scope, one group per thread with disjoint
    framebuffer writes; the OUTPUT is deterministic though thread scheduling is not, so this is gate-enforceable.
    Byte-identity is checked FIRST, before any performance interpretation; the T | correctness | p99 speed matrix is
    GAUNTLET-2's separate off-gate court (verify/gauntlet2.py)."""
    need_rustc()
    want_t = {"1", "2", "4", "8", "16"}
    cases = _g1_cases()
    for (lvl, tiles, cam) in cases:
        th, meta = _g2threads_lines(lvl, tiles, cam)
        if meta.get("selfcheck") != "OK":
            raise Red("kernel did not selfcheck under --gauntlet2-threads on %s@%s" % (lvl, cam))
        miss = want_t - set(th.keys())
        if miss:
            raise Red("GAUNTLET-2 threaded is missing thread counts %s on %s@%s" % (sorted(miss), lvl, cam))
        for t, kv in th.items():
            if kv.get("equal") != "OK":
                raise Red("the threaded emit at T=%s is NOT byte-identical to the frozen picture on %s@%s — a partition/order or race dependency" % (t, lvl, cam))
    return ("GAUNTLET-2 threaded byte-identity (deterministic) over %d cases (corpus x tile sets + adversarial cameras): "
            "emit_threaded — std::thread::scope, one contiguous column group per thread, disjoint framebuffer writes — "
            "reproduces the frozen picture EXACTLY at every thread count T in {1,2,4,8,16}. The output is deterministic "
            "though scheduling is not (disjoint per-column writes, no shared/reduction state), so byte-identity is checked "
            "FIRST and gate-enforced; the T | correctness | p99 speed matrix vs the sealed 7734 us single-thread baseline "
            "is GAUNTLET-2's separate off-gate host court (verify/gauntlet2.py)" % len(cases))


def gauntlet2_threaded_fence():
    """The performance court adds ONLY execution. emit_partitioned stays the clean partition-agnostic core (LOCKED
    floor_blocked + the pre-swizzled floor, never scene.floor, no probe), and emit_threaded routes EVERY pixel through
    emit_partitioned — std::thread::scope with no coordinate, material or pixel algorithm of its own (no duplicate
    renderer). This REPLACES the retired gauntlet2-partition-fence, whose 'no threading yet' job is finished."""
    src = open(os.path.join(ROOT, "kernel", "fast.rs"), encoding="utf-8").read()

    def between(a, b):
        i = src.index(a)
        j = src.index(b, i + len(a))
        return src[i:j]

    def code_only(body):
        return "\n".join(ln for ln in body.splitlines() if not ln.lstrip().startswith("//"))

    def reads_raw_floor(body):
        return "scene.floor" in body.replace("scene.floor_map", "")

    if "pub fn emit_partitioned(" not in src or "pub fn emit_threaded(" not in src:
        raise Red("the partition-agnostic core or the threaded emit is missing")
    core = code_only(between("pub fn emit_partitioned(", "pub fn emit_threaded("))
    if "floor_blocked(" not in core:
        raise Red("emit_partitioned no longer uses the LOCKED blocked index floor_blocked")
    if reads_raw_floor(core):
        raise Red("emit_partitioned reads scene.floor — it must read the pre-swizzled floor buffer")
    if "probe" in core:
        raise Red("emit_partitioned references a probe — the core is not fenced from the apparatus")
    thr = code_only(between("pub fn emit_threaded(", "GAUNTLET-2 threading plumbing"))
    if "emit_partitioned(" not in thr:
        raise Red("emit_threaded does not route pixels through emit_partitioned")
    if "thread::scope" not in thr:
        raise Red("emit_threaded does not use std::thread::scope — the execution boundary is missing")
    for bad in ("floor_blocked(", "scene.floor_map", "scene.wall_map", "texel("):
        if bad in thr:
            raise Red("emit_threaded contains a duplicate-renderer primitive (%s) — it must only orchestrate emit_partitioned" % bad)
    return ("GAUNTLET-2 threaded fence: emit_partitioned stays the clean partition-agnostic core (LOCKED floor_blocked + the "
            "pre-swizzled floor, never scene.floor, no probe); emit_threaded is EXECUTION-only — it routes every pixel through "
            "emit_partitioned across std::thread::scope and holds no coordinate, material or pixel algorithm of its own (no "
            "duplicate renderer). Replaces the retired gauntlet2-partition-fence, whose 'no threading yet' job is finished")


def _render_lines(level, tiles, camera):
    code, out, err = run(KERNEL_EXE, ["--level", os.path.join(ORACLE, "levels", level + ".lvl"),
                                      "--tiles", os.path.join(ORACLE, "tiles", tiles + ".tiles"),
                                      "--camera", camera, "--render"])
    if code != 0:
        raise Red("kernel --render exited %d on %s@%s: %s" % (code, level, camera, err.strip()))
    return dict(ln.split(" ", 1) for ln in out.strip().splitlines() if " " in ln)


def gauntlet2_lock():
    """GAUNTLET-2 LOCK: the accepted production render (fast::render) goes through the threaded emit at the production
    default PROD_THREADS=8 and is byte-identical to the frozen picture — the frame digest AND pixel sha reproduce the
    witness — over corpus + adversarial cameras. T=8 is a production EXECUTION parameter (this row checks it), NOT the
    correctness oracle: the {1,2,4,8,16} court (gauntlet2-threaded-equiv) stays intact and separate."""
    need_rustc()
    cases = _g1_cases()
    for (lvl, tiles, cam) in cases:
        d = _render_lines(lvl, tiles, cam)
        if d.get("selfcheck") != "OK":
            raise Red("kernel did not selfcheck under --render on %s@%s" % (lvl, cam))
        if d.get("render_threads") != "8":
            raise Red("the production render default is not T=8 (render_threads=%s) on %s@%s" % (d.get("render_threads"), lvl, cam))
        if d.get("render_equal") != "OK" or d.get("render_pixels") != d.get("pixels") or d.get("render_frame") != d.get("frame"):
            raise Red("the LOCKED production render (fast::render at T=8) is NOT byte-identical to the frozen picture on %s@%s" % (lvl, cam))
    return ("GAUNTLET-2 LOCK over %d cases (corpus + adversarial cameras): the accepted production render fast::render — "
            "mantle's frozen strips + frame, then the pixels via emit_threaded at the production default PROD_THREADS=8 — is "
            "byte-identical to the frozen picture (render_pixels == pixels AND render_frame == frame everywhere). T=8 is a "
            "production execution parameter, gate-checked here; the {1,2,4,8,16} partition/thread court (gauntlet2-threaded-equiv) "
            "stays intact as the correctness oracle. The shell renders through this path, so the parallel headroom reaches the present")


def gauntlet2_lockfence():
    """The LOCK is structural: fast::render routes through emit_threaded at PROD_THREADS (fixed to 8), the shell's
    production render (shell/present.rs) is wired to fast::render and no longer calls the frozen picture() for its
    pixels, and the single-thread reference (emit / emit_linear) is retained. T=8 is an execution parameter, not
    rendering authority — the correctness court's thread set is untouched."""
    fast_src = open(os.path.join(ROOT, "kernel", "fast.rs"), encoding="utf-8").read()
    present_src = open(os.path.join(ROOT, "shell", "present.rs"), encoding="utf-8").read()

    def between(a, b):
        i = fast_src.index(a)
        j = fast_src.index(b, i + len(a))
        return fast_src[i:j]

    def code_only(body):
        return "\n".join(ln for ln in body.splitlines() if not ln.lstrip().startswith("//"))

    if "pub const PROD_THREADS: usize = 8" not in fast_src:
        raise Red("the production default is not PROD_THREADS = 8")
    if "pub fn render(" not in fast_src:
        raise Red("the production render entry fast::render is missing")
    render_body = code_only(between("pub fn render(", "/// RE-BREAKDOWN-1 — Court A"))
    if "emit_threaded(" not in render_body or "PROD_THREADS" not in render_body:
        raise Red("fast::render does not route the pixels through emit_threaded at PROD_THREADS")
    if "floor_blocked(" in render_body:
        raise Red("fast::render contains a duplicate-renderer primitive — it must only orchestrate emit_threaded")
    if "pub fn emit(" not in fast_src or "pub fn emit_linear(" not in fast_src:
        raise Red("the single-thread reference (emit / emit_linear) was dropped — it must be retained")
    pcode = code_only(present_src)
    if "fast::render(" not in pcode:
        raise Red("the shell production render (shell/present.rs) is NOT wired to fast::render — the production path is not the threaded emit")
    if "picture(" in pcode:
        raise Red("the shell production render still calls the frozen picture() for its pixels — the threaded emit is not the production path")
    return ("GAUNTLET-2 LOCK fence (source): fast::render routes the production pixels through emit_threaded at "
            "PROD_THREADS = 8 (no duplicate renderer), the shell's production render (shell/present.rs) is wired to "
            "fast::render and no longer calls the frozen picture() for its pixels, and the single-thread reference "
            "(emit / emit_linear) is retained. T=8 is an execution parameter fixed for production, not rendering "
            "authority — the {1,2,4,8,16} correctness court is untouched")


# ------------------------------------------------------------------ LATENCY-1R: the court, headless
def latency1r_court():
    """The SAME court the host window runs, driven headless through the deterministic mock surface over the sealed
    reference session: witnesses first (both arms reproduce every sealed frame witness and each other's composites),
    four cells of N samples, the locked regime composition-quantized and the uniform regime phase-offset as declared,
    and the raw record sealed by verify/latency1r.py (the mock has no render headroom, so both regimes read VOID).
    PLANTS: a tampered sealed witness refuses before any clock; a window closed mid-court refuses with no record."""
    need_rustc()
    if SHELL_EXE is None:
        raise Red("the shell was not built")
    import latency1r as L1R
    out = os.path.join(BUILD, "latency1r-mock.json")
    if os.path.exists(out):
        os.remove(out)
    base = ["latency1r-selftest", "--session", SESSIONWALK_DEMO, "--per-cell", "2"]
    cp = subprocess.run([SHELL_EXE] + base + ["--out", out], capture_output=True, text=True, cwd=ROOT)
    if cp.returncode != 0 or "latency1r court OK" not in cp.stdout or not os.path.exists(out):
        raise Red("the headless court did not run: " + (cp.stderr.strip() or cp.stdout.strip()))
    cells = {}
    for ln in cp.stdout.splitlines():
        if ln.startswith("latency1r cell "):
            parts = ln.split()
            cells[(parts[2], parts[3])] = dict(p.split("=") for p in parts[4:])
    head = cp.stdout.splitlines()[0].split()
    if head[:2] != ["latency1r", "refresh_us"] or head[4] != "4" or head[6] != "2" or len(cells) != 4:
        raise Red("the court did not render the 4 sealed moves in 4 cells of 2 samples")
    lp, ls = cells[("locked", "production")], cells[("locked", "single_thread")]
    if not (lp["total_p50"] == lp["total_p99"] == lp["total_max"] == ls["total_p50"] == ls["total_max"]):
        raise Red("the locked regime is not composition-quantized under the mock clock")
    up, us = cells[("uniform", "production")], cells[("uniform", "single_thread")]
    if not (int(up["total_p50"]) < int(lp["total_p50"]) and int(us["total_p50"]) < int(lp["total_p50"])):
        raise Red("the uniform regime did not offset the render start inside the refresh")
    with open(out, encoding="utf-8") as fh:
        raw = json.load(fh)
    os.remove(out)
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    rec, labels = L1R.seal_latency1r(raw, reg, "gate-mock", {"path": "workshop/attest/sessionwalk-demo.json"},
                                     {"rustc": "gate"})
    envelope.validate(rec)
    if labels != {"locked": "VOID", "uniform": "VOID"}:
        raise Red(f"the mock court (no render headroom) read {labels}, not VOID")
    for plant, code in (("witness", "LATENCY1R-WITNESS"), ("close", "LATENCY1R-CLOSED")):
        pout = os.path.join(BUILD, f"latency1r-plant-{plant}.json")
        if os.path.exists(pout):
            os.remove(pout)
        cp = subprocess.run([SHELL_EXE] + base + ["--plant", plant, "--out", pout], capture_output=True, text=True, cwd=ROOT)
        if cp.returncode == 0 or code not in cp.stderr or os.path.exists(pout):
            raise Red(f"PLANT {plant}: the court did not refuse with {code} and no record")
    return ("the LATENCY-1R court runs headless over the mock surface on the sealed reference session: both arms reproduce "
            "all 4 sealed frame witnesses and each other's composites before any clock, 4 cells x 2 samples ABBA, the "
            "locked regime composition-quantized and the uniform regime offset inside the refresh; its raw record seals "
            "under the envelope citing LATENCY-1R and reads VOID in both regimes (the mock has no render headroom); "
            "PLANTS: a tampered sealed witness refuses LATENCY1R-WITNESS and a window closed mid-court refuses "
            "LATENCY1R-CLOSED, each writing no record")


def latency1r_fence():
    """The structure LATENCY-1/1R rest on: LATENCY-0's instrument is a byte-exact PREFIX of shell/win32.rs (1R is
    appended after it), playback::frames and the playback-window dispatch are unchanged, the GDI surface's present
    mirrors LATENCY-0's present_once, the two arms differ only in the pixel pass, and inside the court the render sits
    between render-start and the present with the witnesses before the clock and the drift check after it."""
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if len(w32) < LATENCY0_WIN32_LEN or sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    if not tail.startswith("\n// ================================================================== LATENCY-1R (appended)"):
        raise Red("what follows LATENCY-0's instrument is not the appended LATENCY-1R section")
    pres = src_span(tail, "fn present(&mut self", "fn flush(&mut self)")
    order = [pres.find(t) for t in ("GetDC(", "StretchDIBits(", "let ready = qpc();", "(self.flush_fn)();", "Some(qpc())", "ReleaseDC(")]
    if -1 in order or order != sorted(order):
        raise Red("the GDI surface's present does not mirror LATENCY-0's present_once (GetDC, StretchDIBits, ready, DwmFlush, composited, ReleaseDC)")
    pb = read(os.path.join(SHELL, "playback.rs")).decode("utf-8")
    i = pb.index("pub fn frames(")
    if sha256(pb[i:pb.index("\n}\n", i) + 3].encode("utf-8")) != PLAYBACK_FRAMES_SHA256:
        raise Red("playback::frames (the pre-render LATENCY-0/1 play) changed")
    main_src = read(os.path.join(SHELL, "main.rs")).decode("utf-8")
    if PLAYBACK_WINDOW_DISPATCH not in main_src or "win32::latency1r_window(inputs, per_cell, &host, out);" not in main_src:
        raise Red("the playback-window dispatch changed, or latency1r-window does not reach the appended court")
    pr = read(os.path.join(SHELL, "present.rs")).decode("utf-8")
    arms = src_span(pr, "pub fn arm_composite(", "hud::overlay(scene")
    prod, single = src_span(arms, "Arm::Production =>", "Arm::SingleThread =>"), arms[arms.index("Arm::SingleThread =>"):]
    if "fast::render(scene)" not in prod or "fast::emit(" not in single or "emit_threaded" in single or "picture(" in arms:
        raise Red("the arms differ in more than the pixel pass (production = fast::render, single-thread = fast::emit)")
    if "fast::render(&scene)" not in src_span(pr, "pub fn compose_frame(", "pub fn to_blit("):
        raise Red("compose_frame no longer renders through fast::render")
    rs = read(os.path.join(SHELL, "latency1r.rs")).decode("utf-8")
    court = src_span(rs, "pub fn court(", "fn pct_json(")
    idx = [court.find(t) for t in ("frame_digest(&fp) != f.witness", "if cp != cs", "let refresh_us", "let t0 = s.ticks();",
                                   "arm_composite(&inputs[k].scene, arm)", "s.present(&bgr)", "if comp != expected[k]")]
    if -1 in idx or idx != sorted(idx):
        raise Red("the court's order is not witnesses -> refresh -> t0 -> render -> present -> drift check")
    timed = court[court.index("let t0 = s.ticks();"):court.index("s.present(&bgr)")]
    if "frame_digest" in timed or "sha256" in timed:
        raise Red("witness hashing sits inside the timed interval")
    return ("LATENCY-0's instrument is a byte-exact prefix of shell/win32.rs (%d bytes, sha %s…) with LATENCY-1R appended "
            "after it; playback::frames and the playback-window dispatch are unchanged; the GDI surface's present mirrors "
            "LATENCY-0's present_once; the arms differ only in the pixel pass (fast::render vs fast::emit) and "
            "compose_frame still renders through fast::render; the court orders witnesses -> refresh -> t0 -> render -> "
            "present -> drift check, with no hashing inside the timed interval" % (LATENCY0_WIN32_LEN, LATENCY0_WIN32_SHA256[:12]))


# ------------------------------------------------------------------ FRAME-SPLIT-0
def framesplit_preregistered():
    """FRAME-SPLIT-0's method is locked before any host number: the seven contiguous phases with frame-ready as the
    hard boundary, the uninstrumented envelope beside the instrumented split, witnesses first (the mirror byte-equal
    to the envelope path), no new variable against LATENCY-1R's apparatus, the VOID tax bound, GAUNTLET-0's p99-share
    seat rule on the production arm, and reconciliation reported, never distributed. Code constants must match."""
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    e = reg.get("FRAME-SPLIT-0")
    if not e:
        raise Red("FRAME-SPLIT-0 is not registered")
    hyp, succ, fail = e["hypothesis"].lower(), e["success_condition"].lower(), e["failure_condition"].lower()
    lims = " ".join(e["interpretation_limits"]).lower()
    checks = {
        "the seven phases, in order, frame-ready the hard boundary": all(p in hyp for p in ("strips", "frame", "floor_swizzle", "emit", "hud", "bgr", "blit")) and "hard boundary" in hyp,
        "no new variable against LATENCY-1R": "adds no variable" in hyp and "locked phase origin" in hyp,
        "witnesses first, the mirror byte-equal to the envelope path": "witnesses first" in succ and "byte for byte" in succ,
        "envelope and split interleaved ABBA, warm-up discarded": "envelope" in succ and "abba" in succ and "10 warm-up rounds" in succ,
        "the phases sum to the split total exactly": "sum to its total exactly" in succ,
        "the VOID tax bound": "100 permille" in succ and "void" in succ,
        "GAUNTLET-0's p99 share against the envelope, 500 permille": "1000 * p99(phase) / p99(envelope)" in succ and "500 permille" in succ,
        "the three readings, production arm only": "reads seat" in succ and "multi-component" in succ and "none promoted" in succ and "gets no seat" in succ,
        "reconciliation reported, never distributed": "never distributed" in succ and "distributed among the phases" in fail,
        "never compared to an emit p99 or LATENCY-0/1": "emit p99" in fail and "latency-0/latency-1" in fail,
        "reproducibility and an untouched LATENCY-0 instrument": "--confirm" in fail and "byte-exact prefix" in fail,
        "scope: tax includes mirror cost, allocations attributed, not input-to-photon": "marked mirror" in lims and "allocation" in lims and "not input-to-photon" in lims,
    }
    missing = [k for k, ok in checks.items() if not ok]
    if missing:
        raise Red("the FRAME-SPLIT-0 method is not fully locked: " + "; ".join(missing))
    if not entry_hash_ok("FRAME-SPLIT-0", e):
        raise Red("the FRAME-SPLIT-0 entry was edited after registration (chain hash)")
    import framesplit as FS
    rs = read(os.path.join(SHELL, "framesplit.rs")).decode("utf-8")
    m = re.search(r'pub const PHASES: \[&str; 7\] = \[([^\]]*)\];', rs)
    rs_phases = tuple(x.strip().strip('"') for x in m.group(1).split(",")) if m else ()
    if rs_phases != FS.PHASES or FS.PHASES != ("strips", "frame", "floor_swizzle", "emit", "hud", "bgr", "blit"):
        raise Red("the court's or the sealer's phases are not the registered seven, in order")
    if "pub const WARM_ROUNDS: usize = 10;" not in rs or FS.WARM_ROUNDS != 10:
        raise Red("the warm-up is not the registered 10 rounds")
    if (FS.SEAT_PERMILLE, FS.VOID_TAX_PERMILLE, FS.PROD_THREADS) != (500, 100, 8):
        raise Red("the sealer's decision constants are not the registered ones")
    return ("FRAME-SPLIT-0's method is locked before any host number: render-start -> frame-ready split into seven "
            "contiguous phases (strips, frame, floor_swizzle, emit, hud, bgr, blit; frame-ready the hard boundary) on "
            "LATENCY-1R's apparatus with no new variable, the uninstrumented envelope interleaved ABBA with the split "
            "(10 warm-up rounds), witnesses first with the marked mirror byte-equal to the envelope path; |tax| >= 100 "
            "permille of the envelope reads VOID, else GAUNTLET-0's p99 share against the envelope: one phase >= 500 "
            "permille is the SEAT, none or several is NO SEAT, production arm only; reconciliation reported, never "
            "distributed; the code's phases, warm-up and thresholds equal the registered ones; hash-locked %s" % e["chain_hash"][:8])


def framesplit_sealer():
    """The host sealer is a pure function the gate drives with synthetic splits: SEAT, NO SEAT (multi-component),
    NO SEAT (several at the threshold) and VOID fire exactly at the registered bounds, the shares use the envelope p99
    as the denominator, reconciliation is recorded not distributed, and a malformed record is refused."""
    import framesplit as FS
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]

    def pct(v):
        return {"p50": v, "p95": v, "p99": v, "max": v}

    def arm(env, phases, total=None):
        total = sum(phases) if total is None else total
        return {"envelope": {"render_us": pct(env), "present_us": pct(9000), "samples": 3},
                "split": {"phases_us": {p: pct(v) for p, v in zip(FS.PHASES, phases)}, "render_us": pct(total),
                          "present_us": pct(9000), "samples": 3}}

    def raw(prod, single=None, **over):
        d = {"arms": {"production": prod, "single_thread": single or prod}, "phases": list(FS.PHASES),
             "refresh_period_us": 13500, "sequence_frames": 4, "samples_per_cell": 3, "warm_rounds": 10,
             "production_threads": 8, "phase_origin": "locked"}
        d.update(over)
        return {"name": "verdandi-framesplit", "provenance": {"tool": "synthetic", "unix_seconds": 0}, "data": d}

    session, build = {"path": "synthetic", "chain_hash": "0" * 64}, {"rustc": "gate", "flags": ["-O"]}
    cases = {
        "SEAT: blit": arm(15000, [300, 1500, 100, 2600, 400, 2100, 8000]),              # blit 8000/15000 = 533 permille
        "NO SEAT (multi-component)": arm(15000, [300, 3500, 100, 2600, 400, 3100, 5000]),  # largest 5000/15000 = 333
        "NO SEAT (several at the threshold)": arm(10000, [100, 100, 100, 100, 100, 5000, 5000]),  # two at exactly 500
        "VOID": arm(15000, [300, 3500, 100, 2600, 400, 3100, 5000], total=16600),        # tax 1600 = 106 permille
    }
    for want, prod in cases.items():
        rec, got = FS.seal_framesplit(raw(prod), reg, "gate", session, build)
        envelope.validate(rec)
        if got != want:
            raise Red(f"the sealer read {got!r}, the registered rule says {want!r}")
        if rec["provenance"]["preregistered"]["chain_hash"] != reg["FRAME-SPLIT-0"]["chain_hash"]:
            raise Red("the sealed record does not cite FRAME-SPLIT-0")
    dv = FS.derive(cases["NO SEAT (multi-component)"])
    if dv["shares_p99_permille_of_envelope"]["blit"] != 333 or dv["tax_p50_us"] != 0:
        raise Red("the shares are not computed against the envelope p99")
    skew = arm(15000, [300, 3500, 100, 2600, 400, 3100, 5000])
    skew["split"]["render_us"] = pct(15400)   # a split total the phase p50s do not reach
    dv = FS.derive(skew)
    if dv["median_additivity_gap_us"] != 400 or dv["tax_p50_us"] != 400:
        raise Red("the reconciliation gap and the tax are not recorded as measured")
    for bad in (raw(cases["VOID"], phases=list(FS.PHASES)[::-1]), raw(cases["VOID"], phase_origin="uniform"),
                raw(cases["VOID"], production_threads=4)):
        try:
            FS.seal_framesplit(bad, reg, "gate", session, build)
            raise Red("the sealer accepted phases out of order, another phase origin or another production T")
        except FS.Refuse:
            pass
    return ("verify/framesplit.py, driven with synthetic splits: SEAT (one phase >= 500 permille of the envelope p99), NO "
            "SEAT multi-component (none), NO SEAT several (two at exactly 500) and VOID (|tax| >= 100 permille) fire at the "
            "registered bounds; shares use the envelope p99; the tax and the median-additivity gap are recorded as "
            "measured, never distributed; records cite FRAME-SPLIT-0 and pass the firewall; phases out of order, "
            "another phase origin or another production T are refused")


def framesplit_court():
    """The SAME split court the host window runs, headless over the mock surface on the sealed session: witnesses first
    (the envelope path reproduces every sealed witness, the marked mirror reproduces it byte for byte, the arms
    agree), four cells after the warm-up, and every split's seven phases summing exactly to its total. PLANTS: a
    tampered sealed witness and a mid-court close both refuse with no record."""
    need_rustc()
    if SHELL_EXE is None:
        raise Red("the shell was not built")
    import framesplit as FS
    out = os.path.join(BUILD, "framesplit-mock.json")
    if os.path.exists(out):
        os.remove(out)
    base = ["framesplit-selftest", "--session", SESSIONWALK_DEMO, "--per-cell", "2"]
    cp = subprocess.run([SHELL_EXE] + base + ["--out", out], capture_output=True, text=True, cwd=ROOT)
    if cp.returncode != 0 or "framesplit court OK" not in cp.stdout or not os.path.exists(out):
        raise Red("the headless split court did not run: " + (cp.stderr.strip() or cp.stdout.strip()))
    with open(out, encoding="utf-8") as fh:
        raw = json.load(fh)
    os.remove(out)
    d = raw["data"]
    if d["sequence_frames"] != 4 or d["samples_per_cell"] != 2 or d["warm_rounds"] != 10:
        raise Red("the court did not run the 4 sealed moves, 2 samples per cell after 10 warm-up rounds")
    for arm in FS.ARMS:
        spl = d["arms"][arm]["split"]
        # under the mock clock each phase is exactly one tick, so the telescoping sum is checkable per percentile
        if sum(spl["phases_us"][p]["p50"] for p in FS.PHASES) != spl["render_us"]["p50"] or spl["render_us"]["p50"] != len(FS.PHASES):
            raise Red(f"{arm}: the split's phases do not sum to its total")
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    rec, label = FS.seal_framesplit(raw, reg, "gate-mock", {"path": "workshop/attest/sessionwalk-demo.json"}, {"rustc": "gate"})
    envelope.validate(rec)
    if label != "VOID":
        raise Red(f"the mock court (all tax, no work) read {label!r}, not VOID")
    for plant, code in (("witness", "FRAMESPLIT-WITNESS"), ("close", "FRAMESPLIT-CLOSED")):
        pout = os.path.join(BUILD, f"framesplit-plant-{plant}.json")
        if os.path.exists(pout):
            os.remove(pout)
        cp = subprocess.run([SHELL_EXE] + base + ["--plant", plant, "--out", pout], capture_output=True, text=True, cwd=ROOT)
        if cp.returncode == 0 or code not in cp.stderr or os.path.exists(pout):
            raise Red(f"PLANT {plant}: the split court did not refuse with {code} and no record")
    return ("the FRAME-SPLIT-0 court runs headless over the mock surface on the sealed reference session: witnesses first "
            "(both arms' envelope paths reproduce the 4 sealed frame witnesses, the marked mirror reproduces them byte for "
            "byte, the arms agree), 10 warm-up rounds then 4 cells x 2 samples ABBA, each split's seven phases summing "
            "exactly to its total; the raw record seals citing FRAME-SPLIT-0 and reads VOID (under the mock the probes are "
            "all the time there is); PLANTS: a tampered sealed witness refuses FRAMESPLIT-WITNESS and a window closed "
            "mid-court refuses FRAMESPLIT-CLOSED, each writing no record")


def framesplit_fence():
    """The split measures the path LATENCY-1R timed and nothing else: the envelope cells call arm_composite; the marked
    mirror makes fast::render's calls in fast::render's order (production) or the single-thread arm's (fast::emit),
    with exactly five marks between the phases; the court reads the clock at render-start, at each mark, after the
    BGR conversion and at frame-ready, hashes nothing inside the interval, and the window driver is appended after
    LATENCY-0's untouched instrument."""
    fast_src = read(os.path.join(KERNEL, "fast.rs")).decode("utf-8")
    render = src_span(fast_src, "pub fn render(", "/// RE-BREAKDOWN-1 — Court A")
    pr = read(os.path.join(SHELL, "present.rs")).decode("utf-8")
    mirror = src_span(pr, "pub fn arm_composite_marked<", "\n}\n")
    want_order = ["scene.strips(&mut strips)", "scene.frame(&strips, &mut frame)", "blocked_floor(&scene.floor)", "emit_threaded("]
    ro = [render.find(t) for t in want_order]
    mo = [mirror.find(t) for t in want_order]
    if -1 in ro or ro != sorted(ro) or -1 in mo or mo != sorted(mo):
        raise Red("the marked mirror does not make fast::render's calls in fast::render's order")
    if "fast::PROD_THREADS" not in mirror or "fast::emit(scene, &strips, &frame, &mut pixels, &floor)" not in mirror:
        raise Red("the mirror's arms are not emit_threaded at PROD_THREADS and the single-thread fast::emit")
    if mirror.count("m.mark();") != 5 or "hud::overlay(" not in mirror or "picture(" in mirror:
        raise Red("the mirror does not mark exactly five render phases (strips, frame, floor_swizzle, emit, hud)")
    rs = read(os.path.join(SHELL, "framesplit.rs")).decode("utf-8")
    court = src_span(rs, "pub fn court(", "fn pct_json(")
    if "arm_composite(&inputs[k].scene, arm)" not in court or "arm_composite_marked(&inputs[k].scene, arm, &mut m)" not in court:
        raise Red("the envelope cells do not call arm_composite, or the split cells do not call the marked mirror")
    timed = court[court.index("let t0 = s.ticks();"):court.index("if comp != expected[k]")]
    order = [timed.find(t) for t in ("let t0 = s.ticks();", "arm_composite", "to_blit(&comp)", "let t_bgr", "s.present(&bgr)")]
    if -1 in order or order != sorted(order) or "frame_digest" in timed or "sha256" in timed:
        raise Red("the court's timed interval is not t0 -> render (marked) -> bgr -> present, hash-free")
    if "let bounds = [t0, t[0], t[1], t[2], t[3], t[4], t_bgr, t1];" not in court:
        raise Red("the phases are not consecutive differences of contiguous clock reads ending at frame-ready")
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    if tail.index("FRAME-SPLIT-0 (appended)") < tail.index("LATENCY-1R (appended)") or "framesplit::court(&mut surf, &inputs, per_cell)" not in tail:
        raise Red("the FRAME-SPLIT-0 window driver is not appended after LATENCY-1R's, over the same GDI surface")
    return ("the envelope cells call arm_composite (the path LATENCY-1R timed); the marked mirror makes fast::render's "
            "calls in fast::render's order (strips, frame, blocked_floor, emit_threaded at PROD_THREADS) or the "
            "single-thread fast::emit, with exactly five marks; the court's interval is t0 -> render -> bgr -> present, "
            "hash-free, its phases consecutive differences of contiguous clock reads ending at frame-ready; the window "
            "driver is appended after LATENCY-1R's over the same GDI surface, LATENCY-0's instrument still a byte-exact prefix")


# ------------------------------------------------------------------ PRESENT-SCALE-0
def presentscale_preregistered():
    """PRESENT-SCALE-0's method is locked before any host number: destination geometry (client area, half vs full) the
    only variable over FRAME-SPLIT-0's path, block-ABBA with warm-up after every resize, the client rectangle verified,
    the environment recorded and never varied, and a diagnostic attribution (VOID / CONFOUNDED / SCALING MATERIAL /
    SCALING IMMATERIAL) with no seat and no winner. The code's constants must equal the registered ones."""
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    e = reg.get("PRESENT-SCALE-0")
    if not e:
        raise Red("PRESENT-SCALE-0 is not registered")
    hyp, succ, fail = e["hypothesis"].lower(), e["success_condition"].lower(), e["failure_condition"].lower()
    lims = " ".join(e["interpretation_limits"]).lower()
    checks = {
        "one variable: the client-area destination, half vs full": "one thing" in hyp and "client-area" in hyp and "960x540" in hyp and "1920x1080" in hyp,
        "everything else FRAME-SPLIT-0's path, unchanged": "frame-split-0's production path unchanged" in hyp,
        "a diagnostic, no seat, no predicted outcome": "diagnostic" in hyp and "does not seat" in hyp and "not predicted" in hyp,
        "resize between blocks, H F F H H F F H, warm-up": "h f f h h f f h" in succ and "5 discarded warm-up rounds" in succ,
        "the client rectangle verified": "getclientrect" in succ and "must equal the requested size" in succ,
        "the environment recorded, never varied": "stretch mode" in succ and "never varied" in succ,
        "the four readings": all(x in succ for x in ("void", "confounded", "scaling material", "scaling immaterial")),
        "the thresholds": "100 permille of its envelope" in succ and "50 permille" in succ and "100 permille of blit(half)" in succ,
        "no second variable, no winner": "second variable" in fail and "winner" in fail,
        "never compared to an emit p99 or LATENCY-0/1; --confirm; LATENCY-0 prefix": "emit p99" in fail and "--confirm" in fail and "byte-exact prefix" in fail,
        "scope: the net of scaling vs copy, the wndproc difference, DPI": "net" in lims and "wm_getminmaxinfo" in lims and "dpi-unaware" in lims and "not input-to-photon" in lims,
    }
    missing = [k for k, ok in checks.items() if not ok]
    if missing:
        raise Red("the PRESENT-SCALE-0 method is not fully locked: " + "; ".join(missing))
    if not entry_hash_ok("PRESENT-SCALE-0", e):
        raise Red("the PRESENT-SCALE-0 entry was edited after registration (chain hash)")
    import presentscale as PS
    rs = read(os.path.join(SHELL, "presentscale.rs")).decode("utf-8")
    if ("pub const BLOCK_ORDER: [usize; 8] = [0, 1, 1, 0, 0, 1, 1, 0];" not in rs or "pub const WARM_ROUNDS_PER_BLOCK: usize = 5;" not in rs
            or "pub const GEOMETRIES: [(u32, u32); 2] = [((W / 2) as u32, (H / 2) as u32), (W as u32, H as u32)];" not in rs):
        raise Red("the court's geometries, block order or warm-up are not the registered ones")
    if (PS.VOID_TAX_PERMILLE, PS.CONFOUND_PERMILLE, PS.MATERIAL_PERMILLE, PS.BLOCK_ORDER, PS.WARM_ROUNDS_PER_BLOCK,
            PS.GEOMS) != (100, 50, 100, "HFFHHFFH", 5, {"half": [960, 540], "full": [1920, 1080]}):
        raise Red("the sealer's constants are not the registered ones")
    return ("PRESENT-SCALE-0's method is locked before any host number: the client-area destination (half 960x540 vs full "
            "1920x1080) is the only variable over FRAME-SPLIT-0's unchanged path; blocks H F F H H F F H with 5 warm-up "
            "rounds after every resize; the client rectangle read back and required to match; screen sizes and stretch mode "
            "recorded, never varied; on p50s VOID (tax >= 100 permille) / CONFOUNDED (non-blit moved >= 50) / SCALING "
            "MATERIAL (|blit delta| >= 100 permille, signed) / SCALING IMMATERIAL — a diagnostic with no seat and no winner; "
            "the code's constants equal the registered ones; hash-locked %s" % e["chain_hash"][:8])


def presentscale_sealer():
    """The host sealer, driven with synthetic geometries: VOID, CONFOUNDED, SCALING MATERIAL (both signs) and SCALING
    IMMATERIAL fire exactly at the registered bounds; a client area that is not the requested size, another block
    order, or another source size is refused; every sealed record cites PRESENT-SCALE-0 and passes the firewall."""
    import presentscale as PS
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]

    def pct(v):
        return {"p50": v, "p95": v, "p99": v, "max": v}

    def geom(name, blit, non_blit=8000, env=None, total=None, client=None):
        phases = [1000, 2000, 100, 3000, 100, 1800][:6]
        scale = non_blit / sum(phases)
        vals = [int(round(v * scale)) for v in phases]
        vals[0] += non_blit - sum(vals)
        env = (non_blit + blit) if env is None else env
        total = (non_blit + blit) if total is None else total
        dest = PS.GEOMS[name]
        return {"destination": dest, "client": client or dest,
                "envelope": {"render_us": pct(env), "present_us": pct(9000), "samples": 4},
                "split": {"phases_us": {**{p: pct(v) for p, v in zip(PS.NON_BLIT, vals)}, "blit": pct(blit)},
                          "render_us": pct(total), "present_us": pct(9000), "samples": 4}}

    def raw(half, full, **over):
        d = {"geometries": {"half": half, "full": full}, "source": [1920, 1080], "phases": list(PS.PHASES),
             "block_order": "HFFHHFFH", "warm_rounds_per_block": 5, "refresh_period_us": 13400, "sequence_frames": 4,
             "samples_per_cell": 4, "production_threads": 8, "phase_origin": "locked",
             "screen": {"logical": [1920, 1080], "desktop": [1920, 1080]}, "stretch_mode": 1}
        d.update(over)
        return {"name": "verdandi-presentscale", "provenance": {"tool": "synthetic", "unix_seconds": 0}, "data": d}

    session, build = {"path": "synthetic", "chain_hash": "0" * 64}, {"rustc": "gate", "flags": ["-O"]}
    cases = {
        "SCALING MATERIAL (the full-size destination is cheaper)": (geom("half", 7000), geom("full", 6300)),   # -100 permille
        "SCALING MATERIAL (the full-size destination is dearer)": (geom("half", 7000), geom("full", 7700)),    # +100
        "SCALING IMMATERIAL": (geom("half", 7000), geom("full", 6301)),                                        # 99
        "CONFOUNDED": (geom("half", 7000), geom("full", 5000, non_blit=8400)),                                 # non-blit +50
        "VOID": (geom("half", 7000), geom("full", 5000, env=13000, total=14300)),                              # tax 100
    }
    for want, (h, f) in cases.items():
        rec, got = PS.seal_presentscale(raw(h, f), reg, "gate", session, build)
        envelope.validate(rec)
        if got != want:
            raise Red(f"the sealer read {got!r}, the registered rule says {want!r}")
        if rec["provenance"]["preregistered"]["chain_hash"] != reg["PRESENT-SCALE-0"]["chain_hash"]:
            raise Red("the sealed record does not cite PRESENT-SCALE-0")
    ok_h, ok_f = cases["SCALING IMMATERIAL"]
    for bad, why in ((raw(ok_h, geom("full", 6301, client=[1920, 1049])), "a clamped client area"),
                     (raw(ok_h, ok_f, block_order="HFHFHFHF"), "another block order"),
                     (raw(ok_h, ok_f, source=[1280, 720]), "another source size")):
        try:
            PS.seal_presentscale(bad, reg, "gate", session, build)
            raise Red(f"the sealer accepted {why}")
        except PS.Refuse:
            pass
    return ("verify/presentscale.py, driven with synthetic geometries: SCALING MATERIAL (cheaper and dearer, at exactly 100 "
            "permille), SCALING IMMATERIAL (99), CONFOUNDED (non-blit moved 50) and VOID (tax 100) fire at the registered "
            "bounds; a clamped client area, another block order or another source size is refused; records cite "
            "PRESENT-SCALE-0 and pass the firewall")


def presentscale_court():
    """The SAME geometry court the host window runs, headless over the mock surface on the sealed session: witnesses
    first, 8 blocks with the client area verified after every resize, both geometries' envelope and split recorded.
    PLANTS: a tampered witness, a window manager that clamps the full client area, and a mid-court close all refuse
    with no record."""
    need_rustc()
    if SHELL_EXE is None:
        raise Red("the shell was not built")
    import presentscale as PS
    out = os.path.join(BUILD, "presentscale-mock.json")
    if os.path.exists(out):
        os.remove(out)
    base = ["presentscale-selftest", "--session", SESSIONWALK_DEMO, "--per-cell", "4"]
    cp = subprocess.run([SHELL_EXE] + base + ["--out", out], capture_output=True, text=True, cwd=ROOT)
    if cp.returncode != 0 or "presentscale court OK" not in cp.stdout or not os.path.exists(out):
        raise Red("the headless geometry court did not run: " + (cp.stderr.strip() or cp.stdout.strip()))
    with open(out, encoding="utf-8") as fh:
        raw = json.load(fh)
    os.remove(out)
    d = raw["data"]
    for g, dest in PS.GEOMS.items():
        gd = d["geometries"][g]
        if gd["client"] != dest or gd["envelope"]["samples"] != 4 or gd["split"]["samples"] != 4:
            raise Red(f"{g}: the court did not record 4 samples per cell at the verified {dest[0]}x{dest[1]} client area")
        if sum(gd["split"]["phases_us"][p]["p50"] for p in PS.PHASES) != gd["split"]["render_us"]["p50"]:
            raise Red(f"{g}: the split's phases do not sum to its total")
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    rec, label = PS.seal_presentscale(raw, reg, "gate-mock", {"path": "workshop/attest/sessionwalk-demo.json"}, {"rustc": "gate"})
    envelope.validate(rec)
    if label != "VOID":
        raise Red(f"the mock court (all tax, no work) read {label!r}, not VOID")
    for plant, code in (("witness", "PRESENTSCALE-WITNESS"), ("geometry", "PRESENTSCALE-GEOMETRY"), ("close", "PRESENTSCALE-CLOSED")):
        pout = os.path.join(BUILD, f"presentscale-plant-{plant}.json")
        if os.path.exists(pout):
            os.remove(pout)
        cp = subprocess.run([SHELL_EXE] + base + ["--plant", plant, "--out", pout], capture_output=True, text=True, cwd=ROOT)
        if cp.returncode == 0 or code not in cp.stderr or os.path.exists(pout):
            raise Red(f"PLANT {plant}: the geometry court did not refuse with {code} and no record")
    return ("the PRESENT-SCALE-0 court runs headless over the mock surface on the sealed reference session: witnesses first "
            "(the production envelope path reproduces the sealed witnesses, the marked mirror byte-equal), 8 blocks H F F H H "
            "F F H with the client area verified after every resize, both geometries' envelope and split recorded (4 samples "
            "per cell), each split summing exactly to its total; the raw record seals and reads VOID under the mock; "
            "PLANTS: a tampered witness (PRESENTSCALE-WITNESS), a clamped full client area (PRESENTSCALE-GEOMETRY) and a "
            "mid-court close (PRESENTSCALE-CLOSED) each refuse with no record")


def presentscale_fence():
    """Only the destination changes: the settable surface's present mirrors LATENCY-0's present_once with the
    destination rectangle as the one difference, the window style and position are the same for both geometries, the
    window procedure differs from LATENCY-0's only by WM_GETMINMAXINFO, the court uses FRAME-SPLIT-0's envelope and
    marked paths on the production arm, and LATENCY-0's instrument is still a byte-exact prefix."""
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    i_fs, i_ps = tail.find("FRAME-SPLIT-0 (appended)"), tail.find("PRESENT-SCALE-0 (appended)")
    if i_fs < 0 or i_ps < i_fs:
        raise Red("the PRESENT-SCALE-0 surface is not appended after FRAME-SPLIT-0's driver")
    sect = tail[i_ps:]
    pres = src_span(sect, "fn present(&mut self", "fn flush(&mut self)")
    order = [pres.find(t) for t in ("GetDC(", "StretchDIBits(", "let ready = qpc();", "(self.flush_fn)();", "Some(qpc())", "ReleaseDC(")]
    if -1 in order or order != sorted(order):
        raise Red("the settable surface's present does not mirror LATENCY-0's present_once")
    if "StretchDIBits(hdc, 0, 0, self.dst_w, self.dst_h, 0, 0, W as i32, H as i32," not in pres:
        raise Red("the blit's only change is not the destination rectangle (dst_w, dst_h) over the full W x H source")
    setd = src_span(sect, "fn set_destination(", "fn environment(")
    if ("AdjustWindowRect(&mut r, WS_OVERLAPPEDWINDOW, 0)" not in setd or "SetWindowPos(self.hwnd, std::ptr::null_mut(), 0, 0, ow, oh," not in setd
            or "GetClientRect(" not in setd):
        raise Red("the client area is not sized through AdjustWindowRect at a fixed position and read back")
    wp = src_span(sect, "extern \"system\" fn wnd_proc_geom(", "struct GeomGdiSurface")
    if "WM_GETMINMAXINFO" not in wp or "wnd_proc(hwnd, msg, wp, lp)" not in wp:
        raise Red("the geometry window procedure is not LATENCY-0's plus WM_GETMINMAXINFO")
    if "WS_OVERLAPPEDWINDOW | WS_VISIBLE" not in src_span(sect, "pub fn presentscale_window(", "let header = BitmapInfoHeader"):
        raise Red("the geometry window is not the same overlapped window style")
    rs = read(os.path.join(SHELL, "presentscale.rs")).decode("utf-8")
    court = src_span(rs, "pub fn court<", "fn pct_json(")
    if ("arm_composite(&inputs[k].scene, Arm::Production)" not in court
            or "arm_composite_marked(&inputs[k].scene, Arm::Production, &mut m)" not in court
            or "let bounds = [t0, t[0], t[1], t[2], t[3], t[4], t_bgr, t1];" not in court
            or "if client != (w, h)" not in court):
        raise Red("the court does not use FRAME-SPLIT-0's envelope/marked paths with a verified client area")
    timed = court[court.index("let t0 = s.ticks();"):court.index("if comp != expected[k]")]
    if "frame_digest" in timed or "sha256" in timed or "set_destination" in timed:
        raise Red("the timed interval holds hashing or a resize")
    return ("only the destination changes: the settable surface's present mirrors LATENCY-0's present_once with the "
            "destination rectangle (dst_w, dst_h) over the full W x H source as its one difference; the client area is "
            "sized through AdjustWindowRect at a fixed position and read back; the window style is the same overlapped "
            "window and the window procedure is LATENCY-0's plus WM_GETMINMAXINFO; the court uses FRAME-SPLIT-0's envelope "
            "and marked paths on the production arm, resizes only between blocks, hashes nothing inside the interval; "
            "LATENCY-0's instrument is still a byte-exact prefix")


# ------------------------------------------------------------------ PRESENT-STRETCH-0 and ALLOC-REUSE-0
def locked_entry(rung: str, phrases: dict) -> dict:
    """A registered entry whose method phrases are all present (lower-cased search over its fields) and whose chain hash
    is intact; the Red names the missing clauses."""
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    e = reg.get(rung)
    if not e:
        raise Red(f"{rung} is not registered")
    text = {"hyp": e["hypothesis"].lower(), "succ": e["success_condition"].lower(), "fail": e["failure_condition"].lower(),
            "lims": " ".join(e["interpretation_limits"]).lower()}
    missing = [k for k, (field, needles) in phrases.items() if not all(n in text[field] for n in needles)]
    if missing:
        raise Red(f"the {rung} method is not fully locked: " + "; ".join(missing))
    if not entry_hash_ok(rung, e):
        raise Red(f"the {rung} entry was edited after registration (chain hash)")
    return e


def presentstretch_preregistered():
    """PRESENT-STRETCH-0's method is locked before any host number: the stretch mode (BLACKONWHITE, COLORONCOLOR,
    HALFTONE at the half-size destination) the only variable, set with the brush origin identically before every blit,
    blocks B C H H C B B C H H C B with warm-up, the effective mode and the client area verified, a diagnostic reading
    per mode against the default, no mode adopted. Code constants must match."""
    e = locked_entry("PRESENT-STRETCH-0", {
        "one variable: the stretch mode at 960x540": ("hyp", ("one thing", "960x540", "blackonwhite", "coloroncolor", "halftone")),
        "mode and brush origin set identically before every blit": ("hyp", ("brush origin", "identically in every cell")),
        "a diagnostic, no seat, not predicted": ("hyp", ("diagnostic", "does not seat or adopt", "not predicted")),
        "blocks, warm-up, verified mode and client": ("succ", ("b c h h c b b c h h c b", "5 discarded warm-up rounds", "effective mode", "must be 960x540")),
        "the readings and thresholds": ("succ", ("void", "confounded", "mode material", "mode immaterial", "100 permille", "50 permille")),
        "no second variable, no adopted mode, no general claim": ("fail", ("second variable", "adopted stretch mode", "in general")),
        "--confirm, emit p99, LATENCY-0 prefix": ("fail", ("--confirm", "emit p99", "byte-exact prefix")),
        "scope: GDI's semantics recorded not verified": ("lims", ("not verified", "separate court", "not input-to-photon")),
    })
    import presentstretch as PST
    rs = read(os.path.join(SHELL, "presentstretch.rs")).decode("utf-8")
    if ("pub const MODES: [i32; 3] = [1, 3, 4];" not in rs or "pub const BLOCK_ORDER: [usize; 12] = [0, 1, 2, 2, 1, 0, 0, 1, 2, 2, 1, 0];" not in rs
            or "pub const WARM_ROUNDS_PER_BLOCK: usize = 5;" not in rs):
        raise Red("the court's modes, block order or warm-up are not the registered ones")
    if (PST.MODES, PST.BLOCK_ORDER, PST.VOID_TAX_PERMILLE, PST.CONFOUND_PERMILLE, PST.MATERIAL_PERMILLE) != \
            ({"BLACKONWHITE": 1, "COLORONCOLOR": 3, "HALFTONE": 4}, "BCHHCBBCHHCB", 100, 50, 100):
        raise Red("the sealer's constants are not the registered ones")
    return ("PRESENT-STRETCH-0's method is locked before any host number: the stretch mode (BLACKONWHITE 1, COLORONCOLOR 3, "
            "HALFTONE 4) is the only variable at the 960x540 destination, set with the brush origin identically before every "
            "blit; blocks B C H H C B B C H H C B with 5 warm-up rounds; the effective mode and the client area read back; per "
            "mode against BLACKONWHITE on p50s VOID / CONFOUNDED / MODE MATERIAL / MODE IMMATERIAL — a diagnostic, no mode "
            "adopted; the code's constants equal the registered ones; hash-locked %s" % e["chain_hash"][:8])


def allocreuse_preregistered():
    """ALLOC-REUSE-0's method is locked before any host number: the buffers' lifetime (fresh vs reused) the only
    variable over FRAME-SPLIT-0's apparatus, the same calls and marks, witnesses first with byte-equal reuse, a
    diagnostic reading on the envelope with the per-phase deltas beside, nothing adopted. Code constants must match."""
    e = locked_entry("ALLOC-REUSE-0", {
        "one variable: the buffers' lifetime": ("hyp", ("one thing", "fresh", "reused", "same calls in the same order")),
        "the floor swizzle stays fresh; fast.rs untouched": ("hyp", ("stays fresh in both", "fast.rs is untouched")),
        "a diagnostic, not predicted": ("hyp", ("diagnostic", "does not seat or adopt", "not predicted")),
        "witnesses first, reuse bytes equal": ("succ", ("witnesses first", "reused buffers' index frame, composite and blit bytes equal")),
        "four cells ABBA, warm-up": ("succ", ("four cells", "abba", "10 warm-up rounds")),
        "the readings and thresholds": ("succ", ("void", "confounded", "allocation material", "allocation immaterial", "50 permille of the fresh envelope")),
        "no per-phase verdict, nothing adopted": ("fail", ("per-phase verdict", "adopting buffer reuse")),
        "--confirm, emit p99, LATENCY-0 prefix": ("fail", ("--confirm", "emit p99", "byte-exact prefix")),
        "scope: allocator/OS-specific, not input-to-photon": ("lims", ("page faults", "not input-to-photon")),
    })
    import allocreuse as AR
    rs = read(os.path.join(SHELL, "allocreuse.rs")).decode("utf-8")
    if "pub const WARM_ROUNDS: usize = 10;" not in rs:
        raise Red("the court's warm-up is not the registered 10 rounds")
    if (AR.ALLOCATING, AR.UNCHANGED, AR.VOID_TAX_PERMILLE, AR.CONFOUND_PERMILLE, AR.MATERIAL_PERMILLE) != \
            (("strips", "frame", "emit", "bgr"), ("floor_swizzle", "hud", "blit"), 100, 50, 50):
        raise Red("the sealer's phase groups or constants are not the registered ones")
    return ("ALLOC-REUSE-0's method is locked before any host number: the buffers' lifetime (fresh every frame vs reused) is "
            "the only variable over FRAME-SPLIT-0's apparatus with the same calls and marks, the floor swizzle fresh in both; "
            "witnesses first with the reused bytes equal to the fresh path's; four cells ABBA after 10 warm-up rounds; on p50s "
            "VOID / CONFOUNDED (unchanged phases >= 50) / ALLOCATION MATERIAL (|envelope delta| >= 50 permille) / IMMATERIAL, "
            "per-phase deltas beside and never ruled on; nothing adopted; hash-locked %s" % e["chain_hash"][:8])


def diag_sealer_cases(module, seal_fn_name: str, rung: str, cases: dict, bad: list) -> None:
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    session, build = {"path": "synthetic", "chain_hash": "0" * 64}, {"rustc": "gate", "flags": ["-O"]}
    seal = getattr(module, seal_fn_name)
    for want, raw in cases.items():
        rec, got = seal(raw, reg, "gate", session, build)
        envelope.validate(rec)
        if got != want:
            raise Red(f"{rung}'s sealer read {got!r}, the registered rule says {want!r}")
        if rec["provenance"]["preregistered"]["chain_hash"] != reg[rung]["chain_hash"]:
            raise Red(f"the sealed record does not cite {rung}")
    for raw, why in bad:
        try:
            seal(raw, reg, "gate", session, build)
            raise Red(f"{rung}'s sealer accepted {why}")
        except module.Refuse:
            pass


def _pct4(v):
    return {"p50": v, "p95": v, "p99": v, "max": v}


def _cell(blit, non_blit=8000, env=None, total=None, phases=("strips", "frame", "floor_swizzle", "emit", "hud", "bgr", "blit")):
    base = [1000, 2000, 100, 3000, 100, 1800]
    vals = [int(round(v * non_blit / sum(base))) for v in base]
    vals[0] += non_blit - sum(vals)
    env = non_blit + blit if env is None else env
    total = non_blit + blit if total is None else total
    return {"envelope": {"render_us": _pct4(env), "present_us": _pct4(9000), "samples": 4},
            "split": {"phases_us": dict(zip(phases, [_pct4(v) for v in vals + [blit]])), "render_us": _pct4(total),
                      "present_us": _pct4(9000), "samples": 4}}


def presentstretch_sealer():
    """The stretch sealer, with synthetic modes: per-mode MODE MATERIAL (cheaper/dearer at exactly 100 permille), MODE
    IMMATERIAL (99), CONFOUNDED (50) and a court-wide VOID fire at the registered bounds; a mode the device context did
    not honour, another client area or another block order is refused."""
    import presentstretch as PST

    def raw(c, h, b=None, **over):
        modes = {}
        for name, mode, cell in (("BLACKONWHITE", 1, b or _cell(7000)), ("COLORONCOLOR", 3, c), ("HALFTONE", 4, h)):
            modes[name] = dict(cell, requested=mode, effective=mode)
        d = {"modes": modes, "default_mode": "BLACKONWHITE", "destination": [960, 540], "client": [960, 540],
             "source": [1920, 1080], "phases": list(PST.PHASES), "block_order": "BCHHCBBCHHCB", "warm_rounds_per_block": 5,
             "refresh_period_us": 13400, "sequence_frames": 4, "samples_per_cell": 4, "production_threads": 8, "phase_origin": "locked"}
        d.update(over)
        return {"name": "verdandi-presentstretch", "provenance": {"tool": "synthetic", "unix_seconds": 0}, "data": d}

    cases = {
        "COLORONCOLOR: MODE MATERIAL (cheaper); HALFTONE: MODE MATERIAL (dearer)": raw(_cell(6300), _cell(7700)),
        "COLORONCOLOR: MODE IMMATERIAL; HALFTONE: CONFOUNDED": raw(_cell(6301), _cell(7000, non_blit=8400)),
        "VOID": raw(_cell(6300), _cell(7700, env=14000, total=15700)),
    }
    ignored = raw(_cell(6300), _cell(7700))
    ignored["data"]["modes"]["HALFTONE"]["effective"] = 1
    diag_sealer_cases(PST, "seal_presentstretch", "PRESENT-STRETCH-0", cases,
                      [(ignored, "a mode the device context did not honour"),
                       (raw(_cell(6300), _cell(7700), client=[944, 501]), "another client area"),
                       (raw(_cell(6300), _cell(7700), block_order="BCHBCHBCHBCH"), "another block order")])
    return ("verify/presentstretch.py, driven with synthetic modes: MODE MATERIAL (cheaper and dearer, at exactly 100 permille), "
            "MODE IMMATERIAL (99), CONFOUNDED (50) and a court-wide VOID (tax 100) fire at the registered bounds, per mode "
            "against BLACKONWHITE; an unhonoured mode, another client area or another block order is refused; records cite "
            "PRESENT-STRETCH-0 and pass the firewall")


def allocreuse_sealer():
    """The allocation sealer, with synthetic variants: ALLOCATION MATERIAL (reuse cheaper/dearer at exactly 50 permille of
    the fresh envelope), IMMATERIAL (49), CONFOUNDED (the unchanged phases moved 50) and VOID fire at the registered
    bounds; the per-phase deltas are recorded; another warm-up or phase order is refused."""
    import allocreuse as AR

    def var(env, unchanged=(100, 100, 7000), alloc=(60, 3000, 3600, 1800), env_split=None):
        ph = dict(zip(AR.ALLOCATING, alloc))
        ph.update(dict(zip(AR.UNCHANGED, unchanged)))
        total = sum(ph.values())
        return {"envelope": {"render_us": _pct4(env), "present_us": _pct4(9000), "samples": 4},
                "split": {"phases_us": {p: _pct4(ph[p]) for p in AR.PHASES}, "render_us": _pct4(env if env_split is None else env_split),
                          "present_us": _pct4(9000), "samples": 4}}

    def raw(f, r, **over):
        d = {"variants": {"fresh": f, "reused": r}, "phases": list(AR.PHASES), "warm_rounds": 10, "refresh_period_us": 13400,
             "sequence_frames": 4, "samples_per_cell": 4, "production_threads": 8, "phase_origin": "locked"}
        d.update(over)
        return {"name": "verdandi-allocreuse", "provenance": {"tool": "synthetic", "unix_seconds": 0}, "data": d}

    cases = {
        "ALLOCATION MATERIAL (reuse cheaper)": raw(var(16000), var(15200, alloc=(40, 2600, 3000, 1100))),   # -800 = 50
        "ALLOCATION MATERIAL (reuse dearer)": raw(var(16000), var(16800)),
        "ALLOCATION IMMATERIAL": raw(var(16000), var(15201)),                                             # 49
        "CONFOUNDED": raw(var(16000), var(15000, unchanged=(100, 100, 6640))),                            # 360/7200 = 50
        "VOID": raw(var(16000), var(15000, env_split=16500)),                                             # 1500/15000 = 100
    }
    rec, _ = AR.seal_allocreuse(cases["ALLOCATION MATERIAL (reuse cheaper)"],
                                json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"],
                                "gate", {"path": "synthetic"}, {"rustc": "gate"})
    pd = rec["data"]["derived"]["deltas"]["phase_delta_p50_us"]
    if (pd["frame"], pd["emit"], pd["bgr"], pd["blit"]) != (-400, -600, -700, 0):
        raise Red("the per-phase deltas are not recorded as measured")
    diag_sealer_cases(AR, "seal_allocreuse", "ALLOC-REUSE-0", cases,
                      [(raw(var(16000), var(15200), warm_rounds=5), "another warm-up"),
                       (raw(var(16000), var(15200), phases=list(AR.PHASES)[::-1]), "phases out of order")])
    return ("verify/allocreuse.py, driven with synthetic variants: ALLOCATION MATERIAL (reuse cheaper and dearer, at exactly 50 "
            "permille of the fresh envelope), IMMATERIAL (49), CONFOUNDED (the unchanged phases moved 50) and VOID fire at the "
            "registered bounds; the per-phase deltas are recorded as measured and never ruled on; another warm-up or phase "
            "order is refused; records cite ALLOC-REUSE-0 and pass the firewall")


def diag_court(cmd: str, per_cell: str, ok_marker: str, plants: list, check) -> None:
    need_rustc()
    if SHELL_EXE is None:
        raise Red("the shell was not built")
    out = os.path.join(BUILD, f"{cmd}-mock.json")
    if os.path.exists(out):
        os.remove(out)
    base = [f"{cmd}-selftest", "--session", SESSIONWALK_DEMO, "--per-cell", per_cell]
    cp = subprocess.run([SHELL_EXE] + base + ["--out", out], capture_output=True, text=True, cwd=ROOT)
    if cp.returncode != 0 or ok_marker not in cp.stdout or not os.path.exists(out):
        raise Red(f"the headless {cmd} court did not run: " + (cp.stderr.strip() or cp.stdout.strip()))
    with open(out, encoding="utf-8") as fh:
        raw = json.load(fh)
    os.remove(out)
    check(raw)
    for plant, code in plants:
        pout = os.path.join(BUILD, f"{cmd}-plant-{plant}.json")
        if os.path.exists(pout):
            os.remove(pout)
        cp = subprocess.run([SHELL_EXE] + base + ["--plant", plant, "--out", pout], capture_output=True, text=True, cwd=ROOT)
        if cp.returncode == 0 or code not in cp.stderr or os.path.exists(pout):
            raise Red(f"PLANT {plant}: the {cmd} court did not refuse with {code} and no record")


def presentstretch_court():
    """The SAME stretch court the host window runs, headless over the mock: witnesses first, the client area and each
    effective mode verified, 12 blocks, every mode's envelope and split recorded, each split summing to its total.
    PLANTS: a tampered witness, a device context that ignores the requested mode, and a mid-court close all refuse."""
    import presentstretch as PST
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]

    def check(raw):
        d = raw["data"]
        for name, mode in PST.MODES.items():
            md = d["modes"][name]
            if md["effective"] != mode or md["envelope"]["samples"] != 4 or md["split"]["samples"] != 4:
                raise Red(f"{name}: not recorded at its verified mode with 4 samples per cell")
            if sum(md["split"]["phases_us"][p]["p50"] for p in PST.PHASES) != md["split"]["render_us"]["p50"]:
                raise Red(f"{name}: the split's phases do not sum to its total")
        rec, label = PST.seal_presentstretch(raw, reg, "gate-mock", {"path": "workshop/attest/sessionwalk-demo.json"}, {"rustc": "gate"})
        envelope.validate(rec)
        if label != "VOID":
            raise Red(f"the mock stretch court read {label!r}, not VOID")

    diag_court("presentstretch", "4", "presentstretch court OK",
               [("witness", "PRESENTSTRETCH-WITNESS"), ("mode", "PRESENTSTRETCH-MODE"), ("close", "PRESENTSTRETCH-CLOSED")], check)
    return ("the PRESENT-STRETCH-0 court runs headless over the mock surface on the sealed session: witnesses first, the "
            "960x540 client area and each block's effective mode verified, 12 blocks B C H H C B B C H H C B, all three modes' "
            "envelope and split recorded, each split summing to its total; its raw record seals and reads VOID under the mock; "
            "PLANTS: a tampered witness (PRESENTSTRETCH-WITNESS), an ignored mode (PRESENTSTRETCH-MODE) and a mid-court close "
            "(PRESENTSTRETCH-CLOSED) each refuse with no record")


def allocreuse_court():
    """The SAME allocation court the host window runs, headless over the mock: witnesses first including the reused
    buffers' byte-equality, four cells after the warm-up, each split summing to its total. PLANTS: a tampered witness
    and a mid-court close both refuse with no record."""
    import allocreuse as AR
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]

    def check(raw):
        d = raw["data"]
        if d["warm_rounds"] != 10 or d["samples_per_cell"] != 2:
            raise Red("the court did not run 2 samples per cell after 10 warm-up rounds")
        for v in AR.VARIANTS:
            spl = d["variants"][v]["split"]
            if sum(spl["phases_us"][p]["p50"] for p in AR.PHASES) != spl["render_us"]["p50"]:
                raise Red(f"{v}: the split's phases do not sum to its total")
        rec, label = AR.seal_allocreuse(raw, reg, "gate-mock", {"path": "workshop/attest/sessionwalk-demo.json"}, {"rustc": "gate"})
        envelope.validate(rec)
        if label != "VOID":
            raise Red(f"the mock allocation court read {label!r}, not VOID")

    diag_court("allocreuse", "2", "allocreuse court OK",
               [("witness", "ALLOCREUSE-WITNESS"), ("close", "ALLOCREUSE-CLOSED")], check)
    return ("the ALLOC-REUSE-0 court runs headless over the mock surface on the sealed session: witnesses first (the fresh "
            "path reproduces the sealed witnesses, the marked mirror byte-equal, the reused buffers' frame, composite and blit "
            "bytes equal the fresh path's for all 4 frames), 10 warm-up rounds then 4 cells ABBA, each split summing to its "
            "total; its raw record seals and reads VOID under the mock; PLANTS: a tampered witness (ALLOCREUSE-WITNESS) and a "
            "mid-court close (ALLOCREUSE-CLOSED) each refuse with no record")


def presentstretch_fence():
    """Only the stretch mode changes: the stretch surface's present is LATENCY-0's present_once plus SetStretchBltMode and
    SetBrushOrgEx before the blit into the fixed half-size destination; the window is the plain overlapped window with
    LATENCY-0's procedure; the court uses FRAME-SPLIT-0's envelope and split paths and changes the mode only between
    blocks; LATENCY-0's instrument is still a byte-exact prefix."""
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    i_ps, i_st = tail.find("PRESENT-SCALE-0 (appended)"), tail.find("PRESENT-STRETCH-0 and ALLOC-REUSE-0 (appended)")
    if i_ps < 0 or i_st < i_ps:
        raise Red("the stretch/allocation section is not appended after PRESENT-SCALE-0's")
    sect = tail[i_st:]
    pres = src_span(sect, "fn present(&mut self", "fn flush(&mut self)")
    order = [pres.find(t) for t in ("GetDC(", "SetStretchBltMode(hdc, self.mode)", "SetBrushOrgEx(hdc, 0, 0,", "StretchDIBits(",
                                    "let ready = qpc();", "(self.flush_fn)();", "Some(qpc())", "ReleaseDC(")]
    if -1 in order or order != sorted(order):
        raise Red("the stretch surface's present is not LATENCY-0's present_once with the mode and brush origin set before the blit")
    if "StretchDIBits(hdc, 0, 0, (W as i32) / 2, (H as i32) / 2, 0, 0, W as i32, H as i32," not in pres:
        raise Red("the stretch surface does not blit into the fixed half-size destination")
    win = src_span(sect, "pub fn presentstretch_window(", "pub fn allocreuse_window(")
    if "AdjustWindowRect(&mut r, WS_OVERLAPPEDWINDOW, 0)" not in win or "lpfn_wnd_proc: Some(wnd_proc)" not in sect:
        raise Red("the stretch window is not the plain overlapped window sized to a 960x540 client with LATENCY-0's procedure")
    rs = read(os.path.join(SHELL, "presentstretch.rs")).decode("utf-8")
    court = src_span(rs, "pub fn court<", "fn pct_json(")
    if ("arm_composite(&inputs[k].scene, Arm::Production)" not in court or "arm_composite_marked(&inputs[k].scene, Arm::Production, &mut m)" not in court
            or "if effective != MODES[mi]" not in court or "if client != DESTINATION" not in court):
        raise Red("the court does not use FRAME-SPLIT-0's paths with a verified mode and client area")
    timed = court[court.index("let t0 = s.ticks();"):court.index("if comp != expected[k]")]
    if "set_mode" in timed or "frame_digest" in timed or "sha256" in timed:
        raise Red("the timed interval holds a mode change or hashing")
    return ("only the stretch mode changes: the present is LATENCY-0's present_once with SetStretchBltMode and SetBrushOrgEx "
            "before the blit into the fixed 960x540 destination; the window is the plain overlapped window with LATENCY-0's "
            "procedure; the court uses FRAME-SPLIT-0's envelope and split paths, verifies the mode and the client area, and "
            "changes the mode only between blocks; LATENCY-0's instrument is still a byte-exact prefix")


def allocreuse_fence():
    """Only the buffers' lifetime changes: the reuse path makes the marked mirror's calls in its order with the same five
    marks into persistent buffers, `to_blit_into` is `to_blit`'s transform, the window and surface are FRAME-SPLIT-0's,
    and every composite and blit buffer is checked after its sample."""
    pr = read(os.path.join(SHELL, "present.rs")).decode("utf-8")
    mirror = src_span(pr, "pub fn arm_composite_marked<", "\n}\n")
    reuse = src_span(pr, "pub fn arm_composite_reuse_marked<", "\n}\n")
    calls = ["strips(&mut", "m.mark();", ".frame(&", "m.mark();", "blocked_floor(&scene.floor)", "m.mark();", "emit_threaded(", "m.mark();", "hud::overlay(", "m.mark();"]

    def ordered(body):
        pos, out = 0, []
        for c in calls:
            i = body.find(c, pos)
            if i < 0:
                return False
            pos = i + len(c)
        return True

    if not ordered(mirror) or not ordered(reuse) or reuse.count("m.mark();") != 5:
        raise Red("the reuse path does not make the marked mirror's calls in its order with the same five marks")
    if "fast::PROD_THREADS" not in reuse or "vec![" in reuse or "Vec::with_capacity" in reuse:
        raise Red("the reuse path allocates, or is not the production arm")
    tb, tbi = src_span(pr, "pub fn to_blit(", "\n}\n"), src_span(pr, "pub fn to_blit_into(", "\n}\n")
    for line in ("out[i * 3] = rgb[i * 3 + 2];", "out[i * 3 + 1] = rgb[i * 3 + 1];", "out[i * 3 + 2] = rgb[i * 3];"):
        if line not in tb or line not in tbi:
            raise Red("to_blit_into is not to_blit's transform")
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    win = src_span(w32.decode("utf-8"), "pub fn allocreuse_window(", "\n}\n")
    if "CW_USEDEFAULT, CW_USEDEFAULT," not in win or "(W as i32) / 2 + 16, (H as i32) / 2 + 39" not in win or "GdiSurface {" not in win:
        raise Red("the allocation court does not run in FRAME-SPLIT-0's window over LATENCY-1R's GDI surface")
    rs = read(os.path.join(SHELL, "allocreuse.rs")).decode("utf-8")
    court = src_span(rs, "pub fn court(", "fn pct_json(")
    if ("bufs.pixels != expected[k] || bufs.bgr != expected_bgr[k]" not in court or "comp != expected[k] || bgr != expected_bgr[k]" not in court
            or "let bounds = [t0, t[0], t[1], t[2], t[3], t[4], t_bgr, t1];" not in court):
        raise Red("the court does not check both variants' bytes after every sample, or its phases are not contiguous")
    return ("only the buffers' lifetime changes: the reuse path makes the marked mirror's calls in its order with the same "
            "five marks into persistent buffers and allocates none of them (the floor swizzle stays fast.rs's, fresh in both); "
            "to_blit_into is to_blit's transform; the court runs in "
            "FRAME-SPLIT-0's window over LATENCY-1R's GDI surface and checks both variants' composite and blit bytes after "
            "every sample; LATENCY-0's instrument is still a byte-exact prefix")


# ------------------------------------------------------------------ ALLOC-REUSE-1 and HOST-STATE-0
# the fresh reference's source, pinned: ALLOC-REUSE-1 keeps it as the frozen differential oracle, never rewritten
FRESH_REFERENCE_SHA256 = {
    ("kernel/fast.rs", "pub fn render(scene: &Scene)"): "6f9b5c0b7fb32a06cd4cdb2da06921908943a20032b842b40411c75c775e41bf",
    ("shell/present.rs", "pub fn arm_composite(scene"): "b8d57e860fe3d9ef6d27b9f5ac8e273e4b137137438f4e87f410cc02e411a118",
    ("shell/present.rs", "pub fn to_blit(rgb"): "35596a52318218c937380673fabbeb4e1aa4b08710efa7537919f9b4b1fa08cd",
    ("shell/present.rs", "pub fn compose_frame("): "a353608befb32a4af06ca7a4bfc816e5c62bf1884bd2dad755acb3fb9f407446",
}
# HOST-STATE-0 records and never controls: none of these may appear in its source
HOSTSTATE_FORBIDDEN = ("SetPriorityClass", "SetProcessAffinityMask", "SetThreadPriority", "SetThreadAffinityMask",
                       "SetThreadExecutionState", "PowerSetActiveScheme", "SetSystemPowerState", "SetProcessPriorityBoost",
                       "timeBeginPeriod", "NtSetTimerResolution", "SetProcessWorkingSetSize", "/setactive", "/change",
                       "/hibernate", "open(", ".write(")


def allocreuse1_preregistered():
    """ALLOC-REUSE-1's method is locked before any host number: an entry contract (no shipped window changes), the fresh
    path the frozen reference, correctness first over corpus + adversarial + session from poisoned buffers in three
    orders, then the same-run ABBA p99 rule with its 50 permille adoption margin, ADOPT only when the run and --confirm
    both pass. The code's constants must equal the registered ones."""
    e = locked_entry("ALLOC-REUSE-1", {
        "an entry contract, not a shipped-window change": ("hyp", ("entry contract", "run renders once", "playback-window pre-renders", "never deleted or rewritten")),
        "the fresh path is the frozen reference": ("hyp", ("frozen reference and differential oracle",)),
        "correctness first: corpus, adversarial, session, poisoned, three orders": ("succ", ("correctness first", "poisoned", "adversarial witness cameras", "three orders", "byte for byte", "no buffer replaced")),
        "same-run ABBA, warm-up, 1000 per cell": ("succ", ("interleaved abba in the same run", "10 warm-up rounds", "1000 samples per cell")),
        "the p99 rule and its adoption margin": ("succ", ("p99(reused) <= 950 permille x p99(fresh)", "adoption margin", "not a measurement uncertainty", "adopt iff the run and its --confirm run both read performance pass")),
        "what ADOPT and REJECT do": ("succ", ("call-site fence", "unused candidate")),
        "no p50, cross-run or one-run decision; no shipped claim": ("fail", ("off the p50s", "sealed in another run", "shipped window got faster", "deleting or rewriting the fresh reference")),
        "--confirm and the LATENCY-0 prefix": ("fail", ("--confirm", "byte-exact prefix")),
        "scope: a loop contract, the tail shown, host state never read": ("lims", ("entry contract for a render loop", "10th-largest sample", "host-state-0", "never read by the rule")),
    })
    import allocreuse1 as AR1
    rs = read(os.path.join(SHELL, "allocreuse1.rs")).decode("utf-8")
    for const in ("pub const WARM_ROUNDS: usize = 10;", "pub const DEFAULT_PER_CELL: usize = 1000;", "pub const TAIL: usize = 12;"):
        if const not in rs:
            raise Red("the court's constants are not the registered ones: %s is missing" % const)
    if (AR1.REQUIRED_PER_CELL, AR1.ADOPT_P99_PERMILLE, AR1.WARM_ROUNDS, AR1.TAIL, AR1.VARIANTS) != (1000, 950, 10, 12, ("fresh", "reused")):
        raise Red("the sealer's constants are not the registered ones")
    return ("ALLOC-REUSE-1's method is locked before any host number: an entry contract for a render loop (no shipped window "
            "changes; the fresh path stays the frozen reference); correctness first over the corpus, the adversarial cameras "
            "and the sealed session from poisoned buffers in three orders; then fresh and reused ABBA in the same run, 10 "
            "warm-up rounds, 1000 samples per cell; PERFORMANCE PASS iff p99(reused) <= 950 permille of p99(fresh) (an "
            "adoption margin, not an uncertainty); ADOPT only if the run and --confirm both pass; the code's constants equal "
            "the registered ones; hash-locked %s" % e["chain_hash"][:8])


def _loop_cases_file() -> tuple[str, dict]:
    """The correctness court's cases: every corpus scene x its tile sets (with the goldens) and the adversarial cameras."""
    c = corpus()
    goldens = {}
    for _name, sc in c["scenes"].items():
        x, z, f = sc["camera"]
        for tiles, g in sc["witnesses"].items():
            goldens[(sc["level"], tiles, "%d,%d,%s" % (x, z, f))] = (g["frame"], g["pixels"])
    lines = []
    for (lvl, tiles, cam) in _g1_cases():
        gf, gp = goldens.get((lvl, tiles, cam), ("-", "-"))
        lines.append("\t".join(["%s/%s@%s" % (lvl, tiles, cam), os.path.join(ORACLE, "levels", lvl + ".lvl"),
                                os.path.join(ORACLE, "tiles", tiles + ".tiles"), cam, gf, gp]))
    path = os.path.join(BUILD, "loop-equiv-cases.tsv")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path, goldens


def allocreuse1_equiv():
    """ALLOC-REUSE-1's correctness court: one LoopRenderer, its byte buffers poisoned first, renders every corpus scene x
    tile set (goldens), every adversarial camera and every sealed session frame, forward, reverse and zigzag; each render
    equals the fresh reference byte for byte and no buffer is replaced. PLANTS: a renderer that skips the pixel pass on
    alternate renders (stale pixels) is caught; a replaced buffer is caught."""
    need_rustc()
    if SHELL_EXE is None:
        raise Red("the shell was not built")
    path, goldens = _loop_cases_file()
    n_file = len(open(path, encoding="utf-8").read().strip().splitlines())
    base = [SHELL_EXE, "loop-equiv", "--cases", path, "--session", SESSIONWALK_DEMO]
    cp = subprocess.run(base, capture_output=True, text=True, cwd=ROOT)
    m = re.search(r"loop-equiv OK cases (\d+) goldens (\d+) orders 3 renders (\d+) buffers persistent", cp.stdout)
    if cp.returncode != 0 or not m:
        raise Red("the loop renderer is not byte-identical to the fresh path: " + (cp.stderr.strip() or cp.stdout.strip())[-300:])
    cases, gold, renders = int(m.group(1)), int(m.group(2)), int(m.group(3))
    session_lines = [ln for ln in cp.stdout.splitlines() if ln.startswith("case session:")]
    if cases != n_file + len(session_lines) or not session_lines or renders != 3 * cases:
        raise Red("the correctness court did not render every case in all three orders")
    corpus_lines = 0
    for ln in cp.stdout.splitlines():
        parts = ln.split()
        if len(parts) == 6 and parts[0] == "case" and not parts[1].startswith("session:"):
            lvl, rest = parts[1].split("/", 1)
            tiles, cam = rest.split("@")
            g = goldens.get((lvl, tiles, cam))
            if g is not None:
                corpus_lines += 1
                if (parts[3], parts[5]) != g:
                    raise Red("the loop's printed identities are not the goldens on %s" % parts[1])
    if corpus_lines != len(goldens) or gold != len(goldens) + len(session_lines):
        raise Red("not every golden was checked")
    for plant, code in (("stale", "LOOP-EQUIV"), ("realloc", "LOOP-PERSIST")):
        pp = subprocess.run(base + ["--plant", plant], capture_output=True, text=True, cwd=ROOT)
        if pp.returncode == 0 or code not in pp.stderr:
            raise Red("PLANT %s: the correctness court did not refuse with %s" % (plant, code))
    return ("one LoopRenderer, its byte buffers poisoned first, renders %d cases (every corpus scene x tile set with its goldens, "
            "the adversarial witness cameras, the %d sealed session frames) forward, reverse and zigzag — %d renders, each one's "
            "index frame, viewport, composite and blit byte-identical to the fresh reference, the corpus's frame digests and pixel "
            "shas and the session's witnesses reproduced (%d goldens), no buffer ever replaced; PLANTS: skipping the pixel pass on "
            "alternate renders (LOOP-EQUIV) and replacing a buffer (LOOP-PERSIST) are both caught"
            % (cases, len(session_lines), renders, gold))


def _ar1_raw(f99, r99, n=1000, f50=16000, r50=15000, **over):
    def var(p50, p99):
        t = [p99 + 400 - 20 * i for i in range(12)][:min(12, n)]
        return {"envelope": {"render_us": {"p50": p50, "p95": p99 - 200, "p99": p99, "max": t[0]},
                             "present_us": {"p50": 8000, "p95": 11000, "p99": 12000, "max": 13000}, "samples": n},
                "tail_render_us": t}
    d = {"variants": {"fresh": var(f50, f99), "reused": var(r50, r99)}, "block_order": "ABBA", "warm_rounds": 10,
         "refresh_period_us": 13400, "sequence_frames": 4, "samples_per_cell": n, "production_threads": 8,
         "phase_origin": "locked", "persistent_buffers": 4, "reuse_renders": n + 14}
    d.update(over)
    return {"name": "verdandi-allocreuse1", "provenance": {"tool": "synthetic", "unix_seconds": 0}, "data": d}


def allocreuse1_sealer():
    """The adoption sealer, with synthetic runs: PERFORMANCE PASS exactly at p99(reused) = 950 permille of p99(fresh) and
    FAIL one microsecond above; the p50s never decide; ADOPT only when a run and its confirmation both pass; a run that
    is not 1000 samples per cell, not ABBA, not warmed up, or with a malformed tail is refused."""
    import allocreuse1 as AR1
    cases = {
        AR1.PASS: _ar1_raw(20000, 19000),                          # exactly 950 permille
        AR1.FAIL: _ar1_raw(20000, 19001),                          # one microsecond over
    }
    diag_sealer_cases(AR1, "seal_allocreuse1", "ALLOC-REUSE-1", cases,
                      [(_ar1_raw(20000, 18000, n=300), "300 samples per cell"),
                       (_ar1_raw(20000, 18000, n=999), "999 samples per cell"),
                       (_ar1_raw(20000, 18000, block_order="AABB"), "another block order"),
                       (_ar1_raw(20000, 18000, warm_rounds=5), "another warm-up"),
                       (_ar1_raw(20000, 18000, reuse_renders=500), "a loop that did not render every sample")])
    bad_tail = _ar1_raw(20000, 18000)
    bad_tail["data"]["variants"]["reused"]["tail_render_us"] = list(reversed(bad_tail["data"]["variants"]["reused"]["tail_render_us"]))
    try:
        AR1.seal_allocreuse1(bad_tail, json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"],
                             "gate", {"path": "synthetic"}, {"rustc": "gate"})
        raise Red("the sealer accepted a tail that is not largest-first")
    except AR1.Refuse:
        pass
    # the p50s never decide: a far cheaper reused p50 with a failing p99 fails; a dearer reused p50 with a passing p99 passes
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    if AR1.seal_allocreuse1(_ar1_raw(20000, 19500, r50=9000), reg, "gate", {}, {})[1] != AR1.FAIL or \
            AR1.seal_allocreuse1(_ar1_raw(20000, 18000, r50=17000), reg, "gate", {}, {})[1] != AR1.PASS:
        raise Red("a p50 moved the performance label")
    table = {(AR1.PASS, AR1.PASS): "ADOPT", (AR1.PASS, AR1.FAIL): "REJECT", (AR1.FAIL, AR1.PASS): "REJECT", (AR1.FAIL, AR1.FAIL): "REJECT"}
    for (a, b), want in table.items():
        if AR1.adoption(a, b) != want:
            raise Red("the adoption rule reads %s for %s then %s" % (AR1.adoption(a, b), a, b))
        run2 = _ar1_raw(20000, 19000) if b == AR1.PASS else _ar1_raw(20000, 19500)
        rec, _ = AR1.seal_allocreuse1(run2, reg, "gate", {}, {}, confirm_of={"of": "synthetic", "chain_hash": "0" * 64, "original_label": a})
        envelope.validate(rec)
        if ("ADOPTION: %s" % want) not in rec["reading"] or "adoption" in rec["data"]:
            raise Red("the confirmation record does not state %s in its reading (and only there)" % want)
        if rec["provenance"]["host_state_preregistered"]["chain_hash"] != reg["HOST-STATE-0"]["chain_hash"]:
            raise Red("the record does not cite HOST-STATE-0")
    return ("verify/allocreuse1.py, driven with synthetic runs: PERFORMANCE PASS exactly at p99(reused) = 950 permille of "
            "p99(fresh) and FAIL one microsecond above; the p50s never move the label; ADOPT only for PASS then PASS, REJECT "
            "for the other three; the adoption is stated in the confirmation's reading, never stored as data; 300 or 999 "
            "samples per cell, another block order or warm-up, an unrendered sample or a malformed tail are refused; records "
            "cite ALLOC-REUSE-1 and HOST-STATE-0 and pass the firewall")


def allocreuse1_court():
    """The SAME adoption court the host window runs, headless over the mock: witnesses first (the poisoned loop renderer
    reproduces the fresh index frame, composite and blit), 10 warm-up rounds, fresh and reused ABBA, the buffers
    persistent throughout. Under the mock both variants take the same ticks, so the rule reads PERFORMANCE FAIL (1000
    permille). PLANTS: a tampered witness, a mid-court close and a replaced buffer each refuse with no record."""
    import allocreuse1 as AR1
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]

    def check(raw):
        d = raw["data"]
        if d["samples_per_cell"] != 2 or d["warm_rounds"] != 10 or d["reuse_renders"] < 2 + 10 + 4:
            raise Red("the court did not render the witnesses, the warm-up and 2 samples per cell through the loop")
        rec, label = AR1.seal_allocreuse1(raw, reg, "gate-mock", {"path": "workshop/attest/sessionwalk-demo.json"},
                                          {"rustc": "gate"}, required_per_cell=2)
        envelope.validate(rec)
        if label != AR1.FAIL:
            raise Red("the mock adoption court read %r, not %r" % (label, AR1.FAIL))

    diag_court("allocreuse1", "2", "allocreuse1 court OK",
               [("witness", "ALLOCREUSE1-WITNESS"), ("close", "ALLOCREUSE1-CLOSED"), ("persist", "ALLOCREUSE1-PERSIST")], check)
    return ("the ALLOC-REUSE-1 court runs headless over the mock surface on the sealed session: witnesses first (the poisoned "
            "loop renderer reproduces the fresh index frame, composite and blit of every sealed frame), 10 warm-up rounds, "
            "fresh and reused ABBA, the loop's buffers persistent throughout; its raw record seals and reads PERFORMANCE FAIL "
            "under the mock (equal ticks, 1000 permille); PLANTS: a tampered witness (ALLOCREUSE1-WITNESS), a mid-court close "
            "(ALLOCREUSE1-CLOSED) and a replaced buffer (ALLOCREUSE1-PERSIST) each refuse with no record")


def allocreuse1_fence():
    """Only the buffers' lifetime changes, and the fresh reference stays frozen: LoopRenderer makes fast::render's calls
    in fast::render's order and then the HUD, into buffers it allocates only in new(); its blit is to_blit_into; the
    fresh reference's source is pinned; the court runs in FRAME-SPLIT-0's window with the locked phase origin and
    nothing but rendering and the blit inside its interval; LATENCY-0's instrument is still a byte-exact prefix. (Who
    may render per frame, and through what, is allocreuse1-lock's since the ADOPT.)"""
    pr = read(os.path.join(SHELL, "present.rs")).decode("utf-8")
    impl = src_span(pr, "impl LoopRenderer {", "\n}\n")
    vp = src_span(impl, "pub fn viewport(&mut self", "pub fn overlay(")
    fr = src_span(read(os.path.join(KERNEL, "fast.rs")).decode("utf-8"), "pub fn render(scene: &Scene)", "\n}\n")

    def order(body, calls):
        pos = []
        for c in calls:
            i = body.find(c)
            if i < 0:
                return None
            pos.append(i)
        return pos == sorted(pos)

    if not order(fr, ["scene.strips(", "scene.frame(", "blocked_floor(", "emit_threaded(", "PROD_THREADS"]) or \
            not order(vp, ["scene.strips(&mut self.b.strips);", "scene.frame(&self.b.strips, &mut self.b.frame);",
                           "fast::blocked_floor(&scene.floor)",
                           "fast::emit_threaded(scene, &self.b.strips, &self.b.frame, &mut self.b.pixels, &floor, fast::PROD_THREADS);"]):
        raise Red("the loop renderer's viewport does not make fast::render's calls in fast::render's order")
    if "hud::overlay(scene, &self.b.strips, &mut self.b.pixels);" not in src_span(impl, "pub fn overlay(", "pub fn render("):
        raise Red("the loop renderer's overlay is not the HUD over its own strips and pixels")
    rend = src_span(impl, "pub fn render(&mut self", "pub fn blit(")
    if not order(rend, ["self.viewport(scene);", "self.overlay(scene)"]) or rend.count("self.") != 2:
        raise Red("the loop renderer's render is not exactly its viewport then its overlay")
    if "to_blit_into(&self.b.pixels, &mut self.b.bgr);" not in src_span(impl, "pub fn blit(", "pub fn composite("):
        raise Red("the loop renderer's blit is not to_blit_into into its own BGR buffer")
    body = impl.replace(src_span(impl, "pub fn new()", "pub fn viewport("), "")
    for alloc in ("vec![", "Vec::with_capacity", "Vec::new", ".to_vec()", ".clone()", "to_blit(", "Box::new", "String::"):
        if alloc in body:
            raise Red("the loop renderer allocates outside new(): %s" % alloc)
    for (path, start), want in FRESH_REFERENCE_SHA256.items():
        if sha256(src_span(read(os.path.join(ROOT, path)).decode("utf-8"), start, "\n}\n").encode("utf-8")) != want:
            raise Red("the fresh reference was rewritten: %s in %s" % (start, path))
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    i0, i1 = tail.find("PRESENT-STRETCH-0 and ALLOC-REUSE-0 (appended)"), tail.find("ALLOC-REUSE-1 (appended)")
    if i0 < 0 or i1 < i0:
        raise Red("the ALLOC-REUSE-1 section is not appended after ALLOC-REUSE-0's")
    win = src_span(tail[i1:], "pub fn allocreuse1_window(", "\n}\n")
    if ("CW_USEDEFAULT, CW_USEDEFAULT," not in win or "(W as i32) / 2 + 16, (H as i32) / 2 + 39" not in win or "GdiSurface {" not in win
            or "crate::allocreuse1::court(&mut surf, &inputs, per_cell, false)" not in win):
        raise Red("the adoption court does not run in FRAME-SPLIT-0's window over LATENCY-1R's GDI surface, unplanted")
    rs = read(os.path.join(SHELL, "allocreuse1.rs")).decode("utf-8")
    court = src_span(rs, "pub fn court(", "fn pct_json(")
    if "s.flush(); // the locked phase origin\n            let t0 = s.ticks();" not in court:
        raise Red("the adoption court does not start each sample at the locked phase origin")
    fresh = src_span(court, "// FRESH", "let t = s.present(&bgr);")
    reuse = src_span(court, "// REUSED", "let t = s.present(lr.blit());")
    for b in (fresh, reuse):
        for bad in ("sha256", "frame_digest", "identity", "!=", "poison"):
            if bad in b:
                raise Red("the timed interval holds %s" % bad)
    if "arm_composite(&inputs[k].scene, Arm::Production).1" not in fresh or "to_blit(&comp)" not in fresh or \
            "lr.render(&inputs[k].scene);" not in reuse:
        raise Red("the two cells are not the fresh reference and the loop entry")
    return ("only the buffers' lifetime changes and the fresh reference stays frozen: LoopRenderer makes fast::render's calls "
            "in fast::render's order and then the HUD into buffers it allocates only in new(), its render is exactly viewport "
            "then overlay, its blit is to_blit_into; the fresh reference's source (fast::render, arm_composite, to_blit, "
            "compose_frame) is pinned; the court runs in FRAME-SPLIT-0's window over LATENCY-1R's GDI surface with the "
            "locked phase origin and only rendering and the blit inside its interval; LATENCY-0's instrument is still a "
            "byte-exact prefix")


# ALLOC-REUSE-1 LOCK: the fresh render entries' call sites, pinned per shell file. They are the frozen reference and
# the courts that measure against it (present.rs's definitions, run's single compose, playback's owned pre-render, the
# court modules, LATENCY-0's prefix). Any new site is a loop that bypasses the adopted LoopRenderer, or a new reference
# site that must be re-pinned on purpose.
FRESH_ENTRY_TOKENS = ("compose_frame(", "arm_composite(", "arm_composite_marked(", "arm_composite_reuse_marked(",
                      "fast::render(", "fast::emit_threaded(", "fast::emit(", "to_blit(")
FRESH_ENTRY_SITES = {
    "allocreuse.rs": {"arm_composite(": 2, "arm_composite_marked(": 2, "arm_composite_reuse_marked(": 3, "to_blit(": 2},
    "allocreuse1.rs": {"arm_composite(": 2, "fast::render(": 1, "to_blit(": 3},
    "framesplit.rs": {"arm_composite(": 2, "arm_composite_marked(": 2, "to_blit(": 1},
    "latency1r.rs": {"arm_composite(": 3, "to_blit(": 1},
    "main.rs": {"compose_frame(": 1, "to_blit(": 1},
    "playback.rs": {"compose_frame(": 2, "to_blit(": 2},
    "present.rs": {"compose_frame(": 1, "arm_composite(": 2, "fast::render(": 2, "fast::emit_threaded(": 3, "fast::emit(": 2, "to_blit(": 6},
    "presentscale.rs": {"arm_composite(": 2, "arm_composite_marked(": 2, "to_blit(": 1},
    "presentstretch.rs": {"arm_composite(": 2, "arm_composite_marked(": 2, "to_blit(": 1},
    # re-pinned on purpose with PRESENT-EXACT-0: its witnesses compare the loop against the fresh reference
    "presentexact.rs": {"arm_composite(": 1, "to_blit(": 1},
    # re-pinned on purpose with PRESENT-EXACT-0 LOCK: the presenter's blit-hash guard on its pre-rendered frames
    "win32.rs": {"to_blit(": 4},
}
# the adoption evidence, sealed on the owner's host (committed there; this checkout may not carry it)
ALLOCREUSE1_RECORDS = {"allocreuse1-DANIELDILLBERG.json": "8036e65488f168b87cc3cf26798d25aed0c2b9fe249118c30a4b175258505b96",
                       "allocreuse1-confirm-DANIELDILLBERG.json": "256e8a6e8d8b07e59a92b16ee1303021c1a526f93aac095a08adf32760e0fc04"}


def allocreuse1_lock():
    """ALLOC-REUSE-1 LOCK: the persistent-buffer LoopRenderer is ADOPTED as the production entry for in-loop rendering.
    Every call site of a fresh render entry in the shell is pinned (a new one is a loop bypassing the entry, or a new
    reference site to re-pin on purpose); the renderer declares its adoption; the fresh reference stays pinned by
    allocreuse1-fence. Where the checkout carries the host records, they are the pinned ones, both read PERFORMANCE PASS,
    the confirmation cites the first, and the adoption reads ADOPT."""
    import allocreuse1 as AR1
    got = {}
    for fn in sorted(os.listdir(SHELL)):
        if fn.endswith(".rs"):
            src = read(os.path.join(SHELL, fn)).decode("utf-8")
            c = {t: src.count(t) for t in FRESH_ENTRY_TOKENS if src.count(t)}
            if c:
                got[fn] = c
    if got != FRESH_ENTRY_SITES:
        moved = sorted(set(got) ^ set(FRESH_ENTRY_SITES) | {f for f in set(got) & set(FRESH_ENTRY_SITES) if got[f] != FRESH_ENTRY_SITES[f]})
        raise Red("a fresh render entry's call sites changed in %s: in-loop rendering enters through the adopted LoopRenderer; "
                  "a new reference site is re-pinned on purpose" % ", ".join(moved))
    pr = read(os.path.join(SHELL, "present.rs")).decode("utf-8")
    doc = pr[pr.index("/// ALLOC-REUSE-1: the render-loop entry"):pr.index("pub struct LoopRenderer {")]
    if "ADOPTED (ALLOC-REUSE-1 LOCK)" not in doc or "production entry for in-loop rendering" not in doc:
        raise Red("the LoopRenderer does not declare its adoption")
    attest = os.path.join(ROOT, "shell", "attest")
    present = [f for f in ALLOCREUSE1_RECORDS if os.path.exists(os.path.join(attest, f))]
    if present:
        if len(present) != 2:
            raise Red("the checkout carries one of the two adoption records but not the other")
        first = envelope.read(os.path.join(attest, "allocreuse1-DANIELDILLBERG.json"))
        conf = envelope.read(os.path.join(attest, "allocreuse1-confirm-DANIELDILLBERG.json"))
        if (first["chain_hash"], conf["chain_hash"]) != tuple(ALLOCREUSE1_RECORDS.values()):
            raise Red("the adoption records are not the pinned ones")
        l1, _ = AR1.performance(first["data"]["derived"]["variants"])
        l2, _ = AR1.performance(conf["data"]["derived"]["variants"])
        if conf["provenance"]["confirms"]["chain_hash"] != first["chain_hash"] or AR1.adoption(l1, l2) != "ADOPT" \
                or "ADOPTION: ADOPT" not in conf["reading"]:
            raise Red("the adoption records do not read ADOPT")
        evidence = "the two host records are in this checkout, are the pinned ones, both read PERFORMANCE PASS, and read ADOPT"
    else:
        evidence = ("the two host records are cited by hash (%s, %s); this checkout does not carry them"
                    % tuple(h[:8] for h in ALLOCREUSE1_RECORDS.values()))
    return ("ALLOC-REUSE-1 LOCK: the persistent-buffer LoopRenderer is the production entry for in-loop rendering and says so; "
            "every fresh render entry's call site in the shell is pinned (%d files), so a new loop cannot render around the "
            "entry and a new reference site is re-pinned on purpose; the fresh reference stays pinned (allocreuse1-fence); %s"
            % (len(FRESH_ENTRY_SITES), evidence))


def hoststate_preregistered():
    """HOST-STATE-0's method is locked: record, never control; every registered field or an unavailable marker; integers
    and strings only; capture_safe never raises; before and after a window court; association, never cause."""
    e = locked_entry("HOST-STATE-0", {
        "recorded, never controlled; association only": ("hyp", ("recorded, never controlled", "association only", "changes nothing on the host")),
        "the snapshot's shape": ("succ", ("every registered field in order", "integers and strings only", "thermal is declared not captured")),
        "never blocks; before and after; writes nothing": ("succ", ("capture_safe never raises", "never blocks a court", "just before and one just after", "writes nothing")),
        "no control, no rule reads it, no cause": ("fail", ("any control of the host", "any rule reading host state", "association, never cause", "reported mhz as a measured frequency")),
        "scope: as reported; no thermal; never explained": ("lims", ("as it reports it", "thermal state is not captured", "never explained")),
    })
    import hoststate as HS
    if (HS.FIELDS, HS.LOAD_WINDOW_MS) != (("cpu", "power", "load", "memory", "process", "display", "uptime", "thermal"), 1000):
        raise Red("the recorder's fields or load window are not the registered ones")
    return ("HOST-STATE-0's method is locked: the host's state is recorded, never controlled — every registered field in "
            "order (cpu, power, load, memory, process, display, uptime, thermal), each captured or marked unavailable with its "
            "reason, integers and strings only; capture_safe never raises, so recording never blocks a court; one snapshot "
            "just before and one just after a window court; association, never cause; the code's fields and 1000 ms load "
            "window equal the registered ones; hash-locked %s" % e["chain_hash"][:8])


def hoststate_record():
    """The recorder on this gate: off Windows every field is unavailable and nothing raises; the Windows capture path,
    run where its APIs are absent, degrades field by field to unavailable; a float, a boolean, a missing field or a
    raising capture becomes an unavailable snapshot, never an exception; a Windows-shaped snapshot validates; the
    source calls no control API and writes no file."""
    import hoststate as HS
    snap = HS.validate(HS.capture())
    if any(v != {"unavailable": HS.NOT_WINDOWS} for k, v in snap["fields"].items() if k != "thermal") and os.name != "nt":
        raise Red("off Windows a field was captured or its marker is not the registered one")
    if snap["fields"]["thermal"] != {"unavailable": HS.THERMAL} or not isinstance(snap["unix_seconds"], int):
        raise Red("thermal is not declared not captured, or the time is not an integer")
    if os.name != "nt":
        forced = HS.validate(HS.capture(windows=True))
        if not all("unavailable" in v for v in forced["fields"].values()):
            raise Red("the Windows capture path did not degrade to unavailable where its APIs are absent")

    def boom():
        raise RuntimeError("planted capture failure")

    bad = [boom,
           lambda: dict(HS.capture(), unix_seconds=1.5),
           lambda: dict(HS.capture(), platform=True),
           lambda: {"hoststate": "HOST-STATE-0", "fields": {"cpu": {}}}]
    for fn in bad:
        s = HS.capture_safe(fn)
        if set(s) != {"hoststate", "version", "unavailable"}:
            raise Red("capture_safe let a bad snapshot through or raised")
    win = {"hoststate": "HOST-STATE-0", "version": 1, "unix_seconds": 1790000000, "platform": "win32", "fields": {
        "cpu": {"model": "synthetic CPU", "logical_processors": 16, "mhz": {"current_min": 3000, "current_median": 3600,
                "current_max": 4200, "max": 4200, "limit_min": 4200, "source": "synthetic"}},
        "power": {"ac_line_status": 1, "battery_flag": 128, "battery_percent": 255, "battery_saver": 0, "codes": "synthetic",
                  "plan": {"guid": "381b4222-f694-41f0-9685-ff5bb260df2e", "name": "Balanced"}},
        "load": {"cpu_busy_permille": 37, "window_ms": 1000, "source": "synthetic"},
        "memory": {"load_percent": 41, "total_mb": 32000, "available_mb": 18000},
        "process": {"priority_class": "0x20", "affinity_mask": "0xffff", "system_affinity_mask": "0xffff", "of": "synthetic"},
        "display": {"logical": [1920, 1080], "physical": [1920, 1080], "bits_per_pixel": 32, "vertical_refresh_hz": 75, "source": "synthetic"},
        "uptime": {"ms": 123456},
        "thermal": {"unavailable": HS.THERMAL}}}
    if HS.capture_safe(lambda: win) is not win:
        raise Red("a well-formed Windows snapshot did not validate")
    src = read(os.path.join(ROOT, "verify", "hoststate.py")).decode("utf-8")
    for tok in HOSTSTATE_FORBIDDEN:
        if tok in src:
            raise Red("HOST-STATE-0's source contains %r: it may record, never control or write" % tok)
    runs = re.findall(r"subprocess\.run\((\[[^\]]*\])", src)
    if runs != ['["powercfg", "/getactivescheme"]']:
        raise Red("HOST-STATE-0 runs a command other than the one query: %s" % runs)
    return ("verify/hoststate.py on this gate: off Windows every field is recorded unavailable with the registered marker "
            "and nothing raises; the Windows capture path, run where its APIs are absent, degrades field by field; a planted "
            "failure, a float, a boolean or a missing field becomes an unavailable snapshot, never an exception; a Windows-"
            "shaped snapshot validates; the source calls no control API, writes no file, and runs one command (powercfg "
            "/getactivescheme, a query)")


def hoststate_fence():
    """No rule reads host state and recording cannot block: the same ALLOC-REUSE-1 raw sealed with no probe and with two
    different host states gives the same label, the same derived numbers and the same reading; the rule takes only the
    derived variants; the host state is attached after the label and the adoption are fixed; host_run's probe is
    optional, taken through capture_safe just before and just after the window court, and the diagnostic sealers pass
    none."""
    import allocreuse1 as AR1
    import inspect
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    raw = _ar1_raw(20000, 19000)
    a = {"before": {"hoststate": "HOST-STATE-0", "version": 1, "unavailable": "A"}, "after": {"hoststate": "HOST-STATE-0", "version": 1, "unavailable": "A"}}
    b = {"before": {"hoststate": "HOST-STATE-0", "version": 1, "unavailable": "B, a wholly different host"}, "after": {"hoststate": "HOST-STATE-0", "version": 1, "unavailable": "B"}}
    outs = []
    for hs in (None, a, b):
        for conf in (None, {"of": "synthetic", "chain_hash": "0" * 64, "original_label": AR1.PASS}):
            rec, label = AR1.seal_allocreuse1(raw, reg, "gate", {}, {}, confirm_of=conf, host_state=hs)
            outs.append((conf is None, label, json.dumps(rec["data"]["derived"], sort_keys=True), rec["reading"]))
    if len({o for o in outs if o[0]}) != 1 or len({o for o in outs if not o[0]}) != 1:
        raise Red("the host state moved a label, a derived number or a reading")
    if list(inspect.signature(AR1.performance).parameters) != ["dv"] or list(inspect.signature(AR1.adoption).parameters) != ["first_label", "confirm_label"]:
        raise Red("the rule can receive more than the derived variants and the two labels")
    seal_src = inspect.getsource(AR1.seal_allocreuse1)
    i_rule, i_adopt, i_hs = seal_src.find("performance(dv)"), seal_src.find("adoption(confirm_of"), seal_src.find('data["host_state"] =')
    if min(i_rule, i_adopt, i_hs) < 0 or not (i_rule < i_adopt < i_hs):
        raise Red("the host state is not attached after the label and the adoption are fixed")
    dc = read(os.path.join(ROOT, "verify", "diagcommon.py")).decode("utf-8")
    hr = src_span(dc, "def host_run(", "\ndef ")
    if ("probe: dict | None = None" not in hr or hr.count("hoststate.capture_safe()") != 2 or "hoststate.capture()" in hr
            or not (hr.index('probe["before"]') < hr.index('f"{cmd}-window"') < hr.index('probe["after"]'))):
        raise Red("host_run's probe is not optional, not safe, or not taken just before and just after the window court")
    for sealer in ("presentstretch.py", "allocreuse.py"):
        s = read(os.path.join(ROOT, "verify", sealer)).decode("utf-8")
        if "probe=" in s:
            raise Red("%s passes a probe: the diagnostic courts' flow must not change" % sealer)
    return ("no rule reads host state and recording cannot block: one ALLOC-REUSE-1 raw sealed with no probe and with two "
            "different host states gives the same label, derived numbers and reading (run and confirmation alike); the rule "
            "takes only the derived variants and the adoption only the two labels; the host state is attached after both are "
            "fixed; host_run's probe is optional and taken through capture_safe just before and just after the window court; "
            "the diagnostic sealers pass none")


# ------------------------------------------------------------------ PRESENTATION-CHOICE-0 and PRESENT-EXACT-0
def presentationchoice_declared():
    """PRESENTATION-CHOICE-0 is a decision, hash-locked: the shell presents the certified composite 1:1 in a borderless
    window covering the 1920x1080 screen at (0,0); conformance is witnessed by the composed screen read back; LATENCY-0's
    frozen half-size windows are not changed to meet it."""
    e = locked_entry("PRESENTATION-CHOICE-0", {
        "a decision: the certified picture, 1:1, borderless": ("hyp", ("a decision, not a measurement", "the certified picture, 1:1", "borderless", "no new view law")),
        "what conforms, and its witness": ("succ", ("destination = source = 1920x1080", "no dpi virtualisation", "read back, equals the certified picture byte for byte")),
        "no scaling, no partial frame, frozen windows untouched": ("fail", ("partially visible frame", "reading this decision as a measurement", "latency-0's frozen windows")),
        "scope: a decision; the composed screen; one screen size": ("lims", ("semantic decision", "outside every witness", "1920x1080 screen at 100% scaling only")),
    })
    return ("PRESENTATION-CHOICE-0 is declared and hash-locked %s: the shell presents the certified 1920x1080 composite 1:1, "
            "no reduction by GDI or the kernel, in a borderless window covering the 1920x1080 screen at (0,0); an "
            "implementation conforms when the composed screen read back equals the certified picture byte for byte; "
            "LATENCY-0's frozen half-size windows are not changed to meet it; a decision, earning nothing until "
            "PRESENT-EXACT-0 witnesses an implementation" % e["chain_hash"][:8])


def presentexact_preregistered():
    """PRESENT-EXACT-0's method is locked before any host number: the call the only variable, the screen readback a
    hard gate, the same-run ABBA p99 rule with its 950 permille margin, SetDIBitsToDevice the default. The code's
    constants must equal the registered ones."""
    e = locked_entry("PRESENT-EXACT-0", {
        "one variable: the call; the composed-screen witness": ("hyp", ("one variable: the present call", "stretchdibits at 1:1", "setdibitstodevice", "composed screen", "neither call", "adopted looprenderer")),
        "the readback is a hard gate": ("succ", ("hard gate", "zero differing bytes", "read back white")),
        "same-run ABBA, warm-up, 1000 per cell": ("succ", ("interleaved abba in the same run", "10 warm-up rounds", "1000 samples per cell")),
        "the rule, its margin and the default": ("succ", ("950 permille", "adoption margin", "both runs read stretchdibits cheaper", "otherwise setdibitstodevice, the simpler semantics")),
        "no p50, cross-run or one-run decision; nothing inside the clock": ("fail", ("off the p50s", "sealed in another run", "readback or clearing inside the timed interval", "reach the eye unchanged")),
        "the LATENCY-0 prefix": ("fail", ("byte-exact prefix",)),
        "scope: before scan-out, the tail shown, host state beside": ("lims", ("before scan-out", "11th-largest sample", "host-state-0", "refuses rather than measuring around it")),
    })
    import presentexact as PX
    rs = read(os.path.join(SHELL, "presentexact.rs")).decode("utf-8")
    for const in ('pub const CALLS: [&str; 2] = ["stretchdibits", "setdibitstodevice"];', "pub const WARM_ROUNDS: usize = 10;",
                  "pub const DEFAULT_PER_CELL: usize = 1000;", "pub const TAIL: usize = 12;"):
        if const not in rs:
            raise Red("the court's constants are not the registered ones: %s is missing" % const)
    if (PX.REQUIRED_PER_CELL, PX.MARGIN_PERMILLE, PX.WARM_ROUNDS, PX.TAIL, PX.CALLS, PX.TARGET) != \
            (1000, 950, 10, 12, ("stretchdibits", "setdibitstodevice"), [1920, 1080]):
        raise Red("the sealer's constants are not the registered ones")
    return ("PRESENT-EXACT-0's method is locked before any host number: in a borderless 1920x1080 window at (0,0), DPI-aware, "
            "the present call is the only variable (StretchDIBits at 1:1 or SetDIBitsToDevice), frames through the adopted "
            "LoopRenderer; the composed screen read back equal to the certified picture, after a white clear read back, is a "
            "hard gate; then ABBA in the same run, 10 warm-up rounds, 1000 samples per cell; a call is cheaper only at <= 950 "
            "permille of the other's p99; StretchDIBits is adopted only if cheaper in both runs, else SetDIBitsToDevice; the "
            "code's constants equal the registered ones; hash-locked %s" % e["chain_hash"][:8])


def _px_raw(s99, d99, n=1000, s50=12000, d50=12000, frames=4, **over):
    def call(p50, p99):
        t = [p99 + 400 - 20 * i for i in range(12)][:min(12, n)]
        return {"envelope": {"render_us": {"p50": p50, "p95": p99 - 200, "p99": p99, "max": t[0]},
                             "call_us": {"p50": 2000, "p95": 2400, "p99": 2600, "max": 3000},
                             "present_us": {"p50": 8000, "p95": 11000, "p99": 12000, "max": 13000}, "samples": n},
                "tail_render_us": t}
    checks = 2 * frames + 2
    d = {"calls": {"stretchdibits": call(s50, s99), "setdibitstodevice": call(d50, d99)},
         "geometry": {"client": [1920, 1080], "origin": [0, 0], "screen_logical": [1920, 1080],
                      "screen_physical": [1920, 1080], "source": [1920, 1080]},
         "readback": {"frames": frames, "checks": checks, "bytes_compared": checks * 1920 * 1080 * 3, "mismatched_bytes": 0,
                      "method": "synthetic"},
         "block_order": "ABBA", "warm_rounds": 10, "refresh_period_us": 13400, "sequence_frames": frames,
         "samples_per_cell": n, "production_threads": 8, "phase_origin": "locked", "render_entry": "LoopRenderer",
         "loop_renders": 2 * (n + 10) + frames}
    for k, v in over.items():
        if k in ("geometry", "readback"):
            d[k] = dict(d[k], **v)
        else:
            d[k] = v
    return {"name": "verdandi-presentexact", "provenance": {"tool": "synthetic", "unix_seconds": 0}, "data": d}


def presentexact_sealer():
    """The implementation sealer, with synthetic runs: each call reads cheaper exactly at 950 permille of the other's
    p99 and NO MATERIAL DIFFERENCE one microsecond short; the p50s never decide; StretchDIBits is adopted only for
    cheaper-then-cheaper, SetDIBitsToDevice otherwise; a readback with one differing byte, another geometry, a short
    readback, another sample count, render entry or block order is refused."""
    import presentexact as PX
    cases = {PX.STRETCH: _px_raw(19000, 20000), PX.SETDIB: _px_raw(20000, 19000), PX.NEITHER: _px_raw(19001, 20000)}
    diag_sealer_cases(PX, "seal_presentexact", "PRESENT-EXACT-0", cases,
                      [(_px_raw(19000, 20000, readback={"mismatched_bytes": 1}), "a readback with one differing byte"),
                       (_px_raw(19000, 20000, readback={"checks": 9, "bytes_compared": 9 * 1920 * 1080 * 3}), "a short readback"),
                       (_px_raw(19000, 20000, geometry={"origin": [0, 39]}), "a client below a title bar"),
                       (_px_raw(19000, 20000, geometry={"screen_logical": [1536, 864]}), "a scaled screen"),
                       (_px_raw(19000, 20000, n=300), "300 samples per cell"),
                       (_px_raw(19000, 20000, render_entry="fresh"), "another render entry"),
                       (_px_raw(19000, 20000, block_order="AABB"), "another block order")])
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    if PX.seal_presentexact(_px_raw(19500, 20000, s50=9000), reg, "gate", {}, {})[1] != PX.NEITHER:
        raise Red("a p50 moved the label")
    for (a, b) in [(x, y) for x in (PX.STRETCH, PX.SETDIB, PX.NEITHER) for y in (PX.STRETCH, PX.SETDIB, PX.NEITHER)]:
        want = "STRETCHDIBITS" if (a, b) == (PX.STRETCH, PX.STRETCH) else "SETDIBITSTODEVICE"
        if PX.adoption(a, b) != want:
            raise Red("the adoption reads %s for %s then %s" % (PX.adoption(a, b), a, b))
    run2 = {PX.STRETCH: _px_raw(19000, 20000), PX.SETDIB: _px_raw(20000, 19000), PX.NEITHER: _px_raw(19001, 20000)}
    for first in (PX.STRETCH, PX.NEITHER):
        for second, raw in run2.items():
            rec, _ = PX.seal_presentexact(raw, reg, "gate", {}, {}, confirm_of={"of": "synthetic", "chain_hash": "0" * 64, "original_label": first})
            envelope.validate(rec)
            if ("ADOPTED CALL: %s" % PX.adoption(first, second)) not in rec["reading"] or "adopted" in json.dumps(rec["data"]).lower():
                raise Red("the confirmation does not state the adopted call in its reading (and only there)")
            if rec["provenance"]["presentation_choice"]["chain_hash"] != reg["PRESENTATION-CHOICE-0"]["chain_hash"] or \
                    rec["provenance"]["host_state_preregistered"]["chain_hash"] != reg["HOST-STATE-0"]["chain_hash"]:
                raise Red("the record does not cite PRESENTATION-CHOICE-0 and HOST-STATE-0")
    return ("verify/presentexact.py, driven with synthetic runs: STRETCHDIBITS CHEAPER and SETDIBITSTODEVICE CHEAPER fire "
            "exactly at 950 permille of the other call's p99, NO MATERIAL DIFFERENCE one microsecond short; the p50s never "
            "move the label; StretchDIBits is adopted only when both runs read it cheaper, SetDIBitsToDevice in the other "
            "eight cases, stated in the confirmation's reading only; one differing readback byte, a short readback, a "
            "client below a title bar, a scaled screen, 300 samples per cell, another render entry or block order are "
            "refused; records cite PRESENT-EXACT-0, PRESENTATION-CHOICE-0 and HOST-STATE-0")


def presentexact_court():
    """The SAME court the borderless host window runs, headless over a mock screen that holds what was last presented:
    the geometry verified, every sealed frame cleared, presented and read back under both calls, the court ABBA over
    the LoopRenderer, the last frame read back again. Under the mock both calls take the same ticks: NO MATERIAL
    DIFFERENCE. PLANTS: a tampered witness, a mid-court close, a client below a title bar, one byte changed on the way
    back, and a call that writes nothing each refuse with no record."""
    import presentexact as PX
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]

    def check(raw):
        d = raw["data"]
        if d["readback"]["checks"] != 10 or d["readback"]["mismatched_bytes"] != 0 or d["render_entry"] != "LoopRenderer":
            raise Red("the mock court did not read back every sealed frame and the closing frame under both calls")
        rec, label = PX.seal_presentexact(raw, reg, "gate-mock", {"path": "workshop/attest/sessionwalk-demo.json"},
                                          {"rustc": "gate"}, required_per_cell=2)
        envelope.validate(rec)
        if label != PX.NEITHER:
            raise Red("the mock court read %r, not %r" % (label, PX.NEITHER))

    diag_court("presentexact", "2", "presentexact court OK",
               [("witness", "PRESENTEXACT-WITNESS"), ("close", "PRESENTEXACT-CLOSED"), ("geometry", "PRESENTEXACT-GEOMETRY"),
                ("readback", "PRESENTEXACT-READBACK"), ("noop", "PRESENTEXACT-READBACK")], check)
    return ("the PRESENT-EXACT-0 court runs headless over a mock screen on the sealed session: the geometry verified, every "
            "sealed frame cleared to white, read back white, presented and read back equal under both calls (10 checks), the "
            "court ABBA over the adopted LoopRenderer, the last frame read back again; it seals and reads NO MATERIAL "
            "DIFFERENCE under the mock; PLANTS: a tampered witness, a mid-court close, a client below a title bar, one byte "
            "changed on the way back and a call that writes nothing each refuse with no record")


def presentexact_fence():
    """Only the call changes, and the witness sits outside the clock: the two presents are LATENCY-0's present_once shape
    with the 1:1 StretchDIBits or SetDIBitsToDevice as the one difference and no stretch mode touched; the window is a
    borderless topmost 1920x1080 popup at (0,0), made DPI-aware first; the clear is PatBlt and the readback a screen-DC
    BitBlt into a 24-bit top-down DIB; the timed interval holds only the loop render, its blit and the call; the
    readback and clear run only before and after the court; LATENCY-0's instrument is still a byte-exact prefix."""
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    i_ar1, i_px = tail.find("ALLOC-REUSE-1 (appended)"), tail.find("PRESENT-EXACT-0 (appended)")
    if i_ar1 < 0 or i_px < i_ar1:
        raise Red("the PRESENT-EXACT-0 section is not appended after ALLOC-REUSE-1's")
    sect = tail[i_px:]
    pres = src_span(sect, "fn present(&mut self", "fn flush(&mut self)")
    order = [pres.find(t) for t in ("GetDC(self.hwnd)", "if self.call == 0", "StretchDIBits(hdc, 0, 0, W as i32, H as i32, 0, 0, W as i32, H as i32,",
                                    "SetDIBitsToDevice(hdc, 0, 0, W as Dword, H as Dword, 0, 0, 0, H as Uint,", "let ready = qpc();",
                                    "(self.flush_fn)();", "Some(qpc())", "ReleaseDC(")]
    if -1 in order or order != sorted(order):
        raise Red("the exact surface's present is not present_once's shape with the 1:1 call as its one difference")
    if "SetStretchBltMode" in sect or "SetBrushOrgEx(" in sect:
        raise Red("the exact section touches the stretch mode: a second variable")
    if "PatBlt(hdc, 0, 0, W as i32, H as i32, WHITENESS)" not in src_span(sect, "fn clear(&mut self)", "fn readback(&mut self)"):
        raise Red("the clear is not a white PatBlt over the whole client")
    rb = src_span(sect, "fn readback(&mut self)", "fn geometry(&mut self)")
    for t in ("ClientToScreen(self.hwnd, &mut org)", "GetDC(std::ptr::null_mut())", "CreateDIBSection(screen, &hdr, DIB_RGB_COLORS",
              "let hdr = court_header();", "BitBlt(mem, 0, 0, W as i32, H as i32, screen, org.x, org.y, SRCCOPY)"):
        if t not in rb:
            raise Red("the readback is not a screen-DC BitBlt of the client into a 24-bit top-down DIB: %s" % t)
    win = src_span(sect, "pub fn presentexact_window(", "\n}\n")
    ew = src_span(sect, "fn exact_window(", "\n}\n")
    if ("CreateWindowExW(WS_EX_TOPMOST, class_name.as_ptr(), title_w.as_ptr(), WS_POPUP | WS_VISIBLE, 0, 0, W as i32, H as i32," not in ew
            or "lpfn_wnd_proc: Some(wnd_proc)" not in ew or win.find("SetProcessDPIAware()") < 0
            or not (0 <= win.find("SetProcessDPIAware()") < win.find("= exact_window(")) or "crate::presentexact::court(&mut surf, &inputs, per_cell)" not in win):
        raise Red("the window is not a DPI-aware, borderless, topmost 1920x1080 popup at (0,0) with LATENCY-0's procedure")
    rs = read(os.path.join(SHELL, "presentexact.rs")).decode("utf-8")
    court = src_span(rs, "pub fn court<", "fn pct_json(")
    timed = src_span(court, "let t0 = s.ticks();", "let presented = s.present(bgr);")
    for bad in ("readback", "clear", "witness_one", "sha256", "frame_digest", "set_call", "arm_composite", "to_blit("):
        if bad in timed:
            raise Red("the timed interval holds %s" % bad)
    if "lr.render(&inputs[k].scene);" not in timed or "let bgr = lr.blit();" not in timed:
        raise Red("the timed frames do not render through the adopted LoopRenderer")
    loop = src_span(court, "// 4. the court", "// 5. after the court")
    if "witness_one" in loop or "readback" in loop or "clear" in loop:
        raise Red("the readback or the clear runs inside the court's rounds")
    if "s.set_call(c);\n            s.flush(); // the locked phase origin\n            let t0 = s.ticks();" not in loop:
        raise Red("the call is not set before the locked phase origin")
    i_probe = tail.find("PRESENT-EXACT-0 probe (appended)")
    if i_probe >= 0:
        i_end = tail.find("PRESENT-EXACT-0 LOCK: the conforming presenter (appended)")
        probe = tail[i_probe:i_end] if i_end > i_probe else tail[i_probe:]
        if "write_raw(" in probe or "crate::presentexact::court(" in probe or "qpc()" in probe.split("pub fn presentexact_probe(")[-1]:
            raise Red("the probe writes a record, runs the court or takes a clock: it is a diagnostic only")
    return ("only the call changes and the witness sits outside the clock: the exact surface's present is present_once's "
            "shape with StretchDIBits at 1:1 or SetDIBitsToDevice as its one difference, no stretch mode touched; the window "
            "is a DPI-aware, borderless, topmost 1920x1080 popup at (0,0) with LATENCY-0's procedure; the clear is a white "
            "PatBlt and the readback a screen-DC BitBlt into a 24-bit top-down DIB; the timed interval holds only the "
            "LoopRenderer's render and blit and the call; the readback and clear run only before and after the rounds; the "
            "probe takes no clock, runs no court and writes no record; LATENCY-0's instrument is still a byte-exact prefix")


# ------------------------------------------------------------------ PRESENT-EXACT-0 LOCK (the conforming presenter)
PRESENTEXACT_RECORDS = {"presentexact-DANIELDILLBERG.json": "2eee8efcbf8ab89c2bac072780d8ba8ed5afaa0ce7910dd3b3a8f0b2d6333175",
                        "presentexact-confirm-DANIELDILLBERG.json": "7af3b71aae7ab35edcfb19f1150debabe4ef552aee0e2b534151f5704191e29d"}


def presentexact_lock():
    """PRESENT-EXACT-0 LOCK: the conforming presenter for PRESENTATION-CHOICE-0, locked to SetDIBitsToDevice. `shell show`
    and `shell show-playback` present pre-rendered certified frames (never a per-frame render loop), each guarded by the
    blit-hash law before any window, 1:1 in the borderless DPI-aware topmost window, through the witnessed surface with
    the call fixed; the composed screen is read back after every present and the run exits 3 if any readback differed;
    Esc closes; no clock, no record; the frozen half-size windows are untouched. Where the checkout carries the host
    records, they are the pinned ones and read SETDIBITSTODEVICE."""
    import presentexact as PX
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    i_probe, i_lock = tail.find("PRESENT-EXACT-0 probe (appended)"), tail.find("PRESENT-EXACT-0 LOCK: the conforming presenter (appended)")
    if i_probe < 0 or i_lock < i_probe:
        raise Red("the presenter's section is not appended after the probe's")
    sect = tail[i_lock:]
    show = src_span(sect, "pub fn show(", "\n}\n")
    if "call: 1," not in show or "call: 0" in sect or "set_call(" in sect or "StretchDIBits(" in sect:
        raise Red("the presenter is not fixed to SetDIBitsToDevice through the witnessed surface")
    order = [show.find(t) for t in ("blit_roundtrip_ok(&c.composite)", "SetProcessDPIAware()", "= show_window(", "surf.geometry()",
                                     "SHELL-SHOW-GEOMETRY", "surf.present(&blits[k])")]
    if -1 in order or order != sorted(order):
        raise Red("the presenter does not guard the blit law, go DPI-aware, open the window and check the geometry, in that order, before presenting")
    if show.count("surf.present(&blits[k])") != show.count("show_witness(&mut surf, &blits[k]") or show.count("show_witness(") < 3:
        raise Red("a present is not followed by a screen readback")
    if "std::process::exit(if st.differed > 0 { 3 } else { 0 });" not in show:
        raise Red("the presenter does not exit non-zero when a readback differed")
    wsrc = src_span(sect, "fn show_window(", "\n}\n")
    proc_ = src_span(sect, "extern \"system\" fn wnd_proc_show(", "\n}\n")
    if ("CreateWindowExW(WS_EX_TOPMOST, class_name.as_ptr(), title_w.as_ptr(), WS_POPUP | WS_VISIBLE, 0, 0, W as i32, H as i32," not in wsrc
            or "lpfn_wnd_proc: Some(wnd_proc_show)" not in wsrc or "msg == WM_KEYDOWN && wp == VK_ESCAPE" not in proc_
            or "wnd_proc(hwnd, msg, wp, lp)" not in proc_):
        raise Red("the presenter's window is not the borderless topmost 1920x1080 popup at (0,0) closing on Esc")
    if "write_raw(" in sect or "qpc()" in sect:
        raise Red("the presenter writes a record or takes a clock")
    main_src = read(os.path.join(SHELL, "main.rs")).decode("utf-8")
    if ("win32::show(vec![c], \"SHOW\");" not in main_src or "win32::show(frames, \"SHOW-PLAYBACK\");" not in main_src
            or PLAYBACK_WINDOW_DISPATCH not in main_src or "win32::run(c, a.measure, &a.host, a.camera);" not in main_src):
        raise Red("show / show-playback are not dispatched to the presenter, or run / playback-window moved")
    if SHELL_EXE is not None:
        for args in (["show", "--level", os.path.join(ORACLE, "levels", "witness.lvl"), "--tiles", os.path.join(ORACLE, "tiles", "identity.tiles"),
                      "--camera", "34,28,W"], ["show-playback", "--session", SESSIONWALK_DEMO]):
            cp = subprocess.run([SHELL_EXE] + args, capture_output=True, text=True, cwd=ROOT)
            if cp.returncode == 0 or "SHELL-NO-WINDOW" not in cp.stderr:
                raise Red("a windowless build did not refuse `%s` with SHELL-NO-WINDOW" % args[0])
    attest = os.path.join(ROOT, "shell", "attest")
    present = [f for f in PRESENTEXACT_RECORDS if os.path.exists(os.path.join(attest, f))]
    if present:
        if len(present) != 2:
            raise Red("the checkout carries one of the two PRESENT-EXACT-0 records but not the other")
        first = envelope.read(os.path.join(attest, "presentexact-DANIELDILLBERG.json"))
        conf = envelope.read(os.path.join(attest, "presentexact-confirm-DANIELDILLBERG.json"))
        if (first["chain_hash"], conf["chain_hash"]) != tuple(PRESENTEXACT_RECORDS.values()):
            raise Red("the PRESENT-EXACT-0 records are not the pinned ones")
        l1, _ = PX.performance(first["data"]["derived"]["calls"])
        l2, _ = PX.performance(conf["data"]["derived"]["calls"])
        if (conf["provenance"]["confirms"]["chain_hash"] != first["chain_hash"] or PX.adoption(l1, l2) != "SETDIBITSTODEVICE"
                or first["data"]["readback"]["mismatched_bytes"] or conf["data"]["readback"]["mismatched_bytes"]
                or "ADOPTED CALL: SETDIBITSTODEVICE" not in conf["reading"]):
            raise Red("the PRESENT-EXACT-0 records do not read an exact screen and SETDIBITSTODEVICE")
        evidence = "the two host records are in this checkout, are the pinned ones, read the screen exact, and adopt SETDIBITSTODEVICE"
    else:
        evidence = ("the two host records are cited by hash (%s, %s); this checkout does not carry them"
                    % tuple(h[:8] for h in PRESENTEXACT_RECORDS.values()))
    return ("PRESENT-EXACT-0 LOCK: `shell show` and `shell show-playback` present pre-rendered certified frames, each guarded by "
            "the blit-hash law before any window, 1:1 in the borderless DPI-aware topmost 1920x1080 window at (0,0), through the "
            "witnessed surface with the call fixed at SetDIBitsToDevice; every present is followed by a composed-screen readback "
            "and the run exits 3 if any differed; Esc closes; no clock, no record; a windowless build refuses both; run and "
            "playback-window are unmoved; %s" % evidence)


# ------------------------------------------------------------------ main
def main() -> int:
    print("VERÐANDI GATE")
    row("oracle-frozen", oracle_frozen)
    row("game-frozen", game_frozen)
    row("game-suites", game_suites)
    row("game-plant", game_plant)
    row("game-not-runtime", game_not_runtime)
    row("oracle-d0", oracle_d0)
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
    row("latency1-preregistered", latency1_preregistered)
    row("latency1a-preregistered", latency1a_preregistered)
    row("latency1r-preregistered", latency1r_preregistered)
    row("latency1-sealers", latency1_sealers)
    row("framesplit-preregistered", framesplit_preregistered)
    row("framesplit-sealer", framesplit_sealer)
    row("presentscale-preregistered", presentscale_preregistered)
    row("presentscale-sealer", presentscale_sealer)
    row("presentstretch-preregistered", presentstretch_preregistered)
    row("presentstretch-sealer", presentstretch_sealer)
    row("allocreuse-preregistered", allocreuse_preregistered)
    row("allocreuse-sealer", allocreuse_sealer)
    row("allocreuse1-preregistered", allocreuse1_preregistered)
    row("allocreuse1-sealer", allocreuse1_sealer)
    row("hoststate-preregistered", hoststate_preregistered)
    row("hoststate-record", hoststate_record)
    row("hoststate-fence", hoststate_fence)
    row("presentationchoice-declared", presentationchoice_declared)
    row("presentexact-preregistered", presentexact_preregistered)
    row("presentexact-sealer", presentexact_sealer)
    row("gauntlet-preregistered", gauntlet_preregistered)
    row("gauntlet1-preregistered", gauntlet1_preregistered)
    row("gauntlet1-equiv", gauntlet1_equiv)
    row("gauntlet1-region", gauntlet1_region)
    row("gauntlet1b-reduction", gauntlet1b_reduction)
    row("gauntlet1c-dda", gauntlet1c_dda)
    row("rebreakdown1-preregistered", rebreakdown1_preregistered)
    row("rebreakdown1-structure", rebreakdown1_structure)
    row("rebreakdown1-fence", rebreakdown1_fence)
    row("locality0-preregistered", locality0_preregistered)
    row("locality0-equiv", locality0_equiv)
    row("locality0-bijection", locality0_bijection)
    row("locality0-provenance", locality0_provenance)
    row("locality0-indextax", locality0_indextax)
    row("locality0-lock", locality0_lock)
    row("locality0-lockfence", locality0_lockfence)
    row("gauntlet2-preregistered", gauntlet2_preregistered)
    row("gauntlet2-partition-invariance", gauntlet2_partition_invariance)
    row("gauntlet2-threaded-equiv", gauntlet2_threaded_equiv)
    row("gauntlet2-threaded-fence", gauntlet2_threaded_fence)
    row("gauntlet2-lock", gauntlet2_lock)
    row("gauntlet2-lockfence", gauntlet2_lockfence)
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
    row("latency1r-court", latency1r_court)
    row("latency1r-fence", latency1r_fence)
    row("framesplit-court", framesplit_court)
    row("framesplit-fence", framesplit_fence)
    row("presentscale-court", presentscale_court)
    row("presentscale-fence", presentscale_fence)
    row("presentstretch-court", presentstretch_court)
    row("presentstretch-fence", presentstretch_fence)
    row("allocreuse-court", allocreuse_court)
    row("allocreuse-fence", allocreuse_fence)
    row("allocreuse1-equiv", allocreuse1_equiv)
    row("allocreuse1-court", allocreuse1_court)
    row("allocreuse1-fence", allocreuse1_fence)
    row("allocreuse1-lock", allocreuse1_lock)
    row("presentexact-court", presentexact_court)
    row("presentexact-fence", presentexact_fence)
    row("presentexact-lock", presentexact_lock)
    fails = sum(1 for st, _, _ in ROWS if st == "FAIL")
    skips = sum(1 for st, _, _ in ROWS if st == "SKIP")
    rowset = sha256("\n".join(name for _, name, _ in ROWS).encode("utf-8"))[:16]
    print("GATE FAILED" if fails else "GATE PASSED")
    print(f"RECONCILE  rowset {rowset}  {len(ROWS)} rows / {fails} fail / {skips} skipped")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
