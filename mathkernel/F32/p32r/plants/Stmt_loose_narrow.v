(* The binary32 range statements of contract P32, frozen before their proofs (2026-11-14). Author: the assistant.

   Why they exist. The tier review of 2026-11-14 (findings F1, F2, F9) showed that P32's theorems, though true, do not
   say what their comment says. The model is Flocq's FLT format without an upper exponent bound, so "format32" holds
   of 2^128, 2^200 and so on, and "faithful32 f v" can be met by a v that is no binary32 number whenever f is above
   the largest one. hypot32 of two binary32 numbers can be such a value (both inputs the largest binary32 number give
   about 1.414 * 2^128), and narrow of a binary64 value at or above 2^128 - 2^103 is 2^128 or more, where the IEEE
   conversion gives infinity. P32_Statement.v is frozen and stays as it is; these statements say what was missing.

   FMAX32 = (2^24 - 1) * 2^104 is the largest finite binary32 number. OVF32 = 2^128 - 2^103 is the midpoint between
   it and 2^128: the least magnitude that the IEEE conversion to binary32 (round to nearest even) takes to infinity.
   finite32 v: v is a number of the binary32 format and its magnitude is at most FMAX32: a finite binary32 number.

   FAITHFUL_FINITE  a faithful rounding of a value inside binary32's finite range is a finite binary32 number. With it
                    every faithfulness theorem of the tier gives a finite binary32 result wherever the exact result is
                    in range.
   NARROW_FINITE    narrow of a binary64 value of magnitude below OVF32 is a finite binary32 number.
   NARROW_SHARP     the limit cannot be raised: at OVF32 itself narrow gives 2^128.
   SQRT32_FINITE, RSQRT32_FINITE   for every finite binary32 input of their domains the result is a finite binary32
                    number: no further premise is needed.
   HYPOT32_FINITE   hypot32 gives a finite binary32 number when the exact result is at most FMAX32. That premise is
                    the caller's obligation; it implies that both inputs are finite binary32 numbers.
   HYPOT32_SHARP    the premise cannot be dropped: with both inputs FMAX32 the result is not a finite binary32 number.

   Not said here: what the functions return outside these premises (measured in the review: values at or above 2^128,
   or NaN, never infinity), and anything about the sign of a zero, infinities or NaN, which the model does not have. *)
From Coq Require Import Reals.
From Flocq Require Import Core.
From MKF.f32 Require Import F32_Statement.
From MKF.p32 Require Import Graphs P32_Statement.
Open Scope R_scope.

Definition FMAX32 : R := (bpow radix2 24 - 1) * bpow radix2 104.
Definition OVF32 : R := bpow radix2 128 - bpow radix2 103.
Definition finite32 (v : R) : Prop := format32 v /\ Rabs v <= FMAX32.

Definition FAITHFUL_FINITE : Prop :=
  forall f v : R, Rabs f <= FMAX32 -> faithful32 f v -> finite32 v.

Definition NARROW_FINITE : Prop :=
  forall v : R, format64 v -> Rabs v <= OVF32 -> finite32 (narrow v).

Definition NARROW_SHARP : Prop := narrow OVF32 = bpow radix2 128.

Definition SQRT32_FINITE : Prop :=
  forall x : R, format32 x -> 0 <= x -> x <= FMAX32 -> finite32 (g_sqrt32 x).

Definition RSQRT32_FINITE : Prop :=
  forall x : R, format32 x -> 0 < x -> x <= FMAX32 -> finite32 (g_rsqrt32 x).

Definition HYPOT32_FINITE : Prop :=
  forall x y : R, format32 x -> format32 y -> sqrt (x * x + y * y) <= FMAX32 -> finite32 (g_hypot32 x y).

Definition HYPOT32_SHARP : Prop := ~ finite32 (g_hypot32 FMAX32 FMAX32).

Definition P32R : Prop :=
  FAITHFUL_FINITE /\ NARROW_FINITE /\ NARROW_SHARP /\ SQRT32_FINITE /\ RSQRT32_FINITE /\ HYPOT32_FINITE /\ HYPOT32_SHARP.
