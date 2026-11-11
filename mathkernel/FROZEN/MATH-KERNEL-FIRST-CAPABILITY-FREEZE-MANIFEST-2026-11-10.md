# MATH-KERNEL-FIRST-CAPABILITY-FREEZE-MANIFEST-2026-11-10

**Status: PREPARED FOR REVIEW — NOT FROZEN.** The freeze requires the owner's explicit §3-b6 authorization against the
identified artifacts and digests below. This manifest performs no freeze, no oracle build, no admission, and no
repository/charter change. Digests are sha256 of the files as they stand now; any later edit changes the digest and
voids this manifest.

## 1. Contract spec — artifacts, sha256, and the precise sections frozen

| file | sha256 | sections being frozen |
|---|---|---|
| `MATH-KERNEL-CONTRACT-SHEET-2026-11-10.md` | `2c22b2f08597a7cce6ad2de1f1e14c64a84bafde31824cb59c8db506a97b9fb5` | §1 guarantee (ADOPTED: specified-frozen-algorithm, controlled-build-scoped, no correct-rounding); §2 the five oracle-life conditions; §3 permanent negative control; §4 three-artifact separation; §5 S1–S6 and the narrow S5 domain selection |
| `MATH-KERNEL-S5-DOMAIN-SPEC-2026-11-10.md` | `bff8111652e6682654623cefb718cee0639bf7f544a6f903b257baeb2c2e5578` | the per-role domain (yaw `[0,2π)` / pitch `[-1.45,+1.45]`); §4 interface policies (ADOPTED: out-of-domain refused; non-finite reaches oracle); the 90-vector corpus description; the yaw-wrap PRESERVE ruling |
| `MATH-KERNEL-CONSTANTS-LEDGER-2026-11-10.md` | `2ce98366fe226c2e1b515e39b07bf708b93a28e5d13256f9b4f5439aec3090b7` | the 43-constant classification and the 19 first-capability set |
| `MATH-KERNEL-ORACLE-SOURCE-PROVENANCE-2026-11-10.md` | `18a458f7e3bbc2172a941c0b63d2db70a3f79fc241a85ec878a0a9a1945abd85` | the Sun fdlibm 5.3 source identity + per-file sha256; the 43/43 constant comparison; the FreeBSD-delta finding |

(Roadmap, not itself a frozen contract term: `MATH-KERNEL-ORACLE-PROVENANCE-PLAN-2026-11-10.md`, sha256
`262c0b03303e5f2c1b252b477f5cfeca1e4620a0ac7778e150786b5a3c97a8f8`.)

## 2. Oracle source — archive identity (pinned)

Six Sun fdlibm 5.3 files, retrieved **2026-11-10T21:47:52Z (UTC)** from `https://www.netlib.org/fdlibm/<file>` into
`orlog-review/fdlibm-5.3/`. All `@(#) <file> 1.3/1.4 95/01/18`, Copyright 1993 Sun Microsystems.

| file | bytes | sha256 | `@(#)` | role |
|---|---|---|---|---|
| `k_sin.c` | 2392 | `75d391f3c124806ce14893cd038ae5dd10663e40430ffa174d5fddcb33012167` | 1.3 | first-capability |
| `k_cos.c` | 3004 | `841086c75288f3f9fef03bae2a9dc24e99c3cdb2035e170c69452013a7b5befc` | 1.3 | first-capability |
| `e_rem_pio2.c` | 5335 | `3a08dd4a38f9f9fc9478a33ca05cb81a6566f1010ab14412e97cae091bede16b` | 1.4 | first-capability |
| `k_rem_pio2.c` | 8460 | `5796209ea3fe1af88e22badeaed0f6a6aa923914e097e227c410527cb5815740` | 1.3 | first-capability (big reduction, not a constant) |
| `e_atan2.c` | 3736 | `61dbf9edc927468280ccde872ecfb7cb1ea7cbaf6e1b28e7021c968abe5f7c6e` | 1.3 | atan2 — future only |
| `s_atan.c` | 4207 | `8583c253aed6318dee2a48135e3f3b1328d838a390372a69414ac41eb5ce5ce1` | 1.3 | atan2 — future only |

## 3. First-capability constant set (19) — all bit-identical to upstream (verified)

| name | source | binary64 bits |
|---|---|---|
| S1–S6 | `k_sin.c` | `bfc5555555555549`, `3f8111111110f8a6`, `bf2a01a019c161d5`, `3ec71de357b1fe7d`, `be5ae5e68a2b9ceb`, `3de5d93a5acfd57c` |
| C1–C6 | `k_cos.c` | `3fa555555555554c`, `bf56c16c16c15177`, `3efa01a019cb1590`, `be927e4f809c52ad`, `3e21ee9ebdb4b1c4`, `bda8fae9be8838d4` |
| INVPIO2 | `e_rem_pio2.c` | `3fe45f306dc9c883` |
| PIO2_1 / 1T | `e_rem_pio2.c` | `3ff921fb54400000` / `3dd0b4611a626331` |
| PIO2_2 / 2T | `e_rem_pio2.c` | `3dd0b4611a600000` / `3ba3198a2e037073` |
| PIO2_3 / 3T | `e_rem_pio2.c` | `3ba3198a2e000000` / `397b839a252049c1` |

Comparison evidence: **19/19** upstream-vs-graybox bit match (full table in the source-provenance doc §3; 6 spot-checks
re-verified against the upstream decimals and their hex comments).

## 4. Explicit exclusions — outside the first capability

- The **24 atan2-only constants**: `ATANHI[0..3]`, `ATANLO[0..3]`, `AT[0..10]`, `TINY`, `PI_O_4`, `PI_O_2`, `PI`,
  `PI_LO`. (They match upstream too, but are research-only, not first-capability requirements.)
- The **FreeBSD `m &= 1` delta** (`rules_ref.py:244`; absent from upstream Sun `e_atan2.c:112`). `atan2` is a **future
  capability**; the delta is identified, not substituted for the upstream source.

## 5. Corpus

`MATH-KERNEL-S5-VECTORS-2026-11-10.csv` — **91 rows** (90 vectors + header), sha256
`622bf3a78964e6dc56a195e6b54f2daee52869c49c4f5c9c91ac982df81d3db8`. Carries the adopted interface outcomes
(out-of-domain → refused; non-finite → reaches oracle, candidate pending oracle freeze) and the movement-law wrap
evidence (2π→+0, −0→+0, the 135° 2-ulp shift), kept as law-level evidence.

## 6. Freeze boundary — contract + source identity ONLY

**Frozen (if authorized):** §1 contract spec, §2 source archive identity, §3 the 19 constants, §4 the exclusions,
§5 the corpus. **NOT frozen / explicitly future:** the oracle **build**, the **executable digest**, the **independent
characterization** reproduced against that executable, the **native backend**, **admission**, and any **repository or
charter change**.

## Important distinction (archive ≠ oracle executable)

The source **archive identity** (§2 — the six Sun fdlibm 5.3 files pinned by sha256) is **not** the normative oracle's
eventual **executable identity**. The archive is pinned now; the controlled build, the executable digest, and the
characterization against it are future work that comes **after** this contract freeze.

## To issue the freeze

On the owner's explicit §3-b6 confirmation — naming this manifest by filename **and its own sha256** (printed to the
owner after this file was written), and the action *"freeze the first-capability contract + source identity as listed
in this manifest"* — the freeze is recorded (a dated, append-only freeze note carrying these digests; still scratch, no
repo/charter write). Until then nothing is frozen, and any listed artifact may still change (which would change its
sha256 above and void the manifest).
