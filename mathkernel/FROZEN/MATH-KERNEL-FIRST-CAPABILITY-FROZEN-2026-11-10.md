# MATH-KERNEL — FIRST CAPABILITY (sin/cos) — FROZEN: contract + source identity

**Status: FROZEN 2026-11-10 by the owner's explicit §3-b6 authorization.** Append-only. The frozen artifacts stay as
they are; a correction is a new freeze or a dated note beside this record (never an in-place edit of a frozen artifact).
This freeze is scratch-only: no oracle build, no executable, no characterization, no native backend, no admission, no
repository or charter change.

## 1. Authorization (recorded per the discipline — assistant restatement + owner's verbatim confirmation)

- **Assistant restatement (presented before the owner's reply):** *"Freeze the first-capability contract + source
  identity as listed in MATH-KERNEL-FIRST-CAPABILITY-FREEZE-MANIFEST-2026-11-10.md, sha256
  e89416a7374d98d5957605cf199057849fd9ea4fa92af7213e54edeb98d9c4a5 — contract and source identity only, no oracle
  build/executable/characterization/native/admission/repo/charter."*
- **Owner's confirmation (verbatim):** *"my ruling: Freeze the first-capability contract + source identity as listed in
  MATH-KERNEL-FIRST-CAPABILITY-FREEZE-MANIFEST-2026-11-10.md, sha256
  e89416a7374d98d5957605cf199057849fd9ea4fa92af7213e54edeb98d9c4a5 — contract and source identity only, no oracle
  build/executable/characterization/native/admission/repo/charter."*

## 2. Integrity check at freeze time

All 12 artifacts verified **sha256-identical** to the confirmed manifest's values (manifest `e89416a7…` unchanged; the
4 contract sheets, the 91-row corpus, and the 6 Sun fdlibm 5.3 source files all match). **FREEZE INTEGRITY: ALL MATCH.**

## 3. Frozen artifacts (pinned by sha256)

| artifact | sha256 |
|---|---|
| `MATH-KERNEL-FIRST-CAPABILITY-FREEZE-MANIFEST-2026-11-10.md` (the manifest) | `e89416a7374d98d5957605cf199057849fd9ea4fa92af7213e54edeb98d9c4a5` |
| `MATH-KERNEL-CONTRACT-SHEET-2026-11-10.md` | `2c22b2f08597a7cce6ad2de1f1e14c64a84bafde31824cb59c8db506a97b9fb5` |
| `MATH-KERNEL-S5-DOMAIN-SPEC-2026-11-10.md` | `bff8111652e6682654623cefb718cee0639bf7f544a6f903b257baeb2c2e5578` |
| `MATH-KERNEL-CONSTANTS-LEDGER-2026-11-10.md` | `2ce98366fe226c2e1b515e39b07bf708b93a28e5d13256f9b4f5439aec3090b7` |
| `MATH-KERNEL-ORACLE-SOURCE-PROVENANCE-2026-11-10.md` | `18a458f7e3bbc2172a941c0b63d2db70a3f79fc241a85ec878a0a9a1945abd85` |
| `MATH-KERNEL-S5-VECTORS-2026-11-10.csv` (91 rows) | `622bf3a78964e6dc56a195e6b54f2daee52869c49c4f5c9c91ac982df81d3db8` |
| `fdlibm-5.3/k_sin.c` | `75d391f3c124806ce14893cd038ae5dd10663e40430ffa174d5fddcb33012167` |
| `fdlibm-5.3/k_cos.c` | `841086c75288f3f9fef03bae2a9dc24e99c3cdb2035e170c69452013a7b5befc` |
| `fdlibm-5.3/e_rem_pio2.c` | `3a08dd4a38f9f9fc9478a33ca05cb81a6566f1010ab14412e97cae091bede16b` |
| `fdlibm-5.3/k_rem_pio2.c` | `5796209ea3fe1af88e22badeaed0f6a6aa923914e097e227c410527cb5815740` |
| `fdlibm-5.3/e_atan2.c` | `61dbf9edc927468280ccde872ecfb7cb1ea7cbaf6e1b28e7021c968abe5f7c6e` |
| `fdlibm-5.3/s_atan.c` | `8583c253aed6318dee2a48135e3f3b1328d838a390372a69414ac41eb5ce5ce1` |

## 4. What is frozen

The first-capability **numerical CONTRACT** — the guarantee (specified-frozen-algorithm, controlled-build-scoped, no
correct-rounding), the five oracle-life conditions, the negative-control + three-artifact architecture, S1–S6, the
per-role narrow domain (yaw `[0,2π)` / pitch `[-1.45,+1.45]`), the two adopted interface policies (out-of-domain
refused; non-finite reaches the oracle), the yaw-wrap PRESERVE ruling, and the 90-vector corpus — **and** the oracle
**SOURCE IDENTITY** (Sun fdlibm 5.3; the 6 files pinned by sha256; the 19 first-capability constants verified
bit-identical to upstream).

## 5. What is NOT frozen (future work, each on its own word)

The oracle **build**, the **executable digest**, the **independent characterization** reproduced against that
executable, the **native backend**, **admission**, and any **repository or charter change**. The source **archive**
identity is pinned; the normative oracle's eventual **executable** identity is future. `atan2` is a separate future
capability (its 24 constants and the FreeBSD `m &= 1` delta are excluded from this first capability).

## 6. Succession

Any later change to a frozen artifact is a **succession event** (contract condition 5): the owner's explicit word, a
replay of every admitted capability against the successor, and a recorded capability-by-capability delta; this freeze is
preserved as historical evidence and is not rewritten.
