# mathkernel/F32: how to check it

Status of the subtree: an unfrozen, unadmitted candidate family; nothing here is adopted (`README.md`).
Grades used below: MEASURED, READ, ARGUED, DECLARED, OBSERVED, NOT_MEASURED. "On origin" means: where the tier was
built, one host, before these files were staged. Nothing below has been run from a checkout of this repository.

## 0. The one rule: every run happens in an EXPORTED COPY, never in the checkout

`mathkernel/check.py` walks every `.py`, `.c` and `.h` file that is on disk under `mathkernel/`. It does not ask git
which files are tracked, so an ignored or untracked file fails it just the same (READ: `mathkernel/check.py`, the
walk and the include rule). Several programs of this subtree write C that includes `<math.h>`:

- `orl/emit.py emit` and `orl/emit2.py emit` write `orl/gen/sweep.c` and `orl/gen/sweep2.c`;
- `orl/evidence/narrow_regress.py` writes `orl/evidence/narrow_regress.c`;
- `orl/evidence/fma_undertest.py` writes `orl/evidence/fma/undertest_sweep.c` and `undertest_sweep2.c`.

Run inside the checkout, any of them turns `MATHKERNEL CHECK PASSED` into `MATHKERNEL CHECK FAILED` (measured on
origin in exported copies of this repository's `mathkernel/`: 1 violation after one test writer, 5 after the emitters
and both writers; those consoles are not in this subtree, so DECLARED for a reader here). The gates, the builds and
the sweeps also write files (`out4/`, `libcache/`, executables, logs). So:

1. Export: `git archive <commit> mathkernel/F32 | tar -x -C <empty folder>` and work in
   `<empty folder>/mathkernel/F32`, called `<F32>` below. `mathkernel/.gitattributes` and this folder's
   `.gitattributes` keep every byte as committed.
2. Run nothing of this page inside the checkout. Copy nothing back from the exported copy.
   Before anything else, compare the exported copy with `MANIFEST.sha256`: it lists the sha256 of each of the 246
   staged files (not of the root files). From `<F32>`, `sha256sum -c MANIFEST.sha256` reads it, the two comment
   lines aside; every line must end `OK`. It shows the bytes are the ones staged, and nothing about what they say.
3. The only command for the checkout is the repository's own: `python -B mathkernel/check.py`, expected last line
   `MATHKERNEL CHECK PASSED`. It reads; it writes nothing. (Measured on origin in an exported copy holding the 246
   staged files and the root files: 49 sources scanned, 0 violations; console not staged, so DECLARED for a reader
   here. Does not show: the checkout, any other check of this repository.)

A rerun never overwrites a record: write new consoles outside `<F32>` or under new names.

## 1. Toolchain, as the records state it

| used for | what the records state | where stated |
|---|---|---|
| proofs and gates | a container image whose id begins `sha256:e5d68b0139b5`; `coqchk` 8.20; Flocq 4.2.1; Python 3 | `f32/gate-run1-console.txt` line 2; `gate/gate4.py` line 38; `ieee64/IEEE64_Statement.v` line 41 |
| programs and tests | `clang version 22.1.8`, options `-O2 -ffp-contract=off -fno-math-errno`; `llvm-objdump` of the same LLVM; Python 3.14 | line 1 of the `orl/evidence/*-run*.txt` records; `orl/evidence/fma-plant-run1.txt` line 2 |
| exp32's reference | Python's `decimal` module (libmpdec), 40 significant digits | `orl/exp_exhaust_nm.py` lines 10 to 17 |

The machine and the versions as read from it are at the opening of `CLAIMS.md`. DECLARED, with no staged record:
Coq 8.20.1, Coq Interval 4.11.1. **The image's recipe is not in this subtree**, and
neither is the cache of checked libraries (`libcache/`). A different image is a different run; its result says nothing
about these records.
Python is run as `python -B` with `PYTHONHASHSEED=0 PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1`; standard library only.
The records' program names end in `.exe` as they were built. No result is claimed for another compiler, another
build or another platform.

## 2. The gates (layers 1 to 4)

The form, from `gate/gate4.py` line 3, with `<F32>` mounted as the tree:

```
docker run --rm --network none -e ANCHOR=<anchor> -v <F32>:/work -w /work <image> \
  sh -c 'timeout <seconds> python3 -B gate/gate4.py <folder> --recheck'
```

One container at a time. The anchor is the sha256 of `<folder>/FROZEN4.txt` and must come from outside the tree you
are judging: take it from the table (the committed consoles' second lines), not from the exported copy's own list.

| folder | ANCHOR | expected last verdict line (from `<folder>/gate4-run1-console.txt`) |
|---|---|---|
| `f32` | `53880a185dd4b23539f38a446d94f16dcb1f1cf1f69a061c78ec32c1f23ca002` | `F32 GATE4 HELD: 20 of 20  [anchor 53880a185dd4b235]` |
| `p32` | `9adba8eecba84425d258869e9a644622281644a1adcf4ebc40b147390ac7ee45` | `P32 GATE4 HELD: 35 of 35  [anchor 9adba8eecba84425]` |
| `p32r` | `2fc8014ccb21d40bb0c9215cbeff931c45f4fc1831528eb6c52e9a07ee84cb5e` | `P32R GATE4 HELD: 41 of 41  [anchor 2fc8014ccb21d40b]` |
| `exp32` | `68481fb907358ff7d76ab974246b42ed4a1eb1c7ebbe31abe309c97c03273fb8` | `EXP32 GATE4 HELD: 47 of 47  [anchor 68481fb907358ff7]` |
| `exp32r` | `c7052646819b4e690ff7c85648f188643442e5701bedfd8fcbfd9151a1ad9b4a` | `EXP32R GATE4 HELD: 54 of 54  [anchor c7052646819b4e69]` |

Each console ends with `exit 0` after the verdict line. What to know before running:

- NOT_MEASURED: a `gate4.py` run in a fresh exported copy. The records were made in a tree that already held
  `libcache/`. With `--recheck` every outside library is checked by `coqchk` in the run itself (READ: `gate/gate4.py`
  lines 22 to 26); whether the run holds with no `libcache/` folder present has not been tried. Time limits are not
  recorded here; a recorded run checked 295 libraries (f32) and takes correspondingly long.
- The gate writes `<folder>/out4/`, `libcache/checked4.log` and `libcache/out4/` in the tree it stands in, and its
  last row fails if anything else is written in that tree during the run. Keep the exported copy quiet.
- Do not run `gate/freeze4.py`: it rewrites a freeze list. By the owner's ruling a changed list is a new list, with
  a new anchor recorded outside the tree before any gate is run on it (`README.md`).
- **`ieee64` has a gate program of its own**, `ieee64/gate_ieee64.py` (sha256 `ac172a43...`, as `ieee64/gate.json`
  line 5 and `ieee64/ANCHOR4-run1.txt` line 8 name it); its header gives the command. A run of it from an exported
  copy is NOT_MEASURED. Its record:
  `ieee64/gate-run1-console.txt`, last verdict line
  `IEEE64 GATE HELD: 13 of 13 rows here, gate4.py 148 of 148 on the copy  [anchor 42e3891e153bafae]`, and the anchor
  record `ieee64/ANCHOR4-run1.txt` (anchor `42e3891e153bafae200b7e3b48c2573fbc4406d58fa941bd0bf1f672f51ddb42`,
  statement sha256 `7cbcac51c912286bc9ea64ef2880cf7685ff2027e02902a5ceeae3e693e428de`).
- The older gate forms `gate/gate.py` and `gate/gate3.py` are kept as history with their consoles
  (`gate-run*-console.txt`, `gate3-run1-console.txt`). They need `-e IMG=<image id>` and a file `libcache/IMAGE.txt`
  that is not staged: not reproducible from a fresh export, and not designed to be.
- The gate's own mutation test: `gate/gate4_selftest.py` (command in its lines 1 to 2). Recorded last lines:
  `GATE4 SELFTEST HELD: 13 of 13  (205 s)` and `GATE4 SELFTEST HELD: 13 of 13  (110 s)` (the time will differ). In a
  fresh export: NOT_MEASURED. It copies `libcache/checked4.log` only if that file is present, and edits it (READ: its
  lines 82 and 121); an export has none.

A HELD shows what `gate/gate4.py` lines 6 to 29 list and nothing of lines 31 to 44. It says nothing about a
program, a compiler or a processor.

## 3. The staged programs and their sweeps (layers 5 and 6)

All from `<F32>/orl`. The emitters and sweeps name their files relative to their own location.

1. Regenerate and compare: `python -B emit_nm.py emit`, then `python -B emit2_nm.py emit`. Expected lines
   (`gen-nm/emit-run1-console.txt`): `emitted gen-nm/sweep.c and 4 corpus laws` and
   `emitted gen-nm/sweep2.c and gen-nm/corpus_exp32.orl (206 inputs)`. Then `gen-nm/sweep.c` must still have sha256
   `34e2ca3d6ac92358da17d716cf55106737941977b7385b2c44c3abec20e21655` and `gen-nm/sweep2.c`
   `597813397118fe8e9645f9e11b12f9b12b80c9af1076c84a2f29ed41ad57956b`. Every record below is keyed by the first 16
   digits of these.
2. Build, in `gen-nm/` (the line each C file carries in its second line):
   `clang -O2 -ffp-contract=off -fno-math-errno sweep.c -o sweep.exe` and the same for `sweep2.c`. Expect one
   deprecation warning each. The staged build logs (`gen-nm/build-sweep.log`, `build-sweep2.log`) were captured from
   another folder and name the source by a longer path, so a rerun's output differs from them from the first byte.
3. **Move the committed logs aside first.** `gen-nm/sweeps-34e2ca3d6ac92358.log` and `sweep2-597813397118fe8e.log`
   carry no header: a sweep run beside them skips every chunk they hold and computes nothing (READ: `emit_nm.py`
   `sweeps`). `exp-exhaust-597813397118fe8e.log` pins in its first line the sha256 of origin's `sweep2.exe`; a rebuilt
   executable has another hash, and `exp_exhaust_nm.py` then stops with `... was begun for another program` and exit 1
   instead of replaying (measured on origin in an exported copy, console not staged: DECLARED for a reader here).
4. `python -B emit_nm.py sweeps`. Expected (`gen-nm/sweeps-run1-console.txt`):
   ```
   narrow   chunks 64/64 inputs 21390950393 | narrow differs from IEEE cast: 0 | not faithful: 0 | differs from correctly rounded: n/a | ok
   rsqrt32  chunks 64/64 inputs 2139095039 | narrow differs from IEEE cast: 0 | not faithful: 0 | differs from correctly rounded: n/a | ok
   sqrt32   chunks 64/64 inputs 2139095040 | narrow differs from IEEE cast: 0 | not faithful: 0 | differs from correctly rounded: 0 | ok
   SWEEPS HELD (program 34e2ca3d6ac92358)
   ```
5. `python -B emit2_nm.py sweep`. Expected last line (`gen-nm/sweep2-run1-console.txt`):
   `SWEEP HELD (program 597813397118fe8e)`. This sweep does not judge faithfulness; step 6 does.
6. `python -B exp_exhaust_nm.py`. Expected last verdict line (`gen-nm/exp-exhaust-run1-console.txt`; the recorded run
   took 1753 s):
   `EXP32 EXHAUSTIVE (decimal) HELD: chunks 4096, inputs 3258020376, shortcut inputs 2645557250, decimal-checked inputs 612463126, not faithful 0, ambiguous 0`
   For a short first look, `--seconds N` starts no chunk after N seconds (READ: `exp_exhaust_nm.py` line 29). OBSERVED
   on origin, one host, no timing claim: steps 4 and 5 took about 53 s and 9 s.

The logs record the sha256 of the executables that wrote them (for example line 1 of
`gen-nm/exp-exhaust-597813397118fe8e.log`). No executable travels, and a rebuild does not give the same bytes
(OBSERVED on origin: two builds of one source on one host differed in one byte; cause not established), so those
hashes can be checked against nothing here. Another compiler version may give other results; that would be a finding,
not a failure of these instructions.

## 4. Corpus and backends (layer 7): needs a checkout that is NOT staged

`python -B emit_nm.py corpus` and `python -B emit2_nm.py corpus` run each corpus law through the Orlog language's
reference interpreter and its C99, Python and Rust backends, and compare bits with the native program of step 3.
They need:

- the Orlog language checkout placed at `<F32>/orl/O` (they run `orl.py` there) and a work folder `<F32>/orl/wd`.
  The language is public at `https://github.com/Dedoc-9/Orlog`. DECLARED: the commit used is
  `221c3874f072bc168e9e412517195681c18a2254`; **no staged record names a commit of that repository**;
- that language's own toolchain for its three backends (not stated in any staged record);
- `gen-nm/sweep.exe` and `gen-nm/sweep2.exe` from step 3.

Expected (`gen-nm/corpus-run1-console.txt`, `gen-nm/corpus-exp32-run1-console.txt`): one line per function ending
`orlog = native C = python graph = IEEE cast: yes` (narrow 322 inputs, sqrt32 200, rsqrt32 200, hypot32 198,
exp32 206) and the last line `CORPUS AGREEMENT HELD`.

These records are backend-specific, consumer-side evidence. The corpus laws are renderings and define nothing.
No check of this repository runs this step, and nothing of this subtree goes to that repository.

## 5. The two test writers: regenerate first (the step the owner's ruling requires)

A record of `narrow_regress.py` or `fma_undertest.py` counts as evidence at this destination when it reproduces in
an exported copy after the staged emitters regenerate `orl/gen/sweep.c` and `orl/gen/sweep2.c`. As staged, neither
reproduces: both read those two files, which are not in this subtree. In `<F32>/orl`:

1. `python -B emit.py emit` and `python -B emit2.py emit`. They write `gen/sweep.c` (sha256 begins
   `9636be961f77f659`) and `gen/sweep2.c` (`fe58a39d58a9618c`), the keys the `orl/gen/` and `orl/evidence/` records
   carry, and rewrite the committed corpus files with the same bytes. Both C files include `<math.h>`: this is why
   the copy is an exported one.
2. Create the folder `evidence/fma/`. No staged file creates it and `fma_undertest.py` stops without it.
3. `python -B evidence/narrow_regress.py`. Expected: the console is byte for byte `evidence/narrow-regress-run3.txt`
   (and its twin `evidence/narrow_regress-main-rerun.txt`), last line
   `NARROW REGRESSION HELD: 32185 inputs; current differs on 0; old differs on 1744 (not sign of zero: 0); run-1 differs on 1742 (not sign of zero: 0); Python differs from C on 0`.
   Byte identity needs the compiler whose version string is the record's first line.
4. `python -B evidence/fma_undertest.py`. It has no console record. Expected: the facts `evidence/FMA-LINKED.md`
   lines 70 to 74 state (undefined symbols `_fltused` only; relocations to floating constants only; 0 call
   instructions, 0 indirect jumps, 0 fused multiply-add instructions; 3 inline `sqrtsd`).

MEASURED on origin in an exported copy: `evidence/dest-repro-run1-console.txt` (made on the 243 files staged before
it and two other records were added). It shows steps 1 to 4 as stated, that without step 1 `narrow_regress.py` stops
with no verdict line, and that the staged files are unchanged afterwards. Does not show: another compiler, another
host; that `fma_undertest.py` stops without step 2 (measured on origin, console not staged: DECLARED).

**Marked reproduced-on-origin-only** (the owner's ruling): `evidence/narrow-regress-run1.txt`,
`evidence/narrow-regress-run2.txt`, `evidence/narrow-regress-run2b-before-binding.txt`. They are byte-identical to
each other and were written by an earlier version of the script; their content is the current console without its
seven later rows, their bytes do not reproduce.

## 6. The other tests on the earlier programs (layer 8)

They read `gen/sweep.c`, `gen/sweep2.c` or the executables built from them, so they also need step 5.1 and then
`clang -O2 -ffp-contract=off -fno-math-errno sweep.c -o sweep.exe` (and `sweep2`) in `gen/`. Each script's header says
what it does; `evidence/main-rerun-2026-11-14.txt` holds one line per script from a second invocation on origin. The
last column says what a run in an exported copy of the 243 files staged before three records were added gave on origin, one host (consoles not staged:
DECLARED for a reader here). `exp_exhaust.py` in full: NOT_MEASURED.

<details>
<summary>The nine commands, their records, and what each gave in an exported copy</summary>

| command (from `<F32>/orl`) | record | expected last line begins | in an exported copy |
|---|---|---|---|
| `python -B evidence/graph_agree.py` | `evidence/graph-agree-run2.txt` | `COQ GRAPH = C PROGRAM HELD: narrow 30036 inputs 0 differ (188 in the sign of zero only, accepted);` ... `plants caught 5 of 5` | last line identical; lines 3 to 4 (executable hashes) differ |
| `python -B evidence/gen_equiv.py` | `evidence/gen-equiv-run1.txt` | `GENERATED = SWEPT HELD: sqrt32 2139095040 inputs 0 differ; rsqrt32 2139095039 inputs 0 differ` | byte-identical after moving `evidence/gen-equiv-*.log` aside; beside those logs it prints `0 chunks run now` and computes nothing |
| `python -B evidence/narrow_top.py` | `evidence/narrow-top-run2.txt` | `NARROW TOP HELD: below OVF 33554432 values, differ from the conversion 0; around FLT_MAX 67108866 values, differ 0;` | byte-identical |
| `python -B evidence/chk_logs.py` | `evidence/chk-logs-run1.txt` | on origin `SWEEP LOGS TILE HELD:` ... `19 of 19 rows ok; plants failed as required 10 of 10` | **fails, exit 1**: `SWEEP LOGS TILE FAILED:` ... `17 of 19 rows ok; plants failed as required 10 of 10` (see below) |
| `python -B hypot_check.py` | `gen/hypot-sample-run1.txt` | `HYPOT32 SAMPLE HELD` | byte-identical |
| `python -B hypot_check2.py` | `evidence/hypot-check2-run1.txt` | `HYPOT32 SAMPLE 2 HELD: 1150003 pairs; in the domain of HYPOT32_FINITE 1024729, not faithful 0;` | byte-identical |
| `python -B exp_check.py` | `gen/exp-sample-run1.txt` | `EXP32 SAMPLE HELD` | byte-identical |
| `python -B emit.py sweeps`, `python -B emit2.py sweep`, `python -B exp_exhaust.py` | `gen/sweeps-run2.txt`, `gen/sweep2-run1.txt`, `gen/exp-exhaust-run2.txt` | `SWEEPS HELD (program 9636be961f77f659)`; `SWEEP HELD (program fe58a39d58a9618c)`; `EXP32 EXHAUSTIVE (decimal) HELD:` (move the committed logs aside first, as in step 3.3) | `emit.py sweeps`: last line identical, without the four plant lines that open the record; `emit2.py sweep`: byte-identical; `exp_exhaust.py`: NOT_MEASURED |
| `python -B evidence/fma_plant.py` | `evidence/fma-plant-run1.txt` | `FMA PLANT HELD: contracted build refused for narrow (n_outer, n_inner, n_both), exp32 (fast, dropped: on 2 of its 3258020376 inputs);` ... | last line identical (about 3 minutes); lines 4 and 273 (hashes, file count) differ |

</details>

`chk_logs.py` covers the logs of the earlier programs only; there is no tiling record for the `gen-nm` logs. In an
exported copy it fails on 2 of its 19 rows: the headers of `gen/exp-exhaust-fe58a39d58a9618c.log` and of its plant log
pin the sha256 of origin's `sweep2.exe`, and a rebuilt executable has another. So `evidence/chk-logs-run1.txt` and
`evidence/chk_logs-main-rerun.txt` reproduce on origin only (by this measurement; the owner's ruling names only the
three records of section 5).
`fma_plant.py` compares against the executables in `gen/`; as staged it stops at the first missing file.

## 7. Files the records cite that are not in this subtree

<details>
<summary>The table of cited files that are absent, and why</summary>

| cited | by | why absent |
|---|---|---|
| `orl/gen/sweep.c`, `orl/gen/sweep2.c` | most `orl/evidence/` records and scripts, `orl/gen/` records | include `<math.h>`; regenerated by step 5.1 |
| `orl/evidence/narrow_regress.c`, `orl/evidence/fma/*` | `narrow-regress-run*.txt` line 1, `FMA-LINKED.md` lines 162 to 164 | written by the test writers (step 5); `<math.h>` |
| every `*.exe`, `*.o`, map and disassembly; `wd/cache/*` | many records, with sha256 | build products; their hashes can be checked against nothing staged |
| `ieee64/STATE.md` | `ieee64/IEEE64_Statement.v` line 195 | a working paper of origin, not staged; the cited timing measurements are not available here |
| paths into an earlier review's working folder | `exp32/EXP32_Statement.NOTE-2026-11-14.md` line 32, `orl/evidence/graph_agree.py` line 8, `orl/evidence/chk_logs.py` line 23 | that review's working files, not staged |
| `libcache/IMAGE.txt`, `libcache/checked4.log` | `gate/gate.py` line 51, `gate/gate4.py` | the checked-library cache, not staged |
| the Orlog checkout `orl/O`, `orl.py` | the four emitters | another repository (step 4) |

</details>

Two staged build logs (`orl/gen-nm/build-sweep.log`, `build-sweep2.log`) are held as captured: they contain drive
paths of the compiler installation on origin and name the source by its path there. They are records; nothing in them
is an instruction.

## 8. When done

Delete the exported copy. Then, in the checkout, `python -B mathkernel/check.py` must still end
`MATHKERNEL CHECK PASSED` and `git status --porcelain mathkernel/F32` must print nothing.
