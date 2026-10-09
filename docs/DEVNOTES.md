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

- **READER-COURT-0's first catch was its author.** A fast path written to make the Python reader usable on real
  files admitted `-0`. The registered case and five mutants of the exhaustive court differed from the Rust reader
  as soon as the two were first compared. Then the strict reader turned eight earlier rows red, because their
  forgeries had been written with the json module's defaults; and a ninth row stayed green for the wrong reason,
  which no red row could show. The gate now watches every refusal by the reader, and that row was found by the
  watch.

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
- **The three passes run at once.** Until READER-COURT-0 the three gate passes of a landing ran one after another.
  They are independent (each has its own copy of the tree and writes only inside it), so they now run together.
  Measured on the build container's two cores: three passes together took 2,000 s once and 2,149 s once (with
  other work running beside the second), against about 57 minutes one after another. The procedure is unchanged:
  the same three passes, the same comparison of their logs. (This paragraph went out in patch 0116 with its
  measured sentence missing and a `%s` in its place; the number was measured then and is written here.)
- **A push is written down from Git's own words.** One patch recorded the range of a push that the owner had not
  reported; it had been read from the host's refs, read-only, and the patch said so. He ruled that it is a
  provenance fact and stays unless it is wrong, and that it is never to be inferred from what a gate did. A range
  is quoted from a push's output when there is one.
- **A message that arrives twice is checked against the tree.** During REASON-COURT-0's census one host message
  was delivered three times, word for word, a failing gate among its lines. It was not answered as a new failure.
  The host's file was read, read-only, and showed the fix was not yet applied; the answer was the two patches
  already delivered.

**A text on the shape of a build turn (declared; the owner brought it, 2026-10-04).** It reads a long build turn as
mostly sequential project management and proposes: run the three independent gate passes at once and let the shell
wait for them; give the build one bounded instruction against a locked plan; fold the repeated chores (hashes,
counts, stale-reference scans, the mutation court, the passes, the comparison) into one driver command; use less
reasoning effort for mechanical phases; and split code, documents and court preparation into parallel tracks where
they do not share an authority. Its own summary: *lock the certification procedure; optimize its execution harness*,
and never omit a registered court or gate to save time.

What stands against the tree, as reviewed:

- **Adopted.** The parallel passes, above. The owner ruled that any driver stays in the build's scratch for now and
  nothing of it enters the repository.
- **Already so.** The passes were already run in the background and polled; what changes is that there is one wait
  and not three.
- **Not the gate's.** The 36-minute gate the text mentions is Urðr's. Here a pass takes about 18 to 20 minutes on
  the build container's two cores. The gain from running three at once is bounded by those two cores, and is
  measured above, not assumed.
- **Not the build's to set.** Which model and how much reasoning effort a turn uses is the owner's setting.
- **Kept sequential on purpose.** An edit, its test and its commit; a gate result, its reading and its correction;
  a registration and then its build.
- **Its citations** are its own and were not opened here.

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

8. **A green row can be wrong about why.** A forgery refused for its form passes a row that only asks for a refusal.
   Watching what refused it, on every gate, is cheaper than trusting that each forgery still reaches its own rule.

9. **Write a planted file as bytes.** A plant opened in text mode ends in CR LF on Windows. The first host run of
   READER-COURT-0 went red on exactly that, on a row that three passes here had shown green. The container is one
   platform; a file's bytes should not depend on which one wrote it.

10. **Count twice.** Both corrections in READER-COURT-0's record came from counting again by a different method. A
   count that feeds a registered bound deserves the same suspicion as a number that feeds a verdict.

11. **An expected value comes from the side that expects.** REASON-COURT-0's register was written from the gate's
   own statements and variables and from registered text. What the programs print was listened to, once, only to
   see that the register could hold. The owner's line: that a program prints X is not that a row requires X.

12. **A commit's name is local.** The same patch has one hash here and another on the host. A registration pins a
   file's bytes and a patch number.

13. **A gate that takes no input has configurations, not runs.** For one tree the gate's children and their
   endings depend on the platform and on which records are present. Hearing each configuration once is the whole
   of it; hearing one of them three times is three samples of one. The list for REASON-COURT-0's register was three
   long, and the third was the host. It was heard there before the build, and read as the others had.

14. **Listen where it is minted, and touch nothing.** The first listener wrapped the sealers' functions and
   reddened a row that reads a sealer's source. The one that replaced it takes the interpreter's own raise events
   and wraps nothing. An instrument that changes what it observes is a second program under test.

15. **Name a count by the partition it belongs to.** A count that is a subset of another, set beside it in one
   block, reads as one more part. The entry's sentence had the partition right; the field's name did not say it.

16. **A measurement can be registered, if it is named one.** MINT-WATCH-0's register has a layer read from
   source and a layer that was heard. The second is not smuggled in as an expectation derived from a requirement:
   it is called a baseline for drift, in the entry and in the file, and the rule it could have bent is restated
   beside it.

17. **Identify a thing by what it says, not by where it stands.** A raise site is its file, its function and its
   text. A line number moves when anything above it moves, and a watch keyed on it would redden on an added
   comment and stay green on a rewritten refusal two lines down.

18. **Before a watch is registered, ask what the rows not yet built do to it.** MINT-WATCH-0 is registered
   between another rung's registration and that rung's build. Read as first drafted, its watch would have gone red
   on the first refusal those six rows raised, or silently learned it. The entry now says which rows were
   measured and how a later row gets an entry.

19. **A survivor is a result.** Thirty-seven defects were planted against REASON-COURT-0's build. Two that survived
   the first run each showed a rule no plant exercised, and became plants. One that survives still shows a check
   stated twice. None was argued away.

20. **Where a rule says "filled by", find an assignment.** The listening instrument took the first endings that
   fit a slot, and every group happened to hold. The gate seats every ending so that each slot holds exactly its
   count: an order of arrival is not part of the registered rule.

21. **A build answers the next watch's question while it is cheap.** MINT-WATCH-0 registered that the six rows of
   this build raise no refusal, or are amended in. The rows were written to compare and not to read forged bytes,
   and one pass of the instrument over the built gate heard none.

22. **Give a plant one difference.** MINT-WATCH-0's first inventory plant changed a site's text, which is a site
   gone and a site new at once. Three weakened rules survived it, each covered by the other half. The plants now
   differ in one thing each.

23. **Two listeners, one interpreter.** Under `sys.monitoring` each takes a tool id and neither knows of the
   other. Under `sys.settrace` there is one function per thread, so the later listener has to carry the earlier
   one's frames to it. That was found by reading what the first would do to the second, before a pass was run.

24. **A path is relative to somewhere.** The gate's own file is named relatively when the gate is run as the owner
   runs it, and absolutely by every development harness. The tap keeps the directory it started in; a test that ran
   the file by a relative name, and then moved the working directory, is what showed it mattered.

25. **The gate is finished when it can stop being run.** Ten rows went on to hold the gate's own
   refusals. The owner's adjustment after them: a new gate only for a new engineering invariant; a design operation
   uses what is certified; a diagnostic is measured and never made authority; an experiment stays off the ladder.

26. **Build the content-time piece first, and let it name the next rung.** The design tool was written over the
   seam as it stands, with no change to the program. Running it once showed what no review had: a 60-cell design
   costs 40 s, because the seam admits one operation per run. The next engineering invariant was measured, not
   argued.

27. **A tool that cannot be trusted should be unable to do harm.** The design tool has one way to change a world,
   and it is the certified shell. So its own checks may stay off the gate: the worst it can do is propose badly.

28. **One word, two objects.** The proposed invariant said *one ordinary session event* and *head identical to
   sequential application*. A head is folded once per event, so one item folded once cannot have the head of N
   edits. Read against `fold`, the sentence held two different things, and the court had to choose: one
   admission, N items.

29. **Find the cost before courting the remedy.** A load cost 4 ms an edit event. The cause was one line: every
   edit hashed the tiles' 983,048 bytes, and a cell edit cannot change them. That turned *verify the delta* into
   two things: an exact memo, which is an equality, and a checkpoint, which is a trust root the tree does not have.

30. **A plant can borrow tomorrow's name.** ADMIT-0 forged a language that is not VRDNP1 and called it `VRDNP2`.
   The next version of the language has that name. Found by searching the gate for the name before registering
   it; the registration keeps the plant refused where it was and says what the plant no longer shows.

31. **A watch names its own price.** Two rungs pin every source and sealer so that a change is a decision. The
   first rung to change the shell after them pays in two amendment entries, and its registration says so before
   the build finds out.

32. **A plant has to be able to reach what it is said to catch.** The draft planted a memo kept stale by a tile
   edit and said the workshop would refuse the saved file. A prototype showed no file is ever saved: the stale
   digest leaves the content unchanged, and the seam refuses an edit that changes nothing. The plant was
   rewritten before the registration was committed, and the registration says a prototype came first.

33. **A registered case left out is found by the mutant it was there for.** The registration named a key's edit
   standing between two places of a batch. The first rows did not build it: taking the envelope off a middle
   event looked like the same thing. It is not. A mutant that let the workshop take an unenveloped event inside a
   batch passed every row, because such an event had only ever been refused by its neighbours' places. Read the
   registered list against the rows, item by item, before trusting the rows.

34. **A plant depends on what it is planted into.** The wrong memo was to make the shell read its own file back as
   verified. On one parent it did. On another the read-back refused, because that parent's own history replays
   differently under the same plant. The claim was true of one case and the court had to pick that case on
   purpose and say why.

35. **An amendment that names files by hash is written last and committed first.** It cannot be registered before
   the files exist. Say so in the entry, and let the gate hold the entry against the files.

36. **Let a script count.** A draft said nine sites were added to the sealer. The script that reads the file found
   seven and stopped.

37. **Keep a plant's whole chain, not its verdict.** "The memo plant fails" was true and said little. The owner's
   account has five steps: a wrong memo; the shell's own read-back fooled by it; the comparison with no memo
   catching it; the workshop catching it; an honest shell catching it. The second step is why the third exists.
   Write the step that shows a check is needed, not only the check.

38. **A deferral is recorded in the words it was ruled in.** An idea the owner defers goes into the record as his
   sentence, with the condition that reopens it, and under no rung. Paraphrase would make it a claim; putting it
   under a rung would make it a debt.

39. **A predicate, not a phrase.** "Full ×2" was a phrase, and a second host run on a tree changed only by documents
   fitted it loosely enough to argue about. As the owner's predicate it does not: the same tree and the same
   output, with identity that was not measured as a third value. The same facts then grade themselves, and
   nobody has to decide whether two runs count. It also said what to run next: the tree's id, the gate twice, the
   tree's id.

40. **A rule that looks like a mirror may be the only copy.** The design tool refused three things before it
   proposed, and called them what the seam was known to refuse. A reference run through the admission showed the
   seam refuses one of the three. A camera's cell closed and a stair opened are admitted. Before a rule is moved,
   find out who else holds it.

41. **Run the registered list through the reference before it is registered.** The corpus of DESIGN-IR/DIFF-0, 40
   refusals and orders, and its ten plants were each run before the entry was committed. One plant gave the honest
   bytes on the registered design and another was refused by the admission itself, so the entry says each plant is
   run where it bites. That was found before the registration, where it costs a sentence.

42. **Name the parts of a court before adding courts.** Seven seams were proposed around the compiler. Read against
   the registration, five were parts of rows it already had, one belonged to the tool's own checks and one was the
   mutation campaign. Naming them cost one entry, a dozen cases and no row. The check to make first is whether a
   proposed court is new or is a name for something registered.

43. **Before claiming a court catches something alone, check what already catches it.** The draft of HERMENEUTICS-0
   required a plant that only it could catch. Reading the five plants against DESIGN-IR/DIFF-0 showed each one
   changes a value that rung had registered before any plant. The requirement was struck before the entry was
   committed, and the entry says what the court adds instead.

44. **A court records how it went, not how it was designed.** The rulings were to be the owner's, made before any
   program's answer. He ruled one case, asked for a recommendation on the rest and ratified it, and four of ten
   targets had been shown by the reference already. The entry says each of those things. Evidence is graded by
   what happened.

45. **No scalar.** The program's state is a panel: what is measured, what is established, what is declared, what is
   not measured. A single grade would add those up, and they do not add.

46. **Write a row about history, not about today.** Three predicates of this build were true when written and
   false after the next legitimate change: a pin held as the file as built, six rows held as the last six, a
   corpus that could not grow. Each was restated about history: a link that starts where the last one ended, a
   position after a fixed predecessor, a registered corpus and what was added to it. The owner's sentence for it:
   *history is immutable; state may evolve; transitions must preserve provenance.* Write the next row as if rows
   will follow it.

47. **A green first run is where the work starts.** Four of the five rows passed the first time they ran. The
   mutation campaign then found a compiler that refused every design made from a stair, and every row passed it.
   The rows were right about everything they looked at.

48. **A check that another check covers is found by taking both out.** Five planted defects survived and were
   equivalent, each because a second check decided first. Taken out alone, each proves nothing. Taken out with its
   cover, each pair was caught. Run the pair before calling a survivor equivalent.

49. **A replacement that changes nothing is not a mutant.** One planted defect survived because the replacement
   never ran: its condition could not hold. A campaign needs a control that passes and a reason to believe each
   mutant is reachable. A survivor is first a question about the mutant.

50. **The broad court catches what no named case does.** Four defects were caught only by the single-byte mutants
   of three small designs. Nobody would have written those cases by hand. That is the reason not to sample it.

51. **Three layers, and no fourth.** History is in the entries, identity in the pins, behaviour in the rows. A pin
   was nearly asked to show intent, and a second mechanism nearly built for it. Each layer already answered its
   own question. The owner's instruction: do not invent a fourth to settle what the three already settle.

52. **Read the chain before comparing two machines.** If the host's log differs from the build container's, there
   are two different findings it could be: the history is broken there, or the platform differs. Reading the
   chain's rows first tells them apart. The owner ruled it a protocol and not a row: it is an order of reading.

53. **An accepted idea goes into a row that exists.** Three ideas were put to the owner in private. He deferred
   one, kept one as a ghost, and accepted one with the words *no new row*. The accepted one became a few lines
   in a fence that was already there. His measure: the rung certifies a transition; it does not grow a provenance
   system.

54. **Say when a new check is implied by old ones.** Over its domain the layout relation follows from three rows
   that already pass. It was built anyway, against the files on disk and in both directions, and the entry says it
   adds no evidence there. A reader should not have to find that out.

55. **Text that holds a number holds a clock.** A row looked for four digits anywhere in a log. The log's records
   carry the time in milliseconds, and one afternoon the time held those digits. Search the member a thing could
   be written to, never the whole text. And read a red row's evidence before believing its sentence.

56. **Fix the observation, not the collision.** The quick repair was to skip the clock. The owner refused it: an
   exclusion moves the accident to the next field that holds digits. The row now names what it reads. Then the
   gate was read for the class of the defect, not for the four digits that showed it: one more defect of the kind
   would have been the same lesson learned twice. A flake with a known mechanism can be made to happen: the clock
   was moved, the old row failed on demand, and the correction was judged at that instant and not by waiting.

57. **Direct the perturbation; watch every row.** A path that spelled three rows' words was tried on those three rows,
   and nothing was found. The same kind of path under the whole gate broke three other rows. A hypothesis may choose
   what to change. It should not choose what to look at.

58. **A count of red rows is not a count of defects.** One space failed four rows: three that read the path, and the
   court that heard their refusals. The fourth was the gate working.

59. **A fluent summary is a claim like any other.** A text arrived describing as built, compiled and absolute what
   another text, the same day, had declared. It was read against the tree line by line before a word of it was
   written down: what stands, what does not, and the rung table it drew, set right.

60. **Write the prediction before the host runs.** The four rows were named in writing, and then the clone was
   made. The host failed those four and no other. A prediction written first turns a run into a test; one written
   after is a description.

61. **A tree id is taken, never inferred.** One pair of host runs printed the same 247 lines twice, and the tree's
   id was taken only before them. The record says half the predicate was read, though nothing in those runs could
   have changed a tracked file.

62. **The id names the commit; the status names the files.** `git rev-parse "HEAD^{tree}"` does not change when a
   tracked file does. It names what is in the folder only beside a status that lists nothing. Read both, at both
   ends: two host runs in a row each missed some of the four readings.

63. **The experiment that found the defect certifies the repair.** The perturbed pass that broke three rows was run
   again on the repaired tree, with its result written into the entry before the run. A probe kept as it was is a
   test of the repair; a probe softened to pass is not.

64. **A witness brackets everything it runs.** The first witness took its last readings before the design checks it
   ran. The owner found it by reading the code, not by a failure. The evidence collector is held to the same rule as
   the gate: what it does not bracket, it does not witness.

65. **Find the carrier before writing the contract.** G33 looked like a row needing a file. Seven cases showed the
   kernel reaches the row as a global, that the file alone does not, and that the row means to depend on it. The
   contract that follows is about a declared input and a clear refusal, not about the order of the rows.

66. **Fix the brittle, not its message.** A clear refusal would have made `input-demo` fail in better words and left it
   failing run alone. Asking for the kernel where it is used, and keeping what was made, ends the dependence on the
   rows before it and keeps the clear refusal for the one case left: a kernel that cannot be built.

67. **The last step is a copy.** His lesson (2026-10-09): verification can fail after the code is correct, when a
   valid result is copied into a claim with the wrong provenance. Six messages here named a wrong tree id, each
   caught by hand before its patch was cut. Two copies that agree can carry the same mistake; a check has to trace
   the claim to its source (EVIDENCE-LINK-0, declared).
68. **Read the earlier rung's rows before writing the later rung's instrument.** HERMENEUTICS-0's entry asked for
   new plants and for the reference in its own rows, and also that DIFF-0's rows not change. Two of those rows
   hold the plants to eleven and the reference to DIFF-0 alone. One author wrote all three and did not see it until
   the build was read.

69. **A guarantee stops where its evidence stops.** His words, on eight ideas that would each let the ladder certify
   more for less: *a passing result cannot inherit a guarantee that its inputs never established.* Composition,
   compression and attestation can carry evidence further; none of them makes any.

## What to watch (pointers into [`GHOSTS.md`](GHOSTS.md))

- The live editor's laws are proven over a mock, and each host run is one run (G14).
- Between the readbacks and between the samples nothing is witnessed; the save is the exhaustive check (G15).
- A seal is a hash (G16), and the shell replays the session with its own copy of the fold (G17).
- The saved form's readers disagreed on hostile input; the remedy is built, and its reach is stated (G19).
- An admission records a claimed proposer and a command line's grant, and nothing about a model (G20).
- The live loop has no latency number (G21), and two host silences were never explained (G22).
- A refusal is held to its code, not its cause (G24): the court is built and passes on both machines. 63
  lines the programs print about themselves are trusted and not opened (G25).
- The mint register's counts are a measurement, and 105 of its 164 sites were never reached (G26).
- The design surface is content time: uncertified by design. It sends one batch now, and its time on the host is
  not measured (G27).
- The batch is built and passes on both machines. What it leaves to the compiler, to the workshop and to the host,
  and what no verifier rebuilds, is stated (G28).
- The compiler is built and passes on both machines. A row written about today breaks at the next change: three
  were met and restated, one more is known. What the compiler's court does not reach, and what was deferred, is
  stated (G29).
- One row could fail for the clock's reason, about one run in three hundred by estimate. Found by meeting it,
  ruled a defect of the gate and corrected; the gate was read for the class, and two rows of the same form are
  named and left (G30).
- A checkout path with a space broke three rows (a walk's path was one word), and the reason court's watch with
  them. Found by a perturbed pass, measured on the host as predicted, repaired by INPUT-0a, both predictions met
  (G31). The walk's other lines drop words they do not use (G32).
- A row could rest on what an earlier row left (G33). For the walk's rung, repaired by INPUT-0b, which the owner has
  closed: its rows ask for what they need and pass run alone. The other rungs' readers of a build global are
  recorded and untouched.

## The one-line retrospective, again

Ten steps, one history, and no second way into the world: every key, every mouse report and the first proposal
became the same kind of event in the same sealed log, each on a rule that was locked before the host ran it. What
Part II produced is not a mouse that turns a camera. It is a window whose every picture is the replay of a file.
