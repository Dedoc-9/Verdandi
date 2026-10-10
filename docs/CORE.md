# Core — what the repository is made of, and how it actually runs

This is the implementation map: the modules, how they are built, how data moves, who may write what, and what the
evidence supports. It describes the checkout as it stands (HEAD `4247a61`, tree `6d0147ee`, 2026-10-09), read from
the source. The *why* of the program is [`PROGRAM.md`](PROGRAM.md). The formats are [`BINARY-SDK.md`](BINARY-SDK.md).
The graybox's boundaries are [`BOUNDARIES.md`](BOUNDARIES.md). What was checked, and how, is
[`REPOSITORY-TRUTH.md`](REPOSITORY-TRUTH.md).

## 1. The shape

Two times are kept apart, and a third runtime stands beside them.

```text
  PROGRAM TIME   verify/verify.py, 251 rows, holds kernel/ shell/ workshop/ and the sealers; oracle/ is its evidence
  CONTENT TIME   design/ (a client) ──► shell design-compile ──► shell design (admit) ──► a sealed session
                 no gate runs; the shell's compiler and admission, which the gate holds, do the work
  BESIDE         graybox/: a browser runtime on the canonical level; its own checks; no row reads it
                 art/: an art file over the graybox's W and C ──► one engine scene ──► Unreal 5.8; its own checks
```

| folder | language | source lines | job | held by |
|---|---|---|---|---|
| `oracle/` | data; Python (`oracle/game`) | — | frozen evidence from Urðr at two tags | `oracle-frozen`, `oracle2-*`, `game-*` |
| `kernel/` | Rust, std-only | 4,655 | the deterministic render: a scene in, an index frame and a picture out | `kernel-*`, `gauntlet*`, `locality0-*`, `bearing*`, `hud-*` |
| `workshop/` | Rust | 3,123 | authority transitions (edit, session, walk, session-walk) and their verifier | `workshop-*`, `text-*`, `input-*`, `sessionwalk-*`, `membrane-*` |
| `shell/` | Rust | 12,641 | presentation, playback, the live loop and its durable session, the tick rules, admission, the batch, the design compiler | `shell-*` and every live, admission and compiler rung |
| `verify/` | Python | 22,643 (`verify.py` 17,025) | the gate, the envelope, the saved-form reader, the registers, the sealers | is the gate |
| `design/` | Python | 1,084 | the design tool, a client of the shell | its own 17 checks; no row |
| `graybox/` | Python, JS, HTML | 2,530 | the FPS slice: converter, map checks, server, simulation, two renderers | its own checks; no row |
| `art/` | Python | 1,531 | prompted art: the art file's reader and exporter to one engine scene, its checks, the Unreal 5.8 importer | `art/check.py`; no row |

Line counts are of tracked `.rs`, `.py`, `.js` and `.html` files.

## 2. How each program is built

The gate builds every binary with `rustc -O <file> -o verify/build/<name>` (`verify/verify.py:534-565`, `FLAGS =
["-O"]`). There is no Cargo, no `--extern` and no edition flag, so the default edition applies (2015). No rustc
version is pinned. A row that plants a defect copies the sources to a scratch `.gate-<name>/` at the root, so that the
`#[path]` includes resolve, and removes it afterwards. Without `rustc` a row is **skipped**, not failed.

| binary | source | flags | note |
|---|---|---|---|
| `kernel` | `kernel/main.rs` | `-O`; `-C overflow-checks=on` for `bearingfast-checked` | portable |
| `edit`, `text`, `session`, `input`, `sessionwalk`, `membrane` | `workshop/*.rs` | `-O`; `membrane-wall` requires `--cfg membrane_probe_illegal` to **fail** with E0502 | portable |
| `shell` (headless) | `shell/main.rs` | `-O` | portable; `win32.rs` is never compiled by the gate |
| `shell.exe` (window) | `shell/main.rs` | `-O --cfg shell_window`, on Windows | built by hand or by a sealer (`verify/diagcommon.py`); the gate rebuilds `verify/build/shell` without the window |
| off-gate kernels | `kernel/main.rs` | `-C opt-level=3` (`verify/bench.py`, `verify/gauntlet*.py`) | speed courts only |

The design tool finds a shell at `verify/build/shell`, then `build/shell`, and otherwise builds one with `rustc -O`
(`design/design.py:104-120`). The graybox needs no build: Python's standard library and a WebGL 1 browser.

## 3. How data moves

**A frame.** Level (W) + camera (C) + tiles (M) are composed into a scene (`kernel/formats.rs:compose`), then strips,
then the index frame (its digest `URDRFB1`), then the picture (its sha256). The kernel holds no state and reads no
clock (`kernel/mantle.rs:34`). The facing camera has the reference (`mantle.rs`) and a staircase of fast siblings
(`fast.rs`, the locked path at 8 threads). The heading camera has the reference (`bearing.rs`) and its fast treads
(`bearingfast.rs`). Every fast path is held byte for byte to its reference.

**An edit (workshop).** `edit record` takes the old authority, validates the edit, writes the new authority beside
the old (it never mutates a file), renders through the kernel and records three witnesses and the difference as a
signed envelope. `edit check` recomputes all of it from the files.

**A live session (shell).**

```text
  key / mouse ──► binding (shell) ──► typed event ──► LiveSession (private fields) ──► fold: witness, head
                                                           │
                                       journal.vsj ◄───────┤ each record flushed before it counts
                                                           │
            render (LoopRenderer or tread ca) ──► SetDIBitsToDevice ──► screen; 1 composition in 75 read back
                                                           │
   Esc ──► every free-heading frame recomputed by the reference ──► session.json written, moved, read back, replayed
```

- **Input timing.** Input is stamped on a 64 Hz tick (15,625 µs, `shell/simtick.rs`). The tick says when; it is never
  folded.
- **The independent check.** The workshop's `sessionwalk verify`, which shares no renderer code with the shell, is
  run by the gate's rows and by `verify/livesession.py` before a session is sealed as a record. The shell does not
  run it when it saves.
- **What is stored.** A session stores the paths and hashes of its base, not the base's bytes.

**An admission.**

- **`shell admit`:** reads one VRDNP1 proposal, checks it in the registered order, and appends one ordinary edit with
  an envelope. It seals a **new** session. The parent is never modified.
- **`shell design`:** does the same for a VRDNP2 batch. N ordinary edits go under one admission. `--dry-run` stops
  before anything is written, and `--previewed DIGEST,HEAD` binds the admission to that preview.
- **What the envelope keeps:** it is checked against the chain but not folded into the head. The proposal's bytes are
  not kept in the session (GHOSTS G20).

**A design.**

```text
  design text ──► shell design-compile ──► one canonical VRDNP2 batch (stdout) ──► shell design --dry-run (preview)
                                                                                 ──► shell design --previewed (admit)
```

`design/design.py` is the client:

- **It computes nothing.** It holds no authority and computes no change set (`design/design.py:6-8`).
- **What it keeps.** The project's files: `project.json`, the pending design and batch, and copies under `designs/`
  and `batches/`.
- **What it shows.** Its top view (`inspect`) re-applies the session's edits in Python. That is a view, not the
  kernel's picture.

**The graybox.**

```text
  tactical.design ──(design tool)──► tactical.layout ─┐
  oracle/levels/witness.lvl (sha256 pinned) ──────────┤
  maps/*.gbx (height, cover, spawns, targets, …) ─────┴──► level.py ──► W canonical ──► C collision (tops only)
                                                                         │                  │
                                         render.js / render_flat.js ◄────┘                  └──► sim.js (moves against C)
```

Each stage, its input and output, and what it keeps:

| stage | in → out | keeps | loses |
|---|---|---|---|
| layout | an admitted session, read back through `design.py inspect --json` → a grid with the design's sha256 and the heads | the heads as header lines | tiles and colours, the camera, the depth table |
| pinned level | `level <path> <sha256>`, the hash checked against the file | the sha256 | the same |
| D → W | the overlay adds heights, cover and marks on floor cells only (a probe may name rock) | every cell's source lines; the manifest's converter hash | stairs become floor at height 0 |
| W → C | the tops alone | `collision_sha256` | everything but the tops |
| simulate | C plus the standing targets; tick 1/120 s; JS doubles | a state hash per tick (FNV-1a over 64-bit floats) | — |
| render | W and the state, read only | — | — |

`check.py` holds W and C to the source with its own reader. The page's self-test holds the movement, the routes, the
replay and the renderers (§6). The manifests' hashes are not pinned anywhere in the tree.

**The art (ART-GENERATION-0).** `art/dress.py` reads an art file (`VERDANDI-ART 0`) and the graybox map it names
through `graybox/level.py`, and writes one scene: C's tops as boxes merged inside 8 × 8 chunks, the look's dressing
and lights, the spawns and critique views, and a lineage binding the art file, the layout's heads, W, C, the
exporter and the scene by sha256. Every dressing choice is a hash of its statement and cell. `art/check.py` holds the
scene to C and to the player with its own arithmetic (`art/README.md`). `art/unreal/verdandi_import.py` runs inside
the Unreal editor and keeps every actor whose item did not change.

| stage | in → out | keeps | loses |
|---|---|---|---|
| dress | W, C and the art file → the scene | C exactly (as play geometry); the lineage | nothing of C; the art's statements become items keyed by statement hash and cell |
| import | the scene → the open Unreal level | each actor's scene id and item hash, as tags | determinism: the engine's pixels are not hashed or claimed |

## 4. Authority and its walls

| role | who | how it is held |
|---|---|---|
| frozen evidence | `oracle/` | `oracle-frozen`, `game-frozen`, `game-not-runtime` |
| pure computation | `kernel/` | structure (its `#[path]` includes reach only kernel files and the oracle's octant) and byte identity; no row forbids an include |
| defines transitions, verifies sessions | `workshop/` | `sessionwalk-*` and the rows that call it |
| holds the live authority, writes saved and admitted sessions | `shell` (`LiveSession`, changed only by `push` and replay) | module privacy; `livesession-*`, `admit-*`, `designevent-*` |
| observes or presents only | `shell/present.rs`, `win32.rs`, playback, the readback, the logs | `shell-blit-*`, `shell-playback-no-authority`, the fences |
| client | `design/design.py` | `design/test_design.py` (17 checks, off the gate) |
| judge | `verify/verify.py` | writes only `verify/build/` and its scratch |
| a separate runtime | `graybox/` (`sim.js` writes the game state; the renderers read it) | its self-test and `check.py`; no row |
| the art | `art/` (writes a scene from W and C; never writes W or C) | `art/check.py`; the importer's in-engine self-check; no row |

The walls, with their real reach:

- **The typestate wall (MEMBRANE-0)** is a demonstration in `workshop/membrane.rs`. No other file uses its
  `Authority` and `Reading` types. The shell keeps its authority with private fields, not with that typestate.
- **The platform wall.** `win32.rs` is included only under `cfg(all(target_os = "windows", shell_window))`. The gate
  reads its text through fences, including LATENCY-0's byte-exact prefix, and never compiles it.
- **Program time against content time.** The gate never runs `design/`, `graybox/` or `art/`. The design tool never runs the
  gate. `designir-fence` and `hermeneutics-fence` check by syntax tree that nothing under `verify/` reads `design/`.

## 5. Restrictions, as the code enforces them

| restriction | where it holds | how |
|---|---|---|
| std-only Rust, no crates | everything the gate builds | structural: bare `rustc`, no Cargo; the pins make any new dependency an amendment. No row greps for crates |
| no `unsafe` | the files with a fence: `bearing.rs`, `vocab.rs`, `bearingfast.rs`, `simtick.rs`, `tickrun.rs`, `heading.rs`, `mouselook.rs`, `savedform.rs`, `admit.rs`, `designevent.rs`, `designcompile.rs` | token fences, file by file |
| `unsafe` that exists | `kernel/fast.rs` (the threaded framebuffer, GHOSTS G1), `shell/livesession.rs` (`MoveFileExW`), `shell/win32.rs` (the window, off the gate) | no `#![forbid(unsafe_code)]` anywhere |
| no float | `shell/simtick.rs` (the `simtick-fence` row) | a token scan. Elsewhere in the kernel and workshop float-freedom is held only by byte identity and the pins; `f64` appears in off-gate timing percentiles |
| Python standard library only | `oracle/game` (`GAME_STDLIB`) | a row. `verify/`, `design/` and `graybox/` follow it by practice; `verify/hoststate.py` uses `ctypes` |
| every Rust source and sealer pinned | 58 files (`RSN_SOURCES`) | `reasoncourt-fence`, `mintwatch-fence`; a change needs a registered amendment and a chain link |

## 6. Determinism and reproducibility: what the evidence supports

| property | evidence | scope |
|---|---|---|
| the kernel reproduces Urðr's digests | `kernel-oracle`, `kernel-corpus` (12 witnesses: 6 scenes × 2 tile sets), `bearing-oracle` (104) | the registered scenes |
| fast paths equal their references | `gauntlet2-threaded-equiv` (T = 1, 2, 4, 8, 16), `bearingfast-court`, `bearingfast-threads`, `bearingfast-checked` | the corpus and registered cameras; those thread counts |
| replay, checkpoint and batching reach one head | `workshop1-replay`, `sessionwalk-batch-invariance`, `shell-playback-checkpoint`, `simtick-equivalence`, `designevent-admit` | the gate's scripts, one build |
| Rust and Python agree | `records-twins`, `readercourt-agree`, `designir-compile`, the Python fold twins | one author wrote both sides (G23) |
| the gate's output twice the same | FULL×2: the compact stdout of two runs on one tree compared byte for byte, here and on the host | the printed lines only; tree identity is taken by an instrument outside the repository |
| container and host print the same gate | 247 and 251 rows, compared as text | on trees that differ by the host's 40 committed records |
| host sessions replay in the container | sessions `aa850e78…`, `5290c848…`, `b28e42be…` (`verify/RUNGS.md`) | those sessions |
| saved session bytes | **not reproducible**: each file embeds a `run_id` from the clock and the process id | heads are |
| graybox replay | the self-test replays a recorded route twice in one page, every tick hashed | one build, one page. The same final hash was seen in Chromium, node and the host's Firefox once; **not claimed** across browsers |
| cross-platform determinism in general | — | **not established** |

## 7. Timing instruments, and what each measures

| instrument | interval | clock | where |
|---|---|---|---|
| `kernel --bench` and the other `--*-bench` flags | per frame or per phase, after the witnesses are checked | `std::time::Instant` | `kernel/main.rs` |
| LATENCY-0 / 1 | frame-ready (blit returned) → composited (the next `DwmFlush` returned); frames pre-rendered | QPC | `shell/win32.rs` |
| LATENCY-1R | render-start → frame-ready → composited | QPC on the host; a mock surface in the gate | `shell/latency1r.rs` |
| FRAME-SPLIT-0 | seven contiguous render phases | the same | `shell/framesplit.rs`, `shell/present.rs` |
| PRESENT-SCALE / STRETCH / ALLOC-REUSE / EXACT, DRIFT-0 | the same envelope with one variable changed; the screen read back as a hard gate | the same | `shell/present*.rs`, `shell/allocreuse*.rs` |
| run ledger | a run's wall time | `SystemTime` | `shell/runledger.rs` |
| graybox HUD: frame | between animation frames | rAF / `performance.now` | `graybox/web/main.js` |
| graybox HUD: sim, draw submit | the ticks of a frame; the `draw` call only (the GPU is not awaited) | `performance.now` | the same |
| graybox HUD: input → tick | an event's timestamp to the first tick that consumes it | event time against `performance.now` | the same |
| graybox bench | the mean of K draws, each followed by a one-pixel readback | `performance.now`; its step printed | `main.js`, `serve.py` |

No gate row reads a clock. G30 records the one row that once did, which has been corrected. No instrument here
measures input to photon, and no document claims it. LATENCY-0's split between software and hardware stops a slow
display from laundering a software number into a refresh claim (`verify/RUNGS.md`, LATENCY-0).

## 8. The gate

- **Rows.** Each row is a `row("name", fn)` call in `main()` (`verify/verify.py:16752-17015`); there are 251 today.
  - A row that returns passes.
  - `Skip` (no rustc) is reported, not failed.
  - `Red`, or **any** other exception, fails: a crash is a red row, never a missing one.
- **The verdict** (`verify.py:17016-17021`). The gate prints `GATE FAILED` if any row failed and `GATE PASSED`
  otherwise, **whatever the number skipped**. The last line is `RECONCILE rowset <sha256 of the names>[:16] N rows /
  F fail / S skipped`, and today's rowset is `74db4c8d78625af5`. The exit code is 1 or 0.
- **The watches.** `subprocess.run` is wrapped so that every non-zero ending is kept by its code head. A
  `sys.monitoring` tap hears raises (MINT-WATCH).
- **Scratch.** The gate writes only `verify/build/` and its scratch folders.
- **What FULL×2 is.** Two runs on one tree whose compact outputs are byte-identical, with the tree read before and
  after by the witness outside the repository.
- **What FULL×2 does not show:**
  - that the checkout was clean (G36);
  - independence from the clock or the folder path (G30, G31);
  - agreement of the row texts the compact output omits;
  - that no row was skipped.
- **When it runs.** By the owner's ruling of 2026-10-09 the full gate runs at release checkpoints, or when a change
  threatens the certified contract. Other work runs its own checks. No release checkpoint is yet defined anywhere.

## 9. What stands

Status key: **G** in the gate · **G-mock** in the gate over a mock, host numbers off it · **O** built outside the gate ·
**D** declared only.

| capability | location | evidence | status | known limit |
|---|---|---|---|---|
| certified facing render | `kernel/mantle.rs` | `kernel-oracle`, `-corpus`, `-selftest` | G | one corpus (G5) |
| fast render, 8 threads | `kernel/fast.rs` | `gauntlet*`, `locality0-*`; host records | G (bytes); speed O | threads per frame (G3); aliasing not Miri-checked (G1) |
| heading camera, reference and fast | `kernel/bearing.rs`, `bearingfast.rs` | `bearing-*`, `bearingfast-*` | G | heading only, no pitch |
| HUD | `kernel/hud.rs` | `hud-*`, `verify/pins/hud-1.json` | G | geometry only |
| edit, record, census | `workshop/edit.rs` | `workshop-*` | G | — |
| session log, undo; session-walk and its verifier | `workshop/session.rs`, `sessionwalk.rs` | `workshop1-*`, `sessionwalk-*` | G | reference kernels only |
| typestate wall | `workshop/membrane.rs` | `membrane-*` | G | a demonstration, unused elsewhere |
| blit law, playback | `shell/present.rs`, `playback.rs` | `shell-blit-*`, `shell-playback-*` | G | — |
| 1:1 present with readback | `shell/win32.rs`, `presentexact.rs` | `presentexact-*`; host records | G-mock | Windows GDI only |
| live loop, input, authoring, hold-walk, mouse look | `shell/live*.rs`, `holdwalk.rs`, `mouselook.rs`, `simtick.rs`, `tickrun.rs` | `liveloop-*` … `mouselook0a-*`; host sessions | G-mock | host runs n = 1 (G14); readback 1 in 75 (G15) |
| durable session | `shell/livesession.rs` | `livesession-*` | G | the seal is a hash (G16); the shell keeps its own fold (G17) |
| admission, batch, compiler | `shell/admit.rs`, `designevent.rs`, `designcompile.rs` | `admit-*`, `designevent-*`, `designir-*`, `hermeneutics-*` | G | no signature (G20); the batch's bytes are not kept |
| saved form, two readers | `kernel/savedform.rs`, `verify/savedform.py` | `readercourt-*` | G | one author (G23) |
| envelope, registrations, registers | `verify/envelope.py`, `preregister.json`, `reasons.json`, `mints.json` | `records-*`, `reasoncourt-*`, `mintwatch-*` | G | G34, G35; the ledger has no head |
| design tool | `design/design.py` | `design/test_design.py` | O | not certified (G27) |
| graybox conversion, simulation, renderers, bench | `graybox/` | `check.py`; the page's self-test; host runs | O | float simulation; one-page replay; hashes unpinned |
| the art: collision is C, dressing out of play, revisions local | `art/` | `art/check.py` | O | the Unreal import not yet run on an engine; visual quality judged by a person, not checked |
| input to photon; a latency claim; a model at the seam; the competitive arena | — | `docs/ROADMAP.md` | D | — |

## 10. What a change touches

This is derived from the pins, the fences and the reads of each row. Treat the row lists as a minimum.

| change | what goes red, or must move |
|---|---|
| any `.rs` under `kernel/`, `shell/`, `workshop/`, or a sealer | `reasoncourt-fence` and `mintwatch-fence` until a registered amendment names the move (`was → is`), with its link in `RSN_CHAIN`; the origin digest must still project. A new file is a link too |
| a renderer source (`mantle`, `formats`, `fast`, `hud`, `present`) | the renderer identity (`RC_RENDERER_ID`) and the per-file constants of every fence that pins it; saved sessions then load as a different renderer |
| the bearing sources or the octant | `bearing-fence`, `bearingfast-fence`, the tick and look fences, the bearing identity |
| the session fold or an event kind | both folds (`sessionwalk.rs` and `playback.rs`), the Python twins, every registered head (the demos, host sessions, the design corpus, `graybox/maps/tactical.layout`) |
| VRDNP1, VRDNP2, the saved form, the envelope | `admit-*`, `designevent-*`, `readercourt-*`, `records-twins`, and their pinned constants |
| a registered entry | never edited: an amendment entry, its hash cited where the rung's rows cite it |
| `verify.py` | the prefix rowset locks held by five fences; the registers' citations of its text |
| `oracle/` | a new oracle, named; `oracle-frozen` |
| `design/` | `design/test_design.py`; no row |
| `graybox/` | `graybox/check.py` (map content); `serve.py --selftest` for both maps (runtime); `--bench` for a cost claim; no row |
| `art/` | `art/check.py` (the art against C and the player, plants, a look and a layout revision); the importer's in-engine self-check and its report on the host; no row |
