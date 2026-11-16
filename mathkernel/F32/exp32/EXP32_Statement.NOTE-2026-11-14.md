# Note beside `EXP32_Statement.v`, 2026-11-14

`EXP32_Statement.v` (sha256 `19d1fb59447305a585e55d03317e414e0ad5c89c0fed1a603cb649702d00aae5`) is frozen and its
bytes are unchanged. This note records what has changed around it since. It follows the tier review of 2026-11-14
(findings F8, F11).

## What the comment says

Lines 7 to 9: XMAX "is the largest binary32 x whose exp is below binary32's largest number; that it is so is not part
of this statement (the model has no overflow) and is left to the exhaustive sweep."

## What is now proved

`exp32r/RANGE_Statement.v` (sha256 `281b28c227a8940c130067261c48e556bc2aa2ec8cd96ad21a421a663aaf2187`), written and
frozen before its proof. Gate record: `EXP32R GATE4 HELD: 54 of 54  [anchor c7052646819b4e69]`, on the four axioms
of `gate/expected-pa-flocq4.txt`.

- EXP32_RANGE: for every binary32 x at most XMAX, exp x is below the largest binary32 number, and the graph's result
  lies between 0 and that number. With EXP32 the result is then a finite binary32 number.
- EXP32_SHARP: at the next binary32 number above XMAX, exp x is already above 2^128.

So the sentence quoted above no longer rests on the sweep alone.

## What EXP32's proof uses of XMAX

Only that x is at most 160 (`Exp32.v` line 298). The same proof holds for any limit up to 160. In the model that is
harmless, because nothing overflows there; on a machine the results above XMAX are not binary32 numbers.

## Above XMAX (measured, not specified)

The function does not return infinity. At the next binary32 number it returns `0x1.000004p+128`; at 100 it returns
`0x1.3494aap+144`; at 709 and above it returns NaN (`tier1-review/repro/repro-run1.txt` in the review's records).
Keeping x at or below XMAX is the caller's obligation.

## The exhaustive evidence

Two exhaustive checks of all 3,258,020,376 inputs exist, with different references:

- `orl/gen/sweep2-run1.txt`: against the C runtime's exp, taken to be within 2^-40 relative. That is an assumption
  about the runtime, not something the sweep measures. Its sign test accepts a result of -0.
- `orl/gen/exp-exhaust-run1.txt` (and a later rerun, `exp-exhaust-run2.txt`, when present): against Python decimal's
  exp at 40 digits, with no use of the C runtime's exp. It requires the sign bit clear.
