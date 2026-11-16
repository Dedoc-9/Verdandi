(* Proof of EXP32_RANGE and EXP32_SHARP (statements in RANGE_Statement.v). Flocq and the standard library only;
   nothing is admitted. The numbers are in Chain.v, which exp32r/gen_range.py generates:
     chain_hi: exp XMAX < (2^24 - 1) * 2^104, from exp (XMAX / 4096) <= P7 + 1/3.6e15 and twelve squarings of an
               upper bound; relative margin 7.3e-6;
     chain_lo: 2^128 < exp (11629080 / 131072), the same with lower bounds; relative margin 2.4e-7.
   Here: exp is increasing, so exp x < FMAX32 for every x <= XMAX; the graph's result is RD32 (exp x) or RU32 (exp x)
   (Exp32.exp32_faithful), 0 and FMAX32 are binary32 numbers, and a rounding of a value between two numbers of the
   format stays between them. *)
From Coq Require Import Reals ZArith Lia Lra.
From Flocq Require Import Core.
From MKF.f32 Require Import F32_Statement.
From MKF.exp32 Require Import Graph EXP32_Statement Exp32.
From MKF.exp32r Require Import RANGE_Statement Chain.
Open Scope R_scope.

#[local] Instance r24 : Prec_gt_0 24 := ltac:(unfold Prec_gt_0; lia).

Lemma fmax_val : FMAX32 = 16777215 * 20282409603651670423947251286016.
Proof.
  unfold FMAX32. change (bpow radix2 24) with 16777216.
  change (bpow radix2 104) with 20282409603651670423947251286016. lra.
Qed.

Lemma fmax_format : format32 FMAX32.
Proof.
  apply generic_format_FLT. apply (FLT_spec radix2 (-149) 24 FMAX32 (Float radix2 16777215 104)).
  - unfold FMAX32, F2R. cbn [Fnum Fexp]. change (bpow radix2 24) with 16777216. lra.
  - cbn [Fnum]. change (Zpower radix2 24) with 16777216%Z. lia.
  - cbn [Fexp]. lia.
Qed.

Lemma exp_xmax : exp XMAX < FMAX32.
Proof. rewrite fmax_val. unfold XMAX. exact chain_hi. Qed.

Lemma exp_below (x : R) : x <= XMAX -> exp x < FMAX32.
Proof.
  intros Hx. apply Rle_lt_trans with (2 := exp_xmax).
  destruct (Req_dec x XMAX) as [E | N]; [rewrite E; apply Rle_refl | left; apply exp_increasing; lra].
Qed.

(* A rounding to binary32 of a value between 0 and FMAX32 stays between them. *)
Lemma round_between (rnd : R -> Z) (f : R) : Valid_rnd rnd -> 0 <= f <= FMAX32 ->
  0 <= round radix2 fexp32 rnd f <= FMAX32.
Proof.
  intros Vr [H0 H1]. split.
  - apply round_ge_generic; [typeclasses eauto | exact Vr | apply generic_format_0 | exact H0].
  - apply round_le_generic; [typeclasses eauto | exact Vr | exact fmax_format | exact H1].
Qed.

Theorem exp32_range : EXP32_RANGE.
Proof.
  unfold EXP32_RANGE. intros x Fx Hx. pose proof (exp_below x Hx) as Hb. split; [exact Hb |].
  assert (Hf : 0 <= exp x <= FMAX32) by (pose proof (exp_pos x); lra).
  destruct (exp32_faithful x Fx Hx) as [E | E]; rewrite E; apply round_between; (typeclasses eauto || exact Hf).
Qed.

Theorem exp32_sharp : EXP32_SHARP.
Proof.
  unfold EXP32_SHARP. change (bpow radix2 128) with 340282366920938463463374607431768211456. exact chain_lo.
Qed.
