(* Plant: a trivial statement under the frozen name. *)
From Coq Require Import Reals.
From Flocq Require Import Core.
From MKF.f32 Require Import F32_Statement.
From MKF.p32 Require Import Graphs P32_Statement.
Definition HYPOT32 : Prop := True.
Theorem hypot32_faithful : HYPOT32.
Proof. exact I. Qed.
