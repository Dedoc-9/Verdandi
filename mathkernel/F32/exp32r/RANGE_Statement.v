(* The EXP32 range statement, frozen before its proof (2026-11-14). Author: the assistant.

   FMAX32 = (2^24 - 1) * 2^104 is the largest finite binary32 number. XMAX = 11629079 / 131072 (EXP32_Statement.v) is
   the upper input limit of exp32, and 11629080 / 131072 is the binary32 number just above XMAX.

   The model is Flocq's FLT format without an upper exponent bound (binary32 as FLT(-149, 24), binary64 as
   FLT(-1074, 53)), so EXP32 itself cannot say that the result is a finite binary32 number: in the model nothing
   overflows. This theorem is what shows it.

   EXP32_RANGE: for every binary32 x at most XMAX, exp x is below FMAX32, and the graph's result lies between 0 and
   FMAX32; with EXP32 (the result is a binary32 number of the unbounded format) that makes it a finite binary32 number.
   EXP32_SHARP: the limit cannot be raised: at the next binary32 number above XMAX, exp is already above 2^128, the
   first power of two past FMAX32, so a faithful result there is not a finite binary32 number. *)
From Coq Require Import Reals.
From Flocq Require Import Core.
From MKF.f32 Require Import F32_Statement.
From MKF.exp32 Require Import Graph EXP32_Statement.
Open Scope R_scope.

Definition FMAX32 : R := (bpow radix2 24 - 1) * bpow radix2 104.

Definition EXP32_RANGE : Prop :=
  forall x : R, format32 x -> x <= XMAX -> exp x < FMAX32 /\ 0 <= g_exp32 x <= FMAX32.

Definition EXP32_SHARP : Prop := bpow radix2 128 < exp (11629080 / 131072).
