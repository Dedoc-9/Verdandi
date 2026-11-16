(* F32 identity check: nothing imported; the kernel checks the definition and coqchk rechecks it from the .vo. *)
From MKF.f32 Require F32_Statement F32.
Definition identity_check : MKF.f32.F32_Statement.F32_REL := MKF.f32.F32.F32_rel.
Print Assumptions identity_check.
