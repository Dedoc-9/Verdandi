# MATH-KERNEL oracle build + three-way sin/cos differential — 2026-11-10

Scratch-only. Built and run on the owner's Windows host (little-endian x86-64).
No repo, frozen file, charter, or `MATH-KERNEL-*` sheet/manifest was written or
changed. No commit/push/admission. Grade of the differential: **MEASURED**.

## 1. Build inputs downloaded (STEP 1)

Retrieved with `curl -sSL --max-time 40` (follows the netlib 301 redirects) from
`https://www.netlib.org/fdlibm/<file>` into
`<SCRATCH>\fdlibm-5.3\`.

| file | bytes | sha256 | retrieved (UTC) |
|---|---|---|---|
| `fdlibm.h` | 6205 | `64113c472c2676499288bc35a821b0867916552930bc52c7445d2c50dddf0e71` | Tue Nov 10 22:11:04 UTC 2026 |
| `s_sin.c`  | 1967 | `4d5edb75368e4f8e0ac18682d3ae4b6944ba06801637cf0df6f378d6211f4c81` | Tue Nov 10 22:11:05 UTC 2026 |
| `s_cos.c`  | 1976 | `bdcbea3c83b2d4aa521b9a5341f3e58b8cb9c8d326fcc4abb715f3704cf17799` | Tue Nov 10 22:11:05 UTC 2026 |

Provenance (genuine Sun fdlibm markers present):
- `s_sin.c` line 2: `/* @(#)s_sin.c 1.3 95/01/18 */`; line 5: `Copyright (C) 1993 by Sun Microsystems, Inc.`
- `s_cos.c` line 2: `/* @(#)s_cos.c 1.3 95/01/18 */`; line 5: `Copyright (C) 1993 by Sun Microsystems, Inc.`
- `fdlibm.h` line 2: `/* @(#)fdlibm.h 1.5 04/04/22 */`; line 5: `Copyright (C) 2004 by Sun Microsystems, Inc.`
  NOTE: the fdlibm *header* carries the distribution's 2004 revision date (1.5
  04/04/22), not the 1993/95-01-18 of the `.c` kernel files. This is the normal
  state of the netlib fdlibm 5.3 drop — the C sources are the 1993 kernels; the
  header was last revised in 2004. It is still genuine Sun fdlibm (Sun
  Microsystems copyright) and is a build input, not a frozen file.

### fdlibm.h configuration

**No edit to `fdlibm.h`.** Endianness is selected by the `__LITTLE_ENDIAN`
macro, which `fdlibm.h` auto-defines only for `i386/i486/intel/x86/i86pc/__alpha/__osf__`
(lines 16-20). clang on `x86_64-pc-windows-msvc` defines none of those, so the
macro was supplied on the compiler command line, as preferred:

    -D__LITTLE_ENDIAN

Verified unchanged after the build (`defined(i386)` guard still present, 1 match).

## 2. Controlled C oracle build (STEP 2)

- Compiler: `clang version 22.1.8` (LLVM `ca7933e47d3a3451d81e72ac174dcb5aa28b59d1`)
- Target triple: `x86_64-pc-windows-msvc`
- Sources (6 frozen + 1 scratch driver), compiled together:
  `s_sin.c s_cos.c k_sin.c k_cos.c e_rem_pio2.c k_rem_pio2.c test_oracle.c`
- Exact flags:

      clang -std=c99 -O2 -ffp-contract=off -fno-fast-math -D__LITTLE_ENDIAN \
        s_sin.c s_cos.c k_sin.c k_cos.c e_rem_pio2.c k_rem_pio2.c test_oracle.c \
        -o build/test_oracle.exe

- Output: `<SCRATCH>\fdlibm-5.3\build\test_oracle.exe`
- Executable sha256: `d1de73d0db367d3ec22a8920cf6fec8dea8f42d964dcbb447d171ce4df3ac960`
- Warnings only (K&R-style non-prototype definitions in the 1993 sources, and
  CRT `scanf`/`sscanf` deprecation notices). clang exit 0. No errors.
- FP environment: default round-to-nearest-even; `-ffp-contract=off` forbids
  FMA contraction; `-fno-fast-math` (and the absence of `/fp:fast`) keeps
  IEEE semantics. **FTZ/DAZ are OFF** — proven empirically, not merely asserted:
  the smallest-subnormal input `0000000000000001` and the largest-subnormal
  `000fffffffffffff` each return themselves for `sin` (fdlibm's `|x|<2^-27`
  branch returns `x`), and the subnormal bits survive in the output unchanged;
  a flushing environment would have returned `+0`.

The driver `test_oracle.c` (sha256
`f22c1e971245a50b7b5d7ca94606b087ae899b3d94fb39f0944658579d61ac89`) reads
whitespace-separated 16-hex big-endian input doubles on stdin and prints, per
input, `<inputhex> <sin_outhex> <cos_outhex>` using the fdlibm top-level
`sin()`/`cos()` (bit patterns via `memcpy`, big-endian).

Frozen build sources used (read-only, unchanged — recorded for traceability):

| file | sha256 |
|---|---|
| `k_sin.c` | `75d391f3c124806ce14893cd038ae5dd10663e40430ffa174d5fddcb33012167` |
| `k_cos.c` | `841086c75288f3f9fef03bae2a9dc24e99c3cdb2035e170c69452013a7b5befc` |
| `e_rem_pio2.c` | `3a08dd4a38f9f9fc9478a33ca05cb81a6566f1010ab14412e97cae091bede16b` |
| `k_rem_pio2.c` | `5796209ea3fe1af88e22badeaed0f6a6aa923914e097e227c410527cb5815740` |

## 3. Three-way differential (STEP 3) — MEASURED

### Corpus

Inputs are the KERNEL-input rows of
`MATH-KERNEL-S5-VECTORS-2026-11-10.csv`, groups `direct sin/cos`,
`reduction stress`, and `exceptional values` (op `sin` or `cos`). The groups
`movement-law normalization`, `pitch clamp`, and `out-of-domain finite` are
EXCLUDED (law-level or refused — not kernel calls). Distinct input doubles were
collected from `input_bits`: **26 distinct inputs**.

### Realizations compared

- **C oracle:** `build/test_oracle.exe` (fdlibm top-level `sin()`/`cos()`).
- **Python:** `graybox/rules_ref.py` → `r.xsin(x)`, `r.xcos(x)`, run with
  `PYTHONHASHSEED=0 PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1`, `python -B`.
- **JS (node v24.19.0):** `graybox/web/sim.js`; `module.exports = make(1)` so
  `M = EXACT = {sin: xsin, cos: xcos}` — `G.math.sin(x)` / `G.math.cos(x)`.

Comparison is bit-exact; NaN-vs-NaN is treated as equal (payload not
spec-fixed), with actual bits recorded.

### Table (input | C sin,cos | py sin,cos | node sin,cos | agree)

```
input_bits       | C_sin            C_cos            | py_sin           py_cos           | node_sin         node_cos         | agree
0000000000000000 | 0000000000000000 3ff0000000000000 | 0000000000000000 3ff0000000000000 | 0000000000000000 3ff0000000000000 | yes
401921fb54442d17 | bcd469898cc51702 3ff0000000000000 | bcd469898cc51702 3ff0000000000000 | bcd469898cc51702 3ff0000000000000 | yes
401921fb54442d18 | bcb1a62633145c07 3ff0000000000000 | bcb1a62633145c07 3ff0000000000000 | bcb1a62633145c07 3ff0000000000000 | yes
3ff7333333333333 | 3fefc44e08da43dc 3fbed944fd82a112 | 3fefc44e08da43dc 3fbed944fd82a112 | 3fefc44e08da43dc 3fbed944fd82a112 | yes
bff7333333333333 | bfefc44e08da43dc 3fbed944fd82a112 | bfefc44e08da43dc 3fbed944fd82a112 | bfefc44e08da43dc 3fbed944fd82a112 | yes
3fe0000000000000 | 3fdeaee8744b05f0 3fec1528065b7d50 | 3fdeaee8744b05f0 3fec1528065b7d50 | 3fdeaee8744b05f0 3fec1528065b7d50 | yes
3ff0000000000000 | 3feaed548f090cee 3fe14a280fb5068c | 3feaed548f090cee 3fe14a280fb5068c | 3feaed548f090cee 3fe14a280fb5068c | yes
3fe921fb54442d18 | 3fe6a09e667f3bcc 3fe6a09e667f3bcd | 3fe6a09e667f3bcc 3fe6a09e667f3bcd | 3fe6a09e667f3bcc 3fe6a09e667f3bcd | yes
3ff921fb54442d18 | 3ff0000000000000 3c91a62633145c07 | 3ff0000000000000 3c91a62633145c07 | 3ff0000000000000 3c91a62633145c07 | yes
3ff921fb54442d17 | 3ff0000000000000 3cb469898cc51702 | 3ff0000000000000 3cb469898cc51702 | 3ff0000000000000 3cb469898cc51702 | yes
3ff921fb54442d19 | 3ff0000000000000 bca72cece675d1fd | 3ff0000000000000 bca72cece675d1fd | 3ff0000000000000 bca72cece675d1fd | yes
400921fb54442d18 | 3ca1a62633145c07 bff0000000000000 | 3ca1a62633145c07 bff0000000000000 | 3ca1a62633145c07 bff0000000000000 | yes
400921fb54442d17 | 3cc469898cc51702 bff0000000000000 | 3cc469898cc51702 bff0000000000000 | 3cc469898cc51702 bff0000000000000 | yes
400921fb54442d19 | bcb72cece675d1fd bff0000000000000 | bcb72cece675d1fd bff0000000000000 | bcb72cece675d1fd bff0000000000000 | yes
4012d97c7f3321d2 | bff0000000000000 bcaa79394c9e8a0a | bff0000000000000 bcaa79394c9e8a0a | bff0000000000000 bcaa79394c9e8a0a | yes
4012d97c7f3321d1 | bff0000000000000 bcd34f272993d141 | bff0000000000000 bcd34f272993d141 | bff0000000000000 bcd34f272993d141 | yes
4012d97c7f3321d3 | bff0000000000000 3cc961b1acd85d7d | bff0000000000000 3cc961b1acd85d7d | bff0000000000000 3cc961b1acd85d7d | yes
8000000000000000 | 8000000000000000 3ff0000000000000 | 8000000000000000 3ff0000000000000 | 8000000000000000 3ff0000000000000 | yes
0000000000000001 | 0000000000000001 3ff0000000000000 | 0000000000000001 3ff0000000000000 | 0000000000000001 3ff0000000000000 | yes
000fffffffffffff | 000fffffffffffff 3ff0000000000000 | 000fffffffffffff 3ff0000000000000 | 000fffffffffffff 3ff0000000000000 | yes
7ff0000000000000 | fff8000000000000 fff8000000000000 | fff8000000000000 fff8000000000000 | fff8000000000000 fff8000000000000 | yes
fff0000000000000 | fff8000000000000 fff8000000000000 | fff8000000000000 fff8000000000000 | fff8000000000000 fff8000000000000 | yes
7ff8000000000000 | 7ff8000000000000 7ff8000000000000 | 7ff8000000000000 7ff8000000000000 | 7ff8000000000000 7ff8000000000000 | yes
fff8000000000000 | fff8000000000000 fff8000000000000 | fff8000000000000 fff8000000000000 | fff8000000000000 fff8000000000000 | yes
7ff0000000000001 | 7ff8000000000001 7ff8000000000001 | 7ff8000000000001 7ff8000000000001 | 7ff8000000000001 7ff8000000000001 | yes
7ffabcdef1234567 | 7ffabcdef1234567 7ffabcdef1234567 | 7ffabcdef1234567 7ffabcdef1234567 | 7ffabcdef1234567 7ffabcdef1234567 | yes
```

### Summary

- Distinct inputs compared: **26**.
- Do all three agree (NaN-vs-NaN excepted): **YES**.
- Mismatches: **none**.

Stronger-than-required observation: the NaN exception was never actually
invoked. Every finite in-domain input (interior points, boundary ulps, signed
zero, both subnormals) agrees bit-identically across C, Python and JS; and every
NaN-producing input agrees bit-identically too — `+inf`/`-inf` both give
`fff8000000000000` via `x-x`, the quiet NaNs pass through unchanged, and the
signaling NaN `7ff0000000000001` is quieted to `7ff8000000000001` (quiet bit
set, payload low bit preserved) identically in all three. On this one host the
three realizations are therefore bit-for-bit identical on the whole kernel
corpus, exceptional values included. This is a single-host agreement result
(three realizations, one x86-64 FP environment), not a cross-platform claim.

### Grade

**MEASURED.** Bit patterns were produced by running the three built/interpreted
realizations and compared exactly.
- *does_not_show:* it does not show correct rounding against an arbitrary-precision
  reference (all three could share a rounding choice); it does not show agreement
  on any other host, OS, CPU, or node/clang version; it does not cover inputs
  outside the 26 frozen kernel-corpus doubles; and the shared `x-x` NaN results
  come from the host FPU, so NaN bit-identity is a property of this FP
  environment, not of the three algorithms.
- *falsifier:* any single input in the corpus for which the three output-bit
  sets are not all equal (NaN-vs-NaN excepted) would turn this red.

## 4. Files written (all scratch, outside any repo)

- `fdlibm-5.3/fdlibm.h`, `fdlibm-5.3/s_sin.c`, `fdlibm-5.3/s_cos.c` — downloaded build inputs
- `fdlibm-5.3/test_oracle.c` — driver
- `fdlibm-5.3/build/test_oracle.exe` — the oracle
- `node_sin_cos.js` — JS driver
- `math_kernel_diff.py` — the comparison harness (re-run with
  `PYTHONHASHSEED=0 PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 python -B math_kernel_diff.py`)
- this document
