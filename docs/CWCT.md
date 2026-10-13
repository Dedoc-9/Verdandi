<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2026 Daniel J. Dillberg -->

# CWCT — the Creative World Closure Theorem, as a research hypothesis

**Status.** The owner's ruling of 2026-10-12, in his words: *"ACCEPT the Creative World Closure Theorem as the
organizing research hypothesis. DEFER any claim that it is proved or novel."* and *"state the l99 version of the
theorem in the docs plainly"*. This document is that statement: the strongest version the studio can be held to, each
clause with what holds it today, what does not, and the batch that owes it. It was revised before it was written by a
review he brought (2026-10-12: the box restated over failures, recovery as an enumerated set, the operators imported,
shared assets as pinned revisions, a batch and a kill criterion per clause, `CWCT ⊃ VCT-0`, liveness as `◊Decided`,
the provenance as hash chains with cross-references) and by a search for what usually breaks such systems (2026-10-12,
`docs/RESEARCH-FINDINGS.md` R-16), whose findings were fixed in B1 the next day. It is a design contract, off the
gate; no row holds it, and nothing here is a proof.

The question it answers, as the proposal put it: *"Can a creative studio guarantee that every accepted world change is
attributable to an explicit intention, bound to the exact inputs that produced it, isolated from unrelated work,
reproducible to the extent promised, and recoverable after interruption—while allowing the creative process itself to
remain open-ended?"*

---

## 1. The theorem, stated plainly

In a tree of worlds kept by the studio, under the axioms A1–A6 (§4) and for **every** schedule of process deaths,
concurrent writers, late model answers and refusals:

1. **Nothing reaches a world but an admission, or is found.** A world's files change only by an admission — a ledger
   event that names, by digest, the intent a person chose, at the head that intent was checked against — or by a write
   from outside the studio (a hand edit), which `verify` finds (UNLOGGED-CHANGE) until a person records it (`rebase`).
2. **What is not admitted changes nothing.** A refused, rejected, superseded, stale or interrupted change leaves every
   world's protected state byte for byte as it was; the ledgers only grow.
3. **An interrupted admission is never half done.** After a process dies at any of an admission's writes, or inside
   its recovery, recovery ends at exactly one of two states — the parent or the child — the same one however often it
   runs, and the ledger verifies.
4. **A late answer never overwrites newer work.** An admission is applied only at the head its evaluation was checked
   against, compared again at the write, under the world's lock; one drawn at an older head is refused.
5. **One world's admission changes no other world.** Until each world keeps its own pinned revision of what it shares,
   a change to something two worlds share is refused; adopting a shared revision is an admission of its own, in each
   world.
6. **Every admitted state is explained by digests.** From any admitted head, a chain of sha256s and record ids leads to
   the intent's bytes, the evaluation that judged them, the request that produced them (the provider, the model, the
   validators' sources, the configuration), the prompt's words, and the person who chose.
7. **No machine admits.** A model proposes; the studio evaluates; a person admits or refuses. The proof stops there:
   the theorem says nothing about whether the result is good art.
8. **Work reaches a decision, conditionally.** While the studio runs and providers answer within their limits, every
   queued request eventually reaches a state the person can decide on, or a failure said with its reason; it is decided
   (admitted, rejected, refused as stale) only by the person.

Clauses 1–7 are safety: they say what never happens. Clause 8 is liveness, and holds only under its assumptions. They
are kept apart on purpose: a candidate can be valid but stale, safe but ugly, or rejected and the system still right.

## 2. What CWCT is to what already exists

**CWCT ⊃ VCT-0.** CWCT is the umbrella. VCT-0 (`docs/STUDIO-APP.md` §5.2) is its **source-domain** instance: a
candidate studio, built, checked and promoted through the promotion journal and the `blessed` record
(`docs/STUDIO-CONTRACT.md`, `art/studio_txn.py`; B2). DIRECTOR-0's content ledger with its pending folder
(`art/director.py`, `art/director/`) is its **content-domain** instance: a candidate world change, evaluated, admitted
or refused (B1, built). What is new in CWCT is the **world and queue dimension**: many worlds in one tree, a queue of
model requests that answer late, and what the two may not do to each other (STUDIO-2 and later). One vocabulary for
freshness, commit and recovery serves all three: the one below.

## 3. The objects and the operators

**The operators, defined once** (imported verbatim from VCT-0): *"`is` is identity: the same bytes, by sha256 — never
a head that looks equal. `==` is equality of bytes. `≡` is equivalence of user data under one named procedure: the
content ledger of a project replays to the files it holds (`director.py verify`), at the reader's version. `<` is the
journal's order (`seq`), and nothing else. `??=` assigns only when the left side is **missing**; an **invalid** left
side is a different state with its own rule (below), never silently reassigned."*

**The studio's state** is `Σ = (W, Q, G, J, D, A)`, and what each is today:

| | meaning | today |
|---|---|---|
| `W` | the worlds: for each, its brief, its ledger, its tags, the maps it plays | the desktop studio's: `%LOCALAPPDATA%\VerdandiStudio\worlds\<name>\` (his choice, 2026-10-13), each a tree of its own with its own maps (STUDIO-2, built); one tree's (the checkout, the self-tests'): `art/briefs/`, `art/ledger/`, `graybox/maps/` |
| `Q` | the queue of model requests, each bound to a world | `art/studio_queue.py`: `<worlds>/queue.jsonl`, tasks in the order queued, at most one running per world (STUDIO-2, built); the page's own request, one at a time per world (`art/studio.py`) |
| `G` | immutable candidate generations of the studio itself | B2 |
| `J` | the journals: each world's ledger; the promotion journal | the ledger (`art/director/ledger.py`); STUDIO-TXN 0 (B2) |
| `D` | what the person made that is not the world: tags, notes | `art/ledger/<brief>.tags.json` |
| `A` | what each world admits now: its head; the active generation | `canon.head(parts)`; `active.json` (B2) |

**Defined here.**

- `Head(w)` is `canon.head` of three digests: the brief's text, the world's canonical layout, and the exporter's own
  code (`art_sha256`, `world_sha256`, `exporter_sha256`; `Workspace.export`). Heads are compared with `is`.
- `ProtectedState(w)` is the bytes of `w`'s brief, its tags file and every map it plays, compared with `==`; its
  ledger is compared by prefix: `J(w)'` extends `J(w)` (nothing in it rewritten).
- `Admit(C, w)` is **defined, not proved**: the ledger of `w` gains an `admit` event naming an `evaluate` event whose
  intent is `C`'s bytes (`is`), whose `head_before` is `Head(w)` read again under the content lock, chosen by a
  person (`chooser`); its files are then written whole. This is the commit: an admission counts once its line is
  flushed.
- `Decided(q) := admitted ∨ rejected ∨ refused-as-stale`, by the person only.

## 4. The fault model and the axioms

**Measured.** Process death: an admission killed at each of its ten writes and once inside its recovery
(`art/director.py crashtest`, 14 cases, PASSED in the container and on the owner's Windows machine); a second writer
at each of an admission's nine writes and another process's recovery against a live one (`racetest`, 32 cases, PASSED
in both); the promotion journal's decision at 41,568 enumerated crash states and 195,376 crashes inside recovery
(`art/studio_txn.py check`, 0 failures, in the container).

**Claimed under axioms, not measured.** An operating-system crash. A process kill leaves the operating system's cache
intact, so it does not exercise what a system crash does; ALICE found 60 vulnerabilities in 11 mature applications
under simulated system crashes. Windows documents `MOVEFILE_WRITE_THROUGH`'s guarantee for a move done as a copy and
a delete, and says nothing of a rename on one volume; `durable.py` does not flush a directory on Windows.

**Not claimed.** Power loss: whether acknowledged writes survive depends on the drive honouring its flushes, which no
software test establishes (13 of 15 SSDs tested failed under power faults, Zheng et al., FAST '13).

**The axioms** are VCT-0's, A1–A6 (`docs/STUDIO-APP.md` §5.2), A6 above all: *"the person who admits is the designer,
and nothing admits for them."* Three rules follow from what was measured:

- **A failed flush is never retried in place.** *"Retrying fsync() is not OK at least on Linux"* (the PostgreSQL
  discussion of 2018): a flush that fails ends the admission, and its pending folder is finished from its own copies
  (redo or undo), with fresh writes.
- **One writer at a time, by the system's lock.** Every writer of a tree's ledgers, briefs, tags and maps holds the
  content lock; recovery takes it too and refuses while a live writer holds it. Without it two threads broke a ledger's
  chain in 19 of 20 trials (MEASURED). The lease is the lock itself, released by the system when its holder dies (on
  Windows taken back after 0.00 s, MEASURED); no timeout takes it from a holder that is alive.
- **Every log written by more than one thread holds a lock.** On the owner's machine, two threads appending to one
  file without one kept 399 lines of 400, 396 of them whole (MEASURED, 2026-10-13): the C runtime's append on Windows
  is a seek to the end, then a write.

## 5. Each clause: what holds it, what does not, who owes it

| clause | holds it today | does not hold yet | batch | kill criterion |
|---|---|---|---|---|
| 1 nothing but admissions | the ledger's `admit`, the content lock; `verify` finds an unlogged change (UNLOGGED-CHANGE, a director self-test plant) | a writer outside the lock (every writer of those folders must hold it; AGENTS.md says so) | B1 (built) | a file of a world changed with no admit event and `verify` silent |
| 2 refusals change nothing | refused, leaking and stale candidates not admitted (director self-test); a refused second admission leaving the first's child (`racetest`, nine points); SHARED-MAP leaving both worlds' heads (director self-test); every answer without candidates (UNSUPPORTED, AMBIGUOUS, DECLINED, FAILED) leaving the brief and the ledger byte for byte (studio self-test, 0220) | the queue's own refusals, each by a test | B1, STUDIO-2 | any refusal after which a protected byte differs |
| 3 parent or child | `crashtest` (14 cases, Linux and Windows); a failure before the manifest leaves no folder, after it the folder is finished at once (`racetest`) | an operating-system crash (§4); B2's promotions on Windows | B1 (built), B2 | a recovery that ends between, or differently on a second run |
| 4 fencing | the head read again under the lock at the write (`commit_admission`); `racetest`'s plant: without it the second admission writes over the first; a queued task reviewed late: its candidates drawn again at the head as it is then, each evaluated again and HEAD-MOVED said (`studio_queue.py selftest`, fix 4's row) | — | B1, STUDIO-2 (built) | an admit event whose `head_before` is not the head it replaced |
| 5 noninterference | in one tree, SHARED-MAP: a layout change refused while another brief plays the map; the plant moves the other world's head (director self-test); in the studio's worlds, each world a tree of its own with its own copy of the maps: an admission in one leaves the other's bytes untouched, and two worlds compile at once each over its own maps (`studio_queue.py selftest`, with the plant of no export lock) | pinned revisions of shared assets; adoption per world | STUDIO-2 (worlds, built), B4 (assets) | either world's protected state changes without its own admit event → assets become immutable pinned revisions before B4 merges |
| 6 provenance by digest | `admit.evaluation` → `evaluate.intent_sha256`; the admit event's note names the request, whose record holds `request_sha256` and `basis` (the validators' and the configuration's sha256s), the intents' bytes and the prompt; the exporter's digest in the head | in the studio's worlds the requests' records are in the world's own folder (`<world>/art/build/studio/`, STUDIO-2), in one tree still in a build folder a clean removes; a query surface in the artist's words; cross-references between records (§8) | STUDIO-2, B3 | an admitted head whose chain cannot be followed to a prompt and a chooser |
| 7 no machine admits | the gateway admits only on the page's request with its token, by this server's name; a provider runs with no tools; every admit event names a chooser; the first window and the read-only views hold a token good only for the heartbeat (0220, a test) | the capability boundary for candidates of the studio itself (low integrity, experiment 4); an agent that operates a tool for the person and runs its admit after the person's words in a chat (the design tool's operator skill) is a person's acceptance carried by a machine, recorded as the person's | B1 (built), B2 | any admit event with no person's action behind it |
| 8 `◊Decided` | a request runs, is superseded, cancelled, timed out or failed, and says which; a request that ends on its own ends in a disposition, REALIZED, UNSUPPORTED, AMBIGUOUS, DECLINED or FAILED, never an empty answer with no reason (0220); the persistent queue, each task queued, running, ready, failed, cancelled, interrupted or reviewed, read back after a restart; a task whose answer was recorded is ready after a restart, not asked again (fix 4) (`studio_queue.py selftest`) | a studio that dies between asking a provider and recording the start asks again at its next start; an order across worlds beyond the order queued | STUDIO-2 (built) | a task left neither ready nor failed while the studio runs and providers answer |

**The integrated experiment, attached to batches** (the proposal's §5, each step with the batch that runs it): steps
1–3 (two worlds, overlapping requests, an edit while one runs, the older finishing after the newer revision) and 8–9
(the old cannot overwrite the new; the page tells failed, stale, rejected and admitted apart) run with STUDIO-2; step 4
(a shared asset changed) with B4; steps 5–7 (the supervisor killed at each boundary, restarted, replayed) with B2,
whose criterion is the journal-replay court's: any decision after a kill that is not the contract's revises the record
form before B2's promotion code. (2026-10-13: STUDIO-2's self-test holds parts of steps 1–3 and 8 — two worlds, two
requests at once and never two in one world, a task reviewed after its world moved and each candidate evaluated again
— but the experiment has not been run as written.)

## 6. What it does not claim

That a candidate is good, beautiful, coherent or original, or that a player will enjoy it (the proposal's Objection A;
machines decide spans, clearances, scopes and recovery, people decide art). That the suites catch every defect. That
a model's proposal is reproducible: it is recorded, not reproduced, and reviewing it again re-evaluates the recorded
intent at the current head without asking the model (with STUDIO-2). That a model stays available: a retired
model's requests fail (*"Requests to models past the retirement date will fail"*, Anthropic's deprecations page), and
the recorded candidates need it no more. Anything outside §4.

## 7. Operational invariants (the four additions of 2026-10-13, with their status)

- **Undo is an intent.** It holds: the studio's undo builds an intent from the admission's recorded inverse, evaluates
  it and admits it through `cmd_admit` (`art/studio.py` `undo`), so it has the lock, the fence and the crash safety of
  any admission. Open: the link *undo of #N* is read from the admission's note rather than a field of its own; a
  layout admission is undone through the design tool, not here.
- **An admission is idempotent.** It holds by refusal: a retried admission meets a moved head and is refused (the
  gateway's STUDIO-STALE, the fence's HEAD-MOVED), and `racetest` shows no admission applied twice. The natural key is
  the request and its letter; open: a retry after a lost answer should say *already admitted*, not *stale*.
- **The world compiler is deterministic.** It holds in part: every admission compiles twice — at evaluation and at
  admission — and is refused if the heads differ; the head carries the exporter's digest, so a new exporter is a new
  head and is recorded (`rebase`), never silent. Not measured: one brief exported in processes with different string
  hash seeds giving one head.
- **Nothing reachable is deleted.** Nothing deletes yet. When generations (B2) and shared revisions (B4) are collected,
  the roots are every world's pins, the active and the previous generation, pending candidates, and every revision any
  ledger has ever named, so a rollback finds what it needs; a store that deletes what a root still names is a defect.

## 8. Provenance: hash chains with cross-references

Each world's ledger is a hash chain that verifies itself. A chain proves its own integrity, not its freshness: a ledger
put back from an older copy verifies too, and is caught only against a digest held somewhere else (Crosby and Wallach:
detection needs commitments that are audited). The design chosen (the review's item 9): the graph stays N hash-chained
records — the world ledgers, the queue's record, the requests' record, the promotion journal — each naming the others'
states by digest (a task the head it was drawn at, an admission its request, a world the revision it pinned), with one
canonical form and one chain rule, rather than one new graph with a validator of its own. What a person asks of it
(*which prompt made this canopy, which worlds use this revision, why is this result stale*) is answered by following
those digests, in words; that surface is STUDIO-2's and B3's.

## 9. At the level of a game and physics engine

His direction of 2026-10-12: *"game/physics engine is desirable abstrations level"*. Three consequences for the
theorem:

- **P1, determinism.** Physics that changes what a world is runs in the kernel (CORE), at a fixed step, without the
  platform's transcendental functions, held by a determinism row run on his machine and in the container (to come);
  physics in the browser is a view and writes nothing. Box2D v3's cross-platform determinism needed no fast-math, no
  fused multiply-add, its own `sin`, `cos` and `atan2`, and determinism tests in its CI; Rapier's needs its
  `enhanced-determinism` feature and warns that `Math.sin` and `Math.cos` are not deterministic across platforms; MDN:
  *"different browsers can give a different result"*. The studio already keeps the browser's numbers out of the world:
  a recorded candidate is replayed from its intent without the provider (the studio's self-test), and the page's
  camera is recorded with a request, not recomputed.
- **P2, ticks.** The world advances in fixed ticks, catching up a bounded number per frame (the spiral of death
  otherwise); an admission takes effect at a tick boundary, never inside one.
- **P3, edits to a running world.** As an engine defers creating and destroying entities to a sync point, an admission
  is applied between ticks; an admitted solid that would overlap the player or a moving body is refused or applied at a
  respawn, by a stated rule (INFERRED: overlap resolution pushes bodies apart violently).

## 10. Creative obligations, measured rather than proved

From the review *Art First*. Each is a property of the studio a person can check, not a clause of the theorem:

| obligation | today | how it is measured |
|---|---|---|
| IntentVisible: the prompt shown with what it made | the panel; `requests.jsonl` | the page shows it with every candidate |
| AlternativesOffered: candidates that differ | up to three | their distance from one another (models tend to near-duplicates; asking for several answers with their probabilities raised diversity 1.6–2.1× in creative writing, verbalized sampling) |
| RejectionExplained: why, in words | codes and messages; a refused tag says what it names | every refusal carries a sentence a person can act on |
| RevisionTracked: the history, followable | the ledger | §8, in the artist's words (STUDIO-2, B3) |
| RollbackPreservesArt: tags and notes survive | undo is an admission; tags are not touched by it | a row per release |

**Open-endedness is measured against an observer, never guaranteed.** Hughes et al. (2024): *"a system is open-ended
if and only if the sequence of artifacts it produces is both novel and learnable"*, to a named observer over a stated
horizon. So: the observer is the designer's own record (what was admitted, and the distance between candidates), the
horizon a stated number of sessions, and the claim a measurement.

**Learning from decisions keeps an exploration slot.** A system that learns only from what it showed narrows (Jiang et
al. 2019, degenerate feedback loops), and the designer's veto sees only what was shown; one candidate of every request
stays off what has been preferred.

## 11. Depth without bloat

From the review *The Eight-Line Language Problem*. Composition (collections, gradients, conditions, groups named by
query, assets made from parts) gives depth that more statement types do not. Its guardrail is the configuration
complexity clock: a language that grows into *"a much crappier language"* than the one it replaced. So every new
primitive is **total** (it terminates), **bounded** (a cap on what it makes, as `VERDANDI-DESIGN 0` caps statements and
operations), **checked by the checks that exist**, and runs no code of the person's or the model's; a primitive that
needs a debugger is not one. Whether a grammar is deep is measured as a generator's expressive range is (Smith and
Whitehead 2010): many candidates scored on two measures and plotted, from the recorded requests, so no model is asked
again to measure it.

## 12. Prior art, and what may be new

Every part has precedent: revision-bound references (Nix), caches keyed by every input (Bazel: *"A false cache hit
spreads a bad result"*), fencing tokens checked by the store itself (Kleppmann's argument against Redlock), rebuilding
by replay with versioned events (event sourcing), a content-addressed DAG (git), write skew and how serializability
prevents it, noninterference (Goguen and Meseguer). The plausible novelty is the composition — and where its proof
stops: a machine-checked transition system for open-ended, multi-world, model-assisted creation, with the artist's
authority as an explicit boundary it does not cross (A6). That is a hypothesis about novelty, not a claim of it; the
comparison has not been done.

## Sources

The proposal, the review and the two art reviews are the owner's (2026-10-12); the four additions and the reviews of
information flow, 2026-10-13. The search of 2026-10-12 is `docs/RESEARCH-FINDINGS.md` R-16, which lists every page;
those quoted here: Pillai et al., ALICE (OSDI 2014); Microsoft Learn, `MoveFileExA` and `LockFileEx`; LWN on
PostgreSQL's fsync (2018); Zheng et al., FAST '13; git for Windows' O_APPEND change; Crosby and Wallach (USENIX
Security 2009); Anthropic's model deprecations; Box2D's determinism post (2024); Rapier's determinism guides; MDN's
`Math`; Gaffer on Games, *Fix Your Timestep*; Unity's structural changes; Tam et al., *Let Me Speak Freely?* (2024);
Zhang et al., verbalized sampling (2025); Hughes et al. (ICML 2024); Jiang et al. (AIES 2019); Hadlow's configuration
complexity clock (2012); Smith and Whitehead (PCG 2010); the Bazel book on hermeticity; Kleppmann on fencing, as
discussed by Hochstein (2025); Cockroach Labs on write skew.