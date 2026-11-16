(* Lemma F32's statement, frozen before its proof (2026-11-14). The keystone of contract P32: a binary32 result
   computed from a real y that approximates the exact value f to relative 2^-27 is a faithful rounding of f.

   Model: Flocq's FLT format with emin = -149 and precision 24 (binary32 without an upper exponent bound, so no
   overflow; the sign of a zero is not seen). RN32 is round-to-nearest-even; RD32 and RU32 round down and up.
   "Faithful" means the result is one of the two binary32 values that bracket f (f itself when it is representable).

   The constant 2^-27 is not arbitrary: at 2^-24 the statement is false (f = 1, y = 1 - 2^-24 rounds to the binary32
   number below 1). Author: the assistant. *)
From Coq Require Import Reals.
From Flocq Require Import Core.
Open Scope R_scope.

Notation fexp32 := (FLT_exp (-149) 24).
Notation format32 := (generic_format radix2 fexp32).
Notation RN32 := (round radix2 fexp32 ZnearestE).
Notation RD32 := (round radix2 fexp32 Zfloor).
Notation RU32 := (round radix2 fexp32 Zceil).

Definition faithful32 (f v : R) : Prop := v = RD32 f \/ v = RU32 f.

Definition F32_REL : Prop :=
  forall f y : R, Rabs (y - f) <= bpow radix2 (-24) * Rabs f -> faithful32 f (RN32 y).
