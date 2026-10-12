<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Verðandi Studio — the architecture contract (STUDIO-CONTRACT 0)

**Status.** The interfaces and the change transaction the studio is built to, frozen before B1 by the review of
2026-10-12; a document and one reference module (`art/studio_txn.py`), off the gate. Nothing here is built into a
program; no row, rung, pinned source or oracle file changes. Where this contract and
[`STUDIO-APP.md`](STUDIO-APP.md) differ, **this contract governs**; the plan keeps the research and the reasons. The
decision table of §7 is printed by `python art/studio_txn.py table`, and `python art/studio_txn.py selftest` refuses
if the two ever differ, so there is one statement of it, not two.

**Why it exists.** One review asked for *"a gate-compatible engineering shape: a small, stable architecture whose
components and change protocol are chosen to satisfy the existing verified contracts by construction, rather than
repeatedly engineering around them after each patch"*, with its limit stated: *"a design can be shaped to satisfy the
existing gates, but it cannot be declared compliant until the actual repository is checked against them."* Another
set the bar for recovery: *"After any tested interruption, recovery must produce one well-defined state, preserve the
last admitted generation as a recoverable fallback, and never bless a candidate without intact evidence that it was
validated against its recorded basis."* And the order: *"Write Experiment 5's state machine and commit-point
semantics before writing its harness."*

---

## 1. The rulings this rests on (2026-10-12)

He brought reviews that state these as rulings and agree on them; they are recorded as his, in the words he brought.
If one is not his, it is struck and nothing below that rests on it stands.

| item | ruling | in the words he brought |
|---|---|---|
| Inno Setup | **accepted, optional** | *"Portable distribution remains primary; packaging is not a runtime dependency."* |
| tags | **persist by first touch, shown** | *"Preserve first-touch numbering and display existing assignments. Define how deleted objects and new projects affect persistence."* (§9) |
| stills to a model | **opt-in, per session** | *"Consent should identify the provider and the content sent, and be explicit for each session."* |
| the journal-replay court | **accepted, before B1's promotion logic** | *"Define the recovery state machine and oracle before writing the harness."* (§6–§8) |
| the five experiments | **accepted, conditionally** | *"Stop or revise the architecture when a probe fails its stated kill criterion; don't let the probe suite become another permanent gate."* (§11) |
| the API provider's default model | **deferred**, then **Opus 5.5, configurable** (the next review he brought, put with one word, *"agree?"*; agreed) | *"the names, availability, and prices in the proposal need current verification before becoming product defaults."* Then: *"I'd use Opus 5.5 for the initial API adapter, matching the model already used through Claude Code … Keep the model configurable so Sonnet can become the cost-optimized default later, based on measured quality and cost."* |

The deferral's condition was checked the same day (VERIFIED, [models overview](https://platform.claude.com/docs/en/about-claude/models/overview),
[pricing](https://platform.claude.com/docs/en/about-claude/pricing)): four current models, none marked deprecated —
Fable 5.1 (`claude-fable-5-1`) $10 / $50 per million tokens in and out, Opus 5.5 (`claude-opus-5-5`) $4 / $20,
Sonnet 5.5 (`claude-sonnet-5-5`) $2 / $10, Haiku 5.5 (`claude-haiku-5-5`) from $0.10 / $0.50; the overview says *"If
you're unsure which model to use, start with Claude Opus 5.5 for most workloads."* His Claude Code CLI answered as
`claude-opus-5-5` on his machine (MEASURED, 2026-10-12). It is a field of the provider's configuration
(`art/providers/anthropic.json`, `--model claude-opus-5-5`), never a constant in the gateway; changing it is one line.

## 2. Who may do what

| part | may | may not |
|---|---|---|
| a model (provider) | answer one request on stdout | hold a file handle, a tool, the pointer, the journal, or a credential of the studio's |
| the gateway (`art/studio.py`) | read an answer whole or refuse it whole; freeze request and response by sha256 | admit, or treat any field of an answer as an instruction |
| the director (`art/director.py`) | evaluate a content candidate; admit it when a person says so | decide for the person |
| the renderer (the page) | show the active generation, or a candidate in its own window | write state the simulation reads, or decide validity |
| the active supervisor (`art/studio_app.py`, B1) | run the lifecycle of source candidates; write lifecycle records and `promote` | write the pointer, write a record while a promotion is open, or bless |
| a candidate generation | run in its own job at low integrity while it is a candidate | write `bin\`, `studio\`, `projects\`, `runtime\` or another generation (§5.2 of the plan, experiment 4) |
| the stub (`VerdandiStudio.exe`, outside every generation) | decide by §7 at every start and every exit; write the pointer and its records; bless | run code from staging; be replaced by a transaction it runs |
| the person | admit; reject; choose in SAFE | — (nothing admits or chooses for them: axiom A6) |

The commit of a promotion (`blessed`) is written by the stub, which no candidate can replace, after its own check of
the candidate's health. Neither a candidate nor its supervisor writes the record that makes it the studio.

## 3. The candidate envelope

One shape for both domains. Every field is immutable once written; a candidate's *status* is not a field — it is
what the journal says (§5, §7), so there is one place where admission is recorded and no copy of it to disagree with.

| field | what it means | content (where it already is) | source (B2) | serves |
|---|---|---|---|---|
| `candidate_id` | the proposal's identity: the sha256 of its exact bytes | `intent_sha256` (the evaluate record) | the patch document's sha256 | `is` |
| `base` | the generation it was made against, by identity | `intent.base` (art, world, exporter sha256s) | `promote.from`, the base generation's hash | `Fresh`, `STUDIO-STALE` |
| `request`, `response` | the frozen model input and output | `request_sha256`, `response_sha256` (`build/studio/requests.jsonl`) | `proposed` | T3, frozen input |
| `product` | what it builds to | `evaluate.after` (the predicted head) | the generation's hash (its manifest's sha256) | `Built`, `Integrity` |
| `compiler` | the identity of what built it | `intent.base.exporter_sha256` | the toolchain in the basis | `Fresh` |
| `validators` | the identity of what judged it | the scope protocol's name and version only — **a gap** | the validators' source hashes in the basis | `Checked`, `Fresh` |
| `configuration` | the configuration it ran under | the config's path and the model's name — **a gap: no digest** | the configuration digest in the basis | `Fresh` |
| `footprint` | what it declared, realized and affected | the verdict's `declared`, `realized`, `affected` | the patch's globs and the paths it changed | T9, `Leak` |
| `reserved` | what it may never touch | `play/…` (`art/director/scope.py:35`) | the reserved list (the plan, §4) | `RESERVED` |
| `evidence` | the result of its validation, by hash | the evaluate record's verdict | `checked.evidence`, a file under `studio\evidence\` | `Checked`, §7 R9–R12 |

The two gaps are B1 work: the gateway's request record gains the sha256 of the director's and the scope's sources
and of the provider's configuration file, so a content verdict carries the whole basis the source domain will.

## 4. The operations

| operation | input | output | record | who | it never |
|---|---|---|---|---|---|
| Propose | the prompt, the tags, the head | a frozen answer of at most three candidates | the gateway's request entry; `proposed` | gateway, provider | changes the world |
| Build | a candidate, its base | a generation directory or a content evaluation | `staged`, `built`; the evaluate record | supervisor; director | activates |
| Check | a built candidate | evidence bound to the basis | `checked{gen, basis, evidence}`; the verdict | supervisor in the candidate's job; director | reuses a result under another basis |
| Try | a checked candidate | a second window on a scratch copy | `launched`, `healthy` or `dead` | the active supervisor | lets the candidate see the pointer, the journal or the projects |
| Admit | a person's click, the candidate shown | `promote{gen, from, basis, tries}`, then the supervisor exits and the stub decides; for content the admit record | the same | the person, through the supervisor | happens without the person, or on a basis that moved (`STUDIO-STALE`) |
| Activate | an open `promote` | the candidate running on trial, then committed or rolled back | `activate`, `boot`, `blessed` or `rollback`, `aborted` | the stub, by §7 | continues past a failed check |

## 5. The promotion journal and its neighbours

**The journal** `studio\promotions.log` (format `STUDIO-TXN 0`): DIRECTOR-0's canonical bytes
(`art/director/intent.py`), one record a line, each with `protocol`, `version`, `seq` (from 0), `prev` (the sha256
of the line before, 64 zeros for the first), `kind`, and its fields. A record counts once its line and LF are written
and flushed to the disk (`os.fsync`, `FlushFileBuffers` in the stub); nothing acts on it before. Kinds:

| kind | fields read by §7 | written by | when |
|---|---|---|---|
| `installed` | `gen` | the installer | once, as record 0: the first committed generation |
| `proposed`, `staged`, `built`, `launched`, `healthy`, `dead`, `rejected` | — | the active supervisor | the lifecycle of a source candidate (annotations to §7) |
| `checked` | `gen`, `basis`, `evidence` | the active supervisor | the candidate's suites passed; `evidence` is the sha256 of `studio\evidence\<evidence>.json` |
| `promote` | `gen`, `from`, `basis`, `tries` | the active supervisor | the person admitted; this record **is** the admission |
| `activate` | `gen` | the stub | before the pointer moves to the candidate |
| `boot` | `gen`, `left` | the stub | before each launch of a candidate on trial; `left` is the tries remaining after it |
| `blessed` | `gen` | the stub | **the commit point** (§6) |
| `rollback` | `from`, `to`, `reason` | the stub | an activated promotion undone, back to the committed generation |
| `aborted` | `gen`, `reason` | the stub | a promotion closed before activation |
| `recovered` | `reason` | the stub | any repair §7 made (a torn tail, a pointer rebuilt) |

**The grammar.** `installed`, then lifecycle records and transactions; a transaction is `promote`, then `aborted`, or
`activate`, `boot`…, and `blessed` or `rollback`. A `promote` is from the committed generation to another, with the
basis of a `checked` record of that generation (or the basis `committed`, for a return to a generation committed
before). While a transaction is open only the stub writes; the supervisor of the outgoing generation has stopped,
and the one on trial writes nothing until it is blessed. One writer at a time is also enforced by an exclusive lock
on `studio\promotions.lock` (Python's `msvcrt.locking` with `LK_NBLCK` raises `OSError` when the bytes are held,
VERIFIED, [msvcrt](https://docs.python.org/3/library/msvcrt.html); Rust's `File::try_lock`, MEASURED here on rustc
1.95). A journal that breaks the grammar is not interpreted (§7 R3).

**The torn tail.** A journal whose bytes do not end in LF has a torn final record: a writer stopped mid-append, and
since nothing acts on a record before its flush, nothing depended on it. The bytes after the last LF are set aside
(`studio\promotions.torn.<offset>`), the file is cut at the last LF, and the repair is recorded. Every other fault
refuses. SQLite's write-ahead log keeps the same policy: a frame counts only if its checksum, chained over the
header and every frame before it, holds, and recovery stops at the first that fails (VERIFIED for the comment's
rule, INFERRED for the recovery code as read: [wal.c](https://sqlite.org/src/doc/tip/src/wal.c)).

**The pointer** `studio\active.json`: `{"gen", "kind": "pointer", "protocol", "seq", "version"}` in the same canonical
form, naming the generation to run and the `seq` of the record that set it (`installed`, `activate`, `blessed` or
`rollback`). It is written after its record, by a temporary file, a flush and a write-through rename. It is a
**cache checked against the journal**, not an authority: missing or unreadable, it is rebuilt; behind, it is moved
on; but a pointer that names a record the journal does not have, or a generation the journal never set at that
`seq`, is evidence the journal lost records or was changed, and nothing is guessed (§7 R4, R5). The tries counter
is not in it: it is the count of `boot` records, so there is no second counter to fall out of step.

**A generation** `versions\<G>\`: its `manifest.json` (format `STUDIO-GEN 0`) lists every file with its sha256, in
ascending path order; `G` is the manifest's sha256. `Integrity(G)` holds when the manifest hashes to `G`, every file
it names hashes as named, and **no file is there that it does not name** — an unnamed `json.py` beside the code would
be imported. `art/studio_txn.py`'s self-test holds all three on a real directory.

## 6. The commit point

**A promotion is committed when its `blessed` record is durable, and not before.** The stub writes it after the
candidate, launched from the pointer in the studio's own job, answered the stub's `GET /healthz` with its own hash
and `ready` within the time allowed, and reported that the page spoke (the page's part is the admitted generation's
own word: trust passed to it at Admit). Before `blessed`, the promotion is uncommitted, whatever the pointer says:
recovery continues the trial only while the candidate verifies, its evidence is intact and a try remains, and
otherwise rolls back to the committed generation. After `blessed`, nothing undoes it: a committed generation that no
longer verifies is SAFE (a person chooses), and a return to an older version is a **new promotion** of a generation
committed before, with its own records. History is never edited.

The reasons, from practice. Mender's *ArtifactCommit*: the *"device is up and running after rebooting, and the commit
makes the update persistent"*, after which *"it is too late to do a rollback"* (VERIFIED,
[state scripts](https://docs.mender.io/artifacts/state-scripts)). Android A/B: the new slot is *"marked as successful
by calling `markBootSuccessful()`"* once `update_verifier`'s check completes, and *"the bootloader will fallback to
the old OS if the new OS fails to boot"* (VERIFIED, [A/B updates](https://source.android.com/docs/core/ota/ab)).
ARIES, and SQLite's log: *"Transactions commit when a frame is written that contains a commit marker"* (VERIFIED,
wal.c). Crash-only software (Candea and Fox,
2003): *"stop=crash and start=recover"*, and *"recovery code is exercised every time the system starts up"*
(VERIFIED, [the paper](https://www.usenix.org/legacy/events/hotos03/tech/full_papers/candea/candea_html/)) — the
stub has no start but §7, and a normal promotion is §7 taken step by step.

Two consequences, stated so they are not found later. A crash of the stub during a trial costs a try (the `boot`
record is written before the launch, so a crash loop always ends); with `tries` 1 such a crash rolls back, and the
plan's policy value, 3, survives two. And the plan's T2 changes in one word: promotion is not one atomic rename but
one durable append; the rename of the pointer is a cache update whose atomicity (axiom A1) no longer bears on
correctness — a torn pointer is rebuilt by R7.

## 7. Recover(J, P, F): the one decision

`J` the journal's bytes, `P` the pointer's, `F` the files (which generations verify; which evidence files hash as
recorded). The stub applies the first rule that holds, makes its writes in the order given (a record before the
pointer that names it), and takes the next decision, until a rule launches or stops:

```text decision-table
R0   J missing                                             SAFE journal-missing
R1   J's bytes do not end in LF                            set the bytes after the last LF aside; truncate; append recovered{torn-tail}; again
R2   a line of J is not the next record of the chain       SAFE journal-fault
R3   J's records break the grammar                         SAFE journal-grammar
R4   P names a seq beyond J's end                          SAFE pointer-ahead
R5   P's seq is not a target record naming P's gen         SAFE pointer-inconsistent
R6   P missing                                             append recovered{pointer-missing}; write P := target; again
R7   P not a pointer document                              append recovered{pointer-invalid}; write P := target; again
R8   P's gen is not the target's                           append recovered{pointer-stale}; write P := target; again
R9   promote open, not activated, and Integrity(C),        append activate{C}; write P := C; again
     Evidence(C), Integrity(committed)
R10  promote open, not activated, otherwise                append aborted{C, reason}; again
R11  activated, Integrity(C), Evidence(C), left > 0        append boot{C, left-1}; BOOT C (the stub appends blessed{C} once Healthy)
R12  activated, otherwise, Integrity(committed)            append rollback{C, committed, reason}; write P := committed; again
R13  activated, otherwise                                  SAFE fallback-corrupt
R14  no transaction open, Integrity(committed)             RUN committed
R15  no transaction open, otherwise                        SAFE committed-corrupt
```

*Target* is the generation the journal says should run: the committed one, or the candidate once `activate` is
durable and until its transaction closes. *Committed* is the last `installed` or `blessed`. `Evidence(C)` is a
`checked` record of `C` with the promotion's basis whose evidence file is intact (a return to a committed generation
needs its integrity alone). **SAFE** launches nothing: the stub shows the reason and the generations the journal's
valid records say were committed and that verify, and the person chooses one or quits. If the journal is intact the
choice is recorded as a promotion; if it is not, the damaged file is kept aside and a new journal begins with the
choice and the old file's sha256. Under the process-kill model, SAFE is never the answer (§8).

Rules R0–R8, R14 and R15 are what B1's stub needs (one generation, no promotion); R9–R13 come with B2.

## 8. What the reference measured, and what it does not show

`python art/studio_txn.py check` (MEASURED here, 2026-10-12, about 75 s and under 100 MB; `selftest` with its
plants about 100 s): 54 scripted promotions (from a fresh install and from a studio with one promotion behind it; to
a checked candidate and back to a committed generation; tries 1, 2 and 3; aborted, blessed after each number of
failed boots, rolled back for tries and for integrity at each boot),
written as sequences apart from `recover()`; **41,568 crash states** — after every durable write, with each append
torn at three places and each pointer write left unreadable, under 16 states of the files; in each, the decision
equals the one a crash-free run would take next from the records that were durable, computed by a second function
written apart (`allowed`); **195,376 crashes inside recovery** itself, after each of its writes and with each of its
appends torn, each held to the contract of the state it left (the only change allowed is a trial lost to the try its
`boot` consumed); every decision idempotent (a RUN taken twice writes nothing the second time); **8,704 chains** of
failed boots, every one ending at the committed generation or SAFE within the tries, and a healthy boot committing;
the commit never undone; every pointer written after its record; **134,773 damaged journals and pointers** — every
middle line altered, doubled, swapped or removed is SAFE, every cut at every byte is a torn tail or a shorter
journal, and a pointer the journal never set is SAFE; **all 16 rules reached**; 0 failures. `selftest` plants 16
wrong decisions (a torn tail treated as damage or kept; a damaged journal cut to a valid prefix; the pointer trusted
over the journal; a pointer ahead of the journal ignored; an inconsistent one rebuilt; a stale one run; a missing
one refused; the pointer moved before `activate`; no evidence check; no fallback check; no integrity check; one try
too many; no `boot` record; a rollback to the first generation; a commit undone) and the check catches each, and it
holds Integrity on a real directory (intact; an unnamed file; a named file changed).

What this does not show. That the stub will do this: it does not exist; B1's and B2's Rust is to be held to these
decisions by vectors the reference is to emit (B1), as `conform.rs` is held to DIRECTOR-0's. That Windows' writes
behave as the model assumes (a flushed line survives the process; a torn append leaves a prefix of its bytes): that is
experiment 5. That the policy is wise: `recover` and `allowed` are two statements of one policy by one author, so
their agreement checks the bytes, the pointer, the order of writes and termination, not the choice of rules. That the
last record is protected as the others are: the chain protects every line by the one after it; the last line is held
by the grammar alone. Anything outside the process-kill model.

## 9. Tags, across deletion and projects

A tag names one object by its id, in one project (`art\ledger\<brief>.tags.json` in the project's tree,
DIRECTOR-0's canonical form, written whole and flushed). Its counter only grows: a tag is never reassigned and never reused, so a deleted object leaves a gap.
When an object's id is gone at the head, its tag stays, listed apart as gone; a prompt that names it is refused
(`STUDIO-REFERENCE`, as today) with the head at which it is missing. An undo, or a candidate, that brings the same id
back brings the same object back — identity is the id (`art/studio_refs.py:17-18`) — and its tag with it. A new
project starts at `@1`; a copy of a project (Try's scratch copy) carries its tags. Tags are names, not content: they
are not in the ledger and change no head; losing the file loses names only.

## 10. The existing contracts, read from the repository

The review mapped its shape onto contracts it named; each was looked up (VERIFIED: it exists, as described here).

| named | what it is in the repository | what the studio takes from it |
|---|---|---|
| `tick_ref.py` | the tick's second implementation, from `RULES-1.md`; plays a browser's trace again and compares every tick byte for byte (`graybox/README.md:45`) | the simulation's authority stays the tick, apart from renderer and model; and the pattern of this contract: `studio_txn.py` is the transaction's second implementation |
| cross-browser comparison | cross-browser equivalence on the tactical map, MEASURED once on 2026-10-11 (`graybox/README.md:258`) | presentation never becomes simulation state |
| BOT-REF-0 | a bot's walk made in Python from the map, played by a browser, compared input by input (`graybox/README.md:47`) | a deterministic bot, not a model; its lesson, that an action is an input judged by the authority, is the same as ADMIT-0's and DIRECTOR-0's, which are the closer precedent for "a model proposes; Verðandi admits" |
| INPUT-0, INPUT-0a | a walk replays headless; G31, a checkout path with a space, found by a perturbed pass (`README.md:264`) | paths are parsed whole at every boundary; B1's self-test includes a profile path with a space and a non-ASCII letter |
| DIFF-0 | DESIGN-IR/DIFF-0: the design text compiles to one canonical change set against a parent; the proposal id is the sha256 of its exact bytes (`README.md:255`) | a candidate is bound to its base by identity and named by its exact bytes (§3) |
| HERMENEUTICS-0 | what the design language means apart from the two programs that compile it (`README.md:272`) — **not a source fence**; the fences are the `*-fence` rows | the reserved list is the studio's fence; HERMENEUTICS-0's lesson is different: a record's meaning is fixed apart from its writers (§5's grammar) |
| environmental independence | a declared audit, deferred by his ruling of 2026-10-08 (`docs/ROADMAP.md:186`); no finding claims it | the basis declares the toolchain and configuration; nothing here claims independence |
| ACCT, VCT-0, T2/T4/T5 | `STUDIO-APP.md` §5 | the claims this contract implements |

## 11. The five experiments

Off the gate, under `tools\probe\`, run on his machine, each printing only what its verdict needs (no edition, no
hardware). Every probe's lines have one form, and its last line is its verdict:

```text
PROBE <n>-<name> <case> HELD|BROKEN|SKIPPED [key=value ...]
PROBE <n>-<name> VERDICT HELD
PROBE <n>-<name> VERDICT KILLED <criterion>
```

| n | name | measures | kill criterion → the change |
|---|---|---|---|
| 1 | `edge_app` | Edge `--app` with a private profile: pointer lock; the tree's end on the last window | pointer lock does not engage → WebView2 moves into B1 |
| 2 | `job_object` | a job with `KILL_ON_JOB_CLOSE` from Python: every child gone when the handle closes | assignment fails under his shell's job → the stub breaks away |
| 3 | `pointer_swap` | 200 killed write-through renames: the pointer reads old or new | a torn pointer is read → nothing changes in correctness (R7 rebuilds it); recorded against A1 |
| 4 | `low_integrity` | the suites at low integrity; a write to `studio\` from inside refused | a suite cannot run there → the boundary is tamper-evidence, written so |
| 5 | `journal_replay` | a writer making §5's records with flush and `_commit` and the pointer by write-through rename, killed by `TerminateProcess` at random over 200 runs; after each kill `python art/studio_txn.py recover` on the directory, compared with the contract for the records the writer had acknowledged, or one more | any SAFE, any chain fault, or any decision not the contract's → the record form is revised (the shell's length-and-hash envelope) before B2's promotion code, and B1 keeps R0–R8, R14, R15 |

## 12. What this contract does not decide

The default model (his). The numbers: `tries` (the plan's 3), the health timeout, the heartbeat. The source domain's
patch format and its footprint grammar (B2). Whether SAFE's choice is a window of the stub's or a page served by a
known generation. Garbage collection beyond its one rule: never the committed generation, the one committed before it,
or an open transaction's candidate. And whether anything here enters the gate: it does not.
