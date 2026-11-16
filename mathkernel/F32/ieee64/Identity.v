(* IEEE64 identity check: nothing imported. The definition is typed by the frozen statement's own name, so the
   kernel accepts it only if Closed.v's theorem has exactly that statement, and coqchk rechecks it from the .vo. *)
From MKF.ieee64 Require IEEE64_Statement Closed.
Definition identity_check : MKF.ieee64.IEEE64_Statement.IEEE64 := MKF.ieee64.Closed.ieee64_holds.
Print Assumptions identity_check.
