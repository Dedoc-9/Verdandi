# Deterministic math kernel — numerical contract decision sheet (2026-11-10)

**Status: SCRATCH DRAFT in `orlog-review`. RATIFIED 2026-11-10 (owner's orders) — §1 the guarantee, the five
oracle-life conditions (§2), the negative-control property (§3), the three-artifact architecture (§4), and ALL of
S1–S6 (§5) including the S5 input-domain selection (the explicitly bounded, post-wrap _game_ domain, NOT all finite
binary64; general-purpose trig is a separate successor capability). The contract's choices are now complete. Remaining
before oracle freeze: draft the *concrete* S5-domain spec (exact interval, endpoints, non-finite + out-of-interval
behavior, vectors) and the oracle-provenance plan — both scratch. Recorded in scratch; recording any of it into a
repository needs a clean §3-b6 confirmation. Nothing is built; nothing is written to any repository or to the red-team
charter (still a proposal).**

## 0. Provenance of this sheet

- **Assistant's restatement (this session), the guarantee put for adoption:** specified-frozen-algorithm as the trig
  guarantee, no correct-rounding claim — *given the same admitted contract and inputs, every conforming backend
  produces exactly the same specified output bits; conformance is agreement with the frozen algorithm, not a claim of
  correctly-rounded results; under four conditions (normative pinned oracle; whole-domain contract; independent oracle
  characterization; re-admission on any bit-affecting change).*
- **Owner's confirmation (verbatim):** "adopt it".
- **Owner's directives for this sheet (verbatim), integrated below:**
  - *"Succession must be a named condition, not an anticipation … any oracle revision, platform retirement, or contract
    repair is a succession event — requiring the owner's word, replay of all admitted capabilities against the new
    oracle, and a recorded delta of which capabilities re-earn admission."*
  - *"Scope the guarantee sentence to controlled builds — or it overpromises … within the controlled build
    configuration recorded at admission …"*
  - *"the negative control stays a standing gate property … and the three-artifact separation — oracle, contract,
    candidate as independently governed items — should appear in the sheet's architecture sketch, since it's the reason
    the guarantee is trustworthy when the generator is an LLM."*
- **Drafting recommendations (relayed by the owner, not themselves rulings):** the precise condition wordings below are
  integrated as proposals, to be ratified.

## 1. RULED — the numerical guarantee (owner: "adopt it")

**Guarantee (specified-frozen-algorithm, controlled-build-scoped):**

> Within the controlled build configuration recorded at admission, every conforming backend produces exactly the same
> specified output bits for the same inputs. Conformance is agreement with the frozen algorithm — **not** a claim of
> correctly-rounded real-valued results. Any change to a bit-affecting toolchain, compiler, flags, target features,
> build semantics, or floating-point environment triggers re-verification before the affected capability retains
> admission.

- Cross-backend bit-determinism *within the recorded build* is the guarantee; universal platform portability is **not**
  promised (a distro's ifunc dispatch or a distro-patched compiler could break a naive "every platform" claim).
- Correct-rounding is deferred to a possible later, separate capability or contract revision — never a cost on the
  first trig capability.
- **Persistent distinction, kept throughout:** oracle agreement proves conformance to the *specified algorithm*, not
  correctness relative to the real-valued mathematical function.

## 2. RULED (ratified 2026-11-10) — the five oracle-life conditions

Four from the recommendation, plus succession as the fifth per the owner's directive.

1. **Normative oracle.** Pin the exact fdlibm-derived source, revision, patches, constants, build semantics, and
   executable provenance. The name "fdlibm" is not a specification.
2. **Whole-domain contract.** Signed zero, NaN/∞, subnormals, rounding mode, FTZ/DAZ, extreme arguments, and atan2
   quadrants have *specified outcomes*, not merely test cases.
3. **Independent oracle characterization.** Record the oracle's accuracy and limitations against high-precision
   mathematical references. Agreement establishes conformance, not mathematical correctness.
4. **Re-admission on any bit-affecting change.** Every change that can affect output bits passes the same frozen-oracle
   gate; a performance measurement never substitutes for it. Admission is bound to the recorded build configuration
   (condition 1's provenance + the guarantee's toolchain-binding). **Change classification:** a *candidate* change →
   re-verification; a *toolchain* change (compiler / flags / target features / FP environment) → re-verification under
   the *unchanged* contract, **not** automatic oracle succession; an *oracle or contract* change → the succession
   procedure of condition 5.
5. **Succession (new, owner's directive).** Any oracle revision, retirement, replacement, or contract repair is a
   *succession event*: it requires the owner's explicit authorization, replay of every previously admitted capability
   against the successor oracle, and a recorded capability-by-capability delta (retains / must re-earn / loses
   admission). No prior admission transfers automatically. The old oracle, contract, and admission records are
   preserved as historical evidence — succession creates a new lineage, it does not rewrite the old one.

## 3. RULED (ratified 2026-11-10) — negative control as a standing gate property

The gate's **permanent** regression suite includes known-invalid candidate plants — at least a one-ULP corruption, a
forbidden FMA contraction, and a range-reduction defect — re-run on **every** gate revision, not a one-time Step-4
demonstration. A gate that admits a negative control is itself unfit to confer admission: the gate is subject to
verification too.

## 4. RULED (ratified 2026-11-10) — architecture: three independently governed artifacts

- **Frozen oracle** — defines the normative output bits; independently sourced, versioned, characterized.
- **Numerical contract** — defines the guarantee, domain, exceptional values, FP environment, conformance rules.
- **Candidate implementation** — generated or hand-written backend; independently tested, admitted or refused.

The admission gate evaluates the candidate against the contract and the oracle. **The candidate cannot modify either
authority.** Each artifact carries its own version identity and change authority. An LLM-generated candidate must never
supply its own oracle, redefine the contract, or certify its own conformance — that separation is why the guarantee
holds when the generator is an LLM (the correlated-error / three-way-agreement failure the whole design exists to
prevent).

## 5. RULED (ratified 2026-11-10) — semantic sub-choices S1–S6; the S5 input-domain *selection* stays OPEN

Each needs an explicit specified outcome. Proposed default (LEAN) = the frozen fdlibm-derived oracle's own behavior,
pinned bit-for-bit, unless noted.

| # | choice | proposed default (LEAN) |
|---|---|---|
| S1 | sin(±0), cos(±0) | sin(+0)=+0, sin(−0)=−0, cos(±0)=+1 (oracle behavior), signs preserved downstream |
| S2 | atan2 over every signed-zero / ∞ combination | the oracle's full quadrant table, pinned explicitly (not inferred) |
| S3 | NaN / ∞ inputs → outputs | **oracle-preserving**: reproduce the oracle's exact NaN/∞ behavior, including observable payload/sign propagation. **No added canonicalization** unless independent characterization shows a concrete need — which would make the normative algorithm "oracle + canonicalization", frozen explicitly as such (not unmodified fdlibm) |
| S4 | subnormals + floating-point environment | FTZ/DAZ **off**, round-to-nearest-even, pinned in the build config |
| S5 | range reduction + input domain | **RULED (2026-11-10): the first capability's input domain is the explicitly bounded, post-wrap _game_ domain — NOT all finite binary64** (general finite-binary64 trig is a separate successor capability with its own reduction, oracle characterization, and admission). Pin the reduction algorithm, constants, and intermediate precision bit-for-bit **even within the narrow domain**. Before oracle freeze the *concrete spec* fixes: the exact binary64 input interval + endpoint inclusion; non-finite handling (handled or refused); exact out-of-interval behavior; **wrapping is law-level only** (the kernel receives an already-normalized argument and never re-wraps — ties to S6); boundary + signed-zero test vectors. The interval derives from the law's post-wrap yaw [0, 2π) and clamped pitch [−pitch_limit, +pitch_limit]. |
| S6 | angle-wrap order in the law | wrap/normalize yaw **before** evaluating sin/cos; wrap interval and endpoint behavior pinned in the law text |

## 6. Governance / status

- **RULED:** §1 the guarantee (owner's "adopt it" to the assistant's restatement above). **Provenance verified:**
  "adopt it" is the owner's own message (a user turn, not relayed/pasted), answering the precisely-stated guarantee —
  so §1 is grounded, not inherited from an unverified founding entry. Caveat: "adopt it" suffices for this scratch
  sheet; before §1 is ever recorded *into a repository* (a consequential write), a clean restatement will be put for an
  ironclad §3-b6 confirmation.
- **RATIFIED (2026-11-10, owner's orders "follow this as my order" and "Take the narrow, game-matched domain"):** §2
  (all five conditions, incl. succession, historical-lineage preservation, and condition 4's change classification),
  §3, §4, and all of S1–S6 — including the S5 input-domain selection (the explicitly bounded, post-wrap game domain,
  not all finite binary64; general-purpose finite-binary64 trig is a separate successor capability). Assistant's
  restatements are on the conversation record; a repository recording of any of it still needs a clean §3-b6
  confirmation.
- **Remaining (scratch drafting, not open rulings):** the *concrete* S5-domain spec (exact interval + endpoints,
  non-finite handling, out-of-interval behavior, boundary/signed-zero vectors) and the oracle-provenance plan. This
  authorizes none of — building the oracle, implementing trig, changing the charter, or writing to a repository.
- **Scratch only.** This sheet lives in `orlog-review`; nothing is written to any repository or to the charter. The
  red-team charter remains a proposal. Building the oracle / contract / trig, or recording any of this into a repo, is
  a later step under your explicit word (§3 b6).
- **Latency lens (your note):** the frozen-algorithm guarantee is the lower-latency determinism-preserving choice;
  closing the latency gap Verðandi established is pursued through optimization-as-search over candidate implementations
  that each re-earn admission through this gate — the specific gap to be pinned from Verðandi's own records
  (the graybox `--bench` draw/readback timing, the 0267 verification-cost/throughput measurements) before any
  optimization begins.
