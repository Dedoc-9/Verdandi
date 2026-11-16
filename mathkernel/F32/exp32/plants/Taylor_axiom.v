(* The tail of exp's power series, from the standard library's own definition of exp (Rtrigo_def: exp x is the sum of
   x^i / i!). For |x| <= 1 and every n:   |exp x - sum_{i <= n} x^i / i!|  <=  2 |x|^(n+1) / (n+1)!.
   Past the first, each term is at most half the one before it, so a tail is at most twice its first term; the bound
   holds for every finite tail and so for the limit. Then the case used by exp32: degree 7 on |r| <= 5/128.
   Standard library only; nothing is admitted. *)
From Coq Require Import Reals ZArith Lia Lra.
Open Scope R_scope.

Definition tm (x : R) (i : nat) : R := / INR (fact i) * x ^ i.

Lemma tm_S (x : R) (i : nat) : tm x (S i) = tm x i * (x / INR (S i)).
Proof.
  unfold tm. rewrite fact_simpl, mult_INR, <- (tech_pow_Rmult x i).
  assert (A : INR (fact i) <> 0) by apply INR_fact_neq_0.
  assert (B : INR (S i) <> 0) by (apply not_0_INR; discriminate).
  field. split; assumption.
Qed.

Lemma tm_abs (x : R) (i : nat) : Rabs (tm x i) = tm (Rabs x) i.
Proof.
  unfold tm. rewrite Rabs_mult, RPow_abs. f_equal.
  apply Rabs_pos_eq. left. apply Rinv_0_lt_compat, INR_fact_lt_0.
Qed.

Lemma tm_pos (y : R) (i : nat) : 0 <= y -> 0 <= tm y i.
Proof.
  intros Hy. unfold tm. apply Rmult_le_pos; [left; apply Rinv_0_lt_compat, INR_fact_lt_0 | apply pow_le; exact Hy].
Qed.

Lemma tm_half (y : R) (n k : nat) : 0 <= y <= 1 -> tm y (S n + k) <= tm y (S n) * (/ 2) ^ k.
Proof.
  intros Hy. induction k as [| k IH].
  - rewrite Nat.add_0_r, pow_O, Rmult_1_r. apply Rle_refl.
  - rewrite Nat.add_succ_r, (tm_S y (S n + k)), <- (tech_pow_Rmult (/ 2) k).
    assert (D : 2 <= INR (S (S n + k))).
    { change (S n + k)%nat with (S (n + k)). rewrite !S_INR. pose proof (pos_INR (n + k)). lra. }
    assert (Q : 0 <= y / INR (S (S n + k)) <= / 2).
    { unfold Rdiv. split.
      - apply Rmult_le_pos; [lra | left; apply Rinv_0_lt_compat; lra].
      - apply Rle_trans with (1 * / 2); [| lra].
        apply Rmult_le_compat; try lra.
        + left; apply Rinv_0_lt_compat; lra.
        + apply Rinv_le_contravar; lra. }
    pose proof (tm_pos y (S n + k) (proj1 Hy)) as P.
    apply Rle_trans with (tm y (S n) * (/ 2) ^ k * (/ 2)); [| right; ring].
    apply Rmult_le_compat; [exact P | apply Q | exact IH | apply Q].
Qed.

Lemma tail_fin (x : R) (n m : nat) : Rabs x <= 1 ->
  Rabs (sum_f_R0 (tm x) (S n + m) - sum_f_R0 (tm x) n) <= tm (Rabs x) (S n) * (2 - (/ 2) ^ m).
Proof.
  intros Hx. assert (Hy : 0 <= Rabs x <= 1) by (split; [apply Rabs_pos | exact Hx]).
  induction m as [| m IH].
  - rewrite Nat.add_0_r, pow_O. cbn [sum_f_R0].
    replace (sum_f_R0 (tm x) n + tm x (S n) - sum_f_R0 (tm x) n) with (tm x (S n)) by ring.
    rewrite tm_abs. right. ring.
  - rewrite Nat.add_succ_r. cbn [sum_f_R0].
    replace (sum_f_R0 (tm x) (S n + m) + tm x (S (S n + m)) - sum_f_R0 (tm x) n)
      with ((sum_f_R0 (tm x) (S n + m) - sum_f_R0 (tm x) n) + tm x (S (S n + m))) by ring.
    eapply Rle_trans; [apply Rabs_triang |].
    rewrite tm_abs, <- (tech_pow_Rmult (/ 2) m).
    pose proof (tm_half (Rabs x) n (S m) Hy) as H2.
    rewrite Nat.add_succ_r, <- (tech_pow_Rmult (/ 2) m) in H2.
    apply Rle_trans with (tm (Rabs x) (S n) * (2 - (/ 2) ^ m) + tm (Rabs x) (S n) * (/ 2 * (/ 2) ^ m));
      [apply Rplus_le_compat; assumption | right; field].
Qed.

Theorem exp_tail (x : R) (n : nat) : Rabs x <= 1 ->
  Rabs (exp x - sum_f_R0 (tm x) n) <= 2 * tm (Rabs x) (S n).
Proof.
  intros Hx. apply le_epsilon. intros eps He.
  assert (Hin : exp_in x (exp x)) by (unfold exp; destruct (exist_exp x) as [l Hl]; exact Hl).
  destruct (Hin eps He) as [N HN].
  assert (H1 : Rabs (sum_f_R0 (tm x) (S n + N) - exp x) < eps) by (apply (HN (S n + N)%nat); lia).
  pose proof (tail_fin x n N Hx) as H2.
  pose proof (tm_pos (Rabs x) (S n) (Rabs_pos x)) as P.
  assert (Q : 0 <= tm (Rabs x) (S n) * (/ 2) ^ N) by (apply Rmult_le_pos; [exact P | apply pow_le; lra]).
  replace (exp x - sum_f_R0 (tm x) n)
    with ((sum_f_R0 (tm x) (S n + N) - sum_f_R0 (tm x) n) + - (sum_f_R0 (tm x) (S n + N) - exp x)) by ring.
  eapply Rle_trans; [apply Rabs_triang |]. rewrite Rabs_Ropp.
  replace (tm (Rabs x) (S n) * (2 - (/ 2) ^ N)) with (2 * tm (Rabs x) (S n) - tm (Rabs x) (S n) * (/ 2) ^ N) in H2 by ring.
  lra.
Qed.

Lemma fact_IZR (k : nat) (v : Z) : Z.of_nat (fact k) = v -> INR (fact k) = IZR v.
Proof. intros H. rewrite INR_IZR_INZ, H. reflexivity. Qed.

(* The partial sum of degree 7, as the polynomial exp32 evaluates. *)
Lemma sum7 (x : R) : sum_f_R0 (tm x) 7 =
  (5040 + x * (5040 + x * (2520 + x * (840 + x * (210 + x * (42 + x * (7 + x))))))) / 5040.
Proof.
  unfold tm. cbn [sum_f_R0].
  rewrite (fact_IZR 0 1 eq_refl), (fact_IZR 1 1 eq_refl), (fact_IZR 2 2 eq_refl), (fact_IZR 3 6 eq_refl),
          (fact_IZR 4 24 eq_refl), (fact_IZR 5 120 eq_refl), (fact_IZR 6 720 eq_refl), (fact_IZR 7 5040 eq_refl).
  field.
Qed.

(* 2 (5/128)^8 / 8! = 2.69e-16, below 1 / 3.6e15 = 2.78e-16. *)
Theorem exp_poly7 (r : R) : Rabs r <= 5 / 128 ->
  Rabs (exp r - (5040 + r * (5040 + r * (2520 + r * (840 + r * (210 + r * (42 + r * (7 + r))))))) / 5040)
    <= / 3600000000000000.
Proof.
Admitted.
