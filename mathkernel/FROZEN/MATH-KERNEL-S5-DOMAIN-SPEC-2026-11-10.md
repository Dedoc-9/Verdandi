# MATH-KERNEL-S5-DOMAIN-SPEC-2026-11-10

**Status: SCRATCH DRAFT in `orlog-review`. The semantic framework is ruled (contract sheet, this date); the wrap/clamp
source expressions are now VERIFIED by quotation (Turn 56 hardening); a few items remain explicitly OPEN. No oracle is
frozen, no implementation is authorized, no repository or charter change is authorized by this draft.**

## 1. Purpose

Define the first trig capability's input domain for Verðandi's movement laws. The first capability is deliberately
**game-matched**, not a general-purpose `sin`/`cos` over all finite binary64 (ruled 2026-11-10). The numerical
guarantee is the ruled **specified-frozen-algorithm** guarantee, scoped to the controlled build configuration recorded
at admission: conformance is exact agreement with the frozen algorithm, **not** correctly-rounded real-valued results.

## 2. Input domain (VERIFIED from source)

| input | domain | endpoints | source (Verðandi 95a9731) |
|---|---|---|---|
| yaw | `[0, 2π)` | lower inclusive, upper exclusive | `graybox/web/sim.js:514` `wrap(a){return ((a % t)+t)%t}` with `t=2π`, applied `:558` `s.yaw = wrap(s.yaw + (inp.dyaw||0))`; twin `graybox/tick_ref.py` `turn`: `s.yaw = fmod(fmod(s.yaw+dyaw, TWO_PI)+TWO_PI, TWO_PI)` |
| pitch | `[-1.45, +1.45]` rad | both inclusive | `sim.js:515` `clamp(v,a,b){return v<a?a:v>b?b:v}`, applied `:559` `s.pitch = clamp(s.pitch+(inp.dpitch||0), -1.45, 1.45)`; twin `tick_ref.py`: `p=s.pitch+dpitch; s.pitch = -K.pitch_limit if p<-K.pitch_limit else K.pitch_limit if p>K.pitch_limit else p`, `K.pitch_limit=1.45` |

The two twins are held bit-for-bit identical by the graybox's own checks, so the wrap/clamp are a single specified
operation, not two independent choices. `2π` here is the binary64 `2 * Math.PI` / `TWO_PI`; the exact bound value is
that double, not the real 2π.

**Spawn yaw:** `sim.js:511` `s.yaw = sp.yaw * Math.PI / 180; s.pitch = 0` — spawn yaw is given in degrees and converted
to radians; it is **not** re-wrapped at the spawn site (only `turn` wraps). Spawn yaws in `[0, 360)°` land in `[0, 2π)`
already; a spawn yaw outside `[0, 360)°` would not be normalized at spawn. (This is the likely real referent of the
"135° spawn-yaw" item — see §5/OPEN; 135° → 2.356… rad is already in-domain and needs no wrap.)

**Trig call sites (first capability):** the look/aim unit vector `sim.js:707-708`
`cp = cos(pitch); [cp*sin(yaw), sin(pitch), -cp*cos(yaw)]` — i.e. `sin`/`cos` of yaw and of pitch. `atan2` appears only
at aim-at-target sites (`sim.js:928`, `:1168`) and the bot; **`atan2` is a separate later capability**, not part of
this first coupled `sin`/`cos`.

## 3. Operation ownership and order (ruled: law-level only)

Wrapping and clamping belong to the **movement law**, never to the trig kernel. Per tick: (1) the law computes and
wraps yaw; (2) the law clamps pitch; (3) the law passes the resulting binary64 values to the trig capability; (4) the
capability evaluates its specified algorithm and **never** re-wraps yaw or re-clamps pitch. The kernel must not
reinterpret a valid in-domain input.

## 4. Out-of-domain and exceptional inputs

Two questions, kept apart: a **policy** (the owner's semantic ruling) and a **mechanism** (the interface contract).

**ADOPTED (owner, explicit §3-b6, 2026-11-10 — restated by the assistant and adopted verbatim by the owner):**
- **Out-of-domain finite → REFUSED.** Finite inputs outside their applicable declared domain are refused with a
  **deterministic capability error and no numeric output** — never a fallback number; the kernel never silently wraps
  or clamps. **Domain validation is per law-level input role:** a value in the **yaw** role is validated against
  `[0, 2π)`, a value in the **pitch** role against `[-1.45, +1.45]`; the capability carries the role and validates
  against that role's interval, not a single merged interval.
- **Non-finite (NaN / ±∞) → REACH the frozen oracle,** whose specified exceptional-value behavior is preserved (the
  ruled S3 oracle-preserving semantics; both twins return NaN via `x − x`). Signed zero follows the ruled S1;
  **no added NaN canonicalization.**

These two policies are **adopted by the owner's explicit confirmation** (his adoption quoted them verbatim beside this
assistant restatement), **superseding** any "still proposed" characterization. They close the S5 interface's semantic
choices. They do **not** authorize freezing, oracle acquisition, oracle construction, or any repository change — those
remain separate words.

## 5. Boundary and regression vectors (to generate before freeze)

Each vector records the binary64 **input and expected-output bit encodings** (decimal display alone is insufficient).

**Corpus split by capability and responsibility (per the review):**

| corpus | tests | status |
|---|---|---|
| movement-law normalization | yaw wrap, pitch clamp, spawn conversion (incl. the top-band→+0, −0→+0, and the 135° 2-ulp shift) | first capability |
| direct `sin`/`cos` kernel | the exact binary64 values *actually reaching* the kernel, and their output bits | first capability |
| exceptional-value kernel | signed zero, NaN, ∞, subnormals | first capability — **subject to the §4 interface ruling** |
| `atan2` quadrants | all signed-zero/∞ combinations | **future capability** (not part of the first freeze) |
| out-of-domain refusal | the §4 interface behavior | **wait for the owner ruling** |

The direct-kernel corpus must test the values that actually reach the kernel (yaw with −0 already destroyed by the
wrap; pitch with −0 preserved), not assume an input property survives the law's preprocessing. The 135° two-ulp change
is a **movement-law** regression vector, **not** a trig-kernel accuracy failure.

- **Yaw:** `+0`; `-0` at the law→kernel boundary; the largest binary64 below `2π`; the double `2π` itself (before
  law-level wrap); the doubles immediately below/above the wrap boundary; positive and negative pre-wrap values; the
  value produced by the spawn-yaw `deg·π/180` conversion for each shipped spawn.
- **Pitch:** exactly `-1.45` and `+1.45`; the adjacent binary64 values just inside and just outside each; pre-clamp
  values just outside; `+0`, `-0`.
- **Exceptional:** ±∞; quiet NaNs incl. distinct payloads where representable; subnormals and the smallest normals;
  values exercising the §4 out-of-domain behavior.

**READY — verification (corpus):** generate and pin the full corpus; the ruled-semantics subset is computable from the
law's exact wrap/clamp (verified below).

**VERIFIED (2026-11-10, both twins agree bit-for-bit) — the law-level wrap's exact edge behavior.**
`wrap(a)=((a%2π)+2π)%2π` (sim.js) ≡ `fmod(fmod(a,2π)+2π,2π)` (tick_ref) is **not identity on [0,2π)**: the largest
binary64 below 2π (`401921FB54442D17`) and `2π` itself both map to **+0**; yaw **−0 → +0**; the 135° spawn value
(`4002D97C7F3321D2`) shifts **two ulps** to `4002D97C7F3321D0` when wrapped (the spawn site does not wrap — the shift
appears on the first `turn`). Confirmed in python (`tick_ref`) **and** node (`sim.js`). The "135°" item is therefore
**CLOSED — evidenced**: it is this deterministic wrap property, **not** a regression and **not** the LAW-A scratch
`aim2` bug.

**Consequence — the corpus must split two vector classes:**
- **Movement-law vectors:** inputs to the law's wrap/clamp and the post-op value the kernel receives (exercises the
  normalization itself, incl. the top-band→0 and −0→+0 behavior).
- **Direct-kernel vectors:** the already-normalized values fed to the trig kernel — yaw ∈ [0, 2π) with −0 gone; pitch ∈
  [−1.45, +1.45] with **−0 preserved** (the clamp keeps it).

**Signed-zero asymmetry (verified):** S1's signed-zero rule is live for the kernel via **pitch −0** (clamp preserves
it), **not** via yaw (the wrap destroys yaw's sign). The corpus and the capability interface must reflect this split.

**RULED (owner, 2026-11-10): PRESERVE and document the existing yaw-wrap edge behavior as the law's semantics.** It is
law-level normalization (`((a%2π)+2π)%2π`), not an accidental kernel detail that could be silently replaced at the
kernel boundary; both twins agree bit-for-bit (largest binary64 below 2π → +0; the 135° input shifts two ulps); and a
correction would be a **distinct behavioral contract** needing its own ruling, fixtures, and verification. The edge
behavior is recorded as **movement-law regression evidence, not a trig-kernel defect**, and kept separate from the
kernel's capability boundary — **Policy 1 applies at the kernel, not to the law's pre-normalized input**, so the wrap
outputs (2π → +0, negative-yaw normalization, the 135° 2-ulp shift) remain movement-law evidence.

**Corpus generated + twin-verified (2026-11-10)** — `MATH-KERNEL-S5-VECTORS-2026-11-10.csv` (90 vectors) + `.md`. Both
twins were run **independently per vector**: `sim.js` exposes the exact kernel (`module.exports = make(1)`,
`EXACT = {sin: xsin, cos: xcos, …}`, L38/283), so node called `xsin`/`xcos` directly, and the wrap/clamp were
reproduced from `sim.js` L514-515 and run in node too. **All 82 twin-run vectors agree bit-for-bit, 0 mismatches**
(I verified the kernel exposure, the `xsin`/`xcos(1.45)` bits, and the provenance — Verðandi 95a9731,
rules_ref.py `ba8e2aa4…`, sim.js `01f3c4c2…`). Closure by group: movement-law normalization, pitch clamp, direct
sin/cos, reduction stress → **CLOSED–evidenced** (twin-run); exceptional values → partly closed, the
interface-dependent cases **PROVISIONAL**; out-of-domain finite → **OPEN–owner-ruling** (inputs only, no normative
outcome). `rem_pio2` is exercised in the reduction group (n=1 at π/2 and 1.45, n=2 near π, n=3 near 3π/2, n=4 near 2π).

## 6. Explicit exclusions

The first capability does not promise: arbitrary finite-binary64 argument support; general-purpose angle normalization;
kernel-level yaw wrapping or pitch clamping; correctly-rounded mathematical results. General finite-binary64 trig is a
**separate successor capability** with its own domain, range reduction, characterization, and admission.

## 7. Freeze prerequisites (before the S5 domain is frozen)

1. (DONE, §2) Quote the exact yaw-wrap and pitch-clamp source expressions and the trig call sites.
2. Resolve the §4 out-of-domain refusal mechanism and the non-finite interface behavior.
3. Generate and pin the §5 binary64 boundary-vector corpus.
4. Confirm the law→kernel boundary preserves the ruled S1 signed-zero and S3 exceptional-value semantics.
5. Confirm the `sim.js`/`tick_ref` wrap/clamp remain bit-identical at the frozen Verðandi commit cited.

**No oracle is frozen, no implementation is authorized, and no repository or charter change is authorized by this draft.**

## 8. Closure states (applied 2026-11-10, owner's order)

Each item carries one of: **OPEN–research** (evidence still to find) · **OPEN–owner-ruling** (a semantic decision) ·
**READY–verification** (answer proposed, needs a reproducible check) · **CLOSED–evidenced** (answer supported, evidence
recorded) · **FROZEN** (owner-authorized). This stops a source citation being mistaken for a ruling or a reproduced
result.

- §2 input domain — intervals, endpoints, wrap/clamp expressions, spawn conversion, trig call sites: **CLOSED–evidenced**
  (quoted source, `sim.js` + `tick_ref`, Verðandi 95a9731).
- §3 law-level-only ownership of wrap/clamp: **CLOSED–evidenced**. This boundary agrees with the oracle-provenance
  plan's contract — in both, the kernel never re-wraps or re-clamps a valid in-domain input.
- §4 out-of-domain finite + non-finite interface: **ADOPTED (owner, explicit §3-b6, 2026-11-10)** — out-of-domain
  finite REFUSED (deterministic capability error, no output; per-role domain validation, yaw vs pitch); non-finite
  NaN/∞ REACH the oracle (S3 oracle-preserving).
- §5 ruled-semantics vectors: **CLOSED–evidenced** (the 90-vector corpus, both twins run per-vector, 0 mismatches). The
  CSV now carries the adopted outcomes (bookkeeping applied 2026-11-10): 8 out-of-domain finite → **refused**
  (deterministic error, no output, role-validated yaw/pitch); 12 non-finite (±∞/NaN) → **reaches the frozen oracle**
  (oracle-specified output per input — NaN here via `x−x`, not blanket-assumed; no NaN canonicalization; exact bits
  pinned at oracle freeze); 4 signed-zero → S1 preserved; 4 subnormal → finite in-domain.
- §5 "135°" origin: **OPEN–research** (investigate separately; does not block the first capability).
- S5 interface freeze: **FROZEN** only after §4 is ruled, the vector corpus pinned, and the owner authorizes.
