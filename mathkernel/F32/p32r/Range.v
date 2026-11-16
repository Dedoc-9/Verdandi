(* Proof of P32R, the seven binary32 range statements of contract P32 (statements in P32R_Statement.v). Flocq and the
   standard library only; nothing is admitted. Author: the assistant.
     FMAX32 = (2^24 - 1) * 2^104 is a binary32 number (fmax_format); a rounding to binary32 of a value between -FMAX32
     and FMAX32 stays between them (round_finite), which is FAITHFUL_FINITE.
     FMAX32's successor in the format is 2^128 (succ_fmax) and OVF32 is their midpoint (midpoint), so the nearest
     rounding of a value below OVF32 is at most FMAX32 (rn32_below, Flocq's round_N_le_midp); with T32 (narrow is RN32
     on binary64) and the symmetry of nearest-even that is NARROW_FINITE.
     OVF32 = (2^25 - 1) * 2^103 is a binary64 number; in binary32 its exponent is 104 and its scaled mantissa is
     2^24 - 1/2, a tie whose floor 2^24 - 1 is odd, so nearest-even gives 2^24: NARROW_SHARP.
     sqrt x <= 2^64 for x <= FMAX32, and / sqrt x <= 2^75 for a positive binary32 x (at least 2^-149); both are at most
     FMAX32, so SQRT32 and RSQRT32 with FAITHFUL_FINITE give SQRT32_FINITE and RSQRT32_FINITE.
     Rabs x <= sqrt (x*x + y*y) gives HYPOT32's premises from HYPOT32_FINITE's: HYPOT32_FINITE.
     With both inputs FMAX32 every step of the graph is at least a power of two of binary64 (2^255, 2^256, 2^128), and
     rounding is monotone and leaves those unchanged, so the result is at least 2^128 > FMAX32: HYPOT32_SHARP. *)
From Coq Require Import Reals ZArith Lia Lra.
From Flocq Require Import Core.
From MKF.f32 Require Import F32_Statement.
From MKF.p32 Require Import Graphs P32_Statement T32 Funcs Hypot.
From MKF.p32r Require Import P32R_Statement.
Open Scope R_scope.

#[local] Instance s24 : Prec_gt_0 24 := ltac:(unfold Prec_gt_0; lia).
#[local] Instance s53 : Prec_gt_0 53 := ltac:(unfold Prec_gt_0; lia).

(* Every power of two with a literal exponent, in the goal and the hypotheses, becomes its numeral. *)
Ltac bnum :=
  repeat match goal with
  | |- context [bpow radix2 (Zpos ?p)] =>
      let z := eval vm_compute in (Zpower_pos 2 p) in change (bpow radix2 (Zpos p)) with (IZR z)
  | |- context [bpow radix2 (Zneg ?p)] =>
      let z := eval vm_compute in (Zpower_pos 2 p) in change (bpow radix2 (Zneg p)) with (/ IZR z)
  | H : context [bpow radix2 (Zpos ?p)] |- _ =>
      let z := eval vm_compute in (Zpower_pos 2 p) in change (bpow radix2 (Zpos p)) with (IZR z) in H
  | H : context [bpow radix2 (Zneg ?p)] |- _ =>
      let z := eval vm_compute in (Zpower_pos 2 p) in change (bpow radix2 (Zneg p)) with (/ IZR z) in H
  end.

(* FMAX32 *)

Lemma fmax_format : format32 FMAX32.
Proof.
  apply generic_format_FLT. apply (FLT_spec radix2 (-149) 24 FMAX32 (Float radix2 16777215 104)).
  - unfold FMAX32, F2R. cbn [Fnum Fexp]. bnum. lra.
  - cbn [Fnum]. change (Zpower radix2 24) with 16777216%Z. lia.
  - cbn [Fexp]. lia.
Qed.

Lemma fmax_lt : FMAX32 < bpow radix2 128.
Proof. unfold FMAX32. bnum. lra. Qed.

Lemma fmax_ge : bpow radix2 127 <= FMAX32.
Proof. unfold FMAX32. bnum. lra. Qed.

(* A rounding to binary32 of a value between -FMAX32 and FMAX32 is a finite binary32 number. *)
Lemma round_finite (rnd : R -> Z) (f : R) : Valid_rnd rnd -> Rabs f <= FMAX32 ->
  finite32 (round radix2 fexp32 rnd f).
Proof.
  intros Vr Hf. apply Rabs_le_inv in Hf. destruct Hf as [H0 H1]. split.
  - apply generic_format_round; [typeclasses eauto | exact Vr].
  - apply Rabs_le. split.
    + apply round_ge_generic;
        [typeclasses eauto | exact Vr | apply generic_format_opp; exact fmax_format | exact H0].
    + apply round_le_generic; [typeclasses eauto | exact Vr | exact fmax_format | exact H1].
Qed.

Theorem faithful_finite : FAITHFUL_FINITE.
Proof.
  unfold FAITHFUL_FINITE. intros f v Hf [E | E]; rewrite E; apply round_finite; (typeclasses eauto || exact Hf).
Qed.

(* narrow below the overflow threshold *)

Lemma mag_fmax : mag radix2 FMAX32 = 128%Z :> Z.
Proof. apply mag_unique_pos. split; [exact fmax_ge | exact fmax_lt]. Qed.

Lemma succ_fmax : succ radix2 fexp32 FMAX32 = bpow radix2 128.
Proof.
  assert (P : 0 < FMAX32) by (pose proof fmax_ge as G; pose proof (bpow_gt_0 radix2 127); lra).
  rewrite succ_eq_pos by lra. rewrite ulp_neq_0 by lra.
  unfold cexp. rewrite mag_fmax. change (fexp32 128) with 104%Z.
  clear P. unfold FMAX32. bnum. lra.
Qed.

Lemma midpoint : (FMAX32 + succ radix2 fexp32 FMAX32) / 2 = OVF32.
Proof. rewrite succ_fmax. unfold FMAX32, OVF32. bnum. lra. Qed.

Lemma rn32_below (w : R) : w < OVF32 -> RN32 w <= FMAX32.
Proof.
  intros Hw.
  apply round_N_le_midp; [typeclasses eauto | exact fmax_format | rewrite midpoint; exact Hw].
Qed.

Theorem narrow_finite : NARROW_FINITE.
Proof.
  unfold NARROW_FINITE. intros v Fv Hv. rewrite (T32_proof v Fv). split.
  - apply generic_format_round; typeclasses eauto.
  - rewrite <- (round_NE_abs radix2 fexp32 v). apply rn32_below. exact Hv.
Qed.

(* narrow at the overflow threshold *)

Lemma ovf_format64 : format64 OVF32.
Proof.
  apply generic_format_FLT. apply (FLT_spec radix2 (-1074) 53 OVF32 (Float radix2 33554431 103)).
  - unfold OVF32, F2R. cbn [Fnum Fexp]. bnum. lra.
  - cbn [Fnum]. change (Zpower radix2 53) with 9007199254740992%Z. lia.
  - cbn [Fexp]. lia.
Qed.

Lemma mag_ovf : mag radix2 OVF32 = 128%Z :> Z.
Proof.
  apply mag_unique_pos. change (128 - 1)%Z with 127%Z. unfold OVF32. bnum. split; lra.
Qed.

(* The tie: 2^24 - 1/2 lies between the odd 2^24 - 1 and the even 2^24. *)
Lemma zne_tie : ZnearestE (33554431 / 2) = 16777216%Z.
Proof.
  assert (Fl : Zfloor (33554431 / 2) = 16777215%Z)
    by (apply Zfloor_imp; change (16777215 + 1)%Z with 16777216%Z; lra).
  assert (Cl : Zceil (33554431 / 2) = 16777216%Z)
    by (apply Zceil_imp; change (16777216 - 1)%Z with 16777215%Z; lra).
  unfold Znearest. rewrite Fl, Cl.
  rewrite Rcompare_Eq by lra. reflexivity.
Qed.

Theorem narrow_sharp : NARROW_SHARP.
Proof.
  unfold NARROW_SHARP. rewrite (T32_proof OVF32 ovf_format64).
  rewrite (round_at fexp32 ZnearestE OVF32 104).
  - cbn [Z.opp].
    replace (OVF32 * bpow radix2 (-104)) with (33554431 / 2) by (unfold OVF32; bnum; lra).
    rewrite zne_tie. bnum. lra.
  - unfold cexp. rewrite mag_ovf. reflexivity.
Qed.

(* sqrt32 and rsqrt32 *)

Theorem sqrt32_finite : SQRT32_FINITE.
Proof.
  unfold SQRT32_FINITE. intros x Fx H0 H1.
  apply (faithful_finite (sqrt x)); [| exact (sqrt32_faithful x Fx H0)].
  rewrite Rabs_pos_eq by apply sqrt_pos.
  apply Rle_trans with 18446744073709551616.
  - rewrite <- (sqrt_square 18446744073709551616) by lra. apply sqrt_le_1_alt.
    apply Rle_trans with (1 := H1). unfold FMAX32. bnum. lra.
  - unfold FMAX32. bnum. lra.
Qed.

Theorem rsqrt32_finite : RSQRT32_FINITE.
Proof.
  unfold RSQRT32_FINITE. intros x Fx H0 H1.
  assert (Hlt : x < bpow radix2 128) by (pose proof fmax_lt; lra).
  apply (faithful_finite (/ sqrt x)); [| exact (rsqrt32_faithful x Fx H0 Hlt)].
  pose proof (f32_pos_ge x Fx H0) as Hx.
  assert (Hs : bpow radix2 (-75) <= sqrt x).
  { rewrite <- (sqrt_square (bpow radix2 (-75))) by apply bpow_ge_0. apply sqrt_le_1_alt.
    rewrite <- bpow_plus. apply Rle_trans with (2 := Hx). apply bpow_le. lia. }
  assert (Bp : 0 < bpow radix2 (-75)) by apply bpow_gt_0.
  rewrite Rabs_pos_eq by (left; apply Rinv_0_lt_compat; lra).
  apply Rle_trans with (/ bpow radix2 (-75)).
  - apply Rinv_le_contravar; assumption.
  - clear. rewrite <- bpow_opp. cbn [Z.opp]. unfold FMAX32. bnum. lra.
Qed.

(* hypot32 *)

Lemma abs_le_hyp (x y : R) : Rabs x <= sqrt (x * x + y * y).
Proof.
  rewrite <- (sqrt_Rsqr_abs x). apply sqrt_le_1_alt.
  pose proof (Rle_0_sqr y) as Hy. unfold Rsqr in *. lra.
Qed.

Theorem hypot32_finite : HYPOT32_FINITE.
Proof.
  unfold HYPOT32_FINITE. intros x y Fx Fy H.
  pose proof fmax_lt as Hl.
  assert (Hx : Rabs x < bpow radix2 128) by (pose proof (abs_le_hyp x y); lra).
  assert (Hy : Rabs y < bpow radix2 128).
  { pose proof (abs_le_hyp y x) as A. replace (y * y + x * x) with (x * x + y * y) in A by ring. lra. }
  apply (faithful_finite (sqrt (x * x + y * y))); [| exact (hypot32_faithful x y Fx Fy Hx Hy)].
  rewrite Rabs_pos_eq by apply sqrt_pos. exact H.
Qed.

Lemma f64_bpow (e : Z) : (-1074 <= e)%Z -> format64 (bpow radix2 e).
Proof. intros H. apply generic_format_FLT_bpow; [typeclasses eauto | exact H]. Qed.

(* With both inputs FMAX32 the graph's result is at least 2^128. *)
Lemma hyp_big : bpow radix2 128 <= g_hypot32 FMAX32 FMAX32.
Proof.
  unfold g_hypot32.
  set (a := RN64 (FMAX32 * FMAX32)).
  assert (Ha : bpow radix2 255 <= a).
  { unfold a. apply round_ge_generic; [typeclasses eauto | typeclasses eauto | apply f64_bpow; lia |].
    unfold FMAX32. bnum. lra. }
  set (s := RN64 (a + a)).
  assert (Hs : bpow radix2 256 <= s).
  { unfold s. apply round_ge_generic; [typeclasses eauto | typeclasses eauto | apply f64_bpow; lia |].
    apply Rle_trans with (bpow radix2 255 + bpow radix2 255); [clear; bnum; lra | lra]. }
  set (r := RN64 (sqrt s)).
  assert (Hr : bpow radix2 128 <= r).
  { unfold r. apply round_ge_generic; [typeclasses eauto | typeclasses eauto | apply f64_bpow; lia |].
    rewrite <- (sqrt_square (bpow radix2 128)) by apply bpow_ge_0. apply sqrt_le_1_alt.
    rewrite <- bpow_plus. exact Hs. }
  assert (Fr : format64 r) by (apply generic_format_round; typeclasses eauto).
  rewrite (T32_proof r Fr).
  apply round_ge_generic; [typeclasses eauto | typeclasses eauto | | exact Hr].
  apply generic_format_FLT_bpow; [typeclasses eauto | lia].
Qed.

Theorem hypot32_sharp : HYPOT32_SHARP.
Proof.
  unfold HYPOT32_SHARP, finite32. intros [_ H].
  pose proof hyp_big as B. pose proof fmax_lt as L.
  pose proof (Rle_abs (g_hypot32 FMAX32 FMAX32)) as A. lra.
Qed.

Theorem p32r : P32R.
Proof.
  exact (conj faithful_finite (conj narrow_finite (conj narrow_sharp (conj sqrt32_finite
          (conj rsqrt32_finite (conj hypot32_finite hypot32_sharp)))))).
Qed.
