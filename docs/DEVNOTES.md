<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2026 Daniel J. Dillberg -->

# Dev notes & review — the optimization campaign

*Working notes and a retrospective on the run from `GAUNTLET-0` to the `GAUNTLET-2` LOCK: how the campaign was
conducted, what each court found, the process that made the results durable, and the practices worth keeping. This
is the narrative counterpart to the terse ledger in [`verify/RUNGS.md`](../verify/RUNGS.md).*

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
- The shell's whole render-start → frame-ready interval is ~15 ms at p50, longer than one refresh on the owner's host
  (G8); split it phase by phase — strips, frame, pixel pass, HUD, conversion, blit — before choosing the next target.
- The render headroom reaches the screen out of phase and is absorbed in phase (G7, `LATENCY-1R`, one run); confirm
  it before building on it.
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
   screen", and both would have been half true. The same run also showed the shell's full render-start → frame-ready
   interval is ~15 ms, longer than a refresh, which moves the next measurement from the emit to the whole frame (G8).

---

## The one-line retrospective

Six rungs, one frozen oracle, zero pixels traded for speed, every number graded to exactly what was measured, and
every dead end kept as evidence. The campaign's real output is not the ~3.3× — it is a method that could produce the
~3.3× *and prove it honestly,* which is the harder and more transferable thing.
