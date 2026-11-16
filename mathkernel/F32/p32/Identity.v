(* P32 identity check: nothing imported; the kernel checks the definition and coqchk rechecks it from the .vo. *)
From MKF.p32 Require P32_Statement T32 Funcs Hypot.
Definition identity_check :
  MKF.p32.P32_Statement.T32 /\ MKF.p32.P32_Statement.SQRT32 /\ MKF.p32.P32_Statement.RSQRT32 /\ MKF.p32.P32_Statement.HYPOT32 :=
  conj MKF.p32.T32.T32_proof (conj MKF.p32.Funcs.sqrt32_faithful (conj MKF.p32.Funcs.rsqrt32_faithful MKF.p32.Hypot.hypot32_faithful)).
Print Assumptions identity_check.
