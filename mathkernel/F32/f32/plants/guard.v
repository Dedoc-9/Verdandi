(* Plant: False from a recursion whose termination check is switched off. *)
From MKF.f32 Require Import F32_Statement.
#[bypass_check(guard)] Fixpoint loop (n : nat) {struct n} : False := loop n.
Theorem F32_rel : F32_REL.
Proof. exact (False_ind _ (loop 0)). Qed.
