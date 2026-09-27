<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2026 Daniel J. Dillberg -->

# Roadmap — toward a live, authorable world

*Where the program stands, what "a live authorable world" means for it, and the sequenced, falsifiable path to get
there. This roadmap names only rungs that are already public in [`verify/RUNGS.md`](../verify/RUNGS.md); the
general techniques it points at are cited prior art, not commitments. Specific new measurement and execution rungs
are under private consideration pending the owner's consensus and are not enumerated here.*

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

### PRESENT-1 — decouple present from refresh (LATENCY-1R measured the coupling absorbing the render headroom in phase)
`LATENCY-0` *established* only that the composed-GDI present costs at least one refresh interval. `PRESENT-1`'s
falsifiable hypothesis — to be measured, never assumed — is that a **flip-model / waitable-swapchain** present can
decouple present latency from refresh. The prior art is well documented: the DXGI flip model shares frames directly
with the compositor with minimal copies, a frame-latency waitable object reaches ~1 frame of latency in Independent
Flip (and lets the DWM sleep), and `ALLOW_TEARING` with multi-plane overlay goes lower still. Built std-only against
raw Win32/COM (as `win32.rs` already hand-rolls GDI); off-gate; `HARDWARE-144` additionally needs a ≥144 Hz panel.

### Interactive capture — the inverse of SHELL-PLAYBACK
Raw window/device event → binding → typed action/edit → `SESSION-WALK` append → the *same* sealed representation that
headless authoring produces. `SHELL-PLAYBACK` already proves a sealed session replays to the exact window frames;
interactive capture closes the loop so a *live* edit produces a sealed session that would replay identically. A
shell/input problem, not a new authority — measured against the existing session machinery, never modifying it. The
industry pattern to borrow is the **authoring-data / runtime-data split** (e.g. Unity DOTS), with deterministic step
and reload atomicity — which is exactly the workshop's edit → authority → record shape. The live loop this needs is its
own rung (timing, cadence, ownership, input). ALLOC-REUSE-1 read ADOPT and is locked, so that loop renders through
`LoopRenderer` rather than deciding its allocation again.

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
