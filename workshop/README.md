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
| `attest/census-witness.json` | the truth table populated (a sealed record): 1,379 single-cell edits of the witness level under (34, 28, W) — 1,308 outside-view, 71 geometry, 0 impossible, 0 unexplained columns; the cone split (712 outside, 596 occluded) with `geometry_outside_cone` 0 |

WORKSHOP-0 landed with the planted falsifiers the rung was ratified on: a stale projection under a changed
authority reddens (`STALE-PROJECTION`), a projection that moved without an authority change is detected
(`PROJECTION-WITHOUT-AUTHORITY`), a turned camera is not an edit (`CAMERA-MOVED`), and an after file that
carries more than the record says is caught (`AUTHORITY-MISMATCH`). The three mutation signatures are rows:
another level moves W and the frame; one cell moves W and the frame in exactly the columns whose pixels
moved; one material moves M and the pixels and leaves the frame digest where it was.
