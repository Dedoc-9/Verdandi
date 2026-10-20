<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# DIRECTOR-0 — the Scope Declaration Protocol and the Intent Ledger (version 0)

A prompt is answered by candidates. Each candidate is checked against the head it meets and gets a verdict. A person
admits one or refuses it, and every step is appended to a ledger that is never rewritten. The protocol protects the
creator's intent; it is not the product. What it proves and what it does not is said at the end.

| file | what |
|---|---|
| `intent.py` | the canonical byte form (VERDANDI-CANON 0) and the intent document (VERDANDI-INTENT, version 0) |
| `scope.py` | `check_scope(intent, base, candidate, current, checks) -> verdict`: pure, no files, no clock |
| `ledger.py` | the append-only, hash-chained ledger |
| `vectors.json` | the conformance vectors: inputs and exact expected outputs, readable by any implementation |
| `vectors_source.py` | the vectors' inputs, and their writer |
| `conform.rs` | a second implementation in std-only Rust, held to the vectors without the Python |
| `inverse/`, `inverse_freeze.py`, `inverse_rows.py` | 0254's freeze of the exact inverse (§9), its reader, and the director's rows that hold the code to it |
| `../director.py` | the commands that run it all over a brief |

## 1. The canonical form (VERDANDI-CANON 0)

It is a restricted JSON. It is not RFC 8785 and claims no compatibility with it. RFC 8785 writes non-ASCII as UTF-8;
this form writes ASCII only. Its keys are ASCII, so the two key orders agree, but the string bytes differ.

| rule | exactly |
|---|---|
| values | objects, arrays, strings, `true`, `false`. No numbers of any kind, no `null` |
| integers | written as strings in the fields that declare them: `0` or `-?[1-9][0-9]*`, at most 19 digits, never `-0` |
| keys | `[a-z][a-z0-9_]*`, unique within their object; members in ascending byte order of key |
| strings | Unicode scalar values (no lone surrogates). `"` → `\"`, `\` → `\\`, U+0008 `\b`, U+0009 `\t`, U+000A `\n`, U+000C `\f`, U+000D `\r`. Every other code point below U+0020, U+007F, and every code point above U+007E → `\u` and four lowercase hex digits (above U+FFFF as a surrogate pair). `/` is not escaped |
| layout | no whitespace outside strings |
| bytes | ASCII. A document's identity is the sha256 of its bytes |

A document is admitted only in this byte form. Bytes that parse but are not their own canonical form are refused.
These are the refusal codes:

| code | for |
|---|---|
| `INTENT-BYTES` | a byte above 0x7F |
| `INTENT-NOT-JSON` | not JSON |
| `INTENT-NUMBER` | a number |
| `INTENT-NULL` | null |
| `INTENT-KEY` | a bad key |
| `INTENT-DUPLICATE-KEY` | a key twice |
| `INTENT-STRING` | a lone surrogate |
| `INTENT-NONCANONICAL` | anything else that parses |
| `INTENT-TYPE` | writing a value of another type |

A document with more than one defect is refused, but which of its codes is reported is not specified. The vectors
plant one defect each.

## 2. The intent (VERDANDI-INTENT, version 0)

Exactly these fields, all strings or lists of strings:

- **`format`** is always `"VERDANDI-INTENT"`.
- **`version`** is `"0"`. Any other version is refused (`INTENT-VERSION`) and never translated. A translator comes with
  the first real change of format, and stored events are never rewritten. The inverse forms below (0254) widened the
  grammar under version "0", by his ruling (2026-10-20): *"Ruling: Keep `VERDANDI-INTENT 0` and append the new vectors directly to the current matrix."*, and *"The tension with the README documentation is recognized; the requirement for a translator tool is deferred until the first real structural format change occurs."* No stored event and no
  expected output changed. It is one way: a reader from before 0254 cannot read a stored inverse that holds an `@`
  line (its `load_intent` raises `INTENT-REVISION`, its studio's Undo is answered as an internal error, and its
  `verify` raises from the first such undo); an inverse of `- KEY` lines alone still reads.
- **`brief`, `prompt`, `candidate`, `rationale`**
- **`base`** holds `{art_sha256, world_sha256, exporter_sha256}`: the head the candidate was written against.
  `world_sha256` is the graybox world W's canonical sha256, which covers the admitted layout, the map's overlay and
  the converter.
- **`scope`** is the address patterns the candidate declares it will touch.
- **`revision`** is a list of art lines:
  - `= <statement>` replaces the statement with the same key;
  - `+ <statement>` adds one whose key is new;
  - `- <key>` removes one.

  Three inverse-only forms (0254), each its two characters, exactly one space, then the VERDANDI-CANON 0 bytes of one
  array: `@= [I,W,R]`, the row at 0-based position I as the admission wrote it (W) and the row to restore (R);
  `@+ [I,R,S]`, the row R to put back at position I, S the row that then stands at I, or `false` when R was the last
  row; `@~ [A,B]`, the count A of trailing empty rows found and the count B to leave. Positions and counts are strings
  matching `0|[1-9][0-9]{0,18}`; a row is a string holding no LF; `false` only as `@+`'s third field; any other line
  beginning `@` is `INTENT-REVISION`. `validate` checks their syntax only. They are applied only by an undo whose
  `--inverse-of N` names the admission that recorded them (`inverse_of_ok`), each under its guard (`INTENT-APPLY` when
  the recorded row does not stand where it says, never searched for by key); anywhere else the revision is refused
  whole, `INTENT-INVERSE-ONLY`. What each forward line records: `=` an `@=`; `-` an `@+`; `+` its `- KEY`, and after it
  `@~ ["1","K"]` when the parent's rows did not end in exactly one empty row.

  A statement's key is its verb (`skyline`, `fog`, `title` and the other statements that occur once), its verb and
  first word (`tower plaza`, `material concrete`), or for a canopy its verb, region and corners. A brief names each
  key once.
- **`layout`** is design-text lines (`open`, `close`, `room`, `entrance`, `paint`), admitted through the design tool.
  It is empty for a revision of the look alone.

The head is `sha256(canonical bytes of the three base parts)`.

## 3. Scope (protocol DIRECTOR-0, version 0)

**Addresses.**

| form | for |
|---|---|
| `<region>/<kind>/<place>` | dressing and its light (`plaza/tower/18,10`, `plaza/neon/13,17:s`; the skyline's region is `city`) |
| `play/<kind>/<id>` | C's boxes |
| `material/<name>`, `env/<field>`, `view/<name>`, `asset/<name>`, `region/<name>` | the rest |

A piece's identity is its kind and place: one fixture to a place, which the exporter enforces.

**The reference graph.** A piece references its material; a material may name a parent, though no brief does yet. A
material's identity is the sha256 of its record: colours as `R,G,B` and every other number as `%.4f` text.

- A material changed if its record's digest changed, or its parent changed. This is the early cutoff: the same
  content gives the same digest, and nothing propagates.
- A piece that did not change, whose material did, is affected.
- A light whose colour and candelas are its material's emission is compared without them, so it is affected, not
  modified.
- A cycle refuses the candidate (`GRAPH-CYCLE`), and so does a reference to a missing material (`GRAPH-DANGLING`).

**Patterns.**

- Patterns are `/`-separated. `*` matches one segment and `**` matches any number.
- A pattern beginning with `*` or `**` never matches the namespaces `play`, `surface`, `material`, `env`, `asset`,
  `view`, `layout` or `region`. Those are granted by name.
- `layout/<region>` allows the layout to change cells in that region, and with them the play boxes the converter
  rebuilds.
- `surface/<kind>` allows a change in the look of play geometry of that kind, never its shape.
- `play/...` is never granted.

**Verdict.** A canonical document with these fields:

- `protocol`, `version`, `verdict`, `codes`, `intent_sha256`;
- `written_against` (the intent's base head) and `checked_against` (the head it met), and `re_evaluated`;
- `declared`, `realized`, `affected`, `unclaimed`, `phantom`, `cells_changed`, `materials_changed`, `failed_checks`.

Lists are in ascending byte order; changed cells are `x,z` in ascending z, then x. The verdict is one of three:

- **REFUSED** on any of:
  - `SCOPE-RESERVED-GRANT` or `SCOPE-PATTERN`;
  - `SCOPE-LAYOUT`: a cell changed outside every layout grant;
  - `SCOPE-PLAY`: the spawns or the grid changed, or play geometry changed with no cell changing;
  - `GRAPH-*`;
  - `CHECK-FAILED`: an art check failed, so the art would stand where a player can be or play would break.
- **LEAKAGE** (`SCOPE-LEAK`) if anything realized or affected is covered by no pattern. It is admissible only when the
  person says so (`--accept-leakage`), and the ledger records that.
- **CLEAN** otherwise.

`phantom` lists the declared patterns that touched nothing.

**Head-specific.** `HEAD-MOVED` says the candidate met a head other than the one it was written against. The verdict
is always the head it met: a candidate is never admitted on a verdict reached at another head.

## 4. The ledger

`art/ledger/<brief>.ledger` holds one canonical document per line, each followed by LF. Every event has:

- `protocol` and `version`;
- `seq`, an integer string;
- `prev`, the sha256 of the previous line's bytes;
- `kind`, and the kind's own fields.

| kind | records |
|---|---|
| `genesis` | the brief, the head and its parts, the art text and the design text |
| `evaluate` | the intent's canonical text and sha256, the verdict (with its base and checked heads), the head after it would be admitted, `re_evaluation_of` (the seq it re-evaluates, or ""), its ADMISSION-0 `record` (0222, §7), observed timings |
| `refuse_input` | an input refused before it was an intent: its sha256 and code |
| `admit` | the evaluation admitted, the head before and after, `accepted_leakage`, the exact inverse revision (positional since 0254 for `=`, `-` and a `+` whose parent did not end in exactly one LF, §2; old ledgers replay as they are, and an inverse of `- KEY` lines alone does not show its era), the layout lines, who chose, and (0222) its `evidence`: the still's sha256 and its detectors as the host read them, whether it was admitted despite them, or the admission it is the exact inverse of |
| `refuse` | an evaluation a person refused, and their words |
| `rebase` | a change made outside the loop (a hand edit, a new exporter): the texts and heads before and after, and (0245) the art checks it passed: a rebase is refused for files that fail one (`REBASE-CHECKS`) or that the exporter refuses (`REBASE-EXPORT`), and is read, replayed and appended under the content lock |
| `approve` | a person's acceptance of a still from a view: the image's sha256, the render configuration, and QUALITY-0's detectors read on it (0221). A still the detectors flag, or cannot read, is approved only with `--despite-detectors`, which the event records (provenance, never a gate: a detector proves nothing either way) |

Re-evaluation appends a new `evaluate` event naming the old one, and the old verdict stays exactly as it was.

Verification (`director.py verify`) replays the ledger from its genesis:

- every event must follow from those before it;
- every admission must rest on an evaluation made at the head it admitted;
- no admission may rest on a REFUSED verdict;
- an admission of an evaluation that has a record must carry the evidence the record requires (`LEDGER-EVIDENCE`), and
  one of an evaluation from before the record carries none;
- every admission's still is on the disk as the bytes it names, its detectors read again from them (`LEDGER-STILL`;
  the launcher's look checks the bytes only);
- a rebase's text must be the art its parts name, and its head its parts' (`LEDGER-REPLAY`), and none may record a
  failing check (`LEDGER-REBASE`, 0245);
- an admission applies an inverse form only as the recorded undo of an earlier admission (`LEDGER-INVERSE-ONLY`, 0254),
  and a stored inverse holding an `@` line must be the one its revision records over the text it was admitted on
  (`LEDGER-INVERSE`, 0254); one without an `@` line is not compared (§9);
- the files must be the text and head the replay reaches.

An edit outside the loop is refused (`UNLOGGED-CHANGE`) until a `rebase` records it. LEDGER-SAFE-0 (0245): no event that names a
head is appended over it meanwhile. An evaluation, an admission or an approval is appended under the content lock, and only
while the files are the head the ledger replays to and that is the head it was checked against; otherwise
`LEDGER-UNLOGGED` (rebase first) or `HEAD-MOVED` (evaluate again), and nothing is appended. A `refuse`, which names no
head, is appended as before. Before it, one evaluation over
an unrecorded change appended an event that replay, and so rebase, refused for good (MEASURED, 2026-10-16).

## 5. Running it

```
python art/director.py lens plaza-night plaza             # what a proposer reads before it writes
python art/director.py evaluate plaza-night art/rounds/plaza-imposing/*.intent
python art/director.py record plaza-night 1               # its record: rung and why, certifies, not checked, needs, rests on
python art/director.py admit plaza-night 1 --still s.png  # a person's choice, by its ledger number, with a still of it as drawn
python art/director.py reevaluate plaza-night 3           # after the head moved
python art/director.py evaluate plaza-night U.intent --inverse-of 5   # an undo of admission #5 (0254): U's revision is #5's stored inverse
python art/director.py admit plaza-night 9 --inverse-of 5  # admitted as #5's exact inverse, in place of a still (--inverse-of since 0222)
python art/director.py reevaluate plaza-night 9 --inverse-of 5        # an undo re-evaluated after the head moved
python art/director.py refuse plaza-night 4 --note "it reaches the bases"
python art/director.py verify plaza-night
python art/director.py selftest                           # the vectors and the whole lifecycle, in a scratch copy
rustc -O art/director/conform.rs -o art/build/conform && art/build/conform art/director/vectors.json
```

On Windows, name the program `art\build\conform.exe`. `art/build/` exists once `art/dress.py` has run.

The self-test's fixture is the round's `base/`: the files at the head its candidates were written against. It checks
that its scratch copy starts at that head, so it does not depend on what has since been admitted to the live brief.

## 7. Every verdict complete (ADMISSION-0, 0222)

By the owner's ruling of 2026-10-13, *"Every verdict states what it did not check."* and *"Four candidate rungs,
classified by the host … The model must not choose its own rung, and filenames alone must not determine it."*, every
evaluation carries a record (`art/director/contract.py`, pure, in the ledger's restricted form) beside its DIRECTOR-0
verdict, which is unchanged (the 62 vectors still hold):

| field | what |
|---|---|
| `rung`, `rung_basis` | computed by the host from the effective change, the scope protocol's realized and affected addresses, never from the intent's words: **A** when each is an instance or a parameter of an admitted kind, **C** when one is of a kind the classifier does not know, **D** when the candidate did not export (its change unknown, classified at the top). An intent carries no code and the language has no form for vocabulary, so B does not arise from one |
| `certifies` | derived: the scope protocol's finding, the layout's cells, and each check that ran and passed, by name |
| `not_checked` | every expected check that did not run (a skip is never a pass) and what the director never checks: whether the candidate does what was asked, whether the picture is good, the scene in Unreal, anything over time, the provider's account of itself |
| `horizon` | 0 ticks: nothing in the scene moves, and nothing over time is claimed |
| `trusted` | the sha256 of the exporter and of each component the verdict rests on (the checks, QUALITY-0, the director, scope, the record, the canonical form, the ledger, the graybox checks, the renderer) |
| `requires` | for rung A: the verdict CLEAN (or LEAKAGE accepted, recorded); every expected check ran and passed; a still of the candidate as drawn, its detectors read by the host, a flagged still admitted only despite them (recorded) — or, for an undo, the admission it is the exact inverse of (checked, not taken on its word). Rungs C and D are not admitted by the director |

`admit` refuses (`ADMISSION-0`) until every item is present; an evaluation from before the record is evaluated again.
The still is kept beside the ledger by its sha256 (`art/ledger/<brief>.ledger.stills/`), written under the content lock
before the admission's first write. It is bound to the admission by digest; nothing here proves it shows the candidate
(the studio's page takes it from the canvas as it draws the candidate; at the command line a person gives it).

## 8. The scene binding's contract (BINDING-0, 0252) and its enforcement (0253)

His ruling (2026-10-18): *"Ruling: LOCK — REFUSE on a scene-binding mismatch for 0252."* An admission that relies on a
still, a preview or an undo account bound to another scene than the exact candidate admitted is refused, and an unknown
binding with it. The contract that makes his ruling exact is registered here before any code enforces it: one file per
version under `bindings/` (`BINDING-0.v0.json`: the identities, the comparison rule, the outcomes, the order, the five
cases in his words with their expected results, the decision record, what is deferred, in his words where it quotes
him), and `bindings/register.jsonl`, one line per version naming its file and sha256, appended and never rewritten.
`python art/director/binding.py check` holds the files to the register (`BINDING-0 REGISTERED version 0 sha256 …`);
it reads, and decides no admission. The inverse's repair is 0254's, against the same contract (§9). The director's command
line is outside version 0 (his choice: it declares no scene). RBAP, the principle the contract states, is a proposed
engineering invariant, not a theorem.

**Its enforcement (0253).** The studio's admission and undo through the host (art/studio.py, `Gateway.admit` and
`Gateway.undo`) enforce version 0, the host authoritative: the evidence a press relies on (the still's kept scene; a
preview the admission names by its id; the undo's `of` and `scene`) is compared, exactly, with the identity v0 names
(the scene the admission's own evaluation exports; the undo's target and the world's scene at the undo), and a press
whose evidence names another is refused `BINDING-MISMATCH`, one absent or not well formed `BINDING-UNKNOWN`. The check
is the `gate` that `cmd_admit` passes to `commit_admission`: the commit calls it under the content lock after every check
it makes (`held_head` the last) and before its first write (the still into `<brief>.ledger.stills/`, the pending folder,
the admit event, the files), and a gate that raises leaves nothing of the admission written. The command line passes
none. The host pins version 0 and its sha256 (`BINDING_SHA256` in art/studio.py) and never reads the register at a
press; STUDIO's rows hold the pin to the register's version-0 line.

Before the check was built its test matrix and its conformance vectors were frozen, files of their own beside the
contract and never in `register.jsonl`: `bindings/0253-matrix.json` (every row's state, switches, answer, director's
code, decision record, ledger delta, brief and certificate) and `bindings/0253-vectors.json` (keeping, the still's rule;
field, the comparison of one field; piece; press; record, the record's bytes; the preview's id), each held to its sha256 by a
line of `bindings/frozen-0253.jsonl`. `python art/director/binding_freeze.py check` reads them (`BINDING-0 0253 FREEZE
FROZEN: 80 vectors, 36 matrix entries naming 92 rows (34 plant rows) against BINDING-0 version 0 sha256 …; nothing
open`); `binding.py check` and the register are unchanged. STUDIO's rows of the matrix (art/binding_rows.py, run by
`python art/studio.py selftest`) hold the host's pure functions to the vectors and every press to the matrix; a frozen
file is never edited (a change is a new freeze, recorded before the code it governs).

## 9. The exact inverse (0254)

His ruling (2026-10-20): *"Ruling: (a). 0254 records the inverse of = and - as the exact row at its position (and the trailing blank lines of +), applied only by undo, frozen first and built second, against BINDING-0 v0 unchanged."* Built in two commits: the freeze first, then the code. The freeze is
`inverse/0254-spec.md` (the specification as he ruled it, his ruling files embedded whole), `inverse/0254-vectors.json`
(115 vectors, 40 of them worked by hand), `inverse/0254-matrix.json` (55 rows in five suites, 33 plants, each with the row
that catches it) and `inverse/legacy/plaza-night.7dee210.ledger` (7dee210's ledger byte for byte, replayed only), each
held to its sha256 by a line of `inverse/frozen-0254.jsonl`. `python art/director/inverse_freeze.py check` reads them
(`INVERSE-0254 FREEZE FROZEN: 115 vectors (40 by hand), 55 matrix rows in 5 suites, 33 plants (28 new keys for R5), …`),
and the director's rows in `inverse_rows.py`, run by `python art/director.py selftest`, hold the code to them. A frozen
file is never edited: a change is a new freeze, recorded before the code it governs. BINDING-0 version 0 is unchanged.
The command line's undo is the evaluation's and the admission's `--inverse-of N`, and there is no undo command (his
ruling: *"Ruling: Implement `evaluate/reevaluate FILE --inverse-of N`."*).

What it does not show (`inverse/0254-spec.md` §9, and docs/CAPABILITY-MATRIX.md, 2026-10-20): an undo over a moved world
restores nothing (it is refused where a recorded row moved, and otherwise applied and reported); a `+` is undone by its
key; the forward ops' own defects stand; a stored inverse with no `@` line (recorded before 0254, or forged in that form
by a writer of the ledger's files) is applied as it stands; the theorem holds for a revision that passes `validate` and
adds no lone verb, not for every revision `apply_revision` accepts.

## 6. What it proves, and what it does not

| claim | shown by | does not show |
|---|---|---|
| the rules are written completely enough to be implemented twice | `conform.rs` reproduces all 97 vectors (62 when this was first written, 65 before 0254): verdicts field by field and canonical bytes byte for byte; three planted rule defects caught | that either implementation is right: one author wrote both, and the vectors are the contract; the inverse forms' application, which the Rust twin does not implement (it checks their syntax only; his ruling on OPEN-4, *"Ruling: Defer."*): the Python-judged frozen 0254 vectors hold it |
| a candidate's verdict belongs to the head it met | `HEAD-MOVED`; the self-test refuses an admission at a moved head and re-evaluates as a new event | — |
| the ledger is append-only and replays to the files | `verify`; the self-test's plants (a hand edit, a changed line, a forged rebase) refused; LEDGER-SAFE-0's rows (0245): an evaluation over an unrecorded hand edit, a late one after the head moved, an admission over a hand change back and a rebase of failing files each refused with nothing appended, and each guard's plant shown to leave a ledger replay refuses | the last line alone has no successor to name it: it rests on the commit that holds it |
| the layout's authority stays the shell's | a layout candidate is compiled and admitted by the design tool, and C is rebuilt by the graybox converter | — |
| every verdict says what it certifies, what it did not check and its rung; an admission brings what its record requires | the director's self-test (17 rows: the record complete, an admission refused without a still, with a flagged still, or with an undo that is not one; the evidence and the still read back; three plants on the evidence; the classifier on a kind it does not know, a candidate that did not export, a skipped check) | that the still shows the candidate, or that the rung is right beyond the kinds the classifier lists: it is a restatement of the language, held to it by the plants |
| the art is good | nothing here | a person judges rendered views; an approved still records acceptance, not reproducibility |
