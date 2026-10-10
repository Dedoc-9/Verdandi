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
  the first real change of format, and stored events are never rewritten.
- **`brief`, `prompt`, `candidate`, `rationale`**
- **`base`** holds `{art_sha256, world_sha256, exporter_sha256}`: the head the candidate was written against.
  `world_sha256` is the graybox world W's canonical sha256, which covers the admitted layout, the map's overlay and
  the converter.
- **`scope`** is the address patterns the candidate declares it will touch.
- **`revision`** is a list of art lines:
  - `= <statement>` replaces the statement with the same key;
  - `+ <statement>` adds one whose key is new;
  - `- <key>` removes one.

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
| `evaluate` | the intent's canonical text and sha256, the verdict (with its base and checked heads), the head after it would be admitted, `re_evaluation_of` (the seq it re-evaluates, or ""), observed timings |
| `refuse_input` | an input refused before it was an intent: its sha256 and code |
| `admit` | the evaluation admitted, the head before and after, `accepted_leakage`, the exact inverse revision, the layout lines, who chose |
| `refuse` | an evaluation a person refused, and their words |
| `rebase` | a change made outside the loop (a hand edit, a new exporter): the texts and heads before and after |
| `approve` | a person's acceptance of a still from a view: the image's sha256 and the render configuration (provenance, never a gate) |

Re-evaluation appends a new `evaluate` event naming the old one, and the old verdict stays exactly as it was.

Verification (`director.py verify`) replays the ledger from its genesis:

- every event must follow from those before it;
- every admission must rest on an evaluation made at the head it admitted;
- no admission may rest on a REFUSED verdict;
- the files must be the text and head the replay reaches.

An edit outside the loop is refused (`UNLOGGED-CHANGE`) until a `rebase` records it.

## 5. Running it

```
python art/director.py lens plaza-night plaza             # what a proposer reads before it writes
python art/director.py evaluate plaza-night art/rounds/plaza-imposing/*.intent
python art/director.py admit plaza-night 1                # a person's choice, by its ledger number
python art/director.py reevaluate plaza-night 3           # after the head moved
python art/director.py refuse plaza-night 4 --note "it reaches the bases"
python art/director.py verify plaza-night
python art/director.py selftest                           # the vectors and the whole lifecycle, in a scratch copy
rustc -O art/director/conform.rs -o art/build/conform && art/build/conform art/director/vectors.json
```

On Windows, name the program `art\build\conform.exe`. `art/build/` exists once `art/dress.py` has run.

## 6. What it proves, and what it does not

| claim | shown by | does not show |
|---|---|---|
| the rules are written completely enough to be implemented twice | `conform.rs` reproduces all 62 vectors: verdicts field by field and canonical bytes byte for byte; three planted rule defects caught | that either implementation is right: one author wrote both, and the vectors are the contract |
| a candidate's verdict belongs to the head it met | `HEAD-MOVED`; the self-test refuses an admission at a moved head and re-evaluates as a new event | — |
| the ledger is append-only and replays to the files | `verify`; the self-test's plants (a hand edit, a changed line) refused | the last line alone has no successor to name it: it rests on the commit that holds it |
| the layout's authority stays the shell's | a layout candidate is compiled and admitted by the design tool, and C is rebuilt by the graybox converter | — |
| the art is good | nothing here | a person judges rendered views; an approved still records acceptance, not reproducibility |
