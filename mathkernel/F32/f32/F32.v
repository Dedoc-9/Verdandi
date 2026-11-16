(* Proof of lemma F32 (statement in F32_Statement.v). Flocq only; nothing is admitted.
   Idea: let a = RD32 f and b = RU32 f. Flocq's midpoint lemmas give a <= RN32 y <= b once y lies strictly between the
   midpoint below a and the midpoint above b. The gap below a positive binary32 a is ulp(pred a), and ulp x exceeds
   |x| * 2^-24, so a relative error of 2^-27 stays inside both half-gaps. Then RN32 y is a binary32 number in [a, b],
   and b is a's successor (or a = b = f), so RN32 y is a or b. *)
From Coq Require Import Reals ZArith Lia Lra Classical_Prop.
From Flocq Require Import Core.
From MKF.f32 Require Import F32_Statement.
Open Scope R_scope.

#[local] Instance p24 : Prec_gt_0 24 := ltac:(unfold Prec_gt_0; lia).
Notation ulp32 := (ulp radix2 fexp32).
Notation succ32 := (succ radix2 fexp32).
Notation pred32 := (pred radix2 fexp32).

(* ulp x > |x| * 2^-24, with the power written as a number (by conversion). *)
Lemma ulp32_gt (x : R) : 0 <= x -> x * / 16777216 < ulp32 x.
Proof.
  intros Hx. pose proof (ulp_FLT_gt radix2 (-149) 24 x) as U.
  rewrite (Rabs_pos_eq x Hx) in U. exact U.
Qed.

Lemma F32_pos (f y : R) : 0 < f -> Rabs (y - f) <= / 134217728 * f ->
  RN32 y = RD32 f \/ RN32 y = RU32 f.
Proof.
  intros Hf Hy.
  destruct (round_DN_pt radix2 fexp32 f) as (Fa & Haf & Hamax).
  destruct (round_UP_pt radix2 fexp32 f) as (Fb & Hfb & Hbmin).
  set (a := RD32 f) in *. set (b := RU32 f) in *.
  assert (Ha0 : 0 <= a) by (apply Hamax; [apply generic_format_0 | lra]).
  assert (Hb0 : 0 < b) by lra.
  apply Rabs_le_inv in Hy.
  assert (Fn : format32 (RN32 y)) by (apply generic_format_round; typeclasses eauto).
  (* above: y is below the midpoint of b and its successor *)
  assert (Hub : RN32 y <= b).
  { apply (round_N_le_midp radix2 fexp32 (fun x => negb (Z.even x)) b y Fb).
    rewrite (succ_eq_pos radix2 fexp32 b) by lra.
    pose proof (ulp32_gt b) as U. lra. }
  (* below: y is above the midpoint of a and its predecessor *)
  assert (Hlb : a <= RN32 y).
  { apply (round_N_ge_midp radix2 fexp32 (fun x => negb (Z.even x)) a y Fa).
    destruct (Req_dec a 0) as [Za | Na].
    - rewrite Za, pred_0, (@ulp_FLT_0 radix2 (-149) 24 p24). pose proof (bpow_gt_0 radix2 (-149)). lra.
    - assert (Hap : 0 < a) by lra.
      pose proof (pred_ge_0 radix2 fexp32 a Hap Fa) as Hp.
      pose proof (succ_pred radix2 fexp32 a Fa) as Hs.
      rewrite (succ_eq_pos radix2 fexp32 _ Hp) in Hs.
      pose proof (ulp32_gt _ Hp) as U.
      lra. }
  (* RN32 y is a binary32 number in [a, b], and nothing lies strictly between a and b *)
  destruct (classic (format32 f)) as [Ff | NFf].
  - left.
    assert (Ea : a = f) by (unfold a; apply round_generic; [typeclasses eauto | exact Ff]).
    assert (Eb : b = f) by (unfold b; apply round_generic; [typeclasses eauto | exact Ff]).
    lra.
  - assert (Hsb : succ32 a = b) by exact (succ_DN_eq_UP radix2 fexp32 f NFf).
    destruct (Req_dec (RN32 y) a) as [E | NE]; [left; exact E | right].
    assert (Hlt : a < RN32 y) by lra.
    pose proof (succ_le_lt radix2 fexp32 a (RN32 y) Fa Fn Hlt) as Hs2.
    rewrite Hsb in Hs2. lra.
Qed.

Lemma F32_neg (f y : R) : f < 0 -> Rabs (y - f) <= / 134217728 * (- f) ->
  RN32 y = RD32 f \/ RN32 y = RU32 f.
Proof.
  intros Hf Hy.
  assert (P : RN32 (- y) = RD32 (- f) \/ RN32 (- y) = RU32 (- f)).
  { apply F32_pos; [lra |].
    replace (- y - - f) with (- (y - f)) by ring. rewrite Rabs_Ropp. exact Hy. }
  destruct P as [E | E].
  - right. rewrite round_NE_opp, round_DN_opp in E. lra.
  - left. rewrite round_NE_opp, round_UP_opp in E. lra.
Qed.

Theorem F32_rel : F32_REL.
Proof.
  unfold F32_REL, faithful32. intros f y H.
  assert (H' : Rabs (y - f) <= / 134217728 * Rabs f) by exact H.
  destruct (Rtotal_order f 0) as [Hn | [Hz | Hp]].
  - rewrite (Rabs_left f Hn) in H'. now apply F32_neg.
  - subst f. rewrite Rabs_R0, Rmult_0_r in H'.
    assert (Zy : y = 0) by (apply Rabs_le_inv in H'; lra).
    subst y. left.
    rewrite (round_0 radix2 fexp32 ZnearestE), (round_0 radix2 fexp32 Zfloor). reflexivity.
  - rewrite (Rabs_pos_eq f) in H' by lra. now apply F32_pos.
Qed.
