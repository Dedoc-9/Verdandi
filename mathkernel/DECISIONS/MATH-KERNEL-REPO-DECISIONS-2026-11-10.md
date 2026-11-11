# MATH-KERNEL — repository-architecture decisions (append-only record)

**Scratch decision record. Append-only. Not frozen, not in any repository.** Records the owner's rulings on the five
decisions of `MATH-KERNEL-REPO-DESTINATION-SHEET-2026-11-10.md`, in dependency order. Rulings are the owner's; the
assistant's restatements are marked as such. **No repository or charter change is authorized by anything here.**

---

## D1 — Authority — ADOPTED 2026-11-10

**Assistant restatement (presented before the owner's reply):**
> *"The math kernel retains its own authority: its numerical contract and succession rules, its oracle provenance and
> executable identity, its independent characterization, and its candidate conformance and admission records — governed
> by the kernel's own contract, freeze, and succession, distinct from Verðandi's 251-row gate, its registers, and its
> RUNGS ledger, regardless of where the kernel's files live."*

**Owner's confirmation (verbatim):** *"adopt D1 as written … I agree with the entire statement. The crucial phrase is
'regardless of where the kernel's files live.' Repository topology must not determine numerical authority. Verðandi's
251-row gate, registers, and RUNGS ledger cannot substitute for the kernel's own contract, oracle provenance,
characterization, or admission records."*

**Status: ADOPTED, as the assistant restatement above, verbatim.** Preserves the frozen three-artifact separation and
succession rules.

---

## D2 — Dependency — PENDING the owner's confirmation of the integrated wording

The owner adopted strict one-way dependency **with one clarification** (verbatim): *"define single explicit
consumer-interface boundary as one logical public API, not necessarily one physical source file. C, Rust, and future
engine integrations may need language-specific adapters, but those adapters must not expose internal kernel
implementation details or create alternate authority paths."*

**Assistant restatement, integrating the clarification (presented for the owner's confirmation):**
> *"Dependency is strictly one-way. Consumers — Verðandi's simulation, a future engine, and Ørlǫg only if it ever
> expresses numeric laws — depend on the kernel through a single logical public API: one logical consumer-interface
> boundary, not necessarily one physical source file. Language-specific adapters (C, Rust, future engine integrations)
> are permitted, provided they expose only that public API and do not expose internal kernel implementation details or
> create alternate authority paths. The kernel depends on nothing above it, imports no Ørlǫg or Verðandi internals, and
> remains independently buildable and verifiable."*

**Status (when written): awaiting the owner's explicit confirmation of this exact integrated wording.** (Recorded as
pending, not adopted.)

**Update 2026-11-10 — D2 ADOPTED.** The owner explicitly confirmed the integrated D2-final wording above (reply:
*"Confirm D2-final"*, selected against the assistant's restatement of that exact text). **Status: ADOPTED, as the
integrated assistant restatement above, verbatim.**

---

## D3a — near-term placement — ADOPTED 2026-11-10

**Assistant restatement (presented before the owner's reply):**
> *"The math kernel's first repository landing is as an independently governed subsystem inside the Verðandi repository
> (the existing simulation · numerical-capability · admission layer), which thereby becomes the provisional unified host.
> The kernel does not go into a standalone repository and does not go into Ørlǫg. This realizes the D1 + D2
> subsystem-boundary architecture in the existing repo from the first commit, and does not merge or touch Ørlǫg's
> history."*

**Owner's confirmation:** *"Adopt D3a"* (selected against the assistant restatement of that exact text).

**Status: ADOPTED, as the assistant restatement above, verbatim.** A placement decision only; it authorizes no actual
repository move, commit, or write.

## D3b — long-term topology — ADOPTED 2026-11-10

**Assistant restatement (presented before the owner's reply):**
> *"The target is a unified Ørlǫg/Verðandi repository with separate, independently governed subsystem boundaries
> (option 3). Whether and how Ørlǫg's history migrates into that unified repository is left undecided — decided
> separately and later, on its own evidence; no immediate history merge is implied. Verðandi serving as the provisional
> unified host (D3a) is the first step on this path and commits to no particular Ørlǫg-history migration."*

**Owner's confirmation:** *"Adopt D3b"* (selected against the assistant restatement of that exact text).

**Status: ADOPTED, as the assistant restatement above, verbatim.** A target-architecture decision; it creates, moves, or
merges no repository.

## Enforcement — ADOPTED 2026-11-10

**Assistant restatement (presented before the owner's reply):**
> *"A math-kernel subsystem counts as 'independently governed' only if all four are mandatory: (1) a directory boundary
> holding only kernel files (contract, oracle, gate, characterization, records); (2) an import/dependency check (a gate
> row or a standalone check) that fails if kernel files import anything above them, or if a consumer reaches kernel
> internals instead of the interface module — enforcing D2's one-way dependency and one-logical-API; (3) the kernel's own
> freeze and succession governing its files, distinct from Verðandi's 251-row gate, registers, and RUNGS ledger —
> enforcing D1's authority; (4) a single consumer-interface module — the one logical public API; language-specific
> adapters expose only it — the sole surface consumers bind to."*

**Owner's confirmation:** *"Adopt Enforcement"* (selected against the assistant restatement of that exact text).

**Status: ADOPTED, as the assistant restatement above, verbatim.** Defines the enforcement contract; builds nothing and
authorizes no repository change.

---

## Summary — all five adopted (2026-11-10)

D1 Authority, D2 Dependency (logical-API clarification), D3a near-term placement (subsystem in Verðandi), D3b long-term
topology (unified repo, Ørlǫg-history separate/later), and Enforcement (four mandatory elements) are **all adopted**. No
repository, charter, commit, push, or admission is authorized by these architectural rulings. The next step is a **PR
proposal — a proposal only**, laying out how the subsystem and its four enforcement elements would land, carrying no
authorization to push.
