(* Proof of T32: narrow v = RN32 v for every binary64 v (FLT model). Flocq only; nothing is admitted.
   Three branches, as in the graph:
   A. |v| <= 2^-150: the graph returns v * 0 = 0, and RN32 v = 0 (the scaled value is at most 1/2 in magnitude; at the
      tie the even neighbour is 0).
   B. |v| < 2^-126: v + mm lies in [2^-97, 2^-96), where binary64's grid is 2^-149, binary32's subnormal grid. Adding
      mm shifts the scaled value by the even integer 3 * 2^51, which commutes with round-to-nearest-even; subtracting
      mm is then exact.
   C. otherwise: the graph is Veltkamp's split with s = 29 (Pff2Flocq.Veltkamp_Even, after RN's oddness and a
      commutation), giving the nearest-even rounding to 24 bits in FLT(-1074, 24), which coincides with FLT(-149, 24)
      once |v| >= 2^-126. *)
From Coq Require Import Reals ZArith Lia Lra.
From Flocq Require Import Core Pff.Pff2Flocq.
From MKF.f32 Require Import F32_Statement.
From MKF.p32 Require Import Graphs P32_Statement.
Open Scope R_scope.

#[local] Instance p24 : Prec_gt_0 24 := ltac:(unfold Prec_gt_0; lia).
#[local] Instance p53 : Prec_gt_0 53 := ltac:(unfold Prec_gt_0; lia).

(* Rounding at a known exponent. *)
Lemma round_at (fexp : Z -> Z) (rnd : R -> Z) (x : R) (e : Z) :
  cexp radix2 fexp x = e -> round radix2 fexp rnd x = IZR (rnd (x * bpow radix2 (- e))) * bpow radix2 e.
Proof. intros H. unfold round, scaled_mantissa, F2R. cbn [Fnum Fexp]. rewrite H. reflexivity. Qed.

Lemma Zfloor_plus_IZR (z : R) (n : Z) : Zfloor (z + IZR n) = (Zfloor z + n)%Z.
Proof.
  apply Zfloor_imp. rewrite !plus_IZR.
  pose proof (Zfloor_lb z). pose proof (Zfloor_ub z). split; lra.
Qed.

(* Shifting by an even integer commutes with round-to-nearest-even. *)
Lemma ZnearestE_plus_even (z : R) (n : Z) : Z.even n = true -> ZnearestE (z + IZR n) = (ZnearestE z + n)%Z.
Proof.
  intros En. unfold ZnearestE, Znearest.
  assert (Hc : Zceil (z + IZR n) = (Zceil z + n)%Z).
  { unfold Zceil. replace (- (z + IZR n)) with (- z + IZR (- n)) by (rewrite opp_IZR; ring).
    rewrite Zfloor_plus_IZR. ring. }
  rewrite Hc, Zfloor_plus_IZR.
  replace (z + IZR n - IZR (Zfloor z + n)) with (z - IZR (Zfloor z)) by (rewrite plus_IZR; ring).
  cbv beta. rewrite Z.even_add, En.
  destruct (Rcompare (z - IZR (Zfloor z)) (/ 2)); try reflexivity.
  destruct (Z.even (Zfloor z)); reflexivity.
Qed.

(* At most one half in magnitude rounds to 0, the tie included. *)
Lemma ZnearestE_half (z : R) : Rabs z <= / 2 -> ZnearestE z = 0%Z.
Proof.
  intros H. destruct (Rle_lt_or_eq_dec _ _ H) as [Hlt | Heq].
  - apply Znearest_imp. now rewrite Rminus_0_r.
  - assert (F0 : Zfloor (/ 2) = 0%Z) by (apply Zfloor_imp; simpl; lra).
    destruct (Rcase_abs z) as [Hn | Hp].
    + assert (Ez : z = - / 2) by (rewrite (Rabs_left z Hn) in Heq; lra). subst z.
      assert (F1 : Zfloor (- / 2) = (-1)%Z) by (apply Zfloor_imp; simpl; lra).
      assert (C1 : Zceil (- / 2) = 0%Z) by (unfold Zceil; rewrite Ropp_involutive, F0; reflexivity).
      unfold ZnearestE, Znearest. rewrite F1, C1, Rcompare_Eq by (simpl; lra). reflexivity.
    + assert (Ez : z = / 2) by (rewrite (Rabs_right z Hp) in Heq; lra). subst z.
      unfold ZnearestE, Znearest. rewrite F0, Rcompare_Eq by (simpl; lra). reflexivity.
Qed.

(* Powers of two, in units of U149 = 2^-149. *)
Definition U149 : R := bpow radix2 (-149).
Lemma u_pos : 0 < U149. Proof. apply bpow_gt_0. Qed.
Lemma TT_u : TT = 8388608 * U149.
Proof. unfold TT, U149. change 8388608 with (bpow radix2 23). rewrite <- bpow_plus. reflexivity. Qed.
Lemma HH_u : HH = / 2 * U149.
Proof. unfold HH, U149. change (/ 2) with (bpow radix2 (-1)). rewrite <- bpow_plus. reflexivity. Qed.
Lemma B97_u : bpow radix2 (-97) = 4503599627370496 * U149.
Proof. unfold U149. change 4503599627370496 with (bpow radix2 52). rewrite <- bpow_plus. reflexivity. Qed.
Lemma B96_u : bpow radix2 (-96) = 9007199254740992 * U149.
Proof. unfold U149. change 9007199254740992 with (bpow radix2 53). rewrite <- bpow_plus. reflexivity. Qed.
Lemma MM_u : MM = 6755399441055744 * U149.
Proof.
  unfold MM, U149. replace 6755399441055744 with (3 * bpow radix2 51) by (change (bpow radix2 51) with 2251799813685248; lra).
  rewrite Rmult_assoc, <- bpow_plus. reflexivity.
Qed.

Lemma cexp32_small (v : R) : v <> 0 -> Rabs v < TT -> cexp radix2 fexp32 v = (-149)%Z.
Proof.
  intros Nz Hv. unfold cexp, FLT_exp.
  assert (mag radix2 v <= -126)%Z by (apply mag_le_bpow; assumption). lia.
Qed.

(* |v| * 2^149 against a bound given in units of U149. *)
Lemma scaled_lt (v c : R) : Rabs v < c * U149 -> Rabs (v * bpow radix2 149) < c.
Proof.
  intros H. rewrite Rabs_mult, (Rabs_pos_eq (bpow radix2 149)) by apply bpow_ge_0.
  apply Rmult_lt_reg_r with (bpow radix2 (-149)); [apply bpow_gt_0 |].
  rewrite Rmult_assoc, <- bpow_plus. change (bpow radix2 (149 + -149)) with 1. unfold U149 in H. lra.
Qed.
Lemma scaled_le (v c : R) : Rabs v <= c * U149 -> Rabs (v * bpow radix2 149) <= c.
Proof.
  intros H. rewrite Rabs_mult, (Rabs_pos_eq (bpow radix2 149)) by apply bpow_ge_0.
  apply Rmult_le_reg_r with (bpow radix2 (-149)); [apply bpow_gt_0 |].
  rewrite Rmult_assoc, <- bpow_plus. change (bpow radix2 (149 + -149)) with 1. unfold U149 in H. lra.
Qed.

(* Branch B. *)
Lemma magic (v : R) : v <> 0 -> Rabs v < TT -> RN64 (RN64 (v + MM) - MM) = RN32 v.
Proof.
  intros Nz Hv. pose proof u_pos as Up.
  assert (Hv' : Rabs v < 8388608 * U149) by (rewrite <- TT_u; exact Hv).
  assert (Hb : - (8388608 * U149) < v < 8388608 * U149) by (apply Rabs_lt_inv; exact Hv').
  assert (Hw : bpow radix2 (-97) <= Rabs (v + MM) < bpow radix2 (-96)).
  { rewrite B97_u, B96_u, MM_u. rewrite Rabs_pos_eq by lra. split; lra. }
  assert (C64 : cexp radix2 fexp64 (v + MM) = (-149)%Z).
  { unfold cexp. rewrite (mag_unique radix2 (v + MM) (-96)) by exact Hw. reflexivity. }
  rewrite (round_at fexp64 ZnearestE (v + MM) (-149) C64).
  rewrite (round_at fexp32 ZnearestE v (-149) (cexp32_small v Nz Hv)).
  change (- -149)%Z with 149%Z.
  replace ((v + MM) * bpow radix2 149) with (v * bpow radix2 149 + IZR 6755399441055744).
  2:{ rewrite MM_u. unfold U149. rewrite Rmult_plus_distr_r, Rmult_assoc, <- bpow_plus.
      change (bpow radix2 (-149 + 149)) with 1. ring. }
  rewrite ZnearestE_plus_even by reflexivity.
  set (k := ZnearestE (v * bpow radix2 149)).
  rewrite plus_IZR, Rmult_plus_distr_r.
  replace (IZR 6755399441055744 * bpow radix2 (-149)) with MM by (rewrite MM_u; reflexivity).
  replace (IZR k * bpow radix2 (-149) + MM - MM) with (IZR k * bpow radix2 (-149)) by ring.
  apply round_generic; [typeclasses eauto |].
  pose proof (scaled_lt v 8388608 Hv') as Hz. apply Rabs_lt_inv in Hz.
  assert (K1 : (k <= 8388608)%Z).
  { unfold k. rewrite <- (@Zrnd_IZR ZnearestE (valid_rnd_N _) 8388608). apply Zrnd_le; [typeclasses eauto | lra]. }
  assert (K2 : (-8388608 <= k)%Z).
  { unfold k. rewrite <- (@Zrnd_IZR ZnearestE (valid_rnd_N _) (-8388608)). apply Zrnd_le; [typeclasses eauto | lra]. }
  apply generic_format_FLT. apply (FLT_spec radix2 (-1074) 53 _ (Float radix2 k (-149))).
  - reflexivity.
  - cbn [Fnum]. assert (E : (radix2 ^ 53 = 9007199254740992)%Z) by reflexivity. rewrite E. lia.
  - cbn [Fexp]. lia.
Qed.

(* Branch C. *)
Lemma veltkamp32 (v : R) : format64 v -> TT <= Rabs v ->
  RN64 (RN64 (KK * v) - RN64 (RN64 (KK * v) - v)) = RN32 v.
Proof.
  intros Fv Hv.
  pose proof (Veltkamp_Even radix2 (-1074) 53 (fun z => negb (Z.even z)) 29
                ltac:(lia) ltac:(lia) ltac:(lia) ltac:(lia) v Fv eq_refl) as V.
  assert (Ec : RN64 (KK * v) = RN64 (v * (bpow radix2 29 + 1))).
  { f_equal. unfold KK. change (bpow radix2 29) with 536870912. ring. }
  rewrite Ec. set (c := RN64 (v * (bpow radix2 29 + 1))).
  replace (RN64 (c - v)) with (- RN64 (v - c)) by (rewrite <- round_NE_opp; f_equal; ring).
  replace (c - - RN64 (v - c)) with (RN64 (v - c) + c) by ring.
  transitivity (round radix2 (FLT_exp (-1074) 24) ZnearestE v); [exact V |].
  assert (Hm : (-125 <= mag radix2 v)%Z) by (apply mag_ge_bpow; exact Hv).
  unfold round, scaled_mantissa, cexp.
  replace (FLT_exp (-1074) 24 (mag radix2 v)) with (FLT_exp (-149) 24 (mag radix2 v)) by (unfold FLT_exp; lia).
  reflexivity.
Qed.

Theorem T32_proof : T32.
Proof.
  unfold T32, narrow. intros v Fv. pose proof u_pos as Up.
  destruct (Rle_dec (Rabs v) HH) as [Hs | Hs].
  - rewrite Rmult_0_r, (round_0 radix2 fexp64 ZnearestE).
    destruct (Req_dec v 0) as [Z0 | Nz].
    + subst v. now rewrite (round_0 radix2 fexp32 ZnearestE).
    + rewrite HH_u in Hs.
      assert (Hv : Rabs v < TT) by (rewrite TT_u; lra).
      rewrite (round_at fexp32 ZnearestE v (-149) (cexp32_small v Nz Hv)).
      change (- -149)%Z with 149%Z.
      rewrite ZnearestE_half by (apply scaled_le; exact Hs). simpl. ring.
  - destruct (Rlt_dec (Rabs v) TT) as [Ht | Ht].
    + apply magic; [| exact Ht]. intros Z0. apply Hs. rewrite Z0, Rabs_R0. unfold HH. apply bpow_ge_0.
    + apply veltkamp32; [exact Fv | lra].
Qed.
