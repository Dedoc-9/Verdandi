# mathkernel/F32: five binary32 functions computed with binary64 operations

**Status: an unfrozen, unadmitted candidate family. Nothing here is adopted.**
No file under `mathkernel/FROZEN/` is added or changed by this subtree, no entry is added to `mathkernel/interface/`,
no backend is admitted, and no consumer may bind to anything in this folder. It is presented at no higher level than
proven primitives, and not as a zero-trust deliverable. Landing these files adopts none of the design choices listed
at the end of this page.

integrity is not truth; declared is not verified; built is not adopted.

Read `LIMITATIONS.md` first: what the five functions do not state, and what their sweeps do not cover.

Every record here was made on one machine. Its operating system, processor and toolchain are stated at the opening of
`CLAIMS.md`.

## What it is

Five functions that take binary32 inputs and return a binary32 result, each written as a short fixed sequence of
binary64 operations (add, subtract, multiply, divide, square root, absolute value, compare-and-select):

| function | in plain words |
|---|---|
| `narrow` | rounds a binary64 value to binary32, to nearest even, using binary64 operations only |
| `sqrt32` | square root |
| `rsqrt32` | one over the square root |
| `hypot32` | square root of x*x + y*y |
| `exp32` | e to the x, for x at most XMAX = 88.72283172607421875 |

For each there are Coq statements written as files of their own, proofs, a gate that judges the proofs and refuses
planted wrong versions, a generated C program, and run records of sweeps and tests. Every statement, note and record
here is descriptive: this subtree carries no F32 contract, frozen or draft, and no consumer interface.

## The layers, and where each lives

A pass at one layer never stands for another. `CLAIMS.md` gives each claim with its grade, its record and what it
does not show.

| layer | what it is about | where |
|---|---|---|
| 1. model statements and proofs | operation graphs over the real numbers in a model of binary64 that has no overflow, no sign of zero, no NaN, no infinity: each graph returns a faithful binary32 rounding (`narrow`: the round-to-nearest-even one) | `f32/` (the lemma `narrow` rests on), `p32/` (`narrow`, `sqrt32`, `rsqrt32`, `hypot32`), `exp32/` |
| 2. finiteness and range | on stated premises the graph's result is a finite binary32 number; the premises are sufficient and not shown necessary (one sharpness example each for `narrow`, `hypot32`, `exp32`) | `p32r/`, `exp32r/` |
| 3. IEEE-level correspondence | IEEE 754 binary64 operations (as one Coq library formalizes them), in the graph's order, in round to nearest even, return a finite value that denotes the graph's value, on each function's premises | `ieee64/` |
| 4. the gates | one program judges a folder: freeze list, anchor, fresh compile, assumptions, independent recheck, plants | `gate/`, each folder's `gate.json`, `plants/`, `FROZEN.txt`, `FROZEN4.txt`, gate consoles |
| 5. generated programs | C written by the emitters; the staged C includes no `<math.h>` | `orl/emit_nm.py`, `orl/emit2_nm.py`, `orl/gen-nm/sweep.c`, `orl/gen-nm/sweep2.c` |
| 6. sweeps and samples | every input of the one-input functions through the compiled program; samples for `hypot32` | `orl/gen-nm/` (the staged C), `orl/gen/` (earlier programs) |
| 7. corpus and backends | a few hundred inputs per function through a prose language's reference interpreter and its three backends | `orl/gen-nm/corpus-*`, `orl/gen/corpus-*` |
| 8. tests and negative controls | graph against program (sampled), top of `narrow`'s range, sign-of-zero regression, contraction plant | `orl/evidence/` |

`orl/gen/` holds the records of the earlier programs `sweep.c` and `sweep2.c`, which include `<math.h>` and are
therefore **not in this subtree**; the emitters `orl/emit.py` and `orl/emit2.py` that write them are. `RUN.md` says
how they are regenerated, and why only ever in an exported copy.

## What is NOT here

- **No program-to-graph proof.** That a compiled program performs the graph's operations is supported by a sampled
  comparison and by exhaustive comparison with references, not by a proof.
- **No verified compiler, and no statement about a processor.** One compiler, one build, one host.
- **`hypot32` is sampled, not swept.** Two samples (1,000,000 and 1,150,003 pairs), both run on the earlier program;
  on the staged C there are 198 corpus inputs and nothing else.
- **No review by another model family, and none by a human expert.** The reviews that exist (2026-11-14 and
  2026-11-15) are by models of the provers' own family (DECLARED). See `FINDINGS.md`.
- **No enforcement of the floating-point control state.** `CLAIMS.md`, section THE BOUNDARY, names the state the
  claims need; nothing here checks it at run time.
- **No composition theorem.** No staged theorem joins layer 3 to layers 1 and 2 in one statement.
- **Nothing about the sign of a zero result, NaN, infinities, or inputs outside the premises.** What the programs
  return there is recorded as measured, not specified.
- **No gate row in this repository's gate, no timing claim, no claim about another platform.**
- **The container image recipe, the checked-library cache, every executable and the language checkout of layer 7**
  are not in this subtree. Several records cite files that are not here; `RUN.md` lists them.

## Three questions the repository owner has ruled (2026-11-16)

- **What defines a function.** Each function is defined by its operation graph as `p32/Graphs.v` and `exp32/Graph.v`
  state it, at the sha256 the tier's `FROZEN4.txt` lists give those files: operations on real numbers in the stated
  order, each rounded to nearest even in the model's binary64, for inputs that meet the premises of its statement and
  of its range statement. The emitter's definition, the generated C, the corpus law and every backend are renderings,
  and none of them is a numerical authority. Three claims stay separate: a proof is about the graph; that a program
  implements the graph is a claim about that program; that a backend conforms is a claim about that backend. This
  fixes which text governs among the renderings. It freezes nothing and adopts no design choice. Nothing is defined,
  until an F32 contract specifies it, for inputs outside the premises, for the sign of a zero result, for NaN and
  for infinities.
- **What the freeze lists are to the kernel's freeze.** The per-folder `FROZEN.txt` and `FROZEN4.txt` lists and their
  anchors are inputs of this tier's own gates. They are not the kernel's freeze under `mathkernel/FROZEN/`, and a
  change to a file they name is not a succession event: it is a new freeze list in place of each list that names the
  file, with its new anchor recorded outside the tree, beside the one it replaces, before a gate is run on it. No
  gate result is stated for a changed list until that gate has been run again on it and has held. Once an F32
  contract that covers a function is frozen, a change to that function's normative definition is a succession event.
  "Frozen" in a file header here means "by the tier's own lists".
- **Square root and absolute value under "no host libm".** For this subtree a generated program may name square root
  and absolute value, applied to binary64 values, in a function under test; that is not host libm in the sense of
  the boundary rule, whatever header names them. Any other host library function may appear only on the harness or
  reference side of a test program. The allowance is about program text and is not evidence about any build. The
  staged C includes no `<math.h>` and calls no host library function for mathematics, so the allowance bears only on
  the C that the staged emitters regenerate in an exported copy (`RUN.md` section 5). `mathkernel/check.py` passes on
  the staged files (measured on origin on one host, console not staged: DECLARED for a reader of this subtree; it
  reads the include lines of `.c` and `.h` files, so it does not show what a build links). One condition is set on
  any later admission of a backend, and it admits nothing: a checked row of that admission's gate must inspect, in
  the exact binary to be admitted, the code that computes the function and every routine that code reaches, and
  require that none of it is a host library function. No such row exists.

These paragraphs restate the rulings; they are not quotations. The rulings' own words are in the owner's records.

## Where to start reading

1. `CLAIMS.md`, then `FINDINGS.md`.
2. `p32/P32_Statement.v` with `p32/P32_Statement.NOTE-2026-11-14.md`; `f32/F32_Statement.v` and
   `exp32/EXP32_Statement.v` with their notes. The notes correct how three header comments are to be read; the
   statement files' bytes are unchanged.
3. `p32r/P32R_Statement.v`, `exp32r/RANGE_Statement.v`.
4. `ieee64/IEEE64_Statement.v`, lines 1 to 45: what it says, what it does not say, what it trusts.
5. `p32/Graphs.v`, `exp32/Graph.v`: the graphs everything is about.
6. `gate/gate4.py`, lines 1 to 44: what a HELD shows and what it does not.
7. `orl/gen-nm/sweep.c`, `orl/gen-nm/sweep2.c`, then the six `orl/gen-nm/*-run1-console.txt`.
8. The kept failures: `orl/gen/sweeps-run1-FAILED-signed-zero.txt`,
   `orl/evidence/graph-agree-run1-FAILED-plant-KK-2p29-is-equivalent.txt`,
   `orl/evidence/narrow-top-run1-FAILED-test-expected-wrong-OVF-bits.txt`.
9. `RUN.md` to check any of it.

## Words used in the recorded files

File headers and records are held by sha256 as written. Folder prefixes in them, and the words that tell two
invocations apart, name nothing in this repository. Findings numbered in the three dated notes and in script headers
(for example "F1, F2, F9") belong to an earlier review of 2026-11-14 and are a different numbering from `FINDINGS.md`.

## Design choices that landing does not adopt

Working defaults of the tier's author, not rulings:

1. Results are carried in binary64 between operations and narrowed once at the end.
2. `narrow` is held to the IEEE binary64-to-binary32 conversion (round to nearest even).
3. The design of `exp32` (divide by 4096, a degree-7 polynomial, twelve squarings) and its input limit XMAX.
4. `hypot32`'s domain is a premise on the exact result (at most the largest binary32 number), the caller's to meet.
