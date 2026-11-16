(* P32_IEEE identity check: nothing imported. Each definition is typed by the frozen statement's own name, so the
   kernel accepts it only if P32_IEEE's theorem has exactly that statement; Print Assumptions then lists what each
   proof rests on. IEEE_EXP32 and IEEE64 are not here: P32_IEEE.v does not prove them. *)
From MKF.ieee64 Require IEEE64_Statement P32_IEEE.
Definition check_cst : MKF.ieee64.IEEE64_Statement.IEEE_CST := MKF.ieee64.P32_IEEE.IEEE_CST_proof.
Definition check_narrow : MKF.ieee64.IEEE64_Statement.IEEE_NARROW := MKF.ieee64.P32_IEEE.IEEE_NARROW_proof.
Definition check_sqrt32 : MKF.ieee64.IEEE64_Statement.IEEE_SQRT32 := MKF.ieee64.P32_IEEE.IEEE_SQRT32_proof.
Definition check_rsqrt32 : MKF.ieee64.IEEE64_Statement.IEEE_RSQRT32 := MKF.ieee64.P32_IEEE.IEEE_RSQRT32_proof.
Definition check_hypot32 : MKF.ieee64.IEEE64_Statement.IEEE_HYPOT32 := MKF.ieee64.P32_IEEE.IEEE_HYPOT32_proof.
Print Assumptions check_cst.
Print Assumptions check_narrow.
Print Assumptions check_sqrt32.
Print Assumptions check_rsqrt32.
Print Assumptions check_hypot32.
