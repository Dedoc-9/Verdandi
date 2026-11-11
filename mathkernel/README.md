# mathkernel — an independently governed numerical subsystem

A deterministic math kernel (first capability: **sin/cos** over a declared game domain) with an
**earned-admission** architecture: an LLM-generated candidate backend earns admission against an
**independent** frozen oracle + contract, or is refused. This subsystem is a **peer of `art/`,
`graybox/`, `design/`** — it sits **outside the 251-row gate** and carries **its own check, no gate row**
(the owner's gate-stops-growing ruling, 2026-10-09).

**The rule under every rule:** a claim is only as strong as the check behind it. `integrity ≠ truth`,
`declared ≠ verified`, `built ≠ adopted`. Read the code, not the prose.

## Authority (D1) — governed here, not by Verðandi's gate
The kernel retains its **own** contract, oracle provenance and identity, independent characterization, and
conformance/admission records, under its **own freeze and succession** (`FROZEN/`), **distinct from**
Verðandi's 251-row gate, its registers, and `RUNGS.md`. Repository topology does not determine numerical
authority. A change to a frozen file here is a **kernel succession event** (owner's word + replay + recorded
delta), not a gate amendment.

## Dependency (D2) — strictly one-way
Consumers depend on the kernel through the **one logical public API** (`interface/`) only. The kernel
**imports nothing above it** (no Verðandi/Ørlǫg internals, no host libm) and is independently buildable and
verifiable. Language adapters are subordinate to the interface and expose only it. Consumers never reach the
oracle, the characterization, or any implementation internal.

## Map

| path | what |
|---|---|
| `FROZEN/` | the frozen numerical contract (guarantee, 5 conditions, S1–S6, domain, policies, corpus) + the oracle **source identity** (Sun fdlibm 5.3, pinned by sha256) |
| `ORACLE/` | the oracle **sources** (`src/`) and its reproducible **build recipe** (`BUILD-RECIPE.md`, `-ffp-contract=off -fno-fast-math`). No executable is committed — conformance is measured on output bits |
| `CHARACTERIZATION/` | the independent characterization (MPFR + Arb certified reference) + results + the retained adversarial corpus + the tooling |
| `GATE/` | the conformance gate + its negative-control self-test + the report (gate accepts the oracle, refuses the three mandatory defects; the gate is itself tested) |
| `interface/` | the one logical public API + its reference C binding |
| `DECISIONS/` | the architecture decisions (D1–D3b + enforcement), the destination sheet, and the PR proposal — the subsystem's charter |
| `check.py` | the boundary check (no gate row): fails on any upward dependency or consumer internal-reach; planted canaries in `test/` prove it bites |
| `test/` | the planted canaries |

## What this landing is — and is NOT
- **IS:** the kernel's authority, its independent evidence (characterization + a gate demonstrated to refuse
  defects), its enforced boundary, and its public interface.
- **IS NOT:** a backend admission. No backend is admitted. The existing graybox `sin`/`cos` are bit-identical
  to the oracle and are the natural first admission candidate — **later, on its own word**. Also deferred:
  the native/optimized backend, `atan2` and further capabilities, rewiring the live simulation to consume the
  interface, and the long-term Ørlǫg/Verðandi repository unification (the target topology; the history
  migration decided separately and later).

## Ghosts (what the evidence does not prove)
- The characterization is 242 certified points + a hard-to-round search, **not** a whole-domain proof of
  ≤1 ULP; its adversarial corpus overstates the disagreement density versus uniform sampling.
- The gate is only as strong as its corpus **and** its build-config check together (the FMA control is
  output-equivalent on the corpus; the build-config check is what catches it).
- The conformance guarantee is controlled-build-scoped; a different toolchain is a different claim.

## Verify
- `python check.py` → `MATHKERNEL CHECK PASSED` (planted canaries caught).
- The gate's result of record is `GATE/MATH-KERNEL-NEGATIVE-CONTROL-REPORT-2026-11-10.md` (MEASURED).
- The kernel adds no gate row and must not perturb Verðandi's gate: `verify/verify.py` stays `GATE PASSED`,
  251 rows / 0 fail, fences green.
