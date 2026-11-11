# MATH-KERNEL — independent characterization of the sin/cos oracle (certified correct rounding)

**Scratch measurement record. Not a ruling, not frozen, not in any repository.** It measures *how good the frozen
algorithm is*; it does **not** change the frozen conformance guarantee (specified-frozen-algorithm, no correct-rounding
claim). Grade: **MEASURED**. Date 2026-11-10, on the owner's Windows host.

## 1. Why this is independent (unlike the differential)

The three-way differential (26/26 bit-for-bit, Turn 73) compared the C oracle against `rules_ref.py` and `sim.js` —
all three **descend from fdlibm**, so that result is faithful-transcription consistency, not a correctness check
(the G23/G29 "one author wrote both twins" lesson). This characterization compares the oracle against references that
**share no code with fdlibm**: **MPFR 4.2.2** (gmpy2 2.3.2, directed rounding) and **Arb** (python-flint 0.9.0, ball
interval arithmetic), with **mpmath 1.4.1** as a point cross-check. MPFR and Arb use independent algorithms and
independent argument reduction. This is the first evidence in the arc that bears on **mathematical correctness**.

## 2. Certification method (certified correctly-rounded reference)

For each finite input `x` (an exact binary64) and each of sin, cos:

1. **MPFR enclosure:** compute the result at working precision `p` rounding **down** → `lo` and **up** → `hi`. By MPFR's
   correct directed rounding, `lo ≤ true ≤ hi` (a guaranteed enclosure).
2. **Round to binary64, RN ties-to-even:** `RN53(lo)`, `RN53(hi)`. Round-to-nearest is monotone, so if
   `RN53(lo) == RN53(hi) == v`, then `RN53(true) = v` — `v` is the **certified** correctly-rounded result.
3. **Escalate** (`p` from 120 bits, doubling to 300000) until certified; **Arb** independently certifies the same way.
   **Certified** requires MPFR and Arb to agree on `v`. If neither certifies within the cap, the input is **UNRESOLVED**
   — recorded as such, never silently a pass (the rounding-boundary escalation rule you required).
4. **S1 / S3 semantics**, not ordinary numeric comparison: an exact-zero result takes its sign of zero from S1
   (`sin(−0) = −0`; MPFR is IEEE-correct here, Arb's interval type does not track ∓0); non-finite inputs are S3
   (they reach the oracle; there is no numeric CR reference — the oracle's NaN is recorded, not rounding-compared).

Harness validation (scratch): sin(0)/cos(0) exact & certified; five ordinary inputs where MPFR, Arb, and the mpmath
point all agree; a **planted wrong oracle (CR+1 ULP)** correctly flagged `ulp=+1, disagree` (the harness has teeth);
`ulp(CR,CR)=0`. One disagreement independently re-checked at 2000-bit MPFR directed enclosure **and** 2000-bit Arb ball.

## 3. Corpus

- **Frozen-corpus kernel inputs** (the `direct sin/cos`, `reduction stress`, `exceptional values` groups of the frozen
  90-vector corpus) — 30 finite + 12 non-finite rows.
- **A separately-identified adversarial characterization corpus**, `MATH-KERNEL-CHAR-CORPUS-2026-11-10.csv` (127 inputs):
  reduction-boundary neighbors (adjacent doubles at `(2k+1)·π/4`), near-`k·π/2` neighbors, small/subnormal and the
  `2^-27` cutoff, declared domain endpoints (yaw `[0,2π)`, pitch `[−1.45,1.45]`), reduction-path representatives, and a
  **hard-to-round search** (hardest 15 each for sin/cos over 60000+ in-domain samples, scored by closeness of the true
  value to a binary64 midpoint). These inputs are **retained permanently** in that CSV.

Full per-input results: `MATH-KERNEL-CHARACTERIZATION-RESULTS-2026-11-10.csv` (oracle bits, certified CR bits, signed
ULP, agrees-CR, abs err, rel err, status, tags).

## 4. The three independent conclusions

| Question | Evidence | Answer |
|---|---|---|
| Does the implementation **conform**? | exact output-bit agreement with the frozen oracle (the differential) | **Yes** — 26/26 bit-for-bit (Turn 73); not re-tested here |
| How accurately does the oracle **approximate** sin/cos? | certified reference + ULP distribution | **Faithfully rounded**: max **1 ULP** (max abs err 8.37e-17, max rel err 1.18e-16) over **242 certified** inputs; **234/242 correctly rounded** |
| Is the oracle **correctly rounded**? | per-input certified rounding comparisons | **No** — **8 certified ±1-ULP counterexamples**. No correct-rounding claim is warranted |

**ULP distribution (signed, oracle → certified CR):**
- sin: 121 certified — `{−1:1, 0:119, +1:1}`; max |ULP| 1.
- cos: 121 certified — `{−1:4, 0:115, +1:2}`; max |ULP| 1.
- 0 UNRESOLVED; 12 non-finite under S3; `sin(−0)=−0` certified under S1.

**Where the error lives.** All 8 disagreements are **reduction-seam** cases: adjacent doubles at odd multiples of `π/4`
(`±π/4, 3π/4, 5π/4, 7π/4`), where the reduced argument lands on the `π/4` boundary and the result is `≈ ±√2/2`
(`0x3fe6a09e667f3bc…`). The oracle is off by exactly 1 ULP there. Notably the **hard-to-round search (60 rows) found
zero disagreements** — fdlibm faithfully rounds even the Table-Maker's-Dilemma-hardest values; its 1-ULP error is
**structural** (argument-reduction/polynomial error at the `π/4` seam), not a hard-to-round-midpoint effect. The 30
frozen kernel inputs were all correctly rounded — the frozen corpus alone does **not** contain the `π/4`-adjacent
doubles that expose the gap, which is exactly why the adversarial corpus was needed.

## 5. Grade and boundary

- **MEASURED.**
- **Does not show:** (a) It is **not** a whole-domain proof that error ≤ 1 ULP — it is 242 certified points plus a
  60000-sample hard search, not exhaustive over `[−1.45, 2π)`. (b) The corpus is **adversarial** (deliberately clustered
  at reduction seams and hard-to-round points), so the 8/242 disagreement density **overstates** the uniform-domain rate;
  under uniform sampling correct rounding would hold far more often. The robust claims are the two extremes: faithful
  rounding (≤1 ULP) held across everything tested **including the hardest cases found**, and correct rounding
  **definitively fails** (≥8 certified in-domain counterexamples exist). (c) Certification rests on the soundness of
  MPFR's directed rounding and Arb's interval arithmetic — two independent engines that agreed on every certified value.
- **Falsifier:** any certified input where the oracle differs from the certified CR by **>1 ULP** (would break faithful
  rounding), or where MPFR and Arb certify **different** CR values (would break the method).

## 6. Impact on the frozen contract

**None — and it confirms the contract's scope.** The frozen guarantee is specified-frozen-algorithm conformance with
**no** correct-rounding claim. This characterization shows correct rounding is **demonstrably false** for this oracle
(8 certified counterexamples), so claiming it would have been wrong; the frozen choice is vindicated, and the measured
property is **faithful rounding (≤1 ULP)**. Nothing frozen is changed; no repository, charter, or admission is touched.

## 7. Provenance

- References: MPFR 4.2.2 (gmpy2 2.3.2), Arb (python-flint 0.9.0), mpmath 1.4.1 — installed in an **isolated scratch
  venv** (`orlog-review/.charvenv`), not the host's global Python.
- Oracle: `fdlibm-5.3/build/test_oracle.exe` (sha256 `d1de73d0…`, the Turn 72/73 build).
- Scripts (scratch): `cert_core.py` (validated core), `corpus_gen.py`, `char_run.py`.
- Python 3.14.5. Nothing in this record is a decision or a frozen artifact.
