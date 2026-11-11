# mathkernel — public API specification (first capability: sin/cos)

The **one logical public API** consumers bind to. The C reference binding is `c/mathkernel.h` +
`c/mathkernel.c`; future language adapters (Rust, engine) are **subordinate to this boundary** and
expose only this API. **Consumers bind only here** — never to the oracle sources, `fdlibm.h`, the
characterization, or any implementation internal (enforced by `../check.py`).

## Surface

| function | meaning |
|---|---|
| `double mathkernel_sin(double x)` | sine of `x` (radians), `x` within the declared domain |
| `double mathkernel_cos(double x)` | cosine of `x` (radians), `x` within the declared domain |

`atan2` and other capabilities are **not** part of the first capability (future, each on its own word).

## Semantics (normative references in `../FROZEN/`)

- **Conformance, not correct rounding.** A backend conforms iff its output **bits** agree exactly with
  the **normative oracle** (Sun fdlibm 5.3, pinned in `../FROZEN/` and built per `../ORACLE/BUILD-RECIPE.md`)
  over the corpus. The guarantee is **specified-frozen-algorithm conformance, controlled-build-scoped,
  no correct-rounding claim** (`FROZEN/MATH-KERNEL-CONTRACT-SHEET`).
- **Accuracy (measured, `../CHARACTERIZATION/`).** The oracle is **faithfully rounded (≤1 ULP)**; it is
  **not** correctly rounded — eight certified 1-ULP cases at odd-multiple-of-π/4 reduction seams are
  **properties of the algorithm**, never contract failures. The API therefore promises conformance to
  the oracle, not correct rounding.
- **Declared domain** (`FROZEN/MATH-KERNEL-S5-DOMAIN-SPEC`): yaw argument `[0, 2π)`, pitch `[-1.45, 1.45]`.
  - **Out-of-domain finite** input → deterministic capability error, no numeric output (interface policy 1).
  - **Non-finite** input → reaches the oracle (interface policy 2).

## What binds to this API
The reference binding forwards to the normative oracle unchanged; it selects no numerics and opens no
alternate authority path. Admitting a *different* backend against this contract is the separate
**backend-admission** step (deferred — not performed in this landing).

## Boundary rule (enforced by `../check.py`)
- No consumer includes `fdlibm.h` or the oracle sources, or reaches an implementation internal.
- No kernel source imports or includes a Verðandi/Ørlǫg component, or host libm.
Planted canaries in `../test/` prove the check catches both.
