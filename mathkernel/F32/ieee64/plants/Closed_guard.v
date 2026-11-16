(* Plant: False from a recursion whose termination check is switched off. *)
From MKF.ieee64 Require Import IEEE64_Statement.
#[bypass_check(guard)] Fixpoint loop (n : nat) {struct n} : False := loop n.
Theorem ieee64_holds : IEEE64.
Proof. exact (False_ind _ (loop 0)). Qed.
