<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# `kernel/` — the deterministic per-frame work

Contract: a scene in (the level, the eye, the facing, the colour table, the per-band maps, the tiles — all
INPUT), an 8-bit index frame and a 1920×1080 RGB picture out, and two witnesses: the URDRFB1 frame digest
(geometry) and the picture's sha256 (appearance). std-only Rust; no shell dependency, no UI toolkit, no
presentation API; nothing here opens a window or reads a clock inside the gate. The kernel mints no authority:
it cannot change a cell, a tile or the camera, and the workshop cannot be reached from here.

Lands at KERNEL-0 as the placement from Urðr's `tools/terrain/mantle_rs/mantle.rs`, verified against
`../oracle/` by `../verify/verify.py`.
