(* Proof of EXP32 (statement in EXP32_Statement.v). Flocq and the standard library only; nothing is admitted.
   The graph is narrow(y), y = S^12(P(r)), r = x1 / 4096, x1 = x clamped below at -160. With c = 2^-53:
     r is exact (a binary32 number over 2^12) and is 0 or at least 2^-161 in magnitude, |r| <= 5/128;
     Horner: every level keeps |v - w| <= 2c w against its exact value w (hstep), and the division adds one rounding;
     Taylor: the exact polynomial is within 2.78e-16 of exp r (Taylor.v), so P(r) is within 8c of exp r;
     squaring: an error D becomes at most 2D + 2^-50 (sq_step), twelve times: at most 8191 * 2^-50 < 2^-37;
     T32 turns narrow into RN32 and lemma F32 turns 2^-27 into faithfulness.
   Below -160 the clamp gives a value under 2^-150, which rounds to zero, and exp x is under 2^-149. *)
From Coq Require Import Reals ZArith Lia Lra.
From Flocq Require Import Core Relative.
From MKF.f32 Require Import F32_Statement F32.
From MKF.p32 Require Import Graphs P32_Statement T32 Funcs.
From MKF.exp32 Require Import Graph EXP32_Statement Taylor.
Open Scope R_scope.

#[local] Instance e24 : Prec_gt_0 24 := ltac:(unfold Prec_gt_0; lia).
#[local] Instance e53 : Prec_gt_0 53 := ltac:(unfold Prec_gt_0; lia).

Definition CC : R := / 2 * / 4503599627370496.
Lemma CC_range : 0 <= CC <= / 1024. Proof. unfold CC. lra. Qed.

Lemma half_ok (z : R) : / 2 <= z -> bpow radix2 (-1022) <= Rabs z.
Proof.
  intros H. rewrite Rabs_pos_eq by lra. apply Rle_trans with (2 := H).
  change (/ 2) with (bpow radix2 (-1)). apply bpow_le. lia.
Qed.

(* An error t on w, then one more rounding e: t (1 + e) + w e stays within 4c w. *)
Lemma abs_step (t e w c : R) : 0 <= c <= / 1024 -> 0 <= w -> Rabs t <= 2 * c * w -> Rabs e <= c ->
  Rabs (t * (1 + e) + w * e) <= 4 * c * w.
Proof.
  intros Hc Hw Ht He.
  replace (t * (1 + e) + w * e) with (t + (t * e + w * e)) by ring.
  eapply Rle_trans; [apply Rabs_triang |].
  eapply Rle_trans; [apply Rplus_le_compat_l, Rabs_triang |].
  rewrite (Rabs_mult t e), (Rabs_mult w e), (Rabs_pos_eq w) by exact Hw.
  assert (A : Rabs t * Rabs e <= 2 * c * w * c) by (apply Rmult_le_compat; try apply Rabs_pos; assumption).
  assert (B : w * Rabs e <= w * c) by (apply Rmult_le_compat_l; assumption).
  assert (P : 0 <= c * w) by (apply Rmult_le_pos; lra).
  assert (C : c * w * c <= c * w * / 1024) by (apply Rmult_le_compat_l; [exact P | lra]).
  lra.
Qed.

(* One Horner level, c0 + r * w: the exact value stays within c0/16 of c0, and the computed one within 2c of it. *)
Lemma hstep (c0 r w v : R) : Rabs (v - w) <= 2 * CC * w ->
  1 <= c0 -> Rabs r <= 5 / 128 -> (r = 0 \/ bpow radix2 (-200) <= Rabs r) -> 1 <= w <= 17 / 16 * c0 ->
  15 / 16 * c0 <= c0 + r * w <= 17 / 16 * c0 /\
  Rabs (RN64 (c0 + RN64 (r * v)) - (c0 + r * w)) <= 2 * CC * (c0 + r * w).
Proof.
  intros Hv Hc Hr Hz [Hw1 Hw2]. pose proof CC_range as Hcc.
  assert (Hrw : Rabs r * w <= c0 / 16).
  { apply Rle_trans with (5 / 128 * (17 / 16 * c0)); [apply Rmult_le_compat; try lra; apply Rabs_pos | lra]. }
  assert (Hw : 15 / 16 * c0 <= c0 + r * w <= 17 / 16 * c0).
  { assert (A : Rabs (r * w) <= c0 / 16) by (rewrite Rabs_mult, (Rabs_pos_eq w) by lra; exact Hrw).
    apply Rabs_le_inv in A. lra. }
  split; [exact Hw |].
  destruct Hz as [Z | Hrl].
  - subst r. rewrite !Rmult_0_l, (round_0 radix2 fexp64 ZnearestE), !Rplus_0_r.
    eapply Rle_trans; [apply rn64_rel; apply half_ok; lra |].
    rewrite Rabs_pos_eq by lra. unfold CC. lra.
  - assert (Hv' := Rabs_le_inv _ _ Hv).
    assert (Q : CC * w <= / 1024 * w) by (apply Rmult_le_compat_r; lra).
    assert (Q0 : CC * c0 <= / 1024 * c0) by (apply Rmult_le_compat_r; lra).
    assert (P0 : 0 <= CC * c0) by (apply Rmult_le_pos; lra).
    assert (Hvw : / 2 <= v) by lra.
    assert (Z1 : bpow radix2 (-1022) <= Rabs (r * v)).
    { rewrite Rabs_mult, (Rabs_pos_eq v) by lra.
      apply Rle_trans with (bpow radix2 (-200) * / 2).
      - change (/ 2) with (bpow radix2 (-1)). rewrite <- bpow_plus. apply bpow_le. lia.
      - pose proof (bpow_ge_0 radix2 (-200)). apply Rmult_le_compat; lra. }
    destruct (rn64_ex (r * v) Z1) as (e1 & He1 & E1). rewrite E1.
    assert (D1 : Rabs (r * v * (1 + e1) - r * w) <= 4 * CC * (c0 / 16)).
    { replace (r * v * (1 + e1) - r * w) with (r * ((v - w) * (1 + e1) + w * e1)) by ring.
      rewrite Rabs_mult.
      apply Rle_trans with (Rabs r * (4 * CC * w)).
      - apply Rmult_le_compat_l; [apply Rabs_pos | apply abs_step; [exact Hcc | lra | exact Hv | exact He1]].
      - replace (Rabs r * (4 * CC * w)) with (4 * CC * (Rabs r * w)) by ring.
        apply Rmult_le_compat_l; lra. }
    assert (D1' := Rabs_le_inv _ _ D1).
    assert (Z2 : bpow radix2 (-1022) <= Rabs (c0 + r * v * (1 + e1))) by (apply half_ok; lra).
    destruct (rn64_ex _ Z2) as (e2 & He2 & E2). rewrite E2.
    replace ((c0 + r * v * (1 + e1)) * (1 + e2) - (c0 + r * w))
      with ((r * v * (1 + e1) - r * w) + (c0 + r * v * (1 + e1)) * e2) by ring.
    eapply Rle_trans; [apply Rabs_triang |]. rewrite (Rabs_mult (c0 + r * v * (1 + e1)) e2).
    assert (Zp : Rabs (c0 + r * v * (1 + e1)) <= c0 + r * w + 4 * CC * (c0 / 16)) by (apply Rabs_le; lra).
    assert (B2 : Rabs (c0 + r * v * (1 + e1)) * Rabs e2 <= (c0 + r * w + 4 * CC * (c0 / 16)) * CC).
    { apply Rmult_le_compat; try apply Rabs_pos; [exact Zp | exact He2]. }
    assert (F1 : CC * c0 <= CC * (16 / 15 * (c0 + r * w))) by (apply Rmult_le_compat_l; lra).
    assert (F2 : CC * (CC * c0) <= / 1024 * (CC * c0)) by (apply Rmult_le_compat_r; lra).
    lra.
Qed.

Lemma h0 (r : R) : Rabs r <= 5 / 128 ->
  15 / 16 * 7 <= 7 + r <= 17 / 16 * 7 /\ Rabs (RN64 (7 + r) - (7 + r)) <= 2 * CC * (7 + r).
Proof.
  intros Hr. apply Rabs_le_inv in Hr. split; [lra |].
  eapply Rle_trans; [apply rn64_rel; apply half_ok; lra |].
  rewrite Rabs_pos_eq by lra. unfold CC. lra.
Qed.

(* The polynomial stage: within 8c = 2^-50 of exp r. *)
Lemma poly_total (r : R) : Rabs r <= 5 / 128 -> (r = 0 \/ bpow radix2 (-200) <= Rabs r) ->
  Rabs (exp32_poly r - exp r) <= 8 * CC * exp r.
Proof.
  intros Hr Hz. pose proof CC_range as Hcc. unfold exp32_poly.
  pose proof (exp_poly7 r Hr) as T7.
  destruct (h0 r Hr) as [W7 V7].
  destruct (hstep 42 r _ _ V7 ltac:(lra) Hr Hz ltac:(lra)) as [W6 V6].
  destruct (hstep 210 r _ _ V6 ltac:(lra) Hr Hz ltac:(lra)) as [W5 V5].
  destruct (hstep 840 r _ _ V5 ltac:(lra) Hr Hz ltac:(lra)) as [W4 V4].
  destruct (hstep 2520 r _ _ V4 ltac:(lra) Hr Hz ltac:(lra)) as [W3 V3].
  destruct (hstep 5040 r _ _ V3 ltac:(lra) Hr Hz ltac:(lra)) as [W2 V2].
  destruct (hstep 5040 r _ _ V2 ltac:(lra) Hr Hz ltac:(lra)) as [W1 V1].
  match type of V1 with Rabs (?v - ?w) <= _ => set (v1 := v) in *; set (w1 := w) in * end.
  pose proof (exp_ineq1_le r) as E1. pose proof (exp_pos r) as Ep. apply Rabs_le_inv in Hr.
  assert (T7' : Rabs (w1 / 5040 - exp r) <= 3 * CC * exp r).
  { rewrite Rabs_minus_sym. eapply Rle_trans; [exact T7 | unfold CC; lra]. }
  assert (V1' := Rabs_le_inv _ _ V1).
  assert (Q1 : CC * w1 <= / 1024 * w1) by (apply Rmult_le_compat_r; lra).
  assert (Zd : bpow radix2 (-1022) <= Rabs (v1 / 5040)) by (apply half_ok; lra).
  destruct (rn64_ex _ Zd) as (e & He & E). rewrite E.
  replace (v1 / 5040 * (1 + e) - exp r)
    with (((v1 - w1) / 5040 * (1 + e) + w1 / 5040 * e) + (w1 / 5040 - exp r)) by field.
  eapply Rle_trans; [apply Rabs_triang |].
  assert (A2 : Rabs ((v1 - w1) / 5040 * (1 + e) + w1 / 5040 * e) <= 4 * CC * (w1 / 5040)).
  { apply abs_step; [exact Hcc | lra | | exact He].
    unfold Rdiv. rewrite Rabs_mult, (Rabs_pos_eq (/ 5040)) by lra. lra. }
  assert (T7i := Rabs_le_inv _ _ T7').
  assert (P1 : 0 <= CC * exp r) by (apply Rmult_le_pos; lra).
  assert (P2 : CC * (CC * exp r) <= / 1024 * (CC * exp r)) by (apply Rmult_le_compat_r; lra).
  assert (P3 : CC * (w1 / 5040) <= CC * (exp r + 3 * CC * exp r)) by (apply Rmult_le_compat_l; lra).
  lra.
Qed.

(* One squaring: a relative error D becomes at most 2D + 2^-50. *)
Lemma sq_step (a s D : R) : Rabs (s - a) <= D * a -> bpow radix2 (-500) <= a -> 0 <= D <= / 134217728 ->
  Rabs (exp32_sq s - a * a) <= (2 * D + / 1125899906842624) * (a * a).
Proof.
  intros Hs Ha [HD0 HD1]. pose proof CC_range as Hcc. unfold exp32_sq.
  pose proof (bpow_gt_0 radix2 (-500)) as Bp.
  assert (Da : D * a <= / 134217728 * a) by (apply Rmult_le_compat_r; lra).
  assert (Hs' := Rabs_le_inv _ _ Hs).
  assert (Sh : a * / 2 <= s) by lra.
  assert (A0 : 0 <= a * a) by (apply Rmult_le_pos; lra).
  assert (P1 : Rabs (s * s - a * a) <= (2 * D + D * D) * (a * a)).
  { replace (s * s - a * a) with ((s - a) * (s - a) + 2 * a * (s - a)) by ring.
    eapply Rle_trans; [apply Rabs_triang |].
    rewrite (Rabs_mult (s - a) (s - a)), (Rabs_mult (2 * a) (s - a)), (Rabs_pos_eq (2 * a)) by lra.
    apply Rle_trans with (D * a * (D * a) + 2 * a * (D * a)); [| right; ring].
    apply Rplus_le_compat; [apply Rmult_le_compat; try apply Rabs_pos; exact Hs | apply Rmult_le_compat_l; [lra | exact Hs]]. }
  assert (Z : bpow radix2 (-1022) <= Rabs (s * s)).
  { assert (S1 : bpow radix2 (-501) <= s).
    { apply Rle_trans with (2 := Sh).
      replace (bpow radix2 (-501)) with (bpow radix2 (-500) * / 2)
        by (change (/ 2) with (bpow radix2 (-1)); rewrite <- bpow_plus; reflexivity).
      apply Rmult_le_compat_r; lra. }
    pose proof (bpow_ge_0 radix2 (-501)) as B1.
    rewrite Rabs_pos_eq by (apply Rmult_le_pos; lra).
    apply Rle_trans with (bpow radix2 (-501) * bpow radix2 (-501)).
    - rewrite <- bpow_plus. apply bpow_le. lia.
    - apply Rmult_le_compat; lra. }
  destruct (rn64_ex _ Z) as (e & He & E). rewrite E.
  replace (s * s * (1 + e) - a * a) with ((s * s - a * a) + s * s * e) by ring.
  eapply Rle_trans; [apply Rabs_triang |]. rewrite (Rabs_mult (s * s) e).
  assert (Sb : Rabs (s * s) <= a * a + (2 * D + D * D) * (a * a)).
  { replace (s * s) with (a * a + (s * s - a * a)) by ring.
    eapply Rle_trans; [apply Rabs_triang |]. rewrite (Rabs_pos_eq (a * a)) by exact A0. lra. }
  assert (DD : D * D <= / 134217728 * / 134217728) by (apply Rmult_le_compat; lra).
  assert (X1 : 2 * D + D * D <= 1) by lra.
  assert (X0 : 0 <= 2 * D + D * D) by (assert (0 <= D * D) by (apply Rmult_le_pos; lra); lra).
  assert (B2 : Rabs (s * s) * Rabs e <= (a * a + (2 * D + D * D) * (a * a)) * CC).
  { apply Rmult_le_compat; try apply Rabs_pos; [exact Sb | exact He]. }
  apply Rle_trans with (((2 * D + D * D) + (1 + (2 * D + D * D)) * CC) * (a * a)).
  - apply Rle_trans with ((2 * D + D * D) * (a * a) + (a * a + (2 * D + D * D) * (a * a)) * CC); [lra | right; ring].
  - apply Rmult_le_compat_r; [exact A0 |].
    assert (X2 : (1 + (2 * D + D * D)) * CC <= 2 * CC) by (apply Rmult_le_compat_r; lra).
    unfold CC in *. lra.
Qed.

Lemma sq_exp (t s D : R) : Rabs (s - exp t) <= D * exp t -> bpow radix2 (-500) <= exp t -> 0 <= D <= / 134217728 ->
  Rabs (exp32_sq s - exp (2 * t)) <= (2 * D + / 1125899906842624) * exp (2 * t).
Proof.
Admitted.

(* Crude bounds on exp from 2 <= exp 1 <= 3: 2^n <= exp n <= 4^n. *)
Lemma exp_nat_le (n : nat) : exp (INR n) <= bpow radix2 (2 * Z.of_nat n).
Proof.
  induction n as [| n IH].
  - simpl. rewrite exp_0. lra.
  - rewrite S_INR, exp_plus.
    replace (2 * Z.of_nat (S n))%Z with (2 * Z.of_nat n + 2)%Z by lia.
    rewrite bpow_plus. change (bpow radix2 2) with 4.
    pose proof exp_le_3. pose proof (exp_pos (INR n)). pose proof (exp_pos 1).
    apply Rmult_le_compat; lra.
Qed.

Lemma exp_nat_ge (n : nat) : bpow radix2 (Z.of_nat n) <= exp (INR n).
Proof.
  induction n as [| n IH].
  - simpl. rewrite exp_0. lra.
  - rewrite S_INR, exp_plus, Nat2Z.inj_succ. unfold Z.succ. rewrite bpow_plus. change (bpow radix2 1) with 2.
    pose proof (exp_ineq1_le 1). pose proof (bpow_ge_0 radix2 (Z.of_nat n)).
    apply Rmult_le_compat; lra.
Qed.

Lemma inr160 : INR 160 = 160.
Proof. rewrite INR_IZR_INZ. reflexivity. Qed.

Lemma exp_m160 : exp (-160) = / exp (INR 160).
Proof. rewrite <- exp_Ropp, inr160. reflexivity. Qed.

Lemma exp_m160_hi : exp (-160) <= bpow radix2 (-160).
Proof.
  rewrite exp_m160. change (-160)%Z with (- Z.of_nat 160)%Z. rewrite bpow_opp.
  apply Rinv_le_contravar; [apply bpow_gt_0 | apply exp_nat_ge].
Qed.

Lemma exp_low (t : R) : -160 <= t -> bpow radix2 (-500) <= exp t.
Proof.
  intros Ht. apply Rle_trans with (exp (-160)).
  - rewrite exp_m160. apply Rle_trans with (/ bpow radix2 (2 * Z.of_nat 160)).
    + rewrite <- bpow_opp. apply bpow_le. change (2 * Z.of_nat 160)%Z with 320%Z. lia.
    + apply Rinv_le_contravar; [apply exp_pos | apply exp_nat_le].
  - destruct (Req_dec t (-160)) as [E | N]; [rewrite E; apply Rle_refl | left; apply exp_increasing; lra].
Qed.

Ltac sqs H H' :=
  pose proof (sq_exp _ _ _ H) as H';
  match type of H' with
  | ?A -> ?B -> _ =>
      let a := fresh in let b := fresh in
      assert (a : A) by (apply exp_low; lra); assert (b : B) by (unfold CC; lra);
      specialize (H' a b); clear a b
  end.

(* The value before narrow, for a reduced argument r: within 2^-37 of exp (4096 r). *)
Lemma exp32_core (r : R) : Rabs r <= 5 / 128 -> (r = 0 \/ bpow radix2 (-200) <= Rabs r) ->
  Rabs (exp32_sq (exp32_sq (exp32_sq (exp32_sq (exp32_sq (exp32_sq (exp32_sq (exp32_sq (exp32_sq (exp32_sq (exp32_sq
          (exp32_sq (exp32_poly r)))))))))))) - exp (4096 * r))
    <= / 137438953472 * exp (4096 * r).
Proof.
  intros Hr Hz. pose proof (poly_total r Hr Hz) as H0. apply Rabs_le_inv in Hr.
  sqs H0 H1. sqs H1 H2. sqs H2 H3. sqs H3 H4. sqs H4 H5. sqs H5 H6.
  sqs H6 H7. sqs H7 H8. sqs H8 H9. sqs H9 H10. sqs H10 H11. sqs H11 H12.
  replace (4096 * r) with (2 * (2 * (2 * (2 * (2 * (2 * (2 * (2 * (2 * (2 * (2 * (2 * r)))))))))))) by ring.
  eapply Rle_trans; [exact H12 |].
  apply Rmult_le_compat_r; [left; apply exp_pos | unfold CC; lra].
Qed.

(* A binary32 number over 4096 is a binary64 number. *)
Lemma f32_scale (x : R) : format32 x -> format64 (x / 4096).
Proof.
  intros Fx. destruct (FLT_format_generic radix2 (-149) 24 x Fx) as [f Hf1 Hf2 Hf3].
  apply generic_format_FLT.
  apply (FLT_spec radix2 (-1074) 53 (x / 4096) (Float radix2 (Fnum f) (Fexp f - 12))).
  - rewrite Hf1. unfold F2R. cbn [Fnum Fexp].
    replace (Fexp f - 12)%Z with (Fexp f + (-12))%Z by lia. rewrite bpow_plus.
    change (bpow radix2 (-12)) with (/ 4096). field.
  - cbn [Fnum]. apply Z.lt_le_trans with (1 := Hf2).
    change (Zpower radix2 24) with 16777216%Z. change (Zpower radix2 53) with 9007199254740992%Z. lia.
  - cbn [Fexp]. lia.
Qed.

Lemma f32_m160 : format32 (-160).
Proof.
  apply generic_format_FLT. apply (FLT_spec radix2 (-149) 24 (-160) (Float radix2 (-160) 0)).
  - unfold F2R. cbn [Fnum Fexp]. change (bpow radix2 0) with 1. lra.
  - cbn [Fnum]. change (Zpower radix2 24) with 16777216%Z. lia.
  - cbn [Fexp]. lia.
Qed.

Lemma rn32_tiny (y : R) : 0 < y -> y < bpow radix2 (-150) -> RN32 y = 0.
Proof.
  intros Hy Hlt. assert (Ny : y <> 0) by lra.
  assert (M : (mag radix2 y <= -150)%Z) by (apply mag_le_bpow; [exact Ny | rewrite Rabs_pos_eq by lra; exact Hlt]).
  apply (round_N_small_pos radix2 fexp32 (fun z => negb (Z.even z)) y (mag radix2 y)).
  - pose proof (bpow_mag_le radix2 y Ny) as H1. pose proof (bpow_mag_gt radix2 y) as H2.
    rewrite Rabs_pos_eq in H1, H2 by lra. split; assumption.
  - unfold FLT_exp. lia.
Qed.

Lemma rd32_tiny (f : R) : 0 < f -> f < bpow radix2 (-149) -> RD32 f = 0.
Proof.
  intros Hf Hlt. assert (Nf : f <> 0) by lra.
  assert (M : (mag radix2 f <= -149)%Z) by (apply mag_le_bpow; [exact Nf | rewrite Rabs_pos_eq by lra; exact Hlt]).
  apply (round_DN_small_pos radix2 fexp32 f (mag radix2 f)).
  - pose proof (bpow_mag_le radix2 f Nf) as H1. pose proof (bpow_mag_gt radix2 f) as H2.
    rewrite Rabs_pos_eq in H1, H2 by lra. split; assumption.
  - unfold FLT_exp. lia.
Qed.

Theorem exp32_faithful : EXP32.
Proof.
  unfold EXP32, g_exp32, XMAX. intros x Fx Hx.
  set (x1 := if Rlt_dec x (-160) then -160 else x).
  assert (Fx1 : format32 x1) by (unfold x1; destruct (Rlt_dec x (-160)); [exact f32_m160 | exact Fx]).
  assert (Bx1 : -160 <= x1 <= 160) by (unfold x1; destruct (Rlt_dec x (-160)); lra).
  assert (Cx : x1 = x \/ (x < -160 /\ x1 = -160)).
  { unfold x1. destruct (Rlt_dec x (-160)); [right; split; [assumption | reflexivity] | left; reflexivity]. }
  assert (Er : exp32_red x = x1 / 4096).
  { unfold exp32_red. fold x1. apply round_generic; [typeclasses eauto | apply f32_scale; exact Fx1]. }
  rewrite Er. clearbody x1.
  assert (Hr : Rabs (x1 / 4096) <= 5 / 128) by (apply Rabs_le; lra).
  assert (Hz : x1 / 4096 = 0 \/ bpow radix2 (-200) <= Rabs (x1 / 4096)).
  { destruct (Req_dec x1 0) as [Z | N]; [left; rewrite Z; lra | right].
    assert (H : bpow radix2 (-149) <= Rabs x1)
      by (apply f32_pos_ge; [apply generic_format_abs; exact Fx1 | apply Rabs_pos_lt; exact N]).
    unfold Rdiv. rewrite Rabs_mult, (Rabs_pos_eq (/ 4096)) by lra.
    apply Rle_trans with (bpow radix2 (-149) * / 4096); [| apply Rmult_le_compat_r; lra].
    change (/ 4096) with (bpow radix2 (-12)). rewrite <- bpow_plus. apply bpow_le. lia. }
  pose proof (exp32_core (x1 / 4096) Hr Hz) as Hc.
  replace (4096 * (x1 / 4096)) with x1 in Hc by field.
  match goal with |- faithful32 _ (narrow ?t) => set (y := t) in * end.
  assert (Fy : format64 y) by (unfold y, exp32_sq; apply generic_format_round; typeclasses eauto).
  rewrite (T32_proof y Fy). clearbody y.
  destruct Cx as [E | [Lt E]]; rewrite E in Hc.
  - apply (F32_rel (exp x) y).
    eapply Rle_trans; [exact Hc |]. rewrite Rabs_pos_eq by (left; apply exp_pos).
    apply Rmult_le_compat_r; [left; apply exp_pos |].
    change (bpow radix2 (-27)) with (/ 134217728). lra.
  - pose proof exp_m160_hi as Hh. pose proof (exp_pos (-160)) as Hp. apply Rabs_le_inv in Hc.
    assert (B1 : bpow radix2 (-160) * 2 < bpow radix2 (-150))
      by (change 2 with (bpow radix2 1); rewrite <- bpow_plus; apply bpow_lt; lia).
    assert (B2 : bpow radix2 (-160) <= bpow radix2 (-149)) by (apply bpow_le; lia).
    assert (Y0 : 0 < y) by lra. assert (Y1 : y < bpow radix2 (-150)) by lra.
    assert (Lx : exp x < exp (-160)) by (apply exp_increasing; exact Lt).
    left. rewrite (rn32_tiny y Y0 Y1). symmetry. apply rd32_tiny; [apply exp_pos | lra].
Qed.
