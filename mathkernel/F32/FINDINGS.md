# mathkernel/F32: review findings F1 to F5

Status of the subtree: an unfrozen, unadmitted candidate family; nothing here is adopted (`README.md`).

## Which review this is

- The review of 2026-11-15, made by an AI model **of the same model family as the tier's author and provers**, in an
  invocation separate from those that wrote the proofs. It worked on fresh copies, with the same container image and
  on the same host. (An earlier review, of 2026-11-14, is cited by staged files; it is of that family too, DECLARED,
  and the three dated notes answer it. This file is not about it.)
- Its result: **no blocking defect; five findings, F1 to F5**, each graded not blocking by the reviewer.
- Each finding was then checked against the files by the tier's author, and each was confirmed (READ at the places
  given below). The reviewer's report and that check are working papers of origin and are **not in this subtree**;
  this file carries the findings. The report is not quoted whole. The check found one of its justifications wrong
  and refined one of its judgments:
  - Wrong: it said the premises of the `ieee64` statement "are not vacuous (finiteness of the result genuinely
    requires them ...)". The premises can be met, so they are not vacuous; but finiteness does not require them all.
    For `sqrt32` the same conclusion was proved on origin without the premise x <= FMAX32, and for `narrow` the
    conclusion holds well beyond its premise. The report's own finding F1 says `sqrt32` needs no bound.
  - Refined, not wrong: it called `hypot32`'s domain "right" and added that HYPOT32_SHARP "proves it cannot be
    dropped". Both are true as far as they go. The premise is sufficient and not necessary (`CLAIMS.md` section 2.4):
    that is an addition the review did not state and did not deny, not an error it made.
- The reviewer read this file against its own report on 2026-11-16, accepted the first point and corrected how an
  earlier wording of this file described the second and the section "What the review did not find". Those
  corrections were checked against the report's text before they were made here.
- Grade of this section: DECLARED. No staged record of the review exists beyond this file.

What this review is not: it is **not a review by another model family, and not a review by a human expert**. No
such review exists. Agreement between models of one family is corroboration, not proof.

## The findings

| | finding | checked | status | answered by |
|---|---|---|---|---|
| F1 | The header comment of `p32/P32_Statement.v` (lines 7 to 8) says the inputs are "below 2^128", but SQRT32 has no such premise. | confirmed (READ: the comment and the definition) | **answered by a dated note; the statement's bytes are unchanged** | `p32/P32_Statement.NOTE-2026-11-14.md` lines 24 to 25: "SQRT32 has no range premise and needs none"; HYPOT32's two range premises are not used by its proof. The missing range statements are `p32r/P32R_Statement.v`. |
| F2 | `narrow` and its constants are written once for each language inside `orl/emit.py` (Coq, C, Python, the corpus law); only the Coq graph is held to its generator by a gate. | confirmed (READ: `orl/emit.py`) | **not answered: disclosed.** Partly measured | `orl/evidence/narrow-regress-run3.txt` (the C and Python `narrow` agree line for line and on 32,185 inputs) and `orl/evidence/graph-agree-run2.txt` (sampled graph against program) bear on it; neither shows that the renderings are one definition. `orl/emit_nm.py` and `orl/emit2_nm.py` add two more copies. |
| F3 | "Frozen before its proof", as the statement files' headers say, rests on no record. | confirmed (READ: `gate/gate4.py` lines 35 to 36) | **not answered: disclosed** | `gate/gate4.py` lines 35 to 36 and each `FROZEN4.txt` header say the list is written after the proofs. The claim is DECLARED only (`CLAIMS.md` section 4). |
| F4 | One author and one model family throughout: statements, proofs, gates, tests. | confirmed; and the reviewer is of that family too | **not answered: accepted at the candidate stage** (see the residual risk below) | none |
| F5 | The exhaustive `narrow` sweep leaves out the 7 test values at and above the largest binary32 number. | confirmed (READ: the line) | **answered by a separate test and two theorems, on the earlier program** | The line is `orl/gen-nm/sweep.c` line 63 in the staged C (the reviewer cited the corresponding line of the earlier program, `orl/gen/sweep.c` line 43, a file not in this subtree). Covered by `orl/evidence/narrow-top-run2.txt` (`NARROW TOP HELD: ...`, run on the earlier program) and by NARROW_FINITE and NARROW_SHARP in `p32r/`. No record covers the top values on the staged C. |

Two numberings, not to be confused: the three dated notes (`*_Statement.NOTE-2026-11-14.md`), `p32r/P32R_Statement.v`
and several script headers cite findings such as "F1, F2, F4, F5, F6, F9, F12" of **an earlier review of
2026-11-14**. Those are that review's numbers. They are not the F1 to F5 of this file.

## What the review did not find

Stated because a review's silence is easily read as a pass. Before the review, four points were known to the tier's
author and withheld from the reviewer, to measure the review against them. It raised none of the four as a finding of
its own. Two notes, so that no contradiction is attributed to the report that is not in it. On the first point the
report did repeat the gate's own caveat, that a premise plant is refused by the route of the proof and not by showing
the statement without the premise false; it did not say which plants are therefore not demonstrations, and it wrote
that no plant that changes nothing is counted as caught, which the two mode plants stand against if the argument made
on origin that they are equivalent is right (that argument is not a proof). On the second point the report treated
the IEEE-level correspondence and the faithfulness theorems as separate results and claimed no composition.

<details>
<summary>The four points</summary>

1. Three of the 38 plants of the `ieee64` gate are not demonstrations: on origin one was proved true without its
   premise and two were argued to be equivalent mutants. The staged text says only that the first is refused by the
   route of the proof (`CLAIMS.md` section 3).
2. The composition of the IEEE-level statement with the tier's other theorems is stated nowhere.
3. The IEEE-level theorem cannot see the sign of a zero (the reviewer repeated the statement's own header, without
   a check of its own).
4. The run-time floating-point environment is unnamed in the statements. It is now named as a boundary
   (`CLAIMS.md`, THE BOUNDARY); it is still not enforced.

</details>

Grade: DECLARED (the record of this comparison is not in this subtree).

## The residual risk

Every prover and every reviewer of this tier is of one model family. An error that family tends to make, in a
statement, in a proof's reading or in a test's design, can pass every check made here: the risk of correlated error
remains. By the repository owner's ruling of 2026-11-16, landing this family as an unfrozen, unadopted candidate
does not require a review by another model family; this risk is accepted at the candidate stage, and it is revisited
before any adoption or freezing.

(The paragraph above restates the ruling; it is not a quotation of it. The ruling's own words are in the owner's
records.)
