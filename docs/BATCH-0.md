# BATCH-0 — batches agreed before they are built (his protocol, as he amended it, 2026-10-21/22)

His rulings are quoted whole in §10, as he pasted them; they are also recorded in 0258's entry of `docs/ROADMAP.md`:
- the hardened contract (*"CHANGE, then adopt"*), with its three non-negotiables;
- 0258 alone, 0259 deferred until its sheet was adjudicated;
- the three refinements approved, with one tightening amendment.

Where this text and his words differ, his words govern. This file enforces nothing: nothing in the program reads it.
The first batch built under it is 0265 (its entry in `docs/ROADMAP.md`).

The principle, in his words: *"batching saves repeated full gates, not evidence about changed dependencies."*

## 1. The batch sheet comes first

A batch is one number and one patch file of N commits, one commit per item. Before any edit, the sheet gives for every
item:
- the exact files it may modify, create or delete (its write set W);
- the obligation it addresses, and its explicit non-claims;
- its dependencies and its expected rung;
- its targeted checks, their exact expected outputs, and what counts as their failure;
- each plant, with its causal witness: the observation that alone qualifies as detection;
- its rollback or forward-repair plan;
- whether it changes registered evidence, reference baselines, admission rules or the gate itself.

He adjudicates each item before it is implemented. **No undeclared write:** if building an item finds another file
must change, the work stops and a revised sheet goes to him. An item is never silently widened.

## 2. Composition is measured, not asserted

For every pair of items A and B: W_A ∩ W_B = ∅, R_A ∩ W_B = ∅ and R_B ∩ W_A = ∅. Here R is the read set of an item's
targeted checks, including imported modules, generated files, configuration, fixtures and reference ledgers.
- **Measured.** R is recorded in scratch by a Python audit hook (`open` events), installed in every Python process a
  targeted check starts. Subprocesses are identified and paths normalized. Readers outside Python (the conformance
  binary and its inputs, a browser's fetches) are recorded separately.
- **Incomplete, not independent.** If a child escapes the hook, or a read cannot be attributed, the read set is
  incomplete. Measured reads add to the declared dependencies; they do not show that a branch never executed could not
  read another file.
- **Conflicts.** A pair that conflicts is ordered, with the dependency on the sheet, or split into another batch.
- **Frozen before the gate.** The measured dependency graph is frozen into the batch's evidence before the expensive
  gate runs. If the actual reads contradict the planned order, the work stops and the sheet is revised. A conflict is
  never found, carried past and explained after the gate.

## 3. Shared documents

Each item edits only its own sections of `docs/ROADMAP.md`, `AGENTS.md` and `docs/CAPABILITY-MATRIX.md`, and its own art
entry in `docs/CORE.md`. The shared line count is written once, by the batch's last commit. The exemption holds only for
documents no check reads. A document a check reads is a measured input, and its edits enter the dependency analysis.

## 4. Every commit has its own evidence

For each item, in order:
1. build only the approved change;
2. commit it on its own;
3. run its targeted checks at that exact commit;
4. record the commit, whether the tree was clean, each command, its exit code, the digest of its output, the plants'
   witnesses and the rung (the classifier over that commit alone);
5. preserve every failure. A repair is a new commit, and the same commit is never re-run until it passes.

A targeted pass shows only the targeted obligations, never the batch's integration.

## 5. The ordered pairs

If A comes before B and B changes a file A's checks read, A's affected targeted checks run again at the batch's last
commit. The sheet lists every such re-run. A check the full check already runs need not be repeated, but only where
that coverage is shown. The others run separately: the conformance runner, doortest, the freeze readers and the rung
self-test, where they apply.

## 6. The batch's last commit

At the last commit: the full check, the plants comparison and the gate, each twice where the protocol says so, one after
another, with nothing else on the machine (no research compute, no second check). `Gated-Tree:` records the tree the gate
ran on. Required:
- the same source tree and the same environment for both runs;
- the gate's two outputs byte-identical;
- the full check's two runs compared suite by suite on verdicts and counts, with every difference explained. Timings
  may differ. An unexplained difference is never normalized away, and matching counts alone are not equivalent
  execution;
- no unexplained failure, skip or missing evidence;
- every expected plant accounted for, by its causal witness.

**A red batch stays red.** It stays red until its cause is resolved and a forward repair passes the required checks.
Per-commit greens never override it, and its failure is never blamed on the last item by default. It is attributed from
the per-commit evidence, then reproduced and isolated by targeted tests or a smaller batch.

## 7. Interactions, said before the build

Each sheet says:
- which cross-item interactions are expected, and which check exercises each one;
- which interactions remain untested, and whether any of them touches safety, admission, provenance or the gate's
  integrity.

An untested interaction at a critical boundary gets a targeted test or goes to another batch. Residual risk elsewhere
may be accepted, but it is recorded, never treated as zero.

## 8. His side is unchanged

The landing check, the full check twice, the classifier and plants, the gate twice, then the push. An item that fails
on his host is repaired forward in the next batch.

## 9. What a clean batch does not show

That every interaction between its items was tested. Disjoint writes, measured reads and independent targeted checks
reduce that risk; they do not remove it.

## 10. His rulings, verbatim

**The hardened contract (2026-10-21, his message of 2026-10-22 03:41 UTC), answering the agent's draft.**

> I’d harden this before adopting it. The core idea is sound: batch independent, low-risk changes; retain per-commit attribution; pay for the expensive gate once at the batch tip. The weak point is that per-item green checks do not establish that the combined tree is green, and a final gate cannot always tell you which item caused a regression.
> I would approve the approach with the following amendments.
> Hardened batch contract
> 1. Batch sheet is a precondition, not documentation after the fact
> Before any edit, every item must declare:
>
> * Exact files it may modify, create, or delete.
> * The obligation it addresses and its explicit non-claims.
> * Its dependencies and expected rung.
> * Targeted checks, exact expected outputs, and failure conditions.
> * Each plant and its causal witness—what observation uniquely qualifies as detection.
> * Its rollback or forward-repair plan.
> * Whether it changes registered evidence, reference baselines, admission rules, or the gate itself.
>
> No undeclared write. If implementation discovers that another file must change, stop and submit a revised sheet for adjudication. Do not silently expand the item.
> 2. Composition must be checked, not asserted
> Disjoint write sets are necessary but insufficient. Two items can write different files while one changes the assumptions under which the other's checks operate.
> For each pair of items \(A,B\), require:
> \[ W_A \cap W_B = \varnothing \]
> and, for their targeted checks,
> \[ R_A \cap W_B = \varnothing,\qquad R_B \cap W_A = \varnothing \]
> where \(W\) is the declared write set and \(R\) is the actual read set, including imported modules, generated files, configuration, fixtures, and reference ledgers.
> Static declarations alone can miss dynamic reads. Record observed file access where feasible, and fail closed on undeclared accesses to protected inputs. If the checks or runtime dependencies cannot be established sufficiently, order the items or split the batch.
> 3. Every commit gets attributable evidence
> For each item:
>
> 1. Build only the approved change.
> 2. Commit it separately.
> 3. Run its targeted checks at that exact commit.
> 4. Record the commit hash, dirty-tree status, command, exit code, output digest, plant witnesses, and rung.
> 5. Preserve failures. Repair forward in a new commit; never rewrite a failure into a green result by rerunning the same commit until it passes.
>
> A targeted pass proves only the targeted obligations. It does not establish batch integration.
> 4. The batch tip gets the full gate
> At the last commit, record `Gated-Tree` as the exact tree identity, then run the prescribed full check, plant suite, and gate twice, serially.
> Require:
>
> * The same source tree and relevant environment for both runs.
> * Byte-identical outputs where the protocol requires them.
> * Zero unexplained failures, skips, or missing evidence.
> * Explicit accounting for every expected plant and its causal witness.
> * No concurrent research or other machine-intensive check during the window.
>
> If the final gate fails, do not automatically blame the last item. The failure is attributed using the per-commit evidence; then reproduce and isolate the interaction with targeted tests or a smaller follow-up batch. Preserve the red batch result until a forward repair passes the required checks.
> 5. Define the limit honestly
> A clean batch does not prove that every interaction between its items was tested. Disjoint files and independent targeted checks reduce the risk; they do not eliminate it.
> Add an explicit interaction obligation to each batch sheet:
>
> * Which cross-item interactions are expected?
> * Which check exercises each interaction?
> * Which interactions remain untested?
> * Does any untested interaction affect safety, admission, provenance, or gate integrity?
>
> Any untested interaction touching a critical boundary must either receive a targeted test or be separated into another batch. Noncritical residual risk may be accepted, but must be recorded rather than silently treated as zero.
> Batch adjudication sheet
> This is the format I would require before approving any batch.
> Batch contract
> Batch number / patch filename
> Items and intended order
> 1
> Files per item (read/write sets)
> Obligations, non-claims, expected rung
> Targeted checks and exact expected outcomes
> Plants and causal witnesses
> Dependencies and commit order
> Cross-item interactions and residual risks
>  Copy batch sheet
> My ruling
> CHANGE, then adopt. The batching policy is worth using, but three requirements are non-negotiable:
>
> 1. Observed dependency/read-set conflicts must be considered, not just overlapping writes.
> 2. A batch-level failure must remain red until its cause is resolved; per-commit green results cannot override it.
> 3. The batch sheet must expose critical untested interactions before the build, not after the gate fails.
>
> This preserves your intended payoff—one expensive full cycle per batch—without pretending that independent item checks prove the composition. The batch sheet comes first; I adjudicate each item before implementation.

**0258 alone, 0259 the first agreed batch (2026-10-21, his message of 2026-10-22 03:41 UTC), answering "Ship 0258 alone, then make 0259 the first agreed batch?".**

> Yes: ship 0258 alone, then make 0259 the first agreed batch. That is the safer sequence because 0258 repairs an existing evidence-integrity defect in two R5 kill-plant rows, while the proposed 0259 items are still awaiting design and interaction review.
> One qualification: 0258 passing STUDIO 214/214 is a targeted result, not release clearance. Its full release checks have not run, and the two mutation comparisons are still pending. Keep those distinctions explicit.
> Release order
>
> 1. Finish the two scratch mutation comparisons. Confirm that the repaired predicate rejects the old false-catch cases and accepts only the genuine descendant-survives-kill witness.
> 2. Complete 0258’s release checks at its own commit, including the required full checks, plants, and gate twice. Preserve the exact outputs and any failures; do not call it released before those checks finish.
> 3. Keep the read-only plant audit and web research separate from the release check window.
> 4. Once 0258 is settled, review the 0259 batch sheet before any 0259 implementation begins.
>
> 0259 admission criteria
> The candidates are reasonable, but I am not pre-approving them as one batch. The batch sheet must establish:
>
> * F-17: the no-ledger case returns an explicit refusal code, and verify/rebase cannot silently create or assume missing authority.
> * F-16: request IDs are unique across gateways, and saved records cannot overwrite earlier requests. Define the uniqueness scope and test collisions, retries, and persistence.
> * Plant-predicate repairs: one item per suite where write/read-set analysis permits. Each repaired predicate needs a specific causal witness and negative controls.
> * DES-0 leak: demonstrate that the plant variable no longer leaks into `play.py` in a way that changes unrelated test behavior. Test both the plant and its control.
>
> For every item, require the exact files, dependencies, targeted checks and expected results, plants and witnesses, and expected rung. In particular, check whether F-16 and F-17 touch shared ledger or gateway code; if their checks read files changed by the other item, order them or split them.
> The research may improve the batching policy, but it cannot override observed file conflicts or weaken the evidence rules. Any proposed optimal batch size is an estimate under your actual cycle costs—not a correctness theorem.
> Final ruling: BUILD 0258 alone; DEFER 0259 implementation until I adjudicate its complete batch sheet. Keep the research and plant audit off the release check window. Once 0258 is clean on its own release criteria, 0259 can become the first batch under the agreed protocol.

**The three refinements, approved with one tightening amendment (2026-10-21, his message of 2026-10-22 03:44 UTC), answering "Add the three refinements to BATCH-0 as written?".**

> Yes—with one tightening amendment. I approve all three refinements for BATCH-0, subject to the exact rules below. The 0258 mutation results are useful targeted evidence, but they do not substitute for its pending release gate.
> BATCH-0 — amended ruling
> 1. Shared documentation — APPROVE
> Each item may edit only its own designated sections in `docs/ROADMAP.md`, `AGENTS.md`, and `docs/CAPABILITY-MATRIX.md`, plus its own art entry in `docs/CORE.md`. The shared line count is updated once, in the batch's last commit.
> The exemption applies only to documentation that no check reads. If a check consumes a shared document, that document is a measured input and its edits must participate in the dependency analysis.
> 2. Measured read sets — APPROVE
> Use the Python audit hook in scratch to record opened files across every Python process spawned by each targeted check. Record non-Python readers separately, including the conformance binary and its inputs.
> The measurement must identify subprocesses and normalize paths consistently. If a child process escapes instrumentation, or a read cannot be attributed, mark the read set incomplete—not independent. Measured reads supplement declared dependencies; they do not prove that an unexecuted branch could never read another file.
> 3. Ordered pairs — APPROVE
> If B changes a file read by A's checks, and A precedes B, rerun A's affected targeted checks at the batch tip.
> The batch sheet must list every such rerun explicitly. Checks already covered by the full check need not be duplicated, but only when their coverage is demonstrated. Otherwise run them separately, including the conformance runner, doortest, freeze readers, and rung self-test where applicable.
> 4. Output comparison — CLARIFIED
> Byte identity is required for the two gate outputs where the existing protocol requires it. Full-check outputs may differ in timings: compare suite verdicts and counts, then explain every difference. Do not normalize away unexplained differences or treat matching counts alone as proof of equivalent execution.
> One additional enforcement rule
> The measured dependency graph must be frozen into the batch evidence before the expensive batch gate. If actual reads contradict the planned order, stop and revise the sheet before proceeding. Do not discover a conflict, continue anyway, and rationalize it after the gate.
> For F-16 and F-17, for example, if F-17 writes `director.py` and F-16's STUDIO checks read it, the sheet must capture that dependency even though their implementation write sets do not overlap.
> Execution decision
>
> * 0258: wait for the web research and plant audit to finish, then open its isolated release window. Preserve the reported `214/214`, `213/214`, and `206/214` targeted results as measured evidence; do not yet label the release fully gated.
> * BATCH-0: record these amendments in the protocol before building 0259.
> * 0259: no implementation until the complete item-level batch sheet is submitted and adjudicated.
>
> The key principle is now explicit: batching saves repeated full gates, not evidence about changed dependencies. Every item retains its own commit-level attribution, and every affected obligation is checked again at the final tree.
