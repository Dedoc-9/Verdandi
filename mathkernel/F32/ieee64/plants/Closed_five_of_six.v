(* Plant: under the name IEEE64, a statement of five of the six parts (IEEE_EXP32 left out), and its proof. *)
From MKF.ieee64 Require Import IEEE64_Statement P32_IEEE.
Definition IEEE64 : Prop := IEEE_NARROW /\ IEEE_SQRT32 /\ IEEE_RSQRT32 /\ IEEE_HYPOT32 /\ IEEE_CST.
Theorem ieee64_holds : IEEE64.
Proof.
  exact (conj IEEE_NARROW_proof
          (conj IEEE_SQRT32_proof (conj IEEE_RSQRT32_proof (conj IEEE_HYPOT32_proof IEEE_CST_proof)))).
Qed.
