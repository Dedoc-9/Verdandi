(* EXP32R identity check: nothing imported; the kernel checks the definition and coqchk rechecks it from the .vo. *)
From MKF.exp32r Require RANGE_Statement Range.
Definition identity_check : MKF.exp32r.RANGE_Statement.EXP32_RANGE /\ MKF.exp32r.RANGE_Statement.EXP32_SHARP :=
  conj MKF.exp32r.Range.exp32_range MKF.exp32r.Range.exp32_sharp.
Print Assumptions identity_check.
