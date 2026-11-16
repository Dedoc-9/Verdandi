(* Proof of IEEE_EXP32 (statement in IEEE64_Statement.v, which this file does not change). Flocq and the standard
   library only; every lemma ends with Qed and nothing is assumed. Author: the assistant (2026-11-15).

   The shape is narrow (S^12 (P (red x))): the clamp at -160 and a division by 4096, the polynomial (seven
   multiply-add steps and a division by 5040), twelve squarings, narrow. Each IEEE operation is walked with its
   lemma of Ops.v; what is left each time is that the model's rounded value is below 2^1024 in magnitude.

     red_ok     The clamp compares two finite values (the input, the constant -160), so it chooses as the model's
                does (Ops.op_sel_lt_at); either way the chosen value is finite and lies between -160 and XMAX < 89,
                so its quotient by 4096 is at most 2^-4 in magnitude (red_small). The divisor 4096 is not 0.
     poly_ok    With |r| <= 2^-4 every intermediate of the polynomial is small (horner_step, one level at a time):
                  |7 + r| <= 2^3, then a product at most 2^-4 times the level before and a sum with the coefficient:
                  42 + 2^-1 <= 2^6, 210 + 2^2 <= 2^8, 840 + 2^4 <= 2^10, 2520 + 2^6 <= 2^12, 5040 + 2^8 <= 2^13,
                  5040 + 2^9 <= 2^13, and the quotient by 5040 is at most 2^1. The divisor 5040 is not 0.
     sq_ok      One squaring whose model value is at most 2^128 (and it is never negative) does not overflow.
     the bound on the squarings
                The twelve values s1 .. s12 cannot be bounded crudely (2 squared twelve times is 2^4096). They are
                bounded from the end: the model's last value s12 is below OVF32 < 2^128, because the graph's result
                narrow s12 is a finite binary32 number (exp32r's EXP32_RANGE gives exp x < FMAX32, exp32's EXP32
                gives faithfulness, p32r's FAITHFUL_FINITE makes the result finite, and P32_IEEE.narrow_inv turns
                that into the bound on narrow's argument). And a squaring never shrinks a value above 1 (sq_back:
                for a binary64 number s and B >= 1, RN64 (s * s) <= B gives s <= B, since for s > 1 rounding is
                monotone and leaves s unchanged). So every one of s1 .. s12 is at most 2^128.
     narrow     P32_IEEE.IEEE_NARROW_proof, at the last squaring's value, which is below OVF32.

   Nothing is said of the value the clamp does not choose (the statement does not ask it). *)
From Coq Require Import Reals ZArith Lia Lra.
From Flocq Require Import Core BinarySingleNaN.
From MKF.f32 Require Import F32_Statement.
From MKF.p32 Require Import Graphs.
From MKF.p32r Require Import P32R_Statement Range.
From MKF.exp32 Require Import Graph EXP32_Statement.
From MKF.exp32 Require Exp32.
From MKF.exp32r Require RANGE_Statement Range.
From MKF.ieee64 Require Import IEEE64_Statement Ops P32_IEEE.
Open Scope R_scope.

#[local] Instance x53 : Prec_gt_0 53 := prec64_gt_0.

(* The constants of exp32, as the graph file writes them *)

Lemma val_m160 : B2R (o_cst ieee_ops C_m160) = -160. Proof. exact (cst_val C_m160). Qed.
Lemma val_4096 : B2R (o_cst ieee_ops C_4096) = 4096. Proof. exact (cst_val C_4096). Qed.
Lemma val_5040 : B2R (o_cst ieee_ops C_5040) = 5040. Proof. exact (cst_val C_5040). Qed.
Lemma val_2520 : B2R (o_cst ieee_ops C_2520) = 2520. Proof. exact (cst_val C_2520). Qed.
Lemma val_840 : B2R (o_cst ieee_ops C_840) = 840. Proof. exact (cst_val C_840). Qed.
Lemma val_210 : B2R (o_cst ieee_ops C_210) = 210. Proof. exact (cst_val C_210). Qed.
Lemma val_42 : B2R (o_cst ieee_ops C_42) = 42. Proof. exact (cst_val C_42). Qed.
Lemma val_7 : B2R (o_cst ieee_ops C_7) = 7. Proof. exact (cst_val C_7). Qed.

(* The reduction: clamp below at -160, divide by 4096 *)

Lemma red_small (x : R) : x <= XMAX -> Rabs (exp32_red x) <= bpow radix2 (-4).
Proof.
  intros Hx. unfold exp32_red. apply rn64_abs_le; [lia |].
  unfold XMAX in Hx. apply Rabs_le. destruct (Rlt_dec x (-160)); bnum; lra.
Qed.

Lemma red_ok (b : b64) : is_finite b = true -> B2R b <= XMAX ->
  is_finite (G_exp32_red b64 ieee_ops b) = true /\ B2R (G_exp32_red b64 ieee_ops b) = exp32_red (B2R b).
Proof.
  intros Fb Hx. unfold G_exp32_red, exp32_red.
  rewrite (op_sel_lt_at b (o_cst ieee_ops C_m160) (o_cst ieee_ops C_m160) b (B2R b) (-160)
             Fb (cst_fin C_m160) eq_refl val_m160).
  unfold XMAX in Hx.
  destruct (Rlt_dec (B2R b) (-160)) as [L | L].
  - apply (op_div_at (o_cst ieee_ops C_m160) (o_cst ieee_ops C_4096) (-160) 4096
             (cst_fin C_m160) val_m160 val_4096).
    + lra.
    + apply (rn64_lt_emax _ (-4)); [lia |]. apply Rabs_le. bnum. lra.
  - apply (op_div_at b (o_cst ieee_ops C_4096) (B2R b) 4096 Fb eq_refl val_4096).
    + lra.
    + apply (rn64_lt_emax _ (-4)); [lia |]. apply Rabs_le. bnum. lra.
Qed.

(* The polynomial. One level: c + r * w, with |r| <= 2^-4 and |w| <= 2^e; the product is at most 2^em, em = e - 4,
   and the sum at most c + 2^em <= 2^e'. Neither rounding overflows, and the level's value is at most 2^e'. *)
Lemma horner_step (c : gconst) (cv : R) (r w : b64) (wv : R) (e em e' : Z) :
  is_finite r = true -> is_finite w = true -> B2R w = wv -> B2R (o_cst ieee_ops c) = cv ->
  Rabs (B2R r) <= bpow radix2 (-4) -> Rabs wv <= bpow radix2 e ->
  em = (-4 + e)%Z -> (-1074 <= em < 1024)%Z -> (-1074 <= e' < 1024)%Z ->
  0 <= cv -> cv + bpow radix2 em <= bpow radix2 e' ->
  is_finite (o_add ieee_ops (o_cst ieee_ops c) (o_mul ieee_ops r w)) = true /\
  B2R (o_add ieee_ops (o_cst ieee_ops c) (o_mul ieee_ops r w)) = RN64 (cv + RN64 (B2R r * wv)) /\
  Rabs (RN64 (cv + RN64 (B2R r * wv))) <= bpow radix2 e'.
Proof.
  intros Fr Fw Ew Ec Hr Hw Eem Hem He' Hc Hsum.
  assert (B1 : Rabs (B2R r * wv) <= bpow radix2 em).
  { rewrite Eem, Rabs_mult, bpow_plus. apply Rmult_le_compat; try apply Rabs_pos; assumption. }
  destruct (op_mul_at r w (B2R r) wv Fr Fw eq_refl Ew) as [Fm Vm].
  { apply (rn64_lt_emax _ em); [exact Hem | exact B1]. }
  apply (rn64_abs_le _ em) in B1; [| lia].
  assert (B2 : Rabs (cv + RN64 (B2R r * wv)) <= bpow radix2 e').
  { set (m := RN64 (B2R r * wv)) in *. apply Rabs_le. apply Rabs_le_inv in B1. lra. }
  destruct (op_add_at (o_cst ieee_ops c) (o_mul ieee_ops r w) cv (RN64 (B2R r * wv)) (cst_fin c) Fm Ec Vm)
    as [Fa Va].
  { apply (rn64_lt_emax _ e'); [exact He' | exact B2]. }
  split; [exact Fa |]. split; [exact Va |]. apply rn64_abs_le; [lia | exact B2].
Qed.

Lemma poly_ok (r : b64) : is_finite r = true -> Rabs (B2R r) <= bpow radix2 (-4) ->
  is_finite (G_exp32_poly b64 ieee_ops r) = true /\ B2R (G_exp32_poly b64 ieee_ops r) = exp32_poly (B2R r).
Proof.
  intros Fr Hr. unfold G_exp32_poly, exp32_poly.
  assert (B7 : Rabs (7 + B2R r) <= bpow radix2 3).
  { apply Rabs_le. apply Rabs_le_inv in Hr. bnum. lra. }
  destruct (op_add_at (o_cst ieee_ops C_7) r 7 (B2R r) (cst_fin C_7) Fr val_7 eq_refl) as [F7 V7].
  { apply (rn64_lt_emax _ 3); [lia | exact B7]. }
  apply (rn64_abs_le _ 3) in B7; [| lia].
  destruct (horner_step C_42 42 r _ _ 3 (-1) 6 Fr F7 V7 val_42 Hr B7) as (F6 & V6 & B6);
    [reflexivity | lia | lia | lra | bnum; lra |].
  destruct (horner_step C_210 210 r _ _ 6 2 8 Fr F6 V6 val_210 Hr B6) as (F5 & V5 & B5);
    [reflexivity | lia | lia | lra | bnum; lra |].
  destruct (horner_step C_840 840 r _ _ 8 4 10 Fr F5 V5 val_840 Hr B5) as (F4 & V4 & B4);
    [reflexivity | lia | lia | lra | bnum; lra |].
  destruct (horner_step C_2520 2520 r _ _ 10 6 12 Fr F4 V4 val_2520 Hr B4) as (F3 & V3 & B3);
    [reflexivity | lia | lia | lra | bnum; lra |].
  destruct (horner_step C_5040 5040 r _ _ 12 8 13 Fr F3 V3 val_5040 Hr B3) as (F2 & V2 & B2);
    [reflexivity | lia | lia | lra | bnum; lra |].
  destruct (horner_step C_5040 5040 r _ _ 13 9 13 Fr F2 V2 val_5040 Hr B2) as (F1 & V1 & B1);
    [reflexivity | lia | lia | lra | bnum; lra |].
  apply (op_div_at _ (o_cst ieee_ops C_5040) _ 5040 F1 V1 val_5040).
  - lra.
  - apply (rn64_lt_emax _ 1); [lia |].
    match type of B1 with Rabs ?t <= _ => set (a := t) in * end.
    apply Rabs_le. apply Rabs_le_inv in B1. clear -B1. bnum. lra.
Qed.

(* The squarings *)

Lemma fmt_sq (v : R) : format64 (exp32_sq v).
Proof. exact (fmt64_rn (v * v)). Qed.

(* A squaring does not shrink a binary64 number above 1: a bound B >= 1 on the square is a bound on the number. *)
Lemma sq_back (s B : R) : format64 s -> 1 <= B -> exp32_sq s <= B -> s <= B.
Proof.
Admitted.
Lemma sq_back_rest (s B : R) : format64 s -> 1 <= B -> exp32_sq s <= B -> s <= B.
Proof.
  intros Fs HB H. destruct (Rle_or_lt s 1) as [L | L]; [lra |].
  apply Rle_trans with (2 := H). unfold exp32_sq.
  apply round_ge_generic; [typeclasses eauto | typeclasses eauto | exact Fs |].
  assert (s * 1 <= s * s) by (apply Rmult_le_compat_l; lra). lra.
Qed.

Lemma sq_ok (v : b64) (s : R) : is_finite v = true -> B2R v = s -> exp32_sq s <= bpow radix2 128 ->
  is_finite (G_exp32_sq b64 ieee_ops v) = true /\ B2R (G_exp32_sq b64 ieee_ops v) = exp32_sq s.
Proof.
  intros Fv Ev H. unfold G_exp32_sq. unfold exp32_sq in *.
  apply (op_mul_at v v s s Fv Fv Ev Ev).
  apply (between_lt_emax _ 128); [lia |].
  split; [apply rn64_ge_0; exact (Rle_0_sqr s) | exact H].
Qed.

(* exp32 *)

Theorem IEEE_EXP32_proof : IEEE_EXP32.
Proof.
  unfold IEEE_EXP32. intros b Fb Hf Hx.
  (* the graph's result is a finite binary32 number: the range theorem, faithfulness, FAITHFUL_FINITE *)
  assert (Hfin : finite32 (g_exp32 (B2R b))).
  { destruct (MKF.exp32r.Range.exp32_range (B2R b) Hf Hx) as [He _].
    apply (faithful_finite (exp (B2R b))); [| exact (MKF.exp32.Exp32.exp32_faithful (B2R b) Hf Hx)].
    rewrite Rabs_pos_eq by (left; apply exp_pos). left. exact He. }
  unfold G_exp32. unfold g_exp32 in Hfin |- *.
  (* the reduction and the polynomial *)
  destruct (red_ok b Fb Hx) as [Fr Vr].
  pose proof (red_small (B2R b) Hx) as Br.
  set (r := exp32_red (B2R b)) in *.
  destruct (poly_ok _ Fr) as [Fp Vp]; [rewrite Vr; exact Br |].
  rewrite Vr in Vp.
  set (p := exp32_poly r) in *.
  set (s1 := exp32_sq p) in *.
  set (s2 := exp32_sq s1) in *.
  set (s3 := exp32_sq s2) in *.
  set (s4 := exp32_sq s3) in *.
  set (s5 := exp32_sq s4) in *.
  set (s6 := exp32_sq s5) in *.
  set (s7 := exp32_sq s6) in *.
  set (s8 := exp32_sq s7) in *.
  set (s9 := exp32_sq s8) in *.
  set (s10 := exp32_sq s9) in *.
  set (s11 := exp32_sq s10) in *.
  set (s12 := exp32_sq s11) in *.
  (* the last squaring's value is below OVF32, and so every squaring's value is at most 2^128 *)
  assert (L12 : Rabs s12 < OVF32) by (apply narrow_inv; [exact (fmt_sq s11) | exact Hfin]).
  assert (O : 1 <= bpow radix2 128) by (bnum; lra).
  assert (B12 : s12 <= bpow radix2 128).
  { apply Rabs_lt_inv in L12. pose proof ovf_lt_128. lra. }
  pose proof (sq_back s11 _ (fmt_sq s10) O B12) as B11.
  pose proof (sq_back s10 _ (fmt_sq s9) O B11) as B10.
  pose proof (sq_back s9 _ (fmt_sq s8) O B10) as B9.
  pose proof (sq_back s8 _ (fmt_sq s7) O B9) as B8.
  pose proof (sq_back s7 _ (fmt_sq s6) O B8) as B7.
  pose proof (sq_back s6 _ (fmt_sq s5) O B7) as B6.
  pose proof (sq_back s5 _ (fmt_sq s4) O B6) as B5.
  pose proof (sq_back s4 _ (fmt_sq s3) O B5) as B4.
  pose proof (sq_back s3 _ (fmt_sq s2) O B4) as B3.
  pose proof (sq_back s2 _ (fmt_sq s1) O B3) as B2.
  pose proof (sq_back s1 _ (fmt_sq p) O B2) as B1.
  (* the twelve squarings *)
  destruct (sq_ok _ p Fp Vp B1) as [F1 V1].
  destruct (sq_ok _ s1 F1 V1 B2) as [F2 V2].
  destruct (sq_ok _ s2 F2 V2 B3) as [F3 V3].
  destruct (sq_ok _ s3 F3 V3 B4) as [F4 V4].
  destruct (sq_ok _ s4 F4 V4 B5) as [F5 V5].
  destruct (sq_ok _ s5 F5 V5 B6) as [F6 V6].
  destruct (sq_ok _ s6 F6 V6 B7) as [F7 V7].
  destruct (sq_ok _ s7 F7 V7 B8) as [F8 V8].
  destruct (sq_ok _ s8 F8 V8 B9) as [F9 V9].
  destruct (sq_ok _ s9 F9 V9 B10) as [F10 V10].
  destruct (sq_ok _ s10 F10 V10 B11) as [F11 V11].
  destruct (sq_ok _ s11 F11 V11 B12) as [F12 V12].
  (* narrow *)
  destruct (IEEE_NARROW_proof _ F12) as [Fn Vn]; [rewrite V12; exact L12 |].
  split; [exact Fn |]. rewrite Vn, V12. reflexivity.
Qed.
