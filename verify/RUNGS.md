<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# The rungs — Verðandi's ledger

One entry per rung, in the order they landed. Each states what was measured, what it does not show, and the
row that reddens if the claim is false. Grades: MEASURED (a row computes it live), ESTABLISHED (read off the
code or the frozen record), DECLARED (stated, not yet earned).

## KERNEL-0 — the placement reproduces the oracle natively, against the tag

**What landed.** `kernel/mantle.rs` — Urðr's `tools/terrain/mantle_rs/mantle.rs` at `urdr-oracle-1`
(source sha256 `9e8a8f7d…`), made a library: the same constants, SHA-256, traversal in reduced rationals,
strip and floor fills, texture coordinates and per-band emission, with `pub` visibility, the scene parser
returning a typed `Refusal`, and the command line moved to `kernel/main.rs`. `kernel/formats.rs` — the
studio's three input formats: **W** the level (`VRDNLVL1`: cells, depth, the depth's table and band maps),
**M** the tiles (`VRDNTIL1`), **C** the camera (carried, inside neither), and their composition into the
`URDRMNTI` bytes the oracle fixes as the kernel's input. `oracle/levels/*.lvl` (witness `0xABCDE/1`,
corridor `0/1`, room `12345/7`, landmark `0xC0FFEE/2`, neighbour `0xABCDF/1`), `oracle/tiles/{identity,
oriented}.tiles` and `oracle/witnesses.json` — frozen live from Urðr at `4c8c2451` (CPython 3.11.15, Linux,
`PYTHONHASHSEED=0`), every level beside Urðr's own `level_digest`, every tile set beside Urðr's `tiles_digest`.

**Rows.** `oracle-frozen` — every W and M equals its file's sha256; the witness scene's frame, identity pixels
and oriented pixels equal `urdr-oracle-1.json`; corridor and pointblank share a level. `kernel-build` — the
kernel compiles live. `kernel-oracle` — the placement prints the oracle's frame digest `9bb45bf3…` and
identity pixel sha `0bef7c1e…` at (34, 28) facing W, twice. `kernel-corpus` — 12 witnesses over 6 scenes ×
2 tile sets equal the frozen values, and within each scene both tile sets share one frame digest.
`kernel-selftest` — a mirrored sign table moves 6 of 6 oriented pictures and no frame digest and no identity
picture: the rows can redden, and geometry and appearance are distinct witnesses.

**Grade.** MEASURED: both witnesses on every corpus scene, the selftest control, the corpus's self-consistency.
ESTABLISHED: the port changed visibility and shape and no arithmetic (read off the diff against the tag's
source). DECLARED: nothing.

**does_not_show.** `D_0` — Urðr's composed CORE identity (level, entity, RNG stream, action log) is carried
in the oracle as evidence and is neither recomputed nor minted here. Any frame budget (off-gate:
`kernel --bench N --warm M` on a named host; the owner's Urðr record stands at p99 12,319 µs within 60 Hz).
That the corpus is representative — six scenes, two tile sets. A window, a present, an input.

**Falsifier.** `kernel-oracle` and `kernel-corpus` redden on any drift in the arithmetic; `kernel-selftest`
reddens if the comparison ever stops biting.

## WORKSHOP-0 — an edit is a new authority, and the witnesses say what it moved

**What landed.** `workshop/edit.rs` (std-only; built over the kernel's own `mantle.rs` and `formats.rs` by
`#[path]` — one traversal, one emission, no mirror). `edit record` takes an authority (W a level file, M a
tiles file, C a camera) and one edit — `cell:X,Z,C`, `tile:CLASS,R,G,B`, `level:PATH` (the seed edit: another
frozen level from the oracle, since the studio generates no levels and ports no CORE), or `none` — validates
it before any projection (the cell in range and in the alphabet, the border still rock, the carried camera
still on a traversable cell of the new authority, the material class known), writes the new level and tiles
as files beside the record (the world survives the app), and records before/after W, M, C, frame digest and
pixel sha with the consequence: `strips_changed` (columns whose index column differs), `columns_changed`
(columns with any pixel differing), `pixels_changed` and its permille. `edit check` re-derives every value
from the files and refuses typed: `STALE-PROJECTION`, `PROJECTION-WITHOUT-AUTHORITY`, `CAMERA-MOVED`,
`AUTHORITY-MISMATCH`, `BEFORE-MISMATCH`, `CONSEQUENCE-MISMATCH`, `INVALID-EDIT`.

**Rows (on the witness authority, camera (34, 28) W carried).** `workshop-seed` — the neighbour level
`0xABCDF/1`: W moved, M unmoved, frame moved, 1,919 of 1,920 strips and 1,228,154 pixels (592 permille);
CHECK OK. `workshop-cell` — cell (31, 27) rock → floor: W moved, M unmoved, the frame moved in 440 columns
and the pixels in exactly those 440 (165,558 pixels, 79 permille) — with M unmoved, appearance moves only
where geometry moved; 1,480 columns untouched. `workshop-tile` — the floor tile recoloured flat: M moved, W
unmoved, the frame digest UNMOVED, 0 strips, 694,648 pixels (334 permille) in 1,920 columns — the
lookup-moves-no-index law as a consequence row (694,648 is the witness frame's floor pixel count, measured in
Urðr's TILE-0: every floor pixel and only floor pixels). `workshop-identity` — the no-op is accepted with
everything unmoved, so the refusals are not vacuous. `workshop-stale` — PLANT: the authoritative cell changed
while the recorded projection stayed → `STALE-PROJECTION`. `workshop-projection` — PLANT: the picture changed
while W, M and the camera did not → `PROJECTION-WITHOUT-AUTHORITY`. `workshop-camera` — PLANT: a turned camera
→ `CAMERA-MOVED`. `workshop-authority` — PLANT: one more cell changed in the after FILE than the record says →
`AUTHORITY-MISMATCH`; restored, the record re-derives. `workshop-invalid` — six edits refused before any
projection, each `INVALID-EDIT` with its reason.

**Grade.** MEASURED: the three signatures (seed: W+frame+pixels; cell: W+frame+pixels, columns = strips;
tile: M+pixels, frame unmoved) and the five refusals, live on every gate run. ESTABLISHED: the workshop
holds no renderer state (it calls `picture()` and writes files; read off the source). DECLARED: nothing.

**does_not_show.** A level generated here (the seed edit is a choice among frozen authorities). An edit to
the camera as a design act (a camera record is a later rung — it is refused here on purpose). Filtering,
variety within a class, stairs, sky, motion. Any wall-clock: `record` is off the frame path. That a
projection tampered *after* the kernel — by a shell — is caught: that needs the shell to hash what it
blits (SHELL-0's contract), not this rung.

**Falsifier.** Each PLANT row reddens if its refusal stops firing; `workshop-cell` reddens if appearance ever
moves in a column whose geometry did not (with M unmoved); `workshop-tile` reddens if a material edit ever
moves the frame digest.
