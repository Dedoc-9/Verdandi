# Binary formats, and what an SDK would need

This is a reference for every byte format the repository writes or reads, taken from the writers and readers, not
from the prose beside them. It is also the preparation for an SDK. **There is no SDK today**, and nothing here
promises one. Each statement names the code it was read from. Each layout marked *checked* was confirmed against the
bytes of a committed file or by running the code during the audit of 2026-10-09 (`docs/REPOSITORY-TRUTH.md`).
Where something could not be established, it says so.

## 0. What exists, and what does not

- **No library.** There is no `Cargo.toml` and no `lib.rs`. Each Rust program is one `rustc -O <file>.rs`, and shared
  code is pasted in by `#[path]` (`kernel/main.rs`, `shell/main.rs:21-119`, `workshop/*.rs`). A `pub` item is visible
  only inside the binary it is compiled into. The README's "the crate names" (`README.md:4`) names no crate that
  exists.
- **No Python package.** There is no `__init__.py`. Modules are found by editing `sys.path`:
  - `design/design.py:57` imports `verify/savedform`;
  - `graybox/check.py` and `graybox/serve.py` import `graybox/level.py`.
- **The nearest reusable pieces** carry no stability promise:
  - `kernel/formats.rs` and `kernel/mantle.rs`: the level, the tiles, the scene, SHA-256 and the frame digest;
  - `kernel/savedform.rs` and `verify/savedform.py`: the two readers of the saved form;
  - `verify/envelope.py`: the record envelope;
  - `graybox/level.py: convert(name)`.
- **The user interfaces are command lines**, listed in §8. A "plugin SDK" and a "compatibility inspector" are declared
  in `docs/ROADMAP.md` and are not built.

## 1. Words that are kept apart

| word | what it means here | example |
|---|---|---|
| syntactic validity | the bytes are a sentence of the language | VRDNP1 has exactly eight lines in the one form `recognize` accepts |
| structural validity | the sentence fits its context | a cell inside the level; a parent head that is the session's head |
| semantic validity | it means what was intended | a design's literal target (HERMENEUTICS-0): no parser checks this; the owner's targets do |
| canonical encoding | one value has exactly one byte form | VRDNP1/VRDNP2; the envelope's canonical JSON. The saved form is **not** canonical bytes; only its strings have one spelling |
| provenance | where the bytes came from and by what | a record's `provenance`; a graybox cell's `src`; the manifest's `converter_sha256` |
| integrity | the bytes are the bytes that were hashed | a matching sha256, a seal, a `chain_hash` |
| authenticity | who made them | **nowhere**: every hash here can be recomputed by anyone. A seal is not a signature (GHOSTS G16) |
| compatibility | an old file still reads, and reads the same | **no policy exists** (§9) |

A matching digest establishes integrity of the bytes it covers. It does not establish that they are correct, that
they mean what was intended, or who wrote them. `integrity ≠ truth`.

## 2. Conventions shared by the formats

| convention | value | source |
|---|---|---|
| digest | SHA-256, hand-written, lower-case hex | `kernel/mantle.rs:89-151` |
| axes | x across (east +x), z down (south +z); cells row-major at `z*w + x` | `kernel/formats.rs`, `kernel/mantle.rs` |
| facing | 0 N (−z), 1 E (+x), 2 S (+z), 3 W (−x); letters `N E S W` | `kernel/formats.rs:121-145` |
| fixed point | a cell is Q = 256 units; the frame is 1920 × 1080; FOCAL 960; 32 depth bands; 256-texel tiles | `kernel/mantle.rs:36-53` |
| byte order | little-endian, except the frame digest's width and height, which are big-endian | `kernel/formats.rs`; `kernel/mantle.rs:509-517` |
| line endings | LF; `.gitattributes` sets `* text=auto eol=lf` | `.gitattributes` |
| refusals | `TOOL-CODE: detail` with exit 2. The kernel's are untyped: `KERNEL-REFUSE: <message>`. `edit` prints its refusal on stdout | each tool's `main` |

## 3. The catalogue

| format | identifier | written by | read by | identity | rows |
|---|---|---|---|---|---|
| level | `VRDNLVL1` | Urðr (oracle files); `text from-text`; `edit record`; `session replay --out-level`; `shell checkpoint` | `kernel/formats.rs:parse_level`; Python readers of the header and cells in `design/`, `graybox/`, `verify/` | W = sha256(file) | `oracle-frozen`, `text-*` |
| tiles | `VRDNTIL1` | Urðr | `kernel/formats.rs:parse_tiles` | M = sha256(file) | `oracle-frozen` |
| scene | `URDRMNTI` | `kernel/formats.rs:compose`; `kernel --write-scene` | `kernel/mantle.rs:parse_scene` | — | `kernel-*` |
| bearing scene | `URDRBRGI` | `kernel/vocab.rs:compose` | `kernel/bearing.rs:parse_scene` | — | `bearing-*` |
| frame digest | `URDRFB1` | `kernel/mantle.rs:frame_digest` | compared as text | the digest | `kernel-oracle`, `bearing-oracle` |
| level text | `VWTX1` (comment only) | `text to-text` | `text from-text` | content W and an authoring digest | `text-*` |
| walk | `VWLK1` | `input write` | `input replay/verify` | chain head | `input-*` |
| saved form | (a language) | every writer, checked first | `kernel/savedform.rs`, `verify/savedform.py` | — | `readercourt-*` |
| record envelope | `name`/`version` fields | `verify/envelope.py`; Rust twin in `workshop/edit.rs` | `envelope.read` | `chain_hash` | `records-*` |
| workshop session | `VRDNSES1` | `session new/commit/undo` | `session replay/verify` | chain over raw digests | `workshop1-*` |
| session-walk | `VRDNSW1` | `sessionwalk`; the shell's seal | `sessionwalk verify`; the shell's loader | head over hex text | `sessionwalk-*`, `livesession-*` |
| live journal | `VRDNLJ1` | the shell's live loop | the shell's loader | a sha256 per record | `livesession-*` |
| proposal | `VRDNP1` | a proposer | `shell/admit.rs:recognize` | sha256 of the exact bytes | `admit-*` |
| batch | `VRDNP2` | `shell design-compile` | `shell/designevent.rs:recognize_batch` | sha256 of the exact bytes | `designevent-*` |
| design text | `VERDANDI-DESIGN 0` | a person, script or model | `shell/designcompile.rs` | sha256 of the exact bytes | `designir-*`, `hermeneutics-*` |
| registration ledger | `verdandi-preregistration` | by hand, by the owner's ruling | `verify.py:records_preregistered` | a `chain_hash` per entry | `records-preregistered`, `*-preregistered` |
| refusal log, run ledger | one JSON line each | `shell/refusallog.rs`, `shell/runledger.rs` | `verify/refusallog.py`, `verify/runledger.py` | — (not sealed) | `refusallog-*`, `runledger-*` |
| design project | `project.json` and files | `design/design.py` | `design/design.py` | — | none |
| graybox map | `GRAYBOX 0` | a person | `graybox/level.py` | sha256 recorded in the manifest | none (`graybox/check.py`) |
| graybox worlds | `VERDANDI-GRAYBOX-WORLD 0`, `-COLLISION 0`, `-MANIFEST 0` | `graybox/level.py` | `graybox/check.py`; the page | sha256 of canonical JSON | none |

## 4. The world: level, tiles, scenes, digests

**Level (`VRDNLVL1`)**, `kernel/formats.rs:58-93`, little-endian. *Checked* against all five oracle levels (18,708
bytes each at 48 × 32):

| offset | field | bytes |
|---|---|---|
| 0 | magic `VRDNLVL1` | 8 |
| 8 | u32 w | 4 |
| 12 | u32 rows | 4 |
| 16 | cells, one byte each from `# . < >`, row-major | w · rows |
| 16 + w·rows | u32 depth | 4 |
| +4 | colour table, 256 RGB entries | 768 |
| +768 | wall map, 32 bands × 256 | 8,192 |
| +8,192 | floor map, 32 bands × 256 | 8,192 |

- **Refusals:** `input truncated`, `level magic is not VRDNLVL1`, `level extent outside the lattice` (w or rows 0 or
  above 48), `cell byte N is not in the alphabet #.<>`, `level has trailing bytes`.
- **Not checked by the parser:** a rock border, and the table and maps. The editors refuse an open border. A level
  that parses can still stop the kernel at render time with `the ray at column c left the world`.
- `depth` is read but not used by the renderers. How Urðr generated the table and maps is not established here.

**Tiles (`VRDNTIL1`)**, `kernel/formats.rs:95-119`. *Checked*: 983,048 bytes, which is the magic and then five tiles of
256 × 256 × 3 RGB, four walls then the floor. The wall tiles are indexed by light family (`kernel/mantle.rs:58-66`).
The edit classes `wall0..wall3` and `floor` name these five.

**Camera token `x,z,F`**, `kernel/formats.rs:121-137`. It is **not canonical**: each part is trimmed and parsed as an
i64, and `compose` narrows x and z with `as i32`. During the audit `+34, 28 ,3` was read as `34,28,W`. Treat the
printed token, not the input, as the camera's identity.

**Scene (`URDRMNTI`)**, `kernel/formats.rs:150-168`. Layout: magic, u32 w, u32 rows, cells, i32 x, i32 z, u8 facing,
u32 depth, the table and both maps, then the five tiles. It is 1,001,757 bytes at 48 × 32. The scene parser treats any
cell byte other than `#` as floor. It refuses a facing outside 0..3, trailing bytes and an eye on a non-traversable
cell.

**Bearing scene (`URDRBRGI`)**, `kernel/vocab.rs:172-192` and `kernel/bearing.rs:97-146`. As the scene, but the facing
byte is replaced by i64 A, B, C: a Pythagorean direction with C ≥ 1 (1,001,780 bytes at 48 × 32). The heading
vocabulary `bearing_octant.txt` is compiled in and checked against its sha256 before use (`kernel/vocab.rs:28-86`). A
heading id K is canonical decimal in [0, 360000).

**Frame digest (`URDRFB1`)**, `kernel/mantle.rs:509-517`. sha256 of `"URDRFB1"`, u32 **big-endian** 1920, u32
big-endian 1080, the byte 0x01, then the 1920 × 1080 index frame. It covers geometry at index grain, not appearance.
Two neighbouring headings can share a frame, which is why a look folds its camera token as well. The picture digest
is the sha256 of the 1920 × 1080 × 3 RGB viewport.

## 5. Text the workshop reads

- **Level text (`.wtxt`)**, `workshop/text.rs:54-131`:
  - Comments are lines starting with `;`. `#` is rock, not a comment, whatever `text.rs:69` says.
  - Directives are `depth N` and `grid`, then one row per line from `# . < >`. A trailing CR is dropped.
  - The `VWTX1` mark is written but not checked on read. `from-text` does not enforce the 48-cell lattice, so it can
    write a level the kernel refuses.
- **Walk (`.walk`, VWLK1)**, `workshop/input.rs:126-211`:
  - Directives: `level`, `tiles`, `camera X Z F`, `commands`, `head`. Only the first word after `commands` is kept, so
    spaced commands are silently cut short.
  - The chain mixes raw and hex. `acc0 = sha256("VWLK1" ‖ hex(frame0))`, then each step is `sha256(acc_raw ‖ hex(frame))`.
- **Edit specs**, `workshop/edit.rs:254-291`: `cell:X,Z,C`, `tile:CLASS,R,G,B`, `level:PATH`, `none`. The session tools
  accept the first two only.

## 6. Documents: the saved form, records, sessions

**The saved form** is a JSON subset with one reader in each language (`kernel/savedform.rs:10-36`,
`verify/savedform.py`):

- **Document and payload.** A document is one object followed by exactly one LF. A payload is one object and nothing
  else.
- **Whitespace.** Spaces and LFs only, between tokens.
- **Names.** No name twice in one object.
- **Depth.** At most seven levels deep, the root counted.
- **Integers only.** Signed 64-bit, with no leading zero, no `-0`, no fraction and no exponent.
- **Strings.** Well-formed UTF-8. Raw characters are allowed from U+0020 except `"` and `\`. The escapes are
  `\" \\ \b \f \n \r \t`, and `\u00xx` (lower-case) only for the other control characters.
- **What is not required:** sorted keys or any particular whitespace. The language is not canonical bytes.
- **Codes:** `READER-TRUNCATED | TRAILING | DEPTH | DUPLICATE | STRING | NUMBER | STRUCTURE`, each with a byte offset.
- **Who uses it:** every writer in the shell and the workshop checks its bytes with the reader before writing them
  (`readercourt-writers`).
- **Not everything is saved form.** `design/`'s `project.json`, the refusal log, the run ledger, the graybox JSON and
  the oracle's JSON records are read with Python's `json` module, outside the saved form.

**The record envelope (RECORD-0)**, `verify/envelope.py:1-60`:

- **Members:** `{name, version, claim_class, provenance, validity_scope, forbidden_interpretations, data, reading,
  chain_hash}`.
- **`claim_class`:** one of `measured | established | declared | predicted`.
- **`chain_hash`:** the sha256 of the canonical JSON of the seven required members. Canonical means sorted keys by code
  point, no whitespace, integers only, and the saved form's string spelling. The Rust twin is
  `workshop/edit.rs:87-190`.
- **Outside the hash:** `reading` and any extra member.
- **The firewall:** a verdict-shaped key (`verdict`, `ok`, `passed`, …) anywhere in `data` is refused.
- **What a matching `chain_hash` does not show:** authorship, a link to any other record, or the truth of `data`.

**The workshop session (`VRDNSES1`)**, `workshop/session.rs:126-147`. The chain is over raw 32-byte digests:

- `content = sha256(W ‖ M)`;
- `genesis = sha256("VRDNSES1" ‖ content)`;
- `full = sha256(parent_full ‖ content)`.

**The session-walk (`VRDNSW1`)**, `workshop/sessionwalk.rs:17-60, 421-439`. The chain is over **hex text**:

- `head0 = sha256("VRDNSW1" ‖ content_hex ‖ "@" ‖ "x,z,F")`;
- then `head = sha256(head_hex ‖ ":" ‖ tag ‖ ":" ‖ witness)`, with the tag `M` for a move (the witness is the frame
  digest), `E` for an edit (the content) and `K` for a look (`token:frame`);
- a sensitivity change folds nothing.

The fold is copied in `shell/playback.rs` and twinned in Python in `verify/verify.py` and `verify/livesession.py`
(GHOSTS G17). `sessionwalk verify` re-derives every witness and the head. It does not compare the stored base W, M
or content, `final_content`, the counts or empty camera tokens: the head is what binds the base. Example 2 in §10
recomputes a head from the stored witnesses, which shows the chain is consistent and not that the frames are right.

**The live journal (`journal.vsj`, `VRDNLJ1`)**, `shell/livesession.rs:9-12, 382-441`:

- **Where:** under `$VERDANDI_SESSIONS` (default `build/sessions`), in `<run_id>/`.
- **Records:** one per line, `R <byte length> <sha256 of payload> <payload>`, where the payload is compact saved form.
  The header record comes first, then one record per event, each flushed before it counts.
- **Damage:** a torn last line is dropped; any other bad line refuses.

**The sealed session (`session.json`)**, `shell/livesession.rs:13-19, 440-460`:

- **Format:** the session-walk format with a `live` block and a `seal`.
- **The seal:** the sha256 of every byte up to and including the line feed before `"seal": "`. The file must end
  `<seal>"\n}\n`.
- **How it is written:** to a temporary file, flushed, and moved over the old one. On Windows that is `MoveFileExW`;
  elsewhere a rename and a directory flush.
- **Then:** it is read back and replayed before the run reports success.
- **Its bytes are not reproducible run to run:** the `run_id` is wall-clock milliseconds and the process id. The head
  is reproducible.

## 7. Proposals and designs

**VRDNP1**, `shell/admit.rs:12-52`. Exactly eight lines, each ended by one LF:

```
VRDNP1
renderer=<64 hex>
bearing=<64 hex>
parent=<64 hex>
proposal=<64 hex>
op=open | op=close | op=paint
target=<x>,<z> | target=<wall0|wall1|wall2|wall3|floor>
value=0 | value=<colour>
```

- **Numbers.** A coordinate is canonical decimal in 0..65535. A colour is canonical decimal in 0..16777215, read as
  R·65536 + G·256 + B.
- **One byte form.** Each typed proposal has exactly one: `emit` writes it and `recognize` accepts nothing else.
- **Size.** 327 to 337 bytes. Only the maximum is tested directly; the minimum follows from the grammar.
- **Refusals,** in order: `ADMIT-IO, -SIZE, -PARSE, -RANGE, -PROGRAM`, the loader's codes, `-SESSION, -ANCHOR,
  -DUPLICATE, -CAPABILITY, -AUTHORITY`.

**VRDNP2**, `shell/designevent.rs:12-50`:

- **Lines.** The same first five lines, with `VRDNP2`, then `operations=N` (N in 1..4096), then N lines of
  `open x,z`, `close x,z` or `paint <class> <colour>`.
- **The net change set.** The cell operations come first, in strictly ascending (z, x) order, then the paints in tile
  class order. Anything else is refused with `ADMIT-ORDER`.
- **Size.** 322 to 74,059 bytes.
- **Dry run and binding.** `--dry-run` runs every check and writes nothing. `--previewed DIGEST,HEAD` binds an
  admission to its preview (`ADMIT-PREVIEW`).

**VERDANDI-DESIGN 0**, `shell/designcompile.rs:12-60`:

- **Limits.** At most 16,384 bytes. Lines split on LF, with a CR dropped before an LF.
- **Line 1.** After trimming spaces and tabs it must equal the version. It takes no comment.
- **Later lines.** From line 2, `#` starts a comment. The statements are:
  - `open CELL [CELL]` and `close CELL [CELL]`;
  - `room CELL CELL`, at least 3 × 3;
  - `entrance CELL`;
  - `paint CLASS R,G,B`.
- **Numbers.** A cell coordinate is canonical decimal of at most five digits; a colour channel is 0..255.
- **Statements.** 1 to 64, applied in order to a copy of the parent's world, a later one writing over an earlier.
- **Output.** One canonical VRDNP2 batch on stdout. Its id is the sha256 of the design's bytes.
- **Refusals, in order:** `COMPILE-IO, -SIZE`, the loader's codes, `-SESSION, -PARSE, -RANGE, -SIZE` (a 65th
  statement), `-BORDER, -STAIR, -CAMERA, -SIZE` (over 4,096 operations), `-EMPTY`.

## 8. The command-line interfaces

| program | user commands, as parsed | internal and test-only |
|---|---|---|
| `kernel` | `<scene.bin>`; `--level L --tiles T --camera x,z,F`; `--at x,z,K`; `--hud`; `--write-png P` (writes **PPM**); `--write-scene P`; `--bench N --warm M` | `--fast*`, `--emit-*`, `--locality*`, `--gauntlet2*`, `--bearing-*`, `--breakdown`, `--render` |
| `shell` | `witness`, `selfcheck`, `playback`, `checkpoint`, `resume`, `admit`, `admit-anchor`, `design`, `design-compile`; the window commands need `--cfg shell_window` on Windows and refuse elsewhere with `SHELL-NO-WINDOW` | the `*-selftest` mock courts, `loop-equiv`, `form-*`, `simtick-law` |
| `workshop` | `edit record\|check\|census`; `text to-text\|from-text\|digests`; `session new\|propose\|commit\|undo\|replay\|verify`; `input replay\|write\|verify`; `sessionwalk new\|move\|edit\|look\|replay\|verify`; `membrane witness\|legal` | the plants the gate builds |
| `design/design.py` | `new`, `open`, `grant`, `inspect`, `propose`, `preview`, `admit`, `reject`, `undo`, `status` (`--project`, else `$VERDANDI_DESIGN`, else `design/work/`) | — |
| `graybox` | `serve.py [MAP] [--port N] [--no-browser] [--renderer flat] [--selftest \| --bench [--samples N] [--batch K]] [--timeout S]`; `check.py [MAP…] [--compile]` | — |
| `verify` | `verify.py [-v]`; `savedform.py FILE [--payload]`; `refusallog.py`; `runledger.py` | the sealers, on a named host |

Name the map before any option to `serve.py`. Its parser takes the first word that is not an option's value, so
`serve.py --port 8000 witness` plays the tactical map.

## 9. Compatibility and versioning

No compatibility policy was found for any of the studio's formats. What the code does instead:

- **A new name rather than an edit.** VRDNP2 stands beside VRDNP1, which is unchanged. A new oracle is a new tag.
- **Hard version checks:** `edit check` refuses an edit record whose version is not 3; the design text must say
  `VERDANDI-DESIGN 0`.
- **Optional members are additive.** A session-walk with no looks or ticks is written as it always was
  (`workshop/sessionwalk.rs:612-622`).
- **Identity is advisory.** A session saved by another renderer loads as a different renderer, and the replay decides
  (`shell/livesession.rs:20-24`).
- **Not checked on load:** the `version` member of a session or a session-walk. There is no magic and no version in
  `project.json`, the refusal log, the run ledger or a checkpoint.

## 10. Examples

Each was run from the repository root on 2026-10-09 with Python 3.11 and printed what is shown. Each needs only the
standard library.

```python
# Example 1 — a level's header and its identity W
import hashlib, struct
data = open("oracle/levels/witness.lvl", "rb").read()
assert data[:8] == b"VRDNLVL1"
w, rows = struct.unpack_from("<II", data, 8)
cells = data[16:16 + w * rows]
print(w, rows, cells.count(b"."), "floor cells;", "W =", hashlib.sha256(data).hexdigest())
# 48 32 330 floor cells; W = 1b84db41a5fb3a397be81842db5df587111ac11c3ce91f8c5b560ef80c40bbec
```

```python
# Example 2 — a session-walk head, recomputed from the witnesses the file stores
import hashlib, json
d = json.load(open("workshop/attest/sessionwalk-demo.json", encoding="utf-8"))["data"]
h = lambda b: hashlib.sha256(b).hexdigest()
head = h(b"VRDNSW1" + d["base"]["content"].encode() + b"@" + d["base"]["camera"].encode())
for ev in d["log"]:
    head = h((head + ":" + {"move": "M", "edit": "E"}[ev["kind"]] + ":" + ev["witness"]).encode())
print(head == d["head"])   # True: the chain is consistent; whether each frame is right needs the kernel
```

```python
# Example 3 — every registration's chain hash, recomputed
import sys; sys.path.insert(0, "verify")
import json, envelope
entries = json.load(open("verify/preregister.json", encoding="utf-8"))["entries"]
bad = [r for r, e in entries.items() if e["chain_hash"] != envelope.chain_hash({
    "name": "verdandi-preregistration-entry", "version": 1, "claim_class": "declared",
    "provenance": {"registered_in": "verify/preregister.json"},
    "validity_scope": {"certifies": "the conditions %s was seated under" % r},
    "forbidden_interpretations": ["that registering a condition earns it"],
    "data": {k: v for k, v in e.items() if k != "chain_hash"}})]
print(len(entries), "entries;", len(bad), "differ")   # 55 entries; 0 differ
```

Example 3 shows what `records-preregistered` checks, and why that check is weaker than its refusal text. The hash
is not keyed, so an entry edited together with a hash recomputed this way also passes. What holds an older entry
against that is a full hash constant in the gate, a committed record that cites the hash, or the Git history
(`docs/REPOSITORY-TRUTH.md`, finding T-12).

## 11. Edge cases no other document states

- The camera token's leniency and its `as i32` narrowing (§4).
- `URDRMNTI` reads any non-`#` cell byte as floor; `from-text` can exceed the 48-cell lattice.
- `graybox/level.py` parses cells with Python `int()`, so it accepts `+3`, `003` and non-ASCII digits. It reads a
  spawn's yaw as `float(...) % 360`, so `inf` becomes `NaN`, which the canonical JSON then writes as `NaN` and a
  browser cannot parse.
- `shell playback` applies edit specs without the bounds and border checks the other readers make. This was found by
  reading `shell/playback.rs:141-187` and was not run.
- `MIN_BYTES` (`shell/admit.rs:51`) and `MIN_BATCH_BYTES` (`shell/designevent.rs:48`) are declared and never tested;
  the grammar holds them.

## 12. What an SDK would need decided first

These are decisions for the owner, not recommendations made here:

1. **Which formats are public.** Candidates: the design text, VRDNP2, the session-walk and the record envelope.
2. **A compatibility rule** for each public format: what a version means, what a reader does with an unknown one, and
   whether old files must replay to the same head forever.
3. **Whether a library exists at all.** That means a crate or a package with a stable surface, against the charter's
   std-only rule and the single-file builds the pins hold. Today every Rust source is pinned by hash, so any new file
   is an amendment.
4. **Canonical forms.** The saved form has none; the envelope's canonical JSON sorts by code point, which differs from
   RFC 8785 for characters outside the Basic Multilingual Plane (`docs/RESEARCH-FINDINGS.md`, R-4).
5. **Authenticity.** No format carries a signature. Whether one should is a separate decision (GHOSTS G16, G20).
