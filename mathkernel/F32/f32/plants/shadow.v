(* Plant: a trivial statement under the frozen name. *)
From MKF.f32 Require Import F32_Statement.
Definition F32_REL : Prop := True.
Theorem F32_rel : F32_REL.
Proof. exact I. Qed.
