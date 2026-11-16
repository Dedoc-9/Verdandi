(* Proofs of IEEE_CST, IEEE_NARROW, IEEE_SQRT32, IEEE_RSQRT32 and IEEE_HYPOT32 (statements in IEEE64_Statement.v,
   which this file does not change). Flocq and the standard library only; every lemma ends with Qed and nothing
   is assumed. Author: the assistant (2026-11-15). IEEE_EXP32, and so IEEE64 itself, is not proved here.

   How each goes.
     IEEE_CST      Ops.cst_ok: each constant's mantissa and exponent, computed.
     IEEE_NARROW   The two selections compare finite values (the absolute value of a finite value, a constant), so
                   they choose as the model's do (Ops.op_sel_le_at, op_sel_lt_at), and the branch the model takes is
                   the branch IEEE takes. In that branch each operation is walked with its lemma of Ops.v; what is
                   left each time is that the model's rounded value is below 2^1024, and it is far below:
                     |v| <= HH        v * 0 is 0;
                     |v| < TT         |v + MM| <= 2^-96, then |.. - MM| <= 2^-95;
                     otherwise        |v| < OVF32 < 2^128, so |KK * v| <= 2^158, |c - v| <= 2^159 and
                                      |c - (c - v)| <= 2^160.
                   Nothing is said of the two branches not taken (the statement does not ask it).
     narrow_inv    The range theorems bound narrow's result, and the walk needs a bound on its argument: for a
                   binary64 number v, if narrow v is a finite binary32 number then |v| < OVF32. It is the converse
                   of p32r's NARROW_FINITE, from p32r's own NARROW_SHARP (narrow OVF32 = 2^128), T32 (narrow is
                   RN32 on binary64) and the monotonicity of rounding.
     IEEE_SQRT32   Bsqrt of a finite value that is not negative is finite and denotes RN64 (sqrt x); p32r's
                   SQRT32_FINITE with narrow_inv puts that value below OVF32; IEEE_NARROW does the rest.
     IEEE_RSQRT32  The same, and the division: its divisor RN64 (sqrt x) is at least 2^-1022 (x is a positive
                   binary32 number, so x >= 2^-149), so it is not 0; its rounded quotient is below OVF32 by p32r's
                   RSQRT32_FINITE with narrow_inv, so below 2^1024.
     IEEE_HYPOT32  |x|, |y| <= sqrt (x*x + y*y) <= FMAX32 < 2^128, so each rounded square is between 0 and 2^256
                   and their rounded sum between 0 and 2^257: no overflow, and the square root's operand is not
                   negative. p32r's HYPOT32_FINITE with narrow_inv puts the rounded root below OVF32; IEEE_NARROW
                   does the rest. *)
From Coq Require Import Reals ZArith Lia Lra.
From Flocq Require Import Core BinarySingleNaN.
From MKF.f32 Require Import F32_Statement.
From MKF.p32 Require Import Graphs P32_Statement T32 Funcs.
From MKF.p32r Require Import P32R_Statement Range.
From MKF.ieee64 Require Import IEEE64_Statement Ops.
Open Scope R_scope.

#[local] Instance i24 : Prec_gt_0 24 := ltac:(unfold Prec_gt_0; lia).
#[local] Instance i53 : Prec_gt_0 53 := prec64_gt_0.

(* The constants *)

Theorem IEEE_CST_proof : IEEE_CST.
Proof. exact cst_ok. Qed.

Lemma val_KK : B2R (o_cst ieee_ops C_KK) = KK. Proof. exact (cst_val C_KK). Qed.
Lemma val_MM : B2R (o_cst ieee_ops C_MM) = MM. Proof. exact (cst_val C_MM). Qed.
Lemma val_TT : B2R (o_cst ieee_ops C_TT) = TT. Proof. exact (cst_val C_TT). Qed.
Lemma val_HH : B2R (o_cst ieee_ops C_HH) = HH. Proof. exact (cst_val C_HH). Qed.
Lemma val_0 : B2R (o_cst ieee_ops C_0) = 0. Proof. exact (cst_val C_0). Qed.
Lemma val_1 : B2R (o_cst ieee_ops C_1) = 1. Proof. exact (cst_val C_1). Qed.

(* narrow *)

Lemma ovf_lt_128 : OVF32 < bpow radix2 128.
Proof. unfold OVF32. bnum. lra. Qed.

Lemma ovf_lt_emax : OVF32 < bpow radix2 1024.
Proof. apply Rlt_trans with (1 := ovf_lt_128). apply bpow_lt. lia. Qed.

Theorem IEEE_NARROW_proof : IEEE_NARROW.
Proof.
  unfold IEEE_NARROW. intros b Fb Hb.
  unfold G_narrow, narrow.
  assert (Fa : is_finite (o_abs ieee_ops b) = true) by (rewrite op_abs_fin; exact Fb).
  rewrite (op_sel_lt_at (o_abs ieee_ops b) (o_cst ieee_ops C_TT) _ _ (Rabs (B2R b)) TT
             Fa (cst_fin C_TT) (op_abs_val b) val_TT).
  rewrite (op_sel_le_at (o_abs ieee_ops b) (o_cst ieee_ops C_HH) _ _ (Rabs (B2R b)) HH
             Fa (cst_fin C_HH) (op_abs_val b) val_HH).
  destruct (Rle_dec (Rabs (B2R b)) HH) as [H1 | H1].
  - (* |v| <= HH: v * 0 *)
    apply (op_mul_at b (o_cst ieee_ops C_0) (B2R b) 0 Fb (cst_fin C_0) eq_refl val_0).
    rewrite Rmult_0_r. rewrite (round_0 radix2 fexp64 ZnearestE). rewrite Rabs_R0. apply bpow_gt_0.
  - destruct (Rlt_dec (Rabs (B2R b)) TT) as [H2 | H2].
    + (* |v| < TT: (v + MM) - MM *)
      assert (B1 : Rabs (B2R b + MM) <= bpow radix2 (-96)).
      { apply Rabs_le. apply Rabs_lt_inv in H2. unfold MM, TT in *. bnum. lra. }
      destruct (op_add_at b (o_cst ieee_ops C_MM) (B2R b) MM Fb (cst_fin C_MM) eq_refl val_MM) as [Fp Vp].
      { apply (rn64_lt_emax _ (-96)); [lia | exact B1]. }
      assert (B2 : Rabs (RN64 (B2R b + MM) - MM) <= bpow radix2 (-95)).
      { apply (rn64_abs_le _ (-96)) in B1; [| lia].
        set (p := RN64 (B2R b + MM)) in *.
        apply Rabs_le. apply Rabs_le_inv in B1. unfold MM in *. bnum. lra. }
      apply (op_sub_at _ (o_cst ieee_ops C_MM) _ MM Fp (cst_fin C_MM) Vp val_MM).
      apply (rn64_lt_emax _ (-95)); [lia | exact B2].
    + (* otherwise: c - (c - v) with c = KK * v *)
      assert (B1 : Rabs (KK * B2R b) <= bpow radix2 158).
      { apply Rabs_le. apply Rabs_lt_inv in Hb. unfold KK, OVF32 in *. bnum. lra. }
      destruct (op_mul_at (o_cst ieee_ops C_KK) b KK (B2R b) (cst_fin C_KK) Fb val_KK eq_refl) as [Fc Vc].
      { apply (rn64_lt_emax _ 158); [lia | exact B1]. }
      apply (rn64_abs_le _ 158) in B1; [| lia].
      assert (B2 : Rabs (RN64 (KK * B2R b) - B2R b) <= bpow radix2 159).
      { set (c := RN64 (KK * B2R b)) in *.
        apply Rabs_le. apply Rabs_le_inv in B1. apply Rabs_lt_inv in Hb. unfold OVF32 in *. bnum. lra. }
      destruct (op_sub_at _ b _ (B2R b) Fc Fb Vc eq_refl) as [Fd Vd].
      { apply (rn64_lt_emax _ 159); [lia | exact B2]. }
      apply (rn64_abs_le _ 159) in B2; [| lia].
      assert (B3 : Rabs (RN64 (KK * B2R b) - RN64 (RN64 (KK * B2R b) - B2R b)) <= bpow radix2 160).
      { set (c := RN64 (KK * B2R b)) in *. set (d := RN64 (c - B2R b)) in *.
        apply Rabs_le. apply Rabs_le_inv in B1. apply Rabs_le_inv in B2. bnum. lra. }
      apply (op_sub_at _ _ _ _ Fc Fd Vc Vd).
      apply (rn64_lt_emax _ 160); [lia | exact B3].
Qed.

(* The converse of NARROW_FINITE: a binary64 number whose narrow is a finite binary32 number is below OVF32. *)
Lemma narrow_inv (v : R) : format64 v -> finite32 (narrow v) -> Rabs v < OVF32.
Proof.
  intros Fv [_ H].
  destruct (Rlt_or_le (Rabs v) OVF32) as [L | L]; [exact L | exfalso].
  rewrite (T32_proof v Fv) in H.
  rewrite <- (round_NE_abs radix2 fexp32 v) in H.
  assert (M : RN32 OVF32 <= RN32 (Rabs v)) by (apply round_le; [typeclasses eauto | typeclasses eauto | exact L]).
  rewrite <- (T32_proof OVF32 ovf_format64) in M.
  pose proof narrow_sharp as Sh. unfold NARROW_SHARP in Sh. rewrite Sh in M.
  pose proof fmax_lt. lra.
Qed.

Lemma fmt64_rn (z : R) : format64 (RN64 z).
Proof. apply generic_format_round; typeclasses eauto. Qed.

(* sqrt32 *)

Theorem IEEE_SQRT32_proof : IEEE_SQRT32.
Proof.
  unfold IEEE_SQRT32. intros b Fb Hf H0 H1.
  unfold G_sqrt32.
  destruct (op_sqrt b Fb H0) as [Fs Vs].
  assert (Hv : Rabs (B2R (o_sqrt ieee_ops b)) < OVF32).
  { rewrite Vs. apply narrow_inv; [apply fmt64_rn |]. exact (sqrt32_finite (B2R b) Hf H0 H1). }
  destruct (IEEE_NARROW_proof (o_sqrt ieee_ops b) Fs Hv) as [Fn Vn].
  split; [exact Fn |]. rewrite Vn, Vs. reflexivity.
Qed.

(* rsqrt32 *)

Theorem IEEE_RSQRT32_proof : IEEE_RSQRT32.
Proof.
  unfold IEEE_RSQRT32. intros b Fb Hf H0 H1.
  unfold G_rsqrt32.
  destruct (op_sqrt b Fb (Rlt_le _ _ H0)) as [Fs Vs].
  assert (Hq : Rabs (RN64 (1 / RN64 (sqrt (B2R b)))) < OVF32).
  { apply narrow_inv; [apply fmt64_rn |]. exact (rsqrt32_finite (B2R b) Hf H0 H1). }
  assert (Hs : RN64 (sqrt (B2R b)) <> 0).
  { apply Rgt_not_eq. apply Rlt_le_trans with (bpow radix2 (-1022)); [apply bpow_gt_0 |].
    apply round_ge_generic; [typeclasses eauto | typeclasses eauto | apply fmt64_bpow; lia |].
    apply sqrt_ge_bpow. apply Rle_trans with (2 := f32_pos_ge (B2R b) Hf H0). apply bpow_le. lia. }
  destruct (op_div_at (o_cst ieee_ops C_1) (o_sqrt ieee_ops b) 1 (RN64 (sqrt (B2R b))) (cst_fin C_1) val_1 Vs Hs)
    as [Fd Vd].
  { apply Rlt_trans with (1 := Hq). exact ovf_lt_emax. }
  destruct (IEEE_NARROW_proof (o_div ieee_ops (o_cst ieee_ops C_1) (o_sqrt ieee_ops b)) Fd) as [Fn Vn].
  { rewrite Vd. exact Hq. }
  split; [exact Fn |]. rewrite Vn, Vd. reflexivity.
Qed.

(* hypot32 *)

Lemma sq_between (x : R) (e : Z) : Rabs x <= bpow radix2 e -> 0 <= x * x <= bpow radix2 (e + e).
Proof.
  intros H. split.
  - exact (Rle_0_sqr x).
  - replace (x * x) with (Rabs x * Rabs x) by (unfold Rabs; destruct (Rcase_abs x); ring).
    rewrite bpow_plus. pose proof (Rabs_pos x). apply Rmult_le_compat; assumption.
Qed.

Lemma rn64_between (z : R) (e : Z) : (-1074 <= e)%Z -> 0 <= z <= bpow radix2 e -> 0 <= RN64 z <= bpow radix2 e.
Proof.
  intros He [H0 H1]. split.
  - apply rn64_ge_0. exact H0.
  - apply round_le_generic; [typeclasses eauto | typeclasses eauto | apply fmt64_bpow; exact He | exact H1].
Qed.

Lemma between_lt_emax (z : R) (e : Z) : (e < 1024)%Z -> 0 <= z <= bpow radix2 e -> Rabs z < bpow radix2 1024.
Proof.
  intros He [H0 H1]. rewrite Rabs_pos_eq by exact H0.
  apply Rle_lt_trans with (1 := H1). apply bpow_lt. exact He.
Qed.

Theorem IEEE_HYPOT32_proof : IEEE_HYPOT32.
Proof.
  unfold IEEE_HYPOT32. intros b1 b2 F1 F2 Hf1 Hf2 H.
  unfold G_hypot32.
  pose proof fmax_lt as HM.
  assert (Hx : Rabs (B2R b1) <= bpow radix2 128).
  { pose proof (abs_le_hyp (B2R b1) (B2R b2)). lra. }
  assert (Hy : Rabs (B2R b2) <= bpow radix2 128).
  { pose proof (abs_le_hyp (B2R b2) (B2R b1)) as A.
    replace (B2R b2 * B2R b2 + B2R b1 * B2R b1) with (B2R b1 * B2R b1 + B2R b2 * B2R b2) in A by ring. lra. }
  assert (Ba : 0 <= RN64 (B2R b1 * B2R b1) <= bpow radix2 256).
  { apply rn64_between; [lia |]. exact (sq_between (B2R b1) 128 Hx). }
  assert (Bb : 0 <= RN64 (B2R b2 * B2R b2) <= bpow radix2 256).
  { apply rn64_between; [lia |]. exact (sq_between (B2R b2) 128 Hy). }
  assert (Bs : 0 <= RN64 (RN64 (B2R b1 * B2R b1) + RN64 (B2R b2 * B2R b2)) <= bpow radix2 257).
  { apply rn64_between; [lia |].
    set (a := RN64 (B2R b1 * B2R b1)) in *. set (c := RN64 (B2R b2 * B2R b2)) in *.
    change (bpow radix2 257) with (bpow radix2 (256 + 1)). rewrite bpow_plus.
    change (bpow radix2 1) with 2. lra. }
  destruct (op_mul b1 b1 F1 F1) as [Fa Va].
  { apply (between_lt_emax _ 256); [lia | exact Ba]. }
  destruct (op_mul b2 b2 F2 F2) as [Fc Vc].
  { apply (between_lt_emax _ 256); [lia | exact Bb]. }
  destruct (op_add_at _ _ _ _ Fa Fc Va Vc) as [Fs Vs].
  { apply (between_lt_emax _ 257); [lia | exact Bs]. }
  destruct (op_sqrt_at _ _ Fs Vs (proj1 Bs)) as [Fr Vr].
  assert (Hv : Rabs (RN64 (sqrt (RN64 (RN64 (B2R b1 * B2R b1) + RN64 (B2R b2 * B2R b2))))) < OVF32).
  { apply narrow_inv; [apply fmt64_rn |]. exact (hypot32_finite (B2R b1) (B2R b2) Hf1 Hf2 H). }
  destruct (IEEE_NARROW_proof _ Fr) as [Fn Vn].
  { rewrite Vr. exact Hv. }
  split; [exact Fn |]. rewrite Vn, Vr. reflexivity.
Qed.
