<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2026 Daniel J. Dillberg -->

# Dev notes & review

*Working notes and retrospectives: how each campaign was conducted, what each court found, the process that made
the results durable, and the practices worth keeping. This is the narrative counterpart to the terse ledger in
[`verify/RUNGS.md`](../verify/RUNGS.md). **Part I** is the optimization campaign, from `GAUNTLET-0` to the
`GAUNTLET-2` LOCK, with its epilogue on the present path. **Part II** is the live campaign, from `LIVE-LOOP-0` to
`ADMIT-0`: the window made a place where the world is walked, turned and edited, and where a proposal is admitted.*

---

# Part I — the optimization campaign

---

## The arc, in numbers

The campaign optimized one thing — the emit (texel) pass — and never touched the frozen oracle. The emit's journey,
each tread proven byte-identical to the frozen renderer:

| Rung | Technique | What moved | Same-apparatus result |
|---|---|---|---|
| GAUNTLET-0 | *measure, don't optimize* | named emit the target | emit = 695‰ of the instrumented render |
| GAUNTLET-1a | the differential court, seeded | proved the harness, no technique | exact transcription, byte-identical |
| GAUNTLET-1b | floor divide-collapse | 4 → 2 floor divides/px | 6928 → 5455 µs p99 (~1.27×) |
| GAUNTLET-1c | row-major floor **DDA** | per-pixel → per-row divide (O(rows)) | ~4,734 µs emit p99 (~536× fewer divides) |
| RE-BREAKDOWN-1 | *re-measure, don't optimize* | named the tile fetch (~4.4× the map) | no technique committed |
| LOCALITY-0 | 8×8 **blocked** floor layout | cache-friendlier fetch | 8185 → 7734 µs p99 (~1.07×), blocked LOCKED |
| GAUNTLET-2 | **parallel** column stripping | T threads over the columns | 7734 → ~2355 µs p99 at T=8 (~3.3×) |

The staircase reads **projection arithmetic → data locality → parallel execution** — three genuinely different
levers, not a stack of ever-cleverer projection formulas. Each lever was chosen because a *measurement* pointed at
it, not because it was the next clever idea.

---

## What each court actually found

- **GAUNTLET-0** refused to let the campaign start on intuition. It decomposed the render at the kernel's pub-phase
  boundaries and locked a 500‰ decision rule *before* looking: a phase earns an optimization seat only if it owns
  ≥500‰ of the render p99. Emit cleared it (695‰); the original "incremental floor cast" hypothesis, which named
  `frame()`, would have *died* had `frame()` come in under 500‰. Measure, then optimize.

- **GAUNTLET-1c** is the prettiest single result: the floor's perspective divide, done per *pixel* by the frozen
  emit, becomes a per-*row* Bresenham-exact recurrence — O(rows) divides where there were O(pixels), ~536× fewer on
  the witness. It was validated offline over 2.07M recurrence points and 3.93M facing/assignment texels *before* a
  line of Rust, then proven byte-identical on the gate.

- **RE-BREAKDOWN-1** is the discipline's conscience. After the DDA cut the divides ~536×, the obvious move was
  another arithmetic trick — but the cost structure had *shifted*, so the rung **measured instead of optimized.**
  Its fenced ablation probes (with the RE-BREAKDOWN-1b constant-anchor refinement, so the probe tax cancels in the
  increments) named the *tile fetch* as the new leading cost, ~4.4× the map indirection. That measurement is what
  pointed at LOCALITY-0. Optimizing by intuition here would have polished the wrong thing.

- **LOCALITY-0** is where the *Epistemic Invariance of the Boundary* theorem was born: to compare two memory layouts
  fairly you must hold everything constant except the address arithmetic, hot-swapping the whole binary
  (monomorphize) and process-isolating each variant (clean branch predictor, single-variant I-cache), interleaved so
  drift cancels. Its three exits were ratified before the number, and — crucially — the *third* exit ("neither beats
  the baseline") was made **load-bearing**: it is not a null but a proof that the stall is capacity/LRU-bound, which
  would have redirected the whole trajectory to parallelism *without a single wasted layout patch.* Exit 1 fired
  (blocked won), but the theorem's real gift was certifying the dead end as rigorously as the win.

- **GAUNTLET-2** reframed parallelism as a *property*, not a feature: *partitioning the column domain changes
  execution parallelism but not the certified picture.* The correctness court proved that deterministically over
  contiguous *and* adversarial partitions (strided, reversed, single-column, seeded permutation) — catching any
  shared-state or reduction-order dependency **without spawning a thread.** Only then did the performance court add
  the threads, as pure execution around an already-proven core.

---

## The process rhythm

Every rung ran the same loop, and the loop is the product as much as the code:

    court ──► ratify ──► preregister the decision rule ──► build ──► gate TWICE byte-identical ──►
        deliver as a patch ──► host-run the sealer ──► seal the record ──► (confirm the shape) ──► push

- **Court before build.** Nothing was built until the method — hypothesis, success, failure, interpretation limits —
  was argued and hash-locked. The `preregister.json` entry is the contract; the code is its fulfilment.
- **Gate twice, byte-identical.** A landing condition is two consecutive gate runs whose full logs `sha256` to the
  same value, with `GATE PASSED` and a `RECONCILE` line. Determinism is the floor: a hash-seed-dependent result is
  not a result (`PYTHONHASHSEED=0`).
- **Correctness on the gate, speed off it.** The gate carries no wall-clock. The host sealers (`locality0.py`,
  `gauntlet2.py`) check byte-identity *first*, then time, then seal under the envelope — witnesses before numbers,
  always.
- **The record stores numbers; the reading interprets.** No verdict is ever stored as data. `PROMOTE` and the exit
  lines live in `reading`, computed from the numbers, never as a `pass` key.

---

## Lessons worth keeping

1. **Measure before you optimize, and re-measure after.** RE-BREAKDOWN-1 exists because the cost structure moved;
   skipping it would have optimized the wrong pass. The single most valuable rung committed *no* optimization.

2. **Preregister the decision rule, including the null.** LOCALITY-0's third exit and GAUNTLET-2's memory-hierarchy
   redirect were both written *before* the numbers. When the numbers came, there was nothing to argue about — the
   rule fired. A decision rule chosen after seeing data is a decision looking for a justification.

3. **A dead end is a result.** The whole point of the Epistemic-Invariance boundary is that "neither layout wins"
   would have been a *finding* (capacity-bound, go parallel), not a wasted month. Rigor that only certifies wins is
   half a discipline.

4. **Grade to the evidence, not the headline.** The T=8 plateau *looks* like a bandwidth wall and the reading says
   so — but graded as a *hypothesis supported by variance,* not a bus measurement, because no bus was measured. The
   patch that promoted the threaded emit corrected an earlier, slightly-too-confident phrasing to exactly this.

5. **Reproduce the shape.** One sweep establishes a verdict per the preregistration; a second confirms it is not a
   fluke. GAUNTLET-2 was run twice (T=16 2311/2208, T=8 2360/2355 at 0.2% run-to-run), and `--confirm` was built so
   that confirmation is *durable evidence* — a separate sealed record citing the original — never a silent
   overwrite of the canonical measurement.

6. **Keep the oracle frozen and the apparatus fenced.** `mantle.rs` was never touched; the probes never entered the
   promotion chain (a source-grep gate row enforces it). The renderer and its measurement instruments are different
   authorities, and the gate keeps them apart.

---

## What to watch (pointers into [`GHOSTS.md`](GHOSTS.md))

- The threaded write is race-free but not Miri-clean (G1); a row-band `chunks_mut` decomposition makes it sound.
- The T=8 plateau is a hypothesis, not a bus measurement (G2); a roofline settles it.
- The shell's whole render-start → frame-ready interval is ~15 ms at p50, longer than one refresh on the owner's host,
  and FRAME-SPLIT-0 found, twice, no single dominant phase (blit 427–434‰, emit ~270‰, frame ~255‰, bgr ~137‰): no
  target is promoted (G8). The narrower diagnostic of the largest component, PRESENT-SCALE-0, found the blit's 2:1
  reduction material on this host (the 1:1 blit ~5.3–5.6 ms cheaper at p50, confirmed; G11). Choosing the shell's
  presentation geometry is still a separate court. Two narrower diagnostics have each run twice on the host.
  PRESENT-STRETCH-0 found `COLORONCOLOR`'s blit materially cheaper than the default `BLACKONWHITE`'s in both runs;
  `HALFTONE` read material once and then CONFOUNDED, so it is unresolved. ALLOC-REUSE-0 read ALLOCATION MATERIAL
  twice: reusing the frame's buffers was 1.6–1.8 ms cheaper at the envelope p50. Neither adopts anything.
- The render-loop courts time a modelled loop: the shipped shell renders once (`run`) or pre-renders (`playback-window`)
  and has no per-frame render loop (G12). ALLOC-REUSE-1 therefore adopts only an entry contract for a future live
  loop. Both of its runs passed (reuse's p99 at 886‰ and 929‰ of fresh's), so it reads ADOPT, and ALLOC-REUSE-1 LOCK
  makes `LoopRenderer` the production entry for in-loop rendering, with every fresh render call site pinned.
- The same court can run 40–60% slower on another run the same day (G13). HOST-STATE-0 put memory pressure beside one
  such run: an association, not a cause. Read absolute milliseconds as belonging to their own run.
- What the shell shows is decided (PRESENTATION-CHOICE-0): the certified picture 1:1 in a borderless window.
  PRESENT-EXACT-0 read the composed screen back exact on every checked frame under both GDI calls (with the host's
  performance overlay switched off, which it had found drawn over the picture), found no material cost difference,
  and adopted SetDIBitsToDevice (G11). `shell show` / `show-playback` is the locked presenter: it reads the screen
  back after every present and exits 3 if the screen ever was not the certified picture.
- The render headroom reaches the screen out of phase and is absorbed in phase (G7, `LATENCY-1R`, reproduced over two
  runs); presentation latency is phase-dependent, and no low-latency claim is made.
- A 200-sample p99 is three samples (G10); read a tail-sensitive category only after a confirmation.

---

## Epilogue — does the speed reach the glass (`LATENCY-1`, `LATENCY-1a`, `LATENCY-1R`)

The campaign's last question was whether the ~3.3× emit reaches the screen. Answering it produced three lessons of
its own.

1. **Read the instrument before the number.** `LATENCY-1` was preregistered to compare the present path before and
   after the fast render, with a reading of "improvement = the render headroom propagates". Building its sealer meant
   reading LATENCY-0's instrument, which renders every frame *before* its window opens and times only blit →
   composited. The renderer was never inside the clock, so that reading could not fire. The fix was an amendment
   registered before the number (`LATENCY-1a`: the delta speaks only about the presentation interval) and a separate,
   render-inclusive court preregistered as its own rung (`LATENCY-1R`). The hash-locked entry stayed untouched and
   the correction is visible in the ledger.

2. **A p99 of 200 samples is three samples.** LATENCY-1's first run read DEGRADATION on three slow samples; its
   confirmation read NO MATERIAL CHANGE, p99 within 21 µs of LATENCY-0. The `--confirm` habit from GAUNTLET-2 caught
   it; without a second run the ledger would carry a regression that was never there.

3. **Phase is a variable, not noise.** `LATENCY-1R` declared the render's phase against composition before measuring
   and got two opposite answers from one apparatus. In the locked regime the faster render's ~2.6 ms is fully absorbed
   by the composition wait (0‰). In the uniform regime composited output arrives 3.6 ms earlier at the median. Timing
   the loop only one way would have produced either "the optimization is useless" or "the optimization reaches the
   screen", and both would have been half true. The confirmation reproduced both halves in magnitude, though the
   locked label flipped across a boundary with no noise margin (8‰ vs 0‰) — a reminder that a category is only as
   stable as its boundary. Both runs also showed the shell's full render-start → frame-ready interval is ~15 ms, longer
   than a refresh, which moves the next measurement from the emit to the whole frame (G8).

4. **A court that names no target is doing its job.** FRAME-SPLIT-0 split the ~15 ms frame and found its largest phase,
   the blit, at 434‰ — large, and below the 500‰ rule locked before the number. The rule held: the reading is NO SEAT,
   multi-component, and no optimization is promoted. Without the preregistered threshold, "the blit is the bottleneck"
   would have been the headline and a present-path rewrite the next month's work, on a phase that owns well under
   half the frame.

The campaign's status, graded: **renderer latency materially improved; end-to-end presentation latency phase-dependent
and not certified low-latency; the whole frame multi-component, with no single phase promoted.** The next rung is a
narrower measurement, not an optimization.

---

## The one-line retrospective

Six rungs, one frozen oracle, zero pixels traded for speed, every number graded to exactly what was measured, and
every dead end kept as evidence. The campaign's real output is not the ~3.3× — it is a method that could produce the
~3.3× *and prove it honestly,* which is the harder and more transferable thing.

---

# Part II — the live campaign

*From `LIVE-LOOP-0` to `ADMIT-0`. Part I made a renderer fast and proved it honest. Part II is the other half: the
closed cycle of input, authority, render, present, observe and the next input, in a real window, with every
accepted change one event in one sealed history.*

## The arc

| Rung | What it added | The law, proven with no window | What the host showed |
|---|---|---|---|
| LIVE-LOOP-0 | the first loop that renders every composition | the bytes are checked before every present | 246 compositions, 6 of 6 readbacks exact |
| LIVE-INPUT-0 | a key press is a session event | the binding; the log replayed by the workshop to the same heads | three runs, every readback exact; the first received no key press |
| LIVE-SESSION-0 | the journal, the seal, resume, recovery | save, resume, recover and classify against really changed shells | a saved walk and its continuation, both replayed on another machine |
| LIVE-AUTHOR-0 | tile classes painted live | a tile edit moves M and leaves W; off-screen controls leave the pixels | 28 tile edits, saved, resumed with the painting intact |
| HOLD-WALK-0 | held keys walk the grid | one admitted repeat a composition; a held walk saves what the pressed walk saves | 31 held repeats; judged not the free movement wanted |
| BEARING-0 | the turning camera, carried from Urðr | the 104 witnesses; the anchor law | the gate passes there |
| BEARING-FAST-0 | that camera made fast | every tread byte-identical at 1,972 cameras | worst-camera p99 3,716 µs against a 6,667 µs target; 622,440 of 622,440 frames equal |
| SIM-TICK-0, 0a | the mouse-look rules as integer law | a 15,625 µs tick, one command a tick, the same head at any ticks, every free-heading frame recomputed at the save | the gate passes there |
| MOUSE-LOOK-0, 0a | a real mouse on those rules | capture as shell state; the samples; the picture alone at a free heading | the first run had no mouse report; the second, 13,931 raw reports, 1,761 looks, 1,775 of 1,775 frames the reference's |
| ADMIT-0 | the admission seam | one recognizer against an independent one over 513,792 mutants; the anchor; the grant; death at eight points | the first admission sealed, its head computed beforehand; the same bytes refused as stale |

The staircase reads **a loop → input → durability → authoring → a camera that turns → the rules of turning → the
device → a proposer that is not a hand**. Each step added one thing and was measured on the host before the next was
registered.

## What each court actually found

- **LIVE-LOOP-0 was narrow on purpose.** No input, no camera, no clock: its court was the loop itself, walking a
  session that was already sealed. Everything after it could assume a loop that renders, checks and presents in
  that order, because a row reads the source for it.

- **LIVE-INPUT-0's evidence was console text, and that decided the order.** The live session worked, and each walk
  had to be replayed by hand from the printed events. The owner moved LIVE-SESSION-0 ahead of LIVE-AUTHOR-0 for that
  reason. From then on a host walk is a saved file the workshop verifies.

- **LIVE-SESSION-0's mutation pass found the comparison that mattered.** A mutant that skipped comparing the saved
  file with the live session survived the first pass, because the saved file was sealed and self-consistent. The
  plant that came of it — a sealed, self-consistent file that is not the live session — is now a case.

- **LIVE-AUTHOR-0 was declared the last bespoke input case.** After it the rule is general: an accepted edit is a
  typed session event, the event changes the authoritative W or M, the next frame is rendered from the result, and
  the event is durable. Richer editing is vocabulary on the one live editor and not a new pathway.

- **HOLD-WALK-0 measured the wrong thing well.** Held keys walked cell by cell, exactly as registered. Walking it,
  the owner judged it was not the free movement he wanted. Nothing was patched: the next thing was earned from the
  start, with the turning camera certified in Urðr first, because no frozen oracle existed to hold a renderer to
  outside the four facings.

- **The rules and the device were never built together.** SIM-TICK-0 put every mouse-look rule in integers with no
  window, no clock and no mouse in the proof. Only then did MOUSE-LOOK-0 add the device. When the first host run
  made no look, the rules were not in question; only the device's path was.

- **MOUSE-LOOK-0a was written from a run that showed nothing.** The first `look-window` run received no mouse
  report. The amendment, registered after it, corrected a limit's wording, recorded how a run ends, and made the
  window count the raw input it receives before it reads it, so a second silent run would at least say where the
  silence was. The second run looked. Nothing shows the changed read was what had failed, and the ledger says so.
  The gate's own model was found to share a blind spot with the mock (the frames of the tick applied as a run ends)
  and now counts them.

- **ADMIT-0 chose a new language over a hardened old one.** Its courts had a strict JSON subset on the table. The
  owner's ruling was a line language, VRDNP1, whose accepted bytes are canonical: eight lines, one byte sequence per typed
  proposal. A recognizer for it is small enough to be held against an independent one over every single-byte
  mutant. Its 39 planted mutations left two survivors, and both became cases: a range fault with a byte after the
  last line feed, and an envelope forged onto a move.

- **Reading the code for READER-COURT-0 corrected two counts.** There were four JSON parsers and not three. And the
  deepest nesting among the records was seven and not six: sixteen of the host's sealed measurement records hold
  seven levels, and the first count had missed them. The owner had already ruled that bounds come from the writers
  and not from the files, so the ruling stood and only the number changed.

## The process rhythm, as it runs now

    court ──► ratify ──► preregister, in its own commit, pushed first ──► build ──► mutation-test ──►
        gate TWICE byte-identical (a third pass with the host's records present) ──► deliver as a patch ──►
        the owner applies, gates, runs, seals and pushes ──► document

- **The court is questions with answers.** Each rung's design choices are put to the owner as questions before
  anything is registered, and his answers are recorded in his words. A registration that surprised him would be a
  failure of the court, not of the entry.
- **A registration is pushed before its build exists.** Until its commit is pushed an entry can still be changed.
  After that it is never edited: a correction is an amendment with its own hash (LATENCY-1a, SIM-TICK-0a,
  MOUSE-LOOK-0a). READER-COURT-0's entry was changed once in that window, on the owner's review, and the ledger
  keeps both hashes.
- **Mutation testing sits between the build and the gate.** A row is trusted after planted defects in the program
  each turn it red. The counts are in the ledger, with the survivors and what they became.
- **The host is a second machine, not a formality.** The gate runs on Linux here and on the owner's Windows, and a
  rung lands when both read the same rowset and both pass. The host has found what the container could not: a file
  checked out with other line endings, and runs that received no input.
- **Documentation is a patch too.** What the host did is written down from the host's own output, after the fact,
  as its own commit. A claim about a host run is never written before the run.

## Lessons worth keeping

1. **Prove the law without the device.** A mock surface with a scripted mouse and a counted clock makes the loop's
   rules a gate matter. The host run is then about the host.

2. **Treat the first host run as an instrument.** Two first runs showed nothing where something was expected. Each
   became an amendment or a recorded unknown. Neither became a quiet fix.

3. **Make it durable before making it richer.** Saving came before painting. Every later claim about the live
   editor is about a file another machine replays.

4. **Earn semantics where they can be held to account.** The turning camera went through Urðr and came back frozen.
   Building it here first would have been faster and would have had nothing to be compared with.

5. **One pathway.** Input, a script, and a proposal all end as the same typed event in the same log. Each new
   source was a new binding or a new recognizer in front of the session, never a second way into the world.

6. **Buy evidence, not optimizations.** After BEARING-FAST-0 met its target the owner ruled that the next work is
   chosen by what evidence is worth buying. Nothing has been optimized from a first host run, and the live loop's
   timing is still unmeasured on purpose (G21).

7. **At a trust boundary, prefer a language with one reading.** A proposal is not JSON. It is eight lines that have
   exactly one byte form, so there is nothing for two readers to disagree about. The old saved form is being brought
   to the same standard afterwards, as its own rung.

8. **Count twice.** Both corrections in READER-COURT-0's record came from counting again by a different method. A
   count that feeds a registered bound deserves the same suspicion as a number that feeds a verdict.

9. **No scalar.** The program's state is a panel: what is measured, what is established, what is declared, what is
   not measured. A single grade would add those up, and they do not add.

## What to watch (pointers into [`GHOSTS.md`](GHOSTS.md))

- The live editor's laws are proven over a mock, and each host run is one run (G14).
- Between the readbacks and between the samples nothing is witnessed; the save is the exhaustive check (G15).
- A seal is a hash (G16), and the shell replays the session with its own copy of the fold (G17).
- The saved form's readers disagreed on hostile input; the remedy is registered and not built (G19).
- An admission records a claimed proposer and a command line's grant, and nothing about a model (G20).
- The live loop has no latency number (G21), and two host silences were never explained (G22).

## The one-line retrospective, again

Ten steps, one history, and no second way into the world: every key, every mouse report and the first proposal
became the same kind of event in the same sealed log, each on a rule that was locked before the host ran it. What
Part II produced is not a mouse that turns a camera. It is a window whose every picture is the replay of a file.
