# MATH-KERNEL — PR proposal (proposal only)

**Scratch proposal. Not a ruling, not frozen, not in any repository. It authorizes no push.** It lays out how the math
kernel would land as an independently governed subsystem inside Verðandi, realizing the five adopted decisions
(`MATH-KERNEL-REPO-DECISIONS-2026-11-10.md`). The actual landing would need the owner's explicit §3 b6 word; he applies
patches, runs the checks on his host, and pushes.

## 1. Shape of the landing

A **new top-level subsystem directory** in Verðandi — a peer of `art/`, `graybox/`, and `design/`, which already sit
**outside the 251-row gate with "their own checks; no row"** (AGENTS.md §2). This matches the repo's existing pattern
exactly and keeps the kernel off the frozen gate core:

- It is **not** under `kernel/`, `shell/`, `workshop/`, or `verify/`, so it is **not** in `RSN_SOURCES` (the 58
  sha256-pinned files) and needs no `RSN_CHAIN` link — it cannot turn `reasoncourt-fence`/`mintwatch-fence` red.
- It respects the **gate-stops-growing** ruling (2026-10-09): **no new gate row or rung**. Enforcement is a **standalone
  check** the owner runs, like `art/check.py` / `graybox/check.py` / `design/test_design.py`.

**Name: `mathkernel/`** (settled by the owner 2026-11-11: it communicates the subsystem's purpose more precisely than
`numerics/`, which could encompass unrelated numerical code, despite sitting beside the Rust render `kernel/`).

## 2. The four enforcement elements, concretely

| element (adopted) | concrete form in the landing |
|---|---|
| **1. Directory boundary** | `mathkernel/` holds only kernel files: the frozen contract, the oracle (source + reproducible build recipe), the characterization, the negative-control gate, the consumer-interface module, and the kernel's own governance records. Nothing else lives there; the kernel's files live nowhere else. |
| **2. Import/dependency check** | `mathkernel/check.py` (standalone, **no gate row**): **FAILS** if any kernel source imports or includes anything above the subsystem (no `graybox/`, `shell/`, `kernel/`, `art/`, Ørlǫg, host libm), and **FAILS** if a consumer reaches a kernel internal instead of the interface module. A planted upward-import and a planted internal-reach are its canaries (proving it bites). Enforces **D2**. |
| **3. Own freeze / succession** | `mathkernel/FROZEN/` carries the frozen contract + manifest + freeze record + oracle provenance (the scratch artifacts `9de3943b…`, `e89416a7…`, etc.), governed by the **kernel's own** contract and succession rule — **distinct from** `verify/`'s gate, registers, and `RUNGS.md`. A change to a frozen kernel file is a kernel succession event, not a gate amendment. Enforces **D1**. |
| **4. Single interface module** | `mathkernel/interface/` is the **boundary inside `mathkernel/`** — one logical public API (the sin/cos — later atan2 — surface). Its **C reference binding (`interface/c/`) and future language adapters are subordinate to that boundary** and expose **only** that API. **Consumers bind only to the interface**; they never reach the oracle, the characterization, or any implementation internal, and no adapter opens an alternate authority path. Enforces **D2's** clarified interface (owner's structural clarification, 2026-11-11). |

## 3. Proposed first-landing contents

**Governance + evidence (the kernel's authority, D1):**
- `FROZEN/` — the frozen numerical contract, manifest, freeze record, and oracle **source identity** (Sun fdlibm 5.3,
  6 files sha256-pinned; the 19 first-capability constants).
- `ORACLE/` — the oracle **build recipe**: the pinned sources + build inputs (`fdlibm.h`, `s_sin.c`, `s_cos.c`), the
  exact flags (`-ffp-contract=off -fno-fast-math`), and the build provenance record. **Not** a committed executable
  (exe hashes are non-reproducible; the conformance target is output bits, built on demand).
- `CHARACTERIZATION/` — the independent-characterization method + results + the retained adversarial corpus (faithful
  rounding ≤1 ULP; the 8 certified 1-ULP counterexamples recorded as **properties of the algorithm, not gate failures**).
- `GATE/` — the conformance gate + its self-tests + the negative-control report (positive control + three mandatory
  controls + the weakened-gate detection).
- `DECISIONS/` — the architecture decision record (this proposal's parent) as the subsystem's charter.

**Interface (D2):**
- `interface/` — the one logical public-API **specification plus one reference C binding** (`interface/c/`), subordinate
  to the interface boundary and exposing only the API. Rust/engine adapters deferred. Consumers bind only here.

**Enforcement:**
- `check.py` — the import/dependency check (element 2), with its planted canaries.
- `README.md` — the subsystem contract (what it governs, its invariants, its ghosts), in the repo's README style.

## 4. What the first landing DEFERS (named, not hidden)
- **Backend admission.** No backend is admitted. The gate is demonstrated (self-test); admitting a real backend is the
  separate **backend-admission milestone**. The existing graybox `sin`/`cos` are bit-identical to the oracle (the
  differential) and would be the natural first admission candidate — **later, on its own word**.
- **The native/optimized backend**, `atan2` and further capabilities, and any **rewiring of the live simulation** to
  consume the interface (the graybox keeps its current sin/cos until a consumer-migration step is ruled).
- **The Ørlǫg-history merge** (D3b: separate and later).

## 5. How it would land (no push authorized)
Per the established Verðandi workflow and the owner's privacy/landing rules:
1. Scratch clone of Verðandi at a pinned commit; add `mathkernel/`; run `mathkernel/check.py` (expect PASS + canaries),
   `art/check.py`/`graybox/check.py`/`design/test_design.py` unaffected, and `verify/verify.py` twice byte-identical
   (the new subsystem must not perturb the gate — expect `GATE PASSED`, `RECONCILE … 251 rows / 0 fail`).
2. `git format-patch` into the patches folder; **the owner** applies, runs the checks on his host, and pushes.
3. The **landing check** (from 0254): the last commit carries `Gated-Tree: <40-hex>`; after `git am`, `TREE HELD` or stop.
4. **Privacy**: scrub personal details/paths before anything leaves the machine; check largest files vs the 100 MB limit;
   no engine brand names ("future engine integration").

## 6. NOT authorized
No repository creation or write, no commit, no push, no admission, no frozen-file landing. This is a document for review.
The actual landing requires the owner's explicit §3 b6 confirmation naming the action and target.

## 7. Settled answers (owner, 2026-11-10/11)
1. **Name:** `mathkernel/` (communicates the subsystem's purpose more precisely than `numerics/`).
2. **First-landing scope:** full authority and proof — contract, oracle build recipe, characterization,
   negative-control gate, standalone check, and interface. Defer additional adapters and backend admission.
3. **Interface form:** specification plus one reference C binding.
4. **Enforcement:** standalone `mathkernel/check.py`; **no Verðandi gate row**.
5. **Landing vehicle:** scratch clone → `git format-patch` → owner applies, runs checks, and pushes, including the 0254
   `Gated-Tree` landing check.
6. **Structural clarification:** the logical interface lives inside `mathkernel/`, with its C reference binding and
   future adapters **subordinate** to that boundary; consumers bind only to the interface, never reaching the oracle,
   characterization, or implementation internals.

**The proposal is final.** The next step — actually building the `mathkernel/` subsystem (writing its files, running
its check, and preparing the `git format-patch`) — is the first consequential step and would begin only under the
owner's explicit §3 b6 authorization. Nothing here authorizes it.
