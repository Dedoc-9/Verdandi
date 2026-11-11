# MATH-KERNEL-CONSTANTS-LEDGER-2026-11-10

**Status: read-only local source tracing. Classification is CLOSED — evidenced (traced in `graybox/rules_ref.py` and
verified locally). Upstream provenance is OPEN — research for every constant: NO bit pattern was compared to Netlib
fdlibm 5.3; no upstream match is claimed. No download, oracle build, freeze, or repo/charter write.**

## Verification (this host)

Subagent traced `rules_ref.py`; I verified its key claims directly: `constants_digest() = b258b096`; the group count is
exactly **43** (6 sine + 6 cosine + 7 reduction + 4 ATANHI + 4 ATANLO + 11 AT + 5 atan2 = 43); spot-checked bits match
(`S1 bfc5555555555549`, `C1 3fa555555555554c`, `INVPIO2 3fe45f306dc9c883`, `PIO2_1 3ff921fb54400000`,
`TINY 01a56e1fc2f8f359`, `PI_O_2 3ff921fb54442d18`, `PI_LO 3ca1a62633145c07`); and `xsin`/`xcos` (L143–171) **each**
call both `k_sin` and `k_cos` (quadrant folding), so S1–S6 and C1–C6 are all required for the first (sin+cos) freeze.

## Call graph (actual use, traced — not declaration section)

`k_sin`(L58) uses S1–S6; `k_cos`(L70) uses C1–C6; `rem_pio2`(L90) uses INVPIO2, PIO2_1/1T/2/2T/3/3T. `xsin`(L140) and
`xcos`(L157) each call `rem_pio2`, `k_sin`, and `k_cos`. `xatan`(L181) uses ATANHI[0-3], ATANLO[0-3], AT[0-10];
`xatan2`(L221) uses TINY, PI_O_4, PI_O_2, PI, PI_LO and **calls `xatan`** — so all atan/atan2 constants are reached only
via `xatan2`, never on a sin/cos path.

## Ledger (name · big-endian hex · line · class · REQUIRED-for-first-freeze; provenance = UPSTREAM_UNRESOLVED for all)

**Sine kernel — SIN_ONLY, required:** S1 `bfc5555555555549` L52 · S2 `3f8111111110f8a6` · S3 `bf2a01a019c161d5` ·
S4 `3ec71de357b1fe7d` L53 · S5 `be5ae5e68a2b9ceb` · S6 `3de5d93a5acfd57c`.
**Cosine kernel — COS_ONLY, required:** C1 `3fa555555555554c` L54 · C2 `bf56c16c16c15177` · C3 `3efa01a019cb1590` ·
C4 `be927e4f809c52ad` L55 · C5 `3e21ee9ebdb4b1c4` · C6 `bda8fae9be8838d4`.
**Argument reduction — SHARED_REDUCTION, required:** INVPIO2 `3fe45f306dc9c883` L84 · PIO2_1 `3ff921fb54400000` L85 ·
PIO2_1T `3dd0b4611a626331` · PIO2_2 `3dd0b4611a600000` L86 · PIO2_2T `3ba3198a2e037073` · PIO2_3 `3ba3198a2e000000` L87
· PIO2_3T `397b839a252049c1`.
**Arctangent kernel/tables — ATAN2_ONLY, NOT required (future capability):** ATANHI[0] `3fddac670561bb4f` L174 ·
ATANHI[1] `3fe921fb54442d18` · ATANHI[2] `3fef730bd281f69b` · ATANHI[3] `3ff921fb54442d18` · ATANLO[0] `3c7a2b7f222f65e2`
L175 · ATANLO[1] `3c81a62633145c07` · ATANLO[2] `3c7007887af0cbbd` · ATANLO[3] `3c91a62633145c07` ·
AT[0] `3fd555555555550d` L176 · AT[1] `bfc999999998ebc4` · AT[2] `3fc24924920083ff` · AT[3] `bfbc71c6fe231671` ·
AT[4] `3fb745cdc54c206e` L177 · AT[5] `bfb3b0f2af749a6d` · AT[6] `3fb10d66a0d03d51` · AT[7] `bfadde2d52defd9a` ·
AT[8] `3fa97b4b24760deb` L178 · AT[9] `bfa2b4442c6a6c2f` · AT[10] `3f90ad3ae322da11`.
**atan2 — ATAN2_ONLY, NOT required:** TINY `01a56e1fc2f8f359` L217 · PI_O_4 `3fe921fb54442d18` L218 ·
PI_O_2 `3ff921fb54442d18` · PI `400921fb54442d18` · PI_LO `3ca1a62633145c07`.

## Sets

- **MINIMUM first-capability (sin/cos) set = 19:** S1–S6, C1–C6, INVPIO2, PIO2_1, PIO2_1T, PIO2_2, PIO2_2T, PIO2_3,
  PIO2_3T.
- **ATAN2_ONLY (held out of the first freeze) = 24:** ATANHI[0-3], ATANLO[0-3], AT[0-10], TINY, PI_O_4, PI_O_2, PI,
  PI_LO. 19 + 24 = 43.
- **SHARED_CROSS_CAPABILITY: empty** (no constant is used by both the sin/cos path and `xatan2`). **UNUSED_OR_UNRESOLVED:
  none.**

## Notes / closure

- **Classification: CLOSED — evidenced** (local tracing + verification). **Upstream provenance: OPEN — research** for all
  43 (no Netlib comparison performed). Bit coincidences (ATANHI[1]=PI_O_4, ATANHI[3]=PI_O_2, the `…a62633145c07` tails)
  are separate symbols with separate use sites and imply nothing about provenance.
- **Domain-width (D3):** for a *strictly* narrow |x| ≤ π/4 the kernel returns without `rem_pio2`, so the 7 reduction
  constants would not execute. But the first capability's ruled domain is yaw ∈ [0, 2π) and pitch ∈ [−1.45, +1.45],
  **both exceeding π/4 ≈ 0.785** — so `rem_pio2` *is* reached and the 7 reduction constants are genuinely required. The
  first set stays 19.
- Not in the 43 (correctly excluded): `PIO2D`, `TWOPI`, `EDGES`, `SPECIAL` — the test-argument generator's, not the
  algorithms'.
