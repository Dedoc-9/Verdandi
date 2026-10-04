<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# `workshop/` — the design loop

Contract: an authored edit in, a new authority out, and beside it a consequence record that says exactly what
the edit moved. The authority is split three ways and the record keeps them apart: **W** the level (its
cells, its depth, the depth's table and maps), **M** the material set (the tiles), **C** the camera — carried
through an edit untouched, because a view mutation is not an edit. The consequence is measured, not
estimated: three witnesses before and after — the exact strips, the frame digest, the pixel sha — the columns
whose strip, index or pixels changed, and a **signature** from an exhaustive classification (`identity`,
`outside-view`, `geometry`, `material`, `geometry+material`, `sub-index`, `sub-pixel`). The laws are
one-directional with the camera carried: pixels moved ⟹ strips moved or index moved or M moved. An edit the
world accepts and the screen does not see (`outside-view`) is a consequence, not a fault — 948 permille of
single-cell edits on the witness level are that.

The workshop validates before it projects (an edit that cannot play is refused with a reason and the old
authority stands), creates new authority as files (the world survives the app), and holds no renderer
state: it calls the kernel; it never draws.

## Blueprint

The workshop is where a change becomes authority, so its design is three objects and one rule about order.

```text
    W the level ─┐
    M the tiles ─┼─► content = sha256( sha256(W) ‖ sha256(M) )        C the camera: carried, never edited
                 │
    an edit ─────┴─► validate ─► W′, M′ ─► the kernel, before and after ─► a consequence record
                     (refused typed,                                       strips · frame digest · pixel sha
                      the old authority stands)                            the columns moved · a signature

    a session-walk: one append-only log, every event evaluated against the world the events before it made

    head0 = sha256( "VRDNSW1" ‖ content(base) ‖ "@" ‖ "x,z,F" )
    a move      witness = the frame digest at the new camera          head = sha256( head ‖ ":M:" ‖ witness )
    an edit     witness = content(W′, M′)                             head = sha256( head ‖ ":E:" ‖ witness )
    a look      witness = the frame digest at the new heading         head = sha256( head ‖ ":K:" ‖ token ‖ ":" ‖ witness )
    a sensitivity change, a tick, an admission's envelope             recorded, checked for form, never folded
```

Order is meaning: an edit that opens a cell changes what a later move sees, so moves and edits cannot be two
chains. Batching is not meaning: the head is one left fold, so a checkpoint and a full replay reach the same head.
What is folded is what happened to the world. When it happened, at what sensitivity, and through which proposal
are saved beside the events and never enter the head.

`sessionwalk verify` is this folder's side of the live editor. The shell saves a session; this tool replays it from
the base, re-derives every witness and the head, and renders with the reference kernels only. The fast path the
shell rendered live with is not compiled here, so a saved session is checked by code that shares none of it.

| Invariant | Mechanism | Row |
|---|---|---|
| An edit that cannot play is refused and the old authority stands | validation before projection | `workshop-invalid` |
| The record says everything the edit moved | an after file holding more than the record says is caught | `workshop-authority`, `workshop-stale`, `workshop-projection` |
| A consequence is measured, not estimated | three witnesses before and after, an exhaustive signature | `workshop-cell`, `workshop-tile`, `workshop-census` |
| A read cannot edit | the borrow checker refuses the plant | `membrane-wall` |
| A reformat is not an edit | a content digest beside an authoring digest | `text-reformat`, `text-edit` |
| Undo is replay | the log is the history | `workshop1-undo`, `workshop1-replay` |
| A walk reads the authority and never writes it | W and M unchanged by any move | `input-not-authority`, `sessionwalk-projection` |
| Order is meaning; batching is not | one fold; every split point resumes to the same head | `sessionwalk-interleave`, `sessionwalk-batch-invariance` |
| A changed event is caught at that event | every witness re-derived | `sessionwalk-tamper`, `workshop1-tamper`, `input-tamper` |
| A live session saved by the shell replays here | the workshop's own replay of the saved file | `liveinput-continuity`, `livesession-save`, `admit-replay` |

| File | What it is |
|---|---|
| `edit.rs` | `edit record --level L --tiles T --camera x,z,F --edit SPEC --out-dir DIR --name N` writes `N.before.*`, `N.after.*` and `N.record.json`; `edit check --record R` re-derives every value and refuses typed; `edit census ... --out FILE.json` classifies every single-cell edit of a level under a camera (off-gate). SPEC: `cell:X,Z,C` · `tile:CLASS,R,G,B` · `level:PATH.lvl` · `none` |
| `membrane.rs` | MEMBRANE-0: `Authority` owns the world, `Reading<'a>` borrows it immutably, `edit_cell` needs `&mut` — so editing the authority through a live read-borrow does not compile (rows `membrane-*`; the wall's PASS is rustc's refusal) |
| `text.rs` | TEXT-0: the level as text (`depth` + a `#.<>` grid; `;` comments). `text to-text` / `from-text --palette-from R.lvl` / `digests` — round-trips to the same W, and a content digest (W, unmoved by a reformat) beside an authoring digest (the text bytes) tells a reformat from an edit (rows `text-*`) |
| `session.rs` | WORKSHOP-1: a session is a base authority + a hash-chained cell/tile edit log. `session new / propose / commit / undo / replay / verify` — undo is deterministic replay, propose is a scratchpad (no write), each entry carries content and full digests (a single-writer chain); the head is the session's integrity (rows `workshop1-*`) |
| `input.rs` | INPUT-0: moving around is the projection's job. A **walk** = an initial camera + a typed command log (`L`/`R` turn, `F`/`B` step, `Q`/`E` strafe; blocked by rock = a no-op, still logged), replayed against a FIXED level. `input replay / write / verify` — each step's kernel `URDRFB1` frame digest is chained into a head (`VWLK1`); a tampered command breaks the chain; a walk reads the authority and never writes W or M (rows `input-*`) |
| `attest/session-demo.json` | a committed session (5 edits on the witness base), sealed under RECORD-0; it replays to its head |
| `attest/walk-demo.json` | a committed reference walk (commands `LFFRFFBQE` from `34,28,W`, all six letters), sealed under RECORD-0 as *established* (host-independent); `input verify` replays it to its sealed head |
| `sessionwalk.rs` | SESSION-WALK: move while authoring — ONE interleaved append-only log of edits AND moves (and, with SIM-TICK-0, looks: `sessionwalk look --delta D` turns the heading by D ids; a look's frame is the bearing reference kernel's, and it folds its camera token with its witness; a tick run's stamps are checked for form and never folded; with SIM-TICK-0a a tick session's sensitivity events are replayed as configuration, one legal transition each, and fold nothing). `sessionwalk new / move / edit / look / replay / verify` — each event is evaluated in log order against the authority the preceding events produced, folded into a single head; a move sees a prior edit (order is meaning), the head is checkpoint/replay-equivalent (batching cannot change it), `walk_head`/`edit_head` are derived projections (rows `sessionwalk-*`). ADMIT-0: an admitted edit carries its envelope beside it; `verify` checks each envelope's form and its two heads against the chain, folds none of it, and prints how many edits were admitted |
| `attest/sessionwalk-demo.json` | a committed interleaved session (open a doorway, walk through it, retexture the floor, turn and step — 2 edits + 4 moves from `28,28,N`), sealed under RECORD-0 as *established*; `verify` replays it to its head |
| `attest/census-witness.json` | the truth table populated (a sealed record): 1,379 single-cell edits of the witness level under (34, 28, W) — 1,308 outside-view, 71 geometry, 0 impossible, 0 unexplained columns; the cone split (712 outside, 596 occluded) with `geometry_outside_cone` 0 |

WORKSHOP-0 landed with the planted falsifiers the rung was ratified on: a stale projection under a changed
authority reddens (`STALE-PROJECTION`), a projection that moved without an authority change is detected
(`PROJECTION-WITHOUT-AUTHORITY`), a turned camera is not an edit (`CAMERA-MOVED`), and an after file that
carries more than the record says is caught (`AUTHORITY-MISMATCH`). The three mutation signatures are rows:
another level moves W and the frame; one cell moves W and the frame in exactly the columns whose pixels
moved; one material moves M and the pixels and leaves the frame digest where it was.

## Dev notes

- **Outside the view is a consequence.** 948 permille of single-cell edits on the witness level change nothing on
  the screen. The record says so (`outside-view`) and the check passes: an edit the world accepts and the screen does
  not see is not a fault.
- **An expected-change field was declined.** A record that stored what the author expected to move could not be
  falsified. The record stores what moved.
- **Each tool is one file and one binary.** `edit`, `text`, `session`, `input`, `sessionwalk` and `membrane` each
  include the kernel's files by path and nothing of each other. That is why the JSON reader was copied: one text in
  `sessionwalk.rs` and `session.rs` (and in the shell), and a different one in `edit.rs`. READER-COURT-0, registered
  and not built, replaces all four with one file shared by path.
- **Two spellings of two characters.** This folder's writer spells backspace and form feed `\u0008` and `\u000c`;
  the shell and Python spell them `\b` and `\f`. No file has ever held either character. READER-COURT-0 aligns the
  workshop's writer to the one spelling.
- **The reference renders the replay.** `sessionwalk` replays a look with `kernel/bearing.rs`. It is slower than
  the shell's fast tread and that is the point: the check and the thing checked are different code.

## Ghosts

In full in [`../docs/GHOSTS.md`](../docs/GHOSTS.md). The ones that live in this folder:

- **G17.** The shell replays a session with its own copy of this folder's fold. The two are held together by rows
  and by this folder verifying every saved file, not by sharing one text.
- **G19.** The saved form has four Rust parsers and four Python readers today, and on hostile input they were seen
  to disagree. Nothing in the tree's own files reaches the disagreement.
- **G16.** A session's head is its integrity, not its authorship: a single-writer chain, a hash and no signature.
- The census and the signatures are for the witness level under one camera. Another level, another camera or
  another tile set has its own table, and none has been populated.
