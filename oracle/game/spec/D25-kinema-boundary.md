<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# D25 — KINEMA, the discrete-to-continuous refinement boundary (the cinematic membrane)

Status: **PROSPECTIVE — a preregistration, not an implementation.** No `kinema` module exists at the
commit that writes this. D25 states the boundary and the falsifiable questions a future `kinema`
(URDRKIN1) must submit to, before there is code to define them retroactively — D24's move, one layer
down: a line drawn after the code describes the code, a line drawn before it is a contract. Nothing
here is MEASURED; every relation below is a **candidate**, graded DECLARED, and named as such. Its
correctness test is **retro-admission**, D17's shape and D24 §8's: when the first `kinema` module
lands it must classify cleanly under §2 and satisfy the falsifiers of §10, or D25 is wrong and is
amended *before* the module is graded. The implementation does not get to define the contract after
the fact.

> **LANDED — 2026-09-19 (URDRKIN1).** `kinema` now satisfies this preregistration by RETRO-ADMISSION and
> the contract below was NOT amended to admit it. It classifies cleanly under §2 (it PRODUCES a view of
> canonical state; it does not AFFECT state), consumes a real `enact` transition `D_n → D_{n+1}` that
> `statecanon` identifies rather than synthesising one, refines the entity POSITION in observer space over
> the frozen Q32.32 substrate (never the digest), consumes `descent.traversable` for containment (§4), and
> bites the §10 plants: Plant A (a BLOCKED move presented as motion, target a wall) and the realizable form
> of Plant B (a forged non-adjacent/wall-crossing pair) refuse `KINEMA-REFUSE`; Plant C is the full-AST
> direction-aware one-way guard (which also closes the function-local import escape hatch the tree's earlier
> guards left open) plus the observer-presence differential of §14; Plant D is sampling invariance; Plant E
> is the one-ULP perturbation, observable on the moving axis. Two §10 items are honestly recorded as NOT
> realizable under the currently earned single-cell MOVE vocabulary and are DEFERRED rather than
> manufactured: the literal `A─X─B` intermediate-wall containment (there is no cell between two adjacent
> cells) and a bounded-i64 arithmetic model (§6 — a cross-placement obligation, the arithmetic is graded
> reference on the frozen radix until then). The prospective text below is preserved as the contract
> `kinema` was admitted against.

Capability: `URDRKIN1` (proposed). Substrate: Q32.32 fixed-point view coordinates (proposed).
Authority: the existing canonical discrete game state — `gamegen` (URDRGEN1) and its topology witness
`descent` (URDRDSC1). Position in D24: **view-side refinement under §5 and §6**; no authority crosses
the boundary. This document extends D24 rather than restating it, and inherits D15's view contract
and the four-layer `CORE` / `VIEW` / `ALLOCATOR` / `OBSERVER` discipline unchanged.

## 1. Purpose

Urðr's canonical simulation is deliberately discrete, deterministic and authority-bearing. Rendering
benefits from a continuous-looking trajectory: motion between authoritative ticks, fractional camera
positions, an arbitrary number of visual frames per simulation step. KINEMA reconciles the two
**without weakening the authority model**.

KINEMA is **not** a second simulation, a physics engine, a prediction system, or a source of
canonical state. It is a one-way refinement membrane:

```text
        canonical discrete state
                 │  read
                 ▼
        continuous view refinement
                 │  render only
                 ▼
             visual frame
```

There is deliberately no reverse arrow. **A rendered frame may witness canonical state; it may never
become an input to it.**

The danger this boundary exists to close is the gap between *"the simulation says you cannot be
there"* and *"the renderer temporarily shows you there."* That is the **temporal-spatial leak**, and
§10 is careful about what it is: a false visual witness is a different, weaker failure than authority
contamination, and the plants must keep the two apart.

## 2. The boundary question

Every KINEMA operation answers one question — D24 §1, applied here:

> **Is this operation changing canonical game state, or producing a view of canonical game state?**

There are only two answers. If it changes canonical state it belongs to the authority side and is
governed by the existing simulation rules. If it produces a visual representation of canonical state
it belongs to KINEMA. A module doing both is two modules and is separated. This preserves the D24
`CORE` / `VIEW` split at the point where the temptation to blur it is strongest, because in a game
the view is the product and the state is invisible.

## 3. The proposed refinement relation — CANDIDATE

Let `D_n` be the authoritative discrete state at tick `n`, `α` a fixed-point interpolation parameter
in `[0, 1]`, and `R(·)` the rendering projection. KINEMA proposes that a visual state may **refine**
an authoritative transition, with the view derived **solely from the authoritative endpoints**:

```text
    D_n ─────────────► D_{n+1}          (authority)
              │ refinement
              ▼
          G(α),  0 ≤ α ≤ 1              (view)

    G(α) = D_n + ((α · (D_{n+1} − D_n)) >> Q_SHIFT)     computed in Q32.32
```

The property that matters is **not** that the view is continuous in an abstract sense. It is that the
refinement **cannot acquire authority**: the renderer sees `G(α)`; the simulation does not. This is a
candidate shape only, and §15 requires it to be measured against the real `gamegen`/`descent`
representation before it is promoted to a law.

## 4. Proposed containment law — CANDIDATE, and deliberately too weak as stated

The first candidate law is a refinement-containment property: for a permitted authoritative
transition, every rendered sample stays within the authoritative domain it belongs to. Its simplest
cell-based form is

```text
    floor(G(α)) ∈ { D_n, D_{n+1} }        for every permitted sample α
```

**This is a candidate formulation, not a theorem, and it is not enough.** It must not be confused
with a collision or topology law, and it must not claim more than it establishes:

- If the real world permits transitions **through** intermediate cells, the law must represent those
  cells explicitly — endpoint membership is silent about everything between the endpoints.
- If an intermediate cell can be **blocked**, the witness must test **traversability**, not
  membership. `descent` already established that a wall between two cells breaks a path, and that a
  level can satisfy every generation predicate and still be untraversable. The containment witness
  therefore **consumes `descent`'s traversability relation** rather than inventing a weaker one.

The implementation may not promote the endpoint-membership expression into a correctness law until
its semantics are established against the canonical level representation. If the representation does
not support this law, **the law is revised before the module is graded** (§15).

## 5. Temporal refinement — the memoryless-membrane contract

KINEMA must define exactly which visual samples belong to which authoritative tick. For each
transition `D_n → D_{n+1}` the view may produce any **declared** number of samples
`G(α_0), …, G(α_k)`, each `α_i ∈ [0, 1]` in deterministic fixed-point. Every sample carries its
**interval identity**, so a frame is not a loose position but a witness of a named transition:

```text
    Frame { source_tick = n,  alpha = α,  refined = R(D_n, D_{n+1}, α) }
```

The testable invariant is then:

```text
    sample(n, α)  depends only on  D_n, D_{n+1}, α
```

and **must not** depend on any of:

```text
    the previous rendered frame · future authoritative state · render cadence
    the wall clock · a GPU result · camera feedback
```

That is the memoryless-membrane claim, and it is what makes cadence-independence checkable rather
than asserted. The number of visual frames must not alter the authoritative trajectory: **6 samples
and 144 samples describe the same authoritative transition**, and changing the cadence must not
change canonical state, simulation timing, replay identity, or subsequent authority. That is a core
candidate falsifier (Plant D, §10).

## 6. Fixed-point representation — and the arithmetic that must be established, not assumed

The proposed view representation is Q32.32:

```text
    Q_SHIFT = 32
    Q_ONE   = 1 << Q_SHIFT
    result  = before + ((alpha * (after − before)) >> Q_SHIFT)
```

Every overflow, division, rounding and signed-value behaviour is **specified explicitly**, never
inherited accidentally from the host language. In particular:

> A claim of "i64 arithmetic" is valid only if the implementation **establishes** the bounded
> arithmetic semantics it names. Python's arbitrary-precision integers must not be mistaken for an
> i64 machine-arithmetic model.

This is a measurement obligation, not a comment: the fixed-point relation and its bounds are pinned
and checked (a cross-placement to a genuinely bounded implementation escalates with importance, as
the placement ladder always does), or the claim stays "reference arithmetic on unbounded integers"
and says so. A one-ULP perturbation (Plant E, §10) is admissible as a falsifier **only if the chosen
law makes that perturbation observable** — it is not assumed in advance.

## 7. Authority ownership

KINEMA does **not** own terrain, movement legality, collision legality, topology, game progression,
combat outcomes, canonical coordinates, replay state or network state. Those remain properties of the
existing authority. **KINEMA may query them; it may not redefine them.**

There is therefore no private replacement for the canonical terrain field, the movement law, the
collision law or the game state built merely to make interpolation convenient. A temporary synthetic
fixture may be used during development, but **a synthetic fixture cannot become evidence that KINEMA
is correct against the production authority** — proving the bridge against a miniature world it
carries with it proves only that it agrees with itself. This is why Plant B (§10) consumes a real
`gamegen` level through `descent` rather than a private mock.

## 8. Dependency direction

```text
    permitted:   CORE → canonical state        VIEW → canonical state
    forbidden:   CORE → KINEMA view state
```

The renderer may consume a canonical snapshot, interpolate it, and discard the result. Nothing
rendered may feed back into the canonical simulation. An absent rendering backend is a **labelled
`SKIP`**, not a core failure — `voxin-placement`'s shape, `SKIPPED (backend absent) — honestly
labelled, not passed`. Conversely, **if the verification regime requires a rendering dependency for
the core to pass, that dependency has become a core dependency**, which is a §2 violation caught by
the gate reddening on a host without it. No view dependency enters a canonical digest (D24 §6, D11
§4).

## 9. Identity separation

View-only quantities never enter canonical identity. The following changing must not alter canonical
game identity: interpolation rate, number of rendered frames, camera sampling time, presentation
cadence, visual smoothing, display refresh rate. **The canonical state is identical whether it is
rendered once, six times, 144 times, or not at all.** A view digest, if one is ever useful, is a
*view witness* and never a replacement for canonical identity — the `descent` distinction (a path
property is not a digest) restated on the presentation side.

## 10. Non-vacuity — the plants, and what each one establishes

KINEMA must not certify itself by reproducing its own implementation. The falsifiers introduce
**actual** violations of the boundary, and they are deliberately of **two different failure classes**
that the first draft of this proposal conflated:

- a **false visual witness** — the VIEW presents a transition or occupancy the authority refused
  (Plants A, B). This is a real defect and it is *not*, by itself, a `CORE → KINEMA` dependency: a
  renderer can ghost through a wall while feeding nothing back into the simulation.
- **authority contamination** — a rendered result influences subsequent canonical state (Plant C).
  This is the separate, stronger failure the one-way membrane exists to forbid.

Keeping them apart is the point; a suite that proved only one would leave the other unguarded.

| plant | construction | what it establishes | expected |
|---|---|---|---|
| **A — unauthorized boundary crossing** | authority refuses a move (`D_n = A`, `D_{n+1} = A`); KINEMA is handed a malformed refinement `KINEMA(A → B, α)` with `B` across the refused boundary | a view cannot present a transition the authority did not authorize | **REFUSED** |
| **B — forbidden intermediate occupancy** | a real `gamegen` level with `A ─ X ─ B` where `X` is wall; the trajectory's intermediate samples pass through `X` | interpolation cannot occupy a region the *actual* topology (`descent`) declares inaccessible; endpoint membership is insufficient | **REFUSED** |
| **C — feedback / contamination** | the rendered output is deliberately wired to influence the next simulated state | the membrane is one-way: the canonical transcript cannot legitimately depend on a rendered result | **REFUSED** (structurally *and* behaviourally) |
| **D — sampling invariance** | the same authoritative transition rendered at 1, 6, 60, 144 samples | presentation cadence cannot change canonical state or identity | canonical state **unchanged** |
| **E — arithmetic perturbation** | perturb the refinement arithmetic (e.g. one ULP) | the declared fixed-point relation is real — **conditional on §6**: admissible only once the chosen law makes the perturbation observable | **REFUSED**, if observable |

Plant A attacks the **transition**, not a speed parameter: `speed_q + 1` does not necessarily cross
any boundary and is a poor falsifier, so it is not used as the primary plant. Plant B uses the
**actual topology** — `gamegen` → `descent` → KINEMA witness — never a private `MOCK_potentials`,
which would be the second miniature world §7 forbids. Plant D compares the **whole canonical state**
where the test can see it, with the digest as an *additional* identity check rather than the
behavioural oracle. Plant C is the one that separates *false visual witness* from *actual authority
contamination*, and it must bite in both the structural guard (§11) and a behavioural fixture.

## 11. The structural guard is a fourth layer, not the oracle

"Read-only" cannot be a comment. An AST guard inspects the actual `kinema` module and rejects:

- imports from the game/authority side in the forbidden direction;
- assignments to authoritative state, and calls to authoritative mutators;
- references to canonical state through dynamically reconstructed names, where those forms are in
  scope;
- a KINEMA object passed back into the simulation;
- imports that make the renderer a prerequisite for the core gate.

It carries a **positive control**: a synthetic module containing an explicitly forbidden write is
rejected, so the checker is shown to bite rather than to pass by habit. And it is explicitly bounded:
**the AST guard does not attempt to prove the whole semantic property.** This tree has repeated
evidence that structural matching without binding resolution produces false positives — *a structural
match identifies a candidate; only resolution and dependence establish the claim.* The guard is one
of four layers (A, B behavioural; C behavioural *and* structural; the guard structural), never the
correctness oracle on its own.

## 12. What KINEMA does not claim

KINEMA does not establish that continuous rendering is necessary; that interpolation is perceptually
superior; that any particular frame rate is correct; that the renderer can meet a frame-time budget;
that motion will look smooth; that the game feels responsive; that the game is fun; that the
rendering algorithm is efficient; that interpolation constitutes physics; or that the underlying
simulation should become continuous. Each is a separate question. A **measurement** may establish one
of them as an observation; a **correctness law** requires an independently defensible predicate and
falsifier. The two are never interchangeable (D24 §4).

## 13. Performance stays outside the correctness gate

Existing presentation measurements (`voxwork-clock`, `voxref`, `voxbreak`, `sealframe`) remain
relevant evidence and do **not** become a KINEMA correctness oracle merely because KINEMA exists:

```text
    view correctness   → potentially gateable
    presentation cost  → measurement, on a named host, in a committed record
    frame-time budget  → separately registered only if independently justified
```

`voxwork-clock` already places wall-clock off-gate by rule; KINEMA inherits that and does not convert
an observed rendering budget into a new FPS requirement. Wall-clock performance stays outside the
deterministic correctness claim unless a separate, independently justified performance experiment is
registered.

## 14. Relationship to lockstep and replay

If KINEMA is later connected to the network/replay layer it consumes the **authoritative transcript**
and never reconstructs authority from rendered frames:

```text
    lockstep.canon → authoritative state → KINEMA refinement → visual frames
```

Replay reproduces the same canonical state **whether or not KINEMA is present**. The renderer is a
*consumer* of replay, not part of replay authority — the cardinal invariant of D15 and D24 §1
(replay stays byte-identical with every observer active) applied to the refinement membrane.

## 15. Admission criterion — measurement before implementation

The first `kinema` module may be admitted only after its actual inputs and semantics are measured
against the existing canonical representation. Before implementation, establish:

1. the exact authoritative state consumed;
2. the authoritative movement / collision boundary (through `descent`, not a mock);
3. the temporal relationship between ticks and view samples;
4. the exact fixed-point representation and its bounded-arithmetic semantics (§6);
5. the interpolation domain;
6. the view-only quantities;
7. the absence of a feedback path;
8. the independently constructed falsifiers (§10).

If the existing representation does not support the proposed law, **the law is revised before the
implementation is graded.** The implementation does not define the contract retroactively — that
inversion is the one this whole tree exists to refuse.

## 16. The first vertical slice

The smallest useful KINEMA slice is not a cinematic system. It is:

```text
    authoritative transition → deterministic refinement → intermediate view samples → containment witness
```

with a planted counterexample that must refuse. The first successful experiment demonstrates **only**
that a view can refine an authoritative transition without acquiring authority and without presenting
an explicitly forbidden spatial transition. Everything else stays outside the claim. Stated as the
narrow success claim:

> KINEMA demonstrates that a visual refinement of an authoritative transition can be produced without
> changing canonical state and without presenting an explicitly forbidden spatial transition.

Not "continuous rendering is safe." Not "the renderer cannot ghost through walls" in the general
case. Not "the simulation is mathematically bulletproof." Those broader statements would outrun the
falsifiers.

## 17. The rung sequence

```text
    1. Register the temporal/spatial refinement contract (this document, committed as the debt)
    2. Measure the real gamegen state + descent topology representation
    3. Implement one-way read-only refinement in Q32.32
    4. AST-check the forbidden dependency, with a positive control (§11)
    5. Plant A — refused authority crossing
    6. Plant B — forbidden intermediate occupancy, over a real level
    7. Plant C — feedback attempt (structural and behavioural)
    8. Plant D — sampling invariance
    9. Verify the renderer/backend is unnecessary for CORE (labelled SKIP when absent)
   10. Full gate twice, byte-identical
```

## 18. Architectural consequence

If the experiment succeeds, KINEMA establishes a deliberately asymmetric membrane:

```text
                         AUTHORITY
                             │
          ┌──────────────────┴──────────────────┐
          │  canonical game state                │
          │  deterministic simulation            │
          │  lockstep / replay                   │
          └──────────────────┬──────────────────┘
                             │ read
                             ▼
                          KINEMA
                  discrete → continuous
                       refinement
                             │  render only
                             ▼
                           VIEW
              interpolation / camera / presentation
```

Authority determines *what happened*. KINEMA determines only *how that state may be presented between
authoritative observations*. The elegant form of this architecture is not "continuous simulation
behind an integer firewall"; it is **canonical simulation → explicitly bounded temporal-spatial
witness → presentation** — the authority stays discrete while the view is allowed to look continuous,
without granting continuity any authority of its own.

## Grade

**DECLARED — prospective.** This document asserts a partition, a candidate relation, a candidate law
and a falsifier set, and measures nothing, because there is nothing yet to measure. Its falsifier is
retro-admission: the first `kinema` module classifies under §2 and satisfies §10, or D25 is amended
first. Its `does_not_show`: that the refinement relation of §3 is the RIGHT one — §15 requires it to
survive contact with the real representation, and §4 already flags that the simplest containment form
is too weak; that KINEMA should be built at all; that continuous rendering is necessary or superior
(§12); that any frame rate or budget is met (§13 says the opposite is the current measurement); that
the §10 plant set is exhaustive, only that each plant bites a real and distinct failure; and nothing
about what the view should *look like* — D25 decides where a view claim may stand, never how the game
should be presented.

## Appendix — what the first draft got wrong, recorded rather than erased

The preregistration is stronger for keeping its own refuted heuristics, the way `ratchet` and
`voxin` keep theirs:

- **The leakage/dependency conflation.** The first draft treated a temporal-spatial leak as a
  `CORE → KINEMA` dependency. It is not: a false visual witness (Plants A, B) and authority
  contamination (Plant C) are different failure classes, and collapsing them would have left the
  one-way membrane guarded only by arithmetic.
- **`speed_q + 1` as Plant A.** A speed perturbation need not cross any boundary, so it is a poor
  falsifier for "the view cannot present a refused transition." Plant A now attacks the transition
  directly.
- **`MOCK_potentials` as Plant B's world.** A private miniature world model would prove the bridge
  only against itself (§7). Plant B consumes a real `gamegen` level through `descent`.
- **The assumed one-ULP failure.** Plant E is now conditional on §6 establishing an observable
  relation, rather than assuming a one-ULP perturbation must fail.
- **"i64 arithmetic" as a given.** §6 makes the bounded-arithmetic semantics a measurement
  obligation; Python's bigints are not an i64 model until something establishes the bound.
