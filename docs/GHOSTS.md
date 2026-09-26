<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2026 Daniel J. Dillberg -->

# Ghosts — what the gate does not prove

*The honest catalog. A "ghost" is a thing that is true-enough to ship but not yet nailed down: an unproven
assumption, a caveat the numbers carry, a soundness question the compiler cannot answer, a claim graded below the
confidence its headline might suggest. Each ghost is stated plainly, graded, and given an **exorcism** — the
specific measurement or change that would lay it to rest. Nothing here is a defect the gate missed; these are the
edges of what the gate is designed to prove. `integrity ≠ truth`, and this file is where that motto is paid for.*

The grades borrow the claim ladder: **ESTABLISHED / MEASURED / UNDERDETERMINED / SPECULATIVE / NOT_MEASURED**, plus
**SOUND?** for the one memory-model question.

---

## G1 — the threaded framebuffer write is race-free but not Miri-clean · SOUND?

`emit_threaded` gives each scoped thread a `*mut u8` to the *whole* framebuffer (a `Send` wrapper) and each thread
reconstructs `&mut [u8]` over the entire buffer, writing only its own disjoint columns. Because the column partition
is disjoint, no two threads ever touch the same byte, and none reads `out`: there is **no data race** at the
hardware or LLVM level, and the gate proves the output byte-identical at every `T`. But under Rust's formal aliasing
model (Stacked/Tree Borrows) creating multiple `&mut` over overlapping memory is undefined behaviour *regardless* of
whether the accesses are disjoint — so a strict Miri run would flag it. This is the standard std-only pattern for
disjoint-but-interleaved writes, chosen because a crate (rayon/crossbeam) is forbidden by the charter and a
copy-merge would double the memory traffic on a bandwidth-bound kernel.

**Exorcism.** Partition the framebuffer by **contiguous row-bands** instead of columns, so each thread's bytes are a
single contiguous slice and `slice::chunks_mut` hands out genuinely disjoint `&mut` — sound with no `unsafe`, and
the standard decomposition for multithreaded software rasterizers (which tile the framebuffer into disjoint
regions). The catch: the correctness court proved *column*-partition invariance; a row-band emit would need its own
invariance proof (the per-row DDA recurrence is column-indexed, so a row-band split changes which axis carries the
recurrence). Alternatively, run the existing column path under Miri and record what it says. Either is a clean,
self-contained follow-up; neither is urgent, because the output is gate-proven and the writes are provably disjoint.

---

## G2 — the T=8 plateau is a bandwidth *hypothesis*, not a bandwidth *measurement* · SPECULATIVE

`GAUNTLET-2` measured that p99 stops improving past ~8 threads (T8 2360/2355 µs, T16 2311/2208 with 4.5% run-to-run
variance) and read that plateau as **memory-bandwidth / cache contention**, consistent with `LOCALITY-0`'s
memory-bound finding. That reading is *supported by evidence* — the flattening and the elevated high-`T` variance
are what a bandwidth wall looks like — but it is **not a direct measurement of the memory bus.** This court never
measured the machine's bandwidth or the emit's operational intensity; it does not establish that *eight* threads is
the exact saturation point, nor that bandwidth (rather than, say, the per-frame thread-spawn cost of G3, or SMT
contention, or thermal/frequency behaviour at high `T`) is the binding constraint.

**Exorcism.** A roofline measurement: probe the host's sustained memory bandwidth (a STREAM-style triad) and the
emit's bytes-touched-per-pixel, place the emit on the machine's roofline, and show it sits on the bandwidth roof
rather than the compute roof. That would convert "consistent with bandwidth saturation" into "measured
bandwidth-bound," and would name the saturation point instead of guessing it. Until then the plateau stays
SPECULATIVE and `T=8` is chosen for its *deterministic p99*, not because eight is proven optimal.

---

## G3 — the threaded emit spawns fresh threads every frame · MEASURED (cost included), not optimized

`std::thread::scope` creates new OS threads on every call, so `emit_threaded` — and therefore the shell's per-frame
render — pays thread-creation cost each frame. That cost is *inside* every `GAUNTLET-2` number (the sweep still beat
the baseline 3.3× with it included), so nothing is being hidden; but it is pure overhead a persistent thread pool
would remove, and multithreaded rasterizers universally use a pool rather than per-frame spawns. At real-time rates
in the window path, spawning eight threads per frame is measurable waste.

**Exorcism.** A std-only persistent worker pool (threads parked on a channel/condvar, handed column groups per
frame) replacing the per-frame `scope` spawn — byte-identical by construction (same `emit_partitioned`), measured
against the current spawn-per-frame path. This pairs naturally with G1's row-band rework.

---

## G4 — the performance numbers are cross-apparatus and not directly comparable · MEASURED, with a caveat

Three different harnesses produced three "single-thread emit" p99s that look comparable but are not: `GAUNTLET-1c`'s
`--fast-bench` reported ~4,734 µs, `LOCALITY-0`'s process-isolated `locality0.py` sealed **7,734 µs** (the
`GAUNTLET-2` baseline), and `gauntlet2.py`'s own `T=1` point read ~5,019/5,067 µs. These differ because the
harnesses differ — process isolation, interleave structure, warm-up, and what is timed around the emit all move the
absolute. This is *by design*: the discipline forbids cross-apparatus absolute comparison and permits only
*within-apparatus deltas*. But it means no single "the emit is X µs" headline is apparatus-free, and the sealed
baseline (7,734) is the one and only reference the parallel court is judged against.

**Exorcism.** None needed — this is a correctly-handled caveat, not a bug. It is listed so a future reader does not
mistake `4,734` and `7,734` for a regression. The rule to keep: cite the *ratio within a run*, never the absolute
across runs.

---

## G5 — every number is one host and one corpus · NOT_MEASURED beyond that

All wall-clock is `DANIELDILLBERG`; all correctness is the witness corpus plus adversarial cameras. The speedups,
the plateau, the layout win — none is established for another CPU, another scene, another tile set, or another
resolution. Byte-identity is proven over the corpus and adversarial cameras (a strong set), but *capacity* behaviour
(the whole locality/bandwidth story) is scene-dependent: a scene whose floor working set fits differently in cache
could move the LOCALITY-0 and GAUNTLET-2 verdicts.

**Exorcism.** Run the sealers on a second host and seal those records too (the envelope is host-parameterised
already); add scenes to the corpus that stress the floor working set. The `--confirm` mode exists precisely so a
second run's evidence is durable without overwriting the first.

---

## G6 — instruction-level invariance is a goal, not a proof · ESTABLISHED (as a limit)

The *Epistemic Invariance of the Boundary* theorem asks that variants be "bitwise-invariant up to the
address-generation instructions." The build pursues this by monomorphizing each layout, process-isolating each
variant, and interleaving — but what is actually *proven* is **output** byte-identity (the gate) and constant
*anchor* tax (the RE-BREAKDOWN-1b probe). The instruction-level invariance itself is best-effort code structure a
compiler may schedule around; it is not gate-provable, and the theorem's own "honest limits" section says so.

**Exorcism.** Inherently not fully exorcisable without a cycle-accurate instruction trace or a compiler that
guarantees the schedule — outside this project's tooling. The correct posture is the one already taken: the record
says what is proven (output) and what is aspired to (instruction schedule), and does not conflate them.

---

## G7 — the render headroom reaches the screen only out of phase with the present · MEASURED (two runs)

`LATENCY-0` *established* that the composed-GDI present (`StretchDIBits` under DWM) is refresh-coupled. Whether
`GAUNTLET-2`'s faster render survives it was the open question, and `LATENCY-1` turned out unable to ask it: its
instrument renders every frame before the window opens (the amendment `LATENCY-1a`). `LATENCY-1R` put the render inside
the clock and measured it twice on the owner's host (`shell/attest/latency1r-DANIELDILLBERG.json` and its `-confirm-`).
Render-start → composited, production (T=8) against the single-thread reference, p50:

- **Locked** (the render starts right after a composition): 25,550 vs 25,552 µs, then 25,563 vs 25,587 µs. **Absorbed**
  — less than 1% of the ~2.6–2.8 ms render saving reached composited output in either run; both arms land on the same
  composition and the saving becomes waiting. (The preregistered label flipped from ABSORBED to PARTIALLY ABSORBED
  between the runs on a 22 µs difference — see G10.)
- **Uniform** (the render starts at a random phase): 21,400 vs 24,987 µs, then 21,977 vs 25,217 µs. **Propagates** —
  composited output 3.2–3.6 ms earlier at the median, reproduced.

So the headroom reaches the glass for work that arrives at an arbitrary moment (an input, say) and not for a loop that
renders right after it presents. The renderer's own latency is materially improved; end-to-end presentation latency is
phase-dependent; no low-latency, competitive or input-to-photon claim is made.

**Exorcism.** For the locked regime, the absorption is what `PRESENT-1` (a flip-model / waitable-swapchain present)
hypothesizes it can remove — but not before G8's split shows whether the present or the software frame dominates.

---

## G8 — the render-inclusive frame is longer than one refresh, and its split is unmeasured · MEASURED (total), UNDERDETERMINED (split)

The GAUNTLET staircase optimized only the *emit* (texel) pass, because `GAUNTLET-0` measured it as the dominant render
phase (695‰). `Scene::strips` and `Scene::frame` remain mantle's frozen, single-threaded code. `LATENCY-1R` measured the
whole render-start → frame-ready interval in the shell window: **14.8–15.7 ms at p50 for the production arm** across
two runs and both regimes — longer than every refresh estimate taken on that host (13.1–13.9 ms) — while the two arms
differ in it by only 2.6–2.8 ms. That interval holds more than `--breakdown` times: strips, frame, the pixel pass, the
HUD overlay, the RGB → BGR conversion, fresh buffer allocation, and `StretchDIBits`'s 2:1 downscale into the half-size
client area. How the ~15 ms divides among them is not measured, and it is where the dominant whole-frame cost now
hides. (It is not the whole software-to-screen path either: render-start → composited is 21.4–25.6 ms at p50 across both runs.)

**Exorcism.** Split the render-start → frame-ready interval on the same window apparatus and the same sealed session,
phase by phase — renderer output, HUD, conversion, blit — with the render-start → frame-ready total and the frame-ready →
composited interval kept beside them as anchors: the `GAUNTLET-0` pattern applied to the shell's whole frame, before
any optimization (renderer or presentation) is chosen. The `--breakdown` rerun alone would miss the conversion and blit
phases, which sit outside the kernel.

---

## G9 — the shell now compiles the entire fast/apparatus stack · MEASURED (benign), noted

To render through the threaded path, `shell/main.rs` now builds `kernel/fast.rs` in full, including the RE-BREAKDOWN
probe module and the LOCALITY court apparatus — none of which the shell calls. It is dead code (`#[allow(dead_code)]`),
so it does not run, but it does enlarge the shell's compiled surface and couples the shell's build to the whole
optimization stack.

**Exorcism.** If the coupling ever grates, split `fast.rs` so the production render path (`render`, `emit_threaded`,
`emit_partitioned`, `emit`, `blocked_floor`, `floor_blocked`) lives in one module and the measurement apparatus
(`probe`, `locality`, `structure`) in another; the shell would then build only the former. Not urgent — it is a
tidiness ghost, not a correctness or performance one.

---

## G10 — the latency statistics are thin, and one category boundary has no margin · MEASURED

Some of the present-path statistics rest on very few samples. With n = 200, **p99 is the third-largest sample** (two
lie beyond it): the first `LATENCY-1` run read DEGRADATION (p99 12,299 µs vs 7,318) on three slow samples, and its
confirmation read NO MATERIAL CHANGE (p99 7,339 µs) — the category flipped on a three-sample tail while p50 and p95
held. The **refresh period** is the median of eight idle `DwmFlush` intervals, and across five runs on the same host it
read between 13,089 and 13,926 µs, a 63‰ spread. And `LATENCY-1R`'s rule puts the boundary between ABSORBED (≤ 0‰) and
PARTIALLY ABSORBED (1–499‰) at exactly zero, so the locked regime's label flipped between runs on 2 vs 24 µs of glass
delta while its magnitude (under 1% propagated) held. None of these statistics is wrong; each is coarser than its
precision suggests, and the medians across repeated runs deserve more weight than any single tail or label.

**Exorcism.** For a tail-sensitive verdict, raise N or report the number of samples beyond the threshold beside the
percentile; estimate the refresh from a longer idle run; give a category boundary a declared noise margin. Each is a
method change, so it would be preregistered before a number, never applied to one already taken.

---

## G11 — the window shows GDI's 2:1 downscale of the certified picture · NOT_MEASURED

The blit-hash law proves the shell hands `StretchDIBits` exactly the kernel's composite. But the window's client area
is half size (960 × 540), so GDI downsamples the 1920 × 1080 picture on the way to the glass, under whatever stretch
mode the device context has — the shell never sets one. What actually reaches the screen is therefore an OS
resampling of the certified picture, which no row checks, and the resampling's cost sits inside `LATENCY-1R`'s
render-start → frame-ready interval (it is before `LATENCY-0`'s frame-ready, so outside `LATENCY-0` and `LATENCY-1`).

**Exorcism.** Present 1:1 (a full-size client area, or a 1:1 blit of a region), or set the stretch mode explicitly and
state what it does; either way, time the blit as its own phase in the G8 split.

---

## The disposition

None of these ghosts is load-bearing for a claim the program actually makes. G1 and G3 are execution refinements
with sound remedies; G2 is an honest boundary of what the courts measured; G7 is now measured and reproduced (twice), and
G8 has turned from a hunch into a measured total with an unmeasured split — the program's next measurement; G4, G5, G6, G9, G10 and
G11 are caveats a careful reader must carry, recorded so they are carried on purpose.
The program's value is that it *knows* these are ghosts and *says so* — a result the gate could not prove is graded
exactly that far and no further. That is the whole point of the discipline: a dead end is documented as rigorously
as a win, and a hypothesis is never dressed as a measurement.
