<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2026 Daniel J. Dillberg -->

# Ghosts — what the gate does not prove

*The honest catalog. A "ghost" is a thing that is true-enough to ship but not yet nailed down: an unproven
assumption, a caveat the numbers carry, a soundness question the compiler cannot answer, a claim graded below the
confidence its headline might suggest. Each ghost is stated plainly, graded, and given an **exorcism** — the
specific measurement or change that would lay it to rest. Nothing here is a defect the gate missed; these are the
edges of what the gate is designed to prove. `integrity ≠ truth`, and this file is where that motto is paid for.*

The grades borrow the claim ladder: **ESTABLISHED / MEASURED / UNDERDETERMINED / SPECULATIVE / NOT_MEASURED**, plus
**SOUND?** for the one memory-model question and **OBSERVED** for something seen once, outside the gate.

**Where they sit.** G1–G6 are the renderer's. G7–G13 are the present path's. G14–G23 came with the live editor and
admission. G24–G26 came with the courts over the gate's own refusals. G27 is the design surface's, and G28 the
batch's. Each folder's
README names the ones that live in it.

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

The choice is now made (PRESENTATION-CHOICE-0, `4a7a32d9`): the certified picture 1:1 in a borderless window, so no
reduction at all. PRESENT-EXACT-0 (`bc910e2f`) implements it and adds the missing check: the composed screen under the
window, read back, must equal the certified picture byte for byte. Once that court has run, the ghost's last clause,
"which no row checks", is answered for the chosen presentation. The half-size windows keep showing the AND-reduction
as the frozen instrument they are.

The readback's first use on the host found something nothing had checked before. The composed screen is not only
what the shell hands the compositor: the host's performance overlay (a translucent bar across 446×28 pixels at the top
of the screen) is drawn over every window, dimming the certified picture there to about 70%. Everywhere else, frame 0
read back exact under both calls (a probe, not yet a sealed court). The court refused rather than measuring around the
bar. With the overlay off it ran twice, and **the composed screen equalled the certified picture on all 20 checked frames
under both calls**, 0 differing bytes. For the chosen presentation (1:1, borderless, SetDIBitsToDevice adopted), the
ghost's last clause, "which no row checks", is answered on this host up to the composed screen, while nothing draws over
the window. What lies past composition (scan-out, the panel) stays outside every witness. The shipped presenter
(`shell show`, PRESENT-EXACT-0 LOCK) carries the check with it: it reads the screen back after every present and says
when the screen is not the certified picture.

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

**Since the live rungs.** Half of this ghost is laid. A loop ships: from LIVE-LOOP-0 on, the live windows render
every composition from the current state, through `LoopRenderer` at the four facings and through BEARING-FAST-0's
tread at a free heading. The other half stands, and is now sharper: that shipped loop has never had its phases
timed. The courts' numbers are still the modelled loop's, and nothing licenses carrying them to the live editor,
which also drains input, closes ticks, journals events and reads the screen back (G21).

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
PRESENT-EXACT-0's two runs add a pair without drift: they were within 2% at p50, with memory at 85–86% before both.
HOST-STATE-1 now provides the two missing witnesses: the clock as the OS computes it (% Processor Performance against
the nominal frequency, uncapped, so boost shows) and the system's paging rates. Both are recorded, never read by a rule,
and only by a court whose own entry asks for them. They can make a drift explainable. They cannot explain it. Their
first look already separates two things G13's association had merged: 94% memory load came with 1 hard fault per
second, so a high memory load does not by itself mean paging (one second, one look). DRIFT-0 (preregistered) is the
designed measurement of this ghost: the same locked court, 3 sittings of 4 runs, host state beside each, and a
descriptive panel of within-run and between-run variation, with no verdict.

**Exorcism.** Keep recording, and don't control yet. Each further pair of runs either repeats the association (slow runs
under memory pressure) or breaks it (a slow run with memory to spare, which would say the recorded state is
insufficient). Only after that, and preregistered, might a court hold memory pressure or the power state fixed. Until
then, read absolute milliseconds as belonging to their own run, and let within-run comparisons carry the rules.

---

## G14 — the live editor's laws are proven over a mock, and the host runs are few · ESTABLISHED (the mock); MEASURED (each host run, n = 1)

Every law of the live editor is a row over a mock surface: a scripted mouse, scripted keys, scripted focus, and a
clock that is the composition count. Those rows run on every gate, and they prove the loop's logic: one command a
tick, the capture rule, the byte check before every present, the save's recomputation. What they cannot prove is
what Windows delivers. That is the host's, and the host's evidence is a handful of runs, each sealed as its own
record and each one run: LIVE-LOOP-0 one walk, LIVE-INPUT-0 three, LIVE-SESSION-0 two saved walks, LIVE-AUTHOR-0
four, HOLD-WALK-0 one held walk, MOUSE-LOOK-0 two, ADMIT-0 one admission and one stale refusal. Several host paths
have never been exercised at all: recovery from a real crash, a refused edit, coalesced repeats.

**Exorcism.** More runs, each sealed, and the unexercised paths walked on purpose (kill a live run and resume its
journal; hold a key into a composition that already admitted one). A scripted host driver was considered and is
recorded as not part of LIVE-SESSION-0; it would trade a real hand for repeatability and would be its own rung.

---

## G15 — between the checks nothing is witnessed · ESTABLISHED (as a limit)

The live loop compares the bytes it hands the present call with a reference on every composition. Past that call
it samples. The composed screen is read back on the first composition after a change and then at one composition
in 75. A frame at a free heading is rendered by the fast tread and recomputed by the reference, off the loop, at
one frame in 64; only the save recomputes every such frame, and it refuses the save if one differs. So a picture
that was wrong on the glass for a few compositions between readbacks would not be seen, and a fast-path defect that
struck only unsampled frames would be caught at the save and not while the run was live.

**Exorcism.** The periods are registered constants and tightening either is a registered change with a measured
cost. The stronger remedy for the screen is an independent witness (capture hardware, or a second reader of the
composed surface), which the route names for PRESENT-1: the GDI readback cannot be assumed to survive a move off
GDI.

---

## G16 — a seal is a hash, and durability is the file system's promise · ESTABLISHED (as a limit)

A saved session's seal is the sha256 of its bytes before the seal. It shows the file is whole. It does not show who
wrote it: anyone who can write the file can reseal it, and what catches a forgery is the replay (a forged event
does not reproduce its witness) and the committed RECORD-0 copy, not the seal. A session's head is likewise a
single-writer chain's integrity and not its authorship. And "journaled before it counts" means flushed: a disk that
acknowledges a flush it did not perform is outside every claim here, and the crash courts end a process at
registered points; they do not cut the power.

**Exorcism.** A signature, and with it a key, an identity and a threat model, none of which the program has or
claims. Until a rung registers one, read "sealed" as "whole", never as "authentic".

---

## G17 — the shell replays the session with its own copy of the workshop's fold · ESTABLISHED (read from the code)

The charter says the shell contains no authority mirror. The live editor keeps the session in the shell's process
(`playback::LiveSession`): the log, and by replaying it, W, M, the camera and the head. That replay is a second
implementation of the rule `workshop/sessionwalk.rs` defines, with the fold's constants written twice. It was
declared when SHELL-PLAYBACK landed and it is now load-bearing. What holds the two together is not shared text.
It is that every saved session is replayed by the workshop's own tool before it is sealed as a record, that the
gate replays each scripted session through both, and that the workshop renders with the reference kernels only, so
the check shares neither the fold's text nor the renderer with the thing checked.

**Exorcism.** Not a clear one. Sharing one text of the fold by path, as READER-COURT-0 is registered to do for the
reader beneath it, would remove the second copy and with it the redundancy that makes the cross-check worth
something. Which is wanted is the owner's to rule, and nothing on the route changes it.

---

## G18 — the fast bearing path beyond its court · ESTABLISHED (the court); DECLARED (the angle bound)

BEARING-FAST-0 holds the fast tread to the reference byte for byte over a court set of 1,972 cameras, at every
thread count in its threads set, and on the host over a sweep of 622,440 frames. Outside those sets agreement is
not compared; it rests on the exact arithmetic the gate bounds and checks for overflow. The live editor then
samples it (G15) and recomputes every saved frame, which is evidence about the sessions actually walked and
nothing wider. The bound on how far a registered heading's angle lies from its nominal millidegree is declared, as
it is in Urðr.

**Exorcism.** The natural first theorem, named in the roadmap: for every admissible row, camera and scene, the
exact walker produces the same pixel inputs as the reference. Until then, every free-heading frame of every saved
session is recomputed, which makes the claim per-session and exact.

---

## G19 — the saved form had many readers, and on hostile input they disagreed · ESTABLISHED (the remedy, on the gate); limits stated

Everything the tree saves and reads back is JSON, and it is read by four Rust parsers (one text copied into three
files, and a different one in `workshop/edit.rs`) and four Python tools that use `json.load`. Given 19 hostile
inputs, the Rust reader and Python's differed on 12, and on three the Rust reader returned no verdict at all (two
panics and one abort). The three writers also
spell two control characters two ways, and the integer bound belongs to one reader and to no writer. None of this
touches a file the tree has ever written: every committed record, the host's records and its saved sessions lie
inside a small common language. It is a seam, and it sits directly under ADMIT-0, which reads the session through
it.

**Exorcism.** READER-COURT-0 (`f53017cd`), built: the saved form is one bounded language, one Rust reader shared by
path replaces the four parsers, an independent Python reader with no `json.loads` beneath it replaces `json.load`
in the four tools, and every writer checks its bytes before it writes them. On each of the 19 inputs both readers
and every command now give one verdict, a code and a byte offset, and none panics.

**What remains of it.** The court's reach, not the old disagreement. The two readers agree on every single-byte
mutant of three small documents and on the registered boundary mutations of real files, and on nothing they were
not shown. Both were written by one author from one grammar (G23). The raws a command writes, the two logs, the
registry and the frozen JSON under `oracle/` are read as before and are not the saved form. And outside the shell's
save, a writer's check is held by source: that shows it is written before the write, not that it fires.

---

## G20 — what an admission does not record · ESTABLISHED (as a limit)

ADMIT-0 admits a proposal as one ordinary edit and writes an envelope beside it: the language, the proposer's
handle, the proposal's digest, the two identities, the two heads, the grant. Four things it is not. The handle is
64 hex digits the proposal claims; nothing authenticates it. The digest cannot be recomputed later, because the
proposal's bytes are not kept. The grant is whatever the admitting command line said; it is recorded, not judged.
And the envelope is the admitting shell's own record under a seal that is a hash (G16). Nothing here shows that a
model can write a proposal worth admitting, or any safety property of a system that includes one: no model is in
the tree, and the gate wrote every proposal the rows admit. The vocabulary is a cell opened or closed and a tile
class painted, and no more.

**Exorcism.** None of these is a patch; each would be registered as its own rung, and none is: a proposal's bytes
kept, so that its digest can be recomputed; an authenticated proposer, which needs G16's signature; a model at the
seam, which is LIVE-AI-EDIT-0, declared and not registered.

---

## G21 — the live loop has no latency, frame-rate or feel number · NOT_MEASURED

By design an input is applied up to one tick and one composition after it is drained, and its tick is the tick it
was drained in, not the moment the device moved. What that costs on the screen has not been measured. Nor has what
a look costs phase by phase, how often the loop fell behind the tick schedule on the host, or why. For admission the
run ledger's wall-clock stamps give two intervals, 44.2 s for the first admission and 16.3 s for the stale refusal,
one run each; they are observations, no rule reads them, and what an admission costs is not measured. The
present-path courts (G7–G13) measured a different,
modelled loop and their numbers do not carry over (G12).

**Exorcism.** The presentation and latency measurement the route places after mouse-look: input to photon in
separate segments, each with its own instrument, registered before its number. Frame rate alone is no claim.

---

## G22 — two host observations have no explanation · UNDERDETERMINED

In LIVE-INPUT-0's first host run no key press reached the window: 31,640 compositions, every readback exact, no
event. In MOUSE-LOOK-0's first host run no mouse report reached the loop: the keys walked on the tick and no look
was made. Each later run worked. For the mouse, the window's read of raw input was changed between the runs and
counters were added, and nothing shows the old read was what failed, or that the mouse was moved in the first run
at all. For the keys, keyboard focus is the leading candidate (the window is topmost, so it sits on top whether or
not it holds the keyboard) and it stays a candidate, because that run recorded no focus state.

**Exorcism.** These cannot be settled after the fact; the runs left consoles and counts. What exists now is the
means to see a recurrence: the window counts the raw input it receives before it reads it, and every run leaves a
ledger line. A recurrence would be a recorded event with counters beside it and not a recollection.

---

## G23 — two implementations by one author agree · ESTABLISHED (as a limit)

Several of the program's strongest checks are a pair held against each other: the envelope written in Python and in
Rust, the fold in the workshop and in the gate's Python twin, the recognizer of VRDNP1 and the gate's independent
one over 513,792 single-byte mutants, and the two readers of the saved form over 163,072. One author wrote both
halves of each from one description. Their agreement shows the two are consistent with each other. It cannot show
that the description was right, and a misreading shared by both would pass every such row.

**Exorcism.** What stands against a shared mistake is what neither implementation produced: cases whose verdicts
are written into the registration before either reader exists, offsets computed from where a mutation was placed
and not by a reader, the writers' own output as a positive witness, and the frozen oracle, which was computed by a
different program at a different time. A second author or a mechanized grammar would close more of it and neither
is on the route.

## G24 — a refusal is held to its code, not to its cause · ESTABLISHED (the court, on the gate here); MEASURED (the host's gate, one run); limits stated

Before REASON-COURT-0 a row held a refusal's reason only as that row was written: 73 of the 103 coded checks look
for the code anywhere in the output, 22 hold only that the subject refused, and nothing held a refusal to its code
from outside the row. The court is built and passes here and on the host. What it leaves:

- **A code is not a cause.** `INVALID-EDIT` answers six different edits and `DIVERGED` four forgeries. The text
  that tells them apart is, by ruling, not locked.
- **42 refusal checks are `REFUSE(any)`.** Each is a registered decision with its reason. 21 are sealers, which
  have no codes.
- **Debts.** 16 planted records of the sealers and 2 forged envelopes have no accepted twin one mutation away, so
  their refusal is not tied to the field the row names. Five statements judge a refusal for its reason and hold a
  word or an exit status where a code is owed. They are listed, not paid.
- **The watch counts by group.** It knows how many endings of a row, program and command carry a code, not which
  input drew it. Where a group holds coded and open slots together and one more ending carries the code than is
  owed, a changed code can hide: three groups today (`shell-blit-law`, `refusallog-bijection`, `bearing-refuse`).
  The row's own statement judges those endings.
- **Inside the gate's process the watch sees nothing.** 15 coded checks are judged there (an exception's key, a
  verdict line, a trace) and stay held by their row alone. Counted once, off the gate: 142,083 refusal-type
  exceptions are raised there in a run, 74 of them the sealers' and 32 the envelope's, and all but one are claimed
  by a registered statement or by the agreement court. Thirteen more statements judge a refusal that is neither a
  child's non-zero ending nor an exception there, and no tap hears those. A watch over the raises is its own
  slice, MINT-WATCH-0, built since (G26).
- **Each machine has run the built gate a few times at most.** The host ran it once: 232 of 232. Its rows' texts,
  which carry the counts and name the listener's tap, were not printed, because the run was the compact one.
- **The source row holds text, not meaning.** It shows that a judging statement still stands, word for word. It
  does not show that the statement is reached, or that the row acts on it. A statement rewritten to say the same
  thing in other words reddens it.

**Exorcism.** Paying a debt is a code in a sealer or an accepted twin in a row, each a
decision of its own. Telling causes apart would mean locking text, which the owner ruled out. For the
gate's own process two remedies are declared and not seated: an accounting of every refusal site, and the sealers'
refusals turned from an exception into a datum. The first closes a missed check and not a missed kind; the second
changes the sealers.

## G25 — the gate trusts 63 lines that programs print about themselves · ESTABLISHED (counted in the census)

63 functions of the gate run a program and require a line it prints about its own court: the kernel's `selfcheck
OK` and its equality verdicts, the shell's `blit_roundtrip OK`, the mock courts' `court OK`, the admission
self-test, Urðr's own suites. What the program checks before it prints that line is in the program. The gate holds
the line; the census did not read the Rust behind it, and REASON-COURT-0 registers those courts as outside.

**Exorcism.** None on the route. Where it matters most the gate already does more than trust the line: the saved
form's court compares every line the Rust reader writes with the Python reader's, and the admission court compares
the shell's verdicts with the gate's own recognizer by digest. The others are a program vouching for itself, with
the frozen oracle and the plants as the outside checks.

## G26 — the mint register is a measurement, most of its sites were never reached, and a mint is not a judgment · ESTABLISHED (the watch, on the gate here); OBSERVED (the measured layer); limits stated

MINT-WATCH-0 is built and passes here and on the host. What it holds, and what it does not:

- **The counts were heard, not derived.** 142,082 mints in 70 entries are what four passes raised, one per
  configuration. All four agree. That shows the gate's in-process refusals recur; it does not show one of them is
  right. The entry says so in those terms, and the rule that an expected reason never comes from what a program
  does is not bent by it.
- **105 of 164 raise sites were never reached.** 90 of them are in the eleven sealer files. A sealer's host path
  and its command line are not run by the gate, and the register says only that those sites were not reached. By
  the owner's ruling they stay facts about reach, and are not expectations that a refusal be planted there.
- **A mint is counted where it is raised.** What catches it, and whether anything judges it, is not seen. A
  refusal raised and swallowed looks the same as one a statement requires. The gate's own plant is the known case.
- **Counts are by row and site, not by input.** Two plants of one row that exchanged the sites refusing them would
  leave every count as it was. One plant that moves to another site moves two counts, and that is caught.
- **The watch hears up to its own row.** A row that a later rung places after it is not heard by it until that
  rung says how. REASON-COURT-0's six rows, which were not built when the register was measured, have since been
  heard once by the instrument: they raise no refusal.
- **The instrument that took the measurement is outside the repository.** Its four reports are named by hash and
  are not in the tree. The gate's own tap follows the same rule for a mint, and on the three interpreters tried
  here it heard the same counts.
- **A skipped row has never happened.** Its entries are then not expected; no pass has skipped a row, and the rule
  is held by plants alone.
- **On an interpreter before 3.12 the tap is the thread's one trace function.** Anything else that sets a trace
  function there, a debugger for one, takes the tap's place, and the watch says the entries were not heard.

**Exorcism.** For the first: none wanted — a registered measurement is the design, and the remedy for drift is an
amendment. For the sites never reached: none on the route; the register says only that they were not reached.
For the third and fourth: a refusal that is a datum with its input beside it, which is the declared emission rung
and changes the sealers.

## G27 — the design surface is not certified · ESTABLISHED (its own checks, off the gate); OBSERVED (its cost, one sitting)

`design/` is content time. What it is not:

- **Not on the gate.** Its twelve checks are its own. They run it against a real shell and plant what they claim to
  catch, and no row holds them. A defect in the tool can show a wrong top view or propose the wrong cells; it
  cannot admit what the shell refuses, because the tool has no way to change a session but the shell.
- **Its view is a second reading of the world.** It replays a session's edits over the base level itself to draw
  from above. The shell's replay is the authority. The tool checks the base files against the session's hashes and
  takes the head from the shell; the cells in between are its own arithmetic.
- **It was slow, by a named cause, and is not for that cause now.** Over ADMIT-0 a design of 60 cells took about
  20 s to preview and 20 s to admit: one operation per run of the shell. With DESIGN-EVENT-0 a design is one batch
  and one run. On the build container that design previews in 0.10 s and admits in 0.13 s. The host's time is not
  measured.
- **No objects, no constraints.** A room is a statement that expands to cells. "Reachable from the camera" is a
  reading the tool computes and nothing holds.
- **The project's pointer is not sealed.** Which session is current, and the history behind `undo`, are a file the
  tool writes. Every session it points at is sealed; the pointer is not.
- **A model has not used it.** The design text was written by hand in every check.

**Exorcism.** For the cost: done, by DESIGN-EVENT-0 (G28 holds what that leaves). For the view: the shell printing
the world of a session, so that the tool draws what the verifier replayed. For the pointer and the model: use, and
what it shows.

---

## G28 — the batch is built; what it leaves open · ESTABLISHED (the six rows, on the gate here); MEASURED (host: the gate, 242 of 242 on each of its runs, FULL×2 on two of them); limits stated; its cost on the host NOT_MEASURED

DESIGN-EVENT-0 is built, and the gate passes with it here and on the host. A design is one batch, admitted whole or
refused whole. What that does not give:

- **The compiler was not certified, and now is.** The seam holds the normal form: one byte sequence for each
  change set. What turned a design into that change set was content time. DESIGN-IR/DIFF-0 (`2baa42f3`) is built:
  the compiler is the shell's, held to a reference and to the design's target. What that leaves open is G29.
- **Two of the tool's rules are nobody else's.** The design tool refuses a design that closes the camera's cell or
  writes over a stair, and called both refusals it predicted of the seam. The seam makes neither: the admission
  admits a batch that closes the camera's cell, and one that opens a stair (seen with the shell as built,
  2026-10-07). Until the compiler is built those rules are held by uncertified Python, and after it they are the
  source language's and still not the authority's: a batch from any other editor is not held to them. The owner
  ruled that this stays so in DESIGN-IR/DIFF-0, and carries the question forward unanswered: *Should camera/stair
  validity be an authority invariant, or deliberately remain a property of the design language?*
- **The cost of an admission still grows with the session.** Every admission replays the whole parent and verifies
  the file it wrote. The memo removes a megabyte of hashing from each cell edit and nothing else. Verifying only
  the change is deferred by name: a seal is a hash, and no earlier verification is something a later run may rely on.
- **A batch's records are flushed one by one.** An earlier fence holds the one path a journal record is written
  by. The build went through it. What N flushes cost on the host is not measured. The owner's word: *The Windows
  journal-flush cost remains an explicit performance unknown.*
- **The times are development measurements.** 0.10 s and 0.13 s are the build container's, one sitting. By the
  owner's word they are not made a row.
- **The host's runs are all compact.** 242 of 242 each time; after the first, each on a tree that differs from the
  one before in documents only. What they printed reads the same. The rows' counts were printed by none. The runs
  are listed in [`verify/RUNGS.md`](../verify/RUNGS.md).
- **On the host the gate is FULL×2 as far as its witnesses reach.** The owner's predicate asks for the same tree and
  the same output, and two host runs gave both. The tree's identity there is Git's id of the commit's tree with a
  status that lists nothing, taken before the first run and after the second: files Git ignores are outside it, the
  gate's build directory among them. The outputs were compared as printed, and no digest of them was taken there.
  And the gate prints nothing of the tree it ran on, so on either machine a tree's identity is taken outside it;
  where it is not taken, it is not established.
- **No verifier rebuilds a proposal.** Deferred by the owner's ruling, outside this rung, in his words: *The
  verifier does not reconstruct VRDNP2 proposal bytes from admitted events or independently recompute the proposal
  digest. Doing so would introduce a second VRDNP2 writer into the verification path and is outside the present
  admission boundary. Reopen only if durable independent provenance of the original proposal bytes becomes a
  requirement.*
- **The shell's read-back is not a check of the memo.** It replays the file it wrote with the same memo. A shell
  planted with a wrong one calls its own file verified, and the court shows it. The workshop, which keeps no memo,
  is the check, and the workshop runs when a session is sealed, not when it is designed.
- **That plant depends on its parent.** The wrong memo fools the read-back only where the parent's own history has
  no cell edit after a paint. Elsewhere the read-back replays that history under the same plant and refuses. The
  court plants it where it bites. The other case was seen and is held by no row.
- **Two pins on a text became a check on values.** `liveinput-fence` and `liveauthor-fence` held, by its text, that
  an edit's content is computed by the reference replay's own statement. They now hold the memo's statements. That
  the two agree is a comparison over the sessions the court replays. A text pin held it for every session.
- **The bound is above the world.** The language allows 4,096 operations. The lattice is 48, so 2,121 is the most
  that could ever be admitted and 2,120 the most the court's level admits. 4,096 is held only as a refusal.
- **Equivalence is shown where it can be run.** One at a time, 60 operations is the court's largest. For 2,120 the
  reference is two independent replays.
- **A binding is not a look.** An admission bound to a preview has the previewed bytes and reaches the previewed
  head. Whether anyone looked at the preview is not recorded, and an admission with no preview is legal.
- **ADMIT-0's plant borrowed a name.** Its row forges an eight-member envelope naming `VRDNP2`. It is refused where
  and as it was. The name is now a registered language, so the plant shows less than its label says; an unknown
  language is planted again by this rung as `VRDNP3`.
- **This rung's rows are heard by neither watch.** They run after both. Their endings are judged by the rung's own
  last row, by code head. What they raise inside the gate's process is not registered anywhere as measured.
- **One mutant is equivalent.** The loader's check that a place is not above its count never decides: a batch that
  is whole and in order cannot hold such a place. It is kept as the envelope's form.
- **The registration was not blind.** A prototype ran before it was committed. The registered head predates the
  prototype; the deaths, the largest batch and the forged envelopes were seen to behave as drafted first.
- **One consumer.** That every editor speaks the same event is declared. The design tool is the only editor there
  is.

**Exorcism.** For the compiler: DESIGN-IR/DIFF-0, built. For the two rules, as far as designs go: the same
rung. For the cost:
the host's own time for a design, which the owner's run will give, and, if replay ever has to be skipped, a rung
that gives a session a trust root. For the memo outside the court: the workshop at sealing, as now. For the
proposal's bytes: nothing, unless the requirement the ruling names arrives. For the last: a second editor.

## G29 — a predicate about the present, written into a row that outlives it · ESTABLISHED (three met and restated, on the gate here); MEASURED (host: the gate, 247 of 247 twice on one tree, FULL×2); one more known and not met; the compiler's own limits stated

DESIGN-IR/DIFF-0 is built. Its build met the same ghost three times, and the owner gave it one name: *history is
immutable; state may evolve; transitions must preserve provenance.* A row that says *today* or *last* is true when
it is written and false after the next legitimate change.

- **Met: a pin held against today.** `designevent-preregistered` held each pin an amendment moved as the file as
  built. The next amendment to move one of them broke it, and no pin could mend it, because an entry is never
  edited. Restated as a chain: an amendment starts where the one before it ended.
- **Met: rows held as the last.** `designevent-fence` held its six rows as the gate's last six. Restated as a
  position: the six that follow the 236.
- **Met: a corpus that could not grow.** A planted defect survived the three registered parents. Restated: the
  registered corpus stands as history, and the current one names what was added and why.
- **Known, not met.** MINT-WATCH-0a's pin on `verify/livesession.py` is still held against the file as built. That
  file does not change with this rung. The first rung that changes it will meet this.
- **This rung's own source reading will be met too.** `designir-fence` reads the command's arm and the compiler's
  functions by their text. A later rung that changes either moves more than a pin, and the stop clause applies
  again. *Met by HERMENEUTICS-0:* two of this rung's rows held the plants to eleven and the reference to this rung
  alone, and that rung's instrument needed both widened. The owner ruled the least widening (HERMENEUTICS-0a); each
  changed line is marked in its row.
- **The origin rests on a commit.** The 56 pins the first court found are registered as a digest computed with
  this build and checked against the gate's table at the commit that built that court. That entry itself names no
  hash.
- **A pin names a file.** It shows the bytes and nothing of why they changed. Intent is held by rows that exercise
  it. A byte changed where no row looks is caught by nothing but the pin's refusal to move without an entry.
- **Equivalence is shown where the court compiles.** Sixteen designs on four parents, and the single-byte mutants
  of three designs. Nothing is shown for every design.
- **A shared misreading is caught by neither equality.** The compiler and the reference are two programs written
  from one description by one hand, and the target is taken by the gate's own reading. HERMENEUTICS-0 is built for
  that: both programs are held to the owner's literal targets at ten designs and to four laws at their instances, and
  five shared misreadings, planted alike, are caught. Anywhere else a shared misreading is still caught by
  neither.
- **The camera's and the stair's rules are still the language's.** A batch from any other editor is not held to
  them. The owner's question on that is carried and not answered.
- **Five checks decide only because another has not.** The printable check and the word split, the colour's digit
  count and its bound, paint's word count on both sides. Each is equivalent alone. Each pair together is caught.
- **Four defects were caught only by the broad court.** No named case reaches the border's first and last rows,
  a level read one row short, or paint with a fourth word. The single-byte mutants do. A sample of them might not.
- **One ending has no code.** A failed write to standard output ends 1. No row reaches it.
- **Two usage refusals cannot be run.** That `design-compile` takes no plant, and that the selftest takes only a
  registered one, are held by reading the arm. A usage refusal has no registered code, so no row may require it.
- **The mutation campaign is one sitting.** Its mutants are the ones that were written. One of them was no mutant
  at all and is named.
- **The tool is a client by its own checks.** CLIENT-FENCE-0 is off the gate by the owner's locks. It holds the
  tool as it stands and says nothing of a tool that is replaced.
- **The host has run the gate, and no time.** 247 of 247 twice on one tree, FULL×2, and the tool's own checks once.
  The output carries no time: what a compile costs on Windows is not measured.
- **No compile is checked as it is made.** The court holds the compiler on sixteen designs and the mutants of
  three. The owner rejected a per-compile check for this rung and keeps it here, for a later rung: *validate every
  actual compile against the statements applied to it, without making content-time validation part of DIFF-0.* It
  would collapse the thing compiled and the court that judges it.
- **The ledger has no head.** Each entry is locked by its own hash and held by a constant in the gate. Nothing
  commits to the ledger as a whole, so that a later ledger is shown to extend an earlier one. Deferred by his
  ruling: it answers a later question.
- **The layout holds 58 files.** Outside them the gate keeps no origin: its own text, the ledger, the registers,
  the design tool, the documents. There a transition is what Git's comparison of two commits says.
- **A file moved back to its origin would be refused.** It would be named as changed and would not differ. The
  relation as ruled refuses that tree, and the case would be his to rule.
- **The origin's digest is a commitment, not a truth.** It anchors which pins the history began from. It says
  nothing of whether those files are right.
- **Two machines, two trees.** The host's tree holds its records and is not the container's. What was compared is
  what the gate printed, and the registered values the rows hold.

**Exorcism.** For the present tense: write a row about history, and let the stop clause catch the ones not yet
found. For the shared misreading: HERMENEUTICS-0. For every design: a later rung, by his ruling. For the ledger's
head: deferred. For the cost on the host: a time taken there.

## G30 — a row that read the clock without meaning to · OBSERVED (one failed pass in the build container, its cause read from the log it left); its rate an estimate; ruled a defect of the gate and corrected (`REFUSAL-WHY-1a`); two rows of the same form named and left

The gate failed once on a tree that was right. `refusalwhy1-log` holds that a mock overlay's pid never reaches the
refusal log, and tests it by looking for the four digits `4242` anywhere in the log's text. Every record in that
log carries the clock. For a hundred seconds the clock's own digits held `4242`, and the pass ran inside them.

- **A row's outcome depended on the time of day.** The rule that no row reads a wall-clock number was written about
  numbers a row compares. This row compared no number. It searched text that had a number in it.
- **About one run in three hundred.** An estimate from sampled start times, not a measurement. Rare enough that
  dozens of runs on two machines never met it, common enough to meet in a long life.
- **A failure of this kind looks like a finding.** The line it prints says a pid reached the log. It takes reading
  the log to see that nothing did.
- **FULL×2 does not protect against it, and is not broken by it.** Two runs on one tree with one output is still
  the claim. A run that fails for the clock's reason is a run that did not pass: it is said, and the tree is run
  again. It is never dropped silently.
- **It is corrected, by the owner's ruling.** *A real gate defect, not a tree defect.* The row reads each record's
  context and named members. It keeps no list of things to skip: his word was that one more exclusion would only
  move the accidental dependence. No reason was registered for it.
- **One commit, two verdicts.** The same commit, untouched, passed whole when run again. The clock was the only
  difference.
- **It can be made to happen.** With the shell's clock moved into the colliding seconds, the row as it was fails
  every time and the corrected row passes. A second route, through the ids minted from the clock in hexadecimal,
  fails the same way; its next window is 2026-10-16, 01:09:44 UTC, for sixty-five seconds.
- **The class was read, and holds two more rows in form.** `mouselook-capture` searches a saved session's whole
  data for five words about focus. `presentexact-sealer` searches a record's whole data for one word. Neither word
  can be spelled by a clock, an id or a digest, so neither has a source of chance. They are not changed.
- **The reading has an edge.** It is by syntax: membership tests, counts, finds, matches. A search built another
  way is outside it. And a path that a program prints can hold any word.
- **The real leaks were mostly caught elsewhere.** Of six defects planted in the shell, four were caught by the
  row's exact comparison of its fields before the corrected test ran. The corrected test is what catches a leak
  into a field that was not there before.

**Exorcism.** Done for this row: `REFUSAL-WHY-1a`. For the two rows of the same form: the owner's ruling, if a
source of chance for their words is ever found. For searches built another way: a wider reading.

## G31 — the folder the tree is checked out in, read without meaning to · OBSERVED (one whole pass in a perturbed environment, in the build container, bisected); MEASURED (host: one run in a clone under a folder with a space, the four rows predicted before it); repaired by INPUT-0a (built; both predictions met; FULL×2 on the host; pushed)

- **What happened.** One whole pass of the gate, off the gate, with seven things about its surroundings changed at
  once. It read 243 PASS / 4 FAIL. `input-tamper`, `input-not-authority` and `input-demo` could not read a level:
  the path they named had been cut at a space.
- **The cause, read from the source.** A walk file's `level` and `tiles` lines take one word each. The rows write
  into the walk the absolute path of the oracle's files, joined from wherever the tree is checked out.
- **One cause, four FAILs.** The fourth was `reasoncourt-watch`. It heard the input program's three refusals,
  endings no group of the register holds, and said so. That is the watch working, and a reason a count of red rows
  is not a count of defects.
- **Repetition cannot see it.** FULL×2 runs twice in one folder. The host's re-run is another folder on another
  machine, and its path has no space either.
- **Bisected.** With the rows run alone: a path with a space and nothing else fails the three; a path with `ð` and
  no space passes them.
- **What the pass did not find.** Nothing else failed: not a clock in 2041 whose every millisecond held `4242`, not
  a time zone fourteen hours ahead, a Turkish locale, umask 077, another home folder or another hash seed. Seven
  things were changed together, and only the space was isolated.
- **On Windows, measured.** The four rows were named before the run. The owner cloned the tree under a folder
  with a space in its name, and the gate failed exactly those four, the other 243 passing.
- **The cut path named something real.** On the host it became the owner's own checkout folder, and Windows refused
  to read a folder as a file. A walk's line keeps its first words and drops the rest without refusing, so a cut path
  that named a readable file would be read. Not measured.
- **The class, by syntax.** Of three Rust readers that split a line on whitespace, the walk and the level text drop
  the words they do not use; the camera list refuses them. Only the walk and the camera list carry a path, and the
  camera list refuses a path with a space with its line.
- **Repaired, by his ruling: INPUT-0a.** `level` and `tiles` take the rest of the line. `input-tamper` writes its
  walk through a folder whose name holds a space, so every gate holds the repair wherever the tree is checked out.
  With first-word parsing restored, that row fails. The perturbed whole pass that found the defect, run again on the
  repaired tree as the entry predicted, read 247 rows / 0 fail.
- **And on the host.** The owner's clone under a folder with a space, run twice by the witness: 247 rows / 0 fail,
  FULL×2, as the entry predicted. Pushed, `59edc01..a16d663`.
- **What is left.** The walk's other lines, which still drop words they do not use (G32).

**Exorcism.** Done, by INPUT-0a, on both machines.

## G32 — a walk's other lines drop the words they do not use · DECLARED (read from the source); not demonstrated; recorded and not registered, by the owner's ruling

- **What the source says.** After INPUT-0a, `level` and `tiles` take the rest of their line. `camera` keeps three
  words, and `commands` and `head` keep one; anything after them is dropped without a refusal. A walk written
  `commands LFF RFF` means `LFF`, and `input write` writes back `LFF`.
- **Nothing has been shown to go wrong by it.** No run met it.
- **Why it is not fixed.** A refusal would need a plant in a row, the plant an ending, and the ending a statement of
  the reason register. The owner: *don't add a refusal and reason-register entry for a defect that hasn't been
  demonstrated.*

**Exorcism.** The owner's ruling, when a case shows it.

## G33 — a row rests on what an earlier row left · OBSERVED (seven cases on one row, in the build container); repaired for the walk's rung by INPUT-0b (Lazy Setup; its six predictions met, the sixth on the host, FULL×2 by the witness; pushed); the class beyond it recorded

- **The hypothesis.** The gate runs its rows in one order, and a row can use what an earlier row made: a built
  program, a global it set, a file it left. If a row's verdict changes because an earlier row changed shared state,
  the row's evidence is not its own.
- **One instance, seen by an instrument outside the repository.** Run alone, without `kernel-build` before it,
  `input-demo` raised a `TypeError`: its Python twin uses the kernel's path, which `kernel-build` sets. With
  `kernel-build` first, it passed. That is a dependency on a build, of the kind the gate's order is made for; whether
  it is the kind the hypothesis fears is the owner's to say.
- **What is not done.** No search of every row. No mechanism to run rows apart. His word: *don't add a general
  isolation mechanism before establishing the actual dependency.*

- **Investigated, by his ruling (RUNGS, INPUT-0).** `input-demo` rests on the kernel's executable, handed to it as a
  Python global by `kernel-build`, a row of another rung: without the row it fails, with the file alone it fails,
  with the global and the file handed in by hand it passes. The twin's separate kernel process is the row's design,
  so the prerequisite is intended. It is not declared, and it fails as a crash whose words name a `NoneType`.
- **The class.** Rows that read a build global they do not set, and do not test it for `None`, are many: by syntax,
  32 of 45 for the kernel, 9 of 76 for the shell, all 5 for the walk program.
- **Red, never green.** In the gate's order a missing build turns later rows red. The risk is in the words, which
  name the wrong thing, not in the verdict.

- **Repaired for the walk's rung: INPUT-0b.** The walk's rows ask for the kernel and the walk program where they use
  them, made on first request and kept. Each of the five passes run alone; a kernel that cannot be built is refused in
  words that name it; a bare read given back fails `input-demo` on the gate. On the host, by the witness: FULL×2, 247 /
  0 twice, `f644947d…` at every reading; pushed, `89d082e..b386b85`.
- **What is left.** The other rungs' readers of a build global (the census): untouched, by his word.

**Exorcism.** Done for the walk's rung. For the rest: his ruling, if a reader of another rung is shown to need it.


## G34 — a citation's line number is read and not checked · OBSERVED (read from the source); a real defect of the gate, by the owner's ruling; its repair deferred

`reasoncourt-source` holds each code cited from `verify/RUNGS.md` to the line it quotes. It parses the line number
the citation gives and then asks only whether the quoted text stands on some line. A citation with the wrong line
passes. The refusal's own words say the line *no longer stands there word for word*.

**Exorcism.** Deferred by his ruling (2026-10-09): recorded as a source-validation defect, repaired later. Whether a
citation binds the line or only the text is part of that repair.

## G35 — a record that cites no registration is skipped · OBSERVED (read from the source); a real defect of the gate, by the owner's ruling; its repair deferred

`records-preregistered` joins each sealed record to the ledger entry it cites. A record whose provenance names no
entry is passed over, not refused: an inner join where the rule wants every record of a preregistered rung to cite
its entry.

**Exorcism.** Deferred by his ruling (2026-10-09): recorded as a registration-coverage defect, repaired later. It
changes a registered row, so the repair is an amendment.

## G36 — the witness's empty status is not proof of a clean checkout · OBSERVED (tested with Git 2.43 off the host, not on it); a real limit of the witness, by the owner's ruling

The witness reads `git status --porcelain`. Two things make that print nothing while the checkout differs from what
it shows. A `status.showUntrackedFiles=no` setting hides untracked files. A tracked file flagged `assume-unchanged`
or `skip-worktree` and then edited leaves the status empty and the tree id unchanged, while the gate runs on other
bytes. Both were shown with a local Git, not on the owner's host.

**Exorcism.** Not the witness's, by his ruling: its empty status alone is not to be taken as proof of a clean
checkout. A direct check of the Git state stands beside it at a push.


---

## The disposition

None of these ghosts is load-bearing for a claim the program actually makes. G1 and G3 are execution refinements
with sound remedies; G2 is an honest boundary of what the courts measured; G7 is now measured and reproduced (twice), and
G8 has turned from a hunch into a confirmed split with no single dominant phase; G11 is now measured and confirmed (costly here,
and not a faithful scaling); G4, G5, G6, G9, G10, G12 and G13 are caveats a careful reader must carry, recorded so they are carried on
purpose. Of the live editor's, G14, G15, G16, G18, G20, G23 and G25 are limits of method, stated so no claim is read
past them; G24 is a built court with its reach and its debts stated; G26 is the stated reach of a second built watch; G27 is the first content-time tool, uncertified by design; G28 is the built batch's reach, with what it leaves to the compiler, to the workshop and to the host stated; G17 is a design tension the charter names and the rows hold in check; G19 is a seam whose remedy is
built, with the court's reach stated; G21 is a measurement not yet taken; G22 is two things that happened once and were never
explained. G34 and G35 are defects of the gate and G36 a limit of the host's witness, each recorded by the owner's
ruling for repair later.
The program's value is that it *knows* these are ghosts and *says so* — a result the gate could not prove is graded
exactly that far and no further. That is the whole point of the discipline: a dead end is documented as rigorously
as a win, and a hypothesis is never dressed as a measurement.
