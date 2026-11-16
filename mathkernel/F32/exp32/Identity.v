(* EXP32 identity check: nothing imported; the kernel checks the definition and coqchk rechecks it from the .vo. *)
From MKF.exp32 Require EXP32_Statement Exp32.
Definition identity_check : MKF.exp32.EXP32_Statement.EXP32 := MKF.exp32.Exp32.exp32_faithful.
Print Assumptions identity_check.
