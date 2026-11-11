# MATH-KERNEL-ORACLE-SOURCE-PROVENANCE-2026-11-10

**Status: read-only source research. Downloaded upstream fdlibm 5.3 source into scratch and recorded provenance; the
43-constant upstream comparison follows. No single archive is distributed by Netlib — it serves individual files, so
provenance is recorded per file. This selects no normative oracle, builds nothing, freezes nothing, and makes no
repository/charter change.**

## 1. Download provenance

- **Source:** `https://www.netlib.org/fdlibm/` (the `https://www.netlib.org/fdlibm/<file>` URLs 301-redirect; fetched
  with redirect-follow).
- **Retrieved:** 2026-11-10T21:47:52Z (UTC), into `orlog-review/fdlibm-5.3/`.
- **Upstream identity:** Sun Microsystems fdlibm, files marked `@(#) <file> 1.3 95/01/18` (`e_rem_pio2.c` is `1.4`),
  Copyright (C) 1993 by Sun Microsystems — the documented fdlibm 5.3 basis.

| file | bytes | sha256 | `@(#)` version |
|---|---|---|---|
| `k_sin.c` | 2392 | `75d391f3c124806ce14893cd038ae5dd10663e40430ffa174d5fddcb33012167` | 1.3 95/01/18 |
| `k_cos.c` | 3004 | `841086c75288f3f9fef03bae2a9dc24e99c3cdb2035e170c69452013a7b5befc` | 1.3 95/01/18 |
| `e_rem_pio2.c` | 5335 | `3a08dd4a38f9f9fc9478a33ca05cb81a6566f1010ab14412e97cae091bede16b` | 1.4 95/01/18 |
| `k_rem_pio2.c` | 8460 | `5796209ea3fe1af88e22badeaed0f6a6aa923914e097e227c410527cb5815740` | 1.3 95/01/18 |
| `e_atan2.c` | 3736 | `61dbf9edc927468280ccde872ecfb7cb1ea7cbaf6e1b28e7021c968abe5f7c6e` | 1.3 95/01/18 |
| `s_atan.c` | 4207 | `8583c253aed6318dee2a48135e3f3b1328d838a390372a69414ac41eb5ce5ce1` | 1.3 95/01/18 |

(First-capability sin/cos source: `k_sin.c`, `k_cos.c`, `e_rem_pio2.c`, `k_rem_pio2.c`. atan2 research only:
`e_atan2.c`, `s_atan.c`.)

## 2. The FreeBSD `atan2` delta — identified separately, NOT substituted

- **Upstream Sun `e_atan2.c:112`:** `if(k > 60) z=pi_o_2+0.5*pi_lo;` — the large-ratio branch **without** `m &= 1`
  (verified in the downloaded Sun source).
- **Graybox `rules_ref.py:244`:** the same branch **adds `m &= 1`** — the FreeBSD-derived delta, **absent from upstream
  Sun fdlibm 5.3**.
- So the graybox `atan2` derivative = **Sun fdlibm 5.3 + the FreeBSD `m &= 1` delta**. This is kept explicit; the
  upstream Sun source is recorded as-is and the derivative is not silently substituted for it. (atan2 is a *future*
  capability; this is provenance research only.)

## 3. Constant comparison (upstream vs graybox)

Split per the owner's instruction: **19** first-capability constants (S1–S6, C1–C6, INVPIO2, PIO2_1/1T/2/2T/3/3T) vs
**24** atan2-only (research only). Method: extract each constant's value from the downloaded upstream `.c`, convert to
its binary64 bit pattern, and compare to the graybox's bits (`MATH-KERNEL-CONSTANTS-LEDGER-2026-11-10.md`). Any
discrepancy is **reported, not reconciled**.

*(Results appended below once the comparison completes.)*

## Closure

- Upstream Sun fdlibm 5.3 source identity + per-file sha256: **CLOSED — evidenced** (downloaded, versioned, hashed).
- FreeBSD `m &= 1` delta identified vs upstream absence: **CLOSED — evidenced**.
- Exact 43-constant bit comparison (19 + 24): **in progress** (§3).
- Still no normative-oracle selection, build, freeze, or admission.

## 3 (completed): constant comparison results

**Date:** 2026-11-10. **Method (MEASURED):** each constant's decimal literal was extracted verbatim from the downloaded
upstream `.c`, converted with Python `float()` to binary64, and rendered big-endian with `struct.pack('>d', v).hex()`;
the result was compared to the graybox's bit pattern. Run with `PYTHONHASHSEED=0 PYTHONUTF8=1` under `python -B -I`.
Graybox bits are both the ledger's recorded patterns (`MATH-KERNEL-CONSTANTS-LEDGER-2026-11-10.md`) and the same bits
recomputed live from `graybox/rules_ref.py` (`struct.pack('>d', rules_ref.NAME)`); ledger and recomputation agree for
all 43. Upstream `.c` files, `rules_ref.py`, and the charter were not modified. **does_not_show:** that the graybox's
arithmetic (the tick, the kernels' order of operations, the `m &= 1` atan2 delta recorded in §2) matches upstream — only
that the 43 named constant *values* are bit-identical. **Falsifier:** any upstream decimal whose binary64 bits differ
from the graybox pattern.

### A.1 First-capability (19): S1–S6, C1–C6, INVPIO2, PIO2_1/1T/2/2T/3/3T

| name | upstream decimal | upstream bits | graybox bits | MATCH |
|---|---|---|---|---|
| S1 | -1.66666666666666324348e-01 | bfc5555555555549 | bfc5555555555549 | yes |
| S2 | 8.33333333332248946124e-03 | 3f8111111110f8a6 | 3f8111111110f8a6 | yes |
| S3 | -1.98412698298579493134e-04 | bf2a01a019c161d5 | bf2a01a019c161d5 | yes |
| S4 | 2.75573137070700676789e-06 | 3ec71de357b1fe7d | 3ec71de357b1fe7d | yes |
| S5 | -2.50507602534068634195e-08 | be5ae5e68a2b9ceb | be5ae5e68a2b9ceb | yes |
| S6 | 1.58969099521155010221e-10 | 3de5d93a5acfd57c | 3de5d93a5acfd57c | yes |
| C1 | 4.16666666666666019037e-02 | 3fa555555555554c | 3fa555555555554c | yes |
| C2 | -1.38888888888741095749e-03 | bf56c16c16c15177 | bf56c16c16c15177 | yes |
| C3 | 2.48015872894767294178e-05 | 3efa01a019cb1590 | 3efa01a019cb1590 | yes |
| C4 | -2.75573143513906633035e-07 | be927e4f809c52ad | be927e4f809c52ad | yes |
| C5 | 2.08757232129817482790e-09 | 3e21ee9ebdb4b1c4 | 3e21ee9ebdb4b1c4 | yes |
| C6 | -1.13596475577881948265e-11 | bda8fae9be8838d4 | bda8fae9be8838d4 | yes |
| INVPIO2 | 6.36619772367581382433e-01 | 3fe45f306dc9c883 | 3fe45f306dc9c883 | yes |
| PIO2_1 | 1.57079632673412561417e+00 | 3ff921fb54400000 | 3ff921fb54400000 | yes |
| PIO2_1T | 6.07710050650619224932e-11 | 3dd0b4611a626331 | 3dd0b4611a626331 | yes |
| PIO2_2 | 6.07710050630396597660e-11 | 3dd0b4611a600000 | 3dd0b4611a600000 | yes |
| PIO2_2T | 2.02226624879595063154e-21 | 3ba3198a2e037073 | 3ba3198a2e037073 | yes |
| PIO2_3 | 2.02226624871116645580e-21 | 3ba3198a2e000000 | 3ba3198a2e000000 | yes |
| PIO2_3T | 8.47842766036889956997e-32 | 397b839a252049c1 | 397b839a252049c1 | yes |

Source files: S1–S6 ← `k_sin.c`; C1–C6 ← `k_cos.c`; INVPIO2, PIO2_1/1T/2/2T/3/3T ← `e_rem_pio2.c` (hi/lo split mapped
`pio2_N` → PIO2_N high part, `pio2_Nt` → PIO2_NT tail).

### A.2 atan2-only (24, research only): TINY, PI_O_4, PI_O_2, PI, PI_LO, ATANHI[0..3], ATANLO[0..3], AT[0..10]

| name | upstream decimal | upstream bits | graybox bits | MATCH |
|---|---|---|---|---|
| TINY | 1.0e-300 | 01a56e1fc2f8f359 | 01a56e1fc2f8f359 | yes |
| PI_O_4 | 7.8539816339744827900E-01 | 3fe921fb54442d18 | 3fe921fb54442d18 | yes |
| PI_O_2 | 1.5707963267948965580E+00 | 3ff921fb54442d18 | 3ff921fb54442d18 | yes |
| PI | 3.1415926535897931160E+00 | 400921fb54442d18 | 400921fb54442d18 | yes |
| PI_LO | 1.2246467991473531772E-16 | 3ca1a62633145c07 | 3ca1a62633145c07 | yes |
| ATANHI[0] | 4.63647609000806093515e-01 | 3fddac670561bb4f | 3fddac670561bb4f | yes |
| ATANHI[1] | 7.85398163397448278999e-01 | 3fe921fb54442d18 | 3fe921fb54442d18 | yes |
| ATANHI[2] | 9.82793723247329054082e-01 | 3fef730bd281f69b | 3fef730bd281f69b | yes |
| ATANHI[3] | 1.57079632679489655800e+00 | 3ff921fb54442d18 | 3ff921fb54442d18 | yes |
| ATANLO[0] | 2.26987774529616870924e-17 | 3c7a2b7f222f65e2 | 3c7a2b7f222f65e2 | yes |
| ATANLO[1] | 3.06161699786838301793e-17 | 3c81a62633145c07 | 3c81a62633145c07 | yes |
| ATANLO[2] | 1.39033110312309984516e-17 | 3c7007887af0cbbd | 3c7007887af0cbbd | yes |
| ATANLO[3] | 6.12323399573676603587e-17 | 3c91a62633145c07 | 3c91a62633145c07 | yes |
| AT[0] | 3.33333333333329318027e-01 | 3fd555555555550d | 3fd555555555550d | yes |
| AT[1] | -1.99999999998764832476e-01 | bfc999999998ebc4 | bfc999999998ebc4 | yes |
| AT[2] | 1.42857142725034663711e-01 | 3fc24924920083ff | 3fc24924920083ff | yes |
| AT[3] | -1.11111104054623557880e-01 | bfbc71c6fe231671 | bfbc71c6fe231671 | yes |
| AT[4] | 9.09088713343650656196e-02 | 3fb745cdc54c206e | 3fb745cdc54c206e | yes |
| AT[5] | -7.69187620504482999495e-02 | bfb3b0f2af749a6d | bfb3b0f2af749a6d | yes |
| AT[6] | 6.66107313738753120669e-02 | 3fb10d66a0d03d51 | 3fb10d66a0d03d51 | yes |
| AT[7] | -5.83357013379057348645e-02 | bfadde2d52defd9a | bfadde2d52defd9a | yes |
| AT[8] | 4.97687799461593236017e-02 | 3fa97b4b24760deb | 3fa97b4b24760deb | yes |
| AT[9] | -3.65315727442169155270e-02 | bfa2b4442c6a6c2f | bfa2b4442c6a6c2f | yes |
| AT[10] | 1.62858201153657823623e-02 | 3f90ad3ae322da11 | 3f90ad3ae322da11 | yes |

Source files: TINY, PI_O_4, PI_O_2, PI, PI_LO ← `e_atan2.c`; ATANHI[0..3], ATANLO[0..3], AT[0..10] ← `s_atan.c`
(array element order preserved). `k_rem_pio2.c`'s `two_over_pi[]` integer table is not among the 43 and was not compared.

### B. Summary

- **First-capability: 19 / 19 match.**
- **atan2-only: 24 / 24 match.**
- **Total: 43 / 43 match.** The upstream decimal literal of every one of the 43 constants converts to binary64 bits
  byte-identical to the graybox's pattern.
- **Mismatches: none.** No constant's upstream bits differ from the graybox's.

### C. Could not extract / parse

None. All 43 decimal literals were extracted and parsed; every graybox name resolved in `rules_ref.py` (the ledger's
recorded bits equal the live recomputation for all 43).

**Grade: MEASURED** (exact bit comparison, both sources present and run here). This compares only the 43 constant
*values*; it does not bless the atan2 derivative, whose `m &= 1` delta versus upstream Sun is recorded in §2. No
oracle selection, build, freeze, or repository/charter change.
