# Note beside `F32_Statement.v`, 2026-11-14

`F32_Statement.v` (sha256 `098937171e5e6971ac673994cefaf10a0c8b678984a2c954934f6afe5580cc73`) is frozen and its
bytes are unchanged. This note records two points from the tier review of 2026-11-14 (finding F9).

## "Faithful" is a statement about the unbounded format

`format32` is Flocq's FLT format with least exponent -149 and precision 24, without an upper exponent bound. When f
is above the largest binary32 number, `faithful32 f v` can hold for a v that is not a binary32 number at all (2^128,
for example). F32_REL is true as stated; read alone it does not say that a result is a finite binary32 number.

The statement that closes this is FAITHFUL_FINITE in `p32r/P32R_Statement.v`: a faithful rounding of a value of
magnitude at most the largest binary32 number is a finite binary32 number. Gate record: `P32R GATE4 HELD: 41 of 41
[anchor 2fc8014ccb21d40b]`.

## The constant 2^-27

Lines 8 and 9 say the constant is not arbitrary because the statement is false at 2^-24. That is true. It does not
follow that 2^-27 is the largest constant that works: the reviewer's hand calculation suggests 2^-25 would also hold.
That has not been checked in Coq. Nothing in the tier depends on the constant being the largest possible.
