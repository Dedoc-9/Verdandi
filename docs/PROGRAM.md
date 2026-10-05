<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2026 Daniel J. Dillberg -->

# Verðandi — the program in depth

*A guided reading of what the program is, how its parts hold each other honest, and why every claim it makes
carries its own falsifier. For the terse ledger see [`verify/RUNGS.md`](../verify/RUNGS.md); for the isolation
theorem see [`EPISTEMIC-INVARIANCE.md`](../EPISTEMIC-INVARIANCE.md); for the honest limits see
[`GHOSTS.md`](GHOSTS.md); for where it is going see [`ROADMAP.md`](ROADMAP.md).*

**Author:** Daniel J. Dillberg · **Contact:** [bigdilly95@gmail.com](mailto:bigdilly95@gmail.com)

---

## 1. What it is

`Verðandi` is a deterministic 1080p game-rendering studio built over a frozen renderer it does not own. It is the
second of three norns. `Urðr` — *what has become* — is the certified renderer, frozen at the tag `urdr-oracle-1`
(commit `4c8c2451…`) and, for the camera that turns, at `urdr-oracle-2` (commit `ad6d55fe…`); it is evidence, not a
dependency. `Verðandi` — *what is becoming* — reproduces that renderer's
pixels bit-for-bit in native std-only Rust, then turns an authored edit into a new authority and an exact
consequence record. `Ursprung` — *the origin* — is the older studio arc, measured and retired, whose one settled
lesson is carried in the shell's contract: *a shell that mirrors kernel logic is a second authority.*

The program's governing conviction is that **`integrity ≠ truth`**. A record that validates is not thereby correct;
a build that compiles is not thereby adopted; a condition that is registered is not thereby earned. Every mechanism
in the tree exists to keep those distinctions visible, so that a claim can be graded rather than believed.

---

## 2. The charter, and the dependency rule

The charter was ratified before the first commit and has not moved since:

    KERNEL     deterministic · std-only · no shell dependency · no UI toolkit · no presentation API
    WORKSHOP   owns authored edits · validates before projection · can create new authority · records consequences
    SHELL      owns window / input / presentation · contains no kernel logic · contains no authority mirror
    UI         viewport + HUD = the kernel's framebuffer, digest-pinned; editor panes = shell chrome, off-gate
    ORACLE     Urðr is frozen evidence (the tags urdr-oracle-1 and urdr-oracle-2) · not a runtime dependency

The dependencies flow one way, and the negation is enforced as hard as the assertion:

    oracle ──► kernel                    never:  kernel ──► shell
                 ▲                               kernel ──► workshop
                 │                               shell  ──► canonical authority
    workshop ────┘
    shell ──────► kernel framebuffer

`MEMBRANE-0` made the one-way law a compile-time wall: a gate row passes precisely when `rustc` *refuses* to compile
a planted violation. The wall is not a comment; it is the type system declining to let the shell touch the truth.

---

## 3. The four layers

Every subsystem is classified before it is built, on a discipline inherited from `Ursprung`:

- **CORE** — the only layer that may move committed state. In `Verðandi` the kernel is CORE-adjacent but *mints no
  authority*: it cannot change a cell, a tile, or the camera. The workshop is the true CORE — it alone creates a new
  authority, and it records the consequence beside it. In the live editor the committed state is the session's log:
  it moves only by an appended event, and the workshop's `sessionwalk` is the replay every saved session is held to
  (§11, and ghost G17 on where that log is kept while it runs).
- **VIEW** — consumes CORE state and produces a rendering or a reading. It mints nothing. The kernel's per-frame work
  (a scene in, an index frame and a picture out) is VIEW; so is the HUD.
- **ALLOCATOR** — hands out bounded, predictable working sets (`O(record)`), free of dynamic runtime scaling.
- **OBSERVER** — reads and measures without perturbing. The cardinal invariant: **replay stays byte-identical with
  observers active.** A benchmark that changed the picture would not be an observer.

The layers are not documentation; they decide what a piece of code is *allowed* to do. A performance probe that
wrote a wrong pixel would be a VIEW masquerading as an OBSERVER, and the gate says so.

---

## 4. The frozen oracle

`kernel/mantle.rs` is Urðr's placement made a library: `parse_scene`, `picture`, `Scene::{strips, frame, emit}`,
`frame_digest`, `sha256`. Its arithmetic is the tag's, byte for byte. It is **never modified for performance.** It
is the correctness oracle, and the relationship to it is asymmetric on purpose: a candidate is *guilty until its
bytes agree*, and the differential always compares candidate → frozen, never the reverse. The harness is not the
oracle; a green harness that disagreed with the frozen emit would be the harness that is wrong.

Two witnesses accompany every frame where two quantities exist: the `URDRFB1` index digest (geometry) and the
picture's `sha256` (appearance). Never one where two are due. Wall-clock is never a witness — it is off-gate, on a
named host, and the witnesses are checked before any number is printed.

The oracle is more than the renderer. `oracle/game/` (`GAME-0`) carries Urðr's game layer from the same tag, verbatim:
seventeen discrete vertical slices from level generation (`gamegen`) through the assembled state identity
(`statecanon`), the kinema view membrane and the input membrane (`cue`), with their frozen corpora and red-first suites.
Every file is listed with its sha256 and its Urðr git blob id, and the gate runs Urðr's own 411 tests in place. It is
evidence the gate reads. No kernel, workshop or shell code depends on it. Since ORACLE-D0 the gate also asks Urðr's own
`statecanon`, in place, to compose the oracle's third hash, `D_0`, from the oracle's view, and checks it against the
frozen value — the studio checks it and still mints none of it.

A second tag stands beside the first. `urdr-oracle-2` freezes the **bearing camera**: a heading is an integer id in
[0, 360000) naming one primitive Pythagorean triple, and at the four cardinals it is the frame the first tag already
fixes. `kernel/bearing.rs` is its reference, the tag's text with only visibility changed, reproducing all 104
witnesses; `kernel/bearingfast.rs` is its fast sibling, held to it byte for byte. The pattern is the facing
camera's, repeated: the turning camera was certified in Urðr first, because nothing here could have held a renderer
to account outside the four facings.

---

## 5. RECORD-0 — the envelope every claim is written in

Nothing the program measures is stored as a bare number. Every record is sealed in the RECORD-0 envelope
(`verify/envelope.py`, with a Rust twin in `workshop/edit.rs`):

    { name, version, claim_class, provenance, validity_scope, forbidden_interpretations, data, reading, chain_hash }

- `claim_class` is one of `measured | established | declared | predicted`.
- `validity_scope.certifies` says exactly what the record vouches for, and for what inputs.
- `forbidden_interpretations` is a non-empty list of readings the record must *not* be given.
- `data` is the measurement — and carries **no verdict-shaped key anywhere inside it** (scanned recursively:
  `verdict`, `valid`, `passed`, `ok`, `pass`, `fail`, `within`, `over`, …). A comparison against a budget is *two
  numbers in `data` and a sentence in `reading`* — never a stored `PASS`.
- `chain_hash` is the `sha256` of the canonical JSON of the seven required fields; `reading` stays outside it.

Two languages write these bytes and one gate reads them: `records-twins` proves Python and Rust seal identical
hashes, and `records-firewall` proves every committed record carries the fields, hides no verdict, and cannot be
tampered without the hash moving. The point is structural: a gate that prints `PASS`/`FAIL` must never be able to
find one *stored as data*, or the record would be smuggling a verdict past the reader.

---

## 6. Preregistration — the method before the number

A rung that will produce a number on a host registers its **hypothesis, success condition, failure condition, and
interpretation limits** in `verify/preregister.json` *before its instrument runs*. Each entry is hash-locked; the
record the rung later seals must cite that hash. **An entry without a failure condition is refused a seat.**

This is a fork of the author's executable-epistemics registry, and its purpose is to make weakening a method a
*visible diff* rather than a silent re-hash. The decision rule is fixed before any result can tempt it. When
`GAUNTLET-2` promoted the threaded emit, the rule it was judged against — *some `T>1` p99 below the sealed baseline*
— had been hash-locked (`711cc1d4`) a patch earlier, including the reading that a *scaling stall is memory-bandwidth
contention, not a call for more threads.*

---

## 7. The two-court rule

Correctness and performance are **two separate courts**, never conflated:

- **Correctness** is byte-identity to the frozen oracle. It is *mandatory* and *gate-enforced*. A candidate that
  differs by a single pixel is not a renderer at any speed.
- **Performance** is wall-clock speed. It is judged *independently*, *off-gate*, on a *named host*, with the
  witnesses checked first. A speed number is never cross-compared to a different apparatus's absolute — only
  same-apparatus deltas are legitimate.

The separation is what lets the optimization staircase move fast without ever risking the picture: every tread is
proven byte-identical on the gate, and only *then* is its speed a separate question.

---

## 8. The pieces, and how a frame flows

    scene ──► Scene::strips ──► Scene::frame ──► emit ──► picture ──► composite ──► to_blit ──► present
    (parse)   (traversal)       (walls+floor     (texel   (two        (+HUD         (BGR         (the window,
                                 cast, the        pass)    witnesses)   overlay)      top-down)    off-gate)
                                 index frame)

- `kernel/mantle.rs` — the frozen oracle (geometry + the reference emit).
- `kernel/fast.rs` — the optimization staircase, every tread byte-identical to the frozen emit (see §9).
- `kernel/formats.rs` — the studio's input formats (level `VRDNLVL1`, tiles `VRDNTIL1`, camera) composed into the
  kernel's `URDRMNTI` scene.
- `kernel/hud.rs` — the overlay drawn into the picture, under its own pins, index-free.
- `workshop/edit.rs` — an edit in, a new authority out, a hash-chained consequence record beside it; the Rust twin
  of the envelope.
- `shell/present.rs` — renders a scene to the composite (now via the LOCKED threaded fast path, byte-identical) and
  proves the blit is an invertible carrier of the kernel's bytes (the blit-hash law).
- `shell/win32.rs` — the only file that opens a window and reads DWM's composition clock; behind `--cfg
  shell_window`, off-gate.
- `shell/heading.rs` — the only file of the shell that reaches the bearing kernels: the fast tread for the live
  frame at a free heading, the reference to recompute it.
- `shell/liveloop.rs`, `liveinput.rs`, `liveauthor.rs`, `holdwalk.rs`, `simtick.rs`, `tickrun.rs`, `mouselook.rs` —
  the live editor: the loop, the bindings, the tick (§11).
- `shell/playback.rs`, `shell/livesession.rs` — the session the loop renders, and its journal, seal and loader.
- `shell/admit.rs` — the admission seam (§12).
- `workshop/sessionwalk.rs` — the session-walk's definition and its verifier, rendering with the references only.
- `verify/verify.py` — the gate: every claim above as a row that can redden; two runs byte-identical or nothing
  landed.

---

## 9. The fast-path staircase

`kernel/fast.rs` is a sibling of the frozen emit, never `mantle.rs`. It holds the whole optimization staircase, each
tread proven byte-identical to the frozen oracle:

| Function | Rung | What it is |
|---|---|---|
| `emit` | LOCALITY-0 LOCKED | the accepted single-thread emit: the row-major floor DDA with the floor fetched from the 8×8 **blocked** execution format (`floor_blocked` + `blocked_floor`), monomorphized |
| `emit_linear` | GAUNTLET-1c archived | the linear-fetch DDA, retained verbatim as the immutable reference witness the historical courts measure against |
| `emit_collapse` | GAUNTLET-1b | the floor divide-collapse (2 divides/floor px), the same-apparatus speed baseline |
| `emit_partitioned(group)` | GAUNTLET-2 | the partition-agnostic core: any column subset in any order, byte-identical; a pure function of the column *set* (disjoint writes, no shared state) |
| `emit_threaded(threads)` | GAUNTLET-2 | execution only: the contiguous `T`-group partition rendered across `std::thread::scope`, routed entirely through `emit_partitioned` |
| `render` | GAUNTLET-2 LOCKED | the accepted production render: mantle's frozen geometry, then the pixels via `emit_threaded` at `PROD_THREADS = 8` |

Beside them stand the measurement apparatus, fenced from the promotion chain: `structure` (RE-BREAKDOWN-1 Court A,
deterministic), `mod probe` (RE-BREAKDOWN-1 Court B, `black_box`-anchored ablation, never a renderer), and `mod
locality` (LOCALITY-0's swizzle bijections and per-band instruments). A gate row greps the source to prove the
production functions reference *no probe* — the apparatus cannot leak into the renderer.

---

## 10. The ledger, in one breath

The seated order reaches everything the frozen oracle certifies. `WORKSHOP-1` authors walls, ground and tiles as a
hash-chained, replayable history; `INPUT-0` turns shell input into a typed command and a new camera that replays
headless; `SESSION-WALK` interleaves moving and authoring into one sealed chain; `SHELL-PLAYBACK` proves the window
shows exactly that sealed becoming; `LATENCY-0` locked the present-timing method before any number; and the
**GAUNTLET staircase** — measure (`0`), the arithmetic (`1a/1b/1c`), re-measure (`RE-BREAKDOWN-1`), data locality
(`LOCALITY-0`), and parallel execution (`GAUNTLET-2`) — carried the emit from the certified baseline to a stable
~2,355 µs p99 at eight threads, ~3.3× faster, byte-identical every step, the frozen oracle untouched throughout.

The boundary holds end to end: `SESSION-WALK` proves what is becoming, `SHELL-PLAYBACK` proves the window shows
exactly that becoming, and `LATENCY-0`/`GAUNTLET` measure how fast it is produced and shown — and every performance
step survives the same pixel-level oracle, so speed is never traded for correctness and a failed experiment stays
permanently useful evidence.

Since then the ledger has grown two more arcs, each described below: the **live editor** (`LIVE-LOOP-0` through
`MOUSE-LOOK-0a`, §11) and **admission** (`ADMIT-0` and `READER-COURT-0`, built; §12 and §13). The rung after
them, `REASON-COURT-0`, is registered and not built: it holds every refusal the gate requires to a registered
reason (see [`ROADMAP.md`](ROADMAP.md) and ghost G24).

---

## 11. The live session — one log, and the window is its replay

The live editor (`shell live-window`, `shell look-window`) closes the cycle the earlier rungs built in halves:
input, authority, render, present, observe, the next input.

    device ─► tick ─► typed action ─► an event appended ─► replay: W, M, camera, head ─► kernel ─► screen ─► readback
                                            │
                                            └─► journal.vsj (flushed before it counts) ─► on Esc: session.json, sealed,
                                                read back, replayed, and only then counted as saved

Five design decisions carry it.

- **The loop holds no world.** A key, a mouse report or a script becomes a typed event (a move, a look, a cell
  opened or closed, a tile class painted, a sensitivity change). The event is appended; W, M and the camera are what
  the log replays to. There is no preview, no pending state and no second copy to drift.
- **A tick is when; an event is what.** Mouse-look runs on a 64 Hz tick of exactly 15,625 µs: the reports of a tick
  are summed into one look, then the tick's other inputs apply in arrival order, one command a tick. Ticks are
  saved and checked for form and are never folded into the head, so the same commands at other ticks reach the
  same head. All of it is integers; there is no float in a rule.
- **The fast path renders; the reference certifies.** At one of the four facings a frame is the facing kernel's, as
  always. At a free heading it is rendered once by the fast bearing tread, and recomputed by the reference: one
  frame in 64 during the run, off the loop, and every such frame before the session is saved. A save that finds a
  difference refuses and writes nothing.
- **Capture is the shell's, not the session's.** Whether the window holds the mouse, has the focus or shows a
  cursor never becomes an event. Input that arrives while the window is in the background is dropped and counted.
- **Saved means verified.** The session is written in the workshop's own session-walk format, moved into place
  atomically, read back from the disk and replayed to every witness before the run reports success. Resuming
  continues into a new file whose lineage names its parent; the parent is never modified. A crashed run's journal
  resumes the same way, dropping a torn final record.

What is measured and what is not: the laws above are rows over a mock on every gate; on the owner's host a real
mouse turned the camera through 1,761 looks with every free-heading frame the reference's. No latency, frame rate
or feel is claimed (G21), and the screen is read back on a schedule, not at every composition (G15).

---

## 12. Admission — program time and content time

Two different things can change, and they are certified differently.

    program time    the machine changes ──► the gate runs: 226 rows, twice, byte-identical
    content time    the world changes   ──► the artifact is checked and admitted; the gate does not run

*The gate certifies the machine. ADMIT admits the world's changes.* `ADMIT-0` is the first seam built on that
split. A proposal is a file in a line language, `VRDNP1`: exactly eight lines, each ended by one line feed, 327 to
337 bytes — the language's name, the renderer's identity, the bearing kernel's, the parent head, the proposer's
handle, an operation, a target, a value. Every typed proposal has exactly one byte form, so its digest is the
sha256 of its bytes and there is nothing for two readers to disagree about.

    bytes ─► size ─► recognize ─► identities ─► load the session ─► anchor ─► duplicate ─► grant ─► authority
              │          │            │                │               │          │          │          │
              └──────────┴────────────┴── each a typed refusal that leaves nothing ──────────┴──────────┘
                                                                                                        │ admitted
                                             one ordinary edit, appended by the session's own push ◄───┘
                                             its envelope beside the event, never in the head

Three properties are the design.

- **One recognizer.** It is small, it is the only reader of the language in the program, and the gate holds it
  against a recognizer written apart, over the corpus and every single-byte mutant of three proposals.
- **Stale is refused, never rebased.** A proposal names the head it was written against. If the session has moved
  on, the proposal is refused and nothing is merged or replayed onto the new head.
- **An admitted proposal is an ordinary event.** The world cannot tell an admitted edit from a typed one: the head
  folds the edit and nothing of the envelope. The envelope records how the edit arrived, for a reader; it is not
  authority.

The grant (which operations, which cells, which tile classes) comes from the admitting command line, not from the
proposal. The process is killed at eight registered points in the gate, and after each the session is either the
parent untouched or the child whole. What an admission does not record is G20; that nothing here involves a model
is said there too.

---

## 13. The saved form — one language for everything read back

Every artifact the program saves and later reads (a session, a journal record's payload, a checkpoint's line, every
sealed record) is JSON written by one of three writers. It used to be read by one of eight readers, which agreed
on files the tree had written and were seen not to on hostile bytes (G19). `READER-COURT-0` (`f53017cd`) closed that,
and its design is the same move ADMIT-0 made, applied to the old language instead of a new one.

- **The language is the writers'.** Not general JSON and not canonical bytes: the bounded language the tree's own
  writers are permitted to emit. One object and one final line feed; spaces and line feeds alone between tokens; no
  name twice in an object; integers only, in signed 64 bits, with one spelling; strings in well-formed UTF-8 with
  one spelling of every character; at most seven levels of objects and arrays, the root object counted as the
  first.
- **The verdict belongs to the language.** Bytes are accepted, with a typed value, or refused with one of seven
  codes and a byte offset: the first byte at which the input stops being the beginning of any document. The offset
  is defined by the language and the bytes, so no reader owns it and every reader must give the same one.
- **One reader in production, two at the boundary.** One Rust reader, in one file shared by path, replaces the four
  parsers. An independent Python reader, with no `json.loads` beneath it, is the sealer's. The court holds them to
  each other over every single-byte mutant of three registered documents, and holds both to verdicts written into
  the registration before either exists.
- **Writers refuse beyond it.** Each writer gives its bytes to the reader before it writes them, so the language is
  enforced where a file is made and not only where it is read.

It is built: `kernel/savedform.rs`, `verify/savedform.py`, and eight rows. The two readers give the same verdict
on all 163,072 single-byte mutants of the three registered documents and on every registered boundary mutation of
every real file the gate holds. What that does and does not reach is G19 and G23.
