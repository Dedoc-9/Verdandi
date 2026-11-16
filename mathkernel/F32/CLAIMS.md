# mathkernel/F32: claims

Status of the subtree: an unfrozen, unadmitted candidate family; nothing here is adopted (`README.md`).
integrity is not truth; declared is not verified; built is not adopted.

## Where this was built and checked

Every record this file cites was made on one machine, called "origin" below. It is described in general terms, at the
repository owner's instruction: its processor's vendor and model, its host name and its account are not recorded in
this repository. No result is claimed for any other machine, compiler or build.

| | |
|---|---|
| operating system | Windows 11, 64-bit |
| processor | x86-64 (vendor and model not recorded here) |
| memory | about 12 GB |
| C compiler, for the programs and tests | clang 22.1.8, target `x86_64-pc-windows-msvc`, options `-O2 -ffp-contract=off -fno-math-errno` |
| Python, for the emitters, sweeps and references | 3.14.5, standard library only |
| Rust, for one backend of the corpus step | rustc 1.96.1 |
| proofs and gates | Coq 8.20.1, Flocq 4.2.1, Coq Interval 4.11.1, in a Linux container (Docker 29.9.3, linux/amd64, on WSL 2) whose image id begins `sha256:e5d68b0139b5` |

Grade: DECLARED. These lines were read from the machine when this file was written; the staged records carry only
parts of them (`RUN.md` section 1 says which). The image's recipe is not in this subtree.

## How to read this file

- **Grades.** MEASURED: a run was made and its console is a staged file, named with the verdict line copied from it.
  READ: a staged file says so at the place given. ARGUED: reasoned from measured or read facts. DECLARED: stated by
  the tier's author with no staged record behind it. OBSERVED: seen once, not under a check. NOT_MEASURED: not done.
- **Every MEASURED below is a record of a run made on origin** (where the tier was built: one host, one container
  image, one compiler). None was repeated from a checkout of this repository. `RUN.md` says how to repeat each and
  which cannot be repeated from this subtree alone.
- **A claim is no stronger than its record**, and a pass at one layer (statement, proof about the Coq graph, graph to
  program, backend) never stands for another.
- Each claim has four parts: the claim, its grade and record, what it does not show, and what would refute it.

## THE BOUNDARY: the floating-point control state

Every claim in this file about a computation in binary64 holds only under this control state:

1. rounding to nearest, ties to even;
2. no flush-to-zero;
3. no denormals-are-zero;
4. no contraction (no fused multiply-add in place of a multiply followed by an add or subtract).

**Under any other control state the guarantee is void**: not weakened, void. The statements give every operation in
round to nearest even (READ: `ieee64/IEEE64_Statement.v` lines 11 to 18). That they also fix the fourth point, one
rounding per operation, is ARGUED: each operation of a graph is one operation of the Coq library and no fused
operation appears in a graph. The second and third are needed because the model has subnormal numbers and uses them
(`narrow`'s branch below 2^-126; READ, `orl/emit.py` lines 3 to 4).

The owner's ruling of 2026-11-16, an excerpt of the text the owner confirmed (a restatement written for his
confirmation, not his own wording): "The tier's claims name the floating-point
control state — round-to-nearest-even, no flush-to-zero, no denormals-are-zero, no contraction — as a boundary, and
state that the guarantee is void under any other control state. Enforcement is a check the binding makes at start-up
and re-asserts at any boundary where the control state could have changed (for example after third-party or driver
code that may touch the control register); its cadence and form are designed as their own unit."

- **Enforcement is not built.** No file in this subtree reads or sets a control register, and there is no binding.
  The check, its cadence and its form are a later unit of their own. Grade: NOT_MEASURED.
- What exists is evidence about builds, not enforcement. The records of the earlier programs name their compiler and
  options (READ: `orl/evidence/gen-equiv-run1.txt` lines 1 to 2: `clang version 22.1.8`, `-ffp-contract=off`). For the
  staged C no staged record holds a compiler version or a build command: its second line gives the build line as a
  comment, and that it was built so is DECLARED. Section 8 shows a contracted build is a different function for
  `narrow` and `exp32`.
- Does not show: that any program, on any processor, runs under this state at any moment. The sweeps of section 6
  ran under whatever state their process had; that state is recorded nowhere (NOT_MEASURED).

## 1. Model statements and their proofs (one section per function)

Common to this section. The model is Flocq's FLT format: binary64 as FLT(-1074, 53), binary32 as FLT(-149, 24),
**without an upper exponent bound**: nothing overflows, there is no sign of zero, no NaN, no infinity. "Faithful"
means: one of the two binary32 values of that format that bracket the exact real result (the result itself when
representable). Because the format is unbounded, a faithful value can be 2^128 or more: finiteness is section 2's.
The proofs are about the operation graphs `p32/Graphs.v` and `exp32/Graph.v`. By the owner's ruling of 2026-11-16
those graphs are the defining text of each function; the C, the corpus laws and the backends are renderings
(`README.md`). That ruling fixes which text governs; it freezes nothing and adopts no design choice.

Records (the gate, section 4): `f32/gate4-run1-console.txt` `F32 GATE4 HELD: 20 of 20  [anchor 53880a185dd4b235]`;
`p32/gate4-run1-console.txt` `P32 GATE4 HELD: 35 of 35  [anchor 9adba8eecba84425]`;
`exp32/gate4-run1-console.txt` `EXP32 GATE4 HELD: 47 of 47  [anchor 68481fb907358ff7]`.

### 1.0 The lemma the others rest on (F32_REL)
- Claim: a binary32 rounding of a real y that approximates f to relative 2^-27 is a faithful rounding of f, as
  `f32/F32_Statement.v` states it (sha256 `09893717...cc73`).

<details>
<summary>Grade, record, what it does not show</summary>

- Grade and record: MEASURED, the F32 line above.
- Does not show: anything about a program; that 2^-27 is the best constant (the statement's header says 2^-24 fails).
- Refuted by: a gate run on these sources that does not hold; a reading of the statement that finds it says less.

</details>

### 1.1 narrow (T32)
- Claim: for every binary64 value v of the model, the graph `narrow` returns the binary32 round-to-nearest-even of v
  (`p32/P32_Statement.v`, sha256 `a1b2af32...422d`: `forall v, format64 v -> narrow v = RN32 v`).

<details>
<summary>Grade, record, what it does not show</summary>

- Grade and record: MEASURED, the P32 line above.
- Does not show: a finite binary32 result (at 2^128 - 2^103 and above the graph gives 2^128 or more, where the IEEE
  conversion gives infinity: section 2.1); the sign of a zero; anything about a program.
- Refuted by: a v of the model with `narrow v <> RN32 v`; a failing gate run.

</details>

### 1.2 sqrt32 (SQRT32)
- Claim: for every binary32 x >= 0 of the model, `g_sqrt32 x` is a faithful binary32 rounding of sqrt x.

<details>
<summary>Grade, record, what it does not show</summary>

- Grade and record: MEASURED, the P32 line above.
- Does not show: correct rounding (the sweep of section 6.2 measures that for the program, the proof does not state
  it); the header comment's "inputs below 2^128" is not a premise of SQRT32
  (`p32/P32_Statement.NOTE-2026-11-14.md` lines 24 to 25; finding F1 of `FINDINGS.md`).
- Refuted by: a failing gate run; a model input where the graph's value is not one of the two bracketing values.

</details>

### 1.3 rsqrt32 (RSQRT32)
- Claim: for every binary32 x with 0 < x < 2^128, `g_rsqrt32 x` is a faithful binary32 rounding of 1 / sqrt x.

<details>
<summary>Grade, record, what it does not show</summary>

- Grade and record: MEASURED, the P32 line above.
- Does not show: correct rounding (not claimed, not measured); x = 0; the sign of a zero.
- Refuted by: as 1.2.

</details>

### 1.4 hypot32 (HYPOT32)
- Claim: for binary32 x, y of magnitude below 2^128, `g_hypot32 x y` is a faithful rounding, in the unbounded
  format, of sqrt(x*x + y*y).

<details>
<summary>Grade, record, what it does not show</summary>

- Grade and record: MEASURED, the P32 line above.
- Does not show: a finite binary32 result (with both inputs the largest binary32 number the result is about 1.414 *
  2^128: the dated note, lines 20 to 21); the two range premises are not used by the proof (same note, line 24).
- Refuted by: as 1.2.

</details>

### 1.5 exp32 (EXP32)
- Claim: for every binary32 x <= XMAX = 11629079 / 2^17, `g_exp32 x` is a faithful binary32 rounding of exp x
  (`exp32/EXP32_Statement.v`, sha256 `19d1fb59...aae5`).

<details>
<summary>Grade, record, what it does not show</summary>

- Grade and record: MEASURED, the EXP32 line above.
- Does not show: that XMAX is the largest input whose exp is a finite binary32 number (section 2.5); correct
  rounding (not claimed); the sign of a zero; anything about a program.
- Refuted by: as 1.2.

</details>

## 2. Finiteness and range

Records: `p32r/gate4-run1-console.txt` `P32R GATE4 HELD: 41 of 41  [anchor 2fc8014ccb21d40b]`
(`p32r/P32R_Statement.v`, sha256 `0b98724a...421f`); `exp32r/gate4-run1-console.txt`
`EXP32R GATE4 HELD: 54 of 54  [anchor c7052646819b4e69]` (`exp32r/RANGE_Statement.v`, sha256 `281b28c2...2187`).
FMAX32 = (2^24 - 1) * 2^104 is the largest finite binary32 number; OVF32 = 2^128 - 2^103.

### 2.0 FAITHFUL_FINITE
- Claim: a faithful rounding of a value of magnitude at most FMAX32 is a finite binary32 number.

<details>
<summary>Grade, record, what it does not show</summary>

- Grade and record: MEASURED, the P32R line.

</details>

### 2.1 narrow (NARROW_FINITE, NARROW_SHARP)
- Claim: `narrow` of a binary64 value of magnitude below OVF32 is a finite binary32 number; at OVF32 it gives 2^128.

<details>
<summary>Grade, record, what it does not show</summary>

- Grade and record: MEASURED, the P32R line. Companion, on the earlier program: `orl/evidence/narrow-top-run2.txt`
  `NARROW TOP HELD: below OVF 33554432 values, differ from the conversion 0; around FLT_MAX 67108866 values, differ 0; at and above OVF 33554434 values, narrow returns +-2^128 on 33554434 (finite, not binary32) where the conversion returns infinity on 33554434`.
- Does not show: what a caller should do at and above OVF32. That is measured, not specified.

</details>

### 2.2 sqrt32, 2.3 rsqrt32 (SQRT32_FINITE, RSQRT32_FINITE)
- Claim: for every finite binary32 input of its domain (x >= 0; x > 0) the graph's result is a finite binary32 number.

<details>
<summary>Grade, record, what it does not show</summary>

- Grade and record: MEASURED, the P32R line.

</details>

### 2.4 hypot32 (HYPOT32_FINITE, HYPOT32_SHARP)
- Claim: the result is a finite binary32 number when the exact result sqrt(x*x + y*y) is at most FMAX32; with both
  inputs FMAX32 it is not.

<details>
<summary>Grade, record, what it does not show</summary>

- Grade and record: MEASURED, the P32R line.
- Does not show: any policy for a caller whose inputs do not meet the premise. The premise is the caller's. That the
  premise is necessary: it is sufficient only, with one sharpness example. In the second sample of section 6.4, 19,622
  pairs outside it gave a finite binary32 result (READ: the verdict line of `orl/evidence/hypot-check2-run1.txt`).

</details>

### 2.5 exp32 (EXP32_RANGE, EXP32_SHARP)
- Claim: for binary32 x <= XMAX, exp x < FMAX32 and 0 <= `g_exp32 x` <= FMAX32; at the next binary32 number above
  XMAX, exp is above 2^128.

<details>
<summary>Grade, record, what it does not show</summary>

- Grade and record: MEASURED, the EXP32R line.

</details>

For all of section 2. Does not show: anything outside the premises; sign of zero, NaN, infinities (the model has
none); anything about a program. Refuted by: a failing gate run; a counterexample in the model.

## 3. IEEE-level correspondence (all five functions, one statement)

- Claim: for each function and every finite binary64 input inside its premises, IEEE binary64 operations, as
  Flocq's `BinarySingleNaN` formalizes them, in round to nearest even, in the graph's order and on the graph's
  constants, return a finite binary64 value whose real number is the graph's value (`ieee64/IEEE64_Statement.v`,
  sha256 `7cbcac51c912286bc9ea64ef2880cf7685ff2027e02902a5ceeae3e693e428de`: IEEE_NARROW, IEEE_SQRT32, IEEE_RSQRT32,
  IEEE_HYPOT32, IEEE_EXP32, IEEE_CST).
- Grade and record: MEASURED. `ieee64/gate-run1-console.txt`:
  `IEEE64 GATE HELD: 13 of 13 rows here, gate4.py 148 of 148 on the copy  [anchor 42e3891e153bafae]`; its line 3,
  the statement has the sha256 given from outside; its line 473, `148 rows; 38 plants refused`; the anchor record
  `ieee64/ANCHOR4-run1.txt`.
- Does not show (the statement's own list, its lines 29 to 39): the sign of a zero result; inputs outside the
  premises, NaN or infinite inputs; the value a selection does not return; intermediate values; exception flags; any
  compiler, processor or program. It trusts that Flocq's operations are IEEE 754's.
- Does not show, further: the 13 outer rows are printed by `ieee64/gate_ieee64.py`, which is staged at the sha256
  that `ieee64/gate.json` line 5 and `ieee64/ANCHOR4-run1.txt` line 8 name; a rerun of it from an exported copy is
  NOT_MEASURED.
  **No composition**: no staged theorem states "IEEE operations give a faithful, finite binary32 result" in one
  sentence; that reading joins this section to sections 1 and 2 by hand (ARGUED, not proved here).
- Plants that are not demonstrations, said as such: `prem-sqrt-no-fmax` is refused "by the route of the proof ... not
  because the statement without it is known false" (READ: `ieee64/gate.json`, that plant's entry). DECLARED, with no
  staged record: on origin the statement without that premise was proved, so this plant removes nothing false; and
  `mode-div-na` and `mode-sqrt-na` (ties away from zero for division and square root) were argued on origin to be
  equivalent mutants. So "38 plants refused" is at most 35 demonstrations.
- Refuted by: a finite input inside the premises where IEEE binary64 arithmetic in round to nearest even gives
  another value than the graph; a defect in Flocq's formalization.

## 4. The gates

- Claim: a line `<NAME> GATE4 HELD: n of n [anchor ...]` shows what `gate/gate4.py` lines 6 to 29 list: the freeze
  list is readable, complete and matches the files; its sha256 is the anchor given to the run; every listed source
  compiles in a fresh root; Print Assumptions of the folder's identity is exactly the four axioms of
  `gate/expected-pa-flocq4.txt`; `coqchk -norec` accepts each module and every outside library of the closure; each
  plant is refused for its stated reason; nothing else was written in the tree.
- Grade and record: MEASURED, the six verdict lines of sections 1 to 3. The gate's own mutation test:
  `gate/gate4-selftest-run1.txt` `GATE4 SELFTEST HELD: 13 of 13  (205 s)`; `gate/gate4-selftest-run2-main.txt`
  `GATE4 SELFTEST HELD: 13 of 13  (110 s)`. Earlier gate forms and their consoles are kept as history.
- Does not show (READ: `gate/gate4.py` lines 31 to 44): that an anchor was recorded outside the tree before a run.
  Only `ieee64` has a staged anchor record; **for `f32`, `p32`, `p32r`, `exp32`, `exp32r` "the anchor was given from
  outside" is DECLARED by each console's line 7** and by nothing else staged. That a statement was fixed before its
  proof: `FROZEN4.txt` is written after the proofs, and "frozen before its proof" in a file header is DECLARED
  (finding F3). That the image is sound. That a statement says what it should, or that the plants are the right
  plants: a reader's judgment. The self-test has no mutant for the row "fresh root holds only the listed sources".
- By the owner's ruling of 2026-11-16 these lists and anchors are inputs of the tier's gates and are not the
  kernel's freeze: a changed file means a new list, a new anchor recorded outside the tree, and the gate run again
  (`README.md`).
- Refuted by: a gate run on these bytes, with the anchor from the table in `RUN.md`, that does not hold.

## 5. Generated programs against the graphs

- Claim 5a: the staged C (`orl/gen-nm/sweep.c`, sha256 begins `34e2ca3d6ac92358`; `orl/gen-nm/sweep2.c`,
  `597813397118fe8e`) includes no `<math.h>`, names square root and absolute value as compiler builtins, and passes
  this repository's `mathkernel/check.py`.
  Grade: READ for the first two (`orl/gen-nm/sweep.c` lines 3 to 12). The pass: MEASURED on origin in an exported
  copy (49 sources, 0 violations; a control file with `<math.h>` refused), **console not staged**: for a reader of
  this subtree it is DECLARED until `python -B mathkernel/check.py` is run here. Does not show: what a build links.
  By the owner's ruling of 2026-11-16, naming square root and absolute value in a function under test is not host
  libm in the sense of the boundary rule; the staged C names no header at all, so that allowance bears only on the
  C regenerated in an exported copy (`README.md`). The ruling is about program text, not about any build.
- Claim 5b: on sampled inputs the compiled earlier programs return, bit for bit up to the sign of zero, the values
  of the Coq graph texts evaluated exactly.
  Grade and record: MEASURED. `orl/evidence/graph-agree-run2.txt`:
  `COQ GRAPH = C PROGRAM HELD: narrow 30036 inputs 0 differ (188 in the sign of zero only, accepted); sqrt32 6011 inputs 0 differ ...; rsqrt32 6010 inputs 0 differ ...; hypot32 8000 inputs 0 differ ...; exp32 5516 inputs 0 differ ...; plants caught 5 of 5`.
  The first run is kept as failed: one of its plants was an equivalent mutant
  (`graph-agree-run1-FAILED-plant-KK-2p29-is-equivalent.txt`).
  Does not show: about 56,000 inputs are a sample; the evaluator is a Python program; the programs are the earlier
  ones, **not the staged C** (the record's lines 3 to 4 give the executables' sha256, beginning `6ed70f8f` and
  `ef9d229a`; it does not name the source keys `9636be961f77f659`, `fe58a39d58a9618c` that the other records carry).
- Claim 5c: for sqrt32 and rsqrt32 the generated functions equal the expression the earlier sweep ran, on every input.
  Grade and record: MEASURED. `orl/evidence/gen-equiv-run1.txt`:
  `GENERATED = SWEPT HELD: sqrt32 2139095040 inputs 0 differ; rsqrt32 2139095039 inputs 0 differ (plant: rsqrt32 differs on 2139095037 of 2139095039; program 9636be961f77f659)`.
  Does not show: the staged C (earlier program).
- **There is no program-to-graph proof**, and none is claimed. A sampled comparison cannot find a difference as rare
  as the one section 8 measures (2 inputs of 3,258,020,376).
- **The earlier programs and the staged C.** Claims 5b and 5c, the two `hypot32` samples, the `narrow` tests of
  section 9 and all of section 8 are keyed to the earlier programs. What ties them to the staged C: MEASURED,
  `orl/gen-nm/bridge-earlier-to-staged-run1-console.txt`, last line `CSIDE VERIFY HELD (run1)`: for `narrow`,
  `f_narrow`, `f_sqrt32`, `f_rsqrt32`, `f_hypot32` and `g_exp32` the compiled code is the same bytes in the earlier
  and the staged program (a planted change is seen as different); eleven sample sweep ranges print the same lines;
  the corpus mode gives the same 1,001,126 results for the five functions. Does not show: another compiler or host;
  the functions were made external in copies of the two files to be compared, since the programs inline them; the
  script that printed that console is not staged, so its rows cannot be read against a program.
- Refuted by: an input where a compiled program and the graph's exact value differ beyond the sign of a zero.

## 6. Sweeps and samples (the compiled programs against references)

One host, one compiler, one build of each program. For the earlier programs the records name compiler and options
(READ: lines 1 to 2 of `orl/evidence/gen-equiv-run1.txt`: `clang version 22.1.8`,
`-O2 -ffp-contract=off -fno-math-errno`). For the staged C the same compiler and options are DECLARED: no record under
`orl/gen-nm/` holds a version or a build command. No executable is staged. A log's executable hash can be compared
only with a rebuild, and a rebuild is not byte for byte the same (OBSERVED on origin: two builds of one source on one
host differed in one byte; cause not established).

### 6.1 narrow
- Claim: on 21,390,950,393 test values (five binary64 values for each finite binary32 number: the number, its upper
  tie point, the two binary64 neighbours of that point, one value just above the number) the staged program's
  `narrow` equals the C conversion `(double)(float)v`, bit for bit.

<details>
<summary>Grade, record, what it does not show</summary>

- Grade and record: MEASURED. `orl/gen-nm/sweeps-run1-console.txt` line 1
  `narrow   chunks 64/64 inputs 21390950393 | narrow differs from IEEE cast: 0 | not faithful: 0 | differs from correctly rounded: n/a | ok`
  and `SWEEPS HELD (program 34e2ca3d6ac92358)`; chunk log `orl/gen-nm/sweeps-34e2ca3d6ac92358.log`.
- Does not show: the test values at and above the largest binary32 number, which the loop leaves out
  (`orl/gen-nm/sweep.c` line 63; finding F5; covered on the earlier program by section 2.1's companion); every
  binary64 value (the sweep is over binary32 neighbourhoods); that the compiler's conversion is IEEE's (trusted). The
  chunk log is byte-identical to the earlier program's (`orl/gen/sweeps-9636be961f77f659.log`, same sha256) and names
  no program, executable or time: only its file name and the console tie it to the staged C.

</details>

### 6.2 sqrt32
- Claim: on all 2,139,095,040 non-negative finite binary32 inputs the staged program's result is faithful and equals
  the correctly rounded square root.

<details>
<summary>Grade, record, what it does not show</summary>

- Grade and record: MEASURED. Same console, line 3
  `sqrt32   chunks 64/64 inputs 2139095040 | narrow differs from IEEE cast: 0 | not faithful: 0 | differs from correctly rounded: 0 | ok`.
- Does not show: the loop computes a hand-written expression, not the generated function; that the two are the same is
  claim 5c of section 5, measured on the earlier program only. The reference for "correctly rounded" is the compiler's
  binary32 square-root builtin (`orl/gen-nm/sweep.c` lines 11 and 80): trusted.

</details>

### 6.3 rsqrt32
- Claim: on all 2,139,095,039 positive finite binary32 inputs the staged program's result is faithful.

<details>
<summary>Grade, record, what it does not show</summary>

- Grade and record: MEASURED. Same console, line 2
  `rsqrt32  chunks 64/64 inputs 2139095039 | narrow differs from IEEE cast: 0 | not faithful: 0 | differs from correctly rounded: n/a | ok`.
- Does not show: correct rounding (`n/a`: not judged); as 6.2 for the hand-written expression.

</details>

### 6.4 hypot32: SAMPLED ONLY, and only on the earlier program
- Claim: on two samples the earlier program's `hypot32` is faithful wherever it was judged.

<details>
<summary>Grade, record, what it does not show</summary>

- Grade and record: MEASURED. `orl/gen/hypot-sample-run1.txt`: `hypot32 sampled check: 1000000 pairs; not faithful: 0;`
  ... `HYPOT32 SAMPLE HELD`. `orl/evidence/hypot-check2-run1.txt`:
  `HYPOT32 SAMPLE 2 HELD: 1150003 pairs; in the domain of HYPOT32_FINITE 1024729, not faithful 0; outside it 125274 (not judged), of which the result is a finite binary32 number on 19622 and not on 105652; plant (two steps up) flagged on 1011 of the 1011 in-domain pairs it touched, 1124 touched in all, from 8 of 8 regimes`.
- Does not show: **there is no exhaustive record for hypot32 and there cannot be one of this kind** (two binary32
  inputs). On the staged C, hypot32 has 198 corpus inputs (section 7) and nothing else. Outside the domain nothing is
  judged. `hypot-sample-run1.txt` names no program and no seed: that it ran on the earlier program with a fixed seed
  is READ in the script (`orl/hypot_check.py` lines 2 and 13), not in the record.

</details>

### 6.5 exp32
- Claim: on all 3,258,020,376 finite binary32 inputs x <= XMAX the staged program's result is a non-negative finite
  binary32 number and a faithful rounding of exp x, judged against decimal arithmetic.

<details>
<summary>Grade, record, what it does not show</summary>

- Grade and record: MEASURED. `orl/gen-nm/sweep2-run1-console.txt`:
  `exp32 (sweep2.exe) chunks 256/256 inputs 3258020376 of 3258020376 | narrow differs from IEEE cast: 0 | not a non-negative binary32: 0 | faithfulness: NOT judged here (exp_exhaust_nm.py, decimal)`,
  `SWEEP HELD (program 597813397118fe8e)`. `orl/gen-nm/exp-exhaust-run1-console.txt`:
  `EXP32 EXHAUSTIVE (decimal) HELD: chunks 4096, inputs 3258020376, shortcut inputs 2645557250, decimal-checked inputs 612463126, not faithful 0, ambiguous 0`;
  log `orl/gen-nm/exp-exhaust-597813397118fe8e.log`.
- Does not show: correct rounding (not claimed). 2,645,557,250 inputs are judged by three shortcuts whose premises
  are checked in decimal at start-up, not by a decimal exp each. The reference is Python's `decimal` at 40 digits:
  trusted (section TRUST). The earlier program's comparison with the C runtime's `exp` is dropped for the staged C;
  its record stays (`orl/gen/sweep2-run1.txt`: `differs from the rounded runtime exp: 1714`).

</details>

### 6.6 Earlier programs, kept records
- `orl/gen/sweeps-run2.txt` `SWEEPS HELD (program 9636be961f77f659)`; `orl/gen/sweep2-run1.txt`
  `SWEEP HELD (program fe58a39d58a9618c)`; `orl/gen/exp-exhaust-run2.txt` and `exp-exhaust-run1.txt` (two consoles
  under one log name: run1's invocation computed 82 of the 4096 chunks, run2's all 4096; same totals as 6.5); plants
  `exp-exhaust-plant-run1.txt`, `exp-exhaust-plant-run2-boundaries.txt`, `sweep2-plant-run1.txt`; sample
  `orl/gen/exp-sample-run1.txt` `EXP32 SAMPLE HELD`. Log tiling: `orl/evidence/chk-logs-run1.txt`
  `SWEEP LOGS TILE HELD: ... 19 of 19 rows ok; plants failed as required 10 of 10` (earlier logs only; **no tiling
  record for the `gen-nm` logs**). That record reproduces on origin only: in an exported copy the test ends
  `17 of 19 rows ok`, because the two `exp-exhaust` logs pin the sha256 of origin's executable (measured on origin,
  console not staged: DECLARED for a reader of this subtree; `RUN.md` section 6).
- A kept failure, not a pass: `orl/gen/sweeps-run1-FAILED-signed-zero.txt` `SWEEPS FAILED (program a28f24687031a586)`
  (an earlier `narrow` returned +0 where the conversion returns -0; repaired; section 9).

Refuted by, for all of section 6: one input in a swept range where a build of the staged C under THE BOUNDARY returns
a value that is not faithful.

## 7. Corpus and backends

- Claim: on 1,126 chosen inputs (narrow 322, sqrt32 200, rsqrt32 200, hypot32 198, exp32 206) the Orlog language's
  reference interpreter, its C99, Python and Rust backends, the staged native program, a Python evaluation of the
  graph and the C conversion agree bit for bit.
- Grade and record: MEASURED, backend-specific. `orl/gen-nm/corpus-run1-console.txt` (four lines ending
  `orlog = native C = python graph = IEEE cast: yes`, then `CORPUS AGREEMENT HELD`);
  `orl/gen-nm/corpus-exp32-run1-console.txt` (`exp32    206 inputs | ... yes`, `CORPUS AGREEMENT HELD`). Earlier:
  `orl/gen/corpus-run1.txt`, `corpus-run2.txt`, `corpus-exp32-run1.txt`.
- Does not show: a sweep (the inputs are chosen and seeded); agreement with the graph beyond these inputs;
  conformance of any backend in general; which commit of the language ran (no staged record names one); that
  language's own claims. The corpus laws are renderings and define nothing; this is consumer-side evidence.
- Refuted by: a corpus input on which two of the parties differ, at the commit `RUN.md` declares.

## 8. Contraction (fused multiply-add) evidence

- Claim: a build that contracts is refused by the tier's references for `narrow` and for `exp32`; for `hypot32` and
  two sites of `exp32` contraction changed no result on the inputs tried; `sqrt32` and `rsqrt32` have no site of
  their own.
- Grade and record: MEASURED. `orl/evidence/fma-plant-run1.txt` last line:
  `FMA PLANT HELD: contracted build refused for narrow (n_outer, n_inner, n_both), exp32 (fast, dropped: on 2 of its 3258020376 inputs); equivalent mutant for hypot32 (fast, dropped: 0 of 1158209 pairs of binary32 inputs differ, and none can), exp32 (x_mm, x_cv: 0 of its 3258020376 inputs differ); no contraction site in sqrt32, rsqrt32 (none of their own; narrow's, which every function ends in, is counted under narrow)`.
- Claim: the code under test in the earlier programs holds no fused multiply-add instruction and makes no call.
  Grade and record: `orl/evidence/FMA-LINKED.md`, "holds as far as the checks below reach" (its line 13): MEASURED
  for the counts, ARGUED for reachability; its section "What remains unproven" (line 139) is part of the claim.
- Does not show: **where the plant is an equivalent mutant the test cannot refuse a contracted build**, and says so;
  "and none can" for hypot32 is the record's own argument, not checked here; everything is on the earlier programs
  and one toolchain; this is evidence about `-ffp-contract=off` builds and **not enforcement of THE BOUNDARY**.
  At this destination: `fma_undertest.py` reproduces after the regeneration step of `RUN.md` section 5 (MEASURED on
  origin in an exported copy: `orl/evidence/dest-repro-run1-console.txt`: 0 call instructions, 0 fused multiply-add,
  3 `sqrtsd`). `fma_plant.py` ends with the same last line (measured on origin in an exported copy, console not
  staged: DECLARED for a reader of this subtree).
- Refuted by: a fused multiply-add instruction inside the functions under test in a build with the recorded options.

## 9. narrow: the sign-of-zero regression and the top of the range

- Claim: the current `narrow` equals the C conversion on a fixed list of 32,185 inputs; the earlier `narrow` and the
  one of the failed run differ from it, in the sign of a zero only; the Python and C definitions agree.
- Grade and record: MEASURED. `orl/evidence/narrow-regress-run3.txt` (and its byte-identical twin
  `narrow_regress-main-rerun.txt`):
  `NARROW REGRESSION HELD: 32185 inputs; current differs on 0; old differs on 1744 (not sign of zero: 0); run-1 differs on 1742 (not sign of zero: 0); Python differs from C on 0`.
  Under the owner's ruling it counts as evidence at this destination when it reproduces in an exported copy after the
  staged emitters regenerate `orl/gen/sweep.c` and `sweep2.c` (`RUN.md` section 5). That it does: MEASURED on
  origin in an exported copy, `orl/evidence/dest-repro-run1-console.txt`:
  `narrow_regress.py: exit 0, console 3593 bytes, BYTE FOR BYTE the staged record narrow-regress-run3.txt (3593 bytes)`.
  That console was made on the 243 files staged before it and two other records were added. Does not show: another
  compiler or host; a run from a checkout of this repository.
- **Reproduced-on-origin-only** (the owner's ruling): `narrow-regress-run1.txt`, `narrow-regress-run2.txt`,
  `narrow-regress-run2b-before-binding.txt`. Byte-identical to each other; an earlier script wrote them.
- The top of the range: section 2.1's companion record. Its first run is kept as failed
  (`narrow-top-run1-FAILED-test-expected-wrong-OVF-bits.txt`: the test's own expectation was wrong).
- Does not show: the staged C (earlier program; the sign of zero on the staged C is covered by section 6.1's
  comparison with the conversion, which is bit for bit).

## TRUST: what every claim above rests on and cannot remove

| trusted | for | note |
|---|---|---|
| the Coq kernel (`coqc`) | sections 1 to 3 | version as the image holds it; the image is not staged |
| `coqchk` | sections 1 to 3 | an independent recheck of each compiled module, run with `-norec`; outside libraries held one by one |
| four axioms, exactly: `ClassicalDedekindReals.sig_not_dec`, `ClassicalDedekindReals.sig_forall_dec`, `FunctionalExtensionality.functional_extensionality_dep`, `Classical_Prop.classic` | sections 1 to 3 | `gate/expected-pa-flocq4.txt`; the gate fails on any other assumption and on a missing one |
| Flocq 4.2.1: its FLT model, and that its `BinarySingleNaN` operations are IEEE 754 binary64's | sections 1 to 3 | the correspondence is to Flocq's formalization, not to a standard's text |
| the generators (`orl/emit.py`, `emit2.py`, `emit_nm.py`, `emit2_nm.py`, `exp32r/gen_range.py`, the plant makers) | sections 1 to 7 | the gate holds a generated Coq file to what its generator prints; `narrow` and its constants are written once per language inside the emitters, and only the Coq rendering is held this way (finding F2) |
| the gate programs and the container image | sections 1 to 4 | written by the tier's author; the self-test is by the same author |
| the C compiler, its builtins (the binary32 square root is section 6.2's reference) and its float conversion; the linker and runtime | sections 5 to 9 | one version, one option set; not verified |
| the processor's binary64 arithmetic and its control state | sections 5 to 9 | THE BOUNDARY; not checked |
| Python's `decimal` (libmpdec) `exp`, documented as correctly rounded, at 40 digits | exp32, section 6.5 | the only reference for exp32's faithfulness on the staged C |
| Python's float and integer arithmetic in the test scripts | sections 5 to 9 | the references and the graph evaluator are Python programs |
| the Orlog language's interpreter and backends | section 7 | another repository's |
| the statements say what is meant | everything | a reader's judgment. The reviews that exist (2026-11-14, 2026-11-15) are by models of the provers' own family (DECLARED; `FINDINGS.md`) |

## What is NOT claimed

- Not that any function is correct on a processor: only the layered claims above, each with its limits.
- Not a zero-trust result. The list above is what is trusted.
- Not a proof that a program computes a graph. Not a verified compiler.
- Not correct rounding, except where a sweep line says `differs from correctly rounded: 0` (sqrt32, the program).
- Not exhaustive coverage of hypot32.
- Not the sign of a zero result, NaN, infinities, or any input outside the premises: what the programs return there
  is recorded as measured, not specified. There is no out-of-domain policy and no consumer interface.
- Not enforcement of the control state. Not behaviour under any other control state.
- Not another compiler, option set, build, operating system or processor. No cross-platform determinism.
- Not speed, latency or cost of any kind.
- Not review by another model family or by a human expert.
- Not that a backend of the Orlog language conforms; not anything about that language.
- Not a contract, a freeze or an admission: nothing under `mathkernel/FROZEN/` or `mathkernel/interface/` changes, and
  nothing here is adopted.
- Not a composition of the IEEE-level statement with the faithfulness and range theorems as one theorem.
- Not a contract for any function. The owner has ruled which text defines a function (its operation graph); no
  F32 contract exists, and outside the premises nothing is defined.
