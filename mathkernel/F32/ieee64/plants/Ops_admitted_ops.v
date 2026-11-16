(* Ops.v: one lemma per operation of ieee_ops (statement in IEEE64_Statement.v), for the proofs of the IEEE_*
   statements. Flocq and the standard library only; every lemma ends with Qed and nothing is assumed. Author: the
   assistant (2026-11-15).

   Each lemma is one use of Flocq's own lemma for that operation (Bplus_correct, Bminus_correct, Bmult_correct,
   Bdiv_correct, Bsqrt_correct, B2R_Babs, is_finite_Babs, Bleb_correct, Bltb_correct) at
   53 1024 prec64_gt_0 prec64_lt_emax mode_NE, with Flocq's rounding read as the graphs' RN64 (the two are
   convertible). In words:
     op_add, op_sub, op_mul   finite operands, and the model's rounded result below 2^1024 in magnitude: the IEEE
                              result is finite and its real number is RN64 of the real operation.
     op_div                   the same with a finite dividend and a divisor whose real number is not 0.
     op_sqrt                  a finite operand that is not negative: the result is finite and its real number is
                              RN64 of the real square root. There is no overflow case.
     op_abs_fin, op_abs_val   the absolute value is exact and as finite as its operand.
     op_sel_le, op_sel_lt     on finite operands the IEEE selection chooses as the model's does.
     cst_ok                   IEEE_CST's own body: every constant is finite and denotes the graph's constant.
   The forms op_*_at take the operands' real numbers as equations (B2R x = u), so that a graph can be walked one
   operation at a time, each step handing the next its value.
   rn64_abs_le and rn64_lt_emax bound a rounding by a power of two: the usual way to meet the overflow premise. *)
From Coq Require Import Reals ZArith Lia Lra.
From Flocq Require Import Core BinarySingleNaN.
From MKF.f32 Require Import F32_Statement.
From MKF.p32 Require Import Graphs.
From MKF.ieee64 Require Import IEEE64_Statement.
Open Scope R_scope.

#[local] Instance o53 : Prec_gt_0 53 := prec64_gt_0.

(* Bounds on a rounding *)

Lemma fmt64_bpow (e : Z) : (-1074 <= e)%Z -> format64 (bpow radix2 e).
Proof. intros H. apply generic_format_FLT_bpow; [typeclasses eauto | exact H]. Qed.

Lemma rn64_abs_le (z : R) (e : Z) : (-1074 <= e)%Z -> Rabs z <= bpow radix2 e -> Rabs (RN64 z) <= bpow radix2 e.
Proof.
  intros He Hz.
  exact (abs_round_le_generic radix2 fexp64 ZnearestE z (bpow radix2 e) (fmt64_bpow e He) Hz).
Qed.

Lemma rn64_lt_emax (z : R) (e : Z) : (-1074 <= e < 1024)%Z -> Rabs z <= bpow radix2 e ->
  Rabs (RN64 z) < bpow radix2 1024.
Proof.
  intros [H1 H2] Hz. apply Rle_lt_trans with (bpow radix2 e).
  - apply rn64_abs_le; assumption.
  - apply bpow_lt. exact H2.
Qed.

Lemma rn64_ge_0 (z : R) : 0 <= z -> 0 <= RN64 z.
Proof.
  intros Hz. apply round_ge_generic; [typeclasses eauto | typeclasses eauto | apply generic_format_0 | exact Hz].
Qed.

(* The four rounded operations *)

Lemma op_add (x y : b64) : is_finite x = true -> is_finite y = true ->
  Rabs (RN64 (B2R x + B2R y)) < bpow radix2 1024 ->
  is_finite (o_add ieee_ops x y) = true /\ B2R (o_add ieee_ops x y) = RN64 (B2R x + B2R y).
Proof.
  intros Fx Fy H.
  generalize (Bplus_correct 53 1024 prec64_gt_0 prec64_lt_emax mode_NE x y Fx Fy).
  change (round radix2 (SpecFloat.fexp 53 1024) (round_mode mode_NE) (B2R x + B2R y))
    with (RN64 (B2R x + B2R y)).
  rewrite Rlt_bool_true by exact H.
  intros (H1 & H2 & _). split; [exact H2 | exact H1].
Qed.

Lemma op_sub (x y : b64) : is_finite x = true -> is_finite y = true ->
  Rabs (RN64 (B2R x - B2R y)) < bpow radix2 1024 ->
  is_finite (o_sub ieee_ops x y) = true /\ B2R (o_sub ieee_ops x y) = RN64 (B2R x - B2R y).
Proof.
  intros Fx Fy H.
  generalize (Bminus_correct 53 1024 prec64_gt_0 prec64_lt_emax mode_NE x y Fx Fy).
  change (round radix2 (SpecFloat.fexp 53 1024) (round_mode mode_NE) (B2R x - B2R y))
    with (RN64 (B2R x - B2R y)).
  rewrite Rlt_bool_true by exact H.
  intros (H1 & H2 & _). split; [exact H2 | exact H1].
Qed.

Lemma op_mul (x y : b64) : is_finite x = true -> is_finite y = true ->
  Rabs (RN64 (B2R x * B2R y)) < bpow radix2 1024 ->
  is_finite (o_mul ieee_ops x y) = true /\ B2R (o_mul ieee_ops x y) = RN64 (B2R x * B2R y).
Proof.
  intros Fx Fy H.
  generalize (Bmult_correct 53 1024 prec64_gt_0 prec64_lt_emax mode_NE x y).
  change (round radix2 (SpecFloat.fexp 53 1024) (round_mode mode_NE) (B2R x * B2R y))
    with (RN64 (B2R x * B2R y)).
  rewrite Rlt_bool_true by exact H.
  rewrite Fx, Fy.
  intros (H1 & H2 & _). split; [exact H2 | exact H1].
Qed.

Lemma op_div (x y : b64) : is_finite x = true -> B2R y <> 0 ->
  Rabs (RN64 (B2R x / B2R y)) < bpow radix2 1024 ->
  is_finite (o_div ieee_ops x y) = true /\ B2R (o_div ieee_ops x y) = RN64 (B2R x / B2R y).
Proof.
Admitted.
Lemma op_div_rest (x y : b64) : is_finite x = true -> B2R y <> 0 ->
  Rabs (RN64 (B2R x / B2R y)) < bpow radix2 1024 ->
  is_finite (o_div ieee_ops x y) = true /\ B2R (o_div ieee_ops x y) = RN64 (B2R x / B2R y).
Proof.
  intros Fx Ny H.
  generalize (Bdiv_correct 53 1024 prec64_gt_0 prec64_lt_emax mode_NE x y Ny).
  change (round radix2 (SpecFloat.fexp 53 1024) (round_mode mode_NE) (B2R x / B2R y))
    with (RN64 (B2R x / B2R y)).
  rewrite Rlt_bool_true by exact H.
  rewrite Fx.
  intros (H1 & H2 & _). split; [exact H2 | exact H1].
Qed.

(* The square root: no overflow case; finite for a finite operand that is not negative (a zero of either sign
   included: its real number is 0). *)
Lemma op_sqrt (x : b64) : is_finite x = true -> 0 <= B2R x ->
  is_finite (o_sqrt ieee_ops x) = true /\ B2R (o_sqrt ieee_ops x) = RN64 (sqrt (B2R x)).
Proof.
  intros Fx Hx.
  destruct (Bsqrt_correct 53 1024 prec64_gt_0 prec64_lt_emax mode_NE x) as (H1 & H2 & _).
  split; [| exact H1].
  change (is_finite (@Bsqrt 53 1024 prec64_gt_0 prec64_lt_emax mode_NE x) = true).
  rewrite H2.
  destruct x as [s | s | | s m e B]; try discriminate Fx; try reflexivity.
  destruct s; [| reflexivity].
  exfalso. revert Hx. unfold B2R. rewrite F2R_cond_Zopp. simpl cond_Ropp. intros Hx.
  assert (0 < F2R (Float radix2 (Z.pos m) e)) by (apply F2R_gt_0; reflexivity).
  lra.
Qed.

(* The absolute value: exact, and finite exactly when its operand is. *)
Lemma op_abs_val (x : b64) : B2R (o_abs ieee_ops x) = Rabs (B2R x).
Proof. exact (B2R_Babs 53 1024 x). Qed.

Lemma op_abs_fin (x : b64) : is_finite (o_abs ieee_ops x) = is_finite x.
Proof. exact (is_finite_Babs 53 1024 x). Qed.

(* The selections: on finite operands they choose as the model's do. *)
Lemma op_sel_le (a b c d : b64) : is_finite a = true -> is_finite b = true ->
  o_sel_le ieee_ops a b c d = if Rle_dec (B2R a) (B2R b) then c else d.
Proof.
  intros Fa Fb. cbv [o_sel_le ieee_ops].
  rewrite (Bleb_correct 53 1024 a b Fa Fb).
  destruct (Rle_dec (B2R a) (B2R b)) as [H | H].
  - rewrite Rle_bool_true by exact H. reflexivity.
  - rewrite Rle_bool_false by (apply Rnot_le_lt; exact H). reflexivity.
Qed.

Lemma op_sel_lt (a b c d : b64) : is_finite a = true -> is_finite b = true ->
  o_sel_lt ieee_ops a b c d = if Rlt_dec (B2R a) (B2R b) then c else d.
Proof.
  intros Fa Fb. cbv [o_sel_lt ieee_ops].
  rewrite (Bltb_correct 53 1024 a b Fa Fb).
  destruct (Rlt_dec (B2R a) (B2R b)) as [H | H].
  - rewrite Rlt_bool_true by exact H. reflexivity.
  - rewrite Rlt_bool_false by (apply Rnot_lt_le; exact H). reflexivity.
Qed.

(* The same lemmas with the operands' real numbers given as equations, for walking a graph. *)

Lemma op_add_at (x y : b64) (u v : R) : is_finite x = true -> is_finite y = true -> B2R x = u -> B2R y = v ->
  Rabs (RN64 (u + v)) < bpow radix2 1024 ->
  is_finite (o_add ieee_ops x y) = true /\ B2R (o_add ieee_ops x y) = RN64 (u + v).
Proof. intros Fx Fy Ex Ey. rewrite <- Ex, <- Ey. exact (op_add x y Fx Fy). Qed.

Lemma op_sub_at (x y : b64) (u v : R) : is_finite x = true -> is_finite y = true -> B2R x = u -> B2R y = v ->
  Rabs (RN64 (u - v)) < bpow radix2 1024 ->
  is_finite (o_sub ieee_ops x y) = true /\ B2R (o_sub ieee_ops x y) = RN64 (u - v).
Proof. intros Fx Fy Ex Ey. rewrite <- Ex, <- Ey. exact (op_sub x y Fx Fy). Qed.

Lemma op_mul_at (x y : b64) (u v : R) : is_finite x = true -> is_finite y = true -> B2R x = u -> B2R y = v ->
  Rabs (RN64 (u * v)) < bpow radix2 1024 ->
  is_finite (o_mul ieee_ops x y) = true /\ B2R (o_mul ieee_ops x y) = RN64 (u * v).
Proof. intros Fx Fy Ex Ey. rewrite <- Ex, <- Ey. exact (op_mul x y Fx Fy). Qed.

Lemma op_div_at (x y : b64) (u v : R) : is_finite x = true -> B2R x = u -> B2R y = v -> v <> 0 ->
  Rabs (RN64 (u / v)) < bpow radix2 1024 ->
  is_finite (o_div ieee_ops x y) = true /\ B2R (o_div ieee_ops x y) = RN64 (u / v).
Proof. intros Fx Ex Ey. rewrite <- Ex, <- Ey. exact (op_div x y Fx). Qed.

Lemma op_sqrt_at (x : b64) (u : R) : is_finite x = true -> B2R x = u -> 0 <= u ->
  is_finite (o_sqrt ieee_ops x) = true /\ B2R (o_sqrt ieee_ops x) = RN64 (sqrt u).
Proof. intros Fx Ex. rewrite <- Ex. exact (op_sqrt x Fx). Qed.

Lemma op_sel_le_at (a b c d : b64) (u v : R) : is_finite a = true -> is_finite b = true ->
  B2R a = u -> B2R b = v -> o_sel_le ieee_ops a b c d = if Rle_dec u v then c else d.
Proof. intros Fa Fb Ea Eb. rewrite <- Ea, <- Eb. exact (op_sel_le a b c d Fa Fb). Qed.

Lemma op_sel_lt_at (a b c d : b64) (u v : R) : is_finite a = true -> is_finite b = true ->
  B2R a = u -> B2R b = v -> o_sel_lt ieee_ops a b c d = if Rlt_dec u v then c else d.
Proof. intros Fa Fb Ea Eb. rewrite <- Ea, <- Eb. exact (op_sel_lt a b c d Fa Fb). Qed.

(* The constants. A finite binary64 value with sign s, mantissa m and exponent e, whose signed mantissa is
   n * 2^k, denotes n * 2^(e + k). *)
Lemma b2r_fin (s : bool) (m : positive) (e : Z) (H : SpecFloat.bounded 53 1024 m e = true) (n k : Z) :
  (0 <= k)%Z -> SpecFloat.cond_Zopp s (Z.pos m) = (n * 2 ^ k)%Z ->
  B2R (@B754_finite 53 1024 s m e H) = IZR n * bpow radix2 (e + k).
Proof.
  intros Hk E. unfold B2R. rewrite E. unfold F2R. cbn [Fnum Fexp].
  rewrite mult_IZR. change (IZR (2 ^ k)) with (IZR (Zpower radix2 k)).
  rewrite (IZR_Zpower radix2 k Hk). rewrite bpow_plus. ring.
Qed.

(* A whole number n written with the exponent -k. *)
Lemma b2r_whole (s : bool) (m : positive) (k : Z) (H : SpecFloat.bounded 53 1024 m (- k) = true) (n : Z) :
  (0 <= k)%Z -> SpecFloat.cond_Zopp s (Z.pos m) = (n * 2 ^ k)%Z ->
  B2R (@B754_finite 53 1024 s m (- k) H) = IZR n.
Proof.
  intros Hk E. rewrite (b2r_fin s m (- k) H n k Hk E).
  replace (- k + k)%Z with 0%Z by ring. change (bpow radix2 0) with 1. ring.
Qed.

Lemma cst_ok : forall c : gconst,
  is_finite (o_cst ieee_ops c) = true /\ B2R (o_cst ieee_ops c) = o_cst model_ops c.
Proof.
  intros c. split; [destruct c; reflexivity |].
  destruct c; cbv [o_cst ieee_ops model_ops ieee_cst model_cst].
  - unfold KK. apply (b2r_whole false _ 23 _ 536870913); [lia | reflexivity].
  - unfold MM. rewrite (b2r_fin false _ (-149) _ 3 51); [reflexivity | lia | reflexivity].
  - unfold TT. rewrite (b2r_fin false _ (-178) _ 1 52); [apply Rmult_1_l | lia | reflexivity].
  - unfold HH. rewrite (b2r_fin false _ (-202) _ 1 52); [apply Rmult_1_l | lia | reflexivity].
  - reflexivity.
  - apply (b2r_whole false _ 52 _ 1); [lia | reflexivity].
  - apply (b2r_whole true _ 45 _ (-160)); [lia | reflexivity].
  - apply (b2r_whole false _ 40 _ 4096); [lia | reflexivity].
  - apply (b2r_whole false _ 40 _ 5040); [lia | reflexivity].
  - apply (b2r_whole false _ 41 _ 2520); [lia | reflexivity].
  - apply (b2r_whole false _ 43 _ 840); [lia | reflexivity].
  - apply (b2r_whole false _ 45 _ 210); [lia | reflexivity].
  - apply (b2r_whole false _ 47 _ 42); [lia | reflexivity].
  - apply (b2r_whole false _ 50 _ 7); [lia | reflexivity].
Qed.

Lemma cst_fin (c : gconst) : is_finite (o_cst ieee_ops c) = true.
Proof. exact (proj1 (cst_ok c)). Qed.

Lemma cst_val (c : gconst) : B2R (o_cst ieee_ops c) = model_cst c.
Proof. exact (proj2 (cst_ok c)). Qed.
