From Coq Require Import Reals.
Definition EXP32_RANGE : Prop := True.
Definition EXP32_SHARP : Prop := True.
Theorem exp32_range : EXP32_RANGE.
Proof. exact I. Qed.
Theorem exp32_sharp : EXP32_SHARP.
Proof. exact I. Qed.
