<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# `kernel/` — the deterministic per-frame work

Contract: a scene in (the level, the eye, the facing, the colour table, the per-band maps, the tiles — all
INPUT), an 8-bit index frame and a 1920×1080 RGB picture out, and two witnesses: the URDRFB1 frame digest
(geometry) and the picture's sha256 (appearance). std-only Rust; no shell dependency, no UI toolkit, no
presentation API; nothing here opens a window or reads a clock inside the gate. The kernel mints no authority:
it cannot change a cell, a tile or the camera, and the workshop cannot be reached from here.

| File | What it is |
|---|---|
| `mantle.rs` | the kernel proper: Urðr's placement made a library (`parse_scene`, `picture`, `Scene::{strips,frame,emit}`, `frame_digest`, `sha256`); the arithmetic is the tag's, byte for byte — the **frozen correctness oracle**, never modified for performance |
| `fast.rs` | GAUNTLET-1: a SIBLING of `emit` (never `mantle.rs`), the optimization staircase — each tread byte-identical to the frozen emit. `emit` = GAUNTLET-1c's **row-major floor DDA** (ceiling + wall an exact transcription; the floor's perspective divide done per-ROW by a Bresenham-exact recurrence, O(rows) not O(pixels)). `emit_collapse` = GAUNTLET-1b's **divide-collapse** (2 `div_euclid`/floor px), kept verbatim as the same-apparatus speed BASELINE. `structure` = RE-BREAKDOWN-1 Court A (deterministic divide/read/working-set/locality/write-once measures). `mod probe` = RE-BREAKDOWN-1 Court B, a FENCED ablation apparatus (`emit_probe<MODE>` ADDR/LOOKUP/FULL/VERIFY, `black_box`-anchored; VERIFY == emit) — measurement scaffold, never a renderer, never in the promotion chain. Rows `gauntlet1-equiv` / `gauntlet1b-reduction` / `gauntlet1c-dda` / `rebreakdown1-*` |
| `formats.rs` | the studio's input formats — W the level (`VRDNLVL1`), M the tiles (`VRDNTIL1`), C the camera — and `compose()` into the kernel's `URDRMNTI` scene |
| `hud.rs` | HUD-0: the overlay drawn into the picture — reticle, strip-band bar, facing plate, minimap; a declared region; the overlay's own identity; the region audit |
| `main.rs` | the command line: a scene or `--level/--tiles/--camera`, the two witnesses, `--hud` for the overlay's three lines, `--write-png` (a PPM), and off-gate `--bench` (2-phase) / `--breakdown` (GAUNTLET-0: strips/frame/emit + the two witness hashes) / `--fast` (GAUNTLET-1: DDA + collapse vs frozen emit, region divide-work) / `--fast-bench` (GAUNTLET-1c: frozen / collapse / DDA emit timed on one apparatus, all three must reproduce the witness) / `--emit-structure` (RE-BREAKDOWN-1 Court A, deterministic) / `--emit-breakdown` (RE-BREAKDOWN-1 Court B: the addr/lookup/full/emit ablation ladder, probe VERIFY == emit). It only times pub calls — it never modifies the frozen renderer |
| `attest/bench-<host>.json` | the kernel's wall-clock on a named host, sealed under RECORD-0's envelope (written by `../verify/bench.py`; budgets as data, the comparison in the reading) |
| `attest/breakdown-<host>.json` | GAUNTLET-0: the render decomposed per pub-phase (strips/frame/emit) with the two witness hashes separated, sealed under RECORD-0 (written by `../verify/gauntlet.py`, cites the GAUNTLET-0 preregistration; the 500-permille decision rule is the reader's) |
| `attest/gauntlet1b-<host>.json` | GAUNTLET-1b: the same-apparatus emit-level speed delta (frozen emit vs the collapse) on a named host, sealed under RECORD-0 (written by `../verify/gauntlet1b.py`, cites the GAUNTLET-1 preregistration; witnesses checked first, the promotion comparison in the reading, never cross-compared to GAUNTLET-0's absolute) |
| `attest/gauntlet1c-<host>.json` | GAUNTLET-1c: the same-apparatus emit-level speed delta (the DDA vs the GAUNTLET-1b collapse baseline, frozen for context) on a named host, sealed under RECORD-0 (written by `../verify/gauntlet1c.py`, cites the GAUNTLET-1 preregistration; all three emits reproduce the witness first, the promotion comparison — vs the collapse, not frozen — in the reading) |
| `attest/emit-breakdown-<host>.json` | RE-BREAKDOWN-1: emit's deterministic structure (Court A) and the same-apparatus ablation attribution of its work classes (Court B) on a named host, sealed under RECORD-0 (written by `../verify/rebreakdown1.py`, cites the RE-BREAKDOWN-1 preregistration; probe VERIFY == emit checked first; the increments read as incremental attribution under controlled ablation, never a resource cost, never vs GAUNTLET-0's absolute) |

Placed at KERNEL-0 from Urðr's `tools/terrain/mantle_rs/mantle.rs` at `urdr-oracle-1`, verified against
`../oracle/` by `../verify/verify.py` on every run (rows `kernel-oracle`, `kernel-corpus`, `kernel-selftest`).
HUD-0 added the overlay under its own pins (`../verify/pins/hud-1.json`; rows `hud-*`): the certified picture
underneath is untouched, the index frame is never written, and the overlay reads the strips, the cells and the
camera — never a material, never the shell.
