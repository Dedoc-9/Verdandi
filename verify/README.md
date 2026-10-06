<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# `verify/` — the gate

`python verify/verify.py` runs every row and prints `GATE PASSED` or `GATE FAILED`, then a reconcile line
naming the rowset. A change is landed only when two consecutive runs are byte-identical (`sha256` of the two
logs equal) and the gate reads PASSED. Rows that need `rustc` are SKIPPED without it, count-stable, so the
rowset digest does not depend on the toolchain being present — only the verdict does.

## Blueprint

The gate is the program's only judge, so its design is about what it may and may not be made to say.

```text
    verify.py     row(name, fn) in a fixed order ─► PASS, or Red with a reason ─► GATE PASSED | GATE FAILED
                  RECONCILE  rowset <sha256 of the row names>  <rows> / <fail> / <skipped>
                  242 rows today, rowset aa94c886190510c7

    a row         builds what it tests from source · runs it · compares bytes · then PLANTS a defect and
                  requires the refusal. A row with no plant that bites is not finished.

    landing       two consecutive passes, their logs byte-identical, GATE PASSED. A third pass with the host's
                  records present, when a rung reads them.

    preregister.json   43 entries: hypothesis · success · failure · limits · instrument · chain hash.
                       Locked before the instrument runs. Never edited after it is pushed: a correction is an
                       amendment entry with its own hash.

    envelope.py   RECORD-0: one writer, one firewall, for every record the tree mints
    savedform.py  READER-COURT-0: the strict reader of everything read back; no json.load beneath it
    reasons.json  REASON-COURT-0: the reason register — what every refusal the gate requires is expected to say,
                  and where that expectation comes from. Registered, pinned by its hash in the ledger; read
                  by the six reasoncourt rows, through savedform.py, and written by nothing
    mints.json    MINT-WATCH-0: the mint register — every raise site of a refusal class, read from source,
                  and which row reaches which site how often, measured. Registered; read by the four
                  mintwatch rows, through savedform.py, and written by nothing
    pins/         the goldens Verðandi mints itself (the HUD's, the blit's)
    the sealers   off the gate, on a named host: witnesses first, then the number, then the envelope
```

| Invariant | Mechanism | Row |
|---|---|---|
| The gate's output is a function of the tree | no clock, no host name and no wall-time inside a row; two passes compared byte for byte | the landing condition |
| The rowset is what was run | its digest is over the row names in order; a skipped row still counts | the `RECONCILE` line |
| No record hides a verdict | a recursive scan for verdict-shaped keys; a planted one is refused | `records-firewall` |
| Two languages seal the same hash | Python recomputes every Rust-written chain hash | `records-twins` |
| A method is locked before its number | every entry's hash recomputed; an entry with no failure condition is refused a seat | `records-preregistered`, each rung's `*-preregistered` |
| A sealer cannot seal a malformed run | each sealer is given malformed raws and must refuse them | `*-sealer` rows |
| A fence is read from the source | a row reads the program's text for what must and must not appear | `*-fence` rows |
| A record on the disk is of the saved form | read through the strict reader; written only after it accepts the bytes | `readercourt-corpus`, `readercourt-writers` |
| A forgery is refused for its own row's reason | every command and every read is watched for a refusal by the reader | `readercourt-fence` |

Off-gate instruments (wall-clock on a named host) never print inside the gate; they write records beside the
oracle with the witnesses checked first.

`pins/` holds the goldens Verðandi mints itself (the HUD's overlay identities and composites), each held under
laws by rows; the oracle folder holds only what Urðr certified.

`envelope.py` is RECORD-0: every record Verðandi mints (pins, `workshop/attest`, `kernel/attest`,
`shell/attest`) is written in the envelope — data + provenance + `claim_class` + `validity_scope` +
`forbidden_interpretations` + a chain hash, with no verdict-shaped key inside data — and read through one
firewall (`records-firewall`); `workshop/edit.rs` carries the Rust twin, and `records-twins` proves the two
agree. `preregister.json` hash-locks each host-measuring rung's hypothesis and success **and** failure
conditions before its instrument runs (`records-preregistered`); a fork of the owner's
`executable-epistemics`. `bench.py` writes the kernel's wall-clock as such a record, budgets as data, the
comparison in the reading.

`savedform.py` is READER-COURT-0's Python reader: the saved form's language implemented apart from the Rust reader
in `../kernel/savedform.rs`, with no `json.load` or `json.loads` beneath it. `envelope.py`, `livesession.py`,
`seal_sessionwalk.py` and `seal_session.py` read through it; `envelope.py`'s write gives it the bytes first. The json
module is still used here to render, and by rows that inspect a raw the shell wrote: neither is a reading of the
saved form.

`RUNGS.md` is the ledger: one graded entry per rung, with what it measured, what it does not show, and the
row that would redden if the claim were false.

## The instruments, off the gate

| File | What it seals, or reads |
|---|---|
| `bench.py`, `gauntlet.py`, `gauntlet1b.py`, `gauntlet1c.py`, `rebreakdown1.py`, `locality0.py`, `gauntlet2.py` | the render campaign's host courts, into `kernel/attest/` |
| `bearingfast.py`, `bearingsweep.py` | BEARING-FAST-0's speed court and its sweep, into `kernel/attest/` |
| `seal_present.py`, `seal_latency.py`, `latency1.py`, `latency1r.py`, `framesplit.py`, `presentscale.py`, `presentstretch.py`, `allocreuse.py`, `allocreuse1.py`, `presentexact.py` | the present-path courts, into `shell/attest/`; `diagcommon.py` is their shared host flow |
| `hoststate.py` | HOST-STATE-0 and HOST-STATE-1: the host's state recorded beside a court, read by no rule |
| `drift.py` | DRIFT-0: the locked court repeated, each run sealed, a descriptive panel and no verdict |
| `refusallog.py`, `runledger.py` | readers of the shell's two unsealed logs: they validate, count and join, and never write |
| `liveloop.py` | LIVE-LOOP-0's live walk, counts only |
| `livesession.py` | a saved live session made a committed record: the seal, the base files, the fold, the lineage, the renderer identity, the workshop's own `sessionwalk verify`, (ADMIT-0) each admitted edit's envelope, and (DESIGN-EVENT-0) each batch whole, in order and agreeing, counted in the record |
| `seal_walk.py`, `seal_session.py`, `seal_sessionwalk.py` | the committed reference walk, session and session-walk under `workshop/attest/` |

## Dev notes

- **How a rung lands.** Court, ratify, preregister in its own commit, build, mutation-test, gate twice
  byte-identical, deliver as a patch, run on the host, seal, document. The registration is pushed before the build
  exists, so the method cannot be fitted to the result.
- **Mutation testing is off the gate and decides whether a row is trusted.** Defects are planted in the program one
  at a time and every one must turn some row red. The counts are in the ledger (ADMIT-0: 39; DESIGN-EVENT-0: 49, one
  of them equivalent). A mutant that
  survives is a missing case, and the case is added before the rung is delivered.
- **Rows assert the apparatus.** A row checks that the plant bites and the bytes agree. It never asserts a hoped
  result, and no row reads a wall-clock number.
- **A registration is text the gate hashes.** The entry's chain hash is recomputed on every pass, so a silent edit
  to a locked method is a red row and not a judgement call.
- **Count again.** The gate reads what it is pointed at. Two facts recorded for READER-COURT-0 (the number of JSON
  parsers, the deepest nesting among the records) were each off by one until they were recounted. Neither was a
  row's to catch.
- **A plant is bytes.** A file the gate plants for a command is written in binary mode or with a fixed line ending.
  One opened in text mode became CR LF on the owner's Windows host and was refused for its form; the watch said so.
- **The register is the expected side.** `reasons.json` was written from the gate's own statements and variables
  and from registered text, never from what a program printed. Its line numbers are lines of the `verify.py` it
  names by hash; the build will move them and hold the text.
- **Read the register's counts by the entry's sentence.** Four parts make the 1,103 endings: 1,072 in a code head,
  23 `REFUSE(any)`, 6 held only by their row, 2 unjudged. `endings_with_one_code_in_prose` (3) is inside the first
  part and is not a fifth. The build's row is to hold that and cite the entry for it.
- **A mutant can be a non-mutant.** In READER-COURT-0's mutation test four planted defects survived because they
  were written so that they changed nothing. A survivor is first a question about the mutant.
- **The dev harness is not the gate.** Running chosen rows alone can fail a row that depends on an earlier row's
  outputs (`records-twins` wants the workshop's records present). Only a full pass is a pass.

## Ghosts

In full in [`../docs/GHOSTS.md`](../docs/GHOSTS.md). The ones that live in this folder:

- **The gate and the program have one author.** A row can only catch what its writer thought to plant. Mutation
  testing widens that and does not close it.
- **G23.** Where two implementations are held against each other (the envelope's twins, the two recognizers of a
  proposal, and by registration the two readers of the saved form) one author wrote both from one grammar. Their
  agreement shows consistency. The cases with verdicts written down beforehand are what stand against a shared
  mistake.
- **G19.** These tools read saved-form documents through the strict reader now. The gate's own rows still read the
  raws a command writes with `json.load`, the registry too: those are not the saved form.
- **A source fence shows where a check is written, not that it runs.** `readercourt-writers` plants a fault in the
  shell's save and sees it refused. For the journal, the checkpoint and the workshop's writers it reads the source.
- **A green pass is not proof by itself.** A stale build directory or a cached bytecode file can make a pass lie.
  The landing condition is two passes from clean trees, and a number that looks impossible is checked before it is
  believed.
- **G5, G10.** Every sealed number is one host; some tails are a handful of samples.
