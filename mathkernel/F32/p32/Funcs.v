(* Proofs of SQRT32 and RSQRT32 (statements in P32_Statement.v). Flocq only; nothing is admitted.
   Pattern: the graph is narrow(y) with y a binary64 value; T32 turns narrow into RN32; each binary64 rounding of a
   value of magnitude at least 2^-1022 is within 2^-53 relative (Flocq's relative_error_N_FLT); lemma F32 turns a
   relative error of at most 2^-27 into faithfulness. *)
From Coq Require Import Reals ZArith Lia Lra Psatz.
From Flocq Require Import Core Relative.
From MKF.f32 Require Import F32_Statement F32.
From MKF.p32 Require Import Graphs P32_Statement T32.
Open Scope R_scope.

#[local] Instance q24 : Prec_gt_0 24 := ltac:(unfold Prec_gt_0; lia).
#[local] Instance q53 : Prec_gt_0 53 := ltac:(unfold Prec_gt_0; lia).

(* One binary64 rounding, away from the subnormals: RN64 z = z (1 + e), |e| <= 2^-53. *)
Lemma rn64_ex (z : R) : bpow radix2 (-1022) <= Rabs z ->
  exists e : R, Rabs e <= / 2 * / 4503599627370496 /\ RN64 z = z * (1 + e).
Proof. intros H. exact (relative_error_N_FLT_ex radix2 (-1074) 53 ltac:(lia) (fun z => negb (Z.even z)) z H). Qed.

Lemma rn64_rel (z : R) : bpow radix2 (-1022) <= Rabs z -> Rabs (RN64 z - z) <= / 2 * / 4503599627370496 * Rabs z.
Proof. intros H. exact (relative_error_N_FLT radix2 (-1074) 53 ltac:(lia) (fun z => negb (Z.even z)) z H). Qed.

Lemma f32_pos_ge (x : R) : format32 x -> 0 < x -> bpow radix2 (-149) <= x.
Proof.
  intros Fx Hx. apply (generic_format_ge_bpow radix2 fexp32 (-149)); [intros e; unfold FLT_exp; lia | exact Hx | exact Fx].
Qed.

Lemma sqrt_ge_bpow (x : R) : bpow radix2 (-2044) <= x -> bpow radix2 (-1022) <= sqrt x.
Proof.
  intros H. rewrite <- (sqrt_square (bpow radix2 (-1022))) by apply bpow_ge_0.
  apply sqrt_le_1_alt. rewrite <- bpow_plus. exact H.
Qed.

Theorem sqrt32_faithful : SQRT32.
Proof.
  unfold SQRT32, g_sqrt32. intros x Fx Hx.
  assert (Fy : format64 (RN64 (sqrt x))) by (apply generic_format_round; typeclasses eauto).
  rewrite (T32_proof _ Fy).
  apply (F32_rel (sqrt x) (RN64 (sqrt x))).
  destruct (Req_dec x 0) as [Z0 | Nz].
  - subst x. rewrite sqrt_0, (round_0 radix2 fexp64 ZnearestE), Rminus_0_r, Rabs_R0. lra.
  - assert (H149 : bpow radix2 (-149) <= x) by (apply f32_pos_ge; [exact Fx | lra]).
    assert (Hs : bpow radix2 (-1022) <= sqrt x).
    { apply sqrt_ge_bpow. apply Rle_trans with (2 := H149). apply bpow_le. lia. }
    eapply Rle_trans; [apply rn64_rel; rewrite Rabs_pos_eq by apply sqrt_pos; exact Hs |].
    apply Rmult_le_compat_r; [apply Rabs_pos |].
    change (bpow radix2 (-27)) with (/ 134217728). lra.
Qed.

(* (1 + e2) / (1 + e1) is within 4c of 1 when both errors are within c. *)
Lemma quot_bound (e1 e2 c : R) : 0 <= c <= / 8 -> Rabs e1 <= c -> Rabs e2 <= c ->
  Rabs ((1 + e2) / (1 + e1) - 1) <= 4 * c.
Proof.
  intros Hc H1 H2. apply Rabs_le_inv in H1. apply Rabs_le_inv in H2.
  assert (P : 0 < 1 + e1) by lra.
  replace ((1 + e2) / (1 + e1) - 1) with ((e2 - e1) / (1 + e1)) by (field; lra).
  assert (G : 4 * c * (1 + e1) >= 4 * c * (7 / 8)) by nra.
  apply Rabs_le. split.
  - apply Rmult_le_reg_r with (1 + e1); [exact P |].
    unfold Rdiv. rewrite Rmult_assoc, Rinv_l by lra. lra.
  - apply Rmult_le_reg_r with (1 + e1); [exact P |].
    unfold Rdiv. rewrite Rmult_assoc, Rinv_l by lra. lra.
Qed.

Theorem rsqrt32_faithful : RSQRT32.
Proof.
  unfold RSQRT32, g_rsqrt32. intros x Fx Hx Hlt.
  assert (Fy : format64 (RN64 (1 / RN64 (sqrt x)))) by (apply generic_format_round; typeclasses eauto).
  rewrite (T32_proof _ Fy).
  apply (F32_rel (/ sqrt x) (RN64 (1 / RN64 (sqrt x)))).
  assert (H149 : bpow radix2 (-149) <= x) by (apply f32_pos_ge; assumption).
  assert (Hs : bpow radix2 (-1022) <= sqrt x).
  { apply sqrt_ge_bpow. apply Rle_trans with (2 := H149). apply bpow_le. lia. }
  assert (Sp : 0 < sqrt x) by (pose proof (bpow_gt_0 radix2 (-1022)); lra).
  assert (Sh : sqrt x < bpow radix2 64).
  { rewrite <- (sqrt_square (bpow radix2 64)) by apply bpow_ge_0.
    apply sqrt_lt_1_alt. split; [lra |]. rewrite <- bpow_plus. exact Hlt. }
  destruct (rn64_ex (sqrt x)) as (e1 & He1 & E1); [rewrite Rabs_pos_eq by lra; exact Hs |].
  assert (C : / 2 * / 4503599627370496 <= / 8) by lra.
  pose proof (Rabs_le_inv _ _ He1) as B1.
  assert (S1p : 0 < sqrt x * (1 + e1)) by (apply Rmult_lt_0_compat; lra).
  assert (S1h : sqrt x * (1 + e1) <= bpow radix2 65).
  { replace (bpow radix2 65) with (bpow radix2 64 * 2)
      by (change 2 with (bpow radix2 1); rewrite <- bpow_plus; reflexivity).
    apply Rmult_le_compat; lra. }
  assert (Hq : bpow radix2 (-1022) <= Rabs (1 / (sqrt x * (1 + e1)))).
  { rewrite Rabs_pos_eq by (apply Rlt_le, Rdiv_lt_0_compat; lra).
    apply Rle_trans with (/ bpow radix2 65).
    - rewrite <- bpow_opp. apply bpow_le. lia.
    - unfold Rdiv. rewrite Rmult_1_l. apply Rinv_le_contravar; assumption. }
  rewrite E1.
  destruct (rn64_ex (1 / (sqrt x * (1 + e1))) Hq) as (e2 & He2 & E2).
  rewrite E2.
  replace (1 / (sqrt x * (1 + e1)) * (1 + e2) - / sqrt x) with (/ sqrt x * ((1 + e2) / (1 + e1) - 1)) by (field; lra).
  rewrite Rabs_mult, Rmult_comm.
  apply Rmult_le_compat_r; [apply Rabs_pos |].
  eapply Rle_trans; [apply (quot_bound e1 e2 (/ 2 * / 4503599627370496)); [lra | exact He1 | exact He2] |].
  change (bpow radix2 (-27)) with (/ 134217728). lra.
Qed.
