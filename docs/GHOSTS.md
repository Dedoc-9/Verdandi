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

## G8 — the render-inclusive frame is longer than one refresh, and it has no single dominant phase · MEASURED (confirmed)

The GAUNTLET staircase optimized only the *emit* (texel) pass, because `GAUNTLET-0` measured it as the dominant render
phase (695‰). `LATENCY-1R` then measured the shell's whole render-start → frame-ready interval at 14.8–15.7 ms p50 for
the production arm — longer than every refresh estimate on the owner's host — without a split. `FRAME-SPLIT-0`
(`739dc807`) split it (`shell/attest/framesplit-DANIELDILLBERG.json`): envelope p50 15,690 µs, and p99 shares of the
envelope — **blit 434‰**, emit 272‰, frame 251‰, bgr 139‰, and strips, floor swizzle and HUD under 10‰ each. **No phase
reaches 500‰, so the court reads NO SEAT (multi-component):** the post-GAUNTLET-2 frame is not dominated by any single
renderer or presentation phase, and no single optimization is promoted. The instrumentation tax was −154 µs at p50
(9‰), recorded and not used to correct any phase.

The preregistered confirmation reproduced the reading (NO SEAT; blit 427‰, emit 269‰, frame 259‰, bgr 136‰; every
share within 8‰ of the first run). What remains open is not the shape but its parts: the split cannot say how much of
the largest phase, the blit, is `StretchDIBits`'s 2:1 downscale rather than the copy itself (G11), and the emit and
frame phases include their buffers' allocation. `ALLOC-REUSE-0` (preregistered, `aaaada37`) measures how much of the
frame that allocation is, as a diagnostic that adopts nothing. It read ALLOCATION MATERIAL twice: reuse was 1.59 and
1.82 ms (91‰ and 105‰) cheaper at the envelope p50, with the deltas mostly in bgr and emit. The production path is
unchanged; adopting reuse would be its own court.

**Exorcism.** Because the multi-component result promotes nothing by itself, any next step is a narrower measurement of
one named component, preregistered on its own — not an optimization chosen because a share looks large. The first was
`PRESENT-SCALE-0` (G11); `PRESENT-STRETCH-0` and `ALLOC-REUSE-0` follow the same way. A return to `emit` because it was once dominant, a present-path
rewrite because blit is largest, or a BGR change because 139‰ looks tempting would each skip the rule this court
applied.

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

## G10 — the latency statistics are thin, and the category boundaries have no declared margin · MEASURED

Some of the present-path statistics rest on very few samples. With n = 200, **p99 is the third-largest sample** (two
lie beyond it): the first `LATENCY-1` run read DEGRADATION (p99 12,299 µs vs 7,318) on three slow samples, and its
confirmation read NO MATERIAL CHANGE (p99 7,339 µs) — the category flipped on a three-sample tail while p50 and p95
held. The **refresh period** is the median of eight idle `DwmFlush` intervals, and across five runs on the same host it
read between 13,089 and 13,926 µs, a 63‰ spread. And `LATENCY-1R`'s rule puts the boundary between ABSORBED (≤ 0‰) and
PARTIALLY ABSORBED (1–499‰) at exactly zero, so the locked regime's label flipped between runs on 2 vs 24 µs of glass
delta while its magnitude (under 1% propagated) held. `PRESENT-STRETCH-0`'s confirmation added two more cases at the
50‰ confound bound. `HALFTONE`'s label flipped from MODE MATERIAL to CONFOUNDED on a non-blit movement of 53‰, and
`COLORONCOLOR` passed the same bound at 48‰. Both happened in a run where every phase was slower than in the first
(the default's blit went from 7.3 to 11.6 ms). ALLOC-REUSE-1 takes this ghost's remedies before its number: 1000 samples
per cell (p99 is the 11th-largest sample, with the 12 largest reported beside it), a same-run comparator, a declared
adoption margin, and HOST-STATE-0's snapshots beside each run. Both of its runs passed, the second with its p99 at 929‰
against a 950‰ bound. That margin was declared before either number, and the second run was 41% slower as a whole
(G13). None of these statistics is wrong; each is coarser than its
precision suggests, and the medians across repeated runs deserve more weight than any single tail or label.

**Exorcism.** For a tail-sensitive verdict, raise N or report the number of samples beyond the threshold beside the
percentile; estimate the refresh from a longer idle run; give a category boundary a declared noise margin. Each is a
method change, so it would be preregistered before a number, never applied to one already taken.

---

## G11 — the window shows GDI's 2:1 Boolean-AND reduction of the certified picture, and here that reduction is costly · MEASURED (confirmed)

The blit-hash law proves the shell hands `StretchDIBits` exactly the kernel's composite. But the window's client area
is half size (960 × 540), so GDI reduces the 1920 × 1080 picture on the way to the glass, under the device context's
default stretch mode — the shell never sets one. `PRESENT-SCALE-0` recorded that mode on the owner's host: **1,
`BLACKONWHITE`**, which combines the pixels a reduction eliminates with a Boolean AND of their colour values rather than
an average. What the half-size window shows is therefore not the certified picture scaled but an AND-reduction of it,
which no row checks.

It is also expensive here. With the destination client area as the only variable, the blit's p50 fell from 7,755 µs
(half) to 2,194 µs (full, 1:1), and on the preregistered second run from 7,461 to 2,199 µs — **SCALING MATERIAL** both
times (717‰ and 705‰), with the non-blit phases inside the confound bound (48‰ and 33‰). On this host, in this exact GDI
apparatus and workload, the 1:1 destination configuration had a far lower blit p50 than the 2:1 `BLACKONWHITE` one; that
is the net of removing the scaling and adding the larger copy, and not a general statement about GDI.

**Exorcism.** As a measurement ghost this one is laid: the reading reproduced. What is still open is a choice, not a
measurement — what the shell should present (its geometry, a stretch mode set and stated, or a 1:1 region) changes
what the window shows, so each is its own court, never a consequence drawn from this diagnostic. `PRESENT-STRETCH-0`
(`f5372890`) asks only whether the half-size blit's cost depends on the stretch mode, and it chooses none. Over two
runs `COLORONCOLOR`'s blit read MODE MATERIAL (cheaper) against the default both times (392‰ and 449‰ at p50). So on
this host the half-size blit's cost depends materially on which reduction GDI performs, and the default
`BLACKONWHITE` was dearer than `COLORONCOLOR` in both runs. `HALFTONE` read MODE MATERIAL once and CONFOUNDED on the
confirmation, and it stays unresolved.

---

## G12 — the render-loop courts measure a loop the shipped shell does not run · ESTABLISHED (read from the code)

LATENCY-1R, FRAME-SPLIT-0, PRESENT-SCALE-0, PRESENT-STRETCH-0 and ALLOC-REUSE-0 all time a loop that renders a frame and
then presents it, sample after sample. The shipped shell has no such loop. `run` renders one frame and presents it
until the window closes. `playback-window` renders every frame and every blit before its window opens, then presents
the stored bytes. So the courts' "production frame" is the production *render* inside a *modelled* loop: the loop a
live, authorable window will need, not one that ships today. Their numbers stand as measurements of that model. They
are not measurements of `run` or `playback-window`, whose present loops do no rendering at all.

This came to light before ALLOC-REUSE-1 was preregistered. Adopting reuse "in the production path" had nothing to act
on, so what that court can adopt is an entry contract: the renderer a future live loop must enter.

**Exorcism.** The live-loop rung (ROADMAP's interactive capture) will make the modelled loop a shipped one, and its own
court will measure it. It will render through `LoopRenderer`, adopted by ALLOC-REUSE-1 LOCK. Until then, read "the
shell's frame" in these courts as "the render-inclusive frame of the modelled loop".

---

## G13 — the same court can run 40–60% slower on another run the same day, and the cause is unmeasured · MEASURED (the drift); UNDERDETERMINED (the cause)

Twice now a preregistered second run has been much slower as a whole than its first, at a similar refresh.
PRESENT-STRETCH-0's default-mode blit p50 went from 7,274 to 11,589 µs (+59%). ALLOC-REUSE-1's fresh envelope p50 went
from 15,469 to 21,808 µs (+41%), about 45 minutes after the first run. The within-run comparisons the rules use
absorbed a shift common to both cells: ALLOC-REUSE-1's saving held at about 1.8 ms in both runs. But a shift that is not
common to both cells can move a label: PRESENT-STRETCH-0's HALFTONE flipped to CONFOUNDED in its slower run. And no
millisecond figure from one run can be carried to another.

HOST-STATE-0 recorded the host around ALLOC-REUSE-1's two runs. The OS reported the same CPU clock state, plan and power
before both. What differed was memory: 96% load with 359 MB available before the slower run, against 89% with
1,222 MB before the faster one. That is one coincidence, on one pair of runs. It is not a cause: the OS-reported MHz
cannot show boost, thermal state is not captured, and the snapshots bracket the run rather than sample it.

**Exorcism.** Keep recording, and don't control yet. Each further pair of runs either repeats the association (slow runs
under memory pressure) or breaks it (a slow run with memory to spare, which would say the recorded state is
insufficient). Only after that, and preregistered, might a court hold memory pressure or the power state fixed. Until
then, read absolute milliseconds as belonging to their own run, and let within-run comparisons carry the rules.

---

## The disposition

None of these ghosts is load-bearing for a claim the program actually makes. G1 and G3 are execution refinements
with sound remedies; G2 is an honest boundary of what the courts measured; G7 is now measured and reproduced (twice), and
G8 has turned from a hunch into a confirmed split with no single dominant phase; G11 is now measured and confirmed (costly here,
and not a faithful scaling); G4, G5, G6, G9, G10, G12 and G13 are caveats a careful reader must carry, recorded so they are carried on
purpose.
The program's value is that it *knows* these are ghosts and *says so* — a result the gate could not prove is graded
exactly that far and no further. That is the whole point of the discipline: a dead end is documented as rigorously
as a win, and a hypothesis is never dressed as a measurement.
