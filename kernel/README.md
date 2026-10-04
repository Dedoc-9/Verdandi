<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# `kernel/` — the deterministic per-frame work

Contract: a scene in (the level, the eye, the facing, the colour table, the per-band maps, the tiles — all
INPUT), an 8-bit index frame and a 1920×1080 RGB picture out, and two witnesses: the URDRFB1 frame digest
(geometry) and the picture's sha256 (appearance). std-only Rust; no shell dependency, no UI toolkit, no
presentation API; nothing here opens a window or reads a clock inside the gate. The kernel mints no authority:
it cannot change a cell, a tile or the camera, and the workshop cannot be reached from here.

## Blueprint

Two cameras live here, and each has the same shape: a frozen reference that is the correctness court, and a fast
sibling that is the production path and is held to the reference byte for byte.

```text
    the facing camera (N, E, S, W)                   the bearing camera (any registered heading)

    mantle.rs    frozen: the tag's arithmetic        bearing.rs       frozen: the tag's text
        │        byte-identical at every tread           │            byte-identical at every tread
        ▼                                                ▼
    fast.rs      render(): the threaded emit, T=8    bearingfast.rs   tread ca: exact stepping, 8 row bands
        │                                                │
        └────────────► the shell's present path ◄────────┘     shell/present.rs, shell/heading.rs

    formats.rs   W the level · M the tiles · C the camera ──► compose() ──► the scene the kernels take
    vocab.rs     the headings: 360,000 ids, each naming one primitive Pythagorean triple; pinned, fail-closed
    hud.rs       the overlay, drawn into the picture and never into the index frame
```

The asymmetry is the design. A candidate is guilty until its bytes agree; the differential always runs candidate
against frozen, never the reverse; and a reference is never edited for speed, so a faster path can only ever be
wrong, not redefine what right is.

| Invariant | Mechanism | Row |
|---|---|---|
| The facing kernel reproduces `urdr-oracle-1` | both witnesses recomputed against the record and the corpus | `kernel-oracle`, `kernel-corpus` |
| The bearing reference reproduces `urdr-oracle-2` | its 104 witnesses, bit for bit | `bearing-oracle` |
| At the four cardinals the bearing camera is the facing camera | the anchor law, with a mirrored plant | `bearing-anchors` |
| Every fast tread equals its reference | a differential court over the corpus and adversarial cameras, at every partition and thread count | `gauntlet1-equiv`, `gauntlet2-partition-invariance`, `gauntlet2-threaded-equiv`, `bearingfast-court`, `bearingfast-threads` |
| The fast bearing path cannot overflow unseen | a checked build over the court set; every narrowing through `narrow` with its bound | `bearingfast-checked`, `bearingfast-bounds` |
| A reference is not edited, and apparatus is not a renderer | source fences | `bearing-fence`, `gauntlet2-lockfence`, `rebreakdown1-fence` |
| The heading vocabulary is the tag's | the table's pin checked before a triple is read | `bearing-vocab`, `oracle2-identity` |

| File | What it is |
|---|---|
| `mantle.rs` | the kernel proper: Urðr's placement made a library (`parse_scene`, `picture`, `Scene::{strips,frame,emit}`, `frame_digest`, `sha256`); the arithmetic is the tag's, byte for byte — the **frozen correctness oracle**, never modified for performance |
| `fast.rs` | GAUNTLET-1: a SIBLING of `emit` (never `mantle.rs`), the optimization staircase — each tread byte-identical to the frozen emit. `emit` = **LOCALITY-0 LOCKED** — the GAUNTLET-1c row-major floor DDA (ceiling + wall an exact transcription; the floor's perspective divide done per-ROW by a Bresenham-exact recurrence, O(rows) not O(pixels)) with the floor tile fetched from the 8×8 **BLOCKED** execution format. `floor_blocked` is the single repo-wide blocked-index definition; `blocked_floor` swizzles the tile into that format ONCE at scene load; the hot path reads that pre-swizzled buffer via `floor_blocked` — monomorphized, no runtime layout branch, `scene.floor` never read there. `emit_linear` = the GAUNTLET-1c **archived linear-fetch DDA**, retained verbatim on the archive shelf as the immutable **reference witness** the historical courts measure against. `emit_collapse` = GAUNTLET-1b's **divide-collapse** (2 `div_euclid`/floor px), kept verbatim as the same-apparatus speed BASELINE. `emit_partitioned(group)` = **GAUNTLET-2**'s partition-agnostic core (the parallelizable form): renders any column subset in any order, byte-identical to the frozen emit, via the LOCKED blocked DDA seeded per contiguous run — output is a pure function of the column SET (disjoint writes, no shared/reduction state), so any partition of `0..W` in any order equals the frozen picture. `emit_threaded(threads)` = **GAUNTLET-2**'s execution mechanism: builds the contiguous `T`-group partition and calls `emit_partitioned` once per group across `std::thread::scope`, one contiguous group per thread, disjoint framebuffer writes — no rendering logic of its own (every pixel routed through `emit_partitioned`), byte-identical to frozen at every `T`. `render` = **GAUNTLET-2 LOCKED** — the accepted production render: mantle's frozen strips + frame, then the pixels via `emit_threaded` at `PROD_THREADS = 8` (the production default; T=8 is an execution parameter, not the oracle — the `{1,2,4,8,16}` court is untouched). The shell's `present.rs` renders through this. `structure` = RE-BREAKDOWN-1 Court A (deterministic divide/read/working-set/locality/write-once measures). `mod probe` = RE-BREAKDOWN-1 Court B, a FENCED ablation apparatus (`emit_probe<MODE>` ADDR/LOOKUP/FULL/VERIFY, `black_box`-anchored; VERIFY == emit_linear) — measurement scaffold, never a renderer, never in the promotion chain. RE-BREAKDOWN-1b's `anchor_of` gives every mode the identical 3-byte combine so the anchor tax is constant and cancels in the increments (`LOOKUP−ADDR` = tile fetch, `FULL−LOOKUP` = map indirection). `mod locality` = LOCALITY-0 court apparatus: `swizzle_index<LAYOUT>` (BLOCKED delegates to `floor_blocked`; MORTON Z-order; both lossless bijections), `swizzle_tile`/`unswizzle_tile`, and `emit_swizzled<LAYOUT>` (the DDA emit with the floor fetched from the re-laid-out copy — byte-identical, the execution FORMAT of the same CONTENT). Rows `gauntlet1-equiv` / `gauntlet1b-reduction` / `gauntlet1c-dda` / `rebreakdown1-*` / `locality0-equiv` / `-bijection` / `-provenance` / `-indextax` / `-lock` / `-lockfence` / `gauntlet2-preregistered` / `gauntlet2-partition-invariance` / `gauntlet2-threaded-equiv` / `gauntlet2-threaded-fence` / `gauntlet2-lock` / `gauntlet2-lockfence` |
| `vocab.rs` | BEARING-0: the bearing vocabulary — `../oracle/bearing_octant.txt` compiled in and checked against urdr-oracle-2's pin before any triple is read (fail-closed, never regenerated); the id read only in canonical decimal inside [0, 360000), never normalized; the record's exact expansion (octant, mirror, gcd, quarter turns); the table digest over all 360,000 ids; the bearing camera (x, z, id) composed into the oracle's `URDRBRGI` scene |
| `bearingfast.rs` | BEARING-FAST-0: the bearing camera's **production path**, a sibling of `bearing.rs` held to it byte for byte. Since MOUSE-LOOK-0 its tread `ca` (exact stepping on PROD_THREADS row bands) is what the live editor renders through at a free heading, reached only from `../shell/heading.rs` — the reference's strips reused, then the index frame and the picture in one row-major pass of exact 64-bit walkers (the floor's two coordinates stepped per column at any heading, the wall's v per row; one 128-bit setup per row or column); treads A (that pass), B (the floor from LOCALITY-0's blocked layout) and C (PROD_THREADS row bands over either); the envelope refused, every narrowing through the checked `narrow` with its bound. Rows `bearingfast-court` / `-threads` / `-checked` / `-bounds` / `-fence` |
| `bearing.rs` | BEARING-0: the **reference bearing kernel** — Urðr's `bearing_rs/bearing.rs` at `urdr-oracle-2` with only visibility and shape changed (its core is the source's text with `pub` added, pinned by `bearing-fence`); i128 where a product exceeds 64 bits; the correctness court every faster bearing path must reproduce byte for byte, never modified for performance. No live path renders through it; since SIM-TICK-0 it recomputes the live path's free-heading frames (every one before a session is saved, one in 64 during a run) and is the only bearing kernel the workshop's `sessionwalk` replays a look with. Rows `bearing-vocab` / `bearing-oracle` / `bearing-anchors` / `bearing-selftest` / `bearing-refuse` / `bearing-fence` |
| `formats.rs` | the studio's input formats — W the level (`VRDNLVL1`), M the tiles (`VRDNTIL1`), C the camera — and `compose()` into the kernel's `URDRMNTI` scene |
| `hud.rs` | HUD-0: the overlay drawn into the picture — reticle, strip-band bar, facing plate, minimap; a declared region; the overlay's own identity; the region audit |
| `main.rs` | the command line: a scene or `--level/--tiles/--camera`, the two witnesses; BEARING-0's `--at x,z,K` (the reference bearing kernel), `--bearing-table` and `--bearing-triple K`, and BEARING-FAST-0's `--bearing-court FILE` (every tread against the reference over a camera list), `--bearing-bench` (off-gate, one tread per process) and `--fast-scene`, apart from the facing path; `--hud` for the overlay's three lines, `--write-png` (a PPM), and off-gate `--bench` (2-phase) / `--breakdown` (GAUNTLET-0: strips/frame/emit + the two witness hashes) / `--fast` (GAUNTLET-1 / LOCALITY-0 LOCK: the LOCKED blocked emit + the archived linear reference + collapse vs frozen emit, region divide-work) / `--fast-bench` (GAUNTLET-1c: frozen / collapse / DDA emit timed on one apparatus, all three must reproduce the witness) / `--emit-structure` (RE-BREAKDOWN-1 Court A, deterministic) / `--emit-breakdown` (RE-BREAKDOWN-1 Court B: the addr/lookup/full/emit ablation ladder, probe VERIFY == emit) / `--locality` (LOCALITY-0 differential: both floor layouts byte-identical + bijection + content/format + per-band locality) / `--locality-bench --variant blocked\|morton` (LOCALITY-0 process-isolated host timing) / `--gauntlet2` (GAUNTLET-2 correctness court: partition invariance — `emit_partitioned` over contiguous + adversarial column partitions byte-identical to frozen, deterministic, no threads) / `--gauntlet2-threads` (GAUNTLET-2 threaded byte-identity: `emit_threaded` byte-identical to frozen at `T` in {1,2,4,8,16}) / `--gauntlet2-bench N --threads T` (off-gate: p99 of the threaded emit at an explicit thread count, byte-identity first) / `--render` (GAUNTLET-2 LOCKED production render: `fast::render` at `PROD_THREADS=8` byte-identical to the frozen picture). It only times pub calls — it never modifies the frozen renderer |
| `attest/bench-<host>.json` | the kernel's wall-clock on a named host, sealed under RECORD-0's envelope (written by `../verify/bench.py`; budgets as data, the comparison in the reading) |
| `attest/breakdown-<host>.json` | GAUNTLET-0: the render decomposed per pub-phase (strips/frame/emit) with the two witness hashes separated, sealed under RECORD-0 (written by `../verify/gauntlet.py`, cites the GAUNTLET-0 preregistration; the 500-permille decision rule is the reader's) |
| `attest/gauntlet1b-<host>.json` | GAUNTLET-1b: the same-apparatus emit-level speed delta (frozen emit vs the collapse) on a named host, sealed under RECORD-0 (written by `../verify/gauntlet1b.py`, cites the GAUNTLET-1 preregistration; witnesses checked first, the promotion comparison in the reading, never cross-compared to GAUNTLET-0's absolute) |
| `attest/gauntlet1c-<host>.json` | GAUNTLET-1c: the same-apparatus emit-level speed delta (the DDA vs the GAUNTLET-1b collapse baseline, frozen for context) on a named host, sealed under RECORD-0 (written by `../verify/gauntlet1c.py`, cites the GAUNTLET-1 preregistration; all three emits reproduce the witness first, the promotion comparison — vs the collapse, not frozen — in the reading) |
| `attest/emit-breakdown-<host>.json` | RE-BREAKDOWN-1: emit's deterministic structure (Court A) and the same-apparatus ablation attribution of its work classes (Court B) on a named host, sealed under RECORD-0 (written by `../verify/rebreakdown1.py`, cites the RE-BREAKDOWN-1 preregistration; probe VERIFY == emit checked first; the increments read as incremental attribution under controlled ablation, never a resource cost, never vs GAUNTLET-0's absolute) |
| `attest/locality0-<host>.json` | LOCALITY-0: the process-isolated, interleaved speed of the blocked and Morton floor-tile layouts vs the DDA baseline on a named host, sealed under RECORD-0 (written by `../verify/locality0.py` under the Epistemic-Invariance boundary, cites the LOCALITY-0 preregistration; byte-identity checked first; three exits in the reading, the accepted single-thread emit sealed as the GAUNTLET-2 baseline; never vs GAUNTLET-0's absolute) |
| `attest/gauntlet2-<host>.json` | GAUNTLET-2: the parallel emit's `T \| correctness \| p99` matrix vs the inherited single-thread baseline on a named host, sealed under RECORD-0 (written by `../verify/gauntlet2.py`, cites the GAUNTLET-2 preregistration; byte-identity checked first at every `T`; the baseline is read from the sealed `locality0-<host>.json`, never re-derived; the promotion and the memory-hierarchy reading — a scaling stall is bandwidth/cache contention, not too few threads — are the reader's; never vs GAUNTLET-0's absolute, no refresh claim) |
| `attest/gauntlet2-confirm-<host>.json` | GAUNTLET-2 reproducibility: a confirming sweep sealed under RECORD-0 by `../verify/gauntlet2.py --confirm`, citing the canonical `gauntlet2-<host>.json`'s chain hash and stating whether the shape reproduced. Durable confirmation evidence that never replaces the original sealed measurement |

Placed at KERNEL-0 from Urðr's `tools/terrain/mantle_rs/mantle.rs` at `urdr-oracle-1`, verified against
`../oracle/` by `../verify/verify.py` on every run (rows `kernel-oracle`, `kernel-corpus`, `kernel-selftest`).
HUD-0 added the overlay under its own pins (`../verify/pins/hud-1.json`; rows `hud-*`): the certified picture
underneath is untouched, the index frame is never written, and the overlay reads the strips, the cells and the
camera — never a material, never the shell.

BEARING-0 placed the reference bearing kernel from Urðr's `tools/terrain/bearing_rs/bearing.rs` at `urdr-oracle-2`,
verified against `../oracle/urdr-oracle-2.json` on every run (rows `bearing-oracle`, `bearing-anchors`,
`bearing-selftest`). It is a sibling of `mantle.rs`, not a change to it: the facing path and the production render
are untouched. At BEARING-0 the shell did not include it; since SIM-TICK-0 `../shell/heading.rs` is the one file of
the shell that reaches the bearing kernels.

## Dev notes

- **One apparatus, one delta.** Three harnesses gave three "single-thread emit" p99s (about 4,734, 5,019 and
  7,734 µs). None is wrong and none is comparable with another. A speed claim here is a ratio inside one run of one
  harness.
- **A layout that wins for one camera can lose for the other.** The 8×8 blocked floor was locked for the facing
  emit (LOCALITY-0). For the bearing camera the same layout (tread B) was measured and not kept; exact stepping on
  row bands (`ca`) was. Each was decided by its own court, under a rule locked before its number.
- **Stop when the target is met.** BEARING-FAST-0's target was 6,667 µs; the host read 3,716 µs at the worst
  camera. A persistent worker pool (a tread D) had a registered trigger, and the trigger did not fire.
- **Wide where the product is wide.** The reference uses 128-bit integers wherever a product exceeds 64 bits. The
  fast path walks in 64 bits with one 128-bit setup per row or column, and the court's checked build is what shows
  the narrow walk stays in range over the court set.
- **Registered, not built.** READER-COURT-0 will place `savedform.rs` here beside `formats.rs`, because the shell
  and the workshop already share this folder's files by path. It is the reader of the saved form and no part of a
  renderer; neither renderer identity will include it.

## Ghosts

In full in [`../docs/GHOSTS.md`](../docs/GHOSTS.md). The ones that live in this folder:

- **G1.** The threaded emit's framebuffer write is race-free and not clean under Rust's formal aliasing model.
- **G2, G3.** The T=8 plateau is read as a bandwidth limit and no bus was measured; threads are spawned every frame.
- **G5.** Every speed is one host and one corpus.
- **G6.** What is proven is the output's bytes, not the instruction schedule the isolation theorem asks for.
- **G18.** Outside the court set, the threads set and the sweep, the fast bearing path's agreement with the
  reference rests on the bounds the gate checks, not on an exhaustive comparison; and the quarter-millidegree bound
  on a heading's angle is declared, as it is in Urðr.
