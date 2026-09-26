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
(commit `4c8c2451…`); it is evidence, not a dependency. `Verðandi` — *what is becoming* — reproduces that renderer's
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
    ORACLE     Urðr is frozen evidence (the tag urdr-oracle-1) · not a runtime dependency

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
  authority, and it records the consequence beside it.
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
