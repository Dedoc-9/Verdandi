(* Proof of HYPOT32 (statement in P32_Statement.v). Flocq only; nothing is admitted.
   The graph: R = RN(sqrt(RN(RN(x*x) + RN(y*y)))). A square of a binary32 number is 0 or at least 2^-298, so every
   rounding is away from binary64's subnormals and carries a relative error of at most c = 2^-53:
     RN(x*x) + RN(y*y) lies within (1 -+ c) of t = x*x + y*y;  the rounded sum within (1 -+ c)^2;
     its square root within (1 -+ c) of sqrt t;  the rounded root within (1 -+ c)^2, so within 3c <= 2^-27. *)
From Coq Require Import Reals ZArith Lia Lra Psatz.
From Flocq Require Import Core Relative.
From MKF.f32 Require Import F32_Statement F32.
From MKF.p32 Require Import Graphs P32_Statement T32 Funcs.
Open Scope R_scope.

#[local] Instance r24 : Prec_gt_0 24 := ltac:(unfold Prec_gt_0; lia).
#[local] Instance r53 : Prec_gt_0 53 := ltac:(unfold Prec_gt_0; lia).

Definition C53 : R := / 2 * / 4503599627370496.
Lemma C53_range : 0 <= C53 <= / 1024. Proof. unfold C53. lra. Qed.

Lemma sq_ge (x : R) : format32 x -> x <> 0 -> bpow radix2 (-298) <= x * x.
Proof.
  intros Fx Nz.
  assert (H : bpow radix2 (-149) <= Rabs x)
    by (apply f32_pos_ge; [apply generic_format_abs; exact Fx | apply Rabs_pos_lt; exact Nz]).
  replace (x * x) with (Rabs x * Rabs x) by (rewrite <- Rabs_mult; apply Rabs_pos_eq; nra).
  change (-298)%Z with (-149 + -149)%Z. rewrite bpow_plus.
  apply Rmult_le_compat; try apply bpow_ge_0; exact H.
Qed.

Lemma sq_ex (x : R) : format32 x -> exists e : R, Rabs e <= C53 /\ RN64 (x * x) = x * x * (1 + e).
Proof.
  intros Fx. destruct (Req_dec x 0) as [Z0 | Nz].
  - exists 0. split; [rewrite Rabs_R0; apply C53_range |].
    subst x. rewrite Rmult_0_l, (round_0 radix2 fexp64 ZnearestE). ring.
  - unfold C53. apply rn64_ex. pose proof (sq_ge x Fx Nz) as H. rewrite Rabs_pos_eq by nra.
    apply Rle_trans with (2 := H). apply bpow_le. lia.
Qed.

Lemma m_bounds (a b e1 e2 c : R) : 0 <= a -> 0 <= b -> Rabs e1 <= c -> Rabs e2 <= c ->
  (a + b) * (1 - c) <= a * (1 + e1) + b * (1 + e2) <= (a + b) * (1 + c).
Proof.
  intros Ha Hb H1 H2. apply Rabs_le_inv in H1. apply Rabs_le_inv in H2.
  assert (A1 : a * e1 <= a * c) by (apply Rmult_le_compat_l; lra).
  assert (A2 : a * - c <= a * e1) by (apply Rmult_le_compat_l; lra).
  assert (B1 : b * e2 <= b * c) by (apply Rmult_le_compat_l; lra).
  assert (B2 : b * - c <= b * e2) by (apply Rmult_le_compat_l; lra).
  split; lra.
Qed.

Lemma s_bounds (t m e3 c : R) : 0 <= t -> 0 <= c <= / 1024 -> t * (1 - c) <= m <= t * (1 + c) -> Rabs e3 <= c ->
  t * (1 - c) * (1 - c) <= m * (1 + e3) <= t * (1 + c) * (1 + c).
Proof.
  intros Ht Hc Hm H3. apply Rabs_le_inv in H3.
  assert (M0 : 0 <= m) by (apply Rle_trans with (2 := proj1 Hm); apply Rmult_le_pos; lra).
  split.
  - apply Rle_trans with (m * (1 - c)); [apply Rmult_le_compat_r; lra | apply Rmult_le_compat_l; lra].
  - apply Rle_trans with (m * (1 + c)); [apply Rmult_le_compat_l; lra | apply Rmult_le_compat_r; lra].
Qed.

Lemma sqrt_bounds (t s c : R) : 0 <= t -> 0 <= c <= / 1024 ->
  t * (1 - c) * (1 - c) <= s <= t * (1 + c) * (1 + c) -> sqrt t * (1 - c) <= sqrt s <= sqrt t * (1 + c).
Proof.
  intros Ht Hc Hs. split.
  - rewrite <- (sqrt_square (1 - c)) by lra. rewrite <- sqrt_mult; [| exact Ht | nra].
    apply sqrt_le_1_alt. rewrite <- Rmult_assoc. exact (proj1 Hs).
  - rewrite <- (sqrt_square (1 + c)) by lra. rewrite <- sqrt_mult; [| exact Ht | nra].
    apply sqrt_le_1_alt. rewrite <- Rmult_assoc. exact (proj2 Hs).
Qed.

Lemma hyp_core (f sS e4 c : R) : 0 <= f -> 0 <= c <= / 1024 -> f * (1 - c) <= sS <= f * (1 + c) -> Rabs e4 <= c ->
  Rabs (sS * (1 + e4) - f) <= 3 * c * f.
Proof.
  intros Hf Hc Hs H4. apply Rabs_le_inv in H4.
  assert (S0 : 0 <= sS) by (apply Rle_trans with (2 := proj1 Hs); apply Rmult_le_pos; lra).
  assert (U1 : sS * (1 + e4) <= f * (1 + c) * (1 + c)) by (apply Rmult_le_compat; lra).
  assert (L1 : f * (1 - c) * (1 - c) <= sS * (1 + e4)).
  { apply Rmult_le_compat; try lra. apply Rmult_le_pos; lra. }
  assert (P1 : 0 <= f * c) by (apply Rmult_le_pos; lra).
  assert (P2 : 0 <= f * c * c) by (apply Rmult_le_pos; lra).
  assert (Q : f * c * c <= f * c * 1) by (apply Rmult_le_compat_l; lra).
  apply Rabs_le. split; lra.
Qed.

Lemma hyp_main (a b e1 e2 : R) : 0 <= a -> 0 <= b -> bpow radix2 (-298) <= a + b ->
  Rabs e1 <= C53 -> Rabs e2 <= C53 ->
  Rabs (RN64 (sqrt (RN64 (a * (1 + e1) + b * (1 + e2)))) - sqrt (a + b))
    <= bpow radix2 (-27) * Rabs (sqrt (a + b)).
Proof.
  intros Ha Hb HB H1 H2. pose proof C53_range as Hc. pose proof (bpow_gt_0 radix2 (-298)) as Bp.
  set (t := a + b) in *. set (m := a * (1 + e1) + b * (1 + e2)).
  assert (Ht : 0 <= t) by lra.
  assert (Hm : t * (1 - C53) <= m <= t * (1 + C53)) by exact (m_bounds a b e1 e2 C53 Ha Hb H1 H2).
  assert (Tiny1 : bpow radix2 (-1022) <= bpow radix2 (-298) * / 2 * / 2)
    by (change (/ 2) with (bpow radix2 (-1)); rewrite <- !bpow_plus; apply bpow_le; lia).
  assert (Tiny2 : bpow radix2 (-2044) <= bpow radix2 (-298) * / 2 * / 2)
    by (change (/ 2) with (bpow radix2 (-1)); rewrite <- !bpow_plus; apply bpow_le; lia).
  assert (Mlo : bpow radix2 (-298) * / 2 <= m).
  { apply Rle_trans with (2 := proj1 Hm). apply Rmult_le_compat; lra. }
  destruct (rn64_ex m) as (e3 & He3 & E3); [rewrite Rabs_pos_eq by lra; lra |].
  rewrite E3.
  assert (Hs : t * (1 - C53) * (1 - C53) <= m * (1 + e3) <= t * (1 + C53) * (1 + C53))
    by exact (s_bounds t m e3 C53 Ht Hc Hm He3).
  assert (Slo : bpow radix2 (-298) * / 2 * / 2 <= m * (1 + e3)).
  { apply Rabs_le_inv in He3. apply Rmult_le_compat; lra. }
  set (s := m * (1 + e3)) in *.
  assert (Hss : bpow radix2 (-1022) <= sqrt s) by (apply sqrt_ge_bpow; lra).
  destruct (rn64_ex (sqrt s)) as (e4 & He4 & E4); [rewrite Rabs_pos_eq by apply sqrt_pos; exact Hss |].
  rewrite E4.
  pose proof (sqrt_bounds t s C53 Ht Hc Hs) as Hq.
  assert (Fp : 0 <= sqrt t) by apply sqrt_pos.
  rewrite (Rabs_pos_eq (sqrt t)) by exact Fp.
  eapply Rle_trans; [apply (hyp_core (sqrt t) (sqrt s) e4 C53 Fp Hc Hq He4) |].
  apply Rmult_le_compat_r; [exact Fp |].
  change (bpow radix2 (-27)) with (/ 134217728). unfold C53. lra.
Qed.

Theorem hypot32_faithful : HYPOT32.
Proof.
  unfold HYPOT32, g_hypot32. intros x y Fx Fy _ _.
  assert (Fr : format64 (RN64 (sqrt (RN64 (RN64 (x * x) + RN64 (y * y))))))
    by (apply generic_format_round; typeclasses eauto).
  rewrite (T32_proof _ Fr).
  apply (F32_rel (sqrt (x * x + y * y)) (RN64 (sqrt (RN64 (RN64 (x * x) + RN64 (y * y)))))).
  destruct (sq_ex x Fx) as (e1 & He1 & E1). destruct (sq_ex y Fy) as (e2 & He2 & E2).
  rewrite E1, E2.
  assert (Ha : 0 <= x * x) by nra. assert (Hb : 0 <= y * y) by nra.
  destruct (Req_dec (x * x + y * y) 0) as [Z | NZ].
  - assert (Ea : x * x = 0) by lra. assert (Eb : y * y = 0) by lra. rewrite Ea, Eb.
    replace (0 * (1 + e1) + 0 * (1 + e2)) with 0 by ring.
    rewrite Rplus_0_r, (round_0 radix2 fexp64 ZnearestE), sqrt_0, (round_0 radix2 fexp64 ZnearestE), Rminus_0_r, Rabs_R0.
    lra.
  - destruct (Req_dec x 0) as [Zx | Nx].
    + assert (Ny : y <> 0) by (intros Zy; apply NZ; rewrite Zx, Zy; ring).
      pose proof (sq_ge y Fy Ny). apply hyp_main; try assumption; lra.
    + pose proof (sq_ge x Fx Nx). apply hyp_main; try assumption; lra.
Qed.
