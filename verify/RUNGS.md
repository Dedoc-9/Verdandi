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
textures, INPUT-0 *moves the camera* through them (a VIEW mutation, never an edit), and SESSION-WALK *fuses* the
two into one interleaved log where authoring and moving genuinely interact — the studio's real loop, proven
headless. The locked forward order is **SESSION-WALK → SHELL-PLAYBACK → LATENCY-0**: SHELL-PLAYBACK drives the
window from the same sealed session/`.walk` representation, and only then does LATENCY-0 measure input-to-present
on the host (where the 144Hz/batch scheduler becomes a preregistered, measured hypothesis). Skybox and physics
stay beyond the frozen oracle, named here, gated behind the new-semantics route.
