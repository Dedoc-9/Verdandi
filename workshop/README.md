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

| File | What it is |
|---|---|
| `edit.rs` | `edit record --level L --tiles T --camera x,z,F --edit SPEC --out-dir DIR --name N` writes `N.before.*`, `N.after.*` and `N.record.json`; `edit check --record R` re-derives every value and refuses typed; `edit census ... --out FILE.json` classifies every single-cell edit of a level under a camera (off-gate). SPEC: `cell:X,Z,C` · `tile:CLASS,R,G,B` · `level:PATH.lvl` · `none` |
| `membrane.rs` | MEMBRANE-0: `Authority` owns the world, `Reading<'a>` borrows it immutably, `edit_cell` needs `&mut` — so editing the authority through a live read-borrow does not compile (rows `membrane-*`; the wall's PASS is rustc's refusal) |
| `text.rs` | TEXT-0: the level as text (`depth` + a `#.<>` grid; `;` comments). `text to-text` / `from-text --palette-from R.lvl` / `digests` — round-trips to the same W, and a content digest (W, unmoved by a reformat) beside an authoring digest (the text bytes) tells a reformat from an edit (rows `text-*`) |
| `session.rs` | WORKSHOP-1: a session is a base authority + a hash-chained cell/tile edit log. `session new / propose / commit / undo / replay / verify` — undo is deterministic replay, propose is a scratchpad (no write), each entry carries content and full digests (a single-writer chain); the head is the session's integrity (rows `workshop1-*`) |
| `input.rs` | INPUT-0: moving around is the projection's job. A **walk** = an initial camera + a typed command log (`L`/`R` turn, `F`/`B` step, `Q`/`E` strafe; blocked by rock = a no-op, still logged), replayed against a FIXED level. `input replay / write / verify` — each step's kernel `URDRFB1` frame digest is chained into a head (`VWLK1`); a tampered command breaks the chain; a walk reads the authority and never writes W or M (rows `input-*`) |
| `attest/session-demo.json` | a committed session (5 edits on the witness base), sealed under RECORD-0; it replays to its head |
| `attest/walk-demo.json` | a committed reference walk (commands `LFFRFFBQE` from `34,28,W`, all six letters), sealed under RECORD-0 as *established* (host-independent); `input verify` replays it to its sealed head |
| `sessionwalk.rs` | SESSION-WALK: move while authoring — ONE interleaved append-only log of edits AND moves. `sessionwalk new / move / edit / replay / verify` — each event is evaluated in log order against the authority the preceding events produced, folded into a single head; a move sees a prior edit (order is meaning), the head is checkpoint/replay-equivalent (batching cannot change it), `walk_head`/`edit_head` are derived projections (rows `sessionwalk-*`) |
| `attest/sessionwalk-demo.json` | a committed interleaved session (open a doorway, walk through it, retexture the floor, turn and step — 2 edits + 4 moves from `28,28,N`), sealed under RECORD-0 as *established*; `verify` replays it to its head |
| `attest/census-witness.json` | the truth table populated (a sealed record): 1,379 single-cell edits of the witness level under (34, 28, W) — 1,308 outside-view, 71 geometry, 0 impossible, 0 unexplained columns; the cone split (712 outside, 596 occluded) with `geometry_outside_cone` 0 |

WORKSHOP-0 landed with the planted falsifiers the rung was ratified on: a stale projection under a changed
authority reddens (`STALE-PROJECTION`), a projection that moved without an authority change is detected
(`PROJECTION-WITHOUT-AUTHORITY`), a turned camera is not an edit (`CAMERA-MOVED`), and an after file that
carries more than the record says is caught (`AUTHORITY-MISMATCH`). The three mutation signatures are rows:
another level moves W and the frame; one cell moves W and the frame in exactly the columns whose pixels
moved; one material moves M and the pixels and leaves the frame digest where it was.
