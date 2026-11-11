# MATH-KERNEL — negative-control gate demonstration

**Scratch demonstration record. Not a ruling, not frozen, not in any repository.** Authorized by the owner's §3 b6
confirmation this session ("Authorize as restated", against the restated scratch-only scope). Grade: **MEASURED**
(exact-bit verdicts; the one-ULP math error is ESTABLISHED by the certified reference). Date 2026-11-10, owner's Windows
host. No frozen-artifact, repository, commit, push, or admission change — none authorized, none made.

**What this shows:** a conformance gate that **accepts the normative oracle and refuses all three mandatory defects**,
and whose own verification catches a weakened gate. **What it is not:** backend admission (no candidate backend is
admitted here) — it is a gate self-test. The gate judges **conformance to the oracle**, not correct rounding; the
characterization's eight certified 1-ULP counterexamples are properties of the frozen algorithm, never gate failures.

## 1. The gate

ADMIT a candidate **iff** (build-config: `ffp-contract=off`) **and** (exact output-bit agreement with the normative
oracle over the corpus). REFUSE otherwise, naming the reason. The gate **fails closed**: every fixture must exist and
match its pinned digest or the gate refuses to run (it never treats a missing/altered fixture as a pass).

- Gate logic: `gate.py` sha256 `60ac2284576e3f9c…` (scratch). Normative oracle = `test_oracle.exe` sha256
  `d1de73d0…` (the frozen Turn 72/73 build), pinned; the gate aborts `ORACLE-IDENTITY` if it is not that exact binary.
- **Fixture digests** (`negctl/fixtures.manifest.json`, verified at every run):

| fixture | sha256 |
|---|---|
| frozen_corpus (`MATH-KERNEL-S5-VECTORS-…csv`) | `622bf3a78964e6dc56a195e6b54f2daee52869c49c4f5c9c91ac982df81d3db8` |
| adversarial_corpus (`MATH-KERNEL-CHAR-CORPUS-…csv`) | `869788e678770676f9c69b5064a377f9425f75e0a954ab2b8855de242e354246` |
| certified_reference (`MATH-KERNEL-CHARACTERIZATION-RESULTS-…csv`) | `c1256e2071de98689f0ee141334693da68f4687f80e849e5b47942b904a4422a` |
| normative_oracle (`test_oracle.exe`) | `d1de73d0db367d3ec22a8920cf6fec8dea8f42d964dcbb447d171ce4df3ac960` |

- Corpus = union of the frozen kernel inputs (direct/reduction-stress/exceptional) and the adversarial characterization
  corpus = **127 distinct inputs** (finite + non-finite), each tested for sin and cos.

## 2. Positive control

The normative oracle, **rebuilt independently** here (same 6 frozen sources + driver, same flags), run as a candidate
against the frozen-oracle reference bits over the corpus: **ADMIT**, zero divergences. The rebuilt executable's sha256
differs from the frozen oracle's (clang embeds build paths/timestamps, so the exe hash is not reproducible), but
**every output bit over the corpus is identical** — which is what conformance measures. This establishes the gate
accepts the known-good realization, and that the oracle reproduces at the output-bit level across builds.

## 3. The three mandatory negative controls

Mutant **source** identity is the stable identity (exe hashes are non-reproducible build provenance). All three were
built with `clang 22.1.8`, `-std=c99 -O2 -ffp-contract=off -fno-fast-math -D__LITTLE_ENDIAN` (FMA control excepted,
see below), from the 6 frozen sources with one file replaced by a scratch mutant copy; **frozen originals unchanged**.

| control | mutant source (sha256, first 20) | exe (prov.) | expected reason | observed verdict / reason | defect exercised |
|---|---|---|---|---|---|
| **one-ULP** | `mutant_oneulp.c` `79f785749097949b74ae` (driver nudges the sin output of x=0.5 by +1 representable step) | `9861f8e2…` | exact-bit failure | **REFUSE** `EXACT-BITS:1` | sin(0.5)=`…f1` vs oracle `…f0`, **+1 ULP**; and **+1 ULP vs certified CR** `3fdeaee8744b05f0` → mathematically wrong (ESTABLISHED by the certified reference) |
| **FMA contraction** | same sources as oracle; built `-ffp-contract=fast -mfma` (forbidden contraction ON) | `bc3600a8…` | build/config or output-bit refusal | **REFUSE** `BUILD-CONFIG:contract=fast` | **output-equivalent on the corpus (0/127)** but **230/20000 divergences on a broad in-domain sweep** (1-ULP) → genuine behavioral mutant. It is refused by the **build-config** check; exact-bit conformance over the corpus alone would have ADMITTED it — this is why the build-configuration gate is necessary |
| **range-reduction** | `mutant_rem_pio2.c` `088e0a30789683746de0` (`pio2_1` corrupted +1 ULP: `0x3FF921FB54400000`→`…01`) | `67059bb6…` | targeted boundary-vector failure | **REFUSE** `EXACT-BITS:96` | **96 divergent outputs, ALL at `|x|>π/4` (reduction zone); 0 in the no-reduction zone `|x|≤π/4`** → the defect is exercised exactly at the reduction path, as intended |

Each mutant **reached the gate** (built with exit 0 and produced outputs for all corpus inputs — not rejected by an
unrelated build error). Each is **demonstrably non-equivalent** (the certified reference establishes the one-ULP math
error; the differential establishes the FMA and reduction deviations from the oracle).

### An equivalent mutant, excluded from the pass count
A first range-reduction attempt corrupted the **tiny low part `pio2_1t`** by 1 ULP (~6e-11). Re-exercised over the
corpus it produced **zero divergences — even at π/2** (MEASURED): the perturbation is below the final rounding. It is an
**equivalent mutant on this corpus** and is **excluded**; it was replaced by the `pio2_1` corruption above, which is
demonstrably non-equivalent. (This is why "corrupt a reduction constant" must be measured, not assumed.)

## 4. The gate's own verification (the gate is tested too)

All run in one pass (`gate.py`); full JSON in `negctl` / the scratch `gate_result.json`:

| self-test | result |
|---|---|
| positive control admitted | **PASS** (ADMIT) |
| all three mandatory controls refused | **PASS** |
| each control has its known expected refusal reason | **PASS** (one-ULP→EXACT-BITS, FMA→BUILD-CONFIG, reduction→EXACT-BITS) |
| a disabled/skipped control **cannot** be counted a pass | **PASS** (suite requires all three present+refused; with one skipped it does **not** report pass) |
| fail-closed on a missing fixture | **PASS** (`FIXTURE-MISSING`, gate refuses to run) |
| deterministic verdict on repeated runs | **PASS** (re-run: identical verdicts for all four candidates) |
| a deliberately weakened gate is caught | **PASS** — see below |

**Weakened-gate detection.** The gate's self-test requires *all three mandatory controls to be refused*; any weakening
that lets a control through breaks that property and is caught. Each weakened variant, run over the mandatory controls,
**admits** a control it must refuse:

| weakened gate | admits (must-refuse) | caught |
|---|---|---|
| tolerance ≥1 ULP (ignore ≤1-ULP errors) | one-ULP | **yes** |
| subset-corpus (skips the one-ULP input) | one-ULP | **yes** |
| skip the build-config check | FMA | **yes** |
| always-admit | one-ULP, FMA, reduction | **yes** |

## 5. Reuse of the graybox battery (as fixtures, not inherited proof)

The graybox has **no single "11-mutant battery"**; it has two sets: `rules_ref.py` has 3 arithmetic plants (one trig),
`tick_ref.py` has 6 tick mutants (one trig). **Only two are sin/cos-kernel-relevant**; the other seven (fall-order,
move-halving, shoot-sign, stand-again, cells-from-centre, sqrt-one-place-up, Math.cos-in-tick) are not conformance
mutants of the trig kernel and are **not inherited as proof**. The two relevant ones were inspected and re-exercised
against the new gate:

- **`tick_ref._sin_short`** — sine kernel polynomial cut after x⁵ (drop S3…S6), rebuilt in C (`mutant_kshort.c`
  `98194f04f64e71cfee4b`, exe `22f7892b…`): **REFUSE** `EXACT-BITS:52` (10 of them at `|x|≤π/4`). Caught by the new gate.
- **`rules_ref` one-bit-off** — `xsin` low-bit flipped at the graybox's own argument. That argument is **617.32**
  (bits `40834a956a2e549d`), **outside this capability's domain `[−1.45,2π)` and not a corpus point**; re-exercised
  verbatim it is **ADMIT = equivalent on this corpus**, so it is **excluded, not inherited as proof**. Its defect class
  (a 1-ULP sine error at a selected argument) is covered, in-corpus, by the mandatory one-ULP control, which **is**
  refused. This is a concrete instance of why a mutant that fails the graybox's own 20000-argument digest is **not**
  automatically caught by a corpus-based gate on a different argument set.

## 6. Verdict and boundary

**Milestone reached: the gate accepts the normative oracle and refuses all three mandatory defects, and its own
verification is sound (fail-closed, deterministic, skip-proof, weakening-proof).**

- **MEASURED.** Does not show: (a) that the corpus catches *every* defect — the FMA mutant is output-equivalent on the
  corpus (caught only by the build-config check) and the graybox one-bit-off mutant is equivalent on the corpus; a gate
  is only as strong as its corpus *and* its config check together. (b) It is not backend admission. (c) Exe hashes are
  not reproducible; identity rests on source digests + output bits.
- **Falsifier:** a mandatory control that the gate ADMITS; a positive control the gate REFUSES; or a weakened gate that
  the self-test fails to catch.
- **Excluded from the pass count:** the `pio2_1t` equivalent mutant (§3) and the graybox one-bit-off mutant (§5).

## 7. Provenance
clang 22.1.8; scratch venv `orlog-review\.charvenv` (MPFR/Arb/mpmath) for the certified-reference evidence; scripts
`build_mutants.py` `d09a26ea…`, `gate.py` `60ac2284…`, `battery_reuse.py` (scratch). Frozen fdlibm originals and the
freeze record `MATH-KERNEL-FIRST-CAPABILITY-FROZEN-…md` (`9de3943b…`) unchanged. Nothing in this record is a decision
or a frozen artifact.
