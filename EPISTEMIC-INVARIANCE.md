<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2026 Daniel J. Dillberg -->

# The Epistemic Invariance of the Boundary

*A synthesis theorem for how a performance court must legally isolate execution states, so that the cost of a
hardware layout mutation can be extracted cleanly.*

**Author:** Daniel J. Dillberg · **Origin:** the `LOCALITY-0` court of `Verðandi` · **Status:** foundational
principle of the GAUNTLET measurement methodology. This document records the theorem as intellectual property of
the author and states, honestly, both what it asserts and where its formalism is a goal rather than a proof.

---

## Motivation

When a renderer is fought down to a microsecond-scale hardware bottleneck (in `Verðandi`, an `emit` p99 of
4,734 µs after `GAUNTLET-1c`), the two obvious ways to compare two optimization vectors both leak:

- **Two loose runs (separate invocations, separate patches)** leak *macro-environmental drift* — thermal ramp,
  frequency scaling, background load — so an 18%-class margin can flip on run-to-run variance.
- **One combined runtime loop (both variants timed back to back in one process)** leaks *microarchitectural
  cross-talk* — the branch predictor and BTB carry the leading variant's history into the trailing one's tail,
  and packing both address generators into one hot loop bloats the instruction footprint until a *data*-locality
  test silently becomes an *instruction*-locality test.

The theorem states the boundary condition under which neither leak occurs.

---

## The five constituent axioms

The theorem synthesizes five foundational axioms of deterministic systems engineering, each drawn from one of
the author's systems:

1. **The Chained-Identity Axiom (Urðr).** State transitions are valid iff they reduce to a canonical, verifiable
   hash chain: `S_ECHO(A) ≡ S_ECHO(B)`.
2. **The Monotone Lattice Theorem (DVSM).** When execution bounds are tightly sealed, communication is not sent
   over a wire; it is structurally locked and already true within the compiler space.
3. **The Bounded-Memory Law (Hainuwele).** Active working sets must exist inside strict, predictable spatial
   allocations with `O(record)` allocation, free of dynamic runtime scaling.
4. **The Triple-Authority Firewall (Verðandi).** The representation shell holds zero truth; core semantics must be
   structurally immune to presentation and authoring interventions via compile-time typestate walls.
5. **The Non-Destructive Inversion Principle (Ursprung).** Temporal reconstruction is an immutable concatenation
   homomorphism over an event stream, not a stateful, destructive mutation.

---

## The theorem

> **Epistemic Invariance of the Boundary.**
>
> ```
> Ψ_court(L₀)  ⟹  ∮_{∂Ω} Ξ_layout(k) · dτ  ≡  Λ_anchor
> ```
>
> **Statement.** The absolute physical cost of a hardware layout mutation can be cleanly extracted only if the
> execution boundary `∂Ω` remains *microarchitecturally static* across measurements. To prevent cross-variant
> contamination while eliminating macro-environmental drift, the execution environment must be hot-swapped **at the
> binary boundary** — via compile-time monomorphization or clean programmatic execution forks — so that the
> underlying CPU instruction stream is bitwise-invariant *up to the literal address-generation instructions*.

Read plainly: hold everything constant except the address arithmetic under test, and change *that* only by
swapping the whole binary code path, never by branching between variants inside one live loop.

---

## The engineering translation

The theorem's operational content, stripped to what a build must do:

1. **Monomorphize each layout into its own code path** — a `const`-generic index function, so only one variant's
   address-generation instructions exist per compiled build. (Chained-Identity: each build is one canonical path.)
2. **Isolate at the process boundary** — one variant per process invocation, so each measurement begins with a
   clean branch-target buffer and a single variant's instruction-cache footprint. (Monotone Lattice: the boundary
   is sealed at the binary, not negotiated at runtime.)
3. **Interleave the invocations** — alternate the variants in tightly interleaved, pre-warmed strips over a short
   sweep, and strip environmental outliers, so slow thermal drift cancels between neighbours. (Bounded-Memory: a
   fixed, predictable measurement footprint per strip.)
4. **Compare against a same-process baseline** — each variant is timed against the frozen-emit baseline measured in
   *its own* process, and the orchestrator compares the two baseline-relative improvements (ratios, not raw
   microseconds), so per-process baseline drift cancels. (Non-Destructive Inversion: the comparison is a pure fold
   over the strip stream, order-independent up to interleaving.)
5. **Never let the shell touch the truth** — the measurement apparatus is fenced from the certified renderer; the
   output is proven byte-identical to the frozen oracle regardless of layout, so appearance is invariant while the
   execution format moves. (Triple-Authority Firewall: content provenance is structurally separated from execution
   format.)

---

## First application: `LOCALITY-0`

`LOCALITY-0` is the theorem's first court. It compares two floor-tile execution formats — an 8×8 cache-blocked
layout and a Morton (Z-order) space-filling curve — each a lossless bijection over the tile, each proven
byte-identical to the frozen `Urðr` oracle, each with its address-generation tax isolated. The two variants are
hot-swapped by `--variant` on the *same* binary and interleaved across process invocations, so the only quantity
that moves between measurements is the address arithmetic. The court has three honest exits: blocked wins, Morton
wins, or **neither** beats the baseline — which is not a null but a proof that the tile-fetch stall is a
capacity/LRU miss no permutation can fix, redirecting the trajectory to `GAUNTLET-2` (parallelism) to hide the
latency behind compute.

---

## Honest limits of the formalism

This document does not overstate its own theorem. Two limits are recorded so the principle is a tool, not a
talisman:

- **The contour is a metaphor, not a computed integral.** `∮_{∂Ω} Ξ_layout(k) · dτ ≡ Λ_anchor` names the desired
  invariance — that the boundary integral of the layout's cost reduces to the constant anchor tax — but it is a
  *structuring* statement, not a quantity the build evaluates. What the build actually proves is *output*
  invariance (byte-identity against the oracle) and constant *anchor* tax (the RE-BREAKDOWN-1b constant-anchor
  probe); the instruction-level "bitwise-invariance up to address-generation" is a best-effort of code structure
  that a compiler may schedule around, and it is not gate-provable. The record says so rather than asserting it.
- **Process isolation trades cross-talk for cold starts, and interleaving cancels slow drift, not fast spikes.**
  A fresh process begins with a cold data cache — which is *more* render-representative, not less — and each
  invocation self-warms before it samples. Interleaving removes the thermal ramp; it does not remove a one-off
  background spike inside a strip. The robust statistic is therefore the median across interleaved strips with
  outliers stripped, reported as a distribution, never a single hero number.

The theorem earns its place by making the measurement *fair*, not by making it *certain*. Certainty is the gate's
job (byte-identity); fairness is the boundary's.
