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

## HUD-0 — the overlay is a frame (seat 1 of the ratified order)

**What landed.** `kernel/hud.rs` — geometry only, no glyph, no font, no asset: a reticle at the horizon (a black
3-px cross under a white 1-px cross, a gap at the centre), a strip-band bar along the bottom 40 rows (per
column the depth band as height, the light family as shade — read off the strips), a facing plate (four
squares, the current facing white), and a minimap of the level's cells (rock, floor, up, down) with the eye's
cell white and a red tick on its facing side. A declared region (four rectangles); `overlay()` writes only
inside it; `overlay_bytes()` is the overlay drawn on black, its region's pixels — the HUD's identity,
independent of the viewport underneath; `region_audit()` counts pixels changed inside and outside. `kernel
--hud` prints three more lines (`hud_overlay`, `hud`, `hud_region inside= outside=`); `--write-png` writes
the composite as a binary PPM, off-gate, for eyes.

**The pins.** `verify/pins/hud-1.json` — per scene × tile set the overlay identity, the composite sha and the
inside count, minted by the kernel on landing. This is Verðandi's first appearance authority: Urðr has no HUD
to certify, so the pins are goldens held under laws (the four rows below), the way Urðr's own emissions are
pinned. The viewport's authority stays Urðr's (`hud-index` proves the certified picture is untouched
underneath).

**Rows.** `hud-pins` — 12 composites and 12 overlay identities equal the pins. `hud-index` — with the overlay
drawn, every frame digest and viewport pixel sha still equal the frozen corpus: the HUD moves no index.
`hud-region` — 0 pixels changed outside the region in every scene; 106,388 inside (76,800 bar + 2,304 plate
+ 27,200 minimap + 84 reticle arms, every one different from what was under it). `hud-materials` — the overlay
identity is the same under both tile sets in every scene and differs between scenes, including the
camera-only pair corridor/pointblank: it reads geometry and the camera, never a material. `hud-selftest` —
PLANTS: one pixel written outside the region is counted (`outside=1`); the facing frozen to W moves the pinned
overlay of corridor, room and landmark and of none of witness, pointblank and neighbour (which face W).

**Grade.** MEASURED: the four laws and both plants, live. ESTABLISHED: the overlay writes pixels and never
indices (read off the source: `overlay` takes `&mut [u8]` of the picture and no frame). DECLARED: the layout
and the shades (pinned, not argued).

**does_not_show.** Legibility at 1080p (a design judgment, off-gate; a PPM is there to look at). Text of any
kind — the three hashes and the camera as glyphs wait for a bitmap font carried as a frozen asset F with its own
sha256 (never a rasteriser: outline glyphs differ across builds). That the shell blits this buffer (SHELL-0). Any
wall-clock.

**Falsifier.** `hud-region` reddens on the first stray pixel; `hud-index` on the first moved index; `hud-pins`
on any moved mark; `hud-selftest` if either plant stops biting.

## The seated order (COURT-1, ratified)

HUD-0 → SHELL-0 → MEMBRANE-0 → TEXT-0 → WORKSHOP-1 → INPUT-0 → LATENCY-0 → GAUNTLET-1 → GAUNTLET-2 →
MATERIAL-0. Each rung stands on one already measurable; headless before windowed; measure before optimise.

**An open clause, recorded so it is decided on purpose.** New kernel semantics the studio did not inherit from
Urðr (a filtered level per depth band, variety within a class) can be earned by either route: in Urðr under its
gate and re-frozen here as `urdr-oracle-2`, or by a Verðandi-local VIEW reference pinned by rows here (as the
HUD's pins are). CORE semantics have one route only — Urðr. Which route a rung takes is decided when it is
seated; the charter must admit both.

## WORKSHOP-0b — the truth table, populated (an amendment under review)

**Why.** A reviewer proposed a lock-step law for `edit check`: with the camera carried, *authority moved ⟺
projection moved*, refusing `VACUOUS-EDIT` (authority moved, projection static) and `PHANTOM-PROJECTION`
(projection moved, authority static), first over the frame digest and then over frame-or-pixels. Measured
before it was argued: `edit census` over every single-cell edit of the witness level under (34, 28, W) —
1,379 edits — finds **1,308 (948 permille) that move the authority and nothing on screen** (the edit is out of
the view), and 71 that move strips, frame and pixels together. The `workshop-tile` row had already shown M
moving with the frame digest unmoved. So the biconditional is not a law of this system; the rule would refuse
nineteen of every twenty legitimate edits. Its second arm cannot occur on re-derived values (the kernel is a
function of the authority and the carried camera) and, on the record's claims, is already
`PROJECTION-WITHOUT-AUTHORITY`. What the proposal was right about — scope the check to the carried camera,
make the case analysis exhaustive and inspectable, distinguish the two ways a camera can move — is taken.

**What landed.** A third witness: `strips`, the sha256 of the exact strips (voxel, face, `tn/td`, top, bot,
band per column) — geometry at the kernel's own grain, beside the frame digest (geometry at the index grain)
and the pixel sha (appearance). The consequence classified by an exhaustive `match` over (W or M moved,
strips moved, frame moved, pixels moved) into a recorded **signature** — `identity`, `outside-view`,
`geometry`, `material`, `geometry+material`, `sub-index` (strips and pixels moved, the index did not:
possible in principle, unseen), `sub-pixel` — with only the arms the kernel makes impossible refused
(`CONSEQUENCE-IMPOSSIBLE`). Per column, `strips_changed`, `index_changed`, `columns_changed`, and
`columns_unexplained` — pixels moved with no strip, no index and no material behind them — a field whose law
is zero. Two `CAMERA-MOVED` reasons (beside an edit; instead of one). `edit census` as an off-gate
instrument, its record `workshop/attest/census-witness.json` committed (no clock inside, so it reproduces).
Record version 2.

**What the finer grain showed.** On the cell edit, the exact strip moved in 439 columns and the index column
in 440: the index frame draws a seam's ink from the *neighbour's* strip, so an index column can move with its
own strip unmoved. On the level edit, 1,920 strips moved and 1,919 index columns and pixel columns: one
column's geometry moved below what the index and the texel round to. Both are why the per-column law is a
subset — `columns_changed ⊆ strips_changed ∪ index_changed` with M unmoved — and not the equality the
earlier `workshop-cell` row asserted (true on the corpus edit, not provable; corrected here).

**Rows.** `workshop-seed` / `-cell` / `-tile` / `-identity` now assert their signatures (`geometry`,
`geometry`, `material`, `identity`) and zero unexplained columns. `workshop-outside` — cell (1, 1) rock →
floor: signature `outside-view`, W moved, strips/frame/pixels unmoved, CHECK OK: the arm a biconditional
would refuse, accepted as a consequence. `workshop-census` — the record's provenance (W, M, camera, base
witnesses) equals the frozen corpus; impossible 0; unexplained 0; counts sum to the edits tested; the number
stated. `workshop-camera` now carries both plants. `workshop-stale` includes the strips.

**Grade.** MEASURED: the census (1,379 edits), the five signatures on the corpus, the zero-unexplained law on
every edit, both camera plants. ESTABLISHED: the impossible arms (read off the kernel: a function of the
authority and the camera). DECLARED: the signature names.

**does_not_show.** That `sub-index` never occurs (unseen in 1,379 edits on one level and one camera; the
signature exists so it is recorded, not hidden). A census on any other level or camera. That a biconditional
holds for some *other* pair of quantities (none was proposed).

**Falsifier.** `workshop-outside` reddens if an out-of-view edit is ever refused; `workshop-census` if the
record stops re-deriving from the corpus or an unexplained column appears; every signature row if its
classification moves.

## RECORD-0 — the record envelope, the firewall, the preregistration (a fork of executable-epistemics)

**Why.** Reviewer proposals kept pointing at a bridge/epistemic layer; the reusable part was not in the
documents but in the owner's `Dedoc-9/executable-epistemics` — `witness_core.Artifact`: data + provenance +
`claim_class` + `validity_scope` + `forbidden_interpretations`, a chain hash, an interpretive firewall that
raises on any verdict-shaped key inside data, and a registry that refuses a study without a failure condition.
Verðandi's records had provenance and a reading and none of the rest; and Urðr's own bench record carried
`"verdict": {"60Hz": "within"}` — a verdict stored as data, which this firewall refuses. RECORD-0 makes the
envelope the format every record Verðandi mints is written in, in both its languages, read through one gate.

**What landed.** `verify/envelope.py` — the envelope (`seal`, `validate`, `read`, `write`, `chain_hash`,
`canonical`): the seven required fields, `claim_class ∈ {measured, established, declared, predicted}`, a
`validity_scope` with a non-empty `certifies`, a non-empty `forbidden_interpretations`, no verdict-shaped key
anywhere in `data` (scanned; the set extends witness_core's with the gate's own `pass/fail/status/within/over`),
integers only, and a chain hash over the required fields (the `reading` stays outside it). A **Rust twin** in
`workshop/edit.rs` — `json_canonical` + `envelope_seal`/`envelope_validate` — writing the same canonical bytes,
so `edit record` and `edit census` mint sealed records the Python gate re-hashes. The HUD pins re-minted under
the envelope; the census record carries the **cone** split and `geometry_outside_cone`. `verify/bench.py` — the
kernel's wall-clock as a sealed record with the budgets as data and the comparison in the reading (the shape
Urðr's record should have had). `verify/preregister.json` — a hash-locked registry: RECORD-0 and SHELL-0 each
with hypothesis, success **and** failure conditions and interpretation limits, before their instruments run.

**The cone.** A theorem (`in_cone`, `workshop/edit.rs`): every ray has |forward| = 1920, |sideways| ≤ 1919 and
the floor point lies on it, so a cell any ray can touch is forward of the eye and no farther sideways than
forward (+1 for its extent). The census confirms it: of 1,379 single-cell edits, all 71 geometry edits lie
inside the cone; of the 1,308 outside-view edits, **712 are outside the cone** (a coordinate test could name
them without the kernel) and **596 are inside it, occluded** (only the traversal can). An out-of-view cell edit
now carries a computed `explanation` — "outside the view cone" or "inside the view cone, occluded" —
re-derived by `check`. This is the honest form of the reviewer's frustum pre-filter: a coordinate test bounds
the dirty region and names 712/1,308, but cannot replace the kernel for the 596 the cone cannot see are hidden.

**Rows.** `records-firewall` — every committed record validates under the envelope; a `verdict` key inside
data and a change after sealing are both refused. `records-twins` — Python recomputes the chain hash of every
record Rust sealed this run and of the census; Rust refuses the Python-made verdict and tamper plants
(`ENVELOPE`); the two firewalls carry the same 17 verdict keys (read off both sources). `records-preregistered`
— every registry entry has a failure condition and a hash lock; a record of a preregistered rung must cite its
entry's hash (none yet; SHELL-0's is the first).

**Grade.** MEASURED: the firewall on every record, the two plants, the twin agreement, the cone split.
ESTABLISHED: the cone theorem (read off the ray bounds; the census is its witness, not its proof). DECLARED:
the verdict-key set, the claim classes, the preregistered conditions (declared is what a registration is).

**does_not_show.** That a chain hash makes data true — it detects tampering after sealing; `check` and the rows
earn truth. That the firewall catches a verdict smuggled as a value or a string — it scans keys; only reading
catches meaning. That the cone is tight — it is conservative (712 named, 596 not). That the 596 occluded edits
could be named more cheaply than by the traversal.

**Falsifier.** `records-firewall` reddens if any committed record loses a field, gains a verdict key, or
carries a hash it cannot reproduce; `records-twins` if the two languages' canonical forms or verdict sets ever
diverge; `records-preregistered` if an entry is edited after its lock or a rung's record cites a stale one;
`workshop-census` if a geometry edit is ever found outside the cone.

## The seated order (COURT-1, amended by COURT-2)

**RECORD-0** → SHELL-0 → MEMBRANE-0 → TEXT-0 → WORKSHOP-1 → INPUT-0 → LATENCY-0 → **GAUNTLET-0 (the strip
cache)** ‖ GAUNTLET-1 (the floor cast) → GAUNTLET-2 (columns) → MATERIAL-0. RECORD-0 landed before SHELL-0 so
the first present-path record is born under the envelope and preregistered. GAUNTLET-0 — caching the strips and
frame across frames with a still camera and no world edit (proven safe: `strips()` and `frame()` read no tile)
— joins the gauntlet beside GAUNTLET-1. The reviewer's frustum pre-filter and material short-circuit were
measured and are folded in as the cone bound (a census row) and GAUNTLET-0; rayon, per-column hash caching and
edit coalescing were declined (a dependency the charter excludes; memory for a millisecond diff; WORKSHOP-1's
territory). The `intent`/`feedback` bridge was declined: an `expected_change` field is unfalsifiable, and
`outside-view` is already `CHECK OK`, not a refusal.

## SHELL-0a — the blit-hash law, headless (seat 5, the container-verifiable half)

**The boundary.** SHELL-0 opens a window and times `frame-ready → composited` on the owner's host; a Linux
container has no Win32, no window and no DWM clock, so the rung splits. SHELL-0a lands the half that is
verifiable anywhere — the blit-hash law — with the window written and `cfg(target_os = "windows")`-gated, so
the gate compiles the shell with the Win32 module out and the law is what it exercises. The host half
(the window, the present, the number) is a follow-up the owner runs; its conditions are already hash-locked in
`verify/preregister.json` (SHELL-0), and `shell/win32.rs` is the one file the gate does not compile.

**What landed.** `shell/present.rs` (std-only, platform-agnostic): `compose_frame` renders a scene to the
composite the shell shows — the kernel's viewport with the HUD overlay — and `to_blit` converts it to the exact
bytes `StretchDIBits` receives: 24-bit BGR, top-down, DWORD-aligned (W = 1920 → 5760 bytes/row, no padding).
`from_blit` is its inverse (a B↔R swap, self-inverse), so `blit_roundtrip_ok(c) = from_blit(to_blit(c)) == c`
and `blit_witness = sha256(to_blit(c))` is the sha of exactly what the OS is handed — which, the transform being
a bijection, determines the composite's sha and back. `shell/main.rs`: `shell witness` (the composite sha and
the blit witness), `shell selfcheck` (`blit_roundtrip OK|BROKEN`), `shell run` (Windows: the window;
elsewhere: `SHELL-NO-WINDOW`, refusing rather than pretending). `shell/win32.rs` (cfg-gated): a hand-rolled
Win32 window — `RegisterClassW`/`CreateWindowExW`, a message pump, `StretchDIBits`, `DwmFlush`
(the composition barrier), `QueryPerformanceCounter` — that guards every present with the blit witness (a frame
whose blit is not the kernel's composite is refused, not shown) and writes a raw present record. `verify/pins/
shell-1.json` (sealed): per corpus scene × tile, the composite (equal to the HUD composite) and the blit witness.
`verify/seal_present.py`: seals the host's raw present record under RECORD-0's envelope, checking its blit
witness against the pins and citing SHELL-0's registration.

**Rows.** `shell-build` — the shell compiles with the Win32 module cfg'd out. `shell-blit-pins` — 12 composites
and 12 blit witnesses equal the pins, and every composite equals the kernel's HUD composite (the shell shows the
kernel's picture and blits exactly its bytes). `shell-blit-law` — the round-trip holds on all 12 composites, and
a windowless build refuses `run`. `shell-blit-plant` — a present path that drops the red channel moves the blit
witness off the pin and makes `selfcheck` print BROKEN: a picture the kernel did not make is detectable.

**Grade.** MEASURED: the blit-hash law and its plant, the pins, the no-window refusal, live. ESTABLISHED: the
transform is a bijection (read off `to_blit`/`from_blit`; a channel swap is its own inverse). DECLARED: the DIB
format (BGR, top-down); the host present number (preregistered, unmeasured until the owner runs it). UNCOMPILED
here: `shell/win32.rs` (compiled and run only on the host — behind `--cfg shell_window`, which the gate never
passes, so it is out of every gate build on every host; `dwmapi` is loaded at run time, not linked, since its
import library is absent from some mingw toolchains).

**does_not_show.** A present number (the host's, sealed by `seal_present.py`, citing SHELL-0). That
`shell/win32.rs` compiles — the container cannot; the owner compiles it, as with the first `mantle_rs` port. That
the picture on screen is legible. That `frame-ready → composited` is input-to-photon — it is not (input
transport, the present wait beyond composition and the panel need capture hardware).

**Falsifier.** `shell-blit-pins` reddens if the shell's composite ever differs from the kernel's, or the blit
bytes from `to_blit` of it; `shell-blit-law` if the round-trip ever fails or a windowless build stops refusing;
`shell-blit-plant` if a corrupted present path stops being caught.

## SHELL-0 (host) — the first present number

The owner ran `shell run --measure 200` (window build, `--cfg shell_window`) and sealed the record:
`shell/attest/present-DANIELDILLBERG.json`, citing SHELL-0's registration (`de30d1ec`). **frame-ready →
composited: p50 5,289 / p95 6,015 / p99 6,373 / max 6,577 µs**, refresh ~13,466 µs (≈ 74 Hz). It is the blit
plus the wait for the next DWM composition, from a random phase within one refresh — hence a median near 0.4×
the refresh. It **excludes the kernel render** (that is the bench, p50 10.3 ms; the composite is rendered once
and blitted 200 times, so the two instruments do not naively add) and it is **not input-to-photon** (no input,
no scanout, no panel). It is the baseline a flip-model waitable-swapchain shell is later measured against; a
composed GDI present cannot go below one refresh interval, which is the wall the number sits against.
`records-preregistered` counts it as the first committed record to close a preregistered loop.

## MEMBRANE-0 — the one-way law as a compile-time wall (seat 6)

**What landed.** `workshop/membrane.rs` (std-only): `Authority { level, tiles }` owns the world; `read(&self)
-> Reading<'a>` is the render path (an immutable borrow tied to `&self`); `edit_cell(&mut self, …)` is the
write path. While a `Reading` is alive the borrow checker forbids `&mut Authority`, so no edit can run mid-read
— mirrored from the old project's `SimExport<'a>` (a read window that forbids `tick()` while it lives). The
proof is a ROW WHOSE PASS IS rustc's REFUSAL: an `illegal` function, compiled only under `--cfg
membrane_probe_illegal`, edits through a live `Reading` and must fail to borrow-check.

**Rows.** `membrane-build` — the legal build compiles (the control: the file is otherwise sound). `membrane-
witness` — the render path through the typestate (`Authority::read → Reading::witnesses`) reproduces the
kernel's frame digest and pixel sha on all 6 corpus scenes: the wall carries identical semantics and costs
nothing. `membrane-legal` — the permitted sequence (read fully, drop the `Reading`, then edit, then read
again) compiles and runs. `membrane-wall` — compiled with `--cfg membrane_probe_illegal`, editing through a
live read-borrow does NOT compile: rustc refuses with `E0502: cannot borrow *auth as mutable because it is
also borrowed as immutable`. The row passes iff the compile is refused for that reason.

**Grade.** MEASURED (structurally): the wall is rustc's own refusal, checked live; the witness equivalence over
the corpus. ESTABLISHED: the legal build as the control (the failure is the borrow, nothing else). DECLARED:
nothing.

**does_not_show.** Safety against an adversary: `unsafe`, a raw pointer or interior mutability defeats the wall
— it stops HONEST mistakes (a render path that reaches back to mutate the authority), not attacks.
`typestate ≠ security`. That the whole studio is wired through `Authority`/`Reading` — this rung demonstrates
the wall; threading it through `edit.rs`'s full vocabulary is later work. That the wall forbids editing a
DIFFERENT authority while reading one (it does not — the borrow is per-value).

**Falsifier.** `membrane-wall` reddens if the illegal probe ever compiles (the wall stopped biting) or fails
for a reason other than E0502; `membrane-witness` if the typestate path ever renders something other than the
kernel's witnesses; `membrane-build`/`membrane-legal` if the legal path stops compiling or running.

## TEXT-0 — the level as text, content split from provenance (seat 7)

**What landed.** `workshop/text.rs` (std-only): a human authors a level's TOPOLOGY as text — a `depth`
directive and a grid of `#.<>` (rock, floor, up, down) — and it round-trips to the same `VRDNLVL1` bytes.
The depth's colour table and per-band maps are NOT authored here (they are Urðr's derived VIEW semantics, which
the kernel takes as INPUT); `from_text` borrows them from a same-depth oracle level's palette, so the text
holds only what a human should edit. `;` is the comment marker (not `#`, which is always a cell); comments and
blank lines are ignored for content. **Two digests** make the content/provenance split (as Urðr's `worldbind`
row earned it): W (content) = sha256 of the reassembled `VRDNLVL1` bytes, unmoved by a reformat and moved by a
cell edit; authoring digest = sha256 of the exact text bytes, moved by any text change.

**Rows.** `text-build` — compiles. `text-roundtrip` — all 5 corpus levels: `from_text(to_text(L))` rebuilds
the frozen `VRDNLVL1` bytes (W unchanged), and the text form is canonical (re-emitting reproduces it byte for
byte). `text-reformat` — a `;` comment, blank lines and a comment amid the grid leave W (content) UNMOVED at
`1b84db41…` and move the authoring digest (`82015cbb…` → `0336917f…`): the record can tell a reformat from an
edit. `text-edit` — flipping one grid cell (31, 27) rock → floor moves W (`1b84db41…` → `40963eb6…`), and that
W equals the same byte flip applied to the level file — the text's content IS the cells, exactly.
`text-refuse` — three malformed texts refused typed before any content digest: a wrong-depth palette, a
non-alphabet cell, a ragged grid row.

**Grade.** MEASURED: the round-trip and canonicality over the corpus, the reformat/edit split, the cross-check
that a text edit's W equals the byte-level edit's W, the three refusals. ESTABLISHED: the palette is
depth-derived provenance borrowed from a same-depth level (read off `from_text`; the studio computes no
`lut`). DECLARED: the `VWTX1` text format.

**does_not_show.** A text form of the tiles (M) — TEXT-0 is the level (W) only. Authoring a new depth's palette
(the table/maps are Urðr's; a new depth needs a same-depth oracle level as the palette source). That the text
is the only authoring surface — the editor pane (a shell concern) is later. Any wall-clock.

**Falsifier.** `text-roundtrip` reddens if a level ever fails to rebuild its bytes or the text stops being
canonical; `text-reformat` if a reformat ever moves W or ever leaves the authoring digest unmoved; `text-edit`
if a cell edit leaves W unmoved or its W diverges from the byte edit; `text-refuse` if any malformed text is
accepted.

## WORKSHOP-1 — the log is the history, undo is replay, the session is a hash-chained file (seat 8)

**What landed.** `workshop/session.rs` (std-only): a session is a base authority (a level + tiles) and an
ordered log of cell edits (walls and ground) and tile edits (textures) — the two things the frozen oracle
certifies. It is event-sourced: the world is not stored mutably, it is REBUILT by replaying the log from the
base, so `undo to n` is a deterministic replay of the first n edits, never a localised mutation (`apply` is
pure — cells, tiles, no clock, no I/O, no camera). Each entry carries two digests, the claim/full split from
the owner's `provenance_runtime`: `content = sha256(W‖M)` (the authority state after the edit) and
`full = sha256(parent.full‖content)` — a single-writer hash chain whose head is the session's integrity in one
hash. `propose` validates against the head and writes NOTHING (the speculative scratchpad, from
`live_world_kernel`); `commit` appends with its digests; a failed propose leaves the log unchanged. Three
states are reported: committed (in the log), irreversible (something committed depends on it), durable (it
replays). `verify/seal_session.py` seals a committed snapshot under RECORD-0.

**Design, searched.** A single-writer hash chain is the right structure — records are ordered from one author
and verifiers replay from the base anchor, so tampering any entry cascades and breaks every link after it; a
Merkle *tree* only earns its keep for O(log n) sampling proofs a session does not need. Undo-as-replay is
event-sourcing's own rule (rebuild from a snapshot; replay is deterministic because `apply` reads nothing
external). The honest boundary from the audit-log literature: a hash chain catches tampering UNDER REPLAY but
does not prove timing or non-membership, nor stop a rewrite of entries AND hashes together — so the committed
session is additionally sealed under RECORD-0 and anchored by git history.

**Rows.** `workshop1-build` — compiles. `workshop1-replay` — a 4-edit session replays to its head, and a
Python chain twin recomputes the same head independently (a cross-language check, like `records-twins`).
`workshop1-undo` — undo to 2 rewinds the head to exactly a fresh 2-edit session's head (undo is replay), and
verifies committed 2 / irreversible 1. `workshop1-propose` — a valid propose writes nothing; one that opens
the border is refused and still writes nothing. `workshop1-tamper` — changing one log entry's param without
its digests makes `verify` replay and catch `CHAIN-BROKEN`; restored, it re-verifies. `workshop1-demo` — the
committed sealed demo (`workshop/attest/session-demo.json`) replays to its head over 5 edits on the frozen
witness base, three-state consistent.

**Grade.** MEASURED: replay/head, the Python chain twin, undo-as-replay equivalence, propose-writes-nothing,
tamper detection, the sealed demo — all live. ESTABLISHED: `apply` is pure (read off the source: no clock, no
I/O, no camera), which is what makes replay deterministic. DECLARED: the `VRDNSES1` chain construction, the
three-state vocabulary.

**does_not_show.** A skybox or physics — see the open clause below; the log holds only cell and tile edits.
Branching history (the log is linear; a causal-subtree undo is a later rung). A camera (projection-owned,
INPUT-0). Multi-writer or concurrent editing (single-writer by construction). That the chain defeats a
simultaneous rewrite of entries and hashes (it does not; the outer seal and git anchor that).

**Falsifier.** `workshop1-replay` reddens if the head ever diverges from the twin; `workshop1-undo` if undo
ever differs from replay; `workshop1-propose` if a propose writes or an invalid one is accepted;
`workshop1-tamper` if a changed entry is not caught; `workshop1-demo` if the committed session stops replaying
to its head.

## INPUT-0 — moving around is the projection's job, and a walk replays headless (seat 9)

**What landed.** `workshop/input.rs` (std-only): a **walk** is an initial camera and an ordered log of typed
movement commands, replayed against a FIXED level to reproduce the whole camera trajectory and the frame at
every step. The commands are one letter each — `L`/`R` turn (the facing rotates; the cell does not move),
`F`/`B` step along the facing, `Q`/`E` strafe perpendicular — and each is pure and validated against the
level: a step is valid iff the target cell is in the level and not `#` rock, so **walking into a wall does not
move you** (a blocked step is a no-op, still logged). The witness of each step is the kernel's `URDRFB1` frame
digest for (level, camera, tiles), chained into a head like a session: `head = sha256( … sha256( sha256(MAGIC‖
frame0) ‖ frame1 ) … ‖ frameN )`. So a `.walk` file (`VWLK1`, line-oriented, `;` comments) is a hash-chained
artifact: `input write` seals the head, `input verify` replays and catches a tampered command. The camera is
never in W or M — a walk reads the authority and never writes it. `verify/seal_walk.py` seals a reference walk
under RECORD-0 as an *established* (host-independent) record.

**Design, searched.** This is WORKSHOP-0b made operational: the camera is projection-owned, so moving it is a
VIEW mutation, not an edit, and the shell cannot smuggle a camera into the studio because the walk replays
*without* the shell. The direction vectors (N=(0,−1), E=(1,0), S=(0,1), W=(−1,0)) are read straight off the
kernel's `direction`, so the studio and the renderer agree on which way is forward by construction, not by a
second table. The head is the session pattern (genesis over the first frame, then a fold) applied to *frame
digests* rather than authority digests — a walk witnesses the geometry the camera sees, deterministically, on
any host. NOT here: the shell's key/mouse capture (`WM_KEYDOWN` → a command) is **INPUT-0b**, cfg-gated to
Windows in the shell and run on the host; this file is the headless command → camera → frame discipline the
gate exercises.

**Rows.** `input-build` — compiles. `input-replay` — a 5-command walk (`LFFRF`) replays to a camera and head,
and a Python twin *reimplements the movement rules* and chains the frame digests of a *separate kernel process*
to the SAME head (trajectory AND chain cross-checked across two languages and two processes). `input-blocked` —
a forward onto rock does not move the camera, yet the step is logged: its frame equals the unchanged camera's,
and the head is the two-frame chain of that repeat. `input-tamper` — changing one command without recomputing
the head makes `verify` catch `CHAIN-BROKEN` (exit 2); restored, it re-verifies. `input-not-authority` — a
walk moves the camera but the level's W and the tiles' M are byte-identical afterward (the camera is
projection-owned). `input-demo` — the committed sealed walk (`workshop/attest/walk-demo.json`, commands
`LFFRFFBQE`, all six letters) replays to its sealed head over 9 steps (2 blocked), and a Python twin re-derives
it.

**Grade.** MEASURED: replay/head, the two-language two-process twin, the blocked no-op, tamper detection,
authority-untouched, the sealed demo — all live. ESTABLISHED: the direction vectors equal the kernel's
`direction` (read off the source); a blocked step is a no-op (the target-cell test). DECLARED: the `VWLK1`
chain construction and the one-letter command vocabulary.

**does_not_show.** The shell's key/mouse capture (INPUT-0b, host-run — a walk is what a captured session would
*produce*, not the capture). Appearance/lighting beyond geometry (the frame digest is the geometry the camera
sees; M is carried but a walk does not witness a texture change). Collision volume beyond a cell being rock
(the traversability test is per-cell, not sub-cell). A skybox or physics (a walk moves through the frozen
geometry only). That the chain defeats a simultaneous rewrite of commands and head (it does not; the outer seal
and git anchor that).

**Falsifier.** `input-replay` reddens if the head or trajectory ever diverges from the twin; `input-blocked` if
a wall ever moves the camera or the no-op is dropped from the chain; `input-tamper` if a changed command is not
caught; `input-not-authority` if replaying a walk ever changes W or M; `input-demo` if the committed walk stops
replaying to its sealed head.

## SESSION-WALK — move while authoring, one interleaved sealed chain (seat 10)

**What landed.** `workshop/sessionwalk.rs` (std-only): a session-walk is a base authority (W, M) + an initial
camera + ONE append-only log of two event kinds — `move C` (L/R/F/B/Q/E) and `edit SPEC` (cell/tile). It is the
fusion of WORKSHOP-1 (a log of edits) and INPUT-0 (a log of moves), and the central design fact is that the two
**cannot** be independent chains: a move's traversability and its frame are decided against the *current* world,
so an edit that opens a cell changes what a later move sees. Every event is therefore evaluated in log order
against the authority all preceding events produced, and folded into a **single** head:
`content(W,M) = sha256(sha256(W)‖sha256(M))`; `head0 = sha256(MAGIC‖content(base)‖"@"‖camera)`; a move folds the
kernel's frame digest at the new camera over the current (W,M), an edit folds the new content — `head =
sha256(head‖":"‖tag‖":"‖witness)`. `walk_head` and `edit_head` are **derived projections** of this one chain,
never sealed apart. `verify/seal_sessionwalk.py` seals a reference session under RECORD-0 as *established*.

**Design, searched, and a correction.** The tempting architecture was two independent sealed chains combined as
`sha256(walk_head‖edit_head)`, with edits deferred and batch-verified. That is wrong: if a deferred edit opens a
cell a later move enters, batching changes what the move sees, so the same event order yields different
movement — the combined head becomes timing-dependent, breaking the very invariant it claimed. Event-sourcing's
own rule resolves it: the append-only log *is* the authority and read-models/projections are *derived*
([Microsoft's Event Sourcing pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing),
[Kurrent on ES+CQRS](https://www.kurrent.io/blog/event-sourcing-and-cqrs), [read models are derived](https://www.cqrs.com/event-driven-architecture/read-models/)).
So the sealed authority is one interleaved log; the batch scheduler is demoted to a runtime concern whose *only*
certified property is checkpoint/replay equivalence, a known provable property
([replay-determinism equivalence](https://github.com/Obiajulu-gif/vaultquest-archive/issues/751)). Kept out of
the sealed state, by charter: a predicted `expected_change` (unfalsifiable, RECORD-0 firewall-rejected — the
consequence is measured at the event), latency guarantees (declared ≠ verified — timing is LATENCY-0's job), and
adaptive batch sizing (no falsifier). The head stays clock-free.

**Rows.** `sessionwalk-build` — compiles. `sessionwalk-replay` — a 6-event interleaved session replays to its
head, and a Python twin re-derives it (edits mutate W,M; moves render a *separate kernel process's* frame
against the current authority; one fold). `sessionwalk-interleave` — the key one: `EDIT(open 28,27)→MOVE(F)`
steps through the opened cell (final 28,27,N) while `MOVE(F)→EDIT` is blocked (final 28,28,N); same two events,
same final W,M, different head and camera — the move sees the edit, so order is meaning, not a batching artifact.
`sessionwalk-batch-invariance` — the honest delay operator: incremental-append equals monolithic-replay, and
cutting the fold at every split point then resuming from the checkpoint reproduces the identical head.
`sessionwalk-tamper` — changing one event without recomputing its witness makes `verify` catch CHAIN-BROKEN at
that event (exit 2); restored, it re-verifies. `sessionwalk-projection` — dropping every move leaves W,M
identical (moves never author) while dropping every edit changes where a move ends up (edits are not views): the
two-way semiotic separation over one log. `sessionwalk-demo` — a committed sealed interleaved session
(`workshop/attest/sessionwalk-demo.json`: open a doorway, walk through it, retexture the floor, turn and step)
replays to its head.

**Grade.** MEASURED: the interleaved head + twin, order-dependence, checkpoint/replay equivalence, tamper
detection, the two-way projection, the sealed demo — all live. ESTABLISHED: a move evaluates traversability and
its frame against the current authority; an edit never moves the camera; `apply` is pure (read off the source).
DECLARED: the `VRDNSW1` fold construction and the two-tag (M/E) event vocabulary.

**does_not_show.** A live scheduler — this certifies the sealed construction *admits* checkpointing/batching, not
that any batch loop was built (that is the shell, SHELL-PLAYBACK). Timing/latency (LATENCY-0). Branching or
concurrent multi-writer sessions (single-writer, linear log). An edit that turns the camera's own cell to rock
(a real consequence the kernel refuses on the next frame; the demo does not exercise it). A skybox or physics.
That the chain defeats a simultaneous rewrite of events and head (it does not; the outer seal and git anchor).

**Falsifier.** `sessionwalk-replay`/`-demo` redden if the head ever diverges from the twin; `sessionwalk-interleave`
if reordering an edit past a dependent move does *not* move the head (or if the move stops seeing the edit);
`sessionwalk-batch-invariance` if any checkpoint/resume or the incremental vs monolithic head disagree;
`sessionwalk-tamper` if a changed event is not caught; `sessionwalk-projection` if dropping moves ever changes
W,M or dropping edits ever leaves navigation untouched.

## SHELL-PLAYBACK — the window shows exactly the sealed becoming (seat 11)

**What landed.** `shell/playback.rs` (a module of the shell crate, headless): `shell playback --session S` CONSUMES
a sealed SESSION-WALK (`VRDNSW1`) — not a reconstructed action stream — replays it from the base authority, and
for every MOVE renders the kernel's composite through the SHELL-0 present path (`compose_frame` → `to_blit`). The
bridge it certifies is `sealed session → replay → kernel frame → SHELL-0 blit/hash → the window`. Playback
re-derives every event's witness and the head and REFUSES (`DIVERGED`, exit 2) if any diverges from the seal, so
it can never mint a new authority; it reads the level, tiles and session and writes none of them. Checkpoint/
resume is folded in: `shell checkpoint --at K` captures the WHOLE interleaved authority (level bytes, tiles bytes,
camera, head) at event K, and `shell resume --checkpoint CK` reproduces the identical frame-witness suffix and
head as replay from the origin. The on-screen window (`shell playback-window`, **SHELL-PLAYBACK-b**) ships in
`shell/win32.rs` behind `--cfg shell_window`: it guards every frame with the blit law and plays the sealed
session in the real window. Like all of `win32.rs` it is host-run and out of every gate build (graded DECLARED).

**Design, searched.** This is deterministic record-and-replay with per-checkpoint canonical state hashing
([ACM Queue: Deterministic Record-and-Replay](https://queue.acm.org/detail.cfm?id=3688088), [canonical state
hashing at checkpoints](https://github.com/oktayaydogan/aeo2/issues/67)) applied to a sealed authority: the
session is the record, playback is the replay, and the frame-digest sequence is the golden output. The crucial
boundary the search confirmed — separate the simulation from the presentation — is exactly why SHELL-PLAYBACK
certifies the frame SEQUENCE (the theorem: what is shown) and leaves the presentation SCHEDULE (how fast it
reaches the glass) to LATENCY-0's measurement. The checkpoint carries the full authority precisely so it cannot
degrade to a partial projection (only `walk_head` or only `edit_head`) — a corrupted-tiles checkpoint diverges.

**Rows.** `shell-playback-sealed-input` — playback consumes the committed sealed demo and re-derives its head;
refuses a non-session (INVALID-SESSION). `shell-playback-frame-sequence` — **the crown witness**: the composited
frame-digest sequence EQUALS the session's sealed per-move witnesses AND a Python twin rendering each move through
a separate kernel process. `shell-playback-blit-law` — every displayed frame passes `from_blit(to_blit(c))==c`,
and a planted present path that drops red makes playback report BROKEN (the law bites). `shell-playback-no-authority`
— after playback + checkpoint + resume the level's W, the tiles' M and the session file are byte-identical.
`shell-playback-order` — playback presents strictly in log order; a reordered sealed log DIVERGES.
`shell-playback-tamper` — a tampered move and a truncated log both make playback REFUSE (DIVERGED, exit 2).
`shell-playback-checkpoint` — resume from checkpoints at all seven cut positions reproduces prefix++suffix == the
full sequence and the full head, and a corrupted-tiles checkpoint DIVERGES on resume.

**Grade.** MEASURED: the frame-sequence bridge + twin, the blit law + plant, authority-untouched, order
preservation, tamper divergence, checkpoint/resume equivalence — all live headless. ESTABLISHED: playback renders
through the SHELL-0 present path (read off the source: `compose_frame`/`to_blit`); it opens the file read-only.
DECLARED: the checkpoint sidecar format; that the head fold matches `workshop/sessionwalk.rs` (mirrored constants,
cross-checked live by `shell-playback-frame-sequence` and the sealed head).

**does_not_show.** The on-screen window's correctness (SHELL-PLAYBACK-b ships in `win32.rs` but is host-run and
out of every gate build — the gate cannot open a window; what the gate certifies is the headless bridge that
window displays). Presentation timing / frame pacing (LATENCY-0). Appearance
beyond geometry in the *chain* (the move witness is the geometry frame digest; the pixels the window shows are
carried by the blit law but not chained). A skybox or physics. That the chain defeats a joint rewrite of events
and head (the outer seal and git anchor that).

**Falsifier.** `shell-playback-frame-sequence` reddens if the displayed sequence ever differs from the sealed
witnesses or the twin; `shell-playback-blit-law` if a corrupted present path still round-trips; `shell-playback-no-authority`
if playback ever writes W, M or the session; `shell-playback-order`/`-tamper` if a reordered/tampered/truncated
input does not diverge; `shell-playback-checkpoint` if any checkpoint/resume disagrees or a corrupted checkpoint
silently resumes.

## LATENCY-0 — the method is locked before the number; the display is not the software (seat 12)

**What landed (the method, not yet the number).** LATENCY-0 measures ONE thing on the host — the per-frame
`frame-ready → composited` time of the SHELL-PLAYBACK-b present path, replaying the *fixed sealed reference
session* — and it is preregistered before any host number exists. Following the ratified split, the 144Hz claim
is two independent MEASURED conditions, never one Boolean: **SOFTWARE-144-BUDGET** (PASS iff p99(frame-ready →
composited) ≤ 6,944µs — a *budget* condition: 99% of intervals fit the nominal 144Hz period, which is NOT by
itself sustained-144Hz presentation and NOT a refresh-rate claim) and **HARDWARE-144** (PASS iff the *measured*
DwmFlush refresh period ≤ 6,944µs, i.e. ≥144Hz — measured, never inferred from the monitor's nominal setting),
with **SUSTAINED-144Hz = SOFTWARE-144-BUDGET ∧ HARDWARE-144**. The entry in `verify/preregister.json` carries
the hypothesis, both conditions, the failure condition, the interpretation limits and the instrument, hash-locked
(`c4d8db6a…`). `shell/win32.rs playback_window --measure N` is the instrument (QPC after StretchDIBits → QPC
after DwmFlush, per frame across the sealed sequence; refresh = median idle DwmFlush interval); it emits a raw
record `verify/seal_latency.py` seals under RECORD-0 as `shell/attest/latency-<host>.json`, citing this entry.

**Design, searched.** Deterministic record-and-replay measured against a fixed golden sequence, with the honest
boundary the field already draws: `frame-ready → composited` is software-reachable via QPC + DwmFlush, while
input-to-photon needs external capture hardware ([NVIDIA on PC latency](https://developer.nvidia.com/blog/understanding-and-measuring-pc-latency/),
[PresentMon throughput vs latency](https://forums.blurbusters.com/viewtopic.php?t=5552&p=58993),
[DWM present latency](https://jackmin.home.blog/2018/12/14/swapchains-present-and-present-latency/), and
"measure first, then tune" [frame-pacing](https://github.com/portare-ch/distribution/issues/13)). The
software/hardware split exists so a slow display cannot launder a good software number into a false 144Hz claim,
and a good software number cannot imply a display capability that was not measured — on the current ~74Hz panel
(SHELL-0's present record), SOFTWARE-144-BUDGET can pass while HARDWARE-144 is honestly refuted.

**Rows.** `latency-preregistered` — the METHOD is locked: the two conditions are named in both the success and
failure conditions, the budget is 6,944µs, the claim is the conjunction, the budget is named a budget (not a
refresh claim), refresh is measured not inferred, and input-to-photon is out of scope; the entry is hash-locked,
so weakening the method is a visible code diff (this row reddens), not a silent re-hash. `records-preregistered`
additionally hash-locks the entry; `records-firewall` validates the sealed host record.

**Measured (host DANIELDILLBERG, `shell/attest/latency-DANIELDILLBERG.json`, cites LATENCY-0 `c4d8db6a…`).** 200
samples over the 4-move sealed reference session: frame-ready → composited **p50 5,921 / p95 7,078 / p99 7,318 /
max 7,396 µs**, measured refresh **13,298 µs (~75 Hz)**. Verdicts against the locked thresholds: **SOFTWARE-144-
BUDGET FAIL** (p99 7,318 > 6,944), **HARDWARE-144 FAIL** (refresh 13,298 > 6,944), **SUSTAINED-144Hz FAIL**. The
two failures share one cause: the measured interval is frame-ready → *DwmFlush returns*, and DwmFlush blocks
until the next DWM composition, so the present time is the compositor phase wait — bounded by the refresh period
(~half of 13,298 µs). The composed-GDI present is therefore refresh-coupled: on a sub-144Hz panel it cannot fit
the 144Hz budget, not because the software is slow but because DWM composition wait scales with refresh. This is
the baseline the preregistration named. Whether present latency can be *decoupled* from refresh is **PRESENT-1's
hypothesis** (a flip-model / waitable-swapchain path), NOT a consequence LATENCY-0 establishes; reaching
HARDWARE-144 needs a ≥144Hz panel.

**Grade.** DECLARED: the preregistered method, thresholds and interpretation (hash-locked). MEASURED: that the
method IS locked (`latency-preregistered`), and the host number itself — p50/p95/p99/max and the refresh, on
host DANIELDILLBERG, refuting SUSTAINED-144Hz honestly (both conditions FAIL, recorded not massaged). ESTABLISHED
(read off the mechanism): the composed-GDI present is refresh-coupled (frame-ready → next composition), so
SOFTWARE-144-BUDGET *measured on this path* is not display-independent. What LATENCY-0 does NOT establish: that
any other present path could isolate a display-free software latency — that is PRESENT-1's hypothesis, to be
measured, not assumed here.

**does_not_show.** Any latency number (none is claimed until the host record lands). Input-to-photon (capture
hardware). Render time (the kernel bench). The present wait beyond composition (a flip-model / waitable-swapchain
path is a later rung — the composed GDI present is the baseline). Arbitrary interactive load (the fixed sealed
sequence only). Non-Windows hosts.

**Falsifier.** `latency-preregistered` reddens if the method is weakened — a missing condition, a changed
threshold, a dropped conjunction, or a dropped scope limit; `records-preregistered` if the entry is edited after
registration; and when the host record lands, its failure condition (p99 > 6,944µs, or a refresh > 6,944µs, or a
shape not reproducible on a second run) refutes the corresponding claim rather than being massaged into a pass.

## GAUNTLET-0 — measure before optimize; the render breakdown, and a decision rule (seat 13)

**What landed (the method, not the optimization).** GAUNTLET is a performance-certification *staircase* with
progressively narrower intervention, and GAUNTLET-0 is the first tread: the render decomposed, with no renderer
change. `kernel/main.rs --breakdown N` (off-gate, host; `mantle.rs` untouched — it only times the existing pub
calls) measures the reference render at its pub-phase boundaries — **strips** (traversal), **frame** (walls +
floor cast), **emit** (texel pass) — and, separately, the two **witness hashes** (`frame_digest`, `pixel_sha`)
that the render total excludes and an interactive render never pays. `verify/gauntlet.py` compiles, checks the
witnesses against the frozen corpus *before any number*, runs the breakdown and seals a `verdandi-render-breakdown`
record (per-phase p50/p95/p99/max and each render phase's p99 share in permille — no verdict key) as
`kernel/attest/breakdown-<host>.json`, citing GAUNTLET-0. The seat carries **only** the measurement and a
preregistered decision rule; it changes no renderer.

**Design, searched.** "Measure first, then tune" is the rasterizer's own discipline ([ryg on optimizing the
basic rasterizer](https://fgiesen.wordpress.com/2013/02/10/optimizing-the-basic-rasterizer/), [performance &
optimization](https://www.informit.com/articles/article.aspx?p=2115288&seqNum=8)). The preregistered rule
(`verify/preregister.json` → GAUNTLET-0, hash-locked `a8122b4f…`): a render phase must clear **500 permille** of
the render p99 to earn a GAUNTLET-1 seat; GAUNTLET-1 must then prove **byte-identity** against the frozen
reference (a differential oracle — `frame_digest` AND `pixel_sha` equal over the corpus plus adversarial cameras)
*before any speed claim*; and the incremental-floor-cast hypothesis specifically dies unless `frame()` clears the
bar. Correctness stays a headless differential proof; performance stays a host measurement — the two never mix.

**Preliminary (exploratory, container CPU — not the committed host number).** A container breakdown put the p99
render-shares at **strips ≈ 2‰, frame ≈ 306‰, emit ≈ 725‰**, with the witness hashes (`frame_digest` ≈ 20 ms,
`pixel_sha` ≈ 61 ms p99) rivalling the whole render. Read against the locked rule this already refutes the
floor-cast instinct — the floor lives inside `frame` (~30%), while **`emit` (the texel pass) is the dominant
render cost** and would be GAUNTLET-1's target — and flags the witness hashing as a large *verification-only*
tax the interactive path avoids. The committed host record confirms this on the owner's CPU; the shares are the
portable quantity, the microseconds are not.

**Rows.** `gauntlet-preregistered` — the method and decision rule are locked before the host number: the render
phases are named, the 500-permille rule is in both success and failure conditions, GAUNTLET-1 must prove
byte-identity before a speed claim, the incremental-floor-cast hypothesis can die here, the witness hashes are
verification-only, `mantle.rs` is not modified, and the entry is hash-locked — so weakening any of it is a
visible diff, not a silent re-hash. `records-preregistered` additionally hash-locks the entry.

**Grade.** DECLARED: the preregistered method and 500-permille decision rule (hash-locked). MEASURED (live in
the gate): that the method IS locked (`gauntlet-preregistered`). NOT_MEASURED yet (as a committed record): the
host breakdown — produced off-gate by `verify/gauntlet.py` and sealed, like the bench and the present number. The
container preliminary is exploratory only, clearly not the committed number.

**does_not_show.** Any optimization or speedup (GAUNTLET-0 changes no renderer). Floor-vs-walls inside `frame()`,
or any sub-`emit` split (that needs GAUNTLET-1's sibling renderer). Input-to-photon, present, window (none is in
a render number). That the witness hashes are interactive cost (they are verification-only). Any other scene,
tile set or resolution; absolute microseconds (host-specific — the permille shares are portable).

**Falsifier.** `gauntlet-preregistered` reddens if the method is weakened — a phase unnamed, the 500-permille
rule dropped from either condition, the byte-identity precondition removed, the witness-hash or `mantle.rs`
limit dropped; `records-preregistered` if the entry is edited after registration; and when the host record
lands, its failure condition (no render phase ≥ 500‰, or times that do not reconcile with the render total, or a
non-reproducible shape, or a breakdown of anything but the frozen witnesses) kills the single-phase optimization
rather than being massaged into a target.

## GAUNTLET-1a — the emit differential court, seeded and proven; no technique committed (seat 14)

**What landed (the framework, not the optimization).** GAUNTLET-0 seated `emit` as the target; GAUNTLET-1a builds
the court that will judge any candidate `emit`, before a technique is chosen. `kernel/fast.rs` is a SIBLING of the
frozen renderer — never `mantle.rs` — seeded as an **exact transcription** of `Scene::emit` (no optimization).
`kernel/main.rs --fast` renders the candidate against the *same* frozen strips + frame and reports `fast_equal`,
`fast_pixels`, `fast_frame`, a deterministic region measure, and — on any mismatch — a first-differing-pixel
taxonomy (coordinate, region, index, face, frozen vs fast channels). The frame buffer is read-only, so
`frame_digest` cannot move. The comparison is always **candidate → frozen**, never the reverse: the harness is not
the oracle; the candidate is guilty until its bytes agree.

**The law and the cost, read off the source.** Per pixel, `emit` is a ceiling/table copy (0 divides), a wall texel
(`tj = texel(v_base+2r·tn, v_den)`, 1 divide, denominator column-constant), or a floor texel (`tj`, `ti_f` each a
`rem_euclid` + a `div_euclid`, ~4 divides, denominator `kk·Q` moving per row). So `emit` is integer-division-bound
and the floor is the per-pixel hot spot. The **deterministic region measure** (computed from the frozen strips +
frame, no wall-clock) confirms it on the witness frame: **674,760 wall-textured px × 1 = 674,760** vs **694,648
floor-textured px × 4 = 2,778,592** divides — the **floor dominates by ~4×**. So GAUNTLET-1b's exact optimization
targets the floor's per-row perspective divides — not the wall, and not the frame-pass "floor cast" the original
instinct named.

**Design, searched.** Differential testing against a frozen reference at the strongest observable ("measure first,
then tune"; [ryg](https://fgiesen.wordpress.com/2013/02/10/optimizing-the-basic-rasterizer/),
[performance & optimization](https://www.informit.com/articles/article.aspx?p=2115288&seqNum=8)). The GAUNTLET-1
preregistration (`c… 96c42749`, hash-locked) fixes the two-court promotion rule *before* any candidate: byte-identity
to the frozen `emit` (`pixel_sha` and `frame_digest`) over the corpus **plus** adversarial cameras is MANDATORY and
gate-enforced; speed is a SEPARATE court — identical-but-slower is a correctness pass and a performance fail, a
differing pixel is not an accepted renderer at any speed; `mantle.rs` stays frozen; and a speed number is never
cross-compared to GAUNTLET-0's instrumented render absolute (different apparatus).

**Rows.** `gauntlet1-preregistered` — the acceptance/promotion rule is locked (byte-identity mandatory, two courts,
`mantle.rs` frozen, no cross-instrument compare), hash-locked. `gauntlet1-equiv` — the sibling `fast.rs` emit is
byte-identical to the frozen emit over 19 cases (every corpus scene × its tile sets, plus the four spawn facings and
the frozen-traversable sessionwalk positions): `fast_pixels == pixels` and `fast_frame == frame` everywhere — the
seed transcription and the harness are proven before any technique. `gauntlet1-region` — the deterministic divide-work
measure names the floor as GAUNTLET-1b's target.

**Grade.** MEASURED (live, headless): the differential equivalence over corpus + adversarial cameras, and the
deterministic region measure. DECLARED: the hash-locked acceptance/promotion rule. ESTABLISHED (read off the source):
the emit law and its division cost (floor 4 / wall 1 / ceiling 0 per pixel). NOT_MEASURED yet: any speedup — GAUNTLET-1a
commits no optimization; the seed transcription's only claim is byte-identity.

**does_not_show.** Any optimization or speedup (there is none yet — the seed is an exact transcription). Which
technique GAUNTLET-1b will use (uncommitted until the floor path is inspected). A wall-clock region time (the region
measure is source-derived divide-work, a target-finder). The edited-level sessionwalk cameras (28,27 is rock on the
frozen level; the differential renders the unedited corpus). That the harness is the oracle (it is not — `mantle.rs`
is; the candidate is guilty until its bytes agree).

**Falsifier.** `gauntlet1-equiv` reddens if the sibling emit differs from the frozen emit on any case (with the
first-diff taxonomy); `gauntlet1-region` if the divide-work is not per-source or the dominant region is misreported;
`gauntlet1-preregistered` if the acceptance/promotion rule is weakened; and when GAUNTLET-1b's candidate lands, the
same `gauntlet1-equiv` refuses it outright on a single differing pixel, whatever its speed.

## GAUNTLET-1b — the floor divide-collapse: the first exact optimization (seat 15)

**What landed (the first real technique, proven byte-identical).** GAUNTLET-1a named the floor's per-row perspective
divides as the target; GAUNTLET-1b writes the simplest *exact* reduction and nothing more. `kernel/fast.rs`'s floor
loop — and **only** its floor loop — collapses the two `texel(N.rem_euclid(kk·Q), kk·Q)` calls into one `div_euclid`
per floor coordinate: **2 divides per textured floor pixel where the frozen did 4**, and the column-constant `d·EYE_Y`
multiplies are hoisted out of the row loop (no per-pixel `e·kk`). The ceiling and wall passes stay exact
transcriptions; `mantle.rs` is untouched. The candidate is proven byte-identical to the frozen emit — the *same*
`gauntlet1-equiv` court built in 1a now judges a real candidate, and it passes on every corpus and adversarial case.

**The collapse, derived (and why byte-identity is the real proof).** With `den = kk·Q`, `Q == T == 256`, and
`N = e·kk + d·EYE_Y`, the frozen `texel(N.rem_euclid(den), den) = clamp((N.rem_euclid(den)·T).div_euclid(den), 0, T−1)`
reduces **exactly** to `(e + (d·EYE_Y).div_euclid(kk)).rem_euclid(T)`: the clamp never bites (the value is already in
`[0,T)`), and `rem_euclid(256)` is `& (T−1)` for any `i64` (T is a power of two). The identity was checked over
17.6M cases, but the derivation is not the acceptance test — **byte-identity is**: a differing pixel refuses the
candidate at any speed. The deterministic region measure now reports both costs off the same pixel counts: on the
witness frame (34,28,W), frozen floor divide-work **2,778,592** (694,648 px × 4) → candidate **1,389,296** (× 2),
the wall unchanged at **674,760** — **1,389,296 floor divides removed**, the floor still the dominant divide region
left for GAUNTLET-1c.

**Design, searched.** The exact half-reduction is the smallest intervention that attacks the named region: it removes
the redundant `rem_euclid`+scale by recognizing the frozen texel over a `kk·Q` denominator is a fixed-point divide by
`kk` alone. The two-court rule holds: correctness is mandatory and gate-enforced (byte-identity + the deterministic
reduction), speed is measured separately on ONE consistent apparatus and never cross-compared to GAUNTLET-0's
instrumented render absolute. `kernel/main.rs --fast-bench N` times the frozen `mantle` emit and the `fast` emit back
to back over the *same* frozen strips + frame (both must reproduce the witness); `verify/gauntlet1b.py --host NAME`
runs it, checks the witnesses first, and seals `verdandi-gauntlet1b-emit` (an emit-only, same-apparatus delta) to
`kernel/attest/gauntlet1b-<host>.json`, citing the GAUNTLET-1 preregistration.

**Rows.** `gauntlet1-equiv` — unchanged, and now decisive: the candidate `fast.rs` emit (with the collapsed floor) is
byte-identical to the frozen emit over the corpus + adversarial cameras (`fast_pixels == pixels`, `fast_frame ==
frame`). `gauntlet1b-reduction` — new: the candidate is byte-identical on the witness frame AND its floor does exactly
**2 divides/px** (down from the frozen 4), the wall untouched, `floor_saved` exactly the removed half — the
deterministic divide reduction, gate-enforced, no wall-clock.

**Grade.** MEASURED (live, headless): byte-identity of the collapsed-floor candidate over corpus + adversarial
cameras, and the deterministic 4→2 floor divide reduction. ESTABLISHED (derived + 17.6M-case checked, and byte-proven
by the gate): the collapse identity. NOT_MEASURED here: the wall-clock speedup — that is GAUNTLET-1b's separate host
court (`verify/gauntlet1b.py`), sealed off-gate; the gate proves correctness, the host measures speed.

**does_not_show.** A speedup (the gate carries none; the host record does, off-gate). The whole-render cost (the
`--fast-bench` delta is emit only). Any comparison to GAUNTLET-0's instrumented render absolute (different apparatus).
That the harness is the oracle (it is not — `mantle.rs` is; the candidate is guilty until its bytes agree). The
full elimination of the floor's per-row divide (that is GAUNTLET-1c, decided only after this collapse is measured).

**Falsifier.** `gauntlet1-equiv` reddens on a single differing pixel between the collapsed floor and the frozen emit
(with the first-diff taxonomy); `gauntlet1b-reduction` reddens if the candidate is not byte-identical, if the wall
divide-work changes, if the floor is not exactly halved, or if `floor_saved` is not the removed half; and the host
seal refuses to print a number unless both emits reproduce the frozen witness first.

## GAUNTLET-1c — the row-major floor DDA: the perspective divide made per-row (seat 16)

**What landed (the divide eliminated from the pixel, byte-identical).** GAUNTLET-1b halved the floor divides (4→2 per
pixel) and was promoted (emit p99 6928→5455 µs on host). GAUNTLET-1c removes them from the pixel entirely. The floor
is now a **row-major second pass**: the frozen ceiling + wall stay an exact transcription in a column-major pass, and
`kernel/fast.rs::emit` then sweeps the floor row by row. At a fixed row `r`, `kk = 2(r−CY)+1` is constant, so the
perspective divide is done a **bounded number of times per row** and the per-column texel advances by a recurrence —
**O(rows) divides where the collapse did O(pixels)**. On the witness frame that is **2,590 div/rem ops over 518 rows
vs 1,389,296** for the collapse, a **~536× reduction**. The GAUNTLET-1b collapse is retained verbatim as
`fast::emit_collapse` — the same-apparatus baseline the DDA is measured against, never the oracle.

**The DDA, derived off the source.** From `direction(facing, c)`, the camera-space column term `a = 2c+1−W` steps by
`+2` per column while `b = 2·FOCAL` is constant, and each facing carries them onto the world axes so that **exactly one
floor axis is constant across the row and the other is linear in `c`** (N: X varies, Z constant; E: Z varies, X
constant; S, W: the same with a negated step). The frozen (collapse) texel for the varying axis is
`(e + D(c).div_euclid(kk)) & (T−1)` with `D(c) = ±EYE_Y·a(c)` stepping by `±2·EYE_Y`. Tracking `(q, rem) =
(D.div_euclid(kk), D.rem_euclid(kk))` and advancing `D` by its constant step needs **at most one correction** per
column — a Bresenham-exact rational-slope DDA. The constant axis's texel is computed once per row. So per floor row:
~5 `div_euclid`/`rem_euclid` ops (the two step constants, the constant-axis texel, the row's starting `q`/`rem`) and
**zero divides per pixel**.

**Validated before a line of Rust, then proven byte-identical.** The recurrence was checked exhaustively against
`floor(D(c)/kk)` over **2,073,600** points (every floor row `kk = 1..1079`, every column, both step signs; 0
mismatches), and the full facing→assignment mapping and `k` composition against the frozen collapse texel over
**3,932,160** texels (all four facings × 16 cameras × sampled rows × every column; 0 mismatches). The offline proof is
not the acceptance test — **byte-identity is**: the standing `gauntlet1-equiv` court now judges the DDA and finds it
`fast_pixels == pixels` and `fast_frame == frame` over the corpus + adversarial cameras. The row-major pass writes
exactly the floor region (frame index in `[FLOOR0, WALL0)`: floor bands take the texel, stair bands a table copy), so
it never touches Pass 1's ceiling/wall pixels and the seam/stairs stay correct.

**Design, searched.** The naïve column-major elimination was infeasible (the quotient jumps by up to 32,768 near the
horizon as `kk` grows); the row-major restructure is the feasible exact form — at fixed `kk` the slope is rational and
constant, which is the classic DDA/Bresenham setting. The two courts hold: correctness is mandatory and gate-enforced
(byte-identity of the DDA **and** the retained collapse, plus the deterministic per-row divide count); speed is a
SEPARATE, same-apparatus court judged against the **collapse** (GAUNTLET-1b's promoted baseline), never frozen and
never GAUNTLET-0's instrumented absolute. `kernel/main.rs --fast-bench` times frozen / collapse / DDA back to back
(all three must reproduce the witness); `verify/gauntlet1c.py --host NAME` seals `verdandi-gauntlet1c-emit` to
`kernel/attest/gauntlet1c-<host>.json`, citing the GAUNTLET-1 preregistration.

**Rows.** `gauntlet1-equiv` — unchanged and now judging the DDA: byte-identical to the frozen emit over the corpus +
adversarial cameras. `gauntlet1b-reduction` — retargeted to the retained collapse baseline (`collapse_equal`): it
stays byte-identical and 2 divides/floor px, so the baseline is pinned to the oracle. `gauntlet1c-dda` — new: the DDA
is byte-identical, the collapse is byte-identical, and the floor divide-work is `5 × floor_rows` (per-row) strictly
below the collapse's `2 × floor_px` (per-pixel) — the structural elimination, gate-enforced, no wall-clock.

**Grade.** MEASURED (live, headless): byte-identity of the DDA over corpus + adversarial cameras, byte-identity of the
retained collapse, and the deterministic per-row divide reduction. ESTABLISHED (derived + 2.07M/3.93M-case checked,
and byte-proven by the gate): the row-major DDA identity. NOT_MEASURED here: the wall-clock speedup — that is
GAUNTLET-1c's separate host court (`verify/gauntlet1c.py`), judged against the collapse baseline, sealed off-gate.

**does_not_show.** A speedup (the gate carries none; the host record does, off-gate, vs the collapse). The whole-render
cost (the `--fast-bench` delta is emit only). Any comparison to GAUNTLET-0's instrumented render absolute (different
apparatus). That the frozen→DDA cumulative number is the promotion test (1c is promoted against the collapse baseline,
not frozen). That the harness is the oracle (it is not — `mantle.rs` is; the candidate is guilty until its bytes
agree).

**Falsifier.** `gauntlet1-equiv` reddens on a single differing pixel between the DDA and the frozen emit (with the
first-diff taxonomy — and camera/row boundary cases are in the corpus: the four spawn facings, the sessionwalk
positions, the floor-less near-wall frames where `floor_rows = 0`); `gauntlet1c-dda` reddens if the DDA or the
retained collapse is not byte-identical, if the DDA divide-work is not `5 × floor_rows`, or if it does not fall below
the collapse's; the host seal refuses to print a number unless all three emits reproduce the frozen witness first.

## RE-BREAKDOWN-1 — probe emit's cost structure after the DDA (measure, not optimize) (seat 17)

**What landed (a measurement rung, no optimization).** GAUNTLET-1c cut the floor's divides ~536&times; for ~12% wall-clock
— the textbook signal that arithmetic was not the sole limiter. Following GAUNTLET-0's rule (measure when the cost
structure shifts), RE-BREAKDOWN-1 attributes emit's internal cost two ways and commits **no** candidate renderer.
**Court A** (deterministic, gate-enforced, wall-clock-free): `kernel/fast.rs::structure` reads off the frozen frame the
divide-work, the tile/map memory reads (3 texel + 3 map indirections per textured pixel), the tile **working-set
cardinality**, the floor's **adjacent-column texel-stride locality**, and a **write-once coverage** proof. **Court B**
(host, off-gate): `kernel/fast.rs::probe` is a fenced ablation apparatus — `emit_probe<MODE>`, a faithful copy of the
DDA emit, `black_box`-anchored, run at ADDR (classify + coordinate/DDA, constant store), LOOKUP (+ tile fetch), FULL
(+ map/assembly), and VERIFY (+ real store) — timed against emit on one apparatus (`--emit-breakdown`).

**The two courts, the fence, the negative control.** The probes are *measurement apparatus, not renderers*: a probe may
be wrong by construction, provided its wrongness is isolated from the certified path and its work is a demonstrable
subset of it. That subset relation is **gate-proven, not asserted**: `emit_probe<VERIFY>` is byte-identical to `emit`
(and to the frozen oracle), so ADDR/LOOKUP/FULL are truncations of the real path. The fence is structural — the
production `emit` and the GAUNTLET-1b `emit_collapse` baseline reference **no** probe (a gate row reads the source and
asserts so), and the probes never enter the promotion chain. The Court B increments (LOOKUP&minus;ADDR ~ tile fetch,
FULL&minus;LOOKUP ~ map/assembly) are named exactly what they are: **incremental wall-clock attribution under controlled
ablation** — non-additive (cache/branch/scheduling), with no architectural counters claimed.

**What Court A establishes (host-independent).** On the witness frame: emit writes all **2,073,600** framebuffer pixels
**exactly once** (no double-write, no temp buffer); the textured work is **1,369,408 px &times; 3 = 4,108,224** tile reads
and as many map indirections; the tile **working set is 60,176 floor / 65,529 wall distinct texels of 65,536** — both
regions stream nearly the whole 192 KB tile per frame, a working set far past L1; and only **590 permille** of adjacent-
column floor texels fall within a 64-byte cache line (~41% cross a line). This is the memory/locality axis, named as
deterministic data — a candidate for the bottleneck the divide cut left behind, to be confirmed (or not) by Court B.

**The promotion rule (locked before the host number).** A dominant lookup increment or pathological locality LOCKs a
data-layout/locality court; a dominant address/DDA increment the arithmetic path; a dominant full-write increment the
framebuffer path; results that disagree materially, or no clear dominance, DEFER — no optimization by intuition.

**Rows.** `rebreakdown1-preregistered` — the method and the promotion table are hash-locked (`66c3cb64`): measures not
optimizes, two courts, probes-are-apparatus with VERIFY == emit as the subset proof, the incremental/non-additive
boundary, never vs GAUNTLET-0's absolute. `rebreakdown1-structure` — Court A on gate: VERIFY byte-identical to emit,
write-once coverage, 3 reads/textured px, and the working-set + locality reported as data. `rebreakdown1-fence` — the
source-level assertion that the production renderers call no probe.

**Grade.** MEASURED (live, headless, deterministic): Court A's structure, the VERIFY subset proof, the write-once
coverage. DECLARED: the hash-locked method + promotion table. NOT_MEASURED here: the host ablation wall-clock — that is
Court B's sealed host record (`verify/rebreakdown1.py` &rarr; `kernel/attest/emit-breakdown-<host>.json`), the user's run.

**does_not_show.** Any optimization (this rung commits none). The Court B increments as pure resource costs (they are
incremental ablation deltas, non-additive). The whole-render cost (emit only). Any comparison to GAUNTLET-0's
instrumented absolute. That Court A's op counts are a wall-clock (they are a source-cost proxy that names candidates).
That the probes are renderers (they are fenced apparatus; a differing probe pixel is expected).

**Falsifier.** `rebreakdown1-structure` reddens if `emit_probe<VERIFY>` differs from emit, if the memory reads are not
3/textured px, or if any framebuffer pixel is written other than exactly once; `rebreakdown1-fence` reddens if the
production `emit`/`emit_collapse` references a probe or the apparatus loses its `black_box` anchor;
`rebreakdown1-preregistered` reddens if the method or promotion table is weakened.

## The open clause, now with named rungs (skybox, physics)

New semantics the studio did not inherit from Urðr, recorded so they are built on purpose and not by accident:

- **SKYBOX-0 (new VIEW semantics).** The sky is `vista`'s LUT sky-bands per depth, frozen in Urðr. Authoring a
  skybox is a VIEW law Urðr never certified, so it takes one of the two open-clause routes: earned in Urðr and
  re-frozen here as `urdr-oracle-2`, or a Verðandi-local VIEW reference pinned by rows here. Not built until a
  route is chosen and a semantics exists to render it.
- **PHYSICS-0 (new CORE semantics).** Urðr is a renderer; there is no physics in the frozen oracle at all.
  Physics is CORE, and CORE has ONE route only — earned in Urðr (or its successor) and re-frozen. The studio
  authors no physics before a certified semantics renders it; anything else would be a second authority, which
  the charter forbids.

The seated order reaches everything the frozen oracle certifies: WORKSHOP-1 *authors* walls, ground and
textures, INPUT-0 *moves the camera* through them (a VIEW mutation, never an edit), SESSION-WALK *fuses* the two
into one interleaved log where authoring and moving genuinely interact — the studio's real loop — and
SHELL-PLAYBACK proves the window *displays exactly that becoming* and nothing else, through the SHELL-0 blit law.
SHELL-PLAYBACK-b now plays a sealed session in the real window (host-run); LATENCY-0 is measured (the composed-GDI
present is refresh-coupled on a ~75Hz panel — all three verdicts FAIL honestly); and GAUNTLET-0 has decomposed
the render and locked the optimization decision rule. Each rung was proven headless first. The performance
staircase and what remains:

- **The GAUNTLET staircase.** GAUNTLET-0 (seated) measured the render breakdown and locked the 500‰ rule; `emit`
  cleared it (695‰ on host). GAUNTLET-1a (seated) built the differential court — a sibling `fast.rs` emit proven
  byte-identical to the frozen emit over corpus + adversarial cameras — and its deterministic region measure named
  the **floor's per-row perspective divides** as the target (floor divide-work ~4× the wall's). GAUNTLET-1b (seated)
  wrote the first *exact* floor optimization — the **divide-collapse**, 4→2 floor divides per pixel, proven
  byte-identical through the same `gauntlet1-equiv` court and gated by `gauntlet1b-reduction`; measured 6928→5455 µs
  p99 emit on host (~1.27×), promoted. GAUNTLET-1c (seated) took the divide off the pixel entirely — the **row-major
  floor DDA**, O(rows) divides not O(pixels) (~536× fewer on the witness), proven byte-identical through the same
  court and gated by `gauntlet1c-dda`, with the collapse retained verbatim as the same-apparatus baseline; its speed
  is judged against that collapse (`verify/gauntlet1c.py`, sealed off-gate). RE-BREAKDOWN-1 (seated) then re-measured
  the shifted cost structure before any further algorithm — Court A (deterministic: the tile working set streams nearly
  the whole texture, ~41% of adjacent floor texels cross a cache line) and Court B (a fenced ablation apparatus, host
  off-gate) — naming the memory/locality axis as a candidate and committing no optimization. The next optimization
  court is chosen by its promotion table, from the host ablation. **GAUNTLET-2+** only after a measured result.
  **LATENCY-1** then reruns the same fixed session and records the before/after render delta against LATENCY-0's
  immutable baseline.
- **PRESENT-1 (flip-model / waitable-swapchain).** LATENCY-0 *established* only that the composed-GDI present is
  refresh-coupled. PRESENT-1's *hypothesis* — falsifiable, to be measured, never assumed — is that a flip-model
  present CAN decouple present latency from refresh; it becomes experimentally valuable once the render fits the
  budget (so it is not competing with an 11.6 ms render). Off-gate/host; HARDWARE-144 additionally needs a ≥144Hz panel.
- **Interactive capture (parallel, not entangled with the performance chain).** The inverse of SHELL-PLAYBACK:
  raw window/device event → binding → typed action/edit → SESSION-WALK append → the SAME sealed representation
  headless authoring produces. A shell/input problem, not a new authority; measured against the existing session
  machinery, never modifying it.
- **The named future slices** (courted, not seated): IMPOSSIBILITY-0 (measured negative results as level
  preconditions), SEMANTIC-0 (a float-free, geometry-bound semantic layer as a Verðandi-local new-semantics
  authority), MERGE-0 (deterministic commutative merge of non-conflicting edits, stripped of consensus/time).

The boundary holds end to end: SESSION-WALK proves what is becoming, SHELL-PLAYBACK proves the window shows
exactly that becoming, LATENCY-0/GAUNTLET measure how fast it is produced and shown — and every performance step
survives the same pixel-level oracle, so speed is never traded for correctness and a failed experiment stays
permanently useful evidence. Skybox and physics stay beyond the frozen oracle, gated behind the new-semantics route.
