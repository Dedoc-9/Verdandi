# MATH-KERNEL — repository-destination decision sheet

**Scratch decision sheet. Not a ruling, not frozen, not in any repository.** It lays out options for the owner to rule.
**No repository or charter change is authorized by anything here** (the owner's words: *"No repository or charter change
is authorized by that architectural preference alone."*). The owner's stated position this session (verbatim):

> *"Revised recommendation: Verðandi as the provisional home … Unify the repository without unifying the authorities …
> My revised LEAN is option 3 … repository unification, dependency direction, and authority boundaries are three
> separate decisions … I'd make the decision sheet about the path toward unification, not simply where to put the kernel
> today."*

These are his LEAN and framing, recorded as his — not an adoption. The sheet follows his decomposition into three
separable decisions.

## The three separable decisions

| | decision | not |
|---|---|---|
| **D1** | authority boundaries — what the kernel governs for itself | where its files live |
| **D2** | dependency direction — who may depend on whom | whether they share a repo |
| **D3** | repository topology and the path to unification | an immediate history merge |

They are independent: the kernel can hold full internal authority (D1) and strict one-way dependencies (D2) whether it
lives in its own repo, inside Verðandi, or in a unified repo (D3). Conflating them is what makes "where to put it" look
harder than it is.

---

## D1 — Authority boundaries

**Principle (his):** *"Unify the repository without unifying the authorities."* The kernel retains, wherever it lives:
its own numerical **contract + succession rules**; its own **oracle provenance + executable identity**; its own
**independent characterization**; its own **candidate conformance + admission records**; **explicit consumer interfaces**
so Ørlǫg or other components never become implementation dependencies.

| option | consequence |
|---|---|
| **D1-A (LEAN).** Kernel keeps all five authorities, governed by its own contract/freeze/succession, distinct from Verðandi's gate, registers, and RUNGS ledger. | The kernel's freeze (sha256 `9de3943b…`) and its succession rule remain the kernel's law; a kernel change is re-admitted under the kernel's contract, not Verðandi's 251-row gate. Independence is a governance fact, not a repo fact. |
| D1-B. Fold kernel governance into Verðandi's existing gate/registers. | Loses the three-artifact separation (oracle/contract/candidate independently governed); the candidate could reach its own oracle through shared machinery. Rejected by the contract already frozen. |

**Derivation of the LEAN:** the frozen contract's three-artifact separation and succession rule are already the kernel's
independent authority; D1-A simply says the repository choice does not dissolve them. D1-B contradicts a frozen term.

---

## D2 — Dependency direction

| option | consequence |
|---|---|
| **D2-A (LEAN).** Strict one-way: consumers (Verðandi's simulation, a future engine, and — if it ever expresses numeric laws — Ørlǫg) depend on the kernel through **explicit consumer interfaces only**. The kernel depends on **nothing above it** and imports no Ørlǫg or Verðandi internals. | The kernel stays independently consumable and independently verifiable; a consumer change cannot silently alter kernel behavior, and the kernel cannot acquire a hidden dependency on the simulation. Enforceable by an import/boundary check (see D3 enforcement). |
| D2-B. Allow the kernel to reuse Verðandi utilities/helpers for convenience. | Creates a back-edge (kernel → Verðandi), so the kernel is no longer independently buildable or consumable; defeats D1. Rejected. |

**Note:** today the kernel's realizations are deliberately self-contained (the C oracle links no host libm; the Python/JS
references are standalone). D2-A preserves that; it is the cheaper path, not the costlier one.

---

## D3 — Repository topology and the path to unification

The owner's three possibilities, with his criteria (ownership, dependency direction, versioning, independent
consumption) plus fragmentation / CI / coordination / migration cost:

| criterion | 1. Standalone kernel repo | 2. In Verðandi, unify later | 3. Unified repo, separate subsystems from the outset **(his LEAN)** |
|---|---|---|---|
| ownership | kernel fully self-owned | lives in Verðandi | one repo; three subsystems each with its own authority (D1) |
| dependency direction | enforced by repo separation | enforced by discipline/boundary check | enforced by subsystem boundary rules |
| versioning | independent repo semver | shares Verðandi's; kernel versioned by its contract/freeze | repo-level + per-subsystem contract/version records |
| independent consumption | easy (pull the repo/package) | harder unless a clean sub-package interface exists | via explicit interface module; external via a published interface |
| fragmentation / CI / coordination | **high** — separate CI, separate gate runs, cross-repo coordination | low now | **lowest** — one CI, one place, boundaries internal |
| integration / migration cost | **high later** — if the direction is one repo, this is eventual migration work (the fragmentation to avoid) | a later move (the "unify later" step) | **none** — no later migration; boundaries exist from day one |

**His LEAN: option 3.** The sheet treats D3 as a *path*, not one event, and splits it:

- **D3a — near-term placement (the first repo landing of the kernel).** LEAN: land the kernel as an **independently
  governed subsystem inside Verðandi**, which already *is* the "simulation · numerical capability · admission" layer.
  Verðandi becomes the **provisional unified host**; the subsystem-boundary pattern (D1 + D2, enforced) is established
  from the first commit. This realizes option 3's *architecture* immediately using the existing repo — it is option 3's
  first step, not option 2's "drop it in and sort it out later."
- **D3b — long-term topology (whether/how Ørlǫg joins one repo).** Separate and later. His caution (verbatim): *"we
  should not assume the entire Ørlǫg and Verðandi histories need to merge immediately."* So D3b can preserve both
  histories (a unified repo that adopts Ørlǫg as a subsystem without rewriting its history, or keeps Ørlǫg's release
  discipline intact) and is decided on its own evidence when the time comes.

**Why the LEAN holds:** option 1 is rejected by the owner's own fragmentation argument; option 2 defers a move the
direction says must eventually happen; option 3 gets the boundaries right from the outset at the lowest cost, and D3a
lets it start today without touching Ørlǫg.

### Enforcement (what makes "separate subsystems in one repo" real, not nominal)
A monorepo does not enforce boundaries by itself. For option 3 to mean anything, the kernel subsystem needs:
1. A **directory boundary** holding only kernel files (contract, oracle, gate, characterization, records).
2. An **import/dependency check** (a gate row or a standalone check) that fails if kernel files import anything above
   them, or if consumers reach kernel internals instead of the interface module (enforces D2-A).
3. The kernel's **own freeze/succession** governing its files (enforces D1-A), distinct from Verðandi's 251-row gate.
4. A single **consumer interface module** — the only surface Verðandi's sim (and future consumers) bind to.

**One reconciliation for D3b:** Ørlǫg and Verðandi have different contribution workflows today — Ørlǫg through a GitHub
PR the owner merges; Verðandi through a scratch clone + `git format-patch` the owner applies and pushes. A unified repo
would have to choose or bridge these. This is a D3b concern, flagged, not decided here.

---

## What is NOT authorized
No repository creation, move, merge, or write; no charter change; no commit, push, or admission. This sheet is a scratch
analysis. The next step after a ruling is a **PR proposal — a proposal only**, carrying no authorization to push.

## Questions for the owner to rule (any subset)
1. **D1 (authority boundaries):** adopt **D1-A** (kernel retains all five independent authorities, governed by its own
   contract/freeze/succession) — yes / modify?  **LEAN: D1-A.**
2. **D2 (dependency direction):** adopt **D2-A** (strict one-way; consumers → kernel via explicit interface only; kernel
   imports nothing above it) — yes / modify?  **LEAN: D2-A.**
3. **D3a (near-term placement):** land the kernel as an **independently governed subsystem inside Verðandi** (provisional
   unified host), with the boundary enforcement above — yes / standalone repo / other?  **LEAN: D3a (in Verðandi).**
4. **D3b (long-term topology):** target a **unified repo with separate subsystem boundaries (option 3)**, deciding the
   Ørlǫg history question separately and later (no immediate merge) — yes / modify?  **LEAN: option 3, histories decided later.**
5. **Enforcement:** is the four-part enforcement (directory + import check + own freeze/succession + single interface
   module) the right definition of "independently governed subsystem"? — yes / change?
