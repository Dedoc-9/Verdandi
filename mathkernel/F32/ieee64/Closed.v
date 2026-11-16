(* The model-to-binary64 correspondence, closed: IEEE64 (stated in IEEE64_Statement.v, which this file does not
   change) from its six parts. Five are P32_IEEE.v's theorems (IEEE_NARROW, IEEE_SQRT32, IEEE_RSQRT32, IEEE_HYPOT32,
   IEEE_CST) and one is EXP32_IEEE.v's (IEEE_EXP32); each is a theorem of exactly the statement's part and ends
   with Qed. Nothing is proved here but their conjunction, in the statement's own order. Author: the assistant
   (2026-11-15).

   What ieee64_holds says and does not say is what the header of IEEE64_Statement.v says, no more: on each
   function's domain, Flocq's IEEE binary64 operations in round to nearest even, in the graph's order, return a
   finite value whose real number is the graph's. Nothing about the sign of a zero, about inputs outside the
   premises, about NaN or infinite inputs, about a compiler, a processor or any program. It rests on Flocq's
   binary_float operations being IEEE 754's. *)
From MKF.ieee64 Require Import IEEE64_Statement P32_IEEE EXP32_IEEE.

Theorem ieee64_holds : IEEE64.
Proof.
  exact (conj IEEE_NARROW_proof
          (conj IEEE_SQRT32_proof
            (conj IEEE_RSQRT32_proof
              (conj IEEE_HYPOT32_proof
                (conj IEEE_EXP32_proof IEEE_CST_proof))))).
Qed.
