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
sealed chain; and `SHELL-PLAYBACK` proves the window shows *exactly* that sealed becoming.

What is *not* yet joined is the loop between them at interactive speed: editing the world **while** the window shows
it, and seeing the consequence immediately, all through the same sealed representation — and doing it for semantics
the frozen oracle never certified.

---

## What "live authorable world" means here

Not a general game engine. Specifically: **a running window in which an author changes the world, the change becomes
a new authority through the sealed workshop path, the projection updates live, and every frame on the screen is
provably the consequence of that authored history** — with new kinds of world content (skybox, physics, filtering
semantics) admitted only when they *earn* an authority, either re-frozen from Urðr or pinned by a Verðandi-local
reference. The bar is the one the program already holds itself to: `built ≠ adopted`, `declared ≠ verified`, and no
semantics reaches the screen without passing through a gate.

---

## The gap, in four questions

1. **Does the render headroom reach the screen?** The present path is still composed-GDI and refresh-coupled; a
   faster render behind it may buy nothing at the glass. *(Open — G7.)*
2. **Can an author edit the live window?** The pieces exist headless (input → typed edit → SESSION-WALK); they are
   not yet wired into the running present loop with live re-projection.
3. **Can the world hold semantics the oracle never certified?** Skybox, physics, and filtered VIEW semantics live
   *beyond* the frozen oracle and need the new-semantics route.
4. **Can independent edits combine?** Two authored branches of a world need a deterministic, consensus-free merge.

---

## The sequenced path (named rungs only)

### LATENCY-1 — does the headroom survive the present path
Re-run the sealed reference session through the present path *now that the render is fast*, and compare frame-ready →
composited against `LATENCY-0`'s immutable baseline. This is a **measurement, not an optimization** — it answers
question 1 and decides whether `PRESENT-1` is even worth building. Off-gate, host, witnesses first, no refresh claim.

### PRESENT-1 — decouple present from refresh, if LATENCY-1 says the present dominates
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
and reload atomicity — which is exactly the workshop's edit → authority → record shape.

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

### SKYBOX-0 / PHYSICS-0 — content beyond the frozen oracle
Skybox and physics stay *beyond* the frozen oracle and are gated behind the new-semantics route (`SEMANTIC-0`'s
machinery). They are named, courted, and deliberately not seated until the semantics route that would give them an
authority is built.

### IMPOSSIBILITY-0 — measured negative results as level preconditions
Some world states are *provably unreachable*; recording those impossibilities as level preconditions is itself a
form of authored semantics, and a natural companion to `SEMANTIC-0`.

---

## The invariants that carry forward

Everything above obeys the same discipline that carried the render campaign:

- **Earn the authority.** New CORE semantics come only from Urðr, re-frozen and named. New VIEW semantics may be
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
