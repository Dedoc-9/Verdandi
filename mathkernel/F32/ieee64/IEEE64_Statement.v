(* The model-to-binary64 correspondence: its statement, written before any proof of it (2026-11-15). Author: the
   assistant. Definitions only: this file holds no proof script and assumes nothing.

   THE GAP. The tier's five functions (narrow, sqrt32, rsqrt32, hypot32, exp32) are operation graphs over the real
   numbers in Flocq's FLT model of binary64, FLT(-1074, 53) with round to nearest even (RN64): p32/Graphs.v and
   exp32/Graph.v. That model has no upper exponent bound (nothing overflows), no sign of zero, no NaN and no
   infinity, and every theorem of the tier so far is about those graphs. None says that IEEE 754 binary64 arithmetic,
   which overflows to infinity and has NaN, computes the graphs' values. IEEE64 below says so, on each function's
   domain, of Flocq's formalization of IEEE binary64 (Flocq.IEEE754.BinarySingleNaN).

   HOW THE IEEE COMPUTATION IS HELD TO THE GRAPH. Each graph is written once more as a shape G_f: the graph's own
   expression tree with every operation replaced by a field of the record OPS, for any type T of values. model_ops
   gives the fields at T = R exactly as the graph files write the operations; ieee_ops gives them at T = b64 as
   Flocq's IEEE operations in round to nearest even (mode_NE). For each shape a definition G_f_model of type
   forall x : R, G_f R model_ops x = g_f x (narrow for G_narrow) has eq_refl for its body, which the kernel accepts
   only if the shape at the model is convertible with the frozen graph. So G_f b64 ieee_ops is the graph's
   operations in the graph's order, each constant taken from ieee_cst (which IEEE_CST says denotes the graph's),
   and it is the kernel, not a reader, that holds the shape to the graph.

   WHAT IEEE64 SAYS. For each function and every finite binary64 input inside the premises: the IEEE operations, in
   the graph's order, return a finite binary64 value (not an infinity, not NaN), and the real number that value
   denotes (B2R) is the graph's value. IEEE_CST says the same of each constant: its binary64 value is finite and
   denotes the constant the graph files write. The premises are each function's statement premises together with
   its range statement's premises (FMAX32 and OVF32 from p32r/P32R_Statement.v, XMAX from exp32/EXP32_Statement.v).
   A premise that another one implies is not repeated: x < 2^128 follows from x <= FMAX32, and the bounds on the
   inputs of hypot32 from the bound on its exact result. For narrow, the premise that the input is a binary64
   number is the type b64 itself.

   WHAT IT DOES NOT SAY.
   - Nothing about the sign of a zero result: B2R of +0 and of -0 is the real number 0.
   - Nothing about inputs outside the premises, and nothing about NaN or infinite inputs.
   - Nothing about the value a selection does not return. A selection is "c if a <= b, otherwise d" (or a < b)
     between two values already computed; the one not returned is not said to be finite.
   - Nothing about the values in between: only the returned value is said to be finite and to denote the graph's.
     Flocq's operations carry no exception flags, so nothing is said of those either.
   - Nothing about a compiler, a processor, or any program: that some program performs these operations, in this
     order, on these constants, in binary64 and in round to nearest even, is not stated here.
   - Nothing about what the graphs' values are (faithful roundings, finite binary32 numbers): those are the other
     folders' theorems, about the graphs.
   WHAT IT TRUSTS. That Flocq's binary_float operations (Bplus, Bminus, Bmult, Bdiv and Bsqrt at mode_NE, Babs,
   Bleb, Bltb; Flocq 4.2.1 in the image) are IEEE 754's. BinarySingleNaN has a single NaN, without payload. *)
From Coq Require Import Reals.
From Flocq Require Import Core BinarySingleNaN.
From MKF.f32 Require Import F32_Statement.
From MKF.p32 Require Import Graphs.
From MKF.p32r Require Import P32R_Statement.
From MKF.exp32 Require Import Graph EXP32_Statement.
Open Scope R_scope.

(* 1. IEEE binary64: 53 bits of precision, finite values below 2^1024. Flocq's operations take the two facts
   0 < 53 and 53 < 1024; each is a comparison of numerals that computes, so its term is eq_refl. *)
Definition b64 : Set := binary_float 53 1024.
Definition prec64_gt_0 : Prec_gt_0 53 := eq_refl.
Definition prec64_lt_emax : Prec_lt_emax 53 1024 := eq_refl.

(* 2. The constants the graphs use, as names, and the operations the graphs use, as a record over any type T of
   values. o_sel_le o a b c d is "c if a <= b, otherwise d"; o_sel_lt o a b c d is "c if a < b, otherwise d". *)
Inductive gconst : Set :=
  | C_KK | C_MM | C_TT | C_HH | C_0 | C_1 | C_m160 | C_4096 | C_5040 | C_2520 | C_840 | C_210 | C_42 | C_7.

Record OPS (T : Type) : Type := Build_OPS {
  o_add : T -> T -> T;
  o_sub : T -> T -> T;
  o_mul : T -> T -> T;
  o_div : T -> T -> T;
  o_sqrt : T -> T;
  o_abs : T -> T;
  o_sel_le : T -> T -> T -> T -> T;
  o_sel_lt : T -> T -> T -> T -> T;
  o_cst : gconst -> T }.
Arguments o_add {T} _ _ _.
Arguments o_sub {T} _ _ _.
Arguments o_mul {T} _ _ _.
Arguments o_div {T} _ _ _.
Arguments o_sqrt {T} _ _.
Arguments o_abs {T} _ _.
Arguments o_sel_le {T} _ _ _ _ _.
Arguments o_sel_lt {T} _ _ _ _ _.
Arguments o_cst {T} _ _.

(* 3. The model: every field as the graph files write the operation. KK, MM, TT and HH are p32/Graphs.v's own
   (536870913, 3 * bpow radix2 (-98), bpow radix2 (-126), bpow radix2 (-150)); the others are the numerals of
   p32/Graphs.v and exp32/Graph.v. The absolute value is not rounded. *)
Definition model_cst (c : gconst) : R :=
  match c with
  | C_KK => KK
  | C_MM => MM
  | C_TT => TT
  | C_HH => HH
  | C_0 => 0
  | C_1 => 1
  | C_m160 => -160
  | C_4096 => 4096
  | C_5040 => 5040
  | C_2520 => 2520
  | C_840 => 840
  | C_210 => 210
  | C_42 => 42
  | C_7 => 7
  end.

Definition model_ops : OPS R := {|
  o_add := fun a b => RN64 (a + b);
  o_sub := fun a b => RN64 (a - b);
  o_mul := fun a b => RN64 (a * b);
  o_div := fun a b => RN64 (a / b);
  o_sqrt := fun a => RN64 (sqrt a);
  o_abs := Rabs;
  o_sel_le := fun a b c d => if Rle_dec a b then c else d;
  o_sel_lt := fun a b c d => if Rlt_dec a b then c else d;
  o_cst := model_cst |}.

(* 4. IEEE binary64: Flocq's operations in round to nearest even, its comparisons (false when an operand is NaN),
   and each constant as an explicit binary64 value: sign (true is negative), mantissa, exponent, and the term that
   says the pair is a binary64 number, which computes (eq_refl). A value is mantissa * 2^exponent; each mantissa is
   written c * 2^k beside the exponent -k where the constant is the whole number c, so that it can be read off:
     KK = 536870913       MM = 3 * 2^51 * 2^-149 = 3 * 2^-98
     TT = 2^52 * 2^-178 = 2^-126                 HH = 2^52 * 2^-202 = 2^-150
     0 is +0              1 = 2^52 * 2^-52       -160, 4096, 5040, 2520, 840, 210, 42, 7 as written. *)
Definition ieee_cst (c : gconst) : b64 :=
  match c with
  | C_KK => @B754_finite 53 1024 false (536870913 * 2 ^ 23) (-23) eq_refl
  | C_MM => @B754_finite 53 1024 false (3 * 2 ^ 51) (-149) eq_refl
  | C_TT => @B754_finite 53 1024 false (2 ^ 52) (-178) eq_refl
  | C_HH => @B754_finite 53 1024 false (2 ^ 52) (-202) eq_refl
  | C_0 => @B754_zero 53 1024 false
  | C_1 => @B754_finite 53 1024 false (2 ^ 52) (-52) eq_refl
  | C_m160 => @B754_finite 53 1024 true (160 * 2 ^ 45) (-45) eq_refl
  | C_4096 => @B754_finite 53 1024 false (4096 * 2 ^ 40) (-40) eq_refl
  | C_5040 => @B754_finite 53 1024 false (5040 * 2 ^ 40) (-40) eq_refl
  | C_2520 => @B754_finite 53 1024 false (2520 * 2 ^ 41) (-41) eq_refl
  | C_840 => @B754_finite 53 1024 false (840 * 2 ^ 43) (-43) eq_refl
  | C_210 => @B754_finite 53 1024 false (210 * 2 ^ 45) (-45) eq_refl
  | C_42 => @B754_finite 53 1024 false (42 * 2 ^ 47) (-47) eq_refl
  | C_7 => @B754_finite 53 1024 false (7 * 2 ^ 50) (-50) eq_refl
  end.

Definition ieee_ops : OPS b64 := {|
  o_add := @Bplus 53 1024 prec64_gt_0 prec64_lt_emax mode_NE;
  o_sub := @Bminus 53 1024 prec64_gt_0 prec64_lt_emax mode_NE;
  o_mul := @Bmult 53 1024 prec64_gt_0 prec64_lt_emax mode_NE;
  o_div := @Bdiv 53 1024 prec64_gt_0 prec64_lt_emax mode_NE;
  o_sqrt := @Bsqrt 53 1024 prec64_gt_0 prec64_lt_emax mode_NE;
  o_abs := @Babs 53 1024;
  o_sel_le := fun a b c d => if @Bleb 53 1024 a b then c else d;
  o_sel_lt := fun a b c d => if @Bltb 53 1024 a b then c else d;
  o_cst := ieee_cst |}.

(* 5. The shapes: each graph's own expression tree over the record's fields, for any type T and any o : OPS T.
   exp32's graph is written in exp32/Graph.v as three stages (exp32_red, exp32_poly, exp32_sq) and their
   composition, twelve squarings, and so is its shape. *)
Definition G_narrow (T : Type) (o : OPS T) (v : T) : T :=
  o_sel_le o (o_abs o v) (o_cst o C_HH) (o_mul o v (o_cst o C_0))
    (o_sel_lt o (o_abs o v) (o_cst o C_TT) (o_sub o (o_add o v (o_cst o C_MM)) (o_cst o C_MM))
      (o_sub o (o_mul o (o_cst o C_KK) v) (o_sub o (o_mul o (o_cst o C_KK) v) v))).

Definition G_sqrt32 (T : Type) (o : OPS T) (x : T) : T := G_narrow T o (o_sqrt o x).

Definition G_rsqrt32 (T : Type) (o : OPS T) (x : T) : T := G_narrow T o (o_div o (o_cst o C_1) (o_sqrt o x)).

Definition G_hypot32 (T : Type) (o : OPS T) (x y : T) : T :=
  G_narrow T o (o_sqrt o (o_add o (o_mul o x x) (o_mul o y y))).

Definition G_exp32_red (T : Type) (o : OPS T) (x : T) : T :=
  o_div o (o_sel_lt o x (o_cst o C_m160) (o_cst o C_m160) x) (o_cst o C_4096).

Definition G_exp32_poly (T : Type) (o : OPS T) (r : T) : T :=
  o_div o
    (o_add o (o_cst o C_5040) (o_mul o r
    (o_add o (o_cst o C_5040) (o_mul o r
    (o_add o (o_cst o C_2520) (o_mul o r
    (o_add o (o_cst o C_840) (o_mul o r
    (o_add o (o_cst o C_210) (o_mul o r
    (o_add o (o_cst o C_42) (o_mul o r
    (o_add o (o_cst o C_7) r)))))))))))))
    (o_cst o C_5040).

Definition G_exp32_sq (T : Type) (o : OPS T) (v : T) : T := o_mul o v v.

Definition G_exp32 (T : Type) (o : OPS T) (x : T) : T :=
  G_narrow T o
    (G_exp32_sq T o (G_exp32_sq T o (G_exp32_sq T o (G_exp32_sq T o
    (G_exp32_sq T o (G_exp32_sq T o (G_exp32_sq T o (G_exp32_sq T o
    (G_exp32_sq T o (G_exp32_sq T o (G_exp32_sq T o (G_exp32_sq T o
    (G_exp32_poly T o (G_exp32_red T o x)))))))))))))).

(* 6. Each shape at the model is its frozen graph. The body of every definition below is eq_refl, with no
   rewriting and no tactic: the kernel accepts it only if the two sides of the equation are convertible.
   For narrow, sqrt32, rsqrt32, hypot32 and the stages exp32_red and exp32_sq, eq_refl stands alone. For exp32_poly
   and for exp32 it is given its term t. eq_refl t has the type t = t, and the kernel accepts it at the type
   G = g only if t is convertible with G and with g; G and g are then convertible with each other, whatever t is,
   so nothing rests on t and it is not part of what is stated. t is there only for the time the check takes. Left
   to itself, eq_refl takes the shape for its term; Coq's conversion then compares the nested roundings again and
   again, its time multiplies with every nested rounding and every squaring, and for these two definitions it did
   not end within the time allowed (ieee64/STATE.md has the measurements and the reason). With t the same check
   ends in seconds. For exp32_poly t is the graph. For exp32 t is the graph with its stages written out, each
   squaring named once. *)
Definition G_narrow_model : forall v : R, G_narrow R model_ops v = narrow v := fun v => eq_refl.

Definition G_sqrt32_model : forall x : R, G_sqrt32 R model_ops x = g_sqrt32 x := fun x => eq_refl.

Definition G_rsqrt32_model : forall x : R, G_rsqrt32 R model_ops x = g_rsqrt32 x := fun x => eq_refl.

Definition G_hypot32_model : forall x y : R, G_hypot32 R model_ops x y = g_hypot32 x y := fun x y => eq_refl.

Definition G_exp32_red_model : forall x : R, G_exp32_red R model_ops x = exp32_red x := fun x => eq_refl.

Definition G_exp32_poly_model : forall r : R, G_exp32_poly R model_ops r = exp32_poly r :=
  fun r => eq_refl (exp32_poly r).

Definition G_exp32_sq_model : forall v : R, G_exp32_sq R model_ops v = exp32_sq v := fun v => eq_refl.

Definition G_exp32_model : forall x : R, G_exp32 R model_ops x = g_exp32 x :=
  fun x => eq_refl
    (narrow
      (let r := RN64 ((if Rlt_dec x (-160) then (-160) else x) / 4096) in
       let p := RN64 (RN64 (5040 + RN64 (r * RN64 (5040 + RN64 (r * RN64 (2520 + RN64 (r * RN64 (840 + RN64 (r *
                  RN64 (210 + RN64 (r * RN64 (42 + RN64 (r * RN64 (7 + r))))))))))))) / 5040) in
       let s1 := RN64 (p * p) in
       let s2 := RN64 (s1 * s1) in
       let s3 := RN64 (s2 * s2) in
       let s4 := RN64 (s3 * s3) in
       let s5 := RN64 (s4 * s4) in
       let s6 := RN64 (s5 * s5) in
       let s7 := RN64 (s6 * s6) in
       let s8 := RN64 (s7 * s7) in
       let s9 := RN64 (s8 * s8) in
       let s10 := RN64 (s9 * s9) in
       let s11 := RN64 (s10 * s10) in
       RN64 (s11 * s11))).

(* 7. The statements. In each, the real number of a binary64 value b is B2R b. *)
Definition IEEE_NARROW : Prop :=
  forall b : b64, is_finite b = true -> Rabs (B2R b) < OVF32 ->
  is_finite (G_narrow b64 ieee_ops b) = true /\ B2R (G_narrow b64 ieee_ops b) = narrow (B2R b).

Definition IEEE_SQRT32 : Prop :=
  forall b : b64, is_finite b = true -> format32 (B2R b) -> 0 <= B2R b -> B2R b <= FMAX32 ->
  is_finite (G_sqrt32 b64 ieee_ops b) = true /\ B2R (G_sqrt32 b64 ieee_ops b) = g_sqrt32 (B2R b).

Definition IEEE_RSQRT32 : Prop :=
  forall b : b64, is_finite b = true -> format32 (B2R b) -> 0 < B2R b -> B2R b <= FMAX32 ->
  is_finite (G_rsqrt32 b64 ieee_ops b) = true /\ B2R (G_rsqrt32 b64 ieee_ops b) = g_rsqrt32 (B2R b).

Definition IEEE_HYPOT32 : Prop :=
  forall b1 b2 : b64, is_finite b1 = true -> is_finite b2 = true -> format32 (B2R b1) -> format32 (B2R b2) ->
  sqrt (B2R b1 * B2R b1 + B2R b2 * B2R b2) <= FMAX32 ->
  is_finite (G_hypot32 b64 ieee_ops b1 b2) = true /\
  B2R (G_hypot32 b64 ieee_ops b1 b2) = g_hypot32 (B2R b1) (B2R b2).

Definition IEEE_EXP32 : Prop :=
  forall b : b64, is_finite b = true -> format32 (B2R b) -> B2R b <= XMAX ->
  is_finite (G_exp32 b64 ieee_ops b) = true /\ B2R (G_exp32 b64 ieee_ops b) = g_exp32 (B2R b).

Definition IEEE_CST : Prop :=
  forall c : gconst, is_finite (o_cst ieee_ops c) = true /\ B2R (o_cst ieee_ops c) = o_cst model_ops c.

Definition IEEE64 : Prop :=
  IEEE_NARROW /\ IEEE_SQRT32 /\ IEEE_RSQRT32 /\ IEEE_HYPOT32 /\ IEEE_EXP32 /\ IEEE_CST.
