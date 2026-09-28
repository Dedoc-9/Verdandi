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
LIVE-AUTHOR-0    the thing authored is the same authority the next frame renders — painted live on the host by class keys, saved, replayed here
      ↓
free continuous movement → richer edits      vocabulary on the one live editor, not new pathways
      ↓
walking in a live, authorable world
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
editor (`shell live-window`), gated in its binding table, not new pathways or rungs. Mouse-look, cursor authoring,
preview sliders, gizmos and an editor-pane interaction model are deliberately not on the route yet: those are where a
shell starts accumulating an alternate authority.

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

### LIVE-AUTHOR-0 — the thing authored is what the next frame renders · **measured on the host** (`9a3e4521`): tile classes painted live, saved and replayed
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
the edits. A resume of the painted session on the host is still to come.

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
