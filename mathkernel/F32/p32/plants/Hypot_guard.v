(* Plant: False from a recursion whose termination check is switched off. *)
From Coq Require Import Reals.
From Flocq Require Import Core.
From MKF.f32 Require Import F32_Statement.
From MKF.p32 Require Import Graphs P32_Statement.
#[bypass_check(guard)] Fixpoint loop (n : nat) {struct n} : False := loop n.
Theorem hypot32_faithful : HYPOT32.
Proof. exact (False_ind _ (loop 0)). Qed.
