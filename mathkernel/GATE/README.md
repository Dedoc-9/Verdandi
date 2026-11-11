# mathkernel — the conformance gate and its negative-control self-test

The gate admits a candidate backend **iff** (build-config: `ffp-contract=off`) **and** (exact output-bit
agreement with the normative oracle over the corpus). It judges **conformance to the oracle, not correct
rounding**. It **fails closed** on a missing/altered fixture.

- `gate.py` — the gate + its self-tests (positive control + three mandatory negative controls + the
  weakened-gate detection). **This is the demonstration of the gate, not a backend admission**: no backend
  is admitted here.
- `build_mutants.py` — the recipe that builds the three mandatory controls (one-ULP output corruption;
  FMA-contraction; range-reduction-constant defect) from the oracle sources.
- `MATH-KERNEL-NEGATIVE-CONTROL-REPORT-2026-11-10.md` — the authoritative result (MEASURED): the gate
  **accepts the rebuilt oracle and refuses all three mandatory controls**; all eight gate self-tests pass
  (positive admitted; controls refused with known reasons; a skipped control is not a pass; fail-closed on
  a missing fixture; deterministic; every weakened gate caught). Two equivalent mutants are excluded from
  the pass count, as recorded.

## Reproduction (as-run provenance)
`gate.py` and `build_mutants.py` are the **as-run scratch scripts**: they carry absolute scratch paths from
the authoring host (`Desktop\orlog-review`) and use a certified-reference venv (MPFR/Arb/mpmath) for the
one-ULP math-error evidence. To reproduce inside this subsystem: build the oracle from `../ORACLE/src` per
`../ORACLE/BUILD-RECIPE.md`, point the scripts' base paths at this subsystem's `ORACLE/`, `CHARACTERIZATION/`,
and `test_oracle.exe`, and run `gate.py`. The committed **report** is the evidence of record; the executable
is not committed (exe hashes are non-reproducible — conformance is measured on output bits).
