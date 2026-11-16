(* P32R identity check: nothing imported; the kernel checks the definition and coqchk rechecks it from the .vo. *)
From MKF.p32r Require P32R_Statement Range.
Definition identity_check : MKF.p32r.P32R_Statement.P32R := MKF.p32r.Range.p32r.
Print Assumptions identity_check.
