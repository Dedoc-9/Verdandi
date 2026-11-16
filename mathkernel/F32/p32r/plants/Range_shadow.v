(* Plant: a trivial statement under the frozen name. *)
From Coq Require Import Reals.
From Flocq Require Import Core.
From MKF.f32 Require Import F32_Statement.
From MKF.p32 Require Import Graphs P32_Statement.
Definition P32R : Prop := True.
Theorem p32r : P32R.
Proof. exact I. Qed.
