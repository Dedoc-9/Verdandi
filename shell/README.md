<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# `shell/` — the window

Contract: own the window, the input pump and the presentation of the kernel's framebuffer; contain no kernel
logic and no mirror of the authority; be replaceable. The shell blits pixels the kernel produced and hashes
what it blitted, so a picture that reached the screen without passing through the kernel is a detectable
fault, not a feature.

Ratified shape for SHELL-0: hand-rolled Win32 through `extern "system"` declarations — window, `StretchDIBits`,
message pump, `DwmFlush` as the frame → composited barrier — zero crates, std-only like the
kernel, Windows-only and declared so. Native controls are the chrome (menu, text editor, inspector list);
the viewport and HUD are the kernel's frame. A cross-platform shell is a later, separate shell. The old
project's lesson stands here: its eight interactive pages each carried an untested JavaScript mirror of the
Python authority; this shell carries none.

## Blueprint

The shell is where time, devices and the screen enter the program, so its design is a row of seams. Each seam says
what may cross it and what may not, and has a row that goes red when something else does.

```text
    device ──► window procedure ──► the tick ──────────► a typed action
               (win32.rs)           (simtick, mouselook)  (liveinput, liveauthor, holdwalk)
                                                               │ append
    proposal bytes ──► admit.rs: recognize · anchor · grant ───┤
                                                               ▼
                                         playback::LiveSession   the log; W, M, the camera and the head are its replay
                                           │                         │
                                           │ journal, seal           │ state
                                           ▼                         ▼
                              journal.vsj · session.json     present.rs · heading.rs ──► the kernel
                                 (livesession.rs)                    │ the bytes, checked against the reference
                                                                     ▼
                                                    SetDIBitsToDevice ──► the composed screen, read back
                                                                     │ a refusal, a differing readback
                                                                     ▼
                                                    refusals.log · runs.log   observations, read by no rule
```

| Seam | What crosses | What may not | Row |
|---|---|---|---|
| window → loop | key codes and raw mouse counts, stamped with the tick they were drained in | focus, the cursor, capture: shell state, never session state | `mouselook-capture` |
| loop → session | typed events only: a move, a look, a cell opened or closed, a tile class painted, a sensitivity change | a world of the loop's own; a preview | `liveinput-fence`, `liveauthor-authority` |
| proposal → session | one recognized edit, its envelope beside the event and never in the head | an unrecognized byte, a stale parent, a scope the command line did not grant | `admit-reader`, `admit-anchor`, `admit-capability` |
| session → kernel | W, M and the camera | anything back but pixels and a digest | `shell-playback-no-authority`, `liveinput-continuity` |
| kernel → screen | the bytes that were checked against the reference | a picture that did not pass through the kernel | `shell-blit-law`, `mouselook-present` |
| session → disk | a journal record flushed before it counts; a saved file read back and verified before it counts | a save that was not verified; a parent modified by its continuation | `livesession-save`, `livesession-resume`, `livesession-recover`, `admit-crash` |
| run → logs | one line per refusal, one line per run | a log read back by any rule | `refusallog-fence`, `runledger-fence` |

The live session is held in this binary while it runs, and that is the seam to watch. The shell does not own the
world: `LiveSession` is changed only by appending an event, and its saved file is replayed by the workshop's own
`sessionwalk`, which renders with the reference kernels and holds nothing of the fast path.

| File | What it is |
|---|---|
| `present.rs` | the platform-agnostic core: render a scene to the composite (via `fast::render` — GAUNTLET-2's LOCKED threaded emit at `PROD_THREADS=8`, byte-identical to the frozen `picture`, so the parallel render headroom reaches the present path), `to_blit`/`from_blit` (24-bit BGR top-down, a bijection), `blit_witness`, `blit_roundtrip_ok` — the blit-hash law; `LoopRenderer`, the production entry for in-loop rendering (persistent buffers, `fast::render`'s calls then the HUD), adopted by ALLOC-REUSE-1 LOCK; since LIVE-LOOP-0 the live windows render every composition through it, and every fresh render entry's call site is pinned (row `allocreuse1-lock`) |
| `playback.rs` | SHELL-PLAYBACK: `shell playback --session S` consumes a sealed SESSION-WALK, replays it through the present path, and emits the per-move frame digest + blit witness + round-trip; `shell checkpoint --at K` / `shell resume --checkpoint CK` fold in checkpoint/replay equivalence. Re-derives every witness and the head and REFUSES (`DIVERGED`) if the sealed input was tampered; writes no authority (rows `shell-playback-*`) |
| `latency1r.rs` | LATENCY-1R's court, platform-agnostic: render-start → composited for the production render (T=8) and the single-thread reference (`fast::emit`) over the sealed session, in a locked and a uniform phase regime, witnesses first, ABBA-interleaved, against a `Surface` (clock, present, composition barrier, pump). The gate drives it through a deterministic `MockSurface` (`shell latency1r-selftest`, row `latency1r-court`); the host drives it through the GDI surface appended to `win32.rs` |
| `framesplit.rs` | FRAME-SPLIT-0's court, platform-agnostic over LATENCY-1R's `Surface`: the render-start → frame-ready interval split into seven contiguous phases (strips, frame, floor_swizzle, emit, hud, bgr, blit) beside its uninstrumented envelope, both arms, ABBA after a warm-up, witnesses first with the marked mirror (`present.rs::arm_composite_marked`) byte-equal to the envelope path. Gate: `shell framesplit-selftest` (row `framesplit-court`); host: the window driver appended to `win32.rs` |
| `presentscale.rs` | PRESENT-SCALE-0's court, generic over a `GeomSurface` (a `Surface` whose client area can be set): FRAME-SPLIT-0's production frame (envelope and split) presented into a half-size and a full-size client area, the destination the only variable, 8 blocks H F F H H F F H with warm-up after every resize and the client rectangle verified. Gate: `shell presentscale-selftest` (row `presentscale-court`, with a clamped-geometry plant); host: the settable-client GDI surface appended to `win32.rs` |
| `presentstretch.rs` | PRESENT-STRETCH-0's court, generic over a `StretchSurface` (a `Surface` whose stretch mode can be set and read back): FRAME-SPLIT-0's production frame (envelope and split) blitted into the fixed half-size destination under `BLACKONWHITE`, `COLORONCOLOR` and `HALFTONE`, the mode the only variable, 12 blocks B C H H C B B C H H C B with warm-up and the effective mode and client area verified. Gate: `shell presentstretch-selftest` (row `presentstretch-court`, with an ignored-mode plant); host: the stretch-mode GDI surface appended to `win32.rs` |
| `allocreuse.rs` | ALLOC-REUSE-0's court, over LATENCY-1R's `Surface`: FRAME-SPLIT-0's production frame with its buffers allocated every frame (fresh) or once and overwritten (reused, `present.rs::arm_composite_reuse_marked` + `to_blit_into` into `ReuseBufs`), the lifetime the only variable, four cells ABBA after a warm-up, witnesses first with the reused bytes equal to the fresh path's. Gate: `shell allocreuse-selftest` (row `allocreuse-court`); host: FRAME-SPLIT-0's window, driver appended to `win32.rs` |
| `allocreuse1.rs` | ALLOC-REUSE-1's two courts for the persistent-buffer render-loop entry (`present.rs::LoopRenderer`). `loop_equiv` (gate, no clock: `shell loop-equiv`, row `allocreuse1-equiv`): one renderer, its buffers poisoned first, renders the corpus, the adversarial cameras and the sealed session in three orders, byte-identical to the fresh path, no buffer replaced. `court` (over LATENCY-1R's `Surface`): fresh and reused envelopes ABBA, 1000 per cell. Gate: `shell allocreuse1-selftest` (row `allocreuse1-court`); host: FRAME-SPLIT-0's window, driver appended to `win32.rs`. Read ADOPT on the owner's host; locked |
| `presentexact.rs` | PRESENT-EXACT-0's court for PRESENTATION-CHOICE-0 (the certified picture 1:1, borderless), generic over an `ExactSurface` (set the call, clear, read the screen back, report the geometry): StretchDIBits at 1:1 against SetDIBitsToDevice, frames through `LoopRenderer`, the composed screen read back equal to the certified bytes as a hard gate, then ABBA at 1000 per cell. Gate: `shell presentexact-selftest` (row `presentexact-court`, a mock screen with five plants); host: the borderless, topmost, DPI-aware popup appended to `win32.rs` |
| `liveloop.rs` | LIVE-LOOP-0: the first loop that renders every composition live, from the current step of a sealed session, through `LoopRenderer`, presented by SetDIBitsToDevice. Witnesses first, outside the loop; every composition's bytes compared with the step's verified bytes before the present (a difference refuses); the composed screen read back on a schedule, a differing screen counted and logged and never hidden. No input, no clock, no file |
| `liveinput.rs` | LIVE-INPUT-0: a key press becomes a typed event in the session the loop renders — key → action (`bind`) → an event appended to `playback::LiveSession` → the log's replay → `LoopRenderer` → the screen, read back. The binding is fixed and pure; an auto-repeat is counted and never bound unless HOLD-WALK-0's held set admits it; a refused edit is one refusal-log record and no event. The loop never holds a world of its own |
| `livesession.rs` | LIVE-SESSION-0: the live session made durable, without a second authority — the journal (`build/sessions/<run_id>/journal.vsj`, one checksummed record per event, flushed before it counts; a torn final record dropped on load); the seal (the session written in the workshop's session-walk format, moved into place atomically, then read back and replayed before the run counts as saved); the loader (`--resume` of a saved session or a crashed run's journal, classified LOAD, LOAD with a different renderer, TAMPERED or DIFFERENT-RENDERER; the continuation is a new file, the parent never modified). ADMIT-0: the admitted edit's envelope, its form checks, and the registered death points |
| `liveauthor.rs` | LIVE-AUTHOR-0: the live editor's authoring binding — LIVE-INPUT-0's keys, plus 1-5 for the tile classes; a class key is one edit `tile:CLASS,R,G,B` whose colour is the registered palette's next after the class's current colour, read from the session's own M. Pure; it holds no colour, no tile and no preview |
| `holdwalk.rs` | HOLD-WALK-0: which held keys walk — an auto-repeat of W, A, S, D or an arrow is that key's move, at most one admitted per composition, the rest counted as coalesced; a repeat of any other key is ignored. No key state, no clock |
| `refusallog.rs` | REFUSAL-LOG-0: one JSON line per refusal on the present path, appended to `build/refusals.log` (or `$VERDANDI_REFUSAL_LOG`) and never rewritten. An observation: not sealed, not committed, read by no rule; a failed append never changes a refusal. REFUSAL-WHY-1 (in `presentexact.rs`) puts the windows found above ours over a differing box into the record, as program, class, rectangle and flags; a window's title reaches the console and never the log |
| `runledger.rs` | RUN-LEDGER-0: one JSON line per run, refused or not, appended to `build/runs.log` (or `$VERDANDI_RUN_LEDGER`) when the run ends — the denominator the refusal log lacks. The two files join on `run_id` |
| `simtick.rs` | SIM-TICK-0: the mouse-look rules as integer law, pure — the 64 Hz tick of exactly 15,625 µs, the accumulator (one command per tick: the reports' sum, then the other inputs in arrival order), delta = counts × multiplier × step, the heading's turn, the nearest cardinal (the tie clockwise), the rebinding of A and D to the strafes, the tick form a saved log must have, the script reader. SIM-TICK-0a adds the control map (PgUp, PgDn, Tab), the admission of at most one held repeat a tick, and the replay of the configuration (a sensitivity event is one legal transition; a look's inputs carry the configuration in force). No clock, file, static, float or thread |
| `heading.rs` | SIM-TICK-0: the frame at a heading, and the only file of the shell that reaches the bearing kernels — the facing kernel's frame at an anchor (as before), BEARING-FAST-0's production tread `ca` at a free heading, and the reference's recomputation of free-heading frames across threads (`certify`), which every save runs before it writes. MOUSE-LOOK-0: the free-heading render is made by a `Painter` the session keeps, into buffers it reuses, and its picture stays readable, so the loop presents the very render the witness came from |
| `tickrun.rs` | SIM-TICK-0: the tick run — scripted raw inputs with their times through the accumulator into the live session, the look once and first, then the tick's keys; a sensitivity action that takes effect appended as a sensitivity event (the session owns the configuration), and a held key's repeats traced as walked, coalesced or ignored; windowless (`shell simtick-selftest`), no surface, no loop, no clock |
| `mouselook.rs` | MOUSE-LOOK-0: the tick source of the live loop — the trait a surface gives it (a clock in microseconds, the admitted horizontal mouse counts, the release); the ticker (each composition: the tick the clock has passed is closed and its command applied once through `tickrun::apply`, then what the composition drained is stamped with the tick of now); the off-loop sample (every 64th free-heading frame recomputed by the reference on a worker thread, read back oldest first); and the mock's scripted mouse, keyboard, focus and clock (`shell look-selftest`; MOUSE-LOOK-0a: its window closes at an admitted Esc, as the host's does). It appends nothing itself and renders nothing. Capture is shell state: nothing here or in the session knows the focus changed |
| `admit.rs` | ADMIT-0: the admission seam — the recognizer of `VRDNP1` (exactly eight lines, each ended by one LF; 327 to 337 bytes; one byte sequence per typed proposal) and its inverse, the emission; the grant from the command line (operation kinds, a rectangle of cells, tile classes); the run: the proposal's bytes read once and bounded, recognized, then the identities, the saved session loaded once, the anchor (a stale parent refused, never rebased), the proposer's id, the grant and the authority, in the registered order, each refusal typed and leaving nothing; the admitted edit appended by the session's own push in memory, then the run opened and sealed by `livesession.rs`; `admit-anchor` (the four leading lines of a proposal for a saved session; reads only); the reader court in process (every single-byte mutant of a proposal). It spawns nothing, connects to nothing, reads no clock and nothing under `verify/` |
| `main.rs` | `shell witness` / `shell selfcheck` (headless, the law); `shell playback` / `checkpoint` / `resume` (headless, SHELL-PLAYBACK); `shell latency1r-selftest` / `framesplit-selftest` / `presentscale-selftest` / `presentstretch-selftest` / `allocreuse-selftest` / `allocreuse1-selftest` / `presentexact-selftest` (headless, the courts over the mock surface); `shell loop-equiv` (headless, ALLOC-REUSE-1's correctness court); `shell show` / `show-playback` (PRESENT-EXACT-0 LOCK: the conforming presenter, the certified picture 1:1 in a borderless window via SetDIBitsToDevice, the composed screen read back after every present, exit 3 if it ever differed, Esc closes); `shell presentexact-probe` (a readback diagnostic, no clock, no record); `shell run` / `playback-window` / `latency1r-window` / `framesplit-window` / `presentscale-window` / `presentstretch-window` / `allocreuse-window` / `allocreuse1-window` / `presentexact-window` (Windows: the window; elsewhere: `SHELL-NO-WINDOW`); the live rungs, each as `-selftest` (the mock, what the gate runs) and `-window` (the host): `liveloop-`, `liveinput-`, `livesession-`, `live-` (the live editor on keys), `look-` (the live editor with the mouse); `simtick-law` and `simtick-selftest` (windowless); `admit`, `admit-selftest` and `admit-anchor` (ADMIT-0; no window) |
| `win32.rs` | behind `--cfg shell_window` on Windows: the hand-rolled window, `StretchDIBits`, `DwmFlush` as the composition barrier (frame-ready → composited by QPC); guards every present with the blit witness; writes the raw present record. `playback_window` (SHELL-PLAYBACK-b) plays a sealed session frame-by-frame in the real window, each frame blit-law-guarded; with `--measure N` it is LATENCY-0's instrument (per-frame frame-ready → composited across the sealed sequence → `shell/attest/latency-<host>.json`), reused unchanged by LATENCY-1. LATENCY-1R's GDI surface and `latency1r_window` are **appended after** it: LATENCY-0's text stays a byte-exact prefix of this file (row `latency1r-fence`) — host-run, out of every gate build. Every later window is a section appended after it and judged by its own fence: the courts' surfaces, the presenter, and the live windows (`liveloop_window`, `liveinput_window`, `livesession_window`, `live_window`, `look_window` with its raw-input capture) |
| `attest/present-<host>.json` | the host's `frame-ready → composited` record, sealed by `../verify/seal_present.py` under RECORD-0's envelope |
| `attest/latency1-<host>.json`, `attest/latency1r-<host>.json` | LATENCY-1 (the locked present-path court, read through its amendment LATENCY-1a) and LATENCY-1R (render-inclusive), sealed by `../verify/latency1.py` and `../verify/latency1r.py`; `--confirm` seals a separate `-confirm-` record beside each |
| `attest/framesplit-<host>.json` | FRAME-SPLIT-0, sealed by `../verify/framesplit.py` (with `--confirm` beside it) |
| `attest/presentscale-<host>.json` | PRESENT-SCALE-0, sealed by `../verify/presentscale.py` (with `--confirm` beside it) |
| `attest/presentstretch-<host>.json`, `attest/allocreuse-<host>.json` | PRESENT-STRETCH-0 and ALLOC-REUSE-0, sealed by `../verify/presentstretch.py` and `../verify/allocreuse.py` (each with `--confirm` beside it) |
| `attest/presentexact-<host>.json` | PRESENT-EXACT-0, sealed by `../verify/presentexact.py`; its `--confirm` record states the adopted call; each carries HOST-STATE-0's snapshots |
| `attest/liveloop-<host>.json` | LIVE-LOOP-0's first live walk, counts only, sealed by `../verify/liveloop.py` |
| `attest/livesession-<host>-<head12>.json` | a saved live session made a committed record by `../verify/livesession.py`: the session-walk data with its live block, in RECORD-0's envelope, which `shell playback` and the workshop both replay. One per sealed session, named by its head |
| `attest/drift-<host>-s<S>-r<R>.json` | DRIFT-0's runs, sealed by `../verify/drift.py`, each with HOST-STATE-1's snapshots |
| `attest/allocreuse1-<host>.json` | ALLOC-REUSE-1, sealed by `../verify/allocreuse1.py`; its `--confirm` record states ADOPT or REJECT. Each carries HOST-STATE-0's before and after snapshots (`../verify/hoststate.py`) |

SHELL-0a landed the blit-hash law (`../verify/pins/shell-1.json`; rows `shell-*`): the shell shows the kernel's
composite and hands the OS exactly its bytes, and a byte corrupted between the kernel and the blit is detectable
— the defence WORKSHOP-0 named as out of its reach. The window and the number are the host's (SHELL-0,
preregistered); the first host record (`attest/present-<host>.json`) measured frame-ready → composited at
p50 ≈ 5.3 ms on a ~74 Hz panel — the compositor-wait baseline, excluding the kernel render, not input-to-photon.

SHELL-PLAYBACK landed the consumer half (rows `shell-playback-*`): the window shows exactly a sealed
SESSION-WALK and nothing else. Playback consumes the sealed session (never an ad-hoc stream), replays it through
the present path, and its composited frame-digest sequence equals the session's per-move witnesses — the crown
witness tying the sealed-authority mechanism to the certified blit law. It writes no authority, refuses a
tampered/reordered/truncated input (`DIVERGED`), and resumes from any certified checkpoint to the same head. The
on-screen window (SHELL-PLAYBACK-b, `shell playback-window`) now ships in `win32.rs` — host-run under
`--cfg shell_window`, it plays a sealed session in the real window; and only after it does LATENCY-0 measure timing.

What a shell number is and is not: frame → composited is software-reachable; input transport, the present
wait beyond composition, and the panel are not (they need capture hardware). No number from this folder is an
input-to-photon claim.

**What LATENCY-0's window does not time.** `playback-window` renders every frame (`playback::frames`) before the
window opens, then times blit → composited over those bitmaps — so neither LATENCY-0 nor LATENCY-1, which reuses it,
can see the renderer. That is recorded as the amendment LATENCY-1a (before any LATENCY-1 number). LATENCY-1R is the
render-inclusive court: it renders inside its clock, in the same window and on the same sealed session, and compares
the T=8 production render with the single-thread reference only against each other.

## Dev notes

- **Appended, never edited.** LATENCY-0's instrument is a byte-exact prefix of `win32.rs`. Every later window is
  appended after it, so an old number's instrument is still the text that produced it.
- **The mock is a surface, not a model of Windows.** It scripts a clock (the composition count), a mouse, keys and
  focus. A law proven over it is a law of the loop. What Windows delivers is the host run's question, and two first
  host runs answered it with nothing: no key press once, no mouse report once (G22).
- **When is recorded; what is folded.** An input is stamped with the tick it was drained in, not the moment the
  device moved. Ticks are saved and checked for form, and the same commands at other ticks reach the same head.
- **Capture is shell state.** While the window is out of the foreground its input is dropped and counted; no event
  is written and the session holds no word of the focus.
- **A differing screen is counted, and a drifting renderer refuses.** The readback's difference is logged with the
  windows that covered the picture and the loop goes on. A composite that differs from its reference stops the loop.
- **Save, then believe.** A saved session is read back from the disk and replayed before the run reports success.
  A mutation that skipped that comparison once went unseen, and a planted file that is sealed, self-consistent and
  not the live session is now a case.
- **Death is planted, not hoped for.** Admission is killed at eight registered points; after each, the session is
  either the parent untouched or the child whole.

## Ghosts

In full in [`../docs/GHOSTS.md`](../docs/GHOSTS.md). The ones that live in this folder:

- **G7, G8, G10, G11, G13.** The present path: the render headroom reaches the screen only out of phase; the frame
  has no single dominant phase; thin tails; the half-size window's reduction; runs that drift.
- **G12.** The render-loop courts timed a modelled loop. A loop ships now, and its phases have not been timed.
- **G14.** The live windows' laws are proven over the mock; the host runs are few and each is one run.
- **G15.** The screen is read back at one composition in 75, and a free-heading frame is recomputed during a run
  at one in 64. Only the save recomputes every one.
- **G16.** A seal is a hash and durability is the file system's promise.
- **G17.** This binary replays the session with its own copy of the workshop's fold.
- **G20.** Admission records a claimed proposer and a grant from the command line; a later verifier cannot
  recompute the envelope's digest, and nothing is shown about a model.
- **G21, G22.** No latency number exists for the live loop, and two host observations are unexplained.
