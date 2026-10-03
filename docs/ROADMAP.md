<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2026 Daniel J. Dillberg -->

# Roadmap — toward a live, authorable world

*Where the program stands, what "a live authorable world" means for it, and the sequenced, falsifiable path to get
there. This roadmap names rungs that are already public in [`verify/RUNGS.md`](../verify/RUNGS.md), and — since the
owner published it — the route to walking in a live, authorable world, whose rungs are named but not yet built. The
general techniques it points at are cited prior art, not commitments. Other candidate rungs are under private
consideration pending the owner's consensus and are not enumerated here.*

---

## Where we are

Two halves of the studio are built and sealed. The **render** half is fast and honest: the emit is ~3.3× faster than
the certified baseline (a stable ~2,355 µs p99 at eight threads), byte-identical to the frozen oracle at every step,
and the shell now renders through that parallel fast path. The **authoring** half already exists in skeleton:
`WORKSHOP-0/1` turn an edit into a new authority with a hash-chained consequence record; `INPUT-0` turns shell input
into a typed command and a new camera that replays headless; `SESSION-WALK` interleaves moving and authoring into one
sealed chain; and `SHELL-PLAYBACK` proves the window shows *exactly* that sealed becoming. And since `GAME-0`, Urðr's
**game layer** — seventeen discrete vertical slices, from level generation through the input membrane, with their
corpora and suites — sits in `oracle/game/` as frozen evidence from the same tag, passing its own 411 tests in place.

What is *not* yet joined is the loop between them at interactive speed: editing the world **while** the window shows
it, and seeing the consequence immediately, all through the same sealed representation — and doing it for semantics
the frozen oracle never certified.

---

## What "live authorable world" means here

Not a general game engine. Specifically: **a running window in which an author changes the world, the change becomes
a new authority through the sealed workshop path, the projection updates live, and every frame on the screen is
provably the consequence of that authored history** — with new kinds of world content (skybox, filtering semantics,
physics beyond what the tag carries) admitted only when they *earn* an authority, either carried or re-frozen from Urðr
or pinned by a Verðandi-local reference. The bar is the one the program already holds itself to: `built ≠ adopted`, `declared ≠ verified`, and no
semantics reaches the screen without passing through a gate.

---

## The gap, in four questions

1. **Does the render headroom reach the screen?** Measured twice (`LATENCY-1R`): yes for work arriving at a random
   phase (composited output 3.2–3.6 ms earlier at the median), no for a loop that renders right after it presents
   (under 1% gets through the refresh-coupled GDI present). The shell's whole render-start → frame-ready interval is
   14.8–15.7 ms at p50, longer than one refresh on the owner's host, and FRAME-SPLIT-0 found, twice, no single phase
   dominating it (blit largest at 427–434‰). Renderer latency: materially improved. End-to-end presentation latency:
   phase-dependent, no low-latency or competitive claim. The largest phase, the blit, is mostly the 2:1 reduction here:
   at 1:1 it drops ~5.3–5.6 ms (PRESENT-SCALE-0, confirmed on this host). At half size, `COLORONCOLOR`'s blit was
   materially cheaper than the default `BLACKONWHITE`'s in both runs (392‰ and 449‰; `HALFTONE`'s reading did not
   reproduce) (PRESENT-STRETCH-0). Reusing the frame's buffers instead of allocating them every frame took 1.6–1.8 ms
   off the envelope (ALLOC-REUSE-0, confirmed). In this loop most of each saving waits at the composition instead. *(G7 — measured; G8 —
   confirmed, NO SEAT; G11 — confirmed.)*
2. **Can an author edit the live window?** The pieces exist headless (input → typed edit → SESSION-WALK); they are
   not yet wired into the running present loop with live re-projection.
3. **Can the world hold semantics the oracle never certified?** The skybox and filtered VIEW semantics live *beyond*
   the frozen oracle and need the new-semantics route. Physics is different: much of it is already in the tag (see
   below), so the question there is what to carry, not what to invent.
4. **Can independent edits combine?** Two authored branches of a world need a deterministic, consensus-free merge.

---

## The route to walking in a live, authorable world (the owner's order)

The substrate is built: a deterministic world, deterministic materials, a deterministic renderer, an exact presenter,
workshop authority and the session walk. What is missing is the **closed live cycle**: input → authoring authority →
render → present → observe → next input. It is mostly not a renderer problem any more. It is the live loop, live
input and authoring, and making the live chain recoverable. The order:

```text
REFUSAL-LOG-0 → RUN-LEDGER-0 → REFUSAL-WHY / DRIFT-0      the diagnostic foundation (DRIFT-0: sitting 1 of 3 complete)
      ↓
LIVE-LOOP-0      the shipped per-frame loop — walked on the host: 246 compositions live, every readback exact
      ↓
LIVE-INPUT-0     physical input → typed editor action → the workshop/session → a new W, M → the next frame — walked and edited on the host by key presses, every readback exact
      ↓
LIVE-SESSION-0   live events → append-only session → save → restart → replay → the same world — a host walk saved, resumed into a new file, both replayed here
      ↓
LIVE-AUTHOR-0    the thing authored is the same authority the next frame renders — painted live on the host by class keys, saved, resumed there with the painting intact
      ↓
HOLD-WALK-0      held keys walk the grid: the input continuous, the world discrete — measured on the host; not the free movement the owner wants
      ↓
(Urðr)           VIEW-YAW-0: the turning camera earned in Urðr and frozen as urdr-oracle-2 — any heading, the eye still at a cell centre
      ↓
BEARING-0        the bearing camera carried and its reference kernel placed: all 104 witnesses of urdr-oracle-2 bit for bit — built; the gate passes on the host
      ↓
BEARING-FAST-0   the production candidate, held byte for byte to the reference — measured on the host: exact stepping in eight row bands, worst-camera p99 3,716 us (target 6,667); the sweep 622,440 of 622,440 equal
      ↓
SIM-TICK-0       the mouse-look rules as integer law, windowless: the 64 Hz tick, one command per tick, the look event in the one session, reference certification at save — built; the gate passes on the host with the same 197 rows
      ↓
SIM-TICK-0a      two rulings of MOUSE-LOOK-0's court that are rules of the tick, still windowless: a sensitivity change is a typed configuration event in the session, never folded; a held key walks once a tick — built; the gate passes on the host with the same 201 rows
      ↓
MOUSE-LOOK-0     a real mouse on those rules: captured until Esc (shell state, never session state), raw counts into the 64 Hz accumulator, the command into the existing live loop, the picture alone at a free heading, every 64th free-heading frame recomputed off the loop — built; the gate passes on the host; the first window run walked on keys with no mouse report; on the second, under MOUSE-LOOK-0a, a real mouse turned the camera
      ↓
MOUSE-LOOK-0a    an amendment from the owner's review and the first host run: a composition applies at most one closed tick command and span counts tick boundaries between compositions; a run its Esc ended is recorded as escape; the window counts the raw input it receives before it reads it — built; the gate passes on the host with the same 209 rows; the second host run is the execution witness: 13,931 raw reports, 1,761 looks, 1,775 of 1,775 free-heading frames the reference's, a focus loss with no session event
      ↓
the presentation and latency measurement      input to photon in separate segments; frame rate alone is no competitive claim
      ↓
richer edits     vocabulary on the one live editor, not new pathways
      ↓
walking in a live, authorable world
      ⋮
LLM-BUILDER-0    a declared goal beyond the route: a model proposes typed, anchored changes against the sealed session; only the verifier admits them — nothing built, and the route above is built in respect of it. Declared with it (2026-10-03), and by the owner's ruling what the route builds towards: the gate certifies the program and content is admitted, not gated; conversation edits the world through a stream of admitted design events
ADMIT-0          the first rung towards it, chosen in court (2026-10-03) and by the owner's order next after MOUSE-LOOK-0: the admission seam. One strict recognizer for a line language whose accepted bytes are canonical (VRDNP1), an anchor refused when stale, a scope the admitter grants, an admitted proposal an ordinary session event. The gate certifies the machine; ADMIT admits the world's changes — registered (`bdd38593`) and built, nine rows on every gate; not yet run on the host
      ↓
READER-COURT-0 → DESIGN-EVENT-0 → LIVE-AI-EDIT-0 → branch and preview      the owner's order after it; each chosen in its own court; none registered
      ↓
PRESENT-1 (its screen witness settled first), the live-loop re-breakdown, BANDWIDTH-0 / POOL-0; DRIFT-0 continues alongside
```

The owner swapped LIVE-SESSION-0 ahead of LIVE-AUTHOR-0 after LIVE-INPUT-0's host runs. The live loop worked, but its
evidence was still console text that had to be replayed by hand. Durability first means every later host walk,
including LIVE-AUTHOR-0's, is a saved file the workshop verifies, not a transcript.

After LIVE-AUTHOR-0 the owner stops adding bespoke input cases. LIVE-AUTHOR-0 is the last authoring-primitive slice.
From then on the rule is general: every accepted live edit is a typed SESSION-WALK event, the event changes the
authoritative W or M, the next frame is derived from the resulting authority, and the event is durable through
LIVE-SESSION-0. Free continuous movement and richer edits are vocabulary and navigation semantics added to the one live
editor (`shell live-window`), gated in its binding table, not new pathways or rungs. HOLD-WALK-0, registered under its
own name but on the same pathway, made held keys keep walking cell by cell over the same discrete world, because the
frozen renderer draws the eye only at a cell centre facing N, E, S or W. After walking it on his host, the owner judged
that this is not the free movement he wants, and ruled what it becomes: shooter-style mouse-look, taken in rungs. The
turning camera was earned in Urðr first (VIEW-YAW-0, frozen as `urdr-oracle-2`), because no frozen oracle existed to
hold a renderer to outside the four cardinals; here it is carried and placed as a reference (BEARING-0), made fast
against that reference (BEARING-FAST-0), given its rules with no window in the proof (SIM-TICK-0), and only then driven
by a real mouse (MOUSE-LOOK-0). The owner ruled those two are never combined.
Cursor authoring, preview sliders, gizmos and an editor-pane interaction model are deliberately not on the route yet:
those are where a shell starts accumulating an alternate authority.

- **The diagnostic foundation** is not on the critical path to walking. It gives the live loop an instrumented refusal
  surface instead of console archaeology. REFUSAL-LOG-0, RUN-LEDGER-0 and REFUSAL-WHY-1 have landed. REFUSAL-WHY-1
  writes the covering windows into the refusal log as program, class, rectangle and overlay flags. Titles stay
  console-only and are never persisted, and the rectangle is diagnostic geometry, not identity. DRIFT-0 (preregistered)
  repeats the locked PRESENT-EXACT-0 court unchanged, 3 sittings of 4 runs, and is observational first: it counts
  recurrence and cross-run drift from the two files and the host state, with no intervention.
- **LIVE-LOOP-0** is the gate that matters: the current (W, M, C) state → `LoopRenderer` on its persistent buffers →
  one frame rendered from that state → SetDIBitsToDevice → the screen witness → the next frame. It includes window
  events, clean shutdown, refusals logged and runs ledgered. The shell mutates nothing canonical. Its first court is
  narrow: no authoring input, no flip model, no persistent workers, no latency claim.
- **LIVE-INPUT-0** turns physical input into authoring operations through the authority boundary already built
  (Urðr's input membrane `cue`, frozen in `oracle/game/`, the workshop and the session model). The shell never mutates the world directly. The first
  vocabulary is tiny: move the camera, select a cell, open or close a cell, change a tile or material. It is named
  LIVE-INPUT-0 because `INPUT-0` is already seat 9. As ratified and built, the first slice is narrower still: the six
  moves and opening or closing the faced cell, with no cursor and no tile or material keys (those wait for
  LIVE-AUTHOR-0). The authority boundary it goes through is the session model: every press becomes an event in an
  in-memory SESSION-WALK log, and W and M are that log's replay.
- **LIVE-AUTHOR-0** proves the mutation/render bridge. One interaction must demonstrably go input → typed edit →
  session event → authoritative W, M change → next render → changed pixels. The control must hold too: a camera-only
  input may change pixels, and W and M stay unchanged. That preserves the W / M / C boundary the workshop already
  enforces. The test is not "I can click something" but **the thing I author is the same authority that the next frame
  renders**.
- **LIVE-SESSION-0** makes the live chain recoverable by connecting the live loop to the session walk's existing
  authority and deterministic replay, rather than inventing a second live-state system: live events → append-only
  session → checkpoint or save → restart → replay → the same world. It now comes before LIVE-AUTHOR-0.
- **Afterwards:** PRESENT-1, the live-loop re-breakdown, and BANDWIDTH-0 / POOL-0 are optimization and latency work
  measured on the real loop. They are not prerequisites for walking. PRESENT-1 starts with how the screen is witnessed
  once presentation moves off GDI: the GDI readback cannot be assumed to remain a valid witness under flip-model
  presentation, and whatever replaces it is measured before it is trusted.

Each of these rungs is ratified, preregistered and built in turn; none is claimed until its gate stands.

---

## After BEARING-FAST-0: what evidence is worth buying (the owner's ruling, 2026-10-01)

BEARING-FAST-0 is built and measured, and no live path uses it yet. The owner ruled that the next work is chosen by
what evidence is worth buying, not by which optimization can be imagined next. The order:

| # | Work | Why | Where it stands |
|---|---|---|---|
| 1 | BEARING-FAST-0's host speed court | Establish whether the 6,667 µs target is met. | Run: met, 3,716 µs. |
| 2 | Production promotion, only if the target is met | Do not optimize a kernel that is already sufficient. | Met: eight row bands of exact stepping is the production candidate. MOUSE-LOOK-0 wires it into a live path, not before. |
| 3 | SIM-TICK-0, mouse sensitivity and live mouse-look | The actual interaction seam, now that the renderer can support it. | SIM-TICK-0 (the rules and the sensitivity, windowless) is built, and its gate passes on the host. SIM-TICK-0a (the court's two tick rulings, windowless) is built, and its gate passes on the host. MOUSE-LOOK-0 (the real mouse and the window) is built and its gate passes on the host. `shell look-window` ran there once: the keys walked on the tick and the save verified, but no mouse report reached the loop, so the look itself is still to be shown. MOUSE-LOOK-0a (the owner's correction of a registered limit, the run's end, and the window's observation of raw input) is built and its gate passes on the host. On the second run a real mouse turned the camera: 1,761 looks on the tick, the focus lost and regained with no session event, the session's picture on the screen, and every free-heading frame equal under the reference. |
| 4 | PRESENT-1, the flip-model presentation | Renderer speed is not input-to-photon speed; LATENCY-0's evidence makes this the next presentation boundary. | After mouse-look. |
| 5 | A cross-host correctness witness for the fast path | Portability evidence, not worth delaying the interactive path unless a cross-host failure appears. | The gate's court already runs on two hosts (Linux here, the owner's Windows). A further host is deferred. |
| 6 | Benchmark regression recording | Protects a production fast path against performance regressions. | Once the fast path is in a live path. |
| 7 | A persistent worker pool (tread D) | Only if a host court shows thread creation is material. | Its trigger did not fire. |
| 8 | SIMD, structure-of-arrays and cache experiments | Candidate optimization courts: measure first. | Deferred; no gain is claimed. |
| 9 | GPU | A separate architectural branch, not the next CPU optimization. | Deferred. |
| 10 | Lean or SMT formalization | Assurance research, not a prerequisite for the renderer. | Deferred; see below. |
| 11+ | Homotopy type theory, category theory, quantum-inspired work | A research track, not the production roadmap. | Not on the route. |

The sequence is therefore BEARING-FAST-0's host court → promote or defer → SIM-TICK-0 → mouse-look → PRESENT-1 → drift
and regression evidence. The optimization staircase reopens only if a court misses its target. The trap to avoid is
optimizing a renderer that has already crossed its threshold while the actual experience (mouse timing, simulation
ticks, presentation, input to photon) stays unmeasured.

Three rulings on how claims are made:

- **No scalar scorecard.** A letter grade collapses things this repository keeps apart: deterministic correctness,
  mutation resistance, portability, host performance, presentation latency, maintainability and research maturity.
  Each claim keeps its own grade from the existing vocabulary (MEASURED, ESTABLISHED, DECLARED, DEFERRED) and its own
  `does_not_show`.
- **Outside estimates are not Verðandi's claims.** Projected gains from outside analyses, such as a "3–5× ceiling",
  "SIMD 25–50%", "GPU 10–100×" or "world-class", are hypotheses attributed to their sources until measured here. Those
  analyses are not carried in this repository.
- **Formal methods, if opened, start narrow.** A months-long mechanization of the whole studio is a research
  investment, not the next rung. The existing court (1,972 cameras, checked bounds, 14 mutations, the host speed court,
  and the live differential check to come) finishes its job first. The natural first theorem is the seam BEARING-FAST-0
  created: for every admissible row, camera and scene, the exact walker produces the same pixel inputs as the reference
  kernel.

---

## The sequenced path (named rungs only)

### LATENCY-1 — does the headroom survive the present path · **measured and confirmed** (`8e93118e`, amended `b32d226f`)
Re-run the sealed reference session through the present path *now that the render is fast*, and compare frame-ready →
composited against `LATENCY-0`'s immutable baseline. This is a **measurement, not an optimization** — it was meant to
answer question 1; the amendment below records why it cannot, and LATENCY-1R does. Off-gate, host, witnesses first, no refresh claim.
The method is hash-locked (`latency1-preregistered`): the comparator is `LATENCY-0`'s sealed **frame-ready →
composited** p99 — the *same observable*, inherited never re-derived — and **never** an emit p99 (the GAUNTLET-2
7,734 µs baseline is a different observable; mixing them is a category error). The delta reads as
headroom-propagates / presentation-dominant / shell-contention, and none of it proves input-to-photon.

**Amended before the number (LATENCY-1a, `b32d226f`).** LATENCY-0's instrument renders every frame before its window
opens and times only blit → composited, so LATENCY-1 cannot see the renderer; its delta is now read as a statement
about the presentation interval only (a 50‰ materiality bound, declared), never as render headroom or contention.

**Measured.** On the owner's host LATENCY-1's first run read DEGRADATION on a three-sample p99 tail; its confirmation
read NO MATERIAL CHANGE (p99 7,339 vs 7,318 µs). The presentation interval reproduces LATENCY-0, and the first run's
category did not reproduce (`GHOSTS.md` G10).

### LATENCY-1R — the render inside the clock · **measured twice** (`5cfb3ece`)
The question LATENCY-1 cannot answer, as its own observable: render-start → composited on the same sealed session
and GDI present, for the production render (T=8) against the single-thread reference, in a locked and a uniform
phase regime. On the owner's host, two runs: **uniform PROPAGATES** both times (composited output 3.2–3.6 ms earlier
at the median; 1,341‰ and 1,182‰), and the **locked** regime absorbed in both (0‰ and 8‰ of a ~2.7 ms render saving
got through) — its preregistered label flipped from ABSORBED to PARTIALLY ABSORBED across a zero-margin boundary, which
the confirmation record states (`GHOSTS.md` G10). The production render-start → frame-ready interval itself is
14.8–15.7 ms at p50, longer than the 13.1–13.9 ms refresh.

### FRAME-SPLIT-0 — where the ~15 ms goes · **measured and confirmed** (`739dc807`): NO SEAT, multi-component
The production render-start → frame-ready interval split into seven contiguous phases on LATENCY-1R's apparatus, the
uninstrumented envelope beside it. On the owner's host (envelope p50 15.7 ms): blit 434‰ of the envelope p99, emit
272‰, frame 251‰, bgr 139‰, the rest under 10‰ each. No phase reaches 500‰, so **no single optimization is promoted**
— the frame is multi-component after GAUNTLET-2 (`GHOSTS.md` G8). The blit (`StretchDIBits` into the half-size window,
~7.1 ms p50) is the largest component, not a seated bottleneck; how much of it is the 2:1 scaling is unmeasured
(`GHOSTS.md` G11). The confirmation reproduced the reading (blit 427‰, every share within 8‰). Any further step is a
narrower, separately preregistered measurement of a named component, not an optimization.

### PRESENT-SCALE-0 — how much of the blit is the 2:1 scaling · **measured and confirmed** (`64b263da`): SCALING MATERIAL
A diagnostic, not an optimization court: the same frame presented into a half-size (960×540) and a full-size
(1920×1080) client area, the destination the only variable. On the owner's host the blit's p50 fell from 7.76 ms to
2.19 ms at 1:1 (717‰, net of the larger copy), the non-blit phases inside the confound bound (48‰), and the envelope's
p50 from 17.1 to 11.4 ms — below the refresh at full size, above it at half. The default stretch mode is
`BLACKONWHITE`, a Boolean-AND reduction (`GHOSTS.md` G11). It names no winner: what the shell should present is a
separate court, because it changes what the window shows. The confirmation reproduced it (705‰; non-blit 33‰), on
this host and apparatus. `PRESENT-1` below stays a hypothesis for the locked regime.

### PRESENT-STRETCH-0 — does the half-size blit's cost depend on the stretch mode · **measured twice** (`f5372890`): `COLORONCOLOR` MODE MATERIAL reproduced; `HALFTONE` not reproduced
A diagnostic over the same half-size frame, with the stretch mode the only variable: `BLACKONWHITE` (the default, now
set explicitly), `COLORONCOLOR` and `HALFTONE`, in 12 blocks with the effective mode read back. Per mode against the
default it reads MODE MATERIAL or IMMATERIAL (100‰ of the default's blit), unless the court is VOID or that mode is
CONFOUNDED. It adopts no mode: each draws different pixels, so choosing one is a separate court. On the owner's host
the blit's p50 was 7.27 ms under the default, 4.42 ms under `COLORONCOLOR` (392‰ cheaper) and 4.93 ms under
`HALFTONE` (322‰ cheaper), with the non-blit phases inside the confound bound (16‰, 15‰). The confirmation, in a run
that was slower across the board (the default's blit 11.59 ms), read `COLORONCOLOR` MODE MATERIAL again (449‰) and
`HALFTONE` CONFOUNDED (non-blit 53‰). So `COLORONCOLOR` reproduced per mode, `HALFTONE` is unresolved, and the combined
label did not reproduce, which the confirmation record states. No millisecond saving is carried as confirmed.
frame-ready → composited rose by most of the saving in the first run (G7), so this is not an end-to-end result.

### ALLOC-REUSE-0 — how much of the frame is per-frame buffer allocation · **measured and confirmed** (`aaaada37`): ALLOCATION MATERIAL (reuse cheaper)
A diagnostic over FRAME-SPLIT-0's apparatus with the buffers' lifetime the only variable: allocated every frame (the
production path) or once and overwritten, the same calls and marks, the reused bytes proven equal first. On the
envelope it reads ALLOCATION MATERIAL or IMMATERIAL (50‰ of the fresh envelope), with the per-phase deltas beside and
never ruled on. The production path is unchanged by it. On the owner's host the envelope p50 fell 1.59 ms (17.29 →
15.71 ms, 91‰), with the unchanged phases at 10‰. The confirmation reproduced it (17.36 → 15.53 ms, 105‰; unchanged
phases 2‰). In both runs the saving sat mostly in bgr and emit, which is reported and not ruled on. Adopting reuse in
the production path would be its own court.

### ALLOC-REUSE-1 — the render-loop entry's adoption court · **measured twice** (`dc904a6c`): PERFORMANCE PASS in both runs, ADOPT — **LOCKED** (seat 24)
The shipped shell has no per-frame render loop (`run` renders once, `playback-window` pre-renders owned frames;
G12), so what can be adopted is an **entry contract**: the persistent-buffer `LoopRenderer` as the production entry for
any loop that renders once per presented frame. The fresh path stays the frozen reference. Correctness first, on every
gate: byte identity with the fresh path over the corpus (goldens), the adversarial cameras and the sealed session, in
three orders from poisoned buffers, with no buffer replaced. Then performance, on the host: same-run ABBA, 1000 samples
per cell, PERFORMANCE PASS iff p99(reused) ≤ 950‰ of p99(fresh) (an adoption margin). ADOPT only when the run and
`--confirm` both pass. No shipped window changes either way; a later live loop enters through the adopted entry. On
the owner's host reuse's envelope p99 was 886‰ and then 929‰ of fresh's (−2.0 and −1.8 ms), with correctness holding on
every sample, so the reading is **ADOPT**. The second run was 41% slower as a whole (G13), and in both runs the frame
waited longer at the composition by about what it saved (G7). **ALLOC-REUSE-1 LOCK** carries out the ADOPT:
`LoopRenderer` is the production entry for in-loop rendering, and every fresh render entry's call site in the shell is
pinned (`allocreuse1-lock`), so the live loop renders through it. Nothing that ships today changes.

### HOST-STATE-0 — the host's state beside a court · **landed** (`58250382`)
Record, don't control: what the OS reports about the CPU, power plan, load, memory, process, display and uptime, one
snapshot just before and one just after a court's window run. Every value is an integer or a string, a field that
fails is recorded as unavailable, and recording can never block a court or feed a rule. ALLOC-REUSE-1 is the first court
to carry it. It exists to make the next cross-run drift explainable (the +59% in PRESENT-STRETCH-0's confirmation had
nothing to be set beside), never to explain it by itself. Its first snapshots put memory pressure (96% load, 359 MB
free) beside ALLOC-REUSE-1's slower second run, with the same reported clock state and plan in both runs: an
association (G13), not a cause.

### PRESENTATION-CHOICE-0 — what the shell shows · **declared** (`4a7a32d9`)
The owner's decision: the certified picture, 1:1 (the kernel's 1920×1080 composite, pixel for pixel), in a borderless
window covering the 1920×1080 screen at (0,0). No reduction by GDI or the kernel, and no new VIEW law. The half-size
windows stay as LATENCY-0's frozen instrument, and a conforming presenter is locked after PRESENT-EXACT-0.

### PRESENT-EXACT-0 — which GDI call presents it, with the screen read back · **measured twice** (`bc910e2f`): screen exact, SetDIBitsToDevice adopted
StretchDIBits at 1:1 against SetDIBitsToDevice, the call the only variable, frames through the adopted
`LoopRenderer`. The composed screen under the window is read back and must equal the certified picture byte for byte,
after a white clear that is also read back, as a hard gate. The first check of what reaches the screen rather than
what is handed to GDI (G11). Then same-run ABBA at 1000 per cell. StretchDIBits is adopted only if its p99 is ≤ 950‰ of
SetDIBitsToDevice's in both runs; otherwise SetDIBitsToDevice, the simpler semantics. The first host attempt refused
at the readback. A probe traced it to the host's performance overlay, a translucent bar drawn over every window.
Outside that bar, frame 0 read back exact under both calls. With the overlay off, both runs read the composed screen
back exact on all checked frames (20 checks, 0 differing bytes) and read NO MATERIAL DIFFERENCE between the calls
(StretchDIBits at 1,006‰ and 1,013‰ of SetDIBitsToDevice's p99). So SetDIBitsToDevice, the simpler call, is adopted. At
1:1 the call costs about 1.8 ms, and the frame's envelope (about 10 ms at p50) sits below the refresh.
**PRESENT-EXACT-0 LOCK** (seat 25) ships it: `shell show` and `shell show-playback` present the certified frames 1:1
through SetDIBitsToDevice, read the screen back after every present, report any mismatch, keep showing, and exit 3 if
the screen ever differed.

### REFUSAL-WHY-0 — why a readback refused · **landed** (`15701718`)
When the screen read back differs, the refusal now names what lies above the window over the differing box: each
visible, uncloaked top-level window above ours that meets it, with its program, process, class, title and overlay
styles, or "below the window layer" when none does. It is appended after the verdict is decided, it reads and never
acts, and it cannot change a verdict. The first host refusal needed a separate probe run and the owner's knowledge to
be traced to an overlay. The next one names its candidates itself. A candidate is not a cause.

### HOST-STATE-1 — the reported clock and paging · **landed** (`b992d9dd`); first host look taken; no court records it yet
Version 2 of the host snapshot: HOST-STATE-0's fields unchanged, then the clock the OS computes (% Processor Performance
and % Processor Utility, uncapped, with the nominal × performance estimate) and the system's paging rates, each over a
1000 ms window. Version 1 stays the default, so no existing court's records change. It fills the two gaps G13 left: a
reported MHz that cannot show boost, and memory pressure with no paging witness. A court records it only by its own
preregistered entry. Still association, never cause. The first host look read every counter, with performance at
118.5% of nominal (boost now visible) and 1 hard fault/s at 94% memory load. Processor Frequency read 1,658 against a
2,000 maximum, so the entry's "nominal" gloss is not established, and neither is the meaning of the estimate built on it.

### REFUSAL-LOG-0 — refusals that accumulate · **landed** (`424b7c9a`)
Every refusal on the present path (the PRESENT-EXACT-0 court's and the locked presenter's, and every differing screen
readback in `show`) appends one unsealed JSON line to `build/refusals.log`: run, sequence, operation, reason code,
attribution token and context. A console line reports a refusal once. The log turns a recurring refusal into a count
across runs (`python verify/refusallog.py`). It is an observation, never evidence: not sealed, not committed, read by
no rule. The gate proves on the mock court that each refusal leaves exactly one record and each record one refusal.
Since REFUSAL-WHY-1, a screen-readback record also carries what covered the screen (below).

### RUN-LEDGER-0 — the runs, refused or not · **landed** (`ecf3fdb9`)
The refusal log's denominator: one unsealed line per court or presenter run, whatever its outcome, in its own file
(`build/runs.log`), with the run's readback counts, its refusal count and its exit code, joined to the refusal log on
`run_id`. A clean run is counted too, so a recurrence can be stated as "refused in N of M runs". It is an observation,
not evidence, and it is kept out of the refusal log, which holds only refusals.

### REFUSAL-WHY-1 — what covered the screen, accumulated · **landed** (`ac75db51`)
A screen-readback refusal record now carries the covering layer and, for each window above ours over the differing
box, its program, class, overlay flags and rectangle. Titles and process ids are never written, and the rectangle is
geometry, not identity, so recurrence is counted by program, class and flags. The console and the log come from one
walk. A recurring program over the screen is a candidate, never a cause.

### LIVE-LOOP-0 — the first per-frame loop · **measured on the host** (`65550cc0`): the first live walk exact
The sealed session walked live: 24 compositions per step and 150 held, every composition rendered through the
`LoopRenderer` from the current step, checked against that step's verified bytes and presented by SetDIBitsToDevice in
the presenter's borderless window. The screen is read back at every step and twice in the hold, and a differing screen
is counted and logged, never hidden. There is no input, no camera, no clock: counts only. The gate executes the loop
itself over the mock. On the owner's host, the first live walk rendered and presented 246 compositions, and all 6 screen
readbacks were exact. It is the first gate on the route; the authoring input that changes the state is LIVE-INPUT-0's.

### MOUSE-LOOK-0 — a real mouse on the locked tick rules · **built** (`60870497`): the gate passes on the host; a real mouse turns the camera there (the second run, under MOUSE-LOOK-0a)
The fourth rung of the owner's ladder: real mouse → 64 Hz accumulator → command → the existing live loop. By the
owner's ruling it is a new entry, `shell look-window` (and `shell look-selftest` on the mock), on the same loop
function, session, journal and seal; `shell live-window` and every earlier command stay as they were and are given no
tick source. The rules are SIM-TICK-0's and SIM-TICK-0a's and are not touched. What this rung adds is the clock (an
input's tick is the tick of the composition that drained it), the mouse (Windows raw input, the relative horizontal
count and nothing else), the capture (the cursor hidden and confined while the window is in the foreground, released
when it is not, and never an event in the session), and the loop presenting a free heading: the session's own render,
the one its witness came from, with no overlay and no second render. The screen is read back one composition in 75,
and the reference recomputes one free-heading frame in 64 on a worker thread, a difference refusing the run; the save
still recomputes every one. The gate runs the loop over a mock mouse, keyboard, focus and clock: the saved data is
byte-identical to the windowless tick run's on the same inputs at their drain times; a window out of the foreground
changes nothing in the session; the picture handed to the call is the kernel executable's; a defective fast path is
refused by its first sample. No latency is claimed anywhere. 64 ticks against 75 compositions repeats about 11
compositions in 75, and they are counted in every saved session.

On the owner's host the gate passed with the same 207 rows and rowset, the window build compiled, and
`shell look-window` ran once. The window held the foreground throughout, the mouse was captured and released once, 48
key presses were stamped by the window's clock and applied on the tick (47 events), 1,826 compositions of the
composite were byte-checked with 25 screen readbacks exact, and the session saved and verified. What the run did not
show is a look: no mouse report reached the loop, the heading never left north, and so no free-heading picture, no
sample and no free-heading certification happened on the host. The record cannot say why, because the window section
counted nothing before the point where it admits a report. The run also found that Esc destroys the window in the
pump that reads it, so the saved file labelled the run's end `closed` where the tick run says `escape`; the session
itself is right. The owner ruled that a registered limit's wording be corrected by an amendment (MOUSE-LOOK-0a), that
the one check with no row stays a sanity check, and that nothing is optimized from this run.

### MOUSE-LOOK-0a — the timing limit corrected; a run's end and the window's observation · **built** (`3778b592`): the gate passes on the host; the second host run is the execution witness
An amendment to MOUSE-LOOK-0, whose entry is not edited, registered after the first host run and reading none of its
counts. By the owner's ruling the registered timing limit is corrected: a composition applies at most one closed tick
command, `span` records the largest number of tick boundaries between consecutive compositions, and a span above 1
means the loop fell behind the tick schedule, not that several commands were applied. From the host run: Esc destroys
the window in the pump that reads it, so the loop ends there, the tick still open is applied, and the run is recorded
as ended by escape; the mock now closes its window at an Esc as the host's does. And the window section counts every
raw input message before it reads it, every read that was not a mouse report and every report with no horizontal
count, and the run prints that observation, because the first run could not say whether raw input had arrived at all.
The read itself no longer requires an exact size. Nothing is optimized from the first run.

On the owner's host the gate passed with the same 209 rows and rowset, the first run's session was sealed (holding no
look), and `shell look-window` ran a second time. The observation adds up: 14,867 raw input messages, 13,931 of them
relative reports with a horizontal count and all admitted, none unread. They became 1,761 looks, at most one a tick;
with them 14 moves, 57 sensitivity changes across multipliers 1 to 14 and both steps, and a held W walking once a
tick. The window left the foreground once and came back, the mouse released and recaptured, and the session holds no
event of any kind for it. Of 4,649 compositions 4,541 presented the session's own picture; 62 screen readbacks, none
differing. The reference agreed at all 27 samples during the run and at all 1,775 free-heading frames at the save,
and the workshop built in the container recomputes those 1,775 frames from the saved file and reaches the same head:
the production tread on Windows, the reference kernel on Linux. Esc ended the run, recorded as `escape`. The owner
sealed the session on his host (`livesession-DANIELDILLBERG-b28e42be62c4.json`). Counted and
not interpreted: 4,649 compositions against 5,470 ticks, 2,852 repeating the picture before them, a span of 6. The
run does not decide why the first run had no mouse report. No latency is claimed. The owner's report of the run: the
look worked, and only horizontally. That is the registered scope (the carried camera turns in heading alone, and the
936 raw reports with no horizontal part were counted and not used); a camera that looks up and down has no frozen
oracle yet and is not on the route until the owner rules it there.

### SIM-TICK-0a — sensitivity as a typed configuration event; held keys by the tick · **built** (`471f4d72`): the gate passes on the host
MOUSE-LOOK-0's court (2026-10-02) gave four rulings. Two are about the window and wait for it: the mouse is captured
until Esc, and that capture is shell state that never enters the session, so a focus change makes no event; and every
64th free-heading frame is recomputed by the reference off the loop. The other two are rules of the tick, and the
owner's own separation (rules first, with no window in the proof) puts them here, in an amendment to SIM-TICK-0 whose
entry stays unedited. First, a sensitivity change is a typed configuration event: PgUp, PgDn and Tab are the physical
binding, their effect is what the session records, and it takes effect at the next tick. The event carries the
configuration after it and its tick, has no witness and is not folded, because the head is the worldline's and a
setting is not part of the world; the session replays the configuration by one legal transition at a time, and a
look's inputs must carry the configuration in force. Second, HOLD-WALK-0's law takes the tick as its unit: a fresh
press always acts, the first repeat of a held key in a tick walks, later ones are coalesced and counted, and a repeat
of any other key is ignored. The gate drives both with scripts: the owner's own sequence (PgUp, mouse, Tab, mouse,
PgDn), eight forgeries each refused by both verifiers, a crashed run whose configuration comes back from its journal,
and a held walk whose saved data is byte-identical to the same walk pressed. Mutation testing found the configuration
row's first form unable to catch one removed check, and the row was strengthened before it counted. On the owner's
host the gate passed with the same 201 rows and rowset as here. One informal timing was taken there to size
MOUSE-LOOK-0: a windowless run of 640 looks took 13.26 s in all, 20.7 ms per look summed over the live render and
journal, the reference's recomputation at save and the saved file's replay. It bounds each of those and separates
none of them; it is an observation of one run, not a record.

### SIM-TICK-0 — the mouse-look rules as integer law, windowless · **built** (`dc1dddf2`): the gate passes on the host
The third rung of the owner's ladder, and deliberately half of the work: the owner ruled that the rules are locked with
no window in the proof, and that the real mouse comes after, as its own rung. The boundary is raw input → tick command
→ SESSION-WALK → authority. A tick is exactly 15,625 µs (64 Hz). A tick's mouse reports are summed and applied once, as
one look; then its keys apply in arrival order. The look's delta is counts × multiplier × step, in integers: the
multiplier a whole number from 1 to 64, the step 88 heading ids or 1. W, A, S and D step toward the heading's nearest
cardinal, ((k + 45000) div 90000) mod 4 with the tie clockwise, and never turn. The one live session gains one event, a
look, witnessed by the frame at the new heading: the facing kernel's at one of the four anchors, as before, and the
bearing kernel's anywhere else. A tick run saves each event's tick and each look's inputs beside the event; the tick
is recorded and is never authority. Live, a frame at a free heading is rendered once by BEARING-FAST-0's production
tread; at save every such frame is recomputed by the reference across threads, and a session is saved
reference-certified or not saved. The gate drives it all with scripted inputs and integer times: the laws are checked
exhaustively over the 360,000 heading ids against a Python re-derivation, one script exercises the boundaries and the
refusals, the saved session's frames are checked against the kernel executable and by the workshop's verifier, and a
shell with a planted defect in its fast path is refused at the save. One thing was found while building: an index
frame can be the same at two neighbouring headings, so a look folds its camera token together with its witness; the
registration was revised for that before it left the build machine. On the owner's host the gate passed with the same
197 rows and rowset as here. The window build, which the build container could only type-check, compiled there, and a
walk of 46 moves in the live editor rendered, presented and byte-checked 1,034 compositions with 50 screen readbacks,
none differing, and saved and verified as before. That walk held no look: nothing here reads a mouse, a clock or a
window, and nothing here says how it feels.

### BEARING-FAST-0 — the bearing camera made fast, held to the reference · **measured on the host** (`f0a9a57d`): the target met, the sweep exact
One rung with its staircase inside, as the owner ruled. The reference spent its time in per-pixel 128-bit division;
the fast path, `kernel/bearingfast.rs`, keeps the reference's traversal and walks the floor and the walls exactly in
64-bit integers instead: along a row the floor point moves by a fixed exact step per column at any heading (scanline
floor casting, made exact), and down a wall column the texture moves by a fixed step per row, with one 128-bit setup
per row or column. The frame and the picture are written in one row-major pass (tread A); tread B reads the floor from
the blocked layout LOCALITY-0 locked; tread C runs eight row bands on threads. Every tread is the reference byte for
byte at 1,972 registered cameras on every gate, also in a build with overflow checks on, and every narrowing from 128
to 64 bits is checked and bounded. On the owner's host a speed court keeps a tread only by its margin and names the
production candidate against the target, a p99 of at most 6,667 µs (half the 75 Hz refresh), and a sweep checks it
against the reference at every walkable cell at every whole degree. On the owner's host the gate passed with the same 189
rows. The speed court promoted A (7,042 µs worst-camera p99 against the reference's 59,901) and did not keep B (the
blocked floor did not pay single-threaded). It kept C over A's layout: eight row bands at 3,716 µs, under the 6,667 µs
target, so the staircase stopped there with D never needed. The sweep then checked that production tread against the
reference at all 622,440 frames, and every one was equal. Renderer time only; the next measurement on the route is the
present and the input path.

### BEARING-0 — the bearing camera carried, its reference kernel placed · **built** (`de19660f`): the gate passes on the host
The first rung of the owner's mouse-look ladder on this side. Urðr earned the turning camera as VIEW-YAW-0 and froze it
as `urdr-oracle-2`: a heading is an integer id in [0, 360000), millidegrees clockwise from north, naming one primitive
Pythagorean triple, so the renderer consumes exact rational directions and never an angle; the four cardinals are
anchors equal to the frozen frames. BEARING-0 carries the record and its table verbatim (`oracle/urdr-oracle-2.json`,
`oracle/bearing_octant.txt`) and places the reference kernel, `kernel/bearing.rs`, the tag's Rust placement with only
its visibility changed. The camera is (cell_x, cell_z, heading id), the id authoritative and never normalized; the table
is compiled in and refused if it does not match its pin. The gate recomputes every digest the record states from the
record alone, and the reference reproduces all 104 witnesses of urdr-oracle-2 bit for bit. At the four anchors it is
the facing kernel, and dropping the hypotenuse from the depth moves every non-anchor frame. It is the correctness court
for BEARING-FAST-0 and drives no window: the shell, `mantle.rs` and `fast.rs` are unchanged. Its speed (about twice the
facing kernel's single-thread time, measured off the gate here) is why mouse-look waits for the fast path. The owner's
rulings for the rungs after it, recorded in RUNGS.md, are a 64 Hz tick, W/A/S/D toward the nearest cardinal (ties
clockwise, never changing the heading), and an integer sensitivity multiplier on a step of 88 or 1 ids, saved in the
session. On the owner's host the gate passes with the same 183 rows and rowset as here. Its first run there failed one
row, `oracle2-frozen`, on a working copy of `urdr-oracle-1.json` checked out with Windows line endings before
`.gitattributes` existed. That hash was pinned in the docs and enforced by no row until this one. The file was
re-checked out and the row kept strict.

### HOLD-WALK-0 — holding a key walks the live editor; the world stays discrete · **measured on the host** (`c03260a2`): a held walk saved and verified
The live editor, `shell live-window`, now walks while a key is held. W, A, S, D and the arrows are the held keys: the
steps and the quarter turns, so holding A or D looks around. A held key's auto-repeat is bound as its move and appends an
ordinary move event, at most one per composition. Later repeats in the same composition are coalesced: counted, never
an event. A fresh press is never coalesced, and holding Space, Q, E or a class key acts once. The keyboard's repeat is
the only speed source: the shell keeps no clock, reads no key-up and carries no key state between compositions. The
gate proves the held set, the one-per-composition cap with its coalesced count, and that a held walk saves exactly the
data the same walk pressed would. LIVE-INPUT-0's and LIVE-SESSION-0's commands still bind no repeat. On the owner's
host the gate passes with the same 174 rows, and a held walk (31 repeats, each walked, every readback exact) was saved
and verified; pressed instead, the same walk reaches the same head. The owner judged held keys over the grid not to be
the free movement he wants, so that route item is open.

### LIVE-AUTHOR-0 — the thing authored is what the next frame renders · **measured on the host** (`9a3e4521`): tile classes painted live, saved, and resumed
The one live editor, `shell live-window`: LIVE-SESSION-0's durable loop under the authoring binding, which is
LIVE-INPUT-0's keys plus 1–5 for the tile classes wall0–wall3 and floor. A class key paints its class with the next
colour of a registered 8-colour palette, read from the session's own M, as one `tile:CLASS,R,G,B` session event. It is
commit-only: nothing is shown before the edit is appended, and the shell holds no colour of its own. The frame witness
does not see colour, so the picture is witnessed per state by the reference composite's sha256. The gate proves the
camera control condition (a turn changes the pixels while W and M stay the same) and its converse (a tile edit changes
M, leaves W alone, and changes the pixels exactly when its class is on screen). It also proves the painted world
persists: a resumed session's first picture is its parent's last. On the owner's host the live editor walked, resumed a
saved session and saved a verified continuation. A later walk painted all five classes live: 28 tile edits by class
keys, each the palette's next colour, every one of 62 readbacks exact. It was saved and verified there, and here its
file verifies unchanged. The same presses replayed here reach the same head, and the level's bytes are unchanged by
the edits. The painted session was then resumed on the host as LOAD, walked and painted further (two more edits),
and saved as a verified child whose lineage names it, every readback exact.

### LIVE-SESSION-0 — the live session made durable and recoverable · **measured on the host** (`70086a72`): a saved walk and its resumed continuation
LIVE-INPUT-0's loop, unchanged, over a session whose every appended event is journaled: one record per line with its
length and sha256, each flushed before it counts. Esc seals the session in the workshop's own session-walk format by an
atomic replace. The shell then reads the file back and verifies it before the run counts as saved; a seal that fails is
a refusal, never a quiet exit. `--resume` continues a saved session, or recovers a crashed run from its journal, into a
new file whose log begins with its parent's. Loading checks integrity, then the renderer identity (a hash of the render
sources), then replays and classifies: an identity mismatch alone is never corruption, and only replay decides. Saved
sessions live in `build/sessions/` (gitignored). `verify/livesession.py` seals one as a committed record that shell
playback and the workshop both replay. The keyboard-focus observation is recorded, never ruled on. On the owner's host
the first saved walk (37 events, 4 of them edits, every one of 99 readbacks exact) was saved and verified there. Its bytes
verify unchanged on another machine through the workshop's own sessionwalk, with the same renderer identity. It was
then resumed and walked on (197 more events, ended by Esc) into a new file whose lineage lies on its own chain, and the
parent was untouched. A crash recovery on the host is still to come.

### LIVE-INPUT-0 — key presses feed the session the live loop renders · **measured on the host** (`f81c2cf1`): the live session walked and edited by key presses
Walking plus open/close. Arrows or WASD walk and turn, Q and E strafe, Space opens or closes the cell one step ahead of
the camera (rock to floor, floor to rock; a stair is not toggled), Esc ends; an auto-repeat is never bound and any
other key is ignored. Every press becomes an event in an in-memory SESSION-WALK log, validated as the workshop
validates it. W, M, the camera and the head are that log's replay, private to the session, so the shell never writes
the world. Every composition is rendered through the `LoopRenderer` from the session's current state and presented,
and the screen is read back after every change. The gate proves the binding on two key scripts and replays each
script's log through the workshop's own SESSION-WALK to the state and head the loop reached. Nothing is saved; that is
LIVE-SESSION-0's. On the owner's host, key presses walked the live session and opened and closed cells in it. An
opened cell was walked through and a closed one blocked, Esc ended the session, and every screen readback was exact.
Each walked log, replayed through the workshop's own SESSION-WALK, reached the head the loop printed. The deciding walk
was fixed beforehand as the gate's script A. It diverged at one press (S typed for Space), so its predicted head was not
reached; the walk as typed replays exactly. A refused edit was not exercised on the host. In the first run no key press
arrived, and why is not established.

### DRIFT-0 — variation within and between runs of the same workload · **preregistered** (`d445dcf9`); sitting 1 of 3 complete (4 of 12 runs)
Observational: the locked PRESENT-EXACT-0 court repeated without modification, 3 sittings of 4 completed runs (60 s
between runs, 4 h between sittings), with the owner's declared overlay state and HOST-STATE-1 before and after each
run. Refused runs are sealed and kept. The report is a panel: each run's p50, p95 and p99 per call, its within-run
spread and host state, and the between-run spread within and across sittings, with the two earlier PRESENT-EXACT-0
runs beside it as history. No verdict, no threshold, association never cause. It gives the next decision an empirical
basis for G13's drift.

### PRESENT-1 — decouple present from refresh (LATENCY-1R measured the coupling absorbing the render headroom in phase)
`LATENCY-0` *established* only that the composed-GDI present costs at least one refresh interval. `PRESENT-1`'s
falsifiable hypothesis — to be measured, never assumed — is that a **flip-model / waitable-swapchain** present can
decouple present latency from refresh. The prior art is well documented: the DXGI flip model shares frames directly
with the compositor with minimal copies, a frame-latency waitable object reaches ~1 frame of latency in Independent
Flip (and lets the DWM sleep), and `ALLOW_TEARING` with multi-plane overlay goes lower still. Built std-only against
raw Win32/COM (as `win32.rs` already hand-rolls GDI); off-gate; `HARDWARE-144` additionally needs a ≥144 Hz panel.

**Ordered after the live loop, and held as hypotheses until measured here.** The flip model's benefit is for a loop
that renders every frame, so PRESENT-1 comes after the live loop below and is measured on it, not on the pre-rendered
presenter. Until then, four things stay hypotheses for this shell. The borderless 1:1 geometry makes Independent Flip
*eligible*, which is not proof that Windows will use it. A waitable swapchain's latency is documented behaviour, not
evidence about this shell. A flip swapchain takes only 32-bit formats, so the blit-hash law needs a 32-bit carrier
first. And the screen witness must be re-established under the new path: the GDI readback is established only for the
GDI presentation it was measured on, and whether another capture path (for example Desktop Duplication) gives an
exact witness there is itself to be measured.

### Interactive capture — the inverse of SHELL-PLAYBACK
Raw window/device event → binding → typed action/edit → `SESSION-WALK` append → the *same* sealed representation that
headless authoring produces. `SHELL-PLAYBACK` already proves a sealed session replays to the exact window frames;
interactive capture closes the loop so a *live* edit produces a sealed session that would replay identically. A
shell/input problem, not a new authority — measured against the existing session machinery, never modifying it. The
industry pattern to borrow is the **authoring-data / runtime-data split** (e.g. Unity DOTS), with deterministic step
and reload atomicity — which is exactly the workshop's edit → authority → record shape. The live loop this needs is its
own rung (timing, cadence, ownership, input). ALLOC-REUSE-1 read ADOPT and is locked, so that loop renders through
`LoopRenderer` rather than deciding its allocation again. It presents through the locked 1:1 presenter's call and
reads the screen back as that presenter does. It is LIVE-LOOP-0 in the route above, ahead of PRESENT-1, and its first
court is kept narrow: the loop itself, without live editing, input, the flip model or latency claims. After it, and
after any change of presentation path, the frame's breakdown is re-measured rather than carried forward. Interactive
capture itself is LIVE-INPUT-0 through LIVE-SESSION-0.

### SEMANTIC-0 — a float-free, geometry-bound semantic layer
New VIEW semantics the studio did not inherit (filtering, variety) earned by a Verðandi-local reference pinned by
rows here, as the HUD's pins are — CORE semantics have one route only (Urðr, re-frozen). This is the rung that lets
the world mean *more* than the frozen oracle certified, without ever letting the shell mint that meaning.

### MERGE-0 — deterministic, consensus-free merge of non-conflicting edits
Combine two authored branches of a world with a merge that is commutative, associative and idempotent, **stripped of
consensus and wall-clock** — the join-semilattice discipline of conflict-free replicated data types, but applied to
an authored, hash-chained edit history rather than a live distributed store. The prior art (state-based and
delta-state CRDTs; deterministic lockstep simulation) supplies the convergence theory; the Verðandi constraint is
that the merge must produce a *sealed, replayable* history whose result is byte-identical regardless of merge order.

### LLM-BUILDER-0 — the living proposal machine · **declared** (the owner's goal, 2026-10-02); not registered, nothing built
The owner's stated goal for what a language model may be in this studio. It is recorded here before any of it exists,
so that the rungs built before it are built in respect of it. The law:

> **The model may propose becoming; only the verifier may admit it.**

The model is not a programmer inside the runtime. It is a proposal engine working against a sealed worldline, and it
stays outside canonical authority. Four things are kept apart:

```text
IMAGINATION    the model                  "what could change?"                 untrusted
ADMISSIBILITY  the verifier               can refuse; never proposes
AUTHORITY      the session, the workshop  the admitted event, in order
CONSEQUENCE    the kernel, the reference  the frame and the digest it produces
```

```text
model ──► PROPOSAL (typed, bounded, anchored) ──► VERIFIER ──► refuse
                                                      │
                                                  admissible
                                                      ▼
                         SESSION EVENT ──► ordered replay ──► candidate W, M
                                                      │
                                              reference witnesses
                                                      ▼
                                                   COMMIT ──► the new worldline
```

- **A proposer, not an authority.** The model's output is a typed proposal: a target, an operation, its parameters, the
  session head and the authority digest it was made against, and its provenance. It may say "at this exact worldline,
  open cell (28,27)", and later "create a corridor generator with these declared parameters". It may never say "here
  is some code; run it inside the renderer". Arbitrary live code is not the primitive. That distinction is what keeps a
  second authority out.
- **The worldline anchor.** A proposal is born at a session head, an authority digest, a renderer identity and its own
  digest. It proposes what, from exactly here. If the live session has moved on before the proposal is admitted, the
  verifier does not guess whether it still applies: the proposal is rebased explicitly or it is refused. There is no
  silent merge across time. A proposal has no authority until its ancestry is proven.
- **Speculation is an object.** A preview is not a hot swap. It is a speculative worldline: a candidate authority
  replayed from the proposal's anchor, rendered as much as is needed, and never touching the live world. One preview
  frame serves interaction and certifies nothing. Certification asks for the witness set the proposal's kind calls
  for: the authority's validity, targeted falsifiers, the reference's frames, replay from the anchor, exact digests
  where they apply. Only then does the branch become history.
- **The prefix is sacred.** The model appends becoming. It never rewrites what has become. The sealed history is a
  prefix of every continuation; a stream of events is concatenated, never permuted.
- **The commit envelope.** An admitted proposal is recorded with more than an action: its id, the parent head, the
  base authority digest, the proposal's digest, the operation and parameters, the provenance, the verifier's identity,
  the verification witnesses, and the resulting head and authority digest. The model's text is provenance, not
  authority. The authority is the verified typed event, so the session replays the same with the model gone.
- **How it grows.** From "turn this cell into a door" to "generate a corridor", to "author a new material", to
  "propose a new deterministic gameplay mechanism". Each step asks for stronger verifier laws. None gives the model
  more privilege in the runtime.

The sentence the owner would put in the charter: **Verðandi does not execute what the model writes; it records what
the verifier admits.** It stands beside the charter in the README as a declared goal. The ratified charter block is not
edited.

### LLM-BUILDER-0, continued — program time and content time; the design-event stream · **declared** (the owner's, 2026-10-03), and by his ruling what the route builds towards; not registered, nothing built
Two design texts the owner brought on 2026-10-03 and asked to have recorded. Both are replies to his own description
of what he is after, so their wording is quoted where it states the rule and summarized elsewhere. They extend
LLM-BUILDER-0 above and change nothing in it. Nothing here is built, and no rung is seated by it.

**The owner's ruling (2026-10-03): this is what the studio builds towards.** He brought the two texts again with
those words. That makes them the route's destination and not only a record. It seats nothing by itself: each rung
towards it is still chosen in its own court, registered before it is built, and held by rows. The four rules listed
at the end of this section still want their rulings first.

**1. The gate certifies the program. Content is admitted, not gated.**

> **The engineering gate certifies the program. The content admission layer certifies that an artifact conforms to
> the already-certified program. Content generation does not invoke the engineering gate.**

```text
PROGRAM TIME    source ──► GATE ──► certified build            runs when the program changes
─────────────────────────────────────────────────────────────────────────────────────────────
CONTENT TIME    prompt ──► proposal ──► CONTENT CHECK ──► admitted artifact ──► the certified runtime
                                                                        runs when the world changes
```

- **`GATE`: engineering certification.** It answers questions about the program: is the kernel deterministic, does
  replay reproduce, does authority stay apart from presentation, does the fast renderer equal the reference, do the
  seams hold. It runs when the kernel, the renderer, the authority, the session's semantics, the workshop's
  semantics, an optimization or the shell's architecture changes: a targeted gate, then the full gate, then a
  certified build.
- **`CONTENT CHECK`: artifact admission.** It answers questions about one piece of content: is its form valid, are
  its coordinates in bounds, do the things it refers to exist, are its constraints satisfied, does it load without
  breaking the runtime's contracts. It runs when the world changes: a new landscape, a building, a material set, a
  generated scene. It is meant to be fast, and it does not rerun the architectural certification.
- **What a model may do.** In the text's words: *AI may generate content freely, but it may not redefine the laws
  under which content executes.* A model asked for a landscape produces a bounded content description. It does not
  write kernel code. A change to the laws is a new program build, and that is the gate's business, not content
  generation.
- **Why it is written down now.** Without the line, new features leak content generation back into the expensive
  certification loop, and the verification architecture becomes the bottleneck of creation. The text's phrase: the
  engineering gate is *the constitution of the design environment, not the toll booth every time someone creates a
  mountain.*

**2. Conversation as the editor, over a semantic world-edit stream.**

> **Language can propose. The verifier admits. The session records. The kernel renders.**

```text
human ──► LLM designer ──► intent ──► design IR (a bounded world diff) ──┬──► speculative branch ──► fast preview
              ▲                                                           └──► verifier ──► admitted DESIGN EVENT
              │                                                                                   │
        world context (queried, bounded)  ◄──────────────  world authority  ◄──  SESSION  ◄───────┘
```

- **Intent, not code.** The model translates "make the valley narrower, raise the cliffs, put a road through the
  bottom" into typed operations on named targets. It designs transformations. It is not the authority that executes
  them, and it never edits files or reloads a renderer.
- **A spatial vocabulary.** The model does not think in files or pixel coordinates. The world offers regions,
  features, materials and structures by name, and an instruction becomes a relationship between them (above, facing,
  within a distance), which the verifier resolves.
- **Persistent identity.** Every generated object has a stable name, so "move the tower I added earlier" names one
  thing, across hours of conversation.
- **Every action a reversible transaction.** An edit carries its parent world, the intent, the proposed diff, the
  objects it touches, the resulting world and a preview frame. Undo is another event, a semantic inverse or a
  compensating edit; nothing is rewritten.
- **Preview before authority.** A proposal's first result is a speculative branch, fast and disposable. Only "keep
  it" appends it to the authoritative session. Preview is not authority.
- **Three speeds.** The fast path (prompt, proposal, diff, speculative projection, render), the commit path (accept,
  typed session event, authoritative world, save), and the engineering path (source change, gate, certified
  program), which is rare. Hundreds of accepted edits never invoke the gate.
- **A world microscope.** The model can query bounded context (the camera, a region, an object, a material, its
  neighbours, recent edits), so a proposal is made from the world's actual state and not from the words alone.
- **Why did you change that.** Every edit keeps its intent, its proposal, the operations accepted and refused, the
  objects affected, the parent and resulting digests and the model's provenance. The answer comes from that record.
  The world's provenance is authoritative; the model only reads it.
- **The design event.** An `AI_PROPOSAL` never mutates authority. It goes to the verifier, and what the verifier
  admits is a design event in the session, beside edits, moves and looks.
- **Branches.** "Three versions of this coastline" are three branches of one world, each previewed. "The cliffs from
  B, the vegetation from C, the road from A" is an explicit merge of typed events.

The endpoint the text describes is a creator who says what a place should be and watches it change, and never thinks
about source files, compilation, hashes, verification scripts or restarts, while every accepted change underneath is
typed, bounded, provenanced, reversible, deterministic and replayable. Its last line: *a world can be continuously
invented without continuously rebuilding the machine that knows how worlds work.*

**What already stands on each side of the line.**

- **Program time.** The gate is `verify/verify.py`. It runs when a patch lands in the repository. No session event has
  ever invoked it.
- **Content time, as far as it exists.** A live session is content: typed events over W and M, appended by keys and
  a mouse. On the owner's host one run appended 1,832 events with no gate between them. A saved session is admitted
  by checks on the artifact alone: its seal, its base, the fold of its witnesses, and its replay by the shell, the
  workshop and the sealer. That is the studio's content check today, for the one kind of content it has.
- **What LLM-BUILDER-0 already declares.** The typed, anchored proposal; the speculative worldline; the sacred
  prefix; the commit envelope; no silent merge across time.

**What does not exist.** A model in the tree. A proposal format. A verifier for proposals. An intent compiler or a
design IR. Regions, features, structures, vegetation, heights or any named object: the world is a grid of cells (W)
and five tile classes (M), and the renderer draws exactly that. Object identity. Branches, previews or merges. A
content package, or a check for one. The examples in the texts (a valley, cliffs, a coastline, a village) are far
beyond what the frozen oracle certifies.

**Where it meets rules already in force.** Each of these wants the owner's ruling before a rung is seated.

- **Commit-only.** LIVE-AUTHOR-0 forbids showing a change before it is appended, and this roadmap keeps previews and
  gizmos off the route because that is where a shell starts to hold an alternate authority. A preview is admissible
  only in the form LLM-BUILDER-0 gives it: a speculative worldline, itself a typed log replayed from an anchored
  head, never state the shell holds.
- **Earn the authority.** Terrain, heights, vegetation and structures are new CORE semantics. By the rule below they
  come only from Urðr, carried or earned there and re-frozen. A content vocabulary cannot be minted here.
- **How light a content check may be.** Today a session at a free heading is saved only after the reference has
  recomputed every one of its frames. A lighter check for new content kinds has to say which witnesses that kind
  needs, as LLM-BUILDER-0 already asks, and may not become a second, weaker verifier beside replay.
- **Merging branches.** A merge is an explicit, typed, anchored event, or it is refused. There is no silent merge.
- **The charter.** The first text says this boundary should become a charter-level rule. The ratified charter block
  is not edited. The rule stands beside it in the README as declared, and ratifying it is the owner's to do.

**What it would stand on, already built.** Each of these is a rung with rows, and none was built for a model.
WORKSHOP-1's session has `propose` and `commit`: a proposal is validated against the current authority and writes
nothing, and a refused one leaves the log and the head unchanged. WORKSHOP-0 refuses a record whose projection is
stale under a moved authority. SESSION-WALK is one ordered log of typed events folded to a head, verified by replay
without its author. LIVE-SESSION-0 seals a continuation as a new file whose log begins with the parent's events, never
modifies the parent, and refuses a lineage that is not on the session's own chain; it also names the renderer
identity a session was made under. SIM-TICK-0 keeps what is recorded about an event beside it and out of the head (the
tick, the inputs), which is where provenance would sit, and it certifies a session with the reference before it saves.
The carried game layer's input membrane (GAME-0, `cue`) proves its binding is a homomorphism over concatenation, with
refusal atomic for a batch: appended streams compose, and nothing there licenses reordering.

**What does not exist.** No model is anywhere in this tree, and none is a dependency. There is no proposal envelope,
no proposal digest, no anchor check against a live head, no rebase, no speculative worldline as an object, no verifier
law beyond the validation each edit already gets, and no vocabulary above a cell edit, a tile edit, a move and a look.
MERGE-0, above, is still unbuilt, and an explicit rebase would lean on it.

**What it asks of the rungs before it.** These are constraints on the route as it continues, not new work. Every new
event kind stays typed, validated by the session before it is appended, and replayable without whatever produced it.
What is recorded about where an event came from sits beside the event and is never folded into the head. Nothing but
the session's own replay writes W or M. No rung adds a path that executes text.

**Grade.** DECLARED: all of it. Nothing here is established or measured. **does_not_show.** That a model can author
anything useful here; that any verifier law beyond today's edit validation exists; that speculation, rebase or the
commit envelope work; any safety property of a system that includes a model. When it is seated it registers its own
hypothesis, failure condition and limits, like every rung.

### ADMIT-0 — the admission seam · **built** (`bdd38593`): nine rows hold it on every gate; not yet run on the host
The first rung towards the design-event stream above. It was chosen in court, then researched, then reviewed by the
owner, then taken to a second and a third court on the questions the review left, and then registered. This section
records the first court, what the research found, one observation made here while checking it, the review, the
second and third courts, the registration and the owner's acceptance of it. It has since been built: what was
built, the nine rows that hold it and what they do not show are in [`verify/RUNGS.md`](../verify/RUNGS.md).

**The court (2026-10-03).** Three rulings.

- **The first rung is the admission seam.** Windowless. A typed, anchored proposal read from a file is refused or
  admitted by a verifier, and an admitted one becomes an ordinary session event with its envelope beside it. Only
  today's vocabulary: open or close a cell, repaint a tile class. No model in the tree. No gate at content time.
- **A stale anchor is refused, always.** The refusal names both heads. Rebase is a later rung. LLM-BUILDER-0 says a
  stale anchor is "rebased explicitly or refused"; this rung takes the second half only.
- **The charter: beside it for now.** The ratified block is not edited.

**What the research found.** The owner asked for a varied search for hardenings. These are outside sources and
attributed hypotheses, not claims of this repository; the links are under Sources below.

- **Recognition.** LangSec's rule is that input is a formal language, recognized completely before anything acts on
  it, kept as simple as the job allows, and read by equivalent recognizers at every endpoint. Bishop Fox's survey of
  JSON parsers found them disagreeing on duplicate keys, on invalid Unicode (two different keys collapsing into one),
  and on numbers too large to represent, and advises a fatal error for each and never re-serializing input that was
  already validated. RFC 8259 itself only says names should be unique and calls behaviour unpredictable otherwise
  (section 4), and says the same of unpaired surrogates (section 8.2).
- **Binding.** A 2026 preprint on canonicalization failures (Brömme) names the class: a digest binds bytes while the
  system compares meanings, so one meaning with two encodings, or one encoding with two meanings, breaks the binding.
  Its rule is one accepted form, with the others refused and not normalized. Trail of Bits adds that hashed fields
  must be encoded unambiguously and that digests with different purposes carry different tags. RFC 8785 (JCS) gets a
  canonical JSON only by first requiring unique names and bounded numbers.
- **Authority.** The agent design-patterns paper (IBM, Invariant Labs, ETH Zurich, Google, Microsoft) and CaMeL
  (Google DeepMind) both constrain the system and not the model: what a model emits selects among actions a
  deterministic layer already permits, and never decides them. The de Bruijn criterion from proof checking is the
  same shape: anything may propose, and a checker small enough to inspect decides. JSONSchemaBench found
  schema-constrained decoding enforced unevenly across frameworks, and conformance to a schema is not validity
  against a world.
- **Agreement between implementations.** Fluffy (OSDI '21) found consensus bugs in Ethereum's most used client by
  running independent clients on the same adversarial inputs and comparing results. Independent implementations are
  an oracle when they are actually run against each other.
- **Anchors.** EventStoreDB appends against an expected version and refuses a mismatch, and its documentation says
  idempotence is not guaranteed when the expected version is waived. An event-store survey gives the same advice on
  conflict: refuse, and let the caller decide again from the new state.
- **Crashes.** ALICE (OSDI '14) found 60 crash vulnerabilities in 11 applications, among them Git, Mercurial and
  LevelDB. The recurring mistakes were assuming an append is atomic, assuming operations persist in order, and not
  flushing the directory. On Windows, Microsoft documents `MOVEFILE_WRITE_THROUGH` as a flush promise for a move
  performed as a copy and delete, says nothing there about atomicity, and marks `ReplaceFile`'s write-through flag
  as not supported.
- **Generated worlds.** A 2025 level-generation paper (Xu et al.) has the model write constraints in a small
  description language and a solver place the level, and still reports that not every generated level is valid in
  simulation. Agentic PCG shows its agents repeating failed edits before changing approach. Both separate proposing
  from placing, and neither repairs its way to a guarantee.
- **Not acted on.** Microsoft's raw-input documentation recommends buffered reads for high-frequency mice. The
  owner's ruling stands that nothing is optimized from the first host runs; this belongs to the latency rung.

**One observation made here (OBSERVED, outside the gate).** The saved form is read by a small JSON reader in
`shell/playback.rs`, byte-identical in `workshop/sessionwalk.rs` and `workshop/session.rs`. The sealer,
`verify/livesession.py`, reads the same files with Python's `json.loads`. The Rust reader was compiled alone from
its source lines and both were given 19 hostile inputs.

| input | the Rust reader | Python's `json.loads` |
|---|---|---|
| two equal keys | accepts, keeps the last | accepts, keeps the last |
| bytes after the value | accepts | refuses |
| a second object after the first | accepts the first | refuses |
| a leading zero (`007`) | accepts as 7 | refuses |
| a string ending at a backslash | panics | refuses |
| a `\u` escape cut short | panics | refuses |
| an escaped surrogate pair | accepts as two U+FFFD | accepts as one character |
| two keys differing in a lone surrogate | accepts as one key | accepts as two keys |
| a raw newline in a string | accepts | refuses |
| `\b` and `\f` escapes | refuses | accepts |
| an integer beyond 64 bits | refuses | accepts |
| a fraction (`1.5`) | refuses | accepts |
| `NaN` | refuses | accepts |
| a lone minus | refuses | refuses |
| empty input | refuses | refuses |
| a byte-order mark | refuses | refuses |
| a NUL byte in a string | accepts | refuses |
| 20,000 nested arrays | accepts | raises a recursion error |
| 2,000,000 open brackets | aborts on stack overflow | raises a recursion error |

The two differ on 12 of the 19. They agree on four, and on one of those, the duplicate key, both accept silently.
On the other three the Rust reader does not return a verdict at all: two panics and one abort.

**does_not_show.** That any sealed record or saved session is wrong. The shell writes the saved form itself, both
seal checks pin the file's last bytes, and the heads are recomputed by replay. The reader was run alone, not
through any command of the shell, so how a panic surfaces there was not observed; no panic hook was found in
`shell/`. The harness is not in the tree and no row holds any of this. It is where the reader court below starts.

**The owner's review (2026-10-03).** A reply to the research, brought by the owner and recorded at his instruction.
Its outside citations are its own and are attributed the same way. Its first line:

> **ADMIT-0 is the right first rung, but its first hardening should be parser unification, not merely a stricter
> JSON grammar.**

```text
proposal bytes ──► STRICT RECOGNIZER ──► typed proposal ──► ANCHOR CHECK ──► BOUNDED VERIFIER ──► DESIGN EVENT ──► SESSION
                        │ refuse                                │ stale: refuse
```

1. **One recognizer.** *Don't make three independent components parse the proposal language.* One admission parser
   turns the bytes into a typed proposal, and the verifier and the sealer receive that typed object and never the
   text. Three parsers that must agree is a permanent differential-parsing problem; one parser is one recognition
   boundary. Independent implementations stay as test oracles only.
2. **A language smaller than JSON.** Not "a JSON parser with a lot of security rules" but *a tiny world-design
   language with a formally bounded grammar*: an envelope and a bounded list of operations from a fixed vocabulary
   with bounded fields. The model's prose is metadata. The operation is what bears authority. The printable-ASCII,
   no-escape, no-leading-zero rules from the research are not locked as the architecture; the accepted representation
   of a purpose-built language is already canonical. JCS is not made the heart of it: *You control the admission
   language.*
3. **The anchor binds more than the head.** Program identity, renderer identity, session head and proposal schema.
   A proposal made against one head is never applied to another: no automatic rebase, no "close enough", no semantic
   merge hidden inside admission.
4. **Three identities.** `proposal_id` is this attempted admission. `proposal_digest` is these exact bytes. The
   session head is the authority it was proposed against. An admission record carries the id, the digest, the
   program and renderer identities, the parent head, the admitted event's digest and the resulting head.
5. **Typed refusals.** Not one "refused" but a reason: parse, size, depth, duplicate, unknown field, schema, range,
   anchor, program, capability, authority, duplicate proposal, I/O. A creator sees that an edit was not applied
   because the world moved while the model was writing it, and not that "AI failed".
6. **Proposal and admission are different objects.** The proposal is disposable. The design event is authoritative.
   Once admitted, the model's prose is irrelevant to authority.
7. **No filesystem capability for a model.** Not `write_file`, `execute`, `modify_source` or `shell`. A model gets
   `world.query` and `world.propose`, and perhaps later `world.preview` and `world.branch`. It describes a
   transformation, and only Verðandi turns one into an admitted event.
8. **The preview branch comes after admission works.** The order: `ADMIT-0`, then `DESIGN-EVENT-0`, then
   `LIVE-AI-EDIT-0`, then `BRANCH-0`. First prove prompt, proposal, admission, session, world, frame; then make that
   path disposable.
9. **Crash consistency belongs inside ADMIT-0.** After a death anywhere in an admission the session is exactly one
   of NOT ADMITTED or ADMITTED, never a half-state.
10. **Kill every boundary.** Proposal received, parsed, verified, anchor accepted, event materialized, event
    durable, session head durable, admission acknowledged. The process is terminated at each, and a restart finds
    the old head or the new head, never "I don't know".
11. **Capability bounds.** A proposal carries or inherits a scope: an authority, a region, a set of operations. An
    operation outside it is refused by the verifier however well formed it is. The enforcement sits below the model
    and is not a sentence in a prompt.
12. **Provenance attaches to the result.** An admitted event keeps its parent head, the proposal's digest, the
    intent text's digest, the proposer, the scope, the operation's digest, the resulting authority's digest, the
    renderer identity and a reference witness, so what changed, why, from which prompt and what the renderer showed
    are answered from the record and not from a model's memory.

**The courts the review registers with the rung.** They are part of ADMIT-0 and not rungs before it.

- **A. Reader court.** A hostile corpus: duplicate keys, unknown keys, trailing data, malformed UTF-8, invalid
  escapes, leading zeros, oversized numbers, excessive depth, oversized strings, an oversized proposal, truncated
  input, empty input, wrong types. Every one ends in a coded refusal and never in a panic.
- **B. Single-parser court.** The production parser produces the sole typed representation. Independent parsers
  are test oracles.
- **C. Anchor court.** The current head equals the proposal's parent head, or the proposal is refused. No rebase.
- **D. Capability court.** Operations outside the permitted vocabulary or scope all refuse.
- **E. Idempotency court.** The same proposal twice: the first is admitted, the second refused.
- **F. Crash court.** Termination at every admission boundary; recovery yields the old head or the new one.
- **G. Replay court.** The admitted event reproduces the exact resulting authority from the sealed parent.

The sentence the review locks:

> **The gate certifies the machine. ADMIT admits the world's changes.**

One correction the review makes to the research as pasted: `ReplaceFile` with its write-through flag is not to be
cited as the Windows durability mechanism, because Microsoft marks that flag unsupported. Checked here against
Microsoft's page: it does. The tree never calls `ReplaceFile`. Its replace is `MoveFileExW` with
`MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH` (`shell/livesession.rs`), which is the primitive the review
names.

**The second court (2026-10-03), for the registration.** Held after the review, on the four questions it left
for the registration. The owner's rulings:

1. **The proposal language is a line language, locked for ADMIT-0.** In his words, *the proposal itself becomes a
   canonical byte artifact, rather than something that must be canonicalized after parsing.* The registration
   freezes the field vocabulary, the order, the line count, the separators and the integer domains. No optional
   lines, no arbitrary ordering, no nesting, no quoted strings, no escaping, no whitespace normalization, no
   Unicode, no duplicate fields (a field occurs once, at its registered position), nothing before the first line and
   nothing after the last, and LF (`0A`) the only line terminator. There is no parse, normalize, canonicalize and
   hash; there is recognize or refuse, and

   ```text
   proposal_digest = SHA256(exact proposal bytes)
   ```

   - **Not a world language.** *ADMIT-0 should admit the admission envelope*, with a small registered vocabulary
     for its operation, target and value. It does not try to encode the future landscape-edit language.
   - **Versions.** The first language is `VRDNP1`, frozen. A later one is a new version (`VRDNP2`) with
     deliberately different semantics, never a change to this one. That keeps the edit language from growing into
     an unbounded small programming language.
   - **The model writes the language and does not interpret it.** Natural language, then a line-language proposal,
     then admission, then a design event, then the world; never natural language, then arbitrary JSON or code,
     then an interpreter.
   - **Why not the others.** A strict JSON subset brings duplicate keys, escapes, Unicode, numbers, nesting and
     canonicalization back for no architectural gain. A binary record is a good storage form and the wrong proposal
     form: it puts an encoder between the model and admission, which is another trust boundary in front of the
     seam. Binary may still become an internal or session representation later.
   - **What the registration must fix.** *The exact ABNF-like grammar, allowed tokens, integer ranges, byte/line
     limits, and one worked canonical byte example.* Changing any of them afterwards is a new language version and
     not an implementation change.
   - **His sketch, recorded as a sketch.** `VRDNP1`, then `program=`, `renderer=`, `parent=`, `proposal=`,
     `scope=`, `op=`, `target=`, `value=`, one per line. It is "something along these lines"; the registration
     fixes the actual lines. Two things in it meet other rulings: its `program=` line meets ruling 4 below, which
     mints no program identity, and its example operation (`TERRAIN_RAISE` on `west_cliff`) is beyond today's
     vocabulary, which is a cell opened or closed and a tile class repainted.
2. **The saved-form reader is hardened in its own rung, after ADMIT-0: `READER-COURT-0`.** The two are different
   trust boundaries. ADMIT-0 establishes a new language and its recognition rules; the saved-form reader is old
   infrastructure with an observed disagreement surface, and joining them would make the first admission rung carry
   an unrelated migration. `READER-COURT-0` gives the shell's reader, the workshop's and the sealer's one coded
   verdict on the hostile corpus and closes the observed cases by name: trailing bytes and a second object,
   duplicate keys, malformed escapes, a `\u` cut short, a string ending at a backslash, excessive nesting and
   stack exhaustion, the disagreement on accepted numbers and strings, and the surrogate collision. No panic and no
   process abort. The affected reader files are re-pinned once, in that rung, and not dragged through ADMIT-0's
   development. *First we create the new admission seam; then we harden the legacy persistence seam it must
   coexist with.*
   - **The order he locks.** MOUSE-LOOK-0, the LLM-BUILDER-0 declaration, `ADMIT-0`, `READER-COURT-0`,
     `DESIGN-EVENT-0`, `LIVE-AI-EDIT-0`, then branch and preview. This puts ADMIT-0 next after MOUSE-LOOK-0. Where
     the presentation and latency measurement, which the route above still lists, sits against this order was not
     ruled in this court.
3. **The admitter grants the scope.** The admit command takes the grant from whoever runs it. A proposal can only
   do less. The grant is recorded in the envelope, and the capability court tries to exceed it.
4. **The anchor's identity is what a session already records.** The renderer identity, the bearing identity, the
   session head and the proposal language's version. Nothing new is minted. A proposal goes stale when the head
   moves or the rendering sources change, and not when an unrelated file of the shell changes. The gate's rowset is
   not an anchor: it would tie content time to the gate.

**The third court (2026-10-03), on the frozen bytes.** The owner's sketch of the language had a `program=` line
and a `scope=` line, and the second court's rulings 3 and 4 took both away. Two rulings settled the lines.

1. **Eight lines, per the rulings.** `VRDNP1`, `renderer=`, `bearing=`, `parent=`, `proposal=`, `op=`, `target=`,
   `value=`. No program line, because nothing is minted. No scope line, because the grant is the admitter's and one
   operation per proposal leaves nothing narrower to ask for.
2. **The proposal id is the proposer's 64-hex handle.** Chosen by the proposer, carried in the bytes, untrusted and
   recorded. An id already in the session's admitted history is refused as a duplicate. The digest stays the SHA-256
   of the exact bytes.

**The registration (`bdd3859302f61b127c6df050cebf9ca521dc8bc2ca8a96e67b7f27150b39796d`).** Its own commit, with
nothing built. What it freezes, in `verify/preregister.json`:

- **The bytes.** Exactly eight lines, each ended by one LF, nothing before the first and nothing after the last.
  `renderer=`, `bearing=`, `parent=` and `proposal=` carry 64 lower-case hex characters. `op=` is `open`, `close` or
  `paint`. For open and close the target is `x,z` and the last line is exactly `value=0`; for paint the target is
  one of the five tile classes and the value is one integer, R×65536 + G×256 + B. Coordinates lie in 0..65535 and a
  colour in 0..16777215, with no leading zero. No other byte is legal. A proposal is therefore 327 to 337 bytes, each
  typed proposal has one byte sequence, and its digest is the SHA-256 of those bytes. The entry carries a worked
  example of 328 bytes and its digest.
- **What a proposal is checked against.** The renderer and bearing identities of the admitting shell; the head of
  the saved session as loaded (a stale parent refused, always, naming both heads); the ids already admitted in that
  session; the grant given on the command line; and the session's own validation of the edit, with one law added:
  a proposal that would leave W and M as they are is refused.
- **What an admitted proposal becomes.** The edit a key would make, with the head that edit gives. Its envelope
  (the language, the id, the digest, the two identities, the parent head, the resulting head, the grant) sits
  beside the event in the journal record and the saved item, travels with it through later continuations, and is
  never folded into the head.
- **Typed refusals, in a fixed order.** `ADMIT-IO`, `ADMIT-SIZE`, `ADMIT-PARSE`, `ADMIT-RANGE`, `ADMIT-PROGRAM`, the
  session loader's own, `ADMIT-SESSION`, `ADMIT-ANCHOR`, `ADMIT-DUPLICATE`, `ADMIT-CAPABILITY`, `ADMIT-AUTHORITY`. A
  refused admission leaves no run directory, no journal and no file.
- **The courts, as rows.** `admit-reader`, `admit-single`, `admit-anchor`, `admit-capability`, `admit-idempotent`,
  `admit-crash`, `admit-replay`, `admit-fence`, with `admit-preregistered` locking the entry.

Choices the registration makes beyond the rulings, each stated in the entry:

- One operation per proposal and one proposal per run. There is no batch.
- The review's parse, depth, duplicate-key, unknown-field and schema refusals are one refusal, `ADMIT-PARSE`, naming
  the line and what was expected. In a language with fixed positions and no nesting those cases are not distinct.
- Only a saved session can be admitted to. A crashed run's journal is refused `ADMIT-SESSION`.
- The proposal's bytes are not kept. The envelope is a record written by the admitting shell, and the seal is a
  hash and not a signature.
- The seam is per saved session. The same bytes offered to the child are refused as stale; admitted again to the
  untouched parent file, they make a second child with the same head.
- The crash court ends the process at eight points and shows process death, not power loss.
- `shell admit-anchor` prints the first four lines of a proposal for a saved session, and only reads.

**On the owner's host (2026-10-03).** The registration was applied and the gate run with the entry in the
registry: `GATE PASSED`, `RECONCILE  rowset a15345720a81009c  209 rows / 0 fail / 0 skipped`, the rowset and the
count it had before. The host's `verify/preregister.json` is byte-identical to the one registered here, 37 entries.
It was pushed as `0669ecf`. The registration reached the host before the docs commit that records the courts; the
two touch different files, and either order gives the same tree.

**The owner's acceptance (2026-10-03).** A review of the registration, brought by the owner and recorded at his
instruction. He accepts it as the ADMIT-0 design, with the distinction that it is a preregistered specification
and not an implementation result. In its words, the state is:

> **ADMIT-0: REGISTERED / BUILD PENDING.**

- **What the 209 rows show.** They are the gate as it stood plus the registration. They do not establish any of
  the entry's success conditions; the eight courts' rows do not exist yet.
- **The digest's limit, kept explicit.** The proposal's bytes are not kept, so the workshop and the sealer cannot
  recompute the digest in an envelope. The claim is that *the admitting shell measured and recorded the digest of
  the exact proposal bytes it received*. It is not that any later verifier can prove the recorded digest belongs to
  the original bytes. He would not add persistence of the proposal's bytes to remove the limit: that would enlarge
  the seam and bring the parser back into the downstream readers.
- **One operation, one proposal.** It gives atomicity without inventing batch semantics, and it leaves the crash
  court one possible new authority transition to interpret.
- **A boring vocabulary on purpose.** Open, close, paint. ADMIT-0 proves admission, not whether Verðandi can
  understand arbitrary landscape concepts.
- **The route is not changed, and the saved-form reader stays out.** MOUSE-LOOK-0, ADMIT-0, `READER-COURT-0`,
  `DESIGN-EVENT-0`, `LIVE-AI-EDIT-0`, then branch and preview. The saved-form JSON disagreement is not pulled back
  into ADMIT-0.
- **What comes next.** *The next work is therefore implementation against the frozen 0105 bytes—not another
  design round.*

**Where the review meets what stands.** Read against the tree as it stood at the review. The courts above have
since ruled on these, and the registration settled the rest.

- **There is no proposal boundary yet.** The review speaks of the current proposal boundary having shown parser
  disagreement and crashes. What was observed is the saved-form reader, alone, on bytes no command was given. It is
  the reason to build the proposal's recognizer new and strict. It is not a defect found in an admission path,
  because none exists.
- **The gate.** The review's "PowerShell gate" is `verify/verify.py`, which the owner runs from PowerShell.
- **One recognizer, and the three verifiers of a saved session.** A saved session is verified today by three
  programs that each read the saved form: the shell, the workshop and the sealer. The review's rule is about the
  proposal language, and it holds only if nothing downstream ever needs the proposal's text again. So what is saved
  beside the admitted event is typed values the shell writes in its own saved form, and the digest of the
  proposal's bytes, which any verifier recomputes over bytes without parsing them. Embedding the proposal's text
  for the other verifiers to parse again, which was the draft before the review, is dropped. The three readers of
  the saved form remain, and their observed disagreement is closed in `READER-COURT-0`, after this rung (the second
  court, ruling 2).
- **The event ADMIT-0 admits.** By the court it is an ordinary session event in today's vocabulary: a cell edit or
  a tile edit, with the same head the same edit made by a key would give. A design-event kind of its own is
  `DESIGN-EVENT-0`'s business, not this rung's.
- **Scope.** A scope the proposal writes for itself bounds nothing. It bounds something when whoever admits grants
  it, and a proposal can only ask for less: ruled so (the second court, ruling 3). The world has no regions (see
  the section above), so today a scope can name operation kinds, cells and tile classes and nothing larger.
- **Identity.** The tree has a renderer identity (a digest over the render sources compiled into the shell) and a
  bearing identity, both recorded in a session's live block. It has no single program identity; the gate's rowset
  names a gate outcome, not a binary. Ruled (the second court, ruling 4): the anchor is what a session already
  records, and no program identity is minted.
- **`proposal_id`.** If the proposer chooses it, it is as untrusted as the rest of the proposal. Refuse-always
  already makes a second admission of the same bytes stale. Ruled (the third court, ruling 2): the id is the
  proposer's handle, and a duplicate refusal compares it with the ids already admitted in the session.
- **What a crash court can show.** Terminating the process shows what a restart finds after the process dies. It
  does not show a power loss: bytes written and not flushed survive a killed process in the system's cache.
  Microsoft's page promises the write-through flush for a move performed as a copy and delete and is silent on
  atomicity. The court's claim is worded as process death; durability under power loss stays DECLARED from the
  platform's documentation and NOT_MEASURED.
- **The names after ADMIT-0.** `DESIGN-EVENT-0`, `LIVE-AI-EDIT-0` and `BRANCH-0` are the review's order. Each is
  still chosen in its own court. The four rules at the end of the section above stand: commit-only meets
  `BRANCH-0`, and earn-the-authority meets every example the review uses (cliffs, a valley, terrain, materials,
  populations), none of which the frozen oracle certifies.
- **Refusal codes.** The review's list gives the reasons. The registration gives them codes in the tree's form and
  says that a refused admission writes nothing to the session and is recorded like any other refusal.

**Grade.** DECLARED: the three courts' rulings, the review and its seven courts, the registration's conditions,
the owner's acceptance. MEASURED (on the host): the gate passes with the entry in the registry, 209 rows, the rowset
unchanged. OBSERVED: the 19-input table, here, outside the gate. Attributed and not claimed: everything under "What
the research found". Nothing about the seam itself is ESTABLISHED or MEASURED. **does_not_show.** That a strict
recognizer exists; that any of the courts holds; that a model can write a proposal worth admitting; any safety
property of a system that includes a model. The state is registered, build pending.

### The design language — one design authority, many editors · **declared** (the owner's, 2026-10-03); not registered, nothing built
A design text the owner brought on 2026-10-03, after the registration, and asked to have recorded. Like the two
texts above it is a reply to his own description of what he is after, so its wording is quoted where it states the
rule and summarized elsewhere. It extends the design-event stream and seats nothing.

> **Intent → constrained design operation → verified state transition → provenance → deterministic projection.**

- **The design environment is itself a typed, deterministic, inspectable program.** In the text's phrase, *a CAD
  for interactive worlds*, where every design operation has the properties the admission seam is establishing.
- **Design objects and constraints, not tools.** The environment is not built around a wall tool, a terrain tool
  and a mesh tool. It is built around a design state with five parts: geometry (surfaces, volumes, boundaries,
  transforms), semantics (rooms, paths, cover, spawn zones, gameplay volumes, tags), relations (adjacent to,
  contains, connects, blocks, visible from), constraints (dimensions, reachability, clearance, performance,
  visibility, gameplay invariants) and provenance (author, operation, parent, constraint result, resulting
  identity). A viewport is one projection of that state.
- **Geometry is not the primitive.** Conventional CAD goes point, line, surface, solid. Here the order is *intent →
  relation → constraint → realization*. A request is turned into a bounded design representation, and the system
  asks whether the intent can be represented, whether its constraints can coexist, what authority it touches, what
  changed and which constraints became invalid. The answer is a design diff.
- **Constraints are first-class world objects.** Persistent objects with a kind, a subject, a value, a status and a
  witness, and not validation code alone. A design change then has a consequence graph: the operation, the objects
  it changed, the constraints it affected, each satisfied, violated or unknown. What that gives, in the text's
  words: *a machine-readable explanation of why a world is still valid.*
- **One authority, many projections.** The same object seen as geometry (walls, doors, materials), as gameplay
  (cover, routes, spawns) and as runtime cost (draw cost, memory, streaming), with no editor copy of the object
  beside a runtime copy. The text names five such environments over one authority: spatial, gameplay, simulation,
  narrative and performance.
- **A model gets a design language and nothing else.** A proposal goes through a compiler to a candidate diff, the
  constraints are evaluated, a human sees a preview, and only then is it admitted. The model never writes
  arbitrary files, executes arbitrary code or mutates authority. The renderer stays downstream, the model is not an
  authority, and the interface is not the source of truth.
- **Reversible design, as provenance.** Every object keeps its lineage: the event that created it, the events that
  changed it, the constraints on it, the projection that shows it. "Why is this wall here?" is answered from that
  record. The text calls it design provenance and not merely undo history.
- **What the text would not do, and the rung it proposes instead.** It would not start *a giant "next-gen CAD
  editor"*. It proposes a small rung, `DESIGN-IR-0`, proving only a typed design object, a typed relation, a typed
  constraint, a bounded diff, a deterministic serialization and provenance: no viewport, no model, no mesh editor,
  no giant schema. Its one vertical slice is *a rectangular room with doors, connectivity, clearance, and a gameplay
  tag*, produced identically by a human-authored operation and by a hypothetical model's proposal, then mutated on
  purpose to show the constraint's witness change deterministically.

Its last lines:

> **Don't build an AI level editor. Build a deterministic design language with many editors.**

and: the thing that survives every editor is *the design authority + constraints + provenance*.

**What already stands that it would rest on.** The admission seam is registered, with a vocabulary that is boring
on purpose. A projection that never writes is the existing separation of workshop, kernel and shell, and the
invariants below already forbid a view from holding authority. WORKSHOP-0 refuses a record whose projection is
stale under a moved authority, which is one derived thing already tied to the authority it was derived from.
SEMANTIC-0, above, is the named and unbuilt rung for meaning beyond what the oracle certifies. The HUD's pins are
the one case so far of VIEW semantics earned here and held by rows.

**What does not exist.** A design object of any kind. Rooms, doors as objects, paths, cover, spawn zones, volumes
or tags. A relation. A constraint, a constraint's witness, or a solver. A compiler from intent to operations. A
second projection of the world beside the frame and the HUD. Units: the world is a grid of cells and five tile
classes, with no metre, no second and no height.

**Where it meets rules already in force.** Each of these wants the owner's ruling before a rung is seated.

- **Earn the authority.** Anything that decides W or M is CORE and comes only from Urðr, carried or earned there
  and re-frozen. A layer that only names and reads what W already holds (a room as a set of cells, reachability as
  a path over open cells) could instead be VIEW semantics by SEMANTIC-0's route: a reference here, pinned by rows,
  never writing the world. Which route each kind of object takes is a ruling, object kind by object kind.
- **A constraint's status is a witness, not a field.** The declaration of a constraint is authored content, and if
  it is admitted it is an event. Its status is derived from the world. A saved `status = SATISFIED` that a reader
  trusts is a second authority. In this tree the equivalent of a status is a witness: recomputed by replay, compared
  and refused when it differs, never taken from the file.
- **Float-free, and in the world's own units.** The examples speak in metres, seconds and percentages. The rules
  here are integers of the world: cells, ticks, reduced rationals.
- **A panel, not a score.** "14 satisfied, 1 degraded, 0 violated" is a count per status and is admissible as
  that. It is not folded into one number, and "degraded" needs a definition before it is a status.
- **Preview before admission.** The text's flow shows a human preview before the admit. Commit-only still holds: a
  preview is a speculative worldline, a typed log replayed from an anchored head, and that is the branch rung's
  business, after admission works.
- **The compiler.** If it is code in this tree it is program and the gate certifies it. If it is a model it is
  outside the tree. Either way its output is a proposal in a registered language, and the seam admits or refuses it.
- **The order.** The owner's locked order is ADMIT-0, `READER-COURT-0`, `DESIGN-EVENT-0`, `LIVE-AI-EDIT-0`, then
  branch and preview, and his acceptance of the registration says the next work is implementation and not another
  design round. Where `DESIGN-IR-0` sits against `DESIGN-EVENT-0` was not ruled. It is recorded here as a declared
  name and is not seated.

**Grade.** DECLARED: all of it. Nothing here is established or measured. **does_not_show.** That a design object,
a relation or a constraint can be defined over this world without new CORE semantics; that a constraint's witness
can be computed deterministically for anything beyond what the grid already says; that a model can write in such a
language. When a rung is seated from it, the rung registers its own hypothesis, failure condition and limits.


### GAME-0 — Urðr's game layer as frozen evidence · **landed**
The seventeen discrete game-layer slices (`gamegen` … `cue`), their corpora, suites, briefs and the D24/D25 boundaries,
carried verbatim from `urdr-oracle-1` into `oracle/game/`, each file listed with its sha256 and Urðr git blob id, and
Urðr's own suites passing in place (`game-frozen`, `game-suites`, `game-plant`, `game-not-runtime`). Evidence, not a
runtime dependency: the kernel, workshop and shell do not read it. **ORACLE-D0 (landed):** the same carried code,
in place, recomputes the oracle's third hash `D_0` from the oracle's view on every gate (`oracle-d0`, with a plant),
so all three oracle hashes are now checked; the studio still mints none of `D_0`.

### SKYBOX-0 / PHYSICS-0 — the skybox beyond the oracle; physics already in the tag
The skybox stays *beyond* the frozen oracle and is gated behind the new-semantics route (`SEMANTIC-0`'s machinery):
named, courted, and not seated until that route exists. Physics is not in the same position. An earlier version of
this roadmap said it was beyond the oracle, and that was wrong. `urdr-oracle-1` carries Urðr's exact ℤ/ℚ mechanics
(rungs 1–4), its bounded Q32.32 real-time path (rung 5) and its lockstep/rollback netcode, all as earned CORE
semantics with frozen corpora. They reach the studio by the `GAME-0` route, and only physics the tag does not carry
needs the new-semantics route.

### IMPOSSIBILITY-0 — measured negative results as level preconditions
Some world states are *provably unreachable*; recording those impossibilities as level preconditions is itself a
form of authored semantics, and a natural companion to `SEMANTIC-0`.

---

## The invariants that carry forward

Everything above obeys the same discipline that carried the render campaign:

- **Earn the authority.** CORE semantics come only from Urðr: carried verbatim from the tag already cited (as
  `GAME-0` carries the game layer), or earned there and re-frozen under a new name. New VIEW semantics may be
  Verðandi-local but must be pinned by rows here. The shell never mints truth.
- **Byte-identity where an oracle exists; a pinned reference where one does not.** A rung with a frozen oracle proves
  byte-identity against it; a rung inventing new semantics defines a reference and pins it, then defends *that*.
- **The model may propose; only the verifier may admit** (declared, LLM-BUILDER-0). Anything that suggests a change —
  a key, a mouse, a script, one day a model — reaches the world only as a typed event the session validates and
  replays. Verðandi does not execute what a proposer writes; it records what the verifier admits.
- **The gate certifies the program; content is admitted, not gated** (declared, 2026-10-03). The engineering gate
  runs when the program changes. Content, which today means a session's events, is admitted by checks on the
  artifact itself and never invokes the gate. A change to the laws content runs under is a program change.
- **Preregister the method before the number,** including the failure condition and the null. Measure before
  optimize; re-measure after. Correctness on the gate, speed off it. The record stores numbers; the reading
  interprets.

The render half proved this discipline scales to a hard optimization campaign. The authoring half is where it meets
its more interesting test: proving that a *living, editable world* can be as honestly evidenced as a static picture.

---

## Sources (prior art the named rungs draw on)

- [DXGI flip model — DirectX Developer Blog](https://devblogs.microsoft.com/directx/dxgi-flip-model/) and
  [Reduce latency with DXGI 1.3 swap chains — Microsoft Learn](https://learn.microsoft.com/en-us/windows/uwp/gaming/reduce-latency-with-dxgi-1-3-swap-chains) (PRESENT-1)
- [Multithreaded software rasterizer — Zach Bethel](https://zachbethel.wordpress.com/2012/11/28/multithreaded-software-rasterizer/) and
  [Thread pool — Wikipedia](https://en.wikipedia.org/wiki/Thread_pool) (execution refinements; see [`GHOSTS.md`](GHOSTS.md) G1/G3)
- [Roofline: an insightful visual performance model — CACM](https://cacm.acm.org/research/roofline-an-insightful-visual-performance-model-for-multicore-architectures/) and
  [Roofline Performance Model — NERSC](https://docs.nersc.gov/tools/performance/roofline/) (the T=8 bandwidth question; see [`GHOSTS.md`](GHOSTS.md) G2)
- [Working with authoring and runtime data — Unity Entities](https://docs.unity3d.com/Packages/com.unity.entities@1.0/manual/editor-authoring-runtime.html) (interactive capture; the authoring/runtime split)
- [Conflict-free replicated data type — Wikipedia](https://en.wikipedia.org/wiki/Conflict-free_replicated_data_type) and
  [Delta-state replicated data types (Almeida et al.)](https://members.loria.fr/CIgnat/files/replication/Delta-CRDT.pdf) (MERGE-0's convergence theory)
- [Scoped threads (`std::thread::scope`) — Rust](https://doc.rust-lang.org/std/thread/fn.scope.html) (structured concurrency; see [`GHOSTS.md`](GHOSTS.md) G1)
- ADMIT-0 (outside sources, attributed; hypotheses, not claims of this repository):
  [LangSec explained in a few slogans](https://sergey.cs.dartmouth.edu/langsec/occupy/),
  [JSON interoperability vulnerabilities — Bishop Fox](https://bishopfox.com/blog/json-interoperability-vulnerabilities),
  [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.txt),
  [RFC 8785 (JCS)](https://www.rfc-editor.org/rfc/rfc8785.html),
  [Canonicalization Failures as a Recurring Vulnerability Class (Brömme)](https://arxiv.org/abs/2608.06508),
  ["YOLO" is not a valid hash construction — Trail of Bits](https://blog.trailofbits.com/2024/08/21/yolo-is-not-a-valid-hash-construction/),
  Design Patterns for Securing LLM Agents against Prompt Injections (arXiv 2506.08837) and CaMeL: Defeating Prompt
  Injections by Design (arXiv 2503.18813), both read in Simon Willison's summaries
  ([patterns](https://simonwillison.net/2025/Jun/13/prompt-injection-design-patterns/),
  [CaMeL](https://simonwillison.net/2025/apr/11/camel/)),
  [The kernel and the De Bruijn criterion](https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026/book/peano/kernel.html),
  [JSONSchemaBench](https://arxiv.org/html/2501.10868v2),
  [Finding Consensus Bugs in Ethereum via Multi-transaction Differential Fuzzing (Fluffy, OSDI '21)](https://www.usenix.org/conference/osdi21/presentation/yang),
  [Appending events — EventStoreDB](https://docs.kurrent.io/clients/tcp/dotnet/21.2/appending.html),
  [Essential features of an Event Store](https://eventsandstuff.substack.com/p/essential-features-of-an-event-store),
  [All File Systems Are Not Created Equal (ALICE, OSDI '14)](https://cs.uwaterloo.ca/~alkiswan/papers/alice-osdi14.pdf),
  [MoveFileExA — Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-movefileexa),
  [ReplaceFileW — Microsoft Learn](https://learn.microsoft.com/windows/win32/api/winbase/nf-winbase-replacefilew),
  [Constraint Is All You Need (Xu et al.)](https://www.pcgworkshop.com/archive/xu2025constraint.pdf),
  [Agentic PCG](https://zehua-jiang.github.io/AgenticPCG/),
  [About Raw Input — Microsoft Learn](https://learn.microsoft.com/en-au/windows/win32/inputdev/about-raw-input).
  The review's own citations, not opened here: the LangSec workshop page, SLSA provenance v1.2 and OWASP's AI Agent
  Security cheat sheet.
