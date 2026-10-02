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
recorded beside a court, never controlled and never read by a rule), refusalwhy (REFUSAL-WHY-0: a readback refusal
names the windows above ours over the differing box, after its verdict, reading only), hoststate1 (HOST-STATE-1: the
OS-computed clock and the paging rates, a version 2 snapshot that no court records yet), refusallog (REFUSAL-LOG-0:
every refusal on the present path appends one unsealed line to an append-only log; one record per refusal, proven on
the mock court), runledger (RUN-LEDGER-0: one line per court or presenter run, refused or not, joined to the refusal
log on run_id), refusalwhy1 (REFUSAL-WHY-1: a screen-readback refusal's covering windows written into the refusal
log — program, class, flags and rectangle, never a title or a pid), drift (DRIFT-0: the locked PRESENT-EXACT-0 court
repeated unchanged, 3 sittings of 4 runs, HOST-STATE-1 beside, a descriptive panel with no verdict), liveloop
(LIVE-LOOP-0: the first per-frame loop — the sealed session walked live through the LoopRenderer and SetDIBitsToDevice,
the screen read back at every step, counts only), liveinput (LIVE-INPUT-0: key presses become typed events in an
in-memory session-walk whose replay the live loop renders — the binding proven on scripted keys, the log replayed
through the workshop's SESSION-WALK to the state and head the loop reached, nothing saved), liveauthor (LIVE-AUTHOR-0:
the live editor — tile classes painted from a registered palette as session events, commit-only, the pixels witnessed
per state, the camera control condition, the authored world persisting through save and resume), livesession
(LIVE-SESSION-0: the live session journaled as it runs, sealed on Esc by an atomic replace and verified from the disk
before it counts as saved, resumed into new files with lineage, a crashed run recovered from its journal, the loader's
TAMPERED / DIFFERENT-RENDERER classification), and — in the oracle stage —
oracle-d0 (Urðr's own statecanon recomputes the oracle's D_0 in place).
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
    return "kernel/main.rs (+ mantle.rs, formats.rs, hud.rs, fast.rs, vocab.rs, bearing.rs, bearingfast.rs) compiled live with " + " ".join(FLAGS)


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


def w32_section(tail: str, marker: str) -> str:
    """One appended section of shell/win32.rs: from its marker to the next section rule, or to the end of the file."""
    i = tail.find(marker)
    j = tail.find("\n// ==================================================================", i + len(marker))
    return tail[i:] if j < 0 else tail[i:j]


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
    # re-pinned on purpose with LIVE-INPUT-0: the live session's move witness is replay_from's own compose_frame digest;
    # and with SIM-TICK-0: that witness is taken through shell/heading.rs — the same compose_frame at an anchor heading
    "playback.rs": {"compose_frame(": 2, "to_blit(": 2},
    "heading.rs": {"compose_frame(": 1},
    "present.rs": {"compose_frame(": 1, "arm_composite(": 2, "fast::render(": 2, "fast::emit_threaded(": 3, "fast::emit(": 2, "to_blit(": 6},
    "presentscale.rs": {"arm_composite(": 2, "arm_composite_marked(": 2, "to_blit(": 1},
    "presentstretch.rs": {"arm_composite(": 2, "arm_composite_marked(": 2, "to_blit(": 1},
    # re-pinned on purpose with PRESENT-EXACT-0: its witnesses compare the loop against the fresh reference
    "presentexact.rs": {"arm_composite(": 1, "to_blit(": 1},
    # re-pinned on purpose with PRESENT-EXACT-0 LOCK: the presenter's blit-hash guard on its pre-rendered frames
    "win32.rs": {"to_blit(": 4},
    # re-pinned on purpose with LIVE-LOOP-0: its witnesses verify each step's reference before the live walk
    "liveloop.rs": {"arm_composite(": 1, "to_blit(": 1},
    # re-pinned on purpose with LIVE-INPUT-0: one reference render per state change, outside the compositions
    "liveinput.rs": {"arm_composite(": 1, "to_blit(": 1},
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
    if ("probe: dict | None = None" not in hr or hr.count("hoststate.capture_safe(version=hoststate_version)") != 2
            or "hoststate_version: int = 1" not in hr or "hoststate.capture()" in hr
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
    sect = w32_section(tail, "PRESENT-EXACT-0 LOCK: the conforming presenter (appended)")
    show = src_span(sect, "pub fn show(", "\n}\n")
    if "call: 1," not in show or "call: 0" in sect or "set_call(" in sect or "StretchDIBits(" in sect:
        raise Red("the presenter is not fixed to SetDIBitsToDevice through the witnessed surface")
    order = [show.find(t) for t in ("blit_roundtrip_ok(&c.composite)", "SetProcessDPIAware()", "= show_window(", "surf.geometry()",
                                     "SHELL-SHOW-GEOMETRY", "show_present(&mut surf, &blits[k], k, n);")]
    if -1 in order or order != sorted(order):
        raise Red("the presenter does not guard the blit law, go DPI-aware, open the window and check the geometry, in that order, before presenting")
    # every present goes through show_present, which refuses on a failed present, and is followed at once by a readback
    sp = src_span(sect, "fn show_present(", "\n}\n")
    if ("if surf.present(bgr).is_none() {" not in sp or "SHELL-SHOW-NO-PRESENT" not in sp or "std::process::exit(2);" not in sp
            or sect.count("surf.present(") != 1 or "let _ = surf.present(" in sect):
        raise Red("a present in the presenter can fail without a refusal (every present must go through show_present)")
    pairs = show.count("show_present(&mut surf, &blits[k], k, n);\n")
    followed = len(re.findall(r"show_present\(&mut surf, &blits\[k\], k, n\);\n\s*show_witness\(&mut surf, &blits\[k\], k, n, (true|false), &mut st\);", show))
    if pairs < 3 or followed != pairs or show.count("show_witness(") != pairs:
        raise Red("a present is not followed at once by a screen readback")
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
            "witnessed surface with the call fixed at SetDIBitsToDevice; every present goes through show_present, which refuses "
            "(exit 2) if it fails, and is followed at once by a composed-screen readback; the run exits 3 if any readback "
            "differed; Esc closes; no clock, no record; a windowless build refuses both; run and "
            "playback-window are unmoved; %s" % evidence)


# ------------------------------------------------------------------ REFUSAL-WHY-0 and HOST-STATE-1
# REFUSAL-WHY-0 reads: none of these may appear in its section (it moves, shows, activates, closes, messages and
# terminates nothing), and it declares exactly these read-only imports
REFUSALWHY_FORBIDDEN = ("SetWindowPos", "ShowWindow", "PostMessage", "SendMessage", "SetForegroundWindow", "BringWindowToTop",
                        "MoveWindow", "DestroyWindow", "TerminateProcess", "CloseWindow", "SetWindowLong", "SetLayeredWindowAttributes",
                        "EnableWindow", "SetActiveWindow", "SetFocus", "SetParent", "InvalidateRect", "RedrawWindow", "EndTask",
                        "PROCESS_TERMINATE", "PROCESS_ALL_ACCESS", "write_raw(", "qpc()", "std::process::exit")
REFUSALWHY_EXTERNS = ["CloseHandle", "GetClassNameW", "GetTopWindow", "GetWindow", "GetWindowLongW", "GetWindowRect",
                      "GetWindowTextW", "GetWindowThreadProcessId", "OpenProcess", "QueryFullProcessImageNameW"]
REFUSALWHY_MOCK = "attribution: the mock screen has no windows; nothing lies above"
# HOST-STATE-1's counters, by their English names (pdh.dll), and the only PDH calls it makes
HOSTSTATE1_COUNTERS = {
    "clock": (("processor_frequency_mhz", "\\Processor Information(_Total)\\Processor Frequency", 1),
              ("performance_permille", "\\Processor Information(_Total)\\% Processor Performance", 10),
              ("utility_permille", "\\Processor Information(_Total)\\% Processor Utility", 10)),
    "faults": (("page_faults_per_s", "\\Memory\\Page Faults/sec", 1),
               ("page_reads_per_s", "\\Memory\\Page Reads/sec", 1),
               ("pages_input_per_s", "\\Memory\\Pages Input/sec", 1))}
HOSTSTATE1_PDH = {"PdhOpenQueryW", "PdhAddEnglishCounterW", "PdhCollectQueryData", "PdhGetFormattedCounterValue", "PdhCloseQuery"}


def refusalwhy_preregistered():
    """REFUSAL-WHY-0's method is locked: explanatory apparatus appended to a readback refusal or mismatch only after its
    verdict is decided; the differing box, then the visible uncloaked windows above ours that meet it, with their owners;
    read-only; a candidate, never a cause; at most six named."""
    e = locked_entry("REFUSAL-WHY-0", {
        "explanatory apparatus, after the verdict": ("hyp", ("explanatory apparatus, never a correctness dependency", "after its verdict is decided", "changes nothing")),
        "what an attribution names": ("hyp", ("bounding box of the differing pixels", "z order", "visible, not cloaked", "image name", "below the window layer")),
        "a candidate, not a cause": ("hyp", ("a candidate is not a cause",)),
        "where it appears; the decision first": ("succ", ("carry the attribution after the decided text", "computed before the attribution is called", "read-only window and process queries only", "default names nothing")),
        "the gate's plants": ("succ", ("a changed byte, a clear that writes nothing", "no record")),
        "no dependence, no control, no cause": ("fail", ("depends on the attribution", "called before the decision", "setwindowpos", "terminateprocess", "measures around a named window", "candidate, never a cause")),
        "scope: after the fact, top-level only, six, no number": ("lims", ("read after the readback", "only top-level windows", "not a diagnosis", "at most six windows", "no number is produced")),
    })
    w32 = read(os.path.join(SHELL, "win32.rs")).decode("utf-8")
    i = w32.find("REFUSAL-WHY-0 (appended)")
    if i < 0 or "if meets && found.len() < 6 {" not in w32[i:]:
        raise Red("the attribution does not stop at the registered six windows")
    return ("REFUSAL-WHY-0's method is locked (hash %s): an attribution is explanatory apparatus, never a correctness "
            "dependency — appended to a screen-readback refusal or mismatch only after its verdict is decided; it names the "
            "differing box, then the visible, uncloaked top-level windows above ours in the Z order that meet it (owner "
            "image, pid, class, title, rectangle, overlay styles), at most six, or says the cause is below the window layer; "
            "read-only; a candidate, never a cause; no number" % e["chain_hash"][:8])


def refusalwhy_fence():
    """The attribution is decided after, and reads only: the section is appended after the presenter's, declares only
    read-only window and process queries (OpenProcess with limited query rights only) and calls nothing that moves,
    shows, activates, closes, messages or terminates; the court's two refusals call it after their decision and only
    append it; the presenter counts a mismatch before it names one; the trait's default names nothing. PLANTS on the
    mock court: a changed byte and a clear that writes nothing still refuse with no record, and each message carries the
    mock's attribution after the decided text, over the same box the message describes."""
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    i_lock, i_why = tail.find("PRESENT-EXACT-0 LOCK: the conforming presenter (appended)"), tail.find("REFUSAL-WHY-0 (appended)")
    if i_lock < 0 or i_why < i_lock:
        raise Red("the REFUSAL-WHY-0 section is not appended after the presenter's")
    why = w32_section(tail, "REFUSAL-WHY-0 (appended)")
    for tok in REFUSALWHY_FORBIDDEN:
        if tok in why:
            raise Red("the REFUSAL-WHY-0 section contains %r: an attribution may read, never act" % tok)
    externs = sorted(re.findall(r"^\s*fn (\w+)\(", "\n".join(re.findall(r'extern "system" \{(.*?)\n\}', why, re.S)), re.M))
    if externs != REFUSALWHY_EXTERNS:
        raise Red("the REFUSAL-WHY-0 section declares imports other than the read-only ones: %s" % externs)
    if ("const PROCESS_QUERY_LIMITED_INFORMATION: Dword = 0x1000;" not in why or why.count("OpenProcess(") != 2
            or "OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, pid)" not in why):
        raise Red("a process is opened with more than limited query rights")
    # REFUSAL-WHY-1: one walk (covering), reached from the exact surface, the presenter's differing readback and the
    # probe's words (covering_windows) only
    walks = re.findall(r"\bcovering\(", tail)
    ex = src_span(tail, "impl crate::presentexact::ExactSurface for ExactGdiSurface", "\n}\n")
    if (len(walks) != 4 or tail.count("covering_windows(") != 2
            or "fn attribute(&mut self, b: [usize; 4]) -> crate::presentexact::Attribution {\n        // REFUSAL-WHY-0/1: one walk, the console's words and the log's fields\n        let w = covering(self.hwnd, b);" not in ex):
        raise Red("the attribution is called somewhere other than the exact surface, the presenter's mismatch line and the probe")
    sw = src_span(tail, "fn show_witness(", "\n}\n")
    order = [sw.find(t) for t in ("let exact = matches!(&screen, Some(v) if v[..] == bgr[..]);", "st.differed += 1;", "covering(surf.hwnd, b)",
                                  "crate::refusallog::record(", "if fresh || st.last != Some(exact) {", "seen.as_ref().map(crate::presentexact::seen_text)",
                                  "println!(\"[show] frame")]
    if -1 in order or order != sorted(order) or len(re.findall(r"\bexact\s*=(?![=>])", sw)) != 1 or sw.count("covering(") != 1:
        raise Red("the presenter does not decide and count a mismatch before it names one, or walks more than once")
    px = read(os.path.join(SHELL, "presentexact.rs")).decode("utf-8")
    trait = src_span(px, "pub trait ExactSurface: Surface {", "\n}\n")
    if "fn attribute(&mut self, _bbox: [usize; 4]) -> Attribution {\n        Attribution::default()\n    }" not in trait:
        raise Red("the trait's default attribution is not empty")
    wo = src_span(px, "fn witness_one<S: ExactSurface>(", "\n}\n")
    stale = [wo.find(t) for t in ("Some(v) if v.len() == bgr.len() && v.iter().all(|&b| b == 0xFF) => {}", "let (who, seen) = why(s, &v, &|_| 0xFF);",
                                  "PRESENTEXACT-READBACK-STALE:")]
    diff = [wo.find(t) for t in ("if bad != 0 {", "let (who, seen) = why(s, &v, &|i| bgr[i]);", "PRESENTEXACT-READBACK: the composed screen differs")]
    if (-1 in stale + diff or stale != sorted(stale) or diff != sorted(diff) or wo.count("why(") != 2
            or len(re.findall(r"\bwho\b", wo)) != 4 or wo.find("rb.mismatched_bytes += bad;") > diff[1]):
        raise Red("the court calls the attribution before its decision, or uses it for more than the message")
    if px.count(".attribute(") != 1 or "Some(a) if !a.text.is_empty() => (format!(\"; {}\", a.text), a.context)," not in src_span(px, "fn why<S: ExactSurface>(", "\n}\n"):
        raise Red("the attribution is reached other than through why(), or is not appended only")
    need_rustc()
    if SHELL_EXE is None:
        raise Red("the shell was not built")
    box = r"\((\d+),(\d+)\)-\((\d+),(\d+)\)"
    shapes = {"readback": r"PRESENTEXACT-READBACK: the composed screen differs from the certified picture on sealed frame 0 under "
                          r"stretchdibits \(1 of \d+ bytes; 1 of \d+ pixels differ, box " + box + r", [^;]*; " + re.escape(REFUSALWHY_MOCK)
                          + " " + box + r"\)$",
              "stale": r"PRESENTEXACT-READBACK-STALE: the window cleared to white before sealed frame 0 under stretchdibits did not "
                       r"read back as white \(\d+ of \d+ pixels differ, box " + box + r", [^;]*; " + re.escape(REFUSALWHY_MOCK) + " "
                       + box + r"\); the readback does not see the window exactly$"}
    for plant, shape in shapes.items():
        pout = os.path.join(BUILD, f"refusalwhy-plant-{plant}.json")
        if os.path.exists(pout):
            os.remove(pout)
        cp = subprocess.run([SHELL_EXE, "presentexact-selftest", "--session", SESSIONWALK_DEMO, "--per-cell", "2", "--plant", plant,
                             "--out", pout], capture_output=True, text=True, cwd=ROOT)
        lines = [ln for ln in cp.stderr.splitlines() if "PRESENTEXACT-" in ln]
        m = re.search(shape, lines[-1]) if lines else None
        if cp.returncode != 2 or os.path.exists(pout) or not m:
            raise Red("PLANT %s: the court did not refuse with no record and the attribution after the decision" % plant)
        if m.groups()[:4] != m.groups()[4:]:
            raise Red("PLANT %s: the attribution names a box other than the one the message describes" % plant)
    return ("an attribution is decided after and reads only: the REFUSAL-WHY-0 section is appended after the presenter's, "
            "declares only read-only window and process queries (%d imports; OpenProcess with limited query rights) and calls "
            "nothing that moves, shows, activates, closes, messages or terminates; the court's two refusals call it after their "
            "decision and only append it; the presenter counts a mismatch before it names one; the trait's default names "
            "nothing; PLANTS: a changed byte and a clear that writes nothing refuse with no record, each message carrying the "
            "mock's attribution after the decided text over the box it describes" % len(REFUSALWHY_EXTERNS))


def hoststate1_preregistered():
    """HOST-STATE-1's method is locked: version 2 of the snapshot appends clock and faults (PDH counters by English name
    over a 1000 ms window each), version 1 unchanged and the default everywhere; recorded, never controlled; association,
    never cause. The code's fields, counters, format and defaults must equal the registered ones."""
    import hoststate as HS
    import inspect
    e = locked_entry("HOST-STATE-1", {
        "recorded, never controlled; version 2; version 1 the default": ("hyp", ("recorded, never controlled", "version 2 of the snapshot", "version 1 stays the default", "association only")),
        "the two fields and their counters": ("hyp", ("processor frequency", "% processor performance", "% processor utility", "page faults/sec", "page reads/sec", "pages input/sec", "english names")),
        "shape, independence, the default, a look": ("succ", ("then clock and faults", "each counter on its own", "rounded permille", "capture(version=1) is host-state-0's snapshot unchanged", "never raises for either version", "writes nothing", "its own preregistered entry")),
        "no control, no version 1 change, no measured clock, no cause": ("fail", ("any control of the host", "a version 1 snapshot changed", "recording version 2", "measured clock", "court's own", "association, never cause")),
        "scope: the OS's arithmetic, three windows, system-wide": ("lims", ("not a measured frequency", "about three seconds", "system-wide", "thermal state is still not captured", "never explained")),
    })
    if (HS.FIELDS_V2 != HS.FIELDS + ("clock", "faults") or HS.COUNTER_WINDOW_MS != 1000
            or HS.VERSIONS != {1: ("HOST-STATE-0", HS.FIELDS), 2: ("HOST-STATE-1", HS.FIELDS_V2)}
            or (HS.CLOCK_COUNTERS, HS.FAULT_COUNTERS) != (HOSTSTATE1_COUNTERS["clock"], HOSTSTATE1_COUNTERS["faults"])
            or (HS.PDH_FMT_DOUBLE, HS.PDH_FMT_NOCAP100) != (0x200, 0x8000)):
        raise Red("the recorder's version 2 fields, counters, window or format are not the registered ones")
    if (inspect.signature(HS.capture).parameters["version"].default != 1
            or inspect.signature(HS.capture_safe).parameters["version"].default != 1):
        raise Red("version 1 is not the default")
    return ("HOST-STATE-1's method is locked (hash %s): version 2 of the snapshot is HOST-STATE-0's fields unchanged and in "
            "order, then clock (Processor Frequency, %% Processor Performance and %% Processor Utility of \\Processor "
            "Information(_Total), uncapped, as permille, and the nominal x performance estimate) and faults (\\Memory Page "
            "Faults/sec, Page Reads/sec, Pages Input/sec), each counter by its English name over its own 1000 ms window; "
            "version 1 is the default of capture and capture_safe; recorded, never controlled; association, never cause"
            % e["chain_hash"][:8])


def hoststate1_record():
    """The version 2 recorder on this gate, and version 1 unchanged: the default snapshot is HOST-STATE-0's shape and
    markers exactly; off Windows version 2 marks every field unavailable and nothing raises; the Windows path degrades
    field by field; clock's estimate is nominal x performance and needs both; a counter that fails stands alone; a
    Windows-shaped version 2 snapshot validates and a mislabelled, mixed, float-bearing or unknown version becomes an
    unavailable snapshot of its version; no court opts into version 2; the recorder calls only PDH's reading functions."""
    import hoststate as HS
    v1 = HS.validate(HS.capture())
    golden_v1 = {"hoststate": "HOST-STATE-0", "version": 1, "platform": sys.platform,
                 "fields": {k: {"unavailable": HS.THERMAL if k == "thermal" else HS.NOT_WINDOWS} for k in HS.FIELDS}}
    if os.name != "nt" and {k: v for k, v in v1.items() if k != "unix_seconds"} != golden_v1:
        raise Red("the default snapshot is no longer HOST-STATE-0's version 1, unchanged")
    v2 = HS.validate(HS.capture(version=2))
    if (v2["hoststate"], v2["version"], tuple(v2["fields"])) != ("HOST-STATE-1", 2, HS.FIELDS_V2):
        raise Red("a version 2 snapshot is not HOST-STATE-1's fields in order")
    if os.name != "nt":
        if any(v != {"unavailable": HS.THERMAL if k == "thermal" else HS.NOT_WINDOWS_V2} for k, v in v2["fields"].items()):
            raise Red("off Windows a version 2 field was captured or its marker is not the registered one")
        forced = HS.validate(HS.capture(windows=True, version=2))
        if not all("unavailable" in forced["fields"][k] for k in ("clock", "faults")):
            raise Red("the version 2 Windows path did not degrade to unavailable where its APIs are absent")
    real = HS._pdh
    try:
        HS._pdh = lambda counters: {n: {"processor_frequency_mhz": 2900, "performance_permille": 1433, "utility_permille": 1210,
                                        "page_faults_per_s": 5120, "page_reads_per_s": 17, "pages_input_per_s": 64}[n] for n, _, _ in counters}
        c, f = HS.clock(), HS.faults()
        HS._pdh = lambda counters: {n: ({"unavailable": "planted PDH status"} if n == "performance_permille" else 1000) for n, _, _ in counters}
        c_bad = HS.clock()
    finally:
        HS._pdh = real
    if (c["effective_mhz_estimate"] != 2900 * 1433 // 1000 or c["window_ms"] != 1000 or f["page_reads_per_s"] != 17
            or not isinstance(c_bad["effective_mhz_estimate"], dict) or c_bad["processor_frequency_mhz"] != 1000
            or c_bad["utility_permille"] != 1000):
        raise Red("clock's estimate is not nominal x performance, or a failed counter did not stand alone")
    win1 = {"hoststate": "HOST-STATE-0", "version": 1, "unix_seconds": 1790000000, "platform": "win32",
            "fields": {k: {"unavailable": "synthetic"} for k in HS.FIELDS}}
    win2 = dict(win1, hoststate="HOST-STATE-1", version=2, fields=dict(win1["fields"], clock=c, faults=f))
    if HS.capture_safe(lambda: win2, version=2) is not win2 or HS.capture_safe(lambda: win1) is not win1:
        raise Red("a well-formed version 1 or version 2 snapshot did not validate")

    def boom():
        raise RuntimeError("planted capture failure")

    bad = [(boom, 2), (lambda: dict(win2, hoststate="HOST-STATE-0"), 2), (lambda: dict(win1, fields=win2["fields"]), 1),
           (lambda: dict(win2, version=3), 2), (lambda: dict(win2, fields=dict(win2["fields"], clock=dict(c, performance_permille=1433.5))), 2),
           (lambda: dict(win2, fields=dict(win2["fields"], faults=dict(f, page_reads_per_s=True))), 2)]
    for fn, ver in bad:
        s = HS.capture_safe(fn, version=ver)
        if set(s) != {"hoststate", "version", "unavailable"} or (s["hoststate"], s["version"]) != HS.VERSIONS[ver][:1] + (ver,):
            raise Red("capture_safe let a bad snapshot through, raised, or marked it with the wrong version")
    for name in os.listdir(os.path.join(ROOT, "verify")):
        if name.endswith(".py") and name not in ("hoststate.py", "verify.py", "drift.py"):  # DRIFT-0's entry asks for version 2
            if re.search(r"version\s*=\s*2", read(os.path.join(ROOT, "verify", name)).decode("utf-8")):
                raise Red("%s asks for a version 2 snapshot without its own registered entry" % name)
    src = read(os.path.join(ROOT, "verify", "hoststate.py")).decode("utf-8")
    if set(re.findall(r"pdh\.(Pdh\w+)", src)) != HOSTSTATE1_PDH:
        raise Red("the recorder calls a PDH function other than the reading ones")
    # the host's Python (3.12+) warned on an invalid escape in this recorder's docstring; the gate's older Python only
    # deprecates it silently, so every verify/*.py is compiled here with those warnings recorded
    import warnings
    for name in sorted(os.listdir(os.path.join(ROOT, "verify"))):
        if name.endswith(".py"):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                compile(read(os.path.join(ROOT, "verify", name)).decode("utf-8"), name, "exec")
            esc = [w for w in caught if issubclass(w.category, (SyntaxWarning, DeprecationWarning)) and "escape" in str(w.message)]
            if esc:
                raise Red("verify/%s has an invalid escape sequence (line %d): the host's Python warns on it" % (name, esc[0].lineno))
    return ("verify/hoststate.py, version 2 beside version 1: the default snapshot is still HOST-STATE-0's shape and markers; "
            "off Windows version 2 marks every field unavailable and nothing raises, and the Windows path degrades field by "
            "field; clock's estimate is nominal x performance and needs both, and a failed counter stands alone; well-formed "
            "snapshots of both versions validate; a mislabelled, mixed, float- or boolean-bearing or unknown-version snapshot "
            "becomes an unavailable snapshot of its version; no court asks for version 2; the recorder calls only PDH's "
            "reading functions (%s); no verify/*.py carries an invalid escape sequence" % ", ".join(sorted(HOSTSTATE1_PDH)))

# ------------------------------------------------------------------ REFUSAL-LOG-0
# the gate's own refusal log: every shell the gate runs writes here, never into the owner's build/refusals.log
REFUSALLOG_ENV = "VERDANDI_REFUSAL_LOG"
GATE_REFUSAL_LOG = os.path.join(BUILD, "refusals-gate.log")
# the mock court's plants and the attribution each refusal must carry
REFUSALLOG_PLANTS = {"witness": "render.witness", "close": "window.close", "geometry": "window.geometry",
                     "readback": "present.readback", "noop": "present.readback", "stale": "clear.readback"}
# the registered attribution vocabulary: the court's (presentexact.rs) and the presenter's (reason, attribution) pairs
REFUSALLOG_COURT_ATTRIBUTIONS = {"court.input", "window.geometry", "render.witness", "render.loop", "window.close",
                                 "surface.clear", "clear.readback", "surface.readback", "surface.present",
                                 "present.readback", "render.drift"}
REFUSALLOG_SHOW_PAIRS = {("SHELL-SHOW-SCREEN-DIFFERS", "present.readback"), ("SHELL-SHOW-SCREEN-UNREADABLE", "surface.readback"),
                         ("SHELL-SHOW-NO-PRESENT", "surface.present"), ("SHELL-SHOW-EMPTY", "show.input"),
                         ("SHELL-BLIT-REFUSE", "render.blit-law"), ("SHELL-NO-DWM", "surface.compositor"),
                         ("SHELL-NO-WINDOW", "window.create"), ("SHELL-SHOW-GEOMETRY", "window.geometry")}
REFUSALLOG_FORBIDDEN = (".truncate(", "write(true)", "fs::write", "File::create", "remove_file", "rename(", "set_len(",
                        "File::open", "read_to_string", "std::net", "TcpStream", "UdpSocket")


def _code_of(message: str) -> str:
    m = re.match(r"([A-Z0-9-]+):", message)
    return m.group(1) if m else "UNCODED"


def refusallog_preregistered():
    """REFUSAL-LOG-0's method is locked: an observation, never evidence or authority; one unsealed append-only record per
    refusal event on the admitted present-path operations (the PRESENT-EXACT-0 court, the locked presenter, one record
    per differing readback); the record's fields; recurrence only. The code's constants must equal the registered ones."""
    import refusallog as RL
    e = locked_entry("REFUSAL-LOG-0", {
        "an observation, never evidence or authority": ("hyp", ("an observation, never evidence and never authority", "not sealed, not chained and not committed", "never read back")),
        "the admitted operations and the grain": ("hyp", ("present-exact-0 court", "locked presenter", "every completed screen readback whose pixels differ", "one record each")),
        "the record's fields": ("hyp", ("refusal_id", "run_id", "monotonic seq", "unix_ms", "reason_code", "attribution", "registered vocabulary", "never a prose diagnosis", "context_digest")),
        "recurrence only": ("hyp", ("recurrence only", "a count is not a cause", "zero is not proof")),
        "one-to-one, append-only, default, failure, gate isolation": ("succ", ("exactly one record", "exactly one emitted refusal", "six plants", "only grows", "build/refusals.log", "exit status and message are unchanged", "its own scratch file", "writes nothing")),
        "no silent refusal, no rewrite, no dependence, no reading": ("fail", ("prints without a record", "record without a refusal", "two records for one refusal", "rewritten", "depends on the log", "reading the log", "network write", "owner's log", "changed by the instrumentation")),
        "scope: the admitted operations; show fenced not run; a failed append": ("lims", ("outside refusal-log-0", "source-fenced, not executed on the gate", "failed append", "not a timing instrument", "zero records is not proof")),
    })
    rs = read(os.path.join(SHELL, "refusallog.rs")).decode("utf-8")
    keys = re.findall(r'\\"(\w+)\\":', src_span(rs, "pub fn line(", "\n}\n"))
    if ('pub const ENV: &str = "VERDANDI_REFUSAL_LOG";' not in rs or 'pub const DEFAULT_PATH: &str = "build/refusals.log";' not in rs
            or 'pub const LOG: &str = "REFUSAL-LOG-0";' not in rs or tuple(keys) != RL.KEYS
            or (RL.ENV, RL.DEFAULT_PATH, RL.LOG) != (REFUSALLOG_ENV, os.path.join("build", "refusals.log"), "REFUSAL-LOG-0")):
        raise Red("the log's variable, default path, name or record keys are not the registered ones")
    return ("REFUSAL-LOG-0's method is locked (hash %s): an observation, never evidence or authority — one unsealed, "
            "append-only record per refusal event on the PRESENT-EXACT-0 court and the locked presenter (one per differing "
            "readback), with refusal_id, run_id, seq, unix_ms, operation, surface, reason_code, a registered attribution "
            "token, context and context_digest; recurrence only, never a cause; the variable, default path and record keys "
            "in the shell and the reader equal the registered ones" % e["chain_hash"][:8])


def refusallog_bijection():
    """The one-to-one invariant, executed on the mock court: a clean run adds no record; each of the six plants refuses
    once and adds exactly one record, whose reason_code is the code the console printed, whose attribution is the
    registered one for the plant, whose refusal_id is run_id/seq; the log only grows; every run has its own run_id.
    Without the variable the record goes to build/refusals.log under the working directory; a log that cannot be written
    is said on the console and the refusal's exit status and message are unchanged."""
    import refusallog as RL
    need_rustc()
    if SHELL_EXE is None:
        raise Red("the shell was not built")
    log = os.path.join(BUILD, "refusallog-bijection.log")
    if os.path.exists(log):
        os.remove(log)
    env = dict(os.environ, **{REFUSALLOG_ENV: log})
    base = [SHELL_EXE, "presentexact-selftest", "--session", SESSIONWALK_DEMO, "--per-cell", "2"]
    prev, runs, lines = b"", [], {}
    for plant in [""] + list(REFUSALLOG_PLANTS):
        cp = subprocess.run(base + (["--plant", plant] if plant else []), capture_output=True, text=True, cwd=ROOT, env=env)
        now = read(log) if os.path.exists(log) else b""
        if not now.startswith(prev):
            raise Red("the log did not only grow: an earlier byte changed")
        added = now[len(prev):].decode("utf-8").splitlines()
        emitted = [ln for ln in cp.stderr.splitlines() if ln.startswith("SHELL-PRESENTEXACT: ")]
        if not plant:
            if cp.returncode != 0 or added or emitted:
                raise Red("a clean court run refused or wrote a record")
        else:
            if cp.returncode != 2 or len(emitted) != 1 or len(added) != 1:
                raise Red("PLANT %s: %d refusal(s) printed and %d record(s) added, not one of each" % (plant, len(emitted), len(added)))
            rec = json.loads(added[0])
            why = RL.problem(rec)
            if why or rec["reason_code"] != _code_of(emitted[0][len("SHELL-PRESENTEXACT: "):]) or rec["seq"] != 0 \
                    or (rec["operation"], rec["surface"], rec["attribution"]) != ("presentexact.court", "mock", REFUSALLOG_PLANTS[plant]):
                raise Red("PLANT %s: the record does not match the printed refusal (%s)" % (plant, why or rec["reason_code"]))
            runs.append(rec["run_id"])
            lines[plant] = emitted[0]
        prev = now
    records, bad = RL.read(log)
    if bad or len(records) != len(REFUSALLOG_PLANTS) or len(set(runs)) != len(runs):
        raise Red("the log holds other than one well-formed record per plant, each from its own run")
    # the default path: no variable, another working directory
    cwd = os.path.join(BUILD, "refusallog-cwd")
    shutil.rmtree(cwd, ignore_errors=True)
    os.makedirs(cwd)
    env2 = {k: v for k, v in os.environ.items() if k != REFUSALLOG_ENV}
    cp = subprocess.run(base + ["--root", ROOT + os.sep, "--plant", "readback"], capture_output=True, text=True, cwd=cwd, env=env2)
    got, gbad = RL.read(os.path.join(cwd, "build", "refusals.log"))
    shutil.rmtree(cwd, ignore_errors=True)
    if cp.returncode != 2 or len(got) != 1 or gbad or got[0]["attribution"] != "present.readback":
        raise Red("without the variable the record did not go to build/refusals.log under the working directory")
    # a log that cannot be written: the refusal stands exactly as it would without the log
    cp = subprocess.run(base + ["--plant", "readback"], capture_output=True, text=True, cwd=ROOT, env=dict(os.environ, **{REFUSALLOG_ENV: BUILD}))
    emitted = [ln for ln in cp.stderr.splitlines() if ln.startswith("SHELL-PRESENTEXACT: ")]
    if (cp.returncode != 2 or emitted != [lines["readback"]]
            or not any(ln.startswith("SHELL-REFUSAL-LOG-UNWRITTEN: ") for ln in cp.stderr.splitlines())):
        raise Red("an unwritable log changed the refusal's exit status or message, or was not said")
    return ("one record per refusal, one refusal per record, on the mock court: a clean run adds none; each of the %d plants "
            "refuses once and adds exactly one record whose reason_code is the printed code, whose attribution is the "
            "registered one and whose refusal_id is its run_id/seq; the log only grows; each run has its own run_id; "
            "without the variable the record goes to build/refusals.log under the working directory; an unwritable log is "
            "said on the console and the refusal's exit status and message are unchanged" % len(REFUSALLOG_PLANTS))


def refusallog_fence():
    """The log is written only by the primitive and read by nothing on the path: the court builds its refusals as data
    (every Err is refused(...), with a registered attribution) and writes nothing; both of its emission points log
    through refuse before exiting; in the presenter nothing prints a refusal except through refuse, every exit(2)
    follows one, and each differing readback calls record once, after it is counted, with the registered (reason,
    attribution) pairs; the primitive appends and never truncates, rewrites, removes or reaches the network; nothing
    else names the log; the log is gitignored; the gate's variable points into verify/build."""
    px = read(os.path.join(SHELL, "presentexact.rs")).decode("utf-8")
    code = "\n".join(ln for ln in px.splitlines() if not ln.lstrip().startswith("//"))
    errs = re.findall(r"Err\((\w+)", code)
    if not errs or set(errs) != {"refused"} or "refusallog::record" in code or "refusallog::refuse" in code or "eprintln!" in code:
        raise Red("the court returns a refusal that is not data, or writes or prints one itself")
    if set(re.findall(r'refused\("([a-z.\-]+)"', px)) != REFUSALLOG_COURT_ATTRIBUTIONS:
        raise Red("the court's attributions are not the registered vocabulary")
    main_src = read(os.path.join(SHELL, "main.rs")).decode("utf-8")
    if ('let (ev, m) = r.into_event("mock");\n                        refusallog::refuse(&ev, &format!("SHELL-PRESENTEXACT: {}", m));\n                        runledger::end(2);\n                        exit(2)'
            not in main_src or 'refuse("PRESENTEXACT", &m)' in main_src):
        raise Red("the selftest does not log the court's refusal where it emits it")
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    win = src_span(tail, "pub fn presentexact_window(", "\n}\n")
    if ('let (ev, m) = r.into_event("gdi");\n            crate::refusallog::refuse(&ev, &format!("SHELL-{}", m));' not in win
            or 'eprintln!("SHELL-{}", m);' in win):
        raise Red("the host window does not log the court's refusal where it emits it")
    i_lock, i_why = tail.find("PRESENT-EXACT-0 LOCK: the conforming presenter (appended)"), tail.find("REFUSAL-WHY-0 (appended)")
    pres = tail[i_lock:i_why]
    exits = pres.split("std::process::exit(2);")[:-1]
    if "eprintln!(" in pres or len(exits) != 6 or any(c.count("crate::refusallog::refuse(") != 1 for c in exits) \
            or pres.count("crate::refusallog::refuse(") != 6:
        raise Red("a presenter refusal prints or exits without the logging primitive")
    for code_, console in re.findall(r'crate::refusallog::refuse\(&show_(?:event\(\(|setup\()"([A-Z-]+)".*?,\s*&?(?:format!\()?"([A-Z-]+):', pres, re.S):
        if code_ != console:
            raise Red("a presenter refusal logs %s but prints %s" % (code_, console))
    pairs = set(re.findall(r'\("(SHELL-[A-Z-]+)", "([a-z.\-]+)"', pres))
    if pairs != REFUSALLOG_SHOW_PAIRS:
        raise Red("the presenter's (reason, attribution) pairs are not the registered ones")
    sw = src_span(pres, "fn show_witness(", "\n}\n")
    order = [sw.find(t) for t in ("st.differed += 1;", "crate::refusallog::record(", "if fresh || st.last != Some(exact) {")]
    if -1 in order or order != sorted(order) or pres.count("crate::refusallog::record(") != 1 or sw.count("refusallog::") != 1:
        raise Red("a differing readback is not recorded once, after it is counted")
    rl = read(os.path.join(SHELL, "refusallog.rs")).decode("utf-8")
    for tok in REFUSALLOG_FORBIDDEN:
        if tok in rl:
            raise Red("the refusal log's writer contains %r: it may only append" % tok)
    ref = src_span(rl, "pub fn refuse(", "\n}\n")
    if (rl.count("OpenOptions::new().create(true).append(true).open(") != 1 or rl.count("std::env::var(") != 1
            or not (0 <= ref.find("record(ev);") < ref.find("eprintln!("))):
        raise Red("the log is not opened for append only, or the primitive prints before it records")
    for name in os.listdir(SHELL):
        if name.endswith(".rs") and name != "refusallog.rs":
            t = read(os.path.join(SHELL, name)).decode("utf-8")
            if "VERDANDI_REFUSAL_LOG" in t or "refusals.log" in t or "refusallog::line(" in t:
                raise Red("shell/%s names the refusal log: nothing on the path may read it" % name)
    for name in os.listdir(os.path.join(ROOT, "verify")):
        if name.endswith(".py") and name not in ("refusallog.py", "runledger.py", "verify.py", "drift.py"):  # DRIFT-0's report reads it
            t = read(os.path.join(ROOT, "verify", name)).decode("utf-8")
            if "refusallog" in t or "REFUSAL-LOG" in t or "refusals.log" in t:
                raise Red("verify/%s reads the refusal log: no rule may" % name)
    gi = read(os.path.join(ROOT, ".gitignore")).decode("utf-8").splitlines()
    if "*.log" not in gi or os.environ.get(REFUSALLOG_ENV) != GATE_REFUSAL_LOG or os.path.dirname(GATE_REFUSAL_LOG) != BUILD:
        raise Red("the log is not gitignored, or the gate's own refusals are not kept out of the owner's log")
    return ("the log is written only by the primitive and read by nothing on the path: the court returns its refusals as "
            "data with registered attributions (%d) and writes nothing; both emission points log before exiting; in the "
            "presenter every refusal prints through the primitive (6, each before its exit) and each differing readback is "
            "recorded once after it is counted, with the registered (reason, attribution) pairs (%d); the writer only "
            "appends, never truncates, removes or reaches the network; nothing else names the log; it is gitignored; the "
            "gate's variable points into verify/build" % (len(REFUSALLOG_COURT_ATTRIBUTIONS), len(REFUSALLOG_SHOW_PAIRS)))


def refusallog_reader():
    """The reader validates and counts and writes nothing: the bijection row's log reads as six records with the
    registered tallies; a tampered digest, a missing or extra key, a float, a refusal_id that is not run_id/seq, a
    non-JSON line and a skipped seq are each reported by line and not counted; the command prints the counts with the
    caveat and leaves the log's bytes unchanged."""
    import refusallog as RL
    log = os.path.join(BUILD, "refusallog-bijection.log")
    records, bad = RL.read(log)
    t = {(x["reason_code"], x["attribution"]): (x["count"], x["runs"]) for x in RL.tally(records)}
    if bad or t.get(("PRESENTEXACT-READBACK", "present.readback")) != (2, 2) or sum(c for c, _ in t.values()) != len(REFUSALLOG_PLANTS):
        raise Red("the reader did not count the bijection row's log as registered")
    good = dict(records[0])
    tampered = [dict(good, context_digest="0" * 64), {k: v for k, v in good.items() if k != "surface"}, dict(good, extra=1),
                dict(good, seq=0.5), dict(good, refusal_id=good["run_id"] + "/9")]
    skip = dict(good, run_id="skip", refusal_id="skip/2", seq=2)
    scratch = os.path.join(BUILD, "refusallog-reader.log")
    with open(scratch, "w", encoding="utf-8") as fh:
        for r in [good] + tampered:
            fh.write(json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n")
        fh.write("not json at all\n")
        fh.write(json.dumps(skip, separators=(",", ":"), ensure_ascii=False) + "\n")
    got, gbad = RL.read(scratch)
    if len(got) != 2 or len(gbad) != 7 or {n for n, _ in gbad if n} != {2, 3, 4, 5, 6, 7}:
        raise Red("the reader counted a tampered or malformed line, or missed one: %s" % gbad)
    before = read(log)
    cp = subprocess.run([sys.executable, os.path.join(ROOT, "verify", "refusallog.py"), log], capture_output=True, text=True, cwd=ROOT)
    if (cp.returncode != 0 or "%d record(s) from %d run(s)" % (len(REFUSALLOG_PLANTS), len(REFUSALLOG_PLANTS)) not in cp.stdout
            or "not proof that a refusal cannot occur" not in cp.stdout or read(log) != before):
        raise Red("the reader's command did not print the counts with the caveat, or changed the log")
    src = read(os.path.join(ROOT, "verify", "refusallog.py")).decode("utf-8")
    for tok in (".write(", '"w"', "'w'", '"a"', "'a'", "os.remove", "unlink", "rename", "import requests", "urllib"):
        if tok in src:
            raise Red("the reader contains %r: it may only read" % tok)
    os.remove(scratch)
    return ("the reader validates and counts and writes nothing: the bijection log reads as %d records with the registered "
            "tallies; a tampered digest, a missing and an extra key, a float, a refusal_id that is not run_id/seq, a non-"
            "JSON line and a skipped seq are each reported and not counted; the command prints the counts and the caveat "
            "and leaves the log unchanged" % len(REFUSALLOG_PLANTS))

# ------------------------------------------------------------------ RUN-LEDGER-0
RUNLEDGER_ENV = "VERDANDI_RUN_LEDGER"
GATE_RUN_LEDGER = os.path.join(BUILD, "runs-gate.log")
# each mock plant's line: (readbacks_checked, differed) — the court's own counts when it refuses (the mock is exact:
# witness and geometry refuse before any readback, stale at the first clear, close after the 8 witness readbacks, a
# changed byte at the first presented readback, the call that writes nothing at the second)
RUNLEDGER_PLANTS = {"witness": (0, 0), "close": (8, 0), "geometry": (0, 0), "readback": (1, 1), "noop": (2, 1), "stale": (0, 0)}


def runledger_preregistered():
    """RUN-LEDGER-0's method is locked: the denominator — one unsealed append-only line per admitted run, refused or
    not, in a file of its own that joins the refusal log on run_id; exposure only. The shell's and the reader's
    constants must equal the registered ones."""
    import runledger as RLG
    e = locked_entry("RUN-LEDGER-0", {
        "the denominator, an observation": ("hyp", ("denominator", "an observation, never evidence", "cannot be told from", "whatever its outcome")),
        "the line's fields": ("hyp", ("run_id (the refusal log's", "readbacks_checked and differed", "refusals (how many refusal records", "exit_code", "unix_ms_start and unix_ms_end")),
        "the admitted runs, a separate file": ("hyp", ("court run", "presenter run", "ended at every exit", "the refusal log keeps only refusals", "refused in n of m runs")),
        "one line per run, counts, join, isolation": ("succ", ("exactly one line", "exit_code equal to the process's exit status", "the court's own count", "refusals equal to the refusal records", "usage error", "only grows", "build/runs.log", "exit status and output are unchanged", "its own scratch file", "writes nothing")),
        "no missing, extra or wrong lines; no mixing; no dependence": ("fail", ("without a line", "two lines for one run", "disagree with the run", "refusal records written into the ledger", "depends on the ledger", "rate read as a cause", "owner's ledger")),
        "scope: admitted runs; the court's outcome; killed runs": ("lims", ("append no line", "court's outcome", "source-fenced", "killed from outside", "failed append", "not proof that a refusal cannot occur")),
    })
    rs = read(os.path.join(SHELL, "runledger.rs")).decode("utf-8")
    keys = re.findall(r'\\"(\w+)\\":', src_span(rs, "fn line(", "\n}\n"))
    if ('pub const ENV: &str = "VERDANDI_RUN_LEDGER";' not in rs or 'pub const DEFAULT_PATH: &str = "build/runs.log";' not in rs
            or 'pub const LOG: &str = "RUN-LEDGER-0";' not in rs or tuple(keys) != RLG.KEYS
            or (RLG.ENV, RLG.DEFAULT_PATH, RLG.LOG) != (RUNLEDGER_ENV, os.path.join("build", "runs.log"), "RUN-LEDGER-0")):
        raise Red("the ledger's variable, default path, name or line keys are not the registered ones")
    return ("RUN-LEDGER-0's method is locked (hash %s): the denominator — one unsealed, append-only line per admitted run "
            "(a court run or a presenter run), refused or not, in its own file, joining the refusal log on run_id, with "
            "the operation's own readback counts, its refusal count and its exit code; exposure only, never a cause; the "
            "variable, default path and line keys in the shell and the reader equal the registered ones" % e["chain_hash"][:8])


def _runledger_lines(path):
    return read(path).decode("utf-8").splitlines() if os.path.exists(path) else []


def runledger_bijection():
    """One line per admitted run, executed on the mock court: the clean run and each of the six plants append exactly
    one line, whose exit_code is the process's, whose counts are the court's own (the clean run's equal its raw
    record's readback checks), whose refusals equal the refusal records carrying its run_id; a usage error appends
    nothing to either file; the ledger only grows; without the variable the line goes to build/runs.log under the
    working directory; an unwritable ledger is said and the run's exit status and output are unchanged."""
    import refusallog as RL
    import runledger as RLG
    need_rustc()
    if SHELL_EXE is None:
        raise Red("the shell was not built")
    led, rlog = os.path.join(BUILD, "runledger-bijection.log"), os.path.join(BUILD, "runledger-bijection-refusals.log")
    raw_out = os.path.join(BUILD, "runledger-clean-raw.json")
    for f in (led, rlog, raw_out):
        if os.path.exists(f):
            os.remove(f)
    env = dict(os.environ, **{RUNLEDGER_ENV: led, REFUSALLOG_ENV: rlog})
    base = [SHELL_EXE, "presentexact-selftest", "--session", SESSIONWALK_DEMO, "--per-cell", "2"]
    prev, clean_stdout = b"", None
    for plant in [""] + list(RUNLEDGER_PLANTS):
        before_r = len(_runledger_lines(rlog))
        cp = subprocess.run(base + (["--plant", plant] if plant else ["--out", raw_out]), capture_output=True, text=True, cwd=ROOT, env=env)
        now = read(led) if os.path.exists(led) else b""
        if not now.startswith(prev):
            raise Red("the ledger did not only grow: an earlier byte changed")
        added = now[len(prev):].decode("utf-8").splitlines()
        if len(added) != 1:
            raise Red("PLANT %s: %d ledger line(s) for one run" % (plant or "none", len(added)))
        line = json.loads(added[0])
        new_refusals = [json.loads(x) for x in _runledger_lines(rlog)[before_r:]]
        if RLG.problem(line) or line["exit_code"] != cp.returncode or (line["operation"], line["surface"]) != ("presentexact.court", "mock") \
                or line["refusals"] != len(new_refusals) or any(r["run_id"] != line["run_id"] for r in new_refusals):
            raise Red("PLANT %s: the line does not match the run (exit, operation, refusals or run_id)" % (plant or "none"))
        if not plant:
            with open(raw_out, encoding="utf-8") as fh:
                checks = json.load(fh)["data"]["readback"]["checks"]
            if cp.returncode != 0 or (line["readbacks_checked"], line["differed"], line["refusals"]) != (checks, 0, 0):
                raise Red("the clean run's line is not the court's own count (%d readbacks), 0 differed, 0 refusals" % checks)
            clean_stdout = cp.stdout
        elif cp.returncode != 2 or (line["readbacks_checked"], line["differed"]) != RUNLEDGER_PLANTS[plant] or line["refusals"] != 1:
            raise Red("PLANT %s: the line's counts %s are not the court's own %s" % (plant, (line["readbacks_checked"], line["differed"]), RUNLEDGER_PLANTS[plant]))
        prev = now
    runs, bad = RLG.read(led)
    refusals, _ = RL.read(rlog)
    if bad or len(runs) != 1 + len(RUNLEDGER_PLANTS) or RLG.join(runs, refusals):
        raise Red("the ledger and the refusal log do not join one to one")
    # a failure before the run begins appends nothing to either file
    size = (len(read(led)), len(read(rlog)))
    cp = subprocess.run([SHELL_EXE, "presentexact-selftest", "--per-cell", "2"], capture_output=True, text=True, cwd=ROOT, env=env)
    if cp.returncode != 2 or (len(read(led)), len(read(rlog))) != size:
        raise Red("a usage error appended a line: it is not an admitted run")
    # the default path, and an unwritable ledger
    cwd = os.path.join(BUILD, "runledger-cwd")
    shutil.rmtree(cwd, ignore_errors=True)
    os.makedirs(cwd)
    env2 = {k: v for k, v in os.environ.items() if k not in (RUNLEDGER_ENV, REFUSALLOG_ENV)}
    cp = subprocess.run(base + ["--root", ROOT + os.sep, "--plant", "readback"], capture_output=True, text=True, cwd=cwd, env=env2)
    got, gbad = RLG.read(os.path.join(cwd, "build", "runs.log"))
    shutil.rmtree(cwd, ignore_errors=True)
    if cp.returncode != 2 or len(got) != 1 or gbad or got[0]["exit_code"] != 2:
        raise Red("without the variable the line did not go to build/runs.log under the working directory")
    cp = subprocess.run(base, capture_output=True, text=True, cwd=ROOT, env=dict(env, **{RUNLEDGER_ENV: BUILD}))
    if cp.returncode != 0 or cp.stdout != clean_stdout or "SHELL-RUN-LEDGER-UNWRITTEN: " not in cp.stderr:
        raise Red("an unwritable ledger changed the run's exit status or output, or was not said")
    os.remove(raw_out)
    return ("one line per admitted run, on the mock court: the clean run and each of the %d plants append exactly one line, "
            "with the process's exit status, the court's own readback counts (the clean run's equal its raw record's), and "
            "refusals equal to the refusal records carrying its run_id; a usage error appends nothing; the ledger only "
            "grows; without the variable the line goes to build/runs.log under the working directory; an unwritable ledger "
            "is said and the run's exit status and output are unchanged" % len(RUNLEDGER_PLANTS))


def runledger_fence():
    """Every admitted run begins where its operation begins and ends once before each exit, and nothing else writes or
    reads the ledger: the court's two emission points begin just before the court and end with its outcome; the
    presenter begins on entry and ends immediately before each of its seven exits with that exit's code; readbacks are
    counted exactly where the court and the presenter count their own; the ledger only appends, never touches the
    refusal log (nor the log it); nothing else names it; it is gitignored; the gate's variable points into
    verify/build."""
    rs = read(os.path.join(SHELL, "runledger.rs")).decode("utf-8")
    for tok in REFUSALLOG_FORBIDDEN:
        if tok in rs:
            raise Red("the run ledger's writer contains %r: it may only append" % tok)
    if (rs.count("OpenOptions::new().create(true).append(true).open(") != 1 or rs.count("std::env::var(") != 1
            or "refusallog::record" in rs or "refusallog::refuse" in rs
            or "runledger" in read(os.path.join(SHELL, "refusallog.rs")).decode("utf-8")):
        raise Red("the ledger is not append-only, or the two files write into each other")
    main_src = read(os.path.join(SHELL, "main.rs")).decode("utf-8")
    if ('runledger::begin("presentexact.court", "mock"); // RUN-LEDGER-0: the court run begins\n                match presentexact::court(&mut surf, &inputs, per_cell) {\n                    Ok(ex) => {\n                        runledger::end(0);'
            not in main_src or main_src.count("runledger::begin(") != 3 or main_src.count("runledger::end(") != 6
            or 'runledger::begin("liveloop", "mock"); // RUN-LEDGER-0: the live-loop run begins\n                match liveloop::run(&mut surf, &inputs, "mock") {\n                    Ok(live) => {\n                        runledger::end(0);' not in main_src
            or 'runledger::begin("liveinput", "mock"); // RUN-LEDGER-0: the live-input run begins\n                match liveinput::run(&mut surf, &mut session, "mock") {\n                    Ok(live) => {\n                        runledger::end(0);' not in main_src):
        raise Red("the selftest's court run does not begin just before the court and end with its outcome")
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    win = src_span(tail, "pub fn presentexact_window(", "\n}\n")
    if ('crate::runledger::begin("presentexact.court", "gdi"); // RUN-LEDGER-0: the court run begins\n    let result = crate::presentexact::court(&mut surf, &inputs, per_cell);' not in win
            or "        Ok(ex) => {\n            crate::runledger::end(0);" not in win
            or 'crate::refusallog::refuse(&ev, &format!("SHELL-{}", m));\n            crate::runledger::end(2);' not in win):
        raise Red("the host window's court run does not begin just before the court and end with its outcome")
    i_lock, i_why = tail.find("PRESENT-EXACT-0 LOCK: the conforming presenter (appended)"), tail.find("REFUSAL-WHY-0 (appended)")
    pres = tail[i_lock:i_why]
    show = src_span(pres, "pub fn show(", "\n}\n")
    if not show.split("{", 1)[1].lstrip().startswith('crate::runledger::begin("show", "gdi");'):
        raise Red("the presenter's run does not begin on entry")
    exits = re.findall(r"\n( *)(?:crate::runledger::end\(([^;]*)\);\n\1)?std::process::exit\(([^;]*)\);", pres)
    if len(exits) != 7 or any(e != x for _, e, x in exits) or pres.count("crate::runledger::end(") != 7:
        raise Red("a presenter exit is not immediately preceded by the ledger's end with the same code")
    px = read(os.path.join(SHELL, "presentexact.rs")).decode("utf-8")
    sw = src_span(pres, "fn show_witness(", "\n}\n")
    counted = []
    for name in os.listdir(SHELL):
        if name.endswith(".rs") and name != "runledger.rs":
            t = read(os.path.join(SHELL, name)).decode("utf-8")
            counted += re.findall(r"runledger::readback\(", t)
            if "VERDANDI_RUN_LEDGER" in t or "runs.log" in t:
                raise Red("shell/%s names the run ledger: nothing on the path may read it" % name)
    ll = read(os.path.join(SHELL, "liveloop.rs")).decode("utf-8")
    li = read(os.path.join(SHELL, "liveinput.rs")).decode("utf-8")
    if (len(counted) != 4 or "    st.checks += 1;\n    crate::runledger::readback(!exact);" not in sw
            or "            live.screen_readbacks += 1;\n            crate::runledger::readback(!exact);" not in ll
            or "            live.screen_readbacks += 1;\n            crate::runledger::readback(!exact);" not in li
            or "    rb.mismatched_bytes += bad;\n    crate::runledger::readback(bad != 0);" not in px):
        raise Red("readbacks are counted somewhere other than where the court and the presenter count their own")
    for name in os.listdir(os.path.join(ROOT, "verify")):
        if name.endswith(".py") and name not in ("runledger.py", "verify.py", "drift.py"):  # DRIFT-0's report reads it
            t = read(os.path.join(ROOT, "verify", name)).decode("utf-8")
            if "runledger" in t or "RUN-LEDGER" in t or "runs.log" in t:
                raise Red("verify/%s reads the run ledger: no rule may" % name)
    gi = read(os.path.join(ROOT, ".gitignore")).decode("utf-8").splitlines()
    if "*.log" not in gi or os.environ.get(RUNLEDGER_ENV) != GATE_RUN_LEDGER or os.path.dirname(GATE_RUN_LEDGER) != BUILD:
        raise Red("the ledger is not gitignored, or the gate's own runs are not kept out of the owner's ledger")
    return ("every admitted run begins where its operation begins and ends once before each exit: the court's two emission "
            "points begin just before the court and end with its outcome; the presenter begins on entry and ends "
            "immediately before each of its 7 exits with that exit's code; readbacks are counted exactly where the court "
            "and the presenter count their own; the ledger only appends and the two files never write into each other; "
            "nothing else names it; it is gitignored; the gate's variable points into verify/build")


def runledger_reader():
    """The reader validates, counts and joins, and writes nothing: the bijection ledger reads as seven runs that join
    the refusal log one to one; a missing or extra key, a float, a boolean, more differed than checked, an end before
    its start, a repeated run and a non-JSON line are each reported and not counted; a ledger line claiming a refusal the
    log lacks and a refusal record with no ledger line are each reported by the join; the command prints and changes
    nothing."""
    import refusallog as RL
    import runledger as RLG
    led, rlog = os.path.join(BUILD, "runledger-bijection.log"), os.path.join(BUILD, "runledger-bijection-refusals.log")
    runs, bad = RLG.read(led)
    refusals, _ = RL.read(rlog)
    t = {x["exit_code"]: x for x in RLG.tally(runs)}
    if bad or RLG.join(runs, refusals) or t[0]["runs"] != 1 or t[2]["runs"] != len(RUNLEDGER_PLANTS) or t[2]["refused"] != len(RUNLEDGER_PLANTS):
        raise Red("the reader did not count the bijection ledger as registered")
    good = dict(runs[0])
    scratch = os.path.join(BUILD, "runledger-reader.log")
    # each wrong line has a run_id of its own, so each is reported for its own defect; the last repeats the first
    wrong = [{k: v for k, v in good.items() if k != "surface"}, dict(good, extra=1), dict(good, differed=0.5),
             dict(good, exit_code=True), dict(good, readbacks_checked=0, differed=1),
             dict(good, unix_ms_end=good["unix_ms_start"] - 1)]
    wrong = [dict(w, run_id="%s-%d" % (good["run_id"], i)) if "run_id" in w else w for i, w in enumerate(wrong)] + [good]
    with open(scratch, "w", encoding="utf-8") as fh:
        for r in [good] + wrong:
            fh.write(json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n")
        fh.write("not json\n")
    got, gbad = RLG.read(scratch)
    os.remove(scratch)
    if len(got) != 1 or [n for n, _ in gbad] != [2, 3, 4, 5, 6, 7, 8, 9]:
        raise Red("the reader counted a malformed or repeated line, or missed one: %s" % gbad)
    claims = dict(good, run_id="phantom", refusals=1)
    orphan = dict(refusals[0], run_id="orphan", refusal_id="orphan/0")
    j = RLG.join([good, claims], [orphan])
    if len(j) != 2 or not any("phantom" in x for x in j) or not any("orphan" in x for x in j):
        raise Red("the join did not report a claimed refusal the log lacks and a refusal with no ledger line")
    before = (read(led), read(rlog))
    cp = subprocess.run([sys.executable, os.path.join(ROOT, "verify", "runledger.py"), led, rlog], capture_output=True, text=True, cwd=ROOT)
    if (cp.returncode != 0 or "%d run(s)" % (1 + len(RUNLEDGER_PLANTS)) not in cp.stdout or "join" in cp.stdout
            or "not proof that a refusal cannot occur" not in cp.stdout or (read(led), read(rlog)) != before):
        raise Red("the reader's command did not print the counts with the caveat, reported a false join, or changed a file")
    src = read(os.path.join(ROOT, "verify", "runledger.py")).decode("utf-8")
    for tok in (".write(", '"w"', "'w'", '"a"', "'a'", "os.remove", "unlink", "rename", "import requests", "urllib"):
        if tok in src:
            raise Red("the reader contains %r: it may only read" % tok)
    return ("the reader validates, counts and joins, and writes nothing: the bijection ledger reads as %d runs joining the "
            "refusal log one to one; malformed, inconsistent and repeated lines are reported and not counted; the join "
            "reports a claimed refusal the log lacks and a refusal with no ledger line; the command prints the counts and "
            "the caveat and changes nothing" % (1 + len(RUNLEDGER_PLANTS)))

# ------------------------------------------------------------------ REFUSAL-WHY-1
REFUSALWHY1_OVERLAY = {"window_1_program": "mockoverlay.exe", "window_1_class": "MockOverlayClass",
                       "window_1_flags": "topmost+layered+click-through", "window_1_rect": "0,0,1920,40"}
REFUSALWHY1_TITLE, REFUSALWHY1_PID = "a private title the log must never hold", "4242"


def refusalwhy1_preregistered():
    """REFUSAL-WHY-1's method is locked: the covering windows carried into the refusal log after the verdict — layer,
    count, and program, class, flags and rectangle per window; never a title or a pid; the rectangle geometry, not
    identity; one walk for the console and the log; recurrence only."""
    e = locked_entry("REFUSAL-WHY-1", {
        "apparatus, into the log, after the verdict": ("hyp", ("explanatory apparatus, never a correctness dependency", "into the refusal log", "after the verdict is decided and counted")),
        "the fields, and what is never kept": ("hyp", ("windows:", "below:", "unplaced:", "program's image name", "its class", "its overlay flags", "its rectangle", "titles are never persisted", "process ids are not persisted")),
        "geometry not identity; one walk; a candidate": ("hyp", ("diagnostic geometry, not identity", "program, class and flags", "one walk", "a candidate is not a cause")),
        "the plants, the overlay, the reader, one walk": ("succ", ("the refusal itself (code, attribution, exit status, message) is unchanged", "synthetic overlay window", "neither the title nor the pid appears anywhere in the log", "carry no covering fields", "reads neither the title nor the pid", "same single walk", "after it is counted and before it is recorded")),
        "no title, no dependence, no second walk": ("fail", ("a title or a pid in the refusal log", "depends on the attribution", "twice for one readback", "rectangle used as a grouping key", "probe writing to the log")),
        "scope": ("lims", ("not at its instant", "candidate kind of overlay", "group together", "source-fenced", "at most six windows", "not proof")),
    })
    px = read(os.path.join(SHELL, "presentexact.rs")).decode("utf-8")
    keys = re.findall(r'"(window_\d_\w+)"', src_span(px, "const SEEN_KEYS", "\n];"))
    if keys != ["window_%d_%s" % (i, f) for i in range(1, 7) for f in ("program", "class", "flags", "rect")]:
        raise Red("the log's window fields are not the registered program, class, flags and rectangle, six times")
    return ("REFUSAL-WHY-1's method is locked (hash %s): after the verdict, a screen-readback record carries the covering "
            "layer, the count, and program, class, flags and rectangle for up to six windows; never a title or a pid; the "
            "rectangle is geometry, not identity; one walk serves the console and the log; recurrence only, never a cause; "
            "the code's window fields are the registered ones" % e["chain_hash"][:8])


def refusalwhy1_log():
    """Executed on the mock court: the three screen-readback plants' records carry the layer and the count after the
    refusal's own context, with the refusal unchanged; the overlay plant names its window's program, pid, class, title
    and flags on the console, and its record carries program, class, flags and rectangle while neither the title nor the
    pid is anywhere in the log; the other refusals carry no covering fields; the reader counts the overlay by program,
    class and flags."""
    import refusallog as RL
    need_rustc()
    if SHELL_EXE is None:
        raise Red("the shell was not built")
    log = os.path.join(BUILD, "refusalwhy1.log")
    if os.path.exists(log):
        os.remove(log)
    env = dict(os.environ, **{REFUSALLOG_ENV: log})
    base = [SHELL_EXE, "presentexact-selftest", "--session", SESSIONWALK_DEMO, "--per-cell", "2"]
    got = {}
    for plant in ("readback", "noop", "stale", "overlay", "witness", "geometry", "close"):
        before = len(_runledger_lines(log))
        cp = subprocess.run(base + ["--plant", plant], capture_output=True, text=True, cwd=ROOT, env=env)
        added = _runledger_lines(log)[before:]
        if cp.returncode != 2 or len(added) != 1:
            raise Red("PLANT %s: the court did not refuse once with one record" % plant)
        got[plant] = (json.loads(added[0]), [ln for ln in cp.stderr.splitlines() if ln.startswith("SHELL-PRESENTEXACT: ")][0])
    for plant in ("readback", "noop", "stale"):
        rec, _ = got[plant]
        c = list(rec["context"].items())
        if RL.problem(rec) or c[-2:] != [("covering_layer", "below"), ("covering_count", 0)] or c[-3][0] != "box":
            raise Red("PLANT %s: the record does not carry the layer and count after the refusal's own context" % plant)
    rec, line = got["overlay"]
    base_rec, _ = got["readback"]
    ctx = rec["context"]
    for t in ("mockoverlay.exe (pid 4242)", 'class "MockOverlayClass"', 'title "%s"' % REFUSALWHY1_TITLE, "[topmost, layered, click-through]"):
        if t not in line:
            raise Red("the overlay's console line does not name %r" % t)
    if (RL.problem(rec) or (rec["reason_code"], rec["attribution"]) != (base_rec["reason_code"], base_rec["attribution"])
            or (ctx.get("covering_layer"), ctx.get("covering_count")) != ("windows", 1)
            or {k: ctx.get(k) for k in REFUSALWHY1_OVERLAY} != REFUSALWHY1_OVERLAY):
        raise Red("the overlay's record does not carry its window's program, class, flags and rectangle")
    text = read(log).decode("utf-8")
    if REFUSALWHY1_TITLE in text or "private title" in text or REFUSALWHY1_PID in text:
        raise Red("a title or a pid reached the refusal log")
    for plant in ("witness", "geometry", "close"):
        if any(k.startswith(("covering_", "window_")) for k in got[plant][0]["context"]):
            raise Red("PLANT %s: a refusal that is not a screen readback carries covering fields" % plant)
    records, bad = RL.read(log)
    cov = {(c["kind"], c["key"]): (c["count"], c["runs"]) for c in RL.covering(records)}
    if bad or cov.get(("window", "mockoverlay.exe | MockOverlayClass | topmost+layered+click-through")) != (1, 1) \
            or cov.get(("layer", "below")) != (3, 3) or cov.get(("layer", "windows")) != (1, 1):
        raise Red("the reader did not count the covering windows by layer and by program, class and flags")
    return ("on the mock court: the changed byte, the call that writes nothing and the clear that writes nothing carry the "
            "layer and the count after their own context, the refusal unchanged; the overlay plant names its window's "
            "program, pid, class, title and flags on the console, and its record carries program, class, flags and "
            "rectangle while neither the title nor the pid is anywhere in the log; the other refusals carry no covering "
            "fields; the reader counts the overlay by program, class and flags and the layers by run")


def refusalwhy1_fence():
    """The log's covering fields are built by one function that reads neither the title nor the pid; the host surface
    and the presenter take the console's words and the log's fields from one walk; the presenter walks once per
    differing readback, after the count and before the record, and passes its fields only through its context; the
    probe and the log's writer never touch a title."""
    px = read(os.path.join(SHELL, "presentexact.rs")).decode("utf-8")
    sc = src_span(px, "pub fn seen_context(", "\n}\n")
    if ".title" in sc or ".pid" in sc or "seen_text" in sc or px.count("seen_context(") != 3:
        raise Red("the log's covering fields read a title or a pid, or are built other than by seen_context")
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    ex = src_span(tail, "impl crate::presentexact::ExactSurface for ExactGdiSurface", "\n}\n")
    att = ex[ex.index("fn attribute("):]
    if att.count("covering(") != 1 or "seen_text(&w)" not in att or "seen_context(&w)" not in att:
        raise Red("the host surface does not take the console's words and the log's fields from one walk")
    i_lock, i_why = tail.find("PRESENT-EXACT-0 LOCK: the conforming presenter (appended)"), tail.find("REFUSAL-WHY-0 (appended)")
    pres = tail[i_lock:i_why]
    sw = src_span(pres, "fn show_witness(", "\n}\n")
    ctx = src_span(pres, "fn show_ctx(", "\n}\n")
    if (sw.count("covering(") != 1 or "show_ctx(k, n, fresh, Some((v, bgr)), seen.as_ref())" not in sw
            or "c.extend(crate::presentexact::seen_context(w));" not in ctx or ".title" in ctx or ".pid" in ctx):
        raise Red("the presenter does not pass one walk's fields through its context")
    i_probe = tail.find("PRESENT-EXACT-0 probe (appended)")
    probe = tail[i_probe:i_lock]
    rl = read(os.path.join(SHELL, "refusallog.rs")).decode("utf-8")
    if "refusallog::" in probe or "title" in rl or "covering(" in probe:
        raise Red("the probe writes to the refusal log or walks for it, or the log's writer names a title")
    return ("the log's covering fields are built by seen_context alone, which reads neither the title nor the pid; the host "
            "surface and the presenter take the console's words and the log's fields from one walk; the presenter walks "
            "once per differing readback and passes the fields only through its context; the probe never writes to the "
            "log and the log's writer names no title")

# ------------------------------------------------------------------ DRIFT-0
def drift_preregistered():
    """DRIFT-0's method is locked: observational; the locked PRESENT-EXACT-0 court repeated without modification; 3
    sittings of 4 completed runs, 60 s and 4 h apart; the overlay declared; HOST-STATE-1 before and after; every run
    sealed, refused runs kept; the panel descriptive. The sealer's constants must equal the registered ones."""
    import drift as D
    import presentexact as PX
    e = locked_entry("DRIFT-0", {
        "observational, the workload unchanged": ("hyp", ("observational", "no intervention, no rule, no verdict, no threshold", "without modification", "changes repetition and observation, not the workload")),
        "the design": ("hyp", ("3 sittings of 4 completed runs", "at least 60 s apart", "at least 4 hours apart", "declared overlay state", "host-state-1's version 2")),
        "refused runs kept": ("hyp", ("kept and never discarded", "does not count toward the sitting's four")),
        "records, protocol, panel": ("succ", ("drift-<host>-s<s>-r<r>.json", "exactly as present-exact-0's sealer derives them", "within-run spread", "never reads a number to decide", "within each sitting", "across the sittings' medians", "never pooled", "writes nothing")),
        "no change, no verdict, no discard, no cause": ("fail", ("any change to the workload", "a stable or unstable label", "a run discarded", "left unsealed", "condition, exclude or correct a run", "history pooled", "association, never cause")),
        "scope": ("lims", ("these 12 completed runs", "recorded percentiles", "lower median", "not verified", "by time", "association, never cause")),
    })
    if ((D.SITTINGS, D.RUNS_PER_SITTING, D.MIN_RUN_GAP_S, D.MIN_SITTING_GAP_S, D.OVERLAY, D.HOSTSTATE_VERSION, D.WORKLOAD)
            != (3, 4, 60, 14400, ("on", "off", "unknown"), 2, "PRESENT-EXACT-0") or PX.REQUIRED_PER_CELL != 1000):
        raise Red("the sealer's design constants are not the registered ones")
    return ("DRIFT-0's method is locked (hash %s): observational — the locked PRESENT-EXACT-0 court repeated without "
            "modification, 3 sittings of 4 completed runs, runs 60 s and sittings 4 h apart, the overlay declared, "
            "HOST-STATE-1 before and after each run; every run sealed and refused runs kept; the panel descriptive, no "
            "verdict or threshold; the sealer's constants equal the registered ones" % e["chain_hash"][:8])


def _drift_rec(D, reg, sitting, run, start, s50, d50, host_state=None, refresh=13400):
    raw = _px_raw(s50 + 9000, d50 + 9000, s50=s50, d50=d50, refresh_period_us=refresh)
    return D.seal_drift(raw, reg, "gate", {"path": "synthetic", "chain_hash": "0" * 64}, {"rustc": "gate"},
                        D.protocol(sitting, run, "off", start, start + 90), host_state)


def drift_sealer():
    """The sealer, on synthetic runs: a completed run carries the workload's own derivation, the within-run spread, the
    protocol and the host state, cites DRIFT-0, PRESENT-EXACT-0 and HOST-STATE-1, and holds no label; the host state
    moves nothing; a raw the workload's check refuses is refused; a refused run seals; the protocol refuses a sitting
    out of range or out of order, a full sitting, a run under 60 s after the previous and a sitting under 4 h after the
    last, and counts refused runs for spacing but not for completion."""
    import drift as D
    import presentexact as PX
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    rec = _drift_rec(D, reg, 1, 1, 1_790_000_000, 10000, 9800)
    envelope.validate(rec)
    d = rec["data"]
    want = {c: PX.derive(PX.check_raw(_px_raw(19000, 18800, s50=10000, d50=9800))["calls"][c]) for c in PX.CALLS}
    if (d["derived"]["calls"] != want or d["derived"]["within_run"]["setdibitstodevice"]
            != {"p95_minus_p50_us": 8800, "p99_minus_p50_us": 9000, "p95_minus_p50_permille": 897, "p99_minus_p50_permille": 918}):
        raise Red("a completed run does not carry the workload's own derivation and the within-run spread")
    prov = rec["provenance"]
    if ((prov["preregistered"]["chain_hash"], prov["workload"]["chain_hash"], prov["host_state_preregistered"]["chain_hash"])
            != (reg["DRIFT-0"]["chain_hash"], reg["PRESENT-EXACT-0"]["chain_hash"], reg["HOST-STATE-1"]["chain_hash"])):
        raise Red("the record does not cite DRIFT-0, PRESENT-EXACT-0 and HOST-STATE-1")
    body = json.dumps(d) + rec["reading"]
    for label in (PX.STRETCH, PX.SETDIB, PX.NEITHER, "ADOPT", "stable", "unstable"):
        if label in body:
            raise Red("a DRIFT-0 record carries a label: %r" % label)
    other = _drift_rec(D, reg, 1, 1, 1_790_000_000, 10000, 9800, {"before": {"unavailable": "B"}, "after": {"unavailable": "B"}})
    if other["data"]["derived"] != d["derived"]:
        raise Red("the host state moved a derived number")
    for raw, why in ((_px_raw(19000, 20000, readback={"mismatched_bytes": 1}), "a differing byte"), (_px_raw(19000, 20000, n=300), "300 samples"),
                     (_px_raw(19000, 20000, render_entry="fresh"), "another render entry")):
        try:
            D.seal_drift(raw, reg, "gate", {}, {}, D.protocol(1, 1, "off", 0, 1))
            raise Red("the sealer accepted %s: the workload's own check must refuse it" % why)
        except D.Refuse:
            pass
    ref = D.seal_refused(reg, "gate", D.protocol(1, 0, "on", 1_790_000_200, 1_790_000_260), "the window court refused")
    envelope.validate(ref)
    if ref["name"] != D.REFUSED or "derived" in ref["data"]:
        raise Red("a refused run is not sealed as a refusal with no numbers")
    t0 = 1_790_000_000

    def run(s, r, start, name=None):
        x = _drift_rec(D, reg, s, r, start, 10000, 9800)
        return x if name is None else dict(x, name=name)

    def refuses(recs, sitting, now):
        try:
            D.plan_next(recs, sitting, now)
            return False
        except D.Refuse:
            return True

    one = [run(1, 1, t0)]
    four = [run(1, i, t0 + 200 * (i - 1)) for i in range(1, 5)]
    end4 = t0 + 600 + 90
    cases = [(D.plan_next([], 1, t0) == 1, "an empty first sitting starts at run 1"),
             (refuses(one, 1, t0 + 90 + 59), "a run 59 s after the previous"),
             (D.plan_next(one, 1, t0 + 90 + 60) == 2, "a run 60 s after the previous"),
             (refuses(four, 1, end4 + 1000), "a fifth run in a full sitting"),
             (refuses(four[:3], 2, end4 + 20000), "sitting 2 before sitting 1 is complete"),
             (refuses(four, 2, end4 + 14399), "sitting 2 under 4 h after sitting 1"),
             (D.plan_next(four, 2, end4 + 14400) == 1, "sitting 2 at 4 h"),
             (refuses(four + [run(2, 1, end4 + 14400)], 1, end4 + 30000), "sitting 1 after sitting 2 began"),
             (refuses([], 4, t0), "a fourth sitting"),
             (refuses([run(1, 0, t0, D.REFUSED)], 1, t0 + 90 + 10), "a run 10 s after a refused run"),
             (D.plan_next([run(1, 0, t0, D.REFUSED)], 1, t0 + 90 + 60) == 1, "a refused run does not count toward completion")]
    for ok_, what in cases:
        if not ok_:
            raise Red("the protocol is wrong: %s" % what)
    try:
        D.protocol(1, 1, "maybe", 0, 1)
        raise Red("an undeclared overlay state was accepted")
    except D.Refuse:
        pass
    return ("the DRIFT-0 sealer on synthetic runs: a completed run carries PRESENT-EXACT-0's own derivation, the within-run "
            "spread, the protocol and the host state, cites DRIFT-0, PRESENT-EXACT-0 and HOST-STATE-1 and holds no label; "
            "the host state moves nothing; the workload's check refuses a differing byte, 300 samples and another render "
            "entry; a refused run seals with no numbers; the protocol holds the sitting order, four completed runs, 60 s "
            "between runs and 4 h between sittings, counting refused runs for spacing and not for completion")


def drift_report():
    """The panel, on 12 synthetic completed runs, one refused run, a synthetic ledger, refusal log and history: every run
    with its within-run spread, measured refresh, host state, ledger line and refusals; the between-run spread (min,
    lower median, max, range) within each sitting, across all runs and across the sittings' medians, and of the
    measured refresh; the history beside; no verdict or threshold word; the command writes nothing."""
    import drift as D
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    t0 = 1_790_000_000
    p50 = {1: [9800, 9900, 10000, 10100], 2: [10500, 10400, 10600, 10700], 3: [9700, 9600, 9900, 9800]}
    hs = {"before": {"hoststate": "HOST-STATE-1", "version": 2, "fields": {"memory": {"load_percent": 94, "available_mb": 649},
                                                                         "clock": {"performance_permille": 1185}}},
          "after": {"unavailable": "synthetic"}}
    recs, ledger, t = [], [], t0
    for s in (1, 2, 3):
        for i, v in enumerate(p50[s], 1):
            recs.append(_drift_rec(D, reg, s, i, t, v + 100, v, hs, refresh=12400 + 100 * (4 * (s - 1) + i)))
            ledger.append({"log": "RUN-LEDGER-0", "run_id": "r%d%d" % (s, i), "operation": "presentexact.court", "surface": "gdi",
                           "readbacks_checked": 10, "differed": 0, "refusals": 0, "exit_code": 0,
                           "unix_ms_start": (t + 5) * 1000, "unix_ms_end": (t + 80) * 1000})
            t += 200
        if s == 2:
            recs.append(D.seal_refused(reg, "gate", D.protocol(2, 0, "on", t, t + 60), "the window court refused"))
            ledger.append({"log": "RUN-LEDGER-0", "run_id": "rx", "operation": "presentexact.court", "surface": "gdi",
                           "readbacks_checked": 1, "differed": 1, "refusals": 1, "exit_code": 2,
                           "unix_ms_start": (t + 5) * 1000, "unix_ms_end": (t + 50) * 1000})
            refusal = {"run_id": "rx", "unix_ms": (t + 40) * 1000, "operation": "presentexact.court", "surface": "gdi",
                       "reason_code": "PRESENTEXACT-READBACK", "attribution": "present.readback",
                       "context": {"covering_layer": "windows", "covering_count": 1, "window_1_program": "mockoverlay.exe",
                                   "window_1_class": "MockOverlayClass", "window_1_flags": "topmost", "window_1_rect": "0,0,1920,40"}}
            t += 200
        t += 20000
    history = [dict(_drift_rec(D, reg, 1, 1, t0 - 99999, 12000, 11000), name="verdandi-presentexact")]
    lines = D.report("gate", sorted(recs, key=lambda r: r["data"]["protocol"]["unix_seconds_start"]), history, ledger, [refusal])
    text = "\n".join(lines)
    need = ["12 completed run(s), 1 refused",
            "between runs, setdibitstodevice render_p50_us: min 9600 median 9900 max 10700 range 1100 us (111‰ of the median), 12 runs",
            "within sitting 2: min 10400 median 10500 max 10700 range 300 us, 4 runs",
            "between sittings (their medians): min 9700 median 9900 max 10500 range 800 us",
            "refusal: PRESENTEXACT-READBACK / present.readback; covering windows: mockoverlay.exe | MockOverlayClass | topmost",
            "ledger: exit=2 readbacks=1 differed=1 refusals=1", "mem 94% avail 649 MB", "perf 1185‰",
            "history (beside, not pooled): verdandi-presentexact p50/p99 SetDIBitsToDevice 11000/20000 us",
            "refresh measured 12500 us (the court's idle compositions)",
            "between runs, measured refresh period: min 12500 median 13000 max 13600 range 1100 us, 12 runs",
            "within sitting 2: min 12900 median 13000 max 13200 range 300 us, 4 runs",
            "no verdict, no threshold"]
    for n_ in need:
        if n_ not in text:
            raise Red("the panel does not say %r" % n_)
    if text.count("ledger: exit=0 readbacks=10 differed=0 refusals=0") != 12:
        raise Red("a completed run was not joined to its one ledger line")
    hit = re.search(r"\b(stable|unstable|cheaper|adopt\w*|drift detected|material|pass\w*|fail\w*|significant\w*)\b", text.lower())
    if hit:
        raise Red("the panel carries a verdict word: %r" % hit.group(0))
    before = sorted(os.listdir(os.path.join(ROOT, "shell"))) + sorted(os.listdir(BUILD))
    env = dict(os.environ, **{REFUSALLOG_ENV: os.path.join(BUILD, "drift-none-refusals.log"),
                              RUNLEDGER_ENV: os.path.join(BUILD, "drift-none-runs.log")})
    cp = subprocess.run([sys.executable, os.path.join(ROOT, "verify", "drift.py"), "--host", "gate-none", "--report"],
                        capture_output=True, text=True, cwd=ROOT, env=env)
    after = sorted(os.listdir(os.path.join(ROOT, "shell"))) + sorted(os.listdir(BUILD))
    if cp.returncode != 0 or "0 completed run(s), 0 refused" not in cp.stdout or before != after:
        raise Red("the report command did not print an empty panel, or it wrote something")
    return ("the panel on 12 synthetic runs, a refused run, a ledger, a refusal log and history: every run with its within-"
            "run spread, host state, ledger line and refusals (the refused run's covering window named); the between-run "
            "spread within each sitting, across all runs and across the sittings' medians (min, lower median, max, range); "
            "the history beside; no verdict word; the command writes nothing")


def drift_fence():
    """DRIFT-0 changes repetition and observation, not the workload: the sealer takes the workload's own check and
    derivation and never its rule; it runs the unchanged court command at the registered sample count with HOST-STATE-1;
    the protocol reads no number; the sealing functions never read the shell's logs (only the report does); the shell
    holds nothing of DRIFT-0; host_run raises CourtRefused only where the window court refused."""
    src = read(os.path.join(ROOT, "verify", "drift.py")).decode("utf-8")
    sd = src_span(src, "def seal_drift(", "\ndef ")
    if "PX.check_raw(raw)" not in sd or "PX.derive(" not in sd or "performance(" in src or "adoption(" in src:
        raise Red("the sealer does not take the workload's own check and derivation, or reads its rule")
    if ('host_run("DRIFT-0", "presentexact", a.host, a.session, PX.REQUIRED_PER_CELL, 2, probe=probe,' not in src
            or "hoststate_version=HOSTSTATE_VERSION)" not in src or src.count("host_run(") != 1):
        raise Red("the run is not the unchanged court command at the registered sample count with HOST-STATE-1")
    pn = src_span(src, "def plan_next(", "\ndef ")
    if "derived" in pn or "render_" in pn or "calls" in pn:
        raise Red("the protocol reads a number")
    for fn in ("def plan_next(", "def protocol(", "def within_run(", "def seal_drift(", "def seal_refused(", "def load("):
        if "refusallog" in src_span(src, fn, "\ndef ") or "runledger" in src_span(src, fn, "\ndef "):
            raise Red("%s reads the shell's logs: only the report may" % fn.strip("def ("))
    for name in os.listdir(SHELL):
        if name.endswith(".rs") and ("DRIFT-0" in read(os.path.join(SHELL, name)).decode("utf-8")):
            raise Red("shell/%s holds DRIFT-0: the workload must be unchanged" % name)
    dc = read(os.path.join(ROOT, "verify", "diagcommon.py")).decode("utf-8")
    hr = src_span(dc, "def host_run(", "\ndef ")
    if (dc.count("raise CourtRefused(") != 1 or "if rc != 0 or not os.path.exists(raw_path):\n        raise CourtRefused(" not in hr):
        raise Red("CourtRefused is raised other than where the window court refused")
    return ("DRIFT-0 changes repetition and observation, not the workload: the sealer takes PRESENT-EXACT-0's own check and "
            "derivation and never its rule, and runs the unchanged court command at 1000 per cell with HOST-STATE-1; the "
            "protocol reads no number; only the report reads the shell's logs; the shell holds nothing of DRIFT-0; "
            "CourtRefused marks only a window court's refusal")

# ------------------------------------------------------------------ LIVE-LOOP-0
LIVELOOP_PLANTS_REFUSE = {"witness": ("LIVELOOP-WITNESS", "render.witness"), "close": ("LIVELOOP-CLOSED", "window.close"),
                          "geometry": ("LIVELOOP-GEOMETRY", "window.geometry")}


def liveloop_preregistered():
    """LIVE-LOOP-0's method is locked: the sealed session walked live — every composition rendered through the
    LoopRenderer from the current step, byte-checked and presented by SetDIBitsToDevice; the screen read back at every
    step and in the hold; counts only. The shell's and the sealer's constants must equal the registered ones."""
    import liveloop as LL
    e = locked_entry("LIVE-LOOP-0", {
        "the first live loop, narrow": ("hyp", ("renders every composition live", "walks the sealed session live", "nothing is pre-rendered for presentation", "no authoring input, no camera control, no clock", "not how fast")),
        "the walk and the witnesses": ("hyp", ("24 compositions per step", "held for 150 compositions", "adopted looprenderer", "setdibitstodevice", "witnesses first", "every 75th composition of the hold")),
        "the gate, the plants, the host record": ("succ", ("steps x 24 + 150 compositions", "steps + 2 times", "session file's hash unchanged", "tampered witness, a mid-walk close and a client below a title bar", "a present that writes nothing", "liveloop-<host>.json")),
        "no unrendered frame, no hidden difference, no input, no clock": ("fail", ("not rendered through the looprenderer", "a byte difference not refused", "a screen difference hidden", "pre-rendered frame presented", "a clock taken", "the sealed session changed", "a run that did not finish")),
        "scope": ("lims", ("twice in the hold", "fresh present from a stale one", "sealed session is the state source", "counts only", "this host")),
    })
    rs = read(os.path.join(SHELL, "liveloop.rs")).decode("utf-8")
    for const in ("pub const DWELL: u64 = 24;", "pub const HOLD: u64 = 150;", "pub const RECHECK: u64 = 75;", "pub const CALL: usize = 1;"):
        if const not in rs:
            raise Red("the loop's constants are not the registered ones: %s is missing" % const)
    if (LL.DWELL, LL.HOLD, LL.RECHECK, LL.TARGET) != (24, 150, 75, [1920, 1080]):
        raise Red("the sealer's constants are not the registered ones")
    return ("LIVE-LOOP-0's method is locked (hash %s): the sealed session walked live — 24 compositions per step and 150 "
            "held, every composition rendered through the LoopRenderer from the current step, byte-checked against the "
            "step's verified bytes and presented by SetDIBitsToDevice; the screen read back at every step and every 75th "
            "held composition; no input, no clock, counts only; the shell's and the sealer's constants equal the "
            "registered ones" % e["chain_hash"][:8])


def liveloop_court():
    """The SAME loop the host window runs, headless over the mock: the clean walk completes with every composition
    rendered, byte-checked and presented, the screen read back steps + 2 times with no difference, the session file
    unchanged, and seals; PLANTS: a tampered witness, a mid-walk close and a client below a title bar refuse with no
    record, logged and ledgered; a present that writes nothing completes with every readback differing, each counted,
    logged once with its covering fields and ledgered. The ledger and the refusal log join one to one."""
    import liveloop as LL
    import refusallog as RL
    import runledger as RLG
    need_rustc()
    if SHELL_EXE is None:
        raise Red("the shell was not built")
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    rlog, led, out = (os.path.join(BUILD, f) for f in ("liveloop-refusals.log", "liveloop-runs.log", "liveloop-mock.json"))
    for f in (rlog, led, out):
        if os.path.exists(f):
            os.remove(f)
    env = dict(os.environ, **{REFUSALLOG_ENV: rlog, RUNLEDGER_ENV: led})
    base = [SHELL_EXE, "liveloop-selftest", "--session", SESSIONWALK_DEMO, "--per-cell", "0"]
    cp = subprocess.run(base + ["--out", out], capture_output=True, text=True, cwd=ROOT, env=env)
    if cp.returncode != 0 or "liveloop court OK" not in cp.stdout or not os.path.exists(out):
        raise Red("the headless live loop did not run: " + (cp.stderr.strip() or cp.stdout.strip()))
    with open(out, encoding="utf-8") as fh:
        raw = json.load(fh)
    os.remove(out)
    d = raw["data"]
    steps = d["steps"]
    if (d["compositions"], d["frames_rendered"], d["frames_presented"], d["byte_checks"], d["screen_readbacks"], d["screen_differed"]) \
            != (steps * 24 + 150,) * 4 + (steps + 2, 0) or d["session"]["sha256_before"] != sha256(read(SESSIONWALK_DEMO)):
        raise Red("the clean walk's counts or its session hash are not the registered ones")
    try:
        rec = LL.seal_liveloop(raw, reg, "gate-mock", {"path": "workshop/attest/sessionwalk-demo.json"}, {"rustc": "gate"})
    except LL.Refuse as e_:
        raise Red("the sealer refused the clean walk: %s" % e_)
    envelope.validate(rec)
    if "exact at every one of its %d readbacks" % (steps + 2) not in rec["reading"]:
        raise Red("the sealed reading does not say the screen was exact at every readback")
    for plant, (code, attribution) in LIVELOOP_PLANTS_REFUSE.items():
        pout = os.path.join(BUILD, f"liveloop-plant-{plant}.json")
        cp = subprocess.run(base + ["--plant", plant, "--out", pout], capture_output=True, text=True, cwd=ROOT, env=env)
        if cp.returncode != 2 or code not in cp.stderr or os.path.exists(pout):
            raise Red("PLANT %s: the loop did not refuse with %s and no record" % (plant, code))
    cp = subprocess.run(base + ["--plant", "noop", "--out", out], capture_output=True, text=True, cwd=ROOT, env=env)
    if cp.returncode != 0 or not os.path.exists(out):
        raise Red("PLANT noop: a present that writes nothing stopped the loop; a differing screen is counted, not refused")
    with open(out, encoding="utf-8") as fh:
        nd = json.load(fh)["data"]
    os.remove(out)
    if cp.returncode != 0 or nd["screen_differed"] != nd["screen_readbacks"] or nd["screen_readbacks"] != steps + 2:
        raise Red("PLANT noop: a present that writes nothing was not counted at every readback, or the loop stopped")
    records, rbad = RL.read(rlog)
    runs, lbad = RLG.read(led)
    by = {}
    for r in records:
        by.setdefault((r["reason_code"], r["attribution"]), []).append(r)
    want_refusals = {v: 1 for v in LIVELOOP_PLANTS_REFUSE.values()}
    diffs = by.get(("LIVELOOP-SCREEN-DIFFERS", "present.readback"), [])
    if (rbad or lbad or any(len(by.get(k, [])) != n for k, n in want_refusals.items()) or len(diffs) != steps + 2
            or any(r["operation"] != "liveloop" or r["surface"] != "mock" for r in records)
            or any("covering_layer" not in r["context"] for r in diffs) or len(records) != 3 + steps + 2):
        raise Red("the refusal log does not hold one record per refusal and per differing readback")
    exits = sorted((x["exit_code"], x["readbacks_checked"], x["differed"]) for x in runs if x["operation"] == "liveloop")
    if (len(runs) != 5 or RLG.join(runs, records) or [e_[0] for e_ in exits] != [0, 0, 2, 2, 2]
            or (0, steps + 2, 0) not in exits or (0, steps + 2, steps + 2) not in exits):
        raise Red("the run ledger does not hold one line per run with the loop's own counts, joined to the refusal log")
    return ("the live loop runs headless over the mock on every gate: %d steps walked, %d compositions each rendered through "
            "the LoopRenderer, byte-checked and presented, the screen read back %d times with no difference, the session "
            "file unchanged, sealed; PLANTS: a tampered witness, a mid-walk close and a client below a title bar refuse "
            "with no record; a present that writes nothing completes with all %d readbacks differing; each refusal and "
            "each differing readback is one refusal-log record (with its covering fields), each run one ledger line, "
            "joined one to one" % (steps, steps * 24 + 150, steps + 2, steps + 2))


def _ll_raw(**over):
    steps = over.pop("steps", 4)
    total = steps * 24 + 150
    d = {"steps": steps, "dwell": 24, "hold": 150, "recheck": 75, "compositions": total, "frames_rendered": total,
         "frames_presented": total, "byte_checks": total, "screen_readbacks": steps + 2, "screen_differed": 0,
         "geometry": {"client": [1920, 1080], "origin": [0, 0], "screen_logical": [1920, 1080], "screen_physical": [1920, 1080],
                      "source": [1920, 1080]},
         "call": "setdibitstodevice", "render_entry": "LoopRenderer", "loop_renders": total,
         "session": {"path": "synthetic", "sha256_before": "a" * 64, "sha256_after": "a" * 64}}
    for k, v in over.items():
        d[k] = dict(d[k], **v) if k in ("geometry", "session") else v
    return {"name": "verdandi-liveloop", "provenance": {"tool": "synthetic", "unix_seconds": 0}, "data": d}


def liveloop_sealer():
    """The sealer, on synthetic raws: a walk with the registered counts seals, cites LIVE-LOOP-0 and PRESENT-EXACT-0,
    carries no timing, and its reading says exact or how many readbacks differed; a short walk, a render or present
    count off, a missing byte check, a readback count off, more differing than read, a changed session, another
    geometry, call or entry, and another dwell are refused."""
    import liveloop as LL
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    try:
        rec = LL.seal_liveloop(_ll_raw(), reg, "gate", {}, {})
        other = LL.seal_liveloop(_ll_raw(screen_differed=2), reg, "gate", {}, {})
    except LL.Refuse as e_:
        raise Red("the sealer refused the registered walk: %s" % e_)
    envelope.validate(rec)
    if (rec["provenance"]["preregistered"]["chain_hash"], rec["provenance"]["presenter"]["chain_hash"]) != \
            (reg["LIVE-LOOP-0"]["chain_hash"], reg["PRESENT-EXACT-0"]["chain_hash"]):
        raise Red("the record does not cite LIVE-LOOP-0 and PRESENT-EXACT-0")
    if any(k.endswith("_us") for k in rec["data"]) or "exact at every one of its 6 readbacks" not in rec["reading"]:
        raise Red("the record carries timing, or its reading does not say the screen was exact")
    if "differed at 2 of its 6 readbacks" not in other["reading"]:
        raise Red("a run whose screen differed does not say how many readbacks differed")
    bad = [(_ll_raw(compositions=245), "a short walk"), (_ll_raw(frames_rendered=245), "a render count off"),
           (_ll_raw(frames_presented=245), "a present count off"), (_ll_raw(byte_checks=240), "missing byte checks"),
           (_ll_raw(screen_readbacks=5), "a readback count off"), (_ll_raw(screen_differed=7), "more differing than read"),
           (_ll_raw(session={"sha256_after": "b" * 64}), "a changed session"), (_ll_raw(geometry={"origin": [0, 39]}), "a client below a title bar"),
           (_ll_raw(call="stretchdibits"), "another call"), (_ll_raw(render_entry="fresh"), "another entry"),
           (_ll_raw(dwell=12), "another dwell"), (_ll_raw(loop_renders=10), "renders not from the loop")]
    for raw, why in bad:
        try:
            LL.seal_liveloop(raw, reg, "gate", {}, {})
            raise Red("the sealer accepted %s" % why)
        except LL.Refuse:
            pass
    return ("the LIVE-LOOP-0 sealer on synthetic raws: the registered walk seals, cites LIVE-LOOP-0 and PRESENT-EXACT-0, "
            "carries no timing and says whether the screen was exact or how many readbacks differed; %d malformed walks "
            "(counts, readbacks, a changed session, geometry, call, entry, dwell) are refused" % len(bad))


def liveloop_fence():
    """The loop renders live and nothing else: the witnesses run before the walk; inside it the only render is the
    LoopRenderer's from the current step, what is presented is its blit, the byte check precedes the present, the call
    is fixed at SetDIBitsToDevice; the loop takes no clock and writes no file; its refusals are data and its only log
    write is a differing readback's record. The host window is the presenter's borderless window procedure (Esc or
    close only), appended after REFUSAL-WHY-0's section, DPI-aware first, the ledger begun just before the loop; a
    windowless build refuses it."""
    rs = read(os.path.join(SHELL, "liveloop.rs")).decode("utf-8")
    run = src_span(rs, "pub fn run<S: ExactSurface>(", "\npub fn summary(")
    walk = run[run.index("for c in 0..total {"):]
    if run.index("arm_composite(&f.scene, Arm::Production)") > run.index("for c in 0..total {") or "arm_composite(" in walk or "to_blit(" in walk:
        raise Red("the reference renders inside the walk, or the witnesses do not come first")
    order = [walk.find(t) for t in ("if !s.pump()", "lr.render(&inputs[k].scene);", "lr.blit();", "if lr.composite() != &expected[k][..] || lr.bgr() != &expected_bgr[k][..]",
                                    "if s.present(lr.bgr()).is_none()", "if reads_back(c, steps)", "s.readback()")]
    if -1 in order or order != sorted(order) or walk.count("lr.render(") != 1 or walk.count("s.present(") != 1:
        raise Red("the walk is not: events, render the current step, check its bytes, present them, then read back")
    for tok in ("ticks(", "qpc", "Instant", "SystemTime", "fs::", "File::", "write_raw(", "refusallog::refuse(", "set_call(0", "StretchDIBits"):
        if tok in rs:
            raise Red("the loop contains %r: no clock, no file, refusals as data, the call fixed" % tok)
    if run.count("s.set_call(CALL);") != 1 or rs.count("crate::refusallog::record(") != 1 or rs.count("crate::runledger::readback(") != 1:
        raise Red("the call is not set once to the adopted call, or the loop logs more than a differing readback")
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    i_why, i_ll = tail.find("REFUSAL-WHY-0 (appended)"), tail.find("LIVE-LOOP-0 (appended)")
    if i_why < 0 or i_ll < i_why:
        raise Red("the LIVE-LOOP-0 section is not appended after REFUSAL-WHY-0's")
    sect = w32_section(tail, "LIVE-LOOP-0 (appended)")
    order = [sect.find(t) for t in ("SetProcessDPIAware()", "= show_window(", 'crate::runledger::begin("liveloop", "gdi");',
                                    'crate::liveloop::run(&mut surf, &inputs, "gdi")')]
    if (-1 in order or order != sorted(order) or "call: 1," not in sect or "call: 0" in sect or "set_call(" in sect
            or "StretchDIBits" in sect or "qpc()" in sect or "WM_" in sect or "crate::refusallog::refuse(&ev" not in sect):
        raise Red("the host window is not the presenter's DPI-aware borderless window with the call fixed and the ledger around the loop")
    if SHELL_EXE is not None:
        cp = subprocess.run([SHELL_EXE, "liveloop-window", "--session", SESSIONWALK_DEMO], capture_output=True, text=True, cwd=ROOT)
        if cp.returncode == 0 or "SHELL-NO-WINDOW" not in cp.stderr:
            raise Red("a windowless build did not refuse liveloop-window with SHELL-NO-WINDOW")
    return ("the loop renders live and nothing else: witnesses before the walk; inside it the LoopRenderer renders the "
            "current step, its bytes are checked, then presented; the call is fixed at SetDIBitsToDevice; no clock, no file; "
            "refusals are data and a differing readback its only log write; the host window is the presenter's DPI-aware "
            "borderless window with the ledger around the loop, appended after REFUSAL-WHY-0's section; a windowless build "
            "refuses it")


# ------------------------------------------------------------------ LIVE-INPUT-0
# The gate's two key scripts and what every press must become: a typed event (kind, command or spec, camera after it),
# or "repeat", "unbound", "end" or "refused CODE". Script A walks from the witness base camera: the faced cell opened and
# walked through, a blocked step, a cell opened and closed with a turn away and back between, a back step, both strafes,
# a stair refused, a cell closed and then walked into; an auto-repeat and an unbound key on the way. Script B stands at
# the east border and is refused there.
LIVEINPUT_SCRIPTS = {
    "A": ("28,28,N", [
        ("SPACE", ("edit", "cell:28,27,.", "28,28,N")), ("W", ("move", "F", "28,27,N")), ("UP", ("move", "F", "28,26,N")),
        ("UP", ("move", "F", "28,26,N")), ("SPACE", ("edit", "cell:28,25,.", "28,26,N")), ("A", ("move", "L", "28,26,W")),
        ("D", ("move", "R", "28,26,N")), ("SPACE", ("edit", "cell:28,25,#", "28,26,N")), ("W+", "repeat"), ("F1", "unbound"),
        ("S", ("move", "B", "28,27,N")), ("DOWN", ("move", "B", "28,28,N")), ("Q", ("move", "Q", "27,28,N")),
        ("E", ("move", "E", "28,28,N")), ("RIGHT", ("move", "R", "28,28,E")), ("W", ("move", "F", "29,28,E")),
        ("UP", ("move", "F", "30,28,E")), ("W", ("move", "F", "31,28,E")), ("UP", ("move", "F", "32,28,E")),
        ("W", ("move", "F", "33,28,E")), ("SPACE", "refused LIVEINPUT-EDIT-STAIR"), ("LEFT", ("move", "L", "33,28,N")),
        ("SPACE", ("edit", "cell:33,27,#", "33,28,N")), ("RIGHT", ("move", "R", "33,28,E")), ("LEFT", ("move", "L", "33,28,N")),
        ("W", ("move", "F", "33,28,N")), ("ESC", "end")]),
    "B": ("46,14,E", [
        ("SPACE", "refused LIVEINPUT-EDIT-BORDER"), ("W", ("move", "F", "46,14,E")), ("SPACE", "refused LIVEINPUT-EDIT-BORDER"),
        ("ESC", "end")]),
}
LIVEINPUT_EVERY = 3
LIVEINPUT_SHORT = "W,SPACE,ESC"  # the plants' script: a blocked step, then the faced cell opened


def _li_run(tag, camera, keys, logs, plant=None):
    """One liveinput-selftest over the mock; returns (completed process, raw or None). Logs go to the row's own files."""
    out = os.path.join(BUILD, "liveinput-%s.json" % tag)
    if os.path.exists(out):
        os.remove(out)
    args = [SHELL_EXE, "liveinput-selftest", "--level", os.path.join("oracle", "levels", "witness.lvl"),
            "--tiles", os.path.join("oracle", "tiles", "identity.tiles"), "--camera", camera, "--keys", keys, "--out", out]
    if plant:
        args += ["--plant", plant]
    env = dict(os.environ, **{REFUSALLOG_ENV: logs[0], RUNLEDGER_ENV: logs[1]})
    cp = subprocess.run(args, capture_output=True, text=True, cwd=ROOT, env=env)
    raw = None
    if os.path.exists(out):
        with open(out, encoding="utf-8") as fh:
            raw = json.load(fh)
        os.remove(out)
    return cp, raw


def _li_logs(name):
    logs = (os.path.join(BUILD, "liveinput-%s-refusals.log" % name), os.path.join(BUILD, "liveinput-%s-runs.log" % name))
    for f in logs:
        if os.path.exists(f):
            os.remove(f)
    return logs


def _li_script(steps):
    return ",".join(k for k, _ in steps)


def _li_clean(tag, logs):
    """Run script `tag` and require a clean end: exit 0, the court's line, a raw."""
    camera, steps = LIVEINPUT_SCRIPTS[tag]
    cp, raw = _li_run(tag, camera, _li_script(steps), logs)
    if cp.returncode != 0 or "liveinput court OK" not in cp.stdout or raw is None:
        raise Red("script %s did not run to its end: %s" % (tag, cp.stderr.strip() or cp.stdout.strip()))
    return raw["data"]


def liveinput_preregistered():
    """LIVE-INPUT-0's method is locked: the fixed binding, the faced cell, the session log replayed and read-only to the
    loop, every composition rendered live and presented, no persistence. The loop's constants and its binding table must
    be the registered ones."""
    e = locked_entry("LIVE-INPUT-0", {
        "walk plus open/close, narrow": ("hyp", ("walk plus open/close", "one press, one action", "unbound and ignored", "no tile or material edit, no cursor, no clock")),
        "the faced cell and the session": ("hyp", ("one step ahead of the camera", "a stair is not toggled", "a refused edit is not appended", "read-only to the loop", "the shell never writes w or m", "every 75th composition")),
        "the gate: binding, continuity, the loop": ("succ", ("binding determinism", "authority continuity", "sessionwalk new, then one move or edit per event, then verify", "workshop-certified frame digest", "one press every 3 compositions", "no file is written but the refusal log and run ledger lines")),
        "no stray event, no second authority, no disk": ("fail", ("auto-repeat or unbound key producing an event", "a refused edit appended", "other than by an event appended to the log", "disagreeing with the loop", "the session written to disk", "a clock taken")),
        "scope": ("lims", ("only the last is presented", "holding a key does not walk", "no persistence, no save and no recovery", "the host run writes no record", "counts only")),
    })
    rs = read(os.path.join(SHELL, "liveinput.rs")).decode("utf-8")
    for const in ("pub const RECHECK: u64 = 75;", "pub const CALL: usize = 1;", "pub const MOCK_EVERY: u64 = 3;",
                  "pub const VK_SPACE: u32 = 0x20;", "pub const VK_ESCAPE: u32 = 0x1B;", "pub const VK_LEFT: u32 = 0x25;",
                  "pub const VK_UP: u32 = 0x26;", "pub const VK_RIGHT: u32 = 0x27;", "pub const VK_DOWN: u32 = 0x28;"):
        if const not in rs:
            raise Red("the loop's constants are not the registered ones: %s is missing" % const)
    bind = src_span(rs, "pub fn bind(vk: u32) -> Action {", "\n}\n")
    arms = re.findall(r"\n\s+([^\n=]+?) => Action::([A-Za-z]+(?:\(b'[A-Z]'\))?),", bind)
    want = [("VK_UP | 0x57", "Move(b'F')"), ("VK_DOWN | 0x53", "Move(b'B')"), ("VK_LEFT | 0x41", "Move(b'L')"),
            ("VK_RIGHT | 0x44", "Move(b'R')"), ("0x51", "Move(b'Q')"), ("0x45", "Move(b'E')"), ("VK_SPACE", "Toggle"),
            ("VK_ESCAPE", "End"), ("_", "Unbound")]
    if arms != want:
        raise Red("the binding table is not the registered one: %s" % arms)
    tog = src_span(rs, "pub fn toggle(", "\n}\n")
    if "Some(b'#') => Ok((faced.0, faced.1, b'.'))" not in tog or "Some(b'.') => Ok((faced.0, faced.1, b'#'))" not in tog \
            or tog.count("Ok(") != 2:
        raise Red("the faced cell's edit is not rock to floor and floor to rock, and nothing else")
    return ("LIVE-INPUT-0's method is locked (hash %s): Up/W forward, Down/S back, Left/A and Right/D turn, Q and E strafe, "
            "Space opens or closes the faced cell (rock to floor, floor to rock, nothing else), Esc ends, every other key "
            "unbound; one press every %d compositions on the mock, the screen re-read every 75 held compositions, the call "
            "fixed at SetDIBitsToDevice" % (e["chain_hash"][:8], LIVEINPUT_EVERY))


def liveinput_binding():
    """Binding determinism: each scripted press becomes exactly its registered outcome — the typed event (kind, command or
    spec, the camera after it), or a repeat, an unbound key, a refused edit or the end — in order, at its registered
    composition; the events are exactly the appended ones; a refused edit is one refusal-log record and no event; every
    composition is rendered through the LoopRenderer, byte-checked and presented, the screen read back once per change
    with no difference; the runs end on Esc, exit 0, one ledger line each, joined to the refusal log."""
    import refusallog as RL
    import runledger as RLG
    need_rustc()
    if SHELL_EXE is None:
        raise Red("the shell was not built")
    logs = _li_logs("binding")
    total = {"presses": 0, "events": 0}
    for tag, (camera, steps) in sorted(LIVEINPUT_SCRIPTS.items()):
        d = _li_clean(tag, logs)
        got = [(t["key"] + ("+" if t["repeat"] else ""), t["outcome"], t["composition"]) for t in d["trace"]]
        want, events = [], []
        for i, (key, outcome) in enumerate(steps):
            if isinstance(outcome, tuple):
                want.append((key, "event %d" % len(events), LIVEINPUT_EVERY * i + 1))
                events.append(outcome)
            else:
                want.append((key, outcome, LIVEINPUT_EVERY * i + 1))
        if got != want:
            diff = next((i, g, w) for i, (g, w) in enumerate(zip(got + [None] * len(want), want + [None] * len(got))) if g != w)
            raise Red("script %s: press %d became %s, not %s" % (tag, diff[0], diff[1], diff[2]))
        typed = [(e["kind"], e.get("command", e.get("spec")), e["camera"]) for e in d["events"]]
        if typed != events:
            raise Red("script %s: the typed events are not the expected sequence" % tag)
        n, c = len(steps), d["counts"]
        comps = LIVEINPUT_EVERY * (n - 1) + 1
        moves = [e for e in events if e[0] == "move"]
        exp = {"keys": n, "repeats": sum(o == "repeat" for _, o in steps), "unbound": sum(o == "unbound" for _, o in steps),
               "events": len(events), "moves": len(moves), "edits": len(events) - len(moves),
               "refused": sum(isinstance(o, str) and o.startswith("refused ") for _, o in steps),
               "references": len(events) + 1, "compositions": comps, "frames_rendered": comps, "frames_presented": comps,
               "byte_checks": comps, "loop_renders": comps, "screen_readbacks": len(events) + 1, "screen_differed": 0}
        if any(c[k] != v for k, v in exp.items()) or d["ended"] != "escape" or (d["every"], d["recheck"]) != (LIVEINPUT_EVERY, 75):
            raise Red("script %s: the counts are not the registered walk's: %s" % (tag, {k: (c[k], v) for k, v in exp.items() if c[k] != v}))
        g = d["geometry"]
        if (g["client"], g["origin"], g["screen_logical"], g["screen_physical"]) != ([1920, 1080], [0, 0], [1920, 1080], [1920, 1080]) \
                or (d["call"], d["render_entry"]) != ("setdibitstodevice", "LoopRenderer"):
            raise Red("script %s: not the certified frame 1:1 at (0,0) through SetDIBitsToDevice and the LoopRenderer" % tag)
        total["presses"] += n
        total["events"] += len(events)
    records, rbad = RL.read(logs[0])
    runs, lbad = RLG.read(logs[1])
    got = sorted((r["reason_code"], r["attribution"], r["context"]["x"], r["context"]["z"], r["context"].get("cell")) for r in records)
    want = sorted([("LIVEINPUT-EDIT-STAIR", "input.edit", "34", "28", "<")] + [("LIVEINPUT-EDIT-BORDER", "input.edit", "47", "14", "#")] * 2)
    if rbad or lbad or got != want or any((r["operation"], r["surface"]) != ("liveinput", "mock") for r in records):
        raise Red("the refused edits are not one refusal-log record each, with the faced cell: %s" % got)
    if len(runs) != 2 or RLG.join(runs, records) or sorted((r["exit_code"], r["refusals"], r["differed"]) for r in runs) != [(0, 1, 0), (0, 2, 0)]:
        raise Red("the run ledger does not hold one line per scripted run, joined to the refusal log")
    return ("binding determinism on the mock: %d scripted presses (two scripts) each became exactly its registered outcome at "
            "its registered composition — %d typed events in the expected order (all six moves from arrows and letters, "
            "blocked steps, the faced cell opened and closed), an auto-repeat and an unbound key ignored, a stair and the "
            "border refused as one refusal-log record each and no event; every composition rendered through the "
            "LoopRenderer, byte-checked and presented, the screen read back once per change with no difference; both runs "
            "end on Esc, exit 0, one ledger line each, joined one to one" % (total["presses"], total["events"]))


def liveinput_continuity():
    """Authority continuity: each script's event log, replayed headless through the workshop's SESSION-WALK (sessionwalk
    new, then one move or edit per event, then verify), reproduces every event's witness and camera, the final camera,
    the final content and the head the live loop reached; W and M recomputed from the level with the log's cell edits
    applied are the loop's; every state after an edit recurs at a move with the same W and camera, and the frame the loop
    presented after the edit has that move's workshop-certified frame digest; the level and tiles files are unchanged."""
    need_rustc()
    if SHELL_EXE is None or SESSIONWALK_EXE is None:
        raise Red("the shell or the workshop's sessionwalk was not built")
    os.makedirs(SW, exist_ok=True)
    lv_path, tl_path = os.path.join(ORACLE, "levels", "witness.lvl"), os.path.join(ORACLE, "tiles", "identity.tiles")
    before = (sha256(read(lv_path)), sha256(read(tl_path)))
    logs = _li_logs("continuity")
    n_events, n_ties = 0, 0
    for tag, (camera, _steps) in sorted(LIVEINPUT_SCRIPTS.items()):
        d = _li_clean(tag, logs)
        events = d["events"]
        sp = os.path.join(SW, "liveinput-%s.json" % tag)
        code, _o, err = run(SESSIONWALK_EXE, ["new", "--level", lv_path, "--tiles", tl_path, "--camera", camera, "--out", sp])
        if code != 0:
            raise Red("sessionwalk new: " + err.strip())
        if json.load(open(sp, encoding="utf-8"))["data"]["head"] != d["base"]["genesis"]:
            raise Red("script %s: the live session's genesis is not the workshop's" % tag)
        for e in events:
            verb, flag, param = ("move", "--command", e["command"]) if e["kind"] == "move" else ("edit", "--edit", e["spec"])
            code, _o, err = run(SESSIONWALK_EXE, [verb, "--session", sp, flag, param])
            if code != 0:
                raise Red("script %s: the workshop refused the live log's %s %s: %s" % (tag, verb, param, err.strip()))
        code, out, err = run(SESSIONWALK_EXE, ["verify", "--session", sp])
        if code != 0 or "SESSIONWALK verify OK" not in out:
            raise Red("script %s: the workshop's replay of the live log does not verify: %s" % (tag, err.strip()))
        sw = json.load(open(sp, encoding="utf-8"))["data"]
        if [(x["kind"], x["witness"]) for x in sw["log"]] != [(e["kind"], e["witness"]) for e in events]:
            raise Red("script %s: an event's witness under the workshop's replay is not the live loop's" % tag)
        if [x["camera"] for x in sw["log"] if x["kind"] == "move"] != [e["camera"] for e in events if e["kind"] == "move"]:
            raise Red("script %s: a move's camera under the workshop's replay is not the live loop's" % tag)
        f = d["final"]
        if (sw["head"], sw["final_camera"], sw["final_content"], sw["base"]["content"]) != (f["head"], f["camera"], f["content"], d["base"]["content"]):
            raise Red("script %s: the workshop's replay does not reach the live loop's head, camera and content" % tag)
        lv, tl = read(lv_path), read(tl_path)
        for e in events:
            if e["kind"] == "edit":
                lv, tl = _sw_apply(lv, tl, e["spec"])
        if (sha256(lv), sha256(tl), _sw_content(lv, tl)) != (f["W"], f["M"], f["content"]):
            raise Red("script %s: W and M recomputed from the log's edits are not the live loop's" % tag)
        views = d["views"]
        if len(views) != len(events) + 1 or any(views[k + 1] != e["witness"] for k, e in enumerate(events) if e["kind"] == "move"):
            raise Red("script %s: a move's presented frame digest is not its chain witness" % tag)
        for k, e in enumerate(events):
            if e["kind"] != "edit":
                continue
            ties = [m for m in events if m["kind"] == "move" and (m["content"], m["camera"]) == (e["content"], e["camera"])]
            if not ties:
                raise Red("script %s: the state after edit %d never recurs at a move, so its presented frame is not tied" % (tag, k))
            if views[k + 1] != ties[0]["witness"]:
                raise Red("script %s: the frame presented after edit %d is not the workshop's frame for the same W and camera" % (tag, k))
            n_ties += 1
        n_events += len(events)
    if (sha256(read(lv_path)), sha256(read(tl_path))) != before:
        raise Red("the level or the tiles file changed: the live session wrote the authority's files")
    return ("authority continuity: both scripts' logs (%d events), replayed headless through the workshop's SESSION-WALK "
            "(sessionwalk new, one move or edit per event, verify), reproduce every witness and camera, the final camera, "
            "content and head the live loop reached, from the same genesis; W and M recomputed from the level with the "
            "log's edits are the loop's; each of the %d edits' states recurs at a move, and the frame presented after the "
            "edit has that move's workshop-certified digest; the level and tiles files are unchanged" % (n_events, n_ties))


def liveinput_court():
    """The loop's refusals and its screen: a client below a title bar refuses with no raw output, logged and ledgered; a
    present that writes nothing completes with every readback differing, each counted and logged once with its covering
    fields; the clean short run reads the screen exact; a spent script closes the window, a normal end; an unknown key
    and a camera on rock are usage errors before the run, with no ledger line."""
    import refusallog as RL
    import runledger as RLG
    need_rustc()
    if SHELL_EXE is None:
        raise Red("the shell was not built")
    logs = _li_logs("court")
    cp, raw = _li_run("clean", "28,28,N", LIVEINPUT_SHORT, logs)
    if cp.returncode != 0 or raw is None or raw["data"]["counts"]["screen_readbacks"] != 3 or raw["data"]["counts"]["screen_differed"] != 0:
        raise Red("the short script did not run clean with 3 exact readbacks")
    cp, raw = _li_run("geometry", "28,28,N", LIVEINPUT_SHORT, logs, "geometry")
    if cp.returncode != 2 or "LIVEINPUT-GEOMETRY" not in cp.stderr or raw is not None:
        raise Red("PLANT geometry: a client below a title bar did not refuse with no raw output")
    cp, raw = _li_run("noop", "28,28,N", LIVEINPUT_SHORT, logs, "noop")
    if cp.returncode != 0 or raw is None:
        raise Red("PLANT noop: a present that writes nothing stopped the loop; a differing screen is counted, not refused")
    c = raw["data"]["counts"]
    if (c["screen_readbacks"], c["screen_differed"], c["events"]) != (3, 3, 2):
        raise Red("PLANT noop: not every readback was counted as differing")
    cp, raw = _li_run("spent", "28,28,N", "W", logs)
    if cp.returncode != 0 or raw is None or raw["data"]["ended"] != "closed" or raw["data"]["counts"]["events"] != 1:
        raise Red("a spent script (the window closed) is not a normal end")
    for args in (["--keys", "W,BOGUS"], ["--camera", "28,27,N", "--keys", "ESC"]):
        cp = subprocess.run([SHELL_EXE, "liveinput-selftest"] + args, capture_output=True, text=True, cwd=ROOT,
                            env=dict(os.environ, **{REFUSALLOG_ENV: logs[0], RUNLEDGER_ENV: logs[1]}))
        if cp.returncode != 2:
            raise Red("a usage error (%s) was not refused" % " ".join(args))
    records, rbad = RL.read(logs[0])
    runs, lbad = RLG.read(logs[1])
    by = {}
    for r in records:
        by.setdefault((r["reason_code"], r["attribution"]), []).append(r)
    diffs = by.get(("LIVEINPUT-SCREEN-DIFFERS", "present.readback"), [])
    if (rbad or lbad or len(by.get(("LIVEINPUT-GEOMETRY", "window.geometry"), [])) != 1 or len(diffs) != 3 or len(records) != 4
            or any("covering_layer" not in r["context"] for r in diffs) or any(r["operation"] != "liveinput" for r in records)):
        raise Red("the refusal log does not hold one record per refusal and per differing readback")
    exits = sorted((x["exit_code"], x["readbacks_checked"], x["differed"]) for x in runs)
    if len(runs) != 4 or RLG.join(runs, records) or exits != [(0, 2, 0), (0, 3, 0), (0, 3, 3), (2, 0, 0)]:
        raise Red("the run ledger does not hold one line per run (and none for a usage error), joined to the refusal log")
    return ("the loop's refusals and its screen, on the mock: a client below a title bar refuses with no raw output; a "
            "present that writes nothing completes with all 3 readbacks differing, each counted and logged once with its "
            "covering fields; the clean short run reads the screen exact 3 times; a spent script is a normal end; an unknown "
            "key and a camera on rock are refused before the run; each run one ledger line, joined one to one")


def liveinput_fence():
    """The loop appends and reads, and never holds a world: the session's state is private to shell/playback.rs and
    changed only by push_move and push_edit_cell, each replaying one appended event by replay_from's own statements; the
    loop turns each press into an action (a repeat never reaching LIVE-INPUT-0's binding: its run passes no held set,
    re-pinned on purpose with HOLD-WALK-0), renders the reference once per change,
    and in every composition renders the current state through the LoopRenderer, checks its bytes, presents, then reads
    back; no clock, no file, refusals as data; the host window is the presenter's borderless window with the keyboard read
    from the message queue, appended after LIVE-LOOP-0's section, writing nothing; a windowless build refuses it."""
    pb = read(os.path.join(SHELL, "playback.rs")).decode("utf-8")
    # bounded at the next appended section (LIVE-SESSION-0's reader), which its own fence judges
    sect = w32_section(pb, "// ================================================================== LIVE-INPUT-0 (appended): the live session")
    body = src_span(sect, "pub struct LiveSession {", "\n}\n")
    if re.search(r"\n\s+pub ", body) or sect.count("(&mut self,") != 2 or sect.count("self.log.push(") != 2:
        raise Red("the live session's state is not private, or it changes other than by appending one event")
    mv, ed = src_span(sect, "pub fn push_move(", "\n    }\n"), src_span(sect, "pub fn push_edit_cell(", "\n    }\n")
    # re-pinned on purpose with SIM-TICK-0: the move's witness is taken through shell/heading.rs, which is compose_frame's
    # digest at an anchor heading (simtick-fence judges heading.rs); the statements are otherwise replay_from's.
    # And with MOUSE-LOOK-0: it is taken by the session's own Painter there (the same render, its picture kept)
    if not all(t in mv for t in ("let cam = step(&self.level, self.cam, cmd);", "self.painter.witness(&self.level, &self.tiles, cam, yaw)?", "fold(&self.head, b'M', &witness)")) \
            or not all(t in ed for t in ("if (x == 0 || z == 0 || x as usize == w - 1 || z as usize == rows - 1) && to != b'#' {",
                                         "apply_spec(&mut self.level, &mut self.tiles, &spec)", "content_hex(&self.level, &self.tiles)", "fold(&self.head, b'E', &self.content)")):
        raise Red("the live session's replay is not replay_from's statements (step, compose_frame's digest, apply_spec, content_hex, fold)")
    if any(t in sect for t in ("fs::", "File::", "write(")):
        raise Red("the live session touches a file")
    rs = read(os.path.join(SHELL, "liveinput.rs")).decode("utf-8")
    runf = src_span(rs, "pub fn run<S: ExactSurface + Keys>(", "\npub fn summary(")
    for tok in ("fs::", "File::", "write_raw(", "refusallog::refuse(", "set_call(0", "StretchDIBits", "apply_spec", "compose_frame(",
                "LiveEvent {", "Instant", "SystemTime", "qpc"):
        if tok in rs:
            raise Red("the loop contains %r: no clock, no file, no world of its own, refusals as data, the call fixed" % tok)
    if "ticks(" in runf or "ticks(" in src_span(rs, "fn reference(", "\n}\n"):
        raise Red("the loop reads a clock")
    # re-pinned on purpose with SIM-TICK-0: the loop also reads the heading (free_heading, token), to refuse a free one
    # and with MOUSE-LOOK-0: under a tick source it reads the log's last event, to hold an anchor's reference to its witness
    if set(re.findall(r"session\.(\w+)\(", runf)) - {"push_move", "push_edit_cell", "camera", "faced", "cell", "push_edit_tile", "tile_rgb", "free_heading", "token", "log"} \
            or "arm_composite(" in runf or src_span(rs, "fn reference(", "\n}\n").count("arm_composite(") != 1:
        raise Red("the loop reaches into the session other than to append and read, or renders a reference outside reference()")
    loop = runf[runf.index("    loop {"):]
    # re-pinned on purpose with MOUSE-LOOK-0: the presses bound here are the surface's unless the loop has a tick source
    # (then none: they went to the tick), and what is presented is the checked LoopRenderer bytes unless the heading is
    # free under a tick source (then the session's picture) — one render site and one present site still; mouselook-fence
    # judges the tick source's side
    order = [loop.find(t) for t in ("let open = s.pump();", "None => s.keys(),", "for (vk, repeat) in presses {", "if repeat {", "match binding(vk) {",
                                    "lr.render(&scene);", "lr.blit();", "if lr.composite() != &expected[..] || lr.bgr() != &expected_bgr[..]",
                                    "lr.bgr()\n        };", "if s.present(out).is_none()", "s.readback()")]
    if -1 in order or order != sorted(order) or loop.count("lr.render(") != 1 or loop.count("s.present(") != 1:
        raise Red("a composition is not: presses to events (repeats unbound), render the current state, check, present, read back")
    if "run_with(s, session, surface, bind, None)" not in src_span(rs, "pub fn run<S: ExactSurface + Keys>(", "\n}\n"):
        raise Red("LIVE-INPUT-0's run passes a held set: its repeats must never reach the binding")
    if (runf.count("s.set_call(CALL);") != 1 or rs.count("crate::refusallog::record(") != 2 or rs.count("crate::runledger::readback(") != 1
            or runf.count("reference(session, Some((&witness, k)))?") != 1):
        raise Red("the call is not fixed once, a move's reference does not check its witness, or the loop logs more than a refused edit and a differing readback")
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    i_ll, i_li = tail.find("LIVE-LOOP-0 (appended)"), tail.find("LIVE-INPUT-0 (appended)")
    if i_ll < 0 or i_li < i_ll:
        raise Red("the LIVE-INPUT-0 section is not appended after LIVE-LOOP-0's")
    ws = w32_section(tail, "LIVE-INPUT-0 (appended)")
    win = src_span(ws, "pub fn liveinput_window(", "\n}\n")
    order = [win.find(t) for t in ("SetProcessDPIAware()", "= show_window(", 'crate::runledger::begin("liveinput", "gdi");',
                                   'crate::liveinput::run(&mut keys, &mut session, "gdi")')]
    if (-1 in order or order != sorted(order) or "call: 1," not in ws or "call: 0" in ws or "set_call(" in win
            or any(t in ws for t in ("StretchDIBits", "qpc()", "fs::", "File::", "write_raw(", "SystemTime"))
            or "crate::refusallog::refuse(&ev" not in win or ws.count("self.pending.push(") != 1
            or "if msg.message == WM_KEYDOWN_LIVE {" not in ws or "const WM_KEYDOWN_LIVE: Uint = 0x0100;" not in ws
            or "self.pending.push((msg.w_param as u32, (msg.l_param >> 30) & 1 == 1));" not in ws):
        raise Red("the host window is not the presenter's DPI-aware borderless window with the call fixed, the keys read from "
                  "WM_KEYDOWN with their auto-repeat bit, the ledger around the loop and no file")
    main_src = read(os.path.join(SHELL, "main.rs")).decode("utf-8")
    if 'runledger::begin("liveinput", "mock"); // RUN-LEDGER-0: the live-input run begins\n                match liveinput::run(&mut surf, &mut session, "mock") {\n                    Ok(live) => {\n                        runledger::end(0);' not in main_src:
        raise Red("the selftest's live-input run does not begin just before the loop and end with its outcome")
    if SHELL_EXE is not None:
        cp = subprocess.run([SHELL_EXE, "liveinput-window"], capture_output=True, text=True, cwd=ROOT)
        if cp.returncode == 0 or "SHELL-NO-WINDOW" not in cp.stderr:
            raise Red("a windowless build did not refuse liveinput-window with SHELL-NO-WINDOW")
    return ("the loop appends and reads, and never holds a world: the session's state is private to shell/playback.rs and "
            "changes only by push_move and push_edit_cell, each replaying one appended event by replay_from's statements; "
            "a repeat never reaches LIVE-INPUT-0's binding (its run passes no held set); a move's reference must reproduce its "
            "witness; every composition renders the "
            "current state through the LoopRenderer, checks it, presents, then reads back; no clock, no file; the host window "
            "reads WM_KEYDOWN from the queue, is appended after LIVE-LOOP-0's section and writes nothing; a windowless build "
            "refuses it")


# ------------------------------------------------------------------ LIVE-SESSION-0
LIVESESSION_ENV = "VERDANDI_SESSIONS"
GATE_SESSIONS = os.path.join(BUILD, "sessions-gate")
# what continuing script A's saved session with RIGHT, W, SPACE, ESC must append: turn east, step onto the stair cell,
# close the floor beyond it
LIVESESSION_RESUME_KEYS = "RIGHT,W,SPACE,ESC"
LIVESESSION_RESUME_EVENTS = [("move", "R", "33,28,E"), ("move", "F", "34,28,E"), ("edit", "cell:35,28,#", "34,28,E")]
LIVESESSION_DIGEST_SITE = "let digest = frame_digest(&frame);"


def _ls_logs(name):
    logs = (os.path.join(BUILD, "livesession-%s-refusals.log" % name), os.path.join(BUILD, "livesession-%s-runs.log" % name))
    for f in logs:
        if os.path.exists(f):
            os.remove(f)
    return logs


def _ls_run(args, logs, exe=None):
    """One livesession-selftest; returns (completed process, the saved session's path or None)."""
    env = dict(os.environ, **{REFUSALLOG_ENV: logs[0], RUNLEDGER_ENV: logs[1], LIVESESSION_ENV: GATE_SESSIONS})
    cp = subprocess.run([exe or SHELL_EXE, "livesession-selftest"] + args, capture_output=True, text=True, cwd=ROOT, env=env)
    m = re.search(r"saved and verified: (.+?session\.json)", cp.stdout)
    return cp, (m.group(1) if m else None)


def _ls_script_a(logs, exe=None):
    camera, steps = LIVEINPUT_SCRIPTS["A"]
    cp, path = _ls_run(["--camera", camera, "--keys", _li_script(steps)], logs, exe)
    if cp.returncode != 0 or path is None or "livesession court OK" not in cp.stdout:
        raise Red("script A did not run to a saved and verified session: " + (cp.stderr.strip() or cp.stdout.strip()))
    return path


def _ls_journal(path):
    """A journal's records: (payloads, torn) where torn says the final line was not a complete record."""
    raw = read(path)
    lines = raw.split(b"\n")
    tail = lines.pop()
    out = []
    for n, ln in enumerate(lines):
        parts = ln.split(b" ", 3)
        if len(parts) != 4 or parts[0] != b"R" or int(parts[1]) != len(parts[3]) or hashlib.sha256(parts[3]).hexdigest().encode() != parts[2]:
            raise Red("journal record %d is not a record whose length and checksum agree" % n)
        out.append(json.loads(parts[3].decode("utf-8")))
    return out, tail != b""


def _ls_reseal(text):
    """Recompute a saved file's seal after an edit (a forger's step)."""
    import livesession as LS
    b = text.encode("utf-8")
    i = b.rfind(LS.SEAL_KEY)
    return (b[:i + len(LS.SEAL_KEY)] + hashlib.sha256(b[:i + 1]).hexdigest().encode() + b'"\n}\n').decode("utf-8")


def _ls_forge_witness(text, kind):
    """Change the first `kind` event's witness, fold the head again and reseal: a consistent forgery."""
    import livesession as LS
    doc = json.loads(text)
    d = doc["data"]
    k = next(i for i, x in enumerate(d["log"]) if x["kind"] == kind)
    old = d["log"][k]["witness"]
    new = ("0" if old[0] != "0" else "1") + old[1:]
    d["log"][k]["witness"] = new
    head = LS.heads(d["base"]["content"], d["base"]["camera"], d["log"])[-1]
    lines = text.split("\n")
    items = [i for i, ln in enumerate(lines) if ln.startswith('   {"kind": ')]
    if len(items) != len(d["log"]) or lines[items[k]].count(old) != 1 or text.count('"head": "%s"' % d["head"]) != 1:
        raise Red("the forgery's strings are not where the saved file keeps them")
    lines[items[k]] = lines[items[k]].replace(old, new)
    return _ls_reseal("\n".join(lines).replace('"head": "%s"' % d["head"], '"head": "%s"' % head)), k


def _ls_verify(exe, args):
    cp = subprocess.run([exe] + args, capture_output=True, text=True, cwd=ROOT)
    return cp.returncode, cp.stdout, cp.stderr


def _ls_write(name, text):
    p = os.path.join(BUILD, "livesession-%s.json" % name)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return p


def livesession_preregistered():
    """LIVE-SESSION-0's method is locked: the journal (length and checksum per record, flushed before counted), the seal
    (atomic replace, then read back and verified before the run counts as saved), the loader's order and its
    classification, lineage by chain prefix, the renderer identity's sources. The shell's and the sealer's constants
    must be the registered ones."""
    import livesession as LS
    e = locked_entry("LIVE-SESSION-0", {
        "durable without a second authority": ("hyp", ("durable and recoverable without a second authority", "moved ahead of live-author-0", "live-input-0's loop unchanged", "flushed to the disk before it is counted as journaled")),
        "the seal, the identity, the load": ("hyp", ("movefile_replace_existing | movefile_write_through", "read back from the disk and verified", "never a quiet exit", "kernel mantle.rs, formats.rs, fast.rs, hud.rs and shell/present.rs", "an identity mismatch alone never means corruption", "the parent file is never modified")),
        "the gate: save, resume, recovery, classification": ("succ", ("the workshop's sessionwalk verify passes on the saved file itself", "whose chain reaches that head at that count", "torn final record is dropped", "refuses different-renderer", "seals a record-0 copy citing live-session-0")),
        "no false durability, no second state": ("fail", ("an exit 0 after a seal failure", "counted as journaled before its record was flushed", "a parent session modified", "a renderer-identity mismatch treated as corruption", "live-input-0's command writing to disk", "the focus observation read by any rule")),
        "scope": ("lims", ("durability is the file system's", "the seal is a checksum, not a signature", "the renderer identity is evidence, not a verdict", "a journal recovers what was flushed", "recorded, not explained")),
    })
    rs = read(os.path.join(SHELL, "livesession.rs")).decode("utf-8")
    for const in ('pub const ENV: &str = "VERDANDI_SESSIONS";', 'pub const DEFAULT_ROOT: &str = "build/sessions";',
                  'pub const JOURNAL: &str = "journal.vsj";', 'pub const SESSION: &str = "session.json";',
                  'pub const JOURNAL_MAGIC: &str = "VRDNLJ1";', 'pub const SEAL_KEY: &str = "\\n \\"seal\\": \\"";'):
        if const not in rs:
            raise Red("the shell's constants are not the registered ones: %s is missing" % const)
    # re-pinned on purpose with SIM-TICK-0: read inside RENDER_SOURCES only (the bearing identity's sources are a second
    # list, consulted for frames at free headings alone; simtick-certify holds it to the sealer's)
    names = re.findall(r'\("((?:kernel|shell)/[a-z]+\.rs)", include_bytes!\("([^"]+)"\)\)', src_span(rs, "const RENDER_SOURCES:", "\n];"))
    if [n for n, _ in names] != list(LS.SOURCES) or [p for _, p in names] != ["../kernel/mantle.rs", "../kernel/formats.rs", "../kernel/fast.rs", "../kernel/hud.rs", "present.rs"]:
        raise Red("the renderer identity's sources are not the registered five, in order, in the shell and the sealer")
    if LS.SEAL_KEY != b'\n "seal": "' or LIVESESSION_ENV != "VERDANDI_SESSIONS":
        raise Red("the sealer's or the gate's constants are not the shell's")
    return ("LIVE-SESSION-0's method is locked (hash %s): records with their length and sha256, each flushed before it is "
            "counted; the seal written by an atomic replace and verified from the disk before the run counts as saved; "
            "load in the registered order and classification; lineage by chain prefix; the renderer identity over the five "
            "registered sources, the same in the shell and the sealer" % e["chain_hash"][:8])


def livesession_save():
    """Script A runs to Esc and is saved: the journal holds a header and one checksummed record per event, matching the
    saved log; the saved file's seal recomputes; its renderer identity is the one recomputed from this checkout; the
    workshop's sessionwalk verifies the saved file itself; its events are script A's; the run says saved and verified
    only after that and exits 0. PLANTS: a seal that cannot be written, a saved file corrupted before its verification, and
    a sealed, self-consistent file that is not the live session refuse (exit 2, logged, ledgered) and never say saved."""
    import livesession as LS
    import refusallog as RL
    import runledger as RLG
    need_rustc()
    if SHELL_EXE is None or SESSIONWALK_EXE is None:
        raise Red("the shell or the workshop's sessionwalk was not built")
    logs = _ls_logs("save")
    path = _ls_script_a(logs)
    run_dir = os.path.dirname(path)
    if os.path.dirname(run_dir) != GATE_SESSIONS or os.path.basename(path) != "session.json":
        raise Red("the saved session is not build/sessions/<run_id>/session.json under the gate's root")
    raw = read(path)
    try:
        doc = LS.check_saved(raw, ROOT)
    except LS.Refuse as e_:
        raise Red("the saved session does not check: %s" % e_)
    d, live = doc["data"], doc["live"]
    typed = [(x["kind"], x.get("command", x.get("spec")), x.get("camera", "")) for x in d["log"]]
    want = [o for _, o in LIVEINPUT_SCRIPTS["A"][1] if isinstance(o, tuple)]
    if [(k, p) for k, p, _ in typed] != [(k, p) for k, p, _ in want] or [c for k, _, c in typed if k == "move"] != [c for k, _, c in want if k == "move"]:
        raise Red("the saved log is not script A's events")
    if live["renderer"] != LS.renderer_id(ROOT) or live["ended"] != "escape" or live["lineage"] is not None or not isinstance(live.get("focus"), dict):
        raise Red("the live block does not name this checkout's renderer, the Esc end, no lineage and a focus observation")
    records, torn = _ls_journal(os.path.join(run_dir, "journal.vsj"))
    j = live["journal"]
    if (torn or records[0].get("journal") != "VRDNLJ1" or records[0]["renderer"] != live["renderer"] or records[0]["base"] != d["base"]
            or [(r["k"], r["witness"]) for r in records[1:]] != [(i, x["witness"]) for i, x in enumerate(d["log"])]
            or (j["records"], j["events"], j["complete"]) != (len(d["log"]) + 1, len(d["log"]), True)
            or j["sha256"] != sha256(read(os.path.join(run_dir, "journal.vsj")))):
        raise Red("the journal is not a header and one checksummed record per saved event, as the live block says")
    code, out, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", path])
    if code != 0 or "SESSIONWALK verify OK" not in out or ("head " + d["head"][:12]) not in out:
        raise Red("the workshop's sessionwalk does not verify the saved file itself: " + err.strip())
    for plant, code_ in (("seal-unwritable", "LIVESESSION-SEAL-UNWRITTEN"), ("seal-flip", "LIVESESSION-SEAL-UNVERIFIED"),
                         ("seal-stale", "LIVESESSION-SEAL-UNVERIFIED")):
        cp, p = _ls_run(["--keys", LIVEINPUT_SHORT, "--plant", plant], logs)
        if cp.returncode != 2 or code_ not in cp.stderr or p is not None or "saved and verified" in cp.stdout:
            raise Red("PLANT %s: the run did not refuse %s without claiming durability" % (plant, code_))
    records_, rbad = RL.read(logs[0])
    runs, lbad = RLG.read(logs[1])
    seals = sorted(r["reason_code"] for r in records_ if r["attribution"] == "session.seal")
    if (rbad or lbad or seals != ["LIVESESSION-SEAL-UNVERIFIED", "LIVESESSION-SEAL-UNVERIFIED", "LIVESESSION-SEAL-UNWRITTEN"]
            or RLG.join(runs, records_) or sorted(r["exit_code"] for r in runs) != [0, 2, 2, 2] or any(r["operation"] != "livesession" for r in runs)):
        raise Red("the seal refusals are not one record each, or the runs not one ledger line each, joined")
    return ("script A saved as a live session: %d events journaled one checksummed record each and saved in the workshop's "
            "format, the seal recomputes, the renderer identity is this checkout's, and the workshop's sessionwalk "
            "verifies the saved file itself (head %s...); only then the run said saved and exited 0; PLANTS: an "
            "unwritable seal, a file corrupted before its verification and a self-consistent file that is not the live "
            "session refuse, logged and ledgered, never saved"
            % (len(d["log"]), d["head"][:12]))


def livesession_resume():
    """Continuing script A's saved session: a new file whose first events are the parent's, whose lineage names the
    parent's head, event count and bytes, whose own chain reaches that head at that count, whose new events are the
    expected ones, and which the workshop verifies; the parent's bytes are unchanged."""
    import livesession as LS
    need_rustc()
    if SHELL_EXE is None or SESSIONWALK_EXE is None:
        raise Red("the shell or the workshop's sessionwalk was not built")
    logs = _ls_logs("resume")
    parent = _ls_script_a(logs)
    before = read(parent)
    cp, child = _ls_run(["--resume", parent, "--keys", LIVESESSION_RESUME_KEYS], logs)
    if cp.returncode != 0 or child is None or "(LOAD)" not in cp.stdout or child == parent:
        raise Red("the saved session did not resume into a new saved file: " + (cp.stderr.strip() or cp.stdout.strip()))
    if read(parent) != before:
        raise Red("resuming modified the parent session")
    p, c = json.loads(before.decode("utf-8")), LS.check_saved(read(child), ROOT)
    pd, cd, lin = p["data"], c["data"], c["live"]["lineage"]
    n = len(pd["log"])
    if cd["log"][:n] != pd["log"] or cd["base"] != pd["base"]:
        raise Red("the child's log does not begin with the parent's events over the same base")
    if (lin or {}).get("parent_head") != pd["head"] or lin["parent_events"] != n or lin["source"] != "session" or lin["parent_sha256"] != sha256(before):
        raise Red("the lineage does not name the parent's head, event count and bytes")
    if LS.heads(cd["base"]["content"], cd["base"]["camera"], cd["log"])[n] != pd["head"]:
        raise Red("the parent's head is not on the child's own chain at the parent's event count")
    new = [(x["kind"], x.get("command", x.get("spec")), x.get("camera", "")) for x in cd["log"][n:]]
    if [(k, q) for k, q, _ in new] != [(k, q) for k, q, _ in LIVESESSION_RESUME_EVENTS] or c["live"]["resumed"]["classification"] != "LOAD":
        raise Red("the continuation's events are not the expected ones, or it was not loaded as LOAD")
    code, out, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", child])
    if code != 0 or "SESSIONWALK verify OK" not in out:
        raise Red("the workshop's sessionwalk does not verify the continued session: " + err.strip())
    return ("script A's saved session continued into a new file: its first %d events are the parent's, its lineage names the "
            "parent's head, count and bytes and lies on its own chain, its %d new events are the expected ones, the "
            "workshop verifies it, and the parent's bytes are unchanged" % (n, len(new)))


def livesession_recover():
    """A run that crashes after five journaled events leaves a journal with a torn final record and no saved session and
    no ledger line; resuming from the journal drops the torn record, recovers the five events and continues into a saved
    session whose lineage says so; a journal with a bad record before its last, with no header, or whose record heads do
    not fold, or that is bad just before its torn tail, refuses."""
    import livesession as LS
    import runledger as RLG
    need_rustc()
    if SHELL_EXE is None or SESSIONWALK_EXE is None:
        raise Red("the shell or the workshop's sessionwalk was not built")
    logs = _ls_logs("recover")
    camera, steps = LIVEINPUT_SCRIPTS["A"]
    cp, p = _ls_run(["--camera", camera, "--keys", _li_script(steps), "--plant", "crash"], logs)
    m = re.search(r"LIVESESSION-PLANT-CRASH: .*\((.+journal\.vsj)\)", cp.stderr)
    if cp.returncode != 70 or p is not None or m is None:
        raise Red("PLANT crash: the run did not die after journaling")
    journal = m.group(1)
    if os.path.dirname(os.path.dirname(journal)) != GATE_SESSIONS or os.path.exists(os.path.join(os.path.dirname(journal), "session.json")):
        raise Red("PLANT crash: the crashed run left a saved session, or its journal is not under the gate's root")
    records, torn = _ls_journal(journal)
    runs, _lb = RLG.read(logs[1])
    if not torn or len(records) != 1 + 5 or runs:
        raise Red("the crashed run's journal is not a header, five records and a torn tail, or the crash left a ledger line")
    cp, child = _ls_run(["--resume", journal, "--keys", "S,ESC"], logs)
    if cp.returncode != 0 or child is None or "a torn final journal record was dropped" not in cp.stdout:
        raise Red("the journal did not recover into a saved session: " + (cp.stderr.strip() or cp.stdout.strip()))
    c = LS.check_saved(read(child), ROOT)
    lin = c["live"]["lineage"]
    if ([x["witness"] for x in c["data"]["log"][:5]] != [r["witness"] for r in records[1:]] or len(c["data"]["log"]) != 6
            or (lin["source"], lin["parent_events"], lin["torn"], lin["parent_head"]) != ("journal", 5, 1, records[-1]["head"])):
        raise Red("the recovered session is not the journal's five events and one more, with the journal as its lineage")
    code, out, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", child])
    if code != 0:
        raise Red("the workshop does not verify the recovered session: " + err.strip())
    raw = read(journal)
    lines = raw.split(b"\n")
    bad = []
    mid = lines[:]
    mid[2] = mid[2].replace(b'"witness":"', b'"witness":"0', 1)
    bad.append(("a bad middle record", b"\n".join(mid)))
    before_tail = lines[:]
    before_tail[-1 - 1] = before_tail[-2].replace(b'"witness":"', b'"witness":"0', 1)
    bad.append(("a bad record before the torn tail", b"\n".join(before_tail)))
    bad.append(("no header", b"\n".join(lines[1:])))
    rec = json.loads(lines[3].split(b" ", 3)[3].decode("utf-8"))
    rec["head"] = "0" * 64
    pl = json.dumps(rec, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    wrong = lines[:]
    wrong[3] = b"R %d %s %s" % (len(pl), hashlib.sha256(pl).hexdigest().encode(), pl)
    bad.append(("a record head that does not fold", b"\n".join(wrong)))
    for why, blob in bad:
        jp = os.path.join(BUILD, "livesession-bad.vsj")
        with open(jp, "wb") as fh:
            fh.write(blob)
        cp, child = _ls_run(["--resume", jp, "--keys", "ESC"], logs)
        if cp.returncode != 2 or "LIVESESSION-JOURNAL-CORRUPT" not in cp.stderr or child is not None:
            raise Red("a journal with %s did not refuse LIVESESSION-JOURNAL-CORRUPT" % why)
    return ("a run that died after five journaled events left a torn final record, no saved session and no ledger line; "
            "resuming from its journal dropped the torn record, recovered the five events and saved them with one more, "
            "the journal named as the lineage, verified by the workshop; a bad middle record, a missing header and a "
            "record head that does not fold, and a bad record just before the torn tail each refuse")


def livesession_classify():
    """The loader's classification: a consistently forged frame witness under the same shell refuses TAMPERED; a shell
    built from the same sources with CRLF line endings names the same renderer and loads as LOAD; a shell whose render
    sources differ only by a comment loads the saved session as LOAD with a different renderer and seals its
    continuation naming both identities; a shell whose render source changes the frame digest refuses
    DIFFERENT-RENDERER; a forged edit witness refuses TAMPERED under a different identity; an altered seal, a changed base
    and an off-chain lineage refuse before any replay."""
    import livesession as LS
    import refusallog as RL
    need_rustc()
    if SHELL_EXE is None:
        raise Red("the shell was not built")
    logs = _ls_logs("classify")
    parent = _ls_script_a(logs)
    text = read(parent).decode("utf-8")
    pr = read(os.path.join(SHELL, "present.rs")).decode("utf-8")
    if pr.count(LIVESESSION_DIGEST_SITE) != 1:
        raise Red("the digest site for the different-renderer shell is not unique in present.rs")
    comment = compile_rs(SHELL, "main.rs", "shell-ls-comment", {"present.rs": pr + "\n// LIVE-SESSION-0 gate: a comment; the rendering is unchanged\n"})
    digest = compile_rs(SHELL, "main.rs", "shell-ls-digest", {"present.rs": pr.replace(
        LIVESESSION_DIGEST_SITE, "let digest = { let mut f2 = frame.clone(); f2[0] ^= 1; frame_digest(&f2) };")})
    frame_forged, _k = _ls_forge_witness(text, "move")
    edit_forged, _k2 = _ls_forge_witness(text, "edit")
    s = text.rfind('"seal": "') + 9
    bad_seal = text[:s] + ("0" if text[s] != "0" else "1") + text[s + 1:]
    w = json.loads(text)["data"]["base"]["W"]
    changed_base = _ls_reseal(text.replace('"W":"%s"' % w, '"W":"%s"' % ("0" * 64), 1))
    off_chain = _ls_reseal(text.replace('"lineage":null', '"lineage":{"parent_head":"%s","parent_events":3,"source":"session","parent_sha256":"%s","torn":0}' % ("0" * 64, "0" * 64), 1))
    cases = [("a forged frame witness, same shell", frame_forged, None, "LIVESESSION-TAMPERED"),
             ("a forged frame witness, a digest-changing shell", text, digest, "LIVESESSION-DIFFERENT-RENDERER"),
             ("a forged edit witness, a different identity", edit_forged, comment, "LIVESESSION-TAMPERED"),
             ("an altered seal", bad_seal, None, "LIVESESSION-CORRUPT"),
             ("a changed base", changed_base, None, "LIVESESSION-BASE"),
             ("an off-chain lineage", off_chain, None, "LIVESESSION-LINEAGE")]
    for i, (why, body, exe, code_) in enumerate(cases):
        p = _ls_write("case%d" % i, body)
        cp, child = _ls_run(["--resume", p, "--keys", "ESC"], logs, exe)
        if cp.returncode != 2 or code_ not in cp.stderr or child is not None:
            raise Red("%s did not refuse %s: %s" % (why, code_, (cp.stderr.strip() or cp.stdout.strip())[:200]))
    crlf = compile_rs(SHELL, "main.rs", "shell-ls-crlf", {"present.rs": pr.replace("\r\n", "\n").replace("\n", "\r\n")})
    cp, child = _ls_run(["--resume", parent, "--keys", "ESC"], logs, crlf)
    if cp.returncode != 0 or child is None or "(LOAD)" not in cp.stdout:
        raise Red("a checkout with CRLF line endings does not name the same renderer: " + (cp.stderr.strip() or cp.stdout.strip())[:200])
    cp, child = _ls_run(["--resume", parent, "--keys", "ESC"], logs, comment)
    if cp.returncode != 0 or child is None or "(LOAD-DIFFERENT-RENDERER)" not in cp.stdout:
        raise Red("a comment-only render change did not load the session as LOAD with a different renderer: " + cp.stderr.strip())
    live = LS.check_saved(read(child), ROOT)["live"]
    parent_id = json.loads(text)["live"]["renderer"]
    if (live["resumed"] != {"classification": "LOAD-DIFFERENT-RENDERER", "parent_renderer": parent_id}
            or live["renderer"] == parent_id or live["renderer"] == LS.renderer_id(ROOT)):
        raise Red("the continuation does not name the parent's renderer and its own, different, one")
    records, rbad = RL.read(logs[0])
    got = sorted(r["reason_code"] for r in records if r["operation"] == "livesession")
    if rbad or got != sorted(c[3] for c in cases):
        raise Red("the classification refusals are not one refusal-log record each: %s" % got)
    return ("the loader classifies as registered: a consistent frame forgery under the same shell is TAMPERED; CRLF line "
            "endings name the same renderer (LOAD); a digest-changing render source is DIFFERENT-RENDERER; a comment-only "
            "change loads as LOAD with a different "
            "renderer and its continuation names both identities; a forged edit witness is TAMPERED under a different "
            "identity (no renderer explains a content); an altered seal, a changed base and an off-chain lineage refuse "
            "before any replay; one refusal-log record each")


def livesession_sealer():
    """The sealer on the gate's saved session: it checks the seal, base, fold and counts, has the workshop verify the
    file, and seals a RECORD-0 copy citing LIVE-SESSION-0 and LIVE-INPUT-0 that shell playback and the workshop both
    replay to the same head; a bad seal, a changed base, a head that is not the fold, counts off and an off-chain
    lineage are refused."""
    import livesession as LS
    need_rustc()
    if SHELL_EXE is None or SESSIONWALK_EXE is None:
        raise Red("the shell or the workshop's sessionwalk was not built")
    logs = _ls_logs("sealer")
    path = _ls_script_a(logs)
    raw = read(path)
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    code, out, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", path])
    try:
        rec = LS.seal_livesession(raw, reg, "gate-mock", out.strip())
    except LS.Refuse as e_:
        raise Red("the sealer refused the gate's saved session: %s" % e_)
    envelope.validate(rec)
    prov = rec["provenance"]
    if ((prov["preregistered"]["chain_hash"], prov["loop"]["chain_hash"]) != (reg["LIVE-SESSION-0"]["chain_hash"], reg["LIVE-INPUT-0"]["chain_hash"])
            or prov["saved_sha256"] != sha256(raw) or "the same as the one it was made with" not in rec["reading"]):
        raise Red("the record does not cite LIVE-SESSION-0 and LIVE-INPUT-0, the saved bytes, and the same renderer")
    out_p = os.path.join(BUILD, "livesession-record.json")
    envelope.write(out_p, rec)
    code, pout, perr = _ls_verify(SHELL_EXE, ["playback", "--session", out_p])
    code2, wout, werr = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", out_p])
    if code != 0 or ("playback head " + rec["data"]["head"]) not in pout or code2 != 0 or "SESSIONWALK verify OK" not in wout:
        raise Red("the sealed copy does not replay in shell playback and the workshop to its head")
    text = raw.decode("utf-8")
    d = json.loads(text)["data"]
    bad = [("a bad seal", text.replace('"seal": "', '"seal": "0', 1)),
           ("a changed base", _ls_reseal(text.replace('"M":"%s"' % d["base"]["M"], '"M":"%s"' % ("1" * 64), 1))),
           ("a head that is not the fold", _ls_reseal(text.replace('"head": "%s"' % d["head"], '"head": "%s"' % ("2" * 64), 1))),
           ("counts off", _ls_reseal(text.replace('"moves": %d' % d["moves"], '"moves": %d' % (d["moves"] + 1), 1))),
           ("an off-chain lineage", _ls_reseal(text.replace('"lineage":null', '"lineage":{"parent_head":"%s","parent_events":2,"source":"session","parent_sha256":"x","torn":0}' % ("3" * 64), 1)))]
    for why, body in bad:
        try:
            LS.seal_livesession(body.encode("utf-8"), reg, "gate", "")
            raise Red("the sealer accepted %s" % why)
        except LS.Refuse:
            pass
    return ("the sealer checks the gate's saved session (seal, base, fold, counts), seals a RECORD-0 copy citing LIVE-SESSION-0 "
            "and LIVE-INPUT-0 that shell playback and the workshop both replay to head %s...; %d malformed sessions are "
            "refused" % (rec["data"]["head"][:12], len(bad)))


def livesession_fence():
    """Durability is claimed only where it is earned: each journal record is written and flushed before it is counted,
    the journal only appends; the saved file is a flushed temporary moved over the destination atomically (MoveFileEx
    with both registered flags on Windows), then read back and verified before the run says saved and ends 0; every
    refusal ends the ledger; the loader's steps run in the registered order; the session's reader opens no file and the
    sink is handed each event after it is appended; LIVE-INPUT-0's loop and command are unchanged; the host window loads
    before it opens, observes the focus without ruling on it, writes nothing itself, and is appended after LIVE-INPUT-0's
    section; build/sessions/ is gitignored and the gate's sessions stay in verify/build; a windowless build refuses."""
    rs = read(os.path.join(SHELL, "livesession.rs")).decode("utf-8")
    put = src_span(rs, "    fn put(&mut self, payload: &str)", "\n    }\n")
    order = [put.find(t) for t in ("self.file.write_all(", "self.file.sync_data()", "self.records += 1;")]
    if -1 in order or order != sorted(order) or "OpenOptions::new().create_new(true).append(true).open(path)" not in rs:
        raise Red("a journal record is counted before it is flushed, or the journal does not only append")
    for tok in (".truncate(", "set_len(", "remove_file", "remove_dir", "File::create"):
        if tok in rs:
            raise Red("shell/livesession.rs contains %r: nothing is truncated or removed" % tok)
    ws = src_span(rs, "fn write_saved(", "\n}\n")
    order = [ws.find(t) for t in ("create_new(true).write(true).open(&tmp)", "f.write_all(text.as_bytes())", "f.sync_all()", "replace::atomic_replace(&tmp, dst)?;")]
    win = src_span(rs, '#[cfg(target_os = "windows")]\nmod replace {', "\n}\n")
    if (-1 in order or order != sorted(order) or "const MOVEFILE_REPLACE_EXISTING: u32 = 0x1;" not in win or "const MOVEFILE_WRITE_THROUGH: u32 = 0x8;" not in win
            or "MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)" not in win or "d.sync_all()" not in rs):
        raise Red("the saved file is not a flushed temporary moved over the destination atomically with the registered flags")
    # re-pinned on purpose with LIVE-AUTHOR-0: go is LIVE-INPUT-0's binding over go_with, which holds the run; and with
    # HOLD-WALK-0: go passes no held set, so LIVE-SESSION-0 binds no repeat
    if "go_with(s, p, crate::liveinput::bind, None).0" not in src_span(rs, "pub fn go<S: ExactSurface + Keys + Focus>(", "\n}\n"):
        raise Red("LIVE-SESSION-0's go is not LIVE-INPUT-0's binding over go_with")
    # re-pinned on purpose with SIM-TICK-0: the seal is `finish`, shared by the loop's run (go_with: the loop, the focus,
    # then finish) and the tick run; the order inside it is the registered one, after the reference's certification
    go = src_span(rs, "pub fn go_with<S: ExactSurface + Keys + Focus>(", "\n}\n")
    fin = src_span(rs, "fn finish(p: Prepared, ended: &str, focus: &str) -> i32 {", "\n}\n")
    order_go = [go.find(t) for t in ("crate::liveinput::run_with(s, &mut session, surface, binding, hold)", "let focus = s.focus();", "finish(Prepared {")]
    order = [fin.find(t) for t in ("saved_text(&session, &base, &live_json)", "write_saved(&dst, &text, &plant)",
                                   "fs::read(&dst)", "load(&dst)", 'println!("[livesession] saved and verified:', "crate::runledger::end(0);")]
    if (-1 in order or order != sorted(order) or -1 in order_go or order_go != sorted(order_go)
            or rs.count("saved and verified:") != 1 or rs.count("crate::runledger::end(0);") != 1
            or not all(t in fin for t in ("if b != text.as_bytes() {", "l.session.head() != session.head()", "l.session.content() != session.content()",
                                          "a.iter().zip(b2.iter()).any(|(x, y)| x.witness != y.witness || x.param != y.param)"))):
        raise Red("the run says saved, or ends 0, other than after the saved file was read back and verified against the live session")
    prep = src_span(rs, "pub fn prepare(plan: Plan)", "\n}\n")
    if (not prep.split("{", 1)[1].lstrip().startswith('crate::runledger::begin("livesession", plan.surface);')
            or len(re.findall(r"return Err\(refuse_run\(", prep)) != prep.count("return Err(") or "crate::runledger::end(2);" not in src_span(rs, "fn refuse_run(", "\n}\n")
            or len(re.findall(r"return refuse_run\(", fin)) != 3 or "refuse_run(" in go):
        raise Red("the run does not begin its ledger first, or a refusal does not end it")
    ld = src_span(rs, "pub fn load(path: &str)", "\nfn saved_event(")
    order = [ld.find(t) for t in ("read_journal(&bytes)?", "check_seal(&bytes)?;", "chain_heads(", "LIVESESSION-LINEAGE", "renderer_id()", "LiveSession::new(", "s.push_move(", "LIVESESSION-DIFFERENT-RENDERER")]
    bases = [m_.start() for m_ in re.finditer(r"read_base\(", ld)]
    if (-1 in order or order != sorted(order) or len(bases) != 2 or not order[0] < bases[0] < order[1] < bases[1] < order[2]
            or "let renderable = frame && camera_ok;" not in ld or "if renderable && !same" not in ld
            or 'heads[n as usize] != l.get("parent_head").s()' not in ld or "None if last => torn = 1," not in rs):
        raise Red("the loader does not go integrity, identity, replay, witnesses, classification, with only a frame renderable")
    sealer = read(os.path.join(ROOT, "verify", "livesession.py")).decode("utf-8")
    # re-pinned on purpose with MOUSE-LOOK-0: go_look records its surface's observation too (the second read), and the
    # sealer still never reads it
    if rs.count(".focus()") != 2 or '["focus"]' in sealer or '.get("focus")' in sealer or '"focus"' in sealer:
        raise Red("the focus observation is read other than to be recorded")
    pb = read(os.path.join(SHELL, "playback.rs")).decode("utf-8")
    rd = pb[pb.index("// ================================================================== LIVE-SESSION-0 (appended)"):]
    li = pb[pb.index("// ================================================================== LIVE-INPUT-0 (appended)"):pb.index("// ================================================================== LIVE-SESSION-0 (appended)")]
    mv, ed = src_span(li, "pub fn push_move(", "\n    }\n"), src_span(li, "pub fn push_edit_cell(", "\n    }\n")
    if (any(t in rd for t in ("fs::", "File::", "write(")) or li.count("self.handed();") != 2
            or any(not (0 <= f.find("self.log.push(") < f.find("self.handed();")) for f in (mv, ed))
            or "pub fn with_sink(mut self, sink: Box<dyn EventSink>) -> LiveSession {" not in li):
        raise Red("the session's reader opens a file, or the sink is not handed each event after it is appended")
    main_src = read(os.path.join(SHELL, "main.rs")).decode("utf-8")
    sw = src_span(main_src, '"livesession-selftest" | "livesession-window" => {', "\n        other => ")
    if 'plant: String::new(), surface: "gdi"' not in sw or "livesession::go(&mut surf, prepared)" not in sw:
        raise Red("the host window's run is planted, or the selftest does not run the shared code")
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    i_li, i_ls = tail.find("LIVE-INPUT-0 (appended)"), tail.find("LIVE-SESSION-0 (appended)")
    sect = w32_section(tail, "LIVE-SESSION-0 (appended)")
    # re-pinned on purpose with LIVE-AUTHOR-0: the window takes its binding; LIVE-SESSION-0's passes LIVE-INPUT-0's
    if "session_window(plan, crate::liveinput::bind, None)" not in src_span(sect, "pub fn livesession_window(", "\n}\n"):
        raise Red("LIVE-SESSION-0's window is not LIVE-INPUT-0's binding over the shared window")
    win = src_span(sect, "fn session_window(", "\n}\n")
    order = [win.find(t) for t in ("SetProcessDPIAware()", "crate::livesession::prepare(plan)", "= show_window(", "crate::livesession::go_with(&mut keys, prepared, binding, hold)")]
    if (i_li < 0 or i_ls < i_li or -1 in order or order != sorted(order) or "call: 1," not in sect or "set_call(" in win
            or any(t in sect for t in ("fs::", "File::", "write_raw(", "WM_KEYDOWN", "StretchDIBits", "qpc()"))
            or "unsafe { GetForegroundWindow() } == self.hwnd" not in sect):
        raise Red("the host window is not LIVE-INPUT-0's window and keys with the focus observed, loading before it opens and writing nothing")
    gi = read(os.path.join(ROOT, ".gitignore")).decode("utf-8").splitlines()
    if "build/sessions/" not in gi or os.environ.get(LIVESESSION_ENV) != GATE_SESSIONS or os.path.dirname(GATE_SESSIONS) != BUILD:
        raise Red("build/sessions/ is not gitignored, or the gate's sessions are not kept in verify/build")
    if SHELL_EXE is not None:
        cp = subprocess.run([SHELL_EXE, "livesession-window"], capture_output=True, text=True, cwd=ROOT)
        if cp.returncode == 0 or "SHELL-NO-WINDOW" not in cp.stderr:
            raise Red("a windowless build did not refuse livesession-window with SHELL-NO-WINDOW")
    return ("durability is claimed only where earned: each journal record is flushed before it is counted and the journal "
            "only appends; the saved file is a flushed temporary moved atomically (MoveFileEx with both flags on Windows), "
            "then read back and verified before the run says saved and ends 0; every refusal ends the ledger; the loader "
            "runs in the registered order; the reader opens no file and the sink sees each event after it is appended; the "
            "host window loads first, observes the focus without ruling on it and writes nothing; build/sessions/ is "
            "gitignored; a windowless build refuses")


# ------------------------------------------------------------------ LIVE-AUTHOR-0
LIVEAUTHOR_PALETTE = [(96, 80, 64), (176, 176, 176), (178, 58, 48), (56, 104, 168), (72, 136, 72), (200, 176, 96),
                      (120, 80, 152), (232, 232, 224)]
# script C from 28,28,N: (key, outcome, picture) — the outcome a typed event (kind, command or spec, camera after it);
# the picture registers, from the renderer's own output, whether that state's pixels differ from the state before
# ("changed") or not ("same"); "tile-offscreen" marks a tile edit of a class that is not on screen there
_C = lambda rgb: "%d,%d,%d" % rgb
LIVEAUTHOR_SCRIPT = ("28,28,N", [
    ("5", ("edit", "tile:floor," + _C(LIVEAUTHOR_PALETTE[0]), "28,28,N"), "same"),   # the floor is off screen facing north
    ("LEFT", ("move", "L", "28,28,W"), "changed"),
] + [("5", ("edit", "tile:floor," + _C(LIVEAUTHOR_PALETTE[i % 8]), "28,28,W"), "changed") for i in range(1, 9)] + [
    ("1", ("edit", "tile:wall0," + _C(LIVEAUTHOR_PALETTE[0]), "28,28,W"), "changed"),
    ("2", ("edit", "tile:wall1," + _C(LIVEAUTHOR_PALETTE[0]), "28,28,W"), "same"),   # wall1 is off screen facing west
    ("3", ("edit", "tile:wall2," + _C(LIVEAUTHOR_PALETTE[0]), "28,28,W"), "changed"),
    ("4", ("edit", "tile:wall3," + _C(LIVEAUTHOR_PALETTE[0]), "28,28,W"), "changed"),
    ("RIGHT", ("move", "R", "28,28,N"), "changed"),
    ("SPACE", ("edit", "cell:28,27,.", "28,28,N"), "changed"),
    ("W", ("move", "F", "28,27,N"), "changed"),
    ("ESC", "end", None)])
LIVEAUTHOR_RESUME = ("5,ESC", [("edit", "tile:floor," + _C(LIVEAUTHOR_PALETTE[1]), "28,27,N")])


def _la_run(args, logs, out=None):
    env = dict(os.environ, **{REFUSALLOG_ENV: logs[0], RUNLEDGER_ENV: logs[1], LIVESESSION_ENV: GATE_SESSIONS})
    extra = ["--out", out] if out else []
    cp = subprocess.run([SHELL_EXE, "live-selftest"] + args + extra, capture_output=True, text=True, cwd=ROOT, env=env)
    m = re.search(r"saved and verified: (.+?session\.json)", cp.stdout)
    raw = None
    if out and os.path.exists(out):
        with open(out, encoding="utf-8") as fh:
            raw = json.load(fh)["data"]
        os.remove(out)
    return cp, (m.group(1) if m else None), raw


def _la_script_c(logs):
    camera, steps = LIVEAUTHOR_SCRIPT
    out = os.path.join(BUILD, "liveauthor-c.json")
    cp, path, raw = _la_run(["--camera", camera, "--keys", ",".join(k for k, _o, _p in steps)], logs, out)
    if cp.returncode != 0 or path is None or raw is None or "live court OK" not in cp.stdout:
        raise Red("script C did not run to a saved and verified live session: " + (cp.stderr.strip() or cp.stdout.strip()))
    return path, raw


def liveauthor_preregistered():
    """LIVE-AUTHOR-0's method is locked: one live editor under the authoring binding (LIVE-INPUT-0's keys plus 1-5 for
    the tile classes), the palette's next colour read from the session's own M, commit-only, the pixels witnessed per
    state, the camera control condition and its converse. The palette and the binding must be the registered ones."""
    e = locked_entry("LIVE-AUTHOR-0", {
        "the last authoring primitive, one live editor": ("hyp", ("the last authoring-primitive slice", "one live editor command", "wall0, wall1, wall2, wall3 and floor", "fixed, registered palette of 8 colours", "the same key over the same m always gives the same edit")),
        "commit-only; pixels; the control": ("hyp", ("commit-only: no preview", "the loop's only way to change m is to append the edit", "witnessed by the reference composite's sha256", "w and m stay unchanged", "exactly when the class is on screen")),
        "the gate": ("succ", ("the floor cycled through the whole palette and back to its first colour", "the class keys stay unbound in liveinput-selftest", "and not for the off-screen control", "its first presented picture is the parent's last", "holds no colour or tile state")),
        "no stray colour, no preview, no second authority": ("fail", ("an edit whose colour is not the palette's next", "a colour shown before it is appended", "w changed by a tile edit", "pixels unchanged by a turn", "liveinput-* or livesession-* changed in behaviour")),
        "scope": ("lims", ("a solid fill of a whole class", "the frame witness does not see colour", "registered per scripted state", "no continuous movement", "8 fixed colours")),
    })
    la = read(os.path.join(SHELL, "liveauthor.rs")).decode("utf-8")
    pal = [tuple(int(x) for x in m_.groups()) for m_ in re.finditer(r"\[(\d+), (\d+), (\d+)\],\s+//", src_span(la, "pub const PALETTE", "\n];"))]
    if pal != LIVEAUTHOR_PALETTE:
        raise Red("the shell's palette is not the registered one: %s" % pal)
    b = src_span(la, "pub fn bind(vk: u32) -> Action {", "\n}\n")
    if ("0x31..=0x35 => Action::Tile((vk - 0x31) as u8)," not in b or "_ => crate::liveinput::bind(vk)," not in b
            or b.count("=>") != 2):
        raise Red("the live editor's binding is not LIVE-INPUT-0's plus 1-5 for the tile classes")
    nc = src_span(la, "pub fn next_colour(", "\n}\n")
    if "Some(i) => PALETTE[(i + 1) % PALETTE.len()]," not in nc or "None => PALETTE[0]," not in nc:
        raise Red("a class key's colour is not the palette's next after the current, or its first")
    pb = read(os.path.join(SHELL, "playback.rs")).decode("utf-8")
    if 'pub const TILE_CLASSES: [&str; 5] = ["wall0", "wall1", "wall2", "wall3", "floor"];' not in pb:
        raise Red("the tile classes are not wall0..wall3, floor in the tiles file's order")
    return ("LIVE-AUTHOR-0's method is locked (hash %s): the live editor is LIVE-INPUT-0's binding plus 1-5 for wall0..wall3 "
            "and floor; a class key's colour is the registered 8-colour palette's next after the class's current colour, "
            "or its first; the palette and the class order are the registered ones" % e["chain_hash"][:8])


def liveauthor_binding():
    """Binding determinism for the live editor: script C's presses become exactly their registered outcomes — the floor
    painted off screen, a turn, the floor cycled through the whole palette back to its first colour, each wall class
    painted, a turn back, a cell opened and walked through, Esc — at their registered compositions, with the tile specs
    in palette order; the class keys stay unbound in liveinput-selftest; the run is saved and verified."""
    need_rustc()
    if SHELL_EXE is None:
        raise Red("the shell was not built")
    logs = _ls_logs("liveauthor-binding")
    path, raw = _la_script_c(logs)
    camera, steps = LIVEAUTHOR_SCRIPT
    saved = json.loads(read(path).decode("utf-8"))["data"]["log"]
    typed = [(x["kind"], x.get("command", x.get("spec")), x.get("camera")) for x in saved]
    want_ev = [(k, q, c_ if k == "move" else None) for _k, o, _p in steps if isinstance(o, tuple) for (k, q, c_) in [o]]
    if typed != want_ev:
        raise Red("script C's events are not the registered ones (a class, a colour or a camera): %r"
                  % (next((g, w) for g, w in zip(typed + [None] * 99, want_ev) if g != w),))
    got = [(t["key"], t["outcome"], t["composition"]) for t in raw["trace"]]
    want, n = [], 0
    for i, (k, o, _p) in enumerate(steps):
        want.append((k, "event %d" % n if isinstance(o, tuple) else o, LIVEINPUT_EVERY * i + 1))
        n += isinstance(o, tuple)
    if got != want:
        raise Red("script C's presses did not become their registered outcomes: %r" % (next((g, w) for g, w in zip(got + [None] * 99, want) if g != w),))
    c = raw["counts"]
    tiles = sum(1 for _k, o, _p in steps if isinstance(o, tuple) and o[1].startswith("tile:"))
    if (c["events"], c["edits"], c["moves"], c["unbound"], c["refused"], raw["ended"]) != (n, tiles + 1, 3, 0, 0, "escape"):
        raise Red("script C's counts are not the registered walk's: %s" % c)
    cp = subprocess.run([SHELL_EXE, "liveinput-selftest", "--keys", "1,2,3,4,5,ESC"], capture_output=True, text=True, cwd=ROOT,
                        env=dict(os.environ, **{REFUSALLOG_ENV: logs[0], RUNLEDGER_ENV: logs[1]}))
    if cp.returncode != 0 or cp.stdout.count("-> unbound (ignored)") != 5 or "edit tile:" in cp.stdout:
        raise Red("the class keys are not unbound in liveinput-selftest")
    return ("the live editor's binding on the mock: script C's %d presses became exactly their registered outcomes — %d tile "
            "edits in palette order (the floor cycled back to its first colour), a cell opened and walked through, two "
            "turns — saved and verified; in liveinput-selftest the class keys stay unbound" % (len(steps), tiles))


def liveauthor_authority():
    """The thing authored is the authority the next frame renders: for every tile edit W is unchanged, M is the base tiles
    with the log's tile edits applied, the frame witness is unchanged, and the pixels change exactly where script C
    registers the class on screen (and not for the two off-screen controls); for every turn W and M are unchanged while
    the pixels and the frame witness change; every state's presented frame is the one rendered from its own authority;
    the workshop's sessionwalk replays the saved log to the loop's witnesses, final content and head."""
    import livesession as LS
    need_rustc()
    if SHELL_EXE is None or SESSIONWALK_EXE is None:
        raise Red("the shell or the workshop's sessionwalk was not built")
    logs = _ls_logs("liveauthor-authority")
    path, raw = _la_script_c(logs)
    doc = LS.check_saved(read(path), ROOT)
    d = doc["data"]
    events = d["log"]
    camera, steps = LIVEAUTHOR_SCRIPT
    typed = [o for _k, o, _p in steps if isinstance(o, tuple)]
    pics = [p for _k, o, p in steps if isinstance(o, tuple)]
    if [(x["kind"], x.get("command", x.get("spec"))) for x in events] != [(k, q) for k, q, _c in typed]:
        raise Red("the saved log is not script C's events")
    lv0, tl0 = read(os.path.join(ORACLE, "levels", "witness.lvl")), read(os.path.join(ORACLE, "tiles", "identity.tiles"))
    lv, tl = lv0, tl0
    contents = [_sw_content(lv, tl)]
    for x in events:
        if x["kind"] == "edit":
            lv, tl = _sw_apply(lv, tl, x["spec"])
        contents.append(_sw_content(lv, tl))
    views, pixels = raw["views"], raw["pixels"]
    if len(views) != len(events) + 1 or len(pixels) != len(events) + 1:
        raise Red("the loop did not record a frame witness and the pixels for every state")
    shown = raw["shown"]
    if [k for k, _h in shown] != list(range(len(events) + 1)) or any(h != pixels[k] for k, h in shown):
        raise Red("a state's presented frame is not the one rendered from its own authority (what the loop handed the "
                  "call differs from the state's reference)")
    level_now = lv0
    for k, x in enumerate(events):
        moved = x["kind"] == "move"
        tile = x["kind"] == "edit" and x["spec"].startswith("tile:")
        if tile:
            if views[k + 1] != views[k]:
                raise Red("event %d (%s) moved the frame witness: a colour must not" % (k, x["spec"]))
            if contents[k + 1] == contents[k]:
                raise Red("event %d (%s) did not change M" % (k, x["spec"]))
        if moved and contents[k + 1] != contents[k]:
            raise Red("event %d, a camera-only move, changed W or M" % k)
        if moved and x["command"] in "LR" and (views[k + 1] == views[k] or pixels[k + 1] == pixels[k]):
            raise Red("event %d, a turn, did not change the frame witness and the pixels" % k)
        changed = pixels[k + 1] != pixels[k]
        if changed != (pics[k] == "changed"):
            raise Red("event %d (%s): the pixels %s, where script C registers them %s" % (k, x.get("spec", x.get("command")), "changed" if changed else "stayed", pics[k]))
    lvt, tlt = lv0, tl0
    for x in events:
        if x["kind"] == "edit" and x["spec"].startswith("tile:"):
            lvt, tlt = _sw_apply(lvt, tlt, x["spec"])
    if lvt != lv0:
        raise Red("the tile edits changed W")
    code, out, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", path])
    if code != 0 or "SESSIONWALK verify OK" not in out or (d["head"][:12] not in out):
        raise Red("the workshop's sessionwalk does not replay the live editor's saved log: " + err.strip())
    if contents[-1] != d["final_content"]:
        raise Red("W and M recomputed from the log are not the saved session's")
    offscreen = sum(1 for p, (k, q, _c) in zip(pics, typed) if q.startswith("tile:") and p == "same")
    return ("the thing authored is what the next frame renders: %d tile edits each changed M and left W and the frame "
            "witness alone, their pixels changing exactly where script C registers the class on screen (%d off-screen "
            "controls unchanged); the turns changed the pixels and the frame witness with W and M unchanged; the "
            "workshop's sessionwalk replays the saved log to its head" % (sum(1 for _k, q, _c in typed if q.startswith("tile:")), offscreen))


def liveauthor_persist():
    """Persistence: every tile edit was journaled as it was made (one record per saved event); script C's saved session
    verifies in the workshop; resuming it in live-selftest loads as LOAD and its
    first presented picture is the parent's last (the same pixels and frame witness); a tile edit after the resume is the
    palette's next for that class and is sealed into a child whose lineage lies on its own chain; the parent is
    unchanged."""
    import livesession as LS
    need_rustc()
    if SHELL_EXE is None or SESSIONWALK_EXE is None:
        raise Red("the shell or the workshop's sessionwalk was not built")
    logs = _ls_logs("liveauthor-persist")
    parent, raw = _la_script_c(logs)
    before = read(parent)
    pdoc = json.loads(before.decode("utf-8"))
    records, torn = _ls_journal(os.path.join(os.path.dirname(parent), "journal.vsj"))
    if (torn or not pdoc["live"]["journal"]["complete"]
            or [(r["k"], r["witness"]) for r in records[1:]] != [(i, x["witness"]) for i, x in enumerate(pdoc["data"]["log"])]):
        raise Red("the tile edits were not journaled as they were made: the journal is not one record per saved event")
    keys, want = LIVEAUTHOR_RESUME
    out = os.path.join(BUILD, "liveauthor-resume.json")
    cp, child, raw2 = _la_run(["--resume", parent, "--keys", keys], logs, out)
    if cp.returncode != 0 or child is None or raw2 is None or "(LOAD)" not in cp.stdout:
        raise Red("the live editor's saved session did not resume: " + (cp.stderr.strip() or cp.stdout.strip()))
    if (raw2["pixels"][0], raw2["views"][0]) != (raw["pixels"][-1], raw["views"][-1]):
        raise Red("the resumed session's first picture is not its parent's last: the authored look did not persist")
    if read(parent) != before:
        raise Red("resuming modified the parent")
    c = LS.check_saved(read(child), ROOT)
    n = len(json.loads(before.decode("utf-8"))["data"]["log"])
    new = [(x["kind"], x.get("command", x.get("spec")), x.get("camera", "")) for x in c["data"]["log"][n:]]
    if [(k, q) for k, q, _c in new] != [(k, q) for k, q, _c in want] or c["live"]["lineage"]["parent_events"] != n:
        raise Red("the edit after the resume is not the palette's next, or the child's lineage is not the parent's")
    code, out_, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", child])
    if code != 0:
        raise Red("the workshop does not verify the continued live session: " + err.strip())
    return ("the authored world persists: script C's saved session resumed as LOAD with its first picture the parent's last "
            "(pixels and frame witness), the next floor edit took the palette's next colour, the child's lineage is the "
            "parent's %d events, the workshop verifies it, and the parent is unchanged" % n)


def liveauthor_fence():
    """Commit-only, one pathway: the authoring module holds no colour, tile or preview state and makes no edit itself;
    the loop's Tile arm reads the class's colour from the session and appends push_edit_tile, then renders the reference
    of the resulting state, like every other event; the session's tile edit applies, folds and hands to the sink like a
    cell edit; the live command runs LIVE-SESSION-0's go_with under the authoring binding, and LIVE-INPUT-0 and
    LIVE-SESSION-0 keep their own bindings; the host window is LIVE-SESSION-0's window under the binding, appended after
    its section; a windowless build refuses live-window."""
    la = read(os.path.join(SHELL, "liveauthor.rs")).decode("utf-8")
    code_ = "\n".join(ln for ln in la.splitlines() if not ln.lstrip().startswith("//"))
    for tok in ("static", "Vec<", "fs::", "push_edit", "LiveSession", "Cell<", "mut "):
        if tok in code_:
            raise Red("the authoring module contains %r: it holds no state and makes no edit" % tok)
    li = read(os.path.join(SHELL, "liveinput.rs")).decode("utf-8")
    runf = src_span(li, "pub fn run<S: ExactSurface + Keys>(", "\npub fn summary(")
    # re-pinned on purpose with HOLD-WALK-0: LIVE-INPUT-0's run passes no held set
    if "run_with(s, session, surface, bind, None)" not in src_span(li, "pub fn run<S: ExactSurface + Keys>(", "\n}\n"):
        raise Red("LIVE-INPUT-0's run is not its own binding over the shared loop")
    arm = src_span(runf, "Action::Tile(class) => {", "\n                }\n")
    order = [arm.find(t) for t in ("crate::liveauthor::next_colour(session.tile_rgb(class))", "session.push_edit_tile(class, rgb)", "reference(session, None)?", "live.pixels.push(r.4);")]
    before = arm[:arm.find("session.push_edit_tile(class, rgb)")]
    if -1 in order or order != sorted(order) or any(t in before for t in ("scene", "render", "present", "reference(", "blit", "expected")):
        raise Red("the Tile arm does not read the session's colour, append the edit, then render the resulting state")
    pb = read(os.path.join(SHELL, "playback.rs")).decode("utf-8")
    # re-pinned on purpose with SIM-TICK-0: bounded at the next appended section (SIM-TICK-0's, which simtick-fence judges)
    sect = w32_section(pb, "// ================================================================== LIVE-AUTHOR-0 (appended)")
    pt = src_span(sect, "pub fn push_edit_tile(", "\n    }\n")
    order = [pt.find(t) for t in ("apply_spec(&mut self.level, &mut self.tiles, &spec);", "self.content = content_hex(&self.level, &self.tiles);",
                                  "self.head = fold(&self.head, b'E', &self.content);", "self.log.push(", "self.handed();")]
    if -1 in order or order != sorted(order) or sect.count("&mut self") != 3 or any(t in sect for t in ("fs::", "File::")):
        raise Red("the session's tile edit is not apply, content, fold, append, hand — the cell edit's own path")
    ls = read(os.path.join(SHELL, "livesession.rs")).decode("utf-8")
    if ("go_with(s, p, crate::liveinput::bind, None).0" not in src_span(ls, "pub fn go<S: ExactSurface + Keys + Focus>(", "\n}\n")
            or "crate::liveinput::run_with(s, &mut session, surface, binding, hold)" not in ls or "s.push_edit_tile(class, rgb)" not in ls):
        raise Red("LIVE-SESSION-0's run is not its own binding over go_with, or the loader does not replay tile edits through the session")
    main_src = read(os.path.join(SHELL, "main.rs")).decode("utf-8")
    sw = src_span(main_src, '"live-selftest" | "live-window" => {', "\n        other => ")
    # re-pinned on purpose with HOLD-WALK-0: the live editor runs with HOLD-WALK-0's held set (holdwalk-fence judges it)
    if "livesession::go_with(&mut surf, prepared, liveauthor::bind, Some(holdwalk::held))" not in sw or 'plant: String::new(), surface: "gdi"' not in sw:
        raise Red("the live command does not run LIVE-SESSION-0's go_with under the authoring binding")
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    i_ls, i_la = tail.find("LIVE-SESSION-0 (appended)"), tail.find("LIVE-AUTHOR-0 (appended)")
    sect = w32_section(tail, "LIVE-AUTHOR-0 (appended)")
    lw = src_span(sect, "pub fn live_window(", "\n}\n")
    if i_ls < 0 or i_la < i_ls or "session_window(plan, crate::liveauthor::bind, Some(crate::holdwalk::held))" not in lw or any(t in sect for t in ("fs::", "File::", "WM_", "set_call(")):
        raise Red("the live editor's window is not LIVE-SESSION-0's window under the authoring binding, appended after its section")
    if SHELL_EXE is not None:
        cp = subprocess.run([SHELL_EXE, "live-window"], capture_output=True, text=True, cwd=ROOT)
        if cp.returncode == 0 or "SHELL-NO-WINDOW" not in cp.stderr:
            raise Red("a windowless build did not refuse live-window with SHELL-NO-WINDOW")
    return ("commit-only, one pathway: the authoring module holds no colour, tile or preview state and makes no edit; the "
            "Tile arm reads the session's colour, appends push_edit_tile and renders the resulting state; the session's tile "
            "edit is the cell edit's own path (apply, content, fold, append, hand); the live command is LIVE-SESSION-0's "
            "go_with under the authoring binding while LIVE-INPUT-0 and LIVE-SESSION-0 keep theirs; the host window is "
            "LIVE-SESSION-0's under the binding; a windowless build refuses")

# ------------------------------------------------------------------ HOLD-WALK-0
# the held set, registered: W, A, S, D, Up, Left, Down, Right — the steps and the quarter turns (not Q/E, not edits)
HOLDWALK_HELD = [0x57, 0x41, 0x53, 0x44, 0x26, 0x25, 0x28, 0x27]
# script H from 28,28,N: groups of (key, outcome); a group is the presses one composition drains (joined by "/"); the
# outcome is a typed event (kind, command or spec, camera after it), "coalesced", "repeat" (ignored) or "end"
HOLDWALK_SCRIPT = ("28,28,N", [
    [("LEFT", ("move", "L", "28,28,W"))],
    [("W", ("move", "F", "27,28,W"))],
    [("W+", ("move", "F", "26,28,W"))],
    [("W+", ("move", "F", "25,28,W")), ("W+", "coalesced"), ("W+", "coalesced")],
    [("W+", ("move", "F", "24,28,W"))],
    [("5", ("edit", "tile:floor,96,80,64", "24,28,W"))],
    [("5+", "repeat")],                                          # holding a class key paints once
    [("Q+", "repeat")],                                          # a strafe is not in the held set
    [("A", ("move", "L", "24,28,S"))],
    [("W", ("move", "F", "24,28,S"))],                           # blocked: rock to the south
    [("W+", ("move", "F", "24,28,S"))],                          # a held step into rock is a blocked move, as pressed
    [("D+", ("move", "R", "24,28,W")), ("D+", "coalesced")],     # a held quarter turn (free look), one per composition
    [("D+", ("move", "R", "24,28,N"))],
    [("W+", ("move", "F", "24,27,N")), ("W", ("move", "F", "24,26,N"))],   # a fresh press is never coalesced
    [("W+", ("move", "F", "24,25,N")), ("A+", "coalesced")],     # one admitted repeat per composition, whichever key
    [("SPACE", ("edit", "cell:24,24,#", "24,25,N"))],
    [("SPACE+", "repeat")],                                      # holding Space toggles once
    [("W+", ("move", "F", "24,25,N"))],                          # into the cell just closed: blocked
    [("ESC", "end")]])
HOLDWALK_COUNTS = {"keys": 24, "repeats": 16, "walked": 9, "coalesced": 4, "events": 16, "moves": 14, "edits": 2,
                   "unbound": 0, "refused": 0}


def _hw_keys(groups):
    return ",".join("/".join(k for k, _o in g) for g in groups)


def _hw_pressed(groups):
    """The same walk pressed: each walked repeat typed as a fresh press, the coalesced and ignored repeats left out."""
    out = []
    for g in groups:
        for k, o in g:
            if isinstance(o, tuple) or o == "end":
                out.append(k.rstrip("+"))
    return ",".join(out)


def _hw_script_h(logs, tag="h"):
    camera, groups = HOLDWALK_SCRIPT
    out = os.path.join(BUILD, "holdwalk-%s.json" % tag)
    cp, path, raw = _la_run(["--camera", camera, "--keys", _hw_keys(groups)], logs, out)
    if cp.returncode != 0 or path is None or raw is None or "live court OK" not in cp.stdout:
        raise Red("script H did not run to a saved and verified live session: " + (cp.stderr.strip() or cp.stdout.strip()))
    return cp, path, raw


def holdwalk_preregistered():
    """HOLD-WALK-0's method is locked: a held W/A/S/D or arrow walks the one live editor, at most one admitted repeat per
    composition and the rest coalesced and counted, a fresh press never coalesced, no clock and no key state, the session
    unchanged. The held set in the shell must be the registered one: exactly the keys LIVE-INPUT-0 binds to a step or a
    quarter turn."""
    e = locked_entry("HOLD-WALK-0", {
        "vocabulary on the one live editor; the world stays discrete": ("hyp", ("vocabulary on the live editor", "not a new pathway", "the session, the renderer, replay, save and collision are unchanged", "w, a, s, d, up, down, left, right")),
        "one admitted repeat per composition, the rest coalesced": ("hyp", ("at most one repeat is admitted per composition", "coalesced — counted and traced, never an event, never silently dropped", "a fresh press is never coalesced", "holding space or a class key edits once")),
        "no clock, no key-up, no key state": ("hyp", ("keeps no clock, reads no key-up and holds no key state across compositions", "free look is a held quarter turn")),
        "the gate": ("succ", ("repeats = walked + coalesced + ignored", "no composition admits more than one repeat", "the same walk pressed", "is identical to the held walk's", "a held key's repeats are counted and bind nothing")),
        "no movement after release, no new session field": ("fail", ("an event made in a composition where no press arrived", "any new event kind, marker or field in the session", "a fresh press coalesced", "a coalesced repeat not counted")),
        "scope": ("lims", ("the input is continuous, the world is not", "mouse-look and any angle between them stay out", "the message's own repeat count is not read", "no walking-speed claim")),
    })
    hw = read(os.path.join(SHELL, "holdwalk.rs")).decode("utf-8")
    names = {"VK_UP": 0x26, "VK_LEFT": 0x25, "VK_DOWN": 0x28, "VK_RIGHT": 0x27}
    toks = [t.strip() for t in src_span(hw, "pub const HELD: [u32; 8] = [", "];")[len("pub const HELD: [u32; 8] = ["):].split(",")]
    got = [names[t] if t in names else int(t, 16) for t in toks]
    if got != HOLDWALK_HELD:
        raise Red("the shell's held set is not the registered one: %s" % [hex(x) for x in got])
    if src_span(hw, "pub fn held(vk: u32) -> bool {", "\n}\n").split("{", 1)[1].strip() != "HELD.contains(&vk)":
        raise Red("whether a repeat walks is decided by more than the key code's membership in the held set")
    li = read(os.path.join(SHELL, "liveinput.rs")).decode("utf-8")
    b = src_span(li, "pub fn bind(vk: u32) -> Action {", "\n}\n")
    arms = {}
    for m_ in re.finditer(r"^\s+([A-Z_0-9x| ]+) => Action::Move\(b'(\w)'\)", b, re.M):
        for t in m_.group(1).split("|"):
            t = t.strip()
            arms[{"VK_UP": 0x26, "VK_DOWN": 0x28, "VK_LEFT": 0x25, "VK_RIGHT": 0x27}.get(t) or int(t, 16)] = m_.group(2)
    steps_and_turns = sorted(k for k, c_ in arms.items() if c_ in "FBLR")
    if sorted(HOLDWALK_HELD) != steps_and_turns or any(arms.get(k) in ("Q", "E") for k in HOLDWALK_HELD):
        raise Red("the held set is not exactly the keys LIVE-INPUT-0 binds to a step or a quarter turn")
    la = read(os.path.join(SHELL, "liveauthor.rs")).decode("utf-8")
    if any(0x31 <= k <= 0x35 for k in HOLDWALK_HELD) or "0x31..=0x35 => Action::Tile((vk - 0x31) as u8)," not in la:
        raise Red("a class key is in the held set")
    return ("HOLD-WALK-0's method is locked (hash %s): the held set is W, A, S, D and the four arrows — exactly the keys "
            "LIVE-INPUT-0 binds to a step or a quarter turn, no strafe, no edit key — and whether a repeat walks is the "
            "key code's membership alone" % e["chain_hash"][:8])


def holdwalk_binding():
    """Script H's presses, delivered in groups, become exactly their registered outcomes at their registered compositions:
    the first held repeat in a composition walks, later ones are coalesced, a fresh press acts, a repeat outside the held
    set is ignored; the saved log is the registered events and the counts the registered ones; in liveinput-selftest and
    livesession-selftest a held key's repeats bind nothing."""
    need_rustc()
    if SHELL_EXE is None:
        raise Red("the shell was not built")
    logs = _ls_logs("holdwalk-binding")
    cp, path, raw = _hw_script_h(logs)
    camera, groups = HOLDWALK_SCRIPT
    want, n = [], 0
    for i, g in enumerate(groups):
        for k, o in g:
            want.append((k.rstrip("+"), k.endswith("+"), "event %d" % n if isinstance(o, tuple) else o, LIVEINPUT_EVERY * i + 1))
            n += isinstance(o, tuple)
    got = [(t["key"], t["repeat"], t["outcome"], t["composition"]) for t in raw["trace"]]
    if got != want:
        raise Red("script H's presses did not become their registered outcomes: %r" % (next((g, w) for g, w in zip(got + [None] * 99, want) if g != w),))
    saved = json.loads(read(path).decode("utf-8"))["data"]["log"]
    typed = [(x["kind"], x.get("command", x.get("spec")), x.get("camera")) for x in saved]
    want_ev = [(k, q, c_ if k == "move" else None) for g in groups for _k, o in g if isinstance(o, tuple) for (k, q, c_) in [o]]
    if typed != want_ev:
        raise Red("script H's saved events are not the registered ones: %r" % (next((g, w) for g, w in zip(typed + [None] * 99, want_ev) if g != w),))
    c = raw["counts"]
    got_c = {k: c.get(k) for k in HOLDWALK_COUNTS}
    if got_c != HOLDWALK_COUNTS or raw["ended"] != "escape":
        raise Red("script H's counts are not the registered ones: %s" % got_c)
    if "liveinput held repeats 16 walked 9 coalesced 4 ignored 3" not in cp.stdout:
        raise Red("the live editor did not report its held repeats (walked, coalesced, ignored)")
    for cmd, extra in (("liveinput-selftest", {}), ("livesession-selftest", {LIVESESSION_ENV: GATE_SESSIONS})):
        cp2 = subprocess.run([SHELL_EXE, cmd, "--keys", "LEFT,W,W+,W+,ESC"], capture_output=True, text=True, cwd=ROOT,
                             env=dict(os.environ, **{REFUSALLOG_ENV: logs[0], RUNLEDGER_ENV: logs[1]}, **extra))
        if (cp2.returncode != 0 or "liveinput keys 5 repeats 2 unbound 0 events 2 moves 2" not in cp2.stdout
                or "W+ ->" in cp2.stdout or "liveinput held" in cp2.stdout):
            raise Red("%s bound a held key's repeat: LIVE-INPUT-0 and LIVE-SESSION-0 must bind none" % cmd)
    return ("the held keys on the mock: script H's %d presses in %d groups became exactly their registered outcomes — %d "
            "repeats walked, %d coalesced, %d ignored (Space, a class key, Q), fresh presses never coalesced, blocked held "
            "steps appended as moves — saved and verified; in liveinput-selftest and livesession-selftest a held key's "
            "repeats bind nothing" % (HOLDWALK_COUNTS["keys"], len(groups), HOLDWALK_COUNTS["walked"], HOLDWALK_COUNTS["coalesced"],
                                     HOLDWALK_COUNTS["repeats"] - HOLDWALK_COUNTS["walked"] - HOLDWALK_COUNTS["coalesced"]))


def holdwalk_coalesce():
    """Coalescing is observable and bounded: from script H's trace, no composition admits more than one repeat, every
    coalesced press follows that composition's admitted repeat, no fresh press is coalesced, repeats are exactly walked +
    coalesced + ignored, and every saved event is one traced press's (no event without a press, so none after release)."""
    need_rustc()
    if SHELL_EXE is None:
        raise Red("the shell was not built")
    logs = _ls_logs("holdwalk-coalesce")
    _cp, path, raw = _hw_script_h(logs, "coalesce")
    trace = raw["trace"]
    per = {}
    for t in trace:
        per.setdefault(t["composition"], []).append(t)
    for comp, ts in per.items():
        walked = [i for i, t in enumerate(ts) if t["repeat"] and t["outcome"].startswith("event")]
        if len(walked) > 1:
            raise Red("composition %d admitted %d repeats" % (comp, len(walked)))
        for i, t in enumerate(ts):
            if t["outcome"] == "coalesced" and (not t["repeat"] or not walked or i < walked[0]):
                raise Red("composition %d coalesced a press that was not a repeat after its admitted one" % comp)
    rep = [t for t in trace if t["repeat"]]
    w_ = sum(1 for t in rep if t["outcome"].startswith("event"))
    co = sum(1 for t in rep if t["outcome"] == "coalesced")
    ig = sum(1 for t in rep if t["outcome"] == "repeat")
    c = raw["counts"]
    if (w_ + co + ig, w_, co) != (c["repeats"], c["walked"], c["coalesced"]) or co == 0 or w_ == 0:
        raise Red("the repeats are not exactly walked + coalesced + ignored, or a coalesced repeat was not counted")
    evs = [int(t["outcome"].split()[1]) for t in trace if t["outcome"].startswith("event")]
    saved = json.loads(read(path).decode("utf-8"))["data"]["log"]
    if evs != list(range(len(saved))) or c["events"] != len(saved):
        raise Red("an event was made without a press (movement after release), or a press's event is missing")
    return ("coalescing is observable and bounded: over script H's %d compositions with presses, none admitted more than "
            "one repeat, every coalesced press followed its composition's admitted repeat, no fresh press was coalesced, "
            "the %d repeats are %d walked + %d coalesced + %d ignored, and every one of the %d saved events is a traced "
            "press's" % (len(per), c["repeats"], w_, co, ig, len(saved)))


def holdwalk_equivalence():
    """The world stays discrete: the same walk pressed — each walked repeat typed as a fresh press, the coalesced and
    ignored repeats left out — saves a session whose data (base, log, head, final camera, final content) is byte-identical
    to the held walk's; the workshop's sessionwalk verifies both."""
    import livesession as LS
    need_rustc()
    if SHELL_EXE is None or SESSIONWALK_EXE is None:
        raise Red("the shell or the workshop's sessionwalk was not built")
    logs = _ls_logs("holdwalk-equivalence")
    _cp, held_path, _raw = _hw_script_h(logs, "equiv")
    camera, groups = HOLDWALK_SCRIPT
    cp, pressed_path, _r = _la_run(["--camera", camera, "--keys", _hw_pressed(groups)], logs)
    if cp.returncode != 0 or pressed_path is None:
        raise Red("the pressed walk did not run to a saved and verified session: " + (cp.stderr.strip() or cp.stdout.strip()))
    a, b = read(held_path), read(pressed_path)
    da, db = a[:a.index(b'\n "live": ')], b[:b.index(b'\n "live": ')]
    if da != db:
        raise Red("the held walk's saved data is not the pressed walk's: holding a key changed the session")
    for p_ in (held_path, pressed_path):
        LS.check_saved(read(p_), ROOT)
        code, out, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", p_])
        if code != 0 or "SESSIONWALK verify OK" not in out:
            raise Red("the workshop does not verify %s: %s" % (p_, err.strip()))
    d = json.loads(a.decode("utf-8"))["data"]
    return ("the world stays discrete: script H held and the same walk pressed (%d presses) save byte-identical session data "
            "— %d events, head %s…, final %s — and the workshop's sessionwalk verifies both"
            % (len(_hw_pressed(groups).split(",")), len(d["log"]), d["head"][:12], d["final_camera"]))


def holdwalk_fence():
    """No clock, no key-up, no key state: the held set is a pure function of the key code in a stateless module; the
    loop's admitted flag is declared inside each composition, and its repeat branch walks only the first held repeat and
    counts the rest; LIVE-INPUT-0's run, LIVE-SESSION-0's go and window pass no held set, the live command (selftest and
    window) passes HOLD-WALK-0's; the host window still reads only WM_KEYDOWN (no key-up) from LIVE-INPUT-0's section."""
    hw = read(os.path.join(SHELL, "holdwalk.rs")).decode("utf-8")
    code_ = "\n".join(ln for ln in hw.splitlines() if not ln.lstrip().startswith("//"))
    for tok in ("static", "mut ", "Vec<", "Cell<", "fs::", "Instant", "SystemTime", "ticks(", "unsafe", "Keys", "LiveSession"):
        if tok in code_:
            raise Red("the held-set module contains %r: it holds no state, reads no clock and touches no session" % tok)
    li = read(os.path.join(SHELL, "liveinput.rs")).decode("utf-8")
    runf = src_span(li, "pub fn run_with<S: ExactSurface + Keys>(", "\npub fn summary(")
    loop = runf[runf.index("    loop {"):]
    # re-pinned on purpose with MOUSE-LOOK-0: the presses this loop binds are named `presses` (the surface's, or none
    # under a tick source, where the tick's accumulator holds the held set instead)
    order = [loop.find(t) for t in ("let open = s.pump();", "let mut admitted = false;", "for (vk, repeat) in presses {", "if repeat {",
                                    "let walks = hold.map_or(false, |h| h(vk));", "if !walks || admitted {", "live.coalesced += 1;", "continue;",
                                    "admitted = true;", "live.walked += 1;", "match binding(vk) {")]
    if -1 in order or order != sorted(order) or li.count("let mut admitted") != 1 or runf.count("admitted = true;") != 1 \
            or "admitted" in runf[:runf.index("    loop {")]:
        raise Red("the admitted flag is not declared inside each composition, or the repeat branch does not walk only the "
                  "first held repeat and count the rest")
    if "ticks(" in runf or any(t in li for t in ("Instant", "SystemTime", "qpc")):
        raise Red("the loop reads a clock")
    if "run_with(s, session, surface, bind, None)" not in src_span(li, "pub fn run<S: ExactSurface + Keys>(", "\n}\n"):
        raise Red("LIVE-INPUT-0's run passes a held set")
    ls = read(os.path.join(SHELL, "livesession.rs")).decode("utf-8")
    if "go_with(s, p, crate::liveinput::bind, None).0" not in src_span(ls, "pub fn go<S: ExactSurface + Keys + Focus>(", "\n}\n"):
        raise Red("LIVE-SESSION-0's go passes a held set")
    main_src = read(os.path.join(SHELL, "main.rs")).decode("utf-8")
    sw = src_span(main_src, '"live-selftest" | "live-window" => {', "\n        other => ")
    if ("livesession::go_with(&mut surf, prepared, liveauthor::bind, Some(holdwalk::held))" not in sw
            or "liveinput::ScriptedKeys::grouped(mock, script, liveinput::MOCK_EVERY)" not in sw or "holdwalk" in main_src.replace(sw, "").replace('#[path = "holdwalk.rs"]\nmod holdwalk;', "")):
        raise Red("the held set reaches a command other than the live editor, or the live selftest does not run it")
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    ls_sect, la_sect = w32_section(tail, "LIVE-SESSION-0 (appended)"), w32_section(tail, "LIVE-AUTHOR-0 (appended)")
    if ("session_window(plan, crate::liveinput::bind, None)" not in src_span(ls_sect, "pub fn livesession_window(", "\n}\n")
            or "session_window(plan, crate::liveauthor::bind, Some(crate::holdwalk::held))" not in src_span(la_sect, "pub fn live_window(", "\n}\n")
            or tail.count("holdwalk") != 1):
        raise Red("LIVE-SESSION-0's window passes a held set, or the live editor's window does not pass HOLD-WALK-0's")
    if any(t in tail for t in ("WM_KEYUP", "0x0101", "GetAsyncKeyState", "GetKeyState")) or tail.count("self.pending.push(") != 1:
        raise Red("the host window reads a key-up or a key state: the held keys must come only from WM_KEYDOWN's repeat bit")
    return ("no clock, no key-up, no key state: the held set is the key code's membership in a stateless module; the "
            "admitted flag lives inside each composition and only the first held repeat walks, the rest counted; "
            "LIVE-INPUT-0's run and LIVE-SESSION-0's go and window pass no held set, the live editor (selftest and window) "
            "passes HOLD-WALK-0's; the window still reads only WM_KEYDOWN and its repeat bit")

# ------------------------------------------------------------------ BEARING-0
# The bearing camera of urdr-oracle-2, carried, and its reference kernel placed. The record and the octant are
# Urðr's bytes at the tag; the vocabulary is their data, compiled into the kernel and fail-closed against the pin;
# kernel/bearing.rs is the tag's bearing_rs with `pub` added — the correctness court for every faster bearing path.
ORACLE2_PATH = os.path.join(ORACLE, "urdr-oracle-2.json")
OCTANT_PATH = os.path.join(ORACLE, "bearing_octant.txt")
ORACLE2_ORIGIN = ("urdr-oracle-2", "ad6d55fea165c13841d8305bec38b7f93e8f0f77")
ORACLE2_SHA256 = "61d51062917bce7b25fb76c7fbbdc30d42bb3c98a7f044c4a863329d73e2d8c5"
OCTANT_SHA256 = "f70b2fc20ba8ea8fde7f802ae0f1180ae003d2de5acb963524ca58421405a82c"
# Urðr's tools/terrain/bearing_rs/bearing.rs at the tag, and the sha256 of its core — from the vista marker up to its
# `fn percentiles(` — which kernel/bearing.rs must reproduce with `pub ` removed (both computed from the tag's file)
BEARING_SOURCE_SHA256 = "aeda8e65dc56652fbfc5b67723f78800b2c2b55cb68609149b64910d8e6130be"
BEARING_CORE_SHA256 = "7bcd8165b6856f7de98fb8a8a5ab40b386bb56c8b0b4abcaf83ab63ced02c9f6"
BEARING_CORE_MARK = "// ------------------------------------------------------------------ vista: the camera and one column's strip"
BEARING_ANCHORS = {0: "N", 90000: "E", 180000: "S", 270000: "W"}
BEARING_YAW_MOD = 360000


def oracle2() -> dict:
    with open(ORACLE2_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _octant_pairs() -> list:
    return [tuple(int(x) for x in ln.split(" ")) for ln in read(OCTANT_PATH).decode("ascii").split("\n") if ln]


def _bearing_triple(pairs: list, k: int) -> tuple:
    """The record's `expansion`, restated here: the octant, its mirror, the gcd, then quarter turns."""
    import math
    turns, r = divmod(k, BEARING_YAW_MOD // 4)
    if r <= BEARING_YAW_MOD // 8:
        p, q = pairs[r]
        a, b, c = 2 * p * q, -(q * q - p * p), p * p + q * q
    else:
        p, q = pairs[BEARING_YAW_MOD // 4 - r]
        a, b, c = q * q - p * p, -2 * p * q, p * p + q * q
    g = math.gcd(math.gcd(a, b), c)
    a, b, c = a // g, b // g, c // g
    for _ in range(turns):
        a, b = -b, a
    return a, b, c


def bearing_lines(exe: str, level: str, tiles: str, at: str) -> dict:
    code, out, err = run(exe, ["--level", os.path.join(ORACLE, "levels", level + ".lvl"),
                               "--tiles", os.path.join(ORACLE, "tiles", tiles + ".tiles"), "--at", at])
    if code != 0:
        raise Red(f"the bearing kernel exited {code} at {level}/{tiles}/{at}: {err.strip()}")
    lines = dict(ln.split(" ", 1) for ln in out.strip().splitlines() if " " in ln)
    if lines.get("selfcheck") != "OK":
        raise Red(f"the bearing kernel's selfcheck DIVERGED at {level}/{tiles}/{at}")
    return lines


def bearing_preregistered():
    """BEARING-0's method is locked: the carry verbatim from the tag, the id authoritative and never normalized, the
    vocabulary compiled in and fail-closed, the reference a port of the tag's source in shape only, and no live path."""
    e = locked_entry("BEARING-0", {
        "the ladder and this rung's place on it": ("hyp", ("bearing-0 (the reference)", "bearing-fast-0", "mouse-look-0 with sim-tick-0", "the presentation and latency measurement")),
        "carried verbatim from the tag": ("hyp", ("carried verbatim from urðr at the tag urdr-oracle-2", "urdr-oracle-1's carry is untouched")),
        "the camera and the vocabulary": ("hyp", ("c = (cell_x, cell_z, heading id)", "the id is authoritative", "never normalized", "fail-closed, never regenerated")),
        "the reference, never a live path": ("hyp", ("visibility and shape only, never arithmetic", "the correctness court", "no live window uses it")),
        "the gate": ("succ", ("all 104 witnesses", "48 pairs", "every one of the 52 non-anchor scenes", "with nothing of urðr imported", "the same span of the tag's source")),
        "what fails it": ("fail", ("an id normalized", "the reference reachable from the shell or the workshop", "a speed, frame-rate or latency claim")),
        "scope": ("lims", ("correctness, not speed", "the eye stays at a cell centre", "no mouse, no tick, no movement change", "stays declared")),
    })
    return ("BEARING-0's method is locked (hash %s): the record and the octant carried verbatim from urdr-oracle-2, the "
            "camera (x, z, id) with the id authoritative and never normalized, the vocabulary compiled in and fail-closed, "
            "the reference kernel the tag's arithmetic, and no live path renders at a bearing" % e["chain_hash"][:8])


def oracle2_frozen():
    raw, octant = read(ORACLE2_PATH), read(OCTANT_PATH)
    if sha256(raw) != ORACLE2_SHA256:
        raise Red("oracle/urdr-oracle-2.json is not the bytes carried from the tag")
    if sha256(octant) != OCTANT_SHA256:
        raise Red("oracle/bearing_octant.txt is not the bytes carried from the tag")
    r = json.loads(raw.decode("utf-8"))
    if r.get("name") != "studio-oracle-2" or r.get("capability") != "URDRBRG1":
        raise Red("the carried record is not studio-oracle-2 (URDRBRG1)")
    if r["vocabulary"]["octant_sha256"] != OCTANT_SHA256:
        raise Red("the record pins another octant than the one carried")
    if r["extends"]["sha256"] != sha256(read(os.path.join(ORACLE, "urdr-oracle-1.json"))):
        raise Red("the record extends another studio-oracle-1 than the one carried")
    o, c = oracle(), corpus()
    for name, v in r["corpus"]["views"].items():
        sc = c["scenes"].get(name)
        if sc is None or sc["level"] != name:
            raise Red(f"the record's view {name!r} is not a scene of witnesses.json on its own level")
        lv = c["levels"][name]
        if (int(lv["seed"], 16), lv["depth"]) != (int(v["seed"], 16), v["depth"]) or list(sc["camera"][:2]) != list(v["pos"]):
            raise Red(f"the record's view {name!r} names another seed, depth or cell than the carried level")
    aw = r["anchor_witness"]
    if (aw["bearing"], aw["triple"]) != (270000, [-1, 0, 1]) or (aw["frame_digest_urdrfb1"], aw["identity_pixels_sha256"],
            aw["oriented_pixels_sha256"]) != (o["frame_digest_urdrfb1"], o["identity_pixels_sha256"], o["oriented_pixels_sha256"]):
        raise Red("the record's anchor witness is not urdr-oracle-1's three hashes at W")
    fwd = {"N": [0, -1, 1], "E": [1, 0, 1], "S": [0, 1, 1], "W": [-1, 0, 1]}
    if {int(k): (v["facing"], v["triple"]) for k, v in r["vocabulary"]["anchors"].items()} != {k: (f, fwd[f]) for k, f in BEARING_ANCHORS.items()}:
        raise Red("the record's anchors are not the four cardinals")
    return (f"urdr-oracle-2.json ({ORACLE2_SHA256[:12]}…) and bearing_octant.txt ({OCTANT_SHA256[:12]}…) are the bytes of "
            f"{ORACLE2_ORIGIN[0]} @ {ORACLE2_ORIGIN[1][:7]}; the record extends the carried urdr-oracle-1.json by its sha256, "
            f"its {len(r['corpus']['views'])} views are scenes of witnesses.json on their own levels, its anchor witness at W "
            f"is urdr-oracle-1's three hashes, and its anchors are the cardinals")


def oracle2_identity():
    """The checker is not the prover: every digest the record states is recomputed from the record's own rules and the
    carried octant, with nothing of Urðr imported."""
    r = oracle2()
    pairs = _octant_pairs()
    if len(pairs) != BEARING_YAW_MOD // 8 + 1:
        raise Red(f"the octant has {len(pairs)} pairs")
    h = hashlib.sha256(b"URDRBRG1|table|")
    top = 0
    for k in range(BEARING_YAW_MOD):
        a, b, cc = _bearing_triple(pairs, k)
        h.update(b"%d,%d,%d;" % (a, b, cc))
        top = max(top, cc)
    if h.hexdigest() != r["vocabulary"]["table_digest"]:
        raise Red("the table digest recomputed over all 360,000 ids is not the record's")
    if top != r["vocabulary"]["largest_hypotenuse"]:
        raise Red("the largest hypotenuse is not the record's")
    views, adv = r["corpus"]["views"], r["corpus"]["adversarial"]
    by = {(cs["view"], cs["bearing"]): cs for cs in r["corpus"]["cases"]}
    if set(by) != {(n, k) for n in views for k in adv} or len(by) != len(r["corpus"]["cases"]):
        raise Red("the cases are not exactly the views x the adversarial ids")
    order = []
    for n in sorted(views):
        v = views[n]
        for k in adv:
            cs = by[(n, k)]
            if tuple(cs["triple"]) != _bearing_triple(pairs, k):
                raise Red(f"{n}:{k}: the case's triple is not the expansion's")
            rowt = ("view=%s/%d/%d/(%d, %d)|bearing=%d|triple=%d,%d,%d|frame=%s|identity=%s|oriented=%s"
                    % (n, int(v["seed"], 16), v["depth"], v["pos"][0], v["pos"][1], k, *cs["triple"],
                       cs["frame_digest_urdrfb1"], cs["identity_pixels_sha256"], cs["oriented_pixels_sha256"]))
            hc = sha256(b"URDRBRG1|" + rowt.encode("utf-8"))
            if hc != cs["case"]:
                raise Red(f"{n}:{k}: the case hash recomputed is not the record's")
            order.append(hc)
    ident = sha256(b"URDRBRG1|" + "|".join([r["vocabulary"]["table_digest"]] + order).encode("utf-8"))
    if ident != r["identity"]["bearing"]:
        raise Red("URDRBRG1's identity recomputed is not the record's")
    return (f"from the record and the octant alone: the table digest over all 360,000 ids ({h.hexdigest()[:12]}…), the "
            f"largest hypotenuse {top:,}, the {len(order)} case hashes and URDRBRG1's identity ({ident[:12]}…) recomputed by "
            f"the record's own rules equal the record's — nothing of Urðr imported")


def bearing_vocab():
    need_rustc()
    r = oracle2()
    code, out, err = run(KERNEL_EXE, ["--bearing-table"])
    lines = dict(ln.split(" ", 1) for ln in out.strip().splitlines() if " " in ln)
    if code != 0 or lines.get("octant") != OCTANT_SHA256 or lines.get("table") != r["vocabulary"]["table_digest"]:
        raise Red(f"the kernel's vocabulary is not the record's: {out.strip()} {err.strip()}")
    pairs = _octant_pairs()
    cases = {cs["bearing"]: tuple(cs["triple"]) for cs in r["corpus"]["cases"]}
    ids = sorted(set(BEARING_ANCHORS) | set(r["corpus"]["adversarial"]))
    for k in ids:
        code, out, err = run(KERNEL_EXE, ["--bearing-triple", str(k)])
        want = _bearing_triple(pairs, k)
        if code != 0 or out.strip() != "triple %d %d,%d,%d" % (k, *want) or (k in cases and cases[k] != want):
            raise Red(f"id {k}: the kernel's triple {out.strip()!r} is not the record's {want}")
    bad = ["360000", "-1", "1.5", "007", "+5", " 5", "", "abc", "3600000", "0x10"]
    for s in bad:
        code, out, err = run(KERNEL_EXE, ["--bearing-triple", s])
        if code == 0 or "BEARING-REFUSE" not in err or "triple" in out:
            raise Red(f"the id {s!r} was not refused typed")
    return (f"the kernel's table digest over all 360,000 ids is the record's, its triple at the {len(ids)} anchor and "
            f"adversarial ids is the expansion's and the record's, and {len(bad)} malformed ids (out of range, signed, "
            f"zero-padded, fractional, spaced, empty, hex) are each refused typed, never normalized")


def bearing_oracle():
    need_rustc()
    r = oracle2()
    views = r["corpus"]["views"]
    n = 0
    for cs in r["corpus"]["cases"]:
        v = views[cs["view"]]
        at = "%d,%d,%d" % (v["pos"][0], v["pos"][1], cs["bearing"])
        frames = set()
        for tname, key in (("identity", "identity_pixels_sha256"), ("oriented", "oriented_pixels_sha256")):
            d = bearing_lines(KERNEL_EXE, cs["view"], tname, at)
            if d.get("triple") != ",".join(str(x) for x in cs["triple"]):
                raise Red(f"{cs['view']}:{cs['bearing']}: triple {d.get('triple')} is not the record's")
            if d["frame"] != cs["frame_digest_urdrfb1"]:
                raise Red(f"{cs['view']}:{cs['bearing']}/{tname}: frame {d['frame'][:12]} != oracle {cs['frame_digest_urdrfb1'][:12]}")
            if d["pixels"] != cs[key]:
                raise Red(f"{cs['view']}:{cs['bearing']}/{tname}: pixels {d['pixels'][:12]} != oracle {cs[key][:12]}")
            frames.add(d["frame"])
            n += 2
        if len(frames) != 1:
            raise Red(f"{cs['view']}:{cs['bearing']}: the tile sets do not share one frame digest")
    a = bearing_lines(KERNEL_EXE, "witness", "identity", "34,28,123457")
    b = bearing_lines(KERNEL_EXE, "witness", "identity", "34,28,123457")
    if (a["frame"], a["pixels"]) != (b["frame"], b["pixels"]):
        raise Red("two runs of one case disagree")
    return (f"the reference bearing kernel reproduces all {n} witnesses of urdr-oracle-2 — {len(r['corpus']['cases'])} cases "
            f"({len(r['corpus']['adversarial'])} adversarial ids from the {' and '.join(sorted(views))} views, hypotenuses "
            f"up to 2^33) x 2 tile sets x the frame digest and the pixel sha256 — bit for bit, each selfcheck OK, the tile "
            f"sets of a case sharing one frame, one case twice in separate processes")


def bearing_anchors():
    """At C = 1 the reference is the facing kernel: the frame and the picture at each anchor equal the facing
    kernel's at that cardinal, live, over every corpus scene — and a mirrored screen-right is caught at every scene."""
    need_rustc()
    c = corpus()
    pairs, pinned = 0, 0
    for name, e in c["scenes"].items():
        x, z, own = e["camera"]
        for k, f in BEARING_ANCHORS.items():
            for tname, w in e["witnesses"].items():
                b = bearing_lines(KERNEL_EXE, e["level"], tname, f"{x},{z},{k}")
                fd, ps = witnesses(KERNEL_EXE, e["level"], tname, f"{x},{z},{f}")
                if (b["frame"], b["pixels"]) != (fd, ps):
                    raise Red(f"{name}/{tname} at {k}: the reference is not the facing kernel at {f}")
                if f == own:
                    if (b["frame"], b["pixels"]) != (w["frame"], w["pixels"]):
                        raise Red(f"{name}/{tname}: the anchor at the scene's own facing is not the frozen pin")
                    pinned += 1
                pairs += 1
    src = read(os.path.join(KERNEL, "bearing.rs")).decode("utf-8")
    anchor = "(a_ * b - b_ * a, b_ * b + a_ * a)"
    if src.count(anchor) != 1:
        raise Red("the ray anchor is not where the mirror plant expects it")
    exe = compile_rs(KERNEL, "main.rs", "kernel-bearing-mirrored", {"bearing.rs": src.replace(anchor, "(a_ * b + b_ * a, b_ * b - a_ * a)")})
    caught = 0
    for name, e in c["scenes"].items():
        x, z, _own = e["camera"]
        if any(bearing_lines(exe, e["level"], "identity", f"{x},{z},{k}")["frame"]
               != witnesses(KERNEL_EXE, e["level"], "identity", f"{x},{z},{f}")[0] for k, f in BEARING_ANCHORS.items()):
            caught += 1
    if caught != len(c["scenes"]):
        raise Red(f"a mirrored screen-right was caught at {caught} of {len(c['scenes'])} scenes")
    return (f"at the four anchors the reference IS the facing kernel: {pairs} pairs over {len(c['scenes'])} scenes x "
            f"{len(c['tiles'])} tile sets equal the facing kernel's frame and pixels live, {pinned} of them the frozen pins; "
            f"a reference with screen-right mirrored fails the anchor law at every one of the {caught} scenes")


def bearing_selftest():
    """The C law is load-bearing: a reference that drops the hypotenuse from the depth moves every non-anchor frame,
    and at an anchor (C = 1) it moves nothing."""
    need_rustc()
    src = read(os.path.join(KERNEL, "bearing.rs")).decode("utf-8")
    anchor = "let h2d = 2 * focal * self.c * tn;"
    if src.count(anchor) != 1:
        raise Red("the depth anchor is not where the selftest expects it")
    exe = compile_rs(KERNEL, "main.rs", "kernel-bearing-dropc", {"bearing.rs": src.replace(anchor, "let h2d = 2 * focal * tn;")})
    r = oracle2()
    moved = 0
    for cs in r["corpus"]["cases"]:
        v = r["corpus"]["views"][cs["view"]]
        for tname in ("identity", "oriented"):
            d = bearing_lines(exe, cs["view"], tname, "%d,%d,%d" % (v["pos"][0], v["pos"][1], cs["bearing"]))
            if d["frame"] == cs["frame_digest_urdrfb1"]:
                raise Red(f"{cs['view']}:{cs['bearing']}/{tname}: dropping C did not move the frame — the row is vacuous")
            moved += 1
    o = oracle()
    d = bearing_lines(exe, "witness", "identity", "34,28,270000")
    if (d["frame"], d["pixels"]) != (o["frame_digest_urdrfb1"], o["identity_pixels_sha256"]):
        raise Red("dropping C moved an anchor, where C = 1")
    return (f"a reference that drops the hypotenuse from the depth (the frozen strip expression used verbatim) moves the "
            f"frame digest of every one of the {moved} non-anchor scenes and leaves the witness anchor at W untouched: the "
            f"C law is what the rows above measure")


def bearing_refuse():
    need_rustc()
    raw = read(OCTANT_PATH)
    # one pair altered into another CANONICAL pair (q + 1 beside p = 1 stays coprime), so only the pin can catch it
    first = raw.split(b"\n")[1]
    p_, q_ = first.split(b" ")
    altered = raw.replace(b"\n" + first + b"\n", b"\n%s %d\n" % (p_, int(q_) + 1), 1)
    if altered == raw or p_ != b"1":
        raise Red("the octant plant did not alter the file as registered")
    os.makedirs(BUILD, exist_ok=True)
    with open(os.path.join(BUILD, "octant-altered.txt"), "wb") as fh:
        fh.write(altered)
    vsrc = read(os.path.join(KERNEL, "vocab.rs")).decode("utf-8")
    inc = 'include_bytes!("../oracle/bearing_octant.txt")'
    if vsrc.count(inc) != 1:
        raise Red("the vocabulary's include is not where the plant expects it")
    exe = compile_rs(KERNEL, "main.rs", "kernel-octant-altered", {"vocab.rs": vsrc.replace(inc, 'include_bytes!("../verify/build/octant-altered.txt")')})
    code, out, err = run(exe, ["--bearing-table"])
    if code == 0 or "BEARING-REFUSE" not in err or "table" in out:
        raise Red("an altered octant compiled in was not refused at load")
    code, out, err = run(exe, ["--level", os.path.join(ORACLE, "levels", "witness.lvl"), "--tiles",
                               os.path.join(ORACLE, "tiles", "identity.tiles"), "--at", "34,28,123457"])
    if code == 0 or "BEARING-REFUSE" not in err or "frame" in out:
        raise Red("an altered octant compiled in still rendered at a bearing")
    o = oracle()
    if witnesses(exe, "witness", "identity", "34,28,W") != (o["frame_digest_urdrfb1"], o["identity_pixels_sha256"]):
        raise Red("the altered octant reached the facing path")
    lvl = read(os.path.join(ORACLE, "levels", "witness.lvl"))
    w_, rows_ = int.from_bytes(lvl[8:12], "little"), int.from_bytes(lvl[12:16], "little")
    cells = lvl[16:16 + w_ * rows_]
    rock = next(i for i, ch in enumerate(cells) if ch == ord("#"))
    code, out, err = run(KERNEL_EXE, ["--level", os.path.join(ORACLE, "levels", "witness.lvl"), "--tiles",
                                      os.path.join(ORACLE, "tiles", "identity.tiles"), "--at", f"{rock % w_},{rock // w_},0"])
    if code == 0 or "non-traversable" not in err or "frame" in out:
        raise Red("an eye on rock was not refused")
    for at in ("34,28,360000", "34,28,-1", "34,28,1.5", "34,28,0123", "34,28"):
        code, out, err = run(KERNEL_EXE, ["--level", os.path.join(ORACLE, "levels", "witness.lvl"), "--tiles",
                                          os.path.join(ORACLE, "tiles", "identity.tiles"), "--at", at])
        if code == 0 or "BEARING-REFUSE" not in err or "frame" in out:
            raise Red(f"the bearing camera {at!r} was not refused typed")
    return ("fail-closed: an octant with one pair altered into another canonical pair, compiled in, is refused at load by "
            "its pin (no table, no frame) while the "
            "same binary's facing path still reproduces urdr-oracle-1; an eye on rock and five malformed bearing cameras "
            "are refused typed")


def bearing_fence():
    src = read(os.path.join(KERNEL, "bearing.rs")).decode("utf-8")
    voc = read(os.path.join(KERNEL, "vocab.rs")).decode("utf-8")
    if BEARING_CORE_MARK not in src or "/// The two witnesses' material" not in src:
        raise Red("the reference's core markers moved")
    core = re.sub(r"\bpub ", "", src[src.index(BEARING_CORE_MARK):src.index("/// The two witnesses' material")]).rstrip() + "\n"
    if sha256(core.encode("utf-8")) != BEARING_CORE_SHA256:
        raise Red("kernel/bearing.rs's core is no longer the tag's text: the reference is never modified")
    if BEARING_SOURCE_SHA256 not in src or "urdr-oracle-2" not in src:
        raise Red("kernel/bearing.rs does not cite its source at the tag")
    code_of = lambda t: "\n".join(ln.split("//", 1)[0] for ln in t.splitlines())   # comments out; no literal holds //
    for name, text in (("bearing.rs", code_of(src)), ("vocab.rs", code_of(voc))):
        for tok in ("Instant", "std::time", "SystemTime", "thread", "fs::", "File", "unsafe", "env::"):
            if tok in text:
                raise Red(f"kernel/{name} uses {tok}")
    if code_of(src).count("std::process::exit") != 1 or "exit" in code_of(voc):
        raise Red("the reference exits anywhere but its invariant stop, or the vocabulary exits")
    if len(re.findall(r"include_(bytes|str)!", voc)) != 1 or voc.count('include_bytes!("../oracle/bearing_octant.txt")') != 1 \
            or re.findall(r"include_(bytes|str)!", src):
        raise Red("the vocabulary includes anything but the carried octant, or the reference includes a file")
    if f'pub const OCTANT_SHA256: &str = "{OCTANT_SHA256}";' not in voc:
        raise Red("the vocabulary's pin is not the record's octant sha256")
    # re-pinned on purpose with SIM-TICK-0: the windowless session witnesses a look by the frame at its heading, so
    # shell/heading.rs uses the vocabulary and the reference (the frames and their certification at save), shell/main.rs
    # declares the modules, shell/livesession.rs names the files in the bearing identity, and the workshop's session-walk
    # verifier renders a look with the reference; nothing else does, and no window renders at a bearing
    allowed = {(SHELL, "heading.rs"), (SHELL, "main.rs"), (SHELL, "livesession.rs"), (WORKSHOP, "sessionwalk.rs")}
    for d in (SHELL, WORKSHOP):
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".rs") and (d, fn) not in allowed:
                t = read(os.path.join(d, fn)).decode("utf-8")
                if re.search(r"kernel/(bearing|vocab)\.rs|\b(bearing|vocab)::", t):
                    raise Red(f"{os.path.basename(d)}/{fn} reaches the reference bearing kernel or its vocabulary")
    tail = read(os.path.join(SHELL, "win32.rs"))[LATENCY0_WIN32_LEN:].decode("utf-8")
    code_ = lambda fn: "\n".join(ln.split("//", 1)[0] for ln in read(os.path.join(SHELL, fn)).decode("utf-8").splitlines())
    if "bearing" in tail or "heading::" in tail or re.search(r"\b(bearing|vocab)::", code_("main.rs")) or re.search(r"\b(bearing|vocab)::", code_("livesession.rs")):
        raise Red("a window renders at a bearing, or shell/main.rs or shell/livesession.rs uses the reference itself")
    return ("the reference is the tag's arithmetic: its core, `pub` removed, hashes to the same span of Urðr's "
            "bearing_rs at urdr-oracle-2; it and the vocabulary read no clock, spawn no thread, touch no file at run "
            "time, use no unsafe; the vocabulary's one include is the carried octant under the record's pin; in the "
            "shell only heading.rs uses them (the windowless session's frames and their certification), in the workshop "
            "only the session-walk verifier — no window renders at a bearing")

# ------------------------------------------------------------------ BEARING-FAST-0
# The bearing camera made fast, held byte for byte to the reference (kernel/bearing.rs, never modified). The court runs
# in kernel processes over a registered camera list; the gate splits the list across processes only for wall-clock,
# and every number it reports is a function of the list, never of the split.
BF_HEADINGS = (0, 90000, 180000, 270000, 1, 359999, 89999, 90001, 179999, 180001, 269999, 270001,
               45000, 135000, 225000, 315000, 44999, 45001, 134999, 135001, 224999, 225001, 314999, 315001,
               88, 359912, 89912, 90088, 179912, 180088, 269912, 270088,
               12345, 77777, 123457, 166667, 199999, 234567, 300001, 333333)
BF_TREADS = ("a", "b", "ca", "cb")
BF_THREADS_SET = "1,2,3,7,8,16"
# the registered camera list (the 52 oracle scenes, then the 1,920 court frames), as text with relative paths
BF_LIST_SHA256 = "e34469b21c394fd704412881154ec631f0c2412a50e03ecf1fe14137982483db"
# the production kernel this rung must not touch (re-pinned on purpose by a rung that changes it)
MANTLE_RS_SHA256 = "ab08361dc82d9fd8c040fc96386c5d81118c04851efee718c4dc9a72d273095c"
FAST_RS_SHA256 = "5de110834ac015ad6ab0e5fae0bed8a49aa6fd19cbb77bd1cb63edbbd0362f77"
BF_NARROWINGS = 7
BF_STATE: dict = {}


def _bf_walkable(level: str) -> list:
    b = read(os.path.join(ORACLE, "levels", level + ".lvl"))
    w, h = int.from_bytes(b[8:12], "little"), int.from_bytes(b[12:16], "little")
    cells = b[16:16 + w * h]
    return [(x, z) for z in range(h) for x in range(w) if cells[z * w + x] != ord("#")]


def bf_court_cameras() -> list:
    """The registered set: the six corpus scenes in name order; per scene its own camera cell, then seven walkable cells
    of its level (sorted by z then x) at floor((i+1)*n/8) + s mod n, repeats skipped forward; times the 40 headings."""
    c = corpus()
    cams = []
    for s, name in enumerate(sorted(c["scenes"])):
        e = c["scenes"][name]
        cells = _bf_walkable(e["level"])
        n = len(cells)
        chosen = [(e["camera"][0], e["camera"][1])]
        for i in range(7):
            j = ((i + 1) * n // 8 + s) % n
            while cells[j] in chosen:
                j = (j + 1) % n
            chosen.append(cells[j])
        for (x, z) in chosen:
            for k in BF_HEADINGS:
                cams.append((e["level"], x, z, k))
    return cams


def bf_list() -> tuple:
    """(text, expected): the camera list the kernel reads — the 52 oracle scenes (each case in the identity then the
    oriented tiles) then the 1,920 court frames (tile sets alternating identity, oriented) — and, for the oracle lines,
    the record's (frame, pixels)."""
    r = oracle2()
    lines, expected = [], {}
    for cs in r["corpus"]["cases"]:
        v = r["corpus"]["views"][cs["view"]]
        for tname, key in (("identity", "identity_pixels_sha256"), ("oriented", "oriented_pixels_sha256")):
            expected[len(lines)] = (cs["frame_digest_urdrfb1"], cs[key])
            lines.append(f"oracle/levels/{cs['view']}.lvl oracle/tiles/{tname}.tiles {v['pos'][0]} {v['pos'][1]} {cs['bearing']}")
    for j, (lvl, x, z, k) in enumerate(bf_court_cameras()):
        lines.append(f"oracle/levels/{lvl}.lvl oracle/tiles/{'identity' if j % 2 == 0 else 'oriented'}.tiles {x} {z} {k}")
    return "\n".join(lines) + "\n", expected


def bf_run(exe: str, text: str, extra: list, tag: str) -> list:
    """The court over a camera list, split across processes (camera i to process i mod P, for wall-clock only); returns
    each camera's fields after `cam I ref` — the reference's FD PS, then NAME FD PS EQ per tread — in list order."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    procs_n = max(1, min(8, os.cpu_count() or 1, len(lines)))
    os.makedirs(BUILD, exist_ok=True)
    procs = []
    for p in range(procs_n):
        path = os.path.join(BUILD, f"bf-{tag}-{p}.txt")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines[p::procs_n]) + "\n")
        procs.append(subprocess.Popen([exe, "--bearing-court", path] + extra, cwd=ROOT, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True))
    res = [None] * len(lines)
    for p, pr in enumerate(procs):
        out, err = pr.communicate()
        if pr.returncode != 0:
            raise Red(f"the court process exited {pr.returncode}: {err.strip()[-300:]}")
        for ln in out.splitlines():
            f = ln.split()
            res[int(f[1]) * procs_n + p] = f[3:]
    if any(x is None for x in res):
        raise Red("the court did not report every camera")
    return res


def bearingfast_preregistered():
    """BEARING-FAST-0's method is locked: one rung, its staircase inside, held byte for byte to the reference; the
    camera set, the checked build, the bounds and the host courts registered before any build or timing."""
    e = locked_entry("BEARING-FAST-0", {
        "a sibling of the reference": ("hyp", ("a sibling of kernel/bearing.rs", "never modified", "reuses the reference's traversal")),
        "the treads": ("hyp", ("tread a, exact stepping", "tread b, memory layout", "tread c, threads", "tread d, persistent workers, only on its trigger")),
        "the exact walker and the bounds": ("hyp", ("m = floor(n*t/den)", "written worst-case bound", "refused by the fast path, never wrapped")),
        "the gate": ("succ", ("1,920 frames", "the camera set's digest pinned", "t in {1, 2, 3, 7, 8, 16}", "overflow checks on")),
        "the host courts": ("succ", ("950 permille", "the target is a production p99 at most 6,667 us", "622,440 frames")),
        "what fails it": ("fail", ("a number kept before its witnesses were checked", "the target or the margin changed after a number was seen")),
        "scope": ("lims", ("renderer time only", "never kept merely because it exists", "no live window renders at a bearing until mouse-look-0")),
    })
    return ("BEARING-FAST-0's method is locked (hash %s) before any build or timing: one rung, treads A (exact stepping), "
            "B (the blocked floor), C (row-banded threads) and D only on its trigger, each byte-identical to the "
            "reference; the camera set, the checked build, the bounds, the host speed court's margin and target "
            "(p99 <= 6,667 us) and the sweep" % e["chain_hash"][:8])


def bearingfast_court():
    need_rustc()
    text, expected = bf_list()
    if sha256(text.encode("utf-8")) != BF_LIST_SHA256:
        raise Red("the registered camera list is not the pinned one (%s)" % sha256(text.encode("utf-8"))[:16])
    res = bf_run(KERNEL_EXE, text, [], "court")
    for i, f in enumerate(res):
        names = f[2::4]
        if tuple(names) != BF_TREADS:
            raise Red(f"camera {i}: the court ran {names}, not the registered treads")
        for j, name in enumerate(names):
            if f[2 + 4 * j + 3] != "1":
                raise Red(f"camera {i} ({text.splitlines()[i]}): tread {name} differs from the reference")
        if i in expected and (f[0], f[1]) != expected[i]:
            raise Red(f"oracle camera {i}: the reference is not urdr-oracle-2's witness")
    digest = sha256("".join(f"{f[0]} {f[1]}\n" for f in res).encode("utf-8"))
    BF_STATE["ref"] = [(f[0], f[1]) for f in res]
    BF_STATE["text"] = text
    return (f"every tread (A exact stepping, B the blocked floor, C in {8} row bands over each) is byte-identical to the "
            f"reference, index frame and picture, at all {len(res)} cameras: the 52 oracle scenes, each also urdr-oracle-2's "
            f"own witness, and the 1,920 registered frames (six scenes x eight cells x forty headings, the list pinned); "
            f"court digest {digest[:16]}")


def bearingfast_threads():
    need_rustc()
    text, expected = bf_list()
    oracle_text = "\n".join(text.splitlines()[:len(expected)]) + "\n"
    res = bf_run(KERNEL_EXE, oracle_text, ["--threads-set", BF_THREADS_SET], "threads")
    counts = [int(t) for t in BF_THREADS_SET.split(",")]
    for i, f in enumerate(res):
        if (f[0], f[1]) != expected[i]:
            raise Red(f"oracle camera {i}: the reference is not urdr-oracle-2's witness")
        names = f[2::4]
        if len(names) != 2 * len(counts) or any(f[2 + 4 * j + 3] != "1" for j in range(len(names))):
            raise Red(f"oracle camera {i}: tread C differs from the reference at some thread count")
    return (f"tread C is byte-identical to the reference at T in {{{BF_THREADS_SET.replace(',', ', ')}}}, in both floor "
            f"layouts, over the {len(res)} oracle scenes: uneven bands and more threads than cores move no byte")


def bearingfast_checked():
    need_rustc()
    if "ref" not in BF_STATE:
        raise Red("the court did not run before the checked build")
    cp = subprocess.run([RUSTC] + FLAGS + ["-C", "overflow-checks=on", os.path.join(KERNEL, "main.rs"), "-o",
                         os.path.join(BUILD, "kernel-checked" + EXE)], capture_output=True, text=True)
    if cp.returncode != 0:
        raise Red("rustc failed on the checked build: " + cp.stderr.strip().splitlines()[0])
    res = bf_run(os.path.join(BUILD, "kernel-checked" + EXE), BF_STATE["text"], ["--no-reference"], "checked")
    hashed = 0
    for i, f in enumerate(res):
        cells = [f[2 + 4 * j:2 + 4 * j + 4] for j in range(len(BF_TREADS))]
        got = [(c[1], c[2]) for c in cells if c[1] != "-"]
        if len(got) != 1 or got[0] != BF_STATE["ref"][i]:
            raise Red(f"camera {i}: the checked build's rotated tread is not the reference's digest")
        hashed += 1
    return (f"the fast path built with overflow checks on renders every tread at all {len(res)} cameras without an "
            f"overflow, and the tread each camera hashes in rotation ({hashed} digests, each tread a quarter) equals the "
            f"reference's digest there: the 64-bit arithmetic does not wrap on the court set")


def bearingfast_bounds():
    need_rustc()
    src = read(os.path.join(KERNEL, "bearingfast.rs")).decode("utf-8")
    code = "\n".join(ln.split("//", 1)[0] for ln in src.splitlines())
    calls = [ln for ln in src.splitlines() if "narrow(" in ln.split("//", 1)[0] and "fn narrow(" not in ln]
    n_calls = sum(ln.split("//", 1)[0].count("narrow(") for ln in calls)
    if n_calls != BF_NARROWINGS or any("2^" not in (ln.split("//", 1)[1] if "//" in ln else "") for ln in calls):
        raise Red(f"{n_calls} narrowings, or one without its written bound (registered: {BF_NARROWINGS}, each with a 2^ bound)")
    body = code[code.index("fn narrow("):]
    body = body[body.index("\n}\n") + 3:]
    if re.findall(r"as i64", body.replace("r as i64", "")):
        raise Red("an `as i64` outside `narrow` (an unchecked narrowing)")
    # the envelope's edge: the registered heading with the largest hypotenuse, every tread against the reference
    pairs = _octant_pairs()
    kmax = max(range(BEARING_YAW_MOD // 8 + 1), key=lambda k: _bearing_triple(pairs, k)[2])
    cmax = _bearing_triple(pairs, kmax)[2]
    res = bf_run(KERNEL_EXE, f"oracle/levels/witness.lvl oracle/tiles/identity.tiles 34 28 {kmax}\n"
                             f"oracle/levels/witness.lvl oracle/tiles/oriented.tiles 34 28 {kmax}\n", [], "edge")
    if any(f[2 + 4 * j + 3] != "1" for f in res for j in range(len(BF_TREADS))):
        raise Red(f"at the largest registered hypotenuse (id {kmax}) a tread differs from the reference")
    # beyond the edge: a Pythagorean triple with C >= 2^33 — the reference renders it, the fast path refuses it
    lvl = read(os.path.join(ORACLE, "levels", "witness.lvl"))
    w_, rows_ = int.from_bytes(lvl[8:12], "little"), int.from_bytes(lvl[12:16], "little")
    cells = lvl[16:16 + w_ * rows_]
    rest = lvl[16 + w_ * rows_:]
    k_ = 1 << 31
    a_, b_, c_ = -4 * k_, 3 * k_, 5 * k_
    scene = (b"URDRBRGI" + lvl[8:16] + cells + (34).to_bytes(4, "little", signed=True) + (28).to_bytes(4, "little", signed=True)
             + a_.to_bytes(8, "little", signed=True) + b_.to_bytes(8, "little", signed=True) + c_.to_bytes(8, "little", signed=True)
             + rest[:4] + rest[4:] + read(os.path.join(ORACLE, "tiles", "identity.tiles"))[8:])
    path = os.path.join(BUILD, "bf-beyond.bin")
    with open(path, "wb") as fh:
        fh.write(scene)
    code_, out, err = run(KERNEL_EXE, ["--fast-scene", path])
    if not out.startswith("ref ") or code_ == 0 or "BEARING-FAST-REFUSE" not in err or "\na " in out:
        raise Red("beyond the envelope (C = 5 * 2^31 >= 2^33) the reference must render and the fast path refuse")
    return (f"{BF_NARROWINGS} narrowings from 128 to 64 bits, each through the checked `narrow` with its bound written "
            f"beside it, and no other; at the registered heading with the largest hypotenuse (id {kmax}, C = {cmax:,}) "
            f"every tread is the reference; beyond the envelope (C = 5 * 2^31) the reference renders and the fast path "
            f"refuses typed, never wraps")


def bearingfast_fence():
    src = read(os.path.join(KERNEL, "bearing.rs")).decode("utf-8")
    core = re.sub(r"\bpub ", "", src[src.index(BEARING_CORE_MARK):src.index("/// The two witnesses' material")]).rstrip() + "\n"
    if sha256(core.encode("utf-8")) != BEARING_CORE_SHA256:
        raise Red("the reference's core changed: the correctness court is never modified")
    if sha256(read(os.path.join(KERNEL, "mantle.rs"))) != MANTLE_RS_SHA256 or sha256(read(os.path.join(KERNEL, "fast.rs"))) != FAST_RS_SHA256:
        raise Red("mantle.rs or fast.rs changed: BEARING-FAST-0 touches neither")
    bf = read(os.path.join(KERNEL, "bearingfast.rs")).decode("utf-8")
    code = "\n".join(ln.split("//", 1)[0] for ln in bf.splitlines())
    for tok in ("Instant", "std::time", "SystemTime", "fs::", "File", "unsafe", "env::"):
        if tok in code:
            raise Red(f"kernel/bearingfast.rs uses {tok}")
    if code.count("std::thread::scope") != 1 or code.count("thread::") != 1:
        raise Red("a thread outside tread C's one scope")
    # re-pinned on purpose with SIM-TICK-0: the windowless session renders a free heading's frame once with the production
    # tread, through shell/heading.rs alone (shell/main.rs declares the module, shell/livesession.rs names the file in the
    # bearing identity); no window does until MOUSE-LOOK-0, and the workshop never does
    for d in (SHELL, WORKSHOP):
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".rs") and (d, fn) not in ((SHELL, "heading.rs"), (SHELL, "main.rs"), (SHELL, "livesession.rs")) \
                    and re.search(r"bearingfast", read(os.path.join(d, fn)).decode("utf-8")):
                raise Red(f"{os.path.basename(d)}/{fn} reaches the fast bearing path: only shell/heading.rs does, and no window before MOUSE-LOOK-0")
    w32 = read(os.path.join(SHELL, "win32.rs")).decode("utf-8", "replace")
    ls = "\n".join(ln.split("//", 1)[0] for ln in read(os.path.join(SHELL, "livesession.rs")).decode("utf-8").splitlines())
    if "bearing" in w32[LATENCY0_WIN32_LEN:] or "heading::" in w32 or ls.count("bearingfast") != 2 or "bearingfast::" in ls:
        raise Red("a window reaches the bearing path before MOUSE-LOOK-0, or shell/livesession.rs does more than name the file in the identity")
    return ("the reference's core is still the tag's text; mantle.rs and fast.rs are unchanged; the fast path reads no "
            "clock, touches no file, uses no unsafe and starts threads only in tread C's one scope; in the shell only "
            "heading.rs reaches it (the windowless session's frame at a free heading), no window does, and the workshop "
            "never does")

# ------------------------------------------------------------------ SIM-TICK-0
# The mouse-look rules as integer law, windowless: raw input -> tick command -> SESSION-WALK -> authority. The twin
# below re-derives the laws and a whole tick run in Python from the registered constants alone; frames come from the
# kernel executable (the facing kernel at an anchor, the bearing REFERENCE at a free heading), never from the shell.
ST_HZ, ST_TICK_US, ST_YAW, ST_QUARTER = 64, 15625, 360000, 90000
ST_COARSE, ST_FINE, ST_MULT_MAX, ST_COUNTS_MAX = 88, 1, 64, 2 ** 31 - 1
ST_DELTA_MAX = ST_COUNTS_MAX * ST_MULT_MAX * ST_COARSE
ST_CAMERA = "28,28,N"
# the tick binding: LIVE-AUTHOR-0's with A and D the strafes
ST_BIND = {"W": ("move", "F"), "UP": ("move", "F"), "S": ("move", "B"), "DOWN": ("move", "B"), "A": ("move", "Q"),
           "Q": ("move", "Q"), "D": ("move", "E"), "E": ("move", "E"), "LEFT": ("move", "L"), "RIGHT": ("move", "R"),
           "SPACE": ("toggle",), "1": ("tile", 0), "2": ("tile", 1), "3": ("tile", 2), "4": ("tile", 3), "5": ("tile", 4),
           "ESC": ("end",)}
_ST_CLASSES = ["wall0", "wall1", "wall2", "wall3", "floor"]
# script S, from 28,28,N on the witness level with identity tiles: (tick, microseconds into the tick, input). Each line
# says what it registers.
SIMTICK_SCRIPT = (
    [(0, 0, "m+3"), (0, 5000, "m+2"), (0, 15624, "m-1"),      # three reports summed in one tick, the last a microsecond before the boundary
     (1, 0, "m+1"),                                          # a report at exactly the boundary: tick 1's
     (2, 0, "m+5"), (2, 8750, "m-5"),                        # a zero-sum tick: no look, no command
     (3, 0, "m+506"),                                        # coarse steps up to 44968, still north
     (4, 0, "W"), (4, 5, "m+1"),                             # the key first, the report after: the look is applied first (45056, east), then W steps east
     (5, 0, "step"),                                         # fine steps from the next tick
     (6, 0, "m-56"), (6, 1, "W"),                            # the exact tie, 45000: east (clockwise); W steps east
     (7, 0, "m-1"), (7, 1, "W"),                             # one id below the tie, 44999: north; W is blocked by rock
     (8, 0, "A"), (9, 0, "D"),                               # the strafes, toward the cardinals left and right of north
     (10, 0, "S"),                                           # back, into rock: blocked
     (11, 0, "SPACE"), (11, 1, "W"),                         # the cell ahead of the nearest cardinal opens; W steps into it
     (12, 0, "1"),                                           # a class key at a free heading
     (13, 0, "LEFT"),                                        # a quarter turn at a free heading: 44999 - 90000 = 314999
     (14, 0, "step"),                                        # coarse again
     (15, 0, "mult+"), (15, 1, "m+1"),                       # a sensitivity action in the same tick as a look: the look uses the old multiplier
     (16, 0, "m+1"),                                         # the raised multiplier, used
     (17, 0, "m+255"),                                       # through 360000 to 143
     (18, 0, "m-1"),                                         # a negative look through 0
     (19, 0, "mult-"), (19, 1, "step"),
     (20, 0, "m+33"),                                        # exactly back to an anchor: 0, token N, the facing kernel's frame
     (21, 0, "m+360000"),                                    # a whole turn: an event, the heading where it was
     (22, 0, "mult-")]                                       # the multiplier pushed below 1: refused
    + [(23, i, "mult+") for i in range(64)]                  # up to 64, then pushed above it: refused
    + [(24, 0, "m+1"),                                       # multiplier 64, used
       (25, 0, "m+2147483647"), (25, 1, "m+1"), (25, 2, "W"),  # the counts leave 2^31 - 1: the look refused, W still applied
       (26, 0, "Z"),                                         # an unbound key
       (27, 0, "ESC")])
# re-pinned on purpose with SIM-TICK-0a: the 68 sensitivity actions of script S that take effect are now sensitivity
# events in its saved log (the two refused ones still are not), and the run counts its repeats (script S has none)
SIMTICK_COUNTS = {"inputs": 102, "reports": 19, "keys": 13, "actions": 70, "commands": 27, "looks": 13, "events": 24,
                  "moves": 9, "blocked": 2, "edits": 2, "unbound": 1, "refused": 3,
                  "settings": 68, "repeats": 0, "walked": 0, "coalesced": 0, "ignored": 0}
# SIM-TICK-0a: HOLD-WALK-0's held set by key name, and the control keys' typed effects
ST_HELD = ("W", "A", "S", "D", "UP", "LEFT", "DOWN", "RIGHT")
ST_CONTROL = {"PGUP": "mult+", "PGDN": "mult-", "TAB": "step"}
SIMTICK_FINAL = {"camera": "30,26,64", "ticks": 28, "sensitivity": [64, 1], "free_frames": 20}
# the continuation of S's saved session: the heading back to an anchor with the saved multiplier, a blocked step, the
# multiplier lowered and used, end — its ticks follow the parent's 28
SIMTICK_RESUME = [(0, 0, "m-1"), (1, 0, "W"), (2, 0, "mult-"), (3, 0, "m+2"), (4, 0, "ESC")]
SIMTICK_LAW_MUTANTS = {
    "the tie-break reversed": ("(((k + HALF_SECTOR) / QUARTER) % 4) as u8", "(((k + HALF_SECTOR - 1) / QUARTER) % 4) as u8", ("cardinal_digest", "boundaries")),
    "the tick one microsecond short": ("pub const TICK_US: u64 = 15_625;", "pub const TICK_US: u64 = 15_624;", ("tick", "tick_of")),
    "the tick one microsecond long": ("pub const TICK_US: u64 = 15_625;", "pub const TICK_US: u64 = 15_626;", ("tick", "tick_of")),
    "a coarse step of 87": ("pub const STEP_COARSE: i64 = 88;", "pub const STEP_COARSE: i64 = 87;", ("delta_digest", "delta", "sens")),
}
SIMTICK_LAW_MAIN = ('#[allow(dead_code)]\n#[path = "../kernel/mantle.rs"]\nmod mantle;\n#[allow(dead_code)]\n#[path = "simtick.rs"]\nmod simtick;\n'
                    'fn main() {\n    for ln in simtick::law_lines(|b| mantle::hex(&mantle::sha256(b))) {\n        println!("{}", ln);\n    }\n}\n')
# the planted fast-path defect for the certification row: the wall's bottom edge loses its ink — every frame with a
# wall strip in view changes, the same way every time (live and on replay), so only the reference can see it
SIMTICK_PLANT = ("(r == k.top || r == k.bot)", "(r == k.top)")
BEARINGFAST_RS_SHA256 = "97ab3bf3a575954fdbaa0f1b4d3ed8bd511a6d8dffa01a3b99d864e393a2ee84"
VOCAB_RS_SHA256 = "30b9199255b0e342c1a20b9b47043c567b54c756e178f4fd7b7d633708dc69c0"
SIMTICK_KERNEL_PINS = {"formats.rs": "d948f8ce596400096271b6f9a63d257160540d424c06d0345dd8dc43ce3b0175", "hud.rs": "553d3ef7264b2587e724f974be3cc5a73299526e2a95480da6740d181c96dba4"}
PRESENT_RS_SHA256 = "8834752cfe2f1bdac046ee0b6d8d5a791467fef8deea4d6516a382834a5b71a3"


def _st_cardinal(k: int) -> int:
    return ((k + 45000) // ST_QUARTER) % 4


def _st_turn(k: int, d: int) -> int:
    return (k + d) % ST_YAW


def _st_delta(c: int, m: int, s: int):
    if not -ST_COUNTS_MAX <= c <= ST_COUNTS_MAX or not 1 <= m <= ST_MULT_MAX or s not in (ST_FINE, ST_COARSE):
        return None
    return c * m * s


def _st_token(x: int, z: int, yaw: int) -> str:
    return "%d,%d,%s" % (x, z, _LETTER[yaw // ST_QUARTER] if yaw % ST_QUARTER == 0 else yaw)


def _st_law_twin() -> list:
    """The laws, re-derived: the lines shell simtick-law must print."""
    L = "NESW"
    show = lambda v: "refused" if v is None else str(v)
    out = ["tick %d %d" % (ST_HZ, ST_TICK_US)]
    out.append("tick_of " + " ".join("%d=%d" % (t, t // ST_TICK_US) for t in (0, 1, 15624, 15625, 15626, 31249, 31250, 999999, 1000000)))
    cards = [_st_cardinal(k) for k in range(ST_YAW)]
    out.append("cardinal_digest " + sha256(bytes(ord(L[c]) for c in cards)))
    out.append("cardinal_owns " + " ".join("%s=%d" % (L[i], cards.count(i)) for i in range(4)))
    out.append("boundaries " + " ".join("%d=%s" % (k, L[cards[k]]) for k in (0, 44999, 45000, 134999, 135000, 224999, 225000, 314999, 315000, 359999)))
    out.append("quarter_law %d" % sum(1 for k in range(ST_YAW) if cards[(k + ST_QUARTER) % ST_YAW] == (cards[k] + 1) % 4
                                      and cards[(k - ST_QUARTER) % ST_YAW] == (cards[k] + 3) % 4))
    out.append("anchors " + " ".join("%d=%s" % (k, L[k // ST_QUARTER] if k % ST_QUARTER == 0 else "-") for k in (0, 1, 89999, 90000, 180000, 270000, 270001, 359999)))
    grid = "".join("%d,%d=%d;" % (k, sg * d, _st_turn(k, sg * d))
                   for k in (0, 1, 44999, 45000, 89999, 90000, 179999, 180000, 269999, 270000, 359999)
                   for d in (0, 1, 87, 88, 89999, 90000, 359999, 360000, 360001, ST_DELTA_MAX) for sg in (1, -1))
    out.append("turn_digest " + sha256(grid.encode()))
    out.append("turn " + " ".join("%d%+d=%d" % (k, d, _st_turn(k, d)) for k, d in ((0, -1), (359999, 1), (0, 360000), (0, -360000), (44968, 88), (88, -176))))
    grid = "".join("%d,%d,%d=%s;" % (c, m, s, show(_st_delta(c, m, s)))
                   for c in (1, -1, 2, 511, -511, 65536, ST_COUNTS_MAX, -ST_COUNTS_MAX) for m in (1, 2, 63, 64) for s in (ST_FINE, ST_COARSE))
    out.append("delta_digest " + sha256(grid.encode()))
    out.append("delta " + " ".join("%d,%d,%d=%s" % (c, m, s, show(_st_delta(c, m, s))) for c, m, s in (
        (1, 1, 88), (-3, 2, 88), (32, 1, 1), (ST_COUNTS_MAX, 64, 88), (ST_COUNTS_MAX + 1, 1, 1), (-ST_COUNTS_MAX - 1, 1, 1),
        (1, 0, 88), (1, 65, 88), (1, 1, 87), (1, 1, 2))))
    out.append("sens start=1,%d up(1)=2,%d up(64)=refused down(1)=refused down(64)=63,%d toggle(coarse)=1,%d toggle(fine)=1,%d"
               % (ST_COARSE, ST_COARSE, ST_COARSE, ST_FINE, ST_COARSE))
    out.append("rebind 41=51 44=45 57=57 53=53 51=51 45=45 25=25 27=27 20=20")
    # SIM-TICK-0a: the control map and the legal transitions (lines added on purpose with the amendment)
    out.append("control 21=mult+ 22=mult- 09=step 57=- 20=- 23=-")
    legal = lambda a, b: all(1 <= x[0] <= ST_MULT_MAX and x[1] in (ST_FINE, ST_COARSE) for x in (a, b)) and (
        (a[1] == b[1] and abs(a[0] - b[0]) == 1) or (a[0] == b[0] and a[1] != b[1]))
    out.append("transition " + " ".join("%d,%d>%d,%d=%s" % (a + b + ("legal" if legal(a, b) else "refused",)) for a, b in (
        ((1, 88), (2, 88)), ((2, 88), (1, 88)), ((1, 88), (1, 1)), ((1, 1), (1, 88)), ((1, 88), (3, 88)), ((1, 88), (2, 1)),
        ((1, 88), (1, 88)), ((64, 88), (65, 88)), ((1, 88), (0, 88)), ((64, 1), (63, 1)))))
    return out


def _st_text(script) -> str:
    return ",".join("%d:%s" % (t * ST_TICK_US + off, what) for t, off, what in script)


def _st_frame(lvl, til, x, z, yaw, cache):
    """The frame digest at a camera and heading from the kernel executable: the facing kernel at an anchor, the bearing
    REFERENCE anywhere else (`--at x,z,K` renders with kernel/bearing.rs and selfchecks)."""
    if yaw % ST_QUARTER == 0:
        return _sw_frame(lvl, til, (x, z, yaw // ST_QUARTER), cache)
    _sw_frame(lvl, til, (x, z, _st_cardinal(yaw)), cache) if cache.get("lvl") != lvl or cache.get("til") != til else None
    key = ("free", x, z, yaw, hashlib.sha256(lvl).hexdigest(), hashlib.sha256(til).hexdigest())
    if key not in cache:
        code, out, err = run(KERNEL_EXE, ["--level", cache["lp"], "--tiles", cache["tp"], "--at", "%d,%d,%d" % (x, z, yaw)])
        d = dict(ln.split(" ", 1) for ln in out.strip().splitlines() if " " in ln)
        if code != 0 or d.get("selfcheck") != "OK":
            raise Red("twin: the bearing reference at %d,%d,%d: %s" % (x, z, yaw, err.strip()))
        cache[key] = d["frame"]
    return cache[key]


def _st_start(camera=ST_CAMERA):
    lv = read(os.path.join(ORACLE, "levels", "witness.lvl"))
    tl = read(os.path.join(ORACLE, "tiles", "identity.tiles"))
    x, z, f = _cam_tuple(camera)
    return {"lvl": lv, "til": tl, "x": x, "z": z, "yaw": f * ST_QUARTER, "head": _sw_genesis(_sw_content(lv, tl), (x, z, f)),
            "sens": (1, ST_COARSE), "ticks": 0, "log": []}


def _st_twin(script, st, cache):
    """A whole tick run, re-derived: the commands (one per tick: the reports' sum applied once and first, then the other
    inputs in arrival order), the events with their cameras, witnesses, ticks and inputs, the head, the trace, the
    counts. `st` is the state the run starts from (a fresh base, or a parent's final state)."""
    import struct as _s
    first = st["ticks"]
    per = {}
    order = []
    for t, off, what in script:
        if t not in per:
            per[t] = {"sum": 0, "acts": []}
            order.append(t)
        if what[0] == "m" and what[1] in "+-" and what[2:].isdigit():   # a mouse report
            per[t]["sum"] += int(what[1:])
        else:
            per[t]["acts"].append(what)
    c = {k: 0 for k in SIMTICK_COUNTS}
    is_report = lambda w: w[0] == "m" and w[1] in "+-" and w[2:].isdigit()
    trace, ended, last_tick = [], "script", None
    lvl, til, x, z, yaw, head = st["lvl"], st["til"], st["x"], st["z"], st["yaw"], st["head"]
    m, s = st["sens"]
    log = list(st["log"])
    for t in order:
        if ended == "escape":
            break
        for _t, _o, what in [i for i in script if i[0] == t]:
            c["inputs"] += 1
            c["reports" if is_report(what) else ("actions" if what in ("mult+", "mult-", "step") else "keys")] += 1
        tick = first + t
        last_tick = tick
        cmd = per[t]
        over = abs(cmd["sum"]) > ST_COUNTS_MAX
        if cmd["sum"] == 0 and not over and not cmd["acts"]:
            continue
        c["commands"] += 1
        if over:
            c["refused"] += 1
            trace.append("tick %d look -> refused SIMTICK-COUNTS" % tick)
        elif cmd["sum"] != 0:
            d = cmd["sum"] * m * s
            yaw = _st_turn(yaw, d)
            wit = _st_frame(lvl, til, x, z, yaw, cache)
            tok = _st_token(x, z, yaw)
            head = _sw_fold(head, b"K", tok + ":" + wit)
            trace.append("tick %d look counts=%d multiplier=%d step=%d -> event %d look %d %s" % (tick, cmd["sum"], m, s, len(log), d, tok))
            log.append({"kind": "look", "delta": d, "camera": tok, "witness": wit, "tick": tick, "input": {"counts": cmd["sum"], "multiplier": m, "step": s}})
            c["looks"] += 1
            c["events"] += 1
        admitted = False   # SIM-TICK-0a: the tick is the coalescing boundary — one walked repeat a tick
        for what in cmd["acts"]:
            typed = what in ("mult+", "mult-", "step")
            repeat = not typed and what.endswith("+")
            key = what[:-1] if repeat else what
            if repeat:
                c["repeats"] += 1
                if key not in ST_HELD:
                    c["ignored"] += 1
                    trace.append("tick %d key %s+ -> repeat" % (tick, key))
                    continue
                if admitted:
                    c["coalesced"] += 1
                    trace.append("tick %d key %s+ -> coalesced" % (tick, key))
                    continue
                admitted = True
                c["walked"] += 1
            name = what if typed else "key " + what
            action = what if typed else ST_CONTROL.get(key)
            if action:
                # SIM-TICK-0a: a sensitivity action that takes effect is one configuration event; it folds nothing
                n = (m + 1, s) if action == "mult+" else (m - 1, s) if action == "mult-" else (m, ST_FINE if s == ST_COARSE else ST_COARSE)
                if 1 <= n[0] <= ST_MULT_MAX:
                    m, s = n
                    trace.append("tick %d %s -> event %d sensitivity %d,%d" % (tick, name, len(log), m, s))
                    log.append({"kind": "sensitivity", "multiplier": m, "step": s, "tick": tick})
                    c["settings"] += 1
                else:
                    c["refused"] += 1
                    trace.append("tick %d %s -> refused SIMTICK-MULTIPLIER" % (tick, name))
                continue
            b = ST_BIND.get(key)
            if b is None:
                c["unbound"] += 1
                trace.append("tick %d %s -> unbound" % (tick, name))
            elif b[0] == "end":
                trace.append("tick %d %s -> end" % (tick, name))
                ended = "escape"
                break
            elif b[0] == "move":
                f = _st_cardinal(yaw)
                nx, nz, nf = _sw_step(lvl, (x, z, f), b[1])
                if b[1] in "FBQE" and (nx, nz) == (x, z):
                    c["blocked"] += 1
                yaw = _st_turn(yaw, ST_QUARTER * ((nf - f) % 4))
                x, z = nx, nz
                wit = _st_frame(lvl, til, x, z, yaw, cache)
                tok = _st_token(x, z, yaw)
                head = _sw_fold(head, b"M", wit)
                trace.append("tick %d %s -> event %d move %s %s" % (tick, name, len(log), b[1], tok))
                log.append({"kind": "move", "command": b[1], "camera": tok, "witness": wit, "tick": tick})
                c["moves"] += 1
                c["events"] += 1
            else:
                if b[0] == "toggle":
                    dx, dz = _FWD[_st_cardinal(yaw)]
                    fx, fz = x + dx, z + dz
                    w_, h_ = _s.unpack_from("<II", lvl, 8)
                    cell = chr(lvl[16 + fz * w_ + fx]) if 0 <= fx < w_ and 0 <= fz < h_ else None
                    code = ("LIVEINPUT-EDIT-OUTSIDE" if cell is None else "LIVEINPUT-EDIT-STAIR" if cell not in "#." else
                            "LIVEINPUT-EDIT-BORDER" if cell == "#" and (fx in (0, w_ - 1) or fz in (0, h_ - 1)) else None)
                    if code:
                        c["refused"] += 1
                        trace.append("tick %d %s -> refused %s" % (tick, name, code))
                        continue
                    spec = "cell:%d,%d,%s" % (fx, fz, "." if cell == "#" else "#")
                else:
                    off = 8 + b[1] * 256 * 256 * 3
                    tile = til[off:off + 256 * 256 * 3]
                    cur = tuple(tile[:3]) if tile == tile[:3] * (256 * 256) else None
                    rgb = LIVEAUTHOR_PALETTE[(LIVEAUTHOR_PALETTE.index(cur) + 1) % 8] if cur in LIVEAUTHOR_PALETTE else LIVEAUTHOR_PALETTE[0]
                    spec = "tile:%s,%d,%d,%d" % ((_ST_CLASSES[b[1]],) + tuple(rgb))
                lvl, til = _sw_apply(lvl, til, spec)
                wit = _sw_content(lvl, til)
                head = _sw_fold(head, b"E", wit)
                trace.append("tick %d %s -> event %d edit %s" % (tick, name, len(log), spec))
                log.append({"kind": "edit", "spec": spec, "witness": wit, "tick": tick})
                c["edits"] += 1
                c["events"] += 1
    ticks = first if last_tick is None else last_tick + 1
    return ({"lvl": lvl, "til": til, "x": x, "z": z, "yaw": yaw, "head": head, "sens": (m, s), "ticks": ticks, "log": log},
            trace, c, ended)


def _st_run(script_text, logs, name, extra=None, exe=None):
    """One shell simtick-selftest; returns (completed process, the saved session's path or None, the --out data or None)."""
    env = dict(os.environ, **{REFUSALLOG_ENV: logs[0], RUNLEDGER_ENV: logs[1], LIVESESSION_ENV: GATE_SESSIONS})
    out = os.path.join(BUILD, "simtick-%s.json" % name)
    if os.path.exists(out):
        os.remove(out)
    cp = subprocess.run([exe or SHELL_EXE, "simtick-selftest", "--script", script_text, "--out", out] + (extra or []),
                        capture_output=True, text=True, cwd=ROOT, env=env)
    m_ = re.search(r"saved and verified: (.+?session\.json)", cp.stdout)
    raw = None
    if os.path.exists(out):
        with open(out, encoding="utf-8") as fh:
            raw = json.load(fh)["data"]
        os.remove(out)
    return cp, (m_.group(1) if m_ else None), raw


def _st_script_s(logs, name):
    cp, path, raw = _st_run(_st_text(SIMTICK_SCRIPT), logs, name, ["--camera", ST_CAMERA])
    if cp.returncode != 0 or path is None or raw is None or "simtick court OK" not in cp.stdout:
        raise Red("script S did not run to a saved and verified session: " + (cp.stderr.strip() or cp.stdout.strip())[-300:])
    return cp, path, raw


def _st_need():
    need_rustc()
    if SHELL_EXE is None or SESSIONWALK_EXE is None or KERNEL_EXE is None:
        raise Red("the shell, the workshop's sessionwalk or the kernel was not built")


def simtick_preregistered():
    """SIM-TICK-0's method is locked: the tick, one command per tick, the look's delta, the nearest cardinal, the binding,
    the look event and its fold, ticks recorded and never authority, certification at save — registered before the build."""
    e = locked_entry("SIM-TICK-0", {
        "windowless, never combined with the window": ("hyp", ("completely windowless", "raw input -> tick command -> session-walk -> authority", "never combined")),
        "the tick and one command per tick": ("hyp", ("exactly 15,625 us", "t div 15625", "applied once", "in arrival order", "an empty tick makes nothing")),
        "the look": ("hyp", ("delta = counts x multiplier x step", "a whole number 1..64", "88 ids coarse or 1 id fine", "takes effect from the next tick")),
        "the heading and the nearest cardinal": ("hyp", ("(k + delta) mod 360000", "((k + 45000) div 90000) mod 4", "going clockwise")),
        "the binding": ("hyp", ("a and d rebound to the strafes", "w, a, s and d never change the heading", "stay quarter turns")),
        "the look event and its fold": ("hyp", ("gains one event, a look", "sha256(head : k : token : witness)", "base camera stays one of the four facings")),
        "ticks are when, not what": ("hyp", ("raw counts are never the meaning of a look", "the tick index is when, not what", "the head does not cover it")),
        "certified at save or not saved": ("hyp", ("rendered once", "recomputed by the reference kernel", "no saved-but-uncertified state")),
        "the law row": ("succ", ("all 360,000 ids", "44999 is n and 45000 is e", "15,624 us is tick 0 and 15,625 us is tick 1", "a coarse step of 87")),
        "the script": ("succ", ("a zero-sum tick", "the look is still applied first", "the exact tie reached and left in fine steps", "a whole turn", "exceed 2^31 - 1")),
        "replay, equivalence, certify, resume": ("succ", ("the kernel executable, asked directly", "refused by both verifiers", "the head covering the token",
                                                          "saves identical data", "livesession-uncertified", "liveinput-heading")),
        "what fails it": ("fail", ("any float, clock, window or win32 input", "going anticlockwise", "two looks to different headings folding to one head",
                                   "saved-but-uncertified", "a rule changed after a row was seen")),
        "scope": ("lims", ("rules only", "it is not authority", "+-45 degrees", "is not measured here", "no picture is shown")),
    })
    return ("SIM-TICK-0's method is locked (hash %s) before the build: the 64 Hz tick of exactly 15,625 us, one command per "
            "tick (the reports' sum applied once and first, then the keys in arrival order), delta = counts x multiplier x "
            "step, the nearest cardinal with the tie clockwise, the look event folded over its token and witness, ticks "
            "recorded and never authority, and a session saved reference-certified or not saved" % e["chain_hash"][:8])


def simtick_law():
    """The laws are the registered ones, exhaustively: shell simtick-law's lines — the tick boundaries, the nearest
    cardinal of all 360,000 ids, the quarter-turn law at every id, the turn's wrap, the delta over the grid, the
    sensitivity's ends, the rebinding — equal a Python re-derivation line for line; and a build with the tie-break
    reversed, the tick a microsecond short or long, or a coarse step of 87 prints different lines."""
    _st_need()
    want = _st_law_twin()
    code, out, err = run(SHELL_EXE, ["simtick-law"])
    got = out.strip().splitlines()
    if code != 0 or got != want:
        raise Red("the shell's laws are not the re-derived ones: %r" % (next(((g, w) for g, w in zip(got + [None] * 20, want) if g != w), err.strip()),))
    d = dict(ln.split(" ", 1) for ln in want)
    if (d["cardinal_owns"] != "N=90000 E=90000 S=90000 W=90000" or d["quarter_law"] != "360000"
            or d["boundaries"] != "0=N 44999=N 45000=E 134999=E 135000=S 224999=S 225000=W 314999=W 315000=N 359999=N"
            or "15624=0 15625=1" not in d["tick_of"]):
        raise Red("the re-derived laws are not the registered boundaries")
    src = read(os.path.join(SHELL, "simtick.rs")).decode("utf-8")
    small = compile_rs(SHELL, "simticklaw.rs", "simtick-law", {"simticklaw.rs": SIMTICK_LAW_MAIN})
    code, out, _e = run(small, [])
    if code != 0 or out.strip().splitlines() != want:
        raise Red("the law instrument (simtick.rs alone) does not print the shell's laws")
    caught = []
    for why, (a, b, lines) in SIMTICK_LAW_MUTANTS.items():
        if src.count(a) != 1:
            raise Red("the mutation site for %s is not unique in simtick.rs" % why)
        exe = compile_rs(SHELL, "simticklaw.rs", "simtick-law-mutant", {"simticklaw.rs": SIMTICK_LAW_MAIN, "simtick.rs": src.replace(a, b)})
        code, out, _e = run(exe, [])
        md = dict(ln.split(" ", 1) for ln in out.strip().splitlines())
        differing = [k for k in d if md.get(k) != d[k]]
        if code != 0 or not all(k in differing for k in lines):
            raise Red("a build with %s was not caught on %s (it differs on %s)" % (why, ", ".join(lines), ", ".join(differing) or "nothing"))
        caught.append(why)
    return ("the laws are the registered ones, line for line with a Python re-derivation: tick t div 15,625 (15,624 us is "
            "tick 0, 15,625 us tick 1); the nearest cardinal of all 360,000 ids (digest %s…; each cardinal owns 90,000; "
            "44999 N, 45000 E, 135000 S, 225000 W, 315000 N); cardinal(k +- 90000) = cardinal(k) +- 1 at all 360,000 ids; "
            "the turn's wrap; delta = counts x multiplier x step over the grid with its refusals; the sensitivity's ends; "
            "A and D rebound to the strafes. A build with %s is caught" % (d["cardinal_digest"][:12], ", with ".join(caught)))


def simtick_script():
    """Script S through shell simtick-selftest becomes exactly its registered commands and events: every outcome at its
    tick, every saved event (kind, parameter, camera token, tick, inputs), the counts, the final camera, tick count and
    sensitivity — against the twin's re-derivation from the script alone; the refusals are one refusal-log record each
    and no event; the run is one ledger line."""
    import refusallog as RL
    import runledger as RLG
    _st_need()
    logs = _ls_logs("simtick-script")
    cp, path, raw = _st_script_s(logs, "script")
    cache = {}
    st, trace, counts, ended = _st_twin(SIMTICK_SCRIPT, _st_start(), cache)
    if raw["trace"] != trace:
        raise Red("script S's outcomes are not the re-derived ones: %r" % (next((g, w) for g, w in zip(raw["trace"] + [None] * 200, trace + [None]) if g != w),))
    if counts != SIMTICK_COUNTS or {k: raw["counts"].get(k) for k in SIMTICK_COUNTS} != SIMTICK_COUNTS or raw["ended"] != "escape" or ended != "escape":
        raise Red("script S's counts are not the registered ones: %s" % raw["counts"])
    d = json.loads(read(path).decode("utf-8"))["data"]
    strip = lambda log: [{k: v for k, v in e.items() if k != "witness"} for e in log]
    if strip(d["log"]) != strip(st["log"]):
        raise Red("script S's saved events are not the re-derived ones: %r" % (next((g, w) for g, w in zip(strip(d["log"]) + [None] * 99, strip(st["log"])) if g != w),))
    fin = SIMTICK_FINAL
    if (d["final_camera"], d["ticks"], d["looks"], d["moves"], d["edits"], d["sensitivity_changes"]) != (
            fin["camera"], {"hz": ST_HZ, "count": fin["ticks"], "multiplier": fin["sensitivity"][0], "step": fin["sensitivity"][1]},
            counts["looks"], counts["moves"], counts["edits"], counts["settings"]) or _st_token(st["x"], st["z"], st["yaw"]) != fin["camera"]:
        raise Red("script S's final camera, tick block or counts are not the registered ones: %s %s" % (d["final_camera"], d["ticks"]))
    # the registered particulars, read from the saved events
    ev = d["log"]
    at = lambda t: [e for e in ev if e["tick"] == t]
    checks = [
        (at(0) == [e for e in ev if e["tick"] == 0] and len(at(0)) == 1 and at(0)[0]["delta"] == 352 and at(0)[0]["input"]["counts"] == 4, "three reports summed in tick 0"),
        (len(at(1)) == 1 and at(1)[0]["delta"] == 88, "the report at exactly 15,625 us is tick 1's"),
        (at(2) == [], "the zero-sum tick made no event"),
        ([e["kind"] for e in at(4)] == ["look", "move"] and at(4)[0]["camera"] == "28,28,45056" and at(4)[1]["camera"] == "29,28,45056", "the look is applied before the key that arrived first"),
        (at(6)[0]["camera"] == "29,28,45000" and at(6)[1]["camera"] == "30,28,45000", "the exact tie is east"),
        (at(7)[0]["camera"] == "30,28,44999" and at(7)[1]["camera"] == "30,28,44999", "one id below the tie is north, and the step is blocked"),
        (at(13)[0]["camera"] == "30,27,314999", "a quarter turn at a free heading"),
        (at(15)[0]["input"] == {"counts": 1, "multiplier": 1, "step": 88} and at(16)[0]["input"] == {"counts": 1, "multiplier": 2, "step": 88}
         and at(15)[1] == {"kind": "sensitivity", "multiplier": 2, "step": 88, "tick": 15}, "a sensitivity action takes effect from the next tick, and is its own event after the look"),
        (at(18)[0]["delta"] == -176 and at(18)[0]["camera"] == "30,27,359967", "a negative look through 0"),
        (at(20)[0]["camera"] == "30,27,N" and at(21)[0]["delta"] == 360000 and at(21)[0]["camera"] == "30,27,N" and at(21)[0]["witness"] == at(20)[0]["witness"], "back to an anchor, then a whole turn"),
        ([e["kind"] for e in at(25)] == ["move"] and at(25)[0]["camera"] == "30,26,64", "the refused look's tick still applied its key"),
    ]
    bad = [why for ok, why in checks if not ok]
    if bad:
        raise Red("script S did not register: " + "; ".join(bad))
    records, rbad = RL.read(logs[0])
    runs, lbad = RLG.read(logs[1])
    got = sorted((r["reason_code"], r["attribution"]) for r in records)
    if rbad or lbad or got != [("SIMTICK-COUNTS", "input.look"), ("SIMTICK-MULTIPLIER", "input.sensitivity"), ("SIMTICK-MULTIPLIER", "input.sensitivity")] \
            or len(runs) != 1 or (runs[0]["operation"], runs[0]["surface"], runs[0]["exit_code"], runs[0]["refusals"]) != ("livesession", "none", 0, 3):
        raise Red("script S's refusals are not one record each, or the run is not one ledger line on surface none: %s" % got)
    return ("script S on the tick run, windowless: %d inputs in 28 ticks became %d commands and exactly the re-derived "
            "outcomes — %d looks, %d moves (%d blocked), %d edits; the look applied once and first in its tick; the tie at "
            "45000 east and 44999 north; a quarter turn, the strafes, Space and a class key at free headings; a look back "
            "to an anchor and a whole turn; the multiplier refused below 1 and above 64 and the over-bound counts refused "
            "(%d refusal-log records, no event), the unbound key ignored — saved and verified, final %s, tick count %d, "
            "sensitivity %d,%d" % (counts["inputs"], counts["commands"], counts["looks"], counts["moves"], counts["blocked"], counts["edits"],
                                   counts["refused"], fin["camera"], fin["ticks"], fin["sensitivity"][0], fin["sensitivity"][1]))


def _st_edit_event(text, k, fn):
    """Edit saved event k's line with fn(line) -> line and reseal; the head is left as stored."""
    lines = text.split("\n")
    items = [i for i, ln in enumerate(lines) if ln.startswith('   {"kind": ')]
    new = fn(lines[items[k]])
    if new == lines[items[k]]:
        raise Red("the forgery's strings are not where the saved file keeps them")
    lines[items[k]] = new
    return _ls_reseal("\n".join(lines))


def simtick_replay():
    """Replay produces the same state and frame witnesses, three ways: every frame witness of S's saved session is the
    kernel executable's at that camera (the bearing reference at a free heading) and the head is the twin's fold; the
    workshop's sessionwalk verifies the file; the same events authored in the workshop reach the same head. One changed
    delta, input or camera token, and a tick run backwards, are each refused by both verifiers — and so is a look moved
    consistently to a neighbouring heading with the same index frame, because the head covers the token."""
    import livesession as LS
    _st_need()
    logs = _ls_logs("simtick-replay")
    _cp, path, _raw = _st_script_s(logs, "replay")
    text = read(path).decode("utf-8")
    d = LS.check_saved(read(path), ROOT)["data"]
    cache = {}
    st, _t, _c, _e = _st_twin(SIMTICK_SCRIPT, _st_start(), cache)
    # re-pinned on purpose with SIM-TICK-0a: a sensitivity event has no witness
    if [e.get("witness") for e in d["log"]] != [e.get("witness") for e in st["log"]] or d["head"] != st["head"]:
        k = next((i for i, (a, b) in enumerate(zip(d["log"], st["log"])) if a.get("witness") != b.get("witness")), None)
        raise Red("the saved session's witnesses are not the kernel executable's (first at event %s), or its head is not the twin's fold" % k)
    free = sum(1 for e in d["log"] if e["kind"] in ("move", "look") and LS.free_heading(e["camera"]))
    code, out, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", path])
    if code != 0 or ("SESSIONWALK verify OK head %s" % d["head"][:12]) not in out:
        raise Red("the workshop does not verify script S's saved session: " + (err.strip() or out.strip()))
    # the same events authored in the workshop, outside time
    sp = os.path.join(SW, "simtick-authored.json")
    code, _o, err = run(SESSIONWALK_EXE, ["new", "--level", os.path.join(ORACLE, "levels", "witness.lvl"), "--tiles", os.path.join(ORACLE, "tiles", "identity.tiles"),
                                          "--camera", ST_CAMERA, "--out", sp])
    for e in d["log"] if code == 0 else []:
        if e["kind"] == "sensitivity":
            continue   # SIM-TICK-0a: configuration, not a world event — the workshop authors the world events alone
        verb, flag, param = {"move": ("move", "--command", e.get("command")), "edit": ("edit", "--edit", e.get("spec")),
                             "look": ("look", "--delta", str(e.get("delta")))}[e["kind"]]
        code, _o, err = run(SESSIONWALK_EXE, [verb, "--session", sp, flag, param])
        if code != 0:
            break
    if code != 0:
        raise Red("the workshop could not author script S's events: " + err.strip())
    authored = _sw_stored(sp)
    if authored["head"] != d["head"] or authored["final_camera"] != d["final_camera"] or "ticks" in authored or any("tick" in e for e in authored["log"]):
        raise Red("the same events authored in the workshop do not reach the saved session's head, or carry ticks")
    # one changed thing, resealed, the stored head left alone: both verifiers refuse
    k_look = next(i for i, e in enumerate(d["log"]) if e["kind"] == "look" and e["tick"] == 7)
    k_move = next(i for i, e in enumerate(d["log"]) if e["kind"] == "move" and e["tick"] == 8)
    cases = [
        ("a changed delta", _st_edit_event(text, k_look, lambda ln: ln.replace('"delta": -1,', '"delta": -2,')), "LIVESESSION-CORRUPT", "TICK-FORM"),
        ("a changed input", _st_edit_event(text, k_look, lambda ln: ln.replace('"counts": -1,', '"counts": -2,')), "LIVESESSION-CORRUPT", "TICK-FORM"),
        ("a changed camera token on a look", _st_edit_event(text, k_look, lambda ln: ln.replace('"camera": "30,28,44999"', '"camera": "30,28,44998"')), "LIVESESSION-CORRUPT", "CHAIN-BROKEN"),
        ("a changed camera token on a move", _st_edit_event(text, k_move, lambda ln: ln.replace('"camera": "29,28,44999"', '"camera": "29,28,44998"')), "LIVESESSION-TAMPERED", "CHAIN-BROKEN"),
        ("a tick run backwards", _st_edit_event(text, k_move, lambda ln: ln.replace('"tick": 8}', '"tick": 6}')), "LIVESESSION-CORRUPT", "TICK-FORM"),
        ("an untimed look given inputs away", _st_edit_event(text, k_look, lambda ln: ln.replace(', "tick": 7,', ',')), "LIVESESSION-CORRUPT", "TICK-FORM"),
    ]
    for i, (why, body, shell_code, ws_code) in enumerate(cases):
        p = _ls_write("simtick-case%d" % i, body)
        cp, child, _r = _st_run("0:ESC", logs, "replay-case", ["--resume", p])
        if cp.returncode != 2 or shell_code not in cp.stderr or child is not None:
            raise Red("%s was not refused by the shell with %s: %s" % (why, shell_code, (cp.stderr.strip() or cp.stdout.strip())[-200:]))
        code, _o, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", p])
        if code != 2 or ws_code not in err:
            raise Red("%s was not refused by the workshop with %s: %s" % (why, ws_code, err.strip()[-200:]))
    # the head covers the token: two fine looks, one id apart, whose index frame the reference shows to be the same
    lv, tl = read(os.path.join(ORACLE, "levels", "witness.lvl")), read(os.path.join(ORACLE, "tiles", "identity.tiles"))
    pair = next(((h, h - 1) for h in range(100, 60, -1) if _st_frame(lv, tl, 28, 28, h, cache) == _st_frame(lv, tl, 28, 28, h - 1, cache)), None)
    if pair is None:
        raise Red("no two neighbouring headings at 28,28 share an index frame: the row has nothing to show (precondition)")
    saved = {}
    for h in pair:
        cp, p, _r = _st_run("0:step,%d:m+%d,%d:ESC" % (ST_TICK_US, h, 2 * ST_TICK_US), logs, "replay-pair", ["--camera", ST_CAMERA])
        if cp.returncode != 0 or p is None:
            raise Red("a single fine look to %d did not save: %s" % (h, cp.stderr.strip()[-200:]))
        saved[h] = read(p).decode("utf-8")
    da, db = (json.loads(saved[h])["data"] for h in pair)
    # re-pinned on purpose with SIM-TICK-0a: the step toggle is now event 0, so the look is event 1
    if da["log"][1]["witness"] != db["log"][1]["witness"] or da["head"] == db["head"]:
        raise Red("two looks to neighbouring headings with one index frame fold to one head, or their frames differ")
    a, b = pair
    moved = _st_edit_event(saved[a], 1, lambda ln: ln.replace('"delta": %d,' % a, '"delta": %d,' % b).replace('"camera": "28,28,%d"' % a, '"camera": "28,28,%d"' % b)
                           .replace('"counts": %d,' % a, '"counts": %d,' % b))
    moved = _ls_reseal(moved.replace('"final_camera": "28,28,%d"' % a, '"final_camera": "28,28,%d"' % b))
    p = _ls_write("simtick-moved", moved)
    cp, child, _r = _st_run("0:ESC", logs, "replay-case", ["--resume", p])
    code, _o, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", p])
    if cp.returncode != 2 or "LIVESESSION-CORRUPT" not in cp.stderr or "not the fold" not in cp.stderr or child is not None or code != 2 or "CHAIN-BROKEN" not in err:
        raise Red("a look moved consistently to a neighbouring heading with the same index frame was accepted: the head does not cover the token")
    return ("replay reproduces the state and the frame witnesses three ways: all %d of script S's saved world events carry the "
            "kernel executable's frame at their camera (%d at free headings, the bearing reference's) and the twin's fold "
            "is the saved head %s…; the workshop's sessionwalk verifies the file; the same events authored in the workshop "
            "reach the same head without ticks. A changed delta, input or camera token, a tick run backwards and a look "
            "stripped of its tick are each refused by both verifiers; and a look moved consistently from %d to %d — one "
            "index frame, the reference shows — is refused too: the head covers the token"
            % (sum(1 for e in d["log"] if "witness" in e), free, d["head"][:12], a, b))


def _st_data(path):
    raw = read(path)
    return raw[:raw.index(b'\n "live": ')]


def simtick_equivalence():
    """The tick is the unit: script S with every input moved inside its own tick and every tick's reports split or
    merged to the same sum saves byte-identical data; the same commands at later ticks save the same events, witnesses
    and head, differing only in their tick fields and the tick count."""
    _st_need()
    logs = _ls_logs("simtick-equivalence")
    _cp, path, _raw = _st_script_s(logs, "equiv")
    # moved: per tick, the non-mouse inputs keep their order but take new times; the reports are merged into one sum
    # (split in two where one report could not hold it) and placed last, a microsecond before the next tick
    moved = []
    ticks = sorted({t for t, _o, _w in SIMTICK_SCRIPT})
    for t in ticks:
        mine = [w for tt, _o, w in SIMTICK_SCRIPT if tt == t]
        acts = [w for w in mine if not (w[0] == "m" and w[1] in "+-")]
        total = sum(int(w[1:]) for w in mine if w[0] == "m" and w[1] in "+-")
        for i, w in enumerate(acts):
            moved.append((t, 100 + 7 * i, w))
        reports = [w for w in mine if w[0] == "m" and w[1] in "+-"]
        if reports:
            parts = [total] if abs(total) <= ST_COUNTS_MAX else [ST_COUNTS_MAX, total - ST_COUNTS_MAX]
            if abs(total) <= ST_COUNTS_MAX and abs(total) > 1:
                parts = [total - total // 2, total // 2]      # split to the same sum
            for i, v in enumerate(parts):
                moved.append((t, ST_TICK_US - len(parts) + i, "m%+d" % v))
    if _st_text(moved) == _st_text(SIMTICK_SCRIPT) or sorted(set(t for t, _o, _w in moved)) != ticks:
        raise Red("the moved script is the script itself, or left its ticks")
    cp, p_moved, _r = _st_run(_st_text(moved), logs, "equiv-moved", ["--camera", ST_CAMERA])
    if cp.returncode != 0 or p_moved is None:
        raise Red("the moved script did not save: " + cp.stderr.strip()[-200:])
    if _st_data(p_moved) != _st_data(path):
        raise Red("moving inputs inside their ticks, or splitting and merging a tick's reports, changed the saved data")
    # later: every tick three times as late, plus 1000
    later = [(1000 + 3 * t, off, w) for t, off, w in SIMTICK_SCRIPT]
    cp, p_later, _r = _st_run(_st_text(later), logs, "equiv-later", ["--camera", ST_CAMERA])
    if cp.returncode != 0 or p_later is None:
        raise Red("the later script did not save: " + cp.stderr.strip()[-200:])
    a, b = (json.loads(read(p_).decode("utf-8"))["data"] for p_ in (path, p_later))
    untimed = lambda dd: [{k: v for k, v in e.items() if k != "tick"} for e in dd["log"]]
    if (untimed(a) != untimed(b) or a["head"] != b["head"] or a["final_camera"] != b["final_camera"] or a["final_content"] != b["final_content"]
            or [e["tick"] for e in b["log"]] != [1000 + 3 * e["tick"] for e in a["log"]] or b["ticks"]["count"] != 1000 + 3 * 27 + 1
            or {k: v for k, v in b["ticks"].items() if k != "count"} != {k: v for k, v in a["ticks"].items() if k != "count"}):
        raise Red("the same commands at later ticks did not save the same events, witnesses and head with only the tick fields different")
    for p_ in (p_moved, p_later):
        code, out, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", p_])
        if code != 0:
            raise Red("the workshop does not verify %s: %s" % (p_, err.strip()))
    return ("the tick is the unit: script S with every input moved inside its own tick and every tick's reports split or "
            "merged to the same sum saves byte-identical data (%d bytes); the same commands at ticks 1000 + 3t save the same "
            "%d events, witnesses and head %s…, differing only in their tick fields and the tick count (%d, not %d) — the "
            "tick index is recorded, and no world state or head depends on it"
            % (len(_st_data(path)), len(a["log"]), a["head"][:12], b["ticks"]["count"], a["ticks"]["count"]))


_ST_PLANTED = {}


def _st_planted():
    """The shell built with the planted, self-consistent fast-path defect (once a gate; MOUSE-LOOK-0's sample row runs
    the same build)."""
    if "exe" not in _ST_PLANTED:
        bf = read(os.path.join(KERNEL, "bearingfast.rs")).decode("utf-8")
        main_src = read(os.path.join(SHELL, "main.rs")).decode("utf-8")
        site = '#[path = "../kernel/bearingfast.rs"]'
        if bf.count(SIMTICK_PLANT[0]) != 1 or main_src.count(site) != 1:
            raise Red("the plant's site is not unique in kernel/bearingfast.rs, or the shell does not include it where expected")
        _ST_PLANTED["exe"] = compile_rs(SHELL, "main.rs", "shell-simtick-planted", {
            "main.rs": main_src.replace(site, '#[path = "bearingfast_planted.rs"]'),
            "bearingfast_planted.rs": bf.replace(SIMTICK_PLANT[0], SIMTICK_PLANT[1])})
    return _ST_PLANTED["exe"]


def simtick_certify():
    """A session is saved reference-certified or not saved: script S's save recomputes every free-heading frame with the
    reference and records how many; a shell built with a planted, self-consistent defect in the fast path renders,
    journals and would replay its own wrong frames, and is refused at the save — LIVESESSION-UNCERTIFIED naming the
    first free-heading event, no session file, exit 2, one refusal-log record; under the same planted shell a walk that
    never leaves the four facings saves, zero frames recomputed."""
    import livesession as LS
    import refusallog as RL
    import runledger as RLG
    _st_need()
    logs = _ls_logs("simtick-certify")
    cp, path, _raw = _st_script_s(logs, "certify")
    doc = LS.check_saved(read(path), ROOT)
    d, live = doc["data"], doc["live"]
    free = [i for i, e in enumerate(d["log"]) if e["kind"] in ("move", "look") and LS.free_heading(e["camera"])]
    if (live.get("certified") != {"reference": "kernel/bearing.rs", "frames": len(free)} or len(free) != SIMTICK_FINAL["free_frames"]
            or live.get("bearing") != LS.bearing_id(ROOT)
            or ("certified: %d free-heading frames recomputed by the reference kernel, all equal" % len(free)) not in cp.stdout):
        raise Red("script S's save did not recompute its %d free-heading frames with the reference and record it: %s" % (len(free), live.get("certified")))
    planted = _st_planted()
    logs2 = _ls_logs("simtick-certify-planted")
    before = set(os.listdir(GATE_SESSIONS))
    cp, p, _r = _st_run(_st_text(SIMTICK_SCRIPT), logs2, "certify-planted", ["--camera", ST_CAMERA], planted)
    m = re.search(r"LIVESESSION-UNCERTIFIED: event (\d+): the reference's frame", cp.stderr)
    made = sorted(set(os.listdir(GATE_SESSIONS)) - before)
    if cp.returncode != 2 or p is not None or m is None or int(m.group(1)) != free[0] or "saved and verified" in cp.stdout:
        raise Red("a shell with a defective fast path was not refused at the save naming the first free-heading event: %s"
                  % (cp.stderr.strip() or cp.stdout.strip())[-300:])
    if len(made) != 1 or sorted(os.listdir(os.path.join(GATE_SESSIONS, made[0]))) != ["journal.vsj"]:
        raise Red("the refused run left something other than its journal: %s" % made)
    records, rbad = RL.read(logs2[0])
    runs, lbad = RLG.read(logs2[1])
    cert = [r for r in records if r["reason_code"] == "LIVESESSION-UNCERTIFIED"]
    if rbad or lbad or len(cert) != 1 or cert[0]["attribution"] != "session.certify" or len(runs) != 1 or runs[0]["exit_code"] != 2:
        raise Red("the uncertified save is not one refusal-log record and one ledger line ending 2")
    # the planted shell's witnesses really are wrong, and self-consistently so: its journal's first look is not the reference's
    recs, _torn = _ls_journal(os.path.join(GATE_SESSIONS, made[0], "journal.vsj"))
    if recs[1 + free[0]]["witness"] == d["log"][free[0]]["witness"] or len(recs) != 1 + len(d["log"]):
        raise Red("the planted shell did not journal a wrong frame at the first free-heading event: the plant did not bite")
    cp, p, _r = _st_run("0:W,15625:RIGHT,31250:W,46875:SPACE,62500:ESC", logs2, "certify-anchors", ["--camera", ST_CAMERA], planted)
    if cp.returncode != 0 or p is None or LS.check_saved(read(p), ROOT)["live"]["certified"]["frames"] != 0 or "certified:" in cp.stdout:
        raise Red("a walk that never leaves the four facings did not save with zero frames recomputed under the planted shell")
    code, _o, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", p])
    if code != 0:
        raise Red("the workshop does not verify the anchors-only tick session: " + err.strip())
    return ("a session is saved reference-certified or not saved: script S's save recomputed its %d free-heading frames "
            "with kernel/bearing.rs across threads, all equal, and recorded it; a shell whose fast path drops the wall's "
            "bottom edge — wrong the same way live and on replay — was refused at the save (LIVESESSION-UNCERTIFIED, event "
            "%d, the first at a free heading), wrote no session file, left only its journal, ended 2 with one refusal-log "
            "record; under that same shell a walk on the four facings saved with zero frames to recompute"
            % (len(free), free[0]))


def simtick_resume():
    """A tick session resumes as itself: S's saved session continues with its heading, its tick count and its
    sensitivity (the first new look uses the saved multiplier, the new ticks follow the parent's 28), re-derived by the
    twin from the parent's state; a crashed tick run's journal recovers its look events, its tick count and its last
    look's sensitivity; a session left at a free heading is refused by the window loop (LIVEINPUT-HEADING), and one left
    at an anchor is continued by it, its untimed events beside the timed ones."""
    import livesession as LS
    _st_need()
    logs = _ls_logs("simtick-resume")
    _cp, parent, _raw = _st_script_s(logs, "resume")
    cache = {}
    st0, _t, _c, _e = _st_twin(SIMTICK_SCRIPT, _st_start(), cache)
    st1, trace, _c1, _e1 = _st_twin(SIMTICK_RESUME, st0, cache)
    cp, child, raw = _st_run(_st_text(SIMTICK_RESUME), logs, "resume-child", ["--resume", parent])
    if cp.returncode != 0 or child is None or raw["trace"] != trace or raw["first_tick"] != 28:
        raise Red("the continuation is not the twin's from the parent's state: %s" % ((cp.stderr.strip() or str(raw and raw["trace"]))[-300:]))
    doc = LS.check_saved(read(child), ROOT)
    d, lin = doc["data"], doc["live"]["lineage"]
    pd = json.loads(read(parent).decode("utf-8"))["data"]
    new = d["log"][len(pd["log"]):]
    # re-pinned on purpose with SIM-TICK-0a: the lowered multiplier is its own event, at tick 30
    if (d["log"][:len(pd["log"])] != pd["log"] or d["head"] != st1["head"] or [e["tick"] for e in new] != [28, 29, 30, 31]
            or new[0]["input"] != {"counts": -1, "multiplier": 64, "step": 1} or new[0]["camera"] != "30,26,N"
            or new[2] != {"kind": "sensitivity", "multiplier": 63, "step": 1, "tick": 30}
            or new[3]["input"] != {"counts": 2, "multiplier": 63, "step": 1} or d["final_camera"] != "30,26,126"
            or d["ticks"] != {"hz": ST_HZ, "count": 33, "multiplier": 63, "step": 1}
            or (lin["source"], lin["parent_events"], lin["parent_head"]) != ("session", len(pd["log"]), pd["head"])):
        raise Red("the continuation did not keep the parent's heading, tick count and sensitivity: %s %s" % (new, d["ticks"]))
    code, _o, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", child])
    if code != 0:
        raise Red("the workshop does not verify the continuation: " + err.strip())
    # the window loop: a free heading refuses; an anchor continues
    cp, p, _r = _la_run(["--resume", child, "--keys", "W,ESC"], logs)
    if cp.returncode != 2 or "LIVEINPUT-HEADING" not in cp.stderr or p is not None:
        raise Red("the window loop did not refuse a session left at a free heading: " + (cp.stderr.strip() or cp.stdout.strip())[-200:])
    cp, anchored, _r = _st_run("0:m-2,15625:ESC", logs, "resume-anchor", ["--resume", child])   # -2 x 63 x 1: back to north
    if cp.returncode != 0 or anchored is None or json.loads(read(anchored).decode("utf-8"))["data"]["final_camera"] != "30,26,N":
        raise Red("the session did not return to an anchor: " + cp.stderr.strip()[-200:])
    cp, cont, _r = _la_run(["--resume", anchored, "--keys", "LEFT,W,ESC"], logs)
    if cp.returncode != 0 or cont is None:
        raise Red("the window loop did not continue a tick session left at an anchor: " + (cp.stderr.strip() or cp.stdout.strip())[-200:])
    cd = LS.check_saved(read(cont), ROOT)["data"]
    tail = cd["log"][-2:]
    if ([e.get("tick") for e in tail] != [None, None] or [e["kind"] for e in tail] != ["move", "move"] or tail[0]["camera"] != "30,26,W"
            or cd["ticks"] != {"hz": ST_HZ, "count": 35, "multiplier": 63, "step": 1}):
        raise Red("the window loop's continuation is not two untimed moves beside the timed events, the tick block kept: %s" % tail)
    code, _o, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", cont])
    if code != 0:
        raise Red("the workshop does not verify the mixed session: " + err.strip())
    # a crashed tick run
    cp, p, _r = _st_run(_st_text(SIMTICK_SCRIPT), logs, "resume-crash", ["--camera", ST_CAMERA, "--plant", "crash"])
    m = re.search(r"LIVESESSION-PLANT-CRASH: .*\((.+journal\.vsj)\)", cp.stderr)
    if cp.returncode != 70 or p is not None or m is None:
        raise Red("PLANT crash: the tick run did not die after journaling")
    records, torn = _ls_journal(m.group(1))
    if not torn or len(records) != 6 or [r["kind"] for r in records[1:]] != ["look", "look", "look", "look", "move"] \
            or records[4].get("input") != {"counts": 1, "multiplier": 1, "step": 88} or records[5].get("tick") != 4:
        raise Red("the crashed tick run's journal is not a header and five timed records with a torn tail")
    cp, rec, raw = _st_run("0:W,15625:m+1,31250:ESC", logs, "resume-recovered", ["--resume", m.group(1)])
    if cp.returncode != 0 or rec is None or "a torn final journal record was dropped" not in cp.stdout:
        raise Red("the tick journal did not recover into a saved session: " + (cp.stderr.strip() or cp.stdout.strip())[-200:])
    rd = LS.check_saved(read(rec), ROOT)
    tail = rd["data"]["log"][5:]
    if (rd["data"]["log"][:5] != pd["log"][:5] or [e.get("tick") for e in tail] != [5, 6] or tail[0]["camera"] != "30,28,45056"
            or tail[1]["input"] != {"counts": 1, "multiplier": 1, "step": 88} or rd["data"]["ticks"]["count"] != 8
            or (rd["live"]["lineage"]["source"], rd["live"]["lineage"]["parent_events"], rd["live"]["lineage"]["torn"]) != ("journal", 5, 1)):
        raise Red("the recovered tick session is not the journal's five events continued at tick 5 with its last look's sensitivity: %s" % tail)
    code, _o, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", rec])
    if code != 0:
        raise Red("the workshop does not verify the recovered tick session: " + err.strip())
    return ("a tick session resumes as itself: script S's saved session continued at tick 28 with its multiplier of 64 — "
            "the twin's own continuation, head %s… — then lowered and used; left at 126 (a free heading) the window loop "
            "refuses it (LIVEINPUT-HEADING), and looked back to north the window loop continues it, two untimed moves "
            "beside the timed events, the tick block kept; a tick run that died after five journaled events recovered "
            "its four looks and a move from the journal and went on at tick 5 with its last look's sensitivity; the "
            "workshop verifies every one" % st1["head"][:12])


def simtick_fence():
    """The rule proof stays windowless and pure: shell/simtick.rs has no clock, file, static, unsafe, float or thread and
    touches no session; shell/win32.rs reads a mouse only in MOUSE-LOOK-0's own section (re-pinned on purpose with that
    rung) and still begins with LATENCY-0's instrument; the live loop's clockless entry points refuse a free heading and
    the loop binds no look; only shell/heading.rs reaches the bearing kernels; the look is folded over its token;
    the kernel's renderers and shell/present.rs are byte-for-byte what they were."""
    code_of_src = lambda t: "\n".join(ln.split("//", 1)[0] for ln in t.splitlines())
    st = code_of_src(read(os.path.join(SHELL, "simtick.rs")).decode("utf-8"))
    for tok in ("static", "unsafe", "f32", "f64", "fs::", "File", "Instant", "SystemTime", "std::time", "thread", "Mutex", "Cell<", "env::",
                "LiveSession", "crate::", "extern"):
        if tok in st:
            raise Red("shell/simtick.rs contains %r: the rules are pure integer functions of their arguments" % tok)
    if re.search(r"\bas f|\d\.\d", st):
        raise Red("shell/simtick.rs holds a float")
    for k_, v_ in (("TICK_HZ: u64", "64"), ("TICK_US: u64", "15_625"), ("YAW_MOD: i64", "360_000"), ("QUARTER: i64", "90_000"),
                   ("HALF_SECTOR: i64", "45_000"), ("STEP_COARSE: i64", "88"), ("STEP_FINE: i64", "1"), ("MULT_MIN: i64", "1"),
                   ("MULT_MAX: i64", "64"), ("COUNTS_MAX: i64", "2_147_483_647")):
        if "pub const %s = %s;" % (k_, v_) not in st:
            raise Red("shell/simtick.rs does not hold the registered constant %s = %s" % (k_, v_))
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    # re-pinned on purpose with MOUSE-LOOK-0: raw input is read in that rung's own appended section and nowhere else;
    # no section, that one included, reads the pointer's position or reaches the tick rules, the session's look or a
    # bearing kernel (mouselook-fence judges the section itself)
    outside = tail.replace(w32_section(tail, "MOUSE-LOOK-0 (appended)"), "") if "MOUSE-LOOK-0 (appended)" in tail else tail
    for tok, where in (("WM_INPUT", outside), ("RegisterRawInputDevices", outside), ("GetRawInputData", outside), ("WM_MOUSEMOVE", tail),
                       ("GetCursorPos", tail), ("SetCursorPos", tail), ("simtick", tail), ("tickrun", tail), ("heading::", tail),
                       ("push_look", tail), ("bearing", tail)):
        if tok in where:
            raise Red("shell/win32.rs contains %r: only MOUSE-LOOK-0's section reads a mouse, by raw input alone, and no window reaches the tick rules" % tok)
    li = read(os.path.join(SHELL, "liveinput.rs")).decode("utf-8")
    runf = src_span(li, "pub fn run_with<S: ExactSurface + Keys>(", "\npub fn summary(")
    # re-pinned on purpose with MOUSE-LOOK-0: a clockless entry point (no tick source) still refuses a free heading
    # before it renders; the loop names the tick run only for its counts and their summary, and still binds no look,
    # stamps no tick and reads no clock of its own
    guard = runf.find("if look.is_none() && session.free_heading() {")
    li_code = code_of_src(li)
    if (guard < 0 or not guard < runf.find("s.set_call(CALL);") < runf.find("    loop {") or "LIVEINPUT-HEADING" not in runf
            or any(t in li for t in ("push_look", "simtick::", "tickrun::apply", "tickrun::run", "Instant", "SystemTime", "qpc", "at_tick"))
            or sorted(re.findall(r"tickrun::\w+", li_code)) != ["tickrun::Run", "tickrun::summary"]):
        raise Red("the live loop does not refuse a free heading before it renders, or it binds a look, a tick or a clock")
    tr = code_of_src(read(os.path.join(SHELL, "tickrun.rs")).decode("utf-8"))
    for tok in ("Instant", "SystemTime", "std::time", "fs::", "File", "unsafe", "Surface", "present", "thread"):
        if tok in tr or re.search(r"\bstatic\s+(mut\s+)?[A-Z_]+\s*:", tr):
            raise Red("shell/tickrun.rs contains %r or a static: the tick run has no clock, file, surface, thread or state of its own" % tok)
    ap = tr[tr.index("fn apply("):tr.index("pub fn run(")]
    order = [ap.find(t) for t in ("session.at_tick(Some(cmd.tick));", "if cmd.over {", "session.push_look(d, Some((cmd.counts, sens.multiplier, sens.step)))",
                                  "for act in cmd.acts.iter() {", "crate::liveauthor::bind(simtick::rebind(vk))", "session.at_tick(None);")]
    if -1 in order or order != sorted(order) or ap.count("push_look(") != 1:
        raise Red("the tick run does not apply a command as the look once and first, then the other inputs in arrival order")
    for d_ in (SHELL, WORKSHOP):
        for fn in sorted(os.listdir(d_)):
            if not fn.endswith(".rs"):
                continue
            src = code_of_src(read(os.path.join(d_, fn)).decode("utf-8"))
            if d_ == WORKSHOP and "bearingfast" in src:
                raise Red("workshop/%s reaches the fast bearing path: the workshop verifies with the reference alone" % fn)
            if d_ == SHELL and fn != "heading.rs" and re.search(r"\bbearingfast::|\bbearing::|\bvocab::", src):
                raise Red("shell/%s reaches the bearing kernels: only shell/heading.rs does" % fn)
    if code_of_src(read(os.path.join(SHELL, "main.rs")).decode("utf-8")).count("mod bearingfast;") != 1:
        raise Red("shell/main.rs does not declare the fast bearing path exactly once")
    hd = code_of_src(read(os.path.join(SHELL, "heading.rs")).decode("utf-8"))
    ref = src_span(hd, "pub fn reference(", "\n}\n")
    # re-pinned on purpose with MOUSE-LOOK-0: the witness is a method of the session's Painter — the same tread ca,
    # entered as its prepare and render_into (what bearingfast::picture is) so the buffers and the picture are kept
    wit = src_span(hd, "pub fn witness(&mut self", "\n    }\n")
    if ("bearingfast" in ref or "sc.strips(&mut strips);" not in ref or "sc.frame(&strips, &mut frame);" not in ref
            or "crate::present::compose_frame(level_bytes, tiles_bytes, cam)" not in wit or "bearingfast::prepare(&sc, PROD)" not in wit
            or "bearingfast::render_into(&sc, PROD, &floor, &mut self.strips, &mut self.frame, &mut self.pixels)" not in wit
            or hd.count("bearingfast::render_into(") != 1 or hd.count("bearingfast::prepare(") != 1 or "bearingfast::picture(" in hd
            or "pub const PROD: bearingfast::Tread = bearingfast::Tread { blocked: false, threads: bearingfast::PROD_THREADS };" not in hd
            or any(t in hd for t in ("fs::", "File", "Instant", "SystemTime", "unsafe"))):
        raise Red("shell/heading.rs is not the facing kernel at an anchor, tread ca elsewhere, and the reference's own traversal and frame for the recomputation")
    pb = read(os.path.join(SHELL, "playback.rs")).decode("utf-8")
    sect = pb[pb.index("// ================================================================== SIM-TICK-0 (appended)"):]
    pl = src_span(sect, "pub fn push_look(", "\n    }\n")
    # re-pinned on purpose with MOUSE-LOOK-0: the look's witness is taken by the session's Painter (shell/heading.rs)
    order = [pl.find(t) for t in ("crate::simtick::turn(self.yaw, delta)", "facing: crate::simtick::cardinal(yaw)", "self.painter.witness(&self.level, &self.tiles, cam, yaw)?",
                                  "fold(&self.head, b'K', &look_fold(&token(cam, yaw), &witness))", "self.log.push(", "self.handed();")]
    if -1 in order or order != sorted(order) or 'format!("{}:{}", token, witness)' not in src_span(sect, "pub fn look_fold(", "\n}\n") \
            or any(t in sect for t in ("fs::", "File::", "Instant")):
        raise Red("the session's look is not turn, nearest cardinal, witness, fold over the token and the witness, append, hand")
    ls = read(os.path.join(SHELL, "livesession.rs")).decode("utf-8")
    fin = src_span(ls, "fn finish(p: Prepared, ended: &str, focus: &str) -> i32 {", "\n}\n")
    if not 0 <= fin.find("certify(&session)") < fin.find("write_saved(&dst, &text, &plant)") or "Err(r) => return refuse_run(r, surface)," not in fin \
            or "crate::heading::certify(batch, threads)" not in src_span(ls, "pub fn certify(", "\n}\n"):
        raise Red("the save does not recompute the free-heading frames with the reference before anything is written")
    pins = {"bearingfast.rs": BEARINGFAST_RS_SHA256, "vocab.rs": VOCAB_RS_SHA256, "mantle.rs": MANTLE_RS_SHA256, "fast.rs": FAST_RS_SHA256}
    pins.update(SIMTICK_KERNEL_PINS)
    for fn, want in pins.items():
        if sha256(read(os.path.join(KERNEL, fn)).replace(b"\r\n", b"\n")) != want:
            raise Red("kernel/%s changed: SIM-TICK-0 touches no renderer" % fn)
    src = read(os.path.join(KERNEL, "bearing.rs")).decode("utf-8")
    core = re.sub(r"\bpub ", "", src[src.index(BEARING_CORE_MARK):src.index("/// The two witnesses' material")]).rstrip() + "\n"
    if sha256(core.encode("utf-8")) != BEARING_CORE_SHA256 or sha256(read(os.path.join(SHELL, "present.rs")).replace(b"\r\n", b"\n")) != PRESENT_RS_SHA256:
        raise Red("the reference's core or shell/present.rs changed")
    if SHELL_EXE is not None:
        cp = subprocess.run([SHELL_EXE, "simtick-selftest", "--script", "15625:W,0:W"], capture_output=True, text=True, cwd=ROOT)
        if cp.returncode != 2 or "SHELL-USAGE" not in cp.stderr or "earlier than the input before it" not in cp.stderr:
            raise Red("a script whose time runs backwards was not refused before anything ran")
    return ("the rule proof stays windowless and pure: shell/simtick.rs holds the registered constants and no clock, file, "
            "static, unsafe, float or thread; the tick run applies a command as the look once and first, then the other "
            "inputs in order, with no clock or surface; shell/win32.rs reads a mouse only in MOUSE-LOOK-0's own section, by raw "
            "input alone, and still begins with LATENCY-0's instrument; the live loop's clockless entry points refuse a "
            "free heading before they render, and the loop binds no look; only shell/heading.rs "
            "reaches the bearing kernels (the facing kernel at an anchor, tread ca elsewhere, the reference's own traversal "
            "and frame to recompute) and the workshop never reaches the fast path; the look folds over its token; the save "
            "certifies before it writes; mantle.rs, fast.rs, formats.rs, hud.rs, vocab.rs, bearingfast.rs, the "
            "reference's core and shell/present.rs are what they were; a script whose time runs backwards is refused")


# ------------------------------------------------------------------ SIM-TICK-0a
# Two of the owner's rulings from MOUSE-LOOK-0's court taken into the tick command, windowless: a sensitivity change is
# a typed configuration event in the session (never folded), and a held key walks at most once a tick.
SIMTICK0_HASH = "dc1dddf255749f878802f3f73543840edf3a5d87a3c3ea816162d59ed5f8ea62"
# the owner's sequence: PgUp, mouse, Tab, mouse, PgDn
SIMTICK0A_CONFIG = [(0, 0, "PGUP"), (1, 0, "m+3"), (2, 0, "TAB"), (3, 0, "m+88"), (4, 0, "PGDN"), (5, 0, "ESC")]
SIMTICK0A_CONFIG_LOG = [
    {"kind": "sensitivity", "multiplier": 2, "step": 88, "tick": 0},
    {"kind": "look", "delta": 528, "camera": "28,28,528", "tick": 1, "input": {"counts": 3, "multiplier": 2, "step": 88}},
    {"kind": "sensitivity", "multiplier": 2, "step": 1, "tick": 2},
    {"kind": "look", "delta": 176, "camera": "28,28,704", "tick": 3, "input": {"counts": 88, "multiplier": 2, "step": 1}},
    {"kind": "sensitivity", "multiplier": 1, "step": 1, "tick": 4}]
# the same two looks with no sensitivity change: other counts, the same deltas
SIMTICK0A_PLAIN = [(1, 0, "m+6"), (3, 0, "m+2"), (5, 0, "ESC")]
# a run that dies after five journaled events, its last sensitivity changes made after its last look
SIMTICK0A_CRASH = [(0, 0, "PGUP"), (1, 0, "m+1"), (2, 0, "PGUP"), (3, 0, "TAB"), (4, 0, "W"), (5, 0, "W"), (6, 0, "ESC")]
# script R, from 28,28,N: presses with their auto-repeat marks (a trailing +). Each line says what it registers.
SIMTICK0A_HOLD = (
    [(0, 0, "RIGHT"),                                             # a fresh quarter turn: east
     (1, 0, "W"), (1, 1, "W+"),                                   # a fresh press and a repeat in one tick: both act
     (2, 0, "W+"), (2, 1, "W+"), (2, 2, "W+"),                    # three repeats in one tick: one walks, two coalesced
     (3, 0, "W+"), (4, 0, "W+"),                                  # repeats in successive ticks: one walks in each
     (5, 0, "W+"), (5, 1, "A+"),                                  # two held keys in one tick: the first walks
     (6, 0, "A+"), (6, 1, "W+")]                                  # and the other way round: the strafe walks
    + [(7, i, "W+") for i in range(6)]                            # a burst, as after a slow frame: one step
    + [(8, 0, "SPACE"), (8, 1, "SPACE+"),                         # holding Space edits once
       (9, 0, "1"), (9, 1, "1+"),                                 # holding a class key paints once
       (10, 0, "Q+"), (10, 1, "E+"),                              # Q and E are not in the held set
       (11, 0, "PGUP"), (11, 1, "PGUP+"),                         # holding PgUp raises the multiplier once
       (12, 0, "TAB+"),                                           # a repeat of Tab alone changes nothing
       (13, 0, "LEFT+"), (13, 1, "D+"),                           # a held quarter turn walks; the strafe behind it is coalesced
       (14, 0, "ESC")])
SIMTICK0A_HOLD_COUNTS = {"keys": 30, "repeats": 24, "walked": 8, "coalesced": 10, "ignored": 6, "events": 12, "moves": 10,
                         "edits": 2, "settings": 1, "refused": 0, "unbound": 0}


def _st0a_delete_event(text, k):
    """Remove saved event k's line (and keep the list's commas right), then reseal."""
    lines = text.split("\n")
    items = [i for i, ln in enumerate(lines) if ln.startswith('   {"kind": ')]
    i = items[k]
    if k == len(items) - 1:
        lines[items[k - 1]] = lines[items[k - 1]].rstrip(",")
    del lines[i]
    return _ls_reseal("\n".join(lines))


def simtick0a_preregistered():
    """SIM-TICK-0a's method is locked: an amendment to SIM-TICK-0 (whose entry is unedited) — a sensitivity change is a
    typed configuration event, never folded, the configuration replayed; a held key walks at most once a tick."""
    e = locked_entry("SIM-TICK-0a", {
        "an amendment, windowless": ("hyp", ("an amendment to sim-tick-0, whose entry stands unedited (dc1dddf2)", "no window, no clock and no win32 input")),
        "sensitivity is a typed configuration event": ("hyp", ("one event of kind sensitivity", "the configuration after it", "it is not folded",
                                                               "the head after it is the head before it", "exactly one legal transition",
                                                               "must carry the configuration in force")),
        "the physical binding": ("hyp", ("pgup is multiplier up, pgdn multiplier down, tab the step toggle", "a pure map")),
        "the tick is the coalescing boundary": ("hyp", ("a fresh press always acts and is never coalesced", "only the first repeat in a tick",
                                                        "is coalesced", "is ignored and counted", "nothing about a repeat is saved")),
        "the configuration row": ("succ", ("pgup, mouse, tab, mouse, pgdn", "a different log and the same head", "refused by both verifiers",
                                           "a change made after the last look is kept")),
        "the held-keys row": ("succ", ("three repeats in one tick", "a burst of repeats in one tick", "repeats = walked + coalesced + ignored",
                                       "saves byte-identical data")),
        "what fails it": ("fail", ("leaves no event, or one folded into the head", "a key itself, rather than its typed effect", "more than one repeat walking in a tick",
                                   "sim-tick-0's entry edited")),
        "scope": ("lims", ("rules only", "it is not in the head", "no longer loads", "never saved", "capture, focus and the cursor are shell state")),
    })
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    if reg["SIM-TICK-0"]["chain_hash"] != SIMTICK0_HASH or not entry_hash_ok("SIM-TICK-0", reg["SIM-TICK-0"]):
        raise Red("SIM-TICK-0's entry was edited: the amendment leaves it as registered")
    return ("SIM-TICK-0a's method is locked (hash %s) before the build, and SIM-TICK-0's entry is unedited (%s): a "
            "sensitivity change is one typed configuration event carrying the configuration after it, never folded, the "
            "configuration replayed by one legal transition at a time; PgUp, PgDn and Tab are the binding; a fresh press "
            "always acts and a held key's repeats walk at most once a tick" % (e["chain_hash"][:8], SIMTICK0_HASH[:8]))


def simtick0a_config():
    """The configuration is in the session's command stream and out of its head: the owner's sequence PgUp, mouse, Tab,
    mouse, PgDn saves exactly its three sensitivity events and two looks, each look carrying the configuration in
    force; the head after a sensitivity event is the head before it; the same looks under no sensitivity change save a
    different log and the same head; a sensitivity event removed, made an illegal transition, stripped of its tick, or
    a tick block that is not the final configuration is refused by both verifiers; a crashed run's journal recovers
    the configuration from its sensitivity events."""
    import livesession as LS
    _st_need()
    logs = _ls_logs("simtick0a-config")
    cache = {}
    cp, path, raw = _st_run(_st_text(SIMTICK0A_CONFIG), logs, "0a-config", ["--camera", ST_CAMERA])
    if cp.returncode != 0 or path is None:
        raise Red("the configuration script did not save: " + (cp.stderr.strip() or cp.stdout.strip())[-300:])
    st, trace, counts, _e = _st_twin(SIMTICK0A_CONFIG, _st_start(), cache)
    text = read(path).decode("utf-8")
    d = LS.check_saved(read(path), ROOT)["data"]
    strip = lambda log: [{k: v for k, v in e.items() if k != "witness"} for e in log]
    if strip(d["log"]) != SIMTICK0A_CONFIG_LOG or strip(st["log"]) != SIMTICK0A_CONFIG_LOG or raw["trace"] != trace or d["head"] != st["head"]:
        raise Red("the owner's sequence did not save its three sensitivity events and two looks as registered: %s" % strip(d["log"]))
    if (d["ticks"], d["sensitivity_changes"], d["looks"], raw["counts"]["settings"]) != ({"hz": ST_HZ, "count": 6, "multiplier": 1, "step": 1}, 3, 2, 3) \
            or any("witness" in e for e in d["log"] if e["kind"] == "sensitivity"):
        raise Red("the tick block is not the final configuration, the counts are off, or a sensitivity event carries a witness")
    # the head after a sensitivity event is the head before it (the journal holds every event's head)
    made = os.path.dirname(path)
    recs, _torn = _ls_journal(os.path.join(made, "journal.vsj"))
    heads = [_sw_genesis(d["base"]["content"], _cam_tuple(d["base"]["camera"]))] + [r["head"] for r in recs[1:]]
    for i, e in enumerate(d["log"]):
        same = heads[i + 1] == heads[i]
        if (e["kind"] == "sensitivity") != same:
            raise Red("event %d (%s): the head %s" % (i, e["kind"], "moved at a sensitivity event" if not same else "did not move at a world event"))
    cp, plain, _r = _st_run(_st_text(SIMTICK0A_PLAIN), logs, "0a-plain", ["--camera", ST_CAMERA])
    if cp.returncode != 0 or plain is None:
        raise Red("the plain script did not save: " + cp.stderr.strip()[-200:])
    pd = json.loads(read(plain).decode("utf-8"))["data"]
    world = lambda log: [(e["kind"], e.get("delta"), e.get("camera"), e["witness"]) for e in log if e["kind"] != "sensitivity"]
    if pd["head"] != d["head"] or world(pd["log"]) != world(d["log"]) or pd["log"] == d["log"] or "sensitivity_changes" in pd:
        raise Red("the same looks under no sensitivity change do not reach the same head with a different log")
    for p_ in (path, plain):
        code, _o, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", p_])
        if code != 0:
            raise Red("the workshop does not verify %s: %s" % (p_, err.strip()))
    first = lambda fn: _st_edit_event(text, 0, fn)
    cases = [
        ("a sensitivity event removed", _st0a_delete_event(text, 0)),
        ("two steps at once", first(lambda ln: ln.replace('"multiplier": 2,', '"multiplier": 3,'))),
        ("a multiplier of 65", first(lambda ln: ln.replace('"multiplier": 2,', '"multiplier": 65,'))),
        ("a multiplier of 0", _st_edit_event(text, 4, lambda ln: ln.replace('"multiplier": 1,', '"multiplier": 0,'))),
        ("a step of 87", first(lambda ln: ln.replace('"step": 88,', '"step": 87,'))),
        ("a sensitivity event with no tick", first(lambda ln: ln.replace(', "tick": 0}', '}'))),
        ("a tick block that is not the final configuration", _ls_reseal(text.replace('"count": 6, "multiplier": 1,', '"count": 6, "multiplier": 2,'))),
        # the delta still multiplies out (6 x 1 x 88 = 528) and every transition is legal: only the configuration in
        # force can refuse it
        ("a look whose inputs are not the configuration in force", _st_edit_event(text, 1, lambda ln: ln.replace('"counts": 3, "multiplier": 2, "step": 88', '"counts": 6, "multiplier": 1, "step": 88'))),
    ]
    for i, (why, body) in enumerate(cases):
        if body == text:
            raise Red("the forgery for %s changed nothing" % why)
        p = _ls_write("simtick0a-case%d" % i, body)
        cp, child, _r = _st_run("0:ESC", logs, "0a-case", ["--resume", p])
        code, _o, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", p])
        if cp.returncode != 2 or "LIVESESSION-CORRUPT: the tick form" not in cp.stderr or child is not None or code != 2 or "TICK-FORM" not in err:
            raise Red("%s was not refused by both verifiers: %s | %s" % (why, (cp.stderr.strip() or cp.stdout.strip())[-160:], err.strip()[-160:]))
    # a crashed run: the configuration comes back from the journaled sensitivity events, not from the last look
    cp, p, _r = _st_run(_st_text(SIMTICK0A_CRASH), logs, "0a-crash", ["--camera", ST_CAMERA, "--plant", "crash"])
    m = re.search(r"LIVESESSION-PLANT-CRASH: .*\((.+journal\.vsj)\)", cp.stderr)
    if cp.returncode != 70 or p is not None or m is None:
        raise Red("PLANT crash: the tick run did not die after journaling")
    recs, torn = _ls_journal(m.group(1))
    if not torn or [r["kind"] for r in recs[1:]] != ["sensitivity", "look", "sensitivity", "sensitivity", "move"] \
            or (recs[4]["multiplier"], recs[4]["step"], recs[2]["input"]) != (3, 1, {"counts": 1, "multiplier": 2, "step": 88}):
        raise Red("the crashed run's journal is not its five events, three of them sensitivity events")
    cp, rec, _r = _st_run("0:m+1,15625:ESC", logs, "0a-recovered", ["--resume", m.group(1)])
    if cp.returncode != 0 or rec is None:
        raise Red("the journal did not recover: " + (cp.stderr.strip() or cp.stdout.strip())[-200:])
    rd = LS.check_saved(read(rec), ROOT)["data"]
    if rd["log"][5].get("input") != {"counts": 1, "multiplier": 3, "step": 1} or rd["log"][5]["delta"] != 3 or rd["log"][5]["tick"] != 5 \
            or rd["ticks"] != {"hz": ST_HZ, "count": 7, "multiplier": 3, "step": 1}:
        raise Red("the recovered run did not keep the sensitivity changed after its last look: %s %s" % (rd["log"][5], rd["ticks"]))
    code, _o, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", rec])
    if code != 0:
        raise Red("the workshop does not verify the recovered session: " + err.strip())
    return ("the configuration is in the command stream and out of the head: PgUp, mouse, Tab, mouse, PgDn saved a "
            "sensitivity event (2, 88), a look carrying 2 and 88, a sensitivity event (2, 1), a look carrying 2 and 1 and "
            "a sensitivity event (1, 1), each at its tick, as the twin re-derives; the head moved at the two looks and at "
            "no sensitivity event; the same looks from other counts with no sensitivity change saved a different log and "
            "the same head %s…; the workshop verifies both; a sensitivity event removed, two steps at once, a multiplier of "
            "0 or 65, a step of 87, no tick, a tick block that is not the final configuration, and a look whose inputs "
            "multiply to its delta under another configuration are each refused by both verifiers; a run that died after a PgUp and a Tab made after its last look came back at multiplier 3, step 1, "
            "and its next look used them" % d["head"][:12])


def simtick0a_hold():
    """The tick is the coalescing boundary: script R's presses, with their auto-repeat marks, become exactly their
    registered outcomes — a fresh press always acts, the first repeat of a held key in a tick walks, later repeats in
    that tick are coalesced, a repeat of any other key is ignored; no tick walks more than one repeat; and the same walk
    with each walked repeat pressed saves byte-identical data."""
    import livesession as LS
    _st_need()
    logs = _ls_logs("simtick0a-hold")
    cache = {}
    cp, path, raw = _st_run(_st_text(SIMTICK0A_HOLD), logs, "0a-hold", ["--camera", ST_CAMERA])
    if cp.returncode != 0 or path is None:
        raise Red("script R did not save: " + (cp.stderr.strip() or cp.stdout.strip())[-300:])
    st, trace, counts, _e = _st_twin(SIMTICK0A_HOLD, _st_start(), cache)
    if raw["trace"] != trace:
        raise Red("script R's presses did not become their registered outcomes: %r" % (next((g, w) for g, w in zip(raw["trace"] + [None] * 99, trace + [None]) if g != w),))
    got = {k: raw["counts"].get(k) for k in SIMTICK0A_HOLD_COUNTS}
    if got != SIMTICK0A_HOLD_COUNTS or {k: counts[k] for k in SIMTICK0A_HOLD_COUNTS} != SIMTICK0A_HOLD_COUNTS \
            or got["repeats"] != got["walked"] + got["coalesced"] + got["ignored"]:
        raise Red("script R's counts are not the registered ones, or repeats are not walked + coalesced + ignored: %s" % got)
    per = {}
    for ln in trace:
        t = int(ln.split()[1])
        per.setdefault(t, []).append(ln)
    for t, lns in per.items():
        walked = [i for i, ln in enumerate(lns) if "+ -> event" in ln]
        if len(walked) > 1 or any("-> coalesced" in ln and (not walked or i < walked[0]) for i, ln in enumerate(lns)):
            raise Red("tick %d walked more than one repeat, or coalesced a repeat with none walked before it" % t)
    by_tick = lambda t: [ln.split(" -> ")[1] for ln in per[t]]
    checks = [
        (len(by_tick(1)) == 2 and all(o.startswith("event") for o in by_tick(1)), "a fresh press and a repeat in one tick both act"),
        ([o.split()[0] for o in by_tick(2)] == ["event", "coalesced", "coalesced"], "three repeats in one tick: one walks"),
        ([o.split()[0] for o in by_tick(5)] == ["event", "coalesced"] and "move F" in by_tick(5)[0], "two held keys in one tick: the first walks"),
        ([o.split()[0] for o in by_tick(6)] == ["event", "coalesced"] and "move Q" in by_tick(6)[0], "the first repeat walks whichever key it is"),
        ([o.split()[0] for o in by_tick(7)] == ["event"] + ["coalesced"] * 5, "a burst of repeats in one tick is one step"),
        ([o.split()[0] for o in by_tick(8)] == ["event", "repeat"] and [o.split()[0] for o in by_tick(9)] == ["event", "repeat"], "holding an edit key edits once"),
        (by_tick(10) == ["repeat", "repeat"], "Q and E do not walk on a repeat"),
        ([o.split()[0] for o in by_tick(11)] == ["event", "repeat"] and by_tick(12) == ["repeat"], "holding a sensitivity key changes it once"),
    ]
    bad = [why for ok, why in checks if not ok]
    if bad:
        raise Red("script R did not register: " + "; ".join(bad))
    d = LS.check_saved(read(path), ROOT)["data"]
    if any(k in e for e in d["log"] for k in ("repeat", "coalesced", "held")) or [e["witness"] for e in d["log"] if "witness" in e] != [e["witness"] for e in st["log"] if "witness" in e]:
        raise Red("something about a repeat was saved, or the saved witnesses are not the twin's")
    # the same walk pressed: each walked repeat a fresh press at its own time, the coalesced and ignored ones left out
    outcome = {}
    acts = [i for i in SIMTICK0A_HOLD if not (i[2][0] == "m" and i[2][1] in "+-")]
    for item, ln in zip(acts, trace):
        outcome[item] = ln.split(" -> ")[1]
    pressed = [(t, off, w.rstrip("+")) for (t, off, w) in SIMTICK0A_HOLD if not w.endswith("+") or outcome[(t, off, w)].startswith("event")]
    if len(pressed) != len(SIMTICK0A_HOLD) - SIMTICK0A_HOLD_COUNTS["coalesced"] - SIMTICK0A_HOLD_COUNTS["ignored"] or any(w.endswith("+") for _t, _o, w in pressed):
        raise Red("the pressed walk is not script R without its coalesced and ignored repeats")
    cp, p2, raw2 = _st_run(_st_text(pressed), logs, "0a-pressed", ["--camera", ST_CAMERA])
    if cp.returncode != 0 or p2 is None or raw2["counts"]["repeats"] != 0:
        raise Red("the pressed walk did not save: " + cp.stderr.strip()[-200:])
    if _st_data(p2) != _st_data(path):
        raise Red("the held walk's saved data is not the pressed walk's: holding a key changed the session")
    code, _o, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", path])
    if code != 0:
        raise Red("the workshop does not verify script R's session: " + err.strip())
    c = SIMTICK0A_HOLD_COUNTS
    return ("the tick is the coalescing boundary: script R's %d key presses, %d of them auto-repeats, became exactly their "
            "registered outcomes — %d repeats walked (never two in one tick), %d coalesced behind them, %d ignored (Space, "
            "a class key, Q, E, PgUp, Tab); a fresh press and a repeat in one tick both acted, three repeats in a tick "
            "were one step and a burst of six was one step; nothing about a repeat is in the saved session, and the same "
            "walk pressed saves byte-identical data (%d events, head %s…)"
            % (c["keys"], c["repeats"], c["walked"], c["coalesced"], c["ignored"], len(d["log"]), d["head"][:12]))


def simtick0a_fence():
    """The amendment stays inside the rules: the session's sensitivity event is one legal transition that folds nothing
    and writes no W, M or camera; every fold skips it; the tick run resolves the control keys to their typed effect
    before the editor's binding and reads the configuration from the session; the accumulator admits one held repeat a
    tick under HOLD-WALK-0's own set; the editor's bindings and the window loop do not know the control keys, and
    outside MOUSE-LOOK-0's own section (re-pinned on purpose with that rung) shell/win32.rs reads no mouse."""
    code_of_src = lambda t: "\n".join(ln.split("//", 1)[0] for ln in t.splitlines())
    pb = read(os.path.join(SHELL, "playback.rs")).decode("utf-8")
    sect = pb[pb.index("// ================================================================== SIM-TICK-0 (appended)"):]
    ps = src_span(sect, "pub fn push_sensitivity(", "\n    }\n")
    order = [ps.find(t) for t in ("crate::simtick::transition(self.sens, to)", "self.sens = to;", "self.log.push(", "head: self.head.clone()", "self.handed();")]
    if -1 in order[:3] or order[4] < order[2] or order[0] > order[1] or order[1] > order[2] \
            or any(t in ps for t in ("fold(", "self.level", "self.tiles", "self.cam =", "self.yaw =", "self.head =", "self.content =")) \
            or "tag: b'S'" not in ps or "witness: String::new()" not in ps or sect.count("self.sens = ") != 1:
        raise Red("the session's sensitivity event is not one legal transition that folds nothing and writes no W, M or camera")
    ch = src_span(pb, "pub fn chain_heads(", "\n}\n")
    if "if *tag != b'S' {" not in ch or "ev.tag == b'S' || crate::simtick::anchor(ev.yaw).is_some()" not in sect:
        raise Red("the chain's fold does not skip a sensitivity event, or the certification walk treats one as a frame")
    tr = code_of_src(read(os.path.join(SHELL, "tickrun.rs")).decode("utf-8"))
    ap = tr[tr.index("fn apply("):tr.index("pub fn run(")]
    order = [ap.find(t) for t in ("let sens = session.sensitivity();", "session.push_look(d, Some((cmd.counts, sens.multiplier, sens.step)))",
                                  "if let Some(action) = simtick::control(vk) {", "crate::liveauthor::bind(simtick::rebind(vk))")]
    cf = tr[tr.index("fn configure("):tr.index("fn apply(")]
    if -1 in order or order != sorted(order) or "session.push_sensitivity(n)" not in cf or "let now = session.sensitivity();" not in cf \
            or "Accumulator::holding(Some(crate::holdwalk::held))" not in tr or "mut sens" in tr or "Sens {" in tr:
        raise Red("the tick run keeps a sensitivity of its own, or does not resolve the control keys before the editor's binding under HOLD-WALK-0's held set")
    st = code_of_src(read(os.path.join(SHELL, "simtick.rs")).decode("utf-8"))
    fd = src_span(st, "pub fn feed(", "\n    }\n")
    order = [fd.find(t) for t in ("Input::Key(vk) => self.acts.push(Act::Key(vk)),", "let walks = self.held.map_or(false, |h| h(vk));", "Act::Ignored(vk)",
                                  "} else if self.admitted {", "Act::Coalesced(vk)", "self.admitted = true;", "Act::Walked(vk)")]
    if -1 in order or order != sorted(order) or st.count("self.admitted = true;") != 1 or "self.admitted = false;" not in src_span(st, "pub fn close(", "\n    }\n") \
            or not all(t in src_span(st, "pub fn control(", "\n}\n") for t in ("0x21 => Some(Input::MultUp)", "0x22 => Some(Input::MultDown)", "0x09 => Some(Input::StepToggle)")):
        raise Red("the accumulator does not admit exactly one held repeat a tick, or the control map is not PgUp, PgDn and Tab")
    hw = read(os.path.join(SHELL, "holdwalk.rs")).decode("utf-8")
    if "pub const HELD: [u32; 8] = [0x57, 0x41, 0x53, 0x44, VK_UP, VK_LEFT, VK_DOWN, VK_RIGHT];" not in hw:
        raise Red("HOLD-WALK-0's held set changed")
    for fn in ("liveinput.rs", "liveauthor.rs"):
        src = code_of_src(read(os.path.join(SHELL, fn)).decode("utf-8"))
        if any(t in src for t in ("0x21", "0x22", "0x09", "control(", "push_sensitivity", "Accumulator")):
            raise Red("shell/%s binds a sensitivity key or reaches the tick's accumulator: the editor's bindings and the window loop are unchanged" % fn)
    ws = code_of_src(read(os.path.join(WORKSHOP, "sessionwalk.rs")).decode("utf-8"))
    arm = src_span(ws[ws.index("fn replay("):], "Event::Sens(_, _) => {", "\n            }\n")
    sealer = read(os.path.join(ROOT, "verify", "livesession.py")).decode("utf-8")
    if "fold(" in arm or "head =" in arm or 'if tag == "S":\n            # SIM-TICK-0a' not in sealer:
        raise Red("the workshop or the sealer folds a sensitivity event")
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    # re-pinned on purpose with MOUSE-LOOK-0: its own appended section reads raw input and confines the cursor; no other
    # section does, and none reaches the tick rules or the session's configuration
    outside = tail.replace(w32_section(tail, "MOUSE-LOOK-0 (appended)"), "") if "MOUSE-LOOK-0 (appended)" in tail else tail
    if any(t in outside for t in ("WM_INPUT", "RegisterRawInputDevices", "GetRawInputData", "ClipCursor")) \
            or any(t in tail for t in ("WM_MOUSEMOVE", "SetCapture", "simtick", "tickrun", "push_sensitivity")):
        raise Red("shell/win32.rs reads a mouse or confines a cursor outside MOUSE-LOOK-0's section, or reaches the tick rules")
    pins = {"bearingfast.rs": BEARINGFAST_RS_SHA256, "vocab.rs": VOCAB_RS_SHA256, "mantle.rs": MANTLE_RS_SHA256, "fast.rs": FAST_RS_SHA256}
    pins.update(SIMTICK_KERNEL_PINS)
    for fn, want in pins.items():
        if sha256(read(os.path.join(KERNEL, fn)).replace(b"\r\n", b"\n")) != want:
            raise Red("kernel/%s changed: SIM-TICK-0a touches no renderer" % fn)
    if sha256(read(os.path.join(SHELL, "present.rs")).replace(b"\r\n", b"\n")) != PRESENT_RS_SHA256:
        raise Red("shell/present.rs changed")
    return ("the amendment stays inside the rules: the session's sensitivity event is one legal transition, carries no "
            "witness, folds nothing and writes no W, M or camera, and every fold (the shell's, the workshop's, the "
            "sealer's) skips it; the tick run keeps no sensitivity of its own, reads the session's, and resolves PgUp, PgDn "
            "and Tab to their typed effect before the editor's binding; the accumulator admits one held repeat a tick "
            "under HOLD-WALK-0's own set, a fresh press always acting; the editor's bindings and the window loop do not "
            "know the control keys; outside MOUSE-LOOK-0's own section shell/win32.rs reads no mouse and confines no cursor; "
            "no renderer source changed")


# ------------------------------------------------------------------ MOUSE-LOOK-0
# A real mouse on the locked tick rules: the live loop under a tick source. The gate runs the loop over the mock — a
# scripted mouse, keyboard and focus, and a clock that is the composition count times 13,333 us.
ML_PERIOD_US, ML_READBACK, ML_SAMPLE, ML_IDLE = 13333, 75, 64, 8
SIMTICK0A_HASH = "471f4d7253ca52139b5073e964c3f79550a872e673454033b99ddac557719450"
SIMTICK_RS_SHA256 = "3122c541d2370f7dc5fe85140dc82470680c1babbaa33205dc000675dfd28ac3"
# script L, from 28,28,N on the witness level with identity tiles: (microseconds, input). The times are not multiples of
# anything: an input's tick is the tick of the composition that drains it. Each line says what it registers.
MOUSELOOK_SCRIPT = [
    (0, "m+3"), (9000, "m+2"),                       # compositions 0 and 1 are both in tick 0: one look of 5 counts, applied at composition 2
    (30000, "W"),                                    # a step at a free heading (north is rock: blocked, still a frame event)
    (41000, "m+500"),                                # 44440: still nearest north
    (60000, "PGUP"),                                 # the multiplier, a configuration event
    (70000, "m+4"), (85000, "m-1"),                  # compositions 6 and 7 share tick 5: 3 counts at multiplier 2
    (100000, "TAB"),                                 # fine steps
    (110000, "m+17"),                                # 45002: the nearest cardinal is now east
    (125000, "W"), (126000, "W+"), (127000, "W+"),   # one composition drains a press and two repeats: two steps east, one coalesced
    (140000, "SPACE"),                               # an edit at a free heading: no frame event, the picture is rendered for the new world
    (160000, "D"),                                   # a strafe at a free heading
    (300000, "m-9"), (313000, "m-9"), (326000, "m-9"), (339000, "m-9"), (352000, "m-9"),   # a steady turn, a report at every composition
    (700000, "LEFT"),                                # a quarter turn at a free heading
    (930000, "5"),                                   # the floor repainted at a free heading: the last change before composition 75's readback
    (1100000, "m-22456"),                           # back to an anchor exactly: the composite again
    (1150000, "W"),                                  # a step on the facing kernel, in the edited world
    (1300000, "m+1"), (1900000, "m-1"),              # off the anchor and, later, back onto it: composition 150 reads back an anchor
    (2050000, "ESC")]
# the capture stretch: the window out of the foreground from 400,000 us to 650,000 us, with mouse motion and key presses
# arriving meanwhile — script L has no input of its own in that stretch
MOUSELOOK_AWAY = [(400000, "blur"), (410000, "m+700"), (450000, "W"), (470000, "SPACE"), (500000, "m-33"), (560000, "PGUP"),
                  (600000, "ESC"), (650000, "focus")]


def _ml_text(items) -> str:
    return ",".join("%d:%s" % (us, what) for us, what in items)


def _ml_schedule(items):
    """The mock's schedule, re-derived. Composition c happens at c * 13,333 us; it drains every scripted item whose time
    has come (those arriving while the window is out of the foreground are dropped); a tick that received inputs is
    closed at the first composition whose clock is in a later tick; the window closes by itself a few compositions
    after the script is spent. Returns the admitted inputs with their drain times, the composition of every close, what
    was dropped, the blurs, the out-of-foreground stretches (as the first and last tick inside them) and the last
    composition the mock allows."""
    c, nxt, fore, idle, open_tick = 0, 0, True, 0, None
    drained, closes, dropped, blurs, away, since = [], {}, 0, 0, [], None
    while True:
        now = c * ML_PERIOD_US
        tick = now // ST_TICK_US
        got = []
        while nxt < len(items) and items[nxt][0] <= now:
            what = items[nxt][1]
            if what == "blur":
                fore, blurs, since = False, blurs + 1, tick
            elif what == "focus":
                fore = True
                away.append((since, tick))
            elif not fore:
                dropped += 1
            else:
                got.append(what)
            nxt += 1
        if nxt >= len(items):
            idle += 1
        if open_tick is not None and open_tick < tick:
            closes[c] = open_tick
            open_tick = None
        if got:
            open_tick = tick
            drained += [(now, what) for what in got]
        if idle > ML_IDLE:
            return {"drained": drained, "closes": closes, "dropped": dropped, "blurs": blurs, "away": away, "closed_at": c}
        c += 1


def _ml_pixels(lvl, til, token, cache):
    """sha256 of the picture at a camera token, from the kernel executable: the composite (the frame under its overlay)
    at an anchor, the bearing REFERENCE's picture alone at a free heading."""
    key = ("px", token, hashlib.sha256(lvl).hexdigest(), hashlib.sha256(til).hexdigest())
    if key not in cache:
        x, z, h = token.split(",")
        _sw_frame(lvl, til, (int(x), int(z), 0), cache) if cache.get("lvl") != lvl or cache.get("til") != til else None
        args = ["--camera", token, "--hud"] if h in "NESW" else ["--at", token]
        code, out, err = run(KERNEL_EXE, ["--level", cache["lp"], "--tiles", cache["tp"]] + args)
        d = dict(ln.split(" ", 1) for ln in out.strip().splitlines() if " " in ln)
        if code != 0 or d.get("selfcheck") != "OK":
            raise Red("twin: the kernel's picture at %s: %s" % (token, err.strip()))
        cache[key] = d["hud"] if h in "NESW" else d["pixels"]
    return cache[key]


def _ml_twin(items, st, cache):
    """A whole look run, re-derived: the schedule gives each admitted input its drain time; the tick run's twin gives
    the events; then, composition by composition, what the loop shows — whether a command changed the state there,
    whether the heading is free (the picture) or an anchor (the composite), and the camera and world at every read-back
    composition."""
    sch = _ml_schedule(items)
    script = [(us // ST_TICK_US, us % ST_TICK_US, what) for us, what in sch["drained"]]
    st2, trace, counts, ended = _st_twin(script, st, cache)
    first = st["ticks"]
    new = st2["log"][len(st["log"]):]
    lvl, til = st["lvl"], st["til"]
    token = _st_token(st["x"], st["z"], st["yaw"])
    loop = {"compositions": 0, "picture": 0, "composite": 0, "repeated": 0, "references": 1, "read": [], "free_frames": [], "ended": "closed"}
    k = len(st["log"])
    for c in range(sch["closed_at"] + 1):
        changed = False
        if c in sch["closes"]:
            tick = first + sch["closes"][c]
            for e in [e for e in new if e["tick"] == tick]:
                changed = True
                if e["kind"] in ("move", "look"):
                    token = e["camera"]
                    if token.split(",")[2] not in "NESW":
                        loop["free_frames"].append(k)
                elif e["kind"] == "edit":
                    lvl, til = _sw_apply(lvl, til, e["spec"])
                k += 1
            if ("tick %d key ESC -> end" % tick) in trace:
                loop["ended"] = "escape"
                break
        if c == sch["closed_at"]:
            break
        free = token.split(",")[2] not in "NESW"
        loop["compositions"] += 1
        loop["picture" if free else "composite"] += 1
        if c > 0 and not changed:
            loop["repeated"] += 1
        if changed and not free:
            loop["references"] += 1
        if c % ML_READBACK == 0:
            loop["read"].append([c, token, _ml_pixels(lvl, til, token, cache)])
    loop["samples"] = len(loop["free_frames"]) // ML_SAMPLE
    return sch, script, st2, trace, counts, loop


def _ml_run(script_text, logs, name, extra=None, exe=None):
    """One shell look-selftest; returns (completed process, the saved session's path or None, the --out data or None)."""
    env = dict(os.environ, **{REFUSALLOG_ENV: logs[0], RUNLEDGER_ENV: logs[1], LIVESESSION_ENV: GATE_SESSIONS})
    out = os.path.join(BUILD, "look-%s.json" % name)
    if os.path.exists(out):
        os.remove(out)
    cp = subprocess.run([exe or SHELL_EXE, "look-selftest", "--script", script_text, "--out", out] + (extra or []),
                        capture_output=True, text=True, cwd=ROOT, env=env)
    m_ = re.search(r"saved and verified: (.+?session\.json)", cp.stdout)
    raw = None
    if os.path.exists(out):
        with open(out, encoding="utf-8") as fh:
            raw = json.load(fh)["data"]
        os.remove(out)
    return cp, (m_.group(1) if m_ else None), raw


def _ml_script_l(logs, name, items=None):
    cp, path, raw = _ml_run(_ml_text(items or MOUSELOOK_SCRIPT), logs, name, ["--camera", ST_CAMERA])
    if cp.returncode != 0 or path is None or raw is None or "look court OK" not in cp.stdout:
        raise Red("script L did not run to a saved and verified session: " + (cp.stderr.strip() or cp.stdout.strip())[-300:])
    return cp, path, raw


# the steady script: a report at every composition for 160 compositions, then Esc — more than 128 looks at free headings
MOUSELOOK_STEADY = [(i * ML_PERIOD_US, "m+1") for i in range(160)] + [(160 * ML_PERIOD_US + 20000, "ESC")]


def mouselook_preregistered():
    """MOUSE-LOOK-0's method is locked: the live editor with the mouse is a new entry on the same loop, session, journal
    and seal; an input's tick is the tick of the composition that drained it; capture is shell state and never a session
    event; the picture alone at a free heading; the readback and the reference sampled; SIM-TICK-0's and SIM-TICK-0a's
    entries unedited."""
    e = locked_entry("MOUSE-LOOK-0", {
        "the entry": ("hyp", ("shell look-window on the host and shell look-selftest on the mock", "the same loop function, session, journal and seal",
                              "live-window, liveinput-* and livesession-* stay exactly as registered and pass no tick source")),
        "the rules are not proved again": ("hyp", ("the rules are sim-tick-0's and sim-tick-0a's, unchanged", "the clock, the mouse, the capture, and the loop presenting a free heading")),
        "the clock": ("hyp", ("an input's tick is the tick of the microsecond at which the loop drained it", "its composition count times 13,333 us",
                              "applied at the first composition whose clock has passed the tick's end")),
        "the mouse": ("hyp", ("windows raw input (wm_input), relative horizontal counts", "pointer movement (wm_mousemove) is never used as counts")),
        "capture is shell state": ("hyp", ("capture is shell state, never session state", "makes no session event of any kind", "no look of zero, no pause, no synthetic input",
                                           "esc releases, then saves, then the reference recomputes")),
        "the picture": ("hyp", ("the picture alone", "the render its witness came from, rendered once, with no overlay", "at an anchor heading it presents the composite as before")),
        "the readback and the sample": ("hyp", ("at the first composition and at every 75th after it", "every 64th frame event at a free heading", "on a worker thread, off the loop",
                                                "a mismatch ends the run refused and nothing is saved", "a sample certifies nothing")),
        "the loop row": ("succ", ("stamped with the tick of the composition that drained it", "byte-identical to what shell simtick-selftest saves from the same inputs at those times",
                                  "a python model of the schedule derives")),
        "the capture row": ("succ", ("none of them reaches the session", "no event carries a tick inside the stretch", "the mouse is released before the save begins")),
        "the present row": ("succ", ("the kernel executable's pixels at that camera", "exactly the first composition and every 75th after it", "counted and logged as a differing screen")),
        "the sample row": ("succ", ("more than 128 frame events at free headings", "exactly one sample per 64", "refused liveinput-sample naming the event of the 64th free-heading frame",
                                    "writes no session file")),
        "the fence row": ("succ", ("pass no tick source and read no clock", "calls no session method and reaches no renderer", "simtick.rs, the kernels and shell/present.rs are unchanged")),
        "what fails it": ("fail", ("a focus or capture change that makes, removes or alters a session event", "mouse motion admitted while the window is not in the foreground",
                                   "a look applied more than once in a tick or before its tick ended", "an overlay drawn at a free heading",
                                   "a session saved after a sample differed, or a sample read as certification", "a latency, frame-rate or feel claim")),
        "scope": ("lims", ("the gate cannot hold a real mouse, a real clock or a real window", "no latency is claimed", "not the tick the device moved in",
                           "about 11 compositions in 75 repeat the picture before them", "only the save's recomputation is exhaustive",
                           "vertical motion, buttons and the wheel are not read")),
    })
    reg = json.load(open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8"))["entries"]
    for rung, want in (("SIM-TICK-0", SIMTICK0_HASH), ("SIM-TICK-0a", SIMTICK0A_HASH)):
        if reg[rung]["chain_hash"] != want or not entry_hash_ok(rung, reg[rung]):
            raise Red("%s's entry was edited: MOUSE-LOOK-0 leaves the rules as registered" % rung)
    return ("MOUSE-LOOK-0's method is locked (hash %s) before the build, and the rules' entries are unedited (SIM-TICK-0 "
            "%s, SIM-TICK-0a %s): look-window and look-selftest are the live editor on the same loop, session, journal and "
            "seal with a tick source switched on; an input's tick is the tick of the composition that drained it; capture "
            "is shell state and never a session event; at a free heading the loop presents the session's own picture; the "
            "screen is read back one composition in 75 and the reference recomputes one free-heading frame in 64, off the "
            "loop; no latency is claimed" % (e["chain_hash"][:8], SIMTICK0_HASH[:8], SIMTICK0A_HASH[:8]))


def mouselook_loop():
    """The window loop adds nothing to the rules: script L through shell look-selftest stamps every input with the tick
    of the composition that drained it, and saves data byte-identical to what shell simtick-selftest saves from the same
    inputs at those times; its trace and counts are the tick run's twin's; its compositions, the ones that showed the
    picture and the composite, the ones that repeated the picture before them, and its references are the ones the
    schedule's model derives; the workshop verifies the file."""
    import livesession as LS
    _st_need()
    logs = _ls_logs("mouselook-loop")
    cache = {}
    cp, path, raw = _ml_script_l(logs, "loop")
    sch, script, st2, trace, counts, loop = _ml_twin(MOUSELOOK_SCRIPT, _st_start(), cache)
    # the model's drain times, stated independently: an item scripted at T is drained by composition ceil(T / 13,333)
    if sch["drained"] != [(-(-us // ML_PERIOD_US) * ML_PERIOD_US, what) for us, what in MOUSELOOK_SCRIPT] or sch["dropped"] or sch["blurs"]:
        raise Red("the schedule's model does not drain each input at the first composition at or after its time")
    cp2, p2, raw2 = _st_run(_st_text(script), logs, "look-as-ticks", ["--camera", ST_CAMERA])
    if cp2.returncode != 0 or p2 is None or raw2 is None:
        raise Red("the same inputs at their drain times did not save through simtick-selftest: " + cp2.stderr.strip()[-200:])
    if _st_data(path) != _st_data(p2):
        raise Red("the look loop's saved data is not the windowless tick run's on the same inputs at their drain times: the window loop added something to the rules")
    tick = raw["tick"]["data"]
    if tick["trace"] != trace or raw2["trace"] != trace:
        raise Red("the look run's trace is not the twin's: %r" % (next((g, w) for g, w in zip(tick["trace"] + [None] * 99, trace + [None]) if g != w),))
    if tick["counts"] != counts or tick["ended"] != "escape" or tick["ticks"] != st2["ticks"] or tick["sensitivity"] != list(st2["sens"]):
        raise Red("the look run's counts, tick count or sensitivity are not the twin's: %s" % tick["counts"])
    d = LS.check_saved(read(path), ROOT)
    log = d["data"]["log"]
    # the two places script L puts two compositions in one tick: one look each, of the summed counts
    shared = [(e["tick"], e["input"]["counts"]) for e in log if e["kind"] == "look" and e["tick"] in (0, 5)]
    if shared != [(0, 5), (5, 3)] or log[7]["tick"] != log[8]["tick"] or [e["kind"] for e in log[7:9]] != ["move", "move"]:
        raise Red("two compositions in one tick did not make one look of the summed counts, or one composition's press and repeat did not share its tick")
    lp = raw["loop"]
    got = {k: lp[k] for k in ("compositions", "picture", "composite", "repeated", "references", "samples", "ended")}
    want = {k: loop[k] for k in got}
    if got != want:
        raise Red("the loop's compositions are not the schedule's: %s, not %s" % (got, want))
    if (lp["presented"] != lp["compositions"] or lp["byte_checks"] != lp["composite"] or lp["picture"] + lp["composite"] != lp["compositions"]
            or lp["span"] != 1 or (lp["sample_every"], lp["readback_every"], lp["period_us"]) != (ML_SAMPLE, ML_READBACK, ML_PERIOD_US)):
        raise Red("a composition was not presented, an anchor composition was not byte-checked, or the clock moved more than a tick between two compositions: %s" % lp)
    look = d["live"].get("look") or {}
    if {k: look.get(k) for k in ("compositions", "picture", "composite", "repeated", "samples", "span")} != {k: lp[k] for k in ("compositions", "picture", "composite", "repeated", "samples", "span")} \
            or look.get("rung") != "MOUSE-LOOK-0" or look.get("tick_hz") != ST_HZ:
        raise Red("the saved file's live block does not record what the loop showed: %s" % look)
    if "look" in json.loads(read(p2).decode("utf-8"))["live"]:
        raise Red("a windowless tick run's saved file claims a look loop")
    code, _o, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", path])
    if code != 0:
        raise Red("the workshop does not verify script L's session: " + err.strip())
    return ("the window loop adds nothing to the rules: script L's %d inputs, each stamped with the tick of the composition "
            "that drained it, saved data byte-identical (%d bytes, %d events, head %s…) to shell simtick-selftest on the "
            "same inputs at those times, with the twin's trace and counts; two compositions inside one tick made one look "
            "of the summed counts; of %d compositions %d presented the session's picture and %d the composite, %d repeated "
            "the picture before them, and the clock never moved more than one tick between two — all as the schedule's "
            "model derives; the counts are in the saved file's live block; the workshop verifies the file"
            % (len(MOUSELOOK_SCRIPT), len(_st_data(path)), len(log), d["data"]["head"][:12], lp["compositions"], lp["picture"],
               lp["composite"], lp["repeated"]))


def mouselook_capture():
    """Capture is shell state: script L with the window out of the foreground for a stretch — mouse motion and key
    presses (an Esc among them) arriving meanwhile — saves byte-identical data and shows the same compositions; none of
    the stretch's inputs reaches the session, no event carries a tick inside it, nothing about the focus is in the
    session's data; the mouse is released before the save begins; and the same inputs with the window in the foreground
    do change the session."""
    import livesession as LS
    _st_need()
    logs = _ls_logs("mouselook-capture")
    cp, path, raw = _ml_script_l(logs, "capture-plain")
    away = sorted(MOUSELOOK_SCRIPT + MOUSELOOK_AWAY, key=lambda i: i[0])
    inside = [i for i in MOUSELOOK_AWAY if i[1] not in ("blur", "focus")]
    lo_us, hi_us = MOUSELOOK_AWAY[0][0], MOUSELOOK_AWAY[-1][0]
    if any(lo_us <= us <= hi_us + 2 * ST_TICK_US for us, _w in MOUSELOOK_SCRIPT) or len(inside) != 6 or not any(w == "ESC" for _u, w in inside):
        raise Red("the capture stretch is not clear of script L's own inputs, or does not carry its six inputs and an Esc")
    cp2, p2, raw2 = _ml_script_l(logs, "capture-away", away)
    if _st_data(p2) != _st_data(path):
        raise Red("the window leaving the foreground changed the saved data: a focus or capture change reached the session")
    sch = _ml_schedule(away)
    a, b = (LS.check_saved(read(p_), ROOT) for p_ in (path, p2))
    if (b["live"]["focus"] != {"source": "mock", "mouse": {"blurs": 1, "dropped": len(inside), "released": True}}
            or a["live"]["focus"] != {"source": "mock", "mouse": {"blurs": 0, "dropped": 0, "released": True}}
            or (sch["blurs"], sch["dropped"]) != (1, len(inside))):
        raise Red("the stretch's inputs were not all dropped and counted, or the mouse was not released: %s" % b["live"]["focus"])
    lo, hi = sch["away"][0]
    if not lo < hi or any(lo <= e["tick"] <= hi for e in b["data"]["log"]) or b["data"]["ticks"] != a["data"]["ticks"]:
        raise Red("an event carries a tick inside the out-of-foreground stretch (ticks %d..%d)" % (lo, hi))
    text = json.dumps(b["data"])
    if any(w in text for w in ("blur", "focus", "capture", "pause", "foreground")) or raw2["loop"] != raw["loop"] or raw2["tick"]["data"]["trace"] != raw["tick"]["data"]["trace"]:
        raise Red("the session's data names the focus, or the loop did not show the same compositions with the window away")
    for cp_ in (cp, cp2):
        out = cp_.stdout
        order = [out.find(t) for t in ("[look] the mouse is released", "[livesession] certified:", "[livesession] saved and verified:")]
        if -1 in order or order != sorted(order):
            raise Red("the mouse was not released before the save began")
    # the control: the same six inputs with the window in the foreground are not inert
    cp3, p3, raw3 = _ml_run(_ml_text([i for i in away if i[1] not in ("blur", "focus")]), logs, "capture-control", ["--camera", ST_CAMERA])
    if cp3.returncode != 0 or p3 is None or _st_data(p3) == _st_data(path):
        raise Red("the stretch's inputs changed nothing even with the window in the foreground: the capture row would prove nothing")
    code, _o, err = _ls_verify(SESSIONWALK_EXE, ["verify", "--session", p2])
    if code != 0:
        raise Red("the workshop does not verify the session walked with the window away: " + err.strip())
    return ("capture is shell state: with the window out of the foreground from tick %d to tick %d and %d inputs arriving "
            "meanwhile (mouse motion, W, Space, PgUp, an Esc), script L saved byte-identical data (head %s…) and showed the "
            "same %d compositions — all %d dropped and counted in the live block, none an event, no event's tick inside the "
            "stretch, no word of the focus in the session's data; the mouse was released before the save began; the same "
            "inputs with the window in the foreground do change the session (it ends at the Esc)"
            % (lo, hi, len(inside), a["data"]["head"][:12], raw["loop"]["compositions"], len(inside)))


def mouselook_present():
    """What the loop hands to the call: at every read-back composition of script L the presented picture's sha256 is the
    kernel executable's — the bearing reference's picture alone at a free heading (in the edited world, after an edit
    that made no frame event), the composite at an anchor (LIVE-INPUT-0's own at the start); the readbacks are exactly
    the first composition and every 75th after it, all exact; a surface whose call writes nothing completes with every
    readback counted and logged as differing, and the same session saved."""
    import livesession as LS
    import refusallog as RL
    import runledger as RLG
    _st_need()
    logs = _ls_logs("mouselook-present")
    cache = {}
    cp, path, raw = _ml_script_l(logs, "present")
    sch, _script, st2, _trace, _counts, loop = _ml_twin(MOUSELOOK_SCRIPT, _st_start(), cache)
    lp = raw["loop"]
    read_ = lp["read"]
    if [r[0] for r in read_] != list(range(0, lp["compositions"], ML_READBACK)) or (lp["screen_readbacks"], lp["screen_differed"]) != (len(read_), 0):
        raise Red("the readbacks are not exactly the first composition and every %dth after it, all exact: %s" % (ML_READBACK, [r[0] for r in read_]))
    if read_ != loop["read"]:
        bad = next((g, w) for g, w in zip(read_, loop["read"]) if g != w)
        raise Red("at composition %d (camera %s) the presented picture is %s…, not the kernel executable's %s… at %s" % (bad[0][0], bad[0][1], bad[0][2][:12], bad[1][2][:12], bad[1][1]))
    kinds = ["anchor" if r[1].split(",")[2] in "NESW" else "free" for r in read_]
    edited = LS.check_saved(read(path), ROOT)["data"]
    if kinds != ["anchor", "free", "anchor"] or edited["edits"] != 2 or read_[0][1] != ST_CAMERA or read_[2][1] == ST_CAMERA:
        raise Red("script L's readbacks do not cover an anchor, a free heading in the edited world and an anchor reached again: %s" % [r[:2] for r in read_])
    # composition 75's picture follows an edit that made no frame event (the session rendered the new world for it), and
    # the edit shows there: the same camera over the world before it is a different picture
    closed_at = {t: c for c, t in sch["closes"].items()}
    k2 = [i for i, e in enumerate(st2["log"]) if e["kind"] == "edit"][1]
    after = next(e for e in st2["log"][k2 + 1:] if e["kind"] in ("move", "look"))
    st0 = _st_start()
    before_edit = _sw_apply(st0["lvl"], st0["til"], st2["log"][[i for i, e in enumerate(st2["log"]) if e["kind"] == "edit"][0]]["spec"])
    if (not closed_at[st2["log"][k2]["tick"]] <= ML_READBACK < closed_at[after["tick"]] or st2["log"][k2 - 1]["kind"] == "edit"
            or _ml_pixels(before_edit[0], before_edit[1], read_[1][1], cache) == read_[1][2]):
        raise Red("composition %d's picture does not follow a visible edit made with no frame event after it: the row would not see a stale picture" % ML_READBACK)
    # the composite at the start is the one LIVE-INPUT-0's loop presents from the same camera
    li_logs = _li_logs("mouselook-present")
    cpl, rawl = _li_run("mouselook-present", ST_CAMERA, "ESC", li_logs)
    if cpl.returncode != 0 or rawl is None or rawl["data"]["pixels"][0] != read_[0][2]:
        raise Red("the composite the look loop presents at an anchor is not the one LIVE-INPUT-0's loop presents there")
    # a surface whose call writes nothing: every readback differs, counted and logged, and the run goes on
    logs2 = _ls_logs("mouselook-present-noop")
    cpn, pn, rawn = _ml_run(_ml_text(MOUSELOOK_SCRIPT), logs2, "present-noop", ["--camera", ST_CAMERA, "--plant", "noop"])
    if cpn.returncode != 0 or pn is None or rawn is None:
        raise Red("PLANT noop: a present that writes nothing stopped the look loop; a differing screen is counted, not refused")
    ln = rawn["loop"]
    records, rbad = RL.read(logs2[0])
    runs, lbad = RLG.read(logs2[1])
    diffs = [r for r in records if (r["reason_code"], r["attribution"]) == ("LIVEINPUT-SCREEN-DIFFERS", "present.readback")]
    if ((ln["screen_readbacks"], ln["screen_differed"]) != (len(read_), len(read_)) or rbad or lbad or len(diffs) != len(read_) or len(records) != len(read_)
            or len(runs) != 1 or (runs[0]["exit_code"], runs[0]["readbacks_checked"], runs[0]["differed"]) != (0, len(read_), len(read_))
            or LS.check_saved(read(pn), ROOT)["live"]["look"]["screen_differed"] != len(read_) or _st_data(pn) != _st_data(path)):
        raise Red("PLANT noop: not every readback was counted and logged as differing, or the session saved is not the same")
    return ("what the loop hands to the call: at script L's %d read-back compositions (%s — the first and every %dth after "
            "it) the presented picture's sha256 is the kernel executable's: the composite at %s (LIVE-INPUT-0's own), the "
            "bearing reference's picture alone at %s in the edited world (%s…, no overlay), the composite again at %s; the "
            "screen read back exact each time; a surface whose call writes nothing completed with all %d readbacks counted, "
            "logged and recorded in the live block as differing, and the same session saved"
            % (len(read_), ", ".join(str(r[0]) for r in read_), ML_READBACK, read_[0][1], read_[1][1], read_[1][2][:12], read_[2][1], len(read_)))


def mouselook_sample():
    """The reference samples the run, off the loop: the steady script (a report at every composition, more than 128
    looks at free headings) takes exactly one sample per 64 free-heading frames, all equal, and saves; in every 75 of
    its compositions 11 repeat the picture before them; a shell built with the planted, self-consistent fast-path defect
    is refused LIVEINPUT-SAMPLE naming the event of the 64th free-heading frame, with the mouse released, exit 2, no
    session file, one refusal-log record."""
    import livesession as LS
    import refusallog as RL
    import runledger as RLG
    _st_need()
    logs = _ls_logs("mouselook-sample")
    cache = {}
    cp, path, raw = _ml_script_l(logs, "sample", MOUSELOOK_STEADY)
    sch, _script, st2, _trace, counts, loop = _ml_twin(MOUSELOOK_STEADY, _st_start(), cache)
    free = loop["free_frames"]
    lp = raw["loop"]
    if len(free) <= 2 * ML_SAMPLE or loop["samples"] != len(free) // ML_SAMPLE or lp["samples"] != loop["samples"] or counts["looks"] != len(free):
        raise Red("the steady script did not take exactly one sample per %d free-heading frames: %d samples over %d frames" % (ML_SAMPLE, lp["samples"], len(free)))
    d = LS.check_saved(read(path), ROOT)
    if d["live"]["look"]["samples"] != lp["samples"] or d["live"]["certified"]["frames"] != len(free) or d["data"]["head"] != st2["head"]:
        raise Red("the sampled run's save did not still recompute every free-heading frame, or its head is not the twin's")
    # 64 ticks against 75 compositions: with an input at every composition, 11 compositions in 75 close no tick
    # 64 ticks against 75 compositions: with an input at every composition, the compositions that close no tick are
    # the ones that repeat the picture — about 11 in 75 (the mock's 13,333 us period is a third of a microsecond short of
    # a 75th of a second, so the count over a stretch is 11 or 12)
    quiet = [c for c in range(76, 151) if c not in sch["closes"]]
    if len(quiet) != 11 or lp["repeated"] != loop["repeated"] or lp["repeated"] != lp["compositions"] - 1 - counts["looks"]:
        raise Red("the steady script's repeated compositions are not the ticks' beat against the compositions: %d in compositions 76..150, %d in all" % (len(quiet), lp["repeated"]))
    planted = _st_planted()
    logs2 = _ls_logs("mouselook-sample-planted")
    before = set(os.listdir(GATE_SESSIONS))
    cpp, pp, rawp = _ml_run(_ml_text(MOUSELOOK_STEADY), logs2, "sample-planted", ["--camera", ST_CAMERA], planted)
    m = re.search(r"LIVEINPUT-SAMPLE: event (\d+): the reference's frame", cpp.stderr)
    made = sorted(set(os.listdir(GATE_SESSIONS)) - before)
    if cpp.returncode != 2 or pp is not None or rawp is not None or m is None or int(m.group(1)) != free[ML_SAMPLE - 1] or "saved and verified" in cpp.stdout:
        raise Red("a shell with a defective fast path was not refused by its first sample, naming the 64th free-heading frame's event: %s"
                  % (cpp.stderr.strip() or cpp.stdout.strip())[-300:])
    if len(made) != 1 or sorted(os.listdir(os.path.join(GATE_SESSIONS, made[0]))) != ["journal.vsj"] or "[look] the mouse is released" not in cpp.stdout:
        raise Red("the refused run left something other than its journal, or did not release the mouse: %s" % made)
    records, rbad = RL.read(logs2[0])
    runs, lbad = RLG.read(logs2[1])
    hit = [r for r in records if r["reason_code"] == "LIVEINPUT-SAMPLE"]
    if (rbad or lbad or len(hit) != 1 or len(records) != 1 or hit[0]["attribution"] != "render.sample" or hit[0]["context"].get("event") != free[ML_SAMPLE - 1]
            or len(runs) != 1 or runs[0]["exit_code"] != 2):
        raise Red("the refused sample is not one refusal-log record and one ledger line ending 2")
    return ("the reference samples the run, off the loop: the steady script's %d looks at free headings took exactly %d "
            "samples (one per %d frames), all equal, and its save still recomputed all %d; with an input at every "
            "composition, 11 of compositions 76 to 150 close no tick and repeat the picture before them (%d of its %d in all); a "
            "shell whose fast path drops the wall's bottom edge was refused by its first sample (LIVEINPUT-SAMPLE, event "
            "%d, the 64th free-heading frame), released the mouse, wrote no session file, left only its journal and ended 2 "
            "with one refusal-log record"
            % (len(free), lp["samples"], ML_SAMPLE, len(free), lp["repeated"], lp["compositions"], free[ML_SAMPLE - 1]))


def mouselook_fence():
    """The tick source is fenced: LIVE-INPUT-0's clockless entry points pass none and the loop reads a clock only
    through one, in one place; only run_look gives one, only go_look calls run_look, and only look-selftest and
    look-window call go_look; the ticker applies every command through the tick run and appends nothing itself; the
    sample is one worker thread per 64th free-heading frame and the save still certifies; the mouse is released before
    the seal; the window's raw input, cursor and clock sit in their own appended section, which calls no session method
    and reaches no renderer; simtick.rs, the kernels and present.rs are unchanged; a windowless build refuses."""
    code_of_src = lambda t: "\n".join(ln.split("//", 1)[0] for ln in t.splitlines())
    li = read(os.path.join(SHELL, "liveinput.rs")).decode("utf-8")
    lic = code_of_src(li)
    body = lambda src, head: src_span(src, head, "\n}\n").split("{", 1)[1].rsplit("}", 1)[0].strip()
    if (body(li, "pub fn run<S: ExactSurface + Keys>(") != "run_with(s, session, surface, bind, None)"
            or body(li, "pub fn run_with<S: ExactSurface + Keys>(") != "run_loop(s, session, surface, binding, hold, None)"
            or body(li, "pub fn run_look<S: ExactSurface + Keys + crate::mouselook::Look>(") != "run_loop(s, session, surface, crate::liveauthor::bind, None, Some(crate::mouselook::Source::of()))"
            or lic.count("run_loop(") != 2 or lic.count("mouselook::Source::of()") != 1 or lic.count("fn run_loop<S: ExactSurface + Keys>(") != 1):
        raise Red("a clockless entry point of the live loop passes a tick source, or the tick source has a second way in")
    loopf = code_of_src(src_span(li, "fn run_loop<S: ExactSurface + Keys>(", "\npub fn summary("))
    gate_ = "if let (Some(src), Some(t)) = (look.as_ref(), ticker.as_mut()) {"
    blk = src_span(loopf, gate_, "\n        }\n")
    if (loopf.count(gate_) != 1 or loopf.count("(src.now_us)(s)") != 1 or loopf.count("(src.reports)(s)") != 1 or "(src.now_us)(s)" not in blk
            or "t.step(session, now, s.keys(), (src.reports)(s), surface)" not in blk or "t.poll().map_err(sampled)?;" not in blk
            or "let mut ticker = look.as_ref().map(|_| crate::mouselook::Ticker::new(session));" not in loopf
            or loopf.count("src.") != 2 or loopf.count("look.") != 3 or "ticks(" in loopf or any(t in li for t in ("Instant", "SystemTime", "qpc", "std::time"))):
        raise Red("the loop reads the clock or the mouse outside its one tick-source block, or holds a clock of its own")
    order = [loopf.find(t) for t in ("let free = ticker.is_some() && session.free_heading();", "let out: &[u8] = if free {", "&expected_bgr\n        } else {",
                                     "lr.render(&scene);", "if s.present(out).is_none()", "let due = c % crate::mouselook::READBACK_EVERY == 0;",
                                     "t.finish(session, surface).map_err(sampled)?;")]
    pic = code_of_src(src_span(li, "fn picture(session: &mut LiveSession, bgr: &mut [u8])", "\n}\n"))
    if (-1 in order or order != sorted(order) or "session.picture()" not in pic or "crate::present::to_blit_into(rgb, bgr);" not in pic
            or any(t in pic for t in ("overlay", "hud", "arm_composite", "lr.", "render(")) or lic.count("session.picture()") != 1
            or 'format!("LIVEINPUT-SAMPLE: ' not in li or lic.count("map_err(sampled)") != 2):
        raise Red("at a free heading the loop does not present the session's own picture, unrendered and with no overlay, or a differing sample does not refuse")
    ml = read(os.path.join(SHELL, "mouselook.rs")).decode("utf-8")
    mlc = code_of_src(ml)
    for tok in ("Instant", "SystemTime", "std::time", "fs::", "File", "unsafe", "push_look", "push_move", "push_edit", "push_sensitivity", "at_tick",
                "bearing", "present::", "LoopRenderer", "arm_composite", "compose_frame"):
        if tok in mlc or re.search(r"\bstatic\s+(mut\s+)?[A-Z_]+\s*:", mlc):
            raise Red("shell/mouselook.rs contains %r or a static: the tick source has no clock of its own, appends nothing and renders nothing" % tok)
    if (set(re.findall(r"session\.(\w+)\(", mlc)) != {"log", "free_frame_at", "sensitivity", "set_tick_count"}
            or mlc.count("tickrun::apply(session, cmd, &mut self.run, surface)") != 1 or mlc.count("tickrun::apply(") != 1
            or "Accumulator::holding(Some(crate::holdwalk::held))" not in mlc
            or mlc.count("std::thread::spawn(move || crate::heading::certify(&[frame], 1))") != 1 or mlc.count("thread::spawn(") != 1
            or "if self.free % SAMPLE_EVERY == 0 {" not in mlc
            or not all(("pub const %s;" % t) in mlc for t in ("SAMPLE_EVERY: u64 = 64", "READBACK_EVERY: u64 = 75", "MOCK_PERIOD_US: u64 = 13_333"))):
        raise Red("the ticker does not apply every command through the tick run under HOLD-WALK-0's held set, or the sample is not one reference recomputation per 64th free-heading frame on a worker thread")
    stp = src_span(mlc, "pub fn step(", "\n    }\n")
    order = [stp.find(t) for t in ("let tick = self.run.first_tick + simtick::tick_of(now_us);", "if t < tick {", "self.acc.close()", "self.apply(session, &cmd, surface, &mut step);",
                                   "for input in inputs {", "self.acc.feed(tick, input)")]
    mock = src_span(mlc, "fn pump(&mut self) -> bool {", "\n    }\n")
    if (-1 in order or order != sorted(order) or "Item::Input(_) if !self.foreground => self.dropped += 1," not in mock
            or not mock.find("Item::Input(_) if !self.foreground") < mock.find("Item::Input(Input::Mouse(c)) => self.reports.push(c),")
            or "self.now = self.pumps.saturating_sub(1) * MOCK_PERIOD_US;" not in mock):
        raise Red("a tick is not closed before the composition's inputs are fed, or the mock admits an input while out of the foreground, or its clock is not the composition count")
    ls = read(os.path.join(SHELL, "livesession.rs")).decode("utf-8")
    go = src_span(ls, "pub fn go_look<S: ExactSurface + Keys + Focus + crate::mouselook::Look>(", "\n}\n")
    order = [go.find(t) for t in ("crate::liveinput::run_look(s, &mut session, surface)", "s.release();", "let live = match result {", "s.focus()", "finish(Prepared {")]
    fin = src_span(ls, "fn finish(p: Prepared, ended: &str, focus: &str) -> i32 {", "\n}\n")
    callers = {fn: code_of_src(read(os.path.join(SHELL, fn)).decode("utf-8")) for fn in sorted(os.listdir(SHELL)) if fn.endswith(".rs")}
    if (-1 in order or order != sorted(order) or not 0 <= fin.find("certify(&session)") < fin.find("write_saved(&dst, &text, &plant)")
            or {fn: src.count("run_look(") for fn, src in callers.items() if src.count("run_look(")} != {"livesession.rs": 1}
            or {fn: src.count("go_look(") for fn, src in callers.items() if src.count("go_look(")} != {"main.rs": 1, "win32.rs": 1}
            or {fn for fn, src in callers.items() if "mouselook::" in src} != {"liveinput.rs", "livesession.rs", "main.rs", "win32.rs"}):
        raise Red("the mouse is not released before the seal, the save no longer certifies, or the tick source is reached by something other than look-selftest and look-window")
    main_src = read(os.path.join(SHELL, "main.rs")).decode("utf-8")
    sw = src_span(main_src, '"look-selftest" | "look-window" => {', '\n        "simtick-law" => {')
    if (main_src.count("go_look(") != 1 or "livesession::go_look(&mut surf, prepared)" not in sw or "mouselook::ScriptedLook::new(mock, script)" not in sw
            or "mouselook::parse_script(" not in sw or "win32::look_window(plan);" not in sw or 'plant: String::new(), surface: "gdi"' not in sw
            or code_of_src(main_src).count("mouselook::") != 2):
        raise Red("look-selftest does not run the shared code over the scripted mock, or the host window's run is planted")
    w32 = read(os.path.join(SHELL, "win32.rs"))
    if sha256(w32[:LATENCY0_WIN32_LEN]) != LATENCY0_WIN32_SHA256:
        raise Red("LATENCY-0's instrument is no longer a byte-exact prefix of shell/win32.rs")
    tail = w32[LATENCY0_WIN32_LEN:].decode("utf-8")
    sect = w32_section(tail, "MOUSE-LOOK-0 (appended)")
    sc = code_of_src(sect) + "\n"
    if not tail.rstrip().endswith(sect.rstrip()) or tail.find("LIVE-AUTHOR-0 (appended)") > tail.find("MOUSE-LOOK-0 (appended)"):
        raise Red("the MOUSE-LOOK-0 section is not appended last, after LIVE-AUTHOR-0's")
    for tok in ("LiveSession", "playback", "LoopRenderer", "render", "present::", "arm_composite", "to_blit", "compose_frame", "fs::", "File::", "write_raw(",
                "StretchDIBits", "set_call(1", "set_call(0", "GetCursorPos", "SetCursorPos", "SetCapture", "GetAsyncKeyState", "GetKeyState", "0x0101", "0x0200",
                "SystemTime", "refusallog", "push_"):
        if tok in sc:
            raise Red("the MOUSE-LOOK-0 window section contains %r: it calls no session method, reaches no renderer, writes nothing and reads no pointer position" % tok)
    pump = src_span(sc, "fn pump(&mut self) -> bool {", "\n    }\n")
    split = pump.find("} else if msg.message == WM_INPUT_LOOK {")
    keys_, mouse_ = pump[:split], pump[split:]
    order = [keys_.find(t) for t in ("let held = unsafe { GetForegroundWindow() } == self.hwnd;", "self.capture(held);", "PeekMessageW(", "if msg.message == WM_KEYDOWN_LIVE {",
                                     "if self.captured {", "self.pressed.push((msg.w_param as u32, (msg.l_param >> 30) & 1 == 1));", "self.dropped_keys += 1;")] \
        + [split + mouse_.find(t) if mouse_.find(t) >= 0 else -1 for t in (
            "GetRawInputData(msg.l_param as *mut c_void, RID_INPUT_LOOK,", "raw.header.kind == RIM_TYPEMOUSE_LOOK",
            "if raw.mouse.flags & MOUSE_MOVE_ABSOLUTE_LOOK != 0 {", "} else if raw.mouse.last_x != 0 {", "if self.captured {",
            "self.counts.push(raw.mouse.last_x as i64);", "self.dropped += 1;")]
    cap = src_span(sc, "fn capture(&mut self, want: bool) {", "\n    }\n")
    win = src_span(sc, "pub fn look_window(", "\n}\n")
    order_w = [win.find(t) for t in ("SetProcessDPIAware()", "crate::livesession::prepare(plan)", "= show_window(", "SetForegroundWindow(hwnd)",
                                     "RawInputDevice { usage_page: HID_PAGE_GENERIC_LOOK, usage: HID_USAGE_MOUSE_LOOK, flags: 0, target: hwnd }",
                                     "RegisterRawInputDevices(&device, 1,", "crate::livesession::go_look(&mut look, prepared)", "DestroyWindow(hwnd)")]
    if (split < 0 or -1 in order or order != sorted(order) or -1 in order_w or order_w != sorted(order_w)
            or pump.count("if self.captured {") != 2 or sc.count(".counts.push(") != 1 or sc.count(".pressed.push(") != 1 or sc.count("last_y") != 1 or sc.count("buttons") != 2
            or not all(t in cap for t in ("ClipCursor(&r);", "ShowCursor(0);", "ClipCursor(std::ptr::null());", "ShowCursor(1);"))
            or sc.count("qpc()") != 1 or "qpc()" not in src_span(sc, "fn now_us(&mut self) -> u64 {", "\n    }\n")
            or "self.capture(false);" not in src_span(sc, "fn release(&mut self) {", "\n    }\n")
            or not all(t in sc for t in ("const WM_INPUT_LOOK: Uint = 0x00FF;", "const RID_INPUT_LOOK: Uint = 0x1000_0003;", "const RIM_TYPEMOUSE_LOOK: Dword = 0;",
                                         "const MOUSE_MOVE_ABSOLUTE_LOOK: u16 = 0x0001;", "const HID_PAGE_GENERIC_LOOK: u16 = 0x01;", "const HID_USAGE_MOUSE_LOOK: u16 = 0x02;"))
            or "call: 1," not in sc or re.search(r"\bsession\.\w+\(", sc)):
        raise Red("the MOUSE-LOOK-0 window does not capture by the foreground, admit only captured keys and relative horizontal raw counts, "
                  "read its clock in one place, or load before it opens")
    pins = {"bearingfast.rs": BEARINGFAST_RS_SHA256, "vocab.rs": VOCAB_RS_SHA256, "mantle.rs": MANTLE_RS_SHA256, "fast.rs": FAST_RS_SHA256}
    pins.update(SIMTICK_KERNEL_PINS)
    for fn, want in pins.items():
        if sha256(read(os.path.join(KERNEL, fn)).replace(b"\r\n", b"\n")) != want:
            raise Red("kernel/%s changed: MOUSE-LOOK-0 touches no renderer" % fn)
    src = read(os.path.join(KERNEL, "bearing.rs")).decode("utf-8")
    core = re.sub(r"\bpub ", "", src[src.index(BEARING_CORE_MARK):src.index("/// The two witnesses' material")]).rstrip() + "\n"
    if (sha256(core.encode("utf-8")) != BEARING_CORE_SHA256 or sha256(read(os.path.join(SHELL, "present.rs")).replace(b"\r\n", b"\n")) != PRESENT_RS_SHA256
            or sha256(read(os.path.join(SHELL, "simtick.rs")).replace(b"\r\n", b"\n")) != SIMTICK_RS_SHA256):
        raise Red("the reference's core, shell/present.rs or shell/simtick.rs changed: MOUSE-LOOK-0 changes no rule and no renderer")
    sealer = read(os.path.join(ROOT, "verify", "livesession.py")).decode("utf-8")
    if 'mouse = live.get("look")' not in sealer or 'prov["look"] = {"rung": "MOUSE-LOOK-0", "chain_hash": reg["MOUSE-LOOK-0"]["chain_hash"]}' not in sealer:
        raise Red("the sealer does not cite MOUSE-LOOK-0 for a session whose live block carries the look loop's counts")
    if SHELL_EXE is not None:
        cp = subprocess.run([SHELL_EXE, "look-window"], capture_output=True, text=True, cwd=ROOT)
        if cp.returncode == 0 or "SHELL-NO-WINDOW" not in cp.stderr:
            raise Red("a windowless build did not refuse look-window with SHELL-NO-WINDOW")
        for bad, why in (("0:mult+,15625:ESC", "a window receives keys and a mouse"), ("15625:m+1,0:ESC", "earlier than the input before it"),
                         ("0:blur,05:focus", "is not whole microseconds")):
            cp = subprocess.run([SHELL_EXE, "look-selftest", "--script", bad], capture_output=True, text=True, cwd=ROOT)
            if cp.returncode != 2 or "SHELL-USAGE" not in cp.stderr or why not in cp.stderr:
                raise Red("the look script %r was not refused before anything ran" % bad)
    return ("the tick source is fenced: LIVE-INPUT-0's run and run_with pass none, and the loop reads the clock and the "
            "mouse only through one, in one block; only run_look gives one, only go_look calls it, and only look-selftest "
            "and look-window call go_look; the ticker closes a tick before it feeds the composition's inputs, applies every "
            "command through the tick run and appends nothing itself; at a free heading the loop presents the session's own "
            "picture, unrendered and with no overlay; the sample is one reference recomputation per 64th free-heading frame "
            "on a worker thread and the save still certifies every one; the mouse is released before the seal; the window's "
            "raw input (relative, horizontal, captured only), cursor and clock sit in the last appended section of "
            "shell/win32.rs, which calls no session method, reaches no renderer and writes nothing; simtick.rs, the kernels "
            "and present.rs are what they were; a windowless build refuses look-window")


# ------------------------------------------------------------------ main
def main() -> int:
    print("VERÐANDI GATE")
    # REFUSAL-LOG-0: every shell the gate runs logs its refusals to the gate's own scratch file, never the owner's log
    os.makedirs(BUILD, exist_ok=True)
    os.environ[REFUSALLOG_ENV] = GATE_REFUSAL_LOG
    if os.path.exists(GATE_REFUSAL_LOG):
        os.remove(GATE_REFUSAL_LOG)
    # RUN-LEDGER-0: and its runs to the gate's own scratch ledger
    os.environ[RUNLEDGER_ENV] = GATE_RUN_LEDGER
    if os.path.exists(GATE_RUN_LEDGER):
        os.remove(GATE_RUN_LEDGER)
    # LIVE-SESSION-0: and every session it saves into its own scratch root, never the owner's build/sessions
    os.environ[LIVESESSION_ENV] = GATE_SESSIONS
    if os.path.isdir(GATE_SESSIONS):
        shutil.rmtree(GATE_SESSIONS)
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
    row("refusalwhy-preregistered", refusalwhy_preregistered)
    row("refusalwhy-fence", refusalwhy_fence)
    row("hoststate1-preregistered", hoststate1_preregistered)
    row("hoststate1-record", hoststate1_record)
    row("refusallog-preregistered", refusallog_preregistered)
    row("refusallog-bijection", refusallog_bijection)
    row("refusallog-fence", refusallog_fence)
    row("refusallog-reader", refusallog_reader)
    row("runledger-preregistered", runledger_preregistered)
    row("runledger-bijection", runledger_bijection)
    row("runledger-fence", runledger_fence)
    row("runledger-reader", runledger_reader)
    row("refusalwhy1-preregistered", refusalwhy1_preregistered)
    row("refusalwhy1-log", refusalwhy1_log)
    row("refusalwhy1-fence", refusalwhy1_fence)
    row("drift-preregistered", drift_preregistered)
    row("drift-sealer", drift_sealer)
    row("drift-report", drift_report)
    row("drift-fence", drift_fence)
    row("liveloop-preregistered", liveloop_preregistered)
    row("liveloop-court", liveloop_court)
    row("liveloop-sealer", liveloop_sealer)
    row("liveloop-fence", liveloop_fence)
    row("liveinput-preregistered", liveinput_preregistered)
    row("liveinput-binding", liveinput_binding)
    row("liveinput-continuity", liveinput_continuity)
    row("liveinput-court", liveinput_court)
    row("liveinput-fence", liveinput_fence)
    row("livesession-preregistered", livesession_preregistered)
    row("livesession-save", livesession_save)
    row("livesession-resume", livesession_resume)
    row("livesession-recover", livesession_recover)
    row("livesession-classify", livesession_classify)
    row("livesession-sealer", livesession_sealer)
    row("livesession-fence", livesession_fence)
    row("liveauthor-preregistered", liveauthor_preregistered)
    row("liveauthor-binding", liveauthor_binding)
    row("liveauthor-authority", liveauthor_authority)
    row("liveauthor-persist", liveauthor_persist)
    row("liveauthor-fence", liveauthor_fence)
    row("holdwalk-preregistered", holdwalk_preregistered)
    row("holdwalk-binding", holdwalk_binding)
    row("holdwalk-coalesce", holdwalk_coalesce)
    row("holdwalk-equivalence", holdwalk_equivalence)
    row("holdwalk-fence", holdwalk_fence)
    row("bearing0-preregistered", bearing_preregistered)
    row("oracle2-frozen", oracle2_frozen)
    row("oracle2-identity", oracle2_identity)
    row("bearing-vocab", bearing_vocab)
    row("bearing-oracle", bearing_oracle)
    row("bearing-anchors", bearing_anchors)
    row("bearing-selftest", bearing_selftest)
    row("bearing-refuse", bearing_refuse)
    row("bearing-fence", bearing_fence)
    row("bearingfast-preregistered", bearingfast_preregistered)
    row("bearingfast-court", bearingfast_court)
    row("bearingfast-threads", bearingfast_threads)
    row("bearingfast-checked", bearingfast_checked)
    row("bearingfast-bounds", bearingfast_bounds)
    row("bearingfast-fence", bearingfast_fence)
    row("simtick-preregistered", simtick_preregistered)
    row("simtick-law", simtick_law)
    row("simtick-script", simtick_script)
    row("simtick-replay", simtick_replay)
    row("simtick-equivalence", simtick_equivalence)
    row("simtick-certify", simtick_certify)
    row("simtick-resume", simtick_resume)
    row("simtick-fence", simtick_fence)
    row("simtick0a-preregistered", simtick0a_preregistered)
    row("simtick0a-config", simtick0a_config)
    row("simtick0a-hold", simtick0a_hold)
    row("simtick0a-fence", simtick0a_fence)
    row("mouselook-preregistered", mouselook_preregistered)
    row("mouselook-loop", mouselook_loop)
    row("mouselook-capture", mouselook_capture)
    row("mouselook-present", mouselook_present)
    row("mouselook-sample", mouselook_sample)
    row("mouselook-fence", mouselook_fence)
    fails = sum(1 for st, _, _ in ROWS if st == "FAIL")
    skips = sum(1 for st, _, _ in ROWS if st == "SKIP")
    rowset = sha256("\n".join(name for _, name, _ in ROWS).encode("utf-8"))[:16]
    print("GATE FAILED" if fails else "GATE PASSED")
    print(f"RECONCILE  rowset {rowset}  {len(ROWS)} rows / {fails} fail / {skips} skipped")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
