(* EXP32_IEEE identity check: nothing imported. check_exp32 is typed by the frozen statement's own name, so the
   kernel accepts it only if EXP32_IEEE's theorem has exactly that statement. check_ieee64 puts the six proofs
   together (five from P32_IEEE.v, exp32's from EXP32_IEEE.v) at the frozen IEEE64, in the statement's own order.
   Print Assumptions then lists what each rests on. *)
From MKF.ieee64 Require IEEE64_Statement P32_IEEE EXP32_IEEE.
Definition check_exp32 : MKF.ieee64.IEEE64_Statement.IEEE_EXP32 := MKF.ieee64.EXP32_IEEE.IEEE_EXP32_proof.
Definition check_ieee64 : MKF.ieee64.IEEE64_Statement.IEEE64 :=
  conj MKF.ieee64.P32_IEEE.IEEE_NARROW_proof
    (conj MKF.ieee64.P32_IEEE.IEEE_SQRT32_proof
      (conj MKF.ieee64.P32_IEEE.IEEE_RSQRT32_proof
        (conj MKF.ieee64.P32_IEEE.IEEE_HYPOT32_proof
          (conj MKF.ieee64.EXP32_IEEE.IEEE_EXP32_proof MKF.ieee64.P32_IEEE.IEEE_CST_proof)))).
Check MKF.ieee64.EXP32_IEEE.IEEE_EXP32_proof.
Print Assumptions check_exp32.
Print Assumptions check_ieee64.
