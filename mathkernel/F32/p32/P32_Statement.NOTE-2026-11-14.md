# Note beside `P32_Statement.v`, 2026-11-14

`P32_Statement.v` (sha256 `a1b2af32031ec3d40a95621a3aa397b9ddc9f707475211aca45a7104b75b422d`) is frozen and its
bytes are unchanged. This note corrects how its comment is to be read. It follows the tier review of 2026-11-14
(findings F1, F2, F9).

## What the comment says

Lines 6 to 8: each graph "returns a faithful binary32 rounding of the exact real result", and "The range premises
are binary32's own: inputs are binary32 values below 2^128."

## What the theorems say

`format32` is Flocq's FLT format with least exponent -149 and precision 24. It has no upper exponent bound, so 2^128
and every larger number with a 24-bit significand belong to it. `faithful32 f v` says that v is f rounded down or up
*in that format*. Therefore:

- T32, SQRT32, RSQRT32 and HYPOT32 are true as stated, and proved.
- None of them says that the result is a finite binary32 number.
- For hypot32 it need not be one. With both inputs the largest binary32 number the function returns
  `0x1.6a09e4p+128` (measured: `orl/evidence/hypot-check2-run1.txt`).
- For narrow it need not be one either. At 2^128 - 2^103 and above, narrow returns 2^128 or more, where the IEEE
  conversion to binary32 gives infinity (measured: `orl/evidence/narrow-top-run2.txt`).
- HYPOT32's two range premises are not used by its proof (`Hypot.v` line 117 discards them). SQRT32 has no range
  premise and needs none. RSQRT32's premise `x < 2^128` is used.

## Where the missing statements are

`p32r/P32R_Statement.v` (sha256 `0b98724aa6206777af9554be751a552cc08a01f739b7e2b2c35d99788481421f`), written and
frozen before its proof, and proved in `p32r/Range.v`. Gate record: `P32R GATE4 HELD: 41 of 41  [anchor
2fc8014ccb21d40b]`, on the four axioms of `gate/expected-pa-flocq4.txt`.

| statement | what it says |
|---|---|
| FAITHFUL_FINITE | a faithful rounding of a value of magnitude at most the largest binary32 number is a finite binary32 number |
| NARROW_FINITE | narrow of a binary64 value of magnitude below 2^128 - 2^103 is a finite binary32 number |
| NARROW_SHARP | at 2^128 - 2^103 narrow gives 2^128 |
| SQRT32_FINITE, RSQRT32_FINITE | for every finite binary32 input of their domains the result is a finite binary32 number |
| HYPOT32_FINITE | hypot32 gives a finite binary32 number when the exact result is at most the largest binary32 number |
| HYPOT32_SHARP | that premise cannot be dropped: with both inputs the largest binary32 number the result is not finite binary32 |

## Not covered by either file

The sign of a zero, infinities and NaN (the model has none of them), and what a function returns outside these
premises. The last is measured, not specified.
